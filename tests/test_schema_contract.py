from __future__ import annotations

import re
import unittest
from pathlib import Path

from longcycle.domain.enums import JobStage


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


class SchemaContractTest(unittest.TestCase):
    def test_migrations_are_ordered_nonempty_and_transaction_free(self) -> None:
        files = sorted(MIGRATIONS.glob("*.sql"))
        versions = [int(path.name[:4]) for path in files]
        self.assertEqual(versions, list(range(1, len(files) + 1)))
        for path in files:
            body = path.read_text(encoding="utf-8")
            self.assertTrue(body.strip(), path.name)
            self.assertIsNone(re.search(r"(?im)^\s*(BEGIN|COMMIT)\s*;", body), path.name)

    def test_database_and_python_job_stages_match(self) -> None:
        body = (MIGRATIONS / "0004_operations.sql").read_text(encoding="utf-8")
        match = re.search(r"CHECK \(stage IN \(([^)]+)\)\)", body)
        self.assertIsNotNone(match)
        assert match is not None
        sql_stages = set(re.findall(r"'([^']+)'", match.group(1)))
        self.assertEqual(sql_stages, {stage.value for stage in JobStage})

    def test_required_research_domains_exist(self) -> None:
        schema = "\n".join(path.read_text(encoding="utf-8") for path in sorted(MIGRATIONS.glob("*.sql")))
        required_tables = {
            "evidence.content_blobs",
            "evidence.evidence_fragments",
            "research.fact_assertions",
            "research.canonical_fact_versions",
            "research.metric_series",
            "research.capacity_projects",
            "research.event_clusters",
            "research.company_exposure_versions",
            "research.industry_relation_versions",
            "research.cycle_snapshots",
            "ops.collection_jobs",
            "ops.document_processing_completions",
            "ops.pipeline_checkpoints",
            "ops.outbox_events",
            "ops.cost_ledger",
        }
        for table in required_tables:
            self.assertIn(f"CREATE TABLE {table}", schema)
        self.assertIn("envelope_payload jsonb NOT NULL", schema)
        self.assertIn("normalizer_version text NOT NULL", schema)
        self.assertIn("ADD COLUMN raw_value text NOT NULL", schema)
        self.assertIn("ADD COLUMN supersedes_assertion_id uuid", schema)
        self.assertIn("THEN 'superseded'", schema)
        self.assertIn("DROP VIEW research.fact_assertions_with_status", schema)
        self.assertIn("evidence_fragments_material_check", schema)
        self.assertIn(") NOT VALID;", schema)
        self.assertIn("DISABLE TRIGGER fact_assertions_immutable", schema)
        self.assertIn("ADD COLUMN unit_dimension_name text", schema)
        self.assertIn("evidence_fragments_artifact_locator_unique", schema)


if __name__ == "__main__":
    unittest.main()
