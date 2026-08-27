from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSTREAM_ROOT = ROOT / ".longcycle" / "workstreams"
INDEX_PATH = WORKSTREAM_ROOT / "active-index.json"
BASELINE_POINTER_PATH = ROOT / ".longcycle" / "baseline" / "current.json"
CAPABILITY_INDEX_PATH = ROOT / ".longcycle" / "capabilities" / "active-index.json"

WORKSTREAM_SCHEMA = "longcycle-workstream/v1"
INDEX_SCHEMA = "longcycle-workstream-index/v1"
ACTIVE_STATUSES = {"planned", "active", "blocked", "ready_for_integration"}
ALL_STATUSES = ACTIVE_STATUSES | {"integrated", "closed"}
KINDS = {"industry", "product", "platform", "research", "governance"}
LANES = {"parallel", "global_serial"}
CAPABILITY_CLASSES = {"high_capability_reasoning", "bounded_execution"}
CHANGE_LEVELS = {"L1", "L2", "L3", "L4"}
DISPOSITIONS = {"reuse", "extend", "replace", "new"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

# A parallel workstream may read these paths but may not claim autonomous write ownership.
# If it needs a change here, it records an integration_request and the mainline integration
# lane performs the shared-control-plane update after parallel work converges.
GLOBAL_CONTROL_PREFIXES = (
    ".longcycle/baseline",
    ".longcycle/handoff/current.json",
    ".longcycle/capabilities/current-admission.json",
    ".longcycle/capabilities/cards",
    ".longcycle/capabilities/active-index.json",
    ".longcycle/change-contract/current.json",
    "ARCHITECTURE_BASELINE_V1.md",
    "STRATEGIC_COMPASS.md",
    "METHODOLOGY_CORE.md",
)


class WorkstreamRegistryError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkstreamRegistryError(f"cannot read valid JSON {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} must contain an object")
    return payload


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _repo_prefix(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise WorkstreamRegistryError(f"{label} must be a nonblank repository-relative path prefix")
    value = raw.strip().rstrip("/")
    if value.startswith(("/", "../")) or "*" in value:
        raise WorkstreamRegistryError(f"{label} must be a literal repository-relative prefix: {raw}")
    resolved = (ROOT / value).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise WorkstreamRegistryError(f"{label} escapes repository: {raw}") from exc
    return value


def _text_list(raw: Any, *, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(raw, list) or (not raw and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise WorkstreamRegistryError(f"{label} must be {qualifier}")
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise WorkstreamRegistryError(f"{label} contains blank/non-text data")
        values.append(item.strip())
    if len(values) != len(set(values)):
        raise WorkstreamRegistryError(f"{label} contains duplicates")
    return values


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
            raise WorkstreamRegistryError("parallel workstreams are limited to L1/L2 Baseline-preserving changes")
        if disposition not in {"reuse", "extend"}:
            raise WorkstreamRegistryError(
                "parallel workstreams may reuse/extend existing semantic owners only; "
                "replace/new ownership enters the global serial integration lane"
            )
    if level in {"L3", "L4"} and lane != "global_serial":
        raise WorkstreamRegistryError("L3/L4 work must use the global_serial integration lane")


def _validate_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != WORKSTREAM_SCHEMA:
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has unsupported schema_version")

    workstream_id = manifest.get("workstream_id")
    if not isinstance(workstream_id, str) or not ID_PATTERN.fullmatch(workstream_id):
        raise WorkstreamRegistryError(f"{path.relative_to(ROOT)} has invalid workstream_id")
    if path.parent.name != workstream_id:
        raise WorkstreamRegistryError(
            f"workstream directory {path.parent.name!r} must match workstream_id {workstream_id!r}"
        )
    if manifest.get("kind") not in KINDS:
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported kind {manifest.get('kind')!r}")
    if manifest.get("status") not in ALL_STATUSES:
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported status {manifest.get('status')!r}")
    if manifest.get("required_capability") not in CAPABILITY_CLASSES:
        raise WorkstreamRegistryError(f"{workstream_id}: invalid required_capability")

    branch = manifest.get("branch")
    if not isinstance(branch, str) or not branch.strip():
        raise WorkstreamRegistryError(f"{workstream_id}: branch must be nonblank")
    if manifest.get("status") in ACTIVE_STATUSES and branch == "main":
        raise WorkstreamRegistryError(f"{workstream_id}: active workstream must use its own branch")

    base_main_sha = manifest.get("base_main_sha")
    if not isinstance(base_main_sha, str) or not SHA_PATTERN.fullmatch(base_main_sha):
        raise WorkstreamRegistryError(f"{workstream_id}: base_main_sha must be a lowercase 40-char SHA")
    if manifest.get("baseline") != _current_baseline_id():
        raise WorkstreamRegistryError(f"{workstream_id}: baseline does not match current Baseline pointer")

    intent_id = manifest.get("intent_id")
    if not isinstance(intent_id, str) or not intent_id.strip():
        raise WorkstreamRegistryError(f"{workstream_id}: intent_id must be nonblank")

    contract_rel = _repo_prefix(manifest.get("change_contract_path"), label=f"{workstream_id} change_contract_path")
    admission_rel = _repo_prefix(
        manifest.get("capability_admission_path"),
        label=f"{workstream_id} capability_admission_path",
    )
    workstream_root_rel = path.parent.relative_to(ROOT).as_posix()
    for rel, label in ((contract_rel, "change contract"), (admission_rel, "capability admission")):
        if not rel.startswith(workstream_root_rel + "/"):
            raise WorkstreamRegistryError(
                f"{workstream_id}: per-workstream {label} must live inside {workstream_root_rel}"
            )
        if not (ROOT / rel).is_file():
            raise WorkstreamRegistryError(f"{workstream_id}: missing {label}: {rel}")

    contract = _load(ROOT / contract_rel)
    admission = _load(ROOT / admission_rel)
    if contract.get("schema_version") != "longcycle-change-contract/v1":
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported per-workstream Change Contract schema")
    if admission.get("schema_version") != "longcycle-capability-admission/v2":
        raise WorkstreamRegistryError(f"{workstream_id}: unsupported per-workstream admission schema")
    if contract.get("intent_id") != intent_id or admission.get("intent_id") != intent_id:
        raise WorkstreamRegistryError(
            f"{workstream_id}: manifest, Change Contract and capability admission must share intent_id"
        )
    if contract.get("baseline") != manifest.get("baseline"):
        raise WorkstreamRegistryError(f"{workstream_id}: Change Contract baseline mismatch")

    targets = _text_list(
        manifest.get("target_capability_ids"),
        label=f"{workstream_id} target_capability_ids",
        allow_empty=True,
    )
    active_capabilities = _active_capability_ids()
    unknown = set(targets) - active_capabilities
    if unknown:
        raise WorkstreamRegistryError(f"{workstream_id}: unknown/inactive capability ids {sorted(unknown)}")
    admission_targets = admission.get("target_capability_ids")
    if not isinstance(admission_targets, list) or set(admission_targets) != set(targets):
        raise WorkstreamRegistryError(
            f"{workstream_id}: manifest target_capability_ids must match per-workstream admission"
        )

    exclusive = [
        _repo_prefix(item, label=f"{workstream_id} exclusive_write_prefixes")
        for item in _text_list(
            manifest.get("exclusive_write_prefixes"),
            label=f"{workstream_id} exclusive_write_prefixes",
            allow_empty=True,
        )
    ]
    if manifest.get("integration_lane") == "parallel":
        forbidden = [item for item in exclusive if _is_global_control_prefix(item)]
        if forbidden:
            raise WorkstreamRegistryError(
                f"{workstream_id}: parallel workstream cannot own global control-plane paths {forbidden}; "
                "record them as integration_requests instead"
            )

    integration_requests = [
        _repo_prefix(item, label=f"{workstream_id} integration_requests")
        for item in _text_list(
            manifest.get("integration_requests"),
            label=f"{workstream_id} integration_requests",
            allow_empty=True,
        )
    ]
    dependencies = _text_list(
        manifest.get("dependencies"),
        label=f"{workstream_id} dependencies",
        allow_empty=True,
    )
    if workstream_id in dependencies:
        raise WorkstreamRegistryError(f"{workstream_id}: workstream cannot depend on itself")

    for field in ("parent_goal_ref", "goal", "done_when", "next_atomic_action"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise WorkstreamRegistryError(f"{workstream_id}: {field} must be nonblank")

    _validate_lane_policy(manifest, contract=contract, admission=admission)

    normalized = dict(manifest)
    normalized["exclusive_write_prefixes"] = exclusive
    normalized["integration_requests"] = integration_requests
    normalized["dependencies"] = dependencies
    normalized["target_capability_ids"] = targets
    return normalized


def load_workstreams() -> list[tuple[Path, dict[str, Any]]]:
    WORKSTREAM_ROOT.mkdir(parents=True, exist_ok=True)
    loaded: list[tuple[Path, dict[str, Any]]] = []
    ids: set[str] = set()
    for path in sorted(WORKSTREAM_ROOT.glob("*/workstream.json")):
        manifest = _validate_manifest(path, _load(path))
        if manifest["workstream_id"] in ids:
            raise WorkstreamRegistryError(f"duplicate workstream id {manifest['workstream_id']}")
        ids.add(manifest["workstream_id"])
        loaded.append((path, manifest))
    _validate_concurrency([manifest for _, manifest in loaded])
    return loaded


def _validate_concurrency(workstreams: list[dict[str, Any]]) -> None:
    active = [item for item in workstreams if item.get("status") in ACTIVE_STATUSES]
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


def build_index(workstreams: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    active = []
    for path, manifest in workstreams:
        if manifest["status"] not in ACTIVE_STATUSES:
            continue
        active.append(
            {
                "workstream_id": manifest["workstream_id"],
                "kind": manifest["kind"],
                "status": manifest["status"],
                "integration_lane": manifest["integration_lane"],
                "branch": manifest["branch"],
                "base_main_sha": manifest["base_main_sha"],
                "baseline": manifest["baseline"],
                "intent_id": manifest["intent_id"],
                "target_capability_ids": manifest["target_capability_ids"],
                "manifest_path": path.relative_to(ROOT).as_posix(),
                "exclusive_write_prefixes": manifest["exclusive_write_prefixes"],
                "integration_requests": manifest["integration_requests"],
                "dependencies": manifest["dependencies"],
            }
        )
    active.sort(key=lambda item: item["workstream_id"])
    return {
        "schema_version": INDEX_SCHEMA,
        "policy": (
            "Global mission/Baseline/semantic ownership remain single control planes. "
            "Parallel L1/L2 workstreams own disjoint branch/path scopes and carry local cursors/contracts; "
            "shared control-plane changes and L3/L4 work enter one global serial integration lane."
        ),
        "active": active,
    }


def rebuild_index() -> None:
    index = build_index(load_workstreams())
    INDEX_PATH.write_text(_canonical_json(index), encoding="utf-8")
    print(f"WORKSTREAM_INDEX_WRITTEN active={len(index['active'])}")


def audit() -> None:
    expected = build_index(load_workstreams())
    if not INDEX_PATH.is_file():
        raise WorkstreamRegistryError(
            "missing .longcycle/workstreams/active-index.json; run scripts/workstream_registry.py rebuild-index"
        )
    actual = _load(INDEX_PATH)
    if actual != expected:
        raise WorkstreamRegistryError(
            "workstream active-index is stale; workstream manifests are canonical. "
            "Run: python scripts/workstream_registry.py rebuild-index"
        )
    print(f"WORKSTREAM_REGISTRY_AUDIT_PASS active={len(expected['active'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Longcycle parallel workstream registry")
    parser.add_argument("command", choices=("audit", "rebuild-index"))
    args = parser.parse_args()
    try:
        if args.command == "audit":
            audit()
        else:
            rebuild_index()
    except WorkstreamRegistryError as exc:
        print(f"WORKSTREAM_REGISTRY_ERROR: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
