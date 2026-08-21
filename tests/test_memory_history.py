from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from longcycle.application.memory_history import scan_memory_history


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(repo), *args),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _write_lines(path: Path, count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f'{{"line": {index}}}\n' for index in range(count)),
        encoding="utf-8",
    )


class MemoryHistoryAuditTest(unittest.TestCase):
    def test_recovers_historical_max_after_larger_state_is_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git(repo, "init", "-b", "main")
            _git(repo, "config", "user.email", "test@example.com")
            _git(repo, "config", "user.name", "Longcycle Test")

            campaign = repo / "research_data" / "memory" / "example" / "campaign"
            shard = campaign / "blind" / "UP-HARDROCK"
            _write_lines(shard / "timeline-v1.jsonl", 2)
            _write_lines(shard / "formal-v3.jsonl", 3)
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "initial memory")

            _write_lines(shard / "batch-v4.jsonl", 7)
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "larger memory")
            larger_sha = _git(repo, "rev-parse", "HEAD")

            (shard / "batch-v4.jsonl").unlink()
            _git(repo, "add", "-A")
            _git(repo, "commit", "-m", "remove larger batch")

            audit = scan_memory_history(repo, campaign)

            self.assertEqual(audit.current_state.raw_leads, 5)
            self.assertEqual(audit.current_state.formal_typed_leads, 3)
            self.assertEqual(audit.max_raw_state.raw_leads, 12)
            self.assertEqual(audit.max_formal_typed_state.formal_typed_leads, 10)
            self.assertEqual(audit.max_raw_state.commit_sha, larger_sha)
            self.assertEqual(audit.max_formal_typed_state.commit_sha, larger_sha)
            self.assertTrue(
                any(state.commit_sha == larger_sha for state in audit.candidates_exceeding_current)
            )
            self.assertTrue(
                any(
                    state.raw_leads == 5 and state.formal_typed_leads == 3
                    for state in audit.distinct_states
                )
            )

    def test_scans_states_reachable_only_from_another_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git(repo, "init", "-b", "main")
            _git(repo, "config", "user.email", "test@example.com")
            _git(repo, "config", "user.name", "Longcycle Test")

            campaign = repo / "research_data" / "memory" / "example" / "campaign"
            shard = campaign / "blind" / "MID-LFP"
            _write_lines(shard / "formal-v3.jsonl", 3)
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "base")
            base_sha = _git(repo, "rev-parse", "HEAD")

            _git(repo, "checkout", "-b", "recovery-candidate")
            _write_lines(shard / "side-v4.jsonl", 9)
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "side larger state")
            side_sha = _git(repo, "rev-parse", "HEAD")

            _git(repo, "checkout", "main")
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), base_sha)

            audit = scan_memory_history(repo, campaign)

            self.assertEqual(audit.current_state.raw_leads, 3)
            self.assertEqual(audit.max_raw_state.raw_leads, 12)
            self.assertEqual(audit.max_raw_state.commit_sha, side_sha)
            self.assertTrue(
                any(state.commit_sha == side_sha for state in audit.candidates_exceeding_current)
            )


if __name__ == "__main__":
    unittest.main()
