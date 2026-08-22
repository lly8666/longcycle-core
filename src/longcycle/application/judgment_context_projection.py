from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from longcycle.application.judgment_projection import GroundedProjectionEvidence
from longcycle.domain.enums import JudgmentRationaleKind, JudgmentRelationType
from longcycle.domain.judgments import JudgmentAssertion, JudgmentRationale, JudgmentRelation
from longcycle.domain.models import DomainModel, stable_uuid_exact


_REVISION_FAMILY = frozenset(
    {
        JudgmentRelationType.REVISES,
        JudgmentRelationType.REAFFIRMS,
        JudgmentRelationType.WITHDRAWS,
        JudgmentRelationType.NARROWS,
        JudgmentRelationType.WIDENS,
    }
)


class GroundedJudgmentRationaleItem(DomainModel):
    rationale_key: str = Field(min_length=1)
    judgment_key: str = Field(min_length=1)
    rationale_kind: JudgmentRationaleKind
    summary: str = Field(min_length=1)
    evidence_fragment_key: str | None = None
    linked_judgment_key: str | None = None
    ordinal: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def has_grounding(self) -> GroundedJudgmentRationaleItem:
        if self.evidence_fragment_key is None and self.linked_judgment_key is None:
            raise ValueError("grounded Judgment rationale requires evidence or a linked Judgment")
        return self


class GroundedJudgmentRelationItem(DomainModel):
    from_judgment_key: str = Field(min_length=1)
    to_judgment_key: str = Field(min_length=1)
    relation_type: JudgmentRelationType
    reason_summary: str | None = None

    @model_validator(mode="after")
    def does_not_self_link(self) -> GroundedJudgmentRelationItem:
        if self.from_judgment_key == self.to_judgment_key:
            raise ValueError("grounded Judgment relation cannot self-link")
        return self


class GroundedJudgmentContextSpec(DomainModel):
    schema_version: Literal["longcycle-judgment-context-projection-spec/v1"]
    task_id: str = Field(min_length=1)
    source_judgment_task_id: str = Field(min_length=1)
    source_evidence_task_id: str = Field(min_length=1)
    allowed_rationale_claim_roles: tuple[str, ...] = ()
    rationales: tuple[GroundedJudgmentRationaleItem, ...] = ()
    relations: tuple[GroundedJudgmentRelationItem, ...] = ()

    @model_validator(mode="after")
    def has_unique_context(self) -> GroundedJudgmentContextSpec:
        if not self.rationales and not self.relations:
            raise ValueError("grounded Judgment context spec must define context")
        rationale_keys = [item.rationale_key for item in self.rationales]
        if len(set(rationale_keys)) != len(rationale_keys):
            raise ValueError("grounded Judgment rationale keys must be unique")
        relation_keys = [
            (item.from_judgment_key, item.to_judgment_key, item.relation_type)
            for item in self.relations
        ]
        if len(set(relation_keys)) != len(relation_keys):
            raise ValueError("grounded Judgment relations must be unique")
        return self


def _judgments_by_key(
    judgments: tuple[JudgmentAssertion, ...],
) -> dict[str, JudgmentAssertion]:
    result: dict[str, JudgmentAssertion] = {}
    for judgment in judgments:
        key = judgment.metadata.get("judgment_key")
        if not isinstance(key, str) or not key:
            raise ValueError("grounded context requires Judgment metadata.judgment_key")
        if key in result:
            raise ValueError("grounded context Judgment keys must be unique")
        result[key] = judgment
    return result


def _same_subject(left: JudgmentAssertion, right: JudgmentAssertion) -> bool:
    return (
        left.subject_entity_id == right.subject_entity_id
        and left.subject_industry_node_id == right.subject_industry_node_id
    )


def build_grounded_judgment_context(
    spec: GroundedJudgmentContextSpec,
    judgments: tuple[JudgmentAssertion, ...],
    evidence: tuple[GroundedProjectionEvidence, ...],
) -> tuple[tuple[JudgmentRationale, ...], tuple[JudgmentRelation, ...]]:
    """Build source-backed cognitive context around already-grounded Judgments.

    The projection never edits a Judgment. Rationale inputs must have been knowable
    no later than the owning Judgment. Revision-family relations require the same
    subject/topic and must point from later-or-equal cognition to earlier cognition.
    """

    by_judgment_key = _judgments_by_key(judgments)
    by_evidence_key = {item.fragment_key: item for item in evidence}
    if len(by_evidence_key) != len(evidence):
        raise ValueError("grounded context evidence keys must be unique")

    rationales: list[JudgmentRationale] = []
    for rationale_item in spec.rationales:
        try:
            judgment = by_judgment_key[rationale_item.judgment_key]
        except KeyError as exc:
            raise ValueError(
                f"rationale references unavailable Judgment: {rationale_item.judgment_key}"
            ) from exc

        evidence_row = None
        if rationale_item.evidence_fragment_key is not None:
            try:
                evidence_row = by_evidence_key[rationale_item.evidence_fragment_key]
            except KeyError as exc:
                raise ValueError(
                    "rationale references unavailable evidence fragment: "
                    f"{rationale_item.evidence_fragment_key}"
                ) from exc
            if (
                spec.allowed_rationale_claim_roles
                and evidence_row.claim_role not in spec.allowed_rationale_claim_roles
            ):
                raise ValueError("rationale cites disallowed claim role: " + evidence_row.claim_role)
            if evidence_row.known_time_upper_bound > judgment.first_known_at:
                raise ValueError("rationale evidence cannot become knowable after its Judgment")

        linked_judgment = None
        if rationale_item.linked_judgment_key is not None:
            try:
                linked_judgment = by_judgment_key[rationale_item.linked_judgment_key]
            except KeyError as exc:
                raise ValueError(
                    "rationale references unavailable linked Judgment: "
                    f"{rationale_item.linked_judgment_key}"
                ) from exc
            if linked_judgment.first_known_at > judgment.first_known_at:
                raise ValueError("rationale cannot cite a Judgment from a later knowledge vintage")

        rationales.append(
            JudgmentRationale(
                id=stable_uuid_exact(
                    "grounded-judgment-rationale",
                    spec.task_id,
                    rationale_item.rationale_key,
                    str(judgment.id),
                    str(evidence_row.evidence_fragment_id) if evidence_row else "",
                    str(linked_judgment.id) if linked_judgment else "",
                ),
                judgment_id=judgment.id,
                rationale_kind=rationale_item.rationale_kind,
                summary=rationale_item.summary,
                linked_judgment_id=linked_judgment.id if linked_judgment is not None else None,
                evidence_fragment_id=(
                    evidence_row.evidence_fragment_id if evidence_row is not None else None
                ),
                ordinal=rationale_item.ordinal,
            )
        )

    relations: list[JudgmentRelation] = []
    for relation_item in spec.relations:
        try:
            from_judgment = by_judgment_key[relation_item.from_judgment_key]
            to_judgment = by_judgment_key[relation_item.to_judgment_key]
        except KeyError as exc:
            raise ValueError(f"relation references unavailable Judgment: {exc.args[0]}") from exc

        if relation_item.relation_type in _REVISION_FAMILY:
            if not _same_subject(from_judgment, to_judgment):
                raise ValueError("revision-family relation requires the same Judgment subject")
            if from_judgment.topic_code != to_judgment.topic_code:
                raise ValueError("revision-family relation requires the same Judgment topic")
            if from_judgment.first_known_at < to_judgment.first_known_at:
                raise ValueError(
                    "revision-family relation cannot point from earlier cognition to later cognition"
                )

        relations.append(
            JudgmentRelation(
                from_judgment_id=from_judgment.id,
                to_judgment_id=to_judgment.id,
                relation_type=relation_item.relation_type,
                reason_summary=relation_item.reason_summary,
            )
        )

    return tuple(rationales), tuple(relations)
