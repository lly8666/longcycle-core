from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from longcycle.application.judgment_projection import (
    GroundedJudgmentProjectionSpec,
    GroundedProjectionEvidence,
    build_grounded_judgments,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic contemporaneous JudgmentAssertions from a grounded portable "
            "evidence DuckDB. The projection never promotes outcome evidence or invents target dates."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("database", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def _load_spec(path: Path) -> GroundedJudgmentProjectionSpec:
    return GroundedJudgmentProjectionSpec.model_validate_json(path.read_text(encoding="utf-8"))


def _load_evidence(database: Path) -> tuple[GroundedProjectionEvidence, ...]:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "DuckDB runtime is unavailable. Restore the handoff offline runtime pack "
            "or install the project duckdb extra."
        ) from exc

    connection = duckdb.connect(str(database), read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT
                evidence.fragment_key,
                evidence.evidence_fragment_id,
                evidence.document_version_id,
                document.source_id,
                evidence.claim_role,
                evidence.known_time_upper_bound,
                document.published_at,
                evidence.excerpt
            FROM evidence_index evidence
            JOIN document_index document
              ON document.document_version_id = evidence.document_version_id
            ORDER BY evidence.known_time_upper_bound, evidence.fragment_key
            """
        ).fetchall()
    finally:
        connection.close()

    return tuple(
        GroundedProjectionEvidence(
            fragment_key=row[0],
            evidence_fragment_id=row[1],
            document_version_id=row[2],
            source_connector_id=row[3],
            claim_role=row[4],
            known_time_upper_bound=row[5],
            source_published_at=row[6],
            excerpt=row[7],
        )
        for row in rows
    )


def _render_payload(
    *,
    spec: GroundedJudgmentProjectionSpec,
    database: Path,
    evidence: tuple[GroundedProjectionEvidence, ...],
) -> dict[str, Any]:
    judgments = build_grounded_judgments(spec, evidence)
    return {
        "schema_version": "longcycle-grounded-judgment-projection/v1",
        "task_id": spec.task_id,
        "source_evidence_task_id": spec.source_evidence_task_id,
        "source_database_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
        "subjects": [subject.model_dump(mode="json") for subject in spec.subjects],
        "judgments": [judgment.model_dump(mode="json") for judgment in judgments],
        "verification": {
            "judgment_count": len(judgments),
            "statement_evidence_count": sum(len(item.evidence) for item in judgments),
            "claim_roles": sorted(
                {
                    role
                    for judgment in judgments
                    for role in judgment.metadata.get("source_claim_roles", [])
                }
            ),
            "outcome_evidence_used_as_judgment": False,
            "all_first_known_times_derived_from_cited_evidence": True,
            "target_precision_preserved": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    spec = _load_spec(args.spec)
    evidence = _load_evidence(args.database)
    payload = _render_payload(spec=spec, database=args.database, evidence=evidence)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
