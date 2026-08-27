from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator, model_validator

from .enums import (
    JudgmentOutcomeStatus,
    JudgmentRationaleKind,
    JudgmentRelationType,
    OutcomeSemanticRelation,
    OutcomeTimingRelation,
    TemporalPrecision,
)
from .models import DomainModel, require_aware_datetime


class MemorySubjectRef(DomainModel):
    """Storage-neutral identity for an entity or an industry node."""

    entity_id: UUID | None = None
    industry_node_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_subject(self) -> "MemorySubjectRef":
        if (self.entity_id is None) == (self.industry_node_id is None):
            raise ValueError("memory subject must identify exactly one entity or industry node")
        return self

    @property
    def key(self) -> str:
        if self.entity_id is not None:
            return f"entity:{self.entity_id}"
        assert self.industry_node_id is not None
        return f"industry:{self.industry_node_id}"


class TemporalExtent(DomainModel):
    """Shared replay-time representation for Reality, Judgment targets and Outcomes.

    Half-open bounds are computational structure. ``precision`` and ``source_text``
    preserve what the source actually supports so a month/quarter is never silently
    reinterpreted as an exact day.
    """

    kind: Literal["instant", "period", "timeless", "unknown"]
    at: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    source_text: str | None = None

    @field_validator("at", "start", "end")
    @classmethod
    def times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def valid_shape(self) -> "TemporalExtent":
        if self.kind == "instant":
            if self.at is None or self.start is not None or self.end is not None:
                raise ValueError("instant temporal extent requires only at")
        elif self.kind == "period":
            if self.at is not None or (self.start is None and self.end is None):
                raise ValueError("period temporal extent requires a start and/or end bound")
            if self.start is not None and self.end is not None and self.end <= self.start:
                raise ValueError("temporal extent end must be after start")
        else:
            if self.at is not None or self.start is not None or self.end is not None:
                raise ValueError("timeless/unknown temporal extent cannot carry bounds")
        if self.precision == TemporalPrecision.APPROXIMATE and not self.source_text:
            raise ValueError("approximate temporal extent must preserve source text")
        return self


class CanonicalRealityRecord(DomainModel):
    canonical_fact_version_id: UUID
    subject: MemorySubjectRef
    predicate_code: str = Field(min_length=1)
    value_kind: str = Field(min_length=1)
    value_text: str | None = None
    value_payload: str | None = None
    unit_code: str | None = None
    valid_time: TemporalExtent
    observed_time: TemporalExtent | None = None
    known_at: datetime
    confidence: float = Field(ge=0, le=1)
    publication_status: str = "trusted"
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def has_grounding(self) -> "CanonicalRealityRecord":
        if not self.evidence_fragment_ids:
            raise ValueError("canonical Reality must retain at least one evidence fragment")
        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("canonical Reality evidence references must be unique")
        if self.observed_time is not None and self.observed_time.kind != "instant":
            raise ValueError("canonical Reality observed_time must be an instant extent")
        return self


class JudgmentMemoryRecord(DomainModel):
    judgment_id: UUID
    judgment_key: str | None = None
    subject: MemorySubjectRef
    speaker_name_text: str | None = None
    topic_code: str = Field(min_length=1)
    judgment_kind: str = Field(min_length=1)
    target_time: TemporalExtent
    value_kind: str = Field(min_length=1)
    value_text: str | None = None
    value_payload: str | None = None
    summary: str = Field(min_length=1)
    known_at: datetime
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def has_grounding(self) -> "JudgmentMemoryRecord":
        if not self.evidence_fragment_ids:
            raise ValueError("Judgment memory record must retain evidence")
        return self


class JudgmentRationaleMemoryRecord(DomainModel):
    """Point-in-time rationale attached to an immutable Judgment."""

    rationale_id: UUID
    judgment_id: UUID
    rationale_kind: JudgmentRationaleKind
    summary: str = Field(min_length=1)
    linked_fact_assertion_id: UUID | None = None
    linked_judgment_id: UUID | None = None
    evidence_fragment_id: UUID | None = None
    ordinal: int = Field(default=0, ge=0)
    known_at: datetime

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked


class JudgmentRelationMemoryRecord(DomainModel):
    """Typed revision/dependency edge visible only once both Judgments are knowable."""

    from_judgment_id: UUID
    to_judgment_id: UUID
    relation_type: JudgmentRelationType
    reason_summary: str | None = None
    known_at: datetime

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked


class OutcomeMemoryRecord(DomainModel):
    evaluation_id: UUID
    judgment_id: UUID
    subject: MemorySubjectRef
    canonical_fact_version_id: UUID | None = None
    outcome_evidence_fragment_id: UUID | None = None
    evaluation_status: str = Field(min_length=1)
    semantic_relation: OutcomeSemanticRelation = OutcomeSemanticRelation.DIRECT_MATCH
    occurrence_time: TemporalExtent
    known_at: datetime
    timing_relation: str = Field(min_length=1)
    timing_delta_value: Decimal | None = None
    timing_delta_unit: str | None = None
    explanation: str | None = None
    evaluator_name: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)

    @field_validator("known_at")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_at")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def semantic_and_timing_contract(self) -> "OutcomeMemoryRecord":
        if (self.timing_delta_value is None) != (self.timing_delta_unit is None):
            raise ValueError("outcome timing delta value/unit must be supplied together")
        if self.semantic_relation != OutcomeSemanticRelation.DIRECT_MATCH:
            if self.evaluation_status != JudgmentOutcomeStatus.INDETERMINATE.value:
                raise ValueError("non-direct outcome memory must remain indeterminate")
            if self.timing_relation != OutcomeTimingRelation.NOT_COMPARABLE.value:
                raise ValueError("non-direct outcome memory cannot carry a timing comparison")
            if self.timing_delta_value is not None:
                raise ValueError("non-direct outcome memory cannot carry a timing delta")
        return self


class IndustrialMemoryTimeline(DomainModel):
    schema_version: Literal["longcycle-industrial-memory-timeline/v1"] = (
        "longcycle-industrial-memory-timeline/v1"
    )
    reality: tuple[CanonicalRealityRecord, ...] = ()
    judgments: tuple[JudgmentMemoryRecord, ...] = ()
    judgment_rationales: tuple[JudgmentRationaleMemoryRecord, ...] = ()
    judgment_relations: tuple[JudgmentRelationMemoryRecord, ...] = ()
    outcomes: tuple[OutcomeMemoryRecord, ...] = ()

    @model_validator(mode="after")
    def deterministic_order_and_references(self) -> "IndustrialMemoryTimeline":
        expected_reality = tuple(
            sorted(self.reality, key=lambda item: (item.known_at, str(item.canonical_fact_version_id)))
        )
        expected_judgments = tuple(
            sorted(self.judgments, key=lambda item: (item.known_at, str(item.judgment_id)))
        )
        expected_rationales = tuple(
            sorted(
                self.judgment_rationales,
                key=lambda item: (
                    item.known_at,
                    str(item.judgment_id),
                    item.ordinal,
                    str(item.rationale_id),
                ),
            )
        )
        expected_relations = tuple(
            sorted(
                self.judgment_relations,
                key=lambda item: (
                    item.known_at,
                    str(item.from_judgment_id),
                    str(item.to_judgment_id),
                    item.relation_type.value,
                ),
            )
        )
        expected_outcomes = tuple(
            sorted(self.outcomes, key=lambda item: (item.known_at, str(item.evaluation_id)))
        )
        if (
            self.reality != expected_reality
            or self.judgments != expected_judgments
            or self.judgment_rationales != expected_rationales
            or self.judgment_relations != expected_relations
            or self.outcomes != expected_outcomes
        ):
            raise ValueError("industrial memory timeline must be deterministically ordered")
        judgment_ids = {item.judgment_id for item in self.judgments}
        reality_ids = {item.canonical_fact_version_id for item in self.reality}
        for rationale in self.judgment_rationales:
            if rationale.judgment_id not in judgment_ids:
                raise ValueError("Judgment rationale references a Judgment missing from the timeline")
        for relation in self.judgment_relations:
            if (
                relation.from_judgment_id not in judgment_ids
                or relation.to_judgment_id not in judgment_ids
            ):
                raise ValueError("Judgment relation references a Judgment missing from the timeline")
        for outcome in self.outcomes:
            if outcome.judgment_id not in judgment_ids:
                raise ValueError("Outcome references a Judgment missing from the timeline")
            if (
                outcome.canonical_fact_version_id is not None
                and outcome.canonical_fact_version_id not in reality_ids
            ):
                raise ValueError("Outcome references canonical Reality missing from the timeline")
        return self


class PointInTimeMemorySnapshot(DomainModel):
    schema_version: Literal["longcycle-point-in-time-memory/v1"] = (
        "longcycle-point-in-time-memory/v1"
    )
    knowledge_cutoff: datetime
    reality: tuple[CanonicalRealityRecord, ...] = ()
    judgments: tuple[JudgmentMemoryRecord, ...] = ()
    judgment_rationales: tuple[JudgmentRationaleMemoryRecord, ...] = ()
    judgment_relations: tuple[JudgmentRelationMemoryRecord, ...] = ()
    outcomes: tuple[OutcomeMemoryRecord, ...] = ()

    @field_validator("knowledge_cutoff")
    @classmethod
    def cutoff_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "knowledge_cutoff")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def no_lookahead(self) -> "PointInTimeMemorySnapshot":
        future = [
            item.known_at
            for group in (
                self.reality,
                self.judgments,
                self.judgment_rationales,
                self.judgment_relations,
                self.outcomes,
            )
            for item in group
            if item.known_at > self.knowledge_cutoff
        ]
        if future:
            raise ValueError("point-in-time memory contains information from after the cutoff")
        return self


def snapshot_from_timeline(
    timeline: IndustrialMemoryTimeline,
    *,
    knowledge_cutoff: datetime,
) -> PointInTimeMemorySnapshot:
    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    return PointInTimeMemorySnapshot(
        knowledge_cutoff=checked,
        reality=tuple(item for item in timeline.reality if item.known_at <= checked),
        judgments=tuple(item for item in timeline.judgments if item.known_at <= checked),
        judgment_rationales=tuple(
            item for item in timeline.judgment_rationales if item.known_at <= checked
        ),
        judgment_relations=tuple(
            item for item in timeline.judgment_relations if item.known_at <= checked
        ),
        outcomes=tuple(item for item in timeline.outcomes if item.known_at <= checked),
    )
