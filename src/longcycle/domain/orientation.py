from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import DomainModel, FactAssertion, require_aware_datetime


IndustryMembershipReasoningMode = Literal["standard", "deep"]


class IndustryDescriptor(DomainModel):
    industry_node_id: UUID
    canonical_name: str = Field(min_length=1)
    node_kind: str = Field(min_length=1)
    archetype: str | None = None


class ResolvedIndustryMembershipResolution(DomainModel):
    """One already-decided CAP-0003 resolution supplied to catalog projection.

    CAP-0003 owns which source-backed assertions are selected. CAP-0005 may need a
    model-mediated semantic decision to turn that selected set into one catalog row,
    but it may never rewrite the source assertions or pretend the model decision is
    source Evidence.
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
    def selected_assertions_are_unique(self) -> ResolvedIndustryMembershipResolution:
        ids = [item.id for item in self.selected_assertions]
        if len(ids) != len(set(ids)):
            raise ValueError("resolution selected assertions must be unique")
        if not ids:
            raise ValueError("industry membership resolution requires selected assertions")
        return self


class IndustryMembershipSemanticJudgment(DomainModel):
    """Transient structured output from the membership semantic model judge.

    A standard pass detects whether the supplied material definitions conflict. When
    they do, the application must escalate to ``deep`` reasoning before any catalog
    materialization. ``can_materialize`` means the model has selected one source-backed
    assertion representation; it does not promote model reasoning into Evidence.
    """

    reasoning_mode: IndustryMembershipReasoningMode
    selected_assertion_id: UUID | None = None
    material_conflict_detected: bool = False
    can_materialize: bool = False
    reasoning_summary: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str | None = None
    decided_at: datetime

    @field_validator("decided_at")
    @classmethod
    def decision_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "membership_semantic_judgment.decided_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def valid_semantic_judgment(self) -> IndustryMembershipSemanticJudgment:
        if self.can_materialize and self.selected_assertion_id is None:
            raise ValueError("materializable membership judgment must select an assertion")
        if self.reasoning_mode == "standard" and self.material_conflict_detected:
            if self.can_materialize:
                raise ValueError(
                    "standard membership judgment with material conflict must escalate to deep reasoning"
                )
        return self


class IndustryMembershipSemanticDecision(DomainModel):
    """Persisted audit provenance for the model-mediated catalog projection.

    This row records how CAP-0005 represented an already-selected CAP-0003 assertion
    set. It is research/projection provenance, not canonical Reality and not Evidence.
    """

    decision_id: UUID
    resolution_id: UUID
    candidate_assertion_ids: tuple[UUID, ...]
    selected_assertion_id: UUID
    reasoning_mode: IndustryMembershipReasoningMode
    material_conflict_detected: bool = False
    reasoning_summary: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str | None = None
    decided_at: datetime
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("decided_at")
    @classmethod
    def persisted_decision_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "membership_semantic_decision.decided_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def auditable_decision(self) -> IndustryMembershipSemanticDecision:
        if not self.candidate_assertion_ids:
            raise ValueError("membership semantic decision requires candidate assertions")
        if len(set(self.candidate_assertion_ids)) != len(self.candidate_assertion_ids):
            raise ValueError("membership semantic decision candidates must be unique")
        if self.selected_assertion_id not in self.candidate_assertion_ids:
            raise ValueError("membership semantic decision must select one candidate assertion")
        if not self.evidence_fragment_ids:
            raise ValueError("membership semantic decision requires source Evidence provenance")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("membership semantic decision Evidence must be unique")
        if self.material_conflict_detected and self.reasoning_mode != "deep":
            raise ValueError("material conflict requires a persisted deep-reasoning decision")
        return self

    @property
    def is_canonical_truth(self) -> bool:
        return False


class IndustryMembershipProjection(DomainModel):
    """Validated materialization payload for the orientation catalog.

    ``known_at`` and Evidence identities remain explicit even though the catalog table
    does not duplicate them. The read adapter reconstructs them from the model-selected
    source assertion behind ``semantic_decision_id``. ``system_from`` is deterministic
    curation provenance only and must never become historical market-known time.
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
    semantic_decision_id: UUID
    assertion_id: UUID
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at", "system_from")
    @classmethod
    def projection_times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "industry_membership_projection_time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_projection(self) -> IndustryMembershipProjection:
        if not self.evidence_fragment_ids:
            raise ValueError("industry membership projection requires supporting Evidence")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("industry membership projection Evidence must be unique")
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to <= self.valid_from
        ):
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustrySubjectMembershipRecord(DomainModel):
    """One source-grounded catalog membership version used for researcher orientation.

    ``known_at`` is reconstructed from the source assertion selected by the persisted
    semantic decision. ``system_from`` is retained only as deterministic curation
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
    semantic_decision_id: UUID | None = None
    semantic_decision_mode: IndustryMembershipReasoningMode | None = None
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at", "system_from")
    @classmethod
    def times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "orientation_time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_entity_membership(self) -> IndustrySubjectMembershipRecord:
        if self.subject.entity_id is None:
            raise ValueError("industry orientation membership must identify an entity subject")
        if not self.evidence_fragment_ids:
            raise ValueError("industry orientation membership must retain Evidence references")
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to <= self.valid_from
        ):
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustrySubjectDiscoveryRecord(DomainModel):
    """A deterministic researcher-discovery basis that is weaker than membership truth.

    These records let the read model recover a subject when already-grounded memory is
    explicitly scoped to the industry. They never create a membership, role, importance
    ranking or causal relation. The distinction between direct membership and entailed
    discoverability stays visible to the researcher.
    """

    industry_node_id: UUID
    subject: MemorySubjectRef
    canonical_name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    basis_kind: Literal["accepted_reality", "grounded_judgment"]
    basis_id: UUID
    semantic_code: str = Field(min_length=1)
    known_at: datetime
    evidence_fragment_ids: tuple[UUID, ...]
    entailment_rule: Literal["explicit_industry_scope"] = "explicit_industry_scope"

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "industry_subject_discovery_known_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def grounded_entity_discovery(self) -> IndustrySubjectDiscoveryRecord:
        if self.subject.entity_id is None:
            raise ValueError("industry discovery must identify an entity subject")
        if not self.evidence_fragment_ids:
            raise ValueError("industry discovery must retain Evidence references")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("industry discovery Evidence must be unique")
        return self


class IndustryOrientationCatalog(DomainModel):
    industry: IndustryDescriptor
    memberships: tuple[IndustrySubjectMembershipRecord, ...] = ()
