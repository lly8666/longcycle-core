from __future__ import annotations

import asyncio
import mimetypes
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition
from longcycle.ports.source import DiscoveryContext, FetchContext


class LocalFolderSource:
    plugin_name = "local_folder"

    def __init__(self, definition: SourceDefinition) -> None:
        self.definition = definition
        configured_root = definition.config.get("root", ".")
        self.root = Path(str(configured_root)).expanduser().resolve()
        patterns = definition.config.get("patterns", ["**/*"])
        if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
            raise ValueError("local_folder patterns must be a list of glob strings")
        self.patterns = tuple(patterns)

    async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveryItem]:
        del context
        seen: set[Path] = set()
        for pattern in self.patterns:
            for path in sorted(self.root.glob(pattern)):
                resolved = path.resolve()
                if (
                    resolved in seen
                    or not resolved.is_file()
                    or not resolved.is_relative_to(self.root)
                ):
                    continue
                seen.add(resolved)
                stat = resolved.stat()
                modified_at = datetime.fromtimestamp(stat.st_mtime, UTC)
                yield DiscoveryItem(
                    source_id=self.definition.id,
                    external_id=str(resolved.relative_to(self.root)).replace("\\", "/"),
                    url=resolved.as_uri(),
                    title_hint=resolved.name,
                    published_at_hint=modified_at,
                    metadata={"file_path": str(resolved), "size": stat.st_size},
                )

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload:
        raw_path = item.metadata.get("file_path")
        if not isinstance(raw_path, str):
            raise ValueError("local discovery item is missing file_path")
        path = Path(raw_path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("refusing to fetch a path outside the configured root")
        if path.stat().st_size > context.maximum_bytes:
            raise ValueError(f"file exceeds {context.maximum_bytes} bytes")
        content = await asyncio.to_thread(self._read_limited, path, context.maximum_bytes)
        if len(content) > context.maximum_bytes:
            raise ValueError(f"file exceeds {context.maximum_bytes} bytes")
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return RawPayload(
            content=content,
            content_type=content_type,
            canonical_url=item.url,
            headers={
                "x-longcycle-transport": self.plugin_name,
                "x-longcycle-raw-source-materialized": "true",
            },
        )

    @staticmethod
    def _read_limited(path: Path, maximum_bytes: int) -> bytes:
        with path.open("rb") as handle:
            return handle.read(maximum_bytes + 1)
