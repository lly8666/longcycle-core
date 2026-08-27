from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from longcycle.domain.enums import EntityType, FactEvidenceRole
from longcycle.domain.models import FactAssertion, FactEvidenceRef, QualityComponents


ASSERTION_ID = UUID("10000000-0000-0000-0000-000000000001")
ENTITY_ID = UUID("10000000-0000-0000-0000-000000000002")
SOURCE_ID = UUID("10000000-0000-0000-0000-000000000003")
DOCUMENT_ID = UUID("10000000-0000-0000-0000-000000000004")
RUN_ID = UUID("10000000-0000-0000-0000-000000000005")
SUPPORTING_ID = UUID("10000000-0000-0000-0000-000000000006")
CONTEXT_ID = UUID("10000000-0000-0000-0000-000000000007")


def _quality() -> QualityComponents:
    return QualityComponents(
        source_quality=1.0,
        extraction_certainty=1.0,
        entity_match=1.0,
        time_unit_completeness=1.0,
        corroboration=0.5,
        freshness=1.0,
    )


def _fact(evidence: tuple[FactEvidenceRef, ...]) -> FactAssertion:
    return FactAssertion(
        id=ASSERTION_ID,
        entity_type=EntityType.PRODUCTION_LINE,
        entity_id=ENTITY_ID,
        field_name="project.first_product_status",
        value="achieved first product",
        source_id=SOURCE_ID,
        document_id=DOCUMENT_ID,
        evidence=evidence,
        extraction_run_id=RUN_ID,
        extractor_name="fact-provenance-test",
        extractor_version="1.0.0",
        confidence=1.0,
        quality=_quality(),
    )


def test_fact_assertion_preserves_typed_multi_fragment_provenance() -> None:
    fact = _fact(
        (
            FactEvidenceRef(
                evidence_fragment_id=SUPPORTING_ID,
                evidence_role=FactEvidenceRole.SUPPORTING,
            ),
            FactEvidenceRef(
                evidence_fragment_id=CONTEXT_ID,
                evidence_role=FactEvidenceRole.CONTEXT,
            ),
        )
    )

    assert [item.evidence_role for item in fact.evidence] == [
        FactEvidenceRole.SUPPORTING,
        FactEvidenceRole.CONTEXT,
    ]
    dumped = fact.model_dump(mode="python")
    assert "evidence" in dumped
    assert "evidence_fragment_id" not in dumped


def test_fact_assertion_requires_a_supporting_fragment() -> None:
    with pytest.raises(ValidationError, match="at least one supporting evidence fragment"):
        _fact(
            (
                FactEvidenceRef(
                    evidence_fragment_id=CONTEXT_ID,
                    evidence_role=FactEvidenceRole.CONTEXT,
                ),
            )
        )


def test_fact_assertion_rejects_duplicate_fragment_identity() -> None:
    with pytest.raises(ValidationError, match="evidence fragments must be unique"):
        _fact(
            (
                FactEvidenceRef(
                    evidence_fragment_id=SUPPORTING_ID,
                    evidence_role=FactEvidenceRole.SUPPORTING,
                ),
                FactEvidenceRef(
                    evidence_fragment_id=SUPPORTING_ID,
                    evidence_role=FactEvidenceRole.CONTEXT,
                ),
            )
        )


def test_fact_immutable_fingerprint_includes_full_provenance() -> None:
    one_fragment = _fact(
        (
            FactEvidenceRef(
                evidence_fragment_id=SUPPORTING_ID,
                evidence_role=FactEvidenceRole.SUPPORTING,
            ),
        )
    )
    two_fragments = _fact(
        (
            FactEvidenceRef(
                evidence_fragment_id=SUPPORTING_ID,
                evidence_role=FactEvidenceRole.SUPPORTING,
            ),
            FactEvidenceRef(
                evidence_fragment_id=CONTEXT_ID,
                evidence_role=FactEvidenceRole.CONTEXT,
            ),
        )
    )

    assert one_fragment.immutable_fingerprint != two_fragments.immutable_fingerprint
