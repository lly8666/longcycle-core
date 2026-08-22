from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:160]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


path = "scripts/smoke_postgres_epistemic.py"

# Keep the existing Reality source byte-for-byte semantically unchanged. The failed
# first gate demonstrated that adding revision language to the outcome document
# rightfully trips FactAssertion immutable-content protection.
replace_once(
    path,
    '''            text=(
                "Management revised first product guidance to July 2022 because qualification "
                "took longer. The production line achieved first product in July 2022."
            ),
''',
    '''            text="The production line achieved first product in July 2022.",
''',
)

# Model the revised guidance as its own source/document/evidence vintage rather than
# mutating evidence already grounding canonical Reality.
replace_once(
    path,
    '''        await research.save_evidence((aug_context_evidence,))

        may_run_id = stable_uuid_exact("epistemic-smoke", "may-extraction")
''',
    '''        await research.save_evidence((aug_context_evidence,))

        revision_document, revision_evidence = await _save_document_with_evidence(
            research,
            source_id=source.id,
            external_id="epistemic-guidance-revision-aug-2022",
            url="https://epistemic-smoke.longcycle.invalid/revision.txt",
            known_at=AUG_KNOWN,
            text=(
                "Management revised first product guidance to July 2022 because "
                "qualification took longer than originally expected."
            ),
        )
        revision_run_id = stable_uuid_exact(
            "epistemic-smoke", "aug-guidance-revision-extraction"
        )
        await research.save_extraction(
            ExtractionEnvelope(
                run_id=revision_run_id,
                document_id=revision_document.id,
                extractor_name="epistemic-smoke",
                extractor_version="1.0.0",
                schema_version="epistemic-smoke/v1",
                evidence=(revision_evidence,),
                candidates=(),
            )
        )

        may_run_id = stable_uuid_exact("epistemic-smoke", "may-extraction")
''',
)

replace_once(
    path,
    '''            "extraction_run_id": aug_run_id,
            "evidence": (
''',
    '''            "extraction_run_id": revision_run_id,
            "evidence": (
''',
)
replace_once(
    path,
    '''                    evidence_fragment_id=aug_evidence.id,
                    evidence_role=JudgmentEvidenceRole.STATEMENT,
''',
    '''                    evidence_fragment_id=revision_evidence.id,
                    evidence_role=JudgmentEvidenceRole.STATEMENT,
''',
)
replace_once(
    path,
    '''        evidence_fragment_id=aug_evidence.id,
    )
    relation = JudgmentRelation(
''',
    '''        evidence_fragment_id=revision_evidence.id,
    )
    relation = JudgmentRelation(
''',
)

print("JUDGMENT_CONTEXT_REPLAY_SMOKE_FIX_APPLIED")
