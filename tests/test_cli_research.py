from __future__ import annotations

import argparse
import asyncio
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

from longcycle.cli import _parser, _run
from longcycle.domain.epistemic import PointInTimeMemorySnapshot


class ResearchCliTest(unittest.TestCase):
    def _core_args(self) -> argparse.Namespace:
        return _parser().parse_args(
            [
                "research",
                "run",
                "spec.json",
                "--source-pack",
                "source-pack.zip",
                "--work-dir",
                "work",
                "--output",
                "receipt.json",
                "--repo-root",
                "repo",
                "--skip-db-upgrade",
            ]
        )

    def _trajectory_args(self) -> argparse.Namespace:
        return _parser().parse_args(
            [
                "research",
                "run",
                "trajectory.json",
                "--material-root",
                "material",
                "--work-dir",
                "work",
                "--output",
                "receipt.json",
                "--repo-root",
                "repo",
                "--skip-db-upgrade",
            ]
        )

    def test_research_run_parser_uses_existing_longcycle_surface(self) -> None:
        args = self._core_args()
        self.assertEqual(args.command, "research")
        self.assertEqual(args.research_command, "run")
        self.assertEqual(args.spec, Path("spec.json"))
        self.assertEqual(args.source_pack, Path("source-pack.zip"))
        self.assertIsNone(args.material_root)
        self.assertEqual(args.work_dir, Path("work"))
        self.assertEqual(args.output, Path("receipt.json"))
        self.assertEqual(args.repo_root, Path("repo"))
        self.assertTrue(args.skip_db_upgrade)

        trajectory = self._trajectory_args()
        self.assertEqual(trajectory.research_command, "run")
        self.assertEqual(trajectory.spec, Path("trajectory.json"))
        self.assertIsNone(trajectory.source_pack)
        self.assertEqual(trajectory.material_root, Path("material"))

    def test_research_run_core_v1_delegates_to_existing_receipt_executor(self) -> None:
        args = self._core_args()
        expected = {
            "schema_version": "longcycle-research-orchestration-execution/v1",
            "task_id": "synthetic",
        }
        with (
            patch(
                "longcycle.cli._research_spec_schema_version",
                return_value="longcycle-research-orchestration/v1",
            ),
            patch(
                "longcycle.cli.execute_research_orchestration_receipt",
                return_value={"ok": True, "result": expected},
            ) as execute,
            patch("longcycle.cli.execute_epistemic_trajectory_receipt") as trajectory,
        ):
            result = asyncio.run(_run(args))

        self.assertEqual(result, expected)
        execute.assert_called_once_with(
            repo_root=Path("repo"),
            spec_path=Path("spec.json"),
            source_pack_path=Path("source-pack.zip"),
            material_root_path=None,
            work_dir=Path("work"),
            output_path=Path("receipt.json"),
            skip_db_upgrade=True,
        )
        trajectory.assert_not_called()

    def test_research_run_core_v2_preserves_material_root_path(self) -> None:
        args = _parser().parse_args(
            [
                "research",
                "run",
                "spec.json",
                "--material-root",
                "material",
                "--work-dir",
                "work",
                "--output",
                "receipt.json",
            ]
        )
        expected = {"schema_version": "longcycle-research-orchestration-execution/v2"}
        with (
            patch(
                "longcycle.cli._research_spec_schema_version",
                return_value="longcycle-research-orchestration/v2",
            ),
            patch(
                "longcycle.cli.execute_research_orchestration_receipt",
                return_value={"ok": True, "result": expected},
            ) as execute,
        ):
            result = asyncio.run(_run(args))

        self.assertEqual(result, expected)
        self.assertEqual(execute.call_args.kwargs["material_root_path"], Path("material"))
        self.assertIsNone(execute.call_args.kwargs["source_pack_path"])

    def test_research_run_trajectory_delegates_to_epistemic_receipt_executor(self) -> None:
        args = self._trajectory_args()
        expected = {
            "schema_version": "longcycle-epistemic-trajectory-execution/v1",
            "task_id": "synthetic-trajectory",
        }
        with (
            patch(
                "longcycle.cli._research_spec_schema_version",
                return_value="longcycle-epistemic-trajectory/v1",
            ),
            patch(
                "longcycle.cli.execute_epistemic_trajectory_receipt",
                return_value={"ok": True, "result": expected},
            ) as execute,
            patch("longcycle.cli.execute_research_orchestration_receipt") as core,
        ):
            result = asyncio.run(_run(args))

        self.assertEqual(result, expected)
        execute.assert_called_once_with(
            repo_root=Path("repo"),
            spec_path=Path("trajectory.json"),
            material_root_path=Path("material"),
            work_dir=Path("work"),
            output_path=Path("receipt.json"),
            skip_db_upgrade=True,
        )
        core.assert_not_called()

    def test_research_run_trajectory_rejects_source_pack_and_missing_material_root(self) -> None:
        with_source_pack = _parser().parse_args(
            [
                "research",
                "run",
                "trajectory.json",
                "--source-pack",
                "legacy.zip",
                "--material-root",
                "material",
                "--work-dir",
                "work",
                "--output",
                "receipt.json",
            ]
        )
        with patch(
            "longcycle.cli._research_spec_schema_version",
            return_value="longcycle-epistemic-trajectory/v1",
        ):
            with self.assertRaisesRegex(ValueError, "does not accept --source-pack"):
                asyncio.run(_run(with_source_pack))

        without_material_root = _parser().parse_args(
            [
                "research",
                "run",
                "trajectory.json",
                "--work-dir",
                "work",
                "--output",
                "receipt.json",
            ]
        )
        with patch(
            "longcycle.cli._research_spec_schema_version",
            return_value="longcycle-epistemic-trajectory/v1",
        ):
            with self.assertRaisesRegex(ValueError, "requires --material-root"):
                asyncio.run(_run(without_material_root))

    def test_research_run_propagates_fail_closed_receipt_as_cli_failure(self) -> None:
        args = self._trajectory_args()
        with (
            patch(
                "longcycle.cli._research_spec_schema_version",
                return_value="longcycle-epistemic-trajectory/v1",
            ),
            patch(
                "longcycle.cli.execute_epistemic_trajectory_receipt",
                return_value={"ok": False, "error": "ValueError: replay leaked future judgment row"},
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "leaked future judgment"):
                asyncio.run(_run(args))

    def test_research_run_rejects_unknown_spec_schema(self) -> None:
        args = self._trajectory_args()
        with patch(
            "longcycle.cli._research_spec_schema_version",
            return_value="longcycle-unknown/v1",
        ):
            with self.assertRaisesRegex(ValueError, "unsupported research run schema_version"):
                asyncio.run(_run(args))

    def test_research_replay_parser_requires_aware_cutoff_and_subject(self) -> None:
        subject = "11111111-1111-1111-1111-111111111111"
        args = _parser().parse_args(
            [
                "research",
                "replay",
                "memory.duckdb",
                "2022-08-03T16:27:49Z",
                "--subject-id",
                subject,
            ]
        )
        self.assertEqual(args.command, "research")
        self.assertEqual(args.research_command, "replay")
        self.assertEqual(args.database, Path("memory.duckdb"))
        self.assertEqual(args.cutoff, datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC))
        self.assertEqual(args.subject_id, [subject])

        without_subject = _parser().parse_args(
            ["research", "replay", "memory.duckdb", "2022-08-03T16:27:49Z"]
        )
        with self.assertRaisesRegex(ValueError, "at least one"):
            asyncio.run(_run(without_subject))

    def test_research_replay_reads_typed_snapshot_and_builds_trajectory(self) -> None:
        subject_id = UUID("11111111-1111-1111-1111-111111111111")
        cutoff = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)
        args = _parser().parse_args(
            [
                "research",
                "replay",
                "memory.duckdb",
                cutoff.isoformat(),
                "--subject-id",
                str(subject_id),
            ]
        )
        snapshot = PointInTimeMemorySnapshot(knowledge_cutoff=cutoff)
        expected = {
            "schema_version": "longcycle-researcher-trajectory-view/v1",
            "knowledge_cutoff": cutoff.isoformat(),
            "entries": [],
        }
        reader = AsyncMock()
        reader.snapshot.return_value = snapshot
        with (
            patch("longcycle.cli.DuckDBEpistemicMemoryReader", return_value=reader) as reader_type,
            patch("longcycle.cli.build_researcher_trajectory_view", return_value=expected) as build,
        ):
            result = asyncio.run(_run(args))

        self.assertEqual(result, expected)
        reader_type.assert_called_once_with(Path("memory.duckdb"))
        reader.snapshot.assert_awaited_once()
        call = reader.snapshot.await_args
        self.assertEqual(call.kwargs["knowledge_cutoff"], cutoff)
        self.assertEqual(call.args[0][0].entity_id, subject_id)
        build.assert_called_once_with(snapshot)


if __name__ == "__main__":
    unittest.main()
