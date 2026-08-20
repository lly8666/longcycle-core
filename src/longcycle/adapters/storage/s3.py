from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from longcycle.ports.archive import ArchivedObject


class S3ArchiveStore:
    """S3-compatible immutable archive; usable with AWS S3, R2 and MinIO."""

    def __init__(self, *, bucket: str, endpoint_url: str | None = None, client: Any | None = None) -> None:
        if client is None:
            try:
                import boto3
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError("install longcycle-core[s3] to use S3ArchiveStore") from exc
            client = boto3.client("s3", endpoint_url=endpoint_url)
        self.client = client
        self.bucket = bucket
        self.use_native_checksum = endpoint_url is None

    async def put_if_absent(
        self,
        *,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ArchivedObject:
        digest = hashlib.sha256(content).hexdigest()
        key = f"raw/sha256/{digest[:2]}/{digest}"

        def upload() -> bool:
            try:
                head = self.client.head_object(Bucket=self.bucket, Key=key)
                stored_sha = (head.get("Metadata") or {}).get("sha256")
                if head.get("ContentLength") != len(content) or stored_sha not in {None, digest}:
                    raise IOError(f"archive object does not match content address: {key}")
                return False
            except self.client.exceptions.ClientError as exc:
                if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                    raise
            request: dict[str, Any] = {
                "Bucket": self.bucket,
                "Key": key,
                "Body": content,
                "ContentType": content_type,
                "Metadata": {**(metadata or {}), "sha256": digest},
            }
            if self.use_native_checksum:
                request["ChecksumSHA256"] = __import__("base64").b64encode(bytes.fromhex(digest)).decode()
            self.client.put_object(
                **request,
            )
            return True

        created = await asyncio.to_thread(upload)
        return ArchivedObject(key=key, sha256=digest, size=len(content), content_type=content_type, created=created)

    async def get(self, key: str) -> bytes:
        response = await asyncio.to_thread(self.client.get_object, Bucket=self.bucket, Key=key)
        content = await asyncio.to_thread(response["Body"].read)
        parts = key.split("/")
        if len(parts) == 4 and parts[:2] == ["raw", "sha256"]:
            expected = parts[-1]
            if len(expected) == 64 and hashlib.sha256(content).hexdigest() != expected:
                raise IOError(f"archive corruption detected at {key}")
        return content

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
