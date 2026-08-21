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
    """Small, slow-changing bootstrap cores and semantic calibration contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_path: Literal["STRATEGIC_COMPASS.md"]
    methodology_path: Literal["METHODOLOGY_CORE.md"]
    mission_fidelity_path: Literal[".longcycle/continuity/mission-fidelity.json"]


class HandoffStrategicHorizon(BaseModel):
    """Dynamic horizon immediately below the long-term mission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    medium_term_goal: str = Field(min_length=1)
    short_term_goal: str = Field(min_length=1)
    next_big_step: str = Field(min_length=1)
    local_optimization_stop_rule: str = Field(min_length=1)
    parallel_permanent_tracks: tuple[str, ...] = ()


AgentCapabilityClass = Literal["high_capability_reasoning", "bounded_execution"]


class HandoffContinuationCursor(BaseModel):
    """Small, live execution pointer beneath the strategic horizon."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parent_workstream_id: str = Field(min_length=1)
    last_completed_action: str = Field(min_length=1)
    current_task: str = Field(min_length=1)
    why_now: str = Field(min_length=1)
    done_when: str = Field(min_length=1)
    required_capability: AgentCapabilityClass
    insufficient_capability_action: Literal["stop_and_escalate"]
    next_atomic_action: str = Field(min_length=1)


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


WorkstreamRole = Literal["main_path", "supporting_quality_gate", "parallel_track"]
ParentGoalRef = Literal[
    "strategic_horizon.short_term_goal",
    "strategic_horizon.medium_term_goal",
    "strategic_horizon.parallel_permanent_tracks",
]


class HandoffWorkstream(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workstream_id: str = Field(min_length=1)
    role: WorkstreamRole
    parent_goal_ref: ParentGoalRef
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    next_actions: tuple[str, ...]
    blockers: tuple[str, ...] = ()

    @model_validator(mode="after")
    def has_next_action(self) -> HandoffWorkstream:
        if not self.next_actions:
            raise ValueError("active handoff workstreams require at least one next action")
        if self.role == "main_path" and self.parent_goal_ref == "strategic_horizon.parallel_permanent_tracks":
            raise ValueError("main-path workstream cannot attach only to a parallel permanent track")
        if self.role == "parallel_track" and self.parent_goal_ref != "strategic_horizon.parallel_permanent_tracks":
            raise ValueError("parallel-track workstream must attach to parallel permanent tracks")
        return self


class SessionHandoffCheckpoint(BaseModel):
    """Bounded repository-backed continuation state for a fresh session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-session-handoff/v4"]
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
    continuation_cursor: HandoffContinuationCursor
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
        if not any(item.role == "main_path" for item in self.workstreams):
            raise ValueError("handoff must identify at least one main-path workstream")
        if self.continuation_cursor.parent_workstream_id not in set(workstream_ids):
            raise ValueError("continuation cursor must point to a declared workstream")

        required_paths = {
            self.core_refs.strategy_path,
            self.core_refs.methodology_path,
            self.core_refs.mission_fidelity_path,
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
