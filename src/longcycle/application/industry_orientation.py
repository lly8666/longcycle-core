from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef, PointInTimeMemorySnapshot
from longcycle.domain.orientation import (
    IndustryOrientationCatalog,
    IndustrySubjectMembershipRecord,
)
from longcycle.domain.models import require_aware_datetime
from longcycle.ports.epistemic import EpistemicMemoryReader
from longcycle.ports.orientation import IndustryOrientationReader


def _membership_visible(
    membership: IndustrySubjectMembershipRecord,
    *,
    knowledge_cutoff: datetime,
) -> bool:
    if membership.known_at > knowledge_cutoff:
        return False
    cutoff_date = knowledge_cutoff.date()
    if membership.valid_from is not None and cutoff_date < membership.valid_from:
        return False
    if membership.valid_to is not None and cutoff_date >= membership.valid_to:
        return False
    return True


def _visible_memberships(
    catalog: IndustryOrientationCatalog,
    *,
    knowledge_cutoff: datetime,
) -> tuple[IndustrySubjectMembershipRecord, ...]:
    """Choose the latest source-knowable curated version for each entity/role.

    ``system_from`` is only a deterministic tie-break among versions supported by
    evidence that was already knowable by the cutoff. It is not itself a knowledge
    timestamp and therefore never admits a membership across the cutoff.
    """

    selected: dict[tuple[UUID, str], IndustrySubjectMembershipRecord] = {}
    for membership in catalog.memberships:
        if not _membership_visible(membership, knowledge_cutoff=knowledge_cutoff):
            continue
        assert membership.subject.entity_id is not None
        key = (membership.subject.entity_id, membership.role)
        existing = selected.get(key)
        candidate_order = (
            membership.known_at,
            membership.system_from,
            str(membership.membership_id),
        )
        if existing is None:
            selected[key] = membership
            continue
        existing_order = (
            existing.known_at,
            existing.system_from,
            str(existing.membership_id),
        )
        if candidate_order > existing_order:
            selected[key] = membership
    return tuple(
        sorted(
            selected.values(),
            key=lambda item: (
                item.canonical_name.casefold(),
                str(item.subject.entity_id),
                item.role,
            ),
        )
    )


def _memory_counts(snapshot: PointInTimeMemorySnapshot) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"reality": 0, "judgments": 0, "outcomes": 0}
    )
    for item in snapshot.reality:
        counts[item.subject.key]["reality"] += 1
    for item in snapshot.judgments:
        counts[item.subject.key]["judgments"] += 1
    for item in snapshot.outcomes:
        counts[item.subject.key]["outcomes"] += 1
    return counts


def _evidence_by_subject(snapshot: PointInTimeMemorySnapshot) -> dict[str, set[str]]:
    evidence: dict[str, set[str]] = defaultdict(set)
    judgment_subjects = {item.judgment_id: item.subject.key for item in snapshot.judgments}
    for item in snapshot.reality:
        evidence[item.subject.key].update(str(value) for value in item.evidence_fragment_ids)
    for item in snapshot.judgments:
        evidence[item.subject.key].update(str(value) for value in item.evidence_fragment_ids)
    for item in snapshot.judgment_rationales:
        subject_key = judgment_subjects.get(item.judgment_id)
        if subject_key is not None and item.evidence_fragment_id is not None:
            evidence[subject_key].add(str(item.evidence_fragment_id))
    for item in snapshot.outcomes:
        if item.outcome_evidence_fragment_id is not None:
            evidence[item.subject.key].add(str(item.outcome_evidence_fragment_id))
    return evidence


def _judgment_relation_markers(
    snapshot: PointInTimeMemorySnapshot,
) -> dict[str, list[dict[str, Any]]]:
    judgment_subjects = {item.judgment_id: item.subject.key for item in snapshot.judgments}
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in snapshot.judgment_relations:
        payload = {
            "from_judgment_id": str(relation.from_judgment_id),
            "to_judgment_id": str(relation.to_judgment_id),
            "relation_type": relation.relation_type.value,
            "reason_summary": relation.reason_summary,
            "known_at": relation.known_at.isoformat(),
        }
        subject_keys = {
            value
            for value in (
                judgment_subjects.get(relation.from_judgment_id),
                judgment_subjects.get(relation.to_judgment_id),
            )
            if value is not None
        }
        for subject_key in sorted(subject_keys):
            result[subject_key].append(payload)
    return result


async def build_researcher_industry_orientation(
    *,
    catalog_reader: IndustryOrientationReader,
    memory_reader: EpistemicMemoryReader,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
) -> dict[str, Any]:
    """Build one bounded researcher entry view without inventing industry semantics.

    Membership visibility is derived from source-grounded catalog resolutions. Reality,
    Judgment and Outcome visibility remains delegated to the existing CAP-0005
    ``EpistemicMemoryReader.snapshot`` boundary at the exact same knowledge cutoff.
    """

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    catalog = await catalog_reader.industry_catalog(industry_node_id)
    visible_memberships = _visible_memberships(catalog, knowledge_cutoff=checked)

    member_subjects: dict[UUID, MemorySubjectRef] = {}
    memberships_by_entity: dict[UUID, list[IndustrySubjectMembershipRecord]] = defaultdict(list)
    for membership in visible_memberships:
        assert membership.subject.entity_id is not None
        member_subjects[membership.subject.entity_id] = membership.subject
        memberships_by_entity[membership.subject.entity_id].append(membership)

    snapshot_subjects = (
        MemorySubjectRef(industry_node_id=industry_node_id),
        *(
            member_subjects[entity_id]
            for entity_id in sorted(member_subjects, key=str)
        ),
    )
    snapshot = await memory_reader.snapshot(snapshot_subjects, knowledge_cutoff=checked)
    counts = _memory_counts(snapshot)
    evidence = _evidence_by_subject(snapshot)
    relation_markers = _judgment_relation_markers(snapshot)

    subject_rows: list[dict[str, Any]] = []
    for entity_id, entity_memberships in sorted(
        memberships_by_entity.items(),
        key=lambda pair: (pair[1][0].canonical_name.casefold(), str(pair[0])),
    ):
        representative = entity_memberships[0]
        subject_key = representative.subject.key
        subject_evidence = set(evidence.get(subject_key, set()))
        for membership in entity_memberships:
            subject_evidence.update(str(value) for value in membership.evidence_fragment_ids)
        subject_rows.append(
            {
                "subject_id": str(entity_id),
                "canonical_name": representative.canonical_name,
                "entity_type": representative.entity_type,
                "memberships": [
                    {
                        "role": membership.role,
                        "exposure_type": membership.exposure_type,
                        "valid_from": (
                            membership.valid_from.isoformat()
                            if membership.valid_from is not None
                            else None
                        ),
                        "valid_to": (
                            membership.valid_to.isoformat()
                            if membership.valid_to is not None
                            else None
                        ),
                        "known_at": membership.known_at.isoformat(),
                        "confidence": membership.confidence,
                        "resolution_id": str(membership.resolution_id),
                        "evidence_fragment_ids": [
                            str(value) for value in membership.evidence_fragment_ids
                        ],
                    }
                    for membership in entity_memberships
                ],
                "memory_counts": counts.get(
                    subject_key,
                    {"reality": 0, "judgments": 0, "outcomes": 0},
                ),
                "judgment_relation_markers": relation_markers.get(subject_key, []),
                "evidence_fragment_ids": sorted(subject_evidence),
                "trajectory_replay": {"subject_id": str(entity_id)},
            }
        )

    industry_subject = MemorySubjectRef(industry_node_id=industry_node_id)
    return {
        "schema_version": "longcycle-researcher-industry-orientation/v1",
        "knowledge_cutoff": checked.isoformat(),
        "industry": {
            "industry_node_id": str(catalog.industry.industry_node_id),
            "canonical_name": catalog.industry.canonical_name,
            "node_kind": catalog.industry.node_kind,
            "archetype": catalog.industry.archetype,
            "memory_counts": counts.get(
                industry_subject.key,
                {"reality": 0, "judgments": 0, "outcomes": 0},
            ),
            "trajectory_replay": {"industry_node_id": str(industry_node_id)},
        },
        "subjects": subject_rows,
        "explicit_open_states": [],
        "boundary": {
            "membership_requires_fact_resolution_and_evidence": True,
            "membership_visibility_uses_source_known_at": True,
            "system_from_is_not_historical_known_at": True,
            "system_from_only_breaks_ties_between_already_knowable_versions": True,
            "memory_visibility_delegated_to_epistemic_snapshot": True,
            "same_knowledge_cutoff_used_for_membership_and_memory": True,
            "canonical_labels_are_current_catalog_identity_not_historical_name_replay": True,
            "presentation_infers_no_value_chain_role": True,
            "presentation_infers_no_importance_or_causality": True,
            "presentation_invents_no_unknown_or_controversy": True,
            "subject_order_is_lexical_not_importance_ranking": True,
        },
    }
