from __future__ import annotations

import pytest

from longcycle.application.industry_orientation import _validate_capability_declaration
from longcycle.application.research_enrichment import ResearchEnrichmentContractViolation


class BareCatalogReader:
    pass


class DeclaredCatalogReader:
    capabilities = frozenset({"deterministic_industry_subjects"})


class MalformedCatalogReader:
    capabilities = {"deterministic_industry_subjects"}


class UnknownCapabilityReader:
    capabilities = frozenset({"mystery_discovery"})


def test_missing_optional_capability_declaration_means_unsupported() -> None:
    assert _validate_capability_declaration(BareCatalogReader()) == frozenset()


def test_explicit_optional_capability_declaration_is_preserved() -> None:
    assert _validate_capability_declaration(DeclaredCatalogReader()) == frozenset(
        {"deterministic_industry_subjects"}
    )


def test_malformed_or_unknown_declared_capability_still_fails_closed() -> None:
    with pytest.raises(ResearchEnrichmentContractViolation):
        _validate_capability_declaration(MalformedCatalogReader())
    with pytest.raises(ResearchEnrichmentContractViolation):
        _validate_capability_declaration(UnknownCapabilityReader())
