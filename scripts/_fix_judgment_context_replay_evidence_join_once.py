from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:160]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


path = "src/longcycle/adapters/storage/postgres_epistemic.py"

# Evidence fragments point to immutable document versions; the source's conservative
# known-time lives on the first fetch for that version, not on a source_documents table.
replace_once(
    path,
    '''            LEFT JOIN evidence.evidence_fragments rationale_evidence
              ON rationale_evidence.id = rationale.evidence_fragment_id
            LEFT JOIN evidence.source_documents rationale_document
              ON rationale_document.id = rationale_evidence.document_id
''',
    '''            LEFT JOIN evidence.evidence_fragments rationale_evidence
              ON rationale_evidence.id = rationale.evidence_fragment_id
            LEFT JOIN evidence.document_versions rationale_version
              ON rationale_version.id = rationale_evidence.document_version_id
            LEFT JOIN evidence.document_fetches rationale_fetch
              ON rationale_fetch.id = rationale_version.first_fetch_id
''',
)

text = Path(path).read_text(encoding="utf-8")
count = text.count("rationale_document.first_known_at")
if count != 2:
    raise SystemExit(
        f"{path}: expected two rationale_document known-time references, found {count}"
    )
text = text.replace(
    "rationale_document.first_known_at",
    "rationale_fetch.first_known_at",
)
linked_fact_count = text.count("linked_fact.known_at")
if linked_fact_count != 2:
    raise SystemExit(
        f"{path}: expected two linked_fact known-time references, found {linked_fact_count}"
    )
text = text.replace("linked_fact.known_at", "linked_fact.first_known_at")
Path(path).write_text(text, encoding="utf-8")

print("JUDGMENT_CONTEXT_REPLAY_EVIDENCE_JOIN_FIX_APPLIED")
