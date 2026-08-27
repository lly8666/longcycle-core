from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path
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
)
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision
from longcycle.domain.models import require_aware_datetime


def _duckdb() -> Any:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install longcycle-core[duckdb] to use portable memory") from exc
    return duckdb


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _subject_values(subject: MemorySubjectRef) -> tuple[str, str | None, str | None]:
    return (
        subject.key,
        str(subject.entity_id) if subject.entity_id is not None else None,
        str(subject.industry_node_id) if subject.industry_node_id is not None else None,
    )


def _subject_from_values(
    entity_id: str | None,
    industry_node_id: str | None,
) -> MemorySubjectRef:
    return MemorySubjectRef(
        entity_id=UUID(entity_id) if entity_id else None,
        industry_node_id=UUID(industry_node_id) if industry_node_id else None,
    )


def _extent_values(extent: TemporalExtent) -> tuple[Any, ...]:
    return (
        extent.kind,
        extent.at,
        extent.start,
        extent.end,
        extent.precision.value,
        extent.source_text,
    )


def seal_industrial_memory(
    path: Path,
    timeline: IndustrialMemoryTimeline,
) -> dict[str, Any]:
    """Write one immutable portable generation from a validated typed timeline."""

    duckdb = _duckdb()
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    try:
        connection.execute(
            """
            CREATE TABLE reality_memory (
                canonical_fact_version_id VARCHAR PRIMARY KEY,
                subject_key VARCHAR NOT NULL,
                subject_entity_id VARCHAR,
                subject_industry_node_id VARCHAR,
                predicate_code VARCHAR NOT NULL,
                value_kind VARCHAR NOT NULL,
                value_text VARCHAR,
                value_payload JSON,
                unit_code VARCHAR,
                valid_time_kind VARCHAR NOT NULL,
                valid_time_at TIMESTAMPTZ,
                valid_time_from TIMESTAMPTZ,
                valid_time_to TIMESTAMPTZ,
                valid_time_precision VARCHAR NOT NULL,
                valid_time_text VARCHAR,
                observed_at TIMESTAMPTZ,
                observed_at_precision VARCHAR NOT NULL,
                observed_at_text VARCHAR,
                known_at TIMESTAMPTZ NOT NULL,
                confidence DOUBLE NOT NULL,
                publication_status VARCHAR NOT NULL,
                evidence_fragment_ids JSON NOT NULL
            )
            """
        )
        for reality_item in timeline.reality:
            subject_key, entity_id, industry_id = _subject_values(reality_item.subject)
            connection.execute(
                """
                INSERT INTO reality_memory
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(reality_item.canonical_fact_version_id),
                    subject_key,
                    entity_id,
                    industry_id,
                    reality_item.predicate_code,
                    reality_item.value_kind,
                    reality_item.value_text,
                    reality_item.value_payload,
                    reality_item.unit_code,
                    *_extent_values(reality_item.valid_time),
                    (
                        reality_item.observed_time.at
                        if reality_item.observed_time is not None
                        else None
                    ),
                    (
                        reality_item.observed_time.precision.value
                        if reality_item.observed_time is not None
                        else TemporalPrecision.UNKNOWN.value
                    ),
                    (
                        reality_item.observed_time.source_text
                        if reality_item.observed_time is not None
                        else None
                    ),
                    reality_item.known_at,
                    reality_item.confidence,
                    reality_item.publication_status,
                    _json([str(value) for value in reality_item.evidence_fragment_ids]),
                ],
            )

        connection.execute(
            """
            CREATE TABLE judgment_memory (
                judgment_id VARCHAR PRIMARY KEY,
                judgment_key VARCHAR,
                subject_key VARCHAR NOT NULL,
                subject_entity_id VARCHAR,
                subject_industry_node_id VARCHAR,
                speaker_name_text VARCHAR,
                topic_code VARCHAR NOT NULL,
                judgment_kind VARCHAR NOT NULL,
                target_time_kind VARCHAR NOT NULL,
                target_time_at TIMESTAMPTZ,
                target_time_from TIMESTAMPTZ,
                target_time_to TIMESTAMPTZ,
                target_time_precision VARCHAR NOT NULL,
                target_time_text VARCHAR,
                value_kind VARCHAR NOT NULL,
                value_text VARCHAR,
                value_payload JSON,
                summary VARCHAR NOT NULL,
                known_at TIMESTAMPTZ NOT NULL,
                evidence_fragment_ids JSON NOT NULL
            )
            """
        )
        for judgment_item in timeline.judgments:
            subject_key, entity_id, industry_id = _subject_values(judgment_item.subject)
            connection.execute(
                """
                INSERT INTO judgment_memory
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(judgment_item.judgment_id),
                    judgment_item.judgment_key,
                    subject_key,
                    entity_id,
                    industry_id,
                    judgment_item.speaker_name_text,
                    judgment_item.topic_code,
                    judgment_item.judgment_kind,
                    *_extent_values(judgment_item.target_time),
                    judgment_item.value_kind,
                    judgment_item.value_text,
                    judgment_item.value_payload,
                    judgment_item.summary,
                    judgment_item.known_at,
                    _json([str(value) for value in judgment_item.evidence_fragment_ids]),
                ],
            )

        connection.execute(
            """
            CREATE TABLE judgment_rationale_memory (
                rationale_id VARCHAR PRIMARY KEY,
                judgment_id VARCHAR NOT NULL,
                rationale_kind VARCHAR NOT NULL,
                summary VARCHAR NOT NULL,
                linked_fact_assertion_id VARCHAR,
                linked_judgment_id VARCHAR,
                evidence_fragment_id VARCHAR,
                ordinal INTEGER NOT NULL,
                known_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        for rationale_item in timeline.judgment_rationales:
            connection.execute(
                """
                INSERT INTO judgment_rationale_memory
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(rationale_item.rationale_id),
                    str(rationale_item.judgment_id),
                    rationale_item.rationale_kind.value,
                    rationale_item.summary,
                    (
                        str(rationale_item.linked_fact_assertion_id)
                        if rationale_item.linked_fact_assertion_id
                        else None
                    ),
                    (
                        str(rationale_item.linked_judgment_id)
                        if rationale_item.linked_judgment_id
                        else None
                    ),
                    (
                        str(rationale_item.evidence_fragment_id)
                        if rationale_item.evidence_fragment_id
                        else None
                    ),
                    rationale_item.ordinal,
                    rationale_item.known_at,
                ],
            )

        connection.execute(
            """
            CREATE TABLE judgment_relation_memory (
                from_judgment_id VARCHAR NOT NULL,
                to_judgment_id VARCHAR NOT NULL,
                relation_type VARCHAR NOT NULL,
                reason_summary VARCHAR,
                known_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (from_judgment_id, to_judgment_id, relation_type)
            )
            """
        )
        for relation_item in timeline.judgment_relations:
            connection.execute(
                """
                INSERT INTO judgment_relation_memory
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    str(relation_item.from_judgment_id),
                    str(relation_item.to_judgment_id),
                    relation_item.relation_type.value,
                    relation_item.reason_summary,
                    relation_item.known_at,
                ],
            )

        connection.execute(
            """
            CREATE TABLE outcome_memory (
                evaluation_id VARCHAR PRIMARY KEY,
                judgment_id VARCHAR NOT NULL,
                subject_key VARCHAR NOT NULL,
                subject_entity_id VARCHAR,
                subject_industry_node_id VARCHAR,
                canonical_fact_version_id VARCHAR,
                outcome_evidence_fragment_id VARCHAR,
                evaluation_status VARCHAR NOT NULL,
                semantic_relation VARCHAR NOT NULL,
                occurrence_time_kind VARCHAR NOT NULL,
                occurrence_time_at TIMESTAMPTZ,
                occurrence_time_from TIMESTAMPTZ,
                occurrence_time_to TIMESTAMPTZ,
                occurrence_time_precision VARCHAR NOT NULL,
                occurrence_time_text VARCHAR,
                known_at TIMESTAMPTZ NOT NULL,
                timing_relation VARCHAR NOT NULL,
                timing_delta_value DECIMAL(38, 12),
                timing_delta_unit VARCHAR,
                explanation VARCHAR,
                evaluator_name VARCHAR NOT NULL,
                evaluator_version VARCHAR NOT NULL
            )
            """
        )
        for outcome_item in timeline.outcomes:
            subject_key, entity_id, industry_id = _subject_values(outcome_item.subject)
            connection.execute(
                """
                INSERT INTO outcome_memory
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(outcome_item.evaluation_id),
                    str(outcome_item.judgment_id),
                    subject_key,
                    entity_id,
                    industry_id,
                    (
                        str(outcome_item.canonical_fact_version_id)
                        if outcome_item.canonical_fact_version_id
                        else None
                    ),
                    (
                        str(outcome_item.outcome_evidence_fragment_id)
                        if outcome_item.outcome_evidence_fragment_id
                        else None
                    ),
                    outcome_item.evaluation_status,
                    outcome_item.semantic_relation.value,
                    *_extent_values(outcome_item.occurrence_time),
                    outcome_item.known_at,
                    outcome_item.timing_relation,
                    outcome_item.timing_delta_value,
                    outcome_item.timing_delta_unit,
                    outcome_item.explanation,
                    outcome_item.evaluator_name,
                    outcome_item.evaluator_version,
                ],
            )

        connection.execute(
            "CREATE INDEX reality_known_idx ON reality_memory(subject_key, known_at)"
        )
        connection.execute(
            "CREATE INDEX judgment_known_idx ON judgment_memory(subject_key, known_at)"
        )
        connection.execute(
            "CREATE INDEX judgment_rationale_known_idx ON judgment_rationale_memory(judgment_id, known_at)"
        )
        connection.execute(
            "CREATE INDEX judgment_relation_known_idx ON judgment_relation_memory(from_judgment_id, to_judgment_id, known_at)"
        )
        connection.execute(
            "CREATE INDEX outcome_known_idx ON outcome_memory(subject_key, known_at)"
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    reader = DuckDBEpistemicMemoryReader(path)
    subjects_by_key: dict[str, MemorySubjectRef] = {}
    for reality_item in timeline.reality:
        subjects_by_key[reality_item.subject.key] = reality_item.subject
    for judgment_item in timeline.judgments:
        subjects_by_key[judgment_item.subject.key] = judgment_item.subject
    for outcome_item in timeline.outcomes:
        subjects_by_key[outcome_item.subject.key] = outcome_item.subject
    all_subjects = sorted(subjects_by_key.values(), key=lambda subject: subject.key)

    round_trip = reader._timeline_sync(all_subjects)
    if round_trip != timeline:
        raise RuntimeError("sealed DuckDB generation does not round-trip to the typed timeline")
    return {
        "schema_version": "longcycle-sealed-industrial-memory/v1",
        "duckdb_version": duckdb.__version__,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "file_bytes": path.stat().st_size,
        "counts": {
            "reality": len(timeline.reality),
            "judgments": len(timeline.judgments),
            "outcomes": len(timeline.outcomes),
        },
        "judgment_context_counts": {
            "rationales": len(timeline.judgment_rationales),
            "relations": len(timeline.judgment_relations),
        },
        "subject_keys": [subject.key for subject in all_subjects],
        "typed_round_trip": True,
    }


class DuckDBEpistemicMemoryReader:
    """Read-only point-in-time reader for one sealed portable generation."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @staticmethod
    def _where(
        subjects: Sequence[MemorySubjectRef],
        cutoff: datetime | None,
    ) -> tuple[str, list[Any]]:
        if not subjects:
            raise ValueError("at least one memory subject is required")
        keys = [subject.key for subject in subjects]
        placeholders = ", ".join("?" for _ in keys)
        clause = f"subject_key IN ({placeholders})"
        params: list[Any] = list(keys)
        if cutoff is not None:
            clause += " AND known_at <= ?"
            params.append(cutoff)
        return clause, params

    async def timeline(
        self,
        subjects: Sequence[MemorySubjectRef],
    ) -> IndustrialMemoryTimeline:
        return self._timeline_sync(subjects)

    async def snapshot(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> PointInTimeMemorySnapshot:
        checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
        assert checked is not None
        timeline = self._timeline_sync(subjects, cutoff=checked)
        return PointInTimeMemorySnapshot(
            knowledge_cutoff=checked,
            reality=timeline.reality,
            judgments=timeline.judgments,
            judgment_rationales=timeline.judgment_rationales,
            judgment_relations=timeline.judgment_relations,
            outcomes=timeline.outcomes,
        )

    def _timeline_sync(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        cutoff: datetime | None = None,
    ) -> IndustrialMemoryTimeline:
        duckdb = _duckdb()
        where, params = self._where(subjects, cutoff)
        connection = duckdb.connect(str(self.path), read_only=True)
        try:
            reality_rows = connection.execute(
                f"""
                SELECT * FROM reality_memory
                WHERE {where}
                ORDER BY known_at, canonical_fact_version_id
                """,
                params,
            ).fetchall()
            reality_columns = [column[0] for column in connection.description]
            judgment_rows = connection.execute(
                f"""
                SELECT * FROM judgment_memory
                WHERE {where}
                ORDER BY known_at, judgment_id
                """,
                params,
            ).fetchall()
            judgment_columns = [column[0] for column in connection.description]

            judgment_id_index = judgment_columns.index("judgment_id")
            judgment_ids = [row[judgment_id_index] for row in judgment_rows]
            table_names = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
            rationale_rows: list[tuple[Any, ...]] = []
            rationale_columns: list[str] = []
            relation_rows: list[tuple[Any, ...]] = []
            relation_columns: list[str] = []
            if judgment_ids and "judgment_rationale_memory" in table_names:
                placeholders = ", ".join("?" for _ in judgment_ids)
                rationale_clause = f"judgment_id IN ({placeholders})"
                rationale_params: list[Any] = list(judgment_ids)
                if cutoff is not None:
                    rationale_clause += " AND known_at <= ?"
                    rationale_params.append(cutoff)
                rationale_rows = connection.execute(
                    f"""
                    SELECT * FROM judgment_rationale_memory
                    WHERE {rationale_clause}
                    ORDER BY known_at, judgment_id, ordinal, rationale_id
                    """,
                    rationale_params,
                ).fetchall()
                rationale_columns = [column[0] for column in connection.description]
            if judgment_ids and "judgment_relation_memory" in table_names:
                placeholders = ", ".join("?" for _ in judgment_ids)
                relation_clause = (
                    f"from_judgment_id IN ({placeholders}) "
                    f"AND to_judgment_id IN ({placeholders})"
                )
                relation_params: list[Any] = [*judgment_ids, *judgment_ids]
                if cutoff is not None:
                    relation_clause += " AND known_at <= ?"
                    relation_params.append(cutoff)
                relation_rows = connection.execute(
                    f"""
                    SELECT * FROM judgment_relation_memory
                    WHERE {relation_clause}
                    ORDER BY known_at, from_judgment_id, to_judgment_id, relation_type
                    """,
                    relation_params,
                ).fetchall()
                relation_columns = [column[0] for column in connection.description]
            outcome_rows = connection.execute(
                f"""
                SELECT * FROM outcome_memory
                WHERE {where}
                ORDER BY known_at, evaluation_id
                """,
                params,
            ).fetchall()
            outcome_columns = [column[0] for column in connection.description]
        finally:
            connection.close()

        reality = tuple(
            self._reality(dict(zip(reality_columns, row, strict=True)))
            for row in reality_rows
        )
        judgments = tuple(
            self._judgment(dict(zip(judgment_columns, row, strict=True)))
            for row in judgment_rows
        )
        rationales = tuple(
            self._judgment_rationale(dict(zip(rationale_columns, row, strict=True)))
            for row in rationale_rows
        )
        relations = tuple(
            self._judgment_relation(dict(zip(relation_columns, row, strict=True)))
            for row in relation_rows
        )
        outcomes = tuple(
            self._outcome(dict(zip(outcome_columns, row, strict=True)))
            for row in outcome_rows
        )
        return IndustrialMemoryTimeline(
            reality=reality,
            judgments=judgments,
            judgment_rationales=rationales,
            judgment_relations=relations,
            outcomes=outcomes,
        )

    @staticmethod
    def _extent(row: dict[str, Any], prefix: str) -> TemporalExtent:
        return TemporalExtent(
            kind=row[f"{prefix}_kind"],
            at=row[f"{prefix}_at"],
            start=row[f"{prefix}_from"],
            end=row[f"{prefix}_to"],
            precision=TemporalPrecision(row[f"{prefix}_precision"]),
            source_text=row[f"{prefix}_text"],
        )

    @classmethod
    def _reality(cls, row: dict[str, Any]) -> CanonicalRealityRecord:
        return CanonicalRealityRecord(
            canonical_fact_version_id=UUID(row["canonical_fact_version_id"]),
            subject=_subject_from_values(
                row["subject_entity_id"],
                row["subject_industry_node_id"],
            ),
            predicate_code=row["predicate_code"],
            value_kind=row["value_kind"],
            value_text=row["value_text"],
            value_payload=row["value_payload"],
            unit_code=row["unit_code"],
            valid_time=cls._extent(row, "valid_time"),
            observed_time=(
                TemporalExtent(
                    kind="instant",
                    at=row.get("observed_at"),
                    precision=TemporalPrecision(
                        row.get("observed_at_precision", TemporalPrecision.UNKNOWN.value)
                    ),
                    source_text=row.get("observed_at_text"),
                )
                if row.get("observed_at") is not None
                else None
            ),
            known_at=row["known_at"],
            confidence=row["confidence"],
            publication_status=row["publication_status"],
            evidence_fragment_ids=tuple(
                UUID(value) for value in json.loads(row["evidence_fragment_ids"])
            ),
        )

    @classmethod
    def _judgment(cls, row: dict[str, Any]) -> JudgmentMemoryRecord:
        return JudgmentMemoryRecord(
            judgment_id=UUID(row["judgment_id"]),
            judgment_key=row["judgment_key"],
            subject=_subject_from_values(
                row["subject_entity_id"],
                row["subject_industry_node_id"],
            ),
            speaker_name_text=row["speaker_name_text"],
            topic_code=row["topic_code"],
            judgment_kind=row["judgment_kind"],
            target_time=cls._extent(row, "target_time"),
            value_kind=row["value_kind"],
            value_text=row["value_text"],
            value_payload=row["value_payload"],
            summary=row["summary"],
            known_at=row["known_at"],
            evidence_fragment_ids=tuple(
                UUID(value) for value in json.loads(row["evidence_fragment_ids"])
            ),
        )

    @staticmethod
    def _judgment_rationale(row: dict[str, Any]) -> JudgmentRationaleMemoryRecord:
        return JudgmentRationaleMemoryRecord(
            rationale_id=UUID(row["rationale_id"]),
            judgment_id=UUID(row["judgment_id"]),
            rationale_kind=JudgmentRationaleKind(row["rationale_kind"]),
            summary=row["summary"],
            linked_fact_assertion_id=(
                UUID(row["linked_fact_assertion_id"])
                if row["linked_fact_assertion_id"]
                else None
            ),
            linked_judgment_id=(
                UUID(row["linked_judgment_id"])
                if row["linked_judgment_id"]
                else None
            ),
            evidence_fragment_id=(
                UUID(row["evidence_fragment_id"])
                if row["evidence_fragment_id"]
                else None
            ),
            ordinal=row["ordinal"],
            known_at=row["known_at"],
        )

    @staticmethod
    def _judgment_relation(row: dict[str, Any]) -> JudgmentRelationMemoryRecord:
        return JudgmentRelationMemoryRecord(
            from_judgment_id=UUID(row["from_judgment_id"]),
            to_judgment_id=UUID(row["to_judgment_id"]),
            relation_type=JudgmentRelationType(row["relation_type"]),
            reason_summary=row["reason_summary"],
            known_at=row["known_at"],
        )

    @classmethod
    def _outcome(cls, row: dict[str, Any]) -> OutcomeMemoryRecord:
        delta = row["timing_delta_value"]
        return OutcomeMemoryRecord(
            evaluation_id=UUID(row["evaluation_id"]),
            judgment_id=UUID(row["judgment_id"]),
            subject=_subject_from_values(
                row["subject_entity_id"],
                row["subject_industry_node_id"],
            ),
            canonical_fact_version_id=(
                UUID(row["canonical_fact_version_id"])
                if row["canonical_fact_version_id"]
                else None
            ),
            outcome_evidence_fragment_id=(
                UUID(row["outcome_evidence_fragment_id"])
                if row["outcome_evidence_fragment_id"]
                else None
            ),
            evaluation_status=row["evaluation_status"],
            semantic_relation=row["semantic_relation"],
            occurrence_time=cls._extent(row, "occurrence_time"),
            known_at=row["known_at"],
            timing_relation=row["timing_relation"],
            timing_delta_value=Decimal(delta) if delta is not None else None,
            timing_delta_unit=row["timing_delta_unit"],
            explanation=row["explanation"],
            evaluator_name=row["evaluator_name"],
            evaluator_version=row["evaluator_version"],
        )