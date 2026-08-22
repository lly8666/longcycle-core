from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from longcycle.domain.enums import Decision, FactStatus, TemporalPrecision, ValidTimeKind
from longcycle.domain.models import FactAssertion, ReconciliationResult

from .quality import QualityGate, quality_score


@dataclass(frozen=True, slots=True)
class ReconciliationPolicy:
    gate: QualityGate = QualityGate()
    numeric_relative_tolerance: Decimal = Decimal("0.01")
    high_impact_min_source_quality: float = 0.80
    high_impact_min_independent_sources: int = 2

    def __post_init__(self) -> None:
        if self.numeric_relative_tolerance < 0:
            raise ValueError("numeric_relative_tolerance cannot be negative")
        if not 0 <= self.high_impact_min_source_quality <= 1:
            raise ValueError("high_impact_min_source_quality must be between 0 and 1")
        if self.high_impact_min_independent_sources < 1:
            raise ValueError("high_impact_min_independent_sources must be positive")
        if not 0 <= self.gate.review <= self.gate.auto_publish <= 1:
            raise ValueError("quality gate thresholds must be ordered within [0, 1]")


class Reconciler:
    evaluator_name = "rule_reconciler"
    evaluator_version = "2.1.0"

    def __init__(
        self,
        policy: ReconciliationPolicy | None = None,
        *,
        predicate_policies: dict[str, ReconciliationPolicy] | None = None,
        evaluator_version: str | None = None,
    ) -> None:
        self.policy = policy or ReconciliationPolicy()
        self.predicate_policies = dict(predicate_policies or {})
        self.evaluator_version = evaluator_version or type(self).evaluator_version

    def reconcile(self, candidate: FactAssertion, existing: Sequence[FactAssertion]) -> ReconciliationResult:
        policy = self._policy_for(candidate.field_name)
        score = quality_score(candidate.quality)
        if not candidate.dimensions_complete:
            return self._review(candidate, score, "incomplete_dimensions")
        source_supported_unknown_onset = (
            candidate.valid_time_kind == ValidTimeKind.UNKNOWN
            and candidate.valid_time.start is None
            and candidate.valid_time.end is None
            and candidate.valid_time_precision == TemporalPrecision.UNKNOWN
            and candidate.observed_at is not None
            and candidate.observed_at_precision != TemporalPrecision.UNKNOWN
            and candidate.observed_at <= candidate.known_at
        )
        if (
            candidate.valid_time_kind == ValidTimeKind.UNKNOWN
            and not source_supported_unknown_onset
        ):
            return self._review(candidate, score, "unknown_valid_time")

        supersession_issue = self._supersession_issue(candidate, existing)
        if supersession_issue is not None:
            return self._review(candidate, score, supersession_issue)

        # A trusted correction removes its predecessor from the active
        # comparison set even if a repository handed us a stale status view.
        superseded_ids = {
            item.supersedes_id
            for item in existing
            if item.status == FactStatus.TRUSTED and item.supersedes_id is not None
        }

        comparable = [
            item
            for item in existing
            if item.id != candidate.id
            and item.id != candidate.supersedes_id
            and item.id not in superseded_ids
            and item.status == FactStatus.TRUSTED
            and item.entity_type == candidate.entity_type
            and item.entity_id == candidate.entity_id
            and item.field_name == candidate.field_name
            and item.comparability_hash == candidate.comparability_hash
            and item.dimensions_complete
            and self._valid_times_overlap(candidate, item)
        ]
        comparisons = [
            (item, self._compare_values(candidate, item, policy))
            for item in comparable
        ]
        matching = [item for item, comparison in comparisons if comparison == "match"]
        conflicting = [item for item, comparison in comparisons if comparison == "conflict"]
        incomparable = [item for item, comparison in comparisons if comparison == "incomparable"]
        independent_clusters = {
            item.source_cluster or str(item.source_id)
            for item in (*matching, candidate)
        }
        reasons: list[str] = []
        if source_supported_unknown_onset:
            reasons.append("source_supported_unknown_onset")
        if candidate.supersedes_id is not None:
            reasons.append("explicit_supersession")

        if matching:
            reasons.append("independent_corroboration" if len(independent_clusters) >= 2 else "duplicate_source_cluster")
            if len(independent_clusters) >= 2:
                score = min(1.0, score + 0.05)

        if conflicting:
            reasons.append("conflicting_values")
            score = max(0.0, score - 0.20)
            return ReconciliationResult(
                assertion_id=candidate.id,
                decision=Decision.CONFLICT,
                score=score,
                reason_codes=tuple(reasons),
                conflicting_assertion_ids=tuple(item.id for item in conflicting),
                status=FactStatus.CONFLICT,
            )

        if incomparable:
            return self._review(candidate, score, "incomparable_unit_or_value_type")

        if candidate.high_impact:
            sufficiently_direct = (
                candidate.quality.source_quality
                >= policy.high_impact_min_source_quality
            )
            sufficiently_corroborated = (
                len(independent_clusters)
                >= policy.high_impact_min_independent_sources
            )
            if not (sufficiently_direct or sufficiently_corroborated):
                reasons.append("high_impact_requires_stronger_evidence")
                return ReconciliationResult(
                    assertion_id=candidate.id,
                    decision=Decision.REVIEW,
                    score=score,
                    reason_codes=tuple(reasons),
                    status=FactStatus.REVIEW,
                )

        gate = policy.gate.classify(score)
        if gate == "auto_publish":
            reasons.append("quality_gate_passed")
            return ReconciliationResult(
                assertion_id=candidate.id,
                decision=Decision.ACCEPT,
                score=score,
                reason_codes=tuple(reasons),
                status=FactStatus.TRUSTED,
            )
        if gate == "review":
            reasons.append("manual_review_band")
            return ReconciliationResult(
                assertion_id=candidate.id,
                decision=Decision.REVIEW,
                score=score,
                reason_codes=tuple(reasons),
                status=FactStatus.REVIEW,
            )
        reasons.append("below_minimum_quality")
        return ReconciliationResult(
            assertion_id=candidate.id,
            decision=Decision.QUARANTINE,
            score=score,
            reason_codes=tuple(reasons),
            status=FactStatus.QUARANTINED,
        )

    def _policy_for(self, predicate: str) -> ReconciliationPolicy:
        exact = self.predicate_policies.get(predicate)
        if exact is not None:
            return exact
        wildcard_matches = [
            (key[:-1], policy)
            for key, policy in self.predicate_policies.items()
            if key.endswith("*") and predicate.startswith(key[:-1])
        ]
        if not wildcard_matches:
            return self.policy
        return max(wildcard_matches, key=lambda item: len(item[0]))[1]

    @staticmethod
    def _compare_values(
        left: FactAssertion,
        right: FactAssertion,
        policy: ReconciliationPolicy,
    ) -> str:
        if left.value_type != right.value_type:
            return "incomparable"
        if left.normalized_number is not None and right.normalized_number is not None:
            if left.normalized_unit is None or left.normalized_unit != right.normalized_unit:
                return "incomparable"
            scale = max(abs(left.normalized_number), abs(right.normalized_number), Decimal("1"))
            within_tolerance = (
                abs(left.normalized_number - right.normalized_number) / scale
                <= policy.numeric_relative_tolerance
            )
            return "match" if within_tolerance else "conflict"
        if (left.normalized_number is None) != (right.normalized_number is None):
            return "incomparable"
        return "match" if left.value_fingerprint == right.value_fingerprint else "conflict"

    def _supersession_issue(
        self,
        candidate: FactAssertion,
        existing: Sequence[FactAssertion],
    ) -> str | None:
        if candidate.supersedes_id is None:
            return None
        if candidate.supersedes_id == candidate.id:
            return "supersession_self_reference"
        target = next(
            (item for item in existing if item.id == candidate.supersedes_id),
            None,
        )
        if target is None:
            return "supersession_target_missing"
        already_superseded = any(
            item.id != candidate.id
            and item.status == FactStatus.TRUSTED
            and item.supersedes_id == target.id
            for item in existing
        )
        if target.status != FactStatus.TRUSTED or already_superseded:
            return "supersession_target_not_current"
        if (
            target.entity_type != candidate.entity_type
            or target.entity_id != candidate.entity_id
            or target.field_name != candidate.field_name
            or target.comparability_hash != candidate.comparability_hash
        ):
            return "supersession_fact_mismatch"
        if (
            target.valid_time_kind != candidate.valid_time_kind
            or target.valid_time.start_utc != candidate.valid_time.start_utc
            or target.valid_time.end_utc != candidate.valid_time.end_utc
        ):
            # Partial-period corrections require interval-level lineage.  Until
            # that exists, fail closed instead of globally retiring the source
            # assertion outside the corrected slice.
            return "supersession_time_range_mismatch"
        if target.source_id != candidate.source_id:
            return "supersession_cross_source_requires_review"
        if target.document_id == candidate.document_id:
            return "supersession_requires_new_document"
        if candidate.known_at < target.known_at:
            return "supersession_not_newer"
        if (
            candidate.source_published_at is not None
            and target.source_published_at is not None
            and candidate.source_published_at < target.source_published_at
        ):
            return "supersession_not_newer"
        return None

    @staticmethod
    def _valid_times_overlap(left: FactAssertion, right: FactAssertion) -> bool:
        if left.valid_time_kind != right.valid_time_kind:
            return False
        if left.valid_time_kind == ValidTimeKind.TIMELESS:
            return True
        if left.valid_time_kind != ValidTimeKind.PERIOD:
            return False
        left_start = left.valid_time.start_utc
        left_end = left.valid_time.end_utc
        right_start = right.valid_time.start_utc
        right_end = right.valid_time.end_utc
        return (
            (left_end is None or right_start is None or right_start < left_end)
            and (
                right_end is None
                or left_start is None
                or left_start < right_end
            )
        )

    @staticmethod
    def _review(candidate: FactAssertion, score: float, reason: str) -> ReconciliationResult:
        return ReconciliationResult(
            assertion_id=candidate.id,
            decision=Decision.REVIEW,
            score=score,
            reason_codes=(reason,),
            status=FactStatus.REVIEW,
        )
