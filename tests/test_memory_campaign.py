from __future__ import annotations

import unittest
from datetime import date

from longcycle.application.memory_campaign import (
    RecallPassOutcome,
    RecallPassSpec,
    SaturationPolicy,
    VerificationSearchProgress,
    build_recall_pass_prompt,
    build_self_verification_prompt,
    evaluate_campaign_saturation,
    verification_depth_satisfied,
    verification_stop_decision,
)


class MemoryCampaignTest(unittest.TestCase):
    def test_recall_pass_prompt_keeps_fresh_search_out(self) -> None:
        prompt = build_recall_pass_prompt(
            industry="新能源锂电池",
            campaign_start=date(2019, 1, 1),
            campaign_end=date(2026, 12, 31),
            spec=RecallPassSpec(
                pass_id="MEM-FAILURES",
                family="failure_dead_end",
                questions=("Recall failed or delayed projects.",),
            ),
        )
        self.assertIn("Fresh web search results are forbidden", prompt)
        self.assertIn("long-tail leads", prompt)
        self.assertIn("What was it likely called at the time?", prompt)
        self.assertIn("approximate period", prompt)
        self.assertIn("instead of fabricating precision", prompt)
        self.assertIn("Do not invent citations, URLs, exact report titles, exact dates", prompt)
        self.assertIn("Do not discard a useful lead", prompt)
        self.assertIn("fake search plan", prompt)

    def test_atlas_only_pass_requires_atlas(self) -> None:
        spec = RecallPassSpec(
            pass_id="MEM-NEGATIVE-SPACE",
            family="negative_space",
            questions=("Find missing links.",),
            requires_atlas_only=True,
        )
        with self.assertRaises(ValueError):
            build_recall_pass_prompt(
                industry="新能源锂电池",
                campaign_start=date(2019, 1, 1),
                campaign_end=date(2026, 12, 31),
                spec=spec,
            )

    def test_self_verification_is_explicitly_search_enabled_but_cannot_rewrite_prior(self) -> None:
        prompt = build_self_verification_prompt(
            industry="新能源锂电池",
            sealed_atlas_digest="abc123",
            lead_packet="lead-1: possible historical pricing mechanism",
        )
        self.assertIn("may use fresh web search", prompt)
        self.assertIn("MUST NOT rewrite", prompt)
        self.assertIn("candidate URL is not Evidence", prompt)
        self.assertIn("not_found is not contradiction", prompt)

    def test_saturation_requires_low_marginal_novelty_and_no_major_gaps(self) -> None:
        outcomes = [
            RecallPassOutcome("a", "x", 3, 8, 1),
            RecallPassOutcome("b", "y", 2, 10, 0),
            RecallPassOutcome("c", "z", 1, 12, 1),
        ]
        result = evaluate_campaign_saturation(
            outcomes=outcomes,
            has_major_coverage_gaps=False,
            required_long_tail_families_missing=(),
            policy=SaturationPolicy(consecutive_low_novelty_passes=3),
        )
        self.assertTrue(result.saturated)

        blocked = evaluate_campaign_saturation(
            outcomes=outcomes,
            has_major_coverage_gaps=True,
            required_long_tail_families_missing=(),
        )
        self.assertFalse(blocked.saturated)
        self.assertIn("major_coverage_gaps_remain", blocked.reason_codes)

    def test_unresolved_search_cannot_claim_exhaustion_before_minimum_depth(self) -> None:
        shallow = VerificationSearchProgress(
            query_family_count=2,
            source_type_count=1,
            primary_domain_checked=False,
            reverse_query_done=False,
            citation_chase_required=True,
            citation_chase_done=False,
        )
        self.assertFalse(verification_depth_satisfied(shallow))
        unresolved = verification_stop_decision(
            resolution="unresolved",
            progress=shallow,
        )
        self.assertFalse(unresolved.allowed)
        self.assertEqual(unresolved.reason_code, "unresolved_minimum_depth_not_met")

        deep = VerificationSearchProgress(
            query_family_count=6,
            source_type_count=3,
            primary_domain_checked=True,
            reverse_query_done=True,
            citation_chase_required=True,
            citation_chase_done=True,
        )
        self.assertTrue(verification_depth_satisfied(deep))
        exhausted = verification_stop_decision(
            resolution="unresolved",
            progress=deep,
        )
        self.assertTrue(exhausted.allowed)
        self.assertEqual(exhausted.reason_code, "exhausted_but_unresolved")

    def test_authoritative_content_can_resolve_claim_without_search_quota(self) -> None:
        shallow = VerificationSearchProgress(
            query_family_count=2,
            source_type_count=1,
            primary_domain_checked=True,
            reverse_query_done=False,
            citation_chase_required=False,
            citation_chase_done=False,
        )
        support = verification_stop_decision(
            resolution="authoritative_support",
            progress=shallow,
        )
        contradiction = verification_stop_decision(
            resolution="authoritative_contradiction",
            progress=shallow,
        )
        self.assertTrue(support.allowed)
        self.assertEqual(support.reason_code, "authoritative_support")
        self.assertTrue(contradiction.allowed)
        self.assertEqual(contradiction.reason_code, "authoritative_contradiction")

    def test_high_impact_resolved_claim_still_requires_reverse_check(self) -> None:
        without_reverse = VerificationSearchProgress(
            query_family_count=2,
            source_type_count=1,
            primary_domain_checked=True,
            reverse_query_done=False,
            citation_chase_required=False,
            citation_chase_done=False,
        )
        blocked = verification_stop_decision(
            resolution="authoritative_support",
            progress=without_reverse,
            high_impact=True,
        )
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason_code, "high_impact_reverse_query_required")

        with_reverse = VerificationSearchProgress(
            query_family_count=2,
            source_type_count=1,
            primary_domain_checked=True,
            reverse_query_done=True,
            citation_chase_required=False,
            citation_chase_done=False,
        )
        resolved = verification_stop_decision(
            resolution="authoritative_support",
            progress=with_reverse,
            high_impact=True,
        )
        self.assertTrue(resolved.allowed)
        self.assertEqual(resolved.reason_code, "authoritative_support")


if __name__ == "__main__":
    unittest.main()
