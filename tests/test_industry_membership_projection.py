from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from longcycle.application.industry_membership_projection import (
    build_industry_membership_projection,
    project_resolved_industry_membership,
)
from longcycle.domain.enums import (
    EntityType,
    FactEvidenceRole,
    FactValueKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import (
    FactAssertion,
    FactDimensions,
    FactEvidenceRef,
    QualityComponents,
    TimeRange,
)
from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    ResolvedIndustryMembershipResolution,
)


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
ENTITY_ID = UUID("20000000-0000-0000-0000-000000000001")
EVIDENCE_ID = UUID("30000000-0000-0000-0000-000000000001")
ASSERTION_ID = UUID("40000000-0000-0000-0000-000000000001")
RESOLUTION_ID = UUID("50000000-0000-0000-0000-000000000001")
KNOWN_AT = datetime(2021, 6, 1, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 8, 24, tzinfo=UTC)


def _quality() -> QualityComponents:
    return QualityComponents(
        source_quality=0.95,
        extraction_certainty=0.95,
        entity_match=0.95,
        time_unit_completeness=0.95,
        corroboration=0.0,
        freshness=0.9,
        conflict_penalty=0.0,
    )


def _assertion(
    *,
    field_name: str = "industry.membership",
    metadata: dict[str, object] | None = None,
    valid_time: TimeRange | None = None,
    valid_time_kind: ValidTimeKind = ValidTimeKind.PERIOD,
) -> FactAssertion:
    return FactAssertion(
        id=ASSERTION_ID,
        entity_type=EntityType.FACILITY,
        entity_id=ENTITY_ID,
        field_name=field_name,
        value="conversion_facility",
        value_type=FactValueKind.TEXT,
        dimensions=FactDimensions(statistical_scope="industry orientation membership"),
        dimensions_complete=True,
        valid_time_kind=valid_time_kind,
        valid_time=valid_time
        or TimeRange(
            start=datetime(2020, 1, 1, tzinfo=UTC),
            end=datetime(2030, 1, 1, tzinfo=UTC),
        ),
        valid_time_precision=(
            TemporalPrecision.RANGE
            if valid_time_kind == ValidTimeKind.PERIOD
            else TemporalPrecision.UNKNOWN
        ),
        known_at=KNOWN_AT,
        source_id=UUID("60000000-0000-0000-0000-000000000001"),
        document_id=UUID("70000000-0000-0000-0000-000000000001"),
        evidence=(FactEvidenceRef(evidence_fragment_id=EVIDENCE_ID),),
        extraction_run_id=UUID("80000000-0000-0000-0000-000000000001"),
        extractor_name="test",
        extractor_version="1",
        source_cluster="test-source",
        confidence=0.95,
        quality=_quality(),
        metadata=metadata
        or {
            "industry_node_id": str(INDUSTRY_ID),
            "exposure_type": "direct",
        },
    )


def _resolution(
    *assertions: FactAssertion,
) -> ResolvedIndustryMembershipResolution:
    return ResolvedIndustryMembershipResolution(
        resolution_id=RESOLUTION_ID,
        selected_assertions=assertions or (_assertion(),),
        confidence=0.93,
        resolved_at=RESOLVED_AT,
    )


def test_membership_projection_preserves_resolution_truth_and_historical_time() -> None:
    resolution = _resolution(_assertion())

    first = build_industry_membership_projection(resolution)
    second = build_industry_membership_projection(resolution)

    assert first == second
    assert first.industry_node_id == INDUSTRY_ID
    assert first.entity_id == ENTITY_ID
    assert first.role == "conversion_facility"
    assert first.exposure_type == "direct"
    assert first.valid_from.isoformat() == "2020-01-01"
    assert first.valid_to.isoformat() == "2030-01-01"
    assert first.known_at == KNOWN_AT
    assert first.system_from == RESOLVED_AT
    assert first.known_at != first.system_from
    assert first.resolution_id == RESOLUTION_ID
    assert first.assertion_id == ASSERTION_ID
    assert first.evidence_fragment_ids == (EVIDENCE_ID,)


def test_membership_projection_rejects_non_membership_predicate() -> None:
    with pytest.raises(ValueError, match="predicate industry.membership"):
        build_industry_membership_projection(_resolution(_assertion(field_name="project.state")))


def test_membership_projection_rejects_ambiguous_selected_resolution() -> None:
    other = _assertion().model_copy(update={"id": uuid4()})
    with pytest.raises(ValueError, match="exactly one selected assertion"):
        build_industry_membership_projection(_resolution(_assertion(), other))


def test_membership_projection_rejects_missing_or_invalid_industry_identity() -> None:
    with pytest.raises(ValueError, match="metadata.industry_node_id"):
        build_industry_membership_projection(_resolution(_assertion(metadata={"exposure_type": "direct"})))
    with pytest.raises(ValueError, match="must be a UUID"):
        build_industry_membership_projection(
            _resolution(_assertion(metadata={"industry_node_id": "not-a-uuid"}))
        )


def test_membership_projection_rejects_non_text_role() -> None:
    invalid = _assertion().model_copy(
        update={
            "value_type": FactValueKind.BOOLEAN,
            "normalized_boolean": True,
        }
    )
    with pytest.raises(ValueError, match="role must use text"):
        build_industry_membership_projection(_resolution(invalid))


def test_membership_projection_rejects_missing_supporting_evidence() -> None:
    invalid = _assertion().model_copy(
        update={
            "evidence": (
                FactEvidenceRef(
                    evidence_fragment_id=EVIDENCE_ID,
                    evidence_role=FactEvidenceRole.CONTEXT,
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="requires supporting Evidence"):
        build_industry_membership_projection(_resolution(invalid))


def test_membership_projection_rejects_lossy_catalog_date_conversion() -> None:
    invalid = _assertion(
        valid_time=TimeRange(
            start=datetime(2020, 1, 1, 12, 0, tzinfo=UTC),
            end=datetime(2030, 1, 1, tzinfo=UTC),
        )
    )
    with pytest.raises(ValueError, match="without losing source time precision"):
        build_industry_membership_projection(_resolution(invalid))


def test_unknown_onset_membership_does_not_invent_validity_start() -> None:
    assertion = _assertion(
        valid_time_kind=ValidTimeKind.UNKNOWN,
        valid_time=TimeRange(),
    ).model_copy(
        update={
            "observed_at": datetime(2021, 5, 31, tzinfo=UTC),
            "observed_at_precision": TemporalPrecision.DAY,
        }
    )
    projection = build_industry_membership_projection(_resolution(assertion))

    assert projection.valid_from is None
    assert projection.valid_to is None
    assert projection.known_at == KNOWN_AT


class _FakeResolutionReader:
    def __init__(self, resolution: ResolvedIndustryMembershipResolution) -> None:
        self.resolution = resolution

    async def industry_membership_resolution(
        self,
        resolution_id: UUID,
    ) -> ResolvedIndustryMembershipResolution:
        assert resolution_id == self.resolution.resolution_id
        return self.resolution


class _FakeProjectionWriter:
    def __init__(self) -> None:
        self.rows: list[IndustryMembershipProjection] = []

    async def append_industry_membership(
        self,
        projection: IndustryMembershipProjection,
    ) -> IndustryMembershipProjection:
        self.rows.append(projection)
        return projection


async def test_projection_service_composes_reader_and_writer_without_changing_semantics() -> None:
    resolution = _resolution(_assertion())
    writer = _FakeProjectionWriter()

    projected = await project_resolved_industry_membership(
        resolution_reader=_FakeResolutionReader(resolution),
        membership_writer=writer,
        resolution_id=RESOLUTION_ID,
    )

    assert writer.rows == [projected]
    assert projected.known_at == KNOWN_AT
    assert projected.system_from == RESOLVED_AT
