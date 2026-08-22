from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from longcycle.domain.judgments import JudgmentOutcomeEvaluation

from .postgres import PostgresSupport


class PostgresOutcomeRepository(PostgresSupport):
    async def append_evaluations(
        self,
        evaluations: Sequence[JudgmentOutcomeEvaluation],
    ) -> None:
        async with self.connection() as connection:
            for evaluation in evaluations:
                existing_cursor = await connection.execute(
                    """
                    SELECT judgment_id, canonical_fact_version_id,
                           outcome_evidence_fragment_id, evaluation_status,
                           outcome_from, outcome_to, outcome_precision, outcome_text,
                           outcome_first_known_at, timing_relation,
                           timing_delta_value, timing_delta_unit,
                           numeric_error, relative_error, timing_error_days,
                           direction_correct, explanation,
                           evaluator_name, evaluator_version, evaluated_at
                    FROM research.judgment_outcome_evaluations
                    WHERE id = %s
                    """,
                    (evaluation.id,),
                )
                existing = await existing_cursor.fetchone()
                expected: dict[str, Any] = {
                    "judgment_id": evaluation.judgment_id,
                    "canonical_fact_version_id": evaluation.canonical_fact_version_id,
                    "outcome_evidence_fragment_id": evaluation.outcome_evidence_fragment_id,
                    "evaluation_status": evaluation.evaluation_status.value,
                    "outcome_from": evaluation.outcome_from,
                    "outcome_to": evaluation.outcome_to,
                    "outcome_precision": evaluation.outcome_precision.value,
                    "outcome_text": evaluation.outcome_text,
                    "outcome_first_known_at": evaluation.outcome_first_known_at,
                    "timing_relation": evaluation.timing_relation.value,
                    "timing_delta_value": evaluation.timing_delta_value,
                    "timing_delta_unit": (
                        evaluation.timing_delta_unit.value
                        if evaluation.timing_delta_unit is not None
                        else None
                    ),
                    "numeric_error": evaluation.numeric_error,
                    "relative_error": evaluation.relative_error,
                    "timing_error_days": None,
                    "direction_correct": evaluation.direction_correct,
                    "explanation": evaluation.explanation,
                    "evaluator_name": evaluation.evaluator_name,
                    "evaluator_version": evaluation.evaluator_version,
                    "evaluated_at": evaluation.evaluated_at,
                }
                if existing is not None:
                    for key, value in expected.items():
                        stored = existing[key]
                        if isinstance(value, Decimal) and stored is not None:
                            stored = Decimal(stored)
                        if stored != value:
                            raise ValueError(
                                f"outcome evaluation id already maps to different immutable content at {key}"
                            )
                    continue

                if await self._missing_reference(connection, "research.judgment_assertions", evaluation.judgment_id):
                    raise ValueError("outcome evaluation references an unknown judgment")
                if (
                    evaluation.canonical_fact_version_id is not None
                    and await self._missing_reference(
                        connection,
                        "research.canonical_fact_versions",
                        evaluation.canonical_fact_version_id,
                    )
                ):
                    raise ValueError("outcome evaluation references an unknown canonical fact version")
                if (
                    evaluation.outcome_evidence_fragment_id is not None
                    and await self._missing_reference(
                        connection,
                        "evidence.evidence_fragments",
                        evaluation.outcome_evidence_fragment_id,
                    )
                ):
                    raise ValueError("outcome evaluation references unknown outcome evidence")

                await connection.execute(
                    """
                    INSERT INTO research.judgment_outcome_evaluations (
                        id, judgment_id, canonical_fact_version_id,
                        outcome_evidence_fragment_id, evaluation_status,
                        outcome_from, outcome_to, outcome_precision, outcome_text,
                        outcome_first_known_at, timing_relation,
                        timing_delta_value, timing_delta_unit,
                        numeric_error, relative_error, timing_error_days,
                        direction_correct, explanation,
                        evaluator_name, evaluator_version, evaluated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, NULL,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        evaluation.id,
                        evaluation.judgment_id,
                        evaluation.canonical_fact_version_id,
                        evaluation.outcome_evidence_fragment_id,
                        evaluation.evaluation_status.value,
                        evaluation.outcome_from,
                        evaluation.outcome_to,
                        evaluation.outcome_precision.value,
                        evaluation.outcome_text,
                        evaluation.outcome_first_known_at,
                        evaluation.timing_relation.value,
                        evaluation.timing_delta_value,
                        evaluation.timing_delta_unit.value if evaluation.timing_delta_unit else None,
                        evaluation.numeric_error,
                        evaluation.relative_error,
                        evaluation.direction_correct,
                        evaluation.explanation,
                        evaluation.evaluator_name,
                        evaluation.evaluator_version,
                        evaluation.evaluated_at,
                    ),
                )

    @staticmethod
    async def _missing_reference(connection: Any, table: str, row_id: Any) -> bool:
        cursor = await connection.execute(f"SELECT 1 FROM {table} WHERE id = %s", (row_id,))
        return await cursor.fetchone() is None
