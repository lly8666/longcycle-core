from __future__ import annotations

import unittest
from uuid import uuid4

from longcycle.application.memory_audit import adjudicate_memory_lead
from longcycle.domain.memory import (
    AuthorityClass,
    ClaimScope,
    EvidenceAssessment,
    EvidenceStance,
    MemoryAuditDisposition,
    MemoryLead,
    MemoryLeadKind,
)


class MemoryAuditTest(unittest.TestCase):
    def make_lead(self, *, scope: ClaimScope = ClaimScope.PROJECT_STATUS) -> MemoryLead:
        return MemoryLead(
            id=uuid4(),
            kind=MemoryLeadKind.PROJECT_PATTERN,
            summary="A project may have commissioned later than commonly reported.",
            claim_scope=scope,
            memory_confidence=0.8,
            importance_score=0.9,
            novelty_score=0.7,
            searchability_score=0.8,
            suggested_queries=("project commissioning annual report",),
        )

    def assessment(
        self,
        *,
        stance: EvidenceStance,
        authority: AuthorityClass,
        scope: ClaimScope = ClaimScope.PROJECT_STATUS,
        scope_match: bool = True,
        cluster: str | None = None,
    ) -> EvidenceAssessment:
        return EvidenceAssessment(
            evidence_fragment_id=uuid4(),
            stance=stance,
            authority_class=authority,
            claim_scope=scope,
            scope_match=scope_match,
            independent_cluster=cluster,
        )

    def test_memory_lead_is_never_publishable(self) -> None:
        result = adjudicate_memory_lead(self.make_lead(), [])
        self.assertFalse(result.lead_may_publish_as_fact)
        self.assertEqual(result.disposition, MemoryAuditDisposition.SEEK_PRIMARY)

    def test_secondary_web_contradiction_does_not_overrule_memory_lead(self) -> None:
        result = adjudicate_memory_lead(
            self.make_lead(),
            [
                self.assessment(
                    stance=EvidenceStance.CONTRADICTS,
                    authority=AuthorityClass.SECONDARY,
                )
            ],
        )
        self.assertEqual(result.disposition, MemoryAuditDisposition.SECONDARY_ONLY_CONTRADICTION)
        self.assertIn("retain_lead_and_search_for_claim_scoped_primary", result.reason_codes)

    def test_claim_scoped_primary_can_contradict_lead(self) -> None:
        evidence = self.assessment(
            stance=EvidenceStance.CONTRADICTS,
            authority=AuthorityClass.AUTHORITATIVE_PRIMARY,
        )
        result = adjudicate_memory_lead(self.make_lead(), [evidence])
        self.assertEqual(result.disposition, MemoryAuditDisposition.PRIMARY_CONTRADICTS_LEAD)
        self.assertEqual(result.contradicting_evidence_ids, (evidence.evidence_fragment_id,))
        self.assertFalse(result.lead_may_publish_as_fact)

    def test_primary_sources_that_disagree_create_conflict(self) -> None:
        supporting = self.assessment(
            stance=EvidenceStance.SUPPORTS,
            authority=AuthorityClass.AUTHORITATIVE_PRIMARY,
            cluster="company_filing",
        )
        contradicting = self.assessment(
            stance=EvidenceStance.CONTRADICTS,
            authority=AuthorityClass.AUTHORITATIVE_PRIMARY,
            cluster="government_approval",
        )
        result = adjudicate_memory_lead(self.make_lead(), [supporting, contradicting])
        self.assertEqual(result.disposition, MemoryAuditDisposition.AUTHORITATIVE_CONFLICT)
        self.assertIn("manual_review_required", result.reason_codes)

    def test_wrong_claim_scope_cannot_resolve_memory_lead(self) -> None:
        evidence = self.assessment(
            stance=EvidenceStance.CONTRADICTS,
            authority=AuthorityClass.AUTHORITATIVE_PRIMARY,
            scope=ClaimScope.MANAGEMENT_GUIDANCE,
            scope_match=False,
        )
        result = adjudicate_memory_lead(self.make_lead(), [evidence])
        self.assertEqual(result.disposition, MemoryAuditDisposition.SCOPE_MISMATCH)

    def test_multiple_secondary_sources_are_still_not_primary_verification(self) -> None:
        result = adjudicate_memory_lead(
            self.make_lead(),
            [
                self.assessment(
                    stance=EvidenceStance.SUPPORTS,
                    authority=AuthorityClass.REPUTABLE_SECONDARY,
                    cluster="newsroom_a",
                ),
                self.assessment(
                    stance=EvidenceStance.SUPPORTS,
                    authority=AuthorityClass.REPUTABLE_SECONDARY,
                    cluster="research_b",
                ),
            ],
        )
        self.assertEqual(result.disposition, MemoryAuditDisposition.SECONDARY_ONLY_SUPPORT)
        self.assertIn("multiple_independent_secondary_clusters", result.reason_codes)
        self.assertFalse(result.lead_may_publish_as_fact)

    def test_discovery_only_material_is_non_decisive(self) -> None:
        result = adjudicate_memory_lead(
            self.make_lead(),
            [
                self.assessment(
                    stance=EvidenceStance.CONTRADICTS,
                    authority=AuthorityClass.DISCOVERY_ONLY,
                )
            ],
        )
        self.assertEqual(result.disposition, MemoryAuditDisposition.SEEK_PRIMARY)

    def test_search_priority_is_investigation_priority_not_truth_probability(self) -> None:
        lead = self.make_lead()
        self.assertGreater(lead.search_priority, 0)
        self.assertLessEqual(lead.search_priority, 1)


if __name__ == "__main__":
    unittest.main()
