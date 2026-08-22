from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from longcycle.application.handoff_freshness import classify_handoff_delta
from longcycle.application.session_handoff import SessionHandoffCheckpoint


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that the checked-in handoff checkpoint is based on an ancestor substantive "
            "commit and that every later path through live HEAD is handoff-sync-only."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    args = _parser().parse_args()
    root = args.root.resolve()
    checkpoint = SessionHandoffCheckpoint.model_validate_json(
        (root / ".longcycle/handoff/current.json").read_text(encoding="utf-8")
    )
    live_head = _git(root, "rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", checkpoint.checkpoint_based_on_head_sha, live_head],
        cwd=root,
    ).returncode == 0
    if not ancestor:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "checkpoint base is not an ancestor of live HEAD",
                    "checkpoint_based_on_head_sha": checkpoint.checkpoint_based_on_head_sha,
                    "live_head_sha": live_head,
                },
                indent=2,
            )
        )

    changed = tuple(
        line
        for line in _git(
            root,
            "diff",
            "--name-only",
            f"{checkpoint.checkpoint_based_on_head_sha}..{live_head}",
        ).splitlines()
        if line
    )
    classification = classify_handoff_delta(changed)
    payload = {
        "ok": classification.is_handoff_only,
        "checkpoint_based_on_head_sha": checkpoint.checkpoint_based_on_head_sha,
        "live_head_sha": live_head,
        "changed_paths": changed,
        "handoff_mutable_paths": classification.mutable_paths,
        "substantive_paths": classification.substantive_paths,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not classification.is_handoff_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
