from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from longcycle.adapters.storage.duckdb_epistemic import (
    DuckDBEpistemicMemoryReader,
    seal_industrial_memory,
)
from longcycle.domain.epistemic import (
    CanonicalRealityRecord,
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    MemorySubjectRef,
    OutcomeMemoryRecord,
    TemporalExtent,
)
from longcycle.domain.enums import TemporalPrecision


SUBJECT = MemorySubjectRef(entity_id=UUID("11111111-1111-1111-1111-111111111111"))
JUDGMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
REALITY_ID = UUID("33333333-3333-3333-3333-333333333333")
OUTCOME_ID = UUID("44444444-4444-4444-4444-444444444444")
JUDGMENT_EVIDENCE_ID = UUID("55555555-5555-5555-5555-555555555555")
OUTCOME_EVIDENCE_ID = UUID("66666666-6666-6666-6666-666666666666")
JUDGMENT_KNOWN = datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC)
OUTCOME_KNOWN = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)


def _timeline() -> IndustrialMemoryTimeline:
    judgment = JudgmentMemoryRecord(
        judgment_id=JUDGMENT_ID,
        judgment_key="first-product-may",
        subject=SUBJECT,
        speaker_name_text="Management",
        topic_code="project.first_product",
        judgment_kind="guidance",
        target_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 5, 1, tzinfo=UTC),
            end=datetime(2022, 6, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="May 2022",
        ),
        value_kind="text",
        value_text="first product expected in May 2022",
        summary="Management expected first product in May 2022.",
        known_at=JUDGMENT_KNOWN,
        evidence_fragment_ids=(JUDGMENT_EVIDENCE_ID,),
    )
    reality = CanonicalRealityRecord(
        canonical_fact_version_id=REALITY_ID,
        subject=SUBJECT,
        predicate_code="project.first_product_status",
        value_kind="text",
        value_text="achieved first product",
        valid_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 7, 1, tzinfo=UTC),
            end=datetime(2022, 8, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="July 2022",
        ),
        known_at=OUTCOME_KNOWN,
        confidence=0.95,
        evidence_fragment_ids=(OUTCOME_EVIDENCE_ID,),
    )
    outcome = OutcomeMemoryRecord(
        evaluation_id=OUTCOME_ID,
        judgment_id=JUDGMENT_ID,
        subject=SUBJECT,
        canonical_fact_version_id=REALITY_ID,
        outcome_evidence_fragment_id=OUTCOME_EVIDENCE_ID,
        evaluation_status="realized",
        occurrence_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 7, 1, tzinfo=UTC),
            end=datetime(2022, 8, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="July 2022",
        ),
        known_at=OUTCOME_KNOWN,
        timing_relation="after_target_window",
        timing_delta_value=Decimal("2"),
        timing_delta_unit="calendar_months",
        evaluator_name="precision-aware-outcome-evaluator",
        evaluator_version="1.0.0",
    )
    return IndustrialMemoryTimeline(
        reality=(reality,),
        judgments=(judgment,),
        outcomes=(outcome,),
    )


@pytest.mark.asyncio
async def test_duckdb_memory_round_trip_and_no_lookahead(tmp_path) -> None:
    path = tmp_path / "industrial-memory.duckdb"
    timeline = _timeline()

    manifest = seal_industrial_memory(path, timeline)
    assert manifest["typed_round_trip"] is True
    assert manifest["counts"] == {"reality": 1, "judgments": 1, "outcomes": 1}

    reader = DuckDBEpistemicMemoryReader(path)
    restored = await reader.timeline((SUBJECT,))
    assert restored == timeline

    before = await reader.snapshot(
        (SUBJECT,),
        knowledge_cutoff=datetime(2022, 8, 3, 16, 27, 48, tzinfo=UTC),
    )
    assert len(before.judgments) == 1
    assert before.reality == ()
    assert before.outcomes == ()

    at = await reader.snapshot((SUBJECT,), knowledge_cutoff=OUTCOME_KNOWN)
    assert len(at.judgments) == 1
    assert len(at.reality) == 1
    assert len(at.outcomes) == 1
    assert at.reality[0].valid_time.kind == "period"
    assert at.reality[0].valid_time.precision == TemporalPrecision.MONTH
    assert at.reality[0].valid_time.source_text == "July 2022"
    assert at.outcomes[0].timing_delta_value == Decimal("2")
    assert at.outcomes[0].timing_delta_unit == "calendar_months"
