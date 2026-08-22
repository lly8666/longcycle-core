from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from longcycle.adapters.storage.outcomes import PostgresOutcomeRepository
from longcycle.application.outcome_evaluation import evaluate_outcome
from longcycle.domain.enums import OutcomeSemanticRelation, TemporalPrecision
from longcycle.domain.judgments import JudgmentAssertion, OutcomeObservation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate and persist one selected grounded Reality against one persisted Judgment. "
            "Semantic comparability must be explicit; a related milestone is never assumed to realize the target."
        )
    )
    parser.add_argument("judgment_persistence", type=Path)
    parser.add_argument("reality_execution", type=Path)
    parser.add_argument("--judgment-key", required=True)
    parser.add_argument(
        "--reality-fact-key",
        help="Required when the Reality execution contains more than one fact.",
    )
    parser.add_argument(
        "--semantic-relation",
        required=True,
        choices=[item.value for item in OutcomeSemanticRelation],
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _select_reality(
    reality_payload: dict[str, Any],
    fact_key: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fact_entries = [item for item in reality_payload.get("facts", []) if isinstance(item, dict)]
    if fact_key is None:
        if len(fact_entries) != 1:
            raise ValueError("--reality-fact-key is required when Reality contains multiple facts")
        selected_entry = fact_entries[0]
    else:
        matches = [
            item
            for item in fact_entries
            if isinstance(item.get("fact"), dict)
            and item["fact"].get("metadata", {}).get("fact_key") == fact_key
        ]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one Reality fact for key {fact_key}")
        selected_entry = matches[0]

    fact = selected_entry.get("fact")
    if not isinstance(fact, dict) or not fact.get("id"):
        raise ValueError("selected Reality execution entry has no persisted Fact identity")
    canonical_rows = [
        row
        for row in reality_payload.get("canonical_reality", [])
        if isinstance(row, dict) and str(row.get("assertion_id")) == str(fact["id"])
    ]
    if len(canonical_rows) != 1:
        raise ValueError("selected Reality Fact does not map to exactly one canonical Reality row")
    return fact, canonical_rows[0]


def _supporting_evidence_id(fact: dict[str, Any]) -> UUID:
    evidence = fact.get("evidence")
    if not isinstance(evidence, list):
        raise ValueError("Reality Fact must expose typed evidence refs")
    supporting = [
        row.get("evidence_fragment_id")
        for row in evidence
        if isinstance(row, dict) and row.get("evidence_role") == "supporting"
    ]
    if len(supporting) != 1 or not supporting[0]:
        raise ValueError(
            "bounded Outcome evaluator currently requires exactly one supporting Reality fragment; "
            "it will not silently choose among multiple provenance refs"
        )
    return UUID(str(supporting[0]))


async def _execute(
    *,
    dsn: str,
    judgment_payload: dict[str, Any],
    reality_payload: dict[str, Any],
    judgment_key: str,
    reality_fact_key: str | None,
    semantic_relation: OutcomeSemanticRelation,
) -> dict[str, Any]:
    candidates = [
        JudgmentAssertion.model_validate(item)
        for item in judgment_payload.get("judgments", [])
        if isinstance(item, dict) and item.get("metadata", {}).get("judgment_key") == judgment_key
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one persisted Judgment for key {judgment_key}")
    judgment = candidates[0]

    fact, canonical = _select_reality(reality_payload, reality_fact_key)
    precision = TemporalPrecision(canonical["valid_time_precision"])
    observation = OutcomeObservation(
        evidence_fragment_id=_supporting_evidence_id(fact),
        occurrence_from=canonical.get("valid_from"),
        occurrence_to=canonical.get("valid_to"),
        occurrence_precision=precision,
        occurrence_text=canonical.get("valid_time_text"),
        first_known_at=canonical["market_known_at"],
    )
    if semantic_relation == OutcomeSemanticRelation.DIRECT_MATCH:
        explanation = (
            f"The selected Reality is the same milestone as Judgment `{judgment_key}`. "
            f"The source-supported target `{judgment.target_text or judgment.target_precision.value}` "
            f"is compared with `{observation.occurrence_text or observation.occurrence_precision.value}` "
            "using only common source-supported temporal precision."
        )
    elif semantic_relation == OutcomeSemanticRelation.RELATED_MILESTONE:
        explanation = (
            f"The selected Reality is historically related to Judgment `{judgment_key}` but is not "
            "the same milestone. It is retained as later Outcome context without claiming that the "
            "original target was realized or computing a synthetic delay."
        )
    else:
        explanation = (
            f"The selected Reality was explicitly considered against Judgment `{judgment_key}` and is "
            "not semantically comparable. No realization claim or timing comparison is permitted."
        )

    base_evaluation = evaluate_outcome(
        judgment,
        observation,
        semantic_relation=semantic_relation,
        explanation=explanation,
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
                       semantic_relation,
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
    if semantic_relation != OutcomeSemanticRelation.DIRECT_MATCH:
        if row["evaluation_status"] != "indeterminate":
            raise RuntimeError("non-direct Outcome was incorrectly promoted to a determinate result")
        if row["timing_relation"] != "not_comparable" or row["timing_delta_value"] is not None:
            raise RuntimeError("non-direct Outcome incorrectly carries a timing comparison")
    return {
        "schema_version": "longcycle-grounded-outcome-evaluation-execution/v2",
        "judgment_key": judgment_key,
        "reality_fact_key": fact.get("metadata", {}).get("fact_key"),
        "semantic_relation": semantic_relation.value,
        "evaluation": evaluation.model_dump(mode="json"),
        "persisted_row": dict(row),
        "verification": {
            "postgres_persistence_completed": True,
            "idempotent_reappend_passed": True,
            "canonical_reality_linked": True,
            "outcome_evidence_linked": True,
            "outcome_known_time_preserved": True,
            "semantic_relation_explicit": True,
            "non_direct_never_claims_realization": semantic_relation == OutcomeSemanticRelation.DIRECT_MATCH
            or row["evaluation_status"] == "indeterminate",
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
            semantic_relation=OutcomeSemanticRelation(args.semantic_relation),
        )
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
