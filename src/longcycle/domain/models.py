from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from .enums import (
    Cadence,
    Decision,
    EntityType,
    FactEvidenceRole,
    FactStatus,
    FactValueKind,
    FreightBasis,
    JobStage,
    JobStatus,
    MarketBasis,
    ObservationFrequency,
    PriceComponent,
    QualityGrade,
    ReviewSeverity,
    SourceKind,
    TaxBasis,
    TemporalPrecision,
    ValidTimeKind,
)

LONGCYCLE_NAMESPACE = UUID("bfc8f890-665e-4d4b-a17c-a56e061e29f3")


def utc_now() -> datetime:
    return datetime.now(UTC)


def stable_uuid(*parts: str) -> UUID:
    normalized = "|".join(part.strip().lower() for part in parts)
    return uuid5(LONGCYCLE_NAMESPACE, normalized)


def stable_uuid_exact(*parts: str) -> UUID:
    """Build an identity for opaque values without case or delimiter loss."""
    identity = "exact-v1:" + json.dumps(
        parts,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return uuid5(LONGCYCLE_NAMESPACE, identity)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def canonical_decimal_identity(value: Decimal | None) -> str | None:
    """Return a scale-insensitive identity for an exact Decimal value."""
    if value is None:
        return None
    if value == 0:
        return "0"
    if not value.is_finite():
        return str(value)
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def require_aware_datetime(value: datetime | None, field_name: str | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{field_name or 'datetime'} must include a timezone")
    return value


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Industry(DomainModel):
    id: UUID
    group_id: UUID
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    canonical_name: str
    archetype: str
    active: bool = True
    taxonomy_version: str


class SourceDefinition(DomainModel):
    id: UUID
    name: str
    kind: SourceKind
    plugin: str
    quality_grade: QualityGrade
    publisher_domain: str | None = None
    rate_limit_per_minute: int = Field(default=30, ge=1, le=10_000)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    syndication_cluster: str | None = None


class DiscoveryItem(DomainModel):
    source_id: UUID
    external_id: str | None = None
    url: str
    title_hint: str | None = None
    published_at_hint: datetime | None = None
    industry_ids: tuple[UUID, ...] = ()
    discovered_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("external_id", mode="before")
    @classmethod
    def blank_external_id_is_missing(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("published_at_hint", "discovered_at")
    @classmethod
    def published_hint_is_aware(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value, "published_at_hint")

    @property
    def idempotency_key(self) -> str:
        return hashlib.sha256(f"{self.source_id}|{self.external_id or self.url}".encode()).hexdigest()


class RawPayload(DomainModel):
    content: bytes
    content_type: str
    canonical_url: str
    status_code: int = 200
    headers: dict[str, str] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=utc_now)

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_is_aware(cls, value: datetime) -> datetime:
        result = require_aware_datetime(value, "retrieved_at")
        assert result is not None
        return result

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class SourceDocument(DomainModel):
    id: UUID
    source_id: UUID
    canonical_url: str
    external_id: str | None = None
    title: str | None = None
    published_at: datetime | None = None
    first_known_at: datetime
    retrieved_at: datetime
    content_type: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    blob_key: str
    byte_length: int = Field(ge=0)
    http_status: int = Field(default=200, ge=100, le=599)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("external_id", mode="before")
    @classmethod
    def blank_document_external_id_is_missing(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("published_at", "first_known_at", "retrieved_at")
    @classmethod
    def document_times_are_aware(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @classmethod
    def from_payload(
        cls,
        *,
        source_id: UUID,
        payload: RawPayload,
        blob_key: str,
        external_id: str | None = None,
        title: str | None = None,
        published_at: datetime | None = None,
        first_known_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SourceDocument":
        digest = payload.sha256
        normalized_external_id = external_id.strip() if external_id and external_id.strip() else None
        document_metadata = dict(metadata or {})
        document_metadata["response_headers"] = dict(payload.headers)
        return cls(
            id=stable_uuid_exact(
                "document-version-v2",
                str(source_id),
                payload.canonical_url,
                normalized_external_id or "",
                digest,
            ),
            source_id=source_id,
            canonical_url=payload.canonical_url,
            external_id=normalized_external_id,
            title=title,
            published_at=published_at,
            first_known_at=first_known_at or payload.retrieved_at,
            retrieved_at=payload.retrieved_at,
            content_type=payload.content_type,
            content_sha256=digest,
            blob_key=blob_key,
            byte_length=len(payload.content),
            http_status=payload.status_code,
            metadata=document_metadata,
        )


class DocumentArtifact(DomainModel):
    """Immutable parser output whose bytes are already stored in the archive."""

    id: UUID
    document_id: UUID
    artifact_type: str = Field(min_length=1)
    producer_name: str = Field(min_length=1)
    producer_version: str = Field(min_length=1)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    blob_key: str = Field(min_length=1)
    byte_length: int = Field(ge=0)
    content_type: str = Field(min_length=1)

    @classmethod
    def create(
        cls,
        *,
        document_id: UUID,
        artifact_type: str,
        producer_name: str,
        producer_version: str,
        input_sha256: str,
        content_sha256: str,
        blob_key: str,
        byte_length: int,
        content_type: str,
    ) -> "DocumentArtifact":
        return cls(
            id=stable_uuid_exact(
                "artifact",
                str(document_id),
                artifact_type,
                producer_name,
                producer_version,
                input_sha256,
            ),
            document_id=document_id,
            artifact_type=artifact_type,
            producer_name=producer_name,
            producer_version=producer_version,
            input_sha256=input_sha256,
            content_sha256=content_sha256,
            blob_key=blob_key,
            byte_length=byte_length,
            content_type=content_type,
        )


class EvidenceFragment(DomainModel):
    id: UUID
    document_id: UUID
    artifact_id: UUID | None = None
    locator: str
    excerpt: str | None = None
    structured_payload: dict[str, Any] | None = None
    fragment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def has_material_evidence(self) -> "EvidenceFragment":
        has_excerpt = self.excerpt is not None and bool(self.excerpt.strip())
        has_structured_payload = self.structured_payload is not None and bool(self.structured_payload)
        if not (has_excerpt or has_structured_payload):
            raise ValueError("evidence requires a nonblank excerpt or structured payload")
        return self

    @classmethod
    def create(
        cls,
        document_id: UUID,
        locator: str,
        excerpt: str | None,
        structured_payload: dict[str, Any] | None = None,
        artifact_id: UUID | None = None,
    ) -> "EvidenceFragment":
        body = canonical_json({"excerpt": excerpt, "structured_payload": structured_payload})
        digest = hashlib.sha256(body.encode()).hexdigest()
        identity_parts = ["evidence", str(document_id), locator, digest]
        if artifact_id is not None:
            identity_parts.append(str(artifact_id))
        return cls(
            id=stable_uuid_exact(*identity_parts),
            document_id=document_id,
            artifact_id=artifact_id,
            locator=locator,
            excerpt=excerpt,
            structured_payload=structured_payload,
            fragment_sha256=digest,
        )

    @property
    def locator_sha256(self) -> str:
        return hashlib.sha256(canonical_json({"locator": self.locator}).encode()).hexdigest()


class TimeRange(DomainModel):
    start: date | datetime | None = None
    end: date | datetime | None = None

    @model_validator(mode="after")
    def valid_order(self) -> "TimeRange":
        if isinstance(self.start, datetime):
            require_aware_datetime(self.start, "start")
        if isinstance(self.end, datetime):
            require_aware_datetime(self.end, "end")
        if self.start is not None and self.end is not None:
            start = (
                datetime.combine(self.start, datetime.min.time(), UTC)
                if isinstance(self.start, date) and not isinstance(self.start, datetime)
                else self.start
            )
            end = (
                datetime.combine(self.end, datetime.min.time(), UTC)
                if isinstance(self.end, date) and not isinstance(self.end, datetime)
                else self.end
            )
            if end <= start:
                raise ValueError("time range end must be greater than start")
        return self

    @staticmethod
    def _as_utc(value: datetime | date | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(UTC)
        return datetime.combine(value, datetime.min.time(), UTC)

    @property
    def start_utc(self) -> datetime | None:
        return self._as_utc(self.start)

    @property
    def end_utc(self) -> datetime | None:
        return self._as_utc(self.end)


class QualityComponents(DomainModel):
    source_quality: float = Field(ge=0, le=1)
    extraction_certainty: float = Field(ge=0, le=1)
    entity_match: float = Field(ge=0, le=1)
    time_unit_completeness: float = Field(ge=0, le=1)
    corroboration: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    conflict_penalty: float = Field(default=0, ge=0, le=1)


class FactDimensions(DomainModel):
    schema_version: str = "fact-dimensions/v1"
    product_spec_id: UUID | None = None
    geography_scheme: str | None = None
    geography_code: str | None = None
    market_basis: MarketBasis | None = None
    contract_basis: str | None = None
    tax_basis: TaxBasis | None = None
    freight_basis: FreightBasis | None = None
    incoterm: str | None = None
    currency_code: str | None = None
    frequency: ObservationFrequency | None = None
    price_component: PriceComponent | None = None
    statistical_scope: str | None = None

    @model_validator(mode="after")
    def geography_is_a_pair(self) -> "FactDimensions":
        if (self.geography_scheme is None) != (self.geography_code is None):
            raise ValueError("geography_scheme and geography_code must be supplied together")
        return self

    @field_validator("geography_scheme", "geography_code", "contract_basis", "statistical_scope")
    @classmethod
    def normalize_dimension_text(cls, value: str | None) -> str | None:
        return " ".join(value.lower().split()) if value else None

    @field_validator("currency_code", "incoterm")
    @classmethod
    def normalize_uppercase_codes(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @property
    def canonical_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=False)

    @property
    def comparability_hash(self) -> str:
        return hashlib.sha256(canonical_json(self.canonical_payload).encode()).hexdigest()


class FactEvidenceRef(DomainModel):
    evidence_fragment_id: UUID
    evidence_role: FactEvidenceRole = FactEvidenceRole.SUPPORTING


class FactAssertion(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    entity_type: EntityType
    entity_id: UUID
    field_name: str
    value: str = Field(min_length=1)
    value_type: FactValueKind = FactValueKind.TEXT
    normalized_number: Decimal | None = None
    normalized_boolean: bool | None = None
    normalized_date: date | None = None
    normalized_entity_id: UUID | None = None
    normalized_json: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    normalized_unit: str | None = None
    dimensions: FactDimensions = Field(default_factory=FactDimensions)
    dimensions_complete: bool = False
    valid_time_kind: ValidTimeKind = ValidTimeKind.UNKNOWN
    valid_time: TimeRange = Field(default_factory=TimeRange)
    valid_time_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    valid_time_text: str | None = None
    observed_at: datetime | None = None
    observed_at_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    observed_at_text: str | None = None
    source_published_at: datetime | None = None
    known_at: datetime = Field(default_factory=utc_now)
    source_id: UUID
    document_id: UUID
    evidence: tuple[FactEvidenceRef, ...]
    extraction_run_id: UUID
    extractor_name: str
    extractor_version: str
    normalizer_name: str = "assertion_normalizer"
    normalizer_version: str = "2.0.0"
    source_cluster: str | None = None
    confidence: float = Field(ge=0, le=1)
    quality: QualityComponents
    high_impact: bool = False
    status: FactStatus = FactStatus.CANDIDATE
    supersedes_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observed_at", "source_published_at", "known_at")
    @classmethod
    def assertion_times_are_aware(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @field_validator("field_name")
    @classmethod
    def field_name_is_namespaced(cls, value: str) -> str:
        if "." not in value:
            raise ValueError("field_name must be namespaced, e.g. capacity.nameplate")
        return value

    @field_validator("value_type", mode="before")
    @classmethod
    def normalize_value_kind(cls, value: Any) -> Any:
        return FactValueKind.NUMERIC.value if value == "number" else value

    @model_validator(mode="before")
    @classmethod
    def restore_and_mirror_valid_time_precision(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        legacy_evidence_id = payload.pop("evidence_fragment_id", None)
        if legacy_evidence_id is not None:
            if payload.get("evidence"):
                raise ValueError(
                    "FactAssertion cannot supply both evidence and legacy evidence_fragment_id"
                )
            payload["evidence"] = (
                {
                    "evidence_fragment_id": legacy_evidence_id,
                    "evidence_role": FactEvidenceRole.SUPPORTING.value,
                },
            )
        metadata = dict(payload.get("metadata") or {})
        precision_key = "_longcycle_valid_time_precision"
        text_key = "_longcycle_valid_time_text"
        if "valid_time_precision" not in payload and precision_key in metadata:
            payload["valid_time_precision"] = metadata[precision_key]
        if "valid_time_text" not in payload and text_key in metadata:
            payload["valid_time_text"] = metadata[text_key]
        precision = payload.get("valid_time_precision", TemporalPrecision.UNKNOWN)
        precision_value = precision.value if isinstance(precision, TemporalPrecision) else str(precision)
        metadata[precision_key] = precision_value
        source_text = payload.get("valid_time_text")
        if source_text is not None:
            metadata[text_key] = source_text
        else:
            metadata.pop(text_key, None)

        observed_precision_key = "_longcycle_observed_at_precision"
        observed_text_key = "_longcycle_observed_at_text"
        if "observed_at_precision" not in payload and observed_precision_key in metadata:
            payload["observed_at_precision"] = metadata[observed_precision_key]
        if "observed_at_text" not in payload and observed_text_key in metadata:
            payload["observed_at_text"] = metadata[observed_text_key]
        if payload.get("observed_at") is not None:
            observed_precision = payload.get(
                "observed_at_precision",
                TemporalPrecision.UNKNOWN,
            )
            observed_precision_value = (
                observed_precision.value
                if isinstance(observed_precision, TemporalPrecision)
                else str(observed_precision)
            )
            metadata[observed_precision_key] = observed_precision_value
            observed_text = payload.get("observed_at_text")
            if observed_text is not None:
                metadata[observed_text_key] = observed_text
            else:
                metadata.pop(observed_text_key, None)
        else:
            metadata.pop(observed_precision_key, None)
            metadata.pop(observed_text_key, None)
        payload["metadata"] = metadata
        return payload

    @model_validator(mode="after")
    def valid_time_precision_matches_semantics(self) -> "FactAssertion":
        bounded = {
            TemporalPrecision.INSTANT,
            TemporalPrecision.SECOND,
            TemporalPrecision.MINUTE,
            TemporalPrecision.HOUR,
            TemporalPrecision.DAY,
            TemporalPrecision.WEEK,
            TemporalPrecision.MONTH,
            TemporalPrecision.QUARTER,
            TemporalPrecision.HALF_YEAR,
            TemporalPrecision.YEAR,
            TemporalPrecision.RANGE,
        }
        if self.valid_time_precision in bounded and self.valid_time_kind != ValidTimeKind.PERIOD:
            raise ValueError("bounded fact valid-time precision requires period valid_time_kind")
        if self.valid_time_precision == TemporalPrecision.APPROXIMATE and not self.valid_time_text:
            raise ValueError("approximate fact valid time must preserve the source time text")
        if self.valid_time_kind == ValidTimeKind.PERIOD and (
            self.valid_time.start is None and self.valid_time.end is None
        ):
            raise ValueError("period fact valid time requires a start and/or end bound")
        if self.observed_at is None:
            if (
                self.observed_at_precision != TemporalPrecision.UNKNOWN
                or self.observed_at_text is not None
            ):
                raise ValueError("observed-at precision/text requires observed_at")
        elif (
            self.observed_at_precision == TemporalPrecision.APPROXIMATE
            and not self.observed_at_text
        ):
            raise ValueError("approximate observed-at time must preserve the source time text")
        if not self.evidence:
            raise ValueError("FactAssertion requires at least one EvidenceFragment reference")
        evidence_ids = [item.evidence_fragment_id for item in self.evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("FactAssertion evidence fragments must be unique")
        if not any(item.evidence_role == FactEvidenceRole.SUPPORTING for item in self.evidence):
            raise ValueError("FactAssertion requires at least one supporting evidence fragment")
        return self

    @property
    def immutable_fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude={"status"})
        if self.value_type == FactValueKind.NUMERIC:
            payload["normalized_number"] = canonical_decimal_identity(self.normalized_number)
        return hashlib.sha256(canonical_json(payload).encode()).hexdigest()

    @property
    def scope_key(self) -> str:
        return canonical_json(
            {
                "subject_type": self.entity_type.value,
                "subject_id": str(self.entity_id),
                "predicate": self.field_name,
                "comparability_hash": self.comparability_hash,
            }
        )

    @property
    def comparability_hash(self) -> str:
        return self.dimensions.comparability_hash

    @property
    def value_fingerprint(self) -> str:
        payload: dict[str, Any]
        if self.value_type == FactValueKind.NUMERIC:
            payload = {
                "kind": self.value_type.value,
                "number": canonical_decimal_identity(self.normalized_number),
                "unit": self.normalized_unit,
            }
        elif self.value_type == FactValueKind.BOOLEAN:
            payload = {"kind": self.value_type.value, "boolean": self.normalized_boolean}
        elif self.value_type == FactValueKind.DATE:
            payload = {
                "kind": self.value_type.value,
                "date": self.normalized_date.isoformat() if self.normalized_date is not None else None,
            }
        elif self.value_type == FactValueKind.ENTITY:
            payload = {
                "kind": self.value_type.value,
                "entity": str(self.normalized_entity_id) if self.normalized_entity_id is not None else None,
            }
        elif self.value_type == FactValueKind.JSON:
            payload = {"kind": self.value_type.value, "json": self.normalized_json}
        else:
            payload = {"kind": self.value_type.value, "text": self.value}
        return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


class ExtractionEnvelope(DomainModel):
    run_id: UUID
    document_id: UUID
    extractor_name: str
    extractor_version: str
    schema_version: str
    prompt_version: str | None = None
    model_name: str | None = None
    evidence: tuple[EvidenceFragment, ...] = ()
    candidates: tuple[FactAssertion, ...]
    tokens_in: int = Field(default=0, ge=0)
    tokens_out: int = Field(default=0, ge=0)
    cost_microunits: int = Field(default=0, ge=0)
    raw_response_blob_key: str | None = None


class ReconciliationResult(DomainModel):
    assertion_id: UUID
    decision: Decision
    score: float = Field(ge=0, le=1)
    reason_codes: tuple[str, ...]
    conflicting_assertion_ids: tuple[UUID, ...] = ()
    status: FactStatus
    evaluator_name: str = "rule_reconciler"
    evaluator_version: str = "2.0.0"

    @model_validator(mode="after")
    def decision_and_status_agree(self) -> "ReconciliationResult":
        expected = {
            Decision.ACCEPT: FactStatus.TRUSTED,
            Decision.REVIEW: FactStatus.REVIEW,
            Decision.CONFLICT: FactStatus.CONFLICT,
            Decision.QUARANTINE: FactStatus.QUARANTINED,
        }[self.decision]
        if self.status != expected:
            raise ValueError(
                f"decision {self.decision.value} requires status {expected.value}"
            )
        return self


class ReviewItem(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    assertion_id: UUID
    severity: ReviewSeverity
    reason_codes: tuple[str, ...]
    related_assertion_ids: tuple[UUID, ...] = ()
    status: str = "open"
    created_at: datetime = Field(default_factory=utc_now)


class CollectionJob(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    stage: JobStage
    status: JobStatus = JobStatus.QUEUED
    source_id: UUID | None = None
    industry_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: float = Field(default=0, ge=0, le=100)
    idempotency_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    available_at: datetime = Field(default_factory=utc_now)
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=5, ge=1, le=50)
    lease_owner: str | None = None
    lease_token: UUID | None = None
    lease_expires_at: datetime | None = None
    parent_job_id: UUID | None = None
    trace_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("available_at", "lease_expires_at", "created_at")
    @classmethod
    def job_times_are_aware(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def leased_job_has_fencing_fields(self) -> "CollectionJob":
        if self.status == JobStatus.LEASED and (
            self.lease_owner is None or self.lease_token is None or self.lease_expires_at is None
        ):
            raise ValueError("leased jobs require owner, token and expiration")
        return self


class CollectionPolicy(DomainModel):
    industry_id: UUID
    cadence: Cadence
    heat_score: float = Field(ge=0, le=100)
    data_risk_score: float = Field(ge=0, le=100)
    consecutive_low_days: int = Field(default=0, ge=0)
    event_override_until: datetime | None = None
    timezone: str = "Asia/Shanghai"

    @field_validator("event_override_until")
    @classmethod
    def override_is_aware(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value, "event_override_until")

    @property
    def priority(self) -> float:
        return round(0.7 * self.heat_score + 0.3 * self.data_risk_score, 2)
