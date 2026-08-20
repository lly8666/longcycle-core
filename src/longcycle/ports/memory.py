from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from longcycle.domain.memory import MemoryLead


@dataclass(frozen=True, slots=True)
class MemoryPriorResponse:
    raw_text: str
    leads: tuple[MemoryLead, ...]


class MemoryPriorGateway(Protocol):
    provider_name: str
    model_name: str
    model_version: str | None
    protocol_version: str

    async def recall(self, *, prompt: str) -> MemoryPriorResponse: ...
