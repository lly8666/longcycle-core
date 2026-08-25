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
    """Typed unsourced recollection preserved before evidence-search planning is complete.

    Atlas admission validates the recalled lead itself, not whether a delegated search packet has
    already been fully designed. Fragmentary memory is allowed to remain fragmentary. The positive
    and disconfirmation query/source fields are still preserved here when available, while
    ``search_delegation_gaps`` provides a separate execution-readiness boundary for later search.
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
    def validate_period(self) -> MemoryLeadCandidate:
        start, end = self.approximate_period
        if start is not None and end is not None and end < start:
            raise ValueError("approximate_period end must not be before start")
        return self

    @property
    def search_delegation_gaps(self) -> tuple[str, ...]:
        """Return planning fields that must be filled before bounded evidence-search delegation."""

        fields = (
            "suggested_queries",
            "disconfirmation_queries",
            "suggested_source_types",
            "disconfirmation_source_types",
        )
        return tuple(field for field in fields if not getattr(self, field))

    @property
    def search_delegation_ready(self) -> bool:
        return not self.search_delegation_gaps


def require_memory_lead_search_ready(candidate: MemoryLeadCandidate) -> None:
    """Fail closed at delegated-search execution, not at Memory Atlas preservation."""

    gaps = candidate.search_delegation_gaps
    if gaps:
        raise ValueError(
            "memory lead is preserved but not ready for delegated evidence search; missing: "
            + ", ".join(gaps)
        )


class MemoryRepairOperation(BaseModel):
    """One explicit structural correction applied without rewriting the raw artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lead_id: str = Field(min_length=1)
    field: str = Field(min_length=1)
    original: Any
    repaired: Any
    reason: str = Field(min_length=1)


class MemoryRepairOverlay(BaseModel):
    """Auditable overlay for schema-only corrections to immutable model output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_file: str = Field(min_length=1)
    repair_policy: Literal["structural_only_no_new_historical_content"]
    repairs: tuple[MemoryRepairOperation, ...]
    raw_file_must_remain_unchanged: Literal[True]
    ingestion_rule: Literal["apply repair overlay before typed candidate validation"]

    @model_validator(mode="after")
    def repair_targets_are_unique(self) -> MemoryRepairOverlay:
        targets = [(repair.lead_id, repair.field) for repair in self.repairs]
        if len(targets) != len(set(targets)):
            raise ValueError("repair overlay contains duplicate lead/field targets")
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


def apply_memory_repair_overlay(
    text: str,
    overlay_text: str,
    *,
    source_file: str | None = None,
) -> str:
    """Apply only declared field substitutions and leave the raw JSONL untouched on disk."""

    overlay = MemoryRepairOverlay.model_validate_json(overlay_text)
    if source_file is not None and overlay.source_file != source_file:
        raise ValueError("repair overlay source_file does not match the JSONL being repaired")

    repairs_by_lead: dict[str, tuple[MemoryRepairOperation, ...]] = {}
    for repair in overlay.repairs:
        repairs_by_lead[repair.lead_id] = (*repairs_by_lead.get(repair.lead_id, ()), repair)

    applied: set[tuple[str, str]] = set()
    repaired_lines: list[str] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            repaired_lines.append(raw_line)
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"cannot apply repair overlay to invalid JSON on line {line_no}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"memory JSONL line {line_no} must contain an object")

        lead_id = payload.get("lead_id")
        if isinstance(lead_id, str):
            for repair in repairs_by_lead.get(lead_id, ()):
                if repair.field not in payload:
                    raise ValueError(
                        f"repair target {lead_id}.{repair.field} does not exist in source record"
                    )
                if payload[repair.field] != repair.original:
                    raise ValueError(
                        f"repair precondition changed for {lead_id}.{repair.field}; refusing drift"
                    )
                payload[repair.field] = repair.repaired
                applied.add((repair.lead_id, repair.field))

        repaired_lines.append(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    expected = {(repair.lead_id, repair.field) for repair in overlay.repairs}
    missing = expected - applied
    if missing:
        missing_text = ", ".join(f"{lead_id}.{field}" for lead_id, field in sorted(missing))
        raise ValueError(f"repair targets were not found in source JSONL: {missing_text}")

    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(repaired_lines) + suffix


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
If a semantic field is ambiguous, choose the least committal valid enum and add the ambiguous
field name to `uncertain_fields`.
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
