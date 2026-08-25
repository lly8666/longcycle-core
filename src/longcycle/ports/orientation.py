from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryMembershipSemanticJudgment,
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    ResolvedIndustryMembershipResolution,
)


class IndustryOrientationReader(Protocol):
    """Storage-neutral catalog and deterministic discovery boundary for researcher entry."""

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog: ...

    async def deterministic_industry_subjects(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[IndustrySubjectDiscoveryRecord, ...]: ...


class IndustryMembershipResolutionReader(Protocol):
    """Read one already-decided CAP-0003 Fact resolution for projection."""

    async def industry_membership_resolution(
        self,
        resolution_id: UUID,
    ) -> ResolvedIndustryMembershipResolution: ...


class IndustryMembershipSemanticJudge(Protocol):
    """Model boundary for choosing one catalog representation from selected assertions.

    ``standard`` is always attempted first. If the supplied material definitions conflict,
    the application must call the same boundary again with ``deep`` before materialization.
    Model output is interpretation provenance, never source Evidence.
    """

    async def judge_industry_membership(
        self,
        resolution: ResolvedIndustryMembershipResolution,
        *,
        reasoning_mode: Literal["standard", "deep"],
    ) -> IndustryMembershipSemanticJudgment: ...


class IndustryMembershipSemanticDecisionWriter(Protocol):
    """Persist audit-only model decision provenance before catalog materialization."""

    async def append_industry_membership_semantic_decision(
        self,
        decision: IndustryMembershipSemanticDecision,
    ) -> IndustryMembershipSemanticDecision: ...


class IndustryMembershipProjectionWriter(Protocol):
    """Materialize a validated membership projection without rewriting source truth."""

    async def append_industry_membership(
        self,
        projection: IndustryMembershipProjection,
    ) -> IndustryMembershipProjection: ...
