from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import workstream_registry as registry

ROOT = Path(__file__).resolve().parents[1]
WORKER_BRANCH_PREFIX = "workstream/"
INTEGRATED_STATUSES = {"integrated", "closed"}
# Keep worker fencing on the registry-owned full reservation schema. The worker may
# advance cursor.json, but every reservation fact remains integration/main-owned.
RESERVATION_FIELDS = registry.RESERVATION_FIELDS
SET_LIKE_RESERVATION_FIELDS = {
    "exclusive_write_prefixes",
    "target_capability_ids",
    "dependencies",
}


class WorkstreamBoundaryError(ValueError):
    pass


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise WorkstreamBoundaryError(f"git {' '.join(args)}: {detail}")
    return completed.stdout


def _path_within(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def _normalized_reservation_value(field: str, value: Any) -> Any:
    if field in SET_LIKE_RESERVATION_FIELDS:
        if not isinstance(value, list):
            return value
        return sorted(value)
    return value


def validate_reservation_unchanged(
    *,
    current: dict[str, Any],
    reserved: dict[str, Any],
) -> None:
    """Legacy unit helper proving a worker cannot self-mutate reservation authority."""

    for field in RESERVATION_FIELDS:
        current_value = _normalized_reservation_value(field, current.get(field))
        reserved_value = _normalized_reservation_value(field, reserved.get(field))
        if current_value != reserved_value:
            raise WorkstreamBoundaryError(
                f"worker cannot change reserved field {field!r} in the same implementation change; "
                "update the main/integration reservation first"
            )


def validate_worker_merge_target(*, branch: str, base_branch: str | None) -> None:
    if branch.startswith(WORKER_BRANCH_PREFIX) and base_branch == "main":
        raise WorkstreamBoundaryError(
            "worker branches are producer branches and may not merge directly to main; "
            "route the ready work through the single global_serial integration lane"
        )


def validate_changed_paths(
    *,
    workstream_id: str,
    reserved: dict[str, Any],
    manifest_path: str,
    changed_paths: list[str],
) -> None:
    prefixes = reserved.get("exclusive_write_prefixes")
    if not isinstance(prefixes, list) or not all(isinstance(item, str) for item in prefixes):
        raise WorkstreamBoundaryError(
            f"{workstream_id}: reserved exclusive_write_prefixes must be a list of paths"
        )

    workstream_control_root = Path(manifest_path).parent.as_posix()
    main_owned_control_paths = {
        path
        for path in (
            manifest_path,
            reserved.get("change_contract_path"),
            reserved.get("capability_admission_path"),
        )
        if isinstance(path, str)
    }
    authority_changes = sorted(set(changed_paths).intersection(main_owned_control_paths))
    if authority_changes:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: worker diff changes main-owned control files {authority_changes}; "
            "the serial integration lane must revise reservation authority first"
        )

    allowed_prefixes = [*prefixes, workstream_control_root]
    violations = [
        path
        for path in changed_paths
        if not any(_path_within(path, prefix) for prefix in allowed_prefixes)
    ]
    if violations:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: actual branch diff escapes reserved write scope: {sorted(violations)}; "
            "record shared needs through integration_request_refs or update the reservation on main first"
        )


def validate_dependency_graph(workstreams: list[dict[str, Any]]) -> None:
    by_id = {item["workstream_id"]: item for item in workstreams}
    active = [item for item in workstreams if item.get("status") in registry.ACTIVE_STATUSES]

    for item in active:
        workstream_id = item["workstream_id"]
        if item.get("integration_lane") == "parallel":
            expected_branch = f"{WORKER_BRANCH_PREFIX}{workstream_id}"
            if item.get("branch") != expected_branch:
                raise WorkstreamBoundaryError(
                    f"{workstream_id}: parallel worker branch must be exactly {expected_branch!r}"
                )

        dependencies = item.get("dependencies")
        if not isinstance(dependencies, list):
            raise WorkstreamBoundaryError(f"{workstream_id}: dependencies must be a list")
        for dependency in dependencies:
            if dependency not in by_id:
                raise WorkstreamBoundaryError(
                    f"{workstream_id}: dependency {dependency!r} has no registered workstream manifest"
                )

        if item.get("status") == "ready_for_integration":
            unfinished = [
                dependency
                for dependency in dependencies
                if by_id[dependency].get("status") not in INTEGRATED_STATUSES
            ]
            if unfinished:
                raise WorkstreamBoundaryError(
                    f"{workstream_id}: ready_for_integration requires dependencies to be integrated/closed; "
                    f"unfinished={sorted(unfinished)}"
                )

    active_ids = {item["workstream_id"] for item in active}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(workstream_id: str, trail: list[str]) -> None:
        if workstream_id in visiting:
            cycle_start = trail.index(workstream_id) if workstream_id in trail else 0
            cycle = [*trail[cycle_start:], workstream_id]
            raise WorkstreamBoundaryError(
                "active workstream dependency cycle: " + " -> ".join(cycle)
            )
        if workstream_id in visited:
            return
        visiting.add(workstream_id)
        current = by_id[workstream_id]
        for dependency in current.get("dependencies", []):
            if dependency in active_ids:
                visit(dependency, [*trail, workstream_id])
        visiting.remove(workstream_id)
        visited.add(workstream_id)

    for workstream_id in sorted(active_ids):
        visit(workstream_id, [])


def _reserved_manifest(base_ref: str, manifest_path: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "show", f"{base_ref}:{manifest_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise WorkstreamBoundaryError(
            f"worker reservation {manifest_path} does not exist on {base_ref}; "
            "reserve the workstream on main/integration before implementation starts"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WorkstreamBoundaryError(
            f"reserved manifest {manifest_path} on {base_ref} is not valid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkstreamBoundaryError(
            f"reserved manifest {manifest_path} on {base_ref} must contain an object"
        )
    return payload


def _worker_cursor(workstream_id: str) -> dict[str, Any]:
    cursor_path = ROOT / ".longcycle" / "workstreams" / workstream_id / "cursor.json"
    try:
        payload = json.loads(cursor_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkstreamBoundaryError(
            f"worker cursor {cursor_path.relative_to(ROOT).as_posix()} is unavailable or invalid: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkstreamBoundaryError(
            f"worker cursor {cursor_path.relative_to(ROOT).as_posix()} must contain an object"
        )
    return payload


def validate_worker_acknowledges_reservation(
    *,
    workstream_id: str,
    branch: str,
    cursor: dict[str, Any],
    reserved: dict[str, Any],
) -> None:
    if reserved.get("lifecycle_state") != "active":
        raise WorkstreamBoundaryError(
            f"{workstream_id}: main reservation is not active: {reserved.get('lifecycle_state')!r}"
        )
    if reserved.get("workstream_id") != workstream_id or reserved.get("branch") != branch:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: refreshed main reservation identity does not authorize branch {branch!r}"
        )
    if cursor.get("workstream_id") != workstream_id or cursor.get("branch") != branch:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: worker cursor identity does not match branch {branch!r}"
        )

    main_revision = reserved.get("reservation_revision")
    cursor_revision = cursor.get("reservation_revision")
    if cursor_revision != main_revision:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: reservation revision acknowledgement pending; "
            f"main={main_revision!r} cursor={cursor_revision!r}. "
            "Refresh main and acknowledge the new reservation revision in cursor.json before substantive work."
        )

    main_epoch = reserved.get("assignment_epoch")
    cursor_epoch = cursor.get("assignment_epoch")
    if cursor_epoch != main_epoch:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: assignment fence mismatch; main={main_epoch!r} cursor={cursor_epoch!r}"
        )


def validate_worker_branch(
    *,
    base_ref: str,
    branch: str,
    base_branch: str | None = None,
    head_ref: str = "HEAD",
) -> None:
    if not branch.startswith(WORKER_BRANCH_PREFIX):
        return

    validate_worker_merge_target(branch=branch, base_branch=base_branch)
    workstream_id = branch.removeprefix(WORKER_BRANCH_PREFIX)
    manifest_path = f".longcycle/workstreams/{workstream_id}/reservation.json"
    reserved = _reserved_manifest(base_ref, manifest_path)
    cursor = _worker_cursor(workstream_id)
    validate_worker_acknowledges_reservation(
        workstream_id=workstream_id,
        branch=branch,
        cursor=cursor,
        reserved=reserved,
    )

    diff_output = _git(
        "diff",
        "--name-only",
        "--diff-filter=ACDMRTUXB",
        f"{base_ref}...{head_ref}",
    )
    changed_paths = [line.strip() for line in diff_output.splitlines() if line.strip()]
    validate_changed_paths(
        workstream_id=workstream_id,
        reserved=reserved,
        manifest_path=manifest_path,
        changed_paths=changed_paths,
    )


def validate(
    *,
    base_ref: str | None = None,
    branch: str | None = None,
    base_branch: str | None = None,
    head_ref: str = "HEAD",
) -> None:
    if base_ref is None and branch is None:
        loaded = registry.load_workstreams()
        validate_dependency_graph([manifest for _, manifest in loaded])
        return
    if not base_ref or not branch:
        raise WorkstreamBoundaryError("--base-ref and --branch must be supplied together")
    if branch.startswith(WORKER_BRANCH_PREFIX):
        validate_worker_branch(
            base_ref=base_ref,
            branch=branch,
            base_branch=base_branch,
            head_ref=head_ref,
        )
        return

    loaded = registry.load_workstreams()
    validate_dependency_graph([manifest for _, manifest in loaded])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate workstream dependency topology and reserved worker write boundaries."
    )
    parser.add_argument(
        "--base-ref",
        help="Integration/base ref whose registered reservation is authoritative.",
    )
    parser.add_argument(
        "--branch",
        help="Actual worker branch name, for example workstream/banking-domain-v1.",
    )
    parser.add_argument(
        "--base-branch",
        help="Logical PR base branch; worker branches may not target main directly.",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used to compute the actual changed paths.",
    )
    args = parser.parse_args()

    try:
        validate(
            base_ref=args.base_ref,
            branch=args.branch,
            base_branch=args.base_branch,
            head_ref=args.head_ref,
        )
    except (WorkstreamBoundaryError, registry.WorkstreamRegistryError) as exc:
        print(f"WORKSTREAM_BOUNDARY_FAIL {exc}")
        return 1

    if args.branch and args.branch.startswith(WORKER_BRANCH_PREFIX):
        print(f"WORKSTREAM_BOUNDARY_PASS branch={args.branch} base={args.base_ref}")
    else:
        print("WORKSTREAM_BOUNDARY_PASS dependency_graph=valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
