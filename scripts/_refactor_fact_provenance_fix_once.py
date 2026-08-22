from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "src/longcycle/application/normalization.py",
    """            str(assertion.document_id),
            str(assertion.evidence_fragment_id),
            assertion.scope_key,
""",
    """            str(assertion.document_id),
            canonical_json(
                [item.model_dump(mode="json") for item in assertion.evidence]
            ),
            assertion.scope_key,
""",
)

replace_once(
    "src/longcycle/adapters/models.py",
    "from longcycle.domain.enums import EntityType, ValidTimeKind\n",
    "from longcycle.domain.enums import EntityType, FactEvidenceRole, ValidTimeKind\n",
)
replace_once(
    "src/longcycle/adapters/models.py",
    "    FactDimensions,\n    QualityComponents,\n",
    "    FactDimensions,\n    FactEvidenceRef,\n    QualityComponents,\n",
)
replace_once(
    "src/longcycle/adapters/models.py",
    "                    evidence_fragment_id=fragment.id,\n",
    """                    evidence=(
                        FactEvidenceRef(
                            evidence_fragment_id=fragment.id,
                            evidence_role=FactEvidenceRole.SUPPORTING,
                        ),
                    ),
""",
)

replace_once(
    "src/longcycle/application/pipeline.py",
    """            if candidate.evidence_fragment_id not in evidence_ids:
                raise ValueError("assertion has no evidence fragment in this extraction")
""",
    """            candidate_evidence_ids = {
                item.evidence_fragment_id for item in candidate.evidence
            }
            if not candidate_evidence_ids.issubset(evidence_ids):
                raise ValueError("assertion has evidence outside this extraction")
""",
)

print("FACT_PROVENANCE_CALLERS_PATCHED")
