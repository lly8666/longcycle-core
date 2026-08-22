from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.domain.enums import FactEvidenceRole, FactStatus, FactValueKind, QualityGrade, SourceKind
from longcycle.domain.models import FactDimensions


class PostgresMappingTest(unittest.TestCase):
    def test_connectors_of_one_publisher_share_the_fallback_cluster(self) -> None:
        publisher_id = uuid4()

        def row(connector_id):  # type: ignore[no-untyped-def]
            return {
                "id": connector_id,
                "publisher_id": publisher_id,
                "name": str(connector_id),
                "source_kind": SourceKind.REGULATOR.value,
                "plugin_name": "http_document",
                "quality_grade": QualityGrade.A.value,
                "publisher_domain": "example.test",
                "rate_limit_per_minute": 30,
                "enabled": True,
                "config": {},
                "independence_cluster": None,
            }

        first = PostgresResearchRepository._source_from_row(row(uuid4()))
        second = PostgresResearchRepository._source_from_row(row(uuid4()))

        self.assertEqual(first.syndication_cluster, f"publisher:{publisher_id}")
        self.assertEqual(first.syndication_cluster, second.syndication_cluster)

    def test_assertion_roundtrip_preserves_raw_value_supersession_and_evidence(self) -> None:
        industry_id = uuid4()
        supersedes_id = uuid4()
        evidence_id = uuid4()
        dimensions = FactDimensions()
        row = {
            "id": uuid4(),
            "subject_entity_id": None,
            "subject_industry_node_id": industry_id,
            "subject_entity_type": None,
            "predicate_code": "capacity.nameplate",
            "value_kind": FactValueKind.NUMERIC.value,
            "raw_value": "2.5 万吨",
            "value_numeric": Decimal("25000"),
            "value_text": None,
            "value_boolean": None,
            "value_date": None,
            "value_entity_id": None,
            "value_json": None,
            "unit_code": "t",
            "canonical_payload": dimensions.canonical_payload,
            "dimensions_complete": True,
            "valid_time_kind": "period",
            "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
            "valid_to": datetime(2027, 1, 1, tzinfo=UTC),
            "observed_at": None,
            "source_published_at": datetime(2026, 2, 1, tzinfo=UTC),
            "first_known_at": datetime(2026, 2, 2, tzinfo=UTC),
            "source_connector_id": uuid4(),
            "document_version_id": uuid4(),
            "evidence_refs": [
                {
                    "evidence_fragment_id": evidence_id,
                    "evidence_role": FactEvidenceRole.SUPPORTING.value,
                }
            ],
            "extraction_run_id": uuid4(),
            "extractor_name": "test",
            "extractor_version": "1",
            "normalizer_name": "assertion_normalizer",
            "normalizer_version": "2.0.0",
            "source_cluster": "publisher:test",
            "confidence": 0.9,
            "source_quality": 1.0,
            "extraction_certainty": 0.9,
            "entity_match": 1.0,
            "time_unit_completeness": 1.0,
            "corroboration": 0.0,
            "freshness": 1.0,
            "conflict_penalty": 0.0,
            "high_impact": False,
            "status": FactStatus.CANDIDATE.value,
            "supersedes_assertion_id": supersedes_id,
            "metadata": {},
        }

        restored = PostgresResearchRepository._assertion_from_row(row)

        self.assertEqual(restored.value, "2.5 万吨")
        self.assertEqual(restored.normalized_number, Decimal("25000"))
        self.assertEqual(restored.supersedes_id, supersedes_id)
        self.assertEqual(restored.evidence[0].evidence_fragment_id, evidence_id)
        self.assertEqual(restored.evidence[0].evidence_role, FactEvidenceRole.SUPPORTING)


if __name__ == "__main__":
    unittest.main()
