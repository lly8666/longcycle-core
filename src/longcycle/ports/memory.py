from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from longcycle.domain.memory import MemoryLead


@dataclass(frozen=True, slots=True)
class MemoryPriorResponse:
    raw_text: str
    leads: tuple[MemoryLead, ...]


class MemoryPriorGateway(Protocol):
    """Prior-only recall. Implementations must not silently add fresh search results."""

    provider_name: str
    model_name: str
    model_version: str | None
    protocol_version: str

    async def recall(self, *, prompt: str) -> MemoryPriorResponse: ...


@dataclass(frozen=True, slots=True)
class MemoryVerificationFinding:
    """Discovery output from a search-enabled high-capability model.

    Candidate URLs are still discovery material. They become Evidence only after the normal
    fetch/archive/locator pipeline persists the underlying source material.
    """

    lead_id: UUID
    refined_summary: str
    candidate_urls: tuple[str, ...] = ()
    refined_queries: tuple[str, ...] = ()
    possible_primary_sources: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryVerificationResponse:
    raw_text: str
    findings: tuple[MemoryVerificationFinding, ...]


class MemorySelfVerificationGateway(Protocol):
    """Search-enabled second stage; must operate on an already sealed blind atlas."""

    provider_name: str
    model_name: str
    model_version: str | None
    protocol_version: str

    async def investigate(
        self,
        *,
        prompt: str,
        leads: tuple[MemoryLead, ...],
    ) -> MemoryVerificationResponse: ...
