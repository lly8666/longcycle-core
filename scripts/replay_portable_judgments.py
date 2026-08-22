from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from longcycle.application.judgment_replay import ReplayJudgment, build_judgment_replay_snapshot


def parse_instant(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("cutoff must include a timezone")
    return parsed


def read_visible_judgments(database: Path, cutoff: datetime) -> tuple[ReplayJudgment, ...]:
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
                judgment_key, judgment_id, subject_entity_id, speaker_name_text,
                topic_code, judgment_kind, target_time_kind, target_at, target_from,
                target_to, target_precision, target_text, value_kind, value_text,
                summary, first_known_at, CAST(evidence_fragment_ids AS VARCHAR)
            FROM judgment_index
            WHERE first_known_at <= ?
            ORDER BY first_known_at, judgment_key
            """,
            [cutoff],
        ).fetchall()
    finally:
        connection.close()

    return tuple(
        ReplayJudgment(
            judgment_key=row[0],
            judgment_id=row[1],
            subject_entity_id=row[2],
            speaker_name_text=row[3],
            topic_code=row[4],
            judgment_kind=row[5],
            target_time_kind=row[6],
            target_at=row[7],
            target_from=row[8],
            target_to=row[9],
            target_precision=row[10],
            target_text=row[11],
            value_kind=row[12],
            value_text=row[13],
            summary=row[14],
            first_known_at=row[15],
            evidence_fragment_ids=tuple(UUID(item) for item in json.loads(row[16])),
        )
        for row in rows
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a no-lookahead Longcycle Judgment replay from a portable DuckDB overlay."
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--cutoff", required=True, type=parse_instant)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    judgments = read_visible_judgments(args.database, args.cutoff)
    snapshot = build_judgment_replay_snapshot(judgments, knowledge_cutoff=args.cutoff)
    payload = snapshot.model_dump_json(indent=2)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
