from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from longcycle.adapters.storage.postgres_epistemic import PostgresEpistemicMemoryReader
from longcycle.adapters.storage.postgres_evidence import PostgresEvidenceDrilldownReader
from longcycle.adapters.storage.postgres_open_states import PostgresOpenStateReader
from longcycle.adapters.storage.postgres_orientation import (
    PostgresIndustryMembershipProjectionStore,
    PostgresIndustryOrientationReader,
)
from longcycle.application.evidence_drilldown import build_researcher_evidence_drilldown
from longcycle.application.industry_membership_projection import project_resolved_industry_membership
from longcycle.application.industry_orientation import build_researcher_industry_orientation
from longcycle.application.open_state_view import build_researcher_open_state_view
from longcycle.application.trajectory_view import build_researcher_trajectory_view
from longcycle.domain.epistemic import MemorySubjectRef


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATION_SPEC = ROOT / (
    "research_data/memory/cross-industry/"
    "2026-08-25-samsung-orientation-real-acceptance-orchestration-v2.json"
)
TAXONOMY_ID = UUID("60c8e8c1-d3ba-51fe-b28e-3d0e280ab131")
INDUSTRY_ID = UUID("180d06d1-2f31-5a7c-8c43-16d0b3d3cce7")
SAMSUNG_ID = UUID("e9ea0f8f-29a7-52de-94d3-ee4c1c9e9066")
BEFORE_KNOWN = datetime(2024, 10, 31, 23, 59, 59, tzinfo=UTC)
KNOWN_AT = datetime(2024, 11, 1, 0, 0, tzinfo=UTC)
EXPECTED_EXCERPT = (
    "In the third quarter, total HBM sales grew by more than 70% Q-on-Q with both "
    "HBM3E 8 and 12 stack layer products in mass production and generating sales."
)


def _seed_current_taxonomy(dsn: str) -> None:
    """Create only current catalog identity needed by the researcher read model.

    The taxonomy row is current research ontology, not historical market knowledge. Historical
    membership visibility still comes only from the source-grounded Fact known time.
    """

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        connection.execute(
            """
            INSERT INTO core.taxonomies (id, code, version, name, description)
            VALUES (
                %s,
                'memory-semiconductors-real-acceptance',
                'v1',
                'Memory semiconductors real-source acceptance taxonomy',
                'CI ontology identity only; historical membership requires grounded Evidence'
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (TAXONOMY_ID,),
        )
        connection.execute(
            """
            INSERT INTO core.taxonomy_nodes (
                id, taxonomy_id, code, slug, canonical_name, node_kind, archetype, attributes
            ) VALUES (
                %s,
                %s,
                'memory-semiconductors',
                'memory-semiconductors',
                'Memory Semiconductors',
                'industry',
                'semiconductor-memory',
                '{"real_source_acceptance_fixture": true}'::jsonb
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (INDUSTRY_ID, TAXONOMY_ID),
        )
        row = connection.execute(
            """
            SELECT node.taxonomy_id, node.canonical_name, node.node_kind
            FROM core.taxonomy_nodes node
            WHERE node.id = %s
            """,
            (INDUSTRY_ID,),
        ).fetchone()
        expected = {
            "taxonomy_id": TAXONOMY_ID,
            "canonical_name": "Memory Semiconductors",
            "node_kind": "industry",
        }
        if row is None or dict(row) != expected:
            raise AssertionError(f"real orientation taxonomy identity mismatch: {row}")


def _execute_real_grounded_membership(dsn: str) -> tuple[UUID, UUID, datetime]:
    with tempfile.TemporaryDirectory(prefix="longcycle-real-orientation-") as temporary:
        root = Path(temporary)
        work_dir = root / "work"
        output_path = root / "orchestration-execution.json"
        completed = subprocess.run(
            [
                "longcycle",
                "--json",
                "research",
                "run",
                str(ORCHESTRATION_SPEC),
                "--material-root",
                str(ROOT),
                "--repo-root",
                str(ROOT),
                "--work-dir",
                str(work_dir),
                "--output",
                str(output_path),
                "--skip-db-upgrade",
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "LONGCYCLE_DATABASE_URL": dsn},
        )
        outer = json.loads(completed.stdout)
        if outer.get("ok") is not True:
            raise AssertionError(outer)
        persisted = json.loads(output_path.read_text(encoding="utf-8"))
        if persisted.get("ok") is not True:
            raise AssertionError(persisted)

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        rows = connection.execute(
            """
            SELECT resolution.id AS resolution_id,
                   assertion.id AS assertion_id,
                   assertion.first_known_at,
                   evidence.evidence_fragment_id
            FROM research.fact_resolutions resolution
            JOIN research.fact_resolution_assertions selected
              ON selected.resolution_id = resolution.id
             AND selected.disposition = 'selected'
            JOIN research.fact_assertions assertion
              ON assertion.id = selected.assertion_id
            JOIN research.assertion_evidence evidence
              ON evidence.assertion_id = assertion.id
             AND evidence.evidence_role = 'supporting'
            WHERE assertion.subject_entity_id = %s
              AND assertion.predicate_code = 'industry.membership'
              AND assertion.value_kind = 'text'
              AND assertion.value_text = 'hbm3e_producer'
            ORDER BY resolution.resolved_at, evidence.evidence_fragment_id
            """,
            (SAMSUNG_ID,),
        ).fetchall()
    if len(rows) != 1:
        raise AssertionError(f"expected one grounded Samsung membership resolution, got {rows}")
    row = rows[0]
    if row["first_known_at"] != KNOWN_AT:
        raise AssertionError("membership Fact known time drifted from preserved source Evidence")
    return row["resolution_id"], row["evidence_fragment_id"], row["first_known_at"]


async def _verify_researcher_path(
    *,
    dsn: str,
    resolution_id: UUID,
    evidence_fragment_id: UUID,
) -> dict[str, object]:
    projection_store = PostgresIndustryMembershipProjectionStore(
        dsn,
        bucket_name="real-orientation-acceptance",
    )
    try:
        projection = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            membership_writer=projection_store,
            resolution_id=resolution_id,
        )
        repeated = await project_resolved_industry_membership(
            resolution_reader=projection_store,
            membership_writer=projection_store,
            resolution_id=resolution_id,
        )
    finally:
        await projection_store.close()
    if repeated != projection:
        raise AssertionError("real membership projection is not idempotent")
    if projection.known_at != KNOWN_AT or projection.system_from <= projection.known_at:
        raise AssertionError("membership projection collapsed source-known and curation time")
    if projection.evidence_fragment_ids != (evidence_fragment_id,):
        raise AssertionError("membership projection changed supporting Evidence identity")

    catalog_reader = PostgresIndustryOrientationReader(dsn)
    memory_reader = PostgresEpistemicMemoryReader(dsn)
    open_state_reader = PostgresOpenStateReader(dsn)
    evidence_reader = PostgresEvidenceDrilldownReader(dsn)
    try:
        before = await build_researcher_industry_orientation(
            catalog_reader=catalog_reader,
            memory_reader=memory_reader,
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=BEFORE_KNOWN,
        )
        after = await build_researcher_industry_orientation(
            catalog_reader=catalog_reader,
            memory_reader=memory_reader,
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=KNOWN_AT,
        )
        if before["subjects"] != []:
            raise AssertionError("real Samsung membership leaked across its source-known cutoff")
        subjects = after["subjects"]
        if len(subjects) != 1 or subjects[0]["subject_id"] != str(SAMSUNG_ID):
            raise AssertionError(f"real orientation did not expose Samsung after cutoff: {subjects}")
        samsung = subjects[0]
        memberships = samsung["memberships"]
        if len(memberships) != 1 or memberships[0]["role"] != "hbm3e_producer":
            raise AssertionError(f"real orientation role mismatch: {memberships}")
        if memberships[0]["known_at"] != KNOWN_AT.isoformat():
            raise AssertionError("orientation did not preserve membership source-known time")
        if memberships[0]["valid_from"] is not None or memberships[0]["valid_to"] is not None:
            raise AssertionError("unknown membership onset was converted into an invented validity date")
        if str(evidence_fragment_id) not in samsung["evidence_fragment_ids"]:
            raise AssertionError("orientation lost membership Evidence provenance")
        if samsung["memory_counts"] != {"reality": 1, "judgments": 0, "outcomes": 0}:
            raise AssertionError(f"unexpected real orientation memory counts: {samsung['memory_counts']}")

        snapshot = await memory_reader.snapshot(
            (MemorySubjectRef(entity_id=SAMSUNG_ID),),
            knowledge_cutoff=KNOWN_AT,
        )
        trajectory = build_researcher_trajectory_view(snapshot)
        if trajectory["counts"]["reality"] != 1:
            raise AssertionError(f"real trajectory lost membership Reality: {trajectory}")
        entries = trajectory["entries"]
        if len(entries) != 1 or entries[0].get("predicate_code") != "industry.membership":
            raise AssertionError(f"real trajectory did not preserve membership Reality: {entries}")
        if entries[0]["historical_time"]["kind"] != "unknown":
            raise AssertionError("trajectory invented membership onset precision")

        open_states = await build_researcher_open_state_view(
            catalog_reader=catalog_reader,
            memory_reader=memory_reader,
            conflict_reader=open_state_reader,
            current_research_reader=open_state_reader,
            industry_node_id=INDUSTRY_ID,
            knowledge_cutoff=KNOWN_AT,
            include_current_research=False,
        )
        historical = open_states["historical_at_cutoff"]
        if any(historical.values()):
            raise AssertionError(f"acceptance fixture manufactured controversy: {historical}")
        if open_states["current_research_overlay"]["included"] is not False:
            raise AssertionError("current research overlay must remain opt-in")

        try:
            await build_researcher_evidence_drilldown(
                reader=evidence_reader,
                evidence_fragment_id=evidence_fragment_id,
                knowledge_cutoff=BEFORE_KNOWN,
            )
        except ValueError as exc:
            if "not knowable" not in str(exc):
                raise
        else:
            raise AssertionError("Evidence drilldown leaked the real fragment before source-known time")

        evidence = await build_researcher_evidence_drilldown(
            reader=evidence_reader,
            evidence_fragment_id=evidence_fragment_id,
            knowledge_cutoff=KNOWN_AT,
        )
        if evidence["evidence"]["excerpt"] != EXPECTED_EXCERPT:
            raise AssertionError("real Evidence drilldown excerpt differs from preserved Samsung text")
        if evidence["source"]["publisher"]["publisher_domain"] != "samsung.com":
            raise AssertionError("real Evidence drilldown lost Samsung source identity")
    finally:
        await catalog_reader.close()
        await memory_reader.close()
        await open_state_reader.close()
        await evidence_reader.close()

    return {
        "industry_node_id": str(INDUSTRY_ID),
        "subject_entity_id": str(SAMSUNG_ID),
        "membership_resolution_id": str(resolution_id),
        "membership_id": str(projection.membership_id),
        "evidence_fragment_id": str(evidence_fragment_id),
        "known_at": KNOWN_AT.isoformat(),
        "role": projection.role,
        "before_cutoff_subject_count": len(before["subjects"]),
        "after_cutoff_subject_count": len(after["subjects"]),
        "trajectory_reality_count": trajectory["counts"]["reality"],
        "historical_open_state_count": sum(len(value) for value in historical.values()),
        "evidence_publisher_domain": evidence["source"]["publisher"]["publisher_domain"],
    }


async def main() -> None:
    dsn = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not dsn:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")
    _seed_current_taxonomy(dsn)
    resolution_id, evidence_fragment_id, known_at = _execute_real_grounded_membership(dsn)
    if known_at != KNOWN_AT:
        raise AssertionError("real acceptance known time mismatch")
    summary = await _verify_researcher_path(
        dsn=dsn,
        resolution_id=resolution_id,
        evidence_fragment_id=evidence_fragment_id,
    )
    print("POSTGRES_REAL_SOURCE_ORIENTATION_ACCEPTANCE_PASS")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
