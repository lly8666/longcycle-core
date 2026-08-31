from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from longcycle.application.handoff_freshness import classify_handoff_delta  # noqa: E402
from longcycle.application.session_handoff import SessionHandoffCheckpoint  # noqa: E402

MAX_AUDITED_COMMITS = 256
REMOTE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh the authoritative remote handoff branch, verify checkpoint ancestry, "
            "and classify every parent-to-child path after the substantive checkpoint."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--remote", default="origin")
    parser.add_argument(
        "--branch",
        help="Authoritative remote branch; defaults to current.json active_branch.",
    )
    return parser


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"git {' '.join(args)}: {detail}")
    return result


def _resolve_remote_head(root: Path, *, remote: str, branch: str) -> str:
    if REMOTE_NAME_PATTERN.fullmatch(remote) is None:
        raise ValueError("remote must be a configured remote name")
    if BRANCH_PATTERN.fullmatch(branch) is None or branch.startswith(("/", "-")) or ".." in branch:
        raise ValueError("branch contains unsafe ref characters")

    full_ref = f"refs/heads/{branch}"
    advertised = _git(root, "ls-remote", "--heads", remote, full_ref).stdout.splitlines()
    matches = [line.split() for line in advertised if line.strip()]
    if len(matches) != 1 or len(matches[0]) != 2 or matches[0][1] != full_ref:
        raise RuntimeError(f"authoritative remote branch {remote}/{branch} was not uniquely resolved")
    advertised_sha = matches[0][0]

    audit_ref = f"refs/longcycle/audit/{remote}/{branch}"
    _git(root, "fetch", "--no-tags", remote, f"+{full_ref}:{audit_ref}")
    fetched_sha = _git(root, "rev-parse", audit_ref).stdout.strip()
    if fetched_sha != advertised_sha:
        raise RuntimeError(
            f"remote ref changed while refreshing: advertised={advertised_sha} fetched={fetched_sha}"
        )
    return fetched_sha


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return _git(root, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0


def _edge_changed_paths(root: Path, *, base: str, head: str) -> tuple[tuple[str, ...], int]:
    """Union paths from every effective parent edge, preserving change-then-revert history."""

    commits = [
        line
        for line in _git(
            root,
            "rev-list",
            "--reverse",
            "--ancestry-path",
            f"{base}..{head}",
        ).stdout.splitlines()
        if line
    ]
    if len(commits) > MAX_AUDITED_COMMITS:
        raise RuntimeError(
            f"handoff delta has {len(commits)} commits; limit is {MAX_AUDITED_COMMITS}; "
            "reconcile it explicitly instead of treating it as a bounded startup delta"
        )

    changed: set[str] = set()
    edge_count = 0
    for commit in commits:
        parts = _git(root, "rev-list", "--parents", "-n", "1", commit).stdout.split()
        parents = parts[1:]
        effective_parents = [
            parent for parent in parents if parent == base or _is_ancestor(root, base, parent)
        ]
        if not effective_parents:
            raise RuntimeError(f"cannot identify an ancestry edge from checkpoint to {commit}")
        for parent in effective_parents:
            edge_count += 1
            paths = _git(
                root,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                parent,
                commit,
            ).stdout.splitlines()
            changed.update(path for path in paths if path)
    return tuple(sorted(changed)), edge_count


def main() -> None:
    args = _parser().parse_args()
    root = args.root.resolve()
    checkpoint = SessionHandoffCheckpoint.model_validate_json(
        (root / ".longcycle/handoff/current.json").read_text(encoding="utf-8")
    )
    branch = args.branch or checkpoint.active_branch
    live_head = _resolve_remote_head(root, remote=args.remote, branch=branch)
    ancestor = _is_ancestor(root, checkpoint.checkpoint_based_on_head_sha, live_head)
    if not ancestor:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "checkpoint base is not an ancestor of authoritative remote HEAD",
                    "remote": args.remote,
                    "branch": branch,
                    "checkpoint_based_on_head_sha": checkpoint.checkpoint_based_on_head_sha,
                    "remote_head_sha": live_head,
                },
                indent=2,
            )
        )
        raise SystemExit(1)

    changed, edge_count = _edge_changed_paths(
        root,
        base=checkpoint.checkpoint_based_on_head_sha,
        head=live_head,
    )
    classification = classify_handoff_delta(changed)
    payload = {
        "ok": classification.is_handoff_only,
        "authority": "refreshed_remote",
        "remote": args.remote,
        "branch": branch,
        "checkpoint_based_on_head_sha": checkpoint.checkpoint_based_on_head_sha,
        "remote_head_sha": live_head,
        "audited_edge_count": edge_count,
        "changed_paths": changed,
        "handoff_mutable_paths": classification.mutable_paths,
        "substantive_paths": classification.substantive_paths,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not classification.is_handoff_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
