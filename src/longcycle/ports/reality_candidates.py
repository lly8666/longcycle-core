from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from longcycle.domain.reality_candidates import RealityResearchCandidate


class RealityResearchCandidateReader(Protocol):
    """Read source-backed noncanonical Reality candidates at one knowledge cutoff."""

    async def candidates_for_industry(
        self,
        industry_node_id: UUID,
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[RealityResearchCandidate, ...]: ...
