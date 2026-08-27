from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.models import DomainModel, require_aware_datetime


SourceCaptureState = Literal["locator_verified", "content_verified", "materialized"]
EvidenceRepresentationKind = Literal[
    "raw_source",
    "readable_representation",
    "legacy_or_unknown",
]


class EvidenceDrilldownRecord(DomainModel):
    """Storage-neutral read model for one claim-scoped Evidence fragment.

    Historical claim visibility is bounded by ``first_known_at``. Current source
    preservation state is retained only as operational provenance and must not be
    narrated as historical market knowledge. The preserved content hash identifies
    the exact bytes used by this Evidence version; it is not automatically a raw
    upstream source hash.
    """

    evidence_fragment_id: UUID
    document_version_id: UUID
    artifact_id: UUID | None = None
    locator: str = Field(min_length=1)
    excerpt: str | None = None
    structured_payload: dict[str, Any] | None = None
    fragment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    logical_document_id: UUID
    canonical_url: str = Field(min_length=1)
    external_id: str | None = None
    logical_title: str | None = None
    document_type: str | None = None

    publisher_id: UUID | None = None
    publisher_name: str | None = None
    publisher_domain: str | None = None
    publisher_source_kind: str | None = None
    publisher_quality_grade: str | None = None
    independence_cluster: str | None = None

    version_ordinal: int = Field(ge=1)
    first_known_at: datetime
    published_at: datetime | None = None
    first_retrieved_at: datetime
    requested_url: str = Field(min_length=1)
    retrieval_url: str = Field(min_length=1)
    retrieval_connector_name: str = Field(min_length=1)

    source_media_type: str | None = None
    current_source_capture_state: SourceCaptureState
    source_locator_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_materialized_document_version_id: UUID | None = None

    representation_kind: EvidenceRepresentationKind
    preserved_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preserved_content_type: str = Field(min_length=1)

    @field_validator("first_known_at", "published_at", "first_retrieved_at")
    @classmethod
    def times_are_aware(cls, value: datetime | None, info: Any) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def evidence_and_source_state_are_truthful(self) -> "EvidenceDrilldownRecord":
        if self.excerpt is None and self.structured_payload is None:
            raise ValueError("Evidence drilldown requires excerpt or structured payload")
        if (
            self.current_source_capture_state == "materialized"
            and self.raw_materialized_document_version_id is None
        ):
            raise ValueError("materialized source state requires a raw document version id")
        if (
            self.current_source_capture_state != "materialized"
            and self.raw_materialized_document_version_id is not None
        ):
            raise ValueError("non-materialized source state cannot claim a raw document version")
        return self
