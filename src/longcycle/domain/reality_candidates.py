from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import DomainModel, require_aware_datetime


RealityCandidateStatus = Literal["review", "quarantined"]


class RealityResearchCandidate(DomainModel):
    """Source-backed Reality assertion that is visible to research but not canonical truth.

    CAP-0003 owns the reconciliation decision. This record is only a CAP-0005 read model for
    assertions whose point-in-time decision is REVIEW or QUARANTINE. It deliberately preserves
    source Evidence and both source-known and decision-known time so researcher visibility cannot
    backdate a later reconciliation result.
    """

    assertion_id: UUID
    industry_node_id: UUID
    subject: MemorySubjectRef
    canonical_name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    predicate_code: str = Field(min_length=1)
    status: RealityCandidateStatus
    raw_value: str = Field(min_length=1)
    value_kind: str = Field(min_length=1)
    unit_code: str | None = None
    valid_time_kind: str = Field(min_length=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    source_known_at: datetime
    decision_known_at: datetime
    confidence: float = Field(ge=0, le=1)
    reconciliation_score: float = Field(ge=0, le=1)
    reason_codes: tuple[str, ...] = ()
    conflicting_assertion_ids: tuple[UUID, ...] = ()
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("valid_from", "valid_to", "source_known_at", "decision_known_at")
    @classmethod
    def times_are_aware(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value, "reality_research_candidate.time")

    @model_validator(mode="after")
    def remains_auditable_research_only_candidate(self) -> RealityResearchCandidate:
        if not self.evidence_fragment_ids:
            raise ValueError("Reality research candidate requires source Evidence")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("Reality research candidate Evidence must be unique")
        if len(set(self.conflicting_assertion_ids)) != len(self.conflicting_assertion_ids):
            raise ValueError("Reality research candidate conflict ids must be unique")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("Reality research candidate valid_to must be after valid_from")
        return self

    @property
    def canonical(self) -> bool:
        return False

    @property
    def research_only(self) -> bool:
        return True
