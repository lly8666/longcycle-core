from __future__ import annotations

import unittest

from longcycle.application.handoff_freshness import (
    HANDOFF_MUTABLE_PATHS,
    classify_handoff_delta,
    require_handoff_only_delta,
)


class HandoffFreshnessContractTest(unittest.TestCase):
    def test_handoff_sync_paths_are_not_substantive(self) -> None:
        classification = classify_handoff_delta(HANDOFF_MUTABLE_PATHS)

        self.assertTrue(classification.is_handoff_only)
        self.assertEqual(classification.substantive_paths, ())

    def test_substantive_path_marks_checkpoint_stale(self) -> None:
        classification = classify_handoff_delta(
            {
                ".longcycle/handoff/current.json",
                "research_data/memory/example.jsonl",
            }
        )

        self.assertFalse(classification.is_handoff_only)
        self.assertEqual(
            classification.substantive_paths,
            ("research_data/memory/example.jsonl",),
        )

        with self.assertRaisesRegex(ValueError, "checkpoint is stale"):
            require_handoff_only_delta(
                {
                    ".longcycle/handoff/current.json",
                    "research_data/memory/example.jsonl",
                }
            )

    def test_duplicate_paths_are_normalized_deterministically(self) -> None:
        classification = classify_handoff_delta(
            [
                "z.py",
                ".longcycle/handoff/current.json",
                "z.py",
                "a.py",
            ]
        )

        self.assertEqual(
            classification.mutable_paths,
            (".longcycle/handoff/current.json",),
        )
        self.assertEqual(classification.substantive_paths, ("a.py", "z.py"))


if __name__ == "__main__":
    unittest.main()
