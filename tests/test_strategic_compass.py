from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPASS = ROOT / "STRATEGIC_COMPASS.md"
METHODS = ROOT / "METHODOLOGY_CORE.md"
CONTINUE = ROOT / "CONTINUE_HERE.md"
AGENTS = ROOT / "AGENTS.md"
HANDOFF = ROOT / ".longcycle" / "handoff" / "current.json"


class StrategicCompassContractTest(unittest.TestCase):
    def test_compass_is_small_and_preserves_only_terminal_direction(self) -> None:
        text = COMPASS.read_text(encoding="utf-8")
        raw = COMPASS.read_bytes()

        self.assertLessEqual(len(raw), 6500)
        self.assertLessEqual(len(text.splitlines()), 100)
        for fragment in (
            "历史本身就是分析",
            "Reality",
            "Expectation",
            "Outcome",
            "point-in-time",
            "中期",
            "短期",
            "Strategic Alignment Gate",
            "先确认航向，再拧螺丝",
        ):
            self.assertIn(fragment, text)

    def test_method_core_is_bounded_and_cross_industry(self) -> None:
        text = METHODS.read_text(encoding="utf-8")
        raw = METHODS.read_bytes()

        self.assertLessEqual(len(raw), 9000)
        self.assertLessEqual(len(text.splitlines()), 170)
        for fragment in (
            "Memory-first, Evidence-final",
            "Source-first, Archive-now",
            "not_found != false",
            "claim scope",
            "Point-in-time",
            "可比性先于数量",
            "Agent 分工",
            "模型升级产生新 research vintage",
            "有限核心 + 动态状态",
        ):
            self.assertIn(fragment, text)

    def test_active_industry_cannot_leak_into_long_term_cores(self) -> None:
        checkpoint = json.loads(HANDOFF.read_text(encoding="utf-8"))
        terms = checkpoint["active_context"]["core_exclusion_terms"]
        core_text = (COMPASS.read_text(encoding="utf-8") + METHODS.read_text(encoding="utf-8")).lower()

        hits = [term for term in terms if term.lower() in core_text]
        self.assertEqual(hits, [])

    def test_bootstrap_reads_bounded_cores_before_dynamic_context(self) -> None:
        continue_text = CONTINUE.read_text(encoding="utf-8")
        agents_text = AGENTS.read_text(encoding="utf-8")

        for path in ("STRATEGIC_COMPASS.md", "METHODOLOGY_CORE.md", ".longcycle/handoff/current.json"):
            self.assertIn(path, continue_text)
            self.assertIn(path, agents_text)

        self.assertLess(
            continue_text.index("STRATEGIC_COMPASS.md"),
            continue_text.index(".longcycle/handoff/current.json"),
        )
        self.assertLess(
            continue_text.index("METHODOLOGY_CORE.md"),
            continue_text.index(".longcycle/handoff/current.json"),
        )
        self.assertIn("不要默认读取旧 devlog", continue_text)


if __name__ == "__main__":
    unittest.main()
