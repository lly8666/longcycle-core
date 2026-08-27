from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from longcycle.application.researcher_interpretation import (
    model_analysis_policy,
    researcher_outcome_interpretation,
    researcher_time_hint,
)
from longcycle.application.trajectory_view import build_researcher_trajectory_view
from longcycle.domain.enums import OutcomeSemanticRelation, TemporalPrecision
from longcycle.domain.epistemic import (
    CanonicalRealityRecord,
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    MemorySubjectRef,
    OutcomeMemoryRecord,
    TemporalExtent,
    snapshot_from_timeline,
)


SUBJECT = MemorySubjectRef(entity_id=UUID("10000000-0000-0000-0000-000000000001"))
REALITY_ID = UUID("20000000-0000-0000-0000-000000000001")
JUDGMENT_ID = UUID("30000000-0000-0000-0000-000000000001")
OUTCOME_ID = UUID("40000000-0000-0000-0000-000000000001")
EVIDENCE_ID = UUID("50000000-0000-0000-0000-000000000001")


def test_unknown_onset_can_surface_as_of_hint_without_inventing_start() -> None:
    hint = researcher_time_hint(
        TemporalExtent(kind="unknown"),
        observed_time=TemporalExtent(
            kind="instant",
            at=datetime(2024, 10, 31, tzinfo=UTC),
            precision=TemporalPrecision.DAY,
            source_text="Q3 results observed state",
        ),
    )

    assert hint == {
        "certainty": "entailed",
        "hint_kind": "state_true_as_of_observation_onset_unknown",
        "at": "2024-10-31T00:00:00+00:00",
        "from": None,
        "to": None,
        "precision": "day",
        "source_text": "Q3 results observed state",
        "onset_known": False,
    }


def test_related_milestone_is_useful_without_becoming_direct_realization() -> None:
    outcome = OutcomeMemoryRecord(
        evaluation_id=OUTCOME_ID,
        judgment_id=JUDGMENT_ID,
        subject=SUBJECT,
        canonical_fact_version_id=REALITY_ID,
        outcome_evidence_fragment_id=EVIDENCE_ID,
        evaluation_status="indeterminate",
        semantic_relation=OutcomeSemanticRelation.RELATED_MILESTONE,
        occurrence_time=TemporalExtent(kind="unknown"),
        known_at=datetime(2024, 11, 1, tzinfo=UTC),
        timing_relation="not_comparable",
        evaluator_name="test",
        evaluator_version="1",
    )

    interpretation = researcher_outcome_interpretation(outcome)

    assert interpretation["certainty"] == "entailed"
    assert interpretation["interpretation_kind"] == "related_milestone_signal"
    assert interpretation["target_resolution"] == "not_directly_resolved"
    assert interpretation["related_milestone_visible"] is True
    assert interpretation["does_not_promote_target_status"] is True


def test_model_analysis_policy_allows_analysis_but_never_truth_promotion() -> None:
    policy = model_analysis_policy()

    assert set(policy["allowed_analytical_claims"]) == {
        "participant_importance",
        "causality",
        "ambiguous_value_chain_role",
    }
    assert policy["certainty_class"] == "model_judgment"
    assert policy["requires_explicit_model_label"] is True
    assert policy["may_create_canonical_reality"] is False
    assert policy["may_create_membership_truth"] is False
    assert policy["may_backdate_historical_market_knowledge"] is False


def test_trajectory_surfaces_time_and_related_milestone_hints() -> None:
    reality = CanonicalRealityRecord(
        canonical_fact_version_id=REALITY_ID,
        subject=SUBJECT,
        predicate_code="product.lifecycle_state",
        value_kind="text",
        value_text="mass_production",
        valid_time=TemporalExtent(kind="unknown"),
        observed_time=TemporalExtent(
            kind="instant",
            at=datetime(2024, 10, 31, tzinfo=UTC),
            precision=TemporalPrecision.DAY,
            source_text="state observed in Q3 results",
        ),
        known_at=datetime(2024, 11, 1, tzinfo=UTC),
        confidence=0.95,
        evidence_fragment_ids=(EVIDENCE_ID,),
    )
    judgment = JudgmentMemoryRecord(
        judgment_id=JUDGMENT_ID,
        subject=SUBJECT,
        topic_code="qualification.target",
        judgment_kind="guidance",
        target_time=TemporalExtent(
            kind="period",
            start=datetime(2024, 7, 1, tzinfo=UTC),
            end=datetime(2024, 10, 1, tzinfo=UTC),
            precision=TemporalPrecision.QUARTER,
            source_text="Q3 2024",
        ),
        value_kind="text",
        value_text="qualification target",
        summary="Qualification expected in Q3.",
        known_at=datetime(2024, 5, 1, tzinfo=UTC),
        evidence_fragment_ids=(UUID("50000000-0000-0000-0000-000000000002"),),
    )
    outcome = OutcomeMemoryRecord(
        evaluation_id=OUTCOME_ID,
        judgment_id=JUDGMENT_ID,
        subject=SUBJECT,
        canonical_fact_version_id=REALITY_ID,
        outcome_evidence_fragment_id=EVIDENCE_ID,
        evaluation_status="indeterminate",
        semantic_relation=OutcomeSemanticRelation.RELATED_MILESTONE,
        occurrence_time=TemporalExtent(kind="unknown"),
        known_at=datetime(2024, 11, 1, tzinfo=UTC),
        timing_relation="not_comparable",
        evaluator_name="test",
        evaluator_version="1",
    )
    snapshot = snapshot_from_timeline(
        IndustrialMemoryTimeline(
            reality=(reality,),
            judgments=(judgment,),
            outcomes=(outcome,),
        ),
        knowledge_cutoff=datetime(2024, 11, 2, tzinfo=UTC),
    )

    view = build_researcher_trajectory_view(snapshot)
    reality_entry = next(item for item in view["entries"] if item["layer"] == "reality")
    outcome_entry = next(item for item in view["entries"] if item["layer"] == "outcome")
    storyline = view["judgment_storylines"][0]

    assert reality_entry["historical_time"]["kind"] == "unknown"
    assert reality_entry["researcher_time_hint"]["certainty"] == "entailed"
    assert reality_entry["researcher_time_hint"]["onset_known"] is False
    assert outcome_entry["evaluation_status"] == "indeterminate"
    assert outcome_entry["semantic_relation"] == "related_milestone"
    assert outcome_entry["researcher_interpretation"]["related_milestone_visible"] is True
    assert "original target remains not directly resolved" in storyline["researcher_summary"]
    assert view["boundary"]["researcher_time_hints_do_not_mutate_canonical_time"] is True
    assert view["boundary"]["related_milestones_surface_without_realization_promotion"] is True
