from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from longcycle.adapters.storage.duckdb_epistemic import DuckDBEpistemicMemoryReader
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import require_aware_datetime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replay canonical Reality, contemporaneous Judgment and later Outcome at one knowledge cutoff "
            "through the typed portable-memory boundary."
        )
    )
    parser.add_argument("database", type=Path)
    parser.add_argument("cutoff")
    parser.add_argument(
        "--subject-id",
        action="append",
        default=[],
        help="Entity UUID to include in the point-in-time replay.",
    )
    parser.add_argument(
        "--industry-node-id",
        action="append",
        default=[],
        help="Industry taxonomy-node UUID to include in the point-in-time replay.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def _parse_cutoff(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    checked = require_aware_datetime(parsed, "knowledge_cutoff")
    assert checked is not None
    return checked


async def replay(
    database: Path,
    cutoff: datetime,
    subjects: tuple[MemorySubjectRef, ...],
) -> dict[str, object]:
    if not subjects:
        raise ValueError("at least one --subject-id or --industry-node-id is required")
    reader = DuckDBEpistemicMemoryReader(database)
    snapshot = await reader.snapshot(subjects, knowledge_cutoff=cutoff)
    return {
        "schema_version": "longcycle-integrated-no-lookahead-replay/v2",
        "knowledge_cutoff": cutoff.isoformat(),
        "reality": [item.model_dump(mode="json") for item in snapshot.reality],
        "judgments": [item.model_dump(mode="json") for item in snapshot.judgments],
        "outcomes": [item.model_dump(mode="json") for item in snapshot.outcomes],
        "boundary": {
            "typed_epistemic_reader_is_semantic_contract": True,
            "future_rows_are_filtered_before_snapshot_materialization": True,
            "reality_is_canonical_fact_only": True,
            "judgment_is_not_rewritten_by_outcome": True,
            "outcome_is_separate_from_original_judgment": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    subjects = tuple(
        [MemorySubjectRef(entity_id=UUID(value)) for value in args.subject_id]
        + [MemorySubjectRef(industry_node_id=UUID(value)) for value in args.industry_node_id]
    )
    payload = asyncio.run(replay(args.database, _parse_cutoff(args.cutoff), subjects))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
