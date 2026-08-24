from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef, PointInTimeMemorySnapshot
from longcycle.domain.models import require_aware_datetime
from longcycle.domain.orientation import (
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    IndustrySubjectMembershipRecord,
)
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


def _visible_discoveries(
    discoveries: tuple[IndustrySubjectDiscoveryRecord, ...],
    *,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
) -> tuple[IndustrySubjectDiscoveryRecord, ...]:
    """Defensively enforce the same no-lookahead boundary on discovery recall."""

    selected: dict[tuple[str, UUID], IndustrySubjectDiscoveryRecord] = {}
    for discovery in discoveries:
        if discovery.industry_node_id != industry_node_id:
            raise ValueError("industry discovery reader returned a record for another industry")
        if discovery.known_at > knowledge_cutoff:
            continue
        selected[(discovery.basis_kind, discovery.basis_id)] = discovery
    return tuple(
        sorted(
            selected.values(),
            key=lambda item: (
                item.canonical_name.casefold(),
                str(item.subject.entity_id),
                item.known_at,
                item.basis_kind,
                str(item.basis_id),
            ),
        )
    )


async def _load_industry_subject_universe(
    *,
    catalog_reader: IndustryOrientationReader,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
) -> tuple[
    datetime,
    IndustryOrientationCatalog,
    tuple[IndustrySubjectMembershipRecord, ...],
    tuple[IndustrySubjectDiscoveryRecord, ...],
    dict[UUID, MemorySubjectRef],
]:
    """Load the CAP-0005 industry subject universe from direct and entailed bases.

    A subject is eligible when it has either a visible source-grounded membership or a
    deterministic discovery basis from already-grounded memory explicitly scoped to the
    industry. The latter is recall-only and never becomes membership truth.
    """

    checked = require_aware_datetime(knowledge_cutoff, "knowledge_cutoff")
    assert checked is not None
    catalog = await catalog_reader.industry_catalog(industry_node_id)
    memberships = _visible_memberships(catalog, knowledge_cutoff=checked)
    discoveries = _visible_discoveries(
        await catalog_reader.deterministic_industry_subjects(
            industry_node_id,
            knowledge_cutoff=checked,
        ),
        industry_node_id=industry_node_id,
        knowledge_cutoff=checked,
    )
    subjects: dict[UUID, MemorySubjectRef] = {}
    for membership in memberships:
        assert membership.subject.entity_id is not None
        subjects[membership.subject.entity_id] = membership.subject
    for discovery in discoveries:
        assert discovery.subject.entity_id is not None
        subjects[discovery.subject.entity_id] = discovery.subject
    return checked, catalog, memberships, discoveries, subjects


def _memory_counts(snapshot: PointInTimeMemorySnapshot) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"reality": 0, "judgments": 0, "outcomes": 0}
    )
    for reality in snapshot.reality:
        counts[reality.subject.key]["reality"] += 1
    for judgment in snapshot.judgments:
        counts[judgment.subject.key]["judgments"] += 1
    for outcome in snapshot.outcomes:
        counts[outcome.subject.key]["outcomes"] += 1
    return counts


def _evidence_by_subject(snapshot: PointInTimeMemorySnapshot) -> dict[str, set[str]]:
    evidence: dict[str, set[str]] = defaultdict(set)
    judgment_subjects = {
        judgment.judgment_id: judgment.subject.key for judgment in snapshot.judgments
    }
    for reality in snapshot.reality:
        evidence[reality.subject.key].update(
            str(value) for value in reality.evidence_fragment_ids
        )
    for judgment in snapshot.judgments:
        evidence[judgment.subject.key].update(
            str(value) for value in judgment.evidence_fragment_ids
        )
    for rationale in snapshot.judgment_rationales:
        subject_key = judgment_subjects.get(rationale.judgment_id)
        if subject_key is not None and rationale.evidence_fragment_id is not None:
            evidence[subject_key].add(str(rationale.evidence_fragment_id))
    for outcome in snapshot.outcomes:
        if outcome.outcome_evidence_fragment_id is not None:
            evidence[outcome.subject.key].add(str(outcome.outcome_evidence_fragment_id))
    return evidence


def _judgment_relation_markers(
    snapshot: PointInTimeMemorySnapshot,
) -> dict[str, list[dict[str, Any]]]:
    judgment_subjects = {
        judgment.judgment_id: judgment.subject.key for judgment in snapshot.judgments
    }
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


def _direct_discovery_basis(membership: IndustrySubjectMembershipRecord) -> dict[str, Any]:
    return {
        "certainty": "direct",
        "basis_kind": "industry_membership",
        "basis_id": str(membership.membership_id),
        "semantic_code": "industry.membership",
        "known_at": membership.known_at.isoformat(),
        "evidence_fragment_ids": [str(value) for value in membership.evidence_fragment_ids],
    }


def _entailed_discovery_basis(discovery: IndustrySubjectDiscoveryRecord) -> dict[str, Any]:
    return {
        "certainty": "entailed",
        "basis_kind": discovery.basis_kind,
        "basis_id": str(discovery.basis_id),
        "semantic_code": discovery.semantic_code,
        "known_at": discovery.known_at.isoformat(),
        "entailment_rule": discovery.entailment_rule,
        "evidence_fragment_ids": [str(value) for value in discovery.evidence_fragment_ids],
    }


async def build_researcher_industry_orientation(
    *,
    catalog_reader: IndustryOrientationReader,
    memory_reader: EpistemicMemoryReader,
    industry_node_id: UUID,
    knowledge_cutoff: datetime,
) -> dict[str, Any]:
    """Build a broad but auditable researcher entry view at one knowledge cutoff.

    Direct membership remains source-grounded catalog truth. Separately, already-grounded
    Reality/Judgment carrying explicit industry scope may deterministically make a subject
    discoverable. That entailment expands recall only: it never manufactures membership,
    role, importance, causality or historical timing.
    """

    checked, catalog, visible_memberships, visible_discoveries, subjects = (
        await _load_industry_subject_universe(
            catalog_reader=catalog_reader,
            industry_node_id=industry_node_id,
            knowledge_cutoff=knowledge_cutoff,
        )
    )

    memberships_by_entity: dict[UUID, list[IndustrySubjectMembershipRecord]] = defaultdict(list)
    discoveries_by_entity: dict[UUID, list[IndustrySubjectDiscoveryRecord]] = defaultdict(list)
    for membership in visible_memberships:
        assert membership.subject.entity_id is not None
        memberships_by_entity[membership.subject.entity_id].append(membership)
    for discovery in visible_discoveries:
        assert discovery.subject.entity_id is not None
        discoveries_by_entity[discovery.subject.entity_id].append(discovery)

    snapshot_subjects = (
        MemorySubjectRef(industry_node_id=industry_node_id),
        *(subjects[entity_id] for entity_id in sorted(subjects, key=str)),
    )
    snapshot = await memory_reader.snapshot(snapshot_subjects, knowledge_cutoff=checked)
    counts = _memory_counts(snapshot)
    evidence = _evidence_by_subject(snapshot)
    relation_markers = _judgment_relation_markers(snapshot)

    rows_to_render: list[
        tuple[
            UUID,
            str,
            str,
            list[IndustrySubjectMembershipRecord],
            list[IndustrySubjectDiscoveryRecord],
        ]
    ] = []
    for entity_id in subjects:
        entity_memberships = memberships_by_entity.get(entity_id, [])
        entity_discoveries = discoveries_by_entity.get(entity_id, [])
        if entity_memberships:
            canonical_name = entity_memberships[0].canonical_name
            entity_type = entity_memberships[0].entity_type
        elif entity_discoveries:
            canonical_name = entity_discoveries[0].canonical_name
            entity_type = entity_discoveries[0].entity_type
        else:  # pragma: no cover - subjects are populated only from one of these inputs
            raise RuntimeError("orientation subject has no discovery basis")
        rows_to_render.append(
            (
                entity_id,
                canonical_name,
                entity_type,
                entity_memberships,
                entity_discoveries,
            )
        )

    subject_rows: list[dict[str, Any]] = []
    for entity_id, canonical_name, entity_type, entity_memberships, entity_discoveries in sorted(
        rows_to_render,
        key=lambda item: (item[1].casefold(), str(item[0])),
    ):
        subject_key = subjects[entity_id].key
        subject_evidence = set(evidence.get(subject_key, set()))
        for membership in entity_memberships:
            subject_evidence.update(str(value) for value in membership.evidence_fragment_ids)
        for discovery in entity_discoveries:
            subject_evidence.update(str(value) for value in discovery.evidence_fragment_ids)
        discovery_bases = [
            *(_direct_discovery_basis(membership) for membership in entity_memberships),
            *(_entailed_discovery_basis(discovery) for discovery in entity_discoveries),
        ]
        subject_rows.append(
            {
                "subject_id": str(entity_id),
                "canonical_name": canonical_name,
                "entity_type": entity_type,
                "discovery_certainty": "direct" if entity_memberships else "entailed",
                "discovery_bases": discovery_bases,
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
            "researcher_discovery_allows_deterministic_entailment": True,
            "entailed_discovery_requires_grounded_explicit_industry_scope": True,
            "entailed_discovery_does_not_create_membership_or_role": True,
            "system_from_is_not_historical_known_at": True,
            "system_from_only_breaks_ties_between_already_knowable_versions": True,
            "memory_visibility_delegated_to_epistemic_snapshot": True,
            "same_knowledge_cutoff_used_for_membership_and_memory": True,
            "same_knowledge_cutoff_used_for_membership_discovery_and_memory": True,
            "canonical_labels_are_current_catalog_identity_not_historical_name_replay": True,
            "presentation_infers_no_value_chain_role": True,
            "presentation_infers_no_importance_or_causality": True,
            "presentation_invents_no_unknown_or_controversy": True,
            "subject_order_is_lexical_not_importance_ranking": True,
        },
    }
