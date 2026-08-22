from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from pathlib import Path

from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition
from longcycle.ports.source import DiscoveryContext, FetchContext


class MaterializedDocumentSource:
    """Read externally acquired source bytes from a bounded local material root.

    The local file is only a transport. Source identity remains the canonical URL,
    publisher domain and external identifier carried by the DiscoveryItem/SourceDefinition.
    """

    plugin_name = "materialized_file"

    def __init__(self, definition: SourceDefinition, *, material_root: Path) -> None:
        if definition.plugin != self.plugin_name:
            raise ValueError("materialized source definition must use materialized_file plugin")
        root = material_root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"material root is not a directory: {root}")
        self.definition = definition
        self.material_root = root

    async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveryItem]:
        del context
        if False:
            yield DiscoveryItem(source_id=self.definition.id, url="https://invalid.example/")

    def _resolve_material_path(self, relative_value: object) -> Path:
        if not isinstance(relative_value, str) or not relative_value.strip():
            raise ValueError("materialized source requires metadata.material_path")
        relative = Path(relative_value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("materialized source path must stay relative to material root")
        resolved = (self.material_root / relative).resolve()
        if not resolved.is_relative_to(self.material_root):
            raise ValueError("materialized source path escapes material root")
        if not resolved.is_file():
            raise ValueError(f"materialized source file does not exist: {relative_value}")
        return resolved

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload:
        if item.source_id != self.definition.id or context.source != self.definition:
            raise ValueError("materialized fetch source identity mismatch")

        path = self._resolve_material_path(item.metadata.get("material_path"))
        expected_sha256 = item.metadata.get("material_expected_sha256")
        if not isinstance(expected_sha256, str) or not _is_lower_sha256(expected_sha256):
            raise ValueError("materialized source requires a lowercase expected SHA-256")
        content_type = item.metadata.get("material_content_type")
        if not isinstance(content_type, str) or not content_type.strip():
            raise ValueError("materialized source requires metadata.material_content_type")

        size = path.stat().st_size
        if size > context.maximum_bytes:
            raise ValueError(f"source payload exceeds {context.maximum_bytes} bytes")
        content = path.read_bytes()
        if len(content) > context.maximum_bytes:
            raise ValueError(f"source payload exceeds {context.maximum_bytes} bytes")

        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_sha256:
            raise ValueError(
                f"materialized source digest mismatch: expected {expected_sha256}, got {digest}"
            )
        return RawPayload(
            content=content,
            content_type=content_type.strip(),
            canonical_url=item.url,
            headers={
                "x-longcycle-transport": self.plugin_name,
                "x-longcycle-material-sha256": digest,
            },
        )


def _is_lower_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
