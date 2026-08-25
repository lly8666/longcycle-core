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
    """One already-decided CAP-0003 resolution supplied to catalog projection."""

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
    """Structured output from one actual host/model judgment execution.

    The running Longcycle Agent may implement the judge directly. This object describes that
    execution's answer; the application later wraps it in an append-only ModelJudgmentRun.
    It is interpretation provenance, never source Evidence or canonical Reality.
    """

    reasoning_mode: IndustryMembershipReasoningMode
    selected_assertion_id: UUID | None = None
    alternative_assertion_ids: tuple[UUID, ...] = ()
    material_conflict_detected: bool = False
    can_materialize: bool = False
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str = Field(min_length=1)
    provider_name: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str | None = None
    started_at: datetime
    completed_at: datetime

    @field_validator("started_at", "completed_at")
    @classmethod
    def run_times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "membership_semantic_judgment.run_time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def valid_semantic_judgment(self) -> IndustryMembershipSemanticJudgment:
        if self.completed_at < self.started_at:
            raise ValueError("membership semantic judgment completed_at precedes started_at")
        if self.can_materialize and self.selected_assertion_id is None:
            raise ValueError("materializable membership judgment must select an assertion")
        if self.selected_assertion_id in self.alternative_assertion_ids:
            raise ValueError("selected assertion cannot also be an alternative")
        if len(set(self.alternative_assertion_ids)) != len(self.alternative_assertion_ids):
            raise ValueError("alternative assertions must be unique")
        return self


class IndustryMembershipModelJudgmentRun(DomainModel):
    """Append-only provenance for one actual standard/deep model execution."""

    run_id: UUID
    resolution_id: UUID
    candidate_assertion_ids: tuple[UUID, ...]
    input_assertion_hashes: tuple[str, ...]
    reasoning_mode: IndustryMembershipReasoningMode
    provider_name: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str | None = None
    started_at: datetime
    completed_at: datetime
    selected_assertion_id: UUID | None = None
    alternative_assertion_ids: tuple[UUID, ...] = ()
    material_conflict_detected: bool = False
    confidence: float = Field(ge=0, le=1)
    can_materialize: bool = False
    reasoning_summary: str = Field(min_length=1)
    triggered_deep: bool = False
    deep_trigger_reasons: tuple[str, ...] = ()
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("started_at", "completed_at")
    @classmethod
    def persisted_run_times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "membership_model_judgment_run.time")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def auditable_run(self) -> IndustryMembershipModelJudgmentRun:
        if not self.candidate_assertion_ids:
            raise ValueError("membership model run requires candidate assertions")
        if len(self.candidate_assertion_ids) != len(self.input_assertion_hashes):
            raise ValueError("membership model run requires one input hash per candidate assertion")
        if len(set(self.candidate_assertion_ids)) != len(self.candidate_assertion_ids):
            raise ValueError("membership model run candidates must be unique")
        if self.selected_assertion_id is not None and self.selected_assertion_id not in self.candidate_assertion_ids:
            raise ValueError("membership model run selected assertion must be a candidate")
        if any(item not in self.candidate_assertion_ids for item in self.alternative_assertion_ids):
            raise ValueError("membership model run alternatives must be candidates")
        if self.completed_at < self.started_at:
            raise ValueError("membership model run completed_at precedes started_at")
        if not self.evidence_fragment_ids:
            raise ValueError("membership model run requires source Evidence provenance")
        if self.triggered_deep != bool(self.deep_trigger_reasons):
            raise ValueError("triggered_deep must match presence of deep trigger reasons")
        return self

    @property
    def is_canonical_truth(self) -> bool:
        return False


class IndustryMembershipSemanticDecision(DomainModel):
    """Durable semantic conclusion supported by source assertions and model judgment runs.

    Decision identity is about the semantic conclusion, not a particular model execution.
    Repeated model vintages may support the same decision while every run remains separately
    auditable. ``supporting_assertion_ids`` is the deterministic equivalence cluster whose
    entity/industry/role/exposure/validity semantics match the chosen representation; it may
    therefore preserve corroboration from more than the representative selected assertion.
    """

    decision_id: UUID
    resolution_id: UUID
    semantic_scope: Literal["industry.membership"] = "industry.membership"
    candidate_assertion_ids: tuple[UUID, ...]
    selected_assertion_id: UUID
    supporting_assertion_ids: tuple[UUID, ...]
    decision_summary: str = Field(min_length=1)
    first_decided_at: datetime
    last_confirmed_at: datetime
    supporting_judgment_run_ids: tuple[UUID, ...]
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("first_decided_at", "last_confirmed_at")
    @classmethod
    def persisted_decision_times_are_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "membership_semantic_decision.time")
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
        if not self.supporting_assertion_ids:
            raise ValueError("membership semantic decision requires supporting source assertions")
        if len(set(self.supporting_assertion_ids)) != len(self.supporting_assertion_ids):
            raise ValueError("membership semantic decision supporting assertions must be unique")
        if self.selected_assertion_id not in self.supporting_assertion_ids:
            raise ValueError("selected assertion must be part of the supporting equivalence cluster")
        if any(item not in self.candidate_assertion_ids for item in self.supporting_assertion_ids):
            raise ValueError("supporting assertions must be CAP-0003 selected candidates")
        if not self.supporting_judgment_run_ids:
            raise ValueError("membership semantic decision requires supporting model judgment runs")
        if len(set(self.supporting_judgment_run_ids)) != len(self.supporting_judgment_run_ids):
            raise ValueError("membership semantic decision judgment runs must be unique")
        if not self.evidence_fragment_ids:
            raise ValueError("membership semantic decision requires source Evidence provenance")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("membership semantic decision Evidence must be unique")
        if self.last_confirmed_at < self.first_decided_at:
            raise ValueError("semantic decision last_confirmed_at precedes first_decided_at")
        return self

    @property
    def is_canonical_truth(self) -> bool:
        return False


class IndustryMembershipProjection(DomainModel):
    """Validated materialization payload for the orientation catalog."""

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
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustrySubjectMembershipRecord(DomainModel):
    """One source-grounded catalog membership version used for researcher orientation."""

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
    semantic_decision_supporting_run_count: int = Field(default=0, ge=0)
    semantic_decision_latest_reasoning_mode: IndustryMembershipReasoningMode | None = None
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
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("membership valid_to must be after valid_from")
        return self


class IndustrySubjectDiscoveryRecord(DomainModel):
    """A deterministic researcher-discovery basis that is weaker than membership truth."""

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
