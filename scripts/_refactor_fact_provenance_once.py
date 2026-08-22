from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# Domain: FactAssertion owns typed, multi-fragment provenance.  Legacy single-ID
# constructor input is translated at the boundary but is not part of the model shape.
replace_once(
    "src/longcycle/domain/models.py",
    "    EntityType,\n    FactStatus,\n",
    "    EntityType,\n    FactEvidenceRole,\n    FactStatus,\n",
)
replace_once(
    "src/longcycle/domain/models.py",
    "\n\nclass FactAssertion(DomainModel):\n",
    """

class FactEvidenceRef(DomainModel):
    evidence_fragment_id: UUID
    evidence_role: FactEvidenceRole = FactEvidenceRole.SUPPORTING


class FactAssertion(DomainModel):
""",
)
replace_once(
    "src/longcycle/domain/models.py",
    "    document_id: UUID\n    evidence_fragment_id: UUID\n    extraction_run_id: UUID\n",
    "    document_id: UUID\n    evidence: tuple[FactEvidenceRef, ...]\n    extraction_run_id: UUID\n",
)
replace_once(
    "src/longcycle/domain/models.py",
    """        payload = dict(value)
        metadata = dict(payload.get("metadata") or {})
""",
    """        payload = dict(value)
        legacy_evidence_id = payload.pop("evidence_fragment_id", None)
        if legacy_evidence_id is not None:
            if payload.get("evidence"):
                raise ValueError(
                    "FactAssertion cannot supply both evidence and legacy evidence_fragment_id"
                )
            payload["evidence"] = (
                {
                    "evidence_fragment_id": legacy_evidence_id,
                    "evidence_role": FactEvidenceRole.SUPPORTING.value,
                },
            )
        metadata = dict(payload.get("metadata") or {})
""",
)
replace_once(
    "src/longcycle/domain/models.py",
    """        if self.valid_time_kind == ValidTimeKind.PERIOD and (
            self.valid_time.start is None and self.valid_time.end is None
        ):
            raise ValueError("period fact valid time requires a start and/or end bound")
        return self

    @property
    def scope_key(self) -> str:
""",
    """        if self.valid_time_kind == ValidTimeKind.PERIOD and (
            self.valid_time.start is None and self.valid_time.end is None
        ):
            raise ValueError("period fact valid time requires a start and/or end bound")
        if not self.evidence:
            raise ValueError("FactAssertion requires at least one EvidenceFragment reference")
        evidence_ids = [item.evidence_fragment_id for item in self.evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("FactAssertion evidence fragments must be unique")
        if not any(item.evidence_role == FactEvidenceRole.SUPPORTING for item in self.evidence):
            raise ValueError("FactAssertion requires at least one supporting evidence fragment")
        return self

    @property
    def immutable_fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude={"status"})
        return hashlib.sha256(canonical_json(payload).encode()).hexdigest()

    @property
    def scope_key(self) -> str:
""",
)

# In-memory repository must enforce immutable identity just like durable adapters.
replace_once(
    "src/longcycle/adapters/storage/memory.py",
    """            for assertion in assertions:
                if assertion.id in self.assertions:
                    continue
                self.assertions[assertion.id] = assertion
""",
    """            for assertion in assertions:
                if assertion.id in self.assertions:
                    existing = self.assertions[assertion.id]
                    if existing.immutable_fingerprint != assertion.immutable_fingerprint:
                        raise ValueError(
                            "FactAssertion id already maps to different immutable content"
                        )
                    continue
                self.assertions[assertion.id] = assertion
""",
)

# PostgreSQL append: validate all evidence belongs to the extraction document, write
# every role, and reject same-ID/different-content reappend.
replace_once(
    "src/longcycle/adapters/storage/postgres.py",
    "    FactAssertion,\n    FactDimensions,\n",
    "    FactAssertion,\n    FactDimensions,\n    FactEvidenceRef,\n",
)
replace_once(
    "src/longcycle/adapters/storage/postgres.py",
    """                await connection.execute(
                    \"\"\"
                    INSERT INTO research.assertion_evidence (assertion_id, evidence_fragment_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                    \"\"\",
                    (assertion.id, assertion.evidence_fragment_id),
                )
""",
    """                evidence_ids = [item.evidence_fragment_id for item in assertion.evidence]
                evidence_cursor = await connection.execute(
                    \"\"\"
                    SELECT fragment.id
                    FROM evidence.evidence_fragments fragment
                    JOIN evidence.extraction_runs run
                      ON run.id = %s
                     AND run.document_version_id = fragment.document_version_id
                    WHERE fragment.id = ANY(%s::uuid[])
                    \"\"\",
                    (assertion.extraction_run_id, evidence_ids),
                )
                related_evidence_ids = {
                    row[\"id\"] for row in await evidence_cursor.fetchall()
                }
                if related_evidence_ids != set(evidence_ids):
                    raise ValueError(
                        "FactAssertion evidence must exist on its extraction document"
                    )
                for evidence_ref in assertion.evidence:
                    await connection.execute(
                        \"\"\"
                        INSERT INTO research.assertion_evidence (
                            assertion_id, evidence_fragment_id, evidence_role
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT (assertion_id, evidence_fragment_id) DO NOTHING
                        \"\"\",
                        (
                            assertion.id,
                            evidence_ref.evidence_fragment_id,
                            evidence_ref.evidence_role.value,
                        ),
                    )
                persisted_assertion = await self._assertion_by_id_on_connection(
                    connection,
                    assertion.id,
                )
                if persisted_assertion is None:
                    raise RuntimeError("persisted FactAssertion could not be reloaded")
                if persisted_assertion.immutable_fingerprint != assertion.immutable_fingerprint:
                    raise ValueError(
                        "FactAssertion id already maps to different immutable content"
                    )
""",
)

old_comparison = """            SELECT assertion.*, link.evidence_fragment_id,
                   run.extractor_name, run.extractor_version, run.document_version_id,
                   entity.entity_type AS subject_entity_type,
                   dimensions.canonical_payload
            FROM research.fact_assertions_with_status assertion
            JOIN research.assertion_evidence link ON link.assertion_id = assertion.id
            JOIN evidence.extraction_runs run ON run.id = assertion.extraction_run_id
"""
new_comparison = """            SELECT assertion.*, evidence.evidence_refs,
                   run.extractor_name, run.extractor_version, run.document_version_id,
                   entity.entity_type AS subject_entity_type,
                   dimensions.canonical_payload
            FROM research.fact_assertions_with_status assertion
            JOIN LATERAL (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'evidence_fragment_id', link.evidence_fragment_id,
                        'evidence_role', link.evidence_role
                    ) ORDER BY link.evidence_fragment_id
                ) AS evidence_refs
                FROM research.assertion_evidence link
                WHERE link.assertion_id = assertion.id
            ) evidence ON true
            JOIN evidence.extraction_runs run ON run.id = assertion.extraction_run_id
"""
# The same JOIN shape appears in comparison and by-id queries.
target = Path("src/longcycle/adapters/storage/postgres.py")
text = target.read_text(encoding="utf-8")
if text.count(old_comparison) != 2:
    raise SystemExit(
        f"postgres evidence query anchor expected twice, found {text.count(old_comparison)}"
    )
text = text.replace(old_comparison, new_comparison)
text = text.replace(
    """            WHERE assertion.id = %s
            ORDER BY link.evidence_fragment_id
            LIMIT 1
""",
    """            WHERE assertion.id = %s
""",
    1,
)
target.write_text(text, encoding="utf-8")

replace_once(
    "src/longcycle/adapters/storage/postgres.py",
    "            evidence_fragment_id=row[\"evidence_fragment_id\"],\n",
    """            evidence=tuple(
                FactEvidenceRef.model_validate(item)
                for item in (row.get("evidence_refs") or [])
            ),
""",
)

# Reality projection adopts the new canonical constructor immediately; the legacy
# input bridge remains only for older callers during repository migration.
replace_once(
    "src/longcycle/application/reality_projection.py",
    "    FactDimensions,\n    QualityComponents,\n",
    "    FactDimensions,\n    FactEvidenceRef,\n    QualityComponents,\n",
)
replace_once(
    "src/longcycle/application/reality_projection.py",
    "from longcycle.domain.enums import (\n    EntityType,\n",
    "from longcycle.domain.enums import (\n    EntityType,\n    FactEvidenceRole,\n",
)
replace_once(
    "src/longcycle/application/reality_projection.py",
    "                evidence_fragment_id=cited.evidence_fragment_id,\n",
    """                evidence=(
                    FactEvidenceRef(
                        evidence_fragment_id=cited.evidence_fragment_id,
                        evidence_role=FactEvidenceRole.SUPPORTING,
                    ),
                ),
""",
)

print("FACT_PROVENANCE_REFACTOR_PATCHED")
