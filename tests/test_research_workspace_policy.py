from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.application.open_state_view import build_researcher_open_state_view
from longcycle.application.research_enrichment import (
    ProviderUnavailable,
    ResearchEnrichmentDefect,
)
from longcycle.cli import _parser
from longcycle.domain.epistemic import PointInTimeMemorySnapshot
from longcycle.domain.orientation import IndustryDescriptor, IndustryOrientationCatalog


INDUSTRY_ID = UUID("10000000-0000-0000-0000-000000000001")
CUTOFF = datetime(2024, 1, 1, tzinfo=UTC)


def test_cli_defaults_to_explicit_plus_current_mode_with_historical_only_opt_out() -> None:
    default_args = _parser().parse_args(
        ["research", "open-states", str(INDUSTRY_ID), CUTOFF.isoformat()]
    )
    assert default_args.research_overlay_mode == "historical_plus_current_research"

    historical_only = _parser().parse_args(
        [
            "research",
            "open-states",
            str(INDUSTRY_ID),
            CUTOFF.isoformat(),
            "--historical-only",
        ]
    )
    assert historical_only.research_overlay_mode == "historical_only"


class _CatalogBase:
    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog:
        assert industry_node_id == INDUSTRY_ID
        return IndustryOrientationCatalog(
            industry=IndustryDescriptor(
                industry_node_id=INDUSTRY_ID,
                canonical_name="Test Industry",
                node_kind="industry",
            )
        )


class _CatalogWithExpectedUnavailableDiscovery(_CatalogBase):
    capabilities = frozenset({"deterministic_industry_subjects"})

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ):
        del industry_node_id, knowledge_cutoff
        raise ProviderUnavailable("optional discovery provider unavailable")


class _CatalogWithEmptyDiscovery(_CatalogBase):
    capabilities = frozenset({"deterministic_industry_subjects"})

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ):
        del industry_node_id, knowledge_cutoff
        return ()


class _CatalogWithDiscoveryDefect(_CatalogBase):
    capabilities = frozenset({"deterministic_industry_subjects"})

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ):
        del industry_node_id, knowledge_cutoff
        raise RuntimeError("SQL shape mismatch")


class _CatalogDeclaresNoDiscovery(_CatalogBase):
    capabilities = frozenset()


class _CatalogDeclaresSupportButMissesMethod(_CatalogBase):
    capabilities = frozenset({"deterministic_industry_subjects"})


class _EmptyHistoricalMemory:
    async def snapshot(self, subjects, *, knowledge_cutoff: datetime) -> PointInTimeMemorySnapshot:
        del subjects
        return PointInTimeMemorySnapshot(knowledge_cutoff=knowledge_cutoff)


class _NoHistoricalConflicts:
    async def historical_source_disagreements(self, subjects, *, knowledge_cutoff: datetime):
        del subjects, knowledge_cutoff
        return ()


class _ExpectedUnavailableCurrentResearch:
    async def current_open_states(self, *, industry_node_id: UUID):
        del industry_node_id
        raise ProviderUnavailable("current model provider unavailable")


class _EmptyCurrentResearch:
    async def current_open_states(self, *, industry_node_id: UUID):
        from longcycle.domain.open_states import CurrentResearchOpenStateBundle

        del industry_node_id
        return CurrentResearchOpenStateBundle()


class _DefectiveCurrentResearch:
    async def current_open_states(self, *, industry_node_id: UUID):
        del industry_node_id
        raise TypeError("unexpected provider payload")


async def test_expected_optional_unavailability_degrades_without_inventing_world_state() -> None:
    view = await build_researcher_open_state_view(
        catalog_reader=_CatalogWithExpectedUnavailableDiscovery(),
        memory_reader=_EmptyHistoricalMemory(),
        conflict_reader=_NoHistoricalConflicts(),
        current_research_reader=_ExpectedUnavailableCurrentResearch(),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
        research_overlay_mode="historical_plus_current_research",
    )

    assert view["research_overlay_mode"] == "historical_plus_current_research"
    assert view["historical_market_knowledge"]["section_label"] == "Historical Market Knowledge"
    assert view["historical_market_knowledge"]["as_of"] == CUTOFF.isoformat()
    overlay = view["current_research_overlay"]
    assert overlay["section_label"] == "TODAY'S RESEARCH OVERLAY"
    assert overlay["historical_cutoff_applies"] is False
    assert CUTOFF.isoformat() in overlay["warning"]
    assert overlay["included"] is True
    assert overlay["degraded"] is True
    assert overlay["available"] is False
    assert overlay["availability_status"] == "UNAVAILABLE_EXPECTED"
    assert view["research_enrichment"]["availability_status"] == "UNAVAILABLE_EXPECTED"
    assert {item["component"] for item in view["research_enrichment"]["failures"]} == {
        "deterministic_industry_subjects",
        "current_research_open_states",
    }
    assert {item["reason"] for item in view["research_enrichment"]["failures"]} == {
        "provider_unavailable"
    }

    coverage = view["archive_research_coverage"]
    assert len(coverage) == 1
    assert coverage[0]["archive_status"] == "no_grounded_record"
    assert coverage[0]["world_state_inference"] == "none"
    assert "absence is not a claim" in coverage[0]["research_interpretation"]


async def test_empty_optional_result_is_available_not_degraded() -> None:
    view = await build_researcher_open_state_view(
        catalog_reader=_CatalogWithEmptyDiscovery(),
        memory_reader=_EmptyHistoricalMemory(),
        conflict_reader=_NoHistoricalConflicts(),
        current_research_reader=_EmptyCurrentResearch(),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
        research_overlay_mode="historical_plus_current_research",
    )

    assert view["research_enrichment"]["availability_status"] == "AVAILABLE"
    assert view["research_enrichment"]["status"] == "complete"
    assert view["research_enrichment"]["failures"] == []
    components = {item["component"]: item for item in view["research_enrichment"]["components"]}
    assert components["deterministic_industry_subjects"] == {
        "component": "deterministic_industry_subjects",
        "status": "AVAILABLE",
        "result_count": 0,
        "reason": None,
        "message": None,
    }
    assert components["current_research_open_states"]["status"] == "AVAILABLE"
    assert components["current_research_open_states"]["result_count"] == 0


async def test_explicitly_unsupported_capability_is_expected_unavailable() -> None:
    view = await build_researcher_open_state_view(
        catalog_reader=_CatalogDeclaresNoDiscovery(),
        memory_reader=_EmptyHistoricalMemory(),
        conflict_reader=_NoHistoricalConflicts(),
        current_research_reader=_EmptyCurrentResearch(),
        industry_node_id=INDUSTRY_ID,
        knowledge_cutoff=CUTOFF,
        research_overlay_mode="historical_only",
    )
    component = view["research_enrichment"]["components"][0]
    assert component["component"] == "deterministic_industry_subjects"
    assert component["status"] == "UNAVAILABLE_EXPECTED"
    assert component["reason"] == "capability_not_supported"
    assert view["current_research_overlay"]["included"] is False


async def test_optional_discovery_programming_defect_is_not_silently_degraded() -> None:
    with pytest.raises(ResearchEnrichmentDefect, match="SQL shape mismatch"):
        await build_researcher_open_state_view(
            catalog_reader=_CatalogWithDiscoveryDefect(),
            memory_reader=_EmptyHistoricalMemory(),
            conflict_reader=_NoHistoricalConflicts(),
            current_research_reader=_EmptyCurrentResearch(),
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=CUTOFF,
            research_overlay_mode="historical_only",
        )


async def test_declared_supported_capability_missing_method_is_a_defect() -> None:
    with pytest.raises(ResearchEnrichmentDefect, match="deterministic_industry_subjects"):
        await build_researcher_open_state_view(
            catalog_reader=_CatalogDeclaresSupportButMissesMethod(),
            memory_reader=_EmptyHistoricalMemory(),
            conflict_reader=_NoHistoricalConflicts(),
            current_research_reader=_EmptyCurrentResearch(),
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=CUTOFF,
            research_overlay_mode="historical_only",
        )


async def test_current_overlay_programming_defect_is_not_silently_degraded() -> None:
    with pytest.raises(ResearchEnrichmentDefect, match="unexpected provider payload"):
        await build_researcher_open_state_view(
            catalog_reader=_CatalogWithEmptyDiscovery(),
            memory_reader=_EmptyHistoricalMemory(),
            conflict_reader=_NoHistoricalConflicts(),
            current_research_reader=_DefectiveCurrentResearch(),
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=CUTOFF,
            research_overlay_mode="historical_plus_current_research",
        )
