from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from longcycle.domain.enums import (
    Decision,
    EntityType,
    FactStatus,
    FactValueKind,
    JobStage,
    JobStatus,
    QualityGrade,
    SourceKind,
    ValidTimeKind,
)
from longcycle.domain.models import (
    CollectionJob,
    DocumentArtifact,
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    ReconciliationResult,
    ReviewItem,
    SourceDefinition,
    SourceDocument,
    TimeRange,
    canonical_json,
    stable_uuid,
    stable_uuid_exact,
)
from longcycle.ports.repository import LeaseLostError, ReconciliationEvaluator


class PostgresSupport:
    def __init__(self, dsn: str, *, pool: Any | None = None, max_pool_size: int = 10) -> None:
        self.dsn = dsn
        self._pool = pool
        self._pool_lock = asyncio.Lock()
        self.max_pool_size = max_pool_size

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        try:
            from psycopg.rows import dict_row
            from psycopg_pool import AsyncConnectionPool
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("install longcycle-core[postgres] to use PostgreSQL") from exc
        if self._pool is None:
            async with self._pool_lock:
                if self._pool is None:
                    pool = AsyncConnectionPool(
                        self.dsn,
                        min_size=0,
                        max_size=self.max_pool_size,
                        open=False,
                        kwargs={"row_factory": dict_row},
                    )
                    await pool.open()
                    self._pool = pool
        async with self._pool.connection() as connection:
            yield connection

    async def close(self) -> None:
        if self._pool is not None and hasattr(self._pool, "close"):
            await self._pool.close()

    @staticmethod
    def jsonb(value: Any) -> Any:
        try:
            from psycopg.types.json import Jsonb
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("install longcycle-core[postgres] to use PostgreSQL") from exc
        return Jsonb(value)


class PostgresJobQueue(PostgresSupport):
    def __init__(self, dsn: str, pools: Sequence[str] = ("default",)) -> None:
        super().__init__(dsn)
        self.pools = tuple(pools)

    async def enqueue(self, job: CollectionJob) -> CollectionJob:
        if job.status != JobStatus.QUEUED:
            raise ValueError("only queued jobs can be enqueued")
        query = """
            INSERT INTO ops.collection_jobs (
                id, pool, stage, source_connector_id, industry_node_id, payload, status,
                priority, available_at, attempt_count, max_attempts, idempotency_key,
                parent_job_id, trace_id, created_at
            ) VALUES (
                %(id)s, %(pool)s, %(stage)s, %(source_id)s, %(industry_id)s, %(payload)s,
                %(status)s, %(priority)s, %(available_at)s, %(attempt)s, %(max_attempts)s,
                %(idempotency_key)s, %(parent_job_id)s, %(trace_id)s, %(created_at)s
            )
            ON CONFLICT (idempotency_key) DO UPDATE
            SET idempotency_key = EXCLUDED.idempotency_key
            RETURNING *
        """
        params = {
            "id": job.id,
            "pool": str(job.payload.get("pool", "default")),
            "stage": job.stage.value,
            "source_id": job.source_id,
            "industry_id": job.industry_id,
            "payload": self.jsonb(job.payload),
            "status": job.status.value,
            "priority": job.priority,
            "available_at": job.available_at,
            "attempt": job.attempt,
            "max_attempts": job.max_attempts,
            "idempotency_key": job.idempotency_key,
            "parent_job_id": job.parent_job_id,
            "trace_id": job.trace_id,
            "created_at": job.created_at,
        }
        async with self.connection() as connection:
            cursor = await connection.execute(query, params)
            row = await cursor.fetchone()
        return self._job_from_row(row)

    async def claim(self, *, worker_id: str, limit: int, lease_seconds: int) -> Sequence[CollectionJob]:
        async with self.connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM ops.claim_collection_jobs(%s, %s, %s, %s)",
                (worker_id, list(self.pools), limit, lease_seconds),
            )
            rows = await cursor.fetchall()
            for row in rows:
                await connection.execute(
                    """
                    INSERT INTO ops.job_attempts (
                        job_id, attempt_number, worker_id, lease_token, status, started_at
                    ) VALUES (%s, %s, %s, %s, 'running', now())
                    ON CONFLICT (job_id, attempt_number) DO NOTHING
                    """,
                    (row["id"], row["attempt_count"], worker_id, row["lease_token"]),
                )
        return tuple(self._job_from_row(row) for row in rows)

    async def acknowledge(self, *, job_id: UUID, worker_id: str, lease_token: UUID) -> None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE ops.collection_jobs
                SET status = 'succeeded', finished_at = now(), lease_owner = NULL,
                    lease_token = NULL, lease_expires_at = NULL
                WHERE id = %s AND status = 'leased' AND lease_owner = %s
                  AND lease_token = %s AND lease_expires_at > now()
                RETURNING attempt_count
                """,
                (job_id, worker_id, lease_token),
            )
            row = await cursor.fetchone()
            if row is None:
                raise LeaseLostError("job lease is stale or no longer owned")
            await connection.execute(
                """
                UPDATE ops.job_attempts SET status = 'succeeded', finished_at = now()
                WHERE job_id = %s AND attempt_number = %s AND lease_token = %s
                """,
                (job_id, row["attempt_count"], lease_token),
            )

    async def fail(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        lease_token: UUID,
        error: str,
        retryable: bool,
    ) -> None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE ops.collection_jobs
                SET status = CASE
                        WHEN NOT %(retryable)s OR attempt_count >= max_attempts THEN 'dead'
                        ELSE 'retry'
                    END,
                    available_at = CASE
                        WHEN NOT %(retryable)s OR attempt_count >= max_attempts THEN available_at
                        ELSE now() + make_interval(
                            secs => floor(
                                random() * (least(3600, power(2, least(attempt_count, 10))::int) + 1)
                            )::int
                        )
                    END,
                    last_error_message = %(error)s,
                    finished_at = CASE
                        WHEN NOT %(retryable)s OR attempt_count >= max_attempts THEN now()
                        ELSE NULL
                    END,
                    lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL
                WHERE id = %(job_id)s AND status = 'leased' AND lease_owner = %(worker_id)s
                  AND lease_token = %(lease_token)s AND lease_expires_at > now()
                RETURNING attempt_count, status
                """,
                {
                    "retryable": retryable,
                    "error": error[:4000],
                    "job_id": job_id,
                    "worker_id": worker_id,
                    "lease_token": lease_token,
                },
            )
            row = await cursor.fetchone()
            if row is None:
                raise LeaseLostError("job lease is stale or no longer owned")
            await connection.execute(
                """
                UPDATE ops.job_attempts
                SET status = %s, finished_at = now(), error_message = %s
                WHERE job_id = %s AND attempt_number = %s AND lease_token = %s
                """,
                (row["status"], error[:4000], job_id, row["attempt_count"], lease_token),
            )
            if row["status"] == "dead":
                await connection.execute(
                    """
                    INSERT INTO ops.dead_letters (job_id, final_error_message)
                    VALUES (%s, %s)
                    ON CONFLICT (job_id) DO UPDATE
                    SET dead_at = now(), final_error_message = EXCLUDED.final_error_message
                    """,
                    (job_id, error[:4000]),
                )

    async def heartbeat(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        lease_token: UUID,
        lease_seconds: int,
    ) -> None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE ops.collection_jobs
                SET lease_expires_at = now() + make_interval(secs => greatest(%s, 1))
                WHERE id = %s AND status = 'leased' AND lease_owner = %s AND lease_token = %s
                  AND lease_expires_at > now()
                RETURNING id
                """,
                (lease_seconds, job_id, worker_id, lease_token),
            )
            if await cursor.fetchone() is None:
                raise LeaseLostError("job lease is stale or no longer owned")

    @staticmethod
    def _job_from_row(row: dict[str, Any]) -> CollectionJob:
        return CollectionJob(
            id=row["id"],
            stage=JobStage(row["stage"]),
            status=JobStatus(row["status"]),
            source_id=row.get("source_connector_id"),
            industry_id=row.get("industry_node_id"),
            payload=row.get("payload") or {},
            priority=row["priority"],
            idempotency_key=row["idempotency_key"],
            available_at=row["available_at"],
            attempt=row["attempt_count"],
            max_attempts=row["max_attempts"],
            lease_owner=row.get("lease_owner"),
            lease_token=row.get("lease_token"),
            lease_expires_at=row.get("lease_expires_at"),
            parent_job_id=row.get("parent_job_id"),
            trace_id=row["trace_id"],
            created_at=row["created_at"],
        )


class PostgresResearchRepository(PostgresSupport):
    def __init__(self, dsn: str, *, bucket_name: str) -> None:
        super().__init__(dsn)
        self.bucket_name = bucket_name

    async def get_source(self, source_id: UUID) -> SourceDefinition:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT connector.*, publisher.source_kind, publisher.quality_grade,
                       publisher.publisher_domain, publisher.independence_cluster
                FROM evidence.source_connectors connector
                LEFT JOIN evidence.publishers publisher ON publisher.id = connector.publisher_id
                WHERE connector.id = %s
                """,
                (source_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            raise KeyError(source_id)
        return self._source_from_row(row)

    @staticmethod
    def _source_from_row(row: dict[str, Any]) -> SourceDefinition:
        return SourceDefinition(
            id=row["id"],
            name=row["name"],
            kind=SourceKind(row.get("source_kind") or SourceKind.MANUAL.value),
            plugin=row["plugin_name"],
            quality_grade=QualityGrade(row.get("quality_grade") or QualityGrade.C.value),
            publisher_domain=row.get("publisher_domain"),
            rate_limit_per_minute=row["rate_limit_per_minute"],
            enabled=row["enabled"],
            config=row.get("config") or {},
            syndication_cluster=(
                row.get("independence_cluster")
                or (
                    f"publisher:{row['publisher_id']}"
                    if row.get("publisher_id") is not None
                    else f"connector:{row['id']}"
                )
            ),
        )

    async def save_document(self, document: SourceDocument) -> SourceDocument:
        blob_id = stable_uuid("blob", document.content_sha256)
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO evidence.content_blobs (
                    id, sha256, bucket_name, object_key, byte_length, content_type, verified_at
                ) VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (sha256) DO NOTHING
                """,
                (
                    blob_id,
                    document.content_sha256,
                    self.bucket_name,
                    document.blob_key,
                    document.byte_length,
                    document.content_type,
                ),
            )
            publisher_cursor = await connection.execute(
                "SELECT publisher_id FROM evidence.source_connectors WHERE id = %s",
                (document.source_id,),
            )
            publisher_row = await publisher_cursor.fetchone()
            if publisher_row is None:
                raise KeyError(f"source connector does not exist: {document.source_id}")
            document_owner_id = publisher_row["publisher_id"] or document.source_id
            identity_owner_key = (
                f"publisher:{publisher_row['publisher_id']}"
                if publisher_row["publisher_id"] is not None
                else f"connector:{document.source_id}"
            )
            proposed_logical_document_id = stable_uuid_exact(
                "logical-document",
                str(document_owner_id),
                document.canonical_url,
                document.external_id or "",
            )
            document_cursor = await connection.execute(
                """
                INSERT INTO evidence.documents (
                    id, publisher_id, identity_owner_key, canonical_url, external_id, logical_title
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (identity_owner_key, canonical_url, external_id)
                    DO UPDATE SET logical_title = coalesce(
                        evidence.documents.logical_title,
                        EXCLUDED.logical_title
                    )
                RETURNING id
                """,
                (
                    proposed_logical_document_id,
                    publisher_row["publisher_id"],
                    identity_owner_key,
                    document.canonical_url,
                    document.external_id,
                    document.title,
                ),
            )
            document_row = await document_cursor.fetchone()
            if document_row is None:
                raise RuntimeError("document upsert did not return an identity")
            logical_document_id = document_row["id"]
            fetch_id = stable_uuid_exact(
                "fetch-v2",
                str(document.source_id),
                str(logical_document_id),
                document.content_sha256,
                document.retrieved_at.isoformat(),
            )
            await connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (str(logical_document_id),),
            )
            await connection.execute(
                """
                INSERT INTO evidence.document_fetches (
                    id, connector_id, document_id, requested_url, final_url, retrieved_at,
                    published_at, first_known_at, http_status, etag, last_modified,
                    response_headers, content_blob_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    fetch_id,
                    document.source_id,
                    logical_document_id,
                    document.metadata.get("requested_url", document.canonical_url),
                    document.canonical_url,
                    document.retrieved_at,
                    document.published_at,
                    document.first_known_at,
                    document.http_status,
                    (document.metadata.get("response_headers") or {}).get("etag"),
                    (document.metadata.get("response_headers") or {}).get("last-modified"),
                    self.jsonb(document.metadata.get("response_headers") or {}),
                    blob_id,
                ),
            )
            existing_cursor = await connection.execute(
                """
                SELECT version.id,
                       min(fetch.first_known_at) AS first_known_at,
                       min(fetch.published_at) FILTER (WHERE fetch.published_at IS NOT NULL) AS published_at
                FROM evidence.document_versions version
                JOIN evidence.document_fetches fetch
                  ON fetch.document_id = version.document_id
                 AND fetch.content_blob_id = version.content_blob_id
                WHERE version.document_id = %s AND version.content_blob_id = %s
                GROUP BY version.id
                """,
                (logical_document_id, blob_id),
            )
            existing = await existing_cursor.fetchone()
            if existing is None:
                await connection.execute(
                    """
                    INSERT INTO evidence.document_versions (
                        id, document_id, content_blob_id, first_fetch_id, version_ordinal, effective_from
                    )
                    SELECT %s, %s, %s, %s, coalesce(max(version_ordinal), 0) + 1, %s
                    FROM evidence.document_versions WHERE document_id = %s
                    """,
                    (
                        document.id,
                        logical_document_id,
                        blob_id,
                        fetch_id,
                        document.published_at,
                        logical_document_id,
                    ),
                )
        if existing is not None:
            return document.model_copy(
                update={
                    "id": existing["id"],
                    "first_known_at": existing["first_known_at"],
                    "published_at": existing["published_at"] or document.published_at,
                }
            )
        return document

    async def document_by_hash(
        self,
        source_id: UUID,
        canonical_url: str,
        content_sha256: str,
        external_id: str | None = None,
    ) -> SourceDocument | None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT version.id, document.canonical_url, document.external_id, document.logical_title,
                       fetch.retrieved_at, fetch.published_at, fetch.first_known_at, fetch.http_status,
                       blob.sha256, blob.object_key, blob.byte_length, blob.content_type
                FROM evidence.document_fetches fetch
                JOIN evidence.documents document ON document.id = fetch.document_id
                JOIN evidence.content_blobs blob ON blob.id = fetch.content_blob_id
                JOIN evidence.document_versions version
                  ON version.document_id = document.id AND version.content_blob_id = blob.id
                WHERE fetch.connector_id = %s
                  AND document.canonical_url = %s
                  AND document.external_id IS NOT DISTINCT FROM %s
                  AND blob.sha256 = %s
                ORDER BY fetch.first_known_at, fetch.retrieved_at
                LIMIT 1
                """,
                (source_id, canonical_url, external_id, content_sha256),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return SourceDocument(
            id=row["id"],
            source_id=source_id,
            canonical_url=row["canonical_url"],
            external_id=row["external_id"],
            title=row["logical_title"],
            published_at=row["published_at"],
            first_known_at=row["first_known_at"],
            retrieved_at=row["retrieved_at"],
            content_type=row["content_type"],
            content_sha256=row["sha256"],
            blob_key=row["object_key"],
            byte_length=row["byte_length"],
            http_status=row["http_status"],
        )

    async def save_artifact(self, artifact: DocumentArtifact) -> DocumentArtifact:
        blob_id = stable_uuid("blob", artifact.content_sha256)
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO evidence.content_blobs (
                    id, sha256, bucket_name, object_key, byte_length, content_type, verified_at
                ) VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (sha256) DO NOTHING
                """,
                (
                    blob_id,
                    artifact.content_sha256,
                    self.bucket_name,
                    artifact.blob_key,
                    artifact.byte_length,
                    artifact.content_type,
                ),
            )
            cursor = await connection.execute(
                """
                INSERT INTO evidence.artifacts (
                    id, document_version_id, artifact_type, content_blob_id,
                    producer_name, producer_version, input_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    document_version_id, artifact_type, producer_name, producer_version, input_hash
                ) DO UPDATE SET id = evidence.artifacts.id
                RETURNING id, content_blob_id
                """,
                (
                    artifact.id,
                    artifact.document_id,
                    artifact.artifact_type,
                    blob_id,
                    artifact.producer_name,
                    artifact.producer_version,
                    artifact.input_sha256,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError("artifact upsert did not return an identity")
            content_cursor = await connection.execute(
                "SELECT sha256 FROM evidence.content_blobs WHERE id = %s",
                (row["content_blob_id"],),
            )
            content_row = await content_cursor.fetchone()
            if content_row is None or content_row["sha256"] != artifact.content_sha256:
                raise ValueError("parser artifact identity produced different content")
        return artifact.model_copy(update={"id": row["id"]})

    async def save_evidence(self, fragments: Sequence[EvidenceFragment]) -> None:
        async with self.connection() as connection:
            for fragment in fragments:
                expected = EvidenceFragment.create(
                    fragment.document_id,
                    fragment.locator,
                    fragment.excerpt,
                    fragment.structured_payload,
                    artifact_id=fragment.artifact_id,
                )
                if expected.id != fragment.id or expected.fragment_sha256 != fragment.fragment_sha256:
                    raise ValueError("evidence fragment identity does not match its content")
                await connection.execute(
                    """
                    INSERT INTO evidence.evidence_fragments (
                        id, document_version_id, artifact_id, locator_type, locator, locator_hash, excerpt,
                        structured_payload, fragment_sha256
                    ) VALUES (%s, %s, %s, 'opaque', %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        fragment.id,
                        fragment.document_id,
                        fragment.artifact_id,
                        self.jsonb({"value": fragment.locator}),
                        fragment.locator_sha256,
                        fragment.excerpt,
                        self.jsonb(fragment.structured_payload) if fragment.structured_payload is not None else None,
                        fragment.fragment_sha256,
                    ),
                )

    async def save_extraction(self, extraction: ExtractionEnvelope) -> ExtractionEnvelope:
        document_id = extraction.document_id
        envelope_payload = extraction.model_dump(mode="json")
        input_hash = hashlib.sha256(
            canonical_json(
                {
                    "run_id": str(extraction.run_id),
                    "document": str(document_id),
                    "extractor": extraction.extractor_name,
                    "version": extraction.extractor_version,
                    "prompt": extraction.prompt_version,
                    "schema": extraction.schema_version,
                    "model": extraction.model_name,
                    "candidate_ids": [str(item.id) for item in extraction.candidates],
                }
            ).encode()
        ).hexdigest()
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO evidence.extraction_runs (
                    id, document_version_id, extractor_name, extractor_version, input_hash,
                    prompt_version_text, schema_version_text, model_name_text,
                    envelope_payload, raw_response_object_key, status,
                    tokens_in, tokens_out, cost_microunits,
                    started_at, finished_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    'succeeded', %s, %s, %s, now(), now()
                )
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    extraction.run_id,
                    document_id,
                    extraction.extractor_name,
                    extraction.extractor_version,
                    input_hash,
                    extraction.prompt_version,
                    extraction.schema_version,
                    extraction.model_name,
                    self.jsonb(envelope_payload),
                    extraction.raw_response_blob_key,
                    extraction.tokens_in,
                    extraction.tokens_out,
                    extraction.cost_microunits,
                ),
            )

            stored_cursor = await connection.execute(
                "SELECT envelope_payload FROM evidence.extraction_runs WHERE id = %s",
                (extraction.run_id,),
            )
            stored = await stored_cursor.fetchone()
            if stored is None:
                raise RuntimeError(f"failed to persist extraction run: {extraction.run_id}")
        return ExtractionEnvelope.model_validate(stored["envelope_payload"])

    async def get_extraction(self, run_id: UUID) -> ExtractionEnvelope | None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                "SELECT envelope_payload FROM evidence.extraction_runs WHERE id = %s",
                (run_id,),
            )
            row = await cursor.fetchone()
        return ExtractionEnvelope.model_validate(row["envelope_payload"]) if row is not None else None

    async def processing_completed(self, run_id: UUID) -> bool:
        async with self.connection() as connection:
            cursor = await connection.execute(
                "SELECT EXISTS (SELECT 1 FROM ops.document_processing_completions WHERE extraction_run_id = %s) AS found",
                (run_id,),
            )
            row = await cursor.fetchone()
        return bool(row["found"])

    async def complete_processing(self, run_id: UUID) -> None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                INSERT INTO ops.document_processing_completions (extraction_run_id)
                SELECT id FROM evidence.extraction_runs WHERE id = %s
                ON CONFLICT (extraction_run_id) DO NOTHING
                RETURNING extraction_run_id
                """,
                (run_id,),
            )
            inserted = await cursor.fetchone()
            if inserted is None:
                exists_cursor = await connection.execute(
                    "SELECT 1 FROM ops.document_processing_completions WHERE extraction_run_id = %s",
                    (run_id,),
                )
                if await exists_cursor.fetchone() is None:
                    raise KeyError(f"extraction run does not exist: {run_id}")

    async def append_assertions(self, assertions: Sequence[FactAssertion]) -> None:
        async with self.connection() as connection:
            batch_ids = {assertion.id for assertion in assertions}
            if any(
                assertion.supersedes_id in batch_ids
                for assertion in assertions
                if assertion.supersedes_id is not None
            ):
                raise ValueError("one assertion batch cannot contain its own supersession target")
            external_supersession_ids = sorted(
                {
                    assertion.supersedes_id
                    for assertion in assertions
                    if assertion.supersedes_id is not None
                    and assertion.supersedes_id not in batch_ids
                },
                key=str,
            )
            if external_supersession_ids:
                target_cursor = await connection.execute(
                    "SELECT id FROM research.fact_assertions WHERE id = ANY(%s)",
                    (external_supersession_ids,),
                )
                found_targets = {row["id"] for row in await target_cursor.fetchall()}
                if found_targets != set(external_supersession_ids):
                    raise ValueError("assertion references an unknown supersession target")
            if any(
                assertion.value_type != FactValueKind.NUMERIC
                and assertion.normalized_unit is not None
                for assertion in assertions
            ):
                raise ValueError("non-numeric assertions cannot carry a normalized unit")
            unit_codes = sorted(
                {
                    assertion.normalized_unit
                    for assertion in assertions
                    if assertion.normalized_unit is not None
                }
            )
            if unit_codes:
                unit_cursor = await connection.execute(
                    "SELECT code FROM core.units WHERE code = ANY(%s)",
                    (unit_codes,),
                )
                registered = {row["code"] for row in await unit_cursor.fetchall()}
                unknown = sorted(set(unit_codes) - registered)
                if unknown:
                    raise ValueError(
                        f"assertions contain unregistered normalized units: {', '.join(unknown)}"
                    )
            for assertion in assertions:
                dimensions = assertion.dimensions
                payload = dimensions.canonical_payload
                await connection.execute(
                    """
                    INSERT INTO research.fact_dimension_sets (
                        comparability_hash, schema_version, product_spec_id,
                        geography_scheme, geography_code, market_basis, contract_basis,
                        tax_basis, freight_basis, incoterm, currency_code, frequency,
                        price_component, statistical_scope, canonical_payload
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (comparability_hash) DO NOTHING
                    """,
                    (
                        assertion.comparability_hash,
                        dimensions.schema_version,
                        dimensions.product_spec_id,
                        dimensions.geography_scheme,
                        dimensions.geography_code,
                        dimensions.market_basis.value if dimensions.market_basis else None,
                        dimensions.contract_basis,
                        dimensions.tax_basis.value if dimensions.tax_basis else None,
                        dimensions.freight_basis.value if dimensions.freight_basis else None,
                        dimensions.incoterm,
                        dimensions.currency_code,
                        dimensions.frequency.value if dimensions.frequency else None,
                        dimensions.price_component.value if dimensions.price_component else None,
                        dimensions.statistical_scope,
                        self.jsonb(payload),
                    ),
                )
                dimension_cursor = await connection.execute(
                    """
                    SELECT canonical_payload
                    FROM research.fact_dimension_sets
                    WHERE comparability_hash = %s
                    """,
                    (assertion.comparability_hash,),
                )
                stored_dimension = await dimension_cursor.fetchone()
                if stored_dimension is None or stored_dimension["canonical_payload"] != payload:
                    raise ValueError("comparability hash maps to a different canonical dimension payload")
                value_kind = assertion.value_type
                numeric = assertion.normalized_number if value_kind == FactValueKind.NUMERIC else None
                text_value = assertion.value if value_kind == FactValueKind.TEXT else None
                boolean_value = (
                    assertion.normalized_boolean if value_kind == FactValueKind.BOOLEAN else None
                )
                date_value = assertion.normalized_date if value_kind == FactValueKind.DATE else None
                entity_value = (
                    assertion.normalized_entity_id if value_kind == FactValueKind.ENTITY else None
                )
                json_value = assertion.normalized_json if value_kind == FactValueKind.JSON else None
                if value_kind == FactValueKind.NUMERIC and numeric is None:
                    raise ValueError("numeric assertion is missing normalized_number")
                if value_kind == FactValueKind.BOOLEAN and boolean_value is None:
                    raise ValueError("boolean assertion is missing normalized_boolean")
                if value_kind == FactValueKind.DATE and date_value is None:
                    raise ValueError("date assertion is missing normalized_date")
                if value_kind == FactValueKind.ENTITY and entity_value is None:
                    raise ValueError("entity assertion is missing normalized_entity_id")
                if value_kind == FactValueKind.JSON and json_value is None:
                    raise ValueError("JSON assertion is missing normalized_json")
                await connection.execute(
                    """
                    INSERT INTO research.fact_assertions (
                        id, subject_entity_id, subject_industry_node_id, predicate_code,
                        comparability_hash, dimensions_complete, valid_time_kind, value_kind, raw_value,
                        value_numeric,
                        value_text, value_boolean, value_date, value_entity_id, value_json,
                        unit_code, valid_from, valid_to, observed_at,
                        source_published_at, first_known_at, extraction_run_id,
                        normalizer_name, normalizer_version,
                        source_connector_id, source_cluster,
                        confidence, source_quality, extraction_certainty, entity_match,
                        time_unit_completeness, corroboration, freshness, conflict_penalty,
                        high_impact, supersedes_assertion_id, ingest_status, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, 'candidate', %s
                    ) ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        assertion.id,
                        None if assertion.entity_type == EntityType.INDUSTRY else assertion.entity_id,
                        assertion.entity_id if assertion.entity_type == EntityType.INDUSTRY else None,
                        assertion.field_name,
                        assertion.comparability_hash,
                        assertion.dimensions_complete,
                        assertion.valid_time_kind.value,
                        value_kind.value,
                        assertion.value,
                        numeric,
                        text_value,
                        boolean_value,
                        date_value,
                        entity_value,
                        self.jsonb(json_value) if value_kind == FactValueKind.JSON else None,
                        assertion.normalized_unit,
                        assertion.valid_time.start_utc,
                        assertion.valid_time.end_utc,
                        assertion.observed_at,
                        assertion.source_published_at,
                        assertion.known_at,
                        assertion.extraction_run_id,
                        assertion.normalizer_name,
                        assertion.normalizer_version,
                        assertion.source_id,
                        assertion.source_cluster,
                        assertion.confidence,
                        assertion.quality.source_quality,
                        assertion.quality.extraction_certainty,
                        assertion.quality.entity_match,
                        assertion.quality.time_unit_completeness,
                        assertion.quality.corroboration,
                        assertion.quality.freshness,
                        assertion.quality.conflict_penalty,
                        assertion.high_impact,
                        assertion.supersedes_id,
                        self.jsonb(assertion.metadata),
                    ),
                )
                await connection.execute(
                    """
                    INSERT INTO research.assertion_evidence (assertion_id, evidence_fragment_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """,
                    (assertion.id, assertion.evidence_fragment_id),
                )

    async def assertions_for_comparison(self, candidate: FactAssertion) -> Sequence[FactAssertion]:
        async with self.connection() as connection:
            return await self._assertions_for_comparison_on_connection(connection, candidate)

    async def _assertions_for_comparison_on_connection(
        self,
        connection: Any,
        candidate: FactAssertion,
    ) -> Sequence[FactAssertion]:
        subject_entity_id = None if candidate.entity_type == EntityType.INDUSTRY else candidate.entity_id
        subject_industry_node_id = candidate.entity_id if candidate.entity_type == EntityType.INDUSTRY else None
        cursor = await connection.execute(
            """
            SELECT assertion.*, link.evidence_fragment_id,
                   run.extractor_name, run.extractor_version, run.document_version_id,
                   entity.entity_type AS subject_entity_type,
                   dimensions.canonical_payload
            FROM research.fact_assertions_with_status assertion
            JOIN research.assertion_evidence link ON link.assertion_id = assertion.id
            JOIN evidence.extraction_runs run ON run.id = assertion.extraction_run_id
            JOIN research.fact_dimension_sets dimensions
              ON dimensions.comparability_hash = assertion.comparability_hash
            LEFT JOIN core.entities entity ON entity.id = assertion.subject_entity_id
            WHERE assertion.subject_entity_id IS NOT DISTINCT FROM %s
              AND assertion.subject_industry_node_id IS NOT DISTINCT FROM %s
              AND assertion.predicate_code = %s
              AND assertion.comparability_hash = %s
              AND (
                  assertion.id = %s
                  OR (
                      %s = 'period'
                      AND assertion.valid_time_kind = 'period'
                      AND tstzrange(assertion.valid_from, assertion.valid_to, '[)')
                          && tstzrange(%s, %s, '[)')
                  )
                  OR (%s = 'timeless' AND assertion.valid_time_kind = 'timeless')
              )
            ORDER BY assertion.recorded_at
            """,
            (
                subject_entity_id,
                subject_industry_node_id,
                candidate.field_name,
                candidate.comparability_hash,
                candidate.id,
                candidate.valid_time_kind.value,
                candidate.valid_time.start_utc,
                candidate.valid_time.end_utc,
                candidate.valid_time_kind.value,
            ),
        )
        rows = await cursor.fetchall()
        return tuple(self._assertion_from_row(row) for row in rows)

    async def _assertion_by_id_on_connection(
        self,
        connection: Any,
        assertion_id: UUID,
    ) -> FactAssertion | None:
        cursor = await connection.execute(
            """
            SELECT assertion.*, link.evidence_fragment_id,
                   run.extractor_name, run.extractor_version, run.document_version_id,
                   entity.entity_type AS subject_entity_type,
                   dimensions.canonical_payload
            FROM research.fact_assertions_with_status assertion
            JOIN research.assertion_evidence link ON link.assertion_id = assertion.id
            JOIN evidence.extraction_runs run ON run.id = assertion.extraction_run_id
            JOIN research.fact_dimension_sets dimensions
              ON dimensions.comparability_hash = assertion.comparability_hash
            LEFT JOIN core.entities entity ON entity.id = assertion.subject_entity_id
            WHERE assertion.id = %s
            ORDER BY link.evidence_fragment_id
            LIMIT 1
            """,
            (assertion_id,),
        )
        row = await cursor.fetchone()
        return self._assertion_from_row(row) if row is not None else None

    async def reconcile_assertion(
        self,
        candidate: FactAssertion,
        evaluator: ReconciliationEvaluator,
    ) -> ReconciliationResult:
        async with self.connection() as connection:
            stored = await self._assertion_by_id_on_connection(connection, candidate.id)
            if stored is None:
                raise KeyError(candidate.id)
            if stored.model_copy(update={"status": candidate.status}) != candidate:
                raise ValueError("candidate does not match the persisted immutable assertion")
            candidate = stored
            proposed_fact_key_id = stable_uuid(
                "fact-key-v3",
                "industry" if candidate.entity_type == EntityType.INDUSTRY else "entity",
                str(candidate.entity_id),
                candidate.field_name,
                candidate.comparability_hash,
            )
            subject_entity_id = (
                None if candidate.entity_type == EntityType.INDUSTRY else candidate.entity_id
            )
            subject_industry_node_id = (
                candidate.entity_id if candidate.entity_type == EntityType.INDUSTRY else None
            )
            fact_key_cursor = await connection.execute(
                """
                INSERT INTO research.fact_keys (
                    id, subject_entity_id, subject_industry_node_id,
                    predicate_code, comparability_hash
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (
                    subject_entity_id, subject_industry_node_id,
                    predicate_code, comparability_hash
                ) DO UPDATE SET predicate_code = EXCLUDED.predicate_code
                RETURNING id
                """,
                (
                    proposed_fact_key_id,
                    subject_entity_id,
                    subject_industry_node_id,
                    candidate.field_name,
                    candidate.comparability_hash,
                ),
            )
            fact_key_row = await fact_key_cursor.fetchone()
            if fact_key_row is None:
                raise RuntimeError("fact-key upsert did not return an identity")
            fact_key_id = fact_key_row["id"]
            await connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (str(fact_key_id),),
            )
            existing_cursor = await connection.execute(
                """
                SELECT assertion_id, decision, score, reason_codes,
                       conflicting_assertion_ids, evaluator_name, evaluator_version
                FROM research.reconciliation_evaluations
                WHERE assertion_id = %s
                  AND evaluator_name = %s
                  AND evaluator_version = %s
                """,
                (candidate.id, evaluator.evaluator_name, evaluator.evaluator_version),
            )
            persisted = await existing_cursor.fetchone()
            if persisted is None:
                existing = await self._assertions_for_comparison_on_connection(
                    connection,
                    candidate,
                )
                computed = evaluator.reconcile(candidate, existing).model_copy(
                    update={
                        "evaluator_name": evaluator.evaluator_name,
                        "evaluator_version": evaluator.evaluator_version,
                    }
                )
                result = ReconciliationResult.model_validate(computed.model_dump(mode="python"))
                if result.assertion_id != candidate.id:
                    raise ValueError("reconciler returned a result for a different assertion")
                inserted_cursor = await connection.execute(
                    """
                    INSERT INTO research.reconciliation_evaluations (
                        assertion_id, decision, score, reason_codes,
                        conflicting_assertion_ids, evaluator_name, evaluator_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (assertion_id, evaluator_name, evaluator_version) DO NOTHING
                    RETURNING assertion_id, decision, score, reason_codes,
                              conflicting_assertion_ids, evaluator_name, evaluator_version
                    """,
                    (
                        result.assertion_id,
                        result.decision.value,
                        result.score,
                        list(result.reason_codes),
                        list(result.conflicting_assertion_ids),
                        result.evaluator_name,
                        result.evaluator_version,
                    ),
                )
                inserted = await inserted_cursor.fetchone()
                if inserted is None:
                    raise RuntimeError("fact-key lock did not serialize reconciliation identity")
                result = self._reconciliation_from_row(inserted)
            else:
                result = self._reconciliation_from_row(persisted)

        # The evaluation is now authoritative and visible to the next worker.
        # Finalization is separately idempotent so a crash can resume it.
        return await self.save_reconciliation(result)

    async def save_reconciliation(self, result: ReconciliationResult) -> ReconciliationResult:
        result = ReconciliationResult.model_validate(result.model_dump(mode="python"))
        async with self.connection() as connection:
            assertion_cursor = await connection.execute(
                "SELECT * FROM research.fact_assertions WHERE id = %s",
                (result.assertion_id,),
            )
            assertion = await assertion_cursor.fetchone()
            if assertion is None:
                raise KeyError(result.assertion_id)
            proposed_fact_key_id = stable_uuid(
                "fact-key-v3",
                "entity" if assertion["subject_entity_id"] is not None else "industry",
                str(assertion["subject_entity_id"] or assertion["subject_industry_node_id"]),
                assertion["predicate_code"],
                assertion["comparability_hash"],
            )
            fact_key_cursor = await connection.execute(
                """
                INSERT INTO research.fact_keys (
                    id, subject_entity_id, subject_industry_node_id, predicate_code, comparability_hash
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (
                    subject_entity_id, subject_industry_node_id,
                    predicate_code, comparability_hash
                ) DO UPDATE SET predicate_code = EXCLUDED.predicate_code
                RETURNING id
                """,
                (
                    proposed_fact_key_id,
                    assertion["subject_entity_id"],
                    assertion["subject_industry_node_id"],
                    assertion["predicate_code"],
                    assertion["comparability_hash"],
                ),
            )
            fact_key_row = await fact_key_cursor.fetchone()
            if fact_key_row is None:
                raise RuntimeError("fact-key upsert did not return an identity")
            fact_key_id = fact_key_row["id"]
            await connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (str(fact_key_id),),
            )
            evaluation_cursor = await connection.execute(
                """
                INSERT INTO research.reconciliation_evaluations (
                    assertion_id, decision, score, reason_codes, conflicting_assertion_ids,
                    evaluator_name, evaluator_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (assertion_id, evaluator_name, evaluator_version) DO NOTHING
                RETURNING assertion_id, decision, score, reason_codes,
                          conflicting_assertion_ids, evaluator_name, evaluator_version
                """,
                (
                    result.assertion_id,
                    result.decision.value,
                    result.score,
                    list(result.reason_codes),
                    list(result.conflicting_assertion_ids),
                    result.evaluator_name,
                    result.evaluator_version,
                ),
            )
            persisted_evaluation = await evaluation_cursor.fetchone()
            if persisted_evaluation is None:
                existing_cursor = await connection.execute(
                    """
                    SELECT assertion_id, decision, score, reason_codes,
                           conflicting_assertion_ids, evaluator_name, evaluator_version
                    FROM research.reconciliation_evaluations
                    WHERE assertion_id = %s
                      AND evaluator_name = %s
                      AND evaluator_version = %s
                    """,
                    (
                        result.assertion_id,
                        result.evaluator_name,
                        result.evaluator_version,
                    ),
                )
                existing = await existing_cursor.fetchone()
                if existing is None:
                    raise RuntimeError("reconciliation uniqueness conflict has no persisted evaluation")
                result = self._reconciliation_from_row(existing)
            else:
                result = self._reconciliation_from_row(persisted_evaluation)
            if result.decision == Decision.CONFLICT:
                conflict_cursor = await connection.execute(
                    """
                    SELECT id, valid_from, valid_to
                    FROM research.fact_assertions
                    WHERE id = ANY(%s)
                    """,
                    (list(result.conflicting_assertion_ids),),
                )
                for conflicting in await conflict_cursor.fetchall():
                    overlap_from, overlap_to = self._overlap_bounds(
                        assertion["valid_from"],
                        assertion["valid_to"],
                        conflicting["valid_from"],
                        conflicting["valid_to"],
                    )
                    member_ids = sorted([result.assertion_id, conflicting["id"]], key=str)
                    case_id = stable_uuid(
                        "conflict",
                        str(fact_key_id),
                        *(str(item) for item in member_ids),
                    )
                    await connection.execute(
                        """
                        INSERT INTO research.conflict_cases (
                            id, fact_key_id, valid_from, valid_to, severity
                        ) VALUES (%s, %s, %s, %s, 'high')
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (case_id, fact_key_id, overlap_from, overlap_to),
                    )
                    for member_id in member_ids:
                        await connection.execute(
                            """
                            INSERT INTO research.conflict_members (conflict_case_id, assertion_id)
                            VALUES (%s, %s) ON CONFLICT DO NOTHING
                            """,
                            (case_id, member_id),
                        )
            if result.decision == Decision.ACCEPT:
                resolution_id = stable_uuid(
                    "resolution",
                    str(result.assertion_id),
                    "accept",
                    result.evaluator_name,
                    result.evaluator_version,
                )
                resolution_cursor = await connection.execute(
                    """
                    INSERT INTO research.fact_resolutions (
                        id, fact_key_id, decision_type, selected_assertion_ids,
                        rejected_assertion_ids, rationale_codes, resolver_type,
                        resolver_id, resolver_version, confidence
                    ) VALUES (%s, %s, 'select', %s, %s, %s, 'rule', %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        resolution_id,
                        fact_key_id,
                        [result.assertion_id],
                        (
                            [assertion["supersedes_assertion_id"]]
                            if assertion["supersedes_assertion_id"] is not None
                            else []
                        ),
                        list(result.reason_codes),
                        result.evaluator_name,
                        result.evaluator_version,
                        result.score,
                    ),
                )
                await resolution_cursor.fetchone()
                await connection.execute(
                    """
                    INSERT INTO research.fact_resolution_assertions (
                        resolution_id, assertion_id, disposition
                    ) VALUES (%s, %s, 'selected')
                    ON CONFLICT DO NOTHING
                    """,
                    (resolution_id, result.assertion_id),
                )
                if assertion["supersedes_assertion_id"] is not None:
                    await connection.execute(
                        """
                        INSERT INTO research.fact_resolution_assertions (
                            resolution_id, assertion_id, disposition
                        ) VALUES (%s, %s, 'rejected')
                        ON CONFLICT DO NOTHING
                        """,
                        (resolution_id, assertion["supersedes_assertion_id"]),
                    )

                version_id = stable_uuid("canonical-fact", str(fact_key_id), str(resolution_id))
                version_cursor = await connection.execute(
                    "SELECT id FROM research.canonical_fact_versions WHERE id = %s",
                    (version_id,),
                )
                if await version_cursor.fetchone() is not None:
                    return result
                current_cursor = await connection.execute(
                    """
                    SELECT *
                    FROM research.canonical_fact_versions
                    WHERE fact_key_id = %s
                      AND system_to IS NULL
                      AND publication_status = 'trusted'
                      AND tstzrange(valid_from, valid_to, '[)') && tstzrange(%s, %s, '[)')
                    FOR UPDATE
                    """,
                    (fact_key_id, assertion["valid_from"], assertion["valid_to"]),
                )
                current_versions = await current_cursor.fetchall()

                transition_cursor = await connection.execute(
                    """
                    SELECT greatest(
                        clock_timestamp(),
                        coalesce(max(system_from) + interval '1 microsecond', clock_timestamp())
                    ) AS transition_at
                    FROM research.canonical_fact_versions
                    WHERE fact_key_id = %s AND system_to IS NULL
                    """,
                    (fact_key_id,),
                )
                transition_row = await transition_cursor.fetchone()
                if transition_row is None:
                    raise RuntimeError("database did not provide a canonical transition timestamp")
                transition_at = transition_row["transition_at"]
                for current in current_versions:
                    await connection.execute(
                        """
                        UPDATE research.canonical_fact_versions
                        SET system_to = %s
                        WHERE id = %s AND system_to IS NULL
                        """,
                        (transition_at, current["id"]),
                    )
                    left_needed = assertion["valid_from"] is not None and (
                        current["valid_from"] is None or current["valid_from"] < assertion["valid_from"]
                    )
                    right_needed = assertion["valid_to"] is not None and (
                        current["valid_to"] is None or assertion["valid_to"] < current["valid_to"]
                    )
                    if left_needed:
                        await self._insert_carry_forward(
                            connection,
                            current,
                            new_id=stable_uuid(
                                "canonical-carry-left",
                                str(current["id"]),
                                str(result.assertion_id),
                            ),
                            valid_from=current["valid_from"],
                            valid_to=assertion["valid_from"],
                            system_from=transition_at,
                        )
                    if right_needed:
                        await self._insert_carry_forward(
                            connection,
                            current,
                            new_id=stable_uuid(
                                "canonical-carry-right",
                                str(current["id"]),
                                str(result.assertion_id),
                            ),
                            valid_from=assertion["valid_to"],
                            valid_to=current["valid_to"],
                            system_from=transition_at,
                        )
                await connection.execute(
                    """
                    INSERT INTO research.canonical_fact_versions (
                        id, fact_key_id, resolution_id, value_kind, value_numeric, value_text,
                        value_boolean, value_date, value_entity_id, value_json, unit_code,
                        valid_from, valid_to, system_from, market_known_at, confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        version_id,
                        fact_key_id,
                        resolution_id,
                        assertion["value_kind"],
                        assertion["value_numeric"],
                        assertion["value_text"],
                        assertion["value_boolean"],
                        assertion["value_date"],
                        assertion["value_entity_id"],
                        self.jsonb(assertion["value_json"]) if assertion["value_json"] is not None else None,
                        assertion["unit_code"],
                        assertion["valid_from"],
                        assertion["valid_to"],
                        transition_at,
                        assertion["first_known_at"],
                        result.score,
                    ),
                )
            return result

    @staticmethod
    def _reconciliation_from_row(row: dict[str, Any]) -> ReconciliationResult:
        decision = Decision(row["decision"])
        status = {
            Decision.ACCEPT: FactStatus.TRUSTED,
            Decision.REVIEW: FactStatus.REVIEW,
            Decision.CONFLICT: FactStatus.CONFLICT,
            Decision.QUARANTINE: FactStatus.QUARANTINED,
        }[decision]
        return ReconciliationResult(
            assertion_id=row["assertion_id"],
            decision=decision,
            score=row["score"],
            reason_codes=tuple(row["reason_codes"]),
            conflicting_assertion_ids=tuple(row["conflicting_assertion_ids"]),
            status=status,
            evaluator_name=row["evaluator_name"],
            evaluator_version=row["evaluator_version"],
        )

    async def _insert_carry_forward(
        self,
        connection: Any,
        current: dict[str, Any],
        *,
        new_id: UUID,
        valid_from: datetime | None,
        valid_to: datetime | None,
        system_from: datetime,
    ) -> None:
        await connection.execute(
            """
            INSERT INTO research.canonical_fact_versions (
                id, fact_key_id, resolution_id, value_kind, value_numeric, value_text,
                value_boolean, value_date, value_entity_id, value_json, unit_code,
                valid_from, valid_to, system_from, market_known_at, confidence,
                publication_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                new_id,
                current["fact_key_id"],
                current["resolution_id"],
                current["value_kind"],
                current["value_numeric"],
                current["value_text"],
                current["value_boolean"],
                current["value_date"],
                current["value_entity_id"],
                self.jsonb(current["value_json"]) if current["value_json"] is not None else None,
                current["unit_code"],
                valid_from,
                valid_to,
                system_from,
                current["market_known_at"],
                current["confidence"],
                current["publication_status"],
            ),
        )

    @staticmethod
    def _overlap_bounds(
        left_start: datetime | None,
        left_end: datetime | None,
        right_start: datetime | None,
        right_end: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        starts = [value for value in (left_start, right_start) if value is not None]
        ends = [value for value in (left_end, right_end) if value is not None]
        return (max(starts) if starts else None, min(ends) if ends else None)

    async def enqueue_review(self, item: ReviewItem) -> None:
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO ops.review_cases (
                    id, subject_type, subject_id, severity, reason_codes, created_at
                ) VALUES (%s, 'assertion', %s, %s, %s, %s)
                ON CONFLICT (subject_type, subject_id)
                    WHERE status IN ('open', 'in_review')
                    DO NOTHING
                """,
                (item.id, item.assertion_id, item.severity.value, list(item.reason_codes), item.created_at),
            )

    @staticmethod
    def _assertion_from_row(row: dict[str, Any]) -> FactAssertion:
        value_kind = FactValueKind(row["value_kind"])
        raw_value = row.get("raw_value")
        if not raw_value:
            legacy_values = {
                FactValueKind.NUMERIC: row["value_numeric"],
                FactValueKind.TEXT: row["value_text"],
                FactValueKind.BOOLEAN: row["value_boolean"],
                FactValueKind.DATE: row["value_date"],
                FactValueKind.ENTITY: row["value_entity_id"],
                FactValueKind.JSON: row["value_json"],
            }
            legacy_value = legacy_values[value_kind]
            raw_value = (
                canonical_json(legacy_value)
                if value_kind == FactValueKind.JSON
                else str(legacy_value)
            )
        return FactAssertion(
            id=row["id"],
            entity_type=PostgresResearchRepository._entity_type_from_row(row),
            entity_id=row["subject_entity_id"] or row["subject_industry_node_id"],
            field_name=row["predicate_code"],
            value=raw_value,
            value_type=value_kind,
            normalized_number=Decimal(row["value_numeric"]) if row["value_numeric"] is not None else None,
            normalized_boolean=row["value_boolean"],
            normalized_date=row["value_date"],
            normalized_entity_id=row["value_entity_id"],
            normalized_json=row["value_json"],
            normalized_unit=row["unit_code"],
            dimensions=FactDimensions.model_validate(row["canonical_payload"]),
            dimensions_complete=row["dimensions_complete"],
            valid_time_kind=ValidTimeKind(row["valid_time_kind"]),
            valid_time=TimeRange(start=row["valid_from"], end=row["valid_to"]),
            observed_at=row["observed_at"],
            source_published_at=row["source_published_at"],
            known_at=row["first_known_at"],
            source_id=row["source_connector_id"],
            document_id=row["document_version_id"],
            evidence_fragment_id=row["evidence_fragment_id"],
            extraction_run_id=row["extraction_run_id"],
            extractor_name=row["extractor_name"],
            extractor_version=row["extractor_version"],
            normalizer_name=row["normalizer_name"],
            normalizer_version=row["normalizer_version"],
            source_cluster=row["source_cluster"],
            confidence=row["confidence"],
            quality=QualityComponents(
                source_quality=row["source_quality"],
                extraction_certainty=row["extraction_certainty"],
                entity_match=row["entity_match"],
                time_unit_completeness=row["time_unit_completeness"],
                corroboration=row["corroboration"],
                freshness=row["freshness"],
                conflict_penalty=row["conflict_penalty"],
            ),
            high_impact=row["high_impact"],
            status=FactStatus(row["status"]),
            supersedes_id=row["supersedes_assertion_id"],
            metadata=row["metadata"] or {},
        )

    @staticmethod
    def _entity_type_from_row(row: dict[str, Any]) -> EntityType:
        if row.get("subject_industry_node_id") is not None:
            return EntityType.INDUSTRY
        mapping = {
            "security": EntityType.SECURITY,
            "facility": EntityType.FACILITY,
            "production_line": EntityType.PRODUCTION_LINE,
            "product": EntityType.PRODUCT,
            "project": EntityType.CAPACITY_PROJECT,
            "event": EntityType.EVENT,
        }
        return mapping.get(row.get("subject_entity_type"), EntityType.ORGANIZATION)
