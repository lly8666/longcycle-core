from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.models import require_aware_datetime
from longcycle.domain.reality_candidates import RealityResearchCandidate
from longcycle.ports.reality_candidates import RealityResearchCandidateReader


def _candidate_payload(candidate: RealityResearchCandidate) -> dict[str, Any]:
    return {
        "assertion_id": str(candidate.assertion_id),
        "subject": candidate.subject.key,
        "canonical_name": candidate.canonical_name,
        "entity_type": candidate.entity_type,
        "predicate_code": candidate.predicate_code,
        "status": candidate.status,
        "raw_value": candidate.raw_value,
        "value_kind": candidate.value_kind,
        "unit_code": candidate.unit_code,
        "valid_time_kind": candidate.valid_time_kind,
        "valid_from": candidate.valid_from.isoformat() if candidate.valid_from is not None else None,
        "valid_to": candidate.valid_to.isoformat() if candidate.valid_to is not None else None,
        "source_known_at": candidate.source_known_at.isoformat(),
        "decision_known_at": candidate.decision_known_at.isoformat(),
        "confidence": candidate.confidence,
        "reconciliation_score": candidate.reconciliation_score,
        "reason_codes": list(candidate.reason_codes),
        "conflicting_assertion_ids": [str(value) for value in candidate.conflicting_assertion_ids],
        "evidence_fragment_ids": [str(value) for value in candidate.evidence_fragment_ids],
        "canonical": False,
        "research_only": True,
    }


async def build_researcher_reality_candidate_view(
    *,
    reader: RealityResearchCandidateReader,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
) -> dict[str, Any]:
    """Expose point-in-time REVIEW/QUARANTINE assertions without promoting them to Reality."""

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    candidates = await reader.candidates_for_industry(
        industry_node_id,
        knowledge_cutoff=checked,
    )

    visible: list[RealityResearchCandidate] = []
    for candidate in candidates:
        if candidate.industry_node_id != industry_node_id:
            raise ValueError("Reality candidate reader returned another industry")
        if candidate.source_known_at > checked or candidate.decision_known_at > checked:
            continue
        visible.append(candidate)

    visible.sort(
        key=lambda item: (
            item.decision_known_at,
            item.source_known_at,
            item.canonical_name.casefold(),
            item.predicate_code,
            str(item.assertion_id),
        )
    )
    return {
        "schema_version": "longcycle-researcher-reality-candidates/v1",
        "industry_node_id": str(industry_node_id),
        "knowledge_cutoff": checked.isoformat(),
        "candidate_count": len(visible),
        "candidates": [_candidate_payload(candidate) for candidate in visible],
        "boundary": {
            "source_backed_only": True,
            "review_and_quarantined_are_research_visible": True,
            "canonical_reality_unchanged": True,
            "candidate_is_never_canonical": True,
            "candidate_is_research_only": True,
            "source_known_at_respects_cutoff": True,
            "reconciliation_decision_known_at_respects_cutoff": True,
            "conflict_remains_owned_by_conflict_open_state": True,
            "no_threshold_relaxation": True,
        },
    }
