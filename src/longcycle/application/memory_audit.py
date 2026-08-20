from __future__ import annotations

from collections.abc import Sequence

from longcycle.domain.memory import (
    AuthorityClass,
    EvidenceAssessment,
    EvidenceStance,
    MemoryAuditDisposition,
    MemoryAuditResult,
    MemoryLead,
)


_PRIMARY_CLASSES = frozenset(
    {
        AuthorityClass.AUTHORITATIVE_PRIMARY,
        AuthorityClass.PRIMARY_SELF_STATEMENT,
        AuthorityClass.METHODOLOGICAL_PRIMARY,
    }
)

_SECONDARY_CLASSES = frozenset(
    {
        AuthorityClass.REPUTABLE_SECONDARY,
        AuthorityClass.SECONDARY,
    }
)


def adjudicate_memory_lead(
    lead: MemoryLead,
    assessments: Sequence[EvidenceAssessment],
) -> MemoryAuditResult:
    """Compare an unsourced model-memory lead with archived evidence.

    This function resolves only the *research lead*. It never promotes model memory into
    a FactAssertion or JudgmentAssertion. Evidence must enter those pipelines separately.
    Search snippets and discovery-only pages are intentionally non-decisive.
    """

    if not assessments:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.SEEK_PRIMARY,
            reason_codes=("no_archived_evidence",),
        )

    scoped = [item for item in assessments if item.scope_match and item.claim_scope == lead.claim_scope]
    if not scoped:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.SCOPE_MISMATCH,
            reason_codes=("evidence_does_not_prove_same_claim_scope",),
        )

    primary_support = [
        item
        for item in scoped
        if item.authority_class in _PRIMARY_CLASSES and item.stance == EvidenceStance.SUPPORTS
    ]
    primary_contradict = [
        item
        for item in scoped
        if item.authority_class in _PRIMARY_CLASSES and item.stance == EvidenceStance.CONTRADICTS
    ]

    if primary_support and primary_contradict:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.AUTHORITATIVE_CONFLICT,
            reason_codes=("claim_scoped_primary_sources_disagree", "manual_review_required"),
            supporting_evidence_ids=tuple(item.evidence_fragment_id for item in primary_support),
            contradicting_evidence_ids=tuple(item.evidence_fragment_id for item in primary_contradict),
        )

    if primary_contradict:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.PRIMARY_CONTRADICTS_LEAD,
            reason_codes=("claim_scoped_primary_evidence_contradicts_memory",),
            contradicting_evidence_ids=tuple(item.evidence_fragment_id for item in primary_contradict),
        )

    if primary_support:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.PRIMARY_SUPPORTS_LEAD,
            reason_codes=("claim_scoped_primary_evidence_supports_memory",),
            supporting_evidence_ids=tuple(item.evidence_fragment_id for item in primary_support),
        )

    secondary_support = [
        item
        for item in scoped
        if item.authority_class in _SECONDARY_CLASSES and item.stance == EvidenceStance.SUPPORTS
    ]
    secondary_contradict = [
        item
        for item in scoped
        if item.authority_class in _SECONDARY_CLASSES and item.stance == EvidenceStance.CONTRADICTS
    ]

    if secondary_support and secondary_contradict:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.SEEK_PRIMARY,
            reason_codes=("secondary_sources_disagree", "do_not_majority_vote",),
            supporting_evidence_ids=tuple(item.evidence_fragment_id for item in secondary_support),
            contradicting_evidence_ids=tuple(item.evidence_fragment_id for item in secondary_contradict),
        )

    if secondary_contradict:
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.SECONDARY_ONLY_CONTRADICTION,
            reason_codes=(
                "memory_conflicts_with_secondary_only",
                "retain_lead_and_search_for_claim_scoped_primary",
            ),
            contradicting_evidence_ids=tuple(item.evidence_fragment_id for item in secondary_contradict),
        )

    if secondary_support:
        clusters = {item.independent_cluster for item in secondary_support if item.independent_cluster}
        reason_codes = ["secondary_support_is_not_verification"]
        if len(clusters) >= 2:
            reason_codes.append("multiple_independent_secondary_clusters")
        return MemoryAuditResult(
            disposition=MemoryAuditDisposition.SECONDARY_ONLY_SUPPORT,
            reason_codes=tuple(reason_codes),
            supporting_evidence_ids=tuple(item.evidence_fragment_id for item in secondary_support),
        )

    return MemoryAuditResult(
        disposition=MemoryAuditDisposition.SEEK_PRIMARY,
        reason_codes=("only_context_weak_match_or_discovery_material",),
    )
