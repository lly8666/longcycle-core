from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from longcycle.application.industry_orientation import _membership_payload
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.orientation import IndustrySubjectMembershipRecord


def test_membership_payload_preserves_multi_run_semantic_audit() -> None:
    membership = IndustrySubjectMembershipRecord(
        membership_id=UUID("10000000-0000-0000-0000-000000000001"),
        industry_node_id=UUID("20000000-0000-0000-0000-000000000001"),
        subject=MemorySubjectRef(
            entity_id=UUID("30000000-0000-0000-0000-000000000001")
        ),
        canonical_name="Example Producer",
        entity_type="company",
        role="producer",
        exposure_type="direct",
        valid_from=date(2022, 1, 1),
        known_at=datetime(2022, 2, 1, tzinfo=UTC),
        system_from=datetime(2026, 8, 25, tzinfo=UTC),
        confidence=0.95,
        resolution_id=UUID("40000000-0000-0000-0000-000000000001"),
        semantic_decision_id=UUID("50000000-0000-0000-0000-000000000001"),
        semantic_decision_supporting_run_count=3,
        semantic_decision_latest_reasoning_mode="deep",
        evidence_fragment_ids=(UUID("60000000-0000-0000-0000-000000000001"),),
    )

    payload = _membership_payload(membership)

    assert payload["semantic_decision_supporting_run_count"] == 3
    assert payload["semantic_decision_latest_reasoning_mode"] == "deep"
    assert payload["semantic_decision_mode"] == "deep"
    assert payload["semantic_decision_mode"] == payload["semantic_decision_latest_reasoning_mode"]
