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


class PostgresSourceLocatorRegistry(PostgresSupport):
    """Persist source identity/locator state before raw-file materialization.

    This registry reuses ``evidence.documents`` as the one logical document identity.
    It intentionally does not create ``document_fetches`` or ``document_versions`` until
    actual source-derived content is archived through the normal archive path.
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
                "materialized is assigned by the normal archived document-version path"
            )
        if verified_at.tzinfo is None or verified_at.utcoffset() is None:
            raise ValueError("verified_at must be timezone-aware")
        if not canonical_url.strip():
            raise ValueError("canonical_url must be non-empty")

        metadata = dict(locator_metadata or {})
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
                    materialized_at
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
                    materialized_at
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
        )
