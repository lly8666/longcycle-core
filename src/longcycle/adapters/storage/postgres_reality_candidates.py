from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import require_aware_datetime
from longcycle.domain.reality_candidates import RealityResearchCandidate

from .postgres import PostgresSupport


class PostgresRealityResearchCandidateReader(PostgresSupport):
    """Read point-in-time REVIEW/QUARANTINE assertions without changing CAP-0003 truth."""

    async def candidates_for_industry(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[RealityResearchCandidate, ...]:
        checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
        assert checked is not None

        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT assertion.id AS assertion_id,
                       assertion.subject_entity_id,
                       assertion.subject_industry_node_id,
                       COALESCE(entity.canonical_name, industry.canonical_name) AS canonical_name,
                       COALESCE(entity.entity_type, 'industry') AS entity_type,
                       assertion.predicate_code,
                       CASE
                           WHEN latest.decision = 'quarantine' THEN 'quarantined'
                           ELSE 'review'
                       END AS status,
                       assertion.raw_value,
                       assertion.value_kind,
                       assertion.unit_code,
                       assertion.valid_time_kind,
                       assertion.valid_from,
                       assertion.valid_to,
                       assertion.first_known_at AS source_known_at,
                       latest.evaluated_at AS decision_known_at,
                       assertion.confidence,
                       latest.score AS reconciliation_score,
                       latest.reason_codes,
                       latest.conflicting_assertion_ids,
                       evidence.evidence_fragment_ids
                FROM research.fact_assertions assertion
                JOIN LATERAL (
                    SELECT evaluation.decision,
                           evaluation.score,
                           evaluation.reason_codes,
                           evaluation.conflicting_assertion_ids,
                           evaluation.evaluated_at,
                           evaluation.id
                    FROM research.reconciliation_evaluations evaluation
                    WHERE evaluation.assertion_id = assertion.id
                      AND evaluation.evaluated_at <= %s
                    ORDER BY evaluation.evaluated_at DESC, evaluation.id DESC
                    LIMIT 1
                ) latest ON true
                JOIN LATERAL (
                    SELECT array_remove(
                               array_agg(
                                   DISTINCT link.evidence_fragment_id
                                   ORDER BY link.evidence_fragment_id
                               ),
                               NULL
                           ) AS evidence_fragment_ids
                    FROM research.assertion_evidence link
                    WHERE link.assertion_id = assertion.id
                ) evidence ON true
                LEFT JOIN core.entities entity
                  ON entity.id = assertion.subject_entity_id
                LEFT JOIN core.taxonomy_nodes industry
                  ON industry.id = assertion.subject_industry_node_id
                WHERE assertion.first_known_at <= %s
                  AND latest.decision IN ('review', 'quarantine')
                  AND cardinality(evidence.evidence_fragment_ids) > 0
                  AND (
                      assertion.subject_industry_node_id = %s
                      OR assertion.metadata->>'industry_node_id' = %s
                  )
                ORDER BY latest.evaluated_at,
                         assertion.first_known_at,
                         assertion.predicate_code,
                         assertion.id
                """,
                (checked, checked, industry_node_id, str(industry_node_id)),
            )
            rows = await cursor.fetchall()

        return tuple(self._candidate_from_row(industry_node_id, row) for row in rows)

    @staticmethod
    def _candidate_from_row(
        industry_node_id: UUID,
        row: dict[str, Any],
    ) -> RealityResearchCandidate:
        subject = (
            MemorySubjectRef(entity_id=row["subject_entity_id"])
            if row["subject_entity_id"] is not None
            else MemorySubjectRef(industry_node_id=row["subject_industry_node_id"])
        )
        return RealityResearchCandidate(
            assertion_id=row["assertion_id"],
            industry_node_id=industry_node_id,
            subject=subject,
            canonical_name=row["canonical_name"],
            entity_type=row["entity_type"],
            predicate_code=row["predicate_code"],
            status=row["status"],
            raw_value=row["raw_value"],
            value_kind=row["value_kind"],
            unit_code=row["unit_code"],
            valid_time_kind=row["valid_time_kind"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            source_known_at=row["source_known_at"],
            decision_known_at=row["decision_known_at"],
            confidence=row["confidence"],
            reconciliation_score=row["reconciliation_score"],
            reason_codes=tuple(row["reason_codes"] or ()),
            conflicting_assertion_ids=tuple(row["conflicting_assertion_ids"] or ()),
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"] or ()),
        )
