from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.memory import (
    DirectSourceSearchStatus,
    MemoryAuditDisposition,
    MemoryHypothesisDisposition,
)
from longcycle.domain.models import DomainModel, require_aware_datetime


CoverageState = Literal["unseen", "thin", "needs_review"]


class RealityConflictAssertionRecord(DomainModel):
    assertion_id: UUID
    source_id: UUID
    known_at: datetime
    value_kind: str = Field(min_length=1)
    value: dict[str, Any]
    unit_code: str | None = None
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_value(self) -> "RealityConflictAssertionRecord":
        if not self.value:
            raise ValueError("conflict assertion must retain its typed value")
        if not self.evidence_fragment_ids:
            raise ValueError("conflict assertion must retain Evidence references")
        return self


class RealitySourceDisagreementRecord(DomainModel):
    """Retrospectively reconstructed source disagreement visible by source-known time.

    ``research_case_opened_at`` is curation provenance, not historical market knowledge.
    The historical visibility boundary is derived only from member assertion ``known_at``.
    """

    conflict_case_id: UUID
    fact_key_id: UUID
    subject: MemorySubjectRef
    predicate_code: str = Field(min_length=1)
    comparability_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    severity: str = Field(min_length=1)
    current_case_status: str = Field(min_length=1)
    archive_disagreement_known_at: datetime
    research_case_opened_at: datetime
    research_case_closed_at: datetime | None = None
    assertions: tuple[RealityConflictAssertionRecord, ...]

    @field_validator(
        "archive_disagreement_known_at",
        "research_case_opened_at",
        "research_case_closed_at",
    )
    @classmethod
    def times_are_aware(cls, value: datetime | None, info: Any) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def explicit_multi_source_conflict(self) -> "RealitySourceDisagreementRecord":
        if len(self.assertions) < 2:
            raise ValueError("source disagreement requires at least two visible conflict members")
        if len({item.source_id for item in self.assertions}) < 2:
            raise ValueError("source disagreement requires at least two distinct sources")
        expected = max(item.known_at for item in self.assertions)
        if self.archive_disagreement_known_at != expected:
            raise ValueError("archive disagreement known time must equal latest visible member known time")
        return self


class MemoryDisagreementOpenRecord(DomainModel):
    disagreement_case_id: UUID
    lead_id: UUID
    subject: MemorySubjectRef
    lead_summary: str = Field(min_length=1)
    claim_scope: str = Field(min_length=1)
    opened_reason: str = Field(min_length=1)
    current_disposition: MemoryAuditDisposition | None = None
    resolution_rationale: str | None = None
    supporting_evidence_ids: tuple[UUID, ...] = ()
    contradicting_evidence_ids: tuple[UUID, ...] = ()
    research_recorded_at: datetime

    @field_validator("research_recorded_at")
    @classmethod
    def research_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "research_recorded_at")
        assert checked is not None
        return checked


class MemoryHypothesisOpenRecord(DomainModel):
    assessment_id: UUID
    lead_id: UUID
    subject: MemorySubjectRef
    lead_summary: str = Field(min_length=1)
    disposition: MemoryHypothesisDisposition
    direct_source_search_status: DirectSourceSearchStatus
    inference_confidence: float = Field(ge=0, le=1)
    reasoning_summary: str = Field(min_length=1)
    alternative_explanations: tuple[str, ...] = ()
    falsification_conditions: tuple[str, ...] = ()
    supporting_evidence_ids: tuple[UUID, ...] = ()
    contradicting_evidence_ids: tuple[UUID, ...] = ()
    research_recorded_at: datetime

    @field_validator("research_recorded_at")
    @classmethod
    def research_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "research_recorded_at")
        assert checked is not None
        return checked


class MemoryCoverageGapRecord(DomainModel):
    campaign_id: UUID
    snapshot_label: str = Field(min_length=1)
    dimension_type: str = Field(min_length=1)
    dimension_key: str = Field(min_length=1)
    period_from: date | None = None
    period_to: date | None = None
    coverage_state: CoverageState
    notes: str | None = None
    research_recorded_at: datetime

    @field_validator("research_recorded_at")
    @classmethod
    def research_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "research_recorded_at")
        assert checked is not None
        return checked


class CurrentResearchOpenStateBundle(DomainModel):
    disagreements: tuple[MemoryDisagreementOpenRecord, ...] = ()
    hypotheses: tuple[MemoryHypothesisOpenRecord, ...] = ()
    coverage_gaps: tuple[MemoryCoverageGapRecord, ...] = ()
