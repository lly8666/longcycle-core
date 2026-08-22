#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from longcycle.application.historical_replay import ReplayEvidence, build_replay_snapshot


def parse_instant(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("cutoff must include a timezone")
    return parsed


def parse_json(value: str | None) -> dict[str, Any] | list[dict[str, Any]] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if parsed is None:
        return None
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
        return parsed
    raise ValueError("timeline JSON must be an object or a list of objects")


def read_visible_evidence(database: Path, cutoff: datetime) -> tuple[ReplayEvidence, ...]:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "DuckDB runtime is unavailable. Restore the handoff offline runtime pack "
            "or install the project duckdb extra."
        ) from exc

    connection = duckdb.connect(str(database), read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT
                fragment_key,
                evidence_fragment_id,
                document_version_id,
                artifact_id,
                locator,
                excerpt,
                claim_role,
                known_time_upper_bound,
                known_time_precision,
                CAST(valid_effective_time AS VARCHAR),
                CAST(expectation_horizon AS VARCHAR)
            FROM evidence_timeline
            WHERE known_time_upper_bound <= ?
            ORDER BY known_time_upper_bound, fragment_key
            """,
            [cutoff],
        ).fetchall()
    finally:
        connection.close()

    return tuple(
        ReplayEvidence(
            fragment_key=row[0],
            evidence_fragment_id=row[1],
            document_version_id=row[2],
            artifact_id=row[3],
            locator=row[4],
            excerpt=row[5],
            claim_role=row[6],
            known_time_upper_bound=row[7],
            known_time_precision=row[8],
            valid_effective_time=parse_json(row[9]),
            expectation_horizon=parse_json(row[10]),
        )
        for row in rows
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a no-lookahead Longcycle evidence replay from a portable DuckDB pack."
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--cutoff", required=True, type=parse_instant)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evidence = read_visible_evidence(args.database, args.cutoff)
    snapshot = build_replay_snapshot(evidence, knowledge_cutoff=args.cutoff)
    payload = snapshot.model_dump_json(indent=2)

    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
