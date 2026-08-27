from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from longcycle.application.session_handoff import SessionHandoffCheckpoint


MAX_HANDOFF_BYTES = 64 * 1024
MAX_RESUME_CONTEXT_BYTES = 256 * 1024


class HandoffDrillCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    passed: bool
    detail: str = Field(min_length=1)


class RecoveredSessionState(BaseModel):
    """State reconstructed from bounded core + dynamic repository context only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    repository: str
    active_branch: str
    active_pr: int | None
    context_id: str
    medium_term_goal: str
    short_term_goal: str
    next_big_step: str
    cursor_parent_workstream_id: str
    cursor_last_completed_action: str
    cursor_current_task: str
    cursor_why_now: str
    cursor_done_when: str
    cursor_next_atomic_action: str
    campaign_id: str | None
    industry: str | None
    phase: str | None
    search_visibility: str | None
    total_raw_leads: int | None = Field(default=None, ge=0)
    shard_count: int | None = Field(default=None, ge=0)
    sealed_shards: tuple[str, ...]
    ordered_next_actions: tuple[str, ...]


class HandoffIsolationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    recovered: RecoveredSessionState
    fidelity_score: float = Field(ge=0, le=1)
    checks: tuple[HandoffDrillCheck, ...]

    @property
    def failed_checks(self) -> tuple[HandoffDrillCheck, ...]:
        return tuple(item for item in self.checks if not item.passed)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _count_jsonl_records(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _count_raw_memory_leads(campaign_root: Path) -> dict[str, int]:
    blind_root = campaign_root / "blind"
    if not blind_root.is_dir():
        raise FileNotFoundError(blind_root)

    counts: dict[str, int] = {}
    for jsonl_path in sorted(blind_root.glob("*.jsonl")):
        count = _count_jsonl_records(jsonl_path)
        if count:
            counts[jsonl_path.stem] = count

    for shard_dir in sorted(path for path in blind_root.iterdir() if path.is_dir()):
        count = sum(_count_jsonl_records(path) for path in sorted(shard_dir.glob("*.jsonl")))
        if count:
            counts[shard_dir.name] = count
    return counts


def _coverage_total(coverage: dict[str, Any]) -> int | None:
    value = coverage.get("total_raw_leads_so_far")
    if value is None:
        value = coverage.get("total_raw_leads")
    return value if isinstance(value, int) else None


def _coverage_shard_count(coverage: dict[str, Any]) -> int | None:
    rows = coverage.get("shards")
    if isinstance(rows, list):
        return len(rows)
    value = coverage.get("canonical_lead_shards")
    return value if isinstance(value, int) else None


def _legacy_coverage_counts(coverage: dict[str, Any]) -> dict[str, int] | None:
    rows = coverage.get("shards")
    if rows is None:
        return None
    if not isinstance(rows, list):
        raise ValueError("coverage-index.json shards must be a list when present")

    counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("coverage shard row must be an object")
        shard_id = row.get("shard_id")
        lead_count = row.get("lead_count")
        if not isinstance(shard_id, str) or not isinstance(lead_count, int):
            raise ValueError("coverage shard row has invalid shard_id/lead_count")
        counts[shard_id] = lead_count
    return counts


def audit_repository_handoff(
    root: Path,
    *,
    checkpoint_override: SessionHandoffCheckpoint | None = None,
) -> HandoffIsolationReport:
    """Context-isolated recovery using only bounded core and referenced active context."""

    handoff_path = root / ".longcycle" / "handoff" / "current.json"
    checkpoint = checkpoint_override or SessionHandoffCheckpoint.model_validate_json(
        handoff_path.read_text(encoding="utf-8")
    )

    strategy = (root / checkpoint.core_refs.strategy_path).read_text(encoding="utf-8")
    methodology = (root / checkpoint.core_refs.methodology_path).read_text(encoding="utf-8")
    mission_contract = _read_json(root / checkpoint.core_refs.mission_fidelity_path)
    continue_here = (root / "CONTINUE_HERE.md").read_text(encoding="utf-8")
    fresh_bootstrap = (root / "FRESH_AGENT_BOOTSTRAP.md").read_text(encoding="utf-8")

    resume_paths = tuple(root / relative for relative in checkpoint.resume_read_set)
    missing_resume_paths = tuple(
        str(path.relative_to(root)) for path in resume_paths if not path.is_file()
    )
    resume_context_bytes = sum(path.stat().st_size for path in resume_paths if path.is_file())
    missing_deep_paths = tuple(
        relative
        for relative in checkpoint.active_context.deep_context_paths
        if not (root / relative).is_file()
    )
    handoff_bytes = handoff_path.stat().st_size

    raw_total: int | None = None
    raw_counts: dict[str, int] = {}
    coverage: dict[str, Any] = {}
    coverage_counts: dict[str, int] | None = None
    sealed_from_checkpoint: tuple[str, ...] = ()
    missing_sealed_shards: tuple[str, ...] = ()
    shard_mismatches: dict[str, dict[str, int | None]] = {}

    campaign = checkpoint.memory_campaign
    if campaign is not None:
        campaign_root_raw = checkpoint.active_context.campaign_root
        coverage_path_raw = checkpoint.active_context.coverage_path
        if campaign_root_raw is None or coverage_path_raw is None:
            raise ValueError("memory campaign context paths are missing")

        campaign_root = root / campaign_root_raw
        coverage = _read_json(root / coverage_path_raw)
        raw_counts = _count_raw_memory_leads(campaign_root)
        raw_total = sum(raw_counts.values())
        coverage_counts = _legacy_coverage_counts(coverage)
        if coverage_counts is not None:
            shard_mismatches = {
                shard_id: {
                    "coverage": coverage_counts.get(shard_id),
                    "raw": raw_counts.get(shard_id),
                }
                for shard_id in sorted(set(coverage_counts) | set(raw_counts))
                if coverage_counts.get(shard_id) != raw_counts.get(shard_id)
            }

        sealed_from_checkpoint = tuple(campaign.sealed_shards)
        missing_sealed_shards = tuple(
            relative for relative in sealed_from_checkpoint if not (root / relative).is_file()
        )

    core_text = f"{strategy}\n{methodology}".lower()
    core_exclusion_hits = tuple(
        term for term in checkpoint.active_context.core_exclusion_terms if term.lower() in core_text
    )

    contract_text = json.dumps(mission_contract, ensure_ascii=False).lower()
    contract_exclusion_hits = tuple(
        term
        for term in checkpoint.active_context.core_exclusion_terms
        if term.lower() in contract_text
    )
    facets = mission_contract.get("required_facets")
    misreadings = mission_contract.get("common_misreadings")
    bootstrap_lower = fresh_bootstrap.lower()
    bootstrap_has_no_reconstruction_rule = (
        "do not ask" in bootstrap_lower or "不要让我重复背景" in fresh_bootstrap
    )

    checks_list = [
        HandoffDrillCheck(
            name="bounded_bootstrap_read_set",
            passed=len(checkpoint.resume_read_set) <= 8,
            detail=f"resume_read_set={len(checkpoint.resume_read_set)}",
        ),
        HandoffDrillCheck(
            name="resume_read_set_paths_exist",
            passed=not missing_resume_paths,
            detail=f"missing={missing_resume_paths}",
        ),
        HandoffDrillCheck(
            name="active_deep_context_paths_exist",
            passed=not missing_deep_paths,
            detail=f"missing={missing_deep_paths}",
        ),
        HandoffDrillCheck(
            name="handoff_file_remains_bounded",
            passed=handoff_bytes <= MAX_HANDOFF_BYTES,
            detail=f"bytes={handoff_bytes}, limit={MAX_HANDOFF_BYTES}",
        ),
        HandoffDrillCheck(
            name="resume_context_remains_bounded",
            passed=resume_context_bytes <= MAX_RESUME_CONTEXT_BYTES,
            detail=f"bytes={resume_context_bytes}, limit={MAX_RESUME_CONTEXT_BYTES}",
        ),
        HandoffDrillCheck(
            name="fresh_bootstrap_preserves_stable_rendezvous",
            passed=(
                "#2" in bootstrap_lower
                and "longcycle live handoff / session bootstrap" in bootstrap_lower
                and "continue_here.md" in bootstrap_lower
                and "typed continuation cursor" in bootstrap_lower
                and bootstrap_has_no_reconstruction_rule
            ),
            detail=(
                "fresh bootstrap must semantically resolve stable issue, active branch bootstrap, "
                "typed cursor and no-user-reconstruction rule independent of Markdown formatting"
            ),
        ),
        HandoffDrillCheck(
            name="bootstrap_reads_strategy_method_then_calibrates",
            passed=(
                checkpoint.core_refs.strategy_path in continue_here
                and checkpoint.core_refs.methodology_path in continue_here
                and checkpoint.core_refs.mission_fidelity_path in continue_here
                and "先用自己的话" in continue_here
            ),
            detail="CONTINUE_HERE must require first-pass synthesis before semantic calibration",
        ),
        HandoffDrillCheck(
            name="strategy_core_preserves_mission",
            passed=(
                "历史本身就是分析" in strategy
                and "Reality" in strategy
                and "Expectation" in strategy
                and "Outcome" in strategy
                and "point-in-time" in strategy
            ),
            detail="strategy core must preserve terminal replay mission",
        ),
        HandoffDrillCheck(
            name="methodology_core_preserves_cross_industry_methods",
            passed=(
                "Memory-first, Evidence-final" in methodology
                and "Source-first, Preserve-now" in methodology
                and "not_found != false" in methodology
                and "Point-in-time" in methodology
                and "主动理解" in methodology
            ),
            detail="method core must preserve adopted cross-industry research and anti-tunnel methods",
        ),
        HandoffDrillCheck(
            name="mission_contract_is_semantic_not_answer_key",
            passed=(
                isinstance(facets, list)
                and len(facets) >= 10
                and isinstance(misreadings, list)
                and len(misreadings) >= 5
                and "not an answer key" in str(mission_contract.get("purpose", ""))
            ),
            detail="mission contract must test semantic facets without becoming canonical prose",
        ),
        HandoffDrillCheck(
            name="long_term_cores_exclude_active_context_terms",
            passed=not core_exclusion_hits,
            detail=f"hits={core_exclusion_hits}",
        ),
        HandoffDrillCheck(
            name="mission_contract_excludes_active_context_terms",
            passed=not contract_exclusion_hits,
            detail=f"hits={contract_exclusion_hits}",
        ),
        HandoffDrillCheck(
            name="strategic_horizon_present",
            passed=all(
                (
                    checkpoint.strategic_horizon.medium_term_goal,
                    checkpoint.strategic_horizon.short_term_goal,
                    checkpoint.strategic_horizon.next_big_step,
                    checkpoint.strategic_horizon.local_optimization_stop_rule,
                )
            ),
            detail="medium/short/next/stop strategic horizon must be explicit",
        ),
        HandoffDrillCheck(
            name="continuation_cursor_complete",
            passed=all(
                (
                    checkpoint.continuation_cursor.parent_workstream_id,
                    checkpoint.continuation_cursor.last_completed_action,
                    checkpoint.continuation_cursor.current_task,
                    checkpoint.continuation_cursor.why_now,
                    checkpoint.continuation_cursor.done_when,
                    checkpoint.continuation_cursor.next_atomic_action,
                )
            ),
            detail="cursor must recover just-finished/current/why/done/next atomic state",
        ),
        HandoffDrillCheck(
            name="resume_actions_present",
            passed=bool(checkpoint.ordered_next_actions),
            detail=f"ordered_next_actions={len(checkpoint.ordered_next_actions)}",
        ),
    ]

    if campaign is not None:
        coverage_total = _coverage_total(coverage)
        coverage_shard_count = _coverage_shard_count(coverage)
        legacy_visibility = coverage.get("search_visibility")
        blind_visibility = coverage.get("blind_source_visibility")
        checks_list.extend(
            [
                HandoffDrillCheck(
                    name="checkpoint_total_matches_raw",
                    passed=campaign.total_raw_leads == raw_total,
                    detail=f"checkpoint={campaign.total_raw_leads}, raw={raw_total}",
                ),
                HandoffDrillCheck(
                    name="coverage_total_matches_raw",
                    passed=coverage_total == raw_total,
                    detail=f"coverage={coverage_total}, raw={raw_total}",
                ),
                HandoffDrillCheck(
                    name="coverage_shard_count_matches_raw",
                    passed=coverage_shard_count == len(raw_counts),
                    detail=f"coverage={coverage_shard_count}, raw={len(raw_counts)}",
                ),
                HandoffDrillCheck(
                    name="legacy_coverage_shard_counts_match_raw",
                    passed=coverage_counts is None or not shard_mismatches,
                    detail="mismatches="
                    + json.dumps(shard_mismatches, ensure_ascii=False, sort_keys=True),
                ),
                HandoffDrillCheck(
                    name="checkpoint_shard_count_matches_raw",
                    passed=campaign.shard_count == len(raw_counts),
                    detail=f"checkpoint={campaign.shard_count}, raw={len(raw_counts)}",
                ),
                HandoffDrillCheck(
                    name="coverage_visibility_boundary_is_sound",
                    passed=(
                        campaign.search_visibility == legacy_visibility
                        if isinstance(legacy_visibility, str)
                        else blind_visibility == "none"
                    ),
                    detail=(
                        f"campaign={campaign.search_visibility}, legacy={legacy_visibility}, "
                        f"blind={blind_visibility}"
                    ),
                ),
                HandoffDrillCheck(
                    name="checkpoint_sealed_shards_exist",
                    passed=(
                        len(sealed_from_checkpoint) == campaign.shard_count
                        and not missing_sealed_shards
                    ),
                    detail=(
                        f"checkpoint={len(sealed_from_checkpoint)}, "
                        f"expected={campaign.shard_count}, missing={missing_sealed_shards}"
                    ),
                ),
            ]
        )

    checks = tuple(checks_list)
    score = sum(item.passed for item in checks) / len(checks)

    cursor = checkpoint.continuation_cursor
    recovered = RecoveredSessionState(
        repository=checkpoint.repository,
        active_branch=checkpoint.active_branch,
        active_pr=checkpoint.active_pr,
        context_id=checkpoint.active_context.context_id,
        medium_term_goal=checkpoint.strategic_horizon.medium_term_goal,
        short_term_goal=checkpoint.strategic_horizon.short_term_goal,
        next_big_step=checkpoint.strategic_horizon.next_big_step,
        cursor_parent_workstream_id=cursor.parent_workstream_id,
        cursor_last_completed_action=cursor.last_completed_action,
        cursor_current_task=cursor.current_task,
        cursor_why_now=cursor.why_now,
        cursor_done_when=cursor.done_when,
        cursor_next_atomic_action=cursor.next_atomic_action,
        campaign_id=campaign.campaign_id if campaign else None,
        industry=campaign.industry if campaign else None,
        phase=campaign.phase if campaign else None,
        search_visibility=campaign.search_visibility if campaign else None,
        total_raw_leads=raw_total,
        shard_count=len(raw_counts) if campaign else None,
        sealed_shards=sealed_from_checkpoint,
        ordered_next_actions=checkpoint.ordered_next_actions,
    )
    return HandoffIsolationReport(recovered=recovered, fidelity_score=score, checks=checks)
