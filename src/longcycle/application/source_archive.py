from __future__ import annotations

from dataclasses import dataclass

from longcycle.domain.models import DiscoveryItem, SourceDefinition, SourceDocument
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.repository import ResearchRepository
from longcycle.ports.source import FetchContext, SourcePlugin


@dataclass(frozen=True, slots=True)
class ArchivedDocumentResult:
    """Result of source-first archival before any model extraction or assertion work."""

    document: SourceDocument
    was_new_document: bool


class DocumentArchiver:
    """Fetch and persist one immutable source version without extracting claims.

    This is the shared source-first boundary for both the full collection pipeline and
    claim-scoped historical evidence work. Archival never creates EvidenceFragments,
    FactAssertions or Judgments on its own.
    """

    def __init__(
        self,
        *,
        repository: ResearchRepository,
        archive: ArchiveStore,
    ) -> None:
        self.repository = repository
        self.archive = archive

    async def archive_document(
        self,
        *,
        plugin: SourcePlugin,
        item: DiscoveryItem,
        fetch_context: FetchContext,
    ) -> ArchivedDocumentResult:
        if item.source_id != fetch_context.source.id:
            raise ValueError("discovery item and fetch context use different sources")

        source = await self.repository.get_source(item.source_id)
        self._validate_source_boundary(
            source=source,
            plugin=plugin,
            fetch_context=fetch_context,
        )

        payload = await plugin.fetch(item, fetch_context)
        if len(payload.content) > fetch_context.maximum_bytes:
            raise ValueError("source payload exceeds configured maximum_bytes")

        archived = await self.archive.put_if_absent(
            content=payload.content,
            content_type=payload.content_type,
            metadata={},
        )
        if (
            archived.sha256 != payload.sha256
            or archived.size != len(payload.content)
            or archived.content_type != payload.content_type
            or not archived.key
        ):
            raise ValueError("archive receipt does not match the fetched payload")

        existing_document = await self.repository.document_by_hash(
            item.source_id,
            payload.canonical_url,
            payload.sha256,
            item.external_id,
        )
        document = SourceDocument.from_payload(
            source_id=item.source_id,
            payload=payload,
            blob_key=archived.key,
            external_id=item.external_id,
            title=item.title_hint,
            published_at=item.published_at_hint,
            first_known_at=item.discovered_at,
            metadata={**item.metadata, "requested_url": item.url},
        )
        document = await self.repository.save_document(document)
        return ArchivedDocumentResult(
            document=document,
            was_new_document=existing_document is None,
        )

    @staticmethod
    def _validate_source_boundary(
        *,
        source: SourceDefinition,
        plugin: SourcePlugin,
        fetch_context: FetchContext,
    ) -> None:
        if not source.enabled:
            raise ValueError(f"source is disabled: {source.id}")
        if source.plugin != plugin.plugin_name:
            raise ValueError("persisted source plugin does not match the supplied plugin")
        if fetch_context.source != source:
            raise ValueError("fetch context must use the persisted source definition")
        plugin_definition = getattr(plugin, "definition", None)
        if isinstance(plugin_definition, SourceDefinition) and plugin_definition != source:
            raise ValueError("plugin must be constructed from the persisted source definition")
