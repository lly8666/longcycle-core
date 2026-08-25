from __future__ import annotations

import json
import unittest

from longcycle.application.memory_ingest import (
    MemoryLeadCandidate,
    build_memory_candidate_repair_prompt,
    require_memory_lead_search_ready,
    validate_memory_jsonl,
)


class MemoryIngestTest(unittest.TestCase):
    def _valid_payload(self) -> dict[str, object]:
        return {
            "lead_id": "X-001",
            "shard_id": "UP-CHEMICALS",
            "pass_id": "test",
            "lead_kind": "mechanism",
            "claim_scope": "technical_specification",
            "memory_basis": "remembered_mechanism",
            "summary": "Different feedstock routes can have different conversion constraints.",
            "approximate_period": ["2020-01-01", "2024-12-31"],
            "memory_confidence": 0.8,
            "importance_score": 0.9,
            "novelty_score": 0.7,
            "searchability_score": 0.8,
            "precision_risk": "low",
            "entity_resolution_state": "stable",
            "uncertain_fields": [],
            "aliases_or_old_terms": ["conversion route"],
            "why_search_may_miss_it": "Project releases often omit comparable process fields.",
            "recalled_details": {},
            "possible_actors": [],
            "suggested_queries": ["lithium conversion route"],
            "disconfirmation_queries": ["all lithium conversion routes identical"],
            "suggested_source_types": ["technical report"],
            "disconfirmation_source_types": ["technical report"],
            "satellite_trigger": None,
            "relations": [],
        }

    def test_valid_candidate_is_accepted(self) -> None:
        candidate = MemoryLeadCandidate.model_validate(self._valid_payload())
        self.assertEqual(candidate.lead_kind.value, "mechanism")
        self.assertEqual(candidate.claim_scope.value, "technical_specification")
        self.assertTrue(candidate.search_delegation_ready)

    def test_fragmentary_recall_can_keep_an_open_ended_approximate_period(self) -> None:
        payload = self._valid_payload()
        payload["approximate_period"] = [None, "2022-12-31"]
        payload["precision_risk"] = "high"
        payload["uncertain_fields"] = ["approximate_period"]

        candidate = MemoryLeadCandidate.model_validate(payload)

        self.assertIsNone(candidate.approximate_period[0])
        self.assertEqual(candidate.approximate_period[1].isoformat(), "2022-12-31")
        self.assertEqual(candidate.precision_risk.value, "high")
        self.assertIn("approximate_period", candidate.uncertain_fields)

    def test_semantic_enum_mixup_is_rejected_not_silently_coerced(self) -> None:
        payload = self._valid_payload()
        payload["lead_kind"] = "technical_specification"
        result = validate_memory_jsonl(json.dumps(payload))
        self.assertFalse(result.is_clean)
        self.assertEqual(len(result.accepted), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertIn("lead_kind", result.failures[0].reason)

    def test_fragmentary_lead_without_complete_search_plan_is_preserved(self) -> None:
        payload = self._valid_payload()
        payload["disconfirmation_queries"] = []
        payload["suggested_source_types"] = []

        result = validate_memory_jsonl(json.dumps(payload))

        self.assertTrue(result.is_clean)
        self.assertEqual(len(result.accepted), 1)
        lead = result.accepted[0]
        self.assertFalse(lead.search_delegation_ready)
        self.assertEqual(
            lead.search_delegation_gaps,
            ("disconfirmation_queries", "suggested_source_types"),
        )

    def test_fragmentary_lead_may_omit_search_plan_fields_entirely(self) -> None:
        payload = self._valid_payload()
        for field in (
            "suggested_queries",
            "disconfirmation_queries",
            "suggested_source_types",
            "disconfirmation_source_types",
            "satellite_trigger",
            "relations",
        ):
            payload.pop(field)

        result = validate_memory_jsonl(json.dumps(payload))

        self.assertTrue(result.is_clean)
        lead = result.accepted[0]
        self.assertEqual(
            lead.search_delegation_gaps,
            (
                "suggested_queries",
                "disconfirmation_queries",
                "suggested_source_types",
                "disconfirmation_source_types",
            ),
        )
        self.assertIsNone(lead.satellite_trigger)
        self.assertEqual(lead.relations, ())

    def test_incomplete_search_plan_fails_at_delegation_boundary_not_atlas_admission(self) -> None:
        payload = self._valid_payload()
        payload["disconfirmation_queries"] = []
        candidate = MemoryLeadCandidate.model_validate(payload)

        with self.assertRaisesRegex(ValueError, "not ready for delegated evidence search"):
            require_memory_lead_search_ready(candidate)

    def test_complete_search_plan_is_ready_for_delegation(self) -> None:
        candidate = MemoryLeadCandidate.model_validate(self._valid_payload())
        require_memory_lead_search_ready(candidate)
        self.assertTrue(candidate.search_delegation_ready)
        self.assertEqual(candidate.search_delegation_gaps, ())

    def test_repair_prompt_forbids_new_research_content(self) -> None:
        prompt = build_memory_candidate_repair_prompt(
            raw_line='{"lead_kind":"technical_specification"}',
            validation_reason="invalid enum",
        )
        self.assertIn("STRUCTURAL REPAIR", prompt)
        self.assertIn("Do not add a new event", prompt)
        self.assertIn("failure_dead_end", prompt)
        self.assertIn("technical_specification", prompt)


if __name__ == "__main__":
    unittest.main()
