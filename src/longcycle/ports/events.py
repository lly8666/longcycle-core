from __future__ import annotations

from typing import Any, Protocol

from longcycle.domain.models import CollectionJob


class EventSink(Protocol):
    async def emit(
        self,
        *,
        job: CollectionJob,
        event: dict[str, Any],
        idempotency_key: str,
    ) -> None: ...
