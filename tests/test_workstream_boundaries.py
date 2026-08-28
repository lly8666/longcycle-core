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
    status: str = "active",
    lane: str = "parallel",
    branch: str | None = None,
    dependencies: list[str] | None = None,
    prefixes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "workstream_id": workstream_id,
        "kind": "industry",
        "status": status,
        "integration_lane": lane,
        "branch": branch or f"workstream/{workstream_id}",
        "baseline": "architecture-v1",
        "exclusive_write_prefixes": prefixes or [f"domain_packs/{workstream_id}"],
        "target_capability_ids": ["CAP-0002"],
        "dependencies": dependencies or [],
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


def test_worker_diff_is_limited_to_reserved_scope_and_own_control_dir() -> None:
    reserved = _manifest(
        "banking-domain",
        prefixes=["domain_packs/banking", "tests/banking"],
    )
    boundaries.validate_changed_paths(
        workstream_id="banking-domain",
        reserved=reserved,
        manifest_path=".longcycle/workstreams/banking-domain/workstream.json",
        changed_paths=[
            "domain_packs/banking/metrics.json",
            "tests/banking/test_metrics.py",
            ".longcycle/workstreams/banking-domain/workstream.json",
            ".longcycle/workstreams/banking-domain/change-contract.json",
        ],
    )


def test_worker_diff_cannot_escape_reserved_scope() -> None:
    reserved = _manifest("banking-domain", prefixes=["domain_packs/banking"])
    with pytest.raises(boundaries.WorkstreamBoundaryError, match="escapes reserved write scope"):
        boundaries.validate_changed_paths(
            workstream_id="banking-domain",
            reserved=reserved,
            manifest_path=".longcycle/workstreams/banking-domain/workstream.json",
            changed_paths=["domain_packs/shipping/metrics.json"],
        )
