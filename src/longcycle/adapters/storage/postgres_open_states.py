from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.memory import (
    DirectSourceSearchStatus,
    MemoryAuditDisposition,
    MemoryHypothesisDisposition,
)
from longcycle.domain.open_states import (
    CurrentResearchOpenStateBundle,
    MemoryCoverageGapRecord,
    MemoryDisagreementOpenRecord,
    MemoryHypothesisOpenRecord,
    RealityConflictAssertionRecord,
    RealitySourceDisagreementRecord,
)

from .postgres import PostgresSupport


_OPEN_MEMORY_DISPOSITIONS = (
    "unresolved",
    "seek_primary",
    "authoritative_conflict",
    "secondary_only_support",
    "secondary_only_contradiction",
    "scope_mismatch",
)
_OPEN_HYPOTHESIS_DISPOSITIONS = (
    "unresolved",
    "mixed",
    "insufficient_basis",
)


class PostgresOpenStateReader(PostgresSupport):
    """Read explicit archive conflicts and current research-only open states.

    Historical conflict visibility is reconstructed from member assertion ``first_known_at``.
    Database curation timestamps stay provenance only. Current Memory/coverage state is read
    separately and must never be presented as historical market knowledge.
    """

    async def historical_source_disagreements(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: Any,
    ) -> tuple[RealitySourceDisagreementRecord, ...]:
        entity_ids = [item.entity_id for item in subjects if item.entity_id is not None]
        industry_ids = [
            item.industry_node_id for item in subjects if item.industry_node_id is not None
        ]
        subject_clauses: list[str] = []
        params: list[Any] = [knowledge_cutoff]
        if entity_ids:
            subject_clauses.append("fact_key.subject_entity_id = ANY(%s::uuid[])")
            params.append(entity_ids)
        if industry_ids:
            subject_clauses.append("fact_key.subject_industry_node_id = ANY(%s::uuid[])")
            params.append(industry_ids)
        if not subject_clauses:
            return ()

        query = f"""
            SELECT conflict.id AS conflict_case_id,
                   conflict.fact_key_id,
                   conflict.severity,
                   conflict.status AS current_case_status,
                   conflict.opened_at AS research_case_opened_at,
                   conflict.closed_at AS research_case_closed_at,
                   fact_key.subject_entity_id,
                   fact_key.subject_industry_node_id,
                   fact_key.predicate_code,
                   fact_key.comparability_hash,
                   assertion.id AS assertion_id,
                   assertion.source_connector_id AS source_id,
                   assertion.first_known_at AS known_at,
                   assertion.value_kind,
                   assertion.value_numeric,
                   assertion.value_text,
                   assertion.value_boolean,
                   assertion.value_date,
                   assertion.value_entity_id,
                   assertion.value_json,
                   assertion.unit_code,
                   array_agg(DISTINCT evidence_link.evidence_fragment_id
                             ORDER BY evidence_link.evidence_fragment_id) AS evidence_fragment_ids
            FROM research.conflict_cases conflict
            JOIN research.fact_keys fact_key
              ON fact_key.id = conflict.fact_key_id
            JOIN research.conflict_members member
              ON member.conflict_case_id = conflict.id
            JOIN research.fact_assertions assertion
              ON assertion.id = member.assertion_id
            JOIN research.assertion_evidence evidence_link
              ON evidence_link.assertion_id = assertion.id
            WHERE assertion.first_known_at <= %s
              AND ({' OR '.join(subject_clauses)})
            GROUP BY conflict.id, conflict.fact_key_id, conflict.severity, conflict.status,
                     conflict.opened_at, conflict.closed_at,
                     fact_key.subject_entity_id, fact_key.subject_industry_node_id,
                     fact_key.predicate_code, fact_key.comparability_hash,
                     assertion.id, assertion.source_connector_id, assertion.first_known_at,
                     assertion.value_kind, assertion.value_numeric, assertion.value_text,
                     assertion.value_boolean, assertion.value_date, assertion.value_entity_id,
                     assertion.value_json, assertion.unit_code
            ORDER BY conflict.id, assertion.first_known_at, assertion.id
        """
        async with self.connection() as connection:
            cursor = await connection.execute(query, tuple(params))
            rows = await cursor.fetchall()

        grouped: dict[UUID, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["conflict_case_id"]].append(row)

        result: list[RealitySourceDisagreementRecord] = []
        for case_id, members in grouped.items():
            if len(members) < 2:
                continue
            assertions = tuple(self._conflict_assertion(row) for row in members)
            if len({item.source_id for item in assertions}) < 2:
                continue
            first = members[0]
            subject = self._subject(first)
            result.append(
                RealitySourceDisagreementRecord(
                    conflict_case_id=case_id,
                    fact_key_id=first["fact_key_id"],
                    subject=subject,
                    predicate_code=first["predicate_code"],
                    comparability_hash=str(first["comparability_hash"]).strip(),
                    severity=first["severity"],
                    current_case_status=first["current_case_status"],
                    archive_disagreement_known_at=max(item.known_at for item in assertions),
                    research_case_opened_at=first["research_case_opened_at"],
                    research_case_closed_at=first["research_case_closed_at"],
                    assertions=assertions,
                )
            )
        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.archive_disagreement_known_at,
                    item.subject.key,
                    item.predicate_code,
                    str(item.conflict_case_id),
                ),
            )
        )

    async def current_open_states(
        self,
        *,
        industry_node_id: UUID,
        entity_ids: Sequence[UUID],
    ) -> CurrentResearchOpenStateBundle:
        async with self.connection() as connection:
            disagreements = await self._current_disagreements(
                connection,
                industry_node_id=industry_node_id,
                entity_ids=entity_ids,
            )
            hypotheses = await self._current_hypotheses(
                connection,
                industry_node_id=industry_node_id,
                entity_ids=entity_ids,
            )
            coverage_gaps = await self._current_coverage_gaps(
                connection,
                industry_node_id=industry_node_id,
            )
        return CurrentResearchOpenStateBundle(
            disagreements=disagreements,
            hypotheses=hypotheses,
            coverage_gaps=coverage_gaps,
        )

    async def _current_disagreements(
        self,
        connection: Any,
        *,
        industry_node_id: UUID,
        entity_ids: Sequence[UUID],
    ) -> tuple[MemoryDisagreementOpenRecord, ...]:
        cursor = await connection.execute(
            """
            SELECT disagreement.id AS disagreement_case_id,
                   disagreement.lead_id,
                   lead.subject_entity_id,
                   lead.subject_industry_node_id,
                   lead.summary AS lead_summary,
                   disagreement.claim_scope,
                   disagreement.opened_reason,
                   disagreement.opened_at,
                   latest.disposition,
                   latest.rationale AS resolution_rationale,
                   latest.resolved_at,
                   evidence.supporting_evidence_ids,
                   evidence.contradicting_evidence_ids
            FROM research.memory_disagreement_cases disagreement
            JOIN research.model_memory_leads lead
              ON lead.id = disagreement.lead_id
            LEFT JOIN LATERAL (
                SELECT resolution.disposition, resolution.rationale, resolution.resolved_at
                FROM research.memory_disagreement_resolutions resolution
                WHERE resolution.disagreement_case_id = disagreement.id
                ORDER BY resolution.resolved_at DESC, resolution.id DESC
                LIMIT 1
            ) latest ON TRUE
            LEFT JOIN LATERAL (
                SELECT coalesce(
                           array_agg(link.evidence_fragment_id ORDER BY link.evidence_fragment_id)
                               FILTER (WHERE link.stance = 'supports'),
                           '{}'::uuid[]
                       ) AS supporting_evidence_ids,
                       coalesce(
                           array_agg(link.evidence_fragment_id ORDER BY link.evidence_fragment_id)
                               FILTER (WHERE link.stance = 'contradicts'),
                           '{}'::uuid[]
                       ) AS contradicting_evidence_ids
                FROM research.memory_lead_evidence_links link
                WHERE link.lead_id = disagreement.lead_id
                  AND link.scope_match = true
            ) evidence ON TRUE
            WHERE (
                    lead.subject_industry_node_id = %s
                    OR lead.subject_entity_id = ANY(%s::uuid[])
                  )
              AND (
                    latest.disposition IS NULL
                    OR latest.disposition = ANY(%s::text[])
                  )
            ORDER BY coalesce(latest.resolved_at, disagreement.opened_at), disagreement.id
            """,
            (industry_node_id, list(entity_ids), list(_OPEN_MEMORY_DISPOSITIONS)),
        )
        rows = await cursor.fetchall()
        return tuple(
            MemoryDisagreementOpenRecord(
                disagreement_case_id=row["disagreement_case_id"],
                lead_id=row["lead_id"],
                subject=self._subject(row),
                lead_summary=row["lead_summary"],
                claim_scope=row["claim_scope"],
                opened_reason=row["opened_reason"],
                current_disposition=(
                    MemoryAuditDisposition(row["disposition"])
                    if row["disposition"] is not None
                    else None
                ),
                resolution_rationale=row["resolution_rationale"],
                supporting_evidence_ids=tuple(row["supporting_evidence_ids"] or ()),
                contradicting_evidence_ids=tuple(row["contradicting_evidence_ids"] or ()),
                research_recorded_at=row["resolved_at"] or row["opened_at"],
            )
            for row in rows
        )

    async def _current_hypotheses(
        self,
        connection: Any,
        *,
        industry_node_id: UUID,
        entity_ids: Sequence[UUID],
    ) -> tuple[MemoryHypothesisOpenRecord, ...]:
        cursor = await connection.execute(
            """
            SELECT assessment.id AS assessment_id,
                   assessment.lead_id,
                   lead.subject_entity_id,
                   lead.subject_industry_node_id,
                   lead.summary AS lead_summary,
                   assessment.disposition,
                   assessment.direct_source_search_status,
                   assessment.inference_confidence,
                   assessment.reasoning_summary,
                   assessment.alternative_explanations,
                   assessment.falsification_conditions,
                   assessment.assessed_at,
                   evidence.supporting_evidence_ids,
                   evidence.contradicting_evidence_ids
            FROM research.model_memory_leads lead
            JOIN LATERAL (
                SELECT candidate.*
                FROM research.memory_hypothesis_assessments candidate
                WHERE candidate.lead_id = lead.id
                ORDER BY candidate.assessed_at DESC, candidate.id DESC
                LIMIT 1
            ) assessment ON TRUE
            LEFT JOIN LATERAL (
                SELECT coalesce(
                           array_agg(link.evidence_fragment_id ORDER BY link.evidence_fragment_id)
                               FILTER (WHERE link.stance = 'supports'),
                           '{}'::uuid[]
                       ) AS supporting_evidence_ids,
                       coalesce(
                           array_agg(link.evidence_fragment_id ORDER BY link.evidence_fragment_id)
                               FILTER (WHERE link.stance = 'contradicts'),
                           '{}'::uuid[]
                       ) AS contradicting_evidence_ids
                FROM research.memory_hypothesis_evidence_links link
                WHERE link.assessment_id = assessment.id
            ) evidence ON TRUE
            WHERE (
                    lead.subject_industry_node_id = %s
                    OR lead.subject_entity_id = ANY(%s::uuid[])
                  )
              AND assessment.disposition = ANY(%s::text[])
            ORDER BY assessment.assessed_at, assessment.id
            """,
            (industry_node_id, list(entity_ids), list(_OPEN_HYPOTHESIS_DISPOSITIONS)),
        )
        rows = await cursor.fetchall()
        return tuple(
            MemoryHypothesisOpenRecord(
                assessment_id=row["assessment_id"],
                lead_id=row["lead_id"],
                subject=self._subject(row),
                lead_summary=row["lead_summary"],
                disposition=MemoryHypothesisDisposition(row["disposition"]),
                direct_source_search_status=DirectSourceSearchStatus(
                    row["direct_source_search_status"]
                ),
                inference_confidence=row["inference_confidence"],
                reasoning_summary=row["reasoning_summary"],
                alternative_explanations=tuple(row["alternative_explanations"] or ()),
                falsification_conditions=tuple(row["falsification_conditions"] or ()),
                supporting_evidence_ids=tuple(row["supporting_evidence_ids"] or ()),
                contradicting_evidence_ids=tuple(row["contradicting_evidence_ids"] or ()),
                research_recorded_at=row["assessed_at"],
            )
            for row in rows
        )

    async def _current_coverage_gaps(
        self,
        connection: Any,
        *,
        industry_node_id: UUID,
    ) -> tuple[MemoryCoverageGapRecord, ...]:
        cursor = await connection.execute(
            """
            WITH ranked AS (
                SELECT cell.*,
                       row_number() OVER (
                           PARTITION BY cell.dimension_type, cell.dimension_key,
                                        cell.period_from, cell.period_to
                           ORDER BY cell.created_at DESC, cell.id DESC
                       ) AS rank_no
                FROM research.model_memory_coverage_cells cell
                JOIN research.model_memory_campaigns campaign
                  ON campaign.id = cell.campaign_id
                WHERE campaign.industry_node_id = %s
            )
            SELECT campaign_id, snapshot_label, dimension_type, dimension_key,
                   period_from, period_to, coverage_state, notes, created_at
            FROM ranked
            WHERE rank_no = 1
              AND coverage_state IN ('unseen', 'thin', 'needs_review')
            ORDER BY dimension_type, dimension_key, period_from NULLS FIRST,
                     period_to NULLS FIRST, created_at
            """,
            (industry_node_id,),
        )
        rows = await cursor.fetchall()
        return tuple(
            MemoryCoverageGapRecord(
                campaign_id=row["campaign_id"],
                snapshot_label=row["snapshot_label"],
                dimension_type=row["dimension_type"],
                dimension_key=row["dimension_key"],
                period_from=row["period_from"],
                period_to=row["period_to"],
                coverage_state=row["coverage_state"],
                notes=row["notes"],
                research_recorded_at=row["created_at"],
            )
            for row in rows
        )

    @staticmethod
    def _subject(row: dict[str, Any]) -> MemorySubjectRef:
        if row.get("subject_entity_id") is not None:
            return MemorySubjectRef(entity_id=row["subject_entity_id"])
        if row.get("subject_industry_node_id") is not None:
            return MemorySubjectRef(industry_node_id=row["subject_industry_node_id"])
        raise ValueError("open-state record has no subject identity")

    @staticmethod
    def _conflict_assertion(row: dict[str, Any]) -> RealityConflictAssertionRecord:
        value_columns = {
            "numeric": row["value_numeric"],
            "text": row["value_text"],
            "boolean": row["value_boolean"],
            "date": row["value_date"],
            "entity": row["value_entity_id"],
            "json": row["value_json"],
        }
        value = {key: item for key, item in value_columns.items() if item is not None}
        return RealityConflictAssertionRecord(
            assertion_id=row["assertion_id"],
            source_id=row["source_id"],
            known_at=row["known_at"],
            value_kind=row["value_kind"],
            value=value,
            unit_code=row["unit_code"],
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"] or ()),
        )
