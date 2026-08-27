from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from uuid import UUID

from longcycle.application.industry_orientation import build_researcher_industry_orientation
from longcycle.domain.epistemic import (
    CanonicalRealityRecord,
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    MemorySubjectRef,
    OutcomeMemoryRecord,
    PointInTimeMemorySnapshot,
    TemporalExtent,
    snapshot_from_timeline,
)
from longcycle.domain.orientation import (
    IndustryDescriptor,
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    IndustrySubjectMembershipRecord,
)


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
EARLY_ENTITY_ID = UUID("20000000-0000-0000-0000-000000000001")
FUTURE_ENTITY_ID = UUID("20000000-0000-0000-0000-000000000002")
REALITY_ID = UUID("30000000-0000-0000-0000-000000000001")
JUDGMENT_ID = UUID("40000000-0000-0000-0000-000000000001")
OUTCOME_ID = UUID("50000000-0000-0000-0000-000000000001")
CUTOFF = datetime(2023, 1, 1, tzinfo=UTC)


class FakeCatalogReader:
    capabilities = frozenset({"deterministic_industry_subjects"})

    def __init__(
        self,
        catalog: IndustryOrientationCatalog,
        discoveries: tuple[IndustrySubjectDiscoveryRecord, ...] = (),
    ) -> None:
        self.catalog = catalog
        self.discoveries = discoveries

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog:
        assert industry_node_id == INDUSTRY_ID
        return self.catalog

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[IndustrySubjectDiscoveryRecord, ...]:
        assert industry_node_id == INDUSTRY_ID
        assert knowledge_cutoff == CUTOFF
        return self.discoveries


class FakeMemoryReader:
    def __init__(self, timeline: IndustrialMemoryTimeline) -> None:
        self.timeline_value = timeline
        self.last_cutoff: datetime | None = None
        self.last_subjects: tuple[MemorySubjectRef, ...] = ()

    def _for_subjects(self, subjects: Sequence[MemorySubjectRef]) -> IndustrialMemoryTimeline:
        subject_keys = {item.key for item in subjects}
        judgments = tuple(
            item for item in self.timeline_value.judgments if item.subject.key in subject_keys
        )
        judgment_ids = {item.judgment_id for item in judgments}
        return IndustrialMemoryTimeline(
            reality=tuple(
                item for item in self.timeline_value.reality if item.subject.key in subject_keys
            ),
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
            outcomes=tuple(
                item for item in self.timeline_value.outcomes if item.subject.key in subject_keys
            ),
        )

    async def timeline(
        self,
        subjects: Sequence[MemorySubjectRef],
    ) -> IndustrialMemoryTimeline:
        return self._for_subjects(subjects)

    async def snapshot(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> PointInTimeMemorySnapshot:
        self.last_subjects = tuple(subjects)
        self.last_cutoff = knowledge_cutoff
        return snapshot_from_timeline(
            self._for_subjects(subjects),
            knowledge_cutoff=knowledge_cutoff,
        )


def _membership(
    *,
    membership_id: str,
    entity_id: UUID,
    name: str,
    known_at: datetime,
    evidence_id: str,
) -> IndustrySubjectMembershipRecord:
    return IndustrySubjectMembershipRecord(
        membership_id=UUID(membership_id),
        industry_node_id=INDUSTRY_ID,
        subject=MemorySubjectRef(entity_id=entity_id),
        canonical_name=name,
        entity_type="project",
        role="conversion_project",
        valid_from=date(2020, 1, 1),
        known_at=known_at,
        system_from=datetime(2026, 8, 24, tzinfo=UTC),
        confidence=0.9,
        resolution_id=UUID(membership_id.replace("60000000", "70000000")),
        evidence_fragment_ids=(UUID(evidence_id),),
    )


def _discovery(
    *,
    basis_id: str,
    entity_id: UUID,
    name: str,
    known_at: datetime,
    evidence_id: str,
    basis_kind: str = "accepted_reality",
) -> IndustrySubjectDiscoveryRecord:
    return IndustrySubjectDiscoveryRecord(
        industry_node_id=INDUSTRY_ID,
        subject=MemorySubjectRef(entity_id=entity_id),
        canonical_name=name,
        entity_type="project",
        basis_kind=basis_kind,
        basis_id=UUID(basis_id),
        semantic_code="project.state",
        known_at=known_at,
        evidence_fragment_ids=(UUID(evidence_id),),
    )


def _timeline() -> IndustrialMemoryTimeline:
    early_subject = MemorySubjectRef(entity_id=EARLY_ENTITY_ID)
    future_subject = MemorySubjectRef(entity_id=FUTURE_ENTITY_ID)
    reality = CanonicalRealityRecord(
        canonical_fact_version_id=REALITY_ID,
        subject=early_subject,
        predicate_code="project.state",
        value_kind="text",
        value_text="commissioning",
        valid_time=TemporalExtent(kind="unknown"),
        known_at=datetime(2022, 6, 1, tzinfo=UTC),
        confidence=0.95,
        evidence_fragment_ids=(UUID("80000000-0000-0000-0000-000000000001"),),
    )
    judgment = JudgmentMemoryRecord(
        judgment_id=JUDGMENT_ID,
        subject=early_subject,
        topic_code="project.ramp",
        judgment_kind="guidance",
        target_time=TemporalExtent(kind="unknown"),
        value_kind="text",
        value_text="ramp expected",
        summary="Management expected ramp progress.",
        known_at=datetime(2022, 7, 1, tzinfo=UTC),
        evidence_fragment_ids=(UUID("80000000-0000-0000-0000-000000000002"),),
    )
    future_outcome = OutcomeMemoryRecord(
        evaluation_id=OUTCOME_ID,
        judgment_id=JUDGMENT_ID,
        subject=early_subject,
        canonical_fact_version_id=REALITY_ID,
        outcome_evidence_fragment_id=UUID("80000000-0000-0000-0000-000000000003"),
        evaluation_status="realized",
        occurrence_time=TemporalExtent(kind="unknown"),
        known_at=datetime(2024, 1, 1, tzinfo=UTC),
        timing_relation="not_comparable",
        evaluator_name="test",
        evaluator_version="1",
    )
    future_reality = reality.model_copy(
        update={
            "canonical_fact_version_id": UUID("30000000-0000-0000-0000-000000000002"),
            "subject": future_subject,
            "known_at": datetime(2022, 8, 1, tzinfo=UTC),
        }
    )
    return IndustrialMemoryTimeline(
        reality=(reality, future_reality),
        judgments=(judgment,),
        outcomes=(future_outcome,),
    )


async def test_orientation_starts_from_industry_without_leaking_future_membership_or_outcome() -> None:
    catalog = IndustryOrientationCatalog(
        industry=IndustryDescriptor(
            industry_node_id=INDUSTRY_ID,
            canonical_name="Lithium conversion",
            node_kind="industry",
        ),
        memberships=(
            _membership(
                membership_id="60000000-0000-0000-0000-000000000001",
                entity_id=EARLY_ENTITY_ID,
                name="Early Project",
                known_at=datetime(2021, 1, 1, tzinfo=UTC),
                evidence_id="90000000-0000-0000-0000-000000000001",
            ),
            _membership(
                membership_id="60000000-0000-0000-0000-000000000002",
                entity_id=FUTURE_ENTITY_ID,
                name="Future-known Project",
                known_at=datetime(2024, 1, 1, tzinfo=UTC),
                evidence_id="90000000-0000-0000-0000-000000000002",
            ),
        ),
    )
    memory = FakeMemoryReader(_timeline())

    view = await build_researcher_industry_orientation(
        catalog_reader=FakeCatalogReader(catalog),
        memory_reader=memory,
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
    )

    assert memory.last_cutoff == CUTOFF
    assert {item.key for item in memory.last_subjects} == {
        MemorySubjectRef(industry_node_id=INDUSTRY_ID).key,
        MemorySubjectRef(entity_id=EARLY_ENTITY_ID).key,
    }
    assert [row["subject_id"] for row in view["subjects"]] == [str(EARLY_ENTITY_ID)]
    subject = view["subjects"][0]
    assert subject["canonical_name"] == "Early Project"
    assert subject["discovery_certainty"] == "direct"
    assert subject["discovery_bases"][0]["basis_kind"] == "industry_membership"
    assert subject["memory_counts"] == {"reality": 1, "judgments": 1, "outcomes": 0}
    assert subject["trajectory_replay"] == {"subject_id": str(EARLY_ENTITY_ID)}
    assert subject["evidence_fragment_ids"] == [
        "80000000-0000-0000-0000-000000000001",
        "80000000-0000-0000-0000-000000000002",
        "90000000-0000-0000-0000-000000000001",
    ]
    assert view["explicit_open_states"] == []
    assert view["boundary"]["memory_visibility_delegated_to_epistemic_snapshot"] is True
    assert view["boundary"]["system_from_is_not_historical_known_at"] is True
    assert view["boundary"]["presentation_invents_no_unknown_or_controversy"] is True


async def test_grounded_industry_scoped_reality_is_discoverable_without_membership() -> None:
    catalog = IndustryOrientationCatalog(
        industry=IndustryDescriptor(
            industry_node_id=INDUSTRY_ID,
            canonical_name="Lithium conversion",
            node_kind="industry",
        ),
    )
    discoveries = (
        _discovery(
            basis_id="30000000-0000-0000-0000-000000000001",
            entity_id=EARLY_ENTITY_ID,
            name="Early Project",
            known_at=datetime(2022, 6, 1, tzinfo=UTC),
            evidence_id="80000000-0000-0000-0000-000000000001",
        ),
        _discovery(
            basis_id="30000000-0000-0000-0000-000000000002",
            entity_id=FUTURE_ENTITY_ID,
            name="Future Project",
            known_at=datetime(2024, 1, 1, tzinfo=UTC),
            evidence_id="80000000-0000-0000-0000-000000000004",
        ),
    )
    memory = FakeMemoryReader(_timeline())

    view = await build_researcher_industry_orientation(
        catalog_reader=FakeCatalogReader(catalog, discoveries),
        memory_reader=memory,
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
    )

    assert {item.key for item in memory.last_subjects} == {
        MemorySubjectRef(industry_node_id=INDUSTRY_ID).key,
        MemorySubjectRef(entity_id=EARLY_ENTITY_ID).key,
    }
    assert len(view["subjects"]) == 1
    subject = view["subjects"][0]
    assert subject["subject_id"] == str(EARLY_ENTITY_ID)
    assert subject["discovery_certainty"] == "entailed"
    assert subject["memberships"] == []
    assert subject["discovery_bases"] == [
        {
            "certainty": "entailed",
            "basis_kind": "accepted_reality",
            "basis_id": str(REALITY_ID),
            "semantic_code": "project.state",
            "known_at": datetime(2022, 6, 1, tzinfo=UTC).isoformat(),
            "entailment_rule": "explicit_industry_scope",
            "evidence_fragment_ids": ["80000000-0000-0000-0000-000000000001"],
        }
    ]
    assert subject["memory_counts"] == {"reality": 1, "judgments": 1, "outcomes": 0}
    assert view["boundary"]["researcher_discovery_allows_deterministic_entailment"] is True
    assert view["boundary"]["entailed_discovery_does_not_create_membership_or_role"] is True
