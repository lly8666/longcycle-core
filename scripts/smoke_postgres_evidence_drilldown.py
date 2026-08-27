from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import UTC, datetime

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import EvidenceFragment, RawPayload, SourceDocument


KNOWN_AT = datetime(2022, 6, 1, 12, 0, tzinfo=UTC)
CUTOFF = datetime(2023, 1, 1, 0, 0, tzinfo=UTC)
EARLY_CUTOFF = datetime(2021, 1, 1, 0, 0, tzinfo=UTC)
RAW_RETRIEVED_AT = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)
CANONICAL_URL = "https://evidence-drilldown-smoke.longcycle.invalid/filing.pdf"
EXTERNAL_ID = "evidence-drilldown-smoke-filing"
EXCERPT = "Synthetic filing expected qualification to finish in the second half."


def _document(
    *,
    source_id,
    payload: RawPayload,
) -> SourceDocument:
    return SourceDocument.from_payload(
        source_id=source_id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id=EXTERNAL_ID,
        title="Synthetic Evidence drilldown filing",
        published_at=KNOWN_AT,
        first_known_at=KNOWN_AT,
        metadata={"synthetic_test_fixture": True},
    )


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="Synthetic Evidence drilldown source",
        publisher_domain="evidence-drilldown-smoke.longcycle.invalid",
        kind=SourceKind.COMPANY,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    repository = PostgresResearchRepository(dsn, bucket_name="evidence-drilldown-smoke")
    try:
        representation_payload = RawPayload(
            content=(EXCERPT + "\n").encode(),
            content_type="text/plain",
            canonical_url=CANONICAL_URL,
            headers={
                "x-longcycle-raw-source-materialized": "false",
                "x-longcycle-source-capture-state": "content_verified",
                "x-longcycle-source-media-type": "application/pdf",
                "x-longcycle-content-verification-mode": "synthetic_page_text",
                "x-longcycle-claim-content-preserved": "true",
            },
            retrieved_at=KNOWN_AT,
        )
        representation_document = await repository.save_document(
            _document(source_id=source.id, payload=representation_payload)
        )
        evidence = EvidenceFragment.create(
            representation_document.id,
            "page:7",
            EXCERPT,
        )
        await repository.save_evidence((evidence,))

        raw_payload = RawPayload(
            content=b"%PDF-1.7\nSynthetic raw upstream PDF bytes for Evidence drilldown smoke.\n",
            content_type="application/pdf",
            canonical_url=CANONICAL_URL,
            headers={"x-longcycle-raw-source-materialized": "true"},
            retrieved_at=RAW_RETRIEVED_AT,
        )
        raw_document = await repository.save_document(
            _document(source_id=source.id, payload=raw_payload)
        )
    finally:
        await repository.close()

    command = [
        "longcycle",
        "--json",
        "research",
        "evidence",
        str(evidence.id),
        CUTOFF.isoformat(),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    outer = json.loads(completed.stdout)
    if outer.get("ok") is not True:
        raise AssertionError(outer)
    result = outer["result"]
    if result["schema_version"] != "longcycle-researcher-evidence-drilldown/v1":
        raise AssertionError(result)
    if result["evidence"]["evidence_fragment_id"] != str(evidence.id):
        raise AssertionError(result)
    if result["evidence"]["excerpt"] != EXCERPT:
        raise AssertionError(result)
    if result["source"]["publisher"]["canonical_name"] != source.name:
        raise AssertionError(result)
    if result["source"]["historical_timing"]["first_known_at"] != KNOWN_AT.isoformat():
        raise AssertionError(result)
    if result["source"]["evidence_representation"]["kind"] != "readable_representation":
        raise AssertionError("later raw materialization relabelled the Evidence representation")
    if result["source"]["evidence_representation"]["content_type"] != "text/plain":
        raise AssertionError(result)
    current = result["source"]["current_preservation"]
    if current["source_capture_state"] != "materialized":
        raise AssertionError(current)
    if current["source_media_type"] != "application/pdf":
        raise AssertionError(current)
    if current["raw_materialized_document_version_id"] != str(raw_document.id):
        raise AssertionError(current)
    if result["source"]["document_version_id"] != str(representation_document.id):
        raise AssertionError(result)
    if not all(result["boundary"].values()):
        raise AssertionError(result["boundary"])

    early_command = [
        "longcycle",
        "--json",
        "research",
        "evidence",
        str(evidence.id),
        EARLY_CUTOFF.isoformat(),
    ]
    early = subprocess.run(
        early_command,
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if early.returncode == 0:
        raise AssertionError("future-known Evidence crossed the historical cutoff")
    early_outer = json.loads(early.stdout)
    if early_outer.get("ok") is not False or "not knowable" not in early_outer.get("error", ""):
        raise AssertionError(early_outer)

    print("POSTGRES_EVIDENCE_DRILLDOWN_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
