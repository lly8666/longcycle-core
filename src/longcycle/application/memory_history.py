from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_FORMAL_MEMORY_JSONL_VERSION = re.compile(r"-v(?P<version>\d+)\.jsonl$")


@dataclass(frozen=True)
class MemoryHistoryState:
    commit_sha: str
    raw_leads: int
    formal_typed_leads: int
    jsonl_files: int
    formal_jsonl_files: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "commit_sha": self.commit_sha,
            "raw_leads": self.raw_leads,
            "formal_typed_leads": self.formal_typed_leads,
            "jsonl_files": self.jsonl_files,
            "formal_jsonl_files": self.formal_jsonl_files,
        }


@dataclass(frozen=True)
class MemoryHistoryAudit:
    current_head: str
    commits_scanned: int
    unique_blind_trees_scanned: int
    current_state: MemoryHistoryState
    max_raw_state: MemoryHistoryState
    max_formal_typed_state: MemoryHistoryState
    candidates_exceeding_current: tuple[MemoryHistoryState, ...]
    distinct_states: tuple[MemoryHistoryState, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "current_head": self.current_head,
            "commits_scanned": self.commits_scanned,
            "unique_blind_trees_scanned": self.unique_blind_trees_scanned,
            "current_state": self.current_state.to_dict(),
            "max_raw_state": self.max_raw_state.to_dict(),
            "max_formal_typed_state": self.max_formal_typed_state.to_dict(),
            "candidates_exceeding_current": [
                state.to_dict() for state in self.candidates_exceeding_current
            ],
            "distinct_states": [state.to_dict() for state in self.distinct_states],
        }


def _run_git_text(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def _run_git_bytes(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=True,
        capture_output=True,
    )
    return result.stdout


def _is_formal_memory_jsonl(path: str) -> bool:
    match = _FORMAL_MEMORY_JSONL_VERSION.search(Path(path).name)
    return match is not None and int(match.group("version")) >= 3


def _blind_tree_sha(repo_root: Path, commit_sha: str, blind_path: str) -> str | None:
    output = _run_git_text(repo_root, "ls-tree", commit_sha, "--", blind_path).strip()
    if not output:
        return None
    left, _path = output.split("\t", 1)
    parts = left.split()
    if len(parts) != 3 or parts[1] != "tree":
        raise ValueError(f"expected tree at {blind_path!r} in {commit_sha}")
    return parts[2]


def _tree_jsonl_blobs(repo_root: Path, tree_sha: str) -> tuple[tuple[str, str], ...]:
    output = _run_git_text(repo_root, "ls-tree", "-r", "-z", tree_sha)
    blobs: list[tuple[str, str]] = []
    for record in output.split("\0"):
        if not record:
            continue
        left, path = record.split("\t", 1)
        parts = left.split()
        if len(parts) != 3:
            raise ValueError(f"unexpected ls-tree record: {record!r}")
        _mode, kind, object_sha = parts
        if kind == "blob" and path.endswith(".jsonl"):
            blobs.append((path, object_sha))
    return tuple(sorted(blobs))


def _nonempty_line_count(repo_root: Path, blob_sha: str) -> int:
    content = _run_git_bytes(repo_root, "cat-file", "blob", blob_sha)
    return sum(1 for line in content.splitlines() if line.strip())


def scan_memory_history(
    repo_root: Path,
    campaign_dir: Path,
    *,
    max_candidates: int = 20,
    max_distinct_states: int = 50,
) -> MemoryHistoryAudit:
    """Scan every reachable Git ref for historical blind-memory count states.

    Raw memory and formal typed memory remain separate: v1/v2 JSONL contributes to
    raw history but only v3+ contributes to the formal typed count. The scan never
    mutates campaign artifacts.
    """

    repo_root = repo_root.resolve()
    campaign_dir = campaign_dir.resolve()
    blind_dir = campaign_dir / "blind"
    try:
        blind_path = blind_dir.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ValueError("campaign_dir must be inside repo_root") from exc

    current_head = _run_git_text(repo_root, "rev-parse", "HEAD").strip()
    commits = tuple(
        line.strip()
        for line in _run_git_text(repo_root, "rev-list", "--all", "--topo-order").splitlines()
        if line.strip()
    )
    if not commits:
        raise ValueError("git history contains no reachable commits")

    blob_line_counts: dict[str, int] = {}
    tree_counts: dict[str | None, tuple[int, int, int, int]] = {}
    states: list[MemoryHistoryState] = []

    for commit_sha in commits:
        tree_sha = _blind_tree_sha(repo_root, commit_sha, blind_path)
        counts = tree_counts.get(tree_sha)
        if counts is None:
            raw_leads = 0
            formal_typed_leads = 0
            jsonl_files = 0
            formal_jsonl_files = 0
            if tree_sha is not None:
                for path, blob_sha in _tree_jsonl_blobs(repo_root, tree_sha):
                    line_count = blob_line_counts.get(blob_sha)
                    if line_count is None:
                        line_count = _nonempty_line_count(repo_root, blob_sha)
                        blob_line_counts[blob_sha] = line_count
                    raw_leads += line_count
                    jsonl_files += 1
                    if _is_formal_memory_jsonl(path):
                        formal_typed_leads += line_count
                        formal_jsonl_files += 1
            counts = (raw_leads, formal_typed_leads, jsonl_files, formal_jsonl_files)
            tree_counts[tree_sha] = counts

        states.append(
            MemoryHistoryState(
                commit_sha=commit_sha,
                raw_leads=counts[0],
                formal_typed_leads=counts[1],
                jsonl_files=counts[2],
                formal_jsonl_files=counts[3],
            )
        )

    state_by_commit = {state.commit_sha: state for state in states}
    current_state = state_by_commit.get(current_head)
    if current_state is None:
        raise ValueError("HEAD is not reachable from git rev-list --all")

    max_raw_state = max(
        states,
        key=lambda state: (state.raw_leads, state.formal_typed_leads),
    )
    max_formal_typed_state = max(
        states,
        key=lambda state: (state.formal_typed_leads, state.raw_leads),
    )

    distinct_by_counts: dict[tuple[int, int, int, int], MemoryHistoryState] = {}
    for state in states:
        key = (
            state.raw_leads,
            state.formal_typed_leads,
            state.jsonl_files,
            state.formal_jsonl_files,
        )
        distinct_by_counts.setdefault(key, state)

    distinct_states = sorted(
        distinct_by_counts.values(),
        key=lambda state: (state.raw_leads, state.formal_typed_leads),
        reverse=True,
    )
    candidates = tuple(
        state
        for state in distinct_states
        if (
            state.raw_leads > current_state.raw_leads
            or state.formal_typed_leads > current_state.formal_typed_leads
        )
    )

    return MemoryHistoryAudit(
        current_head=current_head,
        commits_scanned=len(commits),
        unique_blind_trees_scanned=len(tree_counts),
        current_state=current_state,
        max_raw_state=max_raw_state,
        max_formal_typed_state=max_formal_typed_state,
        candidates_exceeding_current=candidates[:max_candidates],
        distinct_states=tuple(distinct_states[:max_distinct_states]),
    )
