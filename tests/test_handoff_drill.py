from __future__ import annotations

import unittest
from pathlib import Path

from longcycle.application.handoff_drill import audit_repository_handoff
from longcycle.application.session_handoff import HandoffMemoryCampaign, SessionHandoffCheckpoint


ROOT = Path(__file__).resolve().parents[1]


class HandoffIsolationDrillTest(unittest.TestCase):
    def test_repository_only_reconstruction_matches_current_campaign(self) -> None:
        report = audit_repository_handoff(ROOT)

        self.assertEqual(report.fidelity_score, 1.0, report.failed_checks)
        self.assertEqual(report.recovered.repository, "lly8666/longcycle-core")
        self.assertEqual(report.recovered.active_branch, "design/industry-memory")
        self.assertEqual(report.recovered.active_pr, 1)
        self.assertEqual(report.recovered.campaign_id, "2026-08-21-gpt-5.6-sol")
        self.assertEqual(report.recovered.industry, "lithium-battery")
        self.assertEqual(report.recovered.phase, "blind_memory_exhaustion")
        self.assertEqual(report.recovered.search_visibility, "none")
        self.assertEqual(report.recovered.total_raw_leads, 570)
        self.assertEqual(report.recovered.shard_count, 14)
        self.assertEqual(report.recovered.sealed_shards, ())
        self.assertTrue(report.recovered.ordered_next_actions)
        self.assertTrue(report.recovered.north_star)
        self.assertTrue(report.recovered.user_directives)
        self.assertTrue(report.recovered.forbidden_shortcuts)

    def test_stale_checkpoint_is_detected_without_chat_context(self) -> None:
        current_path = ROOT / ".longcycle" / "handoff" / "current.json"
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            current_path.read_text(encoding="utf-8")
        )
        stale_campaign = HandoffMemoryCampaign.model_validate(
            {
                **checkpoint.memory_campaign.model_dump(mode="python"),
                "total_raw_leads": checkpoint.memory_campaign.total_raw_leads - 1,
            }
        )
        stale_checkpoint = checkpoint.model_copy(update={"memory_campaign": stale_campaign})

        report = audit_repository_handoff(ROOT, checkpoint_override=stale_checkpoint)
        failures = {item.name for item in report.failed_checks}

        self.assertLess(report.fidelity_score, 1.0)
        self.assertIn("checkpoint_total_matches_raw", failures)
        self.assertEqual(report.recovered.total_raw_leads, 570)


if __name__ == "__main__":
    unittest.main()
