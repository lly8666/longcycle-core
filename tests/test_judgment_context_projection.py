from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.application.judgment_context_projection import (
    GroundedJudgmentContextSpec,
    GroundedJudgmentRationaleItem,
    GroundedJudgmentRelationItem,
    build_grounded_judgment_context,
)
from longcycle.application.judgment_projection import GroundedProjectionEvidence
from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentRationaleKind,
    JudgmentRelationType,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)
from longcycle.domain.judgments import JudgmentAssertion, JudgmentEvidenceRef


def judgment(
    *,
    key: str,
    known_day: int,
    topic: str = "market.demand-thesis",
    subject_id: int = 10,
) -> JudgmentAssertion:
    return JudgmentAssertion(
        id=UUID(int=known_day),
        speaker_name_text="Management",
        subject_entity_id=UUID(int=subject_id),
        topic_code=topic,
        judgment_kind=JudgmentKind.THESIS,
        target_time_kind=JudgmentTargetTimeKind.TIMELESS,
        target_precision=TemporalPrecision.UNKNOWN,
        value_kind=JudgmentValueKind.TEXT,
        value_text=f"thesis {key}",
        summary=f"Judgment {key}",
        source_published_at=datetime(2019, 1, known_day, tzinfo=UTC),
        first_known_at=datetime(2019, 1, known_day, tzinfo=UTC),
        extraction_run_id=UUID(int=200 + known_day),
        source_connector_id=UUID(int=300),
        extractor_name="fixture",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=UUID(int=100 + known_day),
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
        metadata={"judgment_key": key},
    )


def evidence(
    *,
    key: str,
    known_day: int,
    role: str = "management_thesis_context",
) -> GroundedProjectionEvidence:
    return GroundedProjectionEvidence(
        fragment_key=key,
        evidence_fragment_id=UUID(int=400 + known_day),
        document_version_id=UUID(int=500 + known_day),
        source_connector_id=UUID(int=300),
        claim_role=role,
        known_time_upper_bound=datetime(2019, 1, known_day, tzinfo=UTC),
        source_published_at=datetime(2019, 1, known_day, tzinfo=UTC),
        excerpt=f"context {key}",
    )


def context_spec() -> GroundedJudgmentContextSpec:
    return GroundedJudgmentContextSpec(
        schema_version="longcycle-judgment-context-projection-spec/v1",
        task_id="context-fixture",
        source_judgment_task_id="judgments-fixture",
        source_evidence_task_id="evidence-fixture",
        allowed_rationale_claim_roles=("management_thesis_context",),
        rationales=(
            GroundedJudgmentRationaleItem(
                rationale_key="later-mechanism",
                judgment_key="later",
                rationale_kind=JudgmentRationaleKind.MECHANISM,
                summary="A source-backed mechanism explains the revised pace.",
                evidence_fragment_key="later-context",
                linked_judgment_key="earlier",
            ),
        ),
        relations=(
            GroundedJudgmentRelationItem(
                from_judgment_key="later",
                to_judgment_key="earlier",
                relation_type=JudgmentRelationType.REVISES,
                reason_summary="Later cognition qualifies the earlier same-topic thesis.",
            ),
        ),
    )


def test_builds_stable_source_backed_rationale_and_revision_relation() -> None:
    judgments = (judgment(key="earlier", known_day=1), judgment(key="later", known_day=2))
    evidence_rows = (evidence(key="later-context", known_day=2),)

    first = build_grounded_judgment_context(context_spec(), judgments, evidence_rows)
    second = build_grounded_judgment_context(context_spec(), judgments, evidence_rows)

    rationales, relations = first
    assert first == second
    assert len(rationales) == 1
    assert rationales[0].judgment_id == judgments[1].id
    assert rationales[0].linked_judgment_id == judgments[0].id
    assert rationales[0].evidence_fragment_id == evidence_rows[0].evidence_fragment_id
    assert len(relations) == 1
    assert relations[0].from_judgment_id == judgments[1].id
    assert relations[0].to_judgment_id == judgments[0].id
    assert relations[0].relation_type == JudgmentRelationType.REVISES


def test_revision_family_rejects_cross_topic_semantic_drift() -> None:
    judgments = (
        judgment(key="earlier", known_day=1),
        judgment(key="later", known_day=2, topic="market.price-thesis"),
    )
    with pytest.raises(ValueError, match="same Judgment topic"):
        build_grounded_judgment_context(
            context_spec(), judgments, (evidence(key="later-context", known_day=2),)
        )


def test_revision_family_rejects_cross_subject_semantic_drift() -> None:
    judgments = (
        judgment(key="earlier", known_day=1),
        judgment(key="later", known_day=2, subject_id=11),
    )
    with pytest.raises(ValueError, match="same Judgment subject"):
        build_grounded_judgment_context(
            context_spec(), judgments, (evidence(key="later-context", known_day=2),)
        )


def test_revision_family_rejects_reverse_time_relation() -> None:
    spec = context_spec().model_copy(update={"rationales": ()})
    judgments = (judgment(key="earlier", known_day=3), judgment(key="later", known_day=2))
    with pytest.raises(ValueError, match="earlier cognition"):
        build_grounded_judgment_context(
            spec, judgments, (evidence(key="later-context", known_day=2),)
        )


def test_rationale_rejects_future_evidence_leakage() -> None:
    judgments = (judgment(key="earlier", known_day=1), judgment(key="later", known_day=2))
    with pytest.raises(ValueError, match="after its Judgment"):
        build_grounded_judgment_context(
            context_spec(), judgments, (evidence(key="later-context", known_day=3),)
        )


def test_rationale_rejects_future_linked_judgment_leakage() -> None:
    spec = context_spec().model_copy(update={"relations": ()})
    judgments = (judgment(key="earlier", known_day=3), judgment(key="later", known_day=2))
    with pytest.raises(ValueError, match="later knowledge vintage"):
        build_grounded_judgment_context(
            spec, judgments, (evidence(key="later-context", known_day=2),)
        )


def test_rationale_rejects_disallowed_claim_role() -> None:
    judgments = (judgment(key="earlier", known_day=1), judgment(key="later", known_day=2))
    with pytest.raises(ValueError, match="disallowed claim role"):
        build_grounded_judgment_context(
            context_spec(),
            judgments,
            (evidence(key="later-context", known_day=2, role="later_outcome"),),
        )


def test_unknown_context_key_fails_closed() -> None:
    spec = context_spec().model_copy(
        update={
            "relations": (
                GroundedJudgmentRelationItem(
                    from_judgment_key="missing",
                    to_judgment_key="earlier",
                    relation_type=JudgmentRelationType.REVISES,
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="unavailable Judgment"):
        build_grounded_judgment_context(
            spec,
            (judgment(key="earlier", known_day=1), judgment(key="later", known_day=2)),
            (evidence(key="later-context", known_day=2),),
        )
