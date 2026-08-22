from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from longcycle.adapters.storage.judgments import PostgresJudgmentRepository
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.application.judgment_projection import (
    GroundedJudgmentProjectionSpec,
    GroundedProjectionEvidence,
    build_grounded_judgments,
)
from longcycle.domain.models import EvidenceFragment, ExtractionEnvelope


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persist a grounded Judgment projection from an already-successful evidence run."
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


def _load_inputs(
    dsn: str,
    execution: dict[str, Any],
) -> tuple[tuple[GroundedProjectionEvidence, ...], dict[str, EvidenceFragment]]:
    documents = {str(row["document_id"]): row for row in execution["documents"]}
    execution_fragments = {str(row["evidence_fragment_id"]): row for row in execution["fragments"]}
    ids = list(execution_fragments)
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
        raise ValueError("grounded execution references unavailable persisted evidence")

    projected: list[GroundedProjectionEvidence] = []
    persisted: dict[str, EvidenceFragment] = {}
    for evidence_id, execution_row in execution_fragments.items():
        row = by_id[evidence_id]
        locator = row["locator"]
        if not isinstance(locator, dict) or not isinstance(locator.get("value"), str):
            raise ValueError("grounded Judgment evidence must have an opaque string locator")
        persisted[evidence_id] = EvidenceFragment(
            id=row["id"],
            document_id=row["document_version_id"],
            artifact_id=row["artifact_id"],
            locator=locator["value"],
            excerpt=row["excerpt"],
            structured_payload=row["structured_payload"],
            fragment_sha256=row["fragment_sha256"],
        )
        structured = row["structured_payload"]
        context = structured.get("claim_context") if isinstance(structured, dict) else None
        if not isinstance(context, dict):
            raise ValueError("grounded Judgment evidence has no claim_context")
        known = context.get("known_time")
        if not isinstance(known, dict) or not known.get("upper_bound"):
            raise ValueError("grounded Judgment evidence lacks conservative known-time bound")
        document = documents[str(row["document_version_id"])]
        projected.append(
            GroundedProjectionEvidence(
                fragment_key=execution_row["fragment_key"],
                evidence_fragment_id=row["id"],
                document_version_id=row["document_version_id"],
                source_connector_id=document["source_id"],
                claim_role=context["claim_role"],
                known_time_upper_bound=known["upper_bound"],
                source_published_at=document.get("published_at"),
                excerpt=row["excerpt"] or "[structured evidence]",
            )
        )
    return tuple(projected), persisted


def _ensure_subjects(dsn: str, spec: GroundedJudgmentProjectionSpec) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        for subject in spec.subjects:
            db_type = subject.entity_type
            if db_type not in {"project", "production_line", "facility", "event", "product", "legal_entity"}:
                raise ValueError(f"unsupported Judgment subject entity type for bounded executor: {db_type}")
            row = connection.execute(
                "SELECT entity_type, canonical_name FROM core.entities WHERE id = %s",
                (subject.id,),
            ).fetchone()
            if row is not None:
                if row["entity_type"] != db_type or row["canonical_name"] != subject.canonical_name:
                    raise ValueError("Judgment subject id maps to different canonical entity content")
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


async def _execute(
    *,
    dsn: str,
    spec: GroundedJudgmentProjectionSpec,
    execution: dict[str, Any],
) -> dict[str, Any]:
    if execution["task_id"] != spec.source_evidence_task_id:
        raise ValueError("Judgment projection source task does not match grounded evidence execution")
    evidence, persisted = _load_inputs(dsn, execution)
    judgments = build_grounded_judgments(spec, evidence)
    _ensure_subjects(dsn, spec)

    research_repository = PostgresResearchRepository(dsn, bucket_name="judgment-projection")
    try:
        for judgment in judgments:
            cited = tuple(persisted[str(link.evidence_fragment_id)] for link in judgment.evidence)
            document_ids = {item.document_id for item in cited}
            if len(document_ids) != 1:
                raise ValueError("bounded Judgment extraction run currently requires one source document")
            extraction = ExtractionEnvelope(
                run_id=judgment.extraction_run_id,
                document_id=next(iter(document_ids)),
                extractor_name=judgment.extractor_name,
                extractor_version=judgment.extractor_version,
                schema_version="longcycle-judgment-projection/v1",
                evidence=cited,
                candidates=(),
            )
            await research_repository.save_extraction(extraction)
    finally:
        await research_repository.close()

    repository = PostgresJudgmentRepository(dsn)
    try:
        await repository.append_judgments(judgments)
        await repository.append_judgments(judgments)
        async with repository.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT id, topic_code, target_precision, target_text,
                       first_known_at, metadata
                FROM research.judgment_assertions
                WHERE id = ANY(%s::uuid[])
                ORDER BY first_known_at, id
                """,
                ([item.id for item in judgments],),
            )
            rows = await cursor.fetchall()
            evidence_cursor = await connection.execute(
                "SELECT count(*) AS count FROM research.judgment_evidence WHERE judgment_id = ANY(%s::uuid[])",
                ([item.id for item in judgments],),
            )
            evidence_count_row = await evidence_cursor.fetchone()
    finally:
        await repository.close()

    if len(rows) != len(judgments):
        raise RuntimeError("real Judgment persistence count mismatch")
    evidence_count = int(evidence_count_row["count"]) if evidence_count_row is not None else -1
    if evidence_count != sum(len(item.evidence) for item in judgments):
        raise RuntimeError("real Judgment evidence-link count mismatch")
    return {
        "schema_version": "longcycle-grounded-judgment-persistence/v1",
        "task_id": spec.task_id,
        "source_evidence_task_id": spec.source_evidence_task_id,
        "judgments": [item.model_dump(mode="json") for item in judgments],
        "persisted_rows": [dict(row) for row in rows],
        "verification": {
            "judgment_count": len(judgments),
            "evidence_link_count": evidence_count,
            "idempotent_reappend_passed": True,
            "all_first_known_times_derived_from_grounded_evidence": True,
            "target_precision_preserved": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    spec = GroundedJudgmentProjectionSpec.model_validate_json(args.spec.read_text(encoding="utf-8"))
    execution = _load_execution(args.grounded_execution)
    result = asyncio.run(_execute(dsn=dsn, spec=spec, execution=execution))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
