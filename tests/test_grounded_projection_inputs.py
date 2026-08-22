from __future__ import annotations

import unittest

from longcycle.application.grounded_projection_inputs import select_projection_execution_fragments


class GroundedProjectionInputSelectionTest(unittest.TestCase):
    def test_selects_only_projection_cited_fragments(self) -> None:
        execution = {
            "fragments": [
                {
                    "fragment_key": "cited",
                    "evidence_fragment_id": "11111111-1111-1111-1111-111111111111",
                    "claim_context": {"known_time": {"upper_bound": "2020-01-01T00:00:00Z"}},
                },
                {
                    "fragment_key": "uncited-with-different-annotation-needs",
                    "evidence_fragment_id": "22222222-2222-2222-2222-222222222222",
                    "claim_context": {},
                },
            ]
        }

        selected = select_projection_execution_fragments(execution, ["cited"])

        self.assertEqual(
            tuple(selected),
            ("11111111-1111-1111-1111-111111111111",),
        )
        self.assertEqual(next(iter(selected.values()))["fragment_key"], "cited")

    def test_missing_cited_fragment_is_rejected(self) -> None:
        execution = {
            "fragments": [
                {
                    "fragment_key": "present",
                    "evidence_fragment_id": "11111111-1111-1111-1111-111111111111",
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "unavailable evidence fragments: missing"):
            select_projection_execution_fragments(execution, ["missing"])

    def test_duplicate_fragment_keys_are_rejected(self) -> None:
        execution = {
            "fragments": [
                {
                    "fragment_key": "same",
                    "evidence_fragment_id": "11111111-1111-1111-1111-111111111111",
                },
                {
                    "fragment_key": "same",
                    "evidence_fragment_id": "22222222-2222-2222-2222-222222222222",
                },
            ]
        }

        with self.assertRaisesRegex(ValueError, "duplicate fragment_key: same"):
            select_projection_execution_fragments(execution, ["same"])


if __name__ == "__main__":
    unittest.main()
