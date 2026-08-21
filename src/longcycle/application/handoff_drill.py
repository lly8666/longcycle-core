from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from longcycle.application.session_handoff import SessionHandoffCheckpoint


_CAMPAIGN_RELATIVE_ROOT = Path(
    "research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol"
)


class HandoffDrillCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    passed: bool
    detail: str = Field(min_length=1)


class RecoveredSessionState(BaseModel):
    """State reconstructed only from repository handoff artifacts and raw campaign files."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    repository: str
    active_branch: str
    active_pr: int | None
    campaign_id: str
    industry: str
    phase: str
    search_visibility: str
    total_raw_leads: int = Field(ge=0)
    shard_count: int = Field(ge=0)
    sealed_shards: tuple[str, ...]
    north_star: tuple[str, ...]
    user_directives: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
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


def _count_raw_memory_leads(root: Path) -> dict[str, int]:
    blind_root = root / _CAMPAIGN_RELATIVE_ROOT / "blind"
    if not blind_root.is_dir():
        raise FileNotFoundError(blind_root)

    counts: dict[str, int] = {}
    for shard_dir in sorted(path for path in blind_root.iterdir() if path.is_dir()):
        count = 0
        for jsonl_path in sorted(shard_dir.glob("*.jsonl")):
            count += sum(
                1
                for line in jsonl_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        if count:
            counts[shard_dir.name] = count
    return counts


def audit_repository_handoff(
    root: Path,
    *,
    checkpoint_override: SessionHandoffCheckpoint | None = None,
) -> HandoffIsolationReport:
    """Run a context-isolated handoff drill using repository files only.

    This deliberately does not depend on chat history. Live GitHub HEAD and CI still have
    to be refreshed by the caller because a local checkout cannot prove that it is the
    newest remote state.
    """

    handoff_path = root / ".longcycle" / "handoff" / "current.json"
    checkpoint = checkpoint_override or SessionHandoffCheckpoint.model_validate_json(
        handoff_path.read_text(encoding="utf-8")
    )
    coverage = _read_json(root / _CAMPAIGN_RELATIVE_ROOT / "analysis" / "coverage-index.json")
    raw_counts = _count_raw_memory_leads(root)
    raw_total = sum(raw_counts.values())

    coverage_shards_raw = coverage.get("shards")
    if not isinstance(coverage_shards_raw, list):
        raise ValueError("coverage-index.json shards must be a list")
    coverage_counts: dict[str, int] = {}
    for row in coverage_shards_raw:
        if not isinstance(row, dict):
            raise ValueError("coverage shard row must be an object")
        shard_id = row.get("shard_id")
        lead_count = row.get("lead_count")
        if not isinstance(shard_id, str) or not isinstance(lead_count, int):
            raise ValueError("coverage shard row has invalid shard_id/lead_count")
        coverage_counts[shard_id] = lead_count

    continue_here = (root / "CONTINUE_HERE.md").read_text(encoding="utf-8")
    constitution = (root / "docs" / "development" / "project-constitution.md").read_text(
        encoding="utf-8"
    )

    sealed_from_coverage_raw = coverage.get("sealed_shards")
    if not isinstance(sealed_from_coverage_raw, list) or not all(
        isinstance(item, str) for item in sealed_from_coverage_raw
    ):
        raise ValueError("coverage sealed_shards must be a string list")
    sealed_from_coverage = tuple(sealed_from_coverage_raw)

    checks = (
        HandoffDrillCheck(
            name="checkpoint_total_matches_raw",
            passed=checkpoint.memory_campaign.total_raw_leads == raw_total,
            detail=(
                f"checkpoint={checkpoint.memory_campaign.total_raw_leads}, raw={raw_total}"
            ),
        ),
        HandoffDrillCheck(
            name="coverage_total_matches_raw",
            passed=coverage.get("total_raw_leads_so_far") == raw_total,
            detail=f"coverage={coverage.get('total_raw_leads_so_far')}, raw={raw_total}",
        ),
        HandoffDrillCheck(
            name="coverage_shard_counts_match_raw",
            passed=coverage_counts == raw_counts,
            detail=f"coverage_shards={len(coverage_counts)}, raw_shards={len(raw_counts)}",
        ),
        HandoffDrillCheck(
            name="checkpoint_shard_count_matches_raw",
            passed=checkpoint.memory_campaign.shard_count == len(raw_counts),
            detail=f"checkpoint={checkpoint.memory_campaign.shard_count}, raw={len(raw_counts)}",
        ),
        HandoffDrillCheck(
            name="search_visibility_agrees",
            passed=(
                checkpoint.memory_campaign.search_visibility
                == coverage.get("search_visibility")
                == "none"
            ),
            detail=(
                "checkpoint="
                f"{checkpoint.memory_campaign.search_visibility}, "
                f"coverage={coverage.get('search_visibility')}"
            ),
        ),
        HandoffDrillCheck(
            name="sealed_shards_agree",
            passed=checkpoint.memory_campaign.sealed_shards == sealed_from_coverage,
            detail=(
                f"checkpoint={checkpoint.memory_campaign.sealed_shards}, "
                f"coverage={sealed_from_coverage}"
            ),
        ),
        HandoffDrillCheck(
            name="bootstrap_points_to_checkpoint",
            passed=(
                ".longcycle/handoff/current.json" in continue_here
                and "live" in continue_here.lower()
            ),
            detail="CONTINUE_HERE.md must point to current.json and require live refresh",
        ),
        HandoffDrillCheck(
            name="constitution_preserves_north_star",
            passed=(
                "历史本身就是分析" in constitution
                and "缺的是人站在当时的判断和预期" in constitution
            ),
            detail="project constitution must preserve the core historical-memory intent",
        ),
        HandoffDrillCheck(
            name="resume_actions_present",
            passed=bool(checkpoint.ordered_next_actions),
            detail=f"ordered_next_actions={len(checkpoint.ordered_next_actions)}",
        ),
        HandoffDrillCheck(
            name="user_directives_present",
            passed=bool(checkpoint.user_directives),
            detail=f"user_directives={len(checkpoint.user_directives)}",
        ),
    )
    score = sum(item.passed for item in checks) / len(checks)

    recovered = RecoveredSessionState(
        repository=checkpoint.repository,
        active_branch=checkpoint.active_branch,
        active_pr=checkpoint.active_pr,
        campaign_id=checkpoint.memory_campaign.campaign_id,
        industry=checkpoint.memory_campaign.industry,
        phase=checkpoint.memory_campaign.phase,
        search_visibility=checkpoint.memory_campaign.search_visibility,
        total_raw_leads=raw_total,
        shard_count=len(raw_counts),
        sealed_shards=sealed_from_coverage,
        north_star=checkpoint.north_star,
        user_directives=checkpoint.user_directives,
        forbidden_shortcuts=checkpoint.forbidden_shortcuts,
        ordered_next_actions=checkpoint.ordered_next_actions,
    )
    return HandoffIsolationReport(
        recovered=recovered,
        fidelity_score=score,
        checks=checks,
    )
