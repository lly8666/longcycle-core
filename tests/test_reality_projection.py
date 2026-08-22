from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.application.reality_projection import (
    GroundedRealityEvidence,
    GroundedRealityProjectionItem,
    GroundedRealityProjectionSpec,
    RealityProjectionSubject,
    build_grounded_reality_facts,
)
from longcycle.domain.enums import (
    EntityType,
    FactEvidenceRole,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import FactEvidenceRef


def _evidence(role: str = "outcome_milestone") -> GroundedRealityEvidence:
    return GroundedRealityEvidence(
        fragment_key="first-product",
        evidence_fragment_id=UUID(int=1),
        document_version_id=UUID(int=2),
        source_connector_id=UUID(int=3),
        claim_role=role,
        known_time_upper_bound=datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
        source_published_at=datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
        excerpt="Kemerton I achieved first product in July 2022",
    )


def _spec(*, allowed: tuple[str, ...] = ("outcome_milestone",)) -> GroundedRealityProjectionSpec:
    subject = RealityProjectionSubject(
        id=UUID(int=10),
        entity_type=EntityType.PRODUCTION_LINE,
        canonical_name="Kemerton I",
    )
    return GroundedRealityProjectionSpec(
        schema_version="longcycle-reality-projection-spec/v1",
        task_id="reality-test",
        source_evidence_task_id="evidence-test",
        allowed_claim_roles=allowed,
        subjects=(subject,),
        facts=(
            GroundedRealityProjectionItem(
                fact_key="first-product-july",
                evidence_fragment_key="first-product",
                subject_entity_id=subject.id,
                predicate_code="project.first_product_status",
                value_text="achieved first product",
                valid_from=datetime(2022, 7, 1, tzinfo=UTC),
                valid_to=datetime(2022, 8, 1, tzinfo=UTC),
                valid_time_precision=TemporalPrecision.MONTH,
                valid_time_text="July 2022",
            ),
        ),
    )


def test_grounded_reality_preserves_evidence_known_time_and_month_precision() -> None:
    evidence = _evidence()
    fact = build_grounded_reality_facts(_spec(), (evidence,))[0]

    assert fact.evidence == (
        FactEvidenceRef(
            evidence_fragment_id=evidence.evidence_fragment_id,
            evidence_role=FactEvidenceRole.SUPPORTING,
        ),
    )
    assert fact.source_id == evidence.source_connector_id
    assert fact.document_id == evidence.document_version_id
    assert fact.known_at == evidence.known_time_upper_bound
    assert fact.valid_time_precision == TemporalPrecision.MONTH
    assert fact.valid_time_text == "July 2022"
    assert fact.valid_time.start == datetime(2022, 7, 1, tzinfo=UTC)
    assert fact.metadata["source_claim_role"] == "outcome_milestone"


def test_projection_spec_cannot_allow_management_expectation_roles() -> None:
    with pytest.raises(ValueError, match="cannot allow expectation/guidance"):
        _spec(allowed=("management_expectation",))


def test_management_expectation_cannot_be_projected_as_reality() -> None:
    with pytest.raises(ValueError, match="disallowed claim role"):
        build_grounded_reality_facts(_spec(), (_evidence("management_expectation"),))


def test_reality_projection_requires_source_supported_bounds() -> None:
    subject = RealityProjectionSubject(
        id=UUID(int=10),
        entity_type=EntityType.PRODUCTION_LINE,
        canonical_name="Kemerton I",
    )
    with pytest.raises(ValueError, match="requires at least one valid-time bound"):
        GroundedRealityProjectionItem(
            fact_key="bad",
            evidence_fragment_key="first-product",
            subject_entity_id=subject.id,
            predicate_code="project.first_product_status",
            value_text="achieved first product",
            valid_time_precision=TemporalPrecision.MONTH,
            valid_time_text="July 2022",
        )


def test_unknown_onset_reality_uses_observation_without_fabricating_valid_from() -> None:
    subject = RealityProjectionSubject(
        id=UUID(int=20),
        entity_type=EntityType.PRODUCTION_LINE,
        canonical_name="Kwinana Train 1",
    )
    observed_day = datetime(2022, 12, 3, tzinfo=UTC)
    known_upper_bound = datetime(2022, 12, 3, 23, 59, 59, tzinfo=UTC)
    evidence = GroundedRealityEvidence(
        fragment_key="continuous-production",
        evidence_fragment_id=UUID(int=21),
        document_version_id=UUID(int=22),
        source_connector_id=UUID(int=23),
        claim_role="project_status",
        known_time_upper_bound=known_upper_bound,
        source_published_at=observed_day,
        excerpt="The plant currently has continuous-production operating capability.",
    )
    spec = GroundedRealityProjectionSpec(
        schema_version="longcycle-reality-projection-spec/v1",
        task_id="kwinana-state-as-of-test",
        source_evidence_task_id="kwinana-evidence-test",
        allowed_claim_roles=("project_status",),
        subjects=(subject,),
        facts=(
            GroundedRealityProjectionItem(
                fact_key="continuous-production-as-of",
                evidence_fragment_key=evidence.fragment_key,
                subject_entity_id=subject.id,
                predicate_code="project.continuous_production_capability",
                value_text="had continuous-production operating capability",
                valid_time_kind=ValidTimeKind.UNKNOWN,
                valid_time_precision=TemporalPrecision.UNKNOWN,
                observed_at=observed_day,
                observed_at_precision=TemporalPrecision.DAY,
                observed_at_text="as of 2022-12-03",
            ),
        ),
    )

    fact = build_grounded_reality_facts(spec, (evidence,))[0]

    assert fact.valid_time_kind == ValidTimeKind.UNKNOWN
    assert fact.valid_time.start is None
    assert fact.valid_time.end is None
    assert fact.valid_time_precision == TemporalPrecision.UNKNOWN
    assert fact.observed_at == observed_day
    assert fact.observed_at_precision == TemporalPrecision.DAY
    assert fact.observed_at_text == "as of 2022-12-03"
    assert fact.known_at == known_upper_bound
