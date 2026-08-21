from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import RawPayload, SourceDocument


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="PostgreSQL repository smoke source",
        publisher_domain="smoke.longcycle.invalid",
        kind=SourceKind.MANUAL,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    payload = RawPayload(
        content=b"longcycle postgres repository smoke\n",
        content_type="text/plain",
        canonical_url="https://smoke.longcycle.invalid/document.txt",
        status_code=200,
        headers={"etag": '"smoke-v1"'},
        retrieved_at=datetime(2026, 8, 21, 0, 0, tzinfo=UTC),
    )
    document = SourceDocument.from_payload(
        source_id=source.id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id="postgres-smoke-v1",
        title="PostgreSQL repository smoke document",
        published_at=datetime(2026, 8, 20, 0, 0, tzinfo=UTC),
        first_known_at=datetime(2026, 8, 21, 0, 0, tzinfo=UTC),
        metadata={"requested_url": payload.canonical_url},
    )

    repository = PostgresResearchRepository(dsn, bucket_name="smoke")
    try:
        saved = await repository.save_document(document)
        loaded = await repository.document_by_hash(
            source.id,
            payload.canonical_url,
            payload.sha256,
            "postgres-smoke-v1",
        )
        if loaded is None:
            raise AssertionError("document_by_hash did not return the persisted document")
        if loaded.id != saved.id:
            raise AssertionError("persisted document identity changed on lookup")
        if loaded.content_sha256 != payload.sha256:
            raise AssertionError("persisted content digest changed on lookup")
        if loaded.first_known_at != document.first_known_at:
            raise AssertionError("first_known_at changed on lookup")
    finally:
        await repository.close()

    print("POSTGRES_REPOSITORY_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
