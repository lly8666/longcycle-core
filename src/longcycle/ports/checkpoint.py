from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

class CheckpointStore(Protocol):
    async def get(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
    ) -> Any | None: ...

    async def save(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
        result: Any,
    ) -> Any:
        """Persist first-writer-wins and return the authoritative checkpoint."""
        ...
