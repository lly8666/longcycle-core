from __future__ import annotations

import unittest
from pathlib import Path

from longcycle.application.memory_ingest import (
    apply_memory_repair_overlay,
    validate_memory_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]
MEMORY_DATA = ROOT / "research_data" / "memory"


class MemoryDatasetContractTest(unittest.TestCase):
    def test_all_v3_blind_jsonl_files_pass_typed_candidate_validation(self) -> None:
        files = sorted(MEMORY_DATA.glob("**/blind/**/*-v3.jsonl"))
        self.assertTrue(files, "expected at least one v3 memory dataset")

        failures: list[str] = []
        total_leads = 0
        repaired_files = 0
        for path in files:
            text = path.read_text(encoding="utf-8")
            repair_path = path.with_suffix(".repair.json")
            if repair_path.exists():
                text = apply_memory_repair_overlay(
                    text,
                    repair_path.read_text(encoding="utf-8"),
                    source_file=path.name,
                )
                repaired_files += 1

            result = validate_memory_jsonl(text)
            total_leads += len(result.accepted)
            for failure in result.failures:
                failures.append(f"{path}:{failure.line_no}: {failure.reason}")

        self.assertGreaterEqual(total_leads, 1)
        self.assertGreaterEqual(repaired_files, 1)
        self.assertEqual(failures, [], "\n".join(failures))

    def test_repair_overlay_does_not_rewrite_raw_memory_artifact(self) -> None:
        raw_path = next(MEMORY_DATA.glob("**/blind/DOWN-ESS/expectations-failures-metrics-v3.jsonl"))
        repair_path = raw_path.with_suffix(".repair.json")
        original = raw_path.read_text(encoding="utf-8")

        repaired = apply_memory_repair_overlay(
            original,
            repair_path.read_text(encoding="utf-8"),
            source_file=raw_path.name,
        )

        self.assertIn('"capacity_cycle"', original)
        self.assertNotIn('"capacity_cycle"', repaired)
        self.assertIn('"capital_cycle"', repaired)
        self.assertEqual(raw_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
