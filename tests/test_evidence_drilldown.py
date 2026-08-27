from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.application.evidence_drilldown import build_researcher_evidence_drilldown
from longcycle.domain.evidence import EvidenceDrilldownRecord


FRAGMENT_ID = UUID("10000000-0000-0000-0000-000000000001")
DOCUMENT_VERSION_ID = UUID("20000000-0000-0000-0000-000000000001")
RAW_DOCUMENT_VERSION_ID = UUID("20000000-0000-0000-0000-000000000002")
LOGICAL_DOCUMENT_ID = UUID("30000000-0000-0000-0000-000000000001")
PUBLISHER_ID = UUID("40000000-0000-0000-0000-000000000001")


class FakeEvidenceReader:
    def __init__(self, record: EvidenceDrilldownRecord | None) -> None:
        self.record = record

    async def evidence_fragment(self, fragment_id: UUID) -> EvidenceDrilldownRecord | None:
        if self.record is None or self.record.evidence_fragment_id != fragment_id:
            return None
        return self.record


def _record(*, known_at: datetime) -> EvidenceDrilldownRecord:
    return EvidenceDrilldownRecord(
        evidence_fragment_id=FRAGMENT_ID,
        document_version_id=DOCUMENT_VERSION_ID,
        locator="page:7",
        excerpt="Management expected qualification to finish in the second half.",
        fragment_sha256="1" * 64,
        logical_document_id=LOGICAL_DOCUMENT_ID,
        canonical_url="https://example.invalid/filing.pdf",
        external_id="filing-2022-01",
        logical_title="Synthetic filing",
        document_type="filing",
        publisher_id=PUBLISHER_ID,
        publisher_name="Synthetic Issuer",
        publisher_domain="example.invalid",
        publisher_source_kind="company",
        publisher_quality_grade="A",
        independence_cluster="synthetic-issuer",
        version_ordinal=1,
        first_known_at=known_at,
        published_at=known_at,
        first_retrieved_at=known_at,
        requested_url="https://example.invalid/filing.pdf",
        retrieval_url="https://example.invalid/filing.pdf",
        retrieval_connector_name="Synthetic connector",
        source_media_type="application/pdf",
        current_source_capture_state="materialized",
        source_locator_metadata={
            "raw_source_materialized": True,
            "content_verification_mode": "page_text_read",
            "claim_relevant_content_preserved": True,
        },
        raw_materialized_document_version_id=RAW_DOCUMENT_VERSION_ID,
        representation_kind="readable_representation",
        preserved_content_sha256="2" * 64,
        preserved_content_type="text/plain",
    )


@pytest.mark.asyncio
async def test_drilldown_preserves_representation_identity_after_later_raw_materialization() -> None:
    known_at = datetime(2022, 6, 1, 12, 0, tzinfo=UTC)
    result = await build_researcher_evidence_drilldown(
        reader=FakeEvidenceReader(_record(known_at=known_at)),
        evidence_fragment_id=FRAGMENT_ID,
        knowledge_cutoff=datetime(2023, 1, 1, tzinfo=UTC),
    )

    assert result["schema_version"] == "longcycle-researcher-evidence-drilldown/v1"
    assert result["evidence"]["evidence_fragment_id"] == str(FRAGMENT_ID)
    assert result["evidence"]["locator"] == "page:7"
    assert result["source"]["publisher"]["canonical_name"] == "Synthetic Issuer"
    assert result["source"]["historical_timing"]["first_known_at"] == known_at.isoformat()
    assert result["source"]["evidence_representation"]["kind"] == "readable_representation"
    assert result["source"]["current_preservation"]["source_capture_state"] == "materialized"
    assert (
        result["source"]["current_preservation"]["raw_materialized_document_version_id"]
        == str(RAW_DOCUMENT_VERSION_ID)
    )
    assert result["source"]["evidence_representation"]["sha256"] == "2" * 64
    assert all(result["boundary"].values())


@pytest.mark.asyncio
async def test_future_evidence_is_rejected_at_historical_cutoff() -> None:
    record = _record(known_at=datetime(2024, 6, 1, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="not knowable"):
        await build_researcher_evidence_drilldown(
            reader=FakeEvidenceReader(record),
            evidence_fragment_id=FRAGMENT_ID,
            knowledge_cutoff=datetime(2023, 1, 1, tzinfo=UTC),
        )


@pytest.mark.asyncio
async def test_unknown_evidence_id_fails_closed() -> None:
    with pytest.raises(KeyError):
        await build_researcher_evidence_drilldown(
            reader=FakeEvidenceReader(None),
            evidence_fragment_id=FRAGMENT_ID,
            knowledge_cutoff=datetime(2023, 1, 1, tzinfo=UTC),
        )
