from __future__ import annotations

import asyncio
from uuid import UUID

from longcycle.application.workflow import StageResult


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self.items: dict[tuple[UUID, str, str, str], StageResult] = {}
        self._lock = asyncio.Lock()

    async def get(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
    ) -> StageResult | None:
        return self.items.get((job_id, stage, input_hash, producer_version))

    async def save(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
        result: StageResult,
    ) -> StageResult:
        async with self._lock:
            return self.items.setdefault((job_id, stage, input_hash, producer_version), result)
