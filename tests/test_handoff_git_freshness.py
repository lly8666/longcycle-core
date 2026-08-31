from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_handoff_git_freshness.py"
SPEC = importlib.util.spec_from_file_location("audit_handoff_git_freshness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


class HandoffGitFreshnessTest(unittest.TestCase):
    def test_edge_audit_detects_substantive_change_followed_by_revert(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _git(root, "init")
            _git(root, "config", "user.name", "Longcycle Test")
            _git(root, "config", "user.email", "longcycle-test@example.invalid")

            source = root / "feature.txt"
            source.write_text("base\n", encoding="utf-8")
            _git(root, "add", "feature.txt")
            _git(root, "commit", "-m", "base")
            base = _git(root, "rev-parse", "HEAD")

            source.write_text("substantive\n", encoding="utf-8")
            _git(root, "commit", "-am", "substantive change")
            source.write_text("base\n", encoding="utf-8")
            _git(root, "commit", "-am", "revert substantive change")
            head = _git(root, "rev-parse", "HEAD")

            self.assertEqual(_git(root, "diff", "--name-only", f"{base}..{head}"), "")
            changed, edge_count = audit._edge_changed_paths(root, base=base, head=head)

            self.assertEqual(changed, ("feature.txt",))
            self.assertEqual(edge_count, 2)


if __name__ == "__main__":
    unittest.main()
