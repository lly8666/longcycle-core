from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import (
    JudgmentMemoryRecord,
    JudgmentRationaleMemoryRecord,
    JudgmentRelationMemoryRecord,
    PointInTimeMemorySnapshot,
    TemporalExtent,
)


_LAYER_ORDER = {"judgment": 0, "reality": 1, "outcome": 2}


def _extent_payload(extent: TemporalExtent | None) -> dict[str, Any] | None:
    if extent is None:
        return None
    return extent.model_dump(mode="json")


def _value_payload(*, kind: str, text: str | None, payload: str | None) -> dict[str, Any]:
    return {"kind": kind, "text": text, "payload": payload}


def _judgment_context(
    judgment: JudgmentMemoryRecord,
    rationales: tuple[JudgmentRationaleMemoryRecord, ...],
    relations: tuple[JudgmentRelationMemoryRecord, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    visible_rationales = [
        {
            "rationale_id": str(item.rationale_id),
            "kind": item.rationale_kind.value,
            "summary": item.summary,
            "linked_fact_assertion_id": (
                str(item.linked_fact_assertion_id) if item.linked_fact_assertion_id else None
            ),
            "linked_judgment_id": str(item.linked_judgment_id) if item.linked_judgment_id else None,
            "evidence_fragment_id": (
                str(item.evidence_fragment_id) if item.evidence_fragment_id else None
            ),
            "known_at": item.known_at.isoformat(),
        }
        for item in rationales
        if item.judgment_id == judgment.judgment_id
    ]
    visible_relations = [
        {
            "from_judgment_id": str(item.from_judgment_id),
            "to_judgment_id": str(item.to_judgment_id),
            "relation_type": item.relation_type.value,
            "reason_summary": item.reason_summary,
            "known_at": item.known_at.isoformat(),
        }
        for item in relations
        if item.from_judgment_id == judgment.judgment_id
    ]
    return visible_rationales, visible_relations


def build_researcher_trajectory_view(snapshot: PointInTimeMemorySnapshot) -> dict[str, Any]:
    """Render one no-lookahead snapshot as a researcher-readable cognition timeline.

    This is a deterministic read model only. It does not infer causality, rewrite Judgment from
    Outcome, change temporal precision, or create new Evidence/Fact/Judgment/Outcome records.
    Entries are ordered by when they became knowable; each entry preserves its separate historical
    time (Reality valid time, Judgment target time, or Outcome occurrence time).
    """

    judgments = {item.judgment_id: item for item in snapshot.judgments}
    reality = {item.canonical_fact_version_id: item for item in snapshot.reality}
    entries: list[dict[str, Any]] = []
    subject_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"reality": 0, "judgment": 0, "outcome": 0}
    )

    for item in snapshot.judgments:
        rationales, relations = _judgment_context(
            item,
            snapshot.judgment_rationales,
            snapshot.judgment_relations,
        )
        entry = {
            "entry_id": f"judgment:{item.judgment_id}",
            "layer": "judgment",
            "subject": item.subject.model_dump(mode="json"),
            "known_at": item.known_at.isoformat(),
            "historical_time_role": "target_time",
            "historical_time": _extent_payload(item.target_time),
            "headline": item.summary,
            "speaker_name_text": item.speaker_name_text,
            "topic_code": item.topic_code,
            "judgment_kind": item.judgment_kind,
            "value": _value_payload(
                kind=item.value_kind,
                text=item.value_text,
                payload=item.value_payload,
            ),
            "rationales": rationales,
            "relations": relations,
            "evidence_fragment_ids": [str(value) for value in item.evidence_fragment_ids],
        }
        entries.append(entry)
        subject_counts[item.subject.key]["judgment"] += 1

    for item in snapshot.reality:
        display_value = item.value_text or item.value_payload or "[structured value]"
        entry = {
            "entry_id": f"reality:{item.canonical_fact_version_id}",
            "layer": "reality",
            "subject": item.subject.model_dump(mode="json"),
            "known_at": item.known_at.isoformat(),
            "historical_time_role": "valid_time",
            "historical_time": _extent_payload(item.valid_time),
            "observed_time": _extent_payload(item.observed_time),
            "headline": f"{item.predicate_code}: {display_value}",
            "predicate_code": item.predicate_code,
            "value": _value_payload(
                kind=item.value_kind,
                text=item.value_text,
                payload=item.value_payload,
            ),
            "unit_code": item.unit_code,
            "confidence": item.confidence,
            "publication_status": item.publication_status,
            "evidence_fragment_ids": [str(value) for value in item.evidence_fragment_ids],
        }
        entries.append(entry)
        subject_counts[item.subject.key]["reality"] += 1

    for item in snapshot.outcomes:
        original = judgments[item.judgment_id]
        linked_reality = (
            reality.get(item.canonical_fact_version_id)
            if item.canonical_fact_version_id is not None
            else None
        )
        headline = f"{item.evaluation_status}: {original.summary}"
        entry = {
            "entry_id": f"outcome:{item.evaluation_id}",
            "layer": "outcome",
            "subject": item.subject.model_dump(mode="json"),
            "known_at": item.known_at.isoformat(),
            "historical_time_role": "occurrence_time",
            "historical_time": _extent_payload(item.occurrence_time),
            "headline": headline,
            "evaluation_status": item.evaluation_status,
            "semantic_relation": item.semantic_relation.value,
            "timing_relation": item.timing_relation,
            "timing_delta_value": (
                str(item.timing_delta_value) if item.timing_delta_value is not None else None
            ),
            "timing_delta_unit": item.timing_delta_unit,
            "explanation": item.explanation,
            "links": {
                "judgment_id": str(item.judgment_id),
                "judgment_entry_id": f"judgment:{item.judgment_id}",
                "canonical_fact_version_id": (
                    str(item.canonical_fact_version_id)
                    if item.canonical_fact_version_id is not None
                    else None
                ),
                "reality_entry_id": (
                    f"reality:{item.canonical_fact_version_id}"
                    if linked_reality is not None
                    else None
                ),
            },
            "outcome_evidence_fragment_id": (
                str(item.outcome_evidence_fragment_id)
                if item.outcome_evidence_fragment_id is not None
                else None
            ),
        }
        entries.append(entry)
        subject_counts[item.subject.key]["outcome"] += 1

    entries.sort(
        key=lambda entry: (
            datetime.fromisoformat(str(entry["known_at"])),
            _LAYER_ORDER[str(entry["layer"])],
            str(entry["entry_id"]),
        )
    )

    subject_summary = [
        {
            "subject_key": key,
            "counts": subject_counts[key],
        }
        for key in sorted(subject_counts)
    ]
    return {
        "schema_version": "longcycle-researcher-trajectory-view/v1",
        "knowledge_cutoff": snapshot.knowledge_cutoff.isoformat(),
        "subjects": subject_summary,
        "entries": entries,
        "counts": {
            "reality": len(snapshot.reality),
            "judgments": len(snapshot.judgments),
            "outcomes": len(snapshot.outcomes),
            "judgment_rationales": len(snapshot.judgment_rationales),
            "judgment_relations": len(snapshot.judgment_relations),
        },
        "boundary": {
            "ordered_by_knowledge_time": True,
            "historical_time_kept_separate_from_known_at": True,
            "source_temporal_precision_preserved": True,
            "evidence_references_preserved": True,
            "judgment_not_rewritten_by_outcome": True,
            "no_new_epistemic_records_created": True,
        },
    }
