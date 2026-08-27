from __future__ import annotations

import argparse
import json
from pathlib import Path

from longcycle.application.epistemic_trajectory import execute_epistemic_trajectory_receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one CAP-0007 bounded epistemic trajectory: transport-neutral preserved "
            "material -> Grounded Evidence -> optional Reality/Judgment/Outcome -> sealed "
            "DuckDB -> point-in-time no-lookahead replay. Source restoration happens outside "
            "this runner."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--material-root", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--skip-db-upgrade",
        action="store_true",
        help="Skip `longcycle --json db upgrade` when the caller already migrated PostgreSQL.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    payload = execute_epistemic_trajectory_receipt(
        repo_root=Path.cwd(),
        spec_path=args.spec,
        material_root_path=args.material_root,
        work_dir=args.work_dir,
        output_path=args.output,
        skip_db_upgrade=bool(args.skip_db_upgrade),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
