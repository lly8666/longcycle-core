from __future__ import annotations

import argparse
import json
from pathlib import Path

from longcycle.application.research_orchestration import execute_research_orchestration_receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one repository-owned Longcycle research orchestration contract: verify "
            "preserved source material, apply explicit Evidence-spec repairs, execute Grounded "
            "Evidence and optionally the existing Reality projection path. V2 accepts a "
            "transport-neutral material root; --source-pack is legacy v1 compatibility only."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--source-pack", type=Path)
    parser.add_argument("--material-root", type=Path)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--skip-db-upgrade",
        action="store_true",
        help="Skip `longcycle --json db upgrade` when the caller has already migrated PostgreSQL.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    payload = execute_research_orchestration_receipt(
        repo_root=Path.cwd(),
        spec_path=args.spec,
        source_pack_path=args.source_pack,
        material_root_path=args.material_root,
        work_dir=args.work_dir,
        output_path=args.output,
        skip_db_upgrade=bool(args.skip_db_upgrade),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
