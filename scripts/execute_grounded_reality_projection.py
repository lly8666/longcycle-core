from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.application.reality_projection import (
    GroundedRealityEvidence,
    GroundedRealityProjectionSpec,
    build_grounded_reality_facts,
)
from longcycle.application.reconciliation import Reconciler
from longcycle.domain.enums import EntityType
from longcycle.domain.models import EvidenceFragment, ExtractionEnvelope


_ENTITY_TYPE_TO_DB = {
    EntityType.INDUSTRY: None,
    EntityType.PRODUCT: "product",
    EntityType.ORGANIZATION: "legal_entity",
    EntityType.SECURITY: "security",
    EntityType.FACILITY: "facility",
    EntityType.PRODUCTION_LINE: "production_line",
    EntityType.CAPACITY_PROJECT: "project",
    EntityType.EVENT: "event",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project grounded realized Evidence into canonical Fact/Reality via the normal PostgreSQL path."
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("grounded_execution", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _load_execution(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("ok") is not True:
        raise ValueError("grounded evidence execution must be successful")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("schema_version") != "longcycle-grounded-evidence-execution/v1":
        raise ValueError("unexpected grounded evidence execution schema")
    return result


def _load_spec(path: Path) -> GroundedRealityProjectionSpec:
    return GroundedRealityProjectionSpec.model_validate_json(path.read_text(encoding="utf-8"))


def _load_grounded_evidence(
    dsn: str,
    execution: dict[str, Any],
) -> tuple[tuple[GroundedRealityEvidence, ...], dict[str, EvidenceFragment]]:
    documents = {str(row["document_id"]): row for row in execution["documents"]}
    fragment_rows = {str(row["evidence_fragment_id"]): row for row in execution["fragments"]}
    ids = list(fragment_rows)
    persisted: dict[str, EvidenceFragment] = {}
    projected: list[GroundedRealityEvidence] = []

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        rows = connection.execute(
            """
            SELECT id, document_version_id, artifact_id, locator, excerpt,
                   structured_payload, fragment_sha256
            FROM evidence.evidence_fragments
            WHERE id = ANY(%s::uuid[])
            """,
            (ids,),
        ).fetchall()

    by_id = {str(row["id"]): row for row in rows}
    if set(by_id) != set(ids):
        missing = sorted(set(ids) - set(by_id))
        raise ValueError(f"grounded execution references missing persisted evidence: {missing}")

    for evidence_id, execution_row in fragment_rows.items():
        row = by_id[evidence_id]
        locator_payload = row["locator"]
        if not isinstance(locator_payload, dict) or not isinstance(locator_payload.get("value"), str):
            raise ValueError(f"evidence {evidence_id} does not have an opaque string locator")
        fragment = EvidenceFragment(
            id=row["id"],
            document_id=row["document_version_id"],
            artifact_id=row["artifact_id"],
            locator=locator_payload["value"],
            excerpt=row["excerpt"],
            structured_payload=row["structured_payload"],
            fragment_sha256=row["fragment_sha256"],
        )
        persisted[evidence_id] = fragment

        structured = row["structured_payload"]
        context = structured.get("claim_context") if isinstance(structured, dict) else None
        if not isinstance(context, dict):
            raise ValueError(f"evidence {evidence_id} has no claim_context")
        known = context.get("known_time")
        if not isinstance(known, dict) or not known.get("upper_bound"):
            raise ValueError(f"evidence {evidence_id} has no conservative known-time upper bound")
        claim_role = context.get("claim_role")
        if not isinstance(claim_role, str) or not claim_role:
            raise ValueError(f"evidence {evidence_id} has no claim role")
        document = documents[str(row["document_version_id"])]
        projected.append(
            GroundedRealityEvidence(
                fragment_key=execution_row["fragment_key"],
                evidence_fragment_id=row["id"],
                document_version_id=row["document_version_id"],
                source_connector_id=document["source_id"],
                claim_role=claim_role,
                known_time_upper_bound=known["upper_bound"],
                source_published_at=document.get("published_at"),
                excerpt=row["excerpt"] or "[structured evidence]",
            )
        )
    return tuple(projected), persisted


def _ensure_subjects(dsn: str, spec: GroundedRealityProjectionSpec) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        for subject in spec.subjects:
            db_type = _ENTITY_TYPE_TO_DB[subject.entity_type]
            if db_type is None:
                raise ValueError("industry subjects require taxonomy nodes and are not supported by this bounded Reality executor")
            existing = connection.execute(
                "SELECT entity_type, canonical_name FROM core.entities WHERE id = %s",
                (subject.id,),
            ).fetchone()
            if existing is not None:
                if existing["entity_type"] != db_type or existing["canonical_name"] != subject.canonical_name:
                    raise ValueError(f"subject id {subject.id} maps to different canonical entity content")
                continue
            connection.execute(
                """
                INSERT INTO core.entities (
                    id, entity_type, canonical_name, normalized_name, lifecycle_status
                ) VALUES (%s, %s, %s, %s, 'active')
                """,
                (
                    subject.id,
                    db_type,
                    subject.canonical_name,
                    " ".join(subject.canonical_name.lower().split()),
                ),
            )


async def _persist(
    *,
    dsn: str,
    spec: GroundedRealityProjectionSpec,
    execution: dict[str, Any],
) -> dict[str, Any]:
    if execution["task_id"] != spec.source_evidence_task_id:
        raise ValueError("Reality projection source_evidence_task_id does not match grounded execution")
    evidence, persisted = _load_grounded_evidence(dsn, execution)
    facts = build_grounded_reality_facts(spec, evidence)
    _ensure_subjects(dsn, spec)
    repository = PostgresResearchRepository(dsn, bucket_name="reality-projection")
    reconciler = Reconciler()
    results: list[dict[str, Any]] = []
    try:
        for fact in facts:
            evidence_row = persisted[str(fact.evidence_fragment_id)]
            extraction = ExtractionEnvelope(
                run_id=fact.extraction_run_id,
                document_id=fact.document_id,
                extractor_name=fact.extractor_name,
                extractor_version=fact.extractor_version,
                schema_version="longcycle-reality-projection/v1",
                evidence=(evidence_row,),
                candidates=(fact,),
            )
            await repository.save_extraction(extraction)
            await repository.append_assertions((fact,))
            reconciliation = await repository.reconcile_assertion(fact, reconciler)
            if reconciliation.decision.value != "accept":
                raise RuntimeError(
                    f"grounded Reality fact {fact.id} did not reconcile to canonical Reality: {reconciliation}"
                )
            results.append(
                {
                    "fact": fact.model_dump(mode="json"),
                    "reconciliation": reconciliation.model_dump(mode="json"),
                }
            )
    finally:
        await repository.close()

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        canonical_rows = connection.execute(
            """
            SELECT canonical.id, canonical.fact_key_id, key.predicate_code,
                   canonical.value_kind, canonical.value_text,
                   canonical.valid_from, canonical.valid_to,
                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.market_known_at, canonical.confidence,
                   canonical.publication_status
            FROM research.canonical_fact_versions canonical
            JOIN research.fact_keys key ON key.id = canonical.fact_key_id
            JOIN research.fact_resolution_assertions link
              ON link.resolution_id = canonical.resolution_id
             AND link.disposition = 'selected'
            WHERE link.assertion_id = ANY(%s::uuid[])
              AND canonical.system_to IS NULL
            ORDER BY canonical.market_known_at, canonical.id
            """,
            ([str(item["fact"]["id"]) for item in results],),
        ).fetchall()

    if len(canonical_rows) != len(results):
        raise RuntimeError("canonical Reality row count does not match accepted grounded facts")
    return {
        "schema_version": "longcycle-grounded-reality-execution/v1",
        "task_id": spec.task_id,
        "source_evidence_task_id": spec.source_evidence_task_id,
        "facts": results,
        "canonical_reality": [dict(row) for row in canonical_rows],
        "verification": {
            "fact_count": len(results),
            "canonical_reality_count": len(canonical_rows),
            "all_reconciled_accept": True,
            "all_fact_evidence_ids_persisted": True,
            "all_known_times_derived_from_grounded_evidence": True,
            "valid_time_precision_preserved": all(
                row["valid_time_precision"] != "unknown" for row in canonical_rows
            ),
        },
    }


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    spec = _load_spec(args.spec)
    execution = _load_execution(args.grounded_execution)
    result = asyncio.run(_persist(dsn=dsn, spec=spec, execution=execution))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
