from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator, model_validator

from longcycle.application.outcome_evaluation import evaluate_outcome
from longcycle.domain.enums import (
    JudgmentOutcomeStatus,
    JudgmentValueKind,
    OutcomeSemanticRelation,
    TemporalPrecision,
)
from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentOutcomeEvaluation,
    OutcomeObservation,
)
from longcycle.domain.models import DomainModel, require_aware_datetime


class NumericOutcomeObservation(DomainModel):
    """Canonical Reality value selected for direct numeric Judgment comparison."""

    canonical_fact_version_id: UUID
    evidence_fragment_id: UUID
    predicate_code: str = Field(
        min_length=3,
        pattern=r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$",
    )
    comparability_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    value_numeric: Decimal
    unit_code: str = Field(min_length=1)
    occurrence_from: datetime | None = None
    occurrence_to: datetime | None = None
    occurrence_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    occurrence_text: str | None = None
    first_known_at: datetime

    @field_validator("occurrence_from", "occurrence_to", "first_known_at")
    @classmethod
    def times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def preserves_source_precision(self) -> NumericOutcomeObservation:
        if (
            self.occurrence_from is not None
            and self.occurrence_to is not None
            and self.occurrence_to <= self.occurrence_from
        ):
            raise ValueError("numeric outcome occurrence_to must be after occurrence_from")
        if (
            self.occurrence_precision == TemporalPrecision.APPROXIMATE
            and not self.occurrence_text
        ):
            raise ValueError("approximate numeric outcome must preserve source occurrence text")
        return self


def _direction_correct(forecast: Decimal, realized: Decimal) -> bool | None:
    if forecast == 0 or realized == 0:
        return forecast == realized
    return (forecast > 0) == (realized > 0)


def evaluate_numeric_outcome(
    judgment: JudgmentAssertion,
    outcome: NumericOutcomeObservation,
    *,
    explanation: str,
    evaluation_status: JudgmentOutcomeStatus = JudgmentOutcomeStatus.INDETERMINATE,
    evaluator_name: str = "numeric-outcome-evaluator",
    evaluator_version: str = "1.0.0",
    evaluated_at: datetime | None = None,
) -> JudgmentOutcomeEvaluation:
    """Compare source-grounded numeric Judgment with directly comparable Reality.

    Comparison fails closed on predicate, typed dimensions hash and normalized unit.
    ``numeric_error`` is always realized minus Judgment value. Classification remains
    indeterminate by default because the system does not invent a correctness tolerance.
    """

    if judgment.value_kind != JudgmentValueKind.NUMERIC or judgment.value_numeric is None:
        raise ValueError("numeric Outcome evaluation requires a numeric Judgment value")
    if judgment.predicate_code is None or judgment.comparability_hash is None:
        raise ValueError("numeric Outcome evaluation requires Judgment comparability identity")
    if not judgment.dimensions_complete:
        raise ValueError("numeric Outcome evaluation requires complete Judgment dimensions")
    if judgment.unit_code is None:
        raise ValueError("numeric Outcome evaluation requires a normalized Judgment unit")
    if judgment.predicate_code != outcome.predicate_code:
        raise ValueError("numeric Outcome predicate mismatch")
    if judgment.comparability_hash != outcome.comparability_hash:
        raise ValueError("numeric Outcome dimensions are not directly comparable")
    if judgment.unit_code != outcome.unit_code:
        raise ValueError("numeric Outcome unit mismatch")

    temporal = OutcomeObservation(
        evidence_fragment_id=outcome.evidence_fragment_id,
        occurrence_from=outcome.occurrence_from,
        occurrence_to=outcome.occurrence_to,
        occurrence_precision=outcome.occurrence_precision,
        occurrence_text=outcome.occurrence_text,
        first_known_at=outcome.first_known_at,
    )
    base = evaluate_outcome(
        judgment,
        temporal,
        semantic_relation=OutcomeSemanticRelation.DIRECT_MATCH,
        explanation=explanation,
        evaluation_status=evaluation_status,
        evaluator_name=evaluator_name,
        evaluator_version=evaluator_version,
        evaluated_at=evaluated_at or outcome.first_known_at,
    )
    error = outcome.value_numeric - judgment.value_numeric
    relative_error = (
        float(error / abs(judgment.value_numeric))
        if judgment.value_numeric != 0
        else None
    )
    return JudgmentOutcomeEvaluation.model_validate(
        {
            **base.model_dump(mode="python"),
            "canonical_fact_version_id": outcome.canonical_fact_version_id,
            "numeric_error": error,
            "relative_error": relative_error,
            "direction_correct": _direction_correct(
                judgment.value_numeric,
                outcome.value_numeric,
            ),
        }
    )
