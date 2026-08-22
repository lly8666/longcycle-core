from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from itertools import pairwise
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
    def contains_only_knowable_evidence(self) -> ReplaySnapshot:
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


class ReplayRoleGroup(DomainModel):
    """Visible evidence grouped by its existing claim role without reclassifying truth."""

    claim_role: str = Field(min_length=1)
    evidence: tuple[ReplayEvidence, ...] = ()

    @model_validator(mode="after")
    def group_matches_role_and_order(self) -> ReplayRoleGroup:
        if any(item.claim_role != self.claim_role for item in self.evidence):
            raise ValueError("replay role group contains evidence with another claim role")
        expected = tuple(
            sorted(
                self.evidence,
                key=lambda item: (item.known_time_upper_bound, item.fragment_key),
            )
        )
        if self.evidence != expected:
            raise ValueError("replay role-group evidence must be deterministically ordered")
        return self


class ReplayFrame(DomainModel):
    """One historical frame organized by source claim roles, not hindsight categories."""

    schema_version: Literal["longcycle-replay-frame/v1"] = "longcycle-replay-frame/v1"
    knowledge_cutoff: datetime
    role_groups: tuple[ReplayRoleGroup, ...] = ()

    @field_validator("knowledge_cutoff")
    @classmethod
    def cutoff_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "knowledge_cutoff")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def groups_are_safe_and_deterministic(self) -> ReplayFrame:
        roles = tuple(group.claim_role for group in self.role_groups)
        if roles != tuple(sorted(roles)) or len(roles) != len(set(roles)):
            raise ValueError("replay role groups must be unique and sorted")
        if any(
            item.known_time_upper_bound > self.knowledge_cutoff
            for group in self.role_groups
            for item in group.evidence
        ):
            raise ValueError("replay frame contains evidence from after the knowledge cutoff")
        return self


class ReplayTransition(DomainModel):
    """Evidence that became knowable between two already-valid historical cutoffs."""

    schema_version: Literal["longcycle-replay-transition/v1"] = "longcycle-replay-transition/v1"
    previous_cutoff: datetime
    knowledge_cutoff: datetime
    new_evidence_groups: tuple[ReplayRoleGroup, ...] = ()

    @field_validator("previous_cutoff", "knowledge_cutoff")
    @classmethod
    def cutoffs_are_aware(cls, value: datetime, info: Any) -> datetime:
        checked = require_aware_datetime(value, info.field_name)
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def transition_respects_time_window(self) -> ReplayTransition:
        if self.knowledge_cutoff <= self.previous_cutoff:
            raise ValueError("transition knowledge cutoff must be after previous cutoff")
        roles = tuple(group.claim_role for group in self.new_evidence_groups)
        if roles != tuple(sorted(roles)) or len(roles) != len(set(roles)):
            raise ValueError("transition role groups must be unique and sorted")
        if any(
            item.known_time_upper_bound <= self.previous_cutoff
            or item.known_time_upper_bound > self.knowledge_cutoff
            for group in self.new_evidence_groups
            for item in group.evidence
        ):
            raise ValueError("transition contains evidence outside its knowledge window")
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
    for previous, current in pairwise(cutoffs):
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


def _group_by_claim_role(evidence: Iterable[ReplayEvidence]) -> tuple[ReplayRoleGroup, ...]:
    grouped: dict[str, list[ReplayEvidence]] = {}
    for item in evidence:
        grouped.setdefault(item.claim_role, []).append(item)
    return tuple(
        ReplayRoleGroup(
            claim_role=role,
            evidence=tuple(
                sorted(
                    grouped[role],
                    key=lambda item: (item.known_time_upper_bound, item.fragment_key),
                )
            ),
        )
        for role in sorted(grouped)
    )


def build_replay_frame(snapshot: ReplaySnapshot) -> ReplayFrame:
    """Organize one safe snapshot without changing the semantic authority of evidence."""

    return ReplayFrame(
        knowledge_cutoff=snapshot.knowledge_cutoff,
        role_groups=_group_by_claim_role(snapshot.evidence),
    )


def build_replay_transition(
    previous: ReplaySnapshot,
    current: ReplaySnapshot,
) -> ReplayTransition:
    """Show what became knowable without exposing anything after the current cutoff."""

    if current.knowledge_cutoff <= previous.knowledge_cutoff:
        raise ValueError("current replay snapshot must be after previous snapshot")

    current_by_id = {item.evidence_fragment_id: item for item in current.evidence}
    previous_by_id = {item.evidence_fragment_id: item for item in previous.evidence}
    for evidence_id, previous_item in previous_by_id.items():
        current_item = current_by_id.get(evidence_id)
        if current_item is None:
            raise ValueError("replay snapshots are not monotone")
        if current_item != previous_item:
            raise ValueError("replay evidence changed between snapshots")

    newly_visible = tuple(
        item
        for item in current.evidence
        if item.evidence_fragment_id not in previous_by_id
    )
    return ReplayTransition(
        previous_cutoff=previous.knowledge_cutoff,
        knowledge_cutoff=current.knowledge_cutoff,
        new_evidence_groups=_group_by_claim_role(newly_visible),
    )
