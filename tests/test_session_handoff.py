from __future__ import annotations

import json
import unittest
from pathlib import Path

from longcycle.application.session_handoff import SessionHandoffCheckpoint


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / ".longcycle" / "handoff" / "current.json"


class SessionHandoffContractTest(unittest.TestCase):
    def test_current_handoff_is_typed_and_resumable(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate(
            json.loads(HANDOFF.read_text(encoding="utf-8"))
        )

        self.assertEqual(checkpoint.repository, "lly8666/longcycle-core")
        self.assertEqual(checkpoint.active_branch, "design/industry-memory")
        self.assertEqual(checkpoint.active_pr, 1)
        self.assertTrue(checkpoint.live_refresh_required)
        self.assertTrue(checkpoint.do_not_ask_user_to_repeat)
        self.assertEqual(checkpoint.ci.authority, "snapshot_not_authoritative")

    def test_blind_lithium_campaign_cannot_leak_search_across_sessions(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        campaign = checkpoint.memory_campaign

        self.assertEqual(campaign.campaign_id, "2026-08-21-gpt-5.6-sol")
        self.assertEqual(campaign.total_raw_leads, 552)
        self.assertEqual(campaign.shard_count, 14)
        self.assertEqual(campaign.sealed_shards, ())
        self.assertEqual(campaign.search_visibility, "none")

    def test_resume_set_contains_live_state_and_research_guardrails(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        read_set = set(checkpoint.resume_read_set)

        required = {
            "CONTINUE_HERE.md",
            "AGENTS.md",
            ".longcycle/handoff/current.json",
            "docs/development/project-constitution.md",
            "docs/development/session-handoff-protocol.md",
            "research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/analysis/coverage-index.json",
        }
        self.assertTrue(required.issubset(read_set))


if __name__ == "__main__":
    unittest.main()
