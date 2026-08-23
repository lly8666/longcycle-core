from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import require_aware_datetime
from longcycle.domain.open_states import CurrentResearchOpenStateBundle
from longcycle.ports.epistemic import EpistemicMemoryReader
from longcycle.ports.open_states import CurrentResearchOpenStateReader, RealityConflictReader
from longcycle.ports.orientation import IndustryOrientationReader

from .industry_orientation import _visible_memberships


def _subject_payload(subject: MemorySubjectRef) -> dict[str, str | None]:
    return {
        "subject_key": subject.key,
        "entity_id": str(subject.entity_id) if subject.entity_id is not None else None,
        "industry_node_id": (
            str(subject.industry_node_id) if subject.industry_node_id is not None else None
        ),
    }


def _current_overlay_payload(bundle: CurrentResearchOpenStateBundle) -> dict[str, Any]:
    return {
        "disagreements": [
            {
                "disagreement_case_id": str(item.disagreement_case_id),
                "lead_id": str(item.lead_id),
                "subject": _subject_payload(item.subject),
                "lead_summary": item.lead_summary,
                "claim_scope": item.claim_scope,
                "opened_reason": item.opened_reason,
                "current_disposition": (
                    item.current_disposition.value
                    if item.current_disposition is not None
                    else None
                ),
                "resolution_rationale": item.resolution_rationale,
                "supporting_evidence_ids": [str(value) for value in item.supporting_evidence_ids],
                "contradicting_evidence_ids": [
                    str(value) for value in item.contradicting_evidence_ids
                ],
                "research_recorded_at": item.research_recorded_at.isoformat(),
            }
            for item in bundle.disagreements
        ],
        "hypotheses": [
            {
                "assessment_id": str(item.assessment_id),
                "lead_id": str(item.lead_id),
                "subject": _subject_payload(item.subject),
                "lead_summary": item.lead_summary,
                "disposition": item.disposition.value,
                "direct_source_search_status": item.direct_source_search_status.value,
                "inference_confidence": item.inference_confidence,
                "reasoning_summary": item.reasoning_summary,
                "alternative_explanations": list(item.alternative_explanations),
                "falsification_conditions": list(item.falsification_conditions),
                "supporting_evidence_ids": [str(value) for value in item.supporting_evidence_ids],
                "contradicting_evidence_ids": [
                    str(value) for value in item.contradicting_evidence_ids
                ],
                "research_recorded_at": item.research_recorded_at.isoformat(),
            }
            for item in bundle.hypotheses
        ],
        "model_memory_coverage_gaps": [
            {
                "campaign_id": str(item.campaign_id),
                "snapshot_label": item.snapshot_label,
                "dimension_type": item.dimension_type,
                "dimension_key": item.dimension_key,
                "period_from": item.period_from.isoformat() if item.period_from else None,
                "period_to": item.period_to.isoformat() if item.period_to else None,
                "coverage_state": item.coverage_state,
                "notes": item.notes,
                "research_recorded_at": item.research_recorded_at.isoformat(),
            }
            for item in bundle.coverage_gaps
        ],
    }


async def build_researcher_open_state_view(
    *,
    catalog_reader: IndustryOrientationReader,
    memory_reader: EpistemicMemoryReader,
    conflict_reader: RealityConflictReader,
    current_research_reader: CurrentResearchOpenStateReader,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
    include_current_research: bool = False,
) -> dict[str, Any]:
    """Separate historical controversy from current research-only uncertainty.

    Membership visibility reuses the exact CAP-0005 orientation selector. Historical
    Judgment visibility comes from the typed no-lookahead snapshot. Reality conflict
    visibility is reconstructed from source assertion known-time, never conflict-case
    curation time. Current Memory/coverage state is opt-in and explicitly non-historical.
    """

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    catalog = await catalog_reader.industry_catalog(industry_node_id)
    memberships = _visible_memberships(catalog, knowledge_cutoff=checked)

    entity_subjects: dict[UUID, MemorySubjectRef] = {}
    current_labels: dict[str, str] = {
        f"industry:{industry_node_id}": catalog.industry.canonical_name,
    }
    for membership in memberships:
        assert membership.subject.entity_id is not None
        entity_subjects[membership.subject.entity_id] = membership.subject
        current_labels[membership.subject.key] = membership.canonical_name

    subjects = (
        MemorySubjectRef(industry_node_id=industry_node_id),
        *(entity_subjects[key] for key in sorted(entity_subjects, key=str)),
    )
    snapshot = await memory_reader.snapshot(subjects, knowledge_cutoff=checked)
    reality_disagreements = await conflict_reader.historical_source_disagreements(
        subjects,
        knowledge_cutoff=checked,
    )

    judgment_subjects = {
        item.judgment_id: item.subject for item in snapshot.judgments
    }
    judgment_contradictions: list[dict[str, Any]] = []
    for relation in snapshot.judgment_relations:
        if relation.relation_type != JudgmentRelationType.CONTRADICTS:
            continue
        from_subject = judgment_subjects.get(relation.from_judgment_id)
        to_subject = judgment_subjects.get(relation.to_judgment_id)
        judgment_contradictions.append(
            {
                "from_judgment_id": str(relation.from_judgment_id),
                "to_judgment_id": str(relation.to_judgment_id),
                "from_subject": _subject_payload(from_subject) if from_subject else None,
                "to_subject": _subject_payload(to_subject) if to_subject else None,
                "reason_summary": relation.reason_summary,
                "known_at": relation.known_at.isoformat(),
            }
        )

    judgment_counterarguments: list[dict[str, Any]] = []
    for rationale in snapshot.judgment_rationales:
        if rationale.rationale_kind != JudgmentRationaleKind.COUNTERARGUMENT:
            continue
        subject = judgment_subjects.get(rationale.judgment_id)
        judgment_counterarguments.append(
            {
                "rationale_id": str(rationale.rationale_id),
                "judgment_id": str(rationale.judgment_id),
                "subject": _subject_payload(subject) if subject else None,
                "summary": rationale.summary,
                "evidence_fragment_id": (
                    str(rationale.evidence_fragment_id)
                    if rationale.evidence_fragment_id is not None
                    else None
                ),
                "known_at": rationale.known_at.isoformat(),
            }
        )

    historical_conflicts = [
        {
            "conflict_case_id": str(item.conflict_case_id),
            "fact_key_id": str(item.fact_key_id),
            "subject": {
                **_subject_payload(item.subject),
                "current_catalog_label": current_labels.get(item.subject.key),
            },
            "predicate_code": item.predicate_code,
            "comparability_hash": item.comparability_hash,
            "archive_disagreement_known_at": item.archive_disagreement_known_at.isoformat(),
            "assertions": [
                {
                    "assertion_id": str(assertion.assertion_id),
                    "source_id": str(assertion.source_id),
                    "known_at": assertion.known_at.isoformat(),
                    "value_kind": assertion.value_kind,
                    "value": assertion.value,
                    "unit_code": assertion.unit_code,
                    "evidence_fragment_ids": [
                        str(value) for value in assertion.evidence_fragment_ids
                    ],
                }
                for assertion in item.assertions
            ],
            "current_archive_curation": {
                "severity": item.severity,
                "case_status": item.current_case_status,
                "research_case_opened_at": item.research_case_opened_at.isoformat(),
                "research_case_closed_at": (
                    item.research_case_closed_at.isoformat()
                    if item.research_case_closed_at is not None
                    else None
                ),
                "is_historical_market_knowledge": False,
            },
        }
        for item in reality_disagreements
    ]

    current_overlay: dict[str, Any] = {
        "included": include_current_research,
        "authority_class": "research_only_current_state",
        "is_historical_market_knowledge": False,
        "cutoff_filter_applied": False,
        "disagreements": [],
        "hypotheses": [],
        "model_memory_coverage_gaps": [],
    }
    if include_current_research:
        bundle = await current_research_reader.current_open_states(
            industry_node_id=industry_node_id,
            entity_ids=tuple(sorted(entity_subjects, key=str)),
        )
        current_overlay.update(_current_overlay_payload(bundle))

    return {
        "schema_version": "longcycle-researcher-open-states/v1",
        "knowledge_cutoff": checked.isoformat(),
        "industry": {
            "industry_node_id": str(industry_node_id),
            "canonical_name": catalog.industry.canonical_name,
        },
        "historical_at_cutoff": {
            "reality_source_disagreements": historical_conflicts,
            "judgment_contradictions": judgment_contradictions,
            "judgment_counterarguments": judgment_counterarguments,
        },
        "current_research_overlay": current_overlay,
        "boundary": {
            "membership_visibility_reuses_industry_orientation_owner": True,
            "historical_judgment_visibility_delegated_to_epistemic_snapshot": True,
            "reality_conflict_visibility_uses_member_source_known_at": True,
            "conflict_case_opened_at_is_not_historical_known_at": True,
            "current_research_overlay_is_opt_in": True,
            "current_research_overlay_is_not_cutoff_filtered": True,
            "model_memory_coverage_is_not_archive_absence": True,
            "absence_of_records_does_not_create_an_unknown_state": True,
            "not_found_is_not_false": True,
        },
    }
