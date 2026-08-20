from __future__ import annotations

import unittest
from datetime import date

from longcycle.application.memory_index import build_shard_memory_index
from longcycle.application.memory_ingest import MemoryLeadCandidate
from longcycle.domain.memory import (
    ClaimScope,
    EntityResolutionState,
    MemoryBasis,
    MemoryLeadKind,
    PrecisionRisk,
)


def _lead(*, lead_id: str, shard_id: str = "MID-LFP") -> MemoryLeadCandidate:
    return MemoryLeadCandidate(
        lead_id=lead_id,
        shard_id=shard_id,
        pass_id="self-gap-batch1-v4",
        lead_kind=MemoryLeadKind.MECHANISM,
        claim_scope=ClaimScope.TECHNICAL_SPECIFICATION,
        memory_basis=MemoryBasis.REMEMBERED_MECHANISM,
        summary=f"summary {lead_id}",
        approximate_period=(date(2021, 1, 1), date(2022, 12, 31)),
        memory_confidence=0.9,
        importance_score=0.95,
        novelty_score=0.92,
        searchability_score=0.8,
        precision_risk=PrecisionRisk.HIGH,
        entity_resolution_state=EntityResolutionState.AMBIGUOUS,
        uncertain_fields=("exact_date",),
        aliases_or_old_terms=("old term",),
        why_search_may_miss_it="old vocabulary",
        recalled_details={"gap_reason": "earlier pass focused elsewhere", "private_detail": "drop"},
        possible_actors=("Actor A", "Actor B"),
        suggested_queries=("query",),
        disconfirmation_queries=("reverse query",),
        suggested_source_types=("primary",),
        disconfirmation_source_types=("primary",),
        satellite_trigger="BRIDGE-TEST",
        relations=(),
    )


class MemoryIndexTest(unittest.TestCase):
    def test_builds_compact_deterministic_index(self) -> None:
        index = build_shard_memory_index((_lead(lead_id="L2"), _lead(lead_id="L1")))

        self.assertEqual(index.shard_id, "MID-LFP")
        self.assertEqual(index.lead_count, 2)
        self.assertEqual(index.high_importance_count, 2)
        self.assertEqual(index.high_precision_risk_count, 2)
        self.assertEqual(index.ambiguous_entity_count, 2)
        self.assertEqual(index.unique_actor_count, 2)
        self.assertEqual(index.kind_counts, {"mechanism": 2})
        self.assertEqual(index.basis_counts, {"remembered_mechanism": 2})
        self.assertEqual(index.trigger_counts, {"BRIDGE-TEST": 2})
        self.assertEqual(index.year_counts, {"2021": 2, "2022": 2})
        self.assertEqual([entry.lead_id for entry in index.entries], ["L1", "L2"])
        self.assertEqual(index.entries[0].gap_reason, "earlier pass focused elsewhere")

        dumped = index.model_dump(mode="json")
        first = dumped["entries"][0]
        self.assertNotIn("suggested_queries", first)
        self.assertNotIn("recalled_details", first)
        self.assertNotIn("why_search_may_miss_it", first)

    def test_rejects_mixed_shards(self) -> None:
        with self.assertRaisesRegex(ValueError, "different shards"):
            build_shard_memory_index(
                (
                    _lead(lead_id="A", shard_id="MID-LFP"),
                    _lead(lead_id="B", shard_id="BAT-CELL"),
                )
            )

    def test_rejects_empty_index(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            build_shard_memory_index(())


if __name__ == "__main__":
    unittest.main()
