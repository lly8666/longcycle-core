from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workstream_registry.py"
SPEC = importlib.util.spec_from_file_location("workstream_registry", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
workstreams = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workstreams)


def _active(
    workstream_id: str,
    *,
    branch: str,
    lane: str = "parallel",
    prefixes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "workstream_id": workstream_id,
        "status": "active",
        "branch": branch,
        "integration_lane": lane,
        "exclusive_write_prefixes": prefixes or [],
    }


def test_current_workstream_registry_is_self_consistent() -> None:
    workstreams.audit()


def test_global_control_plane_paths_are_not_parallel_write_scopes() -> None:
    assert workstreams._is_global_control_prefix(".longcycle/handoff/current.json")
    assert workstreams._is_global_control_prefix(".longcycle/capabilities/cards/CAP-0005.json")
    assert workstreams._is_global_control_prefix(".longcycle/workstreams/active-index.json")
    assert workstreams._is_global_control_prefix("ARCHITECTURE_BASELINE_V1.md")
    assert workstreams._is_global_control_prefix("migrations/0040_example.sql")
    assert workstreams._is_global_control_prefix(".github/workflows/ci.yml")
    assert workstreams._is_global_control_prefix("pyproject.toml")
    assert not workstreams._is_global_control_prefix("research_data/memory/banking")


def test_parallel_lane_is_l1_l2_reuse_extend_only() -> None:
    workstreams._validate_lane_policy(
        {"integration_lane": "parallel"},
        contract={"change_level": "L2"},
        admission={"disposition": "extend"},
    )
    with pytest.raises(workstreams.WorkstreamRegistryError, match="L1/L2"):
        workstreams._validate_lane_policy(
            {"integration_lane": "parallel"},
            contract={"change_level": "L3"},
            admission={"disposition": "reuse"},
        )
    with pytest.raises(workstreams.WorkstreamRegistryError, match="reuse/extend"):
        workstreams._validate_lane_policy(
            {"integration_lane": "parallel"},
            contract={"change_level": "L2"},
            admission={"disposition": "new"},
        )


def test_parallel_write_scope_collision_is_rejected() -> None:
    left = _active(
        "banking-domain",
        branch="workstream/banking-domain",
        prefixes=["domain_packs/banking"],
    )
    right = _active(
        "banking-product",
        branch="workstream/banking-product",
        prefixes=["domain_packs/banking/metrics"],
    )
    with pytest.raises(workstreams.WorkstreamRegistryError, match="write-scope collision"):
        workstreams._validate_concurrency([left, right])


def test_disjoint_parallel_workstreams_are_allowed() -> None:
    banking = _active(
        "banking-domain",
        branch="workstream/banking-domain",
        prefixes=["domain_packs/banking"],
    )
    shipping = _active(
        "shipping-domain",
        branch="workstream/shipping-domain",
        prefixes=["domain_packs/shipping"],
    )
    workstreams._validate_concurrency([banking, shipping])


def test_global_serial_lane_has_single_writer() -> None:
    first = _active(
        "architecture-change-a",
        branch="architecture/change-a",
        lane="global_serial",
    )
    second = _active(
        "architecture-change-b",
        branch="architecture/change-b",
        lane="global_serial",
    )
    with pytest.raises(workstreams.WorkstreamRegistryError, match="only one active global_serial"):
        workstreams._validate_concurrency([first, second])
