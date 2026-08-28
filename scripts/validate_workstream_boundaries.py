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
RESERVATION_FIELDS = (
    "workstream_id",
    "kind",
    "branch",
    "baseline",
    "integration_lane",
    "exclusive_write_prefixes",
    "target_capability_ids",
    "dependencies",
)
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
    for field in RESERVATION_FIELDS:
        current_value = _normalized_reservation_value(field, current.get(field))
        reserved_value = _normalized_reservation_value(field, reserved.get(field))
        if current_value != reserved_value:
            raise WorkstreamBoundaryError(
                f"worker cannot change reserved field {field!r} in the same implementation change; "
                "update the main/integration reservation first"
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
    allowed_prefixes = [*prefixes, workstream_control_root]
    violations = [
        path
        for path in changed_paths
        if not any(_path_within(path, prefix) for prefix in allowed_prefixes)
    ]
    if violations:
        raise WorkstreamBoundaryError(
            f"{workstream_id}: actual branch diff escapes reserved write scope: {sorted(violations)}; "
            "record shared needs as integration_requests or update the reservation on main first"
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
            cycle = trail[cycle_start:] + [workstream_id]
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


def validate_worker_branch(
    loaded: list[tuple[Path, dict[str, Any]]],
    *,
    base_ref: str,
    branch: str,
    head_ref: str = "HEAD",
) -> None:
    if not branch.startswith(WORKER_BRANCH_PREFIX):
        return

    matches = [
        (path, manifest)
        for path, manifest in loaded
        if manifest.get("status") in registry.ACTIVE_STATUSES and manifest.get("branch") == branch
    ]
    if len(matches) != 1:
        raise WorkstreamBoundaryError(
            f"worker branch {branch!r} must match exactly one active registered workstream; found {len(matches)}"
        )

    path, current = matches[0]
    manifest_path = path.relative_to(ROOT).as_posix()
    reserved = _reserved_manifest(base_ref, manifest_path)
    validate_reservation_unchanged(current=current, reserved=reserved)

    changed_paths = [
        line.strip()
        for line in _git("diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base_ref}...{head_ref}").splitlines()
        if line.strip()
    ]
    validate_changed_paths(
        workstream_id=current["workstream_id"],
        reserved=reserved,
        manifest_path=manifest_path,
        changed_paths=changed_paths,
    )


def validate(
    *,
    base_ref: str | None = None,
    branch: str | None = None,
    head_ref: str = "HEAD",
) -> None:
    loaded = registry.load_workstreams()
    manifests = [manifest for _, manifest in loaded]
    validate_dependency_graph(manifests)

    if base_ref is None and branch is None:
        return
    if not base_ref or not branch:
        raise WorkstreamBoundaryError("--base-ref and --branch must be supplied together")
    validate_worker_branch(loaded, base_ref=base_ref, branch=branch, head_ref=head_ref)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate workstream dependency topology and reserved worker write boundaries."
    )
    parser.add_argument("--base-ref", help="Integration/base ref whose registered reservation is authoritative.")
    parser.add_argument("--branch", help="Actual worker branch name, for example workstream/banking-domain-v1.")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used to compute the actual changed paths.")
    args = parser.parse_args()

    try:
        validate(base_ref=args.base_ref, branch=args.branch, head_ref=args.head_ref)
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
