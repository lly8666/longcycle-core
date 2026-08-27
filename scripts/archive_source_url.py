from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from longcycle.adapters.sources.http import HttpDocumentSource
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.s3 import S3ArchiveStore
from longcycle.application.source_archive import DocumentArchiver
from longcycle.config import Settings
from longcycle.domain.models import DiscoveryItem
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.source import FetchContext


def _aware_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("datetime must include a timezone offset")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and archive one known HTTP(S) source version without model extraction, "
            "EvidenceFragment creation or Fact/Judgment promotion."
        )
    )
    parser.add_argument("--source-id", type=UUID, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--external-id")
    parser.add_argument("--title")
    parser.add_argument("--published-at", type=_aware_datetime)
    parser.add_argument("--first-known-at", type=_aware_datetime)
    parser.add_argument("--evidence-task-id")
    parser.add_argument("--maximum-bytes", type=int, default=50 * 1024 * 1024)
    return parser


def _archive_store(settings: Settings) -> tuple[ArchiveStore, str]:
    if settings.blob_backend == "filesystem":
        root = settings.blob_root.resolve()
        return FileSystemArchiveStore(root), f"filesystem:{root}"
    if settings.s3_bucket is None:
        raise RuntimeError("LONGCYCLE_S3_BUCKET is required for the s3 blob backend")
    return (
        S3ArchiveStore(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
        ),
        settings.s3_bucket,
    )


async def _run(args: argparse.Namespace) -> dict[str, object]:
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError(
            "LONGCYCLE_DATABASE_URL is required because archive-only ingestion must persist "
            "SourceDocument metadata, not only blob bytes"
        )
    if args.maximum_bytes < 1:
        raise ValueError("--maximum-bytes must be positive")

    archive, bucket_name = _archive_store(settings)
    repository = PostgresResearchRepository(settings.database_url, bucket_name=bucket_name)
    try:
        source = await repository.get_source(args.source_id)
        if source.plugin != HttpDocumentSource.plugin_name:
            raise ValueError(
                f"source {source.id} uses plugin {source.plugin!r}; archive_source_url requires "
                f"{HttpDocumentSource.plugin_name!r}"
            )
        plugin = HttpDocumentSource(source)
        metadata: dict[str, object] = {"ingest_mode": "archive_only"}
        if args.evidence_task_id:
            metadata["evidence_task_id"] = args.evidence_task_id
        item_kwargs: dict[str, object] = {
            "source_id": source.id,
            "external_id": args.external_id,
            "url": args.url,
            "title_hint": args.title,
            "published_at_hint": args.published_at,
            "metadata": metadata,
        }
        if args.first_known_at is not None:
            item_kwargs["discovered_at"] = args.first_known_at
        item = DiscoveryItem.model_validate(item_kwargs)

        result = await DocumentArchiver(
            repository=repository,
            archive=archive,
        ).archive_document(
            plugin=plugin,
            item=item,
            fetch_context=FetchContext(
                source=source,
                maximum_bytes=args.maximum_bytes,
            ),
        )
        document = result.document
        return {
            "document_id": str(document.id),
            "was_new_document": result.was_new_document,
            "canonical_url": document.canonical_url,
            "content_sha256": document.content_sha256,
            "blob_key": document.blob_key,
            "byte_length": document.byte_length,
            "content_type": document.content_type,
            "published_at": document.published_at.isoformat() if document.published_at else None,
            "first_known_at": document.first_known_at.isoformat(),
            "retrieved_at": document.retrieved_at.isoformat(),
            "evidence_created": False,
            "assertions_created": False,
        }
    finally:
        await repository.close()


def main() -> None:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        raise SystemExit(1) from exc
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
