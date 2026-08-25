from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, time
from uuid import UUID, uuid4

from longcycle.domain.enums import EntityType, FactEvidenceRole, FactValueKind, ValidTimeKind
from longcycle.domain.models import FactAssertion, stable_uuid_exact
from longcycle.domain.orientation import (
    IndustryMembershipModelJudgmentRun,
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryMembershipSemanticJudgment,
    ResolvedIndustryMembershipResolution,
)
from longcycle.ports.orientation import (
    IndustryMembershipJudgmentRunWriter,
    IndustryMembershipProjectionWriter,
    IndustryMembershipResolutionReader,
    IndustryMembershipSemanticDecisionWriter,
    IndustryMembershipSemanticJudge,
)


_MEMBERSHIP_PREDICATE = "industry.membership"
_INDUSTRY_NODE_METADATA_KEY = "industry_node_id"
_EXPOSURE_METADATA_KEY = "exposure_type"
_STANDARD_DEEP_CONFIDENCE_THRESHOLD = 0.70


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


def _candidate_ids(resolution: ResolvedIndustryMembershipResolution) -> tuple[UUID, ...]:
    return tuple(sorted((item.id for item in resolution.selected_assertions), key=str))


def _assertion_hash(assertion: FactAssertion) -> str:
    rendered = json.dumps(
        assertion.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _input_hashes(resolution: ResolvedIndustryMembershipResolution) -> tuple[str, ...]:
    by_id = {item.id: item for item in resolution.selected_assertions}
    return tuple(_assertion_hash(by_id[item_id]) for item_id in _candidate_ids(resolution))


def _semantic_signature(assertion: FactAssertion) -> tuple[object, ...]:
    return (
        assertion.entity_type.value,
        str(assertion.entity_id),
        str(_industry_node_id(assertion)),
        assertion.value,
        _exposure_type(assertion),
        assertion.valid_time_kind.value,
        assertion.valid_time.start,
        assertion.valid_time.end,
    )


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
    if judgment.selected_assertion_id is not None and judgment.selected_assertion_id not in candidate_ids:
        raise ValueError("membership semantic judge selected an assertion outside the resolution")
    if any(item not in candidate_ids for item in judgment.alternative_assertion_ids):
        raise ValueError("membership semantic judge returned an alternative outside the resolution")


def _deep_trigger_reasons(
    resolution: ResolvedIndustryMembershipResolution,
    standard: IndustryMembershipSemanticJudgment,
) -> tuple[str, ...]:
    """Bounded deterministic triggers plus model self-escalation.

    The standard model does not get sole authority to decide whether a question deserves deep
    review. We only trigger on observable ambiguity/risk in the accepted candidate set or a
    low-confidence/non-materializable standard judgment; this intentionally avoids a blanket
    expensive-deep threshold.
    """

    reasons: list[str] = []
    if len(resolution.selected_assertions) > 1:
        signatures = {_semantic_signature(item) for item in resolution.selected_assertions}
        if len(signatures) > 1:
            reasons.append("candidate_semantic_definition_mismatch")
        if not standard.can_materialize or standard.selected_assertion_id is None:
            reasons.append("multiple_plausible_assertions")
    if standard.confidence < _STANDARD_DEEP_CONFIDENCE_THRESHOLD:
        reasons.append("low_standard_confidence")
    if standard.material_conflict_detected:
        reasons.append("model_reported_material_conflict")
    return tuple(dict.fromkeys(reasons))


def _judgment_run(
    *,
    resolution: ResolvedIndustryMembershipResolution,
    judgment: IndustryMembershipSemanticJudgment,
    triggered_deep: bool,
    deep_trigger_reasons: tuple[str, ...],
) -> IndustryMembershipModelJudgmentRun:
    return IndustryMembershipModelJudgmentRun(
        run_id=uuid4(),
        resolution_id=resolution.resolution_id,
        candidate_assertion_ids=_candidate_ids(resolution),
        input_assertion_hashes=_input_hashes(resolution),
        reasoning_mode=judgment.reasoning_mode,
        provider_name=judgment.provider_name,
        model_name=judgment.model_name,
        model_version=judgment.model_version,
        started_at=judgment.started_at,
        completed_at=judgment.completed_at,
        selected_assertion_id=judgment.selected_assertion_id,
        alternative_assertion_ids=judgment.alternative_assertion_ids,
        material_conflict_detected=judgment.material_conflict_detected,
        confidence=judgment.confidence,
        can_materialize=judgment.can_materialize,
        reasoning_summary=judgment.reasoning_summary,
        triggered_deep=triggered_deep,
        deep_trigger_reasons=deep_trigger_reasons,
        evidence_fragment_ids=_candidate_evidence(resolution),
    )


def build_industry_membership_projection(
    resolution: ResolvedIndustryMembershipResolution,
    decision: IndustryMembershipSemanticDecision,
) -> IndustryMembershipProjection:
    """Materialize the source assertion chosen by an auditable semantic decision."""

    for assertion in resolution.selected_assertions:
        _validate_membership_candidate(assertion)
    candidate_ids = _candidate_ids(resolution)
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
        system_from=decision.first_decided_at,
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
    judgment_run_writer: IndustryMembershipJudgmentRunWriter,
) -> IndustryMembershipSemanticDecision:
    """Persist every actual model execution and return the durable semantic conclusion."""

    for assertion in resolution.selected_assertions:
        _validate_membership_candidate(assertion)
    candidate_ids = _candidate_ids(resolution)
    candidate_set = set(candidate_ids)

    standard = await semantic_judge.judge_industry_membership(
        resolution,
        reasoning_mode="standard",
    )
    _validate_model_judgment(standard, expected_mode="standard", candidate_ids=candidate_set)
    deep_reasons = _deep_trigger_reasons(resolution, standard)
    standard_run = _judgment_run(
        resolution=resolution,
        judgment=standard,
        triggered_deep=bool(deep_reasons),
        deep_trigger_reasons=deep_reasons,
    )
    persisted_standard = await judgment_run_writer.append_industry_membership_judgment_run(
        standard_run
    )
    if persisted_standard != standard_run:
        raise RuntimeError("persisted standard membership judgment run changed execution provenance")

    runs = [standard_run]
    final = standard
    if deep_reasons:
        deep = await semantic_judge.judge_industry_membership(
            resolution,
            reasoning_mode="deep",
        )
        _validate_model_judgment(deep, expected_mode="deep", candidate_ids=candidate_set)
        deep_run = _judgment_run(
            resolution=resolution,
            judgment=deep,
            triggered_deep=True,
            deep_trigger_reasons=deep_reasons,
        )
        persisted_deep = await judgment_run_writer.append_industry_membership_judgment_run(deep_run)
        if persisted_deep != deep_run:
            raise RuntimeError("persisted deep membership judgment run changed execution provenance")
        runs.append(deep_run)
        final = deep
        if not deep.can_materialize or deep.selected_assertion_id is None:
            raise ValueError("deep membership semantic judgment could not resolve ambiguity safely")
    elif not standard.can_materialize or standard.selected_assertion_id is None:
        raise ValueError("standard membership semantic judgment did not produce a materializable choice")

    assert final.selected_assertion_id is not None
    decision_id = stable_uuid_exact(
        "industry-membership-semantic-decision-v2",
        str(resolution.resolution_id),
        *(str(item) for item in candidate_ids),
        str(final.selected_assertion_id),
        _MEMBERSHIP_PREDICATE,
    )
    first_decided_at = min(item.completed_at for item in runs)
    last_confirmed_at = max(item.completed_at for item in runs)
    return IndustryMembershipSemanticDecision(
        decision_id=decision_id,
        resolution_id=resolution.resolution_id,
        candidate_assertion_ids=candidate_ids,
        selected_assertion_id=final.selected_assertion_id,
        decision_summary=final.reasoning_summary,
        first_decided_at=first_decided_at,
        last_confirmed_at=last_confirmed_at,
        supporting_judgment_run_ids=tuple(item.run_id for item in runs),
        evidence_fragment_ids=_candidate_evidence(resolution),
    )


async def project_resolved_industry_membership(
    *,
    resolution_reader: IndustryMembershipResolutionReader,
    semantic_judge: IndustryMembershipSemanticJudge,
    judgment_run_writer: IndustryMembershipJudgmentRunWriter,
    decision_writer: IndustryMembershipSemanticDecisionWriter,
    membership_writer: IndustryMembershipProjectionWriter,
    resolution_id: UUID,
) -> IndustryMembershipProjection:
    resolution = await resolution_reader.industry_membership_resolution(resolution_id)
    proposed_decision = await resolve_industry_membership_semantics(
        resolution=resolution,
        semantic_judge=semantic_judge,
        judgment_run_writer=judgment_run_writer,
    )
    persisted_decision = await decision_writer.append_industry_membership_semantic_decision(
        proposed_decision
    )
    projection = build_industry_membership_projection(resolution, persisted_decision)
    persisted = await membership_writer.append_industry_membership(projection)
    if persisted != projection:
        raise RuntimeError("persisted industry membership projection changed validated semantics")
    return persisted
