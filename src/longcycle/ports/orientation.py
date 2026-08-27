from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from longcycle.domain.orientation import (
    IndustryMembershipModelJudgmentRun,
    IndustryMembershipProjection,
    IndustryMembershipSemanticDecision,
    IndustryMembershipSemanticJudgment,
    IndustryOrientationCatalog,
    IndustrySubjectDiscoveryRecord,
    ResolvedIndustryMembershipResolution,
)


IndustryOrientationCapability = Literal["deterministic_industry_subjects"]


class IndustryOrientationReader(Protocol):
    """Storage-neutral catalog and explicitly declared researcher-discovery boundary."""

    capabilities: frozenset[IndustryOrientationCapability]

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
    """Host/model boundary for one membership semantic judgment execution.

    The Longcycle-running Agent may implement this boundary directly. ``standard`` is always
    attempted first; application-owned deterministic triggers and model self-escalation decide
    whether the same boundary is called again with ``deep``. Model output is provenance, never
    source Evidence.
    """

    async def judge_industry_membership(
        self,
        resolution: ResolvedIndustryMembershipResolution,
        *,
        reasoning_mode: Literal["standard", "deep"],
    ) -> IndustryMembershipSemanticJudgment: ...


class IndustryMembershipJudgmentRunWriter(Protocol):
    """Append one immutable record for every actual model/host judgment execution."""

    async def append_industry_membership_judgment_run(
        self,
        run: IndustryMembershipModelJudgmentRun,
    ) -> IndustryMembershipModelJudgmentRun: ...


class IndustryMembershipSemanticDecisionWriter(Protocol):
    """Persist/confirm a durable semantic conclusion independently of individual runs."""

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
