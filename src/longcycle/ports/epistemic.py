from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from longcycle.domain.epistemic import (
    IndustrialMemoryTimeline,
    MemorySubjectRef,
    PointInTimeMemorySnapshot,
)


class EpistemicMemoryReader(Protocol):
    """Storage-neutral read boundary for durable industrial memory.

    Writers may use PostgreSQL or another transactional adapter. Replay consumers do
    not depend on those tables; they consume this typed read model instead.
    """

    async def timeline(
        self,
        subjects: Sequence[MemorySubjectRef],
    ) -> IndustrialMemoryTimeline: ...

    async def snapshot(
        self,
        subjects: Sequence[MemorySubjectRef],
        *,
        knowledge_cutoff: datetime,
    ) -> PointInTimeMemorySnapshot: ...
