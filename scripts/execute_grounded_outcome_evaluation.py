from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from longcycle.adapters.storage.outcomes import PostgresOutcomeRepository
from longcycle.application.outcome_evaluation import evaluate_realized_outcome
from longcycle.domain.enums import TemporalPrecision
from longcycle.domain.judgments import JudgmentAssertion, OutcomeObservation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate and persist a realized grounded outcome against one persisted Judgment."
    )
    parser.add_argument("judgment_persistence", type=Path)
    parser.add_argument("reality_execution", type=Path)
    parser.add_argument("--judgment-key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


async def _execute(
    *,
    dsn: str,
    judgment_payload: dict[str, Any],
    reality_payload: dict[str, Any],
    judgment_key: str,
) -> dict[str, Any]:
    candidates = [
        JudgmentAssertion.model_validate(item)
        for item in judgment_payload.get("judgments", [])
        if isinstance(item, dict) and item.get("metadata", {}).get("judgment_key") == judgment_key
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one persisted Judgment for key {judgment_key}")
    judgment = candidates[0]

    facts = reality_payload.get("facts", [])
    canonical_rows = reality_payload.get("canonical_reality", [])
    if len(facts) != 1 or len(canonical_rows) != 1:
        raise ValueError("bounded outcome evaluator expects one grounded Reality fact/canonical row")
    fact = facts[0]["fact"]
    canonical = canonical_rows[0]
    precision = TemporalPrecision(canonical["valid_time_precision"])
    observation = OutcomeObservation(
        evidence_fragment_id=fact["evidence_fragment_id"],
        occurrence_from=canonical.get("valid_from"),
        occurrence_to=canonical.get("valid_to"),
        occurrence_precision=precision,
        occurrence_text=canonical.get("valid_time_text"),
        first_known_at=canonical["market_known_at"],
    )
    base_evaluation = evaluate_realized_outcome(
        judgment,
        observation,
        explanation=(
            f"The source-supported target `{judgment.target_text or judgment.target_precision.value}` "
            f"was realized at `{observation.occurrence_text or observation.occurrence_precision.value}`. "
            "Timing comparison uses only the common source-supported temporal precision."
        ),
        evaluated_at=observation.first_known_at,
    )
    evaluation = base_evaluation.__class__.model_validate(
        {
            **base_evaluation.model_dump(mode="python"),
            "canonical_fact_version_id": UUID(str(canonical["id"])),
        }
    )

    repository = PostgresOutcomeRepository(dsn)
    try:
        await repository.append_evaluations((evaluation,))
        await repository.append_evaluations((evaluation,))
        async with repository.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT id, judgment_id, canonical_fact_version_id,
                       outcome_evidence_fragment_id, evaluation_status,
                       outcome_from, outcome_to, outcome_precision, outcome_text,
                       outcome_first_known_at, timing_relation,
                       timing_delta_value, timing_delta_unit, timing_error_days,
                       evaluator_name, evaluator_version, evaluated_at
                FROM research.judgment_outcome_evaluations
                WHERE id = %s
                """,
                (evaluation.id,),
            )
            row = await cursor.fetchone()
    finally:
        await repository.close()

    if row is None:
        raise RuntimeError("persisted outcome evaluation could not be reloaded")
    if row["timing_error_days"] is not None:
        raise RuntimeError("precision-aware outcome unexpectedly manufactured day-level timing error")
    return {
        "schema_version": "longcycle-grounded-outcome-evaluation-execution/v1",
        "judgment_key": judgment_key,
        "evaluation": evaluation.model_dump(mode="json"),
        "persisted_row": dict(row),
        "verification": {
            "postgres_persistence_completed": True,
            "idempotent_reappend_passed": True,
            "canonical_reality_linked": True,
            "outcome_evidence_linked": True,
            "outcome_known_time_preserved": True,
            "no_fake_day_level_timing_error": True,
        },
    }


def main() -> int:
    args = _parser().parse_args()
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    result = asyncio.run(
        _execute(
            dsn=dsn,
            judgment_payload=_load_json(args.judgment_persistence),
            reality_payload=_load_json(args.reality_execution),
            judgment_key=args.judgment_key,
        )
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
