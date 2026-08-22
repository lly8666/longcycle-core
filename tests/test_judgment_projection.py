from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from longcycle.application.judgment_projection import (
    GroundedJudgmentProjectionItem,
    GroundedJudgmentProjectionSpec,
    GroundedProjectionEvidence,
    JudgmentProjectionSubject,
    build_grounded_judgments,
)
from longcycle.domain.enums import (
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)

ROOT = Path(__file__).resolve().parents[1]
KEMERTON_SPEC = ROOT / (
    "research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/"
    "self_verification/UP-CHEMICALS/run-001/tasks/"
    "EVT-002-kemerton-judgment-projection-v1.json"
)


def projection_spec(*, allowed_claim_roles: tuple[str, ...] = ("management_expectation",)) -> GroundedJudgmentProjectionSpec:
    return GroundedJudgmentProjectionSpec(
        schema_version="longcycle-judgment-projection-spec/v1",
        task_id="fixture",
        source_evidence_task_id="evidence-fixture",
        allowed_claim_roles=allowed_claim_roles,
        subjects=(
            JudgmentProjectionSubject(
                id=UUID(int=10),
                entity_type="project",
                canonical_name="Fixture project",
            ),
        ),
        judgments=(
            GroundedJudgmentProjectionItem(
                judgment_key="late-target",
                evidence_fragment_keys=("expectation",),
                subject_entity_id=UUID(int=10),
                speaker_name_text="Management",
                topic_code="project.completion",
                judgment_kind=JudgmentKind.GUIDANCE,
                target_time_kind=JudgmentTargetTimeKind.UNKNOWN,
                target_precision=TemporalPrecision.APPROXIMATE,
                target_text="late 2021",
                value_kind=JudgmentValueKind.TEXT,
                value_text="completion expected in late 2021",
                summary="Completion was expected in late 2021.",
            ),
        ),
    )


def evidence(*, role: str = "management_expectation") -> GroundedProjectionEvidence:
    return GroundedProjectionEvidence(
        fragment_key="expectation",
        evidence_fragment_id=UUID(int=20),
        document_version_id=UUID(int=21),
        source_connector_id=UUID(int=22),
        claim_role=role,
        known_time_upper_bound=datetime(2021, 2, 19, 16, 37, 48, tzinfo=UTC),
        source_published_at=datetime(2021, 2, 19, 16, 37, 48, tzinfo=UTC),
        excerpt="completion expected in late 2021",
    )


def test_projection_preserves_approximate_source_time_without_fake_bounds() -> None:
    projected = build_grounded_judgments(projection_spec(), (evidence(),))

    assert len(projected) == 1
    judgment = projected[0]
    assert judgment.target_time_kind == JudgmentTargetTimeKind.UNKNOWN
    assert judgment.target_precision == TemporalPrecision.APPROXIMATE
    assert judgment.target_text == "late 2021"
    assert judgment.target_from is None
    assert judgment.target_to is None
    assert judgment.first_known_at == datetime(2021, 2, 19, 16, 37, 48, tzinfo=UTC)


def test_projection_rejects_contract_context_as_management_judgment() -> None:
    with pytest.raises(ValueError, match="disallowed claim roles"):
        build_grounded_judgments(projection_spec(), (evidence(role="contract_schedule"),))


def test_projection_rejects_later_outcome_even_if_role_were_allowlisted() -> None:
    spec = projection_spec(allowed_claim_roles=("management_expectation", "outcome_milestone"))

    with pytest.raises(ValueError, match="outcome evidence"):
        build_grounded_judgments(spec, (evidence(role="outcome_milestone"),))


def test_real_kemerton_projection_preserves_coarse_target_semantics() -> None:
    spec = GroundedJudgmentProjectionSpec.model_validate_json(KEMERTON_SPEC.read_text(encoding="utf-8"))
    by_key = {item.judgment_key: item for item in spec.judgments}

    assert len(spec.judgments) == 7
    assert by_key["2020-construction-completion-late-2021"].target_precision == TemporalPrecision.APPROXIMATE
    assert by_key["2020-construction-completion-late-2021"].target_from is None
    assert by_key["2020-construction-completion-late-2021"].target_to is None
    assert by_key["2021q2-kemerton2-completion-by-q1-2022"].target_from is None
    assert by_key["2021q2-kemerton2-completion-by-q1-2022"].target_precision == TemporalPrecision.QUARTER
    assert by_key["2022q1-kemerton1-first-product-may"].target_precision == TemporalPrecision.MONTH
    assert by_key["2022q1-kemerton2-mechanical-completion-h2"].target_precision == TemporalPrecision.HALF_YEAR
