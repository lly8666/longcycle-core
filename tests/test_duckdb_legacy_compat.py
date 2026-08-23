from __future__ import annotations

from datetime import UTC, datetime
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


SUBJECT = MemorySubjectRef(entity_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
JUDGMENT_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
REALITY_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
OUTCOME_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
EVIDENCE_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
JUDGMENT_KNOWN = datetime(2021, 12, 31, 23, 59, 59, tzinfo=UTC)
OUTCOME_KNOWN = datetime(2022, 12, 3, 23, 59, 59, tzinfo=UTC)


def _timeline() -> IndustrialMemoryTimeline:
    judgment = JudgmentMemoryRecord(
        judgment_id=JUDGMENT_ID,
        judgment_key="legacy-guidance",
        subject=SUBJECT,
        speaker_name_text="Management",
        topic_code="project.operation",
        judgment_kind="guidance",
        target_time=TemporalExtent(
            kind="period",
            start=datetime(2021, 12, 1, tzinfo=UTC),
            end=datetime(2022, 1, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="December 2021",
        ),
        value_kind="text",
        value_text="operation expected by year end",
        summary="Management expected operation by year end.",
        known_at=JUDGMENT_KNOWN,
        evidence_fragment_ids=(EVIDENCE_ID,),
    )
    reality = CanonicalRealityRecord(
        canonical_fact_version_id=REALITY_ID,
        subject=SUBJECT,
        predicate_code="project.commercial_production_capability",
        value_kind="text",
        value_text="commercial production capability reached",
        valid_time=TemporalExtent(
            kind="instant",
            at=datetime(2022, 11, 30, tzinfo=UTC),
            precision=TemporalPrecision.DAY,
            source_text="2022-11-30",
        ),
        observed_time=TemporalExtent(
            kind="instant",
            at=OUTCOME_KNOWN,
            precision=TemporalPrecision.DAY,
            source_text="reported 2022-12-03",
        ),
        known_at=OUTCOME_KNOWN,
        confidence=1.0,
        evidence_fragment_ids=(EVIDENCE_ID,),
    )
    outcome = OutcomeMemoryRecord(
        evaluation_id=OUTCOME_ID,
        judgment_id=JUDGMENT_ID,
        subject=SUBJECT,
        canonical_fact_version_id=REALITY_ID,
        outcome_evidence_fragment_id=EVIDENCE_ID,
        evaluation_status="indeterminate",
        semantic_relation="related_milestone",
        occurrence_time=reality.valid_time,
        known_at=OUTCOME_KNOWN,
        timing_relation="not_comparable",
        evaluator_name="legacy-fixture",
        evaluator_version="1.0.0",
    )
    return IndustrialMemoryTimeline(
        reality=(reality,),
        judgments=(judgment,),
        outcomes=(outcome,),
    )


@pytest.mark.asyncio
async def test_reader_accepts_additive_legacy_v1_generation(tmp_path) -> None:
    duckdb = pytest.importorskip("duckdb")
    path = tmp_path / "legacy-v1.duckdb"
    seal_industrial_memory(path, _timeline())

    connection = duckdb.connect(str(path))
    try:
        connection.execute("DROP TABLE judgment_rationale_memory")
        connection.execute("DROP TABLE judgment_relation_memory")
        connection.execute("ALTER TABLE reality_memory DROP COLUMN observed_at")
        connection.execute("ALTER TABLE reality_memory DROP COLUMN observed_at_precision")
        connection.execute("ALTER TABLE reality_memory DROP COLUMN observed_at_text")
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    reader = DuckDBEpistemicMemoryReader(path)
    restored = await reader.timeline((SUBJECT,))
    assert len(restored.judgments) == 1
    assert len(restored.reality) == 1
    assert restored.reality[0].observed_time is None
    assert len(restored.outcomes) == 1
    assert restored.judgment_rationales == ()
    assert restored.judgment_relations == ()

    before = await reader.snapshot(
        (SUBJECT,),
        knowledge_cutoff=datetime(2022, 12, 3, 23, 59, 58, tzinfo=UTC),
    )
    assert len(before.judgments) == 1
    assert before.reality == ()
    assert before.outcomes == ()

    at = await reader.snapshot((SUBJECT,), knowledge_cutoff=OUTCOME_KNOWN)
    assert len(at.reality) == 1
    assert at.reality[0].valid_time.at == datetime(2022, 11, 30, tzinfo=UTC)
    assert at.reality[0].observed_time is None
    assert len(at.outcomes) == 1
