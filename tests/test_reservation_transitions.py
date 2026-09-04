from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "validate_reservation_transitions.py"
SPEC = importlib.util.spec_from_file_location("validate_reservation_transitions", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
transitions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transitions)


def _reservation(*, revision: int = 1) -> dict[str, object]:
    return {
        "schema_version": "longcycle-workstream-reservation/v2",
        "workstream_id": "shipping-domain-v1",
        "kind": "industry",
        "lifecycle_state": "active",
        "branch": "workstream/shipping-domain-v1",
        "base_main_sha": "a" * 40,
        "baseline": "architecture-v1",
        "intent_id": "SHIPPING-DOMAIN-V1-001",
        "change_contract_path": ".longcycle/workstreams/shipping-domain-v1/change-contract.json",
        "capability_admission_path": ".longcycle/workstreams/shipping-domain-v1/capability-admission.json",
        "integration_lane": "parallel",
        "parent_goal_ref": ".longcycle/handoff/current.json#strategic_horizon.short_term_goal",
        "goal": "Build one bounded Shipping industrial-memory slice.",
        "done_when": "One representative trajectory is traceable and replays without lookahead.",
        "exclusive_write_prefixes": ["domain_packs/shipping", "tests/shipping"],
        "target_capability_ids": ["CAP-0009", "CAP-0010"],
        "dependencies": [],
        "reservation_revision": revision,
        "assignment_epoch": 1,
        "cursor_path": ".longcycle/workstreams/shipping-domain-v1/cursor.json",
    }


def test_new_reservation_starts_at_revision_one() -> None:
    transitions.validate_transition(
        path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
        previous=None,
        current=_reservation(),
    )


def test_new_reservation_cannot_skip_revision_one() -> None:
    with pytest.raises(transitions.ReservationTransitionError, match="must start"):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=None,
            current=_reservation(revision=2),
        )


def test_main_cannot_change_active_reservation_authority_without_revision_bump() -> None:
    previous = _reservation()
    current = dict(previous)
    current["done_when"] = "Exactly one stage-two pilot is accepted."

    with pytest.raises(
        transitions.ReservationTransitionError,
        match="reservation_revision did not advance exactly once",
    ):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=previous,
            current=current,
        )


def test_authority_change_requires_exactly_one_revision_step() -> None:
    previous = _reservation(revision=4)
    current = dict(previous)
    current["done_when"] = "A revised bounded milestone is accepted."
    current["reservation_revision"] = 5

    transitions.validate_transition(
        path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
        previous=previous,
        current=current,
    )


def test_authority_change_cannot_skip_a_revision() -> None:
    previous = _reservation(revision=4)
    current = dict(previous)
    current["goal"] = "A materially revised Shipping workstream goal."
    current["reservation_revision"] = 6

    with pytest.raises(transitions.ReservationTransitionError, match="expected=5"):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=previous,
            current=current,
        )


def test_revision_cannot_bump_without_authority_change() -> None:
    previous = _reservation(revision=2)
    current = dict(previous)
    current["reservation_revision"] = 3

    with pytest.raises(transitions.ReservationTransitionError, match="without any main-owned"):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=previous,
            current=current,
        )


def test_set_like_reordering_is_not_an_authority_change() -> None:
    previous = _reservation(revision=3)
    current = dict(previous)
    current["exclusive_write_prefixes"] = list(
        reversed(previous["exclusive_write_prefixes"])  # type: ignore[arg-type]
    )

    transitions.validate_transition(
        path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
        previous=previous,
        current=current,
    )


def test_assignment_epoch_change_is_versioned_authority() -> None:
    previous = _reservation(revision=7)
    current = dict(previous)
    current["assignment_epoch"] = 2

    with pytest.raises(transitions.ReservationTransitionError, match="assignment_epoch"):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=previous,
            current=current,
        )


def test_active_reservation_cannot_be_deleted() -> None:
    with pytest.raises(transitions.ReservationTransitionError, match="may not be deleted"):
        transitions.validate_transition(
            path=".longcycle/workstreams/shipping-domain-v1/reservation.json",
            previous=_reservation(),
            current=None,
        )
