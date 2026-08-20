from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from longcycle.domain.models import ExtractionEnvelope, SourceDocument, canonical_json, stable_uuid


@dataclass(frozen=True, slots=True)
class ExtractionTarget:
    industry_ids: tuple[UUID, ...] = ()
    predicate_allowlist: tuple[str, ...] = ()
    schema_version: str = "fact-v1"
    prompt_version: str = "extract-v1"
    risk_tier: str = "low"


class ModelGateway(Protocol):
    extractor_name: str
    extractor_version: str
    model_name: str | None

    async def extract(
        self,
        *,
        document: SourceDocument,
        content: bytes,
        target: ExtractionTarget,
    ) -> ExtractionEnvelope: ...


def planned_extraction_run_id(
    *,
    document: SourceDocument,
    gateway: ModelGateway,
    target: ExtractionTarget,
) -> UUID:
    target_hash = hashlib.sha256(
        canonical_json(
            {
                "industries": sorted(str(item) for item in target.industry_ids),
                "predicates": sorted(target.predicate_allowlist),
                "schema": target.schema_version,
                "prompt": target.prompt_version,
                "risk_tier": target.risk_tier,
            }
        ).encode()
    ).hexdigest()
    return stable_uuid(
        "extraction-run-v2",
        str(document.id),
        gateway.extractor_name,
        gateway.extractor_version,
        gateway.model_name or "none",
        target_hash,
    )
