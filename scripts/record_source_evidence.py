from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.s3 import S3ArchiveStore
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.config import Settings
from longcycle.ports.archive import ArchiveStore


def _sha256(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(character not in "0123456789abcdef" for character in normalized):
        raise argparse.ArgumentTypeError("content sha256 must be 64 lowercase hexadecimal characters")
    return normalized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Persist one excerpt as EvidenceFragment only after proving it exists in an "
            "already archived source version. No Fact or Judgment is created."
        )
    )
    parser.add_argument("--source-id", type=UUID, required=True)
    parser.add_argument("--canonical-url", required=True)
    parser.add_argument("--content-sha256", type=_sha256, required=True)
    parser.add_argument("--external-id")
    parser.add_argument("--excerpt", required=True)
    parser.add_argument("--occurrence", type=int)
    return parser


def _archive_store(settings: Settings) -> tuple[ArchiveStore, str]:
    if settings.blob_backend == "filesystem":
        root = settings.blob_root.resolve()
        return FileSystemArchiveStore(root), f"filesystem:{root}"
    if settings.s3_bucket is None:
        raise RuntimeError("LONGCYCLE_S3_BUCKET is required for the s3 blob backend")
    return (
        S3ArchiveStore(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
        ),
        settings.s3_bucket,
    )


async def _run(args: argparse.Namespace) -> dict[str, object]:
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError(
            "LONGCYCLE_DATABASE_URL is required because evidence must reference a persisted "
            "SourceDocument, not an untracked URL"
        )
    if args.occurrence is not None and args.occurrence < 0:
        raise ValueError("--occurrence must be non-negative")

    archive, bucket_name = _archive_store(settings)
    repository = PostgresResearchRepository(settings.database_url, bucket_name=bucket_name)
    try:
        document = await repository.document_by_hash(
            args.source_id,
            args.canonical_url,
            args.content_sha256,
            args.external_id,
        )
        if document is None:
            raise LookupError(
                "archived SourceDocument version not found; run archive_source_url.py first "
                "and use its canonical URL and content digest"
            )

        result = await ArchivedEvidenceRecorder(
            repository=repository,
            archive=archive,
        ).record_excerpt(
            document=document,
            excerpt=args.excerpt,
            occurrence=args.occurrence,
        )
        fragment = result.fragment
        return {
            "document_id": str(document.id),
            "canonical_url": document.canonical_url,
            "content_sha256": document.content_sha256,
            "published_at": document.published_at.isoformat() if document.published_at else None,
            "first_known_at": document.first_known_at.isoformat(),
            "evidence_fragment_id": str(fragment.id),
            "evidence_locator": fragment.locator,
            "fragment_sha256": fragment.fragment_sha256,
            "evidence_created": True,
            "assertions_created": False,
            "judgments_created": False,
        }
    finally:
        await repository.close()


def main() -> None:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        raise SystemExit(1) from exc
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
