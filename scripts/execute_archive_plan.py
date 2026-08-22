from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from longcycle.adapters.sources.http import HttpDocumentSource
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.adapters.storage.s3 import S3ArchiveStore
from longcycle.application.source_archive import DocumentArchiver
from longcycle.application.source_registration import build_http_source_definition
from longcycle.config import Settings
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import DiscoveryItem, SourceDocument
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.source import FetchContext


SCHEMA_VERSION = "longcycle-evidence-archive-plan/v1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one bounded evidence archive plan through Longcycle's normal source "
            "registration and immutable archive path. No EvidenceFragment, Fact or Judgment "
            "is created."
        )
    )
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def _aware_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"datetime must include timezone: {value}")
    return parsed


def _published_at(vintage: dict[str, Any]) -> datetime | None:
    accepted = vintage.get("sec_accepted_at")
    if isinstance(accepted, str):
        return _aware_datetime(accepted)
    source_date = vintage.get("source_date")
    if isinstance(source_date, str):
        parsed = datetime.fromisoformat(source_date)
        return parsed.replace(tzinfo=UTC)
    return None


def _load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("archive plan must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported archive plan schema: {payload.get('schema_version')!r}")
    source_identity = payload.get("source_identity")
    vintages = payload.get("required_vintages")
    acceptance = payload.get("trajectory_acceptance")
    if not isinstance(source_identity, dict):
        raise ValueError("archive plan must define source_identity")
    if not isinstance(vintages, list) or not vintages:
        raise ValueError("archive plan must define required_vintages")
    if not isinstance(acceptance, dict):
        raise ValueError("archive plan must define trajectory_acceptance")
    expected = acceptance.get("minimum_required_archived_vintages")
    if not isinstance(expected, int) or expected != len(vintages):
        raise ValueError("archive-plan vintage count does not match acceptance")
    return payload


def _archive_store(settings: Settings) -> tuple[ArchiveStore, str]:
    if settings.blob_backend == "filesystem":
        root = settings.blob_root.resolve()
        return FileSystemArchiveStore(root), f"filesystem:{root}"
    if settings.s3_bucket is None:
        raise RuntimeError("LONGCYCLE_S3_BUCKET is required for the s3 blob backend")
    return (
        S3ArchiveStore(bucket=settings.s3_bucket, endpoint_url=settings.s3_endpoint_url),
        settings.s3_bucket,
    )


async def _research_row_counts(repository: PostgresResearchRepository) -> dict[str, int]:
    async with repository.connection() as connection:
        fact_row = await (
            await connection.execute("SELECT count(*) AS n FROM research.fact_assertions")
        ).fetchone()
        judgment_row = await (
            await connection.execute("SELECT count(*) AS n FROM research.judgment_assertions")
        ).fetchone()
    if fact_row is None or judgment_row is None:
        raise RuntimeError("research count query returned no row")
    return {"fact_assertions": int(fact_row["n"]), "judgment_assertions": int(judgment_row["n"])}


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    plan = _load_plan(args.plan)
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required for archive-plan execution")

    archive, bucket_name = _archive_store(settings)
    repository = PostgresResearchRepository(settings.database_url, bucket_name=bucket_name)
    registry = PostgresSourceRegistry(settings.database_url)
    try:
        before_counts = await _research_row_counts(repository)
        source_identity = plan["source_identity"]
        allowed_domains = source_identity.get("allowed_retrieval_domains")
        if not isinstance(allowed_domains, list) or not all(
            isinstance(item, str) for item in allowed_domains
        ):
            raise ValueError("source_identity.allowed_retrieval_domains must be a string list")
        source = build_http_source_definition(
            name=str(source_identity["publisher_name"]),
            publisher_domain=str(source_identity["publisher_domain"]),
            kind=SourceKind.COMPANY,
            quality_grade=QualityGrade.A,
            allowed_domains=allowed_domains,
        )
        source = await registry.register(source)
        persisted_source = await repository.get_source(source.id)
        plugin = HttpDocumentSource(persisted_source)
        archiver = DocumentArchiver(repository=repository, archive=archive)

        archived: list[dict[str, Any]] = []
        for vintage in plan["required_vintages"]:
            if not isinstance(vintage, dict):
                raise ValueError("required_vintages entries must be objects")
            vintage_id = vintage.get("vintage_id")
            requested_url = vintage.get("requested_url")
            known_time = vintage.get("known_time_candidate")
            if not isinstance(vintage_id, str) or not vintage_id:
                raise ValueError("vintage_id must be a non-empty string")
            if not isinstance(requested_url, str) or not requested_url:
                raise ValueError(f"{vintage_id}: requested_url must be a non-empty string")
            first_known_at = _aware_datetime(known_time if isinstance(known_time, str) else None)
            if first_known_at is None:
                raise ValueError(f"{vintage_id}: known_time_candidate is required")
            metadata = {
                "ingest_mode": "archive_plan",
                "evidence_task_id": plan["task_id"],
                "vintage_id": vintage_id,
                "epistemic_role": vintage.get("role"),
                "source_type": vintage.get("source_type"),
                "retrieval_transport": "sec" if "sec.gov" in requested_url else "publisher_direct",
                "authority_note": source_identity.get("authority_note"),
            }
            item = DiscoveryItem(
                source_id=persisted_source.id,
                external_id=f"{plan['task_id']}::{vintage_id}",
                url=requested_url,
                title_hint=vintage_id,
                published_at_hint=_published_at(vintage),
                discovered_at=first_known_at,
                metadata=metadata,
            )
            result = await archiver.archive_document(
                plugin=plugin,
                item=item,
                fetch_context=FetchContext(source=persisted_source, maximum_bytes=50 * 1024 * 1024),
            )
            document: SourceDocument = result.document
            archived.append(
                {
                    "vintage_id": vintage_id,
                    "role": vintage.get("role"),
                    "document_id": str(document.id),
                    "source_id": str(document.source_id),
                    "canonical_retrieval_url": document.canonical_url,
                    "content_sha256": document.content_sha256,
                    "blob_key": document.blob_key,
                    "byte_length": document.byte_length,
                    "content_type": document.content_type,
                    "published_at": document.published_at.isoformat() if document.published_at else None,
                    "first_known_at": document.first_known_at.isoformat(),
                    "was_new_document": result.was_new_document,
                }
            )

        after_counts = await _research_row_counts(repository)
        fact_delta = after_counts["fact_assertions"] - before_counts["fact_assertions"]
        judgment_delta = after_counts["judgment_assertions"] - before_counts["judgment_assertions"]
        if fact_delta != 0 or judgment_delta != 0:
            raise ValueError(
                "archive-plan execution must not promote FactAssertions or Judgments: "
                f"fact_delta={fact_delta}, judgment_delta={judgment_delta}"
            )
        expected = int(plan["trajectory_acceptance"]["minimum_required_archived_vintages"])
        if len(archived) != expected:
            raise ValueError(f"expected {expected} archived vintages, got {len(archived)}")
        return {
            "schema_version": "longcycle-evidence-archive-execution/v1",
            "plan_schema_version": plan["schema_version"],
            "task_id": plan["task_id"],
            "source": {
                "source_id": str(persisted_source.id),
                "publisher_domain": persisted_source.publisher_domain,
                "allowed_domains": persisted_source.config.get("allowed_domains", []),
            },
            "documents": archived,
            "acceptance": {
                "archived_vintages": len(archived),
                "fact_assertions_created": fact_delta,
                "judgment_assertions_created": judgment_delta,
            },
        }
    finally:
        await registry.close()
        await repository.close()


def main() -> None:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
        payload = {"ok": True, "result": result}
    except Exception as exc:
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(1) from exc
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
