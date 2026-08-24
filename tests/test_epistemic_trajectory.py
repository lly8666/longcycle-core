from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError

from longcycle.application.epistemic_trajectory import (
    EpistemicTrajectorySpec,
    IntegratedReplayPlan,
    ReplayCounts,
    ReplayCutoff,
    ReplaySubject,
    trajectory_phases,
    validate_replay_sequence,
    validate_replay_snapshot,
)


_SUBJECT = UUID("b5254c47-1de6-5850-a99f-5e5b829884a8")


def _boundary() -> dict[str, bool]:
    return {
        "typed_epistemic_reader_is_semantic_contract": True,
        "future_rows_are_filtered_before_snapshot_materialization": True,
        "reality_is_canonical_fact_only": True,
        "judgment_is_not_rewritten_by_outcome": True,
        "outcome_is_separate_from_original_judgment": True,
    }


def _snapshot(
    cutoff: str,
    *,
    reality: list[dict[str, object]] | None = None,
    judgments: list[dict[str, object]] | None = None,
    outcomes: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "longcycle-integrated-no-lookahead-replay/v2",
        "knowledge_cutoff": cutoff,
        "reality": reality or [],
        "judgments": judgments or [],
        "outcomes": outcomes or [],
        "boundary": _boundary(),
    }


class EpistemicTrajectoryContractTest(unittest.TestCase):
    def test_outcome_requires_judgment_spec(self) -> None:
        with self.assertRaisesRegex(ValidationError, "requires judgment_spec_path"):
            EpistemicTrajectorySpec.model_validate(
                {
                    "schema_version": "longcycle-epistemic-trajectory/v1",
                    "task_id": "synthetic",
                    "research_orchestration_spec_path": "core.json",
                    "outcome_evaluations": [
                        {
                            "key": "later-milestone",
                            "judgment_key": "j-1",
                            "reality_fact_key": "r-1",
                            "semantic_relation": "related_milestone",
                        }
                    ],
                }
            )

    def test_judgment_context_requires_judgment_spec(self) -> None:
        with self.assertRaisesRegex(ValidationError, "judgment context requires judgment_spec_path"):
            EpistemicTrajectorySpec.model_validate(
                {
                    "schema_version": "longcycle-epistemic-trajectory/v1",
                    "task_id": "synthetic",
                    "research_orchestration_spec_path": "core.json",
                    "judgment_context_spec_path": "judgment-context.json",
                }
            )

    def test_replay_contract_requires_unique_subjects_and_increasing_cutoffs(self) -> None:
        with self.assertRaisesRegex(ValidationError, "subjects must be unique"):
            IntegratedReplayPlan.model_validate(
                {
                    "subjects": [
                        {"entity_id": str(_SUBJECT)},
                        {"entity_id": str(_SUBJECT)},
                    ],
                    "cutoffs": [
                        {"key": "first", "knowledge_cutoff": "2022-01-01T00:00:00Z"}
                    ],
                }
            )

        with self.assertRaisesRegex(ValidationError, "strictly increasing"):
            IntegratedReplayPlan.model_validate(
                {
                    "subjects": [{"entity_id": str(_SUBJECT)}],
                    "cutoffs": [
                        {"key": "later", "knowledge_cutoff": "2024-01-01T00:00:00Z"},
                        {"key": "earlier", "knowledge_cutoff": "2023-01-01T00:00:00Z"},
                    ],
                }
            )

    def test_full_trajectory_phases_are_data_driven(self) -> None:
        spec = EpistemicTrajectorySpec.model_validate(
            {
                "schema_version": "longcycle-epistemic-trajectory/v1",
                "task_id": "synthetic",
                "research_orchestration_spec_path": "core.json",
                "judgment_spec_path": "judgment.json",
                "judgment_context_spec_path": "judgment-context.json",
                "outcome_evaluations": [
                    {
                        "key": "later-milestone",
                        "judgment_key": "j-1",
                        "reality_fact_key": "r-1",
                        "semantic_relation": "related_milestone",
                    }
                ],
                "replay": {
                    "subjects": [{"entity_id": str(_SUBJECT)}],
                    "cutoffs": [
                        {"key": "t1", "knowledge_cutoff": "2022-01-01T00:00:00Z"}
                    ],
                },
            }
        )
        self.assertEqual(
            trajectory_phases(spec, core_has_reality=True),
            (
                "grounded_evidence",
                "reality_projection",
                "judgment_persistence",
                "judgment_context_persistence",
                "outcome_evaluation",
                "seal_integrated_memory",
                "point_in_time_replay",
            ),
        )

    def test_snapshot_gate_checks_counts_and_future_leakage(self) -> None:
        cutoff = ReplayCutoff(
            key="t1",
            knowledge_cutoff=datetime(2022, 1, 2, tzinfo=timezone.utc),
            expected_counts=ReplayCounts(reality=1, judgments=1, outcomes=0),
        )
        reality = [
            {
                "canonical_fact_version_id": "r-1",
                "known_at": "2022-01-01T00:00:00+00:00",
                "value_text": "known reality",
            }
        ]
        judgment = [
            {
                "judgment_id": "j-1",
                "known_at": "2022-01-02T00:00:00+00:00",
                "summary": "contemporaneous cognition",
            }
        ]
        payload = _snapshot(
            "2022-01-02T00:00:00+00:00",
            reality=reality,
            judgments=judgment,
        )
        counts = validate_replay_snapshot(payload, cutoff)
        self.assertEqual(counts, ReplayCounts(reality=1, judgments=1, outcomes=0))

        leaked = copy.deepcopy(payload)
        leaked["reality"][0]["known_at"] = "2022-01-03T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "leaked future reality"):
            validate_replay_snapshot(leaked, cutoff)

    def test_sequence_gate_rejects_hindsight_rewrite(self) -> None:
        earlier = _snapshot(
            "2022-01-02T00:00:00+00:00",
            judgments=[
                {
                    "judgment_id": "j-1",
                    "known_at": "2022-01-02T00:00:00+00:00",
                    "summary": "original judgment",
                }
            ],
        )
        later = _snapshot(
            "2024-01-02T00:00:00+00:00",
            judgments=[
                {
                    "judgment_id": "j-1",
                    "known_at": "2022-01-02T00:00:00+00:00",
                    "summary": "original judgment",
                }
            ],
            outcomes=[
                {
                    "evaluation_id": "o-1",
                    "known_at": "2024-01-01T00:00:00+00:00",
                    "evaluation_status": "indeterminate",
                }
            ],
        )
        validate_replay_sequence((earlier, later))

        rewritten = copy.deepcopy(later)
        rewritten["judgments"][0]["summary"] = "hindsight-adjusted judgment"
        with self.assertRaisesRegex(ValueError, "rewrote previously-known judgments"):
            validate_replay_sequence((earlier, rewritten))

    def test_subject_requires_exactly_one_key(self) -> None:
        with self.assertRaisesRegex(ValidationError, "exactly one"):
            ReplaySubject.model_validate({})
        with self.assertRaisesRegex(ValidationError, "exactly one"):
            ReplaySubject.model_validate(
                {
                    "entity_id": str(_SUBJECT),
                    "industry_node_id": str(_SUBJECT),
                }
            )


if __name__ == "__main__":
    unittest.main()
