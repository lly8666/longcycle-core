from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import duckdb
import psycopg
from psycopg.rows import dict_row


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export canonical Reality, contemporaneous Judgment and later Outcome rows into a portable replay DuckDB."
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--subject-id", action="append", required=True)
    parser.add_argument("--manifest-output", type=Path)
    return parser


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def _fetch(dsn: str, subject_ids: list[UUID]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        reality = list(
            connection.execute(
                """
                SELECT canonical.id AS canonical_fact_version_id,
                       key.subject_entity_id, key.predicate_code,
                       canonical.value_kind, canonical.value_text,
                       canonical.valid_from, canonical.valid_to,
                       canonical.valid_time_precision, canonical.valid_time_text,
                       canonical.market_known_at, canonical.confidence,
                       canonical.publication_status
                FROM research.canonical_fact_versions canonical
                JOIN research.fact_keys key ON key.id = canonical.fact_key_id
                WHERE key.subject_entity_id = ANY(%s::uuid[])
                  AND canonical.system_to IS NULL
                  AND canonical.publication_status = 'trusted'
                ORDER BY canonical.market_known_at, canonical.id
                """,
                (subject_ids,),
            ).fetchall()
        )
        judgments = list(
            connection.execute(
                """
                SELECT judgment.id AS judgment_id, judgment.subject_entity_id,
                       judgment.speaker_name_text, judgment.topic_code,
                       judgment.judgment_kind, judgment.target_time_kind,
                       judgment.target_at, judgment.target_from, judgment.target_to,
                       judgment.target_precision, judgment.target_text,
                       judgment.value_kind, judgment.value_text, judgment.summary,
                       judgment.first_known_at, judgment.metadata,
                       COALESCE(array_agg(link.evidence_fragment_id::text ORDER BY link.evidence_fragment_id)
                                FILTER (WHERE link.evidence_fragment_id IS NOT NULL), '{}') AS evidence_fragment_ids
                FROM research.judgment_assertions judgment
                LEFT JOIN research.judgment_evidence link ON link.judgment_id = judgment.id
                WHERE judgment.subject_entity_id = ANY(%s::uuid[])
                GROUP BY judgment.id
                ORDER BY judgment.first_known_at, judgment.id
                """,
                (subject_ids,),
            ).fetchall()
        )
        outcomes = list(
            connection.execute(
                """
                SELECT evaluation.id AS evaluation_id, evaluation.judgment_id,
                       judgment.subject_entity_id,
                       evaluation.canonical_fact_version_id,
                       evaluation.outcome_evidence_fragment_id,
                       evaluation.evaluation_status,
                       evaluation.outcome_from, evaluation.outcome_to,
                       evaluation.outcome_precision, evaluation.outcome_text,
                       evaluation.outcome_first_known_at,
                       evaluation.timing_relation, evaluation.timing_delta_value,
                       evaluation.timing_delta_unit, evaluation.explanation,
                       evaluation.evaluator_name, evaluation.evaluator_version
                FROM research.judgment_outcome_evaluations evaluation
                JOIN research.judgment_assertions judgment ON judgment.id = evaluation.judgment_id
                WHERE judgment.subject_entity_id = ANY(%s::uuid[])
                  AND evaluation.outcome_first_known_at IS NOT NULL
                ORDER BY evaluation.outcome_first_known_at, evaluation.id
                """,
                (subject_ids,),
            ).fetchall()
        )
    return reality, judgments, outcomes


def _write(path: Path, reality: list[dict[str, Any]], judgments: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> None:
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    try:
        connection.execute(
            """
            CREATE TABLE reality_timeline (
                canonical_fact_version_id VARCHAR PRIMARY KEY,
                subject_entity_id VARCHAR NOT NULL,
                predicate_code VARCHAR NOT NULL,
                value_kind VARCHAR NOT NULL,
                value_text VARCHAR,
                valid_from TIMESTAMPTZ,
                valid_to TIMESTAMPTZ,
                valid_time_precision VARCHAR NOT NULL,
                valid_time_text VARCHAR,
                market_known_at TIMESTAMPTZ NOT NULL,
                confidence DOUBLE NOT NULL,
                publication_status VARCHAR NOT NULL
            )
            """
        )
        for row in reality:
            connection.execute(
                "INSERT INTO reality_timeline VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    str(row["canonical_fact_version_id"]), str(row["subject_entity_id"]),
                    row["predicate_code"], row["value_kind"], row["value_text"],
                    row["valid_from"], row["valid_to"], row["valid_time_precision"],
                    row["valid_time_text"], row["market_known_at"], float(row["confidence"]),
                    row["publication_status"],
                ],
            )

        connection.execute(
            """
            CREATE TABLE judgment_timeline (
                judgment_id VARCHAR PRIMARY KEY,
                judgment_key VARCHAR,
                subject_entity_id VARCHAR NOT NULL,
                speaker_name_text VARCHAR,
                topic_code VARCHAR NOT NULL,
                judgment_kind VARCHAR NOT NULL,
                target_time_kind VARCHAR NOT NULL,
                target_at TIMESTAMPTZ,
                target_from TIMESTAMPTZ,
                target_to TIMESTAMPTZ,
                target_precision VARCHAR NOT NULL,
                target_text VARCHAR,
                value_kind VARCHAR NOT NULL,
                value_text VARCHAR,
                summary VARCHAR NOT NULL,
                first_known_at TIMESTAMPTZ NOT NULL,
                evidence_fragment_ids JSON NOT NULL,
                metadata JSON NOT NULL
            )
            """
        )
        for row in judgments:
            metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
            connection.execute(
                "INSERT INTO judgment_timeline VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    str(row["judgment_id"]), metadata.get("judgment_key"), str(row["subject_entity_id"]),
                    row["speaker_name_text"], row["topic_code"], row["judgment_kind"],
                    row["target_time_kind"], row["target_at"], row["target_from"], row["target_to"],
                    row["target_precision"], row["target_text"], row["value_kind"], row["value_text"],
                    row["summary"], row["first_known_at"], _json(row["evidence_fragment_ids"]), _json(metadata),
                ],
            )

        connection.execute(
            """
            CREATE TABLE outcome_timeline (
                evaluation_id VARCHAR PRIMARY KEY,
                judgment_id VARCHAR NOT NULL,
                subject_entity_id VARCHAR NOT NULL,
                canonical_fact_version_id VARCHAR,
                outcome_evidence_fragment_id VARCHAR,
                evaluation_status VARCHAR NOT NULL,
                outcome_from TIMESTAMPTZ,
                outcome_to TIMESTAMPTZ,
                outcome_precision VARCHAR NOT NULL,
                outcome_text VARCHAR,
                outcome_first_known_at TIMESTAMPTZ NOT NULL,
                timing_relation VARCHAR NOT NULL,
                timing_delta_value DECIMAL(40,12),
                timing_delta_unit VARCHAR,
                explanation VARCHAR,
                evaluator_name VARCHAR NOT NULL,
                evaluator_version VARCHAR NOT NULL
            )
            """
        )
        for row in outcomes:
            connection.execute(
                "INSERT INTO outcome_timeline VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    str(row["evaluation_id"]), str(row["judgment_id"]), str(row["subject_entity_id"]),
                    str(row["canonical_fact_version_id"]) if row["canonical_fact_version_id"] else None,
                    str(row["outcome_evidence_fragment_id"]) if row["outcome_evidence_fragment_id"] else None,
                    row["evaluation_status"], row["outcome_from"], row["outcome_to"],
                    row["outcome_precision"], row["outcome_text"], row["outcome_first_known_at"],
                    row["timing_relation"], row["timing_delta_value"], row["timing_delta_unit"],
                    row["explanation"], row["evaluator_name"], row["evaluator_version"],
                ],
            )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()


def _verify(path: Path) -> dict[str, Any]:
    connection = duckdb.connect(str(path), read_only=True)
    try:
        counts = {
            "reality": int(connection.execute("SELECT count(*) FROM reality_timeline").fetchone()[0]),
            "judgments": int(connection.execute("SELECT count(*) FROM judgment_timeline").fetchone()[0]),
            "outcomes": int(connection.execute("SELECT count(*) FROM outcome_timeline").fetchone()[0]),
        }
        broken_outcome_judgments = int(
            connection.execute(
                """
                SELECT count(*) FROM outcome_timeline outcome
                LEFT JOIN judgment_timeline judgment ON judgment.judgment_id = outcome.judgment_id
                WHERE judgment.judgment_id IS NULL
                """
            ).fetchone()[0]
        )
        broken_outcome_reality = int(
            connection.execute(
                """
                SELECT count(*) FROM outcome_timeline outcome
                LEFT JOIN reality_timeline reality
                  ON reality.canonical_fact_version_id = outcome.canonical_fact_version_id
                WHERE outcome.canonical_fact_version_id IS NOT NULL
                  AND reality.canonical_fact_version_id IS NULL
                """
            ).fetchone()[0]
        )
    finally:
        connection.close()
    if broken_outcome_judgments or broken_outcome_reality:
        raise RuntimeError("integrated replay pack contains broken cross-layer references")
    return {
        "counts": counts,
        "broken_outcome_judgment_refs": broken_outcome_judgments,
        "broken_outcome_reality_refs": broken_outcome_reality,
    }


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    subject_ids = [UUID(value) for value in args.subject_id]
    reality, judgments, outcomes = _fetch(dsn, subject_ids)
    _write(args.output, reality, judgments, outcomes)
    verification = _verify(args.output)
    payload = {
        "schema_version": "longcycle-integrated-replay-duckdb/v1",
        "duckdb_version": duckdb.__version__,
        "file_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "file_bytes": args.output.stat().st_size,
        "subject_ids": [str(value) for value in subject_ids],
        "verification": verification,
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.manifest_output:
        args.manifest_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
