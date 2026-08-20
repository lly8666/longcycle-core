from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
from pathlib import Path

from longcycle.ports.archive import ArchivedObject


class FileSystemArchiveStore:
    """Content-addressed local store with the same key layout used in S3/R2."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("archive key escapes root")
        return path

    async def put_if_absent(
        self,
        *,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ArchivedObject:
        return await asyncio.to_thread(self._put_sync, content, content_type, metadata or {})

    def _put_sync(self, content: bytes, content_type: str, metadata: dict[str, str]) -> ArchivedObject:
        digest = hashlib.sha256(content).hexdigest()
        key = f"raw/sha256/{digest[:2]}/{digest}"
        path = self._path(key)
        created = False
        if path.exists():
            stored = path.read_bytes()
            if len(stored) != len(content) or hashlib.sha256(stored).hexdigest() != digest:
                raise IOError(f"archive corruption detected at {key}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{digest}.", dir=path.parent)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.link(temporary_name, path)
                    created = True
                except FileExistsError:
                    pass
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)
        sidecar = self._path(f"{key}.metadata.json")
        if not sidecar.exists():
            sidecar_bytes = json.dumps(
                {**metadata, "sha256": digest, "content_type": content_type, "size": len(content)},
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            self._write_once(
                sidecar,
                sidecar_bytes,
                prefix=f".{digest}.metadata.",
            )
        return ArchivedObject(key=key, sha256=digest, size=len(content), content_type=content_type, created=created)

    @staticmethod
    def _write_once(path: Path, content: bytes, *, prefix: str) -> bool:
        """Atomically publish bytes without replacing an object another worker won."""
        descriptor, temporary_name = tempfile.mkstemp(prefix=prefix, dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_name, path)
                return True
            except FileExistsError:
                return False
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    async def get(self, key: str) -> bytes:
        content = await asyncio.to_thread(self._path(key).read_bytes)
        parts = key.split("/")
        if len(parts) == 4 and parts[:2] == ["raw", "sha256"]:
            expected = parts[-1]
            if len(expected) == 64 and hashlib.sha256(content).hexdigest() != expected:
                raise IOError(f"archive corruption detected at {key}")
        return content

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._path(key).exists)
