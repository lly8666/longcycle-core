from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from longcycle.application.session_handoff import (
    HandoffMemoryCampaign,
    SessionHandoffCheckpoint,
    evaluate_handoff_head,
)

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / ".longcycle" / "handoff" / "current.json"
PROTOCOL = ROOT / "docs" / "development" / "session-handoff-protocol.md"
CONTINUE_HERE = ROOT / "CONTINUE_HERE.md"


class SessionHandoffContractTest(unittest.TestCase):
    def test_current_handoff_is_typed_bounded_and_resumable(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate(
            json.loads(HANDOFF.read_text(encoding="utf-8"))
        )

        self.assertEqual(checkpoint.schema_version, "longcycle-session-handoff/v5")
        self.assertEqual(checkpoint.repository, "lly8666/longcycle-core")
        self.assertEqual(checkpoint.active_branch, "design/industry-memory")
        self.assertEqual(checkpoint.active_pr, 1)
        self.assertEqual(checkpoint.provenance_ordering, "git_commit_graph")
        self.assertTrue(checkpoint.live_refresh_required)
        self.assertTrue(checkpoint.do_not_ask_user_to_repeat)
        self.assertLessEqual(len(checkpoint.resume_read_set), 8)
        self.assertEqual(
            checkpoint.data_plane_manifest_path,
            ".longcycle/handoff/data-plane.json",
        )
        self.assertIn(checkpoint.data_plane_manifest_path, checkpoint.resume_read_set)
        self.assertEqual(checkpoint.ci.authority, "snapshot_not_authoritative")
        self.assertTrue(checkpoint.strategic_horizon.medium_term_goal)
        self.assertTrue(checkpoint.strategic_horizon.short_term_goal)
        self.assertTrue(checkpoint.strategic_horizon.next_big_step)
        self.assertTrue(checkpoint.continuation_cursor.current_task)
        self.assertTrue(checkpoint.continuation_cursor.why_now)
        self.assertTrue(checkpoint.continuation_cursor.done_when)
        self.assertEqual(
            checkpoint.continuation_cursor.required_capability,
            "high_capability_reasoning",
        )
        self.assertEqual(
            checkpoint.continuation_cursor.insufficient_capability_action,
            "stop_and_escalate",
        )
        self.assertTrue(checkpoint.continuation_cursor.next_atomic_action)
        self.assertTrue(any(item.role == "main_path" for item in checkpoint.workstreams))

    def test_long_term_cores_are_references_not_checkpoint_copies(self) -> None:
        payload = json.loads(HANDOFF.read_text(encoding="utf-8"))

        self.assertEqual(payload["core_refs"]["strategy_path"], "STRATEGIC_COMPASS.md")
        self.assertEqual(payload["core_refs"]["methodology_path"], "METHODOLOGY_CORE.md")
        self.assertEqual(
            payload["core_refs"]["mission_fidelity_path"],
            ".longcycle/continuity/mission-fidelity.json",
        )
        for duplicated_key in (
            "user_directives",
            "north_star",
            "non_negotiable_invariants",
            "forbidden_shortcuts",
            "future_phase_commitments",
        ):
            self.assertNotIn(duplicated_key, payload)

    def test_pre_campaign_state_is_explicit_and_campaign_guards_still_hold(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        campaign = checkpoint.memory_campaign

        if campaign is None:
            self.assertIsNone(checkpoint.active_context.campaign_root)
            self.assertIsNone(checkpoint.active_context.coverage_path)
        else:
            self.assertIsNotNone(checkpoint.active_context.campaign_root)
            self.assertIsNotNone(checkpoint.active_context.coverage_path)
            coverage_path = ROOT / checkpoint.active_context.coverage_path
            self.assertTrue(coverage_path.is_file())
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            sealed_from_coverage = tuple(coverage["sealed_shards"])
            self.assertGreater(campaign.total_raw_leads, 0)
            self.assertEqual(campaign.sealed_shards, sealed_from_coverage)
            self.assertEqual(campaign.search_visibility, coverage["search_visibility"])

        blind_campaign = HandoffMemoryCampaign(
            campaign_id="synthetic-blind-contract",
            industry="synthetic-industry",
            phase="blind_recall",
            search_visibility="none",
            total_raw_leads=0,
            sealed_shards=(),
            shard_count=1,
            seal_rule="Synthetic test fixture.",
            next_research_actions=("Continue bounded blind recall.",),
        )
        self.assertEqual(blind_campaign.search_visibility, "none")

        with self.assertRaisesRegex(ValidationError, "blind memory phase cannot expose fresh search"):
            HandoffMemoryCampaign(
                campaign_id="synthetic-invalid-blind-contract",
                industry="synthetic-industry",
                phase="blind_recall",
                search_visibility="self_verification",
                total_raw_leads=0,
                sealed_shards=(),
                shard_count=1,
                seal_rule="Synthetic test fixture.",
                next_research_actions=("This must fail.",),
            )

    def test_resume_set_contains_only_small_bootstrap_plus_active_state(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        read_set = set(checkpoint.resume_read_set)

        required = {
            "STRATEGIC_COMPASS.md",
            "METHODOLOGY_CORE.md",
            ".longcycle/continuity/mission-fidelity.json",
            "CONTINUE_HERE.md",
            ".longcycle/handoff/current.json",
            ".longcycle/handoff/data-plane.json",
        }
        self.assertTrue(required.issubset(read_set))
        self.assertLessEqual(len(read_set), 8)
        self.assertFalse(any(path.startswith("docs/devlog/") for path in read_set))
        self.assertNotIn("docs/development/project-constitution.md", read_set)
        self.assertNotIn("docs/development/session-handoff-protocol.md", read_set)

    def test_workstreams_are_explicitly_attached_to_parent_goals(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
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

    def test_semantic_reread_rule_is_normative_without_changing_v5_shape(self) -> None:
        # HANDOFF_SEMANTIC_REREAD_V1
        protocol = PROTOCOL.read_text(encoding="utf-8")
        bootstrap = CONTINUE_HERE.read_text(encoding="utf-8")

        self.assertIn("HANDOFF_SEMANTIC_REREAD_V1", protocol)
        self.assertIn("HANDOFF_SEMANTIC_REREAD_V1", bootstrap)
        self.assertIn("cursor as the sole owner", protocol)
        self.assertIn("must remain meaningfully broader than `next_atomic_action`", protocol)
        self.assertIn("Must be checked", protocol)
        self.assertIn("写完 JSON 不等于完成 handoff", bootstrap)
        self.assertIn("必须检查不等于必须改值", bootstrap)
        self.assertIn("从 live target ref 重新读取", bootstrap)

    def test_live_head_difference_requires_delta_reconciliation(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        decision = evaluate_handoff_head(checkpoint, live_head_sha="a" * 40)

        self.assertTrue(decision.requires_delta_reconciliation)
        self.assertEqual(decision.status, "delta_reconciliation_required")

    def test_exact_checkpoint_base_can_be_recognized(self) -> None:
        checkpoint = SessionHandoffCheckpoint.model_validate_json(
            HANDOFF.read_text(encoding="utf-8")
        )
        decision = evaluate_handoff_head(
            checkpoint,
            live_head_sha=checkpoint.checkpoint_based_on_head_sha,
        )

        self.assertFalse(decision.requires_delta_reconciliation)
        self.assertEqual(decision.status, "checkpoint_base_matches_live_head")


if __name__ == "__main__":
    unittest.main()
