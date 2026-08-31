from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_workstream_boundaries as boundaries  # noqa: E402


def _manifest(
    workstream_id: str,
    *,
    status: str = "in_progress",
    lane: str = "parallel",
    branch: str | None = None,
    dependencies: list[str] | None = None,
    prefixes: list[str] | None = None,
) -> dict[str, object]:
    lifecycle_state = status if status in {"integrated", "closed"} else "active"
    root = f".longcycle/workstreams/{workstream_id}"
    return {
        "schema_version": boundaries.registry.RESERVATION_SCHEMA,
        "workstream_id": workstream_id,
        "kind": "industry",
        "status": status,
        "lifecycle_state": lifecycle_state,
        "integration_lane": lane,
        "branch": branch or f"workstream/{workstream_id}",
        "base_main_sha": "a" * 40,
        "baseline": "architecture-v1",
        "intent_id": f"{workstream_id.upper()}-001",
        "change_contract_path": f"{root}/change-contract.json",
        "capability_admission_path": f"{root}/capability-admission.json",
        "parent_goal_ref": ".longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
        "goal": f"Deliver the bounded {workstream_id} milestone.",
        "done_when": f"The {workstream_id} acceptance checks pass.",
        "exclusive_write_prefixes": prefixes or [f"domain_packs/{workstream_id}"],
        "target_capability_ids": ["CAP-0002"],
        "dependencies": dependencies or [],
        "reservation_revision": 1,
        "assignment_epoch": 1,
        "cursor_path": f"{root}/cursor.json",
    }


def test_current_workstream_boundary_graph_is_valid() -> None:
    boundaries.validate()


def test_parallel_branch_name_is_deterministic() -> None:
    manifest = _manifest("banking-domain", branch="feature/banking")
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="must be exactly"):
        boundaries.validate_dependency_graph([manifest])


def test_worker_branch_cannot_target_main_directly() -> None:
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="may not merge directly to main"):
        boundaries.validate_worker_merge_target(
            branch="workstream/banking-domain",
            base_branch="main",
        )
    boundaries.validate_worker_merge_target(
        branch="workstream/banking-domain",
        base_branch="integration/batch-001",
    )


def test_active_dependency_must_be_registered() -> None:
    banking = _manifest("banking-domain", dependencies=["shared-scenario-engine"])
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="no registered workstream"):
        boundaries.validate_dependency_graph([banking])


def test_active_dependency_cycle_is_rejected() -> None:
    banking = _manifest("banking-domain", dependencies=["shipping-domain"])
    shipping = _manifest("shipping-domain", dependencies=["banking-domain"])
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="dependency cycle"):
        boundaries.validate_dependency_graph([banking, shipping])


def test_ready_for_integration_requires_dependencies_to_be_integrated() -> None:
    platform = _manifest("shared-scenario-engine", status="active")
    banking = _manifest(
        "banking-domain",
        status="ready_for_integration",
        dependencies=["shared-scenario-engine"],
    )
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="integrated/closed"):
        boundaries.validate_dependency_graph([platform, banking])


def test_ready_for_integration_accepts_integrated_dependency() -> None:
    platform = _manifest("shared-scenario-engine", status="integrated")
    banking = _manifest(
        "banking-domain",
        status="ready_for_integration",
        dependencies=["shared-scenario-engine"],
    )
    boundaries.validate_dependency_graph([platform, banking])


def test_worker_cannot_expand_reserved_write_scope_in_same_change() -> None:
    reserved = _manifest("banking-domain", prefixes=["domain_packs/banking"])
    current = dict(reserved)
    current["exclusive_write_prefixes"] = ["domain_packs/banking", "domain_packs/shipping"]
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="reserved field"):
        boundaries.validate_reservation_unchanged(current=current, reserved=reserved)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("schema_version", "longcycle-workstream-reservation/v3"),
        ("workstream_id", "shipping-domain"),
        ("kind", "product"),
        ("lifecycle_state", "closed"),
        ("branch", "workstream/shipping-domain"),
        ("base_main_sha", "b" * 40),
        ("baseline", "architecture-v2"),
        ("change_contract_path", ".longcycle/workstreams/other/change-contract.json"),
        (
            "capability_admission_path",
            ".longcycle/workstreams/other/capability-admission.json",
        ),
        ("integration_lane", "global_serial"),
        ("reservation_revision", 2),
        ("assignment_epoch", 2),
        ("goal", "A worker-issued replacement goal."),
        ("done_when", "A worker-issued weaker acceptance condition."),
        ("intent_id", "WORKER-REDEFINED-INTENT"),
        ("parent_goal_ref", "worker-local-goal"),
        ("exclusive_write_prefixes", ["domain_packs/shipping"]),
        ("target_capability_ids", ["CAP-0005"]),
        ("dependencies", ["worker-created-dependency"]),
        ("cursor_path", ".longcycle/workstreams/other/cursor.json"),
    ],
)
def test_every_main_owned_reservation_dimension_is_fenced(
    field: str,
    replacement: object,
) -> None:
    reserved = _manifest("banking-domain")
    current = dict(reserved)
    current[field] = replacement

    with pytest.raises(boundaries.WorkstreamBoundaryError, match=field):
        boundaries.validate_reservation_unchanged(current=current, reserved=reserved)


def test_worker_diff_is_limited_to_reserved_scope_and_own_control_dir() -> None:
    reserved = _manifest(
        "banking-domain",
        prefixes=["domain_packs/banking", "tests/banking"],
    )
    boundaries.validate_changed_paths(
        workstream_id="banking-domain",
        reserved=reserved,
        manifest_path=".longcycle/workstreams/banking-domain/reservation.json",
        changed_paths=[
            "domain_packs/banking/metrics.json",
            "tests/banking/test_metrics.py",
            ".longcycle/workstreams/banking-domain/cursor.json",
            ".longcycle/workstreams/banking-domain/requests/shared-export.json",
            ".longcycle/workstreams/banking-domain/receipts/focused-tests.json",
        ],
    )


@pytest.mark.parametrize(
    "path",
    [
        ".longcycle/workstreams/banking-domain/reservation.json",
        ".longcycle/workstreams/banking-domain/change-contract.json",
        ".longcycle/workstreams/banking-domain/capability-admission.json",
    ],
)
def test_worker_cannot_change_main_owned_workstream_authority(path: str) -> None:
    reserved = _manifest("banking-domain", prefixes=["domain_packs/banking"])

    with pytest.raises(boundaries.WorkstreamBoundaryError, match="main-owned control"):
        boundaries.validate_changed_paths(
            workstream_id="banking-domain",
            reserved=reserved,
            manifest_path=".longcycle/workstreams/banking-domain/reservation.json",
            changed_paths=[path],
        )


def test_worker_diff_cannot_escape_reserved_scope() -> None:
    reserved = _manifest("banking-domain", prefixes=["domain_packs/banking"])
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="escapes reserved write scope"):
        boundaries.validate_changed_paths(
            workstream_id="banking-domain",
            reserved=reserved,
            manifest_path=".longcycle/workstreams/banking-domain/reservation.json",
            changed_paths=["domain_packs/shipping/metrics.json"],
        )
