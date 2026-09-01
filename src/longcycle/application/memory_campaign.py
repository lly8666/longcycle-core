from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal


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
    minimum_distinct_recent_families: int = 3

    def __post_init__(self) -> None:
        if self.consecutive_low_novelty_passes < 3:
            raise ValueError("consecutive_low_novelty_passes cannot weaken the three-pass floor")
        if self.max_high_importance_novel_per_low_pass < 0:
            raise ValueError("max_high_importance_novel_per_low_pass must be non-negative")
        if self.max_high_importance_novel_per_low_pass > 1:
            raise ValueError(
                "max_high_importance_novel_per_low_pass cannot weaken the safety ceiling"
            )
        if self.minimum_distinct_recent_families < 3:
            raise ValueError(
                "minimum_distinct_recent_families cannot weaken the three-family floor"
            )
        if self.minimum_distinct_recent_families > self.consecutive_low_novelty_passes:
            raise ValueError(
                "minimum_distinct_recent_families cannot exceed consecutive_low_novelty_passes"
            )


DEFAULT_SATURATION_POLICY = SaturationPolicy()


@dataclass(frozen=True, slots=True)
class SaturationResult:
    saturated: bool
    reason_codes: tuple[str, ...]


CampaignStage = Literal[
    "orientation_only",
    "active_recall",
    "low_novelty_confirmation",
    "seal_candidate",
    "sealed",
    "evidence",
]

FrontierState = Literal["open", "deferred", "closed", "outside_scope"]

_CAMPAIGN_STAGES = {
    "orientation_only",
    "active_recall",
    "low_novelty_confirmation",
    "seal_candidate",
    "sealed",
    "evidence",
}
_FRONTIER_STATES = {"open", "deferred", "closed", "outside_scope"}
MAX_OPEN_EXPLORATION_FRONTIERS = 64


@dataclass(frozen=True, slots=True)
class SealReviewState:
    """Explicit audit state required before a blind-memory shard may seal."""

    campaign_stage: CampaignStage
    negative_space_review_complete: bool
    independent_challenger_complete: bool
    fresh_search_used: bool = False

    def __post_init__(self) -> None:
        if self.campaign_stage not in _CAMPAIGN_STAGES:
            raise ValueError(f"unsupported campaign_stage: {self.campaign_stage}")


@dataclass(frozen=True, slots=True)
class ExplorationFrontier:
    """One sparse candidate for the next bounded recall probe."""

    frontier_id: str
    priority_rank: int
    next_probe: str
    state: FrontierState = "open"

    def __post_init__(self) -> None:
        if not self.frontier_id.strip():
            raise ValueError("frontier_id must not be blank")
        if self.priority_rank < 1:
            raise ValueError("priority_rank must be positive")
        if not self.next_probe.strip():
            raise ValueError("next_probe must not be blank")
        if self.state not in _FRONTIER_STATES:
            raise ValueError(f"unsupported frontier state: {self.state}")


def choose_next_exploration_frontier(
    frontiers: Sequence[ExplorationFrontier],
) -> ExplorationFrontier | None:
    """Choose one deterministic open frontier without constructing a dense coverage grid."""

    open_frontiers = [item for item in frontiers if item.state == "open"]
    if len(open_frontiers) > MAX_OPEN_EXPLORATION_FRONTIERS:
        raise ValueError("too many open exploration frontiers; archive or cohort them first")

    priority_ranks = [item.priority_rank for item in open_frontiers]
    if len(priority_ranks) != len(set(priority_ranks)):
        raise ValueError("open exploration frontiers must have unique priority ranks")

    return min(open_frontiers, key=lambda item: item.priority_rank, default=None)


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
You may inspect ONLY this previously constructed memory-atlas summary.
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
This is one bounded campaign observation. This pass cannot seal its own shard or campaign.
Only a separate compact-index novelty review and seal gate may authorize that transition.
Do not invent citations, URLs, exact report titles, exact dates, or precise numbers when uncertain.
Do not optimize for famous events. Spend at least half of the useful output on long-tail leads,
forgotten actors, mechanisms, historical vocabulary/search keys, failures, or uncertain fragments.
Separate recollection from inference. A strong recollection is still only a search lead.
{atlas_block}
Questions for this pass:
{questions}

For every useful lead preserve the recollection even when later search planning is incomplete:
- lead_kind and claim_scope
- concise summary
- approximate period
- possible actors/entities/projects and old aliases when remembered
- recalled mechanism/context
- memory_confidence as recall strength, never truth probability
- importance, novelty, and searchability scores
- query families/search keys when they come to mind
- likely claim-scoped primary source types when they come to mind
- relations to other leads when useful

Do not discard a useful lead merely because you cannot yet supply a query, source type, relation,
or disconfirmation path. Those are search-planning fields that can be completed before delegation.

For each high-importance lead also answer when memory permits:
1. Who else may be connected?
2. What may have preceded it?
3. What may have followed it?
4. What was it likely called at the time?

At the end, classify candidates as new_category, useful_refinement, or duplicate when a same-shard
compact index was supplied, and report the three counts truthfully. A duplicate is a valid
low-novelty observation; do not rewrite it until it appears novel.

If memory is fragmentary, preserve the fragment instead of fabricating precision or a fake search plan.
"""


def build_self_verification_prompt(
    *,
    industry: str,
    sealed_atlas_digest: str,
    lead_packet: str,
) -> str:
    """Build a search-enabled second-stage prompt that cannot rewrite blind recall."""

    if not industry.strip():
        raise ValueError("industry must not be blank")
    if not sealed_atlas_digest.strip():
        raise ValueError("sealed_atlas_digest must not be blank")
    if not lead_packet.strip():
        raise ValueError("lead_packet must not be blank")

    return f"""You are running Longcycle HIGH-MODEL SELF VERIFICATION.
Industry: {industry}
Sealed blind-atlas digest: {sealed_atlas_digest}

The blind memory atlas is already sealed. You may use fresh web search in this stage,
but you MUST NOT rewrite, delete, or retroactively improve the blind recall.

Leads to investigate:
---
{lead_packet}
---

Objectives:
1. Turn vague memory into precise actor/project/report names, historical aliases, and query terms.
2. Find the most likely claim-scoped PRIMARY or authoritative source for each lead.
3. Detect syndication/repost chains so repeated pages are not mistaken for independent evidence.
4. Run at least one contradiction-oriented search for high-impact leads.
5. Produce candidate URLs and a concrete task packet for delegated evidence agents when more work remains.

Hard boundaries:
- Search snippets are discovery material, not Evidence.
- A candidate URL is not Evidence until the normal Longcycle fetch/archive/locator pipeline persists it.
- Search-result count is not truth.
- not_found is not contradiction.
- Do not discard a lead merely because current search is weak.
- Do not promote model memory to Fact or Judgment.
- If primary sources disagree, preserve an authoritative conflict instead of majority voting.

For each lead return:
- lead_id
- refined_summary
- candidate_urls
- refined_queries
- possible_primary_sources
- likely source-origin relationships/repost clusters
- what would count as supporting evidence
- what would count as contradicting evidence
- unresolved questions
- delegated-agent instructions if the lead is not yet settled
"""


def evaluate_campaign_saturation(
    *,
    outcomes: Sequence[RecallPassOutcome],
    has_major_coverage_gaps: bool,
    required_long_tail_families_missing: Sequence[str],
    review: SealReviewState | None = None,
    policy: SaturationPolicy = DEFAULT_SATURATION_POLICY,
) -> SaturationResult:
    """Approximate saturation through explicit stage, orthogonality and review gates."""

    reasons: list[str] = []
    if review is None:
        reasons.append("explicit_seal_review_required")
    else:
        if review.campaign_stage != "seal_candidate":
            reasons.append("not_in_seal_candidate_stage")
        if review.fresh_search_used:
            reasons.append("blind_recall_contaminated_by_fresh_search")
        if not review.negative_space_review_complete:
            reasons.append("negative_space_review_incomplete")
        if not review.independent_challenger_complete:
            reasons.append("independent_challenger_incomplete")

    if has_major_coverage_gaps:
        reasons.append("major_coverage_gaps_remain")
    if required_long_tail_families_missing:
        reasons.append("required_long_tail_families_missing")

    low_novelty = False
    if len(outcomes) < policy.consecutive_low_novelty_passes:
        reasons.append("insufficient_recent_passes")
    else:
        recent = outcomes[-policy.consecutive_low_novelty_passes :]
        distinct_families = {item.family for item in recent}
        if len(distinct_families) < policy.minimum_distinct_recent_families:
            reasons.append("recent_passes_not_orthogonal")
        low_novelty = all(
            item.high_importance_novel_count
            <= policy.max_high_importance_novel_per_low_pass
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
    """Minimum depth required before declaring an unresolved historical search exhausted.

    This is an anti-premature-stop gate for unresolved-exhaustion, not a corroboration quota for
    claims already resolved by claim-scoped authoritative content. Search depth prevents a model
    from turning a shallow failed search into "nothing happened"; it does not require low-value
    quota chasing after authoritative original content has directly answered the claim.
    """

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


DEFAULT_VERIFICATION_DEPTH = VerificationDepth()


@dataclass(frozen=True, slots=True)
class VerificationSearchProgress:
    query_family_count: int
    source_type_count: int
    primary_domain_checked: bool
    reverse_query_done: bool
    citation_chase_required: bool
    citation_chase_done: bool


VerificationResolution = Literal[
    "authoritative_support",
    "authoritative_contradiction",
    "unresolved",
]


@dataclass(frozen=True, slots=True)
class VerificationStopDecision:
    allowed: bool
    reason_code: str


def verification_depth_satisfied(
    progress: VerificationSearchProgress,
    depth: VerificationDepth = DEFAULT_VERIFICATION_DEPTH,
) -> bool:
    """Return whether unresolved-exhaustion minimum search depth has been satisfied."""

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


def verification_stop_decision(
    *,
    resolution: VerificationResolution,
    progress: VerificationSearchProgress,
    high_impact: bool = False,
    depth: VerificationDepth = DEFAULT_VERIFICATION_DEPTH,
) -> VerificationStopDecision:
    """Decide whether a verification task may stop without turning search depth into a quota.

    Authoritative claim-scoped content may resolve a claim before the generic 6-query/3-source
    exhaustion depth. High-impact resolved claims still retain the configured reverse-query guard.
    Only an unresolved task may claim exhaustive stopping after the full minimum depth is satisfied.
    """

    if resolution in {"authoritative_support", "authoritative_contradiction"}:
        if high_impact and depth.require_reverse_query and not progress.reverse_query_done:
            return VerificationStopDecision(False, "high_impact_reverse_query_required")
        return VerificationStopDecision(True, resolution)

    if not verification_depth_satisfied(progress, depth):
        return VerificationStopDecision(False, "unresolved_minimum_depth_not_met")
    return VerificationStopDecision(True, "exhausted_but_unresolved")
