from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from longcycle.domain.enums import EntityType, FactEvidenceRole, FactValueKind, ValidTimeKind
from longcycle.domain.models import FactAssertion, stable_uuid_exact
from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    ResolvedIndustryMembershipResolution,
)
from longcycle.ports.orientation import (
    IndustryMembershipProjectionWriter,
    IndustryMembershipResolutionReader,
)


_MEMBERSHIP_PREDICATE = "industry.membership"
_INDUSTRY_NODE_METADATA_KEY = "industry_node_id"
_EXPOSURE_METADATA_KEY = "exposure_type"


def _industry_node_id(assertion: FactAssertion) -> UUID:
    raw = assertion.metadata.get(_INDUSTRY_NODE_METADATA_KEY)
    if raw is None:
        raise ValueError("industry.membership assertion must declare metadata.industry_node_id")
    try:
        return UUID(str(raw))
    except (TypeError, ValueError) as exc:
        raise ValueError("industry.membership metadata.industry_node_id must be a UUID") from exc


def _exposure_type(assertion: FactAssertion) -> str | None:
    raw = assertion.metadata.get(_EXPOSURE_METADATA_KEY)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip() or raw != raw.strip():
        raise ValueError("industry.membership metadata.exposure_type must be nonblank trimmed text")
    return raw


def _lossless_date_boundary(value: date | datetime | None, *, label: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        utc_value = value.astimezone(UTC)
        if utc_value.timetz().replace(tzinfo=None) != time.min:
            raise ValueError(
                f"{label} cannot be projected to catalog date without losing source time precision"
            )
        return utc_value.date()
    return value


def _membership_dates(assertion: FactAssertion) -> tuple[date | None, date | None]:
    if assertion.valid_time_kind in {ValidTimeKind.TIMELESS, ValidTimeKind.UNKNOWN}:
        if assertion.valid_time.start is not None or assertion.valid_time.end is not None:
            raise ValueError("non-period membership assertion cannot carry validity bounds")
        return None, None
    if assertion.valid_time_kind != ValidTimeKind.PERIOD:
        raise ValueError(f"unsupported membership valid_time_kind: {assertion.valid_time_kind.value}")
    return (
        _lossless_date_boundary(assertion.valid_time.start, label="membership valid_from"),
        _lossless_date_boundary(assertion.valid_time.end, label="membership valid_to"),
    )


def build_industry_membership_projection(
    resolution: ResolvedIndustryMembershipResolution,
) -> IndustryMembershipProjection:
    """Materialize one unambiguous selected Fact without deciding Fact truth again.

    CAP-0003 owns reconciliation and selected-resolution truth.  This function only
    validates that the selected Fact can be represented losslessly by the existing
    orientation catalog schema.  CAP-0005 remains the historical visibility owner.
    """

    if len(resolution.selected_assertions) != 1:
        raise ValueError(
            "industry membership projection requires exactly one selected assertion"
        )
    assertion = resolution.selected_assertions[0]
    if assertion.field_name != _MEMBERSHIP_PREDICATE:
        raise ValueError(
            "industry membership projection requires predicate industry.membership"
        )
    if assertion.entity_type == EntityType.INDUSTRY:
        raise ValueError("industry membership assertion must identify an entity subject")
    if assertion.value_type != FactValueKind.TEXT:
        raise ValueError("industry membership role must use text Fact value semantics")
    if not assertion.value.strip() or assertion.value != assertion.value.strip():
        raise ValueError("industry membership role must be nonblank trimmed text")

    supporting_evidence = tuple(
        sorted(
            (
                item.evidence_fragment_id
                for item in assertion.evidence
                if item.evidence_role == FactEvidenceRole.SUPPORTING
            ),
            key=str,
        )
    )
    if not supporting_evidence:
        raise ValueError("industry membership assertion requires supporting Evidence")

    industry_node_id = _industry_node_id(assertion)
    valid_from, valid_to = _membership_dates(assertion)
    exposure_type = _exposure_type(assertion)
    membership_id = stable_uuid_exact(
        "industry-membership-projection-v1",
        str(industry_node_id),
        str(assertion.entity_id),
        assertion.value,
        str(resolution.resolution_id),
    )
    return IndustryMembershipProjection(
        membership_id=membership_id,
        industry_node_id=industry_node_id,
        entity_id=assertion.entity_id,
        role=assertion.value,
        exposure_type=exposure_type,
        valid_from=valid_from,
        valid_to=valid_to,
        known_at=assertion.known_at,
        system_from=resolution.resolved_at,
        confidence=resolution.confidence,
        resolution_id=resolution.resolution_id,
        assertion_id=assertion.id,
        evidence_fragment_ids=supporting_evidence,
    )


async def project_resolved_industry_membership(
    *,
    resolution_reader: IndustryMembershipResolutionReader,
    membership_writer: IndustryMembershipProjectionWriter,
    resolution_id: UUID,
) -> IndustryMembershipProjection:
    resolution = await resolution_reader.industry_membership_resolution(resolution_id)
    projection = build_industry_membership_projection(resolution)
    persisted = await membership_writer.append_industry_membership(projection)
    if persisted != projection:
        raise RuntimeError("persisted industry membership projection changed validated semantics")
    return persisted
