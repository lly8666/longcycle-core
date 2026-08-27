from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.source_archive import DocumentArchiver
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition, stable_uuid
from longcycle.ports.source import FetchContext


class FixtureSource:
    plugin_name = "fixture_source"

    def __init__(self, definition: SourceDefinition, payload: RawPayload) -> None:
        self.definition = definition
        self.payload = payload
        self.fetch_count = 0

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload:
        del item, context
        self.fetch_count += 1
        return self.payload


class DocumentArchiverTest(unittest.IsolatedAsyncioTestCase):
    async def test_archive_only_path_persists_source_version_without_extraction(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "archive-fixture"),
            name="archive-fixture",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        published_at = datetime(2018, 12, 18, 8, 0, tzinfo=UTC)
        discovered_at = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)
        retrieved_at = datetime(2026, 8, 21, 14, 5, tzinfo=UTC)
        payload = RawPayload(
            content=b"historical primary source",
            content_type="text/plain",
            canonical_url="https://example.com/history/kwinana",
            retrieved_at=retrieved_at,
        )
        item = DiscoveryItem(
            source_id=source.id,
            external_id="kwinana-2018-12-18",
            url="https://example.com/history/kwinana?requested=1",
            title_hint="Kwinana commissioning update",
            published_at_hint=published_at,
            discovered_at=discovered_at,
            metadata={"evidence_task_id": "EVT-001"},
        )

        with tempfile.TemporaryDirectory(prefix="longcycle-archive-only-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            plugin = FixtureSource(source, payload)
            archiver = DocumentArchiver(repository=repository, archive=archive)

            result = await archiver.archive_document(
                plugin=plugin,
                item=item,
                fetch_context=FetchContext(source=source),
            )

            self.assertTrue(result.was_new_document)
            self.assertEqual(result.document.canonical_url, payload.canonical_url)
            self.assertEqual(result.document.published_at, published_at)
            self.assertEqual(result.document.first_known_at, discovered_at)
            self.assertEqual(result.document.retrieved_at, retrieved_at)
            self.assertEqual(result.document.metadata["requested_url"], item.url)
            self.assertEqual(result.document.metadata["evidence_task_id"], "EVT-001")
            self.assertEqual(
                await archive.get(result.document.blob_key),
                payload.content,
            )
            self.assertEqual(repository.evidence, {})
            self.assertEqual(repository.extractions, {})
            self.assertEqual(repository.assertions, {})

    async def test_repeat_archive_reuses_document_and_preserves_earliest_known_time(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "archive-repeat"),
            name="archive-repeat",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        payload = RawPayload(
            content=b"same bytes",
            content_type="text/plain",
            canonical_url="https://example.com/source",
            retrieved_at=datetime(2026, 8, 21, 14, 5, tzinfo=UTC),
        )
        later = DiscoveryItem(
            source_id=source.id,
            external_id="source-v1",
            url=payload.canonical_url,
            discovered_at=datetime(2026, 8, 21, 14, 0, tzinfo=UTC),
        )
        earlier = later.model_copy(
            update={"discovered_at": datetime(2026, 8, 20, 9, 0, tzinfo=UTC)}
        )

        with tempfile.TemporaryDirectory(prefix="longcycle-archive-repeat-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            plugin = FixtureSource(source, payload)
            archiver = DocumentArchiver(repository=repository, archive=archive)

            first = await archiver.archive_document(
                plugin=plugin,
                item=later,
                fetch_context=FetchContext(source=source),
            )
            second = await archiver.archive_document(
                plugin=plugin,
                item=earlier,
                fetch_context=FetchContext(source=source),
            )

            self.assertTrue(first.was_new_document)
            self.assertFalse(second.was_new_document)
            self.assertEqual(first.document.id, second.document.id)
            self.assertEqual(second.document.first_known_at, earlier.discovered_at)
            self.assertEqual(len(repository.documents), 1)

    async def test_archive_boundary_rejects_mismatched_source_context(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "archive-source-a"),
            name="archive-source-a",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        other = source.model_copy(
            update={"id": stable_uuid("source", "archive-source-b"), "name": "archive-source-b"}
        )
        payload = RawPayload(
            content=b"payload",
            content_type="text/plain",
            canonical_url="https://example.com/source",
        )
        item = DiscoveryItem(source_id=source.id, url=payload.canonical_url)

        with tempfile.TemporaryDirectory(prefix="longcycle-archive-boundary-") as temporary:
            repository = InMemoryResearchRepository([source, other])
            archiver = DocumentArchiver(
                repository=repository,
                archive=FileSystemArchiveStore(Path(temporary)),
            )
            plugin = FixtureSource(source, payload)

            with self.assertRaisesRegex(ValueError, "different sources"):
                await archiver.archive_document(
                    plugin=plugin,
                    item=item,
                    fetch_context=FetchContext(source=other),
                )

            self.assertEqual(plugin.fetch_count, 0)


if __name__ == "__main__":
    unittest.main()
