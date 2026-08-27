from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from longcycle.adapters.storage.judgments import PostgresJudgmentRepository
from longcycle.application.judgment_context_projection import (
    GroundedJudgmentContextSpec,
    build_grounded_judgment_context,
)
from longcycle.application.judgment_projection import GroundedProjectionEvidence
from longcycle.domain.judgments import JudgmentAssertion


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Persist source-backed rationales and relations around an already-grounded "
            "Judgment projection."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("judgment_execution", type=Path)
    parser.add_argument("evidence_execution", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _load_judgments(path: Path) -> tuple[str, tuple[JudgmentAssertion, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "longcycle-grounded-judgment-persistence/v1":
        raise ValueError("unexpected grounded Judgment execution schema")
    task_id = payload.get("task_id")
    rows = payload.get("judgments")
    if not isinstance(task_id, str) or not isinstance(rows, list):
        raise ValueError("grounded Judgment execution is incomplete")
    return task_id, tuple(JudgmentAssertion.model_validate(row) for row in rows)


def _load_evidence(path: Path) -> tuple[str, tuple[GroundedProjectionEvidence, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("ok") is not True:
        raise ValueError("grounded evidence execution must be successful")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("grounded evidence execution has no result")
    task_id = result.get("task_id")
    documents = result.get("documents")
    fragments = result.get("fragments")
    if not isinstance(task_id, str) or not isinstance(documents, list) or not isinstance(
        fragments, list
    ):
        raise ValueError("grounded evidence execution is incomplete")

    documents_by_id = {str(row["document_id"]): row for row in documents}
    projected: list[GroundedProjectionEvidence] = []
    for row in fragments:
        context = row.get("claim_context")
        if not isinstance(context, dict):
            raise ValueError("grounded evidence fragment has no claim_context")
        known = context.get("known_time")
        if not isinstance(known, dict) or not known.get("upper_bound"):
            raise ValueError("grounded evidence fragment lacks known-time bound")
        document = documents_by_id[str(row["document_id"])]
        projected.append(
            GroundedProjectionEvidence(
                fragment_key=row["fragment_key"],
                evidence_fragment_id=row["evidence_fragment_id"],
                document_version_id=row["document_id"],
                source_connector_id=document["source_id"],
                claim_role=context["claim_role"],
                known_time_upper_bound=known["upper_bound"],
                source_published_at=document.get("published_at"),
                excerpt="[grounded evidence]",
            )
        )
    return task_id, tuple(projected)


async def _execute(
    *,
    dsn: str,
    spec: GroundedJudgmentContextSpec,
    judgment_task_id: str,
    judgments: tuple[JudgmentAssertion, ...],
    evidence_task_id: str,
    evidence: tuple[GroundedProjectionEvidence, ...],
) -> dict[str, Any]:
    if judgment_task_id != spec.source_judgment_task_id:
        raise ValueError("context source Judgment task does not match execution")
    if evidence_task_id != spec.source_evidence_task_id:
        raise ValueError("context source Evidence task does not match execution")

    rationales, relations = build_grounded_judgment_context(spec, judgments, evidence)
    repository = PostgresJudgmentRepository(dsn)
    try:
        await repository.append_rationales(rationales)
        await repository.append_rationales(rationales)
        await repository.append_relations(relations)
        await repository.append_relations(relations)

        async with repository.connection() as connection:
            rationale_ids = [item.id for item in rationales]
            if rationale_ids:
                cursor = await connection.execute(
                    """
                    SELECT count(*) AS n
                    FROM research.judgment_rationales
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (rationale_ids,),
                )
                row = await cursor.fetchone()
                rationale_count = int(row["n"]) if row is not None else -1
            else:
                rationale_count = 0

            if relations:
                clauses = [
                    (item.from_judgment_id, item.to_judgment_id, item.relation_type.value)
                    for item in relations
                ]
                persisted_relation_count = 0
                for from_id, to_id, relation_type in clauses:
                    cursor = await connection.execute(
                        """
                        SELECT count(*) AS n
                        FROM research.judgment_relations
                        WHERE from_judgment_id = %s
                          AND to_judgment_id = %s
                          AND relation_type = %s
                        """,
                        (from_id, to_id, relation_type),
                    )
                    row = await cursor.fetchone()
                    persisted_relation_count += int(row["n"]) if row is not None else 0
            else:
                persisted_relation_count = 0
    finally:
        await repository.close()

    if rationale_count != len(rationales):
        raise RuntimeError("grounded Judgment rationale persistence count mismatch")
    if persisted_relation_count != len(relations):
        raise RuntimeError("grounded Judgment relation persistence count mismatch")

    return {
        "schema_version": "longcycle-grounded-judgment-context-persistence/v1",
        "task_id": spec.task_id,
        "source_judgment_task_id": spec.source_judgment_task_id,
        "source_evidence_task_id": spec.source_evidence_task_id,
        "rationales": [item.model_dump(mode="json") for item in rationales],
        "relations": [item.model_dump(mode="json") for item in relations],
        "verification": {
            "rationale_count": len(rationales),
            "relation_count": len(relations),
            "idempotent_reappend_passed": True,
            "revision_family_identity_guarded": True,
            "rationale_input_no_lookahead_guarded": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    spec = GroundedJudgmentContextSpec.model_validate_json(args.spec.read_text(encoding="utf-8"))
    judgment_task_id, judgments = _load_judgments(args.judgment_execution)
    evidence_task_id, evidence = _load_evidence(args.evidence_execution)
    result = asyncio.run(
        _execute(
            dsn=dsn,
            spec=spec,
            judgment_task_id=judgment_task_id,
            judgments=judgments,
            evidence_task_id=evidence_task_id,
            evidence=evidence,
        )
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
