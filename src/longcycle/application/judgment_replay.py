from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from longcycle.domain.enums import (
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)
from longcycle.domain.models import DomainModel, require_aware_datetime


class ReplayJudgment(DomainModel):
    judgment_key: str = Field(min_length=1)
    judgment_id: UUID
    subject_entity_id: UUID
    speaker_name_text: str = Field(min_length=1)
    topic_code: str = Field(min_length=1)
    judgment_kind: JudgmentKind
    target_time_kind: JudgmentTargetTimeKind
    target_at: datetime | None = None
    target_from: datetime | None = None
    target_to: datetime | None = None
    target_precision: TemporalPrecision
    target_text: str | None = None
    value_kind: JudgmentValueKind
    value_text: str | None = None
    summary: str = Field(min_length=1)
    first_known_at: datetime
    evidence_fragment_ids: tuple[UUID, ...]

    @field_validator("target_at", "target_from", "target_to", "first_known_at")
    @classmethod
    def times_are_aware(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value, "judgment replay datetime")


class JudgmentReplaySnapshot(DomainModel):
    schema_version: Literal["longcycle-no-lookahead-judgment-replay/v1"] = (
        "longcycle-no-lookahead-judgment-replay/v1"
    )
    knowledge_cutoff: datetime
    judgments: tuple[ReplayJudgment, ...] = ()

    @field_validator("knowledge_cutoff")
    @classmethod
    def cutoff_is_aware(cls, value: datetime) -> datetime:
        checked = require_aware_datetime(value, "knowledge_cutoff")
        assert checked is not None
        return checked

    @model_validator(mode="after")
    def contains_only_knowable_judgments(self) -> JudgmentReplaySnapshot:
        if any(item.first_known_at > self.knowledge_cutoff for item in self.judgments):
            raise ValueError("judgment replay contains cognition from after the knowledge cutoff")
        expected = tuple(
            sorted(
                self.judgments,
                key=lambda item: (item.first_known_at, item.judgment_key),
            )
        )
        if self.judgments != expected:
            raise ValueError("judgment replay must be deterministically ordered")
        return self


def build_judgment_replay_snapshot(
    judgments: Iterable[ReplayJudgment],
    *,
    knowledge_cutoff: datetime,
) -> JudgmentReplaySnapshot:
    """Build an as-of cognition view; data-source filtering should happen before this call."""

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    visible = tuple(
        sorted(
            (item for item in judgments if item.first_known_at <= checked),
            key=lambda item: (item.first_known_at, item.judgment_key),
        )
    )
    return JudgmentReplaySnapshot(knowledge_cutoff=checked, judgments=visible)
