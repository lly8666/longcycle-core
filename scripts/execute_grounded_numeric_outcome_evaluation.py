from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from longcycle.adapters.storage.outcomes import PostgresOutcomeRepository
from longcycle.application.numeric_outcome_evaluation import (
    NumericOutcomeObservation,
    evaluate_numeric_outcome,
)
from longcycle.domain.judgments import JudgmentAssertion
from longcycle.domain.models import FactAssertion


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one persisted numeric Judgment with one directly comparable canonical "
            "Reality value and persist numeric forecast error without inventing a tolerance."
        )
    )
    parser.add_argument("judgment_persistence", type=Path)
    parser.add_argument("reality_execution", type=Path)
    parser.add_argument("--judgment-key", required=True)
    parser.add_argument("--reality-fact-key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _select_judgment(payload: dict[str, Any], judgment_key: str) -> JudgmentAssertion:
    if payload.get("schema_version") != "longcycle-grounded-judgment-persistence/v1":
        raise ValueError("unexpected grounded Judgment execution schema")
    matches = [
        JudgmentAssertion.model_validate(item)
        for item in payload.get("judgments", [])
        if isinstance(item, dict) and item.get("metadata", {}).get("judgment_key") == judgment_key
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one persisted Judgment for key {judgment_key}")
    return matches[0]


def _select_reality(
    payload: dict[str, Any],
    fact_key: str,
) -> tuple[FactAssertion, dict[str, Any]]:
    matches = [
        item
        for item in payload.get("facts", [])
        if isinstance(item, dict)
        and isinstance(item.get("fact"), dict)
        and item["fact"].get("metadata", {}).get("fact_key") == fact_key
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one Reality fact for key {fact_key}")
    fact = FactAssertion.model_validate(matches[0]["fact"])
    canonical_rows = [
        row
        for row in payload.get("canonical_reality", [])
        if isinstance(row, dict) and str(row.get("assertion_id")) == str(fact.id)
    ]
    if len(canonical_rows) != 1:
        raise ValueError("selected Reality Fact does not map to exactly one canonical Reality row")
    return fact, canonical_rows[0]


def _supporting_evidence_id(fact: FactAssertion) -> UUID:
    supporting = [
        item.evidence_fragment_id
        for item in fact.evidence
        if item.evidence_role.value == "supporting"
    ]
    if len(supporting) != 1:
        raise ValueError(
            "bounded numeric Outcome evaluator requires exactly one supporting Reality fragment"
        )
    return supporting[0]


async def _execute(
    *,
    dsn: str,
    judgment_payload: dict[str, Any],
    reality_payload: dict[str, Any],
    judgment_key: str,
    reality_fact_key: str,
) -> dict[str, Any]:
    judgment = _select_judgment(judgment_payload, judgment_key)
    fact, canonical = _select_reality(reality_payload, reality_fact_key)
    if fact.normalized_number is None or fact.normalized_unit is None:
        raise ValueError("selected Reality Fact is not normalized numeric Reality")

    observation = NumericOutcomeObservation(
        canonical_fact_version_id=UUID(str(canonical["id"])),
        evidence_fragment_id=_supporting_evidence_id(fact),
        predicate_code=fact.field_name,
        comparability_hash=fact.dimensions.comparability_hash,
        value_numeric=fact.normalized_number,
        unit_code=fact.normalized_unit,
        occurrence_from=fact.valid_time.start,
        occurrence_to=fact.valid_time.end,
        occurrence_precision=fact.valid_time_precision,
        occurrence_text=fact.valid_time_text,
        first_known_at=canonical["market_known_at"],
    )
    explanation = (
        f"Judgment `{judgment_key}` and canonical Reality `{reality_fact_key}` share the same "
        "predicate, typed dimensions and normalized unit. Numeric error is realized minus "
        "Judgment value; no correctness tolerance or hindsight backdating is inferred."
    )
    evaluation = evaluate_numeric_outcome(
        judgment,
        observation,
        explanation=explanation,
        evaluated_at=observation.first_known_at,
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
                       semantic_relation,
                       outcome_from, outcome_to, outcome_precision, outcome_text,
                       outcome_first_known_at, timing_relation,
                       timing_delta_value, timing_delta_unit, numeric_error,
                       relative_error, timing_error_days, direction_correct,
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
        raise RuntimeError("persisted numeric outcome evaluation could not be reloaded")
    if row["canonical_fact_version_id"] != observation.canonical_fact_version_id:
        raise RuntimeError("numeric Outcome lost canonical Reality identity")
    if row["outcome_evidence_fragment_id"] != observation.evidence_fragment_id:
        raise RuntimeError("numeric Outcome lost supporting Evidence identity")
    if row["numeric_error"] != evaluation.numeric_error:
        raise RuntimeError("numeric Outcome error did not round-trip through PostgreSQL")
    if row["timing_error_days"] is not None:
        raise RuntimeError("numeric Outcome manufactured day-level timing error")

    return {
        "schema_version": "longcycle-grounded-numeric-outcome-evaluation-execution/v1",
        "judgment_key": judgment_key,
        "reality_fact_key": reality_fact_key,
        "judgment_value_numeric": judgment.value_numeric,
        "reality_value_numeric": fact.normalized_number,
        "unit_code": judgment.unit_code,
        "comparability_hash": judgment.comparability_hash,
        "evaluation": evaluation.model_dump(mode="json"),
        "persisted_row": dict(row),
        "verification": {
            "postgres_persistence_completed": True,
            "idempotent_reappend_passed": True,
            "canonical_reality_linked": True,
            "outcome_evidence_linked": True,
            "outcome_known_time_preserved": True,
            "predicate_dimensions_unit_match_required": True,
            "numeric_error_is_realized_minus_judgment": True,
            "no_correctness_tolerance_inferred": True,
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
            reality_fact_key=args.reality_fact_key,
        )
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
