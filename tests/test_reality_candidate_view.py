from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from longcycle.application.reality_candidate_view import build_researcher_reality_candidate_view
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.reality_candidates import RealityResearchCandidate


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
ENTITY_ID = UUID("20000000-0000-0000-0000-000000000001")
CUTOFF = datetime(2023, 1, 1, tzinfo=UTC)


class FakeCandidateReader:
    def __init__(self, candidates: tuple[RealityResearchCandidate, ...]) -> None:
        self.candidates = candidates

    async def candidates_for_industry(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[RealityResearchCandidate, ...]:
        assert industry_node_id == INDUSTRY_ID
        assert knowledge_cutoff == CUTOFF
        return self.candidates


def _candidate(
    *,
    assertion_id: str,
    status: str,
    source_known_at: datetime,
    decision_known_at: datetime,
    evidence_id: str,
) -> RealityResearchCandidate:
    return RealityResearchCandidate(
        assertion_id=UUID(assertion_id),
        industry_node_id=INDUSTRY_ID,
        subject=MemorySubjectRef(entity_id=ENTITY_ID),
        canonical_name="Example Producer",
        entity_type="organization",
        predicate_code="project.state",
        status=status,
        raw_value="qualification still under review",
        value_kind="text",
        valid_time_kind="unknown",
        source_known_at=source_known_at,
        decision_known_at=decision_known_at,
        confidence=0.7,
        reconciliation_score=0.62,
        reason_codes=("insufficient_dimension_completeness",),
        evidence_fragment_ids=(UUID(evidence_id),),
    )


async def test_review_and_quarantined_assertions_are_visible_but_never_canonical() -> None:
    review = _candidate(
        assertion_id="30000000-0000-0000-0000-000000000001",
        status="review",
        source_known_at=datetime(2022, 6, 1, tzinfo=UTC),
        decision_known_at=datetime(2022, 6, 2, tzinfo=UTC),
        evidence_id="40000000-0000-0000-0000-000000000001",
    )
    quarantined = _candidate(
        assertion_id="30000000-0000-0000-0000-000000000002",
        status="quarantined",
        source_known_at=datetime(2022, 7, 1, tzinfo=UTC),
        decision_known_at=datetime(2022, 7, 2, tzinfo=UTC),
        evidence_id="40000000-0000-0000-0000-000000000002",
    )

    view = await build_researcher_reality_candidate_view(
        reader=FakeCandidateReader((review, quarantined)),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
    )

    assert view["candidate_count"] == 2
    assert [item["status"] for item in view["candidates"]] == ["review", "quarantined"]
    for item in view["candidates"]:
        assert item["canonical"] is False
        assert item["research_only"] is True
        assert item["evidence_fragment_ids"]
        assert item["reason_codes"] == ["insufficient_dimension_completeness"]
    assert view["boundary"]["canonical_reality_unchanged"] is True
    assert view["boundary"]["no_threshold_relaxation"] is True


async def test_candidate_view_does_not_backdate_future_source_or_reconciliation_decision() -> None:
    future_source = _candidate(
        assertion_id="30000000-0000-0000-0000-000000000003",
        status="review",
        source_known_at=datetime(2024, 1, 1, tzinfo=UTC),
        decision_known_at=datetime(2024, 1, 2, tzinfo=UTC),
        evidence_id="40000000-0000-0000-0000-000000000003",
    )
    future_decision = _candidate(
        assertion_id="30000000-0000-0000-0000-000000000004",
        status="quarantined",
        source_known_at=datetime(2022, 1, 1, tzinfo=UTC),
        decision_known_at=datetime(2024, 1, 1, tzinfo=UTC),
        evidence_id="40000000-0000-0000-0000-000000000004",
    )

    view = await build_researcher_reality_candidate_view(
        reader=FakeCandidateReader((future_source, future_decision)),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
    )

    assert view["candidate_count"] == 0
    assert view["candidates"] == []
    assert view["boundary"]["source_known_at_respects_cutoff"] is True
    assert view["boundary"]["reconciliation_decision_known_at_respects_cutoff"] is True
