from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from longcycle.application.judgment_projection import (
    GroundedJudgmentEvidenceRef,
    GroundedJudgmentProjectionItem,
    GroundedJudgmentProjectionSpec,
    GroundedProjectionEvidence,
    JudgmentProjectionSubject,
    build_grounded_judgments,
)
from longcycle.application.normalization import AssertionNormalizer
from longcycle.application.numeric_outcome_evaluation import (
    NumericOutcomeObservation,
    evaluate_numeric_outcome,
)
from longcycle.application.reality_projection import (
    GroundedRealityEvidence,
    GroundedRealityProjectionItem,
    GroundedRealityProjectionSpec,
    RealityProjectionSubject,
    build_grounded_reality_facts,
)
from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    JudgmentKind,
    JudgmentOutcomeStatus,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    OutcomeSemanticRelation,
    TemporalPrecision,
)
from longcycle.domain.judgments import JudgmentAssertion
from longcycle.domain.models import FactAssertion, FactDimensions


SUBJECT_ID = UUID("c46b9fde-ea50-553b-898c-9e02857b07d5")
DIMENSIONS = FactDimensions(statistical_scope="worldwide pc shipments")


def _judgment() -> JudgmentAssertion:
    evidence = GroundedProjectionEvidence(
        fragment_key="forecast",
        evidence_fragment_id=UUID(int=1),
        document_version_id=UUID(int=2),
        source_connector_id=UUID(int=3),
        claim_role="analyst_device_unit_growth_forecast",
        known_time_upper_bound=datetime(2024, 2, 8, tzinfo=UTC),
        excerpt="PC Shipments to Grow 3.5% in 2024",
    )
    spec = GroundedJudgmentProjectionSpec(
        schema_version="longcycle-judgment-projection-spec/v3",
        task_id="numeric-judgment-test",
        source_evidence_task_id="evidence-test",
        allowed_claim_roles=("analyst_device_unit_growth_forecast",),
        subjects=(
            JudgmentProjectionSubject(
                id=SUBJECT_ID,
                entity_type="event",
                canonical_name="Worldwide PC shipments — calendar 2024",
            ),
        ),
        judgments=(
            GroundedJudgmentProjectionItem(
                judgment_key="forecast-2024",
                evidence_refs=(GroundedJudgmentEvidenceRef(fragment_key="forecast"),),
                subject_entity_id=SUBJECT_ID,
                speaker_name_text="Gartner",
                topic_code="market.pc_shipments_yoy_growth",
                predicate_code="market.pc_shipments_yoy_growth",
                dimensions=DIMENSIONS,
                dimensions_complete=True,
                judgment_kind=JudgmentKind.FORECAST,
                target_time_kind=JudgmentTargetTimeKind.PERIOD,
                target_from=datetime(2024, 1, 1, tzinfo=UTC),
                target_to=datetime(2025, 1, 1, tzinfo=UTC),
                target_precision=TemporalPrecision.YEAR,
                target_text="calendar 2024",
                value_kind=JudgmentValueKind.NUMERIC,
                value_numeric=Decimal("0.035"),
                unit_code="ratio",
                summary="Gartner forecast 3.5% PC shipment growth for 2024.",
            ),
        ),
    )
    return build_grounded_judgments(spec, (evidence,))[0]


def _reality() -> FactAssertion:
    evidence = GroundedRealityEvidence(
        fragment_key="outcome",
        evidence_fragment_id=UUID(int=4),
        document_version_id=UUID(int=5),
        source_connector_id=UUID(int=6),
        claim_role="analyst_preliminary_pc_shipment_growth_measurement",
        known_time_upper_bound=datetime(2025, 1, 16, tzinfo=UTC),
        excerpt="1.3% year-over-year",
    )
    spec = GroundedRealityProjectionSpec(
        schema_version="longcycle-reality-projection-spec/v2",
        task_id="numeric-reality-test",
        source_evidence_task_id="evidence-test",
        allowed_claim_roles=("analyst_preliminary_pc_shipment_growth_measurement",),
        subjects=(
            RealityProjectionSubject(
                id=SUBJECT_ID,
                entity_type=EntityType.EVENT,
                canonical_name="Worldwide PC shipments — calendar 2024",
            ),
        ),
        facts=(
            GroundedRealityProjectionItem(
                fact_key="pc-growth-2024",
                evidence_fragment_key="outcome",
                subject_entity_id=SUBJECT_ID,
                predicate_code="market.pc_shipments_yoy_growth",
                value_text="1.3% year-over-year",
                value_kind=FactValueKind.NUMERIC,
                value_numeric=Decimal("0.013"),
                normalized_unit="ratio",
                valid_from=datetime(2024, 1, 1, tzinfo=UTC),
                valid_to=datetime(2025, 1, 1, tzinfo=UTC),
                valid_time_precision=TemporalPrecision.YEAR,
                valid_time_text="calendar 2024",
                dimensions=DIMENSIONS,
                dimensions_complete=True,
            ),
        ),
    )
    return build_grounded_reality_facts(spec, (evidence,))[0]


def test_numeric_projection_reuses_typed_dimensions_for_comparability() -> None:
    judgment = _judgment()
    reality = _reality()

    assert judgment.value_kind == JudgmentValueKind.NUMERIC
    assert judgment.value_numeric == Decimal("0.035")
    assert judgment.unit_code == "ratio"
    assert judgment.predicate_code == reality.field_name
    assert judgment.comparability_hash == reality.dimensions.comparability_hash
    assert judgment.metadata["comparability_dimensions"] == DIMENSIONS.canonical_payload
    assert FactDimensions.model_validate(
        judgment.metadata["comparability_dimensions"]
    ).comparability_hash == judgment.comparability_hash
    assert reality.value_type == FactValueKind.NUMERIC
    assert reality.normalized_number == Decimal("0.013")
    assert reality.normalized_unit == "ratio"


def test_percent_source_alias_normalizes_to_canonical_ratio() -> None:
    raw = _reality().model_copy(
        update={
            "normalized_number": Decimal("999"),
            "normalized_unit": "%",
        }
    )
    normalized = AssertionNormalizer().normalize(raw)

    assert normalized.normalized_number == Decimal("0.013")
    assert normalized.normalized_unit == "ratio"


def test_numeric_outcome_records_realized_minus_forecast_without_threshold() -> None:
    judgment = _judgment()
    reality = FactAssertion.model_validate(_reality().model_dump(mode="json"))
    outcome = NumericOutcomeObservation(
        canonical_fact_version_id=UUID(int=7),
        evidence_fragment_id=reality.evidence[0].evidence_fragment_id,
        predicate_code=reality.field_name,
        comparability_hash=reality.dimensions.comparability_hash,
        value_numeric=reality.normalized_number,
        unit_code=reality.normalized_unit,
        occurrence_from=reality.valid_time.start_utc,
        occurrence_to=reality.valid_time.end_utc,
        occurrence_precision=reality.valid_time_precision,
        occurrence_text=reality.valid_time_text,
        first_known_at=reality.known_at,
    )

    assert reality.valid_time.start_utc == datetime(2024, 1, 1, tzinfo=UTC)
    assert reality.valid_time.end_utc == datetime(2025, 1, 1, tzinfo=UTC)
    evaluation = evaluate_numeric_outcome(
        judgment,
        outcome,
        explanation="same-scope forecast comparison",
    )

    assert evaluation.semantic_relation == OutcomeSemanticRelation.DIRECT_MATCH
    assert evaluation.evaluation_status == JudgmentOutcomeStatus.INDETERMINATE
    assert evaluation.numeric_error == Decimal("-0.022")
    assert evaluation.direction_correct is True
    assert evaluation.canonical_fact_version_id == UUID(int=7)
    assert evaluation.outcome_first_known_at == datetime(2025, 1, 16, tzinfo=UTC)


def test_numeric_outcome_fails_closed_on_scope_mismatch() -> None:
    judgment = _judgment()
    reality = _reality()
    outcome = NumericOutcomeObservation(
        canonical_fact_version_id=UUID(int=7),
        evidence_fragment_id=reality.evidence[0].evidence_fragment_id,
        predicate_code=reality.field_name,
        comparability_hash="0" * 64,
        value_numeric=reality.normalized_number,
        unit_code=reality.normalized_unit,
        occurrence_from=reality.valid_time.start_utc,
        occurrence_to=reality.valid_time.end_utc,
        occurrence_precision=reality.valid_time_precision,
        occurrence_text=reality.valid_time_text,
        first_known_at=reality.known_at,
    )

    with pytest.raises(ValueError, match="dimensions are not directly comparable"):
        evaluate_numeric_outcome(judgment, outcome, explanation="invalid scope")
