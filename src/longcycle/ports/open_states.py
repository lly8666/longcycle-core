from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.open_states import (
    CurrentResearchOpenStateBundle,
    RealitySourceDisagreementRecord,
)


class RealityConflictReader(Protocol):
    """Storage-neutral read boundary for explicit Reality conflict cases."""

    async def historical_source_disagreements(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> tuple[RealitySourceDisagreementRecord, ...]: ...


class CurrentResearchOpenStateReader(Protocol):
    """Current research-state reader; results are never historical market knowledge."""

    async def current_open_states(
        self,
        *,
        industry_node_id: UUID,
        entity_ids: Sequence[UUID],
    ) -> CurrentResearchOpenStateBundle: ...
