from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from longcycle.domain.enums import (
    JudgmentOutcomeStatus,
    JudgmentTargetTimeKind,
    OutcomeSemanticRelation,
    OutcomeTimingRelation,
    TemporalDeltaUnit,
    TemporalPrecision,
)
from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentOutcomeEvaluation,
    OutcomeObservation,
)
from longcycle.domain.models import stable_uuid_exact, utc_now


def _relation(
    judgment: JudgmentAssertion,
    outcome: OutcomeObservation,
) -> OutcomeTimingRelation:
    target_from = judgment.target_from
    target_to = judgment.target_to
    outcome_from = outcome.occurrence_from
    outcome_to = outcome.occurrence_to
    if target_from is None and target_to is None:
        return OutcomeTimingRelation.NOT_COMPARABLE
    if outcome_from is None and outcome_to is None:
        return OutcomeTimingRelation.NOT_COMPARABLE

    if target_to is not None and outcome_from is not None and outcome_from >= target_to:
        return OutcomeTimingRelation.AFTER_TARGET_WINDOW
    if target_from is not None and outcome_to is not None and outcome_to <= target_from:
        return OutcomeTimingRelation.BEFORE_TARGET_WINDOW

    lower_ok = target_from is None or (outcome_from is not None and outcome_from >= target_from)
    upper_ok = target_to is None or (outcome_to is not None and outcome_to <= target_to)
    if lower_ok and upper_ok:
        return OutcomeTimingRelation.WITHIN_TARGET_WINDOW

    if (
        target_from is not None
        and target_to is not None
        and outcome_from is not None
        and outcome_to is not None
        and outcome_from < target_to
        and outcome_to > target_from
    ):
        return OutcomeTimingRelation.OVERLAPS_TARGET_WINDOW
    return OutcomeTimingRelation.NOT_COMPARABLE


def _period_index(value: datetime, precision: TemporalPrecision) -> tuple[int, TemporalDeltaUnit] | None:
    if precision == TemporalPrecision.DAY:
        return value.date().toordinal(), TemporalDeltaUnit.DAYS
    if precision == TemporalPrecision.MONTH:
        return value.year * 12 + value.month - 1, TemporalDeltaUnit.CALENDAR_MONTHS
    if precision == TemporalPrecision.QUARTER:
        return value.year * 4 + (value.month - 1) // 3, TemporalDeltaUnit.CALENDAR_QUARTERS
    if precision == TemporalPrecision.HALF_YEAR:
        return value.year * 2 + (value.month - 1) // 6, TemporalDeltaUnit.HALF_YEARS
    if precision == TemporalPrecision.YEAR:
        return value.year, TemporalDeltaUnit.CALENDAR_YEARS
    return None


def _same_precision_delta(
    judgment: JudgmentAssertion,
    outcome: OutcomeObservation,
) -> tuple[Decimal | None, TemporalDeltaUnit | None]:
    if judgment.target_precision != outcome.occurrence_precision:
        return None, None
    if judgment.target_from is None or outcome.occurrence_from is None:
        return None, None
    target = _period_index(judgment.target_from, judgment.target_precision)
    realized = _period_index(outcome.occurrence_from, outcome.occurrence_precision)
    if target is None or realized is None or target[1] != realized[1]:
        return None, None
    return Decimal(realized[0] - target[0]), target[1]


def evaluate_outcome(
    judgment: JudgmentAssertion,
    outcome: OutcomeObservation,
    *,
    semantic_relation: OutcomeSemanticRelation,
    explanation: str,
    evaluation_status: JudgmentOutcomeStatus | None = None,
    evaluator_name: str = "semantic-outcome-evaluator",
    evaluator_version: str = "2.0.0",
    evaluated_at: datetime | None = None,
) -> JudgmentOutcomeEvaluation:
    """Evaluate a later fact without assuming that a related milestone realized the target.

    Timing comparison is only meaningful for a semantic direct match. Related or
    non-comparable milestones are still useful historical Outcome records, but they
    remain indeterminate and cannot carry synthetic timing relations or deltas.
    """

    if judgment.target_time_kind not in {
        JudgmentTargetTimeKind.PERIOD,
        JudgmentTargetTimeKind.UNKNOWN,
    }:
        raise ValueError("precision-aware milestone evaluator currently supports period/unknown targets")

    if semantic_relation == OutcomeSemanticRelation.DIRECT_MATCH:
        status = evaluation_status or JudgmentOutcomeStatus.REALIZED
        relation = _relation(judgment, outcome)
        delta_value, delta_unit = _same_precision_delta(judgment, outcome)
        if relation == OutcomeTimingRelation.NOT_COMPARABLE:
            delta_value = None
            delta_unit = None
    else:
        if evaluation_status not in {None, JudgmentOutcomeStatus.INDETERMINATE}:
            raise ValueError("non-direct outcome semantics cannot claim a realized/not-realized status")
        status = JudgmentOutcomeStatus.INDETERMINATE
        relation = OutcomeTimingRelation.NOT_COMPARABLE
        delta_value = None
        delta_unit = None

    return JudgmentOutcomeEvaluation(
        id=stable_uuid_exact(
            "judgment-outcome-evaluation-v2",
            str(judgment.id),
            str(outcome.evidence_fragment_id),
            semantic_relation.value,
            evaluator_name,
            evaluator_version,
        ),
        judgment_id=judgment.id,
        outcome_evidence_fragment_id=outcome.evidence_fragment_id,
        evaluation_status=status,
        semantic_relation=semantic_relation,
        outcome_from=outcome.occurrence_from,
        outcome_to=outcome.occurrence_to,
        outcome_precision=outcome.occurrence_precision,
        outcome_text=outcome.occurrence_text,
        outcome_first_known_at=outcome.first_known_at,
        timing_relation=relation,
        timing_delta_value=delta_value,
        timing_delta_unit=delta_unit,
        explanation=explanation,
        evaluator_name=evaluator_name,
        evaluator_version=evaluator_version,
        evaluated_at=evaluated_at or utc_now(),
    )


def evaluate_realized_outcome(
    judgment: JudgmentAssertion,
    outcome: OutcomeObservation,
    *,
    explanation: str,
    evaluator_name: str = "precision-aware-outcome-evaluator",
    evaluator_version: str = "1.0.0",
    evaluated_at: datetime | None = None,
) -> JudgmentOutcomeEvaluation:
    """Backward-compatible direct-match evaluator for already-proven milestone cases."""

    if judgment.target_time_kind not in {
        JudgmentTargetTimeKind.PERIOD,
        JudgmentTargetTimeKind.UNKNOWN,
    }:
        raise ValueError("precision-aware milestone evaluator currently supports period/unknown targets")
    relation = _relation(judgment, outcome)
    delta_value, delta_unit = _same_precision_delta(judgment, outcome)
    if relation == OutcomeTimingRelation.NOT_COMPARABLE:
        delta_value = None
        delta_unit = None

    return JudgmentOutcomeEvaluation(
        id=stable_uuid_exact(
            "judgment-outcome-evaluation",
            str(judgment.id),
            str(outcome.evidence_fragment_id),
            evaluator_name,
            evaluator_version,
        ),
        judgment_id=judgment.id,
        outcome_evidence_fragment_id=outcome.evidence_fragment_id,
        evaluation_status=JudgmentOutcomeStatus.REALIZED,
        semantic_relation=OutcomeSemanticRelation.DIRECT_MATCH,
        outcome_from=outcome.occurrence_from,
        outcome_to=outcome.occurrence_to,
        outcome_precision=outcome.occurrence_precision,
        outcome_text=outcome.occurrence_text,
        outcome_first_known_at=outcome.first_known_at,
        timing_relation=relation,
        timing_delta_value=delta_value,
        timing_delta_unit=delta_unit,
        explanation=explanation,
        evaluator_name=evaluator_name,
        evaluator_version=evaluator_version,
        evaluated_at=evaluated_at or utc_now(),
    )
