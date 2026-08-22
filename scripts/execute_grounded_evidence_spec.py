from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from longcycle.adapters.parsers import HtmlVisibleTextParser, PdfTextParser
from longcycle.adapters.sources.http import HttpDocumentSource
from longcycle.adapters.sources.materialized import MaterializedDocumentSource
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.postgres import PostgresResearchRepository
from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.adapters.storage.s3 import S3ArchiveStore
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.application.parsing import ArtifactPipeline
from longcycle.application.source_archive import DocumentArchiver
from longcycle.application.source_authority import (
    parse_source_authority_profiles,
    validate_redistributed_document_provenance,
)
from longcycle.application.source_registration import (
    build_http_source_definition,
    build_materialized_source_definition,
)
from longcycle.config import Settings
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.memory import SourceAuthorityProfile
from longcycle.domain.models import (
    DiscoveryItem,
    DocumentArtifact,
    SourceDefinition,
    SourceDocument,
)
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.parser import DocumentParser
from longcycle.ports.source import FetchContext, SourcePlugin


SCHEMA_VERSION_V1 = "longcycle-grounded-evidence-spec/v1"
SCHEMA_VERSION_V2 = "longcycle-grounded-evidence-spec/v2"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION_V1, SCHEMA_VERSION_V2})


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one bounded grounded-evidence specification through Longcycle's normal "
            "source registration, immutable archive, parser-artifact and EvidenceFragment path. "
            "The executor never promotes FactAssertions or Judgments."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--material-root",
        type=Path,
        help=(
            "Root containing externally acquired source bytes referenced by v2 materialized "
            "documents. Paths inside the spec must remain relative to this root."
        ),
    )
    return parser


def _aware_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"datetime must include timezone: {value}")
    return parsed


def _load_spec(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("grounded evidence spec must be a JSON object")
    schema_version = payload.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"unsupported grounded evidence spec schema: {schema_version!r}")
    sources = payload.get("sources")
    documents = payload.get("documents")
    fragments = payload.get("fragments")
    acceptance = payload.get("acceptance")
    if not isinstance(sources, list) or not sources:
        raise ValueError("grounded evidence spec must define sources")
    if not isinstance(documents, list) or not documents:
        raise ValueError("grounded evidence spec must define documents")
    if not isinstance(fragments, list) or not fragments:
        raise ValueError("grounded evidence spec must define fragments")
    if not isinstance(acceptance, dict):
        raise ValueError("grounded evidence spec must define acceptance")
    if acceptance.get("required_documents") != len(documents):
        raise ValueError("acceptance.required_documents does not match documents")
    if acceptance.get("required_fragments") != len(fragments):
        raise ValueError("acceptance.required_fragments does not match fragments")
    if acceptance.get("facts_created") != 0 or acceptance.get("judgments_created") != 0:
        raise ValueError("grounded evidence executor only supports zero Fact/Judgment promotion")

    source_transport: dict[str, str] = {}
    for row in sources:
        if not isinstance(row, dict):
            raise ValueError("grounded evidence source specs must be objects")
        key = row.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("source key must be a non-empty string")
        if key in source_transport:
            raise ValueError(f"duplicate source key: {key}")
        transport = str(row.get("transport", "http"))
        if transport not in {"http", "materialized"}:
            raise ValueError(f"source {key} has unsupported transport: {transport}")
        if transport == "materialized" and schema_version != SCHEMA_VERSION_V2:
            raise ValueError("materialized source transport requires grounded evidence spec v2")
        profiles = parse_source_authority_profiles(row.get("authority_profiles"))
        if profiles and schema_version != SCHEMA_VERSION_V2:
            raise ValueError("source authority profiles require grounded evidence spec v2")
        allowed_domains = row.get("allowed_domains")
        if transport == "http" and (
            not isinstance(allowed_domains, list)
            or not all(isinstance(item, str) for item in allowed_domains)
        ):
            raise ValueError(f"source {key} allowed_domains must be a string list")
        source_transport[key] = transport

    seen_document_keys: set[str] = set()
    for row in documents:
        if not isinstance(row, dict):
            raise ValueError("grounded evidence document specs must be objects")
        key = row.get("key")
        source_key = row.get("source_key")
        if not isinstance(key, str) or not key:
            raise ValueError("document key must be a non-empty string")
        if key in seen_document_keys:
            raise ValueError(f"duplicate document key: {key}")
        seen_document_keys.add(key)
        if not isinstance(source_key, str) or source_key not in source_transport:
            raise ValueError(f"document {key} references unknown source {source_key!r}")
        raw_digest = row.get("expected_sha256")
        text_digest = row.get("expected_visible_text_sha256")
        raw_ok = isinstance(raw_digest, str) and bool(raw_digest)
        text_ok = isinstance(text_digest, str) and bool(text_digest)
        if not raw_ok and not text_ok:
            raise ValueError(f"document {key!r} must pin raw SHA or visible-text artifact SHA")
        if source_transport[source_key] == "materialized":
            material_path = row.get("material_path")
            content_type = row.get("content_type")
            if not raw_ok:
                raise ValueError(f"materialized document {key} must pin expected_sha256")
            if not isinstance(material_path, str) or not material_path.strip():
                raise ValueError(f"materialized document {key} must define material_path")
            if not isinstance(content_type, str) or not content_type.strip():
                raise ValueError(f"materialized document {key} must define content_type")
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
    return {
        "fact_assertions": int(fact_row["n"]),
        "judgment_assertions": int(judgment_row["n"]),
    }


async def _register_sources(
    *,
    registry: PostgresSourceRegistry,
    source_specs: list[dict[str, Any]],
) -> tuple[
    dict[str, SourceDefinition],
    dict[str, tuple[SourceAuthorityProfile, ...]],
]:
    registered: dict[str, SourceDefinition] = {}
    profiles_by_key: dict[str, tuple[SourceAuthorityProfile, ...]] = {}
    for row in source_specs:
        key = row.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("source key must be a non-empty string")
        transport = str(row.get("transport", "http"))
        profiles = parse_source_authority_profiles(row.get("authority_profiles"))
        if transport == "http":
            allowed_domains = row.get("allowed_domains")
            if not isinstance(allowed_domains, list) or not all(
                isinstance(item, str) for item in allowed_domains
            ):
                raise ValueError(f"source {key} allowed_domains must be a string list")
            source = build_http_source_definition(
                name=str(row["name"]),
                publisher_domain=str(row["publisher_domain"]),
                kind=SourceKind(str(row["kind"])),
                quality_grade=QualityGrade(str(row["quality_grade"])),
                allowed_domains=allowed_domains,
            )
        elif transport == "materialized":
            source = build_materialized_source_definition(
                name=str(row["name"]),
                publisher_domain=str(row["publisher_domain"]),
                kind=SourceKind(str(row["kind"])),
                quality_grade=QualityGrade(str(row["quality_grade"])),
            )
        else:
            raise ValueError(f"source {key} has unsupported transport: {transport}")
        registered[key] = await registry.register(source, authority_profiles=profiles)
        profiles_by_key[key] = profiles
    return registered, profiles_by_key


def _source_plugin(
    *,
    source: SourceDefinition,
    material_root: Path | None,
) -> SourcePlugin:
    if source.plugin == "http_document":
        return HttpDocumentSource(source)
    if source.plugin == "materialized_file":
        if material_root is None:
            raise ValueError(
                "grounded evidence spec uses materialized source transport but --material-root "
                "was not supplied"
            )
        return MaterializedDocumentSource(source, material_root=material_root)
    raise ValueError(f"unsupported persisted source plugin: {source.plugin}")


async def _archive_documents(
    *,
    repository: PostgresResearchRepository,
    archive: ArchiveStore,
    sources: dict[str, SourceDefinition],
    authority_profiles: dict[str, tuple[SourceAuthorityProfile, ...]],
    document_specs: list[dict[str, Any]],
    task_id: str,
    material_root: Path | None,
) -> dict[str, SourceDocument]:
    archived: dict[str, SourceDocument] = {}
    archiver = DocumentArchiver(repository=repository, archive=archive)
    for row in document_specs:
        key = row.get("key")
        source_key = row.get("source_key")
        if not isinstance(key, str) or not key:
            raise ValueError("document key must be a non-empty string")
        if not isinstance(source_key, str) or source_key not in sources:
            raise ValueError(f"document {key} references unknown source {source_key!r}")
        persisted_source = await repository.get_source(sources[source_key].id)
        retrieval_url = str(row["retrieval_url"])
        retrieval_provenance = row.get("retrieval_provenance") or {}
        validate_redistributed_document_provenance(
            source=persisted_source,
            retrieval_url=retrieval_url,
            retrieval_provenance=retrieval_provenance,
            authority_profiles=authority_profiles[source_key],
        )
        plugin = _source_plugin(source=persisted_source, material_root=material_root)
        metadata = {
            "evidence_task_id": task_id,
            "vintage_id": row.get("vintage_id"),
            "original_source_url": row.get("original_source_url"),
            "retrieval_provenance": retrieval_provenance,
            "transport_plugin": persisted_source.plugin,
        }
        if persisted_source.plugin == "materialized_file":
            metadata.update(
                {
                    "material_path": row.get("material_path"),
                    "material_expected_sha256": row.get("expected_sha256"),
                    "material_content_type": row.get("content_type"),
                }
            )
        item = DiscoveryItem(
            source_id=persisted_source.id,
            external_id=str(row["external_id"]),
            url=retrieval_url,
            title_hint=str(row["title"]),
            published_at_hint=_aware_datetime(row.get("published_at")),
            discovered_at=_aware_datetime(row.get("first_known_at"))
            or datetime.now().astimezone(),
            metadata=metadata,
        )
        result = await archiver.archive_document(
            plugin=plugin,
            item=item,
            fetch_context=FetchContext(
                source=persisted_source,
                maximum_bytes=50 * 1024 * 1024,
            ),
        )
        document = result.document
        expected_raw = row.get("expected_sha256")
        if isinstance(expected_raw, str) and expected_raw:
            if document.content_sha256 != expected_raw:
                raise ValueError(
                    f"document {key} digest mismatch: expected {expected_raw}, "
                    f"got {document.content_sha256}"
                )
        archived[key] = document
    return archived


async def _artifact_for_document(
    *,
    repository: PostgresResearchRepository,
    archive: ArchiveStore,
    document: SourceDocument,
    parser: DocumentParser,
    expected_sha256: str | None = None,
) -> DocumentArtifact:
    source_bytes = await archive.get(document.blob_key)
    parsed = await ArtifactPipeline(repository=repository, archive=archive).parse(
        document=document,
        content=source_bytes,
        parser=parser,
    )
    if len(parsed) != 1:
        raise RuntimeError(
            f"expected one {parser.parser_name} artifact for document {document.id}"
        )
    artifact = parsed[0]
    if expected_sha256 is not None and artifact.content_sha256 != expected_sha256:
        raise ValueError(
            f"document {document.id} parser artifact digest mismatch: "
            f"expected {expected_sha256}, got {artifact.content_sha256}"
        )
    return artifact


async def _record_fragments(
    *,
    repository: PostgresResearchRepository,
    archive: ArchiveStore,
    documents: dict[str, SourceDocument],
    document_specs: list[dict[str, Any]],
    fragment_specs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, DocumentArtifact]]:
    recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)
    artifacts: dict[str, DocumentArtifact] = {}
    fragment_results: list[dict[str, Any]] = []
    spec_by_key = {str(row["key"]): row for row in document_specs}

    for row in fragment_specs:
        fragment_key = row.get("fragment_key")
        document_key = row.get("document_key")
        if not isinstance(fragment_key, str) or not fragment_key:
            raise ValueError("fragment_key must be a non-empty string")
        if not isinstance(document_key, str) or document_key not in documents:
            raise ValueError(f"fragment {fragment_key} references unknown document")
        document = documents[document_key]
        document_spec = spec_by_key[document_key]
        excerpt = str(row["excerpt"])
        claim_context = row.get("claim_context")
        if not isinstance(claim_context, dict) or not claim_context:
            raise ValueError(f"fragment {fragment_key} must carry non-empty claim_context")

        media_type = document.content_type.split(";", 1)[0].strip().lower()
        expected_visible = document_spec.get("expected_visible_text_sha256")
        if media_type == "application/pdf":
            page = row.get("page")
            if not isinstance(page, int) or page < 1:
                raise ValueError(f"PDF fragment {fragment_key} must define one-based page")
            artifact = artifacts.get(document_key)
            if artifact is None:
                artifact = await _artifact_for_document(
                    repository=repository,
                    archive=archive,
                    document=document,
                    parser=PdfTextParser(),
                )
                artifacts[document_key] = artifact
            recorded = await recorder.record_pdf_page_excerpt(
                document=document,
                artifact=artifact,
                page=page,
                excerpt=excerpt,
                occurrence=row.get("occurrence"),
                claim_context=claim_context,
            )
        elif media_type in {"text/html", "application/xhtml+xml"} and isinstance(
            expected_visible, str
        ):
            if row.get("page") is not None:
                raise ValueError(f"HTML fragment {fragment_key} cannot define page")
            artifact = artifacts.get(document_key)
            if artifact is None:
                artifact = await _artifact_for_document(
                    repository=repository,
                    archive=archive,
                    document=document,
                    parser=HtmlVisibleTextParser(),
                    expected_sha256=expected_visible,
                )
                artifacts[document_key] = artifact
            recorded = await recorder.record_html_visible_text_excerpt(
                document=document,
                artifact=artifact,
                excerpt=excerpt,
                occurrence=row.get("occurrence"),
                claim_context=claim_context,
            )
        else:
            if row.get("page") is not None:
                raise ValueError(f"non-PDF fragment {fragment_key} cannot define page")
            recorded = await recorder.record_excerpt(
                document=document,
                excerpt=excerpt,
                occurrence=row.get("occurrence"),
                claim_context=claim_context,
            )

        fragment_results.append(
            {
                "fragment_key": fragment_key,
                "evidence_fragment_id": str(recorded.fragment.id),
                "document_id": str(recorded.fragment.document_id),
                "artifact_id": (
                    str(recorded.fragment.artifact_id)
                    if recorded.fragment.artifact_id is not None
                    else None
                ),
                "locator": recorded.fragment.locator,
                "fragment_sha256": recorded.fragment.fragment_sha256,
                "claim_context": claim_context,
            }
        )

    return fragment_results, artifacts


async def _verify_persistence(
    *,
    repository: PostgresResearchRepository,
    documents: dict[str, SourceDocument],
    fragments: list[dict[str, Any]],
    before_counts: dict[str, int],
    expected_document_count: int,
    expected_fragment_count: int,
) -> dict[str, Any]:
    document_ids = [str(item.id) for item in documents.values()]
    fragment_ids = [str(row["evidence_fragment_id"]) for row in fragments]
    async with repository.connection() as connection:
        document_row = await (
            await connection.execute(
                "SELECT count(*) AS n FROM evidence.document_versions WHERE id = ANY(%s::uuid[])",
                (document_ids,),
            )
        ).fetchone()
        fragment_row = await (
            await connection.execute(
                "SELECT count(*) AS n FROM evidence.evidence_fragments WHERE id = ANY(%s::uuid[])",
                (fragment_ids,),
            )
        ).fetchone()
    after_counts = await _research_row_counts(repository)
    persisted_documents = int(document_row["n"]) if document_row is not None else 0
    persisted_fragments = int(fragment_row["n"]) if fragment_row is not None else 0
    fact_delta = after_counts["fact_assertions"] - before_counts["fact_assertions"]
    judgment_delta = after_counts["judgment_assertions"] - before_counts["judgment_assertions"]
    if persisted_documents != expected_document_count:
        raise ValueError(
            f"expected {expected_document_count} persisted document versions, "
            f"got {persisted_documents}"
        )
    if persisted_fragments != expected_fragment_count:
        raise ValueError(
            f"expected {expected_fragment_count} persisted evidence fragments, "
            f"got {persisted_fragments}"
        )
    if fact_delta != 0 or judgment_delta != 0:
        raise ValueError(
            "grounded evidence execution must not promote FactAssertions or Judgments: "
            f"fact_delta={fact_delta}, judgment_delta={judgment_delta}"
        )
    return {
        "persisted_document_versions": persisted_documents,
        "persisted_evidence_fragments": persisted_fragments,
        "fact_assertions_created": fact_delta,
        "judgment_assertions_created": judgment_delta,
    }


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    spec = _load_spec(args.spec)
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required for grounded evidence execution")
    archive, bucket_name = _archive_store(settings)
    repository = PostgresResearchRepository(settings.database_url, bucket_name=bucket_name)
    registry = PostgresSourceRegistry(settings.database_url)
    try:
        before_counts = await _research_row_counts(repository)
        source_specs = spec["sources"]
        document_specs = spec["documents"]
        fragment_specs = spec["fragments"]
        if (
            not isinstance(source_specs, list)
            or not isinstance(document_specs, list)
            or not isinstance(fragment_specs, list)
        ):
            raise ValueError("spec source/document/fragment collections must be lists")
        sources, authority_profiles = await _register_sources(
            registry=registry,
            source_specs=source_specs,
        )
        documents = await _archive_documents(
            repository=repository,
            archive=archive,
            sources=sources,
            authority_profiles=authority_profiles,
            document_specs=document_specs,
            task_id=str(spec["task_id"]),
            material_root=args.material_root,
        )
        fragments, artifacts = await _record_fragments(
            repository=repository,
            archive=archive,
            documents=documents,
            document_specs=document_specs,
            fragment_specs=fragment_specs,
        )
        acceptance = spec["acceptance"]
        if not isinstance(acceptance, dict):
            raise ValueError("spec acceptance must be an object")
        persistence = await _verify_persistence(
            repository=repository,
            documents=documents,
            fragments=fragments,
            before_counts=before_counts,
            expected_document_count=int(acceptance["required_documents"]),
            expected_fragment_count=int(acceptance["required_fragments"]),
        )
        document_output = []
        by_key = {str(row["key"]): row for row in document_specs}
        for key, document in documents.items():
            row = by_key[key]
            document_output.append(
                {
                    "document_key": key,
                    "document_id": str(document.id),
                    "source_id": str(document.source_id),
                    "transport_plugin": document.metadata.get("transport_plugin"),
                    "canonical_retrieval_url": document.canonical_url,
                    "original_source_url": row.get("original_source_url"),
                    "content_sha256": document.content_sha256,
                    "blob_key": document.blob_key,
                    "byte_length": document.byte_length,
                    "content_type": document.content_type,
                    "published_at": (
                        document.published_at.isoformat() if document.published_at else None
                    ),
                    "first_known_at": document.first_known_at.isoformat(),
                    "retrieval_provenance": row.get("retrieval_provenance") or {},
                    "source_authority_profiles": [
                        profile.model_dump(mode="json")
                        for profile in authority_profiles[str(row["source_key"])]
                    ],
                    "expected_visible_text_sha256": row.get("expected_visible_text_sha256"),
                }
            )
        return {
            "schema_version": "longcycle-grounded-evidence-execution/v1",
            "spec_schema_version": spec["schema_version"],
            "task_id": spec["task_id"],
            "documents": document_output,
            "artifacts": [
                {
                    "document_key": key,
                    "artifact_id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "artifact_sha256": artifact.content_sha256,
                    "artifact_blob_key": artifact.blob_key,
                    "parser_name": artifact.producer_name,
                    "parser_version": artifact.producer_version,
                }
                for key, artifact in artifacts.items()
            ],
            "fragments": fragments,
            "acceptance": persistence,
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
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(1) from exc
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
