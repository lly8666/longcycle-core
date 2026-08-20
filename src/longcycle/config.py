from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str | None
    blob_backend: str
    blob_root: Path
    s3_bucket: str | None
    s3_endpoint_url: str | None
    worker_id: str
    log_level: str
    extraction_schema_version: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("LONGCYCLE_DATABASE_URL"),
            blob_backend=os.getenv("LONGCYCLE_BLOB_BACKEND", "filesystem"),
            blob_root=Path(os.getenv("LONGCYCLE_BLOB_ROOT", ".longcycle/blobs")),
            s3_bucket=os.getenv("LONGCYCLE_S3_BUCKET"),
            s3_endpoint_url=os.getenv("LONGCYCLE_S3_ENDPOINT_URL"),
            worker_id=os.getenv("LONGCYCLE_WORKER_ID", "local-worker"),
            log_level=os.getenv("LONGCYCLE_LOG_LEVEL", "INFO"),
            extraction_schema_version=os.getenv("LONGCYCLE_EXTRACTION_SCHEMA", "fact-v1"),
        )

    def validate(self) -> None:
        if self.blob_backend not in {"filesystem", "s3"}:
            raise ValueError("LONGCYCLE_BLOB_BACKEND must be filesystem or s3")
        if self.blob_backend == "s3" and not self.s3_bucket:
            raise ValueError("LONGCYCLE_S3_BUCKET is required for the s3 blob backend")
