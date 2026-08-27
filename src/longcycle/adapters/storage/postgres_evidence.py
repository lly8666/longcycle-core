from __future__ import annotations

from typing import Any
from uuid import UUID

from longcycle.domain.evidence import EvidenceDrilldownRecord, EvidenceRepresentationKind

from .postgres import PostgresSupport


class PostgresEvidenceDrilldownReader(PostgresSupport):
    """Read one Evidence fragment without exposing PostgreSQL tables to product code."""

    async def evidence_fragment(self, fragment_id: UUID) -> EvidenceDrilldownRecord | None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT fragment.id AS evidence_fragment_id,
                       fragment.document_version_id,
                       fragment.artifact_id,
                       coalesce(fragment.locator ->> 'value', fragment.locator::text) AS locator,
                       fragment.excerpt,
                       fragment.structured_payload,
                       fragment.fragment_sha256,
                       document.id AS logical_document_id,
                       document.canonical_url,
                       document.external_id,
                       document.logical_title,
                       document.document_type,
                       publisher.id AS publisher_id,
                       publisher.canonical_name AS publisher_name,
                       publisher.publisher_domain,
                       publisher.source_kind AS publisher_source_kind,
                       publisher.quality_grade AS publisher_quality_grade,
                       publisher.independence_cluster,
                       version.version_ordinal,
                       timing.first_known_at,
                       timing.published_at,
                       timing.first_retrieved_at,
                       first_fetch.requested_url,
                       first_fetch.final_url AS retrieval_url,
                       connector.name AS retrieval_connector_name,
                       document.source_media_type,
                       document.source_capture_state,
                       document.source_locator_metadata,
                       document.raw_materialized_document_version_id,
                       first_fetch.response_headers ->> 'x-longcycle-raw-source-materialized'
                           AS raw_source_marker,
                       blob.sha256 AS preserved_content_sha256,
                       blob.content_type AS preserved_content_type
                FROM evidence.evidence_fragments fragment
                JOIN evidence.document_versions version
                  ON version.id = fragment.document_version_id
                JOIN evidence.documents document
                  ON document.id = version.document_id
                JOIN evidence.content_blobs blob
                  ON blob.id = version.content_blob_id
                LEFT JOIN evidence.publishers publisher
                  ON publisher.id = document.publisher_id
                JOIN evidence.document_fetches first_fetch
                  ON first_fetch.id = version.first_fetch_id
                 AND first_fetch.document_id = version.document_id
                 AND first_fetch.content_blob_id = version.content_blob_id
                JOIN evidence.source_connectors connector
                  ON connector.id = first_fetch.connector_id
                JOIN LATERAL (
                    SELECT min(source_fetch.first_known_at) AS first_known_at,
                           min(source_fetch.published_at)
                               FILTER (WHERE source_fetch.published_at IS NOT NULL) AS published_at,
                           min(source_fetch.retrieved_at) AS first_retrieved_at
                    FROM evidence.document_fetches source_fetch
                    WHERE source_fetch.document_id = version.document_id
                      AND source_fetch.content_blob_id = version.content_blob_id
                ) timing ON TRUE
                WHERE fragment.id = %s
                """,
                (fragment_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._record(row)

    @classmethod
    def _record(cls, row: dict[str, Any]) -> EvidenceDrilldownRecord:
        return EvidenceDrilldownRecord(
            evidence_fragment_id=row["evidence_fragment_id"],
            document_version_id=row["document_version_id"],
            artifact_id=row["artifact_id"],
            locator=row["locator"],
            excerpt=row["excerpt"],
            structured_payload=row["structured_payload"],
            fragment_sha256=row["fragment_sha256"],
            logical_document_id=row["logical_document_id"],
            canonical_url=row["canonical_url"],
            external_id=row["external_id"],
            logical_title=row["logical_title"],
            document_type=row["document_type"],
            publisher_id=row["publisher_id"],
            publisher_name=row["publisher_name"],
            publisher_domain=row["publisher_domain"],
            publisher_source_kind=row["publisher_source_kind"],
            publisher_quality_grade=row["publisher_quality_grade"],
            independence_cluster=row["independence_cluster"],
            version_ordinal=row["version_ordinal"],
            first_known_at=row["first_known_at"],
            published_at=row["published_at"],
            first_retrieved_at=row["first_retrieved_at"],
            requested_url=row["requested_url"],
            retrieval_url=row["retrieval_url"],
            retrieval_connector_name=row["retrieval_connector_name"],
            source_media_type=row["source_media_type"],
            current_source_capture_state=row["source_capture_state"],
            source_locator_metadata=row["source_locator_metadata"] or {},
            raw_materialized_document_version_id=row["raw_materialized_document_version_id"],
            representation_kind=cls._representation_kind(row),
            preserved_content_sha256=row["preserved_content_sha256"],
            preserved_content_type=row["preserved_content_type"],
        )

    @staticmethod
    def _representation_kind(row: dict[str, Any]) -> EvidenceRepresentationKind:
        marker = row["raw_source_marker"]
        if marker == "true":
            return "raw_source"
        if marker == "false":
            return "readable_representation"
        if row["raw_materialized_document_version_id"] == row["document_version_id"]:
            return "raw_source"
        return "legacy_or_unknown"
