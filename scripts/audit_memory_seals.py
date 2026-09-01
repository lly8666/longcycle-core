from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from longcycle.application.memory_campaign import (  # noqa: E402
    RecallPassOutcome,
    SaturationPolicy,
    SealReviewState,
    evaluate_campaign_saturation,
)

SEAL_DECISION_SCHEMA = "longcycle-memory-seal-decision/v1"
SEAL_SUPERSESSION_SCHEMA = "longcycle-memory-seal-supersession/v1"
MAX_MEMORY_CONTROL_BYTES = 1024 * 1024
MAX_RECENT_SEAL_OUTCOMES = 8
_MEMORY_ROOT = PurePosixPath("research_data/memory")
_SEALED_WORDS = {"seal", "sealed"}
_BLIND_SOURCE_VISIBILITY = {"none", "blind_memory_only", "atlas_only"}
_OPEN_REPLACEMENT_STAGES = {
    "orientation_only",
    "active_recall",
    "low_novelty_confirmation",
    "seal_candidate",
}
_CONTROL_MARKERS = (
    b'"seal"',
    b'"saturation"',
    b'"saturation_result"',
    b'"seal_decision"',
    b"longcycle-memory-seal-",
)


class MemorySealAuditError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SealClaim:
    location: str


@dataclass(frozen=True, slots=True)
class SealAuditFinding:
    artifact_path: str
    location: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class SealSupersession:
    campaign_id: str
    artifact_path: str
    artifact_sha256: str
    replacement_stage: str
    correction_ref: str
    record_path: str


def is_memory_control_candidate(raw: bytes) -> bool:
    return any(marker in raw for marker in _CONTROL_MARKERS)


def _normalized_word(value: str) -> str:
    return value.strip().casefold().replace("-", "_").replace(" ", "_")


def _declares_sealed(container: Mapping[str, Any]) -> bool:
    if container.get("saturated") is True:
        return True
    for field in ("state", "status", "decision"):
        value = container.get(field)
        if not isinstance(value, str):
            continue
        normalized = _normalized_word(value)
        if normalized in _SEALED_WORDS or normalized.startswith("sealed_"):
            return True
    return False


def find_seal_claims(payload: Mapping[str, Any]) -> tuple[SealClaim, ...]:
    """Find only explicit structured seal/saturation decisions, not prose mentions."""

    if payload.get("schema_version") in {SEAL_DECISION_SCHEMA, SEAL_SUPERSESSION_SCHEMA}:
        return ()

    findings: list[SealClaim] = []

    def visit(value: Any, location: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                child_location = f"{location}.{key}"
                if key in {"seal", "saturation", "saturation_result"}:
                    if isinstance(child, Mapping) and _declares_sealed(child):
                        findings.append(SealClaim(location=child_location))
                elif key == "seal_decision" and isinstance(child, str):
                    normalized = _normalized_word(child)
                    if normalized in _SEALED_WORDS or normalized.startswith("sealed_"):
                        findings.append(SealClaim(location=child_location))
                visit(child, child_location)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{location}[{index}]")

    visit(payload, "$")
    return tuple(findings)


def seal_decision_refs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    refs: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                if str(raw_key) == "seal_decision_ref" and isinstance(child, str) and child.strip():
                    refs.add(child.strip())
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return tuple(sorted(refs))


def _required_object(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise MemorySealAuditError(f"{key} must be an object")
    return value


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MemorySealAuditError(f"{key} must be a non-blank string")
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise MemorySealAuditError(f"{key} must be a boolean")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MemorySealAuditError(f"{key} must be an integer")
    return value


def _required_string_list(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise MemorySealAuditError(f"{key} must be a list of non-blank strings")
    return tuple(item.strip() for item in value)


def _safe_repo_path(value: str, *, field: str) -> str:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise MemorySealAuditError(f"{field} must be a safe repository-relative path")
    return candidate.as_posix()


def validate_seal_decision(
    *,
    decision: Mapping[str, Any],
    decision_path: str,
    sealed_artifact_path: str,
    sealed_artifact_bytes: bytes,
    sealed_artifact: Mapping[str, Any],
    reference_exists: Callable[[str], bool],
) -> None:
    """Recompute one exact-artifact decision; caller declarations are never trusted."""

    if decision.get("schema_version") != SEAL_DECISION_SCHEMA:
        raise MemorySealAuditError(f"{decision_path} has unsupported schema_version")

    recorded_path = _safe_repo_path(
        _required_string(decision, "sealed_artifact_path"), field="sealed_artifact_path"
    )
    if recorded_path != sealed_artifact_path:
        raise MemorySealAuditError("seal decision targets a different artifact path")

    recorded_digest = _required_string(decision, "sealed_artifact_sha256").casefold()
    actual_digest = hashlib.sha256(sealed_artifact_bytes).hexdigest()
    if recorded_digest != actual_digest:
        raise MemorySealAuditError("seal decision does not match the exact artifact bytes")

    campaign_id = _required_string(decision, "campaign_id")
    shard_id = _required_string(decision, "shard_id")
    model_vintage = _required_string(decision, "model_vintage")
    artifact_campaign_id = sealed_artifact.get("campaign_id")
    if isinstance(artifact_campaign_id, str) and artifact_campaign_id.strip() != campaign_id:
        raise MemorySealAuditError("seal decision campaign_id does not match the artifact")
    artifact_shard_id = sealed_artifact.get("shard_id")
    if isinstance(artifact_shard_id, str) and artifact_shard_id.strip() != shard_id:
        raise MemorySealAuditError("seal decision shard_id does not match the artifact")
    artifact_model_vintage = sealed_artifact.get("model_vintage")
    if isinstance(artifact_model_vintage, str) and artifact_model_vintage.strip() != model_vintage:
        raise MemorySealAuditError("seal decision model_vintage does not match the artifact")

    source_visibility = _required_string(decision, "source_visibility")
    if source_visibility not in _BLIND_SOURCE_VISIBILITY:
        raise MemorySealAuditError("source_visibility is not a blind-memory-only value")

    review = _required_object(decision, "review")
    negative_space_ref = _safe_repo_path(
        _required_string(review, "negative_space_review_ref"), field="negative_space_review_ref"
    )
    challenger_ref = _safe_repo_path(
        _required_string(review, "independent_challenger_ref"),
        field="independent_challenger_ref",
    )
    if negative_space_ref == challenger_ref:
        raise MemorySealAuditError(
            "negative-space and independent-challenger reviews must be separate artifacts"
        )
    forbidden_review_refs = {sealed_artifact_path, decision_path}
    if negative_space_ref in forbidden_review_refs or challenger_ref in forbidden_review_refs:
        raise MemorySealAuditError("review references cannot point to the artifact or its decision")
    for ref in (negative_space_ref, challenger_ref):
        if not reference_exists(ref):
            raise MemorySealAuditError(f"review reference does not exist at audited head: {ref}")

    review_state = SealReviewState(
        campaign_stage=_required_string(review, "campaign_stage"),  # type: ignore[arg-type]
        negative_space_review_complete=_required_bool(review, "negative_space_review_complete"),
        independent_challenger_complete=_required_bool(
            review, "independent_challenger_complete"
        ),
        fresh_search_used=_required_bool(review, "fresh_search_used"),
    )

    raw_outcomes = decision.get("recent_outcomes")
    if not isinstance(raw_outcomes, list):
        raise MemorySealAuditError("recent_outcomes must be a list")
    if len(raw_outcomes) > MAX_RECENT_SEAL_OUTCOMES:
        raise MemorySealAuditError(
            f"recent_outcomes exceeds the bounded limit of {MAX_RECENT_SEAL_OUTCOMES}"
        )
    outcomes: list[RecallPassOutcome] = []
    receipt_refs: list[str] = []
    for index, raw in enumerate(raw_outcomes):
        if not isinstance(raw, Mapping):
            raise MemorySealAuditError(f"recent_outcomes[{index}] must be an object")
        receipt_ref = _safe_repo_path(
            _required_string(raw, "receipt_ref"), field=f"recent_outcomes[{index}].receipt_ref"
        )
        if not reference_exists(receipt_ref):
            raise MemorySealAuditError(
                f"pass receipt does not exist at audited head: {receipt_ref}"
            )
        receipt_refs.append(receipt_ref)
        outcomes.append(
            RecallPassOutcome(
                pass_id=_required_string(raw, "pass_id"),
                family=_required_string(raw, "family"),
                novel_lead_count=_required_int(raw, "novel_lead_count"),
                duplicate_lead_count=_required_int(raw, "duplicate_lead_count"),
                high_importance_novel_count=_required_int(
                    raw, "high_importance_novel_count"
                ),
            )
        )
    pass_ids = [outcome.pass_id for outcome in outcomes]
    if len(pass_ids) != len(set(pass_ids)):
        raise MemorySealAuditError("recent_outcomes must use distinct pass_id values")
    if len(receipt_refs) != len(set(receipt_refs)):
        raise MemorySealAuditError("recent_outcomes must use distinct receipt_ref values")
    if set(receipt_refs) & {sealed_artifact_path, decision_path, negative_space_ref, challenger_ref}:
        raise MemorySealAuditError("pass receipts must be separate from seal and review artifacts")

    raw_policy = decision.get("policy", {})
    if not isinstance(raw_policy, Mapping):
        raise MemorySealAuditError("policy must be an object when present")
    policy = SaturationPolicy(
        consecutive_low_novelty_passes=int(raw_policy.get("consecutive_low_novelty_passes", 3)),
        max_high_importance_novel_per_low_pass=int(
            raw_policy.get("max_high_importance_novel_per_low_pass", 1)
        ),
        minimum_distinct_recent_families=int(
            raw_policy.get("minimum_distinct_recent_families", 3)
        ),
    )
    result = evaluate_campaign_saturation(
        outcomes=outcomes,
        has_major_coverage_gaps=_required_bool(decision, "has_major_coverage_gaps"),
        required_long_tail_families_missing=_required_string_list(
            decision, "required_long_tail_families_missing"
        ),
        review=review_state,
        policy=policy,
    )

    declared = _required_object(decision, "declared_result")
    declared_saturated = _required_bool(declared, "saturated")
    declared_reasons = _required_string_list(declared, "reason_codes")
    if declared_saturated != result.saturated or declared_reasons != result.reason_codes:
        raise MemorySealAuditError("declared_result does not match the recomputed seal decision")
    if not result.saturated:
        reasons = ",".join(result.reason_codes) or "unspecified"
        raise MemorySealAuditError(f"seal gate rejected the artifact: {reasons}")


def parse_seal_supersessions(
    *,
    payload: Mapping[str, Any],
    record_path: str,
    reference_exists: Callable[[str], bool],
) -> tuple[SealSupersession, ...]:
    if payload.get("schema_version") != SEAL_SUPERSESSION_SCHEMA:
        return ()

    campaign_id = _required_string(payload, "campaign_id")
    replacement_stage = _required_string(payload, "replacement_stage")
    if replacement_stage not in _OPEN_REPLACEMENT_STAGES:
        raise MemorySealAuditError("supersession replacement_stage must remain before sealed")
    _required_string(payload, "reason_code")
    correction_ref = _safe_repo_path(
        _required_string(payload, "correction_ref"), field="correction_ref"
    )
    if not reference_exists(correction_ref):
        raise MemorySealAuditError(f"correction_ref does not exist at audited head: {correction_ref}")

    raw_refs = payload.get("superseded_seals")
    if not isinstance(raw_refs, list) or not raw_refs:
        raise MemorySealAuditError("superseded_seals must be a non-empty list")

    records: list[SealSupersession] = []
    for index, raw in enumerate(raw_refs):
        if not isinstance(raw, Mapping):
            raise MemorySealAuditError(f"superseded_seals[{index}] must be an object")
        artifact_path = _safe_repo_path(
            _required_string(raw, "artifact_path"), field="artifact_path"
        )
        if correction_ref == artifact_path:
            raise MemorySealAuditError("correction_ref cannot point to the superseded artifact")
        artifact_sha256 = _required_string(raw, "artifact_sha256").casefold()
        if len(artifact_sha256) != 64 or any(char not in "0123456789abcdef" for char in artifact_sha256):
            raise MemorySealAuditError("artifact_sha256 must be a lowercase SHA-256 digest")
        records.append(
            SealSupersession(
                campaign_id=campaign_id,
                artifact_path=artifact_path,
                artifact_sha256=artifact_sha256,
                replacement_stage=replacement_stage,
                correction_ref=correction_ref,
                record_path=record_path,
            )
        )
    return tuple(records)


def audit_memory_payloads(
    *,
    payloads: Mapping[str, tuple[Mapping[str, Any], bytes]],
    load_payload: Callable[[str], tuple[Mapping[str, Any], bytes]],
    reference_exists: Callable[[str], bool],
) -> tuple[SealAuditFinding, ...]:
    supersessions: dict[tuple[str, str], SealSupersession] = {}
    findings: list[SealAuditFinding] = []

    for path, (payload, _raw) in payloads.items():
        try:
            records = parse_seal_supersessions(
                payload=payload,
                record_path=path,
                reference_exists=reference_exists,
            )
        except (MemorySealAuditError, TypeError, ValueError) as exc:
            findings.append(SealAuditFinding(path, "$", "ERROR", str(exc)))
            continue
        for record in records:
            try:
                target_payload, target_raw = load_payload(record.artifact_path)
            except (MemorySealAuditError, KeyError, TypeError, ValueError) as exc:
                findings.append(
                    SealAuditFinding(path, "$", "ERROR", f"cannot load superseded seal: {exc}")
                )
                continue
            actual_digest = hashlib.sha256(target_raw).hexdigest()
            if actual_digest != record.artifact_sha256:
                findings.append(
                    SealAuditFinding(
                        path,
                        "$",
                        "ERROR",
                        "supersession does not match the exact old artifact bytes",
                    )
                )
                continue
            target_campaign_id = target_payload.get("campaign_id")
            if (
                isinstance(target_campaign_id, str)
                and target_campaign_id.strip() != record.campaign_id
            ):
                findings.append(
                    SealAuditFinding(path, "$", "ERROR", "supersession campaign_id mismatch")
                )
                continue
            if not find_seal_claims(target_payload):
                findings.append(
                    SealAuditFinding(path, "$", "ERROR", "superseded target has no seal claim")
                )
                continue
            key = (record.artifact_path, record.artifact_sha256)
            if key in supersessions:
                findings.append(
                    SealAuditFinding(path, "$", "ERROR", "duplicate exact-artifact supersession")
                )
            supersessions[key] = record
            if record.artifact_path not in payloads:
                findings.append(
                    SealAuditFinding(
                        path,
                        "$",
                        "SUPERSESSION_VALID",
                        f"reopens {record.artifact_path} as {record.replacement_stage}",
                    )
                )

    for path, (payload, _raw) in payloads.items():
        if payload.get("schema_version") != SEAL_DECISION_SCHEMA:
            continue
        try:
            target_path = _safe_repo_path(
                _required_string(payload, "sealed_artifact_path"), field="sealed_artifact_path"
            )
            if target_path in payloads:
                continue
            target_payload, target_raw = load_payload(target_path)
            validate_seal_decision(
                decision=payload,
                decision_path=path,
                sealed_artifact_path=target_path,
                sealed_artifact_bytes=target_raw,
                sealed_artifact=target_payload,
                reference_exists=reference_exists,
            )
        except (MemorySealAuditError, KeyError, TypeError, ValueError) as exc:
            findings.append(SealAuditFinding(path, "$", "ERROR", str(exc)))
        else:
            findings.append(
                SealAuditFinding(path, "$", "DECISION_VALID", f"authorizes {target_path}")
            )

    for path, (payload, raw) in payloads.items():
        claims = find_seal_claims(payload)
        if not claims:
            continue
        digest = hashlib.sha256(raw).hexdigest()
        supersession = supersessions.get((path, digest))
        if supersession is not None:
            for claim in claims:
                findings.append(
                    SealAuditFinding(
                        path,
                        claim.location,
                        "SUPERSEDED",
                        f"replacement={supersession.replacement_stage} via {supersession.record_path}",
                    )
                )
            continue

        refs = seal_decision_refs(payload)
        if len(refs) != 1:
            detail = "missing seal_decision_ref" if not refs else "multiple seal_decision_ref values"
            for claim in claims:
                findings.append(SealAuditFinding(path, claim.location, "ERROR", detail))
            continue

        decision_path = _safe_repo_path(refs[0], field="seal_decision_ref")
        try:
            decision, _decision_raw = load_payload(decision_path)
            validate_seal_decision(
                decision=decision,
                decision_path=decision_path,
                sealed_artifact_path=path,
                sealed_artifact_bytes=raw,
                sealed_artifact=payload,
                reference_exists=reference_exists,
            )
        except (MemorySealAuditError, KeyError, TypeError, ValueError) as exc:
            for claim in claims:
                findings.append(SealAuditFinding(path, claim.location, "ERROR", str(exc)))
            continue

        for claim in claims:
            findings.append(
                SealAuditFinding(path, claim.location, "AUTHORIZED", f"decision={decision_path}")
            )
    return tuple(findings)


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip() or "no Git diagnostic"
        raise MemorySealAuditError(f"git {' '.join(args[:2])} failed: {detail}")
    return result


def _git_bytes(root: Path, *args: str) -> bytes:
    return _run_git(root, *args).stdout


def _verify_ref(root: Path, ref: str) -> None:
    if not ref.strip() or ref.startswith("-"):
        raise MemorySealAuditError(f"unsafe Git ref: {ref!r}")
    _run_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")


def _changed_memory_json_paths(root: Path, *, base_ref: str, branch: str) -> tuple[str, ...]:
    _verify_ref(root, base_ref)
    _verify_ref(root, branch)
    output = _git_bytes(
        root,
        "diff",
        "--diff-filter=AMR",
        "--name-only",
        "-z",
        f"{base_ref}...{branch}",
        "--",
        _MEMORY_ROOT.as_posix(),
    )
    return tuple(
        sorted(
            path
            for path in output.decode("utf-8", errors="surrogateescape").split("\0")
            if path.endswith(".json")
        )
    )


def _load_payload_at_ref(
    root: Path, *, ref: str, path: str
) -> tuple[Mapping[str, Any], bytes]:
    safe_path = _safe_repo_path(path, field="artifact path")
    raw = _git_bytes(root, "show", f"{ref}:{safe_path}")
    return _decode_control_payload(path=safe_path, raw=raw)


def _decode_control_payload(*, path: str, raw: bytes) -> tuple[Mapping[str, Any], bytes]:
    if len(raw) > MAX_MEMORY_CONTROL_BYTES:
        raise MemorySealAuditError(f"{path} exceeds the 1 MiB memory-control limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MemorySealAuditError(f"{path} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise MemorySealAuditError(f"{path} must contain a JSON object")
    return payload, raw


def audit_git_range(root: Path, *, base_ref: str, branch: str) -> tuple[SealAuditFinding, ...]:
    paths = _changed_memory_json_paths(root, base_ref=base_ref, branch=branch)
    payloads: dict[str, tuple[Mapping[str, Any], bytes]] = {}
    for path in paths:
        raw = _git_bytes(root, "show", f"{branch}:{path}")
        if not is_memory_control_candidate(raw):
            continue
        payloads[path] = _decode_control_payload(path=path, raw=raw)

    def load_payload(path: str) -> tuple[Mapping[str, Any], bytes]:
        return _load_payload_at_ref(root, ref=branch, path=path)

    def reference_exists(path: str) -> bool:
        result = subprocess.run(
            ["git", "cat-file", "-t", f"{branch}:{path}"],
            cwd=root,
            capture_output=True,
        )
        return result.returncode == 0 and result.stdout.strip() == b"blob"

    return audit_memory_payloads(
        payloads=payloads,
        load_payload=load_payload,
        reference_exists=reference_exists,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit changed structured memory-seal claims. Each must carry one recomputable "
            "exact-artifact decision or one exact append-only supersession."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--report-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        findings = audit_git_range(args.root.resolve(), base_ref=args.base_ref, branch=args.branch)
    except MemorySealAuditError as exc:
        print(f"MEMORY_SEAL_AUDIT_ERROR {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        print(
            f"MEMORY_SEAL_{finding.status} path={finding.artifact_path} "
            f"location={finding.location} detail={finding.detail}"
        )
    errors = sum(finding.status == "ERROR" for finding in findings)
    claims = sum(
        finding.status in {
            "ERROR",
            "AUTHORIZED",
            "SUPERSEDED",
            "DECISION_VALID",
            "SUPERSESSION_VALID",
        }
        for finding in findings
    )
    outcome = "PASS" if errors == 0 else "FAIL"
    print(f"MEMORY_SEAL_AUDIT_{outcome} claims={claims} errors={errors}")
    return 0 if errors == 0 or args.report_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
