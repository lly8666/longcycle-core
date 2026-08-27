from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, ValidationInfo, field_validator, model_validator

from longcycle.domain.enums import (
    JudgmentDirection,
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentOutcomeStatus,
    JudgmentRationaleKind,
    JudgmentRelationType,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    OutcomeSemanticRelation,
    OutcomeTimingRelation,
    TemporalDeltaUnit,
    TemporalPrecision,
)
from longcycle.domain.models import DomainModel, canonical_json, require_aware_datetime, utc_now


class JudgmentEvidenceRef(DomainModel):
    evidence_fragment_id: UUID
    evidence_role: JudgmentEvidenceRole = JudgmentEvidenceRole.STATEMENT


class JudgmentAssertion(DomainModel):
    """Append-only record of what a speaker asserted under the knowledge of its vintage."""

    id: UUID = Field(default_factory=uuid4)
    speaker_entity_id: UUID | None = None
    speaker_name_text: str | None = None
    speaker_role: str | None = None
    speaker_affiliation_entity_id: UUID | None = None
    subject_entity_id: UUID | None = None
    subject_industry_node_id: UUID | None = None
    topic_code: str = Field(min_length=1)
    predicate_code: str | None = None
    comparability_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    dimensions_complete: bool = False
    judgment_kind: JudgmentKind
    target_time_kind: JudgmentTargetTimeKind
    target_at: datetime | None = None
    target_from: datetime | None = None
    target_to: datetime | None = None
    target_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    target_text: str | None = None
    value_kind: JudgmentValueKind
    value_numeric: Decimal | None = None
    value_low: Decimal | None = None
    value_high: Decimal | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_date: date | None = None
    value_entity_id: UUID | None = None
    value_json: Any | None = None
    direction: JudgmentDirection | None = None
    unit_code: str | None = None
    expressed_probability: float | None = Field(default=None, ge=0, le=1)
    summary: str = Field(min_length=1)
    source_published_at: datetime | None = None
    first_known_at: datetime
    extraction_run_id: UUID
    source_connector_id: UUID
    extractor_name: str = Field(min_length=1)
    extractor_version: str = Field(min_length=1)
    extraction_confidence: float = Field(ge=0, le=1)
    evidence: tuple[JudgmentEvidenceRef, ...]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "target_at",
        "target_from",
        "target_to",
        "source_published_at",
        "first_known_at",
    )
    @classmethod
    def judgment_times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def matches_database_contract(self) -> JudgmentAssertion:
        if self.speaker_entity_id is None and self.speaker_name_text is None:
            raise ValueError("judgment requires a speaker entity or speaker name")
        if (self.subject_entity_id is None) == (self.subject_industry_node_id is None):
            raise ValueError("judgment requires exactly one subject identity")
        if (self.predicate_code is None) != (self.comparability_hash is None):
            raise ValueError("predicate_code and comparability_hash must be supplied together")
        self._validate_target_time()
        self._validate_value()
        if not self.evidence:
            raise ValueError("judgment requires evidence")
        if not any(item.evidence_role == JudgmentEvidenceRole.STATEMENT for item in self.evidence):
            raise ValueError("judgment requires at least one statement evidence fragment")
        pairs = {(item.evidence_fragment_id, item.evidence_role) for item in self.evidence}
        if len(pairs) != len(self.evidence):
            raise ValueError("judgment evidence links must be unique")
        return self

    def _validate_target_time(self) -> None:
        if self.target_time_kind == JudgmentTargetTimeKind.INSTANT:
            if self.target_at is None or self.target_from is not None or self.target_to is not None:
                raise ValueError("instant judgment target requires only target_at")
        elif self.target_time_kind == JudgmentTargetTimeKind.PERIOD:
            if self.target_at is not None or (self.target_from is None and self.target_to is None):
                raise ValueError("period judgment target requires target_from and/or target_to")
        elif any(value is not None for value in (self.target_at, self.target_from, self.target_to)):
            raise ValueError("timeless/unknown judgment target cannot carry target timestamps")
        if self.target_from is not None and self.target_to is not None and self.target_to <= self.target_from:
            raise ValueError("judgment target_to must be after target_from")
        if self.target_precision == TemporalPrecision.APPROXIMATE and not self.target_text:
            raise ValueError("approximate judgment target must preserve the source target text")
        if (
            self.target_time_kind == JudgmentTargetTimeKind.UNKNOWN
            and self.target_precision != TemporalPrecision.UNKNOWN
            and not self.target_text
        ):
            raise ValueError("non-unknown precision on an unbounded target requires source target text")

    def _validate_value(self) -> None:
        values = {
            JudgmentValueKind.NUMERIC: self.value_numeric,
            JudgmentValueKind.TEXT: self.value_text,
            JudgmentValueKind.BOOLEAN: self.value_boolean,
            JudgmentValueKind.DATE: self.value_date,
            JudgmentValueKind.ENTITY: self.value_entity_id,
            JudgmentValueKind.JSON: self.value_json,
            JudgmentValueKind.DIRECTION: self.direction,
        }
        range_present = self.value_low is not None and self.value_high is not None
        if self.value_kind == JudgmentValueKind.NUMERIC_RANGE:
            if not range_present:
                raise ValueError("numeric-range judgment requires value_low and value_high")
            if self.value_low is not None and self.value_high is not None and self.value_low > self.value_high:
                raise ValueError("judgment value_low must not exceed value_high")
            if any(value is not None for value in values.values()):
                raise ValueError("numeric-range judgment cannot carry another value representation")
            return

        required = values[self.value_kind]
        if required is None:
            raise ValueError(f"{self.value_kind.value} judgment is missing its value")
        competing = [
            value
            for kind, value in values.items()
            if kind != self.value_kind and value is not None
        ]
        if competing or self.value_low is not None or self.value_high is not None:
            raise ValueError("judgment value must use exactly one representation")

    @property
    def content_fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude={"id"})
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class JudgmentRationale(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    judgment_id: UUID
    rationale_kind: JudgmentRationaleKind
    summary: str = Field(min_length=1)
    linked_fact_assertion_id: UUID | None = None
    linked_judgment_id: UUID | None = None
    evidence_fragment_id: UUID | None = None
    ordinal: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def does_not_self_link(self) -> JudgmentRationale:
        if self.linked_judgment_id == self.judgment_id:
            raise ValueError("judgment rationale cannot link to itself")
        return self


class JudgmentRelation(DomainModel):
    from_judgment_id: UUID
    to_judgment_id: UUID
    relation_type: JudgmentRelationType
    reason_summary: str | None = None

    @model_validator(mode="after")
    def does_not_self_link(self) -> JudgmentRelation:
        if self.from_judgment_id == self.to_judgment_id:
            raise ValueError("judgment relation cannot link an assertion to itself")
        return self


class OutcomeObservation(DomainModel):
    """Evidence-backed realized outcome time with source-supported precision."""

    evidence_fragment_id: UUID
    occurrence_from: datetime | None = None
    occurrence_to: datetime | None = None
    occurrence_precision: TemporalPrecision
    occurrence_text: str | None = None
    first_known_at: datetime

    @field_validator("occurrence_from", "occurrence_to", "first_known_at")
    @classmethod
    def outcome_times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def preserves_source_precision(self) -> OutcomeObservation:
        if (
            self.occurrence_from is not None
            and self.occurrence_to is not None
            and self.occurrence_to <= self.occurrence_from
        ):
            raise ValueError("outcome occurrence_to must be after occurrence_from")
        if self.occurrence_precision == TemporalPrecision.APPROXIMATE and not self.occurrence_text:
            raise ValueError("approximate outcome must preserve source occurrence text")
        return self


class JudgmentOutcomeEvaluation(DomainModel):
    """Later evaluation kept separate from the original immutable Judgment."""

    id: UUID = Field(default_factory=uuid4)
    judgment_id: UUID
    canonical_fact_version_id: UUID | None = None
    outcome_evidence_fragment_id: UUID | None = None
    evaluation_status: JudgmentOutcomeStatus
    semantic_relation: OutcomeSemanticRelation = OutcomeSemanticRelation.DIRECT_MATCH
    outcome_from: datetime | None = None
    outcome_to: datetime | None = None
    outcome_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    outcome_text: str | None = None
    outcome_first_known_at: datetime | None = None
    timing_relation: OutcomeTimingRelation = OutcomeTimingRelation.NOT_COMPARABLE
    timing_delta_value: Decimal | None = None
    timing_delta_unit: TemporalDeltaUnit | None = None
    numeric_error: Decimal | None = None
    relative_error: float | None = None
    direction_correct: bool | None = None
    explanation: str | None = None
    evaluator_name: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)
    evaluated_at: datetime = Field(default_factory=utc_now)

    @field_validator("outcome_from", "outcome_to", "outcome_first_known_at", "evaluated_at")
    @classmethod
    def evaluation_times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def timing_fields_are_consistent(self) -> JudgmentOutcomeEvaluation:
        if (
            self.outcome_from is not None
            and self.outcome_to is not None
            and self.outcome_to <= self.outcome_from
        ):
            raise ValueError("outcome_to must be after outcome_from")
        if (self.timing_delta_value is None) != (self.timing_delta_unit is None):
            raise ValueError("timing delta value and unit must be supplied together")
        if self.timing_relation == OutcomeTimingRelation.NOT_COMPARABLE and self.timing_delta_value is not None:
            raise ValueError("non-comparable timing cannot carry a synthetic delta")
        if self.outcome_precision == TemporalPrecision.APPROXIMATE and not self.outcome_text:
            raise ValueError("approximate outcome must preserve source occurrence text")
        if self.semantic_relation != OutcomeSemanticRelation.DIRECT_MATCH:
            if self.evaluation_status != JudgmentOutcomeStatus.INDETERMINATE:
                raise ValueError("non-direct outcome semantics require indeterminate evaluation status")
            if self.timing_relation != OutcomeTimingRelation.NOT_COMPARABLE:
                raise ValueError("non-direct outcome semantics cannot carry a timing comparison")
            if self.timing_delta_value is not None:
                raise ValueError("non-direct outcome semantics cannot carry a timing delta")
        return self
