from __future__ import annotations

from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.orientation import (
    IndustryDescriptor,
    IndustryOrientationCatalog,
    IndustrySubjectMembershipRecord,
)

from .postgres import PostgresSupport


class PostgresIndustryOrientationReader(PostgresSupport):
    """Read source-grounded industry membership without owning catalog truth semantics."""

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
                JOIN research.fact_resolution_assertions selected
                  ON selected.resolution_id = resolution.id
                 AND selected.disposition = 'selected'
                JOIN research.fact_assertions assertion
                  ON assertion.id = selected.assertion_id
                LEFT JOIN research.assertion_evidence evidence_link
                  ON evidence_link.assertion_id = assertion.id
                WHERE membership.industry_node_id = %s
                GROUP BY membership.id, membership.industry_node_id,
                         membership.entity_id, entity.canonical_name,
                         entity.entity_type, membership.role,
                         membership.exposure_type, membership.valid_from,
                         membership.valid_to, membership.system_from,
                         membership.confidence, membership.resolution_id
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
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
        )
