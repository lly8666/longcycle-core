from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from longcycle.domain.judgments import (
    JudgmentAssertion,
    JudgmentRationale,
    JudgmentRelation,
)
from longcycle.domain.models import FactDimensions

from .postgres import PostgresSupport


_FINGERPRINT_KEY = "_longcycle_content_sha256"
_COMPARABILITY_DIMENSIONS_KEY = "comparability_dimensions"


class InMemoryJudgmentRepository:
    def __init__(self) -> None:
        self.judgments: dict[UUID, JudgmentAssertion] = {}
        self.rationales: dict[UUID, JudgmentRationale] = {}
        self.relations: dict[tuple[UUID, UUID, str], JudgmentRelation] = {}
        self._lock = asyncio.Lock()

    async def append_judgments(self, judgments: Sequence[JudgmentAssertion]) -> None:
        async with self._lock:
            for judgment in judgments:
                existing = self.judgments.get(judgment.id)
                if existing is not None and existing.content_fingerprint != judgment.content_fingerprint:
                    raise ValueError("judgment id already maps to different immutable content")
                self.judgments.setdefault(judgment.id, judgment)

    async def append_rationales(self, rationales: Sequence[JudgmentRationale]) -> None:
        async with self._lock:
            for rationale in rationales:
                if rationale.judgment_id not in self.judgments:
                    raise ValueError("judgment rationale references an unknown judgment")
                existing = self.rationales.get(rationale.id)
                if existing is not None and existing != rationale:
                    raise ValueError("judgment rationale id already maps to different content")
                self.rationales.setdefault(rationale.id, rationale)

    async def append_relations(self, relations: Sequence[JudgmentRelation]) -> None:
        async with self._lock:
            for relation in relations:
                if relation.from_judgment_id not in self.judgments:
                    raise ValueError("judgment relation references an unknown source judgment")
                if relation.to_judgment_id not in self.judgments:
                    raise ValueError("judgment relation references an unknown target judgment")
                key = (
                    relation.from_judgment_id,
                    relation.to_judgment_id,
                    relation.relation_type.value,
                )
                existing = self.relations.get(key)
                if existing is not None and existing != relation:
                    raise ValueError("judgment relation key already maps to different content")
                self.relations.setdefault(key, relation)


class PostgresJudgmentRepository(PostgresSupport):
    async def _ensure_comparability_identity(
        self,
        connection: Any,
        judgment: JudgmentAssertion,
    ) -> None:
        if judgment.comparability_hash is None:
            return
        payload = judgment.metadata.get(_COMPARABILITY_DIMENSIONS_KEY)
        if not isinstance(payload, dict):
            raise ValueError(
                "judgment with comparability_hash must preserve comparability_dimensions metadata"
            )
        dimensions = FactDimensions.model_validate(payload)
        if dimensions.comparability_hash != judgment.comparability_hash:
            raise ValueError("judgment comparability hash does not match canonical dimension payload")

        await connection.execute(
            """
            INSERT INTO research.fact_dimension_sets (
                comparability_hash, schema_version, product_spec_id,
                geography_scheme, geography_code, market_basis, contract_basis,
                tax_basis, freight_basis, incoterm, currency_code, frequency,
                price_component, statistical_scope, canonical_payload
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (comparability_hash) DO NOTHING
            """,
            (
                judgment.comparability_hash,
                dimensions.schema_version,
                dimensions.product_spec_id,
                dimensions.geography_scheme,
                dimensions.geography_code,
                dimensions.market_basis.value if dimensions.market_basis else None,
                dimensions.contract_basis,
                dimensions.tax_basis.value if dimensions.tax_basis else None,
                dimensions.freight_basis.value if dimensions.freight_basis else None,
                dimensions.incoterm,
                dimensions.currency_code,
                dimensions.frequency.value if dimensions.frequency else None,
                dimensions.price_component.value if dimensions.price_component else None,
                dimensions.statistical_scope,
                self.jsonb(dimensions.canonical_payload),
            ),
        )
        dimension_cursor = await connection.execute(
            """
            SELECT canonical_payload
            FROM research.fact_dimension_sets
            WHERE comparability_hash = %s
            """,
            (judgment.comparability_hash,),
        )
        stored_dimension = await dimension_cursor.fetchone()
        if (
            stored_dimension is None
            or stored_dimension["canonical_payload"] != dimensions.canonical_payload
        ):
            raise ValueError("comparability hash maps to a different canonical dimension payload")

    async def append_judgments(self, judgments: Sequence[JudgmentAssertion]) -> None:
        async with self.connection() as connection:
            evidence_ids = sorted(
                {
                    link.evidence_fragment_id
                    for judgment in judgments
                    for link in judgment.evidence
                },
                key=str,
            )
            if evidence_ids:
                cursor = await connection.execute(
                    "SELECT id FROM evidence.evidence_fragments WHERE id = ANY(%s)",
                    (evidence_ids,),
                )
                found = {row["id"] for row in await cursor.fetchall()}
                missing = set(evidence_ids) - found
                if missing:
                    raise ValueError(
                        "judgment references unknown evidence fragments: "
                        + ", ".join(sorted(str(item) for item in missing))
                    )

            unit_codes = sorted({judgment.unit_code for judgment in judgments if judgment.unit_code})
            if unit_codes:
                unit_cursor = await connection.execute(
                    "SELECT code FROM core.units WHERE code = ANY(%s)",
                    (unit_codes,),
                )
                registered = {row["code"] for row in await unit_cursor.fetchall()}
                unknown = sorted(set(unit_codes) - registered)
                if unknown:
                    raise ValueError(
                        "judgments contain unregistered units: " + ", ".join(unknown)
                    )

            for judgment in judgments:
                await self._ensure_comparability_identity(connection, judgment)
                fingerprint = judgment.content_fingerprint
                existing_cursor = await connection.execute(
                    """
                    SELECT metadata ->> %s AS content_fingerprint
                    FROM research.judgment_assertions
                    WHERE id = %s
                    """,
                    (_FINGERPRINT_KEY, judgment.id),
                )
                existing = await existing_cursor.fetchone()
                if existing is not None:
                    if existing["content_fingerprint"] != fingerprint:
                        raise ValueError("judgment id already maps to different immutable content")
                else:
                    metadata = {**judgment.metadata, _FINGERPRINT_KEY: fingerprint}
                    await connection.execute(
                        """
                        INSERT INTO research.judgment_assertions (
                            id, speaker_entity_id, speaker_name_text, speaker_role,
                            speaker_affiliation_entity_id, subject_entity_id,
                            subject_industry_node_id, topic_code, predicate_code,
                            comparability_hash, dimensions_complete, judgment_kind,
                            target_time_kind, target_at, target_from, target_to,
                            target_precision, target_text,
                            value_kind, value_numeric, value_low, value_high,
                            value_text, value_boolean, value_date, value_entity_id,
                            value_json, direction, unit_code, expressed_probability,
                            summary, source_published_at, first_known_at,
                            extraction_run_id, source_connector_id, extractor_name,
                            extractor_version, extraction_confidence, metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            judgment.id,
                            judgment.speaker_entity_id,
                            judgment.speaker_name_text,
                            judgment.speaker_role,
                            judgment.speaker_affiliation_entity_id,
                            judgment.subject_entity_id,
                            judgment.subject_industry_node_id,
                            judgment.topic_code,
                            judgment.predicate_code,
                            judgment.comparability_hash,
                            judgment.dimensions_complete,
                            judgment.judgment_kind.value,
                            judgment.target_time_kind.value,
                            judgment.target_at,
                            judgment.target_from,
                            judgment.target_to,
                            judgment.target_precision.value,
                            judgment.target_text,
                            judgment.value_kind.value,
                            judgment.value_numeric,
                            judgment.value_low,
                            judgment.value_high,
                            judgment.value_text,
                            judgment.value_boolean,
                            judgment.value_date,
                            judgment.value_entity_id,
                            self.jsonb(judgment.value_json) if judgment.value_json is not None else None,
                            judgment.direction.value if judgment.direction is not None else None,
                            judgment.unit_code,
                            judgment.expressed_probability,
                            judgment.summary,
                            judgment.source_published_at,
                            judgment.first_known_at,
                            judgment.extraction_run_id,
                            judgment.source_connector_id,
                            judgment.extractor_name,
                            judgment.extractor_version,
                            judgment.extraction_confidence,
                            self.jsonb(metadata),
                        ),
                    )

                for link in judgment.evidence:
                    await connection.execute(
                        """
                        INSERT INTO research.judgment_evidence (
                            judgment_id, evidence_fragment_id, evidence_role
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            judgment.id,
                            link.evidence_fragment_id,
                            link.evidence_role.value,
                        ),
                    )

    async def append_rationales(self, rationales: Sequence[JudgmentRationale]) -> None:
        async with self.connection() as connection:
            for rationale in rationales:
                existing_cursor = await connection.execute(
                    """
                    SELECT judgment_id, rationale_kind, summary,
                           linked_fact_assertion_id, linked_judgment_id,
                           evidence_fragment_id, ordinal
                    FROM research.judgment_rationales
                    WHERE id = %s
                    """,
                    (rationale.id,),
                )
                existing = await existing_cursor.fetchone()
                expected = {
                    "judgment_id": rationale.judgment_id,
                    "rationale_kind": rationale.rationale_kind.value,
                    "summary": rationale.summary,
                    "linked_fact_assertion_id": rationale.linked_fact_assertion_id,
                    "linked_judgment_id": rationale.linked_judgment_id,
                    "evidence_fragment_id": rationale.evidence_fragment_id,
                    "ordinal": rationale.ordinal,
                }
                if existing is not None:
                    if any(existing[key] != value for key, value in expected.items()):
                        raise ValueError("judgment rationale id already maps to different content")
                    continue
                await connection.execute(
                    """
                    INSERT INTO research.judgment_rationales (
                        id, judgment_id, rationale_kind, summary,
                        linked_fact_assertion_id, linked_judgment_id,
                        evidence_fragment_id, ordinal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rationale.id,
                        rationale.judgment_id,
                        rationale.rationale_kind.value,
                        rationale.summary,
                        rationale.linked_fact_assertion_id,
                        rationale.linked_judgment_id,
                        rationale.evidence_fragment_id,
                        rationale.ordinal,
                    ),
                )

    async def append_relations(self, relations: Sequence[JudgmentRelation]) -> None:
        async with self.connection() as connection:
            for relation in relations:
                existing_cursor = await connection.execute(
                    """
                    SELECT reason_summary
                    FROM research.judgment_relations
                    WHERE from_judgment_id = %s
                      AND to_judgment_id = %s
                      AND relation_type = %s
                    """,
                    (
                        relation.from_judgment_id,
                        relation.to_judgment_id,
                        relation.relation_type.value,
                    ),
                )
                existing = await existing_cursor.fetchone()
                if existing is not None:
                    if existing["reason_summary"] != relation.reason_summary:
                        raise ValueError("judgment relation key already maps to different content")
                    continue
                await connection.execute(
                    """
                    INSERT INTO research.judgment_relations (
                        from_judgment_id, to_judgment_id, relation_type, reason_summary
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (
                        relation.from_judgment_id,
                        relation.to_judgment_id,
                        relation.relation_type.value,
                        relation.reason_summary,
                    ),
                )
