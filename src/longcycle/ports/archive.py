from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ArchivedObject:
    key: str
    sha256: str
    size: int
    content_type: str
    created: bool


class ArchiveStore(Protocol):
    async def put_if_absent(
        self,
        *,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ArchivedObject: ...

    async def get(self, key: str) -> bytes: ...

    async def exists(self, key: str) -> bool: ...
