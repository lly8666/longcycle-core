from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition


class SourceNotModified(RuntimeError):
    """A conditional fetch returned HTTP 304 and needs no downstream work."""

    def __init__(self, url: str, headers: dict[str, str]) -> None:
        super().__init__(f"source not modified: {url}")
        self.url = url
        self.headers = headers


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    source: SourceDefinition
    industry_id: UUID | None = None
    since: datetime | None = None
    cursor: dict[str, Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.since is not None and (self.since.tzinfo is None or self.since.utcoffset() is None):
            raise ValueError("since must include a timezone")


@dataclass(frozen=True, slots=True)
class FetchContext:
    source: SourceDefinition
    timeout_seconds: float = 30
    maximum_bytes: int = 50 * 1024 * 1024
    conditional_headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.maximum_bytes < 1:
            raise ValueError("maximum_bytes must be positive")


class SourcePlugin(Protocol):
    plugin_name: str

    def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveryItem]: ...

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload: ...
