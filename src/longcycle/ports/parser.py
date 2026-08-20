from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from longcycle.domain.models import SourceDocument


@dataclass(frozen=True, slots=True)
class ParsedOutput:
    artifact_type: str
    content: bytes
    content_type: str

    def __post_init__(self) -> None:
        if not self.artifact_type.strip():
            raise ValueError("artifact_type must not be blank")
        if not self.content_type.strip():
            raise ValueError("content_type must not be blank")


class DocumentParser(Protocol):
    parser_name: str
    parser_version: str
    supported_media_types: frozenset[str]

    async def parse(self, document: SourceDocument, content: bytes) -> tuple[ParsedOutput, ...]: ...
