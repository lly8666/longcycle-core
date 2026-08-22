from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.adapters.storage.judgments import InMemoryJudgmentRepository
from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentRelationType,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
)
from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentEvidenceRef,
    JudgmentRelation,
)


def judgment(judgment_id: int, *, summary: str = "expected milestone") -> JudgmentAssertion:
    return JudgmentAssertion(
        id=UUID(int=judgment_id),
        speaker_name_text="Management",
        subject_entity_id=UUID(int=100),
        topic_code="project.milestone_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 5, 1, tzinfo=UTC),
        target_to=datetime(2022, 6, 1, tzinfo=UTC),
        value_kind=JudgmentValueKind.TEXT,
        value_text=summary,
        summary=summary,
        source_published_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        first_known_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        extraction_run_id=UUID(int=200),
        source_connector_id=UUID(int=300),
        extractor_name="grounded-judgment-projection",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=UUID(int=400 + judgment_id),
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    )


def test_in_memory_judgment_append_is_idempotent_but_immutable() -> None:
    async def scenario() -> None:
        repository = InMemoryJudgmentRepository()
        original = judgment(1)
        await repository.append_judgments((original,))
        await repository.append_judgments((original,))
        assert repository.judgments == {original.id: original}

        mutated = judgment(1, summary="different immutable content")
        with pytest.raises(ValueError, match="different immutable content"):
            await repository.append_judgments((mutated,))

    asyncio.run(scenario())


def test_in_memory_relation_append_is_idempotent_but_conflict_sensitive() -> None:
    async def scenario() -> None:
        repository = InMemoryJudgmentRepository()
        first = judgment(1)
        second = judgment(2, summary="revised milestone")
        await repository.append_judgments((first, second))

        relation = JudgmentRelation(
            from_judgment_id=first.id,
            to_judgment_id=second.id,
            relation_type=JudgmentRelationType.REVISES,
            reason_summary="later guidance revised the target window",
        )
        await repository.append_relations((relation,))
        await repository.append_relations((relation,))
        assert len(repository.relations) == 1

        conflicting = relation.model_copy(update={"reason_summary": "different rationale"})
        with pytest.raises(ValueError, match="different content"):
            await repository.append_relations((conflicting,))

    asyncio.run(scenario())
