from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import pytest

from longcycle.application.industry_membership_projection import (
    build_industry_membership_projection,
    project_resolved_industry_membership,
    resolve_industry_membership_semantics,
)
from longcycle.domain.enums import (
    EntityType,
    FactEvidenceRole,
    FactValueKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import (
    FactAssertion,
    FactDimensions,
    FactEvidenceRef,
    QualityComponents,
    TimeRange,
)
from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryMembershipSemanticJudgment,
    ResolvedIndustryMembershipResolution,
)


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
ENTITY_ID = UUID("20000000-0000-0000-0000-000000000001")
EVIDENCE_ID = UUID("30000000-0000-0000-0000-000000000001")
ASSERTION_ID = UUID("40000000-0000-0000-0000-000000000001")
RESOLUTION_ID = UUID("50000000-0000-0000-0000-000000000001")
KNOWN_AT = datetime(2021, 6, 1, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)
DECIDED_AT = datetime(2026, 8, 24, 0, 1, tzinfo=UTC)


def _quality() -> QualityComponents:
    return QualityComponents(
        source_quality=0.95,
        extraction_certainty=0.95,
        entity_match=0.95,
        time_unit_completeness=0.95,
        corroboration=0.0,
        freshness=0.9,
        conflict_penalty=0.0,
    )


def _assertion(
    *,
    assertion_id: UUID = ASSERTION_ID,
    evidence_id: UUID = EVIDENCE_ID,
    field_name: str = "industry.membership",
    value: str = "conversion_facility",
    metadata: dict[str, object] | None = None,
    valid_time: TimeRange | None = None,
    valid_time_kind: ValidTimeKind = ValidTimeKind.PERIOD,
) -> FactAssertion:
    return FactAssertion(
        id=assertion_id,
        entity_type=EntityType.FACILITY,
        entity_id=ENTITY_ID,
        field_name=field_name,
        value=value,
        value_type=FactValueKind.TEXT,
        dimensions=FactDimensions(statistical_scope="industry orientation membership"),
        dimensions_complete=True,
        valid_time_kind=valid_time_kind,
        valid_time=valid_time
        or TimeRange(
            start=datetime(2020, 1, 1, tzinfo=UTC),
            end=datetime(2030, 1, 1, tzinfo=UTC),
        ),
        valid_time_precision=(
            TemporalPrecision.RANGE
            if valid_time_kind == ValidTimeKind.PERIOD
            else TemporalPrecision.UNKNOWN
        ),
        known_at=KNOWN_AT,
        source_id=uuid4(),
        document_id=uuid4(),
        evidence=(FactEvidenceRef(evidence_fragment_id=evidence_id),),
        extraction_run_id=uuid4(),
        extractor_name="test",
        extractor_version="1",
        source_cluster=f"test-source-{assertion_id}",
        confidence=0.95,
        quality=_quality(),
        metadata=metadata
        or {
            "industry_node_id": str(INDUSTRY_ID),
            "exposure_type": "direct",
        },
    )


def _resolution(*assertions: FactAssertion) -> ResolvedIndustryMembershipResolution:
    return ResolvedIndustryMembershipResolution(
        resolution_id=RESOLUTION_ID,
        selected_assertions=assertions or (_assertion(),),
        confidence=0.93,
        resolved_at=RESOLVED_AT,
    )


def _decision(
    resolution: ResolvedIndustryMembershipResolution,
    *,
    selected_assertion_id: UUID | None = None,
    reasoning_mode: Literal["standard", "deep"] = "standard",
    material_conflict_detected: bool = False,
) -> IndustryMembershipSemanticDecision:
    selected_id = selected_assertion_id or resolution.selected_assertions[0].id
    evidence_ids = tuple(
        sorted(
            {
                evidence.evidence_fragment_id
                for assertion in resolution.selected_assertions
                for evidence in assertion.evidence
                if evidence.evidence_role == FactEvidenceRole.SUPPORTING
            },
            key=str,
        )
    )
    return IndustryMembershipSemanticDecision(
        decision_id=uuid4(),
        resolution_id=resolution.resolution_id,
        candidate_assertion_ids=tuple(item.id for item in resolution.selected_assertions),
        selected_assertion_id=selected_id,
        reasoning_mode=reasoning_mode,
        material_conflict_detected=material_conflict_detected,
        reasoning_summary="Model selected a source-backed catalog representation.",
        model_name="test-semantic-judge",
        model_version="1",
        decided_at=DECIDED_AT,
        evidence_fragment_ids=evidence_ids,
    )


def test_membership_projection_preserves_source_truth_and_model_audit_boundary() -> None:
    resolution = _resolution(_assertion())
    decision = _decision(resolution)

    first = build_industry_membership_projection(resolution, decision)
    second = build_industry_membership_projection(resolution, decision)

    assert first == second
    assert first.industry_node_id == INDUSTRY_ID
    assert first.entity_id == ENTITY_ID
    assert first.role == "conversion_facility"
    assert first.exposure_type == "direct"
    assert first.valid_from.isoformat() == "2020-01-01"
    assert first.valid_to.isoformat() == "2030-01-01"
    assert first.known_at == KNOWN_AT
    assert first.system_from == DECIDED_AT
    assert first.known_at != first.system_from
    assert first.resolution_id == RESOLUTION_ID
    assert first.semantic_decision_id == decision.decision_id
    assert first.assertion_id == ASSERTION_ID
    assert first.evidence_fragment_ids == (EVIDENCE_ID,)
    assert decision.is_canonical_truth is False


def test_membership_projection_rejects_non_membership_predicate() -> None:
    resolution = _resolution(_assertion(field_name="project.state"))
    with pytest.raises(ValueError, match=r"predicate industry\.membership"):
        build_industry_membership_projection(resolution, _decision(resolution))


def test_membership_projection_accepts_model_selected_assertion_from_multi_assertion_resolution() -> None:
    second_id = UUID("40000000-0000-0000-0000-000000000002")
    second_evidence = UUID("30000000-0000-0000-0000-000000000002")
    first = _assertion()
    second = _assertion(assertion_id=second_id, evidence_id=second_evidence)
    resolution = _resolution(first, second)
    decision = _decision(resolution, selected_assertion_id=second_id)

    projection = build_industry_membership_projection(resolution, decision)

    assert projection.assertion_id == second_id
    assert projection.evidence_fragment_ids == (second_evidence,)
    assert projection.semantic_decision_id == decision.decision_id


def test_membership_projection_rejects_decision_with_mismatched_candidate_set() -> None:
    resolution = _resolution(_assertion())
    decision = _decision(resolution).model_copy(
        update={"candidate_assertion_ids": (ASSERTION_ID, uuid4())}
    )
    with pytest.raises(ValueError, match="candidates do not match"):
        build_industry_membership_projection(resolution, decision)


def test_membership_projection_rejects_missing_or_invalid_industry_identity() -> None:
    missing = _resolution(_assertion(metadata={"exposure_type": "direct"}))
    with pytest.raises(ValueError, match=r"metadata\.industry_node_id"):
        build_industry_membership_projection(missing, _decision(missing))
    invalid = _resolution(_assertion(metadata={"industry_node_id": "not-a-uuid"}))
    with pytest.raises(ValueError, match="must be a UUID"):
        build_industry_membership_projection(invalid, _decision(invalid))


def test_membership_resolution_preserves_upstream_supporting_evidence_invariant() -> None:
    invalid = _assertion().model_copy(
        update={
            "evidence": (
                FactEvidenceRef(
                    evidence_fragment_id=EVIDENCE_ID,
                    evidence_role=FactEvidenceRole.CONTEXT,
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="requires at least one supporting evidence fragment"):
        _resolution(invalid)


def test_membership_projection_rejects_non_text_role() -> None:
    invalid = _assertion().model_copy(
        update={
            "value_type": FactValueKind.BOOLEAN,
            "normalized_boolean": True,
        }
    )
    resolution = _resolution(invalid)
    with pytest.raises(ValueError, match="role must use text"):
        build_industry_membership_projection(resolution, _decision(resolution))


def test_membership_projection_rejects_lossy_catalog_date_conversion() -> None:
    invalid = _assertion(
        valid_time=TimeRange(
            start=datetime(2020, 1, 1, 12, 0, tzinfo=UTC),
            end=datetime(2030, 1, 1, tzinfo=UTC),
        )
    )
    resolution = _resolution(invalid)
    with pytest.raises(ValueError, match="without losing source time precision"):
        build_industry_membership_projection(resolution, _decision(resolution))


def test_unknown_onset_membership_does_not_invent_validity_start() -> None:
    assertion = _assertion(
        valid_time_kind=ValidTimeKind.UNKNOWN,
        valid_time=TimeRange(),
    ).model_copy(
        update={
            "observed_at": datetime(2021, 5, 31, tzinfo=UTC),
            "observed_at_precision": TemporalPrecision.DAY,
        }
    )
    resolution = _resolution(assertion)
    projection = build_industry_membership_projection(resolution, _decision(resolution))

    assert projection.valid_from is None
    assert projection.valid_to is None
    assert projection.known_at == KNOWN_AT


class _FakeSemanticJudge:
    def __init__(
        self,
        *,
        standard: IndustryMembershipSemanticJudgment,
        deep: IndustryMembershipSemanticJudgment | None = None,
    ) -> None:
        self.standard = standard
        self.deep = deep
        self.calls: list[str] = []

    async def judge_industry_membership(
        self,
        resolution: ResolvedIndustryMembershipResolution,
        *,
        reasoning_mode: Literal["standard", "deep"],
    ) -> IndustryMembershipSemanticJudgment:
        del resolution
        self.calls.append(reasoning_mode)
        if reasoning_mode == "standard":
            return self.standard
        if self.deep is None:
            raise AssertionError("unexpected deep membership judgment")
        return self.deep


def _judgment(
    *,
    mode: Literal["standard", "deep"],
    selected_assertion_id: UUID | None,
    conflict: bool,
    can_materialize: bool,
    summary: str,
) -> IndustryMembershipSemanticJudgment:
    return IndustryMembershipSemanticJudgment(
        reasoning_mode=mode,
        selected_assertion_id=selected_assertion_id,
        material_conflict_detected=conflict,
        can_materialize=can_materialize,
        reasoning_summary=summary,
        model_name="test-large-model",
        model_version="2026-08-25",
        decided_at=DECIDED_AT,
    )


async def test_semantic_resolution_uses_standard_model_when_materials_do_not_conflict() -> None:
    resolution = _resolution(_assertion())
    judge = _FakeSemanticJudge(
        standard=_judgment(
            mode="standard",
            selected_assertion_id=ASSERTION_ID,
            conflict=False,
            can_materialize=True,
            summary="The source definitions are materially consistent.",
        )
    )

    decision = await resolve_industry_membership_semantics(
        resolution=resolution,
        semantic_judge=judge,
    )

    assert judge.calls == ["standard"]
    assert decision.selected_assertion_id == ASSERTION_ID
    assert decision.reasoning_mode == "standard"
    assert decision.material_conflict_detected is False


async def test_material_definition_conflict_automatically_escalates_to_deep_reasoning() -> None:
    second_id = UUID("40000000-0000-0000-0000-000000000002")
    second_evidence = UUID("30000000-0000-0000-0000-000000000002")
    resolution = _resolution(
        _assertion(value="conversion_facility"),
        _assertion(
            assertion_id=second_id,
            evidence_id=second_evidence,
            value="integrated_conversion_site",
        ),
    )
    judge = _FakeSemanticJudge(
        standard=_judgment(
            mode="standard",
            selected_assertion_id=None,
            conflict=True,
            can_materialize=False,
            summary="The supplied materials use conflicting role definitions.",
        ),
        deep=_judgment(
            mode="deep",
            selected_assertion_id=second_id,
            conflict=True,
            can_materialize=True,
            summary="After deep comparison, the second assertion is the better scoped representation.",
        ),
    )

    decision = await resolve_industry_membership_semantics(
        resolution=resolution,
        semantic_judge=judge,
    )

    assert judge.calls == ["standard", "deep"]
    assert decision.reasoning_mode == "deep"
    assert decision.material_conflict_detected is True
    assert decision.selected_assertion_id == second_id
    assert "standard:" in decision.reasoning_summary
    assert "deep:" in decision.reasoning_summary
    projection = build_industry_membership_projection(resolution, decision)
    assert projection.role == "integrated_conversion_site"
    assert projection.evidence_fragment_ids == (second_evidence,)


async def test_unresolved_deep_conflict_fails_closed_before_membership_write() -> None:
    second_id = UUID("40000000-0000-0000-0000-000000000002")
    resolution = _resolution(_assertion(), _assertion(assertion_id=second_id, evidence_id=uuid4()))
    judge = _FakeSemanticJudge(
        standard=_judgment(
            mode="standard",
            selected_assertion_id=None,
            conflict=True,
            can_materialize=False,
            summary="Definitions conflict.",
        ),
        deep=_judgment(
            mode="deep",
            selected_assertion_id=None,
            conflict=True,
            can_materialize=False,
            summary="Deep reasoning cannot resolve the contradiction safely.",
        ),
    )

    with pytest.raises(ValueError, match="could not resolve material-definition conflict"):
        await resolve_industry_membership_semantics(
            resolution=resolution,
            semantic_judge=judge,
        )


class _FakeResolutionReader:
    def __init__(self, resolution: ResolvedIndustryMembershipResolution) -> None:
        self.resolution = resolution

    async def industry_membership_resolution(
        self,
        resolution_id: UUID,
    ) -> ResolvedIndustryMembershipResolution:
        assert resolution_id == self.resolution.resolution_id
        return self.resolution


class _FakeDecisionWriter:
    def __init__(self) -> None:
        self.rows: list[IndustryMembershipSemanticDecision] = []

    async def append_industry_membership_semantic_decision(
        self,
        decision: IndustryMembershipSemanticDecision,
    ) -> IndustryMembershipSemanticDecision:
        self.rows.append(decision)
        return decision


class _FakeProjectionWriter:
    def __init__(self) -> None:
        self.rows: list[IndustryMembershipProjection] = []

    async def append_industry_membership(
        self,
        projection: IndustryMembershipProjection,
    ) -> IndustryMembershipProjection:
        self.rows.append(projection)
        return projection


async def test_projection_service_persists_model_decision_before_catalog_projection() -> None:
    resolution = _resolution(_assertion())
    judge = _FakeSemanticJudge(
        standard=_judgment(
            mode="standard",
            selected_assertion_id=ASSERTION_ID,
            conflict=False,
            can_materialize=True,
            summary="Single source-backed definition is materializable.",
        )
    )
    decision_writer = _FakeDecisionWriter()
    membership_writer = _FakeProjectionWriter()

    projected = await project_resolved_industry_membership(
        resolution_reader=_FakeResolutionReader(resolution),
        semantic_judge=judge,
        decision_writer=decision_writer,
        membership_writer=membership_writer,
        resolution_id=RESOLUTION_ID,
    )

    assert judge.calls == ["standard"]
    assert len(decision_writer.rows) == 1
    assert membership_writer.rows == [projected]
    assert projected.semantic_decision_id == decision_writer.rows[0].decision_id
    assert projected.known_at == KNOWN_AT
    assert projected.system_from == DECIDED_AT
