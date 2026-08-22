from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from longcycle.application.historical_replay import (
    ReplayEvidence,
    ReplaySnapshot,
    build_replay_sequence,
    build_replay_snapshot,
)


def evidence(fragment_key: str, known_at: datetime, *, role: str = "management_expectation") -> ReplayEvidence:
    suffix = len(fragment_key)
    return ReplayEvidence(
        fragment_key=fragment_key,
        evidence_fragment_id=UUID(int=suffix + 1),
        document_version_id=UUID(int=suffix + 101),
        artifact_id=None,
        locator=f"text:{suffix}:{suffix + 5}",
        excerpt=f"statement {fragment_key}",
        claim_role=role,
        known_time_upper_bound=known_at,
        known_time_precision="instant",
        valid_effective_time=None,
        expectation_horizon=None,
    )


def test_snapshot_exposes_only_evidence_knowable_by_cutoff() -> None:
    first = datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC)
    outcome = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)
    population = (
        evidence("first-product-expectation", first),
        evidence("first-product-outcome", outcome, role="outcome_milestone"),
    )

    before = build_replay_snapshot(
        population,
        knowledge_cutoff=outcome - timedelta(seconds=1),
    )
    at = build_replay_snapshot(population, knowledge_cutoff=outcome)

    assert [item.fragment_key for item in before.evidence] == ["first-product-expectation"]
    assert [item.fragment_key for item in at.evidence] == [
        "first-product-expectation",
        "first-product-outcome",
    ]
    serialized_before = before.model_dump(mode="json")
    assert "first-product-outcome" not in str(serialized_before)
    assert "hidden" not in serialized_before
    assert "future" not in serialized_before


def test_exact_known_time_boundary_is_inclusive() -> None:
    known_at = datetime(2021, 8, 4, 16, 25, 25, tzinfo=UTC)
    item = evidence("revision", known_at)

    before = build_replay_snapshot(
        (item,),
        knowledge_cutoff=known_at - timedelta(microseconds=1),
    )
    at = build_replay_snapshot((item,), knowledge_cutoff=known_at)

    assert before.evidence == ()
    assert at.evidence == (item,)


def test_sequence_is_monotone_and_deterministic() -> None:
    t1 = datetime(2019, 1, 2, 23, 59, 59, tzinfo=UTC)
    t2 = datetime(2019, 8, 7, 16, 57, 18, tzinfo=UTC)
    population = (
        evidence("z-second-at-first-time", t1),
        evidence("a-first-at-first-time", t1),
        evidence("later", t2),
    )

    snapshots = build_replay_sequence(
        population,
        knowledge_cutoffs=(t1, t2),
    )

    assert [item.fragment_key for item in snapshots[0].evidence] == [
        "a-first-at-first-time",
        "z-second-at-first-time",
    ]
    assert {item.fragment_key for item in snapshots[0].evidence}.issubset(
        {item.fragment_key for item in snapshots[1].evidence}
    )


def test_naive_cutoff_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone"):
        build_replay_snapshot(
            (),
            knowledge_cutoff=datetime(2022, 1, 1),
        )


def test_snapshot_model_rejects_future_evidence() -> None:
    cutoff = datetime(2022, 1, 1, tzinfo=UTC)
    future = evidence("future", cutoff + timedelta(seconds=1))

    with pytest.raises(ValueError, match="after the knowledge cutoff"):
        ReplaySnapshot(
            knowledge_cutoff=cutoff,
            evidence=(future,),
        )


def test_sequence_requires_strictly_increasing_cutoffs() -> None:
    cutoff = datetime(2022, 1, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="strictly increasing"):
        build_replay_sequence(
            (),
            knowledge_cutoffs=(cutoff, cutoff),
        )
