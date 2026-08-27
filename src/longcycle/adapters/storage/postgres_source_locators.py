from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.adapters.storage.postgres import PostgresSupport
from longcycle.domain.models import stable_uuid_exact


_ALLOWED_CAPTURE_STATES = frozenset({"locator_verified", "content_verified"})


@dataclass(frozen=True, slots=True)
class RegisteredSourceLocator:
    document_id: UUID
    canonical_url: str
    external_id: str | None
    logical_title: str | None
    source_media_type: str | None
    source_capture_state: str
    source_locator_metadata: dict[str, Any]
    locator_verified_at: datetime | None
    content_verified_at: datetime | None
    materialized_at: datetime | None
    raw_materialized_document_version_id: UUID | None = None


class PostgresSourceLocatorRegistry(PostgresSupport):
    """Persist source identity/locator state independently from raw-file materialization.

    The registry reuses ``evidence.documents`` as the one logical document identity. A caller may
    establish ``locator_verified`` or ``content_verified`` before raw bytes exist. A later raw-byte
    acquisition must call :meth:`mark_materialized` explicitly after verifying that the archived
    document version really is the upstream raw source. Merely creating a document version from a
    faithful readable representation never means that the raw PDF has been materialized.
    """

    async def register(
        self,
        *,
        source_id: UUID,
        canonical_url: str,
        external_id: str | None = None,
        logical_title: str | None = None,
        document_type: str | None = None,
        source_media_type: str | None = "application/pdf",
        source_capture_state: str = "locator_verified",
        locator_metadata: dict[str, Any] | None = None,
        verified_at: datetime,
    ) -> RegisteredSourceLocator:
        if source_capture_state not in _ALLOWED_CAPTURE_STATES:
            raise ValueError(
                "source locator registration supports only locator_verified/content_verified; "
                "materialized requires explicit verified raw-source materialization"
            )
        if verified_at.tzinfo is None or verified_at.utcoffset() is None:
            raise ValueError("verified_at must be timezone-aware")
        if not canonical_url.strip():
            raise ValueError("canonical_url must be non-empty")

        metadata = dict(locator_metadata or {})
        if source_capture_state == "content_verified":
            verification_mode = metadata.get("content_verification_mode")
            if not isinstance(verification_mode, str) or not verification_mode.strip():
                raise ValueError(
                    "content_verified requires a non-empty content_verification_mode"
                )
            if metadata.get("claim_relevant_content_preserved") is not True:
                raise ValueError(
                    "content_verified requires claim_relevant_content_preserved=true"
                )

        async with self.connection() as connection:
            publisher_cursor = await connection.execute(
                "SELECT publisher_id FROM evidence.source_connectors WHERE id = %s",
                (source_id,),
            )
            publisher_row = await publisher_cursor.fetchone()
            if publisher_row is None:
                raise KeyError(f"source connector does not exist: {source_id}")

            publisher_id = publisher_row["publisher_id"]
            document_owner_id = publisher_id or source_id
            identity_owner_key = (
                f"publisher:{publisher_id}" if publisher_id is not None else f"connector:{source_id}"
            )
            proposed_id = stable_uuid_exact(
                "logical-document",
                str(document_owner_id),
                canonical_url,
                external_id or "",
            )
            locator_verified_at = verified_at
            content_verified_at = (
                verified_at if source_capture_state == "content_verified" else None
            )

            cursor = await connection.execute(
                """
                INSERT INTO evidence.documents (
                    id,
                    publisher_id,
                    identity_owner_key,
                    canonical_url,
                    external_id,
                    logical_title,
                    document_type,
                    source_media_type,
                    source_capture_state,
                    source_locator_metadata,
                    locator_verified_at,
                    content_verified_at
                ) VALUES (
                    %(id)s,
                    %(publisher_id)s,
                    %(identity_owner_key)s,
                    %(canonical_url)s,
                    %(external_id)s,
                    %(logical_title)s,
                    %(document_type)s,
                    %(source_media_type)s,
                    %(source_capture_state)s,
                    %(source_locator_metadata)s,
                    %(locator_verified_at)s,
                    %(content_verified_at)s
                )
                ON CONFLICT (identity_owner_key, canonical_url, external_id)
                DO UPDATE SET
                    logical_title = coalesce(evidence.documents.logical_title, EXCLUDED.logical_title),
                    document_type = coalesce(evidence.documents.document_type, EXCLUDED.document_type),
                    source_media_type = coalesce(
                        evidence.documents.source_media_type,
                        EXCLUDED.source_media_type
                    ),
                    source_locator_metadata = evidence.documents.source_locator_metadata
                        || EXCLUDED.source_locator_metadata,
                    locator_verified_at = coalesce(
                        evidence.documents.locator_verified_at,
                        EXCLUDED.locator_verified_at
                    ),
                    content_verified_at = coalesce(
                        evidence.documents.content_verified_at,
                        EXCLUDED.content_verified_at
                    ),
                    source_capture_state = CASE
                        WHEN evidence.documents.source_capture_state = 'materialized'
                            THEN 'materialized'
                        WHEN evidence.documents.source_capture_state = 'content_verified'
                            OR EXCLUDED.source_capture_state = 'content_verified'
                            THEN 'content_verified'
                        ELSE 'locator_verified'
                    END
                RETURNING
                    id,
                    canonical_url,
                    external_id,
                    logical_title,
                    source_media_type,
                    source_capture_state,
                    source_locator_metadata,
                    locator_verified_at,
                    content_verified_at,
                    materialized_at,
                    raw_materialized_document_version_id
                """,
                {
                    "id": proposed_id,
                    "publisher_id": publisher_id,
                    "identity_owner_key": identity_owner_key,
                    "canonical_url": canonical_url,
                    "external_id": external_id,
                    "logical_title": logical_title,
                    "document_type": document_type,
                    "source_media_type": source_media_type,
                    "source_capture_state": source_capture_state,
                    "source_locator_metadata": self.jsonb(metadata),
                    "locator_verified_at": locator_verified_at,
                    "content_verified_at": content_verified_at,
                },
            )
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("source locator upsert returned no document")
        return self._from_row(row)

    async def mark_materialized(
        self,
        *,
        document_id: UUID,
        document_version_id: UUID,
        verified_at: datetime,
        materialization_metadata: dict[str, Any] | None = None,
    ) -> RegisteredSourceLocator:
        """Mark raw upstream bytes materialized only after caller-side identity verification.

        ``document_version_id`` must belong to the same logical document. This explicit transition
        is deliberately separate from ordinary document-version persistence because a document
        version may contain a faithful readable representation rather than byte-identical raw PDF.
        """

        if verified_at.tzinfo is None or verified_at.utcoffset() is None:
            raise ValueError("verified_at must be timezone-aware")
        metadata = dict(materialization_metadata or {})
        if metadata.get("raw_source_identity_verified") is not True:
            raise ValueError("materialization requires raw_source_identity_verified=true")

        async with self.connection() as connection:
            version_cursor = await connection.execute(
                "SELECT document_id FROM evidence.document_versions WHERE id = %s",
                (document_version_id,),
            )
            version_row = await version_cursor.fetchone()
            if version_row is None:
                raise KeyError(f"document version does not exist: {document_version_id}")
            if version_row["document_id"] != document_id:
                raise ValueError("raw materialization document version belongs to another document")

            cursor = await connection.execute(
                """
                UPDATE evidence.documents
                SET source_capture_state = 'materialized',
                    materialized_at = coalesce(materialized_at, %(verified_at)s),
                    raw_materialized_document_version_id = %(document_version_id)s,
                    source_locator_metadata = source_locator_metadata || %(metadata)s
                WHERE id = %(document_id)s
                RETURNING
                    id,
                    canonical_url,
                    external_id,
                    logical_title,
                    source_media_type,
                    source_capture_state,
                    source_locator_metadata,
                    locator_verified_at,
                    content_verified_at,
                    materialized_at,
                    raw_materialized_document_version_id
                """,
                {
                    "verified_at": verified_at,
                    "document_version_id": document_version_id,
                    "document_id": document_id,
                    "metadata": self.jsonb(metadata),
                },
            )
            row = await cursor.fetchone()
        if row is None:
            raise KeyError(f"logical document does not exist: {document_id}")
        return self._from_row(row)

    async def pending_pdf_materializations(
        self,
        *,
        limit: int = 100,
    ) -> tuple[RegisteredSourceLocator, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT
                    id,
                    canonical_url,
                    external_id,
                    logical_title,
                    source_media_type,
                    source_capture_state,
                    source_locator_metadata,
                    locator_verified_at,
                    content_verified_at,
                    materialized_at,
                    raw_materialized_document_version_id
                FROM evidence.documents
                WHERE source_media_type = 'application/pdf'
                  AND source_capture_state <> 'materialized'
                ORDER BY
                    coalesce(content_verified_at, locator_verified_at, created_at),
                    id
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _from_row(row: dict[str, Any]) -> RegisteredSourceLocator:
        return RegisteredSourceLocator(
            document_id=row["id"],
            canonical_url=row["canonical_url"],
            external_id=row["external_id"],
            logical_title=row["logical_title"],
            source_media_type=row["source_media_type"],
            source_capture_state=row["source_capture_state"],
            source_locator_metadata=dict(row["source_locator_metadata"] or {}),
            locator_verified_at=row["locator_verified_at"],
            content_verified_at=row["content_verified_at"],
            materialized_at=row["materialized_at"],
            raw_materialized_document_version_id=row.get("raw_materialized_document_version_id"),
        )
