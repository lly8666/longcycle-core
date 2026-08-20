from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True, slots=True)
class RecallPassSpec:
    pass_id: str
    family: str
    questions: tuple[str, ...]
    period_start: date | None = None
    period_end: date | None = None
    requires_atlas_only: bool = False


@dataclass(frozen=True, slots=True)
class RecallPassOutcome:
    pass_id: str
    family: str
    novel_lead_count: int
    duplicate_lead_count: int
    high_importance_novel_count: int

    def __post_init__(self) -> None:
        for field_name in (
            "novel_lead_count",
            "duplicate_lead_count",
            "high_importance_novel_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class SaturationPolicy:
    consecutive_low_novelty_passes: int = 3
    max_high_importance_novel_per_low_pass: int = 1

    def __post_init__(self) -> None:
        if self.consecutive_low_novelty_passes < 1:
            raise ValueError("consecutive_low_novelty_passes must be positive")
        if self.max_high_importance_novel_per_low_pass < 0:
            raise ValueError("max_high_importance_novel_per_low_pass must be non-negative")


@dataclass(frozen=True, slots=True)
class SaturationResult:
    saturated: bool
    reason_codes: tuple[str, ...]


def build_recall_pass_prompt(
    *,
    industry: str,
    campaign_start: date,
    campaign_end: date,
    spec: RecallPassSpec,
    atlas_summary: str | None = None,
) -> str:
    """Build one orthogonal memory-recall pass without exposing fresh search results."""

    if not industry.strip():
        raise ValueError("industry must not be blank")
    if campaign_end < campaign_start:
        raise ValueError("campaign_end must not precede campaign_start")
    if spec.requires_atlas_only and not (atlas_summary and atlas_summary.strip()):
        raise ValueError("atlas_summary is required for an atlas-only pass")

    period_start = spec.period_start or campaign_start
    period_end = spec.period_end or campaign_end
    if period_end < period_start:
        raise ValueError("pass period end must not precede start")

    questions = "\n".join(f"- {question}" for question in spec.questions)
    atlas_block = ""
    if atlas_summary is not None:
        atlas_block = f"""
You may inspect ONLY this previously sealed/constructed memory-atlas summary.
It is not fresh web material and must not be treated as evidence:
---
{atlas_summary}
---
"""

    return f"""You are running one pass of a Longcycle MEMORY EXHAUSTION CAMPAIGN.
Industry: {industry}
Campaign period: {campaign_start.isoformat()} to {campaign_end.isoformat()}
Pass: {spec.pass_id}
Pass family: {spec.family}
Pass period: {period_start.isoformat()} to {period_end.isoformat()}

This is UNSOURCED MODEL MEMORY, not evidence.
Fresh web search results are forbidden in this pass.
Do not invent citations, URLs, exact report titles, exact dates, or precise numbers when uncertain.
Do not optimize for famous events. Spend at least half of the useful output on long-tail leads,
forgotten actors, mechanisms, historical vocabulary/search keys, failures, or uncertain fragments.
Separate recollection from inference. A strong recollection is still only a search lead.
{atlas_block}
Questions for this pass:
{questions}

For every useful lead return enough structure for later evidence search:
- lead_kind and claim_scope
- concise summary
- approximate period
- possible actors/entities/projects and old aliases
- recalled mechanism/context
- memory_confidence as recall strength, never truth probability
- importance, novelty, and searchability scores
- query families/search keys
- likely claim-scoped primary source types
- relations to other leads when useful

For each high-importance lead also answer:
1. Who else may be connected?
2. What may have preceded it?
3. What may have followed it?
4. What was it likely called at the time?

If memory is fragmentary, preserve the fragment and give search keys instead of fabricating precision.
"""


def evaluate_campaign_saturation(
    *,
    outcomes: Sequence[RecallPassOutcome],
    has_major_coverage_gaps: bool,
    required_long_tail_families_missing: Sequence[str],
    policy: SaturationPolicy = SaturationPolicy(),
) -> SaturationResult:
    """Approximate saturation; never accepts the model merely saying it has no more memory."""

    reasons: list[str] = []
    if has_major_coverage_gaps:
        reasons.append("major_coverage_gaps_remain")
    if required_long_tail_families_missing:
        reasons.append("required_long_tail_families_missing")
    if len(outcomes) < policy.consecutive_low_novelty_passes:
        reasons.append("insufficient_recent_passes")
        return SaturationResult(False, tuple(reasons))

    recent = outcomes[-policy.consecutive_low_novelty_passes :]
    low_novelty = all(
        item.high_importance_novel_count <= policy.max_high_importance_novel_per_low_pass
        for item in recent
    )
    if not low_novelty:
        reasons.append("high_importance_leads_still_arriving")

    saturated = not reasons and low_novelty
    if saturated:
        reasons.append("orthogonal_passes_reached_low_marginal_novelty")
    return SaturationResult(saturated, tuple(reasons))


@dataclass(frozen=True, slots=True)
class VerificationDepth:
    minimum_query_families: int = 6
    minimum_source_types: int = 3
    require_primary_domain_check: bool = True
    require_reverse_query: bool = True
    require_citation_chase_when_present: bool = True

    def __post_init__(self) -> None:
        if self.minimum_query_families < 1:
            raise ValueError("minimum_query_families must be positive")
        if self.minimum_source_types < 1:
            raise ValueError("minimum_source_types must be positive")


@dataclass(frozen=True, slots=True)
class VerificationSearchProgress:
    query_family_count: int
    source_type_count: int
    primary_domain_checked: bool
    reverse_query_done: bool
    citation_chase_required: bool
    citation_chase_done: bool


def verification_depth_satisfied(
    progress: VerificationSearchProgress,
    depth: VerificationDepth = VerificationDepth(),
) -> bool:
    if progress.query_family_count < depth.minimum_query_families:
        return False
    if progress.source_type_count < depth.minimum_source_types:
        return False
    if depth.require_primary_domain_check and not progress.primary_domain_checked:
        return False
    if depth.require_reverse_query and not progress.reverse_query_done:
        return False
    if (
        depth.require_citation_chase_when_present
        and progress.citation_chase_required
        and not progress.citation_chase_done
    ):
        return False
    return True
