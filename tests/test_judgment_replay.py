from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from longcycle.application.judgment_replay import (
    JudgmentReplaySnapshot,
    ReplayJudgment,
    build_judgment_replay_snapshot,
)
from longcycle.domain.enums import (
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)


def judgment(key: str, known_at: datetime) -> ReplayJudgment:
    suffix = len(key)
    return ReplayJudgment(
        judgment_key=key,
        judgment_id=UUID(int=suffix + 1),
        subject_entity_id=UUID(int=100),
        speaker_name_text="Management",
        topic_code="project.completion",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.UNKNOWN,
        target_precision=TemporalPrecision.APPROXIMATE,
        target_text="late 2021",
        value_kind=JudgmentValueKind.TEXT,
        value_text="completion expected in late 2021",
        summary="Completion expected in late 2021.",
        first_known_at=known_at,
        evidence_fragment_ids=(UUID(int=suffix + 200),),
    )


def test_judgment_snapshot_exposes_only_cognition_knowable_by_cutoff() -> None:
    first = datetime(2021, 2, 19, 16, 37, 48, tzinfo=UTC)
    revision = datetime(2021, 8, 4, 16, 25, 25, tzinfo=UTC)
    population = (judgment("original", first), judgment("revision", revision))

    before = build_judgment_replay_snapshot(
        population,
        knowledge_cutoff=revision - timedelta(seconds=1),
    )
    at = build_judgment_replay_snapshot(population, knowledge_cutoff=revision)

    assert [item.judgment_key for item in before.judgments] == ["original"]
    assert [item.judgment_key for item in at.judgments] == ["original", "revision"]
    assert before.judgments[0].target_precision == TemporalPrecision.APPROXIMATE
    assert before.judgments[0].target_text == "late 2021"
    assert before.judgments[0].target_from is None
    assert before.judgments[0].target_to is None
    assert "revision" not in before.model_dump_json()


def test_snapshot_model_rejects_future_judgment() -> None:
    cutoff = datetime(2021, 1, 1, tzinfo=UTC)
    future = judgment("future", cutoff + timedelta(seconds=1))

    with pytest.raises(ValueError, match="after the knowledge cutoff"):
        JudgmentReplaySnapshot(knowledge_cutoff=cutoff, judgments=(future,))


def test_judgment_replay_rejects_naive_cutoff() -> None:
    with pytest.raises(ValueError, match="timezone"):
        build_judgment_replay_snapshot((), knowledge_cutoff=datetime(2021, 1, 1))
