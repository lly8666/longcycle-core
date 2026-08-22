from __future__ import annotations

from uuid import UUID

import pytest

from longcycle.domain.memory import (
    DirectSourceSearchStatus,
    MemoryHypothesisAssessment,
    MemoryHypothesisDisposition,
)


def base_payload() -> dict[str, object]:
    return {
        "id": UUID(int=1),
        "lead_id": UUID(int=2),
        "disposition": MemoryHypothesisDisposition.INDIRECTLY_CORROBORATED,
        "direct_source_search_status": DirectSourceSearchStatus.EXHAUSTED_NOT_FOUND,
        "inference_confidence": 0.78,
        "reasoning_summary": (
            "The recalled event is consistent with archived downstream operating changes "
            "and a separate primary disclosure describing the prerequisite mechanism."
        ),
        "supporting_evidence_ids": (UUID(int=3), UUID(int=4)),
        "alternative_explanations": (
            "the downstream change could have resulted from a different operational cause",
        ),
        "falsification_conditions": (
            "a contemporaneous primary source shows the prerequisite never occurred",
        ),
        "search_receipt": {
            "query_families": ["old terminology", "actor plus mechanism"],
            "primary_targets_checked": ["issuer archive", "regulator archive"],
            "result": "direct claim source not recovered",
        },
        "assessor_name": "memory-hypothesis-audit",
        "assessor_version": "1.0.0",
    }


def test_indirectly_corroborated_memory_remains_research_only() -> None:
    assessment = MemoryHypothesisAssessment.model_validate(base_payload())

    assert assessment.disposition == MemoryHypothesisDisposition.INDIRECTLY_CORROBORATED
    assert assessment.may_publish_as_fact is False


def test_indirect_corroboration_requires_archived_indirect_evidence() -> None:
    payload = base_payload()
    payload["supporting_evidence_ids"] = ()

    with pytest.raises(ValueError, match="archived indirect evidence"):
        MemoryHypothesisAssessment.model_validate(payload)


def test_indirect_corroboration_requires_search_receipt_and_alternatives() -> None:
    payload = base_payload()
    payload["search_receipt"] = {}

    with pytest.raises(ValueError, match="search receipt"):
        MemoryHypothesisAssessment.model_validate(payload)

    payload = base_payload()
    payload["alternative_explanations"] = ()

    with pytest.raises(ValueError, match="alternative explanations"):
        MemoryHypothesisAssessment.model_validate(payload)


def test_model_memory_agreement_alone_cannot_satisfy_indirect_corroboration() -> None:
    payload = base_payload()
    payload["supporting_evidence_ids"] = ()
    payload["supporting_lead_ids"] = (UUID(int=5), UUID(int=6))

    with pytest.raises(ValueError, match="archived indirect evidence"):
        MemoryHypothesisAssessment.model_validate(payload)
