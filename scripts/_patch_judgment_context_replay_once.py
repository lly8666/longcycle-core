from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:160]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# --- Typed epistemic domain: preserve rationale + revision graph in replay. ---
replace_once(
    "src/longcycle/domain/epistemic.py",
    """from .enums import (\n    JudgmentOutcomeStatus,\n    OutcomeSemanticRelation,\n    OutcomeTimingRelation,\n    TemporalPrecision,\n)\n""",
    """from .enums import (\n    JudgmentOutcomeStatus,\n    JudgmentRationaleKind,\n    JudgmentRelationType,\n    OutcomeSemanticRelation,\n    OutcomeTimingRelation,\n    TemporalPrecision,\n)\n""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """class OutcomeMemoryRecord(DomainModel):\n""",
    """class JudgmentRationaleMemoryRecord(DomainModel):\n    \"\"\"Point-in-time rationale attached to an immutable Judgment.\"\"\"\n\n    rationale_id: UUID\n    judgment_id: UUID\n    rationale_kind: JudgmentRationaleKind\n    summary: str = Field(min_length=1)\n    linked_fact_assertion_id: UUID | None = None\n    linked_judgment_id: UUID | None = None\n    evidence_fragment_id: UUID | None = None\n    ordinal: int = Field(default=0, ge=0)\n    known_at: datetime\n\n    @field_validator(\"known_at\")\n    @classmethod\n    def known_time_is_aware(cls, value: datetime) -> datetime:\n        checked = require_aware_datetime(value, \"known_at\")\n        assert checked is not None\n        return checked\n\n\nclass JudgmentRelationMemoryRecord(DomainModel):\n    \"\"\"Typed revision/dependency edge visible only once both Judgments are knowable.\"\"\"\n\n    from_judgment_id: UUID\n    to_judgment_id: UUID\n    relation_type: JudgmentRelationType\n    reason_summary: str | None = None\n    known_at: datetime\n\n    @field_validator(\"known_at\")\n    @classmethod\n    def known_time_is_aware(cls, value: datetime) -> datetime:\n        checked = require_aware_datetime(value, \"known_at\")\n        assert checked is not None\n        return checked\n\n\nclass OutcomeMemoryRecord(DomainModel):\n""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """    reality: tuple[CanonicalRealityRecord, ...] = ()\n    judgments: tuple[JudgmentMemoryRecord, ...] = ()\n    outcomes: tuple[OutcomeMemoryRecord, ...] = ()\n\n    @model_validator(mode=\"after\")\n    def deterministic_order_and_references(self) -> \"IndustrialMemoryTimeline\":\n        expected_reality = tuple(\n            sorted(self.reality, key=lambda item: (item.known_at, str(item.canonical_fact_version_id)))\n        )\n        expected_judgments = tuple(\n            sorted(self.judgments, key=lambda item: (item.known_at, str(item.judgment_id)))\n        )\n        expected_outcomes = tuple(\n            sorted(self.outcomes, key=lambda item: (item.known_at, str(item.evaluation_id)))\n        )\n        if self.reality != expected_reality or self.judgments != expected_judgments or self.outcomes != expected_outcomes:\n            raise ValueError(\"industrial memory timeline must be deterministically ordered\")\n        judgment_ids = {item.judgment_id for item in self.judgments}\n        reality_ids = {item.canonical_fact_version_id for item in self.reality}\n        for outcome in self.outcomes:\n""",
    """    reality: tuple[CanonicalRealityRecord, ...] = ()\n    judgments: tuple[JudgmentMemoryRecord, ...] = ()\n    judgment_rationales: tuple[JudgmentRationaleMemoryRecord, ...] = ()\n    judgment_relations: tuple[JudgmentRelationMemoryRecord, ...] = ()\n    outcomes: tuple[OutcomeMemoryRecord, ...] = ()\n\n    @model_validator(mode=\"after\")\n    def deterministic_order_and_references(self) -> \"IndustrialMemoryTimeline\":\n        expected_reality = tuple(\n            sorted(self.reality, key=lambda item: (item.known_at, str(item.canonical_fact_version_id)))\n        )\n        expected_judgments = tuple(\n            sorted(self.judgments, key=lambda item: (item.known_at, str(item.judgment_id)))\n        )\n        expected_rationales = tuple(\n            sorted(\n                self.judgment_rationales,\n                key=lambda item: (\n                    item.known_at,\n                    str(item.judgment_id),\n                    item.ordinal,\n                    str(item.rationale_id),\n                ),\n            )\n        )\n        expected_relations = tuple(\n            sorted(\n                self.judgment_relations,\n                key=lambda item: (\n                    item.known_at,\n                    str(item.from_judgment_id),\n                    str(item.to_judgment_id),\n                    item.relation_type.value,\n                ),\n            )\n        )\n        expected_outcomes = tuple(\n            sorted(self.outcomes, key=lambda item: (item.known_at, str(item.evaluation_id)))\n        )\n        if (\n            self.reality != expected_reality\n            or self.judgments != expected_judgments\n            or self.judgment_rationales != expected_rationales\n            or self.judgment_relations != expected_relations\n            or self.outcomes != expected_outcomes\n        ):\n            raise ValueError(\"industrial memory timeline must be deterministically ordered\")\n        judgment_ids = {item.judgment_id for item in self.judgments}\n        reality_ids = {item.canonical_fact_version_id for item in self.reality}\n        for rationale in self.judgment_rationales:\n            if rationale.judgment_id not in judgment_ids:\n                raise ValueError(\"Judgment rationale references a Judgment missing from the timeline\")\n        for relation in self.judgment_relations:\n            if (\n                relation.from_judgment_id not in judgment_ids\n                or relation.to_judgment_id not in judgment_ids\n            ):\n                raise ValueError(\"Judgment relation references a Judgment missing from the timeline\")\n        for outcome in self.outcomes:\n""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """    reality: tuple[CanonicalRealityRecord, ...] = ()\n    judgments: tuple[JudgmentMemoryRecord, ...] = ()\n    outcomes: tuple[OutcomeMemoryRecord, ...] = ()\n\n    @field_validator(\"knowledge_cutoff\")\n""",
    """    reality: tuple[CanonicalRealityRecord, ...] = ()\n    judgments: tuple[JudgmentMemoryRecord, ...] = ()\n    judgment_rationales: tuple[JudgmentRationaleMemoryRecord, ...] = ()\n    judgment_relations: tuple[JudgmentRelationMemoryRecord, ...] = ()\n    outcomes: tuple[OutcomeMemoryRecord, ...] = ()\n\n    @field_validator(\"knowledge_cutoff\")\n""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """        future = [\n            item.known_at\n            for group in (self.reality, self.judgments, self.outcomes)\n            for item in group\n            if item.known_at > self.knowledge_cutoff\n        ]\n""",
    """        future = [\n            item.known_at\n            for group in (\n                self.reality,\n                self.judgments,\n                self.judgment_rationales,\n                self.judgment_relations,\n                self.outcomes,\n            )\n            for item in group\n            if item.known_at > self.knowledge_cutoff\n        ]\n""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """        reality=tuple(item for item in timeline.reality if item.known_at <= checked),\n        judgments=tuple(item for item in timeline.judgments if item.known_at <= checked),\n        outcomes=tuple(item for item in timeline.outcomes if item.known_at <= checked),\n""",
    """        reality=tuple(item for item in timeline.reality if item.known_at <= checked),\n        judgments=tuple(item for item in timeline.judgments if item.known_at <= checked),\n        judgment_rationales=tuple(\n            item for item in timeline.judgment_rationales if item.known_at <= checked\n        ),\n        judgment_relations=tuple(\n            item for item in timeline.judgment_relations if item.known_at <= checked\n        ),\n        outcomes=tuple(item for item in timeline.outcomes if item.known_at <= checked),\n""",
)

# --- PostgreSQL typed read model. No migration: derive epistemic availability from existing rows. ---
replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    MemorySubjectRef,\n""",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    JudgmentRationaleMemoryRecord,\n    JudgmentRelationMemoryRecord,\n    MemorySubjectRef,\n""",
)
replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    "from longcycle.domain.enums import TemporalPrecision\n",
    "from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision\n",
)

replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """            reality_rows = await self._reality_rows(connection, entity_ids, industry_ids)\n            judgment_rows = await self._judgment_rows(connection, entity_ids, industry_ids)\n            outcome_rows = await self._outcome_rows(connection, entity_ids, industry_ids)\n        return IndustrialMemoryTimeline(\n            reality=tuple(self._reality_record(row) for row in reality_rows),\n            judgments=tuple(self._judgment_record(row) for row in judgment_rows),\n            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),\n        )\n""",
    """            reality_rows = await self._reality_rows(connection, entity_ids, industry_ids)\n            judgment_rows = await self._judgment_rows(connection, entity_ids, industry_ids)\n            judgment_ids = [row[\"judgment_id\"] for row in judgment_rows]\n            rationale_rows = await self._judgment_rationale_rows(connection, judgment_ids)\n            relation_rows = await self._judgment_relation_rows(connection, judgment_ids)\n            outcome_rows = await self._outcome_rows(connection, entity_ids, industry_ids)\n        return IndustrialMemoryTimeline(\n            reality=tuple(self._reality_record(row) for row in reality_rows),\n            judgments=tuple(self._judgment_record(row) for row in judgment_rows),\n            judgment_rationales=tuple(\n                self._judgment_rationale_record(row) for row in rationale_rows\n            ),\n            judgment_relations=tuple(\n                self._judgment_relation_record(row) for row in relation_rows\n            ),\n            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),\n        )\n""",
)

replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """            judgment_rows = await self._judgment_rows(\n                connection, entity_ids, industry_ids, knowledge_cutoff=checked\n            )\n            outcome_rows = await self._outcome_rows(\n                connection, entity_ids, industry_ids, knowledge_cutoff=checked\n            )\n        timeline = IndustrialMemoryTimeline(\n            reality=tuple(self._reality_record(row) for row in reality_rows),\n            judgments=tuple(self._judgment_record(row) for row in judgment_rows),\n            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),\n        )\n""",
    """            judgment_rows = await self._judgment_rows(\n                connection, entity_ids, industry_ids, knowledge_cutoff=checked\n            )\n            judgment_ids = [row[\"judgment_id\"] for row in judgment_rows]\n            rationale_rows = await self._judgment_rationale_rows(\n                connection, judgment_ids, knowledge_cutoff=checked\n            )\n            relation_rows = await self._judgment_relation_rows(\n                connection, judgment_ids, knowledge_cutoff=checked\n            )\n            outcome_rows = await self._outcome_rows(\n                connection, entity_ids, industry_ids, knowledge_cutoff=checked\n            )\n        timeline = IndustrialMemoryTimeline(\n            reality=tuple(self._reality_record(row) for row in reality_rows),\n            judgments=tuple(self._judgment_record(row) for row in judgment_rows),\n            judgment_rationales=tuple(\n                self._judgment_rationale_record(row) for row in rationale_rows\n            ),\n            judgment_relations=tuple(\n                self._judgment_relation_record(row) for row in relation_rows\n            ),\n            outcomes=tuple(self._outcome_record(row) for row in outcome_rows),\n        )\n""",
)

rationale_methods = r'''
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
                       linked_fact.known_at,
                       rationale_document.first_known_at
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
            LEFT JOIN evidence.source_documents rationale_document
              ON rationale_document.id = rationale_evidence.document_id
            WHERE rationale.judgment_id = ANY(%s::uuid[])
              AND (
                    %s::timestamptz IS NULL
                 OR GREATEST(
                        owner.first_known_at,
                        linked_judgment.first_known_at,
                        linked_fact.known_at,
                        rationale_document.first_known_at
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

'''
replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    "    @staticmethod\n    async def _outcome_rows(\n",
    rationale_methods + "    @staticmethod\n    async def _outcome_rows(\n",
)

record_methods = r'''
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

'''
replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    "    @staticmethod\n    def _outcome_record(row: dict[str, Any]) -> OutcomeMemoryRecord:\n",
    record_methods + "    @staticmethod\n    def _outcome_record(row: dict[str, Any]) -> OutcomeMemoryRecord:\n",
)

# --- Sealed DuckDB: portable cognitive context. ---
replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    MemorySubjectRef,\n""",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    JudgmentRationaleMemoryRecord,\n    JudgmentRelationMemoryRecord,\n    MemorySubjectRef,\n""",
)
replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    "from longcycle.domain.enums import TemporalPrecision\n",
    "from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision\n",
)

judgment_context_tables = r'''
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

'''
replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """        connection.execute(\n            \"\"\"\n            CREATE TABLE outcome_memory (\n""",
    judgment_context_tables + """        connection.execute(\n            \"\"\"\n            CREATE TABLE outcome_memory (\n""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """        connection.execute(\n            \"CREATE INDEX judgment_known_idx ON judgment_memory(subject_key, known_at)\"\n        )\n        connection.execute(\n            \"CREATE INDEX outcome_known_idx ON outcome_memory(subject_key, known_at)\"\n        )\n""",
    """        connection.execute(\n            \"CREATE INDEX judgment_known_idx ON judgment_memory(subject_key, known_at)\"\n        )\n        connection.execute(\n            \"CREATE INDEX judgment_rationale_known_idx ON judgment_rationale_memory(judgment_id, known_at)\"\n        )\n        connection.execute(\n            \"CREATE INDEX judgment_relation_known_idx ON judgment_relation_memory(from_judgment_id, to_judgment_id, known_at)\"\n        )\n        connection.execute(\n            \"CREATE INDEX outcome_known_idx ON outcome_memory(subject_key, known_at)\"\n        )\n""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """        \"counts\": {\n            \"reality\": len(timeline.reality),\n            \"judgments\": len(timeline.judgments),\n            \"outcomes\": len(timeline.outcomes),\n        },\n        \"subject_keys\": [subject.key for subject in all_subjects],\n""",
    """        \"counts\": {\n            \"reality\": len(timeline.reality),\n            \"judgments\": len(timeline.judgments),\n            \"outcomes\": len(timeline.outcomes),\n        },\n        \"judgment_context_counts\": {\n            \"rationales\": len(timeline.judgment_rationales),\n            \"relations\": len(timeline.judgment_relations),\n        },\n        \"subject_keys\": [subject.key for subject in all_subjects],\n""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """        return PointInTimeMemorySnapshot(\n            knowledge_cutoff=checked,\n            reality=timeline.reality,\n            judgments=timeline.judgments,\n            outcomes=timeline.outcomes,\n        )\n""",
    """        return PointInTimeMemorySnapshot(\n            knowledge_cutoff=checked,\n            reality=timeline.reality,\n            judgments=timeline.judgments,\n            judgment_rationales=timeline.judgment_rationales,\n            judgment_relations=timeline.judgment_relations,\n            outcomes=timeline.outcomes,\n        )\n""",
)

reader_context_query = r'''
            judgment_id_index = judgment_columns.index("judgment_id")
            judgment_ids = [row[judgment_id_index] for row in judgment_rows]
            rationale_rows: list[tuple[Any, ...]] = []
            rationale_columns: list[str] = []
            relation_rows: list[tuple[Any, ...]] = []
            relation_columns: list[str] = []
            if judgment_ids:
                placeholders = ", ".join("?" for _ in judgment_ids)
                rationale_clause = f"judgment_id IN ({placeholders})"
                rationale_params: list[Any] = list(judgment_ids)
                relation_clause = (
                    f"from_judgment_id IN ({placeholders}) "
                    f"AND to_judgment_id IN ({placeholders})"
                )
                relation_params: list[Any] = [*judgment_ids, *judgment_ids]
                if cutoff is not None:
                    rationale_clause += " AND known_at <= ?"
                    rationale_params.append(cutoff)
                    relation_clause += " AND known_at <= ?"
                    relation_params.append(cutoff)
                rationale_rows = connection.execute(
                    f"""
                    SELECT * FROM judgment_rationale_memory
                    WHERE {rationale_clause}
                    ORDER BY known_at, judgment_id, ordinal, rationale_id
                    """,
                    rationale_params,
                ).fetchall()
                rationale_columns = [column[0] for column in connection.description]
                relation_rows = connection.execute(
                    f"""
                    SELECT * FROM judgment_relation_memory
                    WHERE {relation_clause}
                    ORDER BY known_at, from_judgment_id, to_judgment_id, relation_type
                    """,
                    relation_params,
                ).fetchall()
                relation_columns = [column[0] for column in connection.description]
'''
replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """            judgment_columns = [column[0] for column in connection.description]\n            outcome_rows = connection.execute(\n""",
    """            judgment_columns = [column[0] for column in connection.description]\n""" + reader_context_query + """            outcome_rows = connection.execute(\n""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """        outcomes = tuple(\n            self._outcome(dict(zip(outcome_columns, row, strict=True)))\n            for row in outcome_rows\n        )\n        return IndustrialMemoryTimeline(\n            reality=reality,\n            judgments=judgments,\n            outcomes=outcomes,\n        )\n""",
    """        rationales = tuple(\n            self._judgment_rationale(dict(zip(rationale_columns, row, strict=True)))\n            for row in rationale_rows\n        )\n        relations = tuple(\n            self._judgment_relation(dict(zip(relation_columns, row, strict=True)))\n            for row in relation_rows\n        )\n        outcomes = tuple(\n            self._outcome(dict(zip(outcome_columns, row, strict=True)))\n            for row in outcome_rows\n        )\n        return IndustrialMemoryTimeline(\n            reality=reality,\n            judgments=judgments,\n            judgment_rationales=rationales,\n            judgment_relations=relations,\n            outcomes=outcomes,\n        )\n""",
)

reader_context_records = r'''
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

'''
replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    "    @classmethod\n    def _outcome(cls, row: dict[str, Any]) -> OutcomeMemoryRecord:\n",
    reader_context_records + "    @classmethod\n    def _outcome(cls, row: dict[str, Any]) -> OutcomeMemoryRecord:\n",
)

# --- Unit test: portable replay keeps revision/rationale context behind the cutoff. ---
replace_once(
    "tests/test_epistemic_memory.py",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    MemorySubjectRef,\n""",
    """    IndustrialMemoryTimeline,\n    JudgmentMemoryRecord,\n    JudgmentRationaleMemoryRecord,\n    JudgmentRelationMemoryRecord,\n    MemorySubjectRef,\n""",
)
replace_once(
    "tests/test_epistemic_memory.py",
    "from longcycle.domain.enums import TemporalPrecision\n",
    "from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType, TemporalPrecision\n",
)
replace_once(
    "tests/test_epistemic_memory.py",
    "JUDGMENT_ID = UUID(\"22222222-2222-2222-2222-222222222222\")\n",
    "JUDGMENT_ID = UUID(\"22222222-2222-2222-2222-222222222222\")\nREVISED_JUDGMENT_ID = UUID(\"22222222-2222-2222-2222-222222222223\")\nRATIONALE_ID = UUID(\"77777777-7777-7777-7777-777777777777\")\n",
)
replace_once(
    "tests/test_epistemic_memory.py",
    """    reality = CanonicalRealityRecord(\n""",
    """    revised_judgment = judgment.model_copy(\n        update={\n            \"judgment_id\": REVISED_JUDGMENT_ID,\n            \"judgment_key\": \"first-product-july-revision\",\n            \"target_time\": TemporalExtent(\n                kind=\"period\",\n                start=datetime(2022, 7, 1, tzinfo=UTC),\n                end=datetime(2022, 8, 1, tzinfo=UTC),\n                precision=TemporalPrecision.MONTH,\n                source_text=\"July 2022\",\n            ),\n            \"value_text\": \"first product revised to July 2022\",\n            \"summary\": \"Management revised first-product guidance to July 2022.\",\n            \"known_at\": OUTCOME_KNOWN,\n        }\n    )\n    rationale = JudgmentRationaleMemoryRecord(\n        rationale_id=RATIONALE_ID,\n        judgment_id=REVISED_JUDGMENT_ID,\n        rationale_kind=JudgmentRationaleKind.MECHANISM,\n        summary=\"Qualification took longer than originally expected.\",\n        evidence_fragment_id=OUTCOME_EVIDENCE_ID,\n        known_at=OUTCOME_KNOWN,\n    )\n    relation = JudgmentRelationMemoryRecord(\n        from_judgment_id=REVISED_JUDGMENT_ID,\n        to_judgment_id=JUDGMENT_ID,\n        relation_type=JudgmentRelationType.REVISES,\n        reason_summary=\"July timing replaces the earlier May guidance.\",\n        known_at=OUTCOME_KNOWN,\n    )\n    reality = CanonicalRealityRecord(\n""",
)
replace_once(
    "tests/test_epistemic_memory.py",
    """        reality=(reality,),\n        judgments=(judgment,),\n        outcomes=(outcome,),\n""",
    """        reality=(reality,),\n        judgments=(judgment, revised_judgment),\n        judgment_rationales=(rationale,),\n        judgment_relations=(relation,),\n        outcomes=(outcome,),\n""",
)
replace_once(
    "tests/test_epistemic_memory.py",
    """    assert manifest[\"counts\"] == {\"reality\": 1, \"judgments\": 1, \"outcomes\": 1}\n""",
    """    assert manifest[\"counts\"] == {\"reality\": 1, \"judgments\": 2, \"outcomes\": 1}\n    assert manifest[\"judgment_context_counts\"] == {\"rationales\": 1, \"relations\": 1}\n""",
)
replace_once(
    "tests/test_epistemic_memory.py",
    """    assert len(before.judgments) == 1\n    assert before.reality == ()\n    assert before.outcomes == ()\n\n    at = await reader.snapshot((SUBJECT,), knowledge_cutoff=OUTCOME_KNOWN)\n    assert len(at.judgments) == 1\n""",
    """    assert len(before.judgments) == 1\n    assert before.judgment_rationales == ()\n    assert before.judgment_relations == ()\n    assert before.reality == ()\n    assert before.outcomes == ()\n\n    at = await reader.snapshot((SUBJECT,), knowledge_cutoff=OUTCOME_KNOWN)\n    assert len(at.judgments) == 2\n    assert len(at.judgment_rationales) == 1\n    assert at.judgment_rationales[0].rationale_kind == JudgmentRationaleKind.MECHANISM\n    assert len(at.judgment_relations) == 1\n    assert at.judgment_relations[0].relation_type == JudgmentRelationType.REVISES\n""",
)

# --- Existing PostgreSQL hard smoke: make revision context a protected integration contract. ---
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """    JudgmentKind,\n    JudgmentTargetTimeKind,\n    JudgmentValueKind,\n""",
    """    JudgmentKind,\n    JudgmentRationaleKind,\n    JudgmentRelationType,\n    JudgmentTargetTimeKind,\n    JudgmentValueKind,\n""",
)
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """    JudgmentAssertion,\n    JudgmentEvidenceRef,\n    OutcomeObservation,\n""",
    """    JudgmentAssertion,\n    JudgmentEvidenceRef,\n    JudgmentRationale,\n    JudgmentRelation,\n    OutcomeObservation,\n""",
)
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    "text=\"The production line achieved first product in July 2022.\",\n",
    "text=(\n                \"Management revised first product guidance to July 2022 because qualification \"\n                \"took longer. The production line achieved first product in July 2022.\"\n            ),\n",
)

smoke_revision = r'''
    revised_judgment = judgment.model_copy(
        update={
            "id": stable_uuid_exact("epistemic-smoke", "aug-revised-judgment"),
            "target_from": datetime(2022, 7, 1, tzinfo=UTC),
            "target_to": datetime(2022, 8, 1, tzinfo=UTC),
            "target_text": "July 2022",
            "value_text": "first product guidance revised to July 2022",
            "summary": "Management revised first-product guidance to July 2022.",
            "source_published_at": AUG_KNOWN,
            "first_known_at": AUG_KNOWN,
            "extraction_run_id": aug_run_id,
            "evidence": (
                JudgmentEvidenceRef(
                    evidence_fragment_id=aug_evidence.id,
                    evidence_role=JudgmentEvidenceRole.STATEMENT,
                ),
            ),
            "metadata": {"judgment_key": "july-first-product-revision"},
        }
    )
    rationale = JudgmentRationale(
        id=stable_uuid_exact("epistemic-smoke", "aug-revision-rationale"),
        judgment_id=revised_judgment.id,
        rationale_kind=JudgmentRationaleKind.MECHANISM,
        summary="Qualification took longer than originally expected.",
        evidence_fragment_id=aug_evidence.id,
    )
    relation = JudgmentRelation(
        from_judgment_id=revised_judgment.id,
        to_judgment_id=judgment.id,
        relation_type=JudgmentRelationType.REVISES,
        reason_summary="July guidance replaces the earlier May target.",
    )
'''
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """    judgments = PostgresJudgmentRepository(dsn)\n    try:\n        await judgments.append_judgments((judgment,))\n        await judgments.append_judgments((judgment,))\n    finally:\n""",
    smoke_revision + """    judgments = PostgresJudgmentRepository(dsn)\n    try:\n        await judgments.append_judgments((judgment, revised_judgment))\n        await judgments.append_judgments((judgment, revised_judgment))\n        await judgments.append_rationales((rationale,))\n        await judgments.append_rationales((rationale,))\n        await judgments.append_relations((relation,))\n        await judgments.append_relations((relation,))\n    finally:\n""",
)
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """        if len(at_reality.reality) != 1 or len(at_reality.judgments) != 1:\n            raise AssertionError(f\"Reality/Judgment boundary is incomplete: {at_reality}\")\n""",
    """        if len(at_reality.reality) != 1 or len(at_reality.judgments) != 2:\n            raise AssertionError(f\"Reality/Judgment boundary is incomplete: {at_reality}\")\n        if len(at_reality.judgment_rationales) != 1:\n            raise AssertionError(\"Judgment rationale was not replayed from PostgreSQL\")\n        if len(at_reality.judgment_relations) != 1:\n            raise AssertionError(\"Judgment revision relation was not replayed from PostgreSQL\")\n        if at_reality.judgment_relations[0].relation_type != JudgmentRelationType.REVISES:\n            raise AssertionError(\"Judgment revision relation lost its typed semantics\")\n""",
)
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """    if (len(at_outcome.reality), len(at_outcome.judgments), len(at_outcome.outcomes)) != (1, 1, 1):\n        raise AssertionError(f\"integrated PostgreSQL replay is incomplete: {at_outcome}\")\n""",
    """    if (len(at_outcome.reality), len(at_outcome.judgments), len(at_outcome.outcomes)) != (1, 2, 1):\n        raise AssertionError(f\"integrated PostgreSQL replay is incomplete: {at_outcome}\")\n    if (len(at_outcome.judgment_rationales), len(at_outcome.judgment_relations)) != (1, 1):\n        raise AssertionError(\"integrated PostgreSQL replay lost Judgment context\")\n""",
)
replace_once(
    "scripts/smoke_postgres_epistemic.py",
    """    if (len(portable_at.reality), len(portable_at.judgments), len(portable_at.outcomes)) != (1, 1, 1):\n        raise AssertionError(\"portable replay does not match PostgreSQL typed memory\")\n""",
    """    if (len(portable_at.reality), len(portable_at.judgments), len(portable_at.outcomes)) != (1, 2, 1):\n        raise AssertionError(\"portable replay does not match PostgreSQL typed memory\")\n    if (len(portable_at.judgment_rationales), len(portable_at.judgment_relations)) != (1, 1):\n        raise AssertionError(\"portable replay lost Judgment context\")\n""",
)

print("JUDGMENT_CONTEXT_REPLAY_PATCH_APPLIED")
