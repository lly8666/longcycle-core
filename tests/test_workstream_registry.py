from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPT = ROOT / "scripts" / "workstream_registry.py"
SPEC = importlib.util.spec_from_file_location("workstream_registry", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
workstreams = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workstreams)


def _write_json(root: Path, relative: str, payload: dict[str, Any]) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _use_registry_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(workstreams, "ROOT", root)
    monkeypatch.setattr(workstreams, "WORKSTREAM_ROOT", root / ".longcycle" / "workstreams")
    monkeypatch.setattr(
        workstreams,
        "INDEX_PATH",
        root / ".longcycle" / "workstreams" / "active-index.json",
    )
    monkeypatch.setattr(
        workstreams,
        "BASELINE_POINTER_PATH",
        root / ".longcycle" / "baseline" / "current.json",
    )
    monkeypatch.setattr(
        workstreams,
        "CAPABILITY_INDEX_PATH",
        root / ".longcycle" / "capabilities" / "active-index.json",
    )


def _reservation(
    workstream_id: str = "banking-domain-v1",
    *,
    lifecycle_state: str = "active",
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    root = f".longcycle/workstreams/{workstream_id}"
    return {
        "schema_version": workstreams.RESERVATION_SCHEMA,
        "workstream_id": workstream_id,
        "kind": "industry",
        "lifecycle_state": lifecycle_state,
        "branch": f"workstream/{workstream_id}",
        "base_main_sha": "a" * 40,
        "baseline": "architecture-v1",
        "intent_id": f"{workstream_id.upper()}-001",
        "change_contract_path": f"{root}/change-contract.json",
        "capability_admission_path": f"{root}/capability-admission.json",
        "integration_lane": "parallel",
        "parent_goal_ref": ".longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
        "goal": "Prove one bounded banking industry-memory trajectory.",
        "done_when": "The reserved trajectory replays without lookahead and remains traceable.",
        "exclusive_write_prefixes": ["domain_packs/banking", "tests/banking"],
        "target_capability_ids": ["CAP-0009"],
        "dependencies": dependencies or [],
        "reservation_revision": 1,
        "assignment_epoch": 1,
        "cursor_path": f"{root}/cursor.json",
    }


def _cursor(
    workstream_id: str = "banking-domain-v1",
    *,
    checkpoint: str | None = None,
) -> dict[str, Any]:
    checkpoint_sha = checkpoint or "b" * 40
    reservation_path = f".longcycle/workstreams/{workstream_id}/reservation.json"
    return {
        "schema_version": workstreams.CURSOR_SCHEMA,
        "workstream_id": workstream_id,
        "branch": f"workstream/{workstream_id}",
        "reservation_revision": 1,
        "assignment_epoch": 1,
        "cursor_sequence": 1,
        "checkpoint_based_on_head_sha": checkpoint_sha,
        "parent_refs": [
            "terminal_mission=STRATEGIC_COMPASS.md#one-sentence-mission",
            "long_term_direction=STRATEGIC_COMPASS.md#long-term-direction",
            "medium_term_goal=.longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
            "short_term_goal=.longcycle/handoff/current.json#strategic_horizon.short_term_goal",
            f"workstream_goal={reservation_path}#goal",
        ],
        "last_completed_action": None,
        "current_task": "Ground one bounded source packet.",
        "why_now": "This is the next reserved proof step.",
        "task_done_when": "The packet has a focused validation receipt.",
        "next_atomic_action": "Inspect the first source representation.",
        "required_capability": "high_capability_reasoning",
        "insufficient_capability_action": "stop_and_escalate",
        "progress_state": "planned",
        "partial_summary": "No verification has run for the planned first action.",
        "unverified": True,
        "verification_head_sha": None,
        "verification_refs": [],
        "artifact_refs": [],
        "integration_request_refs": [],
        "receipt_refs": [],
    }


def _install_active_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    _use_registry_root(monkeypatch, tmp_path)
    reservation = _reservation()
    cursor = _cursor()
    _write_json(
        tmp_path,
        ".longcycle/baseline/current.json",
        {"current_baseline": "architecture-v1"},
    )
    _write_json(
        tmp_path,
        ".longcycle/capabilities/active-index.json",
        {"active": [{"id": "CAP-0009"}]},
    )
    _write_json(
        tmp_path,
        reservation["change_contract_path"],
        {
            "schema_version": "longcycle-change-contract/v1",
            "intent_id": reservation["intent_id"],
            "baseline": reservation["baseline"],
            "change_level": "L2",
        },
    )
    _write_json(
        tmp_path,
        reservation["capability_admission_path"],
        {
            "schema_version": "longcycle-capability-admission/v2",
            "intent_id": reservation["intent_id"],
            "disposition": "extend",
            "target_capability_ids": reservation["target_capability_ids"],
        },
    )
    reservation_path = _write_json(
        tmp_path,
        f".longcycle/workstreams/{reservation['workstream_id']}/reservation.json",
        reservation,
    )
    cursor_path = _write_json(tmp_path, reservation["cursor_path"], cursor)
    return reservation_path, reservation, cursor_path, cursor


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


def test_active_v2_reservation_and_cursor_build_a_compact_router(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reservation_path, reservation, _, _ = _install_active_v2(monkeypatch, tmp_path)

    loaded = workstreams.load_workstreams()
    assert len(loaded) == 1
    path, normalized = loaded[0]
    assert path == reservation_path
    assert normalized["_control_schema"] == "reservation-cursor-v2"
    assert normalized["status"] == "planned"

    router = workstreams.build_index(loaded)
    assert len(router["active"]) == 1
    routed = router["active"][0]
    assert {
        "workstream_id": reservation["workstream_id"],
        "kind": reservation["kind"],
        "integration_lane": reservation["integration_lane"],
        "branch": reservation["branch"],
        "reservation_revision": reservation["reservation_revision"],
        "assignment_epoch": reservation["assignment_epoch"],
        "reservation_path": reservation_path.relative_to(tmp_path).as_posix(),
        "cursor_path": reservation["cursor_path"],
        "dependencies": [],
    }.items() <= routed.items()
    # Compact routing hints may evolve; duplicated goal/scope authority may not.
    for duplicated_authority_field in (
        "goal",
        "done_when",
        "progress_state",
        "exclusive_write_prefixes",
        "target_capability_ids",
    ):
        assert duplicated_authority_field not in routed


def test_integrated_v1_is_cold_compatible_without_live_owner_revalidation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_registry_root(monkeypatch, tmp_path)
    legacy = {
        "schema_version": workstreams.LEGACY_WORKSTREAM_SCHEMA,
        "workstream_id": "completed-history",
        "status": "integrated",
        "baseline": "obsolete-baseline-is-cold-provenance",
        "target_capability_ids": ["CAP-DOES-NOT-EXIST-ANYMORE"],
    }
    _write_json(
        tmp_path,
        ".longcycle/workstreams/completed-history/workstream.json",
        legacy,
    )

    loaded = workstreams.load_workstreams()
    assert loaded[0][1]["_control_schema"] == "legacy-v1-history"
    assert workstreams.build_index(loaded)["active"] == []


def test_active_v1_must_be_registered_as_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_registry_root(monkeypatch, tmp_path)
    _write_json(
        tmp_path,
        ".longcycle/workstreams/old-active/workstream.json",
        {
            "schema_version": workstreams.LEGACY_WORKSTREAM_SCHEMA,
            "workstream_id": "old-active",
            "status": "active",
        },
    )
    with pytest.raises(workstreams.WorkstreamRegistryError, match="active v1"):
        workstreams.load_workstreams()


def test_v2_cursor_without_main_owned_reservation_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _use_registry_root(monkeypatch, tmp_path)
    _write_json(
        tmp_path,
        ".longcycle/workstreams/orphan-worker/cursor.json",
        {"schema_version": workstreams.CURSOR_SCHEMA},
    )

    with pytest.raises(workstreams.WorkstreamRegistryError, match="orphan v2 cursor"):
        workstreams.load_workstreams()


def test_v2_reservation_rejects_unknown_authority_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reservation_path, reservation, _, _ = _install_active_v2(monkeypatch, tmp_path)
    reservation["worker_redefined_intent"] = "This must not become a second authority."
    reservation_path.write_text(json.dumps(reservation), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match="field mismatch"):
        workstreams.load_workstreams()


def test_cursor_cannot_shadow_main_owned_goal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor["goal"] = "A branch-local replacement goal is forbidden."
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match="may not shadow"):
        workstreams.load_workstreams()


@pytest.mark.parametrize("field", ["reservation_revision", "assignment_epoch"])
def test_cursor_must_acknowledge_the_current_main_fence(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor[field] = 2
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match="identity/fence mismatch"):
        workstreams.load_workstreams()


def test_cursor_reference_must_resolve_to_a_durable_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor["unverified"] = False
    cursor["partial_summary"] = None
    cursor["verification_head_sha"] = cursor["checkpoint_based_on_head_sha"]
    cursor["verification_refs"] = [
        ".longcycle/workstreams/banking-domain-v1/receipts/missing-verification.json"
    ]
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match=r"missing .*verification_refs"):
        workstreams.load_workstreams()


def test_cursor_reference_count_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor["verification_head_sha"] = cursor["checkpoint_based_on_head_sha"]
    cursor["verification_refs"] = [
        f".longcycle/workstreams/banking-domain-v1/receipts/check-{index}.json"
        for index in range(workstreams.MAX_CURSOR_REFS_PER_KIND + 1)
    ]
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match=r"invalid cursor\.json"):
        workstreams.load_workstreams()


def test_hot_request_and_receipt_records_have_a_size_bound(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    request_ref = ".longcycle/workstreams/banking-domain-v1/requests/shared-engine.json"
    request_path = tmp_path / request_ref
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text("x" * (workstreams.MAX_CONTROL_RECORD_BYTES + 1), encoding="utf-8")
    cursor["integration_request_refs"] = [request_ref]
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match="exceeds"):
        workstreams.load_workstreams()


def test_raw_cursor_bytes_are_bounded_even_when_json_whitespace_is_large(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor_path.write_text(
        (" " * workstreams.MAX_CURSOR_BYTES) + json.dumps(cursor),
        encoding="utf-8",
    )

    with pytest.raises(workstreams.WorkstreamRegistryError, match="exceeds"):
        workstreams.load_workstreams()


def test_raw_reservation_bytes_are_bounded_even_when_json_whitespace_is_large(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reservation_path, reservation, _, _ = _install_active_v2(monkeypatch, tmp_path)
    reservation_path.write_text(
        (" " * workstreams.MAX_RESERVATION_BYTES) + json.dumps(reservation),
        encoding="utf-8",
    )

    with pytest.raises(workstreams.WorkstreamRegistryError, match="exceeds"):
        workstreams.load_workstreams()


def test_verified_cursor_is_pinned_to_the_checkpoint_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    verification_ref = (
        ".longcycle/workstreams/banking-domain-v1/receipts/focused-verification.json"
    )
    _write_json(tmp_path, verification_ref, {"result": "observed"})
    cursor["unverified"] = False
    cursor["partial_summary"] = None
    cursor["verification_head_sha"] = cursor["checkpoint_based_on_head_sha"]
    cursor["verification_refs"] = [verification_ref]
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    loaded = workstreams.load_workstreams()
    assert loaded[0][1]["verification_refs"] == [verification_ref]

    cursor["verification_head_sha"] = "c" * 40
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")
    with pytest.raises(workstreams.WorkstreamRegistryError, match=r"invalid cursor\.json"):
        workstreams.load_workstreams()


def test_unverified_false_requires_exact_verification_pointers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, cursor_path, cursor = _install_active_v2(monkeypatch, tmp_path)
    cursor["unverified"] = False
    cursor["partial_summary"] = None
    cursor_path.write_text(json.dumps(cursor), encoding="utf-8")

    with pytest.raises(workstreams.WorkstreamRegistryError, match=r"invalid cursor\.json"):
        workstreams.load_workstreams()


def test_global_control_plane_paths_are_not_parallel_write_scopes() -> None:
    assert workstreams._is_global_control_prefix(".longcycle/handoff/current.json")
    assert workstreams._is_global_control_prefix(".longcycle/handoff/data-plane.json")
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


def test_active_router_cardinality_is_bounded() -> None:
    active = [
        _active(
            f"worker-{index:02d}",
            branch=f"workstream/worker-{index:02d}",
            prefixes=[f"domain_packs/worker-{index:02d}"],
        )
        for index in range(workstreams.MAX_ACTIVE_WORKSTREAMS + 1)
    ]
    with pytest.raises(workstreams.WorkstreamRegistryError, match="active workstreams exceed"):
        workstreams._validate_concurrency(active)


def test_active_router_bytes_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    reservation = _reservation()
    reservation["status"] = "planned"
    reservation["progress_state"] = "planned"
    path = ROOT / ".longcycle/workstreams/banking-domain-v1/reservation.json"
    monkeypatch.setattr(workstreams, "MAX_INDEX_BYTES", 100)

    with pytest.raises(workstreams.WorkstreamRegistryError, match="active-index would exceed"):
        workstreams.build_index([(path, reservation)])


@pytest.mark.parametrize("path", ["../outside", "domain_packs\\banking", "a//b", "./banking"])
def test_registry_paths_are_literal_posix_repository_paths(path: str) -> None:
    with pytest.raises(workstreams.WorkstreamRegistryError, match="literal repository-relative"):
        workstreams._repo_prefix(path, label="test path")
