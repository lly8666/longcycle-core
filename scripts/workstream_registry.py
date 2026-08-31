from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSTREAM_ROOT = ROOT / ".longcycle" / "workstreams"
INDEX_PATH = WORKSTREAM_ROOT / "active-index.json"
BASELINE_POINTER_PATH = ROOT / ".longcycle" / "baseline" / "current.json"
CAPABILITY_INDEX_PATH = ROOT / ".longcycle" / "capabilities" / "active-index.json"

LEGACY_WORKSTREAM_SCHEMA = "longcycle-workstream/v1"
RESERVATION_SCHEMA = "longcycle-workstream-reservation/v2"
CURSOR_SCHEMA = "longcycle-workstream-cursor/v2"
INDEX_SCHEMA = "longcycle-workstream-index/v1"
CURSOR_PROGRESS_STATES = {
    "planned",
    "in_progress",
    "partial",
    "verifying",
    "ready_for_integration",
    "blocked",
    "paused",
    "superseded",
}
# Keep the legacy "active" spelling so the public dependency/boundary helpers remain
# compatible with already-integrated v1 fixtures and callers.
ACTIVE_STATUSES = CURSOR_PROGRESS_STATES | {"active"}
ALL_STATUSES = ACTIVE_STATUSES | {"integrated", "closed"}
LIFECYCLE_STATES = {"active", "integrated", "closed"}
KINDS = {"industry", "product", "platform", "research", "governance"}
LANES = {"parallel", "global_serial"}
CAPABILITY_CLASSES = {"high_capability_reasoning", "bounded_execution"}
CHANGE_LEVELS = {"L1", "L2", "L3", "L4"}
DISPOSITIONS = {"reuse", "extend", "replace", "new"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

# Hot control-plane state must stay bounded as Git history and closed workstreams grow.
# These are guard rails, not product-data limits; large artifacts belong outside these files.
MAX_ACTIVE_WORKSTREAMS = 64
MAX_RESERVATION_BYTES = 16 * 1024
MAX_CURSOR_BYTES = 16 * 1024
MAX_CONTROL_RECORD_BYTES = 16 * 1024
MAX_INDEX_BYTES = 64 * 1024
MAX_DEPENDENCIES = 16
MAX_WRITE_PREFIXES = 32
MAX_CAPABILITY_OWNERS = 16
MAX_PARENT_REFS = 8
MAX_CURSOR_REFS_PER_KIND = 8
MAX_CURSOR_REFS_TOTAL = 24
MAX_TEXT_CHARS = 4_096
MAX_PATH_CHARS = 512

# The full reservation schema is owned here. WorkstreamContinuity intentionally imports
# only its identity/fencing projection; accepting arbitrary extra reservation fields here
# would let a branch create a second, ambiguous source of goal/scope authority.
RESERVATION_FIELDS = (
    "schema_version",
    "workstream_id",
    "kind",
    "lifecycle_state",
    "branch",
    "base_main_sha",
    "baseline",
    "intent_id",
    "change_contract_path",
    "capability_admission_path",
    "integration_lane",
    "parent_goal_ref",
    "goal",
    "done_when",
    "exclusive_write_prefixes",
    "target_capability_ids",
    "dependencies",
    "reservation_revision",
    "assignment_epoch",
    "cursor_path",
)
RESERVATION_FIELD_SET = frozenset(RESERVATION_FIELDS)

CURSOR_REFERENCE_FIELDS = (
    "verification_refs",
    "artifact_refs",
    "integration_request_refs",
    "receipt_refs",
)

# A cursor may repeat only the identity/fencing values that it must acknowledge. It may
# not shadow main-owned reservation intent or authority with convenient branch-local data.
CURSOR_FORBIDDEN_RESERVATION_FIELDS = {
    "kind",
    "lifecycle_state",
    "integration_lane",
    "base_main_sha",
    "baseline",
    "intent_id",
    "change_contract_path",
    "capability_admission_path",
    "parent_goal_ref",
    "goal",
    "done_when",
    "target_capability_ids",
    "exclusive_write_prefixes",
    "dependencies",
    "cursor_path",
}

# A parallel workstream may read these paths but may not claim autonomous write ownership.
# If it needs a change here, it records an integration_request and the mainline integration
# lane performs the shared-control-plane update after parallel work converges.
GLOBAL_CONTROL_PREFIXES = (
    ".longcycle/baseline",
    ".longcycle/handoff",
    ".longcycle/capabilities/current-admission.json",
    ".longcycle/capabilities/cards",
    ".longcycle/capabilities/active-index.json",
    ".longcycle/change-contract/current.json",
    ".longcycle/workstreams/active-index.json",
    ".github/workflows",
    "migrations",
    "pyproject.toml",
    "ARCHITECTURE_BASELINE_V1.md",
    "STRATEGIC_COMPASS.md",
    "METHODOLOGY_CORE.md",
)


class WorkstreamRegistryError(ValueError):
    pass


def _load(path: Path, *, max_bytes: int | None = None, label: str | None = None) -> dict[str, Any]:
    display = label or path.relative_to(ROOT).as_posix()
    try:
        if max_bytes is not None and path.stat().st_size > max_bytes:
            raise WorkstreamRegistryError(f"{display} exceeds {max_bytes} bytes")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except WorkstreamRegistryError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkstreamRegistryError(f"cannot read valid JSON {display}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkstreamRegistryError(f"{display} must contain an object")
    return payload


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _repo_prefix(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise WorkstreamRegistryError(f"{label} must be a nonblank repository-relative path prefix")
    value = raw.strip().rstrip("/")
    if len(value) > MAX_PATH_CHARS:
        raise WorkstreamRegistryError(f"{label} exceeds {MAX_PATH_CHARS} characters")
    parts = value.split("/")
    posix_path = PurePosixPath(value)
    if (
        posix_path.is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
        or "\\" in value
        or "\x00" in value
        or ":" in value
        or "*" in value
    ):
        raise WorkstreamRegistryError(f"{label} must be a literal repository-relative prefix: {raw}")
    resolved = (ROOT / value).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise WorkstreamRegistryError(f"{label} escapes repository: {raw}") from exc
    return value


def _text_list(
    raw: Any,
    *,
    label: str,
    allow_empty: bool = False,
    max_items: int | None = None,
) -> list[str]:
    if not isinstance(raw, list) or (not raw and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise WorkstreamRegistryError(f"{label} must be {qualifier}")
    if max_items is not None and len(raw) > max_items:
        raise WorkstreamRegistryError(f"{label} exceeds the limit of {max_items} items")
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise WorkstreamRegistryError(f"{label} contains blank/non-text data")
        value = item.strip()
        if len(value) > MAX_TEXT_CHARS:
            raise WorkstreamRegistryError(f"{label} contains text longer than {MAX_TEXT_CHARS} characters")
        values.append(value)
    if len(values) != len(set(values)):
        raise WorkstreamRegistryError(f"{label} contains duplicates")
    return values


def _nonblank_text(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise WorkstreamRegistryError(f"{label} must be nonblank")
    value = raw.strip()
    if len(value) > MAX_TEXT_CHARS:
        raise WorkstreamRegistryError(f"{label} exceeds {MAX_TEXT_CHARS} characters")
    return value


def _positive_int(raw: Any, *, label: str, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < minimum:
        qualifier = "non-negative" if allow_zero else "positive"
        raise WorkstreamRegistryError(f"{label} must be a {qualifier} integer")
    return raw


def _repo_file(
    raw: Any,
    *,
    label: str,
    within: str | None = None,
    max_bytes: int | None = None,
) -> str:
    value = _repo_prefix(raw, label=label)
    if within is not None and not (value == within or value.startswith(within.rstrip("/") + "/")):
        raise WorkstreamRegistryError(f"{label} must live inside {within}")
    path = ROOT / value
    if not path.is_file():
        raise WorkstreamRegistryError(f"missing {label}: {value}")
    if max_bytes is not None and path.stat().st_size > max_bytes:
        raise WorkstreamRegistryError(f"{label} exceeds {max_bytes} bytes: {value}")
    return value


def _prefixes_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _is_global_control_prefix(path: str) -> bool:
    return any(_prefixes_overlap(path, protected) for protected in GLOBAL_CONTROL_PREFIXES)


def _current_baseline_id() -> str:
    pointer = _load(BASELINE_POINTER_PATH)
    baseline = pointer.get("current_baseline")
    if not isinstance(baseline, str) or not baseline.strip():
        raise WorkstreamRegistryError("baseline pointer has no current_baseline")
    return baseline


def _active_capability_ids() -> set[str]:
    index = _load(CAPABILITY_INDEX_PATH)
    active = index.get("active")
    if not isinstance(active, list):
        raise WorkstreamRegistryError("capability active-index has no active list")
    ids = {item.get("id") for item in active if isinstance(item, dict)}
    if not all(isinstance(item, str) for item in ids):
        raise WorkstreamRegistryError("capability active-index contains invalid ids")
    return set(ids)


def _validate_lane_policy(
    manifest: dict[str, Any],
    *,
    contract: dict[str, Any],
    admission: dict[str, Any],
) -> None:
    lane = manifest.get("integration_lane")
    level = contract.get("change_level")
    disposition = admission.get("disposition")
    if lane not in LANES:
        raise WorkstreamRegistryError(f"unsupported integration_lane {lane!r}")
    if level not in CHANGE_LEVELS:
        raise WorkstreamRegistryError(f"unsupported workstream change_level {level!r}")
    if disposition not in DISPOSITIONS:
        raise WorkstreamRegistryError(f"unsupported workstream capability disposition {disposition!r}")

    if lane == "parallel":
        if level not in {"L1", "L2"}:
            raise WorkstreamRegistryError(
                "parallel workstreams are limited to L1/L2 Baseline-preserving changes"
            )
        if disposition not in {"reuse", "extend"}:
            raise WorkstreamRegistryError(
                "parallel workstreams may reuse/extend existing semantic owners only; "
                "replace/new ownership enters the global serial integration lane"
            )
    if level in {"L3", "L4"} and lane != "global_serial":
        raise WorkstreamRegistryError("L3/L4 work must use the global_serial integration lane")


def _validate_workstream_identity(path: Path, payload: dict[str, Any]) -> str:
    workstream_id = payload.get("workstream_id")
    if not isinstance(workstream_id, str) or not ID_PATTERN.fullmatch(workstream_id):
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has invalid workstream_id")
    if path.parent.name != workstream_id:
        raise WorkstreamRegistryError(
            f"workstream directory {path.parent.name!r} must match workstream_id {workstream_id!r}"
        )
    return workstream_id


def _validate_legacy_history(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Read v1 only as cold completed provenance.

    A historical manifest must not be re-admitted against today's Baseline or Capability
    index. Doing so would make old completed work fail whenever those live pointers evolve.
    """

    if manifest.get("schema_version") != LEGACY_WORKSTREAM_SCHEMA:
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has unsupported schema_version")
    workstream_id = _validate_workstream_identity(path, manifest)
    status = manifest.get("status")
    if status not in {"integrated", "closed"}:
        raise WorkstreamRegistryError(
            f"{workstream_id}: active v1 workstream.json is no longer supported; "
            "register reservation.json + cursor.json v2 before worker execution"
        )
    normalized = dict(manifest)
    normalized["_control_schema"] = "legacy-v1-history"
    normalized["dependencies"] = manifest.get("dependencies", [])
    normalized["exclusive_write_prefixes"] = manifest.get("exclusive_write_prefixes", [])
    return normalized


def _validate_cursor_with_typed_owner(cursor: dict[str, Any], *, workstream_id: str) -> dict[str, Any]:
    try:
        from pydantic import ValidationError

        from longcycle.application.workstream_continuity import WorkstreamCursorV2
    except ImportError as exc:  # pragma: no cover - packaging failure, not a schema fallback
        raise WorkstreamRegistryError(
            "WorkstreamCursorV2 is unavailable; the application model is the cursor schema owner"
        ) from exc

    try:
        validated = WorkstreamCursorV2.model_validate(cursor)
    except ValidationError as exc:
        raise WorkstreamRegistryError(f"{workstream_id}: invalid cursor.json: {exc}") from exc
    payload = validated.model_dump(mode="json")
    if not isinstance(payload, dict):  # defensive: Pydantic model_dump is contractually a dict
        raise WorkstreamRegistryError(f"{workstream_id}: WorkstreamCursorV2 returned invalid data")
    return payload


def _validate_cursor_refs(cursor: dict[str, Any], *, workstream_id: str) -> dict[str, list[str]]:
    parent_refs = _text_list(
        cursor.get("parent_refs"),
        label=f"{workstream_id} parent_refs",
        max_items=MAX_PARENT_REFS,
    )
    normalized: dict[str, list[str]] = {"parent_refs": parent_refs}
    total_refs = 0
    for field in CURSOR_REFERENCE_FIELDS:
        refs = _text_list(
            cursor.get(field),
            label=f"{workstream_id} {field}",
            allow_empty=True,
            max_items=MAX_CURSOR_REFS_PER_KIND,
        )
        max_bytes = (
            MAX_CONTROL_RECORD_BYTES
            if field in {"integration_request_refs", "receipt_refs"}
            else None
        )
        normalized[field] = [
            _repo_file(
                ref,
                label=f"{workstream_id} {field} reference",
                max_bytes=max_bytes,
            )
            for ref in refs
        ]
        total_refs += len(refs)
    if total_refs > MAX_CURSOR_REFS_TOTAL:
        raise WorkstreamRegistryError(
            f"{workstream_id}: cursor durable refs exceed the total limit of {MAX_CURSOR_REFS_TOTAL}"
        )
    return normalized


def _validate_active_reservation(
    path: Path,
    reservation: dict[str, Any],
    cursor: dict[str, Any],
) -> dict[str, Any]:
    workstream_id = reservation["workstream_id"]
    if reservation.get("kind") not in KINDS:
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported kind {reservation.get('kind')!r}")
    if reservation.get("integration_lane") not in LANES:
        raise WorkstreamRegistryError(
            f"{workstream_id}: unsupported integration_lane {reservation.get('integration_lane')!r}"
        )

    branch = _nonblank_text(reservation.get("branch"), label=f"{workstream_id} branch")
    if branch == "main":
        raise WorkstreamRegistryError(f"{workstream_id}: active workstream must use its own branch")
    base_main_sha = reservation.get("base_main_sha")
    if not isinstance(base_main_sha, str) or not SHA_PATTERN.fullmatch(base_main_sha):
        raise WorkstreamRegistryError(f"{workstream_id}: base_main_sha must be a lowercase 40-char SHA")
    if reservation.get("baseline") != _current_baseline_id():
        raise WorkstreamRegistryError(f"{workstream_id}: baseline does not match current Baseline pointer")

    intent_id = _nonblank_text(reservation.get("intent_id"), label=f"{workstream_id} intent_id")
    workstream_root_rel = path.parent.relative_to(ROOT).as_posix()
    contract_rel = _repo_file(
        reservation.get("change_contract_path"),
        label=f"{workstream_id} change contract",
        within=workstream_root_rel,
    )
    admission_rel = _repo_file(
        reservation.get("capability_admission_path"),
        label=f"{workstream_id} capability admission",
        within=workstream_root_rel,
    )
    contract = _load(ROOT / contract_rel)
    admission = _load(ROOT / admission_rel)
    if contract.get("schema_version") != "longcycle-change-contract/v1":
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported per-workstream Change Contract schema")
    if admission.get("schema_version") != "longcycle-capability-admission/v2":
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported per-workstream admission schema")
    if contract.get("intent_id") != intent_id or admission.get("intent_id") != intent_id:
        raise WorkstreamRegistryError(
            f"{workstream_id}: reservation, Change Contract and capability admission must share intent_id"
        )
    if contract.get("baseline") != reservation.get("baseline"):
        raise WorkstreamRegistryError(f"{workstream_id}: Change Contract baseline mismatch")

    targets = _text_list(
        reservation.get("target_capability_ids"),
        label=f"{workstream_id} target_capability_ids",
        allow_empty=True,
        max_items=MAX_CAPABILITY_OWNERS,
    )
    unknown = set(targets) - _active_capability_ids()
    if unknown:
        raise WorkstreamRegistryError(f"{workstream_id}: unknown/inactive capability ids {sorted(unknown)}")
    admission_targets = admission.get("target_capability_ids")
    if not isinstance(admission_targets, list) or set(admission_targets) != set(targets):
        raise WorkstreamRegistryError(
            f"{workstream_id}: reservation target_capability_ids must match per-workstream admission"
        )

    exclusive = [
        _repo_prefix(item, label=f"{workstream_id} exclusive_write_prefixes")
        for item in _text_list(
            reservation.get("exclusive_write_prefixes"),
            label=f"{workstream_id} exclusive_write_prefixes",
            allow_empty=True,
            max_items=MAX_WRITE_PREFIXES,
        )
    ]
    if reservation.get("integration_lane") == "parallel":
        forbidden = [item for item in exclusive if _is_global_control_prefix(item)]
        if forbidden:
            raise WorkstreamRegistryError(
                f"{workstream_id}: parallel workstream cannot own global control-plane paths {forbidden}; "
                "record a typed integration_request_ref instead"
            )

    dependencies = _text_list(
        reservation.get("dependencies"),
        label=f"{workstream_id} dependencies",
        allow_empty=True,
        max_items=MAX_DEPENDENCIES,
    )
    if workstream_id in dependencies:
        raise WorkstreamRegistryError(f"{workstream_id}: workstream cannot depend on itself")
    for field in ("parent_goal_ref", "goal", "done_when"):
        _nonblank_text(reservation.get(field), label=f"{workstream_id} {field}")

    _validate_lane_policy(reservation, contract=contract, admission=admission)
    ref_values = _validate_cursor_refs(cursor, workstream_id=workstream_id)

    normalized = dict(reservation)
    normalized.update(
        {
            "_control_schema": "reservation-cursor-v2",
            "status": cursor["progress_state"],
            "progress_state": cursor["progress_state"],
            "exclusive_write_prefixes": exclusive,
            "dependencies": dependencies,
            "target_capability_ids": targets,
            **ref_values,
        }
    )
    return normalized


def _validate_v2_workstream(path: Path, reservation: dict[str, Any]) -> dict[str, Any]:
    if reservation.get("schema_version") != RESERVATION_SCHEMA:
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has unsupported schema_version")
    workstream_id = _validate_workstream_identity(path, reservation)
    missing = sorted(RESERVATION_FIELD_SET - set(reservation))
    unknown = sorted(set(reservation) - RESERVATION_FIELD_SET)
    if missing or unknown:
        raise WorkstreamRegistryError(
            f"{workstream_id}: reservation.json field mismatch; missing={missing} unknown={unknown}"
        )
    lifecycle_state = reservation.get("lifecycle_state")
    if lifecycle_state not in LIFECYCLE_STATES:
        raise WorkstreamRegistryError(
            f"{workstream_id}: lifecycle_state must be one of {sorted(LIFECYCLE_STATES)}"
        )
    revision = _positive_int(
        reservation.get("reservation_revision"),
        label=f"{workstream_id} reservation_revision",
    )
    epoch = _positive_int(
        reservation.get("assignment_epoch"),
        label=f"{workstream_id} assignment_epoch",
    )

    workstream_root_rel = path.parent.relative_to(ROOT).as_posix()
    cursor_rel = _repo_file(
        reservation.get("cursor_path"),
        label=f"{workstream_id} cursor_path",
        within=workstream_root_rel,
    )
    expected_cursor_rel = f"{workstream_root_rel}/cursor.json"
    if cursor_rel != expected_cursor_rel:
        raise WorkstreamRegistryError(
            f"{workstream_id}: cursor_path must be exactly {expected_cursor_rel}"
        )
    cursor_path = ROOT / cursor_rel
    cursor_raw = _load(
        cursor_path,
        max_bytes=MAX_CURSOR_BYTES,
        label=f"{workstream_id} cursor.json",
    )
    forbidden = sorted(CURSOR_FORBIDDEN_RESERVATION_FIELDS.intersection(cursor_raw))
    if forbidden:
        raise WorkstreamRegistryError(
            f"{workstream_id}: cursor may not shadow main-owned reservation fields {forbidden}"
        )
    cursor = _validate_cursor_with_typed_owner(cursor_raw, workstream_id=workstream_id)
    expected_identity = {
        "schema_version": CURSOR_SCHEMA,
        "workstream_id": workstream_id,
        "branch": reservation.get("branch"),
        "reservation_revision": revision,
        "assignment_epoch": epoch,
    }
    mismatched = [field for field, expected in expected_identity.items() if cursor.get(field) != expected]
    if mismatched:
        raise WorkstreamRegistryError(
            f"{workstream_id}: cursor reservation identity/fence mismatch in {sorted(mismatched)}"
        )

    if lifecycle_state != "active":
        # Completed v2 records, like legacy v1 records, are cold provenance. Validate only
        # their immutable identity/fence; do not re-admit them against future live owners.
        normalized = dict(reservation)
        normalized.update(
            {
                "_control_schema": "reservation-cursor-v2-history",
                "status": lifecycle_state,
                "progress_state": cursor["progress_state"],
                "dependencies": reservation.get("dependencies", []),
                "exclusive_write_prefixes": reservation.get("exclusive_write_prefixes", []),
            }
        )
        return normalized

    return _validate_active_reservation(path, reservation, cursor)


def _validate_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compatibility dispatch retained for callers that validate one control file."""

    schema = manifest.get("schema_version")
    if schema == LEGACY_WORKSTREAM_SCHEMA:
        return _validate_legacy_history(path, manifest)
    if schema == RESERVATION_SCHEMA:
        return _validate_v2_workstream(path, manifest)
    raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has unsupported schema_version")


def load_workstreams() -> list[tuple[Path, dict[str, Any]]]:
    WORKSTREAM_ROOT.mkdir(parents=True, exist_ok=True)
    loaded: list[tuple[Path, dict[str, Any]]] = []
    ids: set[str] = set()
    orphan_cursors = [
        path
        for path in sorted(WORKSTREAM_ROOT.glob("*/cursor.json"))
        if not (path.parent / "reservation.json").is_file()
    ]
    if orphan_cursors:
        paths = [path.relative_to(ROOT).as_posix() for path in orphan_cursors]
        raise WorkstreamRegistryError(
            f"orphan v2 cursor files have no main-owned reservation.json: {paths}"
        )
    control_paths = [
        *sorted(WORKSTREAM_ROOT.glob("*/reservation.json")),
        *sorted(WORKSTREAM_ROOT.glob("*/workstream.json")),
    ]
    for path in control_paths:
        sibling_name = "workstream.json" if path.name == "reservation.json" else "reservation.json"
        if (path.parent / sibling_name).is_file():
            raise WorkstreamRegistryError(
                f"{path.parent.relative_to(ROOT)} contains both v1 and v2 control files"
            )
        max_bytes = MAX_RESERVATION_BYTES if path.name == "reservation.json" else None
        manifest = _validate_manifest(path, _load(path, max_bytes=max_bytes))
        if manifest["workstream_id"] in ids:
            raise WorkstreamRegistryError(f"duplicate workstream id {manifest['workstream_id']}")
        ids.add(manifest["workstream_id"])
        loaded.append((path, manifest))
    _validate_concurrency([manifest for _, manifest in loaded])
    _validate_dependencies([manifest for _, manifest in loaded])
    return loaded


def _validate_concurrency(workstreams: list[dict[str, Any]]) -> None:
    active = [item for item in workstreams if item.get("status") in ACTIVE_STATUSES]
    if len(active) > MAX_ACTIVE_WORKSTREAMS:
        raise WorkstreamRegistryError(
            f"active workstreams exceed the limit of {MAX_ACTIVE_WORKSTREAMS}"
        )
    branches: dict[str, str] = {}
    serial: list[str] = []
    for item in active:
        branch = item["branch"]
        previous = branches.get(branch)
        if previous is not None:
            raise WorkstreamRegistryError(
                f"active workstreams {previous} and {item['workstream_id']} share branch {branch!r}"
            )
        branches[branch] = item["workstream_id"]
        if item["integration_lane"] == "global_serial":
            serial.append(item["workstream_id"])
    if len(serial) > 1:
        raise WorkstreamRegistryError(
            f"only one active global_serial workstream is allowed; found {serial}"
        )

    parallel = [item for item in active if item["integration_lane"] == "parallel"]
    for index, left in enumerate(parallel):
        for right in parallel[index + 1 :]:
            for left_prefix in left["exclusive_write_prefixes"]:
                for right_prefix in right["exclusive_write_prefixes"]:
                    if _prefixes_overlap(left_prefix, right_prefix):
                        raise WorkstreamRegistryError(
                            "parallel workstream write-scope collision: "
                            f"{left['workstream_id']}:{left_prefix} overlaps "
                            f"{right['workstream_id']}:{right_prefix}"
                        )


def _validate_dependencies(workstreams: list[dict[str, Any]]) -> None:
    by_id = {item["workstream_id"]: item for item in workstreams}
    active = [item for item in workstreams if item.get("status") in ACTIVE_STATUSES]
    active_ids = {item["workstream_id"] for item in active}

    for item in active:
        workstream_id = item["workstream_id"]
        for dependency in item["dependencies"]:
            if dependency not in by_id:
                raise WorkstreamRegistryError(
                    f"{workstream_id}: dependency {dependency!r} has no registered workstream"
                )
        if item.get("status") == "ready_for_integration":
            unfinished = [
                dependency
                for dependency in item["dependencies"]
                if by_id[dependency].get("status") not in {"integrated", "closed"}
            ]
            if unfinished:
                raise WorkstreamRegistryError(
                    f"{workstream_id}: ready_for_integration has unfinished dependencies "
                    f"{sorted(unfinished)}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(workstream_id: str, trail: list[str]) -> None:
        if workstream_id in visiting:
            cycle_start = trail.index(workstream_id) if workstream_id in trail else 0
            cycle = [*trail[cycle_start:], workstream_id]
            raise WorkstreamRegistryError(
                "active workstream dependency cycle: " + " -> ".join(cycle)
            )
        if workstream_id in visited:
            return
        visiting.add(workstream_id)
        for dependency in by_id[workstream_id].get("dependencies", []):
            if dependency in active_ids:
                visit(dependency, [*trail, workstream_id])
        visiting.remove(workstream_id)
        visited.add(workstream_id)

    for workstream_id in sorted(active_ids):
        visit(workstream_id, [])


def build_index(workstreams: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    active: list[dict[str, Any]] = []
    for path, manifest in workstreams:
        if manifest["status"] not in ACTIVE_STATUSES:
            continue
        active.append(
            {
                "workstream_id": manifest["workstream_id"],
                "kind": manifest["kind"],
                "integration_lane": manifest["integration_lane"],
                "branch": manifest["branch"],
                "reservation_revision": manifest["reservation_revision"],
                "assignment_epoch": manifest["assignment_epoch"],
                "reservation_path": path.relative_to(ROOT).as_posix(),
                "cursor_path": manifest["cursor_path"],
                "dependencies": manifest["dependencies"],
            }
        )
    active.sort(key=lambda item: item["workstream_id"])
    index = {
        "schema_version": INDEX_SCHEMA,
        "policy": (
            "Global mission/Baseline/semantic ownership remain single control planes. "
            "Parallel L1/L2 workstreams own disjoint branch/path scopes and carry local cursors/contracts; "
            "shared control-plane changes and L3/L4 work enter one global serial integration lane."
        ),
        "active": active,
    }
    encoded_size = len(_canonical_json(index).encode("utf-8"))
    if encoded_size > MAX_INDEX_BYTES:
        raise WorkstreamRegistryError(
            f"workstream active-index would exceed {MAX_INDEX_BYTES} bytes; "
            "close/archive workstreams or reduce routing metadata"
        )
    return index


def validate() -> None:
    loaded = load_workstreams()
    print(
        "WORKSTREAM_REGISTRY_VALIDATE_PASS "
        f"declared={len(loaded)} active={sum(item['status'] in ACTIVE_STATUSES for _, item in loaded)}"
    )


def rebuild_index() -> None:
    index = build_index(load_workstreams())
    INDEX_PATH.write_text(_canonical_json(index), encoding="utf-8")
    print(f"WORKSTREAM_INDEX_WRITTEN active={len(index['active'])}")


def audit() -> None:
    expected = build_index(load_workstreams())
    if not INDEX_PATH.is_file():
        raise WorkstreamRegistryError(
            "missing .longcycle/workstreams/active-index.json; run "
            "scripts/workstream_registry.py rebuild-index"
        )
    actual = _load(INDEX_PATH)
    if actual != expected:
        raise WorkstreamRegistryError(
            "workstream active-index is stale; workstream manifests are canonical. "
            "The integration/coordinator lane must run: python scripts/workstream_registry.py rebuild-index"
        )
    print(f"WORKSTREAM_REGISTRY_AUDIT_PASS active={len(expected['active'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Longcycle parallel workstream registry")
    parser.add_argument("command", choices=("validate", "audit", "rebuild-index"))
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate()
        elif args.command == "audit":
            audit()
        else:
            rebuild_index()
    except WorkstreamRegistryError as exc:
        print(f"WORKSTREAM_REGISTRY_ERROR: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
