from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TriggerDisposition(StrEnum):
    PROMOTE = "promote"
    CANDIDATE = "candidate"
    ALREADY_ROUTED = "already_routed"
    INSUFFICIENT_INDEPENDENCE = "insufficient_independence"


@dataclass(frozen=True, slots=True)
class TriggerObservation:
    trigger: str
    shard_id: str
    lead_id: str
    importance_score: float

    def __post_init__(self) -> None:
        if not 0 <= self.importance_score <= 1:
            raise ValueError("importance_score must be between 0 and 1")
        if not self.trigger:
            raise ValueError("trigger must not be blank")
        if not self.shard_id:
            raise ValueError("shard_id must not be blank")


@dataclass(frozen=True, slots=True)
class TriggerPromotionDecision:
    trigger: str
    disposition: TriggerDisposition
    distinct_shards: tuple[str, ...]
    observation_count: int
    high_importance_count: int
    reason_codes: tuple[str, ...]


KNOWN_TIER_A_ROUTES: frozenset[str] = frozenset(
    {
        "UP-HARDROCK",
        "UP-BRINE",
        "UP-CONCENTRATE",
        "UP-CHEMICALS",
        "MID-LFP",
        "MID-TERNARY",
        "MID-ANODE",
        "MID-SEPARATOR",
        "MID-ELECTROLYTE",
        "BAT-CELL",
        "DOWN-NEV",
        "DOWN-ESS",
        "DOWN-OTHER",
        "LOOP-RECYCLING",
    }
)


def evaluate_trigger_promotion(
    observations: tuple[TriggerObservation, ...],
    *,
    high_importance_threshold: float = 0.85,
) -> TriggerPromotionDecision:
    if not observations:
        raise ValueError("at least one trigger observation is required")

    trigger = observations[0].trigger
    if any(item.trigger != trigger for item in observations):
        raise ValueError("all observations must refer to the same trigger")

    distinct_shards = tuple(sorted({item.shard_id for item in observations}))
    high_importance_count = sum(
        item.importance_score >= high_importance_threshold for item in observations
    )
    reason_codes: list[str] = []

    if trigger in KNOWN_TIER_A_ROUTES:
        return TriggerPromotionDecision(
            trigger=trigger,
            disposition=TriggerDisposition.ALREADY_ROUTED,
            distinct_shards=distinct_shards,
            observation_count=len(observations),
            high_importance_count=high_importance_count,
            reason_codes=("existing_tier_a_route",),
        )

    if trigger.startswith("BRIDGE-"):
        if len(distinct_shards) >= 2:
            reason_codes.append("independently_recalled_by_multiple_shards")
            return TriggerPromotionDecision(
                trigger=trigger,
                disposition=TriggerDisposition.PROMOTE,
                distinct_shards=distinct_shards,
                observation_count=len(observations),
                high_importance_count=high_importance_count,
                reason_codes=tuple(reason_codes),
            )
        if high_importance_count >= 3:
            reason_codes.append("repeated_high_importance_within_one_shard")
            return TriggerPromotionDecision(
                trigger=trigger,
                disposition=TriggerDisposition.CANDIDATE,
                distinct_shards=distinct_shards,
                observation_count=len(observations),
                high_importance_count=high_importance_count,
                reason_codes=tuple(reason_codes),
            )
        return TriggerPromotionDecision(
            trigger=trigger,
            disposition=TriggerDisposition.INSUFFICIENT_INDEPENDENCE,
            distinct_shards=distinct_shards,
            observation_count=len(observations),
            high_importance_count=high_importance_count,
            reason_codes=("bridge_needs_second_independent_shard",),
        )

    if trigger.startswith("SAT-"):
        if len(distinct_shards) >= 2 and high_importance_count >= 2:
            reason_codes.append("satellite_independently_recalled")
            reason_codes.append("multiple_high_importance_leads")
            return TriggerPromotionDecision(
                trigger=trigger,
                disposition=TriggerDisposition.PROMOTE,
                distinct_shards=distinct_shards,
                observation_count=len(observations),
                high_importance_count=high_importance_count,
                reason_codes=tuple(reason_codes),
            )
        if len(observations) >= 2 and high_importance_count >= 1:
            return TriggerPromotionDecision(
                trigger=trigger,
                disposition=TriggerDisposition.CANDIDATE,
                distinct_shards=distinct_shards,
                observation_count=len(observations),
                high_importance_count=high_importance_count,
                reason_codes=("satellite_repeated_but_not_independent",),
            )
        return TriggerPromotionDecision(
            trigger=trigger,
            disposition=TriggerDisposition.INSUFFICIENT_INDEPENDENCE,
            distinct_shards=distinct_shards,
            observation_count=len(observations),
            high_importance_count=high_importance_count,
            reason_codes=("satellite_needs_more_evidence_of_research_value",),
        )

    return TriggerPromotionDecision(
        trigger=trigger,
        disposition=TriggerDisposition.CANDIDATE,
        distinct_shards=distinct_shards,
        observation_count=len(observations),
        high_importance_count=high_importance_count,
        reason_codes=("unclassified_trigger_requires_review",),
    )
