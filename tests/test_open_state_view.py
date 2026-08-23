from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from uuid import UUID

from longcycle.application.open_state_view import build_researcher_open_state_view
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType
from longcycle.domain.epistemic import (
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    JudgmentRationaleMemoryRecord,
    JudgmentRelationMemoryRecord,
    MemorySubjectRef,
    PointInTimeMemorySnapshot,
    TemporalExtent,
    snapshot_from_timeline,
)
from longcycle.domain.memory import (
    DirectSourceSearchStatus,
    MemoryAuditDisposition,
    MemoryHypothesisDisposition,
)
from longcycle.domain.open_states import (
    CurrentResearchOpenStateBundle,
    MemoryCoverageGapRecord,
    MemoryDisagreementOpenRecord,
    MemoryHypothesisOpenRecord,
    RealityConflictAssertionRecord,
    RealitySourceDisagreementRecord,
)
from longcycle.domain.orientation import (
    IndustryDescriptor,
    IndustryOrientationCatalog,
    IndustrySubjectMembershipRecord,
)


INDUSTRY_ID = UUID("11000000-0000-0000-0000-000000000001")
EARLY_ENTITY_ID = UUID("22000000-0000-0000-0000-000000000001")
FUTURE_ENTITY_ID = UUID("22000000-0000-0000-0000-000000000002")
JUDGMENT_A = UUID("33000000-0000-0000-0000-000000000001")
JUDGMENT_B = UUID("33000000-0000-0000-0000-000000000002")
CUTOFF = datetime(2023, 1, 1, tzinfo=UTC)


class FakeCatalogReader:
    def __init__(self, catalog: IndustryOrientationCatalog) -> None:
        self.catalog = catalog

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog:
        assert industry_node_id == INDUSTRY_ID
        return self.catalog


class FakeMemoryReader:
    def __init__(self, timeline: IndustrialMemoryTimeline) -> None:
        self.timeline_value = timeline
        self.last_subjects: tuple[MemorySubjectRef, ...] = ()
        self.last_cutoff: datetime | None = None

    async def timeline(
        self,
        subjects: Sequence[MemorySubjectRef],
    ) -> IndustrialMemoryTimeline:
        return self.timeline_value

    async def snapshot(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> PointInTimeMemorySnapshot:
        self.last_subjects = tuple(subjects)
        self.last_cutoff = knowledge_cutoff
        subject_keys = {item.key for item in subjects}
        judgments = tuple(
            item for item in self.timeline_value.judgments if item.subject.key in subject_keys
        )
        judgment_ids = {item.judgment_id for item in judgments}
        timeline = IndustrialMemoryTimeline(
            judgments=judgments,
            judgment_rationales=tuple(
                item
                for item in self.timeline_value.judgment_rationales
                if item.judgment_id in judgment_ids
            ),
            judgment_relations=tuple(
                item
                for item in self.timeline_value.judgment_relations
                if item.from_judgment_id in judgment_ids and item.to_judgment_id in judgment_ids
            ),
        )
        return snapshot_from_timeline(timeline, knowledge_cutoff=knowledge_cutoff)


class FakeConflictReader:
    def __init__(self, records: tuple[RealitySourceDisagreementRecord, ...]) -> None:
        self.records = records
        self.last_subjects: tuple[MemorySubjectRef, ...] = ()
        self.last_cutoff: datetime | None = None

    async def historical_source_disagreements(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[RealitySourceDisagreementRecord, ...]:
        self.last_subjects = tuple(subjects)
        self.last_cutoff = knowledge_cutoff
        return self.records


class FakeCurrentResearchReader:
    def __init__(self, bundle: CurrentResearchOpenStateBundle) -> None:
        self.bundle = bundle
        self.calls = 0
        self.last_entity_ids: tuple[UUID, ...] = ()

    async def current_open_states(
        self,
        *,
        industry_node_id: UUID,
        entity_ids: Sequence[UUID],
    ) -> CurrentResearchOpenStateBundle:
        assert industry_node_id == INDUSTRY_ID
        self.calls += 1
        self.last_entity_ids = tuple(entity_ids)
        return self.bundle


def _membership(
    *,
    entity_id: UUID,
    known_at: datetime,
    ordinal: int,
) -> IndustrySubjectMembershipRecord:
    return IndustrySubjectMembershipRecord(
        membership_id=UUID(f"44000000-0000-0000-0000-{ordinal:012d}"),
        industry_node_id=INDUSTRY_ID,
        subject=MemorySubjectRef(entity_id=entity_id),
        canonical_name="Early Project" if entity_id == EARLY_ENTITY_ID else "Future Project",
        entity_type="project",
        role="conversion_project",
        valid_from=date(2020, 1, 1),
        known_at=known_at,
        system_from=datetime(2026, 8, 24, tzinfo=UTC),
        confidence=1.0,
        resolution_id=UUID(f"55000000-0000-0000-0000-{ordinal:012d}"),
        evidence_fragment_ids=(UUID(f"66000000-0000-0000-0000-{ordinal:012d}"),),
    )


def _catalog() -> IndustryOrientationCatalog:
    return IndustryOrientationCatalog(
        industry=IndustryDescriptor(
            industry_node_id=INDUSTRY_ID,
            canonical_name="Synthetic Conversion",
            node_kind="industry",
        ),
        memberships=(
            _membership(
                entity_id=EARLY_ENTITY_ID,
                known_at=datetime(2021, 1, 1, tzinfo=UTC),
                ordinal=1,
            ),
            _membership(
                entity_id=FUTURE_ENTITY_ID,
                known_at=datetime(2024, 1, 1, tzinfo=UTC),
                ordinal=2,
            ),
        ),
    )


def _timeline() -> IndustrialMemoryTimeline:
    subject = MemorySubjectRef(entity_id=EARLY_ENTITY_ID)
    first = JudgmentMemoryRecord(
        judgment_id=JUDGMENT_A,
        subject=subject,
        topic_code="project.ramp",
        judgment_kind="guidance",
        target_time=TemporalExtent(kind="unknown"),
        value_kind="text",
        value_text="ramp expected",
        summary="Ramp expected.",
        known_at=datetime(2022, 1, 1, tzinfo=UTC),
        evidence_fragment_ids=(UUID("77000000-0000-0000-0000-000000000001"),),
    )
    second = first.model_copy(
        update={
            "judgment_id": JUDGMENT_B,
            "value_text": "ramp delayed",
            "summary": "Ramp now expected to be delayed.",
            "known_at": datetime(2022, 6, 1, tzinfo=UTC),
            "evidence_fragment_ids": (
                UUID("77000000-0000-0000-0000-000000000002"),
            ),
        }
    )
    counterargument = JudgmentRationaleMemoryRecord(
        rationale_id=UUID("88000000-0000-0000-0000-000000000001"),
        judgment_id=JUDGMENT_B,
        rationale_kind=JudgmentRationaleKind.COUNTERARGUMENT,
        summary="Qualification could take longer than planned.",
        evidence_fragment_id=UUID("77000000-0000-0000-0000-000000000003"),
        known_at=datetime(2022, 6, 1, tzinfo=UTC),
    )
    contradiction = JudgmentRelationMemoryRecord(
        from_judgment_id=JUDGMENT_B,
        to_judgment_id=JUDGMENT_A,
        relation_type=JudgmentRelationType.CONTRADICTS,
        reason_summary="Later guidance contradicted the earlier ramp expectation.",
        known_at=datetime(2022, 6, 1, tzinfo=UTC),
    )
    return IndustrialMemoryTimeline(
        judgments=(first, second),
        judgment_rationales=(counterargument,),
        judgment_relations=(contradiction,),
    )


def _historical_conflict() -> RealitySourceDisagreementRecord:
    subject = MemorySubjectRef(entity_id=EARLY_ENTITY_ID)
    first = RealityConflictAssertionRecord(
        assertion_id=UUID("99000000-0000-0000-0000-000000000001"),
        source_id=UUID("aa000000-0000-0000-0000-000000000001"),
        known_at=datetime(2022, 3, 1, tzinfo=UTC),
        value_kind="text",
        value={"text": "commissioning"},
        evidence_fragment_ids=(UUID("bb000000-0000-0000-0000-000000000001"),),
    )
    second = RealityConflictAssertionRecord(
        assertion_id=UUID("99000000-0000-0000-0000-000000000002"),
        source_id=UUID("aa000000-0000-0000-0000-000000000002"),
        known_at=datetime(2022, 4, 1, tzinfo=UTC),
        value_kind="text",
        value={"text": "construction"},
        evidence_fragment_ids=(UUID("bb000000-0000-0000-0000-000000000002"),),
    )
    return RealitySourceDisagreementRecord(
        conflict_case_id=UUID("cc000000-0000-0000-0000-000000000001"),
        fact_key_id=UUID("dd000000-0000-0000-0000-000000000001"),
        subject=subject,
        predicate_code="project.state",
        comparability_hash="1" * 64,
        severity="high",
        current_case_status="open",
        archive_disagreement_known_at=second.known_at,
        research_case_opened_at=datetime(2026, 8, 24, tzinfo=UTC),
        assertions=(first, second),
    )


def _current_bundle() -> CurrentResearchOpenStateBundle:
    subject = MemorySubjectRef(entity_id=EARLY_ENTITY_ID)
    recorded = datetime(2026, 8, 24, tzinfo=UTC)
    return CurrentResearchOpenStateBundle(
        disagreements=(
            MemoryDisagreementOpenRecord(
                disagreement_case_id=UUID("ee000000-0000-0000-0000-000000000001"),
                lead_id=UUID("ef000000-0000-0000-0000-000000000001"),
                subject=subject,
                lead_summary="Was commercial output stable?",
                claim_scope="project_status",
                opened_reason="Primary sources still disagree.",
                current_disposition=MemoryAuditDisposition.AUTHORITATIVE_CONFLICT,
                research_recorded_at=recorded,
            ),
        ),
        hypotheses=(
            MemoryHypothesisOpenRecord(
                assessment_id=UUID("f0000000-0000-0000-0000-000000000001"),
                lead_id=UUID("f1000000-0000-0000-0000-000000000001"),
                subject=subject,
                lead_summary="Qualification may explain the delay.",
                disposition=MemoryHypothesisDisposition.UNRESOLVED,
                direct_source_search_status=DirectSourceSearchStatus.ONGOING,
                inference_confidence=0.5,
                reasoning_summary="Research-only hypothesis.",
                research_recorded_at=recorded,
            ),
        ),
        coverage_gaps=(
            MemoryCoverageGapRecord(
                campaign_id=UUID("f2000000-0000-0000-0000-000000000001"),
                snapshot_label="latest",
                dimension_type="mechanism",
                dimension_key="qualification_delay",
                coverage_state="thin",
                notes="Model-memory coverage only.",
                research_recorded_at=recorded,
            ),
        ),
    )


async def test_default_view_keeps_current_research_out_of_historical_cutoff() -> None:
    memory = FakeMemoryReader(_timeline())
    conflicts = FakeConflictReader((_historical_conflict(),))
    current = FakeCurrentResearchReader(_current_bundle())

    view = await build_researcher_open_state_view(
        catalog_reader=FakeCatalogReader(_catalog()),
        memory_reader=memory,
        conflict_reader=conflicts,
        current_research_reader=current,
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
    )

    assert memory.last_cutoff == CUTOFF
    assert conflicts.last_cutoff == CUTOFF
    expected_subjects = {
        MemorySubjectRef(industry_node_id=INDUSTRY_ID).key,
        MemorySubjectRef(entity_id=EARLY_ENTITY_ID).key,
    }
    assert {item.key for item in memory.last_subjects} == expected_subjects
    assert {item.key for item in conflicts.last_subjects} == expected_subjects
    assert current.calls == 0
    historical = view["historical_at_cutoff"]
    assert len(historical["reality_source_disagreements"]) == 1
    assert len(historical["judgment_contradictions"]) == 1
    assert len(historical["judgment_counterarguments"]) == 1
    curation = historical["reality_source_disagreements"][0]["current_archive_curation"]
    assert curation["is_historical_market_knowledge"] is False
    overlay = view["current_research_overlay"]
    assert overlay["included"] is False
    assert overlay["disagreements"] == []
    assert overlay["hypotheses"] == []
    assert overlay["model_memory_coverage_gaps"] == []
    assert view["boundary"]["absence_of_records_does_not_create_an_unknown_state"] is True


async def test_opt_in_overlay_is_explicitly_current_and_not_cutoff_filtered() -> None:
    current = FakeCurrentResearchReader(_current_bundle())
    view = await build_researcher_open_state_view(
        catalog_reader=FakeCatalogReader(_catalog()),
        memory_reader=FakeMemoryReader(_timeline()),
        conflict_reader=FakeConflictReader((_historical_conflict(),)),
        current_research_reader=current,
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
        include_current_research=True,
    )

    assert current.calls == 1
    assert current.last_entity_ids == (EARLY_ENTITY_ID,)
    overlay = view["current_research_overlay"]
    assert overlay["included"] is True
    assert overlay["is_historical_market_knowledge"] is False
    assert overlay["cutoff_filter_applied"] is False
    assert overlay["disagreements"][0]["research_recorded_at"].startswith("2026-08-24")
    assert overlay["hypotheses"][0]["disposition"] == "unresolved"
    assert overlay["model_memory_coverage_gaps"][0]["coverage_state"] == "thin"
    assert view["boundary"]["model_memory_coverage_is_not_archive_absence"] is True
    assert view["boundary"]["not_found_is_not_false"] is True
