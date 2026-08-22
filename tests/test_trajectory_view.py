from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from longcycle.application.trajectory_view import build_researcher_trajectory_view
from longcycle.domain.epistemic import (
    CanonicalRealityRecord,
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    JudgmentRationaleMemoryRecord,
    JudgmentRelationMemoryRecord,
    MemorySubjectRef,
    OutcomeMemoryRecord,
    TemporalExtent,
    snapshot_from_timeline,
)
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision


SUBJECT = MemorySubjectRef(entity_id=UUID("11111111-1111-1111-1111-111111111111"))
EARLY_JUDGMENT = UUID("22222222-2222-2222-2222-222222222222")
REVISED_JUDGMENT = UUID("22222222-2222-2222-2222-222222222223")
REALITY_ID = UUID("33333333-3333-3333-3333-333333333333")
EARLY_KNOWN = datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC)
LATER_KNOWN = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)


def _timeline() -> IndustrialMemoryTimeline:
    early = JudgmentMemoryRecord(
        judgment_id=EARLY_JUDGMENT,
        judgment_key="may-guidance",
        subject=SUBJECT,
        speaker_name_text="Management",
        topic_code="project.first_product",
        judgment_kind="guidance",
        target_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 5, 1, tzinfo=UTC),
            end=datetime(2022, 6, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
        ),
        value_kind="text",
        value_text="first product expected in May 2022",
        summary="Management expected first product in May 2022.",
        known_at=EARLY_KNOWN,
        evidence_fragment_ids=(UUID("55555555-5555-5555-5555-555555555555"),),
    )
    revised = early.model_copy(
        update={
            "judgment_id": REVISED_JUDGMENT,
            "judgment_key": "july-guidance",
            "target_time": TemporalExtent(
                kind="period",
                start=datetime(2022, 7, 1, tzinfo=UTC),
                end=datetime(2022, 8, 1, tzinfo=UTC),
                precision=TemporalPrecision.MONTH,
            ),
            "value_text": "first product revised to July 2022",
            "summary": "Management revised first-product guidance to July 2022.",
            "known_at": LATER_KNOWN,
        }
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
        ),
        observed_time=TemporalExtent(
            kind="instant",
            at=datetime(2022, 8, 3, tzinfo=UTC),
            precision=TemporalPrecision.DAY,
        ),
        known_at=LATER_KNOWN,
        confidence=0.95,
        evidence_fragment_ids=(UUID("66666666-6666-6666-6666-666666666666"),),
    )
    return IndustrialMemoryTimeline(
        reality=(reality,),
        judgments=(early, revised),
        judgment_rationales=(
            JudgmentRationaleMemoryRecord(
                rationale_id=UUID("77777777-7777-7777-7777-777777777777"),
                judgment_id=REVISED_JUDGMENT,
                rationale_kind=JudgmentRationaleKind.MECHANISM,
                summary="Qualification took longer than originally expected.",
                known_at=LATER_KNOWN,
            ),
        ),
        judgment_relations=(
            JudgmentRelationMemoryRecord(
                from_judgment_id=REVISED_JUDGMENT,
                to_judgment_id=EARLY_JUDGMENT,
                relation_type=JudgmentRelationType.REVISES,
                reason_summary="July timing replaces the earlier May guidance.",
                known_at=LATER_KNOWN,
            ),
        ),
        outcomes=(
            OutcomeMemoryRecord(
                evaluation_id=UUID("44444444-4444-4444-4444-444444444444"),
                judgment_id=EARLY_JUDGMENT,
                subject=SUBJECT,
                canonical_fact_version_id=REALITY_ID,
                outcome_evidence_fragment_id=UUID("66666666-6666-6666-6666-666666666666"),
                evaluation_status="realized",
                occurrence_time=reality.valid_time,
                known_at=LATER_KNOWN,
                timing_relation="after_target_window",
                timing_delta_value=Decimal("2"),
                timing_delta_unit="calendar_months",
                evaluator_name="precision-aware-outcome-evaluator",
                evaluator_version="1.0.0",
            ),
        ),
    )


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_trajectory_view_keeps_knowledge_time_and_historical_time_separate() -> None:
    timeline = _timeline()
    before = snapshot_from_timeline(
        timeline,
        knowledge_cutoff=datetime(2022, 8, 3, 16, 27, 48, tzinfo=UTC),
    )
    before_view = build_researcher_trajectory_view(before)
    assert before_view["counts"]["judgments"] == 1
    assert before_view["counts"]["reality"] == 0
    assert before_view["counts"]["outcomes"] == 0
    assert [entry["layer"] for entry in before_view["entries"]] == ["judgment"]
    assert before_view["entries"][0]["known_at"] == EARLY_KNOWN.isoformat()
    early_time = before_view["entries"][0]["historical_time"]
    assert _iso(early_time["start"]) == datetime(2022, 5, 1, tzinfo=UTC)
    assert _iso(early_time["end"]) == datetime(2022, 6, 1, tzinfo=UTC)
    assert early_time["precision"] == "month"

    at = snapshot_from_timeline(timeline, knowledge_cutoff=LATER_KNOWN)
    view = build_researcher_trajectory_view(at)
    assert view["counts"] == {
        "reality": 1,
        "judgments": 2,
        "outcomes": 1,
        "judgment_rationales": 1,
        "judgment_relations": 1,
    }
    assert [entry["layer"] for entry in view["entries"]] == [
        "judgment",
        "judgment",
        "reality",
        "outcome",
    ]
    revised = view["entries"][1]
    assert revised["rationales"][0]["summary"] == "Qualification took longer than originally expected."
    assert revised["relations"][0]["relation_type"] == "revises"
    outcome = view["entries"][3]
    assert outcome["links"]["judgment_entry_id"] == f"judgment:{EARLY_JUDGMENT}"
    assert outcome["links"]["reality_entry_id"] == f"reality:{REALITY_ID}"
    occurrence = outcome["historical_time"]
    assert _iso(occurrence["start"]) == datetime(2022, 7, 1, tzinfo=UTC)
    assert _iso(occurrence["end"]) == datetime(2022, 8, 1, tzinfo=UTC)
    assert occurrence["precision"] == "month"
    assert outcome["known_at"] == LATER_KNOWN.isoformat()
    assert view["boundary"]["judgment_not_rewritten_by_outcome"] is True
