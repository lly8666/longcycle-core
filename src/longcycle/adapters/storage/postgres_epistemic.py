from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import (
    CanonicalRealityRecord,
    IndustrialMemoryTimeline,
    JudgmentMemoryRecord,
    JudgmentRationaleMemoryRecord,
    JudgmentRelationMemoryRecord,
    MemorySubjectRef,
    OutcomeMemoryRecord,
    PointInTimeMemorySnapshot,
    TemporalExtent,
    snapshot_from_timeline,
)
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision
from longcycle.domain.models import canonical_json, require_aware_datetime

from .postgres import PostgresSupport


def _subject_lists(subjects: Sequence[MemorySubjectRef]) -> tuple[list[UUID], list[UUID]]:
    if not subjects:
        raise ValueError("at least one memory subject is required")
    entity_ids = [item.entity_id for item in subjects if item.entity_id is not None]
    industry_ids = [item.industry_node_id for item in subjects if item.industry_node_id is not None]
    return entity_ids, industry_ids


def _subject_from_row(row: dict[str, Any]) -> MemorySubjectRef:
    return MemorySubjectRef(
        entity_id=row.get("subject_entity_id"),
        industry_node_id=row.get("subject_industry_node_id"),
    )


def _value_payload(row: dict[str, Any], *, prefix: str = "") -> str | None:
    fields = {
        "numeric": row.get(f"{prefix}value_numeric"),
        "boolean": row.get(f"{prefix}value_boolean"),
        "date": row.get(f"{prefix}value_date"),
        "entity": row.get(f"{prefix}value_entity_id"),
        "json": row.get(f"{prefix}value_json"),
        "low": row.get(f"{prefix}value_low"),
        "high": row.get(f"{prefix}value_high"),
        "direction": row.get(f"{prefix}direction"),
    }
    material = {key: value for key, value in fields.items() if value is not None}
    return canonical_json(material) if material else None


def _reality_time(row: dict[str, Any]) -> TemporalExtent:
    kind = row["valid_time_kind"]
    return TemporalExtent(
        kind=kind,
        start=row["valid_from"] if kind == "period" else None,
        end=row["valid_to"] if kind == "period" else None,
        precision=TemporalPrecision(row["valid_time_precision"]),
        source_text=row["valid_time_text"],
    )


def _reality_observed_time(row: dict[str, Any]) -> TemporalExtent | None:
    if row["observed_at"] is None:
        return None
    return TemporalExtent(
        kind="instant",
        at=row["observed_at"],
        precision=TemporalPrecision(row["observed_at_precision"]),
        source_text=row["observed_at_text"],
    )


def _judgment_target(row: dict[str, Any]) -> TemporalExtent:
    kind = row["target_time_kind"]
    return TemporalExtent(
        kind=kind,
        at=row["target_at"] if kind == "instant" else None,
        start=row["target_from"] if kind == "period" else None,
        end=row["target_to"] if kind == "period" else None,
        precision=TemporalPrecision(row["target_precision"]),
        source_text=row["target_text"],
    )


def _outcome_time(row: dict[str, Any]) -> TemporalExtent:
    has_bounds = row["outcome_from"] is not None or row["outcome_to"] is not None
    return TemporalExtent(
        kind="period" if has_bounds else "unknown",
        start=row["outcome_from"] if has_bounds else None,
        end=row["outcome_to"] if has_bounds else None,
        precision=TemporalPrecision(row["outcome_precision"]),
        source_text=row["outcome_text"],
    )


class PostgresEpistemicMemoryReader(PostgresSupport):
    """Typed industrial-memory read model over the transactional PostgreSQL adapter.

    Application/replay code depends on this boundary, not on the physical research.*
    tables. PostgreSQL remains free to evolve or be replaced without leaking schema
    joins into scripts and product logic.
    """

    async def timeline(
        self,
        subjects: Sequence[MemorySubjectRef],
    ) -> IndustrialMemoryTimeline:
        entity_ids, industry_ids = _subject_lists(subjects)
        async with self.connection() as connection:
            reality_rows = await self._reality_rows(connection, entity_ids, industry_ids)
            judgment_rows = await self._judgment_rows(connection, entity_ids, industry_ids)
            judgment_ids = [row["judgment_id"] for row in judgment_rows]
            rationale_rows = await self._judgment_rationale_rows(connection, judgment_ids)
            relation_rows = await self._judgment_relation_rows(connection, judgment_ids)
            outcome_rows = await self._outcome_rows(connection, entity_ids, industry_ids)
        return IndustrialMemoryTimeline(
            reality=tuple(self._reality_record(row) for row in reality_rows),
            judgments=tuple(self._judgment_record(row) for row in judgment_rows),
            judgment_rationales=tuple(
                self._judgment_rationale_record(row) for row in rationale_rows
            ),
            judgment_relations=tuple(
                self._judgment_relation_record(row) for row in relation_rows
            ),
            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),
        )

    async def snapshot(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> PointInTimeMemorySnapshot:
        checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
        assert checked is not None
        entity_ids, industry_ids = _subject_lists(subjects)
        async with self.connection() as connection:
            reality_rows = await self._reality_rows(
                connection, entity_ids, industry_ids, knowledge_cutoff=checked
            )
            judgment_rows = await self._judgment_rows(
                connection, entity_ids, industry_ids, knowledge_cutoff=checked
            )
            judgment_ids = [row["judgment_id"] for row in judgment_rows]
            rationale_rows = await self._judgment_rationale_rows(
                connection, judgment_ids, knowledge_cutoff=checked
            )
            relation_rows = await self._judgment_relation_rows(
                connection, judgment_ids, knowledge_cutoff=checked
            )
            outcome_rows = await self._outcome_rows(
                connection, entity_ids, industry_ids, knowledge_cutoff=checked
            )
        timeline = IndustrialMemoryTimeline(
            reality=tuple(self._reality_record(row) for row in reality_rows),
            judgments=tuple(self._judgment_record(row) for row in judgment_rows),
            judgment_rationales=tuple(
                self._judgment_rationale_record(row) for row in rationale_rows
            ),
            judgment_relations=tuple(
                self._judgment_relation_record(row) for row in relation_rows
            ),
            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),
        )
        return snapshot_from_timeline(timeline, knowledge_cutoff=checked)

    @staticmethod
    async def _reality_rows(
        connection: Any,
        entity_ids: list[UUID],
        industry_ids: list[UUID],
        *,
        knowledge_cutoff: datetime | None = None,
    ) -> list[dict[str, Any]]:
        cursor = await connection.execute(
            """
            SELECT canonical.id AS canonical_fact_version_id,
                   key.subject_entity_id, key.subject_industry_node_id,
                   key.predicate_code,
                   canonical.value_kind, canonical.value_numeric,
                   canonical.value_text, canonical.value_boolean,
                   canonical.value_date, canonical.value_entity_id,
                   canonical.value_json, canonical.unit_code,
                   canonical.valid_time_kind,
                   canonical.valid_from, canonical.valid_to,
                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.observed_at, canonical.observed_at_precision,
                   canonical.observed_at_text,
                   canonical.market_known_at, canonical.confidence,
                   canonical.publication_status,
                   array_agg(DISTINCT evidence_link.evidence_fragment_id
                             ORDER BY evidence_link.evidence_fragment_id)
                       AS evidence_fragment_ids
            FROM research.canonical_fact_versions canonical
            JOIN research.fact_keys key ON key.id = canonical.fact_key_id
            JOIN research.fact_resolution_assertions resolution_link
              ON resolution_link.resolution_id = canonical.resolution_id
             AND resolution_link.disposition = 'selected'
            JOIN research.assertion_evidence evidence_link
              ON evidence_link.assertion_id = resolution_link.assertion_id
            WHERE canonical.system_to IS NULL
              AND canonical.publication_status = 'trusted'
              AND (
                    key.subject_entity_id = ANY(%s::uuid[])
                 OR key.subject_industry_node_id = ANY(%s::uuid[])
              )
              AND (%s::timestamptz IS NULL OR canonical.market_known_at <= %s)
            GROUP BY canonical.id, key.subject_entity_id,
                     key.subject_industry_node_id, key.predicate_code
            ORDER BY canonical.market_known_at, canonical.id
            """,
            (entity_ids, industry_ids, knowledge_cutoff, knowledge_cutoff),
        )
        return list(await cursor.fetchall())

    @staticmethod
    async def _judgment_rows(
        connection: Any,
        entity_ids: list[UUID],
        industry_ids: list[UUID],
        *,
        knowledge_cutoff: datetime | None = None,
    ) -> list[dict[str, Any]]:
        cursor = await connection.execute(
            """
            SELECT judgment.id AS judgment_id,
                   judgment.subject_entity_id,
                   judgment.subject_industry_node_id,
                   judgment.speaker_name_text, judgment.topic_code,
                   judgment.judgment_kind, judgment.target_time_kind,
                   judgment.target_at, judgment.target_from, judgment.target_to,
                   judgment.target_precision, judgment.target_text,
                   judgment.value_kind, judgment.value_numeric,
                   judgment.value_low, judgment.value_high,
                   judgment.value_text, judgment.value_boolean,
                   judgment.value_date, judgment.value_entity_id,
                   judgment.value_json, judgment.direction,
                   judgment.summary, judgment.first_known_at,
                   judgment.metadata,
                   array_agg(DISTINCT evidence_link.evidence_fragment_id
                             ORDER BY evidence_link.evidence_fragment_id)
                       AS evidence_fragment_ids
            FROM research.judgment_assertions judgment
            JOIN research.judgment_evidence evidence_link
              ON evidence_link.judgment_id = judgment.id
            WHERE (
                    judgment.subject_entity_id = ANY(%s::uuid[])
                 OR judgment.subject_industry_node_id = ANY(%s::uuid[])
              )
              AND (%s::timestamptz IS NULL OR judgment.first_known_at <= %s)
            GROUP BY judgment.id
            ORDER BY judgment.first_known_at, judgment.id
            """,
            (entity_ids, industry_ids, knowledge_cutoff, knowledge_cutoff),
        )
        return list(await cursor.fetchall())


    @staticmethod
    async def _judgment_rationale_rows(
        connection: Any,
        judgment_ids: list[UUID],
        *,
        knowledge_cutoff: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if not judgment_ids:
            return []
        cursor = await connection.execute(
            """
            SELECT rationale.id AS rationale_id,
                   rationale.judgment_id, rationale.rationale_kind,
                   rationale.summary, rationale.linked_fact_assertion_id,
                   rationale.linked_judgment_id, rationale.evidence_fragment_id,
                   rationale.ordinal,
                   GREATEST(
                       owner.first_known_at,
                       linked_judgment.first_known_at,
                       linked_fact.first_known_at,
                       rationale_fetch.first_known_at
                   ) AS known_at
            FROM research.judgment_rationales rationale
            JOIN research.judgment_assertions owner
              ON owner.id = rationale.judgment_id
            LEFT JOIN research.judgment_assertions linked_judgment
              ON linked_judgment.id = rationale.linked_judgment_id
            LEFT JOIN research.fact_assertions linked_fact
              ON linked_fact.id = rationale.linked_fact_assertion_id
            LEFT JOIN evidence.evidence_fragments rationale_evidence
              ON rationale_evidence.id = rationale.evidence_fragment_id
            LEFT JOIN evidence.document_versions rationale_version
              ON rationale_version.id = rationale_evidence.document_version_id
            LEFT JOIN evidence.document_fetches rationale_fetch
              ON rationale_fetch.id = rationale_version.first_fetch_id
            WHERE rationale.judgment_id = ANY(%s::uuid[])
              AND (
                    %s::timestamptz IS NULL
                 OR GREATEST(
                        owner.first_known_at,
                        linked_judgment.first_known_at,
                        linked_fact.first_known_at,
                        rationale_fetch.first_known_at
                    ) <= %s
              )
            ORDER BY known_at, rationale.judgment_id, rationale.ordinal, rationale.id
            """,
            (judgment_ids, knowledge_cutoff, knowledge_cutoff),
        )
        return list(await cursor.fetchall())

    @staticmethod
    async def _judgment_relation_rows(
        connection: Any,
        judgment_ids: list[UUID],
        *,
        knowledge_cutoff: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if not judgment_ids:
            return []
        cursor = await connection.execute(
            """
            SELECT relation.from_judgment_id, relation.to_judgment_id,
                   relation.relation_type, relation.reason_summary,
                   GREATEST(source.first_known_at, target.first_known_at) AS known_at
            FROM research.judgment_relations relation
            JOIN research.judgment_assertions source
              ON source.id = relation.from_judgment_id
            JOIN research.judgment_assertions target
              ON target.id = relation.to_judgment_id
            WHERE relation.from_judgment_id = ANY(%s::uuid[])
              AND relation.to_judgment_id = ANY(%s::uuid[])
              AND (
                    %s::timestamptz IS NULL
                 OR GREATEST(source.first_known_at, target.first_known_at) <= %s
              )
            ORDER BY known_at, relation.from_judgment_id,
                     relation.to_judgment_id, relation.relation_type
            """,
            (judgment_ids, judgment_ids, knowledge_cutoff, knowledge_cutoff),
        )
        return list(await cursor.fetchall())

    @staticmethod
    async def _outcome_rows(
        connection: Any,
        entity_ids: list[UUID],
        industry_ids: list[UUID],
        *,
        knowledge_cutoff: datetime | None = None,
    ) -> list[dict[str, Any]]:
        cursor = await connection.execute(
            """
            SELECT evaluation.id AS evaluation_id,
                   evaluation.judgment_id,
                   judgment.subject_entity_id,
                   judgment.subject_industry_node_id,
                   evaluation.canonical_fact_version_id,
                   evaluation.outcome_evidence_fragment_id,
                   evaluation.evaluation_status,
                   evaluation.semantic_relation,
                   evaluation.outcome_from, evaluation.outcome_to,
                   evaluation.outcome_precision, evaluation.outcome_text,
                   evaluation.outcome_first_known_at,
                   evaluation.timing_relation, evaluation.timing_delta_value,
                   evaluation.timing_delta_unit, evaluation.explanation,
                   evaluation.evaluator_name, evaluation.evaluator_version
            FROM research.judgment_outcome_evaluations evaluation
            JOIN research.judgment_assertions judgment
              ON judgment.id = evaluation.judgment_id
            WHERE (
                    judgment.subject_entity_id = ANY(%s::uuid[])
                 OR judgment.subject_industry_node_id = ANY(%s::uuid[])
              )
              AND evaluation.outcome_first_known_at IS NOT NULL
              AND (%s::timestamptz IS NULL OR evaluation.outcome_first_known_at <= %s)
            ORDER BY evaluation.outcome_first_known_at, evaluation.id
            """,
            (entity_ids, industry_ids, knowledge_cutoff, knowledge_cutoff),
        )
        return list(await cursor.fetchall())

    @staticmethod
    def _reality_record(row: dict[str, Any]) -> CanonicalRealityRecord:
        return CanonicalRealityRecord(
            canonical_fact_version_id=row["canonical_fact_version_id"],
            subject=_subject_from_row(row),
            predicate_code=row["predicate_code"],
            value_kind=row["value_kind"],
            value_text=row["value_text"],
            value_payload=_value_payload(row),
            unit_code=row["unit_code"],
            valid_time=_reality_time(row),
            observed_time=_reality_observed_time(row),
            known_at=row["market_known_at"],
            confidence=row["confidence"],
            publication_status=row["publication_status"],
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
        )

    @staticmethod
    def _judgment_record(row: dict[str, Any]) -> JudgmentMemoryRecord:
        metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
        return JudgmentMemoryRecord(
            judgment_id=row["judgment_id"],
            judgment_key=metadata.get("judgment_key"),
            subject=_subject_from_row(row),
            speaker_name_text=row["speaker_name_text"],
            topic_code=row["topic_code"],
            judgment_kind=row["judgment_kind"],
            target_time=_judgment_target(row),
            value_kind=row["value_kind"],
            value_text=row["value_text"],
            value_payload=_value_payload(row),
            summary=row["summary"],
            known_at=row["first_known_at"],
            evidence_fragment_ids=tuple(row["evidence_fragment_ids"]),
        )


    @staticmethod
    def _judgment_rationale_record(row: dict[str, Any]) -> JudgmentRationaleMemoryRecord:
        return JudgmentRationaleMemoryRecord(
            rationale_id=row["rationale_id"],
            judgment_id=row["judgment_id"],
            rationale_kind=JudgmentRationaleKind(row["rationale_kind"]),
            summary=row["summary"],
            linked_fact_assertion_id=row["linked_fact_assertion_id"],
            linked_judgment_id=row["linked_judgment_id"],
            evidence_fragment_id=row["evidence_fragment_id"],
            ordinal=row["ordinal"],
            known_at=row["known_at"],
        )

    @staticmethod
    def _judgment_relation_record(row: dict[str, Any]) -> JudgmentRelationMemoryRecord:
        return JudgmentRelationMemoryRecord(
            from_judgment_id=row["from_judgment_id"],
            to_judgment_id=row["to_judgment_id"],
            relation_type=JudgmentRelationType(row["relation_type"]),
            reason_summary=row["reason_summary"],
            known_at=row["known_at"],
        )

    @staticmethod
    def _outcome_record(row: dict[str, Any]) -> OutcomeMemoryRecord:
        value = row["timing_delta_value"]
        return OutcomeMemoryRecord(
            evaluation_id=row["evaluation_id"],
            judgment_id=row["judgment_id"],
            subject=_subject_from_row(row),
            canonical_fact_version_id=row["canonical_fact_version_id"],
            outcome_evidence_fragment_id=row["outcome_evidence_fragment_id"],
            evaluation_status=row["evaluation_status"],
            semantic_relation=row["semantic_relation"],
            occurrence_time=_outcome_time(row),
            known_at=row["outcome_first_known_at"],
            timing_relation=row["timing_relation"],
            timing_delta_value=Decimal(value) if value is not None else None,
            timing_delta_unit=row["timing_delta_unit"],
            explanation=row["explanation"],
            evaluator_name=row["evaluator_name"],
            evaluator_version=row["evaluator_version"],
        )
