from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import require_aware_datetime
from longcycle.domain.orientation import (
    IndustryDescriptor,
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    IndustrySubjectMembershipRecord,
    ResolvedIndustryMembershipResolution,
)

from .postgres import PostgresResearchRepository, PostgresSupport


class PostgresIndustryOrientationReader(PostgresSupport):
    """Read grounded industry entry inputs without owning truth semantics."""

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
                       decision.reasoning_mode AS semantic_decision_mode,
                       max(assertion.first_known_at) AS known_at,
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
                JOIN research.fact_resolution_assertions selected
                  ON selected.resolution_id = resolution.id
                 AND selected.disposition = 'selected'
                 AND (
                     decision.id IS NULL
                     OR selected.assertion_id = decision.selected_assertion_id
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
                         membership.semantic_decision_id, decision.reasoning_mode
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
        """Recover subjects from grounded memory carrying explicit industry scope.

        This is a recall rule, not a truth promotion rule. An accepted Reality or
        grounded Judgment explicitly scoped to an industry makes its entity
        deterministically discoverable at that cutoff. It does not create a catalog
        membership, infer a value-chain role, or rank importance.
        """

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
            semantic_decision_mode=row["semantic_decision_mode"],
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
        )


class PostgresIndustryMembershipProjectionStore(PostgresResearchRepository):
    """Bridge accepted CAP-0003 resolutions into the CAP-0005 orientation catalog.

    CAP-0003 owns the source-backed selected assertion set. A model-mediated CAP-0005
    semantic decision is persisted as audit provenance before materialization. The model
    decision never becomes Evidence and never changes the underlying Fact resolution.
    """

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

    async def append_industry_membership_semantic_decision(
        self,
        decision: IndustryMembershipSemanticDecision,
    ) -> IndustryMembershipSemanticDecision:
        async with self.connection() as connection:
            selected_cursor = await connection.execute(
                """
                SELECT assertion_id
                FROM research.fact_resolution_assertions
                WHERE resolution_id = %s AND disposition = 'selected'
                ORDER BY assertion_id
                """,
                (decision.resolution_id,),
            )
            selected_ids = tuple(row["assertion_id"] for row in await selected_cursor.fetchall())
            if tuple(sorted(selected_ids, key=str)) != tuple(
                sorted(decision.candidate_assertion_ids, key=str)
            ):
                raise ValueError(
                    "membership semantic decision candidates do not match CAP-0003 selected assertions"
                )
            if decision.selected_assertion_id not in selected_ids:
                raise ValueError("membership semantic decision selected a non-selected assertion")

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
            if evidence_ids != tuple(sorted(decision.evidence_fragment_ids, key=str)):
                raise ValueError(
                    "membership semantic decision Evidence does not match selected source assertions"
                )

            await connection.execute(
                """
                INSERT INTO research.industry_membership_semantic_decisions (
                    id, resolution_id, candidate_assertion_ids, selected_assertion_id,
                    reasoning_mode, material_conflict_detected, reasoning_summary,
                    model_name, model_version, decided_at, evidence_fragment_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    decision.decision_id,
                    decision.resolution_id,
                    list(decision.candidate_assertion_ids),
                    decision.selected_assertion_id,
                    decision.reasoning_mode,
                    decision.material_conflict_detected,
                    decision.reasoning_summary,
                    decision.model_name,
                    decision.model_version,
                    decision.decided_at,
                    list(decision.evidence_fragment_ids),
                ),
            )
            stored_cursor = await connection.execute(
                """
                SELECT id, resolution_id, candidate_assertion_ids, selected_assertion_id,
                       reasoning_mode, material_conflict_detected, reasoning_summary,
                       model_name, model_version, decided_at, evidence_fragment_ids
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
            candidate_assertion_ids=tuple(stored["candidate_assertion_ids"]),
            selected_assertion_id=stored["selected_assertion_id"],
            reasoning_mode=stored["reasoning_mode"],
            material_conflict_detected=stored["material_conflict_detected"],
            reasoning_summary=stored["reasoning_summary"],
            model_name=stored["model_name"],
            model_version=stored["model_version"],
            decided_at=stored["decided_at"],
            evidence_fragment_ids=tuple(stored["evidence_fragment_ids"]),
        )
        semantic_fields = (
            "resolution_id",
            "candidate_assertion_ids",
            "selected_assertion_id",
            "reasoning_mode",
            "material_conflict_detected",
            "model_name",
            "model_version",
            "evidence_fragment_ids",
        )
        if any(getattr(persisted, field) != getattr(decision, field) for field in semantic_fields):
            raise ValueError("membership semantic decision id maps to different semantic content")
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
                       decision.decided_at AS semantic_decided_at,
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
                 AND selected.assertion_id = decision.selected_assertion_id
                JOIN research.fact_assertions assertion
                  ON assertion.id = selected.assertion_id
                LEFT JOIN research.assertion_evidence evidence
                  ON evidence.assertion_id = assertion.id
                 AND evidence.evidence_role = 'supporting'
                WHERE resolution.id = %s AND assertion.id = %s
                GROUP BY resolution.confidence, decision.decided_at,
                         assertion.predicate_code, assertion.subject_entity_id,
                         assertion.value_kind, assertion.value_text,
                         assertion.valid_from, assertion.valid_to,
                         assertion.first_known_at, assertion.metadata
                """,
                (
                    projection.semantic_decision_id,
                    projection.resolution_id,
                    projection.assertion_id,
                ),
            )
            source = await source_cursor.fetchone()
            if source is None:
                raise ValueError(
                    "membership projection does not reference the model-selected assertion in its resolution"
                )

            metadata = source["metadata"] or {}
            try:
                source_industry_node_id = UUID(str(metadata.get("industry_node_id")))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "selected industry.membership assertion has invalid industry_node_id metadata"
                ) from exc
            source_exposure = metadata.get("exposure_type")
            source_evidence = tuple(source["supporting_evidence"] or ())
            expected = {
                "predicate": "industry.membership",
                "entity_id": projection.entity_id,
                "value_kind": "text",
                "role": projection.role,
                "industry_node_id": projection.industry_node_id,
                "exposure_type": projection.exposure_type,
                "valid_from": projection.valid_from,
                "valid_to": projection.valid_to,
                "known_at": projection.known_at,
                "system_from": projection.system_from,
                "confidence": projection.confidence,
                "evidence": projection.evidence_fragment_ids,
            }
            actual = {
                "predicate": source["predicate_code"],
                "entity_id": source["subject_entity_id"],
                "value_kind": source["value_kind"],
                "role": source["value_text"],
                "industry_node_id": source_industry_node_id,
                "exposure_type": source_exposure,
                "valid_from": self._catalog_date(
                    source["valid_from"],
                    label="membership valid_from",
                ),
                "valid_to": self._catalog_date(
                    source["valid_to"],
                    label="membership valid_to",
                ),
                "known_at": source["first_known_at"],
                "system_from": source["semantic_decided_at"],
                "confidence": source["confidence"],
                "evidence": source_evidence,
            }
            if actual != expected:
                raise ValueError(
                    "industry membership projection does not exactly match model-selected source assertion"
                )
            if not source_evidence:
                raise ValueError("selected industry.membership assertion has no supporting Evidence")

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
