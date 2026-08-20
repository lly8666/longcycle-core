from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelTier(StrEnum):
    T0_RULES = "t0_rules"
    T1_ECONOMY = "t1_economy"
    T2_REASONING = "t2_reasoning"
    T3_HUMAN = "t3_human"


@dataclass(frozen=True, slots=True)
class RoutingContext:
    high_impact: bool = False
    has_conflict: bool = False
    schema_failures: int = 0
    entity_match_confidence: float = 1.0
    document_complexity: float = 0.0

    def __post_init__(self) -> None:
        if self.schema_failures < 0:
            raise ValueError("schema_failures cannot be negative")
        if not 0 <= self.entity_match_confidence <= 1:
            raise ValueError("entity_match_confidence must be between 0 and 1")
        if not 0 <= self.document_complexity <= 1:
            raise ValueError("document_complexity must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class BudgetState:
    daily_limit_microunits: int
    used_microunits: int
    hard_stop_ratio: float = 1.0

    def __post_init__(self) -> None:
        if self.daily_limit_microunits < 0 or self.used_microunits < 0:
            raise ValueError("budget values cannot be negative")
        if not 0 <= self.hard_stop_ratio <= 1:
            raise ValueError("hard_stop_ratio must be between 0 and 1")

    @property
    def exhausted(self) -> bool:
        return self.used_microunits >= int(self.daily_limit_microunits * self.hard_stop_ratio)


class ModelRouter:
    def route(self, context: RoutingContext, budget: BudgetState) -> ModelTier:
        if context.high_impact and (context.has_conflict or context.entity_match_confidence < 0.8):
            return ModelTier.T3_HUMAN
        if budget.exhausted:
            return ModelTier.T0_RULES
        if context.has_conflict or context.schema_failures >= 2 or context.document_complexity >= 0.75:
            return ModelTier.T2_REASONING
        if context.schema_failures == 1 or context.entity_match_confidence < 0.9:
            return ModelTier.T2_REASONING
        return ModelTier.T1_ECONOMY
