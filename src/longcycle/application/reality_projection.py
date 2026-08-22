from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator, model_validator

from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import (
    DomainModel,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    TimeRange,
    require_aware_datetime,
    stable_uuid_exact,
)


class RealityProjectionSubject(DomainModel):
    id: UUID
    entity_type: EntityType
    canonical_name: str = Field(min_length=1)


class GroundedRealityEvidence(DomainModel):
    fragment_key: str = Field(min_length=1)
    evidence_fragment_id: UUID
    document_version_id: UUID
    source_connector_id: UUID
    claim_role: str = Field(min_length=1)
    known_time_upper_bound: datetime
    source_published_at: datetime | None = None
    excerpt: str = Field(min_length=1)

    @field_validator("known_time_upper_bound", "source_published_at")
    @classmethod
    def times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)


class GroundedRealityProjectionItem(DomainModel):
    fact_key: str = Field(min_length=1)
    evidence_fragment_key: str = Field(min_length=1)
    subject_entity_id: UUID
    predicate_code: str = Field(min_length=3, pattern=r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")
    value_text: str = Field(min_length=1)
    valid_time_kind: Literal[ValidTimeKind.PERIOD] = ValidTimeKind.PERIOD
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    valid_time_precision: TemporalPrecision
    valid_time_text: str | None = None
    statistical_scope: str = Field(default="project milestone", min_length=1)
    extraction_confidence: float = Field(default=1.0, ge=0, le=1)
    source_quality: float = Field(default=1.0, ge=0, le=1)
    corroboration: float = Field(default=0.8, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("valid_from", "valid_to")
    @classmethod
    def valid_times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def has_valid_period(self) -> GroundedRealityProjectionItem:
        if self.valid_from is None and self.valid_to is None:
            raise ValueError("Reality projection period requires at least one valid-time bound")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("Reality projection valid_to must be after valid_from")
        if self.valid_time_precision == TemporalPrecision.APPROXIMATE and not self.valid_time_text:
            raise ValueError("approximate Reality projection must preserve source time text")
        return self


class GroundedRealityProjectionSpec(DomainModel):
    schema_version: Literal["longcycle-reality-projection-spec/v1"]
    task_id: str = Field(min_length=1)
    source_evidence_task_id: str = Field(min_length=1)
    allowed_claim_roles: tuple[str, ...]
    subjects: tuple[RealityProjectionSubject, ...]
    facts: tuple[GroundedRealityProjectionItem, ...]

    @model_validator(mode="after")
    def references_declared_subjects(self) -> GroundedRealityProjectionSpec:
        if not self.allowed_claim_roles:
            raise ValueError("Reality projection requires allowed claim roles")
        if any("expectation" in role or "guidance" in role for role in self.allowed_claim_roles):
            raise ValueError("Reality projection cannot allow expectation/guidance claim roles")
        subject_ids = {subject.id for subject in self.subjects}
        if len(subject_ids) != len(self.subjects):
            raise ValueError("Reality projection subjects must have unique ids")
        keys = {item.fact_key for item in self.facts}
        if len(keys) != len(self.facts):
            raise ValueError("Reality projection fact keys must be unique")
        missing = {item.subject_entity_id for item in self.facts} - subject_ids
        if missing:
            raise ValueError("Reality projection references undeclared subjects")
        return self


def build_grounded_reality_facts(
    spec: GroundedRealityProjectionSpec,
    evidence: tuple[GroundedRealityEvidence, ...],
) -> tuple[FactAssertion, ...]:
    """Project explicitly realized archived evidence into immutable FactAssertions.

    The spec supplies the bounded semantic interpretation. This function never infers
    an occurrence from management guidance and never makes source time more precise.
    """

    by_key = {item.fragment_key: item for item in evidence}
    if len(by_key) != len(evidence):
        raise ValueError("grounded Reality evidence keys must be unique")
    subjects = {item.id: item for item in spec.subjects}
    facts: list[FactAssertion] = []

    for item in spec.facts:
        try:
            cited = by_key[item.evidence_fragment_key]
        except KeyError as exc:
            raise ValueError(f"Reality fact cites unavailable evidence fragment: {exc.args[0]}") from exc
        if cited.claim_role not in set(spec.allowed_claim_roles):
            raise ValueError(f"Reality projection cites disallowed claim role: {cited.claim_role}")
        if "expectation" in cited.claim_role or "guidance" in cited.claim_role:
            raise ValueError("management expectation/guidance cannot be projected as Reality")

        subject = subjects[item.subject_entity_id]
        extraction_run_id = stable_uuid_exact(
            "reality-projection-run",
            spec.task_id,
            item.fact_key,
            str(cited.evidence_fragment_id),
        )
        facts.append(
            FactAssertion(
                id=stable_uuid_exact(
                    "reality-projection",
                    spec.task_id,
                    item.fact_key,
                    str(cited.evidence_fragment_id),
                ),
                entity_type=subject.entity_type,
                entity_id=subject.id,
                field_name=item.predicate_code,
                value=item.value_text,
                value_type=FactValueKind.TEXT,
                dimensions=FactDimensions(statistical_scope=item.statistical_scope),
                dimensions_complete=True,
                valid_time_kind=ValidTimeKind.PERIOD,
                valid_time=TimeRange(start=item.valid_from, end=item.valid_to),
                valid_time_precision=item.valid_time_precision,
                valid_time_text=item.valid_time_text,
                source_published_at=cited.source_published_at,
                known_at=cited.known_time_upper_bound,
                source_id=cited.source_connector_id,
                document_id=cited.document_version_id,
                evidence_fragment_id=cited.evidence_fragment_id,
                extraction_run_id=extraction_run_id,
                extractor_name="grounded-reality-projection",
                extractor_version="1.0.0",
                confidence=item.extraction_confidence,
                quality=QualityComponents(
                    source_quality=item.source_quality,
                    extraction_certainty=item.extraction_confidence,
                    entity_match=1.0,
                    time_unit_completeness=1.0,
                    corroboration=item.corroboration,
                    freshness=1.0,
                ),
                metadata={
                    **item.metadata,
                    "projection_task_id": spec.task_id,
                    "fact_key": item.fact_key,
                    "source_evidence_task_id": spec.source_evidence_task_id,
                    "source_fragment_key": item.evidence_fragment_key,
                    "source_claim_role": cited.claim_role,
                    "subject_canonical_name": subject.canonical_name,
                },
            )
        )

    return tuple(facts)
