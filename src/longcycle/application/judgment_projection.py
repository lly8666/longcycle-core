from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, ValidationInfo, field_validator, model_validator

from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
    TemporalPrecision,
)
from longcycle.domain.judgments import JudgmentAssertion, JudgmentEvidenceRef
from longcycle.domain.models import DomainModel, require_aware_datetime, stable_uuid_exact


class JudgmentProjectionSubject(DomainModel):
    id: UUID
    entity_type: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)


class GroundedProjectionEvidence(DomainModel):
    fragment_key: str = Field(min_length=1)
    evidence_fragment_id: UUID
    document_version_id: UUID
    source_connector_id: UUID
    claim_role: str = Field(min_length=1)
    known_time_upper_bound: datetime
    source_published_at: datetime | None = None
    excerpt: str = Field(min_length=1)

    @field_validator("known_time_upper_bound", "source_published_at")
    @classmethod
    def times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)


class GroundedJudgmentEvidenceRef(DomainModel):
    fragment_key: str = Field(min_length=1)
    evidence_role: JudgmentEvidenceRole = JudgmentEvidenceRole.STATEMENT


class GroundedJudgmentProjectionItem(DomainModel):
    judgment_key: str = Field(min_length=1)
    evidence_refs: tuple[GroundedJudgmentEvidenceRef, ...]
    subject_entity_id: UUID
    speaker_name_text: str = Field(min_length=1)
    speaker_role: str | None = None
    topic_code: str = Field(min_length=1)
    judgment_kind: JudgmentKind
    target_time_kind: JudgmentTargetTimeKind
    target_at: datetime | None = None
    target_from: datetime | None = None
    target_to: datetime | None = None
    target_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    target_text: str | None = None
    value_kind: Literal[JudgmentValueKind.TEXT] = JudgmentValueKind.TEXT
    value_text: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    extraction_confidence: float = Field(default=1.0, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def migrate_v1_fragment_keys(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        legacy = payload.pop("evidence_fragment_keys", None)
        if legacy is None:
            return payload
        if "evidence_refs" in payload:
            raise ValueError("use either evidence_refs or legacy evidence_fragment_keys, not both")
        payload["evidence_refs"] = [
            {
                "fragment_key": fragment_key,
                "evidence_role": JudgmentEvidenceRole.STATEMENT.value,
            }
            for fragment_key in legacy
        ]
        return payload

    @field_validator("target_at", "target_from", "target_to")
    @classmethod
    def target_times_are_aware(
        cls,
        value: datetime | None,
        info: ValidationInfo,
    ) -> datetime | None:
        return require_aware_datetime(value, info.field_name)

    @model_validator(mode="after")
    def has_grounding(self) -> GroundedJudgmentProjectionItem:
        if not self.evidence_refs:
            raise ValueError("grounded judgment projection requires evidence refs")
        fragment_keys = [item.fragment_key for item in self.evidence_refs]
        if len(set(fragment_keys)) != len(fragment_keys):
            raise ValueError("grounded judgment evidence fragment keys must be unique")
        if not any(
            item.evidence_role == JudgmentEvidenceRole.STATEMENT for item in self.evidence_refs
        ):
            raise ValueError("grounded judgment projection requires a statement evidence ref")
        return self


class GroundedJudgmentProjectionSpec(DomainModel):
    schema_version: Literal[
        "longcycle-judgment-projection-spec/v1",
        "longcycle-judgment-projection-spec/v2",
    ]
    task_id: str = Field(min_length=1)
    source_evidence_task_id: str = Field(min_length=1)
    allowed_claim_roles: tuple[str, ...]
    subjects: tuple[JudgmentProjectionSubject, ...]
    judgments: tuple[GroundedJudgmentProjectionItem, ...]

    @model_validator(mode="after")
    def references_declared_subjects(self) -> GroundedJudgmentProjectionSpec:
        if not self.allowed_claim_roles:
            raise ValueError("judgment projection requires allowed claim roles")
        subject_ids = {subject.id for subject in self.subjects}
        if len(subject_ids) != len(self.subjects):
            raise ValueError("judgment projection subjects must have unique ids")
        keys = {item.judgment_key for item in self.judgments}
        if len(keys) != len(self.judgments):
            raise ValueError("judgment projection keys must be unique")
        missing = {item.subject_entity_id for item in self.judgments} - subject_ids
        if missing:
            raise ValueError("judgment projection references undeclared subjects")
        return self


def build_grounded_judgments(
    spec: GroundedJudgmentProjectionSpec,
    evidence: tuple[GroundedProjectionEvidence, ...],
) -> tuple[JudgmentAssertion, ...]:
    """Project archived evidence into immutable judgments without semantic guessing.

    The projection spec supplies the interpretation. This function only verifies that
    the cited evidence exists, is from an allowed contemporaneous claim role, and
    determines conservative provenance/known-time fields from the cited fragments.
    """

    by_key = {item.fragment_key: item for item in evidence}
    if len(by_key) != len(evidence):
        raise ValueError("grounded projection evidence keys must be unique")
    subjects = {item.id: item for item in spec.subjects}
    judgments: list[JudgmentAssertion] = []

    for item in spec.judgments:
        try:
            cited = tuple((ref, by_key[ref.fragment_key]) for ref in item.evidence_refs)
        except KeyError as exc:
            raise ValueError(f"judgment cites unavailable evidence fragment: {exc.args[0]}") from exc

        cited_rows = tuple(row for _, row in cited)
        disallowed = sorted({row.claim_role for row in cited_rows} - set(spec.allowed_claim_roles))
        if disallowed:
            raise ValueError(
                "judgment projection cites disallowed claim roles: " + ", ".join(disallowed)
            )
        if any(row.claim_role == "outcome_milestone" for row in cited_rows):
            raise ValueError("later outcome evidence cannot be projected as contemporaneous judgment")
        for ref, row in cited:
            if row.claim_role == "risk_caveat" and ref.evidence_role != JudgmentEvidenceRole.CAVEAT:
                raise ValueError("risk_caveat evidence must be projected with caveat evidence role")

        source_ids = {row.source_connector_id for row in cited_rows}
        if len(source_ids) != 1:
            raise ValueError("one judgment projection must resolve to one source connector")
        source_connector_id = next(iter(source_ids))
        first_known_at = max(row.known_time_upper_bound for row in cited_rows)
        published_candidates = [row.source_published_at for row in cited_rows if row.source_published_at]
        source_published_at = max(published_candidates) if published_candidates else None
        subject = subjects[item.subject_entity_id]

        if spec.schema_version.endswith("/v1"):
            identity_parts = tuple(str(row.evidence_fragment_id) for row in cited_rows)
            extractor_version = "1.0.0"
        else:
            identity_parts = tuple(
                f"{ref.evidence_role.value}:{row.evidence_fragment_id}" for ref, row in cited
            )
            extractor_version = "2.0.0"

        judgments.append(
            JudgmentAssertion(
                id=stable_uuid_exact(
                    "judgment-projection",
                    spec.task_id,
                    item.judgment_key,
                    *identity_parts,
                ),
                speaker_name_text=item.speaker_name_text,
                speaker_role=item.speaker_role,
                subject_entity_id=item.subject_entity_id,
                topic_code=item.topic_code,
                judgment_kind=item.judgment_kind,
                target_time_kind=item.target_time_kind,
                target_at=item.target_at,
                target_from=item.target_from,
                target_to=item.target_to,
                target_precision=item.target_precision,
                target_text=item.target_text,
                value_kind=JudgmentValueKind.TEXT,
                value_text=item.value_text,
                summary=item.summary,
                source_published_at=source_published_at,
                first_known_at=first_known_at,
                extraction_run_id=stable_uuid_exact(
                    "judgment-projection-run",
                    spec.task_id,
                    item.judgment_key,
                    *identity_parts,
                ),
                source_connector_id=source_connector_id,
                extractor_name="grounded-judgment-projection",
                extractor_version=extractor_version,
                extraction_confidence=item.extraction_confidence,
                evidence=tuple(
                    JudgmentEvidenceRef(
                        evidence_fragment_id=row.evidence_fragment_id,
                        evidence_role=ref.evidence_role,
                    )
                    for ref, row in cited
                ),
                metadata={
                    **item.metadata,
                    "projection_task_id": spec.task_id,
                    "judgment_key": item.judgment_key,
                    "source_evidence_task_id": spec.source_evidence_task_id,
                    "source_fragment_keys": [ref.fragment_key for ref, _ in cited],
                    "source_claim_roles": [row.claim_role for _, row in cited],
                    "evidence_roles": [ref.evidence_role.value for ref, _ in cited],
                    "subject_entity_type": subject.entity_type,
                    "subject_canonical_name": subject.canonical_name,
                },
            )
        )

    return tuple(judgments)
