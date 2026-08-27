from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from longcycle.application.memory_index import (
    build_shard_memory_index_from_directory,
    write_shard_memory_index,
)

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "research_data" / "memory" / "lithium-battery" / "2026-08-21-gpt-5.6-sol"


class MemoryIndexPersistenceTest(unittest.TestCase):
    def test_real_down_ess_shard_applies_repair_overlay_before_indexing(self) -> None:
        index = build_shard_memory_index_from_directory(CAMPAIGN / "blind" / "DOWN-ESS")

        self.assertEqual(index.shard_id, "DOWN-ESS")
        self.assertEqual(index.lead_count, len(index.entries))
        self.assertEqual(
            tuple(item.lead_id for item in index.entries),
            tuple(sorted(item.lead_id for item in index.entries)),
        )
        repaired = next(item for item in index.entries if item.lead_id == "ESS-C006")
        self.assertEqual(repaired.lead_kind.value, "capital_cycle")

    def test_persisted_index_is_deterministic_and_rebuildable(self) -> None:
        shard_dir = CAMPAIGN / "blind" / "MID-ELECTROLYTE"
        with tempfile.TemporaryDirectory(prefix="longcycle-memory-index-") as temporary:
            output = Path(temporary) / "MID-ELECTROLYTE.json"
            first = write_shard_memory_index(shard_dir, output)
            first_payload = output.read_text(encoding="utf-8")
            second = write_shard_memory_index(shard_dir, output)
            second_payload = output.read_text(encoding="utf-8")

        self.assertEqual(first, second)
        self.assertEqual(first_payload, second_payload)
        self.assertEqual(first.lead_count, 34)
        self.assertNotIn("suggested_queries", first_payload)
        self.assertNotIn("disconfirmation_queries", first_payload)
        self.assertNotIn("suggested_source_types", first_payload)


if __name__ == "__main__":
    unittest.main()
