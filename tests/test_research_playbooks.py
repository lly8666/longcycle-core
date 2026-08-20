from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DOCS = ROOT / "docs" / "research"


class ResearchPlaybookTest(unittest.TestCase):
    def test_agent_document_schema_is_valid_json_and_has_point_in_time_fields(self) -> None:
        schema = json.loads(
            (RESEARCH_DOCS / "agent-document-record.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["type"], "object")
        required = set(schema["required"])
        self.assertTrue(
            {
                "task_id",
                "published_at",
                "first_known_at",
                "url",
                "source_origin_role",
                "reality_rank",
                "expectation_rank",
                "material_roles",
            }.issubset(required)
        )
        self.assertIn("knowledge_cutoff", schema["properties"])
        self.assertIn("claimed_primary_source", schema["properties"])
        self.assertIn("independence_cluster_hint", schema["properties"])
        self.assertIn("claims", schema["properties"])
        self.assertIn("realityClaim", schema["$defs"])
        self.assertIn("judgmentClaim", schema["$defs"])

    def test_model_memory_lead_schema_marks_recall_as_unsourced(self) -> None:
        schema = json.loads(
            (RESEARCH_DOCS / "model-memory-lead.schema.json").read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        self.assertTrue(
            {
                "lead_kind",
                "claim_scope",
                "summary",
                "memory_confidence",
                "suggested_queries",
                "relations",
            }.issubset(required)
        )
        description = schema["properties"]["memory_confidence"]["description"]
        self.assertIn("NOT a probability", description)
        self.assertIn("cross_industry_dependency", schema["properties"]["lead_kind"]["enum"])

    def test_lithium_battery_work_packages_are_unique_and_actionable(self) -> None:
        manifest = json.loads(
            (RESEARCH_DOCS / "lithium-battery-work-packages.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], "longcycle-work-packages/v1")
        self.assertEqual(manifest["industry"], "新能源锂电池")

        packages = manifest["packages"]
        task_ids = [item["task_id"] for item in packages]
        self.assertEqual(len(task_ids), len(set(task_ids)))
        self.assertGreaterEqual(len(packages), 10)

        priorities = {"P0", "P1", "P2"}
        modes = {"discover", "extract-light"}
        for item in packages:
            self.assertRegex(item["task_id"], r"^LB-\d{3}$")
            self.assertIn(item["priority"], priorities)
            self.assertIn(item["mode"], modes)
            self.assertTrue(item["objective"].strip())
            self.assertTrue(item["preferred_sources"])
            self.assertTrue(item["query_templates"])
            self.assertTrue(item["must_return"])
            self.assertTrue(item["stop_condition"].strip())

    def test_first_wave_contains_reality_and_expectation_tasks(self) -> None:
        manifest = json.loads(
            (RESEARCH_DOCS / "lithium-battery-work-packages.json").read_text(encoding="utf-8")
        )
        p0 = [item for item in manifest["packages"] if item["priority"] == "P0"]
        titles = "\n".join(item["title"] for item in p0)
        self.assertIn("锂盐", titles)
        self.assertIn("动力电池", titles)
        self.assertIn("管理层", titles)
        self.assertIn("券商", titles)

    def test_lithium_memory_audits_are_separate_from_collection_agents(self) -> None:
        manifest = json.loads(
            (RESEARCH_DOCS / "lithium-battery-memory-audits.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], "longcycle-memory-audits/v1")
        self.assertEqual(manifest["industry"], "新能源锂电池")
        self.assertEqual(manifest["output_schema"], "docs/research/model-memory-lead.schema.json")
        audits = manifest["audits"]
        audit_ids = [item["audit_id"] for item in audits]
        self.assertEqual(len(audit_ids), len(set(audit_ids)))
        self.assertGreaterEqual(len(audits), 5)
        self.assertTrue(any("pricing_and_contracts" in item["must_use_lenses"] for item in audits))
        self.assertTrue(any("negative_space" in item["must_use_lenses"] for item in audits))

    def test_memory_audit_and_authority_playbooks_define_hard_boundaries(self) -> None:
        memory = (RESEARCH_DOCS / "model-memory-audit.md").read_text(encoding="utf-8")
        authority = (RESEARCH_DOCS / "source-authority-policy.md").read_text(encoding="utf-8")

        self.assertIn("Blind Recall", memory)
        self.assertIn("Negative Space", memory)
        self.assertIn("Model memory may challenge the archive", memory)
        self.assertIn("secondary_only_contradiction", memory)
        self.assertIn("claim-scoped authority", authority)
        self.assertIn("Search Result 不是 Evidence", authority)
        self.assertIn("authoritative_conflict", authority)
        self.assertIn("不能简单多数投票", authority)


if __name__ == "__main__":
    unittest.main()
