from __future__ import annotations

from typing import Protocol
from uuid import UUID

from longcycle.domain.orientation import (
    IndustryMembershipProjection,
    IndustryOrientationCatalog,
    ResolvedIndustryMembershipResolution,
)


class IndustryOrientationReader(Protocol):
    """Storage-neutral catalog boundary for researcher industry entry."""

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog: ...


class IndustryMembershipResolutionReader(Protocol):
    """Read one already-decided CAP-0003 Fact resolution for projection."""

    async def industry_membership_resolution(
        self,
        resolution_id: UUID,
    ) -> ResolvedIndustryMembershipResolution: ...


class IndustryMembershipProjectionWriter(Protocol):
    """Materialize a validated membership projection without deciding truth."""

    async def append_industry_membership(
        self,
        projection: IndustryMembershipProjection,
    ) -> IndustryMembershipProjection: ...
