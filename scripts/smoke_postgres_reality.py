from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID

import psycopg

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.reconciliation import Reconciler
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    QualityGrade,
    SourceKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import (
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    RawPayload,
    SourceDocument,
    TimeRange,
    stable_uuid_exact,
)


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="PostgreSQL canonical Reality smoke source",
        publisher_domain="reality-smoke.longcycle.invalid",
        kind=SourceKind.COMPANY,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    event_id = stable_uuid_exact("reality-smoke", "kemerton-first-product")
    with psycopg.connect(dsn) as connection:
        connection.execute(
            """
            INSERT INTO core.entities (
                id, entity_type, canonical_name, normalized_name, lifecycle_status
            ) VALUES (%s, 'event', %s, %s, 'active')
            ON CONFLICT (id) DO NOTHING
            """,
            (event_id, "Kemerton I first product", "kemerton i first product"),
        )

    known_at = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)
    payload = RawPayload(
        content=b"Kemerton I achieved first product in July 2022.\n",
        content_type="text/plain",
        canonical_url="https://reality-smoke.longcycle.invalid/kemerton.txt",
        retrieved_at=known_at,
    )
    document = SourceDocument.from_payload(
        source_id=source.id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id="kemerton-reality-smoke-v1",
        title="Kemerton Reality smoke",
        published_at=known_at,
        first_known_at=known_at,
    )
    repository = PostgresResearchRepository(dsn, bucket_name="smoke")
    try:
        document = await repository.save_document(document)
        evidence = EvidenceFragment.create(
            document.id,
            "text:0:46",
            "Kemerton I achieved first product in July 2022.",
        )
        await repository.save_evidence((evidence,))

        run_id = stable_uuid_exact("reality-smoke-extraction", str(document.id))
        fact = FactAssertion(
            id=stable_uuid_exact("reality-smoke-fact", str(evidence.id)),
            entity_type=EntityType.EVENT,
            entity_id=event_id,
            field_name="project.first_product_status",
            value="achieved first product",
            value_type=FactValueKind.TEXT,
            dimensions=FactDimensions(statistical_scope="project milestone"),
            dimensions_complete=True,
            valid_time_kind=ValidTimeKind.PERIOD,
            valid_time=TimeRange(
                start=datetime(2022, 7, 1, tzinfo=UTC),
                end=datetime(2022, 8, 1, tzinfo=UTC),
            ),
            valid_time_precision=TemporalPrecision.MONTH,
            valid_time_text="July 2022",
            source_published_at=known_at,
            known_at=known_at,
            source_id=source.id,
            document_id=document.id,
            evidence_fragment_id=evidence.id,
            extraction_run_id=run_id,
            extractor_name="grounded-reality-projection",
            extractor_version="1.0.0",
            confidence=1.0,
            quality=QualityComponents(
                source_quality=1.0,
                extraction_certainty=1.0,
                entity_match=1.0,
                time_unit_completeness=1.0,
                corroboration=1.0,
                freshness=1.0,
            ),
        )
        extraction = ExtractionEnvelope(
            run_id=run_id,
            document_id=document.id,
            extractor_name="grounded-reality-projection",
            extractor_version="1.0.0",
            schema_version="reality-smoke/v1",
            evidence=(evidence,),
            candidates=(fact,),
        )
        await repository.save_extraction(extraction)
        await repository.append_assertions((fact,))
        result = await repository.reconcile_assertion(fact, Reconciler())
        if result.decision.value != "accept":
            raise AssertionError(f"Reality smoke did not reconcile to canonical fact: {result}")
    finally:
        await repository.close()

    with psycopg.connect(dsn) as connection:
        assertion_row = connection.execute(
            """
            SELECT valid_time_precision, valid_time_text
            FROM research.fact_assertions
            WHERE id = %s
            """,
            (fact.id,),
        ).fetchone()
        if assertion_row != ("month", "July 2022"):
            raise AssertionError(f"assertion precision was not preserved: {assertion_row}")

        canonical = connection.execute(
            """
            SELECT valid_from, valid_to, valid_time_precision, valid_time_text, market_known_at
            FROM research.canonical_fact_versions
            WHERE system_to IS NULL AND publication_status = 'trusted'
              AND fact_key_id = (
                  SELECT id FROM research.fact_keys
                  WHERE subject_entity_id = %s
                    AND predicate_code = 'project.first_product_status'
              )
            """,
            (event_id,),
        ).fetchone()
        if canonical is None:
            raise AssertionError("canonical Reality row was not created")
        valid_from, valid_to, precision, source_time_text, market_known_at = canonical
        if precision != "month" or source_time_text != "July 2022":
            raise AssertionError(f"canonical precision was not inherited: {canonical}")
        if valid_from != datetime(2022, 7, 1, tzinfo=UTC) or valid_to != datetime(2022, 8, 1, tzinfo=UTC):
            raise AssertionError(f"canonical month bounds changed: {canonical}")
        if market_known_at != known_at:
            raise AssertionError(f"canonical known-time changed: {canonical}")

    print("POSTGRES_REALITY_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
