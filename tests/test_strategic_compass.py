from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPASS = ROOT / "STRATEGIC_COMPASS.md"
CONTINUE = ROOT / "CONTINUE_HERE.md"
AGENTS = ROOT / "AGENTS.md"


class StrategicCompassContractTest(unittest.TestCase):
    def test_compass_preserves_end_state_and_benchmark(self) -> None:
        text = COMPASS.read_text(encoding="utf-8")

        required_fragments = (
            "历史本身就是分析",
            "Reality + Expectation + Outcome",
            "point-in-time",
            "锂电是“证明场”，不是产品终点",
            "Memory Atlas",
            "Memory-first, Evidence-final",
            "Source-first, Archive-now",
            "Strategic Alignment Gate",
            "下一步“大方向”永远比当前 TODO 高一级",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, text)

    def test_compass_explicitly_rejects_local_optima(self) -> None:
        text = COMPASS.read_text(encoding="utf-8")

        for fragment in (
            "generic platform",
            "Memory Lead 数字更大",
            "schema 完美",
            "修 Ruff",
            "提前污染 blind memory",
            "只做历史抢救，忘记今天的 source-first/archive-now",
        ):
            self.assertIn(fragment, text)

    def test_bootstrap_reads_compass_before_todo_execution(self) -> None:
        continue_text = CONTINUE.read_text(encoding="utf-8")
        agents_text = AGENTS.read_text(encoding="utf-8")

        self.assertIn("STRATEGIC_COMPASS.md", continue_text)
        self.assertIn("Strategic Alignment Gate", continue_text)
        self.assertLess(
            continue_text.index("STRATEGIC_COMPASS.md"),
            continue_text.index("ordered_next_actions"),
        )
        self.assertIn("STRATEGIC_COMPASS.md", agents_text)
        self.assertIn("Memory Atlas is a historical coverage instrument, not the product endpoint", agents_text)


if __name__ == "__main__":
    unittest.main()
