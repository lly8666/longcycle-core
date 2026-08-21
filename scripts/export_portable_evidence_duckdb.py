from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import duckdb
import psycopg
from psycopg.rows import dict_row

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.s3 import S3ArchiveStore
from longcycle.config import Settings
from longcycle.ports.archive import ArchiveStore


TABLES = (
    "evidence.publishers",
    "evidence.source_connectors",
    "evidence.content_blobs",
    "evidence.documents",
    "evidence.document_fetches",
    "evidence.document_versions",
    "evidence.artifacts",
    "evidence.evidence_fragments",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export one grounded-evidence execution into a portable DuckDB bundle. The bundle "
            "contains canonical row mirrors plus hot point-in-time indexes/page text, but never "
            "duplicates raw HTML/PDF source bytes from the content-addressed archive."
        )
    )
    parser.add_argument("execution", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-output", type=Path)
    return parser


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    raise TypeError(f"unsupported PostgreSQL value for canonical bundle export: {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    return json.dumps(_normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _row_id(row: dict[str, Any]) -> str:
    value = row.get("id")
    if value is not None:
        return str(value)
    return hashlib.sha256(_canonical_json(row).encode("utf-8")).hexdigest()


def _row_digest(row: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(row).encode("utf-8")).hexdigest()


def _table_digest(rows: list[dict[str, Any]]) -> str:
    digests = sorted(_row_digest(row) for row in rows)
    return hashlib.sha256("\n".join(digests).encode("utf-8")).hexdigest()


def _archive_store(settings: Settings) -> ArchiveStore:
    if settings.blob_backend == "filesystem":
        return FileSystemArchiveStore(settings.blob_root.resolve())
    if settings.s3_bucket is None:
        raise RuntimeError("LONGCYCLE_S3_BUCKET is required for the s3 blob backend")
    return S3ArchiveStore(bucket=settings.s3_bucket, endpoint_url=settings.s3_endpoint_url)


def _load_execution(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise ValueError("execution file must be a successful grounded-evidence execution result")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("schema_version") != "longcycle-grounded-evidence-execution/v1":
        raise ValueError("unexpected grounded-evidence execution schema")
    return result


def _uuid_list(values: list[str]) -> list[UUID]:
    return [UUID(value) for value in values]


def _fetch_rows(dsn: str, execution: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    documents = execution.get("documents")
    artifacts = execution.get("artifacts")
    fragments = execution.get("fragments")
    if not isinstance(documents, list) or not isinstance(artifacts, list) or not isinstance(fragments, list):
        raise ValueError("execution must contain document/artifact/fragment lists")

    document_version_ids = _uuid_list([str(row["document_id"]) for row in documents])
    source_ids = _uuid_list(sorted({str(row["source_id"]) for row in documents}))
    artifact_ids = _uuid_list([str(row["artifact_id"]) for row in artifacts])
    fragment_ids = _uuid_list([str(row["evidence_fragment_id"]) for row in fragments])

    rows: dict[str, list[dict[str, Any]]] = {}
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        rows["evidence.source_connectors"] = list(
            connection.execute(
                "SELECT * FROM evidence.source_connectors WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (source_ids,),
            ).fetchall()
        )
        rows["evidence.publishers"] = list(
            connection.execute(
                """
                SELECT publisher.*
                FROM evidence.publishers publisher
                JOIN evidence.source_connectors connector ON connector.publisher_id = publisher.id
                WHERE connector.id = ANY(%s::uuid[])
                ORDER BY publisher.id
                """,
                (source_ids,),
            ).fetchall()
        )
        rows["evidence.document_versions"] = list(
            connection.execute(
                "SELECT * FROM evidence.document_versions WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (document_version_ids,),
            ).fetchall()
        )
        logical_document_ids = [row["document_id"] for row in rows["evidence.document_versions"]]
        rows["evidence.documents"] = list(
            connection.execute(
                "SELECT * FROM evidence.documents WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (logical_document_ids,),
            ).fetchall()
        )
        rows["evidence.document_fetches"] = list(
            connection.execute(
                "SELECT * FROM evidence.document_fetches WHERE document_id = ANY(%s::uuid[]) ORDER BY id",
                (logical_document_ids,),
            ).fetchall()
        )
        rows["evidence.artifacts"] = list(
            connection.execute(
                "SELECT * FROM evidence.artifacts WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (artifact_ids,),
            ).fetchall()
        )
        rows["evidence.evidence_fragments"] = list(
            connection.execute(
                "SELECT * FROM evidence.evidence_fragments WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (fragment_ids,),
            ).fetchall()
        )
        blob_ids = {
            row["content_blob_id"] for row in rows["evidence.document_versions"]
        } | {
            row["content_blob_id"] for row in rows["evidence.artifacts"]
        }
        rows["evidence.content_blobs"] = list(
            connection.execute(
                "SELECT * FROM evidence.content_blobs WHERE id = ANY(%s::uuid[]) ORDER BY id",
                (list(blob_ids),),
            ).fetchall()
        )

    missing = [table for table in TABLES if table not in rows]
    if missing:
        raise RuntimeError(f"portable bundle exporter failed to collect tables: {missing}")
    return rows


async def _load_page_text(
    *,
    archive: ArchiveStore,
    rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    blobs = {str(row["id"]): row for row in rows["evidence.content_blobs"]}
    page_rows: list[dict[str, Any]] = []
    for artifact in rows["evidence.artifacts"]:
        if artifact.get("artifact_type") != "pdf-text-pages":
            continue
        blob = blobs[str(artifact["content_blob_id"])]
        payload = json.loads((await archive.get(str(blob["object_key"]))).decode("utf-8"))
        pages = payload.get("pages")
        if not isinstance(pages, list):
            raise ValueError("pdf-text-pages artifact has no pages array during bundle export")
        for page in pages:
            if not isinstance(page, dict) or not isinstance(page.get("page"), int) or not isinstance(page.get("text"), str):
                raise ValueError("invalid pdf-text-pages page during bundle export")
            page_rows.append(
                {
                    "document_version_id": str(artifact["document_version_id"]),
                    "artifact_id": str(artifact["id"]),
                    "page": int(page["page"]),
                    "text": page["text"],
                    "producer_name": str(artifact["producer_name"]),
                    "producer_version": str(artifact["producer_version"]),
                }
            )
    return page_rows


def _parse_claim_context(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("structured_payload")
    if not isinstance(payload, dict):
        return {}
    context = payload.get("claim_context")
    return context if isinstance(context, dict) else {}


def _write_bundle(
    *,
    path: Path,
    execution: dict[str, Any],
    rows: dict[str, list[dict[str, Any]]],
    page_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    try:
        connection.execute(
            """
            CREATE TABLE canonical_rows (
                table_name VARCHAR NOT NULL,
                row_id VARCHAR NOT NULL,
                row_json JSON NOT NULL,
                row_sha256 VARCHAR NOT NULL,
                PRIMARY KEY (table_name, row_id)
            )
            """
        )
        for table_name in TABLES:
            for row in rows[table_name]:
                rendered = _canonical_json(row)
                connection.execute(
                    "INSERT INTO canonical_rows VALUES (?, ?, ?, ?)",
                    [table_name, _row_id(row), rendered, hashlib.sha256(rendered.encode("utf-8")).hexdigest()],
                )

        connection.execute(
            """
            CREATE TABLE document_index (
                document_key VARCHAR PRIMARY KEY,
                document_version_id VARCHAR NOT NULL,
                source_id VARCHAR NOT NULL,
                canonical_retrieval_url VARCHAR NOT NULL,
                original_source_url VARCHAR,
                content_sha256 VARCHAR NOT NULL,
                blob_key VARCHAR NOT NULL,
                byte_length BIGINT NOT NULL,
                content_type VARCHAR NOT NULL,
                published_at TIMESTAMPTZ,
                first_known_at TIMESTAMPTZ NOT NULL,
                retrieval_provenance JSON NOT NULL
            )
            """
        )
        for row in execution["documents"]:
            connection.execute(
                "INSERT INTO document_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    row["document_key"], row["document_id"], row["source_id"],
                    row["canonical_retrieval_url"], row.get("original_source_url"),
                    row["content_sha256"], row["blob_key"], row["byte_length"], row["content_type"],
                    row.get("published_at"), row["first_known_at"], _canonical_json(row.get("retrieval_provenance") or {}),
                ],
            )

        fragment_rows = {str(row["id"]): row for row in rows["evidence.evidence_fragments"]}
        connection.execute(
            """
            CREATE TABLE evidence_index (
                fragment_key VARCHAR PRIMARY KEY,
                evidence_fragment_id VARCHAR NOT NULL,
                document_version_id VARCHAR NOT NULL,
                artifact_id VARCHAR,
                locator VARCHAR NOT NULL,
                excerpt VARCHAR NOT NULL,
                fragment_sha256 VARCHAR NOT NULL,
                claim_context JSON NOT NULL,
                claim_role VARCHAR,
                known_time_upper_bound TIMESTAMPTZ,
                known_time_precision VARCHAR,
                valid_effective_time JSON,
                expectation_horizon JSON
            )
            """
        )
        for execution_row in execution["fragments"]:
            persisted = fragment_rows[str(execution_row["evidence_fragment_id"])]
            context = _parse_claim_context(persisted)
            known_time = context.get("known_time") if isinstance(context.get("known_time"), dict) else {}
            connection.execute(
                "INSERT INTO evidence_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    execution_row["fragment_key"], str(persisted["id"]), str(persisted["document_version_id"]),
                    str(persisted["artifact_id"]) if persisted.get("artifact_id") is not None else None,
                    execution_row["locator"], persisted["excerpt"], persisted["fragment_sha256"],
                    _canonical_json(context), context.get("claim_role"), known_time.get("upper_bound"),
                    known_time.get("precision"),
                    _canonical_json(context["valid_effective_time"]) if context.get("valid_effective_time") is not None else None,
                    _canonical_json(context["expectation_horizon"]) if context.get("expectation_horizon") is not None else None,
                ],
            )

        connection.execute(
            """
            CREATE TABLE page_text (
                document_version_id VARCHAR NOT NULL,
                artifact_id VARCHAR NOT NULL,
                page INTEGER NOT NULL,
                text VARCHAR NOT NULL,
                producer_name VARCHAR NOT NULL,
                producer_version VARCHAR NOT NULL,
                PRIMARY KEY (artifact_id, page)
            )
            """
        )
        for row in page_rows:
            connection.execute(
                "INSERT INTO page_text VALUES (?, ?, ?, ?, ?, ?)",
                [row["document_version_id"], row["artifact_id"], row["page"], row["text"], row["producer_name"], row["producer_version"]],
            )

        connection.execute(
            """
            CREATE VIEW evidence_timeline AS
            SELECT fragment_key, evidence_fragment_id, document_version_id, artifact_id,
                   locator, excerpt, claim_role, known_time_upper_bound, known_time_precision,
                   valid_effective_time, expectation_horizon
            FROM evidence_index
            ORDER BY known_time_upper_bound NULLS LAST, fragment_key
            """
        )
        table_manifest = {
            table: {"row_count": len(rows[table]), "canonical_sha256": _table_digest(rows[table])}
            for table in TABLES
        }
        internal_manifest = {
            "schema_version": "longcycle-portable-evidence-duckdb/v1",
            "producer": "duckdb",
            "producer_version": duckdb.__version__,
            "task_id": execution["task_id"],
            "raw_source_bytes_embedded": False,
            "canonical_tables": table_manifest,
            "document_index_rows": len(execution["documents"]),
            "evidence_index_rows": len(execution["fragments"]),
            "page_text_rows": len(page_rows),
        }
        connection.execute("CREATE TABLE bundle_manifest (manifest_json JSON NOT NULL)")
        connection.execute("INSERT INTO bundle_manifest VALUES (?)", [_canonical_json(internal_manifest)])
        connection.execute("CHECKPOINT")
    finally:
        connection.close()
    return internal_manifest


def _verify_bundle(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    connection = duckdb.connect(str(path), read_only=True)
    open_seconds = time.perf_counter() - started
    try:
        counts = {
            "canonical_rows": int(connection.execute("SELECT count(*) FROM canonical_rows").fetchone()[0]),
            "documents": int(connection.execute("SELECT count(*) FROM document_index").fetchone()[0]),
            "evidence": int(connection.execute("SELECT count(*) FROM evidence_index").fetchone()[0]),
            "page_text": int(connection.execute("SELECT count(*) FROM page_text").fetchone()[0]),
        }
        for table_name, expected in manifest["canonical_tables"].items():
            values = [
                row[0]
                for row in connection.execute(
                    "SELECT row_sha256 FROM canonical_rows WHERE table_name = ? ORDER BY row_sha256",
                    [table_name],
                ).fetchall()
            ]
            digest = hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()
            if len(values) != int(expected["row_count"]) or digest != expected["canonical_sha256"]:
                raise ValueError(f"DuckDB canonical mirror mismatch for {table_name}")
        if counts["documents"] != int(manifest["document_index_rows"]):
            raise ValueError("DuckDB document index count mismatch")
        if counts["evidence"] != int(manifest["evidence_index_rows"]):
            raise ValueError("DuckDB evidence index count mismatch")
        broken_doc_refs = int(
            connection.execute(
                """
                SELECT count(*)
                FROM evidence_index evidence
                LEFT JOIN document_index document
                  ON document.document_version_id = evidence.document_version_id
                WHERE document.document_version_id IS NULL
                """
            ).fetchone()[0]
        )
        broken_artifact_refs = int(
            connection.execute(
                """
                SELECT count(*)
                FROM evidence_index evidence
                LEFT JOIN canonical_rows artifact
                  ON artifact.table_name = 'evidence.artifacts'
                 AND artifact.row_id = evidence.artifact_id
                WHERE evidence.artifact_id IS NOT NULL AND artifact.row_id IS NULL
                """
            ).fetchone()[0]
        )
        if broken_doc_refs or broken_artifact_refs:
            raise ValueError(
                f"DuckDB referential check failed: documents={broken_doc_refs}, artifacts={broken_artifact_refs}"
            )
        query_started = time.perf_counter()
        cutoff_count = int(
            connection.execute(
                "SELECT count(*) FROM evidence_timeline WHERE known_time_upper_bound <= TIMESTAMPTZ '2021-12-31 23:59:59+00'"
            ).fetchone()[0]
        )
        cutoff_seconds = time.perf_counter() - query_started
        roles = connection.execute(
            "SELECT claim_role, count(*) FROM evidence_timeline GROUP BY claim_role ORDER BY claim_role"
        ).fetchall()
    finally:
        connection.close()
    return {
        "read_only_open_seconds": open_seconds,
        "point_in_time_query_seconds": cutoff_seconds,
        "evidence_known_by_2021_year_end": cutoff_count,
        "claim_role_counts": {str(role): int(count) for role, count in roles},
        "counts": counts,
        "broken_document_refs": broken_doc_refs,
        "broken_artifact_refs": broken_artifact_refs,
    }


def main() -> None:
    args = _parser().parse_args()
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required for portable DuckDB export")
    execution = _load_execution(args.execution)
    rows = _fetch_rows(settings.database_url, execution)
    page_rows = asyncio.run(_load_page_text(archive=_archive_store(settings), rows=rows))
    manifest = _write_bundle(path=args.output, execution=execution, rows=rows, page_rows=page_rows)
    verification = _verify_bundle(args.output, manifest)
    file_bytes = args.output.stat().st_size
    file_sha256 = hashlib.sha256(args.output.read_bytes()).hexdigest()
    payload = {
        "ok": True,
        "schema_version": "longcycle-portable-evidence-duckdb-export/v1",
        "duckdb_version": duckdb.__version__,
        "output": str(args.output),
        "file_bytes": file_bytes,
        "file_sha256": file_sha256,
        "manifest": manifest,
        "verification": verification,
        "source_database_url_present": bool(os.environ.get("LONGCYCLE_DATABASE_URL")),
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.manifest_output is not None:
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
