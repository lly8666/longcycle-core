from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from longcycle.adapters.storage.duckdb_epistemic import (
    DuckDBEpistemicMemoryReader,
    seal_industrial_memory,
)
from longcycle.adapters.storage.judgments import PostgresJudgmentRepository
from longcycle.adapters.storage.outcomes import PostgresOutcomeRepository
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_epistemic import PostgresEpistemicMemoryReader
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.outcome_evaluation import evaluate_realized_outcome
from longcycle.application.reconciliation import Reconciler
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    QualityGrade,
    SourceKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentEvidenceRef,
    OutcomeObservation,
)
from longcycle.domain.models import (
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    RawPayload,
    SourceDocument,
    TimeRange,
    stable_uuid_exact,
)


MAY_KNOWN = datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC)
AUG_KNOWN = datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC)


async def _save_document_with_evidence(
    repository: PostgresResearchRepository,
    *,
    source_id,
    external_id: str,
    url: str,
    known_at: datetime,
    text: str,
):
    payload = RawPayload(
        content=(text + "\n").encode(),
        content_type="text/plain",
        canonical_url=url,
        retrieved_at=known_at,
    )
    document = SourceDocument.from_payload(
        source_id=source_id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id=external_id,
        title=external_id,
        published_at=known_at,
        first_known_at=known_at,
    )
    document = await repository.save_document(document)
    evidence = EvidenceFragment.create(document.id, f"text:0:{len(text)}", text)
    await repository.save_evidence((evidence,))
    return document, evidence


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="Epistemic integration smoke source",
        publisher_domain="epistemic-smoke.longcycle.invalid",
        kind=SourceKind.COMPANY,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    subject_id = stable_uuid_exact("epistemic-smoke", "project")
    with psycopg.connect(dsn) as connection:
        connection.execute(
            """
            INSERT INTO core.entities (
                id, entity_type, canonical_name, normalized_name, lifecycle_status
            ) VALUES (%s, 'project', %s, %s, 'active')
            ON CONFLICT (id) DO NOTHING
            """,
            (subject_id, "Epistemic smoke project", "epistemic smoke project"),
        )

    research = PostgresResearchRepository(dsn, bucket_name="smoke")
    try:
        may_document, may_evidence = await _save_document_with_evidence(
            research,
            source_id=source.id,
            external_id="epistemic-guidance-may-2022",
            url="https://epistemic-smoke.longcycle.invalid/may.txt",
            known_at=MAY_KNOWN,
            text="Management expected first product in May 2022.",
        )
        aug_document, aug_evidence = await _save_document_with_evidence(
            research,
            source_id=source.id,
            external_id="epistemic-outcome-aug-2022",
            url="https://epistemic-smoke.longcycle.invalid/aug.txt",
            known_at=AUG_KNOWN,
            text="The project achieved first product in July 2022.",
        )

        may_run_id = stable_uuid_exact("epistemic-smoke", "may-extraction")
        await research.save_extraction(
            ExtractionEnvelope(
                run_id=may_run_id,
                document_id=may_document.id,
                extractor_name="epistemic-smoke",
                extractor_version="1.0.0",
                schema_version="epistemic-smoke/v1",
                evidence=(may_evidence,),
                candidates=(),
            )
        )

        aug_run_id = stable_uuid_exact("epistemic-smoke", "aug-extraction")
        fact = FactAssertion(
            id=stable_uuid_exact("epistemic-smoke", "first-product-fact"),
            entity_type=EntityType.PROJECT,
            entity_id=subject_id,
            field_name="project.first_product_status",
            value="achieved first product",
            value_type=FactValueKind.TEXT,
            dimensions=FactDimensions(statistical_scope="project milestone"),
            dimensions_complete=True,
            valid_time_kind=ValidTimeKind.PERIOD,
            valid_time=TimeRange(
                start=datetime(2022, 7, 1, tzinfo=UTC),
                end=datetime(2022, 8, 1, tzinfo=UTC),
            ),
            valid_time_precision=TemporalPrecision.MONTH,
            valid_time_text="July 2022",
            source_published_at=AUG_KNOWN,
            known_at=AUG_KNOWN,
            source_id=source.id,
            document_id=aug_document.id,
            evidence_fragment_id=aug_evidence.id,
            extraction_run_id=aug_run_id,
            extractor_name="epistemic-smoke",
            extractor_version="1.0.0",
            confidence=1.0,
            quality=QualityComponents(
                source_quality=1.0,
                extraction_certainty=1.0,
                entity_match=1.0,
                time_unit_completeness=1.0,
                corroboration=1.0,
                freshness=1.0,
            ),
        )
        await research.save_extraction(
            ExtractionEnvelope(
                run_id=aug_run_id,
                document_id=aug_document.id,
                extractor_name="epistemic-smoke",
                extractor_version="1.0.0",
                schema_version="epistemic-smoke/v1",
                evidence=(aug_evidence,),
                candidates=(fact,),
            )
        )
        await research.append_assertions((fact,))
        result = await research.reconcile_assertion(fact, Reconciler())
        if result.decision.value != "accept":
            raise AssertionError(f"Reality did not reconcile: {result}")
    finally:
        await research.close()

    judgment = JudgmentAssertion(
        id=stable_uuid_exact("epistemic-smoke", "may-judgment"),
        speaker_name_text="Management",
        subject_entity_id=subject_id,
        topic_code="project.first_product_timing",
        judgment_kind=JudgmentKind.GUIDANCE,
        target_time_kind=JudgmentTargetTimeKind.PERIOD,
        target_from=datetime(2022, 5, 1, tzinfo=UTC),
        target_to=datetime(2022, 6, 1, tzinfo=UTC),
        target_precision=TemporalPrecision.MONTH,
        target_text="May 2022",
        value_kind=JudgmentValueKind.TEXT,
        value_text="first product expected in May 2022",
        summary="Management expected first product in May 2022.",
        source_published_at=MAY_KNOWN,
        first_known_at=MAY_KNOWN,
        extraction_run_id=may_run_id,
        source_connector_id=source.id,
        extractor_name="epistemic-smoke",
        extractor_version="1.0.0",
        extraction_confidence=1.0,
        evidence=(
            JudgmentEvidenceRef(
                evidence_fragment_id=may_evidence.id,
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
        metadata={"judgment_key": "may-first-product"},
    )
    judgments = PostgresJudgmentRepository(dsn)
    try:
        await judgments.append_judgments((judgment,))
        await judgments.append_judgments((judgment,))
    finally:
        await judgments.close()

    subject = MemorySubjectRef(entity_id=subject_id)
    reader = PostgresEpistemicMemoryReader(dsn)
    try:
        before_outcome = await reader.snapshot(
            (subject,),
            knowledge_cutoff=datetime(2022, 8, 3, 16, 27, 48, tzinfo=UTC),
        )
        if (len(before_outcome.reality), len(before_outcome.judgments), len(before_outcome.outcomes)) != (0, 1, 0):
            raise AssertionError(f"pre-outcome replay leaked future state: {before_outcome}")

        at_reality = await reader.snapshot((subject,), knowledge_cutoff=AUG_KNOWN)
        if len(at_reality.reality) != 1 or len(at_reality.judgments) != 1:
            raise AssertionError(f"Reality/Judgment boundary is incomplete: {at_reality}")
        canonical = at_reality.reality[0]
        if canonical.valid_time.kind != "period":
            raise AssertionError("canonical valid-time kind was lost")
        if canonical.valid_time.precision != TemporalPrecision.MONTH:
            raise AssertionError("canonical month precision was lost")
        if canonical.valid_time.source_text != "July 2022":
            raise AssertionError("canonical source time text was lost")
    finally:
        await reader.close()

    observation = OutcomeObservation(
        evidence_fragment_id=aug_evidence.id,
        occurrence_from=canonical.valid_time.start,
        occurrence_to=canonical.valid_time.end,
        occurrence_precision=canonical.valid_time.precision,
        occurrence_text=canonical.valid_time.source_text,
        first_known_at=canonical.known_at,
    )
    base_evaluation = evaluate_realized_outcome(
        judgment,
        observation,
        explanation="May target versus source-supported July outcome.",
        evaluated_at=AUG_KNOWN,
    )
    evaluation = base_evaluation.__class__.model_validate(
        {
            **base_evaluation.model_dump(mode="python"),
            "canonical_fact_version_id": canonical.canonical_fact_version_id,
        }
    )
    outcomes = PostgresOutcomeRepository(dsn)
    try:
        await outcomes.append_evaluations((evaluation,))
        await outcomes.append_evaluations((evaluation,))
    finally:
        await outcomes.close()

    reader = PostgresEpistemicMemoryReader(dsn)
    try:
        timeline = await reader.timeline((subject,))
        at_outcome = await reader.snapshot((subject,), knowledge_cutoff=AUG_KNOWN)
    finally:
        await reader.close()

    if (len(at_outcome.reality), len(at_outcome.judgments), len(at_outcome.outcomes)) != (1, 1, 1):
        raise AssertionError(f"integrated PostgreSQL replay is incomplete: {at_outcome}")
    if at_outcome.outcomes[0].timing_delta_value != 2:
        raise AssertionError("month-level Outcome delta was not preserved")

    portable = Path(".artifacts/ci-epistemic-memory.duckdb")
    manifest = seal_industrial_memory(portable, timeline)
    portable_reader = DuckDBEpistemicMemoryReader(portable)
    portable_before = await portable_reader.snapshot(
        (subject,),
        knowledge_cutoff=datetime(2022, 8, 3, 16, 27, 48, tzinfo=UTC),
    )
    portable_at = await portable_reader.snapshot((subject,), knowledge_cutoff=AUG_KNOWN)
    if (len(portable_before.reality), len(portable_before.judgments), len(portable_before.outcomes)) != (0, 1, 0):
        raise AssertionError("portable replay leaked future state")
    if (len(portable_at.reality), len(portable_at.judgments), len(portable_at.outcomes)) != (1, 1, 1):
        raise AssertionError("portable replay does not match PostgreSQL typed memory")
    if not manifest["typed_round_trip"]:
        raise AssertionError("portable memory did not round-trip")

    print("POSTGRES_EPISTEMIC_MEMORY_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
