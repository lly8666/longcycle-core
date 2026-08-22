from __future__ import annotations

import hashlib
import json
import stat
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
