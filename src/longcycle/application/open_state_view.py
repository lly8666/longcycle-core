from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.application.researcher_interpretation import model_analysis_policy
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.open_states import CurrentResearchOpenStateBundle
from longcycle.ports.epistemic import EpistemicMemoryReader
from longcycle.ports.open_states import CurrentResearchOpenStateReader, RealityConflictReader
from longcycle.ports.orientation import IndustryOrientationReader

from .industry_orientation import _load_industry_subject_universe, _memory_counts
from .research_enrichment import (
    EnrichmentComponentResult,
    ExpectedResearchEnrichmentUnavailable,
    available_component,
    defect,
    overall_status,
    unavailable_component,
)


def _subject_payload(subject: MemorySubjectRef) -> dict[str, str | None]:
    return {
        "subject_key": subject.key,
        "entity_id": str(subject.entity_id) if subject.entity_id is not None else None,
        "industry_node_id": (
            str(subject.industry_node_id) if subject.industry_node_id is not None else None
        ),
    }


def _subject_with_current_label_payload(
    subject: MemorySubjectRef,
    current_catalog_label: str | None,
) -> dict[str, str | None]:
    payload = _subject_payload(subject)
    payload["current_catalog_label"] = current_catalog_label
    return payload


def _current_overlay_payload(bundle: CurrentResearchOpenStateBundle) -> dict[str, Any]:
    return {
        "available": True,
        "degraded": False,
        "availability_status": "AVAILABLE",
        "failure": None,
        "analysis_policy": model_analysis_policy(),
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
                "certainty_class": "model_judgment",
                "authority_class": "research_only_current_state",
                "is_canonical_truth": False,
                "is_historical_market_knowledge": False,
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


def _archive_coverage_payload(
    *,
    subjects: tuple[MemorySubjectRef, ...],
    current_labels: dict[str, str],
    memory_counts: dict[str, dict[str, int]],
    membership_subject_keys: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subject in subjects:
        counts = memory_counts.get(
            subject.key,
            {"reality": 0, "judgments": 0, "outcomes": 0},
        )
        memory_record_count = counts["reality"] + counts["judgments"] + counts["outcomes"]
        has_membership = subject.key in membership_subject_keys
        has_grounded_record = memory_record_count > 0 or has_membership
        rows.append(
            {
                "subject": _subject_with_current_label_payload(
                    subject,
                    current_labels.get(subject.key),
                ),
                "archive_status": (
                    "grounded_records_present" if has_grounded_record else "no_grounded_record"
                ),
                "memory_counts": counts,
                "has_grounded_membership": has_membership,
                "world_state_inference": "none",
                "research_interpretation": (
                    "archive contains grounded material"
                    if has_grounded_record
                    else "research coverage may be incomplete or unresearched; absence is not a claim that the world state is unknown or false"
                ),
            }
        )
    return rows


def _component_payloads(
    components: list[EnrichmentComponentResult] | tuple[EnrichmentComponentResult, ...],
) -> dict[str, Any]:
    rendered = [item.as_payload() for item in components]
    availability = overall_status(list(components))
    return {
        "status": "degraded" if availability == "UNAVAILABLE_EXPECTED" else "complete",
        "availability_status": availability,
        "components": rendered,
        "failures": [item for item in rendered if item["status"] == "UNAVAILABLE_EXPECTED"],
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
    """Separate historical controversy, archive coverage and current research analysis.

    Historical truth-bearing reads remain fail-closed. Optional research lanes degrade only
    for explicitly classified expected-unavailability conditions. Programming, SQL, schema,
    payload and contract defects raise instead of being silently reported as provider downtime.
    Current model hypotheses remain MODEL/JUDGMENT, never canonical Reality or historical
    market knowledge.
    """

    checked, catalog, memberships, discoveries, entity_subjects, enrichment_components = (
        await _load_industry_subject_universe(
            catalog_reader=catalog_reader,
            industry_node_id=industry_node_id,
            knowledge_cutoff=knowledge_cutoff,
        )
    )

    current_labels: dict[str, str] = {
        f"industry:{industry_node_id}": catalog.industry.canonical_name,
    }
    for membership in memberships:
        current_labels[membership.subject.key] = membership.canonical_name
    for discovery in discoveries:
        current_labels.setdefault(discovery.subject.key, discovery.canonical_name)

    subjects = (
        MemorySubjectRef(industry_node_id=industry_node_id),
        *(entity_subjects[key] for key in sorted(entity_subjects, key=str)),
    )
    snapshot = await memory_reader.snapshot(subjects, knowledge_cutoff=checked)
    reality_disagreements = await conflict_reader.historical_source_disagreements(
        subjects,
        knowledge_cutoff=checked,
    )

    judgment_subjects = {item.judgment_id: item.subject for item in snapshot.judgments}
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
            "subject": _subject_with_current_label_payload(
                item.subject,
                current_labels.get(item.subject.key),
            ),
            "predicate_code": item.predicate_code,
            "comparability_hash": item.comparability_hash,
            "archive_disagreement_known_at": item.archive_disagreement_known_at.isoformat(),
            "assertions": [
                {
                    "assertion_id": str(assertion.assertion_id),
                    "source_id": str(assertion.source_id),
                    "source_cluster": assertion.source_cluster,
                    "source_independence_key": assertion.source_independence_key,
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
        "available": None if not include_current_research else True,
        "degraded": False,
        "availability_status": None if not include_current_research else "AVAILABLE",
        "failure": None,
        "authority_class": "research_only_current_state",
        "is_historical_market_knowledge": False,
        "cutoff_filter_applied": False,
        "analysis_policy": model_analysis_policy(),
        "disagreements": [],
        "hypotheses": [],
        "model_memory_coverage_gaps": [],
    }
    all_components = list(enrichment_components)
    if include_current_research:
        component_name = "current_research_open_states"
        try:
            bundle = await current_research_reader.current_open_states(
                industry_node_id=industry_node_id,
            )
        except ExpectedResearchEnrichmentUnavailable as exc:
            component = unavailable_component(component_name, exc)
            failure = component.as_payload()
            current_overlay.update(
                {
                    "available": False,
                    "degraded": True,
                    "availability_status": "UNAVAILABLE_EXPECTED",
                    "failure": failure,
                }
            )
            all_components.append(component)
        except Exception as exc:
            raise defect(component_name, exc) from exc
        else:
            result_count = (
                len(bundle.disagreements) + len(bundle.hypotheses) + len(bundle.coverage_gaps)
            )
            all_components.append(available_component(component_name, result_count=result_count))
            current_overlay.update(_current_overlay_payload(bundle))

    counts = _memory_counts(snapshot)
    membership_subject_keys = {item.subject.key for item in memberships}
    archive_coverage = _archive_coverage_payload(
        subjects=subjects,
        current_labels=current_labels,
        memory_counts=counts,
        membership_subject_keys=membership_subject_keys,
    )

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
        "archive_research_coverage": archive_coverage,
        "current_research_overlay": current_overlay,
        "research_enrichment": _component_payloads(all_components),
        "boundary": {
            "subject_universe_reuses_industry_orientation_owner": True,
            "subject_universe_includes_deterministic_entailment_when_available": True,
            "entailed_discovery_does_not_create_membership_or_role": True,
            "membership_visibility_reuses_industry_orientation_owner": True,
            "historical_memory_and_conflict_reads_fail_closed": True,
            "optional_research_enrichments_degrade_gracefully": True,
            "expected_unavailability_is_distinct_from_empty_result": True,
            "unexpected_enrichment_defects_raise": True,
            "optional_capabilities_are_explicitly_declared": True,
            "historical_judgment_visibility_delegated_to_epistemic_snapshot": True,
            "reality_conflict_visibility_uses_member_source_known_at": True,
            "reality_source_independence_reuses_fact_source_cluster": True,
            "conflict_case_opened_at_is_not_historical_known_at": True,
            "current_research_overlay_is_explicitly_separate_from_historical_cutoff": True,
            "current_research_overlay_is_not_cutoff_filtered": True,
            "current_research_scope_uses_own_run_provenance": True,
            "model_judgment_lane_allows_explicit_analysis": True,
            "model_judgment_never_promotes_to_canonical_truth": True,
            "model_memory_coverage_uses_latest_sealed_campaign": True,
            "model_memory_coverage_respects_seal_time": True,
            "model_memory_coverage_is_not_archive_absence": True,
            "archive_absence_is_exposed_as_research_coverage": True,
            "absence_of_records_does_not_create_an_unknown_state": True,
            "not_found_is_not_false": True,
        },
    }
