from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch

from longcycle.cli import _parser, _run


class ResearchCliTest(unittest.TestCase):
    def _args(self) -> object:
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

    def test_research_run_parser_uses_existing_longcycle_surface(self) -> None:
        args = self._args()
        self.assertEqual(args.command, "research")
        self.assertEqual(args.research_command, "run")
        self.assertEqual(args.spec, Path("spec.json"))
        self.assertEqual(args.source_pack, Path("source-pack.zip"))
        self.assertEqual(args.work_dir, Path("work"))
        self.assertEqual(args.output, Path("receipt.json"))
        self.assertEqual(args.repo_root, Path("repo"))
        self.assertTrue(args.skip_db_upgrade)

    def test_research_run_delegates_to_shared_receipt_executor(self) -> None:
        args = self._args()
        expected = {
            "schema_version": "longcycle-research-orchestration-execution/v1",
            "task_id": "synthetic",
        }
        with patch(
            "longcycle.cli.execute_research_orchestration_receipt",
            return_value={"ok": True, "result": expected},
        ) as execute:
            result = asyncio.run(_run(args))

        self.assertEqual(result, expected)
        execute.assert_called_once_with(
            repo_root=Path("repo"),
            spec_path=Path("spec.json"),
            source_pack_path=Path("source-pack.zip"),
            work_dir=Path("work"),
            output_path=Path("receipt.json"),
            skip_db_upgrade=True,
        )

    def test_research_run_propagates_fail_closed_receipt_as_cli_failure(self) -> None:
        args = self._args()
        with patch(
            "longcycle.cli.execute_research_orchestration_receipt",
            return_value={"ok": False, "error": "ValueError: source pack digest mismatch"},
        ):
            with self.assertRaisesRegex(RuntimeError, "source pack digest mismatch"):
                asyncio.run(_run(args))


if __name__ == "__main__":
    unittest.main()
