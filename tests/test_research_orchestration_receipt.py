from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from longcycle.application.research_orchestration import execute_research_orchestration_receipt


class ResearchOrchestrationReceiptTest(unittest.TestCase):
    def test_failure_before_execution_still_writes_machine_readable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "receipt.json"
            payload = execute_research_orchestration_receipt(
                repo_root=root,
                spec_path=root / "missing-spec.json",
                source_pack_path=root / "missing-pack.zip",
                work_dir=root / "work",
                output_path=output,
                skip_db_upgrade=True,
            )

            self.assertFalse(payload["ok"])
            self.assertIn("FileNotFoundError", payload["error"])
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted, payload)


if __name__ == "__main__":
    unittest.main()
