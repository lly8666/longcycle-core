from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from longcycle.domain.memory import (
    ClaimScope,
    EntityResolutionState,
    MemoryBasis,
    MemoryLeadKind,
    PrecisionRisk,
)


MemoryRelationType = Literal[
    "associated_with",
    "possible_cause",
    "possible_effect",
    "predecessor",
    "successor",
    "search_synonym",
    "same_episode",
    "cross_chain_link",
    "possible_revision",
]


class MemoryLeadRelationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_ref: str = Field(min_length=1)
    relation_type: MemoryRelationType
    explanation: str


class MemoryLeadCandidate(BaseModel):
    """Typed candidate emitted by a memory model before persistence.

    This is intentionally stricter than the persisted MemoryLead domain object because
    generation-time search archaeology and falsification fields must be complete before
    a lead is accepted into a campaign atlas.
    """

    model_config = ConfigDict(extra="forbid")

    lead_id: str = Field(min_length=1)
    shard_id: str = Field(min_length=1)
    pass_id: str = Field(min_length=1)
    lead_kind: MemoryLeadKind
    claim_scope: ClaimScope
    memory_basis: MemoryBasis
    summary: str = Field(min_length=1)
    approximate_period: tuple[date | None, date | None]
    memory_confidence: float = Field(ge=0, le=1)
    importance_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    searchability_score: float = Field(ge=0, le=1)
    precision_risk: PrecisionRisk
    entity_resolution_state: EntityResolutionState
    uncertain_fields: tuple[str, ...]
    aliases_or_old_terms: tuple[str, ...]
    why_search_may_miss_it: str | None
    recalled_details: dict[str, Any]
    possible_actors: tuple[str, ...]
    suggested_queries: tuple[str, ...]
    disconfirmation_queries: tuple[str, ...]
    suggested_source_types: tuple[str, ...]
    disconfirmation_source_types: tuple[str, ...]
    satellite_trigger: str | None
    relations: tuple[MemoryLeadRelationCandidate, ...]

    @model_validator(mode="after")
    def validate_period_and_search_contract(self) -> MemoryLeadCandidate:
        start, end = self.approximate_period
        if start is not None and end is not None and end < start:
            raise ValueError("approximate_period end must not be before start")
        if not self.suggested_queries:
            raise ValueError("at least one suggested query is required")
        if not self.disconfirmation_queries:
            raise ValueError("at least one disconfirmation query is required")
        if not self.suggested_source_types:
            raise ValueError("at least one suggested source type is required")
        if not self.disconfirmation_source_types:
            raise ValueError("at least one disconfirmation source type is required")
        return self


@dataclass(frozen=True, slots=True)
class MemoryCandidateValidationFailure:
    line_no: int
    raw_line: str
    reason: str


@dataclass(frozen=True, slots=True)
class MemoryJsonlValidationResult:
    accepted: tuple[MemoryLeadCandidate, ...]
    failures: tuple[MemoryCandidateValidationFailure, ...]

    @property
    def is_clean(self) -> bool:
        return not self.failures


def validate_memory_jsonl(text: str) -> MemoryJsonlValidationResult:
    accepted: list[MemoryLeadCandidate] = []
    failures: list[MemoryCandidateValidationFailure] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(
                MemoryCandidateValidationFailure(
                    line_no=line_no,
                    raw_line=raw_line,
                    reason=f"invalid_json: {exc.msg} at column {exc.colno}",
                )
            )
            continue

        try:
            accepted.append(MemoryLeadCandidate.model_validate(payload))
        except ValidationError as exc:
            failures.append(
                MemoryCandidateValidationFailure(
                    line_no=line_no,
                    raw_line=raw_line,
                    reason=exc.json(),
                )
            )

    return MemoryJsonlValidationResult(tuple(accepted), tuple(failures))


def build_memory_candidate_repair_prompt(*, raw_line: str, validation_reason: str) -> str:
    """Ask a model to repair structure only, without generating new historical content."""

    lead_kinds = ", ".join(item.value for item in MemoryLeadKind)
    claim_scopes = ", ".join(item.value for item in ClaimScope)
    memory_bases = ", ".join(item.value for item in MemoryBasis)

    return f"""Repair ONE Longcycle Memory Lead JSON object.

This is a STRUCTURAL REPAIR task, not a research task.
Do not add a new event, actor, date, number, causal claim, citation, URL, or search result.
Preserve the historical meaning and uncertainty of the original record.
If a semantic field is ambiguous, choose the least committal valid enum and add the ambiguous field name to `uncertain_fields`.
Return exactly one JSON object and no Markdown.

Allowed lead_kind values:
{lead_kinds}

Allowed claim_scope values:
{claim_scopes}

Allowed memory_basis values:
{memory_bases}

Validation failure:
{validation_reason}

Original JSON:
{raw_line}
"""
