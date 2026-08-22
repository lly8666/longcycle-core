from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.models import DomainModel, require_aware_datetime


class ReplayEvidence(DomainModel):
    """One evidence fragment that may become visible at a historical cutoff."""

    fragment_key: str = Field(min_length=1)
    evidence_fragment_id: UUID
    document_version_id: UUID
    artifact_id: UUID | None = None
    locator: str = Field(min_length=1)
    excerpt: str | None = None
    claim_role: str = Field(min_length=1)
    known_time_upper_bound: datetime
    known_time_precision: str = Field(min_length=1)
    valid_effective_time: dict[str, Any] | None = None
    expectation_horizon: dict[str, Any] | list[dict[str, Any]] | None = None

    @field_validator("known_time_upper_bound")
    @classmethod
    def known_time_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "known_time_upper_bound")
        assert checked is not None
        return checked


class ReplaySnapshot(DomainModel):
    """Public as-of view. It deliberately contains no metadata about hidden future rows."""

    schema_version: Literal["longcycle-no-lookahead-replay/v1"] = "longcycle-no-lookahead-replay/v1"
    knowledge_cutoff: datetime
    evidence: tuple[ReplayEvidence, ...] = ()

    @field_validator("knowledge_cutoff")
    @classmethod
    def cutoff_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "knowledge_cutoff")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def contains_only_knowable_evidence(self) -> "ReplaySnapshot":
        if any(item.known_time_upper_bound > self.knowledge_cutoff for item in self.evidence):
            raise ValueError("replay snapshot contains evidence from after the knowledge cutoff")
        expected = tuple(
            sorted(
                self.evidence,
                key=lambda item: (item.known_time_upper_bound, item.fragment_key),
            )
        )
        if self.evidence != expected:
            raise ValueError("replay evidence must be deterministically ordered")
        return self


def build_replay_snapshot(
    evidence: Iterable[ReplayEvidence],
    *,
    knowledge_cutoff: datetime,
) -> ReplaySnapshot:
    """Build a deterministic point-in-time view without leaking future-row identity."""

    checked_cutoff = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked_cutoff is not None
    visible = tuple(
        sorted(
            (
                item
                for item in evidence
                if item.known_time_upper_bound <= checked_cutoff
            ),
            key=lambda item: (item.known_time_upper_bound, item.fragment_key),
        )
    )
    return ReplaySnapshot(
        knowledge_cutoff=checked_cutoff,
        evidence=visible,
    )


def build_replay_sequence(
    evidence: Iterable[ReplayEvidence],
    *,
    knowledge_cutoffs: Iterable[datetime],
) -> tuple[ReplaySnapshot, ...]:
    """Build monotone snapshots from one immutable evidence population."""

    population = tuple(evidence)
    cutoffs = tuple(knowledge_cutoffs)
    for previous, current in zip(cutoffs, cutoffs[1:], strict=False):
        previous_checked = require_aware_datetime(previous, "knowledge_cutoff")
        current_checked = require_aware_datetime(current, "knowledge_cutoff")
        assert previous_checked is not None
        assert current_checked is not None
        if current_checked <= previous_checked:
            raise ValueError("knowledge cutoffs must be strictly increasing")

    return tuple(
        build_replay_snapshot(population, knowledge_cutoff=cutoff)
        for cutoff in cutoffs
    )
