from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from uuid import UUID

from longcycle.adapters.storage.duckdb_epistemic import seal_industrial_memory
from longcycle.adapters.storage.postgres_epistemic import PostgresEpistemicMemoryReader
from longcycle.domain.epistemic import MemorySubjectRef


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Seal canonical Reality, contemporaneous Judgment and later Outcome rows "
            "into a portable DuckDB generation through the typed industrial-memory boundary."
        )
    )
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--subject-id",
        action="append",
        default=[],
        help="Entity UUID. Kept as the compatibility spelling used by existing benchmark workflows.",
    )
    parser.add_argument(
        "--industry-node-id",
        action="append",
        default=[],
        help="Industry taxonomy-node UUID.",
    )
    parser.add_argument("--manifest-output", type=Path)
    return parser


async def _load_timeline(dsn: str, subjects: tuple[MemorySubjectRef, ...]):
    reader = PostgresEpistemicMemoryReader(dsn)
    try:
        return await reader.timeline(subjects)
    finally:
        await reader.close()


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    subjects = tuple(
        [MemorySubjectRef(entity_id=UUID(value)) for value in args.subject_id]
        + [MemorySubjectRef(industry_node_id=UUID(value)) for value in args.industry_node_id]
    )
    if not subjects:
        raise ValueError("at least one --subject-id or --industry-node-id is required")

    timeline = asyncio.run(_load_timeline(dsn, subjects))
    manifest = seal_industrial_memory(args.output, timeline)
    manifest = {
        **manifest,
        "source": {
            "kind": "typed_epistemic_memory_reader",
            "adapter": "postgresql",
        },
    }
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.manifest_output:
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
