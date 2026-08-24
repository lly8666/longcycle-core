from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import DomainModel, FactAssertion, require_aware_datetime


class IndustryDescriptor(DomainModel):
    industry_node_id: UUID
    canonical_name: str = Field(min_length=1)
    node_kind: str = Field(min_length=1)
    archetype: str | None = None


class ResolvedIndustryMembershipResolution(DomainModel):
    """One already-decided CAP-0003 resolution supplied to catalog projection.

    The projection layer is not allowed to choose between assertions.  It receives
    the exact selected assertion set from reconciliation and fails closed unless that
    set can represent one unambiguous industry-membership row.
    """

    resolution_id: UUID
    selected_assertions: tuple[FactAssertion, ...]
    confidence: float = Field(ge=0, le=1)
    resolved_at: datetime

    @field_validator("resolved_at")
    @classmethod
    def resolution_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "resolved_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def selected_assertions_are_unique(self) -> "ResolvedIndustryMembershipResolution":
        ids = [item.id for item in self.selected_assertions]
        if len(ids) != len(set(ids)):
            raise ValueError("resolution selected assertions must be unique")
        return self


class IndustryMembershipProjection(DomainModel):
    """Validated materialization payload for the orientation catalog.

    ``known_at`` and Evidence identities remain explicit even though the catalog table
    does not duplicate them.  The read adapter reconstructs them from the selected
    assertion behind ``resolution_id``.  ``system_from`` is deterministic curation
    provenance only and must never become historical market-known time.
    """

    membership_id: UUID
    industry_node_id: UUID
    entity_id: UUID
    role: str = Field(min_length=1)
    exposure_type: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    known_at: datetime
    system_from: datetime
    confidence: float = Field(ge=0, le=1)
    resolution_id: UUID
    assertion_id: UUID
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at", "system_from")
    @classmethod
    def projection_times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "industry_membership_projection_time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_projection(self) -> "IndustryMembershipProjection":
        if not self.evidence_fragment_ids:
            raise ValueError("industry membership projection requires supporting Evidence")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("industry membership projection Evidence must be unique")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustrySubjectMembershipRecord(DomainModel):
    """One source-grounded catalog membership version used only for researcher orientation.

    ``known_at`` is reconstructed from the selected FactAssertion(s) behind the
    membership resolution. ``system_from`` is retained only as deterministic curation
    provenance; it must never be substituted for historical market-known time.
    """

    membership_id: UUID
    industry_node_id: UUID
    subject: MemorySubjectRef
    canonical_name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    role: str = Field(min_length=1)
    exposure_type: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    known_at: datetime
    system_from: datetime
    confidence: float = Field(ge=0, le=1)
    resolution_id: UUID
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at", "system_from")
    @classmethod
    def times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "orientation_time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_entity_membership(self) -> "IndustrySubjectMembershipRecord":
        if self.subject.entity_id is None:
            raise ValueError("industry orientation membership must identify an entity subject")
        if not self.evidence_fragment_ids:
            raise ValueError("industry orientation membership must retain Evidence references")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustryOrientationCatalog(DomainModel):
    industry: IndustryDescriptor
    memberships: tuple[IndustrySubjectMembershipRecord, ...] = ()
