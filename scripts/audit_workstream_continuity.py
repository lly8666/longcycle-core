from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MAX_CONTROL_RECORD_BYTES = 16 * 1024
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from longcycle.application.workstream_continuity import (  # noqa: E402
    MAX_ANCESTRY_EDGES,
    MAX_CURSOR_BYTES,
    MAX_RESERVATION_BYTES,
    MAX_TOTAL_TOUCHED_PATHS,
    MAX_TOUCHED_PATHS_PER_EDGE,
    WORKSTREAM_CONTINUITY_RESULT_SCHEMA,
    WORKSTREAM_ID_PATTERN,
    RemoteAncestryEdge,
    RemoteReferenceFact,
    RemoteWorkstreamFacts,
    WorkstreamContinuityResult,
    WorkstreamCursorV2,
    WorkstreamReservationV2,
    evaluate_workstream_continuity,
)


class WorkstreamContinuityAuditError(RuntimeError):
    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh remote main and one exact worker ref, then derive CLEAN, "
            "RECOVERY_REQUIRED, or BLOCKED without trusting the local checkout."
        )
    )
    parser.add_argument("workstream_id")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--main-branch", default="main")
    return parser


def _run_git(
    root: Path,
    *args: str,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
    )
    if result.returncode not in allowed_returncodes:
        detail = result.stderr.strip() or result.stdout.strip() or "no Git diagnostic"
        raise WorkstreamContinuityAuditError(
            f"git {' '.join(args[:2])} failed with exit {result.returncode}: {detail}"
        )
    return result


def _git(root: Path, *args: str) -> str:
    return _run_git(root, *args).stdout.strip()


def _normalize_branch(value: str) -> str:
    prefix = "refs/heads/"
    return value[len(prefix) :] if value.startswith(prefix) else value


def _validate_branch(root: Path, branch: str) -> str:
    normalized = _normalize_branch(branch.strip())
    if not normalized or normalized.startswith("-"):
        raise WorkstreamContinuityAuditError(f"unsafe branch name {branch!r}")
    checked = _run_git(
        root,
        "check-ref-format",
        f"refs/heads/{normalized}",
        allowed_returncodes=(0, 1),
    )
    if checked.returncode != 0:
        raise WorkstreamContinuityAuditError(f"invalid branch name {branch!r}")
    return normalized


def _fetch_remote_branch(
    root: Path,
    *,
    remote: str,
    branch: str,
    destination_ref: str,
) -> str:
    if not remote.strip() or remote.startswith("-"):
        raise WorkstreamContinuityAuditError(f"unsafe remote name {remote!r}")
    _git(root, "remote", "get-url", remote)
    normalized_branch = _validate_branch(root, branch)
    _git(
        root,
        "fetch",
        "--no-tags",
        "--force",
        "--no-write-fetch-head",
        remote,
        f"+refs/heads/{normalized_branch}:{destination_ref}",
    )
    return _git(root, "rev-parse", "--verify", f"{destination_ref}^{{commit}}")


def _load_json_at_ref(
    root: Path,
    *,
    ref: str,
    path: str,
    max_bytes: int,
) -> dict[str, Any]:
    object_spec = f"{ref}:{path}"
    size = int(_git(root, "cat-file", "-s", object_spec))
    if size > max_bytes:
        raise WorkstreamContinuityAuditError(f"{path} exceeds the {max_bytes}-byte hot-state limit")
    raw = _git(root, "show", object_spec)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkstreamContinuityAuditError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkstreamContinuityAuditError(f"{path} must contain a JSON object")
    return payload


def _commit_exists(root: Path, sha: str) -> bool:
    checked = _run_git(
        root,
        "cat-file",
        "-e",
        f"{sha}^{{commit}}",
        allowed_returncodes=(0, 1, 128),
    )
    return checked.returncode == 0


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    checked = _run_git(
        root,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        allowed_returncodes=(0, 1),
    )
    return checked.returncode == 0


def _bounded_ancestry_edges(
    root: Path,
    *,
    checkpoint_sha: str,
    remote_head_sha: str,
) -> tuple[tuple[RemoteAncestryEdge, ...], bool]:
    if checkpoint_sha == remote_head_sha:
        return (), True

    revision_range = f"{checkpoint_sha}..{remote_head_sha}"
    count = int(
        _git(
            root,
            "rev-list",
            "--count",
            f"--max-count={MAX_ANCESTRY_EDGES + 1}",
            revision_range,
        )
    )
    if count > MAX_ANCESTRY_EDGES:
        return (), False

    lines = tuple(
        line
        for line in _git(
            root,
            "rev-list",
            "--reverse",
            "--topo-order",
            "--parents",
            revision_range,
        ).splitlines()
        if line
    )
    parsed = tuple(tuple(line.split()) for line in lines)
    commits = {parts[0] for parts in parsed}
    raw_edges: list[tuple[str, str]] = []
    for parts in parsed:
        commit_sha, *parents = parts
        for parent_sha in parents:
            if parent_sha == checkpoint_sha or parent_sha in commits:
                raw_edges.append((parent_sha, commit_sha))
    if len(raw_edges) > MAX_ANCESTRY_EDGES or not raw_edges:
        return (), False

    edges: list[RemoteAncestryEdge] = []
    total_paths = 0
    complete = True
    for parent_sha, commit_sha in raw_edges:
        paths = tuple(
            sorted(
                {
                    line
                    for line in _git(
                        root,
                        "diff",
                        "--name-only",
                        "--no-renames",
                        parent_sha,
                        commit_sha,
                        "--",
                    ).splitlines()
                    if line
                }
            )
        )
        remaining = MAX_TOTAL_TOUCHED_PATHS - total_paths
        edge_limit = min(MAX_TOUCHED_PATHS_PER_EDGE, max(remaining, 0))
        if len(paths) > edge_limit:
            paths = paths[:edge_limit]
            complete = False
        total_paths += len(paths)
        edges.append(
            RemoteAncestryEdge(
                parent_sha=parent_sha,
                commit_sha=commit_sha,
                touched_paths=paths,
            )
        )
    return tuple(edges), complete


def _reference_facts(
    root: Path,
    *,
    worker_head_sha: str,
    cursor: WorkstreamCursorV2,
) -> tuple[RemoteReferenceFact, ...]:
    groups = (
        ("verification", cursor.verification_refs),
        ("artifact", cursor.artifact_refs),
        ("integration_request", cursor.integration_request_refs),
        ("receipt", cursor.receipt_refs),
    )
    facts: list[RemoteReferenceFact] = []
    for kind, refs in groups:
        for ref in refs:
            object_spec = f"{worker_head_sha}:{ref}"
            object_type = _run_git(
                root,
                "cat-file",
                "-t",
                object_spec,
                allowed_returncodes=(0, 1, 128),
            )
            if object_type.returncode != 0:
                facts.append(
                    RemoteReferenceFact(
                        ref=ref,
                        kind=kind,
                        state="missing",
                        detail="path is absent from the exact remote worker head",
                    )
                )
                continue
            resolved_type = object_type.stdout.strip()
            object_oid = _git(root, "rev-parse", "--verify", object_spec)
            if resolved_type != "blob":
                facts.append(
                    RemoteReferenceFact(
                        ref=ref,
                        kind=kind,
                        state="invalid",
                        git_blob_oid=object_oid,
                        detail=f"expected a durable file blob, observed {resolved_type or 'unknown'}",
                    )
                )
                continue
            object_size = int(_git(root, "cat-file", "-s", object_spec))
            if kind in {"integration_request", "receipt"} and object_size > MAX_CONTROL_RECORD_BYTES:
                facts.append(
                    RemoteReferenceFact(
                        ref=ref,
                        kind=kind,
                        state="invalid",
                        git_blob_oid=object_oid,
                        detail=(
                            f"bounded control record is {object_size} bytes; "
                            f"limit is {MAX_CONTROL_RECORD_BYTES}"
                        ),
                    )
                )
                continue
            facts.append(
                RemoteReferenceFact(
                    ref=ref,
                    kind=kind,
                    state="valid",
                    git_blob_oid=object_oid,
                    detail="file blob resolved at the exact remote worker head",
                )
            )
    return tuple(facts)


def _validate_main_reservation_context(
    root: Path,
    *,
    main_head_sha: str,
    reservation: WorkstreamReservationV2,
) -> None:
    """Cross-check the complete reservation against its exact main-side owners."""

    pointer = _load_json_at_ref(
        root,
        ref=main_head_sha,
        path=".longcycle/baseline/current.json",
        max_bytes=MAX_RESERVATION_BYTES,
    )
    if pointer.get("current_baseline") != reservation.baseline:
        raise WorkstreamContinuityAuditError(
            "main reservation baseline does not match the exact main Baseline pointer"
        )

    contract = _load_json_at_ref(
        root,
        ref=main_head_sha,
        path=reservation.change_contract_path,
        max_bytes=MAX_RESERVATION_BYTES,
    )
    admission = _load_json_at_ref(
        root,
        ref=main_head_sha,
        path=reservation.capability_admission_path,
        max_bytes=MAX_RESERVATION_BYTES,
    )
    if contract.get("schema_version") != "longcycle-change-contract/v1":
        raise WorkstreamContinuityAuditError("main workstream Change Contract schema is invalid")
    if admission.get("schema_version") != "longcycle-capability-admission/v2":
        raise WorkstreamContinuityAuditError("main workstream capability admission schema is invalid")
    if contract.get("intent_id") != reservation.intent_id:
        raise WorkstreamContinuityAuditError("reservation and Change Contract intent_id disagree")
    if admission.get("intent_id") != reservation.intent_id:
        raise WorkstreamContinuityAuditError("reservation and capability admission intent_id disagree")
    if contract.get("baseline") != reservation.baseline:
        raise WorkstreamContinuityAuditError("reservation and Change Contract baseline disagree")

    admission_targets = admission.get("target_capability_ids")
    if not isinstance(admission_targets, list) or set(admission_targets) != set(
        reservation.target_capability_ids
    ):
        raise WorkstreamContinuityAuditError(
            "reservation and capability admission target owners disagree"
        )

    capability_index = _load_json_at_ref(
        root,
        ref=main_head_sha,
        path=".longcycle/capabilities/active-index.json",
        max_bytes=64 * 1024,
    )
    active = capability_index.get("active")
    if not isinstance(active, list):
        raise WorkstreamContinuityAuditError("main capability index has no active owner list")
    active_ids = {
        item.get("id")
        for item in active
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    unknown_targets = set(reservation.target_capability_ids) - active_ids
    if unknown_targets:
        raise WorkstreamContinuityAuditError(
            f"reservation routes to inactive or unknown capability owners {sorted(unknown_targets)}"
        )

    level = contract.get("change_level")
    disposition = admission.get("disposition")
    if level not in {"L1", "L2", "L3", "L4"}:
        raise WorkstreamContinuityAuditError("workstream Change Contract has an invalid change_level")
    if disposition not in {"reuse", "extend", "replace", "new"}:
        raise WorkstreamContinuityAuditError("workstream admission has an invalid disposition")
    if reservation.integration_lane == "parallel" and (
        level not in {"L1", "L2"} or disposition not in {"reuse", "extend"}
    ):
        raise WorkstreamContinuityAuditError(
            "parallel workstream authority must remain L1/L2 plus reuse/extend"
        )


def audit_remote_workstream(
    *,
    root: Path,
    workstream_id: str,
    remote_name: str = "origin",
    main_branch: str = "main",
) -> WorkstreamContinuityResult:
    root = root.resolve()
    if not WORKSTREAM_ID_PATTERN.fullmatch(workstream_id):
        raise WorkstreamContinuityAuditError(f"invalid workstream id {workstream_id!r}")

    audit_root = f"refs/longcycle/audit/{workstream_id}"
    main_branch = _validate_branch(root, main_branch)
    main_head_sha = _fetch_remote_branch(
        root,
        remote=remote_name,
        branch=main_branch,
        destination_ref=f"{audit_root}/main",
    )
    reservation_path = f".longcycle/workstreams/{workstream_id}/reservation.json"
    reservation = WorkstreamReservationV2.model_validate(
        _load_json_at_ref(
            root,
            ref=main_head_sha,
            path=reservation_path,
            max_bytes=MAX_RESERVATION_BYTES,
        )
    )
    if reservation.workstream_id != workstream_id:
        raise WorkstreamContinuityAuditError(
            f"{reservation_path} declares workstream_id {reservation.workstream_id!r}"
        )
    _validate_main_reservation_context(
        root,
        main_head_sha=main_head_sha,
        reservation=reservation,
    )

    worker_head_sha = _fetch_remote_branch(
        root,
        remote=remote_name,
        branch=reservation.branch,
        destination_ref=f"{audit_root}/worker",
    )
    cursor = WorkstreamCursorV2.model_validate(
        _load_json_at_ref(
            root,
            ref=worker_head_sha,
            path=reservation.cursor_path,
            max_bytes=MAX_CURSOR_BYTES,
        )
    )

    checkpoint_exists = _commit_exists(root, cursor.checkpoint_based_on_head_sha)
    checkpoint_is_ancestor = checkpoint_exists and _is_ancestor(
        root,
        cursor.checkpoint_based_on_head_sha,
        worker_head_sha,
    )
    if checkpoint_is_ancestor:
        ancestry_edges, ancestry_complete = _bounded_ancestry_edges(
            root,
            checkpoint_sha=cursor.checkpoint_based_on_head_sha,
            remote_head_sha=worker_head_sha,
        )
    else:
        ancestry_edges = ()
        ancestry_complete = checkpoint_exists

    verification_head_exists: bool | None = None
    verification_head_is_ancestor: bool | None = None
    if cursor.verification_head_sha is not None:
        verification_head_exists = _commit_exists(root, cursor.verification_head_sha)
        if verification_head_exists and checkpoint_exists:
            verification_head_is_ancestor = _is_ancestor(
                root,
                cursor.verification_head_sha,
                cursor.checkpoint_based_on_head_sha,
            )
        else:
            verification_head_is_ancestor = False

    remote_facts = RemoteWorkstreamFacts(
        authoritative_remote=remote_name,
        main_ref=f"refs/heads/{main_branch}",
        main_head_sha=main_head_sha,
        worker_ref=f"refs/heads/{reservation.branch}",
        remote_worker_head_sha=worker_head_sha,
        refreshed_from_remote=True,
        checkpoint_is_ancestor=checkpoint_is_ancestor,
        ancestry_complete=ancestry_complete,
        verification_head_exists=verification_head_exists,
        verification_head_is_ancestor_of_checkpoint=verification_head_is_ancestor,
        ancestry_edges=ancestry_edges,
        handoff_only_paths=(reservation.cursor_path,),
        reference_facts=_reference_facts(
            root,
            worker_head_sha=worker_head_sha,
            cursor=cursor,
        ),
    )
    return evaluate_workstream_continuity(
        reservation=reservation,
        cursor=cursor,
        remote=remote_facts,
    )


def _blocked_error_payload(exc: Exception) -> dict[str, object]:
    return {
        "schema_version": WORKSTREAM_CONTINUITY_RESULT_SCHEMA,
        "audit_only": True,
        "status": "BLOCKED",
        "can_execute_cursor": False,
        "requires_handoff_repair": False,
        "requires_coordinator": True,
        "reason_codes": ["remote_preflight_error"],
        "summary": "Remote worker continuity could not be derived from valid bounded facts.",
        "next_action": "Stop worker execution and route this exact preflight error to the coordinator.",
        "error": str(exc),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = audit_remote_workstream(
            root=args.root,
            workstream_id=args.workstream_id,
            remote_name=args.remote,
            main_branch=args.main_branch,
        )
    except (OSError, ValidationError, WorkstreamContinuityAuditError) as exc:
        print(json.dumps(_blocked_error_payload(exc), ensure_ascii=False, indent=2))
        return 2

    print(result.model_dump_json(indent=2))
    if result.status == "CLEAN":
        return 0
    if result.status == "RECOVERY_REQUIRED":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
