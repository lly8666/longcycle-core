from __future__ import annotations

import argparse
import json
from pathlib import Path

from longcycle.application.memory_history import scan_memory_history


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit reachable Git history for blind-memory states that exceed the current campaign "
            "checkpoint."
        )
    )
    parser.add_argument("campaign_dir", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    audit = scan_memory_history(args.repo_root, args.campaign_dir)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(
        json.dumps(audit.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    current = audit.current_state
    print(
        "memory-history "
        f"commits={audit.commits_scanned} "
        f"unique_blind_trees={audit.unique_blind_trees_scanned}"
    )
    print(
        "current "
        f"raw={current.raw_leads} "
        f"formal_typed={current.formal_typed_leads} "
        f"commit={current.commit_sha}"
    )
    print(
        "historical-max-raw "
        f"raw={audit.max_raw_state.raw_leads} "
        f"formal_typed={audit.max_raw_state.formal_typed_leads} "
        f"commit={audit.max_raw_state.commit_sha}"
    )
    print(
        "historical-max-formal "
        f"raw={audit.max_formal_typed_state.raw_leads} "
        f"formal_typed={audit.max_formal_typed_state.formal_typed_leads} "
        f"commit={audit.max_formal_typed_state.commit_sha}"
    )
    print(f"candidates-exceeding-current={len(audit.candidates_exceeding_current)}")
    for state in audit.candidates_exceeding_current:
        print(
            "candidate "
            f"raw={state.raw_leads} "
            f"formal_typed={state.formal_typed_leads} "
            f"commit={state.commit_sha}"
        )


if __name__ == "__main__":
    main()
