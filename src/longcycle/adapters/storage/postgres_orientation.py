from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import require_aware_datetime
from longcycle.domain.orientation import (
    IndustryDescriptor,
    IndustryMembershipModelJudgmentRun,
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    IndustrySubjectMembershipRecord,
    ResolvedIndustryMembershipResolution,
)
from longcycle.ports.orientation import IndustryOrientationCapability

from .postgres import PostgresResearchRepository, PostgresSupport


class PostgresIndustryOrientationReader(PostgresSupport):
    """Read grounded industry entry inputs without owning truth semantics."""

    capabilities: frozenset[IndustryOrientationCapability] = frozenset(
        {"deterministic_industry_subjects"}
    )

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog:
        async with self.connection() as connection:
            industry_cursor = await connection.execute(
                """
                SELECT id, canonical_name, node_kind, archetype
                FROM core.taxonomy_nodes
                WHERE id = %s
                """,
                (industry_node_id,),
            )
            industry_row = await industry_cursor.fetchone()
            if industry_row is None:
                raise KeyError(industry_node_id)

            membership_cursor = await connection.execute(
                """
                SELECT membership.id AS membership_id,
                       membership.industry_node_id,
                       membership.entity_id,
                       entity.canonical_name,
                       entity.entity_type,
                       membership.role,
                       membership.exposure_type,
                       membership.valid_from,
                       membership.valid_to,
                       membership.system_from,
                       membership.confidence,
                       membership.resolution_id,
                       membership.semantic_decision_id,
                       COALESCE(cardinality(decision.supporting_judgment_run_ids), 0)
                           AS semantic_decision_supporting_run_count,
                       latest_run.reasoning_mode AS semantic_decision_latest_reasoning_mode,
                       min(assertion.first_known_at) AS known_at,
                       array_remove(
                           array_agg(
                               DISTINCT evidence_link.evidence_fragment_id
                               ORDER BY evidence_link.evidence_fragment_id
                           ),
                           NULL
                       ) AS evidence_fragment_ids
                FROM core.industry_entity_memberships membership
                JOIN core.entities entity
                  ON entity.id = membership.entity_id
                JOIN research.fact_resolutions resolution
                  ON resolution.id = membership.resolution_id
                LEFT JOIN research.industry_membership_semantic_decisions decision
                  ON decision.id = membership.semantic_decision_id
                 AND decision.resolution_id = membership.resolution_id
                LEFT JOIN LATERAL (
                    SELECT run.reasoning_mode
                    FROM research.industry_membership_model_judgment_runs run
                    WHERE decision.id IS NOT NULL
                      AND run.id = ANY(decision.supporting_judgment_run_ids)
                    ORDER BY run.completed_at DESC, run.id DESC
                    LIMIT 1
                ) latest_run ON true
                JOIN research.fact_resolution_assertions selected
                  ON selected.resolution_id = resolution.id
                 AND selected.disposition = 'selected'
                 AND (
                     decision.id IS NULL
                     OR selected.assertion_id = ANY(decision.supporting_assertion_ids)
                 )
                JOIN research.fact_assertions assertion
                  ON assertion.id = selected.assertion_id
                LEFT JOIN research.assertion_evidence evidence_link
                  ON evidence_link.assertion_id = assertion.id
                 AND evidence_link.evidence_role = 'supporting'
                WHERE membership.industry_node_id = %s
                GROUP BY membership.id, membership.industry_node_id,
                         membership.entity_id, entity.canonical_name,
                         entity.entity_type, membership.role,
                         membership.exposure_type, membership.valid_from,
                         membership.valid_to, membership.system_from,
                         membership.confidence, membership.resolution_id,
                         membership.semantic_decision_id,
                         decision.supporting_judgment_run_ids,
                         latest_run.reasoning_mode
                HAVING bool_and(evidence_link.evidence_fragment_id IS NOT NULL)
                ORDER BY known_at, membership.system_from, membership.id
                """,
                (industry_node_id,),
            )
            membership_rows = await membership_cursor.fetchall()

        return IndustryOrientationCatalog(
            industry=self._industry_record(industry_row),
            memberships=tuple(self._membership_record(row) for row in membership_rows),
        )

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[IndustrySubjectDiscoveryRecord, ...]:
        """Recover subjects from grounded memory carrying explicit industry scope."""

        checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
        assert checked is not None
        async with self.connection() as connection:
            reality_cursor = await connection.execute(
                """
                SELECT canonical.id AS basis_id,
                       key.subject_entity_id AS entity_id,
                       entity.canonical_name,
                       entity.entity_type,
                       key.predicate_code AS semantic_code,
                       canonical.market_known_at AS known_at,
                       array_remove(
                           array_agg(
                               DISTINCT evidence_link.evidence_fragment_id
                               ORDER BY evidence_link.evidence_fragment_id
                           ),
                           NULL
                       ) AS evidence_fragment_ids
                FROM research.canonical_fact_versions canonical
                JOIN research.fact_keys key
                  ON key.id = canonical.fact_key_id
                JOIN research.fact_resolution_assertions selected
                  ON selected.resolution_id = canonical.resolution_id
                 AND selected.disposition = 'selected'
                JOIN research.fact_assertions assertion
                  ON assertion.id = selected.assertion_id
                JOIN core.entities entity
                  ON entity.id = key.subject_entity_id
                LEFT JOIN research.assertion_evidence evidence_link
                  ON evidence_link.assertion_id = assertion.id
                WHERE canonical.system_to IS NULL
                  AND canonical.publication_status = 'trusted'
                  AND key.subject_entity_id IS NOT NULL
                  AND key.predicate_code <> 'industry.membership'
                  AND assertion.metadata->>'industry_node_id' = %s
                  AND canonical.market_known_at <= %s
                GROUP BY canonical.id, key.subject_entity_id,
                         entity.canonical_name, entity.entity_type,
                         key.predicate_code, canonical.market_known_at
                HAVING bool_and(evidence_link.evidence_fragment_id IS NOT NULL)
                """,
                (str(industry_node_id), checked),
            )
            reality_rows = await reality_cursor.fetchall()

            judgment_cursor = await connection.execute(
                """
                SELECT judgment.id AS basis_id,
                       judgment.subject_entity_id AS entity_id,
                       entity.canonical_name,
                       entity.entity_type,
                       judgment.topic_code AS semantic_code,
                       judgment.first_known_at AS known_at,
                       array_remove(
                           array_agg(
                               DISTINCT evidence_link.evidence_fragment_id
                               ORDER BY evidence_link.evidence_fragment_id
                           ),
                           NULL
                       ) AS evidence_fragment_ids
                FROM research.judgment_assertions judgment
                JOIN core.entities entity
                  ON entity.id = judgment.subject_entity_id
                LEFT JOIN research.judgment_evidence evidence_link
                  ON evidence_link.judgment_id = judgment.id
                WHERE judgment.subject_entity_id IS NOT NULL
                  AND judgment.metadata->>'industry_node_id' = %s
                  AND judgment.first_known_at <= %s
                GROUP BY judgment.id, judgment.subject_entity_id,
                         entity.canonical_name, entity.entity_type,
                         judgment.topic_code, judgment.first_known_at
                HAVING bool_and(evidence_link.evidence_fragment_id IS NOT NULL)
                """,
                (str(industry_node_id), checked),
            )
            judgment_rows = await judgment_cursor.fetchall()

        records = [
            IndustrySubjectDiscoveryRecord(
                industry_node_id=industry_node_id,
                subject=MemorySubjectRef(entity_id=row["entity_id"]),
                canonical_name=row["canonical_name"],
                entity_type=row["entity_type"],
                basis_kind="accepted_reality",
                basis_id=row["basis_id"],
                semantic_code=row["semantic_code"],
                known_at=row["known_at"],
                evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
            )
            for row in reality_rows
        ]
        records.extend(
            IndustrySubjectDiscoveryRecord(
                industry_node_id=industry_node_id,
                subject=MemorySubjectRef(entity_id=row["entity_id"]),
                canonical_name=row["canonical_name"],
                entity_type=row["entity_type"],
                basis_kind="grounded_judgment",
                basis_id=row["basis_id"],
                semantic_code=row["semantic_code"],
                known_at=row["known_at"],
                evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
            )
            for row in judgment_rows
        )
        return tuple(
            sorted(
                records,
                key=lambda item: (
                    item.canonical_name.casefold(),
                    str(item.subject.entity_id),
                    item.known_at,
                    item.basis_kind,
                    str(item.basis_id),
                ),
            )
        )

    @staticmethod
    def _industry_record(row: dict[str, Any]) -> IndustryDescriptor:
        return IndustryDescriptor(
            industry_node_id=row["id"],
            canonical_name=row["canonical_name"],
            node_kind=row["node_kind"],
            archetype=row["archetype"],
        )

    @staticmethod
    def _membership_record(row: dict[str, Any]) -> IndustrySubjectMembershipRecord:
        return IndustrySubjectMembershipRecord(
            membership_id=row["membership_id"],
            industry_node_id=row["industry_node_id"],
            subject=MemorySubjectRef(entity_id=row["entity_id"]),
            canonical_name=row["canonical_name"],
            entity_type=row["entity_type"],
            role=row["role"],
            exposure_type=row["exposure_type"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            known_at=row["known_at"],
            system_from=row["system_from"],
            confidence=row["confidence"],
            resolution_id=row["resolution_id"],
            semantic_decision_id=row["semantic_decision_id"],
            semantic_decision_supporting_run_count=row[
                "semantic_decision_supporting_run_count"
            ],
            semantic_decision_latest_reasoning_mode=row[
                "semantic_decision_latest_reasoning_mode"
            ],
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
        )


class PostgresIndustryMembershipProjectionStore(PostgresResearchRepository):
    """Bridge accepted CAP-0003 resolutions into the model-audited CAP-0005 catalog."""

    async def industry_membership_resolution(
        self,
        resolution_id: UUID,
    ) -> ResolvedIndustryMembershipResolution:
        async with self.connection() as connection:
            resolution_cursor = await connection.execute(
                """
                SELECT selected_assertion_ids, confidence, resolved_at
                FROM research.fact_resolutions
                WHERE id = %s
                """,
                (resolution_id,),
            )
            resolution = await resolution_cursor.fetchone()
            if resolution is None:
                raise KeyError(resolution_id)

            selected_cursor = await connection.execute(
                """
                SELECT assertion_id
                FROM research.fact_resolution_assertions
                WHERE resolution_id = %s AND disposition = 'selected'
                ORDER BY assertion_id
                """,
                (resolution_id,),
            )
            selected_ids = tuple(row["assertion_id"] for row in await selected_cursor.fetchall())
            declared_ids = tuple(resolution["selected_assertion_ids"] or ())
            if set(selected_ids) != set(declared_ids) or len(selected_ids) != len(declared_ids):
                raise RuntimeError(
                    "Fact resolution selected assertion links disagree with resolution payload"
                )

            assertions = []
            for assertion_id in selected_ids:
                assertion = await self._assertion_by_id_on_connection(connection, assertion_id)
                if assertion is None:
                    raise RuntimeError(
                        f"selected Fact assertion cannot be reconstructed: {assertion_id}"
                    )
                assertions.append(assertion)

        return ResolvedIndustryMembershipResolution(
            resolution_id=resolution_id,
            selected_assertions=tuple(assertions),
            confidence=resolution["confidence"],
            resolved_at=resolution["resolved_at"],
        )

    async def _selected_ids_and_evidence(
        self,
        connection: Any,
        resolution_id: UUID,
    ) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]:
        selected_cursor = await connection.execute(
            """
            SELECT assertion_id
            FROM research.fact_resolution_assertions
            WHERE resolution_id = %s AND disposition = 'selected'
            ORDER BY assertion_id
            """,
            (resolution_id,),
        )
        selected_ids = tuple(row["assertion_id"] for row in await selected_cursor.fetchall())
        evidence_cursor = await connection.execute(
            """
            SELECT DISTINCT link.evidence_fragment_id
            FROM research.assertion_evidence link
            WHERE link.assertion_id = ANY(%s)
              AND link.evidence_role = 'supporting'
            ORDER BY link.evidence_fragment_id
            """,
            (list(selected_ids),),
        )
        evidence_ids = tuple(row["evidence_fragment_id"] for row in await evidence_cursor.fetchall())
        return selected_ids, evidence_ids

    async def append_industry_membership_judgment_run(
        self,
        run: IndustryMembershipModelJudgmentRun,
    ) -> IndustryMembershipModelJudgmentRun:
        async with self.connection() as connection:
            selected_ids, evidence_ids = await self._selected_ids_and_evidence(
                connection,
                run.resolution_id,
            )
            if tuple(sorted(selected_ids, key=str)) != tuple(
                sorted(run.candidate_assertion_ids, key=str)
            ):
                raise ValueError(
                    "membership judgment run candidates do not match CAP-0003 selected assertions"
                )
            if evidence_ids != tuple(sorted(run.evidence_fragment_ids, key=str)):
                raise ValueError(
                    "membership judgment run Evidence does not match selected source assertions"
                )
            await connection.execute(
                """
                INSERT INTO research.industry_membership_model_judgment_runs (
                    id, resolution_id, candidate_assertion_ids, input_assertion_hashes,
                    reasoning_mode, provider_name, model_name, model_version,
                    started_at, completed_at, selected_assertion_id,
                    alternative_assertion_ids, material_conflict_detected, confidence,
                    can_materialize, reasoning_summary, triggered_deep,
                    deep_trigger_reasons, evidence_fragment_ids
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    run.run_id,
                    run.resolution_id,
                    list(run.candidate_assertion_ids),
                    list(run.input_assertion_hashes),
                    run.reasoning_mode,
                    run.provider_name,
                    run.model_name,
                    run.model_version,
                    run.started_at,
                    run.completed_at,
                    run.selected_assertion_id,
                    list(run.alternative_assertion_ids),
                    run.material_conflict_detected,
                    run.confidence,
                    run.can_materialize,
                    run.reasoning_summary,
                    run.triggered_deep,
                    list(run.deep_trigger_reasons),
                    list(run.evidence_fragment_ids),
                ),
            )
        return run

    async def append_industry_membership_semantic_decision(
        self,
        decision: IndustryMembershipSemanticDecision,
    ) -> IndustryMembershipSemanticDecision:
        async with self.connection() as connection:
            selected_ids, evidence_ids = await self._selected_ids_and_evidence(
                connection,
                decision.resolution_id,
            )
            if tuple(sorted(selected_ids, key=str)) != tuple(
                sorted(decision.candidate_assertion_ids, key=str)
            ):
                raise ValueError(
                    "membership semantic decision candidates do not match CAP-0003 selected assertions"
                )
            if decision.selected_assertion_id not in selected_ids:
                raise ValueError("membership semantic decision selected a non-selected assertion")
            if not set(decision.supporting_assertion_ids).issubset(selected_ids):
                raise ValueError(
                    "membership semantic decision support includes a non-selected assertion"
                )
            if decision.selected_assertion_id not in decision.supporting_assertion_ids:
                raise ValueError(
                    "membership semantic decision support omits the representative assertion"
                )
            if evidence_ids != tuple(sorted(decision.evidence_fragment_ids, key=str)):
                raise ValueError(
                    "membership semantic decision Evidence does not match selected source assertions"
                )

            run_cursor = await connection.execute(
                """
                SELECT id, resolution_id, candidate_assertion_ids, evidence_fragment_ids
                FROM research.industry_membership_model_judgment_runs
                WHERE id = ANY(%s)
                ORDER BY id
                """,
                (list(decision.supporting_judgment_run_ids),),
            )
            run_rows = await run_cursor.fetchall()
            if len(run_rows) != len(decision.supporting_judgment_run_ids):
                raise ValueError("membership semantic decision references missing model judgment runs")
            for row in run_rows:
                if row["resolution_id"] != decision.resolution_id:
                    raise ValueError("membership semantic decision run references another resolution")
                if tuple(sorted(row["candidate_assertion_ids"], key=str)) != tuple(
                    sorted(decision.candidate_assertion_ids, key=str)
                ):
                    raise ValueError("membership semantic decision run candidate set drifted")
                if tuple(sorted(row["evidence_fragment_ids"], key=str)) != evidence_ids:
                    raise ValueError("membership semantic decision run Evidence set drifted")

            await connection.execute(
                """
                INSERT INTO research.industry_membership_semantic_decisions (
                    id, resolution_id, candidate_assertion_ids, selected_assertion_id,
                    supporting_assertion_ids, semantic_scope, decision_summary,
                    first_decided_at, last_confirmed_at,
                    supporting_judgment_run_ids, evidence_fragment_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    supporting_assertion_ids = ARRAY(
                        SELECT DISTINCT value
                        FROM unnest(
                            research.industry_membership_semantic_decisions.supporting_assertion_ids
                            || EXCLUDED.supporting_assertion_ids
                        ) AS value
                        ORDER BY value
                    ),
                    supporting_judgment_run_ids = ARRAY(
                        SELECT DISTINCT value
                        FROM unnest(
                            research.industry_membership_semantic_decisions.supporting_judgment_run_ids
                            || EXCLUDED.supporting_judgment_run_ids
                        ) AS value
                        ORDER BY value
                    ),
                    last_confirmed_at = GREATEST(
                        research.industry_membership_semantic_decisions.last_confirmed_at,
                        EXCLUDED.last_confirmed_at
                    )
                """,
                (
                    decision.decision_id,
                    decision.resolution_id,
                    list(decision.candidate_assertion_ids),
                    decision.selected_assertion_id,
                    list(decision.supporting_assertion_ids),
                    decision.semantic_scope,
                    decision.decision_summary,
                    decision.first_decided_at,
                    decision.last_confirmed_at,
                    list(decision.supporting_judgment_run_ids),
                    list(decision.evidence_fragment_ids),
                ),
            )
            stored_cursor = await connection.execute(
                """
                SELECT id, resolution_id, candidate_assertion_ids, selected_assertion_id,
                       supporting_assertion_ids, semantic_scope, decision_summary,
                       first_decided_at, last_confirmed_at,
                       supporting_judgment_run_ids, evidence_fragment_ids
                FROM research.industry_membership_semantic_decisions
                WHERE id = %s
                """,
                (decision.decision_id,),
            )
            stored = await stored_cursor.fetchone()
            if stored is None:
                raise RuntimeError("membership semantic decision was not persisted")

        persisted = IndustryMembershipSemanticDecision(
            decision_id=stored["id"],
            resolution_id=stored["resolution_id"],
            semantic_scope=stored["semantic_scope"],
            candidate_assertion_ids=tuple(stored["candidate_assertion_ids"]),
            selected_assertion_id=stored["selected_assertion_id"],
            supporting_assertion_ids=tuple(stored["supporting_assertion_ids"]),
            decision_summary=stored["decision_summary"],
            first_decided_at=stored["first_decided_at"],
            last_confirmed_at=stored["last_confirmed_at"],
            supporting_judgment_run_ids=tuple(stored["supporting_judgment_run_ids"]),
            evidence_fragment_ids=tuple(stored["evidence_fragment_ids"]),
        )
        semantic_fields = (
            "resolution_id",
            "semantic_scope",
            "candidate_assertion_ids",
            "selected_assertion_id",
            "evidence_fragment_ids",
        )
        if any(getattr(persisted, field) != getattr(decision, field) for field in semantic_fields):
            raise ValueError("membership semantic decision id maps to different semantic content")
        if not set(decision.supporting_assertion_ids).issubset(persisted.supporting_assertion_ids):
            raise ValueError("membership semantic decision lost supporting source assertions")
        if not set(decision.supporting_judgment_run_ids).issubset(
            persisted.supporting_judgment_run_ids
        ):
            raise ValueError("membership semantic decision lost supporting model judgment runs")
        return persisted

    @staticmethod
    def _catalog_date(value: datetime | None, *, label: str) -> date | None:
        if value is None:
            return None
        utc_value = value.astimezone(UTC)
        if utc_value.timetz().replace(tzinfo=None) != time.min:
            raise ValueError(
                f"{label} cannot be projected to catalog date without losing source time precision"
            )
        return utc_value.date()

    async def append_industry_membership(
        self,
        projection: IndustryMembershipProjection,
    ) -> IndustryMembershipProjection:
        async with self.connection() as connection:
            source_cursor = await connection.execute(
                """
                SELECT resolution.confidence,
                       decision.first_decided_at AS semantic_decided_at,
                       decision.selected_assertion_id,
                       decision.supporting_assertion_ids,
                       assertion.id AS assertion_id,
                       assertion.predicate_code,
                       assertion.subject_entity_id,
                       assertion.value_kind,
                       assertion.value_text,
                       assertion.valid_from,
                       assertion.valid_to,
                       assertion.first_known_at,
                       assertion.metadata,
                       array_remove(
                           array_agg(
                               evidence.evidence_fragment_id
                               ORDER BY evidence.evidence_fragment_id
                           ),
                           NULL
                       ) AS supporting_evidence
                FROM research.fact_resolutions resolution
                JOIN research.industry_membership_semantic_decisions decision
                  ON decision.resolution_id = resolution.id
                 AND decision.id = %s
                JOIN research.fact_resolution_assertions selected
                  ON selected.resolution_id = resolution.id
                 AND selected.disposition = 'selected'
                 AND selected.assertion_id = ANY(decision.supporting_assertion_ids)
                JOIN research.fact_assertions assertion
                  ON assertion.id = selected.assertion_id
                LEFT JOIN research.assertion_evidence evidence
                  ON evidence.assertion_id = assertion.id
                 AND evidence.evidence_role = 'supporting'
                WHERE resolution.id = %s
                GROUP BY resolution.confidence, decision.first_decided_at,
                         decision.selected_assertion_id,
                         decision.supporting_assertion_ids,
                         assertion.id, assertion.predicate_code,
                         assertion.subject_entity_id, assertion.value_kind,
                         assertion.value_text, assertion.valid_from,
                         assertion.valid_to, assertion.first_known_at,
                         assertion.metadata
                ORDER BY assertion.id
                """,
                (
                    projection.semantic_decision_id,
                    projection.resolution_id,
                ),
            )
            sources = await source_cursor.fetchall()
            if not sources:
                raise ValueError(
                    "membership projection has no source assertions in its semantic support cluster"
                )
            supporting_ids = tuple(sources[0]["supporting_assertion_ids"] or ())
            if len(sources) != len(supporting_ids):
                raise ValueError("membership semantic support cluster is incomplete in storage")
            if sources[0]["selected_assertion_id"] != projection.assertion_id:
                raise ValueError(
                    "membership projection does not reference the semantic-decision representative assertion"
                )

            source_evidence_values: set[UUID] = set()
            source_known_at: list[datetime] = []
            expected_semantic = {
                "predicate": "industry.membership",
                "entity_id": projection.entity_id,
                "value_kind": "text",
                "role": projection.role,
                "industry_node_id": projection.industry_node_id,
                "exposure_type": projection.exposure_type,
                "valid_from": projection.valid_from,
                "valid_to": projection.valid_to,
            }
            for source in sources:
                metadata = source["metadata"] or {}
                try:
                    source_industry_node_id = UUID(str(metadata.get("industry_node_id")))
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "supporting industry.membership assertion has invalid industry_node_id metadata"
                    ) from exc
                actual_semantic = {
                    "predicate": source["predicate_code"],
                    "entity_id": source["subject_entity_id"],
                    "value_kind": source["value_kind"],
                    "role": source["value_text"],
                    "industry_node_id": source_industry_node_id,
                    "exposure_type": metadata.get("exposure_type"),
                    "valid_from": self._catalog_date(
                        source["valid_from"], label="membership valid_from"
                    ),
                    "valid_to": self._catalog_date(
                        source["valid_to"], label="membership valid_to"
                    ),
                }
                if actual_semantic != expected_semantic:
                    raise ValueError(
                        "membership semantic support cluster contains a non-equivalent assertion"
                    )
                source_evidence = tuple(source["supporting_evidence"] or ())
                if not source_evidence:
                    raise ValueError(
                        "supporting industry.membership assertion has no supporting Evidence"
                    )
                source_evidence_values.update(source_evidence)
                source_known_at.append(source["first_known_at"])

            actual = {
                **expected_semantic,
                "known_at": min(source_known_at),
                "system_from": sources[0]["semantic_decided_at"],
                "confidence": sources[0]["confidence"],
                "evidence": tuple(sorted(source_evidence_values, key=str)),
            }
            expected = {
                **expected_semantic,
                "known_at": projection.known_at,
                "system_from": projection.system_from,
                "confidence": projection.confidence,
                "evidence": projection.evidence_fragment_ids,
            }
            if actual != expected:
                raise ValueError(
                    "industry membership projection does not exactly match its equivalent source support cluster"
                )

            industry_cursor = await connection.execute(
                "SELECT 1 FROM core.taxonomy_nodes WHERE id = %s",
                (projection.industry_node_id,),
            )
            if await industry_cursor.fetchone() is None:
                raise KeyError(projection.industry_node_id)
            entity_cursor = await connection.execute(
                "SELECT 1 FROM core.entities WHERE id = %s",
                (projection.entity_id,),
            )
            if await entity_cursor.fetchone() is None:
                raise KeyError(projection.entity_id)

            await connection.execute(
                """
                INSERT INTO core.industry_entity_memberships (
                    id, industry_node_id, entity_id, role, exposure_type,
                    valid_from, valid_to, system_from, confidence, resolution_id,
                    semantic_decision_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    projection.membership_id,
                    projection.industry_node_id,
                    projection.entity_id,
                    projection.role,
                    projection.exposure_type,
                    projection.valid_from,
                    projection.valid_to,
                    projection.system_from,
                    projection.confidence,
                    projection.resolution_id,
                    projection.semantic_decision_id,
                ),
            )
            stored_cursor = await connection.execute(
                """
                SELECT id, industry_node_id, entity_id, role, exposure_type,
                       valid_from, valid_to, system_from, system_to,
                       confidence, resolution_id, semantic_decision_id
                FROM core.industry_entity_memberships
                WHERE id = %s
                """,
                (projection.membership_id,),
            )
            stored = await stored_cursor.fetchone()
            if stored is None:
                raise RuntimeError("industry membership projection was not persisted")
            stored_payload = {
                "membership_id": stored["id"],
                "industry_node_id": stored["industry_node_id"],
                "entity_id": stored["entity_id"],
                "role": stored["role"],
                "exposure_type": stored["exposure_type"],
                "valid_from": stored["valid_from"],
                "valid_to": stored["valid_to"],
                "system_from": stored["system_from"],
                "confidence": stored["confidence"],
                "resolution_id": stored["resolution_id"],
                "semantic_decision_id": stored["semantic_decision_id"],
            }
            expected_payload = {
                "membership_id": projection.membership_id,
                "industry_node_id": projection.industry_node_id,
                "entity_id": projection.entity_id,
                "role": projection.role,
                "exposure_type": projection.exposure_type,
                "valid_from": projection.valid_from,
                "valid_to": projection.valid_to,
                "system_from": projection.system_from,
                "confidence": projection.confidence,
                "resolution_id": projection.resolution_id,
                "semantic_decision_id": projection.semantic_decision_id,
            }
            if stored["system_to"] is not None or stored_payload != expected_payload:
                raise ValueError(
                    "industry membership id already maps to different materialized content"
                )
        return projection
