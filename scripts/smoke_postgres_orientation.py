from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from longcycle.application.industry_membership_projection import (
    project_resolved_industry_membership,
)
from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    TemporalPrecision,
    ValidTimeKind,
)
from longcycle.domain.models import (
    EvidenceFragment,
    FactAssertion,
    FactDimensions,
    FactEvidenceRef,
    QualityComponents,
    SourceConnector,
    SourceDocument,
    TimeRange,
)
from longcycle.domain.orientation import IndustryMembershipSemanticJudgment
from longcycle.migrations.runner import MigrationRunner
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_orientation import (
    PostgresIndustryMembershipProjectionStore,
)


INDUSTRY_ID = UUID("484376e9-4ee9-505c-888d-0ef0ac7f4c28")
EARLY_ENTITY_ID = UUID("9ec2ad00-d7a5-5d14-8708-8b9bbc01560c")
FUTURE_ENTITY_ID = UUID("e173b173-7d11-5712-a756-3f8af1e4c9d7")
CUTOFF = datetime(2023, 1, 1, 12, 0, tzinfo=UTC)
EARLY_KNOWN_AT = datetime(2022, 1, 1, 12, 0, tzinfo=UTC)
FUTURE_KNOWN_AT = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)


class _SmokeSemanticJudge:
    async def judge_industry_membership(
        self,
        resolution,
        *,
        reasoning_mode: Literal["standard", "deep"],
    ) -> IndustryMembershipSemanticJudgment:
        selected = resolution.selected_assertions[0]
        now = resolution.resolved_at
        return IndustryMembershipSemanticJudgment(
            reasoning_mode=reasoning_mode,
            selected_assertion_id=selected.id,
            can_materialize=True,
            confidence=0.99,
            reasoning_summary="Synthetic smoke semantic judge selected the sole source assertion.",
            provider_name="orientation-smoke",
            model_name="deterministic-smoke-judge",
            model_version="1",
            started_at=now,
            completed_at=now,
        )


def _quality() -> QualityComponents:
    return QualityComponents(
        source_quality=1.0,
        extraction_certainty=1.0,
        entity_match=1.0,
        time_unit_completeness=1.0,
        corroboration=0.0,
        freshness=1.0,
        conflict_penalty=0.0,
    )


def _assertion(
    *,
    entity_id: UUID,
    known_at: datetime,
    document_id: UUID,
    evidence_id: UUID,
) -> FactAssertion:
    return FactAssertion(
        id=uuid4(),
        entity_type=EntityType.COMPANY,
        entity_id=entity_id,
        field_name="industry.membership",
        value="participant",
        value_type=FactValueKind.TEXT,
        dimensions=FactDimensions(statistical_scope="orientation smoke"),
        dimensions_complete=True,
        valid_time_kind=ValidTimeKind.UNKNOWN,
        valid_time=TimeRange(),
        valid_time_precision=TemporalPrecision.UNKNOWN,
        known_at=known_at,
        source_id=uuid4(),
        document_id=document_id,
        evidence=(FactEvidenceRef(evidence_fragment_id=evidence_id),),
        extraction_run_id=uuid4(),
        extractor_name="orientation-smoke",
        extractor_version="1",
        source_cluster=f"orientation-smoke-{entity_id}",
        confidence=1.0,
        quality=_quality(),
        metadata={
            "industry_node_id": str(INDUSTRY_ID),
            "exposure_type": "direct",
            "subject_canonical_name": str(entity_id),
        },
    )


async def _seed_source_and_evidence(
    repository: PostgresResearchRepository,
    *,
    entity_id: UUID,
    known_at: datetime,
) -> tuple[UUID, UUID]:
    connector = SourceConnector(
        id=uuid4(),
        name=f"orientation-smoke-{entity_id}",
        source_type="synthetic",
        endpoint="https://example.invalid/orientation-smoke",
        base_domain="example.invalid",
        publisher="Longcycle smoke",
    )
    await repository.save_connector(connector)
    document = SourceDocument(
        id=uuid4(),
        connector_id=connector.id,
        canonical_url=f"https://example.invalid/orientation-smoke/{entity_id}",
        published_at=known_at,
        first_known_at=known_at,
        retrieved_at=known_at,
        content_sha256="0" * 64,
        blob_key=f"synthetic/orientation-smoke/{entity_id}",
        byte_length=1,
        content_type="text/plain",
    )
    await repository.save_document(document)
    evidence = EvidenceFragment.create(
        document_id=document.id,
        locator="synthetic:0",
        excerpt="synthetic orientation evidence",
    )
    await repository.save_evidence((evidence,))
    return document.id, evidence.id


async def main() -> None:
    database_url = os.environ["LONGCYCLE_DATABASE_URL"]
    runner = MigrationRunner(database_url)
    await runner.upgrade()

    repository = PostgresResearchRepository(database_url)
    try:
        async with repository.connection() as connection:
            await connection.execute(
                """
                INSERT INTO core.taxonomy_nodes (id, taxonomy_name, node_code, canonical_name, node_kind)
                VALUES (%s, 'industry', 'orientation-smoke', 'Orientation Smoke Industry', 'industry')
                ON CONFLICT (id) DO NOTHING
                """,
                (INDUSTRY_ID,),
            )
            for entity_id in (EARLY_ENTITY_ID, FUTURE_ENTITY_ID):
                await connection.execute(
                    """
                    INSERT INTO core.entities (id, entity_type, canonical_name)
                    VALUES (%s, 'company', %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (entity_id, str(entity_id)),
                )

        early_document, early_evidence = await _seed_source_and_evidence(
            repository,
            entity_id=EARLY_ENTITY_ID,
            known_at=EARLY_KNOWN_AT,
        )
        future_document, future_evidence = await _seed_source_and_evidence(
            repository,
            entity_id=FUTURE_ENTITY_ID,
            known_at=FUTURE_KNOWN_AT,
        )
        early_assertion = _assertion(
            entity_id=EARLY_ENTITY_ID,
            known_at=EARLY_KNOWN_AT,
            document_id=early_document,
            evidence_id=early_evidence,
        )
        future_assertion = _assertion(
            entity_id=FUTURE_ENTITY_ID,
            known_at=FUTURE_KNOWN_AT,
            document_id=future_document,
            evidence_id=future_evidence,
        )
        await repository.append_assertions((early_assertion, future_assertion))
        early_resolution = uuid4()
        future_resolution = uuid4()
        async with repository.connection() as connection:
            for resolution_id, assertion, resolved_at in (
                (early_resolution, early_assertion, datetime(2026, 8, 24, tzinfo=UTC)),
                (future_resolution, future_assertion, datetime(2026, 8, 24, 0, 1, tzinfo=UTC)),
            ):
                await connection.execute(
                    """
                    INSERT INTO research.fact_resolutions (
                        id, fact_key_id, selected_assertion_ids, confidence,
                        resolution_reason, resolved_at, resolver_name, resolver_version
                    )
                    SELECT %s, assertion.fact_key_id, ARRAY[%s]::uuid[], 0.99,
                           'orientation smoke selected source assertion', %s,
                           'orientation-smoke', '1'
                    FROM research.fact_assertions assertion
                    WHERE assertion.id = %s
                    """,
                    (resolution_id, assertion.id, resolved_at, assertion.id),
                )
                await connection.execute(
                    """
                    INSERT INTO research.fact_resolution_assertions (
                        resolution_id, assertion_id, disposition, contribution_weight
                    ) VALUES (%s, %s, 'selected', 1.0)
                    """,
                    (resolution_id, assertion.id),
                )
    finally:
        await repository.close()

    semantic_judge = _SmokeSemanticJudge()
    projection_store = PostgresIndustryMembershipProjectionStore(database_url)
    try:
        early_projection = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
            judgment_run_writer=projection_store,
            decision_writer=projection_store,
            membership_writer=projection_store,
            resolution_id=early_resolution,
        )
        future_projection = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
            judgment_run_writer=projection_store,
            decision_writer=projection_store,
            membership_writer=projection_store,
            resolution_id=future_resolution,
        )
        repeated_early = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
            judgment_run_writer=projection_store,
            decision_writer=projection_store,
            membership_writer=projection_store,
            resolution_id=early_resolution,
        )
    finally:
        await projection_store.close()

    if repeated_early != early_projection:
        raise AssertionError("industry membership projection was not idempotent")
    if early_projection.known_at != EARLY_KNOWN_AT:
        raise AssertionError("membership projection lost source-known time")
    if future_projection.known_at != FUTURE_KNOWN_AT:
        raise AssertionError("future membership projection lost source-known time")
    if early_projection.system_from == early_projection.known_at:
        raise AssertionError("semantic decision time collapsed into historical known time")

    with tempfile.TemporaryDirectory(prefix="longcycle-orientation-smoke-") as temporary:
        output_path = Path(temporary) / "orientation.json"
        completed = subprocess.run(
            ["longcycle", "--json", "research", "orient", str(INDUSTRY_ID), CUTOFF.isoformat()],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "research orient CLI failed "
                f"exit={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        output_path.write_text(completed.stdout, encoding="utf-8")
        outer = json.loads(completed.stdout)

    if outer.get("ok") is not True:
        raise AssertionError(outer)
    result = outer["result"]
    subjects = result["subjects"]
    if [row["subject_id"] for row in subjects] != [str(EARLY_ENTITY_ID)]:
        raise AssertionError(f"future-known membership leaked or early membership was lost: {subjects}")
    early = subjects[0]
    if early["memory_counts"] != {"reality": 1, "judgments": 0, "outcomes": 0}:
        raise AssertionError(early)
    if str(early_evidence) not in early["evidence_fragment_ids"]:
        raise AssertionError(early)
    if early["memberships"][0]["semantic_decision_id"] != str(early_projection.semantic_decision_id):
        raise AssertionError("orientation lost semantic decision audit identity")
    if early["memberships"][0]["semantic_decision_supporting_run_count"] != 2:
        raise AssertionError("orientation lost repeated model-judgment audit history")
    if early["memberships"][0]["semantic_decision_latest_reasoning_mode"] != "standard":
        raise AssertionError("orientation lost latest model-judgment reasoning mode")
    if early["discovery_certainty"] != "direct":
        raise AssertionError(early)
    if result["boundary"]["membership_semantics_can_be_model_judged_but_not_source_truth"] is not True:
        raise AssertionError(result["boundary"])
    if result["boundary"]["presentation_may_add_labelled_interpretation_but_never_truth_promotion"] is not True:
        raise AssertionError(result["boundary"])
    print("POSTGRES_INDUSTRY_ORIENTATION_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
