from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from longcycle.domain.enums import EntityType, ValidTimeKind
from longcycle.domain.models import (
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    SourceDocument,
    TimeRange,
)
from longcycle.ports.model import ExtractionTarget, planned_extraction_run_id


class _FixtureFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: EntityType
    entity_id: UUID
    field_name: str
    value: str
    value_type: str = "text"
    number: Decimal | None = None
    boolean: bool | None = None
    date_value: date | None = None
    entity_value: UUID | None = None
    json_value: dict[str, object] | list[object] | str | int | float | bool | None = None
    unit: str | None = None
    valid_from: date | datetime | None = None
    valid_to: date | datetime | None = None
    observed_at: datetime | None = None
    locator: str
    excerpt: str
    confidence: float = Field(ge=0, le=1)
    entity_match: float = Field(default=1, ge=0, le=1)
    time_unit_completeness: float = Field(default=1, ge=0, le=1)
    freshness: float = Field(default=1, ge=0, le=1)
    corroboration: float = Field(default=0, ge=0, le=1)
    high_impact: bool = False
    dimensions: FactDimensions = Field(default_factory=FactDimensions)
    valid_time_kind: ValidTimeKind = ValidTimeKind.UNKNOWN
    metadata: dict[str, object] = Field(default_factory=dict)


class _FixtureDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts: list[_FixtureFact]


class JsonFixtureGateway:
    """Deterministic extractor for contract tests and structured source feeds.

    Production AI adapters must return the same ExtractionEnvelope contract.
    """

    extractor_name = "json_fixture"
    extractor_version = "1.0.0"
    model_name = None

    def __init__(self, *, source_quality: float = 0.9, source_cluster: str | None = None) -> None:
        self.source_quality = source_quality
        self.source_cluster = source_cluster

    async def extract(
        self,
        *,
        document: SourceDocument,
        content: bytes,
        target: ExtractionTarget,
    ) -> ExtractionEnvelope:
        parsed = _FixtureDocument.model_validate(json.loads(content.decode("utf-8")))
        run_id = planned_extraction_run_id(
            document=document,
            gateway=self,
            target=target,
        )
        evidence: list[EvidenceFragment] = []
        candidates: list[FactAssertion] = []
        for fact in parsed.facts:
            if target.predicate_allowlist and fact.field_name not in target.predicate_allowlist:
                continue
            fragment = EvidenceFragment.create(document.id, fact.locator, fact.excerpt)
            evidence.append(fragment)
            candidates.append(
                FactAssertion(
                    entity_type=fact.entity_type,
                    entity_id=fact.entity_id,
                    field_name=fact.field_name,
                    value=fact.value,
                    value_type=fact.value_type,
                    normalized_number=fact.number,
                    normalized_boolean=fact.boolean,
                    normalized_date=fact.date_value,
                    normalized_entity_id=fact.entity_value,
                    normalized_json=fact.json_value,
                    normalized_unit=fact.unit,
                    dimensions=fact.dimensions,
                    valid_time_kind=fact.valid_time_kind,
                    valid_time=TimeRange(start=fact.valid_from, end=fact.valid_to),
                    observed_at=fact.observed_at,
                    source_id=document.source_id,
                    document_id=document.id,
                    evidence_fragment_id=fragment.id,
                    extraction_run_id=run_id,
                    extractor_name=self.extractor_name,
                    extractor_version=self.extractor_version,
                    source_cluster=self.source_cluster,
                    confidence=fact.confidence,
                    quality=QualityComponents(
                        source_quality=self.source_quality,
                        extraction_certainty=fact.confidence,
                        entity_match=fact.entity_match,
                        time_unit_completeness=fact.time_unit_completeness,
                        corroboration=fact.corroboration,
                        freshness=fact.freshness,
                    ),
                    high_impact=fact.high_impact,
                    metadata=fact.metadata,
                )
            )
        return ExtractionEnvelope(
            run_id=run_id,
            document_id=document.id,
            extractor_name=self.extractor_name,
            extractor_version=self.extractor_version,
            schema_version=target.schema_version,
            prompt_version=target.prompt_version,
            model_name=self.model_name,
            evidence=tuple(evidence),
            candidates=tuple(candidates),
        )


class NoopModelGateway:
    extractor_name = "noop"
    extractor_version = "1.0.0"
    model_name = None

    async def extract(
        self,
        *,
        document: SourceDocument,
        content: bytes,
        target: ExtractionTarget,
    ) -> ExtractionEnvelope:
        del content
        return ExtractionEnvelope(
            run_id=planned_extraction_run_id(
                document=document,
                gateway=self,
                target=target,
            ),
            document_id=document.id,
            extractor_name=self.extractor_name,
            extractor_version=self.extractor_version,
            schema_version=target.schema_version,
            prompt_version=target.prompt_version,
            candidates=(),
        )
