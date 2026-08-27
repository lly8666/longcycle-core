from __future__ import annotations

import unittest
from datetime import date

from longcycle.application.memory_prompt import (
    MEMORY_AUDIT_LENSES,
    build_blind_recall_prompt,
    build_gap_audit_prompt,
)


class MemoryPromptTest(unittest.TestCase):
    def test_blind_prompt_has_no_archive_input_parameter(self) -> None:
        prompt = build_blind_recall_prompt(
            industry="新能源锂电池",
            period_start=date(2021, 1, 1),
            period_end=date(2023, 12, 31),
        )
        self.assertIn("UNSOURCED MODEL-MEMORY LEADS", prompt)
        self.assertIn("NOT been given current web search results", prompt)
        self.assertIn("A strong memory is still not evidence", prompt)
        self.assertIn("negative_space", prompt)

    def test_protocol_has_multiple_hidden_association_lenses(self) -> None:
        codes = {lens.code for lens in MEMORY_AUDIT_LENSES}
        self.assertGreaterEqual(len(codes), 10)
        self.assertIn("pricing_and_contracts", codes)
        self.assertIn("effective_supply_bottlenecks", codes)
        self.assertIn("inventory_location", codes)
        self.assertIn("cross_industry_dependencies", codes)
        self.assertIn("historical_vocabulary", codes)

    def test_gap_prompt_requires_archive_coverage(self) -> None:
        with self.assertRaises(ValueError):
            build_gap_audit_prompt(
                industry="新能源锂电池",
                period_start=date(2021, 1, 1),
                period_end=date(2023, 12, 31),
                archive_coverage_summary="   ",
            )

    def test_gap_prompt_forbids_source_count_resolution(self) -> None:
        prompt = build_gap_audit_prompt(
            industry="新能源锂电池",
            period_start=date(2021, 1, 1),
            period_end=date(2023, 12, 31),
            archive_coverage_summary="已覆盖锂价、动力电池装车和头部项目。",
        )
        self.assertIn("negative space", prompt)
        self.assertIn("claim-scoped primary source", prompt)
        self.assertIn("Do not resolve conflicts by source count", prompt)


if __name__ == "__main__":
    unittest.main()
