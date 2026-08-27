from __future__ import annotations

import json
import unittest
from pathlib import Path

from longcycle.application.handoff_drill import audit_repository_handoff
from longcycle.application.session_handoff import HandoffMemoryCampaign, SessionHandoffCheckpoint

ROOT = Path(__file__).resolve().parents[1]
LITHIUM_ROOT = (
    "research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol"
)
LITHIUM_COVERAGE = f"{LITHIUM_ROOT}/analysis/coverage-index.json"


class HandoffIsolationDrillTest(unittest.TestCase):
    def test_repository_only_reconstruction_matches_current_context(self) -> None:
        report = audit_repository_handoff(ROOT)
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            (ROOT / ".longcycle" / "handoff" / "current.json").read_text(encoding="utf-8")
        )

        self.assertEqual(report.fidelity_score, 1.0, report.failed_checks)
        self.assertEqual(report.recovered.repository, "lly8666/longcycle-core")
        self.assertEqual(report.recovered.active_branch, checkpoint.active_branch)
        self.assertEqual(report.recovered.active_pr, checkpoint.active_pr)
        self.assertEqual(report.recovered.context_id, checkpoint.active_context.context_id)
        self.assertEqual(
            report.recovered.medium_term_goal,
            checkpoint.strategic_horizon.medium_term_goal,
        )
        self.assertEqual(
            report.recovered.short_term_goal,
            checkpoint.strategic_horizon.short_term_goal,
        )
        self.assertEqual(
            report.recovered.next_big_step,
            checkpoint.strategic_horizon.next_big_step,
        )
        self.assertEqual(
            report.recovered.cursor_parent_workstream_id,
            checkpoint.continuation_cursor.parent_workstream_id,
        )
        self.assertEqual(
            report.recovered.cursor_last_completed_action,
            checkpoint.continuation_cursor.last_completed_action,
        )
        self.assertEqual(
            report.recovered.cursor_current_task,
            checkpoint.continuation_cursor.current_task,
        )
        self.assertEqual(
            report.recovered.cursor_done_when,
            checkpoint.continuation_cursor.done_when,
        )
        self.assertEqual(
            report.recovered.cursor_next_atomic_action,
            checkpoint.continuation_cursor.next_atomic_action,
        )
        self.assertTrue(report.recovered.ordered_next_actions)

        workstreams = {item.workstream_id: item for item in checkpoint.workstreams}
        main_paths = [item for item in checkpoint.workstreams if item.role == "main_path"]
        self.assertTrue(main_paths)
        for main_path in main_paths:
            self.assertNotEqual(
                main_path.parent_goal_ref,
                "strategic_horizon.parallel_permanent_tracks",
            )

        cursor_workstream = workstreams[checkpoint.continuation_cursor.parent_workstream_id]
        if cursor_workstream.role == "parallel_track":
            self.assertEqual(
                cursor_workstream.parent_goal_ref,
                "strategic_horizon.parallel_permanent_tracks",
            )
        else:
            self.assertIn(
                cursor_workstream.parent_goal_ref,
                {
                    "strategic_horizon.short_term_goal",
                    "strategic_horizon.medium_term_goal",
                },
            )

        campaign = checkpoint.memory_campaign
        if campaign is None:
            self.assertIsNone(report.recovered.campaign_id)
            self.assertIsNone(report.recovered.phase)
            self.assertIsNone(report.recovered.search_visibility)
            self.assertIsNone(report.recovered.total_raw_leads)
            self.assertIsNone(report.recovered.shard_count)
            self.assertEqual(report.recovered.sealed_shards, ())
            self.assertIsNone(checkpoint.active_context.campaign_root)
            self.assertIsNone(checkpoint.active_context.coverage_path)
        else:
            self.assertEqual(report.recovered.campaign_id, campaign.campaign_id)
            self.assertEqual(report.recovered.phase, campaign.phase)
            self.assertEqual(report.recovered.search_visibility, campaign.search_visibility)
            self.assertEqual(report.recovered.total_raw_leads, campaign.total_raw_leads)
            self.assertEqual(report.recovered.sealed_shards, campaign.sealed_shards)

    def test_fresh_bootstrap_exposes_bounded_on_demand_history_recall(self) -> None:
        bootstrap = (ROOT / "FRESH_AGENT_BOOTSTRAP.md").read_text(encoding="utf-8")
        protocol = (ROOT / "docs" / "development" / "on-demand-history-recall.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/development/on-demand-history-recall.md", bootstrap)
        self.assertIn("Do **not** preload old devlogs/issues/benchmarks", bootstrap)
        self.assertIn("HISTORICAL_RECALL_PROTOCOL_V1", protocol)
        self.assertIn("capability registry relevant/query", protocol)
        self.assertIn("repair-memory relevant/query", protocol)
        self.assertIn("follow exact origin refs / scoped paths", protocol)
        self.assertIn("Do not crawl all devlogs", protocol)
        self.assertIn("Most history should stay cold in Git", protocol)

    def test_cursor_must_point_to_declared_workstream(self) -> None:
        current_path = ROOT / ".longcycle" / "handoff" / "current.json"
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            current_path.read_text(encoding="utf-8")
        )
        payload = checkpoint.model_dump(mode="json")
        payload["continuation_cursor"]["parent_workstream_id"] = "missing-workstream"

        with self.assertRaisesRegex(ValueError, "declared workstream"):
            SessionHandoffCheckpoint.model_validate(payload)

    def test_handoff_requires_a_main_path_workstream(self) -> None:
        current_path = ROOT / ".longcycle" / "handoff" / "current.json"
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            current_path.read_text(encoding="utf-8")
        )
        payload = checkpoint.model_dump(mode="json")
        for workstream in payload["workstreams"]:
            workstream["role"] = "supporting_quality_gate"
            workstream["parent_goal_ref"] = "strategic_horizon.medium_term_goal"

        with self.assertRaisesRegex(ValueError, "main-path workstream"):
            SessionHandoffCheckpoint.model_validate(payload)

    def test_stale_campaign_checkpoint_is_detected_without_chat_context(self) -> None:
        current_path = ROOT / ".longcycle" / "handoff" / "current.json"
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            current_path.read_text(encoding="utf-8")
        )
        coverage = json.loads((ROOT / LITHIUM_COVERAGE).read_text(encoding="utf-8"))
        total_raw = int(coverage["total_raw_leads_so_far"])
        sealed_shards = tuple(coverage["sealed_shards"])
        shard_count = len(coverage["shards"])

        stale_campaign = HandoffMemoryCampaign(
            campaign_id="synthetic-stale-lithium-drill",
            industry="lithium-battery",
            phase="self_verification",
            search_visibility="self_verification",
            total_raw_leads=total_raw - 1,
            sealed_shards=sealed_shards,
            shard_count=shard_count,
            seal_rule="Synthetic fixture: compare checkpoint total to immutable blind files.",
            next_research_actions=("Synthetic stale-campaign drill only.",),
        )
        lithium_context = checkpoint.active_context.model_copy(
            update={
                "campaign_root": LITHIUM_ROOT,
                "coverage_path": LITHIUM_COVERAGE,
            }
        )
        stale_checkpoint = checkpoint.model_copy(
            update={
                "active_context": lithium_context,
                "memory_campaign": stale_campaign,
            }
        )

        report = audit_repository_handoff(ROOT, checkpoint_override=stale_checkpoint)
        failures = {item.name for item in report.failed_checks}

        self.assertLess(report.fidelity_score, 1.0)
        self.assertIn("checkpoint_total_matches_raw", failures)
        self.assertEqual(report.recovered.total_raw_leads, total_raw)


if __name__ == "__main__":
    unittest.main()
