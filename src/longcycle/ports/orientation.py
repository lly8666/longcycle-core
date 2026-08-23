from __future__ import annotations

from typing import Protocol
from uuid import UUID

from longcycle.domain.orientation import IndustryOrientationCatalog


class IndustryOrientationReader(Protocol):
    """Storage-neutral catalog boundary for researcher industry entry."""

    async def industry_catalog(self, industry_node_id: UUID) -> IndustryOrientationCatalog: ...
