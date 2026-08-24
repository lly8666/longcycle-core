from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from longcycle.application.researcher_interpretation import (
    researcher_outcome_interpretation,
    researcher_time_hint,
)
from longcycle.domain.epistemic import (
    JudgmentMemoryRecord,
    JudgmentRationaleMemoryRecord,
    JudgmentRelationMemoryRecord,
    OutcomeMemoryRecord,
    PointInTimeMemorySnapshot,
    TemporalExtent,
)


_LAYER_ORDER = {"judgment": 0, "reality": 1, "outcome": 2}
_COUNT_KEY = {"judgment": "judgments", "reality": "reality", "outcome": "outcomes"}


def _extent_payload(extent: TemporalExtent | None) -> dict[str, Any] | None:
    if extent is None:
        return None
    return extent.model_dump(mode="json")


def _value_payload(*, kind: str, text: str | None, payload: str | None) -> dict[str, Any]:
    return {"kind": kind, "text": text, "payload": payload}


def _relation_payload(item: JudgmentRelationMemoryRecord) -> dict[str, Any]:
    return {
        "from_judgment_id": str(item.from_judgment_id),
        "to_judgment_id": str(item.to_judgment_id),
        "relation_type": item.relation_type.value,
        "reason_summary": item.reason_summary,
        "known_at": item.known_at.isoformat(),
    }


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
        _relation_payload(item)
        for item in relations
        if item.from_judgment_id == judgment.judgment_id
    ]
    return visible_rationales, visible_relations


def _count_phrase(counts: dict[str, int]) -> str:
    return ", ".join(
        (
            f"{counts['judgments']} Judgment",
            f"{counts['reality']} Reality",
            f"{counts['outcomes']} Outcome",
        )
    )


def _knowledge_progression(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[str(entry["known_at"])].append(entry)

    running = {"reality": 0, "judgments": 0, "outcomes": 0}
    progression: list[dict[str, Any]] = []
    for known_at in sorted(grouped, key=datetime.fromisoformat):
        introduced = grouped[known_at]
        introduced_counts = {"reality": 0, "judgments": 0, "outcomes": 0}
        for entry in introduced:
            key = _COUNT_KEY[str(entry["layer"])]
            introduced_counts[key] += 1
            running[key] += 1
        progression.append(
            {
                "known_at": known_at,
                "introduced": [
                    {
                        "entry_id": str(entry["entry_id"]),
                        "layer": str(entry["layer"]),
                        "headline": str(entry["headline"]),
                    }
                    for entry in introduced
                ],
                "introduced_counts": introduced_counts,
                "counts_after": dict(running),
                "researcher_summary": (
                    f"At this knowledge point the archive added {_count_phrase(introduced_counts)}. "
                    f"The visible snapshot then contained {_count_phrase(running)}."
                ),
            }
        )
    return progression


def _outcome_story_payload(
    outcome: OutcomeMemoryRecord,
    *,
    reality_by_id: dict[Any, Any],
) -> dict[str, Any]:
    linked_reality = (
        reality_by_id.get(outcome.canonical_fact_version_id)
        if outcome.canonical_fact_version_id is not None
        else None
    )
    return {
        "evaluation_id": str(outcome.evaluation_id),
        "known_at": outcome.known_at.isoformat(),
        "evaluation_status": outcome.evaluation_status,
        "semantic_relation": outcome.semantic_relation.value,
        "timing_relation": outcome.timing_relation,
        "occurrence_time": _extent_payload(outcome.occurrence_time),
        "researcher_time_hint": researcher_time_hint(outcome.occurrence_time),
        "researcher_interpretation": researcher_outcome_interpretation(outcome),
        "explanation": outcome.explanation,
        "linked_reality": (
            {
                "canonical_fact_version_id": str(linked_reality.canonical_fact_version_id),
                "known_at": linked_reality.known_at.isoformat(),
                "predicate_code": linked_reality.predicate_code,
                "value": _value_payload(
                    kind=linked_reality.value_kind,
                    text=linked_reality.value_text,
                    payload=linked_reality.value_payload,
                ),
                "valid_time": _extent_payload(linked_reality.valid_time),
                "researcher_time_hint": researcher_time_hint(
                    linked_reality.valid_time,
                    observed_time=linked_reality.observed_time,
                ),
            }
            if linked_reality is not None
            else None
        ),
    }


def _judgment_storylines(
    snapshot: PointInTimeMemorySnapshot,
    *,
    reality_by_id: dict[Any, Any],
) -> list[dict[str, Any]]:
    outcomes_by_judgment: dict[Any, list[OutcomeMemoryRecord]] = defaultdict(list)
    for outcome in snapshot.outcomes:
        outcomes_by_judgment[outcome.judgment_id].append(outcome)
    for values in outcomes_by_judgment.values():
        values.sort(key=lambda item: (item.known_at, str(item.evaluation_id)))

    result: list[dict[str, Any]] = []
    for judgment in snapshot.judgments:
        rationales, outgoing = _judgment_context(
            judgment,
            snapshot.judgment_rationales,
            snapshot.judgment_relations,
        )
        incoming = [
            _relation_payload(item)
            for item in snapshot.judgment_relations
            if item.to_judgment_id == judgment.judgment_id
        ]
        outcomes = outcomes_by_judgment.get(judgment.judgment_id, [])
        later_outcomes = [
            _outcome_story_payload(item, reality_by_id=reality_by_id)
            for item in outcomes
        ]
        speaker = judgment.speaker_name_text or "Source-grounded speaker"
        if later_outcomes:
            latest = later_outcomes[-1]
            interpretation = latest["researcher_interpretation"]
            if interpretation["interpretation_kind"] == "related_milestone_signal":
                outcome_clause = (
                    "a related milestone is visible, but the original target remains "
                    "not directly resolved"
                )
            else:
                outcome_clause = (
                    f"the latest evaluation is {latest['evaluation_status']} with semantic relation "
                    f"{latest['semantic_relation']}"
                )
            researcher_summary = (
                f"At {judgment.known_at.isoformat()}, {speaker} recorded: {judgment.summary} "
                f"By the {snapshot.knowledge_cutoff.isoformat()} cutoff, "
                f"{len(later_outcomes)} Outcome evaluation(s) were visible; {outcome_clause}. "
                "The later record does not rewrite the original Judgment."
            )
            status = "outcome_visible"
        else:
            researcher_summary = (
                f"At {judgment.known_at.isoformat()}, {speaker} recorded: {judgment.summary} "
                f"No Outcome evaluation for this Judgment is visible by the "
                f"{snapshot.knowledge_cutoff.isoformat()} cutoff."
            )
            status = "judgment_visible_no_outcome"

        result.append(
            {
                "storyline_id": f"judgment:{judgment.judgment_id}",
                "subject": judgment.subject.model_dump(mode="json"),
                "topic_code": judgment.topic_code,
                "status_as_of_cutoff": status,
                "at_the_time": {
                    "judgment_id": str(judgment.judgment_id),
                    "known_at": judgment.known_at.isoformat(),
                    "speaker_name_text": judgment.speaker_name_text,
                    "judgment_kind": judgment.judgment_kind,
                    "statement": judgment.summary,
                    "target_time": _extent_payload(judgment.target_time),
                    "researcher_time_hint": researcher_time_hint(judgment.target_time),
                    "value": _value_payload(
                        kind=judgment.value_kind,
                        text=judgment.value_text,
                        payload=judgment.value_payload,
                    ),
                    "rationales": rationales,
                    "evidence_fragment_ids": [
                        str(value) for value in judgment.evidence_fragment_ids
                    ],
                },
                "revision_context": {
                    "outgoing_relations": outgoing,
                    "incoming_relations": incoming,
                },
                "later_outcomes": later_outcomes,
                "researcher_summary": researcher_summary,
            }
        )
    return result


def build_researcher_trajectory_view(snapshot: PointInTimeMemorySnapshot) -> dict[str, Any]:
    """Render one no-lookahead snapshot as a researcher-readable cognition timeline.

    Canonical Reality/Judgment/Outcome time and evaluation semantics are never rewritten.
    The presentation layer may add explicitly labelled deterministic researcher hints, such
    as a source-supported time window, an as-of observation with unknown onset, or a related
    milestone signal that does not satisfy the original target. These hints are read-only and
    cannot create new epistemic records or silently become canonical truth.
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
            "researcher_time_hint": researcher_time_hint(judgment.target_time),
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
            "researcher_time_hint": researcher_time_hint(
                reality_item.valid_time,
                observed_time=reality_item.observed_time,
            ),
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
            "researcher_time_hint": researcher_time_hint(outcome.occurrence_time),
            "headline": headline,
            "evaluation_status": outcome.evaluation_status,
            "semantic_relation": outcome.semantic_relation.value,
            "researcher_interpretation": researcher_outcome_interpretation(outcome),
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
    linked_reality_ids = {
        outcome.canonical_fact_version_id
        for outcome in snapshot.outcomes
        if outcome.canonical_fact_version_id is not None
    }
    return {
        "schema_version": "longcycle-researcher-trajectory-view/v1",
        "knowledge_cutoff": snapshot.knowledge_cutoff.isoformat(),
        "subjects": subject_summary,
        "entries": entries,
        "knowledge_progression": _knowledge_progression(entries),
        "judgment_storylines": _judgment_storylines(snapshot, reality_by_id=reality),
        "unlinked_reality_entry_ids": [
            f"reality:{item.canonical_fact_version_id}"
            for item in snapshot.reality
            if item.canonical_fact_version_id not in linked_reality_ids
        ],
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
            "researcher_time_hints_do_not_mutate_canonical_time": True,
            "evidence_references_preserved": True,
            "judgment_not_rewritten_by_outcome": True,
            "storylines_derive_only_from_filtered_snapshot": True,
            "related_milestones_surface_without_realization_promotion": True,
            "presentation_does_not_promote_interpretation_to_truth": True,
            "no_new_epistemic_records_created": True,
        },
    }
