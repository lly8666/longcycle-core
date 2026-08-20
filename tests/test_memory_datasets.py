from __future__ import annotations

import unittest
from pathlib import Path

from longcycle.application.memory_ingest import validate_memory_jsonl


ROOT = Path(__file__).resolve().parents[1]
MEMORY_DATA = ROOT / "research_data" / "memory"


class MemoryDatasetContractTest(unittest.TestCase):
    def test_all_v3_blind_jsonl_files_pass_typed_candidate_validation(self) -> None:
        files = sorted(MEMORY_DATA.glob("**/blind/**/*-v3.jsonl"))
        self.assertTrue(files, "expected at least one v3 memory dataset")

        failures: list[str] = []
        total_leads = 0
        for path in files:
            result = validate_memory_jsonl(path.read_text(encoding="utf-8"))
            total_leads += len(result.accepted)
            for failure in result.failures:
                failures.append(f"{path}:{failure.line_no}: {failure.reason}")

        self.assertGreaterEqual(total_leads, 1)
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
