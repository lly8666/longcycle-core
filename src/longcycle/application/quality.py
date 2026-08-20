from __future__ import annotations

from dataclasses import dataclass

from longcycle.domain.models import QualityComponents

WEIGHTS = {
    "source_quality": 0.30,
    "extraction_certainty": 0.20,
    "entity_match": 0.15,
    "time_unit_completeness": 0.15,
    "corroboration": 0.15,
    "freshness": 0.05,
}


def quality_score(components: QualityComponents) -> float:
    weighted = sum(getattr(components, name) * weight for name, weight in WEIGHTS.items())
    return round(max(0.0, min(1.0, weighted - components.conflict_penalty)), 4)


@dataclass(frozen=True, slots=True)
class QualityGate:
    auto_publish: float = 0.85
    review: float = 0.65

    def classify(self, score: float) -> str:
        if score >= self.auto_publish:
            return "auto_publish"
        if score >= self.review:
            return "review"
        return "quarantine"
