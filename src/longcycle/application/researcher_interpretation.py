from __future__ import annotations

from typing import Any

from longcycle.domain.enums import OutcomeSemanticRelation
from longcycle.domain.epistemic import OutcomeMemoryRecord, TemporalExtent


def researcher_time_hint(
    extent: TemporalExtent,
    *,
    observed_time: TemporalExtent | None = None,
) -> dict[str, Any]:
    """Build a useful retrieval/orientation hint without changing canonical time.

    Canonical temporal semantics stay untouched. This helper only tells researcher-facing
    code how much can safely be said for search/orientation purposes:

    - source-supported instant/period bounds remain direct;
    - timeless remains direct;
    - an unknown onset plus a grounded observation can support only an ``as_of`` hint;
    - otherwise time stays unknown.

    The result is deliberately not a Fact/Reality mutation and must never be persisted as
    occurrence time merely because it is convenient for filtering or narration.
    """

    if extent.kind == "instant":
        assert extent.at is not None
        return {
            "certainty": "direct",
            "hint_kind": "source_supported_instant",
            "at": extent.at.isoformat(),
            "from": None,
            "to": None,
            "precision": extent.precision.value,
            "source_text": extent.source_text,
            "onset_known": True,
        }
    if extent.kind == "period":
        return {
            "certainty": "direct",
            "hint_kind": "source_supported_period",
            "at": None,
            "from": extent.start.isoformat() if extent.start is not None else None,
            "to": extent.end.isoformat() if extent.end is not None else None,
            "precision": extent.precision.value,
            "source_text": extent.source_text,
            "onset_known": extent.start is not None,
        }
    if extent.kind == "timeless":
        return {
            "certainty": "direct",
            "hint_kind": "timeless",
            "at": None,
            "from": None,
            "to": None,
            "precision": extent.precision.value,
            "source_text": extent.source_text,
            "onset_known": False,
        }
    if observed_time is not None and observed_time.kind == "instant":
        assert observed_time.at is not None
        return {
            "certainty": "entailed",
            "hint_kind": "state_true_as_of_observation_onset_unknown",
            "at": observed_time.at.isoformat(),
            "from": None,
            "to": None,
            "precision": observed_time.precision.value,
            "source_text": observed_time.source_text,
            "onset_known": False,
        }
    return {
        "certainty": "unknown",
        "hint_kind": "source_time_unknown",
        "at": None,
        "from": None,
        "to": None,
        "precision": extent.precision.value,
        "source_text": extent.source_text,
        "onset_known": False,
    }


def researcher_outcome_interpretation(outcome: OutcomeMemoryRecord) -> dict[str, Any]:
    """Expose information value without changing CAP-0004 Outcome semantics."""

    if outcome.semantic_relation == OutcomeSemanticRelation.DIRECT_MATCH:
        return {
            "certainty": "direct",
            "interpretation_kind": "direct_target_evaluation",
            "target_resolution": outcome.evaluation_status,
            "related_milestone_visible": False,
            "does_not_promote_target_status": False,
        }
    if outcome.semantic_relation == OutcomeSemanticRelation.RELATED_MILESTONE:
        return {
            "certainty": "entailed",
            "interpretation_kind": "related_milestone_signal",
            "target_resolution": "not_directly_resolved",
            "related_milestone_visible": True,
            "does_not_promote_target_status": True,
        }
    return {
        "certainty": "unknown",
        "interpretation_kind": "not_comparable",
        "target_resolution": "not_directly_resolved",
        "related_milestone_visible": False,
        "does_not_promote_target_status": True,
    }


def model_analysis_policy() -> dict[str, Any]:
    """Declare the allowed researcher-analysis lane without creating truth semantics."""

    return {
        "certainty_class": "model_judgment",
        "allowed_analytical_claims": [
            "participant_importance",
            "causality",
            "ambiguous_value_chain_role",
        ],
        "requires_explicit_model_label": True,
        "requires_reasoning_or_supporting_context": True,
        "may_create_canonical_reality": False,
        "may_create_membership_truth": False,
        "may_backdate_historical_market_knowledge": False,
    }
