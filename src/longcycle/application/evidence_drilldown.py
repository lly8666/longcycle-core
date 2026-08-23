from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.models import require_aware_datetime
from longcycle.ports.evidence import EvidenceDrilldownReader


async def build_researcher_evidence_drilldown(
    *,
    reader: EvidenceDrilldownReader,
    evidence_fragment_id: UUID,
    knowledge_cutoff: datetime,
) -> dict[str, Any]:
    """Render one claim-scoped Evidence fragment without inventing source semantics."""

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    record = await reader.evidence_fragment(evidence_fragment_id)
    if record is None:
        raise KeyError(evidence_fragment_id)
    if record.first_known_at > checked:
        raise ValueError("Evidence fragment is not knowable at the requested cutoff")

    return {
        "schema_version": "longcycle-researcher-evidence-drilldown/v1",
        "knowledge_cutoff": checked.isoformat(),
        "evidence": {
            "evidence_fragment_id": str(record.evidence_fragment_id),
            "locator": record.locator,
            "excerpt": record.excerpt,
            "structured_payload": record.structured_payload,
            "fragment_sha256": record.fragment_sha256,
            "artifact_id": str(record.artifact_id) if record.artifact_id is not None else None,
        },
        "source": {
            "logical_document_id": str(record.logical_document_id),
            "document_version_id": str(record.document_version_id),
            "canonical_url": record.canonical_url,
            "external_id": record.external_id,
            "logical_title": record.logical_title,
            "document_type": record.document_type,
            "publisher": {
                "publisher_id": str(record.publisher_id) if record.publisher_id is not None else None,
                "canonical_name": record.publisher_name,
                "publisher_domain": record.publisher_domain,
                "source_kind": record.publisher_source_kind,
                "quality_grade": record.publisher_quality_grade,
                "independence_cluster": record.independence_cluster,
            },
            "historical_timing": {
                "published_at": (
                    record.published_at.isoformat() if record.published_at is not None else None
                ),
                "first_known_at": record.first_known_at.isoformat(),
                "first_retrieved_at": record.first_retrieved_at.isoformat(),
            },
            "retrieval": {
                "requested_url": record.requested_url,
                "retrieval_url": record.retrieval_url,
                "connector_name": record.retrieval_connector_name,
            },
            "evidence_representation": {
                "kind": record.representation_kind,
                "version_ordinal": record.version_ordinal,
                "sha256": record.preserved_content_sha256,
                "content_type": record.preserved_content_type,
            },
            "current_preservation": {
                "source_media_type": record.source_media_type,
                "source_capture_state": record.current_source_capture_state,
                "raw_materialized_document_version_id": (
                    str(record.raw_materialized_document_version_id)
                    if record.raw_materialized_document_version_id is not None
                    else None
                ),
                "source_locator_metadata": record.source_locator_metadata,
            },
        },
        "boundary": {
            "evidence_visibility_uses_source_first_known_at": True,
            "current_preservation_state_is_operational_not_historical_market_knowledge": True,
            "preserved_content_sha256_is_not_automatically_a_raw_source_hash": True,
            "readable_representation_is_not_relabelled_raw_after_later_materialization": True,
            "locator_only_never_becomes_claim_evidence": True,
            "presentation_infers_no_source_authority_or_claim_truth": True,
        },
    }
