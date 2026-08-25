from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from longcycle.domain.enums import EntityType, FactEvidenceRole, FactValueKind, ValidTimeKind
from longcycle.domain.models import FactAssertion, stable_uuid_exact
from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryMembershipSemanticJudgment,
    ResolvedIndustryMembershipResolution,
)
from longcycle.ports.orientation import (
    IndustryMembershipProjectionWriter,
    IndustryMembershipResolutionReader,
    IndustryMembershipSemanticDecisionWriter,
    IndustryMembershipSemanticJudge,
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


def _supporting_evidence(assertion: FactAssertion) -> tuple[UUID, ...]:
    evidence = tuple(
        sorted(
            (
                item.evidence_fragment_id
                for item in assertion.evidence
                if item.evidence_role == FactEvidenceRole.SUPPORTING
            ),
            key=str,
        )
    )
    if not evidence:
        raise ValueError("industry membership assertion requires supporting Evidence")
    return evidence


def _validate_membership_candidate(assertion: FactAssertion) -> None:
    """Reject structural corruption before asking a model to interpret semantics."""

    if assertion.field_name != _MEMBERSHIP_PREDICATE:
        raise ValueError("industry membership projection requires predicate industry.membership")
    if assertion.entity_type == EntityType.INDUSTRY:
        raise ValueError("industry membership assertion must identify an entity subject")
    if assertion.value_type != FactValueKind.TEXT:
        raise ValueError("industry membership role must use text Fact value semantics")
    if not assertion.value.strip() or assertion.value != assertion.value.strip():
        raise ValueError("industry membership role must be nonblank trimmed text")
    _industry_node_id(assertion)
    _exposure_type(assertion)
    _membership_dates(assertion)
    _supporting_evidence(assertion)


def _assertion_by_id(
    resolution: ResolvedIndustryMembershipResolution,
    assertion_id: UUID,
) -> FactAssertion:
    matches = [item for item in resolution.selected_assertions if item.id == assertion_id]
    if len(matches) != 1:
        raise ValueError("membership semantic decision selected an assertion outside the resolution")
    return matches[0]


def _candidate_evidence(
    resolution: ResolvedIndustryMembershipResolution,
) -> tuple[UUID, ...]:
    values: set[UUID] = set()
    for assertion in resolution.selected_assertions:
        values.update(_supporting_evidence(assertion))
    return tuple(sorted(values, key=str))


def _validate_model_judgment(
    judgment: IndustryMembershipSemanticJudgment,
    *,
    expected_mode: str,
    candidate_ids: set[UUID],
) -> None:
    if judgment.reasoning_mode != expected_mode:
        raise ValueError(
            f"membership semantic judge returned {judgment.reasoning_mode!r} for {expected_mode!r} request"
        )
    if judgment.selected_assertion_id is not None:
        if judgment.selected_assertion_id not in candidate_ids:
            raise ValueError("membership semantic judge selected an assertion outside the resolution")


def build_industry_membership_projection(
    resolution: ResolvedIndustryMembershipResolution,
    decision: IndustryMembershipSemanticDecision,
) -> IndustryMembershipProjection:
    """Materialize the source assertion chosen by an auditable model decision.

    CAP-0003 owns the accepted source-backed assertion set. CAP-0005 owns this catalog
    representation decision. The model may choose among accepted assertions but cannot
    invent a role, entity, industry, time or Evidence identity that is absent from the
    chosen assertion.
    """

    for assertion in resolution.selected_assertions:
        _validate_membership_candidate(assertion)
    candidate_ids = tuple(sorted((item.id for item in resolution.selected_assertions), key=str))
    if decision.resolution_id != resolution.resolution_id:
        raise ValueError("membership semantic decision references another resolution")
    if tuple(sorted(decision.candidate_assertion_ids, key=str)) != candidate_ids:
        raise ValueError("membership semantic decision candidates do not match selected resolution")

    assertion = _assertion_by_id(resolution, decision.selected_assertion_id)
    supporting_evidence = _supporting_evidence(assertion)
    industry_node_id = _industry_node_id(assertion)
    valid_from, valid_to = _membership_dates(assertion)
    exposure_type = _exposure_type(assertion)
    membership_id = stable_uuid_exact(
        "industry-membership-projection-v2",
        str(industry_node_id),
        str(assertion.entity_id),
        assertion.value,
        str(resolution.resolution_id),
        str(decision.decision_id),
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
        system_from=decision.decided_at,
        confidence=resolution.confidence,
        resolution_id=resolution.resolution_id,
        semantic_decision_id=decision.decision_id,
        assertion_id=assertion.id,
        evidence_fragment_ids=supporting_evidence,
    )


async def resolve_industry_membership_semantics(
    *,
    resolution: ResolvedIndustryMembershipResolution,
    semantic_judge: IndustryMembershipSemanticJudge,
) -> IndustryMembershipSemanticDecision:
    """Run standard model interpretation and automatically escalate conflicts to deep reasoning."""

    for assertion in resolution.selected_assertions:
        _validate_membership_candidate(assertion)
    candidate_ids = tuple(sorted((item.id for item in resolution.selected_assertions), key=str))
    candidate_set = set(candidate_ids)

    standard = await semantic_judge.judge_industry_membership(
        resolution,
        reasoning_mode="standard",
    )
    _validate_model_judgment(
        standard,
        expected_mode="standard",
        candidate_ids=candidate_set,
    )

    conflict_detected = standard.material_conflict_detected
    if conflict_detected:
        deep = await semantic_judge.judge_industry_membership(
            resolution,
            reasoning_mode="deep",
        )
        _validate_model_judgment(
            deep,
            expected_mode="deep",
            candidate_ids=candidate_set,
        )
        if not deep.can_materialize or deep.selected_assertion_id is None:
            raise ValueError(
                "deep membership semantic judgment could not resolve material-definition conflict"
            )
        final = deep
        reasoning_summary = (
            f"standard: {standard.reasoning_summary}\n"
            f"deep: {deep.reasoning_summary}"
        )
    else:
        if not standard.can_materialize or standard.selected_assertion_id is None:
            raise ValueError("standard membership semantic judgment did not produce a materializable choice")
        final = standard
        reasoning_summary = standard.reasoning_summary

    assert final.selected_assertion_id is not None
    decision_id = stable_uuid_exact(
        "industry-membership-semantic-decision-v1",
        str(resolution.resolution_id),
        *(str(item) for item in candidate_ids),
        str(final.selected_assertion_id),
        final.reasoning_mode,
        final.model_name,
        final.model_version or "none",
        "material-conflict" if conflict_detected else "no-material-conflict",
    )
    return IndustryMembershipSemanticDecision(
        decision_id=decision_id,
        resolution_id=resolution.resolution_id,
        candidate_assertion_ids=candidate_ids,
        selected_assertion_id=final.selected_assertion_id,
        reasoning_mode=final.reasoning_mode,
        material_conflict_detected=conflict_detected,
        reasoning_summary=reasoning_summary,
        model_name=final.model_name,
        model_version=final.model_version,
        decided_at=final.decided_at,
        evidence_fragment_ids=_candidate_evidence(resolution),
    )


async def project_resolved_industry_membership(
    *,
    resolution_reader: IndustryMembershipResolutionReader,
    semantic_judge: IndustryMembershipSemanticJudge,
    decision_writer: IndustryMembershipSemanticDecisionWriter,
    membership_writer: IndustryMembershipProjectionWriter,
    resolution_id: UUID,
) -> IndustryMembershipProjection:
    resolution = await resolution_reader.industry_membership_resolution(resolution_id)
    proposed_decision = await resolve_industry_membership_semantics(
        resolution=resolution,
        semantic_judge=semantic_judge,
    )
    persisted_decision = await decision_writer.append_industry_membership_semantic_decision(
        proposed_decision
    )
    projection = build_industry_membership_projection(resolution, persisted_decision)
    persisted = await membership_writer.append_industry_membership(projection)
    if persisted != projection:
        raise RuntimeError("persisted industry membership projection changed validated semantics")
    return persisted
