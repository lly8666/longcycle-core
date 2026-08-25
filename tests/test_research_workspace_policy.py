from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from longcycle.application.open_state_view import build_researcher_open_state_view
from longcycle.cli import _parser
from longcycle.domain.epistemic import PointInTimeMemorySnapshot
from longcycle.domain.orientation import IndustryDescriptor, IndustryOrientationCatalog


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
CUTOFF = datetime(2024, 1, 1, tzinfo=UTC)


def test_current_research_workspace_defaults_on_with_explicit_historical_only_opt_out() -> None:
    default_args = _parser().parse_args(
        ["research", "open-states", str(INDUSTRY_ID), CUTOFF.isoformat()]
    )
    assert default_args.include_current_research is True

    historical_only = _parser().parse_args(
        [
            "research",
            "open-states",
            str(INDUSTRY_ID),
            CUTOFF.isoformat(),
            "--historical-only",
        ]
    )
    assert historical_only.include_current_research is False


class _CatalogWithBrokenOptionalDiscovery:
    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog:
        assert industry_node_id == INDUSTRY_ID
        return IndustryOrientationCatalog(
            industry=IndustryDescriptor(
                industry_node_id=INDUSTRY_ID,
                canonical_name="Test Industry",
                node_kind="industry",
            )
        )

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ):
        del industry_node_id, knowledge_cutoff
        raise RuntimeError("optional discovery service unavailable")


class _EmptyHistoricalMemory:
    async def snapshot(self, subjects, *, knowledge_cutoff: datetime) -> PointInTimeMemorySnapshot:
        del subjects
        return PointInTimeMemorySnapshot(knowledge_cutoff=knowledge_cutoff)


class _NoHistoricalConflicts:
    async def historical_source_disagreements(self, subjects, *, knowledge_cutoff: datetime):
        del subjects, knowledge_cutoff
        return ()


class _BrokenCurrentResearch:
    async def current_open_states(self, *, industry_node_id: UUID):
        del industry_node_id
        raise RuntimeError("current model workspace unavailable")


async def test_optional_research_failures_degrade_without_inventing_world_state() -> None:
    view = await build_researcher_open_state_view(
        catalog_reader=_CatalogWithBrokenOptionalDiscovery(),
        memory_reader=_EmptyHistoricalMemory(),
        conflict_reader=_NoHistoricalConflicts(),
        current_research_reader=_BrokenCurrentResearch(),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
        include_current_research=True,
    )

    assert view["historical_at_cutoff"] == {
        "reality_source_disagreements": [],
        "judgment_contradictions": [],
        "judgment_counterarguments": [],
    }
    assert view["current_research_overlay"]["included"] is True
    assert view["current_research_overlay"]["degraded"] is True
    assert view["current_research_overlay"]["available"] is False
    assert view["research_enrichment"]["status"] == "degraded"
    assert {item["component"] for item in view["research_enrichment"]["failures"]} == {
        "deterministic_industry_subjects",
        "current_research_open_states",
    }

    coverage = view["archive_research_coverage"]
    assert len(coverage) == 1
    assert coverage[0]["archive_status"] == "no_grounded_record"
    assert coverage[0]["world_state_inference"] == "none"
    assert "absence is not a claim" in coverage[0]["research_interpretation"]
    assert view["boundary"]["historical_memory_and_conflict_reads_fail_closed"] is True
    assert view["boundary"]["optional_research_enrichments_degrade_gracefully"] is True
