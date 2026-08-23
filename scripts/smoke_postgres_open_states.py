from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg

from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
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

from smoke_postgres_orientation import (
    CUTOFF,
    EARLY_ENTITY_ID,
    FUTURE_ENTITY_ID,
    INDUSTRY_ID,
    main as seed_orientation,
)


SOURCE_A_KNOWN_AT = datetime(2022, 3, 1, 12, 0, tzinfo=UTC)
SOURCE_B_KNOWN_AT = datetime(2022, 4, 1, 12, 0, tzinfo=UTC)
RESEARCH_RECORDED_AT = datetime(2026, 8, 24, 1, 0, tzinfo=UTC)


async def _ground_state_assertion(
    *,
    repository: PostgresResearchRepository,
    source_id: UUID,
    source_cluster: str,
    value: str,
    known_at: datetime,
    field_name: str = "project.state",
    statistical_scope: str = "synthetic open-state conflict",
) -> tuple[FactAssertion, UUID]:
    identity = f"{source_id}-{field_name}-{source_cluster}"
    payload = RawPayload(
        content=(
            f"Synthetic open-state smoke source says {field_name}={value}.\n"
        ).encode(),
        content_type="text/plain",
        canonical_url=(
            f"https://{source_cluster}.open-state-smoke.longcycle.invalid/"
            f"{field_name.replace('.', '-')}-{source_id}.txt"
        ),
        headers={"x-longcycle-raw-source-materialized": "true"},
        retrieved_at=known_at,
    )
    document = SourceDocument.from_payload(
        source_id=source_id,
        payload=payload,
        blob_key=f"raw/sha256/{payload.sha256[:2]}/{payload.sha256}",
        external_id=f"open-state-smoke-{identity}",
        title=f"Synthetic open-state fixture {identity}",
        published_at=known_at,
        first_known_at=known_at,
        metadata={"synthetic_test_fixture": True},
    )
    document = await repository.save_document(document)
    excerpt = f"Synthetic open-state smoke source says {field_name}={value}."
    evidence = EvidenceFragment.create(document.id, "text:0", excerpt)
    await repository.save_evidence((evidence,))

    run_id = stable_uuid_exact("open-state-smoke-extraction", identity)
    assertion = FactAssertion(
        id=stable_uuid_exact("open-state-smoke-assertion", identity),
        entity_type=EntityType.FACILITY,
        entity_id=EARLY_ENTITY_ID,
        field_name=field_name,
        value=value,
        value_type=FactValueKind.TEXT,
        dimensions=FactDimensions(statistical_scope=statistical_scope),
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
        source_cluster=source_cluster,
        document_id=document.id,
        evidence_fragment_id=evidence.id,
        extraction_run_id=run_id,
        extractor_name="synthetic-open-state-smoke",
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
        metadata={"synthetic_test_fixture": True},
    )
    extraction = ExtractionEnvelope(
        run_id=run_id,
        document_id=document.id,
        extractor_name="synthetic-open-state-smoke",
        extractor_version="1.0.0",
        schema_version="open-state-smoke/v1",
        evidence=(evidence,),
        candidates=(assertion,),
    )
    await repository.save_extraction(extraction)
    await repository.append_assertions((assertion,))
    return assertion, evidence.id


def _seed_current_research_overlay(dsn: str) -> tuple[UUID, UUID]:
    prior_run_id = stable_uuid_exact("open-state-smoke", "prior-run")
    lead_id = stable_uuid_exact("open-state-smoke", "lead")
    disagreement_id = stable_uuid_exact("open-state-smoke", "disagreement")
    assessment_id = stable_uuid_exact("open-state-smoke", "hypothesis")
    sealed_campaign_id = stable_uuid_exact("open-state-smoke", "sealed-campaign")
    sealed_coverage_id = stable_uuid_exact("open-state-smoke", "sealed-coverage")
    unsealed_campaign_id = stable_uuid_exact("open-state-smoke", "unsealed-campaign")
    unsealed_coverage_id = stable_uuid_exact("open-state-smoke", "unsealed-coverage")
    digest_a = "a" * 64
    digest_b = "b" * 64
    digest_c = "c" * 64
    digest_d = "d" * 64
    digest_e = "e" * 64

    with psycopg.connect(dsn) as connection:
        connection.execute(
            """
            INSERT INTO research.model_prior_runs (
                id, industry_node_id, run_mode, source_visibility,
                model_provider, model_name, protocol_version,
                prompt_digest, output_digest, raw_output, created_at
            ) VALUES (
                %s, %s, 'blind_recall', 'none',
                'synthetic', 'open-state-smoke', 'v1',
                %s, %s, '{}'::jsonb, %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (prior_run_id, INDUSTRY_ID, digest_a, digest_b, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.model_memory_leads (
                id, prior_run_id, ordinal, lead_kind,
                subject_entity_id, topic_code, summary,
                recalled_details, suggested_queries, suggested_source_types,
                memory_confidence, importance_score, novelty_score, searchability_score,
                created_at
            ) VALUES (
                %s, %s, 0, 'missing_event',
                %s, 'project.state', 'Synthetic unresolved future-member project-state question',
                '{}'::jsonb, '{}', '{}',
                0.5, 0.8, 0.8, 0.8, %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (lead_id, prior_run_id, FUTURE_ENTITY_ID, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.memory_disagreement_cases (
                id, lead_id, claim_scope, opened_reason, opened_at
            ) VALUES (
                %s, %s, 'project_status',
                'Synthetic authoritative disagreement remains open', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (disagreement_id, lead_id, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.memory_hypothesis_assessments (
                id, lead_id, disposition, direct_source_search_status,
                inference_confidence, reasoning_summary,
                alternative_explanations, falsification_conditions, search_receipt,
                assessor_name, assessor_version, assessed_at
            ) VALUES (
                %s, %s, 'unresolved', 'ongoing',
                0.5, 'Synthetic research-only hypothesis remains unresolved',
                '{}', '{}', '{}'::jsonb,
                'open-state-smoke', '1.0.0', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (assessment_id, lead_id, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.model_memory_campaigns (
                id, industry_node_id, campaign_kind,
                model_provider, model_name, protocol_version,
                manifest_version, manifest_digest, source_visibility, created_at
            ) VALUES (
                %s, %s, 'historical_recall',
                'synthetic', 'open-state-smoke-sealed', 'v1',
                'v1', %s, 'none', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (sealed_campaign_id, INDUSTRY_ID, digest_c, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.model_memory_coverage_cells (
                id, campaign_id, snapshot_label, dimension_type, dimension_key,
                coverage_state, notes, created_at
            ) VALUES (
                %s, %s, 'sealed-final', 'mechanism', 'qualification_delay',
                'thin', 'Synthetic sealed model-memory coverage gap', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (sealed_coverage_id, sealed_campaign_id, RESEARCH_RECORDED_AT),
        )
        connection.execute(
            """
            INSERT INTO research.model_memory_campaign_seals (
                campaign_id, sealed_at, stop_reason, coverage_summary,
                lead_count, high_importance_lead_count, output_digest
            ) VALUES (
                %s, %s, 'Synthetic saturation reached', '{}'::jsonb,
                1, 1, %s
            )
            ON CONFLICT (campaign_id) DO NOTHING
            """,
            (sealed_campaign_id, RESEARCH_RECORDED_AT, digest_d),
        )

        # Deliberately create a newer UNSEALED campaign with the same coverage dimension.
        # A truthful current overlay must ignore it until it has an immutable seal.
        connection.execute(
            """
            INSERT INTO research.model_memory_campaigns (
                id, industry_node_id, campaign_kind,
                model_provider, model_name, protocol_version,
                manifest_version, manifest_digest, source_visibility, created_at
            ) VALUES (
                %s, %s, 'historical_recall',
                'synthetic', 'open-state-smoke-unsealed', 'v1',
                'v2', %s, 'none', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (
                unsealed_campaign_id,
                INDUSTRY_ID,
                digest_e,
                RESEARCH_RECORDED_AT + timedelta(hours=1),
            ),
        )
        connection.execute(
            """
            INSERT INTO research.model_memory_coverage_cells (
                id, campaign_id, snapshot_label, dimension_type, dimension_key,
                coverage_state, notes, created_at
            ) VALUES (
                %s, %s, 'unfinished', 'mechanism', 'qualification_delay',
                'dense', 'Must be ignored because campaign is unsealed', %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (
                unsealed_coverage_id,
                unsealed_campaign_id,
                RESEARCH_RECORDED_AT + timedelta(hours=1),
            ),
        )

    return sealed_campaign_id, unsealed_campaign_id


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    await seed_orientation()

    registry = PostgresSourceRegistry(dsn)
    try:
        source_a = await registry.register(
            build_http_source_definition(
                name="Synthetic open-state source A",
                publisher_domain="a.open-state-smoke.longcycle.invalid",
                kind=SourceKind.COMPANY,
                quality_grade=QualityGrade.A,
            )
        )
        source_b = await registry.register(
            build_http_source_definition(
                name="Synthetic open-state source B",
                publisher_domain="b.open-state-smoke.longcycle.invalid",
                kind=SourceKind.COMPANY,
                quality_grade=QualityGrade.A,
            )
        )
    finally:
        await registry.close()

    repository = PostgresResearchRepository(dsn, bucket_name="open-state-smoke")
    try:
        assertion_a, evidence_a = await _ground_state_assertion(
            repository=repository,
            source_id=source_a.id,
            source_cluster="source-a",
            value="commissioning",
            known_at=SOURCE_A_KNOWN_AT,
        )
        first_result = await repository.reconcile_assertion(assertion_a, Reconciler())
        if first_result.decision.value != "accept":
            raise AssertionError(f"first open-state assertion did not reconcile: {first_result}")

        assertion_b, evidence_b = await _ground_state_assertion(
            repository=repository,
            source_id=source_b.id,
            source_cluster="source-b",
            value="construction",
            known_at=SOURCE_B_KNOWN_AT,
        )
        second_result = await repository.reconcile_assertion(assertion_b, Reconciler())
        if second_result.decision.value != "conflict":
            raise AssertionError(f"second open-state assertion did not conflict: {second_result}")

        # A second conflict case uses different connectors but the SAME source cluster.
        # It must remain an archive conflict internally, but must not be promoted to a
        # researcher-facing multi-source disagreement.
        mirror_a, _ = await _ground_state_assertion(
            repository=repository,
            source_id=source_a.id,
            source_cluster="mirrored-upstream",
            value="pilot",
            known_at=SOURCE_A_KNOWN_AT,
            field_name="project.mirror_state",
            statistical_scope="synthetic mirrored-source conflict",
        )
        mirror_first = await repository.reconcile_assertion(mirror_a, Reconciler())
        if mirror_first.decision.value != "accept":
            raise AssertionError(f"first mirror assertion did not reconcile: {mirror_first}")
        mirror_b, _ = await _ground_state_assertion(
            repository=repository,
            source_id=source_b.id,
            source_cluster="mirrored-upstream",
            value="commercial",
            known_at=SOURCE_B_KNOWN_AT,
            field_name="project.mirror_state",
            statistical_scope="synthetic mirrored-source conflict",
        )
        mirror_second = await repository.reconcile_assertion(mirror_b, Reconciler())
        if mirror_second.decision.value != "conflict":
            raise AssertionError(f"second mirror assertion did not conflict: {mirror_second}")
    finally:
        await repository.close()

    sealed_campaign_id, unsealed_campaign_id = _seed_current_research_overlay(dsn)

    base_command = [
        "longcycle",
        "--json",
        "research",
        "open-states",
        str(INDUSTRY_ID),
        CUTOFF.isoformat(),
    ]
    historical_run = subprocess.run(
        base_command,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    historical_outer = json.loads(historical_run.stdout)
    if historical_outer.get("ok") is not True:
        raise AssertionError(historical_outer)
    historical_result = historical_outer["result"]
    if historical_result["schema_version"] != "longcycle-researcher-open-states/v1":
        raise AssertionError(historical_result)
    historical = historical_result["historical_at_cutoff"]
    disagreements = historical["reality_source_disagreements"]
    if len(disagreements) != 1:
        raise AssertionError(
            f"expected only the independent-source disagreement; got {disagreements}"
        )
    disagreement = disagreements[0]
    if disagreement["predicate_code"] != "project.state":
        raise AssertionError(disagreement)
    if disagreement["archive_disagreement_known_at"] != SOURCE_B_KNOWN_AT.isoformat():
        raise AssertionError(disagreement)
    source_ids = {row["source_id"] for row in disagreement["assertions"]}
    if source_ids != {str(source_a.id), str(source_b.id)}:
        raise AssertionError(disagreement)
    source_clusters = {row["source_cluster"] for row in disagreement["assertions"]}
    if source_clusters != {"source-a", "source-b"}:
        raise AssertionError(disagreement)
    evidence_ids = {
        value
        for row in disagreement["assertions"]
        for value in row["evidence_fragment_ids"]
    }
    if not {str(evidence_a), str(evidence_b)}.issubset(evidence_ids):
        raise AssertionError(disagreement)
    if disagreement["current_archive_curation"]["is_historical_market_knowledge"] is not False:
        raise AssertionError(disagreement)

    overlay = historical_result["current_research_overlay"]
    if overlay["included"] is not False:
        raise AssertionError(overlay)
    if overlay["disagreements"] or overlay["hypotheses"] or overlay["model_memory_coverage_gaps"]:
        raise AssertionError("default historical view leaked current research overlay")

    current_run = subprocess.run(
        [*base_command, "--include-current-research"],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    current_outer = json.loads(current_run.stdout)
    if current_outer.get("ok") is not True:
        raise AssertionError(current_outer)
    current_overlay = current_outer["result"]["current_research_overlay"]
    if current_overlay["included"] is not True:
        raise AssertionError(current_overlay)
    if current_overlay["is_historical_market_knowledge"] is not False:
        raise AssertionError(current_overlay)
    if current_overlay["cutoff_filter_applied"] is not False:
        raise AssertionError(current_overlay)
    if not current_overlay["disagreements"]:
        raise AssertionError(current_overlay)
    if current_overlay["disagreements"][0]["subject"]["entity_id"] != str(FUTURE_ENTITY_ID):
        raise AssertionError(
            "current research record for post-cutoff membership was incorrectly filtered"
        )
    if current_overlay["hypotheses"][0]["disposition"] != "unresolved":
        raise AssertionError(current_overlay)
    coverage = current_overlay["model_memory_coverage_gaps"]
    if len(coverage) != 1 or coverage[0]["coverage_state"] != "thin":
        raise AssertionError(current_overlay)
    if coverage[0]["campaign_id"] != str(sealed_campaign_id):
        raise AssertionError("coverage must come from latest sealed campaign")
    if any(row["campaign_id"] == str(unsealed_campaign_id) for row in coverage):
        raise AssertionError("unsealed campaign leaked into current coverage overlay")

    boundary = current_outer["result"]["boundary"]
    required = {
        "membership_visibility_reuses_industry_orientation_owner",
        "historical_judgment_visibility_delegated_to_epistemic_snapshot",
        "reality_conflict_visibility_uses_member_source_known_at",
        "reality_source_independence_reuses_fact_source_cluster",
        "conflict_case_opened_at_is_not_historical_known_at",
        "current_research_overlay_is_opt_in",
        "current_research_overlay_is_not_cutoff_filtered",
        "current_research_scope_uses_own_run_provenance",
        "model_memory_coverage_uses_latest_sealed_campaign",
        "model_memory_coverage_is_not_archive_absence",
        "absence_of_records_does_not_create_an_unknown_state",
        "not_found_is_not_false",
    }
    if not all(boundary.get(key) is True for key in required):
        raise AssertionError(boundary)

    print("POSTGRES_RESEARCHER_OPEN_STATES_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
