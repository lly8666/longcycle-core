from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

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

    judgments = {judgment.judgment_id: judgment for judgment in snapshot.judgments}
    reality = {
        reality_item.canonical_fact_version_id: reality_item
        for reality_item in snapshot.reality
    }
    entries: list[dict[str, Any]] = []
    subject_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"reality": 0, "judgment": 0, "outcome": 0}
    )

    for judgment in snapshot.judgments:
        rationales, relations = _judgment_context(
            judgment,
            snapshot.judgment_rationales,
            snapshot.judgment_relations,
        )
        judgment_entry: dict[str, Any] = {
            "entry_id": f"judgment:{judgment.judgment_id}",
            "layer": "judgment",
            "subject": judgment.subject.model_dump(mode="json"),
            "known_at": judgment.known_at.isoformat(),
            "historical_time_role": "target_time",
            "historical_time": _extent_payload(judgment.target_time),
            "headline": judgment.summary,
            "speaker_name_text": judgment.speaker_name_text,
            "topic_code": judgment.topic_code,
            "judgment_kind": judgment.judgment_kind,
            "value": _value_payload(
                kind=judgment.value_kind,
                text=judgment.value_text,
                payload=judgment.value_payload,
            ),
            "rationales": rationales,
            "relations": relations,
            "evidence_fragment_ids": [
                str(value) for value in judgment.evidence_fragment_ids
            ],
        }
        entries.append(judgment_entry)
        subject_counts[judgment.subject.key]["judgment"] += 1

    for reality_item in snapshot.reality:
        display_value = reality_item.value_text or reality_item.value_payload or "[structured value]"
        reality_entry: dict[str, Any] = {
            "entry_id": f"reality:{reality_item.canonical_fact_version_id}",
            "layer": "reality",
            "subject": reality_item.subject.model_dump(mode="json"),
            "known_at": reality_item.known_at.isoformat(),
            "historical_time_role": "valid_time",
            "historical_time": _extent_payload(reality_item.valid_time),
            "observed_time": _extent_payload(reality_item.observed_time),
            "headline": f"{reality_item.predicate_code}: {display_value}",
            "predicate_code": reality_item.predicate_code,
            "value": _value_payload(
                kind=reality_item.value_kind,
                text=reality_item.value_text,
                payload=reality_item.value_payload,
            ),
            "unit_code": reality_item.unit_code,
            "confidence": reality_item.confidence,
            "publication_status": reality_item.publication_status,
            "evidence_fragment_ids": [
                str(value) for value in reality_item.evidence_fragment_ids
            ],
        }
        entries.append(reality_entry)
        subject_counts[reality_item.subject.key]["reality"] += 1

    for outcome in snapshot.outcomes:
        original = judgments[outcome.judgment_id]
        linked_reality = (
            reality.get(outcome.canonical_fact_version_id)
            if outcome.canonical_fact_version_id is not None
            else None
        )
        headline = f"{outcome.evaluation_status}: {original.summary}"
        outcome_entry: dict[str, Any] = {
            "entry_id": f"outcome:{outcome.evaluation_id}",
            "layer": "outcome",
            "subject": outcome.subject.model_dump(mode="json"),
            "known_at": outcome.known_at.isoformat(),
            "historical_time_role": "occurrence_time",
            "historical_time": _extent_payload(outcome.occurrence_time),
            "headline": headline,
            "evaluation_status": outcome.evaluation_status,
            "semantic_relation": outcome.semantic_relation.value,
            "timing_relation": outcome.timing_relation,
            "timing_delta_value": (
                str(outcome.timing_delta_value) if outcome.timing_delta_value is not None else None
            ),
            "timing_delta_unit": outcome.timing_delta_unit,
            "explanation": outcome.explanation,
            "links": {
                "judgment_id": str(outcome.judgment_id),
                "judgment_entry_id": f"judgment:{outcome.judgment_id}",
                "canonical_fact_version_id": (
                    str(outcome.canonical_fact_version_id)
                    if outcome.canonical_fact_version_id is not None
                    else None
                ),
                "reality_entry_id": (
                    f"reality:{outcome.canonical_fact_version_id}"
                    if linked_reality is not None
                    else None
                ),
            },
            "outcome_evidence_fragment_id": (
                str(outcome.outcome_evidence_fragment_id)
                if outcome.outcome_evidence_fragment_id is not None
                else None
            ),
        }
        entries.append(outcome_entry)
        subject_counts[outcome.subject.key]["outcome"] += 1

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
