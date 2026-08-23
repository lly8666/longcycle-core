from __future__ import annotations

from typing import Protocol
from uuid import UUID

from longcycle.domain.evidence import EvidenceDrilldownRecord


class EvidenceDrilldownReader(Protocol):
    """Storage-neutral read boundary for claim-scoped Evidence navigation."""

    async def evidence_fragment(self, fragment_id: UUID) -> EvidenceDrilldownRecord | None: ...
