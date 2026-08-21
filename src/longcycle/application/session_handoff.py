from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HandoffCIState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: Literal["snapshot_not_authoritative"]
    last_observed_run: int | None = Field(default=None, ge=1)
    observed_head_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    conclusion: str
    mypy_summary: str
    pytest_summary: str
    ruff_summary: str
    refresh_instruction: str


class HandoffCoreRefs(BaseModel):
    """Small, slow-changing bootstrap cores. Dynamic state must not be copied here."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_path: Literal["STRATEGIC_COMPASS.md"]
    methodology_path: Literal["METHODOLOGY_CORE.md"]


class HandoffStrategicHorizon(BaseModel):
    """Dynamic horizon immediately below the long-term mission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    medium_term_goal: str = Field(min_length=1)
    short_term_goal: str = Field(min_length=1)
    next_big_step: str = Field(min_length=1)
    local_optimization_stop_rule: str = Field(min_length=1)
    parallel_permanent_tracks: tuple[str, ...] = ()


class HandoffActiveContext(BaseModel):
    """The current industry / benchmark / task context, intentionally outside long-term cores."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    context_id: str = Field(min_length=1)
    context_kind: str = Field(min_length=1)
    label: str = Field(min_length=1)
    root_path: str = Field(min_length=1)
    campaign_root: str | None = None
    coverage_path: str | None = None
    deep_context_paths: tuple[str, ...] = ()
    core_exclusion_terms: tuple[str, ...] = ()


class HandoffMemoryCampaign(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    campaign_id: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    phase: str = Field(min_length=1)
    search_visibility: Literal["none", "self_verification", "delegated_verification"]
    total_raw_leads: int = Field(ge=0)
    sealed_shards: tuple[str, ...]
    shard_count: int = Field(ge=1)
    seal_rule: str
    next_research_actions: tuple[str, ...]

    @model_validator(mode="after")
    def blind_phase_has_no_search_leak(self) -> HandoffMemoryCampaign:
        if self.phase.startswith("blind") and self.search_visibility != "none":
            raise ValueError("blind memory phase cannot expose fresh search")
        return self


class HandoffWorkstream(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workstream_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    next_actions: tuple[str, ...]
    blockers: tuple[str, ...] = ()

    @model_validator(mode="after")
    def has_next_action(self) -> HandoffWorkstream:
        if not self.next_actions:
            raise ValueError("active handoff workstreams require at least one next action")
        return self


class SessionHandoffCheckpoint(BaseModel):
    """Bounded repository-backed continuation state for a fresh session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-session-handoff/v2"]
    continuity_sequence: int = Field(ge=1)
    provenance_ordering: Literal["git_commit_graph"]
    repository: Literal["lly8666/longcycle-core"]
    active_branch: str = Field(min_length=1)
    active_pr: int | None = Field(default=None, ge=1)
    checkpoint_based_on_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    live_refresh_required: Literal[True]
    do_not_ask_user_to_repeat: Literal[True]
    bootstrap_instruction: str = Field(min_length=1)
    core_refs: HandoffCoreRefs
    strategic_horizon: HandoffStrategicHorizon
    active_context: HandoffActiveContext
    pending_user_directives: tuple[str, ...] = ()
    memory_campaign: HandoffMemoryCampaign | None = None
    ci: HandoffCIState
    workstreams: tuple[HandoffWorkstream, ...]
    resume_read_set: tuple[str, ...]
    deep_reference_paths: tuple[str, ...] = ()
    latest_devlogs: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...]
    ordered_next_actions: tuple[str, ...]

    @model_validator(mode="after")
    def continuation_contract_is_complete(self) -> SessionHandoffCheckpoint:
        if not self.resume_read_set:
            raise ValueError("handoff must provide a minimal resume read set")
        if len(self.resume_read_set) > 8:
            raise ValueError("default resume_read_set must remain bounded at eight files or fewer")
        if not self.ordered_next_actions:
            raise ValueError("handoff must provide ordered next actions")

        workstream_ids = [item.workstream_id for item in self.workstreams]
        if len(workstream_ids) != len(set(workstream_ids)):
            raise ValueError("handoff workstream ids must be unique")

        required_paths = {
            self.core_refs.strategy_path,
            self.core_refs.methodology_path,
            "CONTINUE_HERE.md",
            ".longcycle/handoff/current.json",
        }
        if not required_paths.issubset(set(self.resume_read_set)):
            raise ValueError("resume_read_set is missing bounded bootstrap core files")

        if self.memory_campaign is not None and (
            self.active_context.campaign_root is None
            or self.active_context.coverage_path is None
        ):
            raise ValueError("memory campaign requires active-context campaign_root and coverage_path")

        return self


class HandoffHeadDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["checkpoint_base_matches_live_head", "delta_reconciliation_required"]
    checkpoint_based_on_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    live_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    requires_delta_reconciliation: bool
    reason: str


def evaluate_handoff_head(
    checkpoint: SessionHandoffCheckpoint,
    *,
    live_head_sha: str,
) -> HandoffHeadDecision:
    """Tell a fresh session whether it must inspect commits after the checkpoint base."""

    if re.fullmatch(r"[0-9a-f]{40}", live_head_sha) is None:
        raise ValueError("live_head_sha must be a lowercase 40-character Git SHA")

    if checkpoint.checkpoint_based_on_head_sha == live_head_sha:
        return HandoffHeadDecision(
            status="checkpoint_base_matches_live_head",
            checkpoint_based_on_head_sha=checkpoint.checkpoint_based_on_head_sha,
            live_head_sha=live_head_sha,
            requires_delta_reconciliation=False,
            reason="live HEAD is exactly the repository state used to build the checkpoint",
        )

    return HandoffHeadDecision(
        status="delta_reconciliation_required",
        checkpoint_based_on_head_sha=checkpoint.checkpoint_based_on_head_sha,
        live_head_sha=live_head_sha,
        requires_delta_reconciliation=True,
        reason=(
            "live HEAD differs from the checkpoint base; inspect intervening commits and refresh CI "
            "before trusting snapshot state"
        ),
    )
