from __future__ import annotations

import argparse
from pathlib import Path

from longcycle.application.fresh_agent_drill import validate_fresh_agent_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Fresh-Agent Continuity Drill v3 report."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to this script's repository root.",
    )
    parser.add_argument(
        "--skip-git-provenance",
        action="store_true",
        help="Validate report schema/cue integrity without checking the report-only commit provenance.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    report_path = args.report
    if not report_path.is_absolute():
        report_path = (root / report_path).resolve()

    report = validate_fresh_agent_report(
        root,
        report_path,
        require_git_provenance=not args.skip_git_provenance,
    )
    print(
        "FRESH_AGENT_DRILL_V3_REPORT_PASS "
        f"sequence={report.continuity_sequence} "
        f"subject_head={report.subject_head} "
        f"overall={report.overall_conclusion}"
    )


if __name__ == "__main__":
    main()
