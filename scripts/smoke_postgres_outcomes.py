from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from longcycle.adapters.storage.outcomes import PostgresOutcomeRepository
from longcycle.application.outcome_evaluation import evaluate_realized_outcome
from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)
from longcycle.domain.judgments import JudgmentAssertion, JudgmentEvidenceRef, OutcomeObservation


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    judgment_id = UUID("33333333-3333-3333-3333-333333333333")
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        judgment_row = connection.execute(
            """
            SELECT judgment.extraction_run_id, judgment.source_connector_id,
                   link.evidence_fragment_id
            FROM research.judgment_assertions judgment
            JOIN research.judgment_evidence link ON link.judgment_id = judgment.id
            WHERE judgment.id = %s AND link.evidence_role = 'statement'
            ORDER BY link.evidence_fragment_id
            LIMIT 1
            """,
            (judgment_id,),
        ).fetchone()
        if judgment_row is None:
            raise AssertionError("Judgment smoke must run before Outcome smoke")
        canonical = connection.execute(
            """
            SELECT canonical.id, canonical.valid_from, canonical.valid_to,
                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.market_known_at, assertion.evidence_fragment_id
            FROM research.canonical_fact_versions canonical
            JOIN research.fact_resolution_assertions link
              ON link.resolution_id = canonical.resolution_id
             AND link.disposition = 'selected'
            JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
            WHERE canonical.publication_status = 'trusted'
              AND canonical.system_to IS NULL
              AND canonical.valid_time_precision = 'month'
            ORDER BY canonical.market_known_at DESC
            LIMIT 1
            """
        ).fetchone()
        if canonical is None:
            raise AssertionError("Reality smoke must run before Outcome smoke")

    judgment = JudgmentAssertion(
        id=judgment_id,
        speaker_name_text="Management",
        subject_entity_id=UUID("22222222-2222-2222-2222-222222222222"),
        topic_code="project.first_product_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 5, 1, tzinfo=UTC),
        target_to=datetime(2022, 6, 1, tzinfo=UTC),
        target_precision=TemporalPrecision.MONTH,
        target_text="May 2022",
        value_kind=JudgmentValueKind.TEXT,
        value_text="first product expected during May 2022",
        summary="First product was expected during May 2022.",
        source_published_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        first_known_at=datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        extraction_run_id=judgment_row["extraction_run_id"],
        source_connector_id=judgment_row["source_connector_id"],
        extractor_name="grounded-judgment-projection",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=judgment_row["evidence_fragment_id"],
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    )
    observation = OutcomeObservation(
        evidence_fragment_id=canonical["evidence_fragment_id"],
        occurrence_from=canonical["valid_from"],
        occurrence_to=canonical["valid_to"],
        occurrence_precision=TemporalPrecision(canonical["valid_time_precision"]),
        occurrence_text=canonical["valid_time_text"],
        first_known_at=canonical["market_known_at"],
    )
    base = evaluate_realized_outcome(
        judgment,
        observation,
        explanation="Month-precision smoke: May target versus July outcome.",
        evaluated_at=observation.first_known_at,
    )
    evaluation = base.__class__.model_validate(
        {**base.model_dump(mode="python"), "canonical_fact_version_id": canonical["id"]}
    )

    repository = PostgresOutcomeRepository(dsn)
    try:
        await repository.append_evaluations((evaluation,))
        await repository.append_evaluations((evaluation,))
        async with repository.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT timing_relation, timing_delta_value, timing_delta_unit,
                       timing_error_days, outcome_precision, outcome_first_known_at
                FROM research.judgment_outcome_evaluations
                WHERE id = %s
                """,
                (evaluation.id,),
            )
            row = await cursor.fetchone()
    finally:
        await repository.close()

    if row is None:
        raise AssertionError("Outcome evaluation was not persisted")
    if row["timing_relation"] != "after_target_window":
        raise AssertionError(f"unexpected timing relation: {row}")
    if int(row["timing_delta_value"]) != 2 or row["timing_delta_unit"] != "calendar_months":
        raise AssertionError(f"month-level timing delta was not preserved: {row}")
    if row["timing_error_days"] is not None:
        raise AssertionError("Outcome smoke manufactured day-level timing error")
    if row["outcome_precision"] != "month":
        raise AssertionError("Outcome smoke lost month precision")

    print("POSTGRES_OUTCOME_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
