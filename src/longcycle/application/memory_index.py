from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from longcycle.application.memory_ingest import MemoryLeadCandidate
from longcycle.domain.memory import ClaimScope, MemoryBasis, MemoryLeadKind


class CompactMemoryLead(BaseModel):
    """Small, auditable representation used by self-gap and saturation passes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lead_id: str
    pass_id: str
    lead_kind: MemoryLeadKind
    claim_scope: ClaimScope
    memory_basis: MemoryBasis
    summary: str
    approximate_period: tuple[date | None, date | None]
    importance_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    memory_confidence: float = Field(ge=0, le=1)
    possible_actors: tuple[str, ...]
    aliases_or_old_terms: tuple[str, ...]
    satellite_trigger: str | None
    gap_reason: str | None


class ShardMemoryIndex(BaseModel):
    """Compact shard index that intentionally excludes evidence-like detail and search text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shard_id: str
    lead_count: int = Field(ge=1)
    high_importance_count: int = Field(ge=0)
    high_precision_risk_count: int = Field(ge=0)
    ambiguous_entity_count: int = Field(ge=0)
    unique_actor_count: int = Field(ge=0)
    kind_counts: dict[str, int]
    basis_counts: dict[str, int]
    trigger_counts: dict[str, int]
    year_counts: dict[str, int]
    entries: tuple[CompactMemoryLead, ...]


def _sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _years_touched(period: tuple[date | None, date | None]) -> tuple[int, ...]:
    start, end = period
    if start is None and end is None:
        return ()
    start_year = start.year if start is not None else end.year  # type: ignore[union-attr]
    end_year = end.year if end is not None else start_year
    return tuple(range(start_year, end_year + 1))


def _gap_reason(lead: MemoryLeadCandidate) -> str | None:
    value = lead.recalled_details.get("gap_reason")
    return value if isinstance(value, str) and value.strip() else None


def build_shard_memory_index(
    leads: Iterable[MemoryLeadCandidate],
    *,
    high_importance_threshold: float = 0.9,
) -> ShardMemoryIndex:
    """Build a deterministic compact index from already validated Memory Leads.

    The index deliberately omits suggested queries, disconfirmation queries, source-type
    hints, relation explanations and arbitrary recalled details. It is a navigation aid,
    never a new research assertion or evidence object.
    """

    items = tuple(leads)
    if not items:
        raise ValueError("at least one Memory Lead is required")

    shard_id = items[0].shard_id
    if any(item.shard_id != shard_id for item in items):
        raise ValueError("a shard index cannot mix Memory Leads from different shards")

    kind_counts: Counter[str] = Counter()
    basis_counts: Counter[str] = Counter()
    trigger_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    actors: set[str] = set()
    entries: list[CompactMemoryLead] = []

    high_importance_count = 0
    high_precision_risk_count = 0
    ambiguous_entity_count = 0

    for lead in items:
        kind_counts[lead.lead_kind.value] += 1
        basis_counts[lead.memory_basis.value] += 1
        if lead.satellite_trigger:
            trigger_counts[lead.satellite_trigger] += 1
        for year in _years_touched(lead.approximate_period):
            year_counts[str(year)] += 1
        actors.update(actor for actor in lead.possible_actors if actor.strip())

        if lead.importance_score >= high_importance_threshold:
            high_importance_count += 1
        if lead.precision_risk.value in {"high", "unknown"}:
            high_precision_risk_count += 1
        if lead.entity_resolution_state.value in {"ambiguous", "unresolved"}:
            ambiguous_entity_count += 1

        entries.append(
            CompactMemoryLead(
                lead_id=lead.lead_id,
                pass_id=lead.pass_id,
                lead_kind=lead.lead_kind,
                claim_scope=lead.claim_scope,
                memory_basis=lead.memory_basis,
                summary=lead.summary,
                approximate_period=lead.approximate_period,
                importance_score=lead.importance_score,
                novelty_score=lead.novelty_score,
                memory_confidence=lead.memory_confidence,
                possible_actors=lead.possible_actors,
                aliases_or_old_terms=lead.aliases_or_old_terms,
                satellite_trigger=lead.satellite_trigger,
                gap_reason=_gap_reason(lead),
            )
        )

    entries.sort(key=lambda item: item.lead_id)

    return ShardMemoryIndex(
        shard_id=shard_id,
        lead_count=len(items),
        high_importance_count=high_importance_count,
        high_precision_risk_count=high_precision_risk_count,
        ambiguous_entity_count=ambiguous_entity_count,
        unique_actor_count=len(actors),
        kind_counts=_sorted_counts(kind_counts),
        basis_counts=_sorted_counts(basis_counts),
        trigger_counts=_sorted_counts(trigger_counts),
        year_counts=_sorted_counts(year_counts),
        entries=tuple(entries),
    )
