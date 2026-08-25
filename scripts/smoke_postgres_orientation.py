from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

import psycopg

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_orientation import (
    PostgresIndustryMembershipProjectionStore,
)
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.industry_membership_projection import (
    project_resolved_industry_membership,
)
from longcycle.application.reconciliation import Reconciler
from longcycle.application.source_registration import build_http_source_definition
from longcycle.domain.enums import (
    EntityType,
    FactValueKind,
    QualityGrade,
    SourceKind,
    TemporalPrecision,
    ValidTimeKind,
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
from longcycle.domain.orientation import (
    IndustryMembershipSemanticJudgment,
    ResolvedIndustryMembershipResolution,
)


TAXONOMY_ID = stable_uuid_exact("orientation-smoke", "taxonomy")
INDUSTRY_ID = stable_uuid_exact("orientation-smoke", "industry")
EARLY_ENTITY_ID = stable_uuid_exact("orientation-smoke", "early-facility")
FUTURE_ENTITY_ID = stable_uuid_exact("orientation-smoke", "future-facility")
EARLY_KNOWN_AT = datetime(2021, 6, 1, 12, 0, tzinfo=UTC)
FUTURE_KNOWN_AT = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
CUTOFF = datetime(2023, 1, 1, 12, 0, tzinfo=UTC)


class _SyntheticMembershipSemanticJudge:
    """Deterministic CI substitute for the production large-model semantic judge."""

    async def judge_industry_membership(
        self,
        resolution: ResolvedIndustryMembershipResolution,
        *,
        reasoning_mode: Literal["standard", "deep"],
    ) -> IndustryMembershipSemanticJudgment:
        if reasoning_mode != "standard":
            raise AssertionError("single-definition synthetic smoke must not require deep reasoning")
        if len(resolution.selected_assertions) != 1:
            raise AssertionError("synthetic smoke expects one source-backed candidate")
        return IndustryMembershipSemanticJudgment(
            reasoning_mode="standard",
            selected_assertion_id=resolution.selected_assertions[0].id,
            material_conflict_detected=False,
            can_materialize=True,
            reasoning_summary="Synthetic fixture contains one unambiguous membership definition.",
            model_name="deterministic-ci-membership-semantic-judge",
            model_version="1",
            decided_at=resolution.resolved_at,
        )


async def _ground_membership_assertion(
    *,
    dsn: str,
    repository: PostgresResearchRepository,
    source_id: UUID,
    entity_id: UUID,
    label: str,
    known_at: datetime,
) -> tuple[UUID, UUID]:
    payload = RawPayload(
        content=(
            f"Synthetic orientation smoke fixture: {label} is a conversion facility "
            "in the synthetic orientation industry.\n"
        ).encode(),
        content_type="text/plain",
        canonical_url=f"https://orientation-smoke.longcycle.invalid/{entity_id}.txt",
        headers={"x-longcycle-raw-source-materialized": "true"},
        retrieved_at=known_at,
    )
    document = SourceDocument.from_payload(
        source_id=source_id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id=f"orientation-smoke-{entity_id}",
        title=f"Synthetic orientation fixture for {label}",
        published_at=known_at,
        first_known_at=known_at,
        metadata={"synthetic_test_fixture": True},
    )
    document = await repository.save_document(document)
    excerpt = (
        f"Synthetic orientation smoke fixture: {label} is a conversion facility "
        "in the synthetic orientation industry."
    )
    evidence = EvidenceFragment.create(document.id, "text:0", excerpt)
    await repository.save_evidence((evidence,))

    run_id = stable_uuid_exact("orientation-smoke-extraction", str(document.id))
    assertion = FactAssertion(
        id=stable_uuid_exact("orientation-smoke-membership-assertion", str(evidence.id)),
        entity_type=EntityType.FACILITY,
        entity_id=entity_id,
        field_name="industry.membership",
        value="conversion_facility",
        value_type=FactValueKind.TEXT,
        dimensions=FactDimensions(statistical_scope="synthetic orientation membership"),
        dimensions_complete=True,
        valid_time_kind=ValidTimeKind.PERIOD,
        valid_time=TimeRange(
            start=datetime(2020, 1, 1, tzinfo=UTC),
            end=datetime(2030, 1, 1, tzinfo=UTC),
        ),
        valid_time_precision=TemporalPrecision.RANGE,
        source_published_at=known_at,
        known_at=known_at,
        source_id=source_id,
        document_id=document.id,
        evidence_fragment_id=evidence.id,
        extraction_run_id=run_id,
        extractor_name="synthetic-orientation-smoke",
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
        metadata={
            "synthetic_test_fixture": True,
            "industry_node_id": str(INDUSTRY_ID),
            "exposure_type": "direct",
        },
    )
    extraction = ExtractionEnvelope(
        run_id=run_id,
        document_id=document.id,
        extractor_name="synthetic-orientation-smoke",
        extractor_version="1.0.0",
        schema_version="orientation-smoke/v1",
        evidence=(evidence,),
        candidates=(assertion,),
    )
    await repository.save_extraction(extraction)
    await repository.append_assertions((assertion,))
    result = await repository.reconcile_assertion(assertion, Reconciler())
    if result.decision.value != "accept":
        raise AssertionError(f"orientation membership did not reconcile: {result}")

    with psycopg.connect(dsn) as connection:
        row = connection.execute(
            """
            SELECT resolution_id
            FROM research.fact_resolution_assertions
            WHERE assertion_id = %s AND disposition = 'selected'
            """,
            (assertion.id,),
        ).fetchone()
    if row is None:
        raise AssertionError("orientation membership has no selected resolution")
    return row[0], evidence.id


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    source = build_http_source_definition(
        name="Synthetic PostgreSQL orientation smoke source",
        publisher_domain="orientation-smoke.longcycle.invalid",
        kind=SourceKind.COMPANY,
        quality_grade=QualityGrade.A,
    )
    registry = PostgresSourceRegistry(dsn)
    try:
        source = await registry.register(source)
    finally:
        await registry.close()

    with psycopg.connect(dsn) as connection:
        connection.execute(
            """
            INSERT INTO core.taxonomies (id, code, version, name, description)
            VALUES (%s, 'orientation-smoke', 'v1', 'Synthetic orientation smoke taxonomy',
                    'Ephemeral CI-only taxonomy; never research data')
            ON CONFLICT (id) DO NOTHING
            """,
            (TAXONOMY_ID,),
        )
        connection.execute(
            """
            INSERT INTO core.taxonomy_nodes (
                id, taxonomy_id, code, slug, canonical_name, node_kind, archetype, attributes
            ) VALUES (%s, %s, 'synthetic-conversion', 'synthetic-conversion',
                      'Synthetic Conversion Industry', 'industry', 'synthetic',
                      '{"synthetic_test_fixture": true}'::jsonb)
            ON CONFLICT (id) DO NOTHING
            """,
            (INDUSTRY_ID, TAXONOMY_ID),
        )
        for entity_id, canonical_name, normalized_name in (
            (EARLY_ENTITY_ID, "Early Synthetic Facility", "early synthetic facility"),
            (FUTURE_ENTITY_ID, "Future-known Synthetic Facility", "future-known synthetic facility"),
        ):
            connection.execute(
                """
                INSERT INTO core.entities (
                    id, entity_type, canonical_name, normalized_name, lifecycle_status, attributes
                ) VALUES (%s, 'facility', %s, %s, 'active',
                          '{"synthetic_test_fixture": true}'::jsonb)
                ON CONFLICT (id) DO NOTHING
                """,
                (entity_id, canonical_name, normalized_name),
            )

    repository = PostgresResearchRepository(dsn, bucket_name="orientation-smoke")
    try:
        early_resolution, early_evidence = await _ground_membership_assertion(
            dsn=dsn,
            repository=repository,
            source_id=source.id,
            entity_id=EARLY_ENTITY_ID,
            label="Early Synthetic Facility",
            known_at=EARLY_KNOWN_AT,
        )
        future_resolution, _future_evidence = await _ground_membership_assertion(
            dsn=dsn,
            repository=repository,
            source_id=source.id,
            entity_id=FUTURE_ENTITY_ID,
            label="Future-known Synthetic Facility",
            known_at=FUTURE_KNOWN_AT,
        )
    finally:
        await repository.close()

    projection_store = PostgresIndustryMembershipProjectionStore(
        dsn,
        bucket_name="orientation-smoke",
    )
    semantic_judge = _SyntheticMembershipSemanticJudge()
    try:
        early_projection = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
            decision_writer=projection_store,
            membership_writer=projection_store,
            resolution_id=early_resolution,
        )
        future_projection = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
            decision_writer=projection_store,
            membership_writer=projection_store,
            resolution_id=future_resolution,
        )
        repeated_early = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            semantic_judge=semantic_judge,
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
    if early_projection.semantic_decision_id is None:
        raise AssertionError("membership projection lost semantic decision audit provenance")

    with tempfile.TemporaryDirectory(prefix="longcycle-orientation-smoke-") as temporary:
        output_path = Path(temporary) / "orientation.json"
        command = [
            "longcycle",
            "--json",
            "research",
            "orient",
            str(INDUSTRY_ID),
            CUTOFF.isoformat(),
        ]
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        output_path.write_text(completed.stdout, encoding="utf-8")
        outer = json.loads(completed.stdout)

    if outer.get("ok") is not True:
        raise AssertionError(outer)
    result = outer["result"]
    if result["schema_version"] != "longcycle-researcher-industry-orientation/v1":
        raise AssertionError(result)
    if result["industry"]["industry_node_id"] != str(INDUSTRY_ID):
        raise AssertionError(result)
    if result["industry"]["canonical_name"] != "Synthetic Conversion Industry":
        raise AssertionError(result)

    subjects = result["subjects"]
    if [row["subject_id"] for row in subjects] != [str(EARLY_ENTITY_ID)]:
        raise AssertionError(
            "future-known membership crossed the knowledge cutoff or early membership was lost: "
            f"{subjects}"
        )
    early = subjects[0]
    if early["canonical_name"] != "Early Synthetic Facility":
        raise AssertionError(early)
    if early["memory_counts"] != {"reality": 1, "judgments": 0, "outcomes": 0}:
        raise AssertionError(early)
    if early["trajectory_replay"] != {"subject_id": str(EARLY_ENTITY_ID)}:
        raise AssertionError(early)
    if str(early_evidence) not in early["evidence_fragment_ids"]:
        raise AssertionError(early)
    if early["memberships"][0]["semantic_decision_id"] != str(early_projection.semantic_decision_id):
        raise AssertionError("orientation lost semantic decision audit identity")
    if early["archive_coverage"]["world_state_inference"] != "none":
        raise AssertionError("archive coverage incorrectly inferred a world state")
    if result["explicit_open_states"] != []:
        raise AssertionError("orientation invented an open/unknown state")

    boundary = result["boundary"]
    required_boundary = {
        "membership_requires_fact_resolution_and_evidence",
        "membership_semantic_selection_is_model_audited",
        "model_semantic_decision_is_not_source_evidence_or_canonical_reality",
        "membership_visibility_uses_source_known_at",
        "researcher_discovery_allows_deterministic_entailment",
        "entailed_discovery_does_not_create_membership_or_role",
        "deterministic_role_entailment_allowed_when_rule_is_auditable",
        "ambiguous_role_importance_causality_belong_to_labeled_model_judgment",
        "presentation_does_not_promote_analysis_to_truth",
        "truth_bearing_catalog_and_memory_reads_fail_closed",
        "optional_research_discovery_enrichment_degrades_gracefully",
        "system_from_is_not_historical_known_at",
        "memory_visibility_delegated_to_epistemic_snapshot",
        "same_knowledge_cutoff_used_for_membership_discovery_and_memory",
        "archive_absence_is_research_coverage_not_world_state",
        "presentation_invents_no_unknown_or_controversy",
    }
    if not all(boundary.get(key) is True for key in required_boundary):
        raise AssertionError(boundary)

    print("POSTGRES_INDUSTRY_ORIENTATION_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
