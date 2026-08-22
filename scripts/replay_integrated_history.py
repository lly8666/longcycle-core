from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from longcycle.domain.models import require_aware_datetime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay canonical Reality, contemporaneous Judgment and later Outcome at one knowledge cutoff."
    )
    parser.add_argument("database", type=Path)
    parser.add_argument("cutoff")
    parser.add_argument("--output", type=Path)
    return parser


def _parse_cutoff(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    checked = require_aware_datetime(parsed, "knowledge_cutoff")
    assert checked is not None
    return checked


def _rows(connection: duckdb.DuckDBPyConnection, sql: str, cutoff: datetime) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, [cutoff])
    names = [item[0] for item in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def replay(database: Path, cutoff: datetime) -> dict[str, Any]:
    connection = duckdb.connect(str(database), read_only=True)
    try:
        reality = _rows(
            connection,
            """
            SELECT * FROM reality_timeline
            WHERE market_known_at <= ?
            ORDER BY market_known_at, canonical_fact_version_id
            """,
            cutoff,
        )
        judgments = _rows(
            connection,
            """
            SELECT * FROM judgment_timeline
            WHERE first_known_at <= ?
            ORDER BY first_known_at, judgment_id
            """,
            cutoff,
        )
        outcomes = _rows(
            connection,
            """
            SELECT * FROM outcome_timeline
            WHERE outcome_first_known_at <= ?
            ORDER BY outcome_first_known_at, evaluation_id
            """,
            cutoff,
        )
    finally:
        connection.close()
    return {
        "schema_version": "longcycle-integrated-no-lookahead-replay/v1",
        "knowledge_cutoff": cutoff.isoformat(),
        "reality": reality,
        "judgments": judgments,
        "outcomes": outcomes,
        "boundary": {
            "future_rows_are_filtered_in_sql_before_materialization": True,
            "reality_is_canonical_fact_only": True,
            "judgment_is_not_rewritten_by_outcome": True,
            "outcome_is_separate_from_original_judgment": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    payload = replay(args.database, _parse_cutoff(args.cutoff))
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
