from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class ResearchSourcePackSpec(BaseModel):
    """Immutable externally acquired source-pack identity.

    Transport restoration is deliberately outside this contract. The runner receives one local
    ZIP and verifies that it is exactly the repository-declared Release asset before using bytes.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    transport: Literal["github_release"]
    release_tag: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    sha256: str = Field(pattern=_SHA256_PATTERN)


class GroundedEvidenceRepairOperation(BaseModel):
    """One deliberately narrow repair to a Grounded Evidence fragment expectation.

    V1 only permits exact structured expected-value repair. Claim context, source/document identity,
    locators and acceptance cannot be patched through this mechanism.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    fragment_key: str = Field(min_length=1)
    field: Literal["expected_value"]
    from_value: Any = Field(alias="from")
    to_value: Any = Field(alias="to")
    epistemic_effect: str = Field(min_length=1)


class GroundedEvidenceSpecRepair(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-grounded-evidence-spec-repair/v1"]
    task_id: str = Field(min_length=1)
    base_spec_path: str = Field(min_length=1)
    repair_reason: str = Field(min_length=1)
    probe: dict[str, Any]
    repairs: tuple[GroundedEvidenceRepairOperation, ...]
    acceptance_unchanged: dict[str, Any]

    @model_validator(mode="after")
    def has_repairs(self) -> GroundedEvidenceSpecRepair:
        if not self.repairs:
            raise ValueError("grounded Evidence repair overlay must contain at least one repair")
        return self


class ResearchOrchestrationSpec(BaseModel):
    """Bounded composition contract for source pack -> Evidence -> optional Reality.

    The orchestration spec references the existing epistemic specs instead of restating their
    semantics. It owns only immutable material verification, explicit repair overlays, execution
    order and immutable-path guards.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-research-orchestration/v1"]
    task_id: str = Field(min_length=1)
    source_pack: ResearchSourcePackSpec
    evidence_spec_path: str = Field(min_length=1)
    evidence_repair_paths: tuple[str, ...] = ()
    reality_spec_path: str | None = None
    immutable_paths: tuple[str, ...] = ()


class VerifiedMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    material_path: str
    sha256: str = Field(pattern=_SHA256_PATTERN)
    size_bytes: int = Field(ge=0)


class PreparedEvidenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sha256: str = Field(pattern=_SHA256_PATTERN)
    repair_count: int = Field(ge=0)


def _resolved_under(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository/work root: {relative_path}") from exc
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_orchestration_spec(path: Path) -> ResearchOrchestrationSpec:
    return ResearchOrchestrationSpec.model_validate_json(path.read_text(encoding="utf-8"))


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _fragment_rows(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = spec.get("fragments")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Grounded Evidence spec must contain non-empty fragments")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Grounded Evidence fragment rows must be objects")
        key = row.get("fragment_key")
        if not isinstance(key, str) or not key:
            raise ValueError("Grounded Evidence fragment row has invalid fragment_key")
        if key in indexed:
            raise ValueError(f"duplicate Grounded Evidence fragment_key: {key}")
        indexed[key] = row
    return indexed


def materialize_evidence_spec(
    *,
    repo_root: Path,
    evidence_spec_path: str,
    repair_paths: tuple[str, ...],
    destination: Path,
) -> tuple[dict[str, Any], PreparedEvidenceSpec]:
    source_path = _resolved_under(repo_root, evidence_spec_path)
    spec = load_json_object(source_path, label="Grounded Evidence spec")
    task_id = spec.get("task_id")
    acceptance = spec.get("acceptance")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("Grounded Evidence spec has invalid task_id")
    if not isinstance(acceptance, dict):
        raise ValueError("Grounded Evidence spec has invalid acceptance")

    fragments = _fragment_rows(spec)
    repair_count = 0
    for repair_path in repair_paths:
        overlay_path = _resolved_under(repo_root, repair_path)
        overlay = GroundedEvidenceSpecRepair.model_validate_json(
            overlay_path.read_text(encoding="utf-8")
        )
        if overlay.base_spec_path != evidence_spec_path:
            raise ValueError(
                f"repair overlay {repair_path} targets {overlay.base_spec_path!r}, "
                f"not {evidence_spec_path!r}"
            )
        if overlay.task_id != task_id:
            raise ValueError(f"repair overlay {repair_path} task_id does not match Evidence spec")
        if overlay.acceptance_unchanged != acceptance:
            raise ValueError(f"repair overlay {repair_path} would change Evidence acceptance")
        for operation in overlay.repairs:
            try:
                fragment = fragments[operation.fragment_key]
            except KeyError as exc:
                raise ValueError(
                    f"repair overlay {repair_path} references unknown fragment "
                    f"{operation.fragment_key!r}"
                ) from exc
            current = fragment.get(operation.field)
            if current != operation.from_value:
                raise ValueError(
                    f"repair from-value mismatch for {operation.fragment_key}.{operation.field}: "
                    f"expected {operation.from_value!r}, found {current!r}"
                )
            fragment[operation.field] = operation.to_value
            repair_count += 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    destination.write_text(rendered, encoding="utf-8")
    return spec, PreparedEvidenceSpec(
        path=str(destination),
        sha256=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        repair_count=repair_count,
    )


def _required_materials(evidence_spec: dict[str, Any]) -> dict[str, str]:
    rows = evidence_spec.get("documents")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Grounded Evidence spec must contain non-empty documents")
    required: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Grounded Evidence document rows must be objects")
        material_path = row.get("material_path")
        expected_sha256 = row.get("expected_sha256")
        if not isinstance(material_path, str) or not material_path:
            raise ValueError(
                "research orchestration v1 requires every Evidence document to use "
                "materialized source transport"
            )
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
            raise ValueError(f"materialized document {material_path!r} has no pinned raw SHA-256")
        previous = required.get(material_path)
        if previous is not None and previous != expected_sha256:
            raise ValueError(f"material path {material_path!r} has conflicting expected digests")
        required[material_path] = expected_sha256
    return required


def _validated_zip_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    for info in archive.infolist():
        posix_path = PurePosixPath(info.filename)
        if posix_path.is_absolute() or ".." in posix_path.parts:
            raise ValueError(f"source pack contains unsafe path: {info.filename!r}")
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ValueError(f"source pack contains symbolic link: {info.filename!r}")
        if info.is_dir():
            continue
        normalized = posix_path.as_posix()
        if normalized in entries:
            raise ValueError(f"source pack contains duplicate file path: {normalized!r}")
        entries[normalized] = info
    return entries


def verify_and_extract_source_pack(
    *,
    source_pack_path: Path,
    source_pack_spec: ResearchSourcePackSpec,
    evidence_spec: dict[str, Any],
    material_root: Path,
) -> tuple[VerifiedMaterial, ...]:
    if source_pack_path.name != source_pack_spec.file_name:
        raise ValueError(
            f"source pack filename mismatch: expected {source_pack_spec.file_name!r}, "
            f"got {source_pack_path.name!r}"
        )
    actual_pack_sha = sha256_file(source_pack_path)
    if actual_pack_sha != source_pack_spec.sha256:
        raise ValueError(
            f"source pack digest mismatch: expected {source_pack_spec.sha256}, got {actual_pack_sha}"
        )

    required = _required_materials(evidence_spec)
    material_root.mkdir(parents=True, exist_ok=True)
    verified: list[VerifiedMaterial] = []
    with zipfile.ZipFile(source_pack_path, "r") as archive:
        entries = _validated_zip_entries(archive)
        for relative_path, expected_sha256 in sorted(required.items()):
            try:
                info = entries[PurePosixPath(relative_path).as_posix()]
            except KeyError as exc:
                raise ValueError(f"source pack is missing required material: {relative_path}") from exc
            raw = archive.read(info)
            actual_sha = hashlib.sha256(raw).hexdigest()
            if actual_sha != expected_sha256:
                raise ValueError(
                    f"material digest mismatch for {relative_path}: "
                    f"expected {expected_sha256}, got {actual_sha}"
                )
            destination = _resolved_under(material_root, relative_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            verified.append(
                VerifiedMaterial(
                    material_path=relative_path,
                    sha256=actual_sha,
                    size_bytes=len(raw),
                )
            )
    return tuple(verified)


def immutable_path_digest(repo_root: Path, relative_path: str) -> str:
    target = _resolved_under(repo_root, relative_path)
    if not target.exists():
        raise ValueError(f"immutable guard path does not exist: {relative_path}")
    digest = hashlib.sha256()
    if target.is_file():
        rows = [(relative_path, sha256_file(target))]
    else:
        rows = []
        for path in sorted(item for item in target.rglob("*") if item.is_file()):
            rows.append((path.relative_to(repo_root.resolve()).as_posix(), sha256_file(path)))
    for path_text, file_sha in rows:
        digest.update(path_text.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def snapshot_immutable_paths(
    repo_root: Path,
    relative_paths: tuple[str, ...],
) -> dict[str, str]:
    return {path: immutable_path_digest(repo_root, path) for path in relative_paths}


def execution_phases(spec: ResearchOrchestrationSpec) -> tuple[str, ...]:
    if spec.reality_spec_path is None:
        return ("grounded_evidence",)
    return ("grounded_evidence", "reality_projection")


def _repo_path(repo_root: Path, relative_path: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"repository path escapes root: {relative_path}") from exc
    return candidate


def _clean_work_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError(f"work directory must be absent or empty: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _successful_evidence_result(
    *,
    output_path: Path,
    prepared_spec: dict[str, Any],
) -> dict[str, Any]:
    payload = load_json_object(output_path, label="Grounded Evidence execution")
    if payload.get("ok") is not True:
        raise ValueError("Grounded Evidence execution did not return ok=true")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("Grounded Evidence execution has no result object")

    documents = prepared_spec.get("documents")
    fragments = prepared_spec.get("fragments")
    acceptance = prepared_spec.get("acceptance")
    if not isinstance(documents, list) or not isinstance(fragments, list):
        raise ValueError("prepared Evidence spec has invalid documents/fragments")
    if not isinstance(acceptance, dict):
        raise ValueError("prepared Evidence spec has invalid acceptance")
    result_documents = result.get("documents")
    result_fragments = result.get("fragments")
    result_acceptance = result.get("acceptance")
    if not isinstance(result_documents, list) or len(result_documents) != len(documents):
        raise ValueError("Grounded Evidence execution document count does not match prepared spec")
    if not isinstance(result_fragments, list) or len(result_fragments) != len(fragments):
        raise ValueError("Grounded Evidence execution fragment count does not match prepared spec")
    if not isinstance(result_acceptance, dict):
        raise ValueError("Grounded Evidence execution has invalid acceptance result")
    expected_pairs = {
        "persisted_document_versions": acceptance.get("required_documents"),
        "persisted_evidence_fragments": acceptance.get("required_fragments"),
        "fact_assertions_created": acceptance.get("facts_created"),
        "judgment_assertions_created": acceptance.get("judgments_created"),
    }
    for result_key, expected in expected_pairs.items():
        if result_acceptance.get(result_key) != expected:
            raise ValueError(
                f"Grounded Evidence acceptance mismatch for {result_key}: "
                f"expected {expected!r}, got {result_acceptance.get(result_key)!r}"
            )
    return result


def _successful_reality_result(
    *,
    output_path: Path,
    reality_spec_path: Path,
) -> dict[str, Any]:
    result = load_json_object(output_path, label="Reality execution")
    verification = result.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("Reality execution has no verification object")
    reality_spec = load_json_object(reality_spec_path, label="Reality spec")
    facts = reality_spec.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("Reality spec must contain non-empty facts")
    expected_count = len(facts)
    if verification.get("fact_count") != expected_count:
        raise ValueError("Reality fact_count does not match Reality spec")
    if verification.get("canonical_reality_count") != expected_count:
        raise ValueError("Reality canonical row count does not match Reality spec")
    for key in (
        "all_reconciled_accept",
        "all_fact_evidence_ids_persisted",
        "all_known_times_derived_from_grounded_evidence",
        "stable_assertion_to_canonical_mapping",
        "valid_time_semantics_preserved",
        "observation_semantics_preserved",
    ):
        if verification.get(key) is not True:
            raise ValueError(f"Reality verification gate failed: {key}")
    return result


def _work_member(path: Path, work_dir: Path) -> str:
    return path.resolve().relative_to(work_dir.resolve()).as_posix()


def execute_research_orchestration(
    *,
    repo_root: Path,
    spec: ResearchOrchestrationSpec,
    source_pack_path: Path,
    work_dir: Path,
    skip_db_upgrade: bool = False,
) -> dict[str, Any]:
    """Execute the validated source-pack -> Evidence -> optional Reality composition.

    Transport restoration is still an outer adapter concern. This function starts from one already
    restored immutable source pack and delegates epistemic work to the existing repository scripts.
    """

    repo_root = repo_root.resolve()
    work_dir = _clean_work_dir(work_dir)
    source_pack_path = source_pack_path.resolve()
    before_immutable = snapshot_immutable_paths(repo_root, spec.immutable_paths)
    prepared_path = work_dir / "prepared-grounded-evidence-spec.json"
    prepared_spec, prepared = materialize_evidence_spec(
        repo_root=repo_root,
        evidence_spec_path=spec.evidence_spec_path,
        repair_paths=spec.evidence_repair_paths,
        destination=prepared_path,
    )
    material_root = work_dir / "material"
    materials = verify_and_extract_source_pack(
        source_pack_path=source_pack_path,
        source_pack_spec=spec.source_pack,
        evidence_spec=prepared_spec,
        material_root=material_root,
    )

    if not skip_db_upgrade:
        _run_command(["longcycle", "--json", "db", "upgrade"])

    evidence_output = work_dir / "grounded-evidence-execution.json"
    _run_command(
        [
            sys.executable,
            str(repo_root / "scripts" / "execute_grounded_evidence_spec.py"),
            str(prepared_path),
            "--material-root",
            str(material_root),
            "--output",
            str(evidence_output),
        ]
    )
    evidence_result = _successful_evidence_result(
        output_path=evidence_output,
        prepared_spec=prepared_spec,
    )

    reality_summary: dict[str, Any] | None = None
    if spec.reality_spec_path is not None:
        reality_spec_path = _repo_path(repo_root, spec.reality_spec_path)
        reality_output = work_dir / "reality-execution.json"
        _run_command(
            [
                sys.executable,
                str(repo_root / "scripts" / "execute_grounded_reality_projection.py"),
                str(reality_spec_path),
                str(evidence_output),
                "--output",
                str(reality_output),
            ]
        )
        reality_result = _successful_reality_result(
            output_path=reality_output,
            reality_spec_path=reality_spec_path,
        )
        reality_summary = {
            "spec_path": spec.reality_spec_path,
            "artifact_member": _work_member(reality_output, work_dir),
            "output_sha256": sha256_file(reality_output),
            "verification": reality_result["verification"],
        }

    after_immutable = snapshot_immutable_paths(repo_root, spec.immutable_paths)
    if before_immutable != after_immutable:
        changed = sorted(
            path
            for path in set(before_immutable) | set(after_immutable)
            if before_immutable.get(path) != after_immutable.get(path)
        )
        raise ValueError(f"immutable-path guard changed during orchestration: {changed}")

    return {
        "schema_version": "longcycle-research-orchestration-execution/v1",
        "task_id": spec.task_id,
        "phases": list(execution_phases(spec)),
        "source_pack": spec.source_pack.model_dump(mode="json"),
        "prepared_evidence_spec": {
            "artifact_member": _work_member(prepared_path, work_dir),
            "sha256": prepared.sha256,
            "repair_count": prepared.repair_count,
        },
        "materials": [item.model_dump(mode="json") for item in materials],
        "evidence": {
            "spec_path": spec.evidence_spec_path,
            "repair_paths": list(spec.evidence_repair_paths),
            "artifact_member": _work_member(evidence_output, work_dir),
            "output_sha256": sha256_file(evidence_output),
            "acceptance": evidence_result["acceptance"],
        },
        "reality": reality_summary,
        "immutable_paths": before_immutable,
    }


def execute_research_orchestration_receipt(
    *,
    repo_root: Path,
    spec_path: Path,
    source_pack_path: Path,
    work_dir: Path,
    output_path: Path,
    skip_db_upgrade: bool = False,
) -> dict[str, Any]:
    """Run orchestration and always attempt to persist one machine-readable success/failure receipt."""

    output_path = output_path.resolve()
    try:
        spec = load_orchestration_spec(spec_path.resolve())
        result = execute_research_orchestration(
            repo_root=repo_root,
            spec=spec,
            source_pack_path=source_pack_path,
            work_dir=work_dir,
            skip_db_upgrade=skip_db_upgrade,
        )
        payload: dict[str, Any] = {"ok": True, "result": result}
    except Exception as exc:
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return payload
