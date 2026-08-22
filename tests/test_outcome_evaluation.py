from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from longcycle.application.outcome_evaluation import evaluate_realized_outcome
from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentOutcomeStatus,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    OutcomeTimingRelation,
    TemporalDeltaUnit,
    TemporalPrecision,
)
from longcycle.domain.judgments import JudgmentAssertion, JudgmentEvidenceRef, OutcomeObservation


def may_first_product_judgment() -> JudgmentAssertion:
    return JudgmentAssertion(
        id=UUID(int=1),
        speaker_name_text="Albemarle management",
        subject_entity_id=UUID(int=2),
        topic_code="project.first_product_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 5, 1, tzinfo=UTC),
        target_to=datetime(2022, 6, 1, tzinfo=UTC),
        target_precision=TemporalPrecision.MONTH,
        target_text="May 2022",
        value_kind=JudgmentValueKind.TEXT,
        value_text="first product expected in May 2022",
        summary="First product expected during May 2022.",
        source_published_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        first_known_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        extraction_run_id=UUID(int=3),
        source_connector_id=UUID(int=4),
        extractor_name="grounded-judgment-projection",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=UUID(int=5),
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    )


def july_first_product_outcome() -> OutcomeObservation:
    return OutcomeObservation(
        evidence_fragment_id=UUID(int=6),
        occurrence_from=datetime(2022, 7, 1, tzinfo=UTC),
        occurrence_to=datetime(2022, 8, 1, tzinfo=UTC),
        occurrence_precision=TemporalPrecision.MONTH,
        occurrence_text="in July 2022",
        first_known_at=datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
    )


def test_may_expectation_vs_july_outcome_uses_calendar_months_not_fake_days() -> None:
    evaluation = evaluate_realized_outcome(
        may_first_product_judgment(),
        july_first_product_outcome(),
        explanation="First product was achieved in July rather than the expected May window.",
        evaluated_at=datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
    )

    assert evaluation.evaluation_status == JudgmentOutcomeStatus.REALIZED
    assert evaluation.timing_relation == OutcomeTimingRelation.AFTER_TARGET_WINDOW
    assert evaluation.timing_delta_value == 2
    assert evaluation.timing_delta_unit == TemporalDeltaUnit.CALENDAR_MONTHS
    assert evaluation.outcome_precision == TemporalPrecision.MONTH
    assert evaluation.outcome_first_known_at == datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)


def test_approximate_target_is_not_forced_into_numeric_timing_error() -> None:
    original = may_first_product_judgment()
    approximate = original.model_copy(
        update={
            "target_time_kind": JudgmentTargetTimeKind.UNKNOWN,
            "target_from": None,
            "target_to": None,
            "target_precision": TemporalPrecision.APPROXIMATE,
            "target_text": "late 2021",
        }
    )
    evaluation = evaluate_realized_outcome(
        approximate,
        july_first_product_outcome(),
        explanation="The source target is approximate and cannot support a synthetic exact delay.",
        evaluated_at=datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
    )

    assert evaluation.timing_relation == OutcomeTimingRelation.NOT_COMPARABLE
    assert evaluation.timing_delta_value is None
    assert evaluation.timing_delta_unit is None
