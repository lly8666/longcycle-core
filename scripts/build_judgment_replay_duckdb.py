from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a small immutable DuckDB overlay for point-in-time Judgment replay. "
            "The source evidence DuckDB remains unchanged and is referenced by SHA-256."
        )
    )
    parser.add_argument("projection", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def _load_projection(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("judgment projection must be a JSON object")
    if payload.get("schema_version") != "longcycle-grounded-judgment-projection/v1":
        raise ValueError("unexpected grounded judgment projection schema")
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("judgment projection must contain judgments")
    return payload


def _evidence_ids(row: dict[str, Any]) -> list[str]:
    evidence = row.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("projected judgment must retain statement evidence")
    ids: list[str] = []
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("evidence_fragment_id"), str):
            raise ValueError("projected judgment evidence is malformed")
        ids.append(item["evidence_fragment_id"])
    return ids


def build_overlay(projection: Path, output: Path) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("install the project duckdb extra to build a judgment replay overlay") from exc

    payload = _load_projection(projection)
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(output))
    try:
        connection.execute(
            """
            CREATE TABLE judgment_index (
                judgment_key VARCHAR PRIMARY KEY,
                judgment_id UUID NOT NULL,
                subject_entity_id UUID NOT NULL,
                speaker_name_text VARCHAR NOT NULL,
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
                evidence_fragment_ids JSON NOT NULL
            )
            """
        )
        for row in payload["judgments"]:
            if not isinstance(row, dict):
                raise ValueError("projected judgment row must be an object")
            connection.execute(
                "INSERT INTO judgment_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    row["judgment_key"],
                    row["judgment_id"],
                    row["subject_entity_id"],
                    row["speaker_name_text"],
                    row["topic_code"],
                    row["judgment_kind"],
                    row["target_time_kind"],
                    row.get("target_at"),
                    row.get("target_from"),
                    row.get("target_to"),
                    row["target_precision"],
                    row.get("target_text"),
                    row["value_kind"],
                    row.get("value_text"),
                    row["summary"],
                    row["first_known_at"],
                    json.dumps(_evidence_ids(row)),
                ],
            )
        manifest = {
            "schema_version": "longcycle-portable-judgment-replay-duckdb/v1",
            "source_projection_sha256": hashlib.sha256(projection.read_bytes()).hexdigest(),
            "source_evidence_database_sha256": payload["source_database_sha256"],
            "task_id": payload["task_id"],
            "judgment_count": len(payload["judgments"]),
            "future_rows_must_be_filtered_in_sql": True,
        }
        connection.execute("CREATE TABLE overlay_manifest (manifest_json JSON NOT NULL)")
        connection.execute(
            "INSERT INTO overlay_manifest VALUES (?)",
            [json.dumps(manifest, sort_keys=True, separators=(",", ":"))],
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    return {
        **manifest,
        "output": str(output),
        "file_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "file_bytes": output.stat().st_size,
    }


def main() -> int:
    args = _parser().parse_args()
    print(json.dumps(build_overlay(args.projection, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
