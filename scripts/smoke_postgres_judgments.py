from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID

from longcycle.adapters.storage.judgments import PostgresJudgmentRepository
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentRelationType,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    QualityGrade,
    SourceKind,
)
from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentEvidenceRef,
    JudgmentRelation,
)
from longcycle.domain.models import EvidenceFragment, ExtractionEnvelope, RawPayload, SourceDocument


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="PostgreSQL judgment smoke source",
        publisher_domain="judgment-smoke.longcycle.invalid",
        kind=SourceKind.MANUAL,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    payload = RawPayload(
        content=(
            b"Management expected first product during May 2022. "
            b"Later guidance revised the expected window to July 2022.\n"
        ),
        content_type="text/plain",
        canonical_url="https://judgment-smoke.longcycle.invalid/disclosure.txt",
        status_code=200,
        headers={},
        retrieved_at=datetime(2022, 6, 1, tzinfo=UTC),
    )
    document = SourceDocument.from_payload(
        source_id=source.id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id="judgment-smoke-v1",
        title="Judgment aggregate smoke disclosure",
        published_at=datetime(2022, 6, 1, tzinfo=UTC),
        first_known_at=datetime(2022, 6, 1, tzinfo=UTC),
        metadata={"requested_url": payload.canonical_url},
    )

    first_fragment = EvidenceFragment.create(
        document.id,
        "text:0:50",
        "Management expected first product during May 2022.",
    )
    second_fragment = EvidenceFragment.create(
        document.id,
        "text:51:113",
        "Later guidance revised the expected window to July 2022.",
    )
    extraction = ExtractionEnvelope(
        run_id=UUID("11111111-1111-1111-1111-111111111111"),
        document_id=document.id,
        extractor_name="judgment-smoke-extractor",
        extractor_version="1.0.0",
        schema_version="judgment-smoke/v1",
        evidence=(first_fragment, second_fragment),
        candidates=(),
    )
    subject_id = UUID("22222222-2222-2222-2222-222222222222")

    research_repository = PostgresResearchRepository(dsn, bucket_name="smoke")
    try:
        document = await research_repository.save_document(document)
        await research_repository.save_evidence((first_fragment, second_fragment))
        await research_repository.save_extraction(extraction)
        async with research_repository.connection() as connection:
            await connection.execute(
                """
                INSERT INTO core.entities (
                    id, entity_type, canonical_name, normalized_name, lifecycle_status
                ) VALUES (%s, 'project', %s, %s, 'active')
                ON CONFLICT (id) DO NOTHING
                """,
                (subject_id, "Judgment smoke project", "judgment smoke project"),
            )
    finally:
        await research_repository.close()

    first = JudgmentAssertion(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        speaker_name_text="Management",
        subject_entity_id=subject_id,
        topic_code="project.first_product_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 5, 1, tzinfo=UTC),
        target_to=datetime(2022, 6, 1, tzinfo=UTC),
        value_kind=JudgmentValueKind.TEXT,
        value_text="first product expected during May 2022",
        summary="First product was expected during May 2022.",
        source_published_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        first_known_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        extraction_run_id=extraction.run_id,
        source_connector_id=source.id,
        extractor_name="grounded-judgment-projection",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=first_fragment.id,
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    )
    revised = JudgmentAssertion(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        speaker_name_text="Management",
        subject_entity_id=subject_id,
        topic_code="project.first_product_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 7, 1, tzinfo=UTC),
        target_to=datetime(2022, 8, 1, tzinfo=UTC),
        value_kind=JudgmentValueKind.TEXT,
        value_text="first product expected during July 2022",
        summary="Later guidance revised first product to July 2022.",
        source_published_at=datetime(2022, 6, 1, tzinfo=UTC),
        first_known_at=datetime(2022, 6, 1, tzinfo=UTC),
        extraction_run_id=extraction.run_id,
        source_connector_id=source.id,
        extractor_name="grounded-judgment-projection",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=second_fragment.id,
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    )
    relation = JudgmentRelation(
        from_judgment_id=first.id,
        to_judgment_id=revised.id,
        relation_type=JudgmentRelationType.REVISES,
        reason_summary="later disclosure moved the expected milestone window",
    )

    judgment_repository = PostgresJudgmentRepository(dsn)
    try:
        await judgment_repository.append_judgments((first, revised))
        await judgment_repository.append_judgments((first, revised))
        await judgment_repository.append_relations((relation,))
        await judgment_repository.append_relations((relation,))
        async with judgment_repository.connection() as connection:
            count_cursor = await connection.execute(
                "SELECT count(*) AS count FROM research.judgment_assertions WHERE id = ANY(%s)",
                ([first.id, revised.id],),
            )
            count_row = await count_cursor.fetchone()
            evidence_cursor = await connection.execute(
                "SELECT count(*) AS count FROM research.judgment_evidence WHERE judgment_id = ANY(%s)",
                ([first.id, revised.id],),
            )
            evidence_row = await evidence_cursor.fetchone()
            relation_cursor = await connection.execute(
                """
                SELECT count(*) AS count
                FROM research.judgment_relations
                WHERE from_judgment_id = %s AND to_judgment_id = %s
                  AND relation_type = 'revises'
                """,
                (first.id, revised.id),
            )
            relation_row = await relation_cursor.fetchone()
        if count_row is None or count_row["count"] != 2:
            raise AssertionError("judgment append was not idempotent")
        if evidence_row is None or evidence_row["count"] != 2:
            raise AssertionError("judgment evidence links were not persisted atomically")
        if relation_row is None or relation_row["count"] != 1:
            raise AssertionError("judgment revision relation was not idempotent")
    finally:
        await judgment_repository.close()

    print("POSTGRES_JUDGMENT_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
