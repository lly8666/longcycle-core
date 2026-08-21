from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.application.source_archive import DocumentArchiver
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import DiscoveryItem, RawPayload, SourceDefinition, stable_uuid
from longcycle.ports.source import FetchContext


class FixtureSource:
    plugin_name = "fixture_source"

    def __init__(self, definition: SourceDefinition, payload: RawPayload) -> None:
        self.definition = definition
        self.payload = payload

    async def fetch(self, item: DiscoveryItem, context: FetchContext) -> RawPayload:
        del item, context
        return self.payload


class ArchivedEvidenceRecorderTest(unittest.IsolatedAsyncioTestCase):
    async def _archive_html(
        self,
        *,
        repository: InMemoryResearchRepository,
        archive: FileSystemArchiveStore,
        source: SourceDefinition,
        html: str,
    ):
        payload = RawPayload(
            content=html.encode("utf-8"),
            content_type="text/html; charset=utf-8",
            canonical_url="https://example.com/primary/kwinana",
            retrieved_at=datetime(2026, 8, 21, 15, 0, tzinfo=UTC),
        )
        item = DiscoveryItem(
            source_id=source.id,
            external_id="kwinana-2018-12-18",
            url=payload.canonical_url,
            title_hint="Kwinana commissioning update",
            published_at_hint=datetime(2018, 12, 18, 8, 0, tzinfo=UTC),
            discovered_at=datetime(2026, 8, 21, 14, 30, tzinfo=UTC),
            metadata={"evidence_task_id": "EVT-001-KWINANA-GUIDANCE-TRAJECTORY"},
        )
        result = await DocumentArchiver(
            repository=repository,
            archive=archive,
        ).archive_document(
            plugin=FixtureSource(source, payload),
            item=item,
            fetch_context=FetchContext(source=source),
        )
        return result.document

    async def test_records_only_excerpt_grounded_in_archived_html(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "evidence-recorder"),
            name="evidence-recorder",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        excerpt = (
            "Stage One commissioning will commence at the end of this year, "
            "while Stage Two is expected to be commissioned at the end of 2019."
        )
        html = f"""
        <html><head><script>do not index this text</script></head>
        <body><article><p>{excerpt}</p></article></body></html>
        """

        with tempfile.TemporaryDirectory(prefix="longcycle-evidence-recording-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document = await self._archive_html(
                repository=repository,
                archive=archive,
                source=source,
                html=html,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            first = await recorder.record_excerpt(document=document, excerpt=excerpt)
            second = await recorder.record_excerpt(document=document, excerpt=excerpt)

            self.assertEqual(first.fragment.id, second.fragment.id)
            self.assertTrue(first.fragment.locator.startswith("visible-text:"))
            self.assertEqual(first.fragment.document_id, document.id)
            self.assertEqual(first.fragment.excerpt, excerpt)
            self.assertEqual(len(repository.evidence), 1)
            self.assertEqual(repository.extractions, {})
            self.assertEqual(repository.assertions, {})

    async def test_ambiguous_excerpt_requires_explicit_occurrence(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "evidence-ambiguous"),
            name="evidence-ambiguous",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        excerpt = "commissioning remains on target"
        html = f"<html><body><p>{excerpt}</p><p>{excerpt}</p></body></html>"

        with tempfile.TemporaryDirectory(prefix="longcycle-evidence-ambiguous-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document = await self._archive_html(
                repository=repository,
                archive=archive,
                source=source,
                html=html,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            with self.assertRaisesRegex(ValueError, "multiple times"):
                await recorder.record_excerpt(document=document, excerpt=excerpt)

            result = await recorder.record_excerpt(
                document=document,
                excerpt=excerpt,
                occurrence=1,
            )
            self.assertEqual(len(repository.evidence), 1)
            self.assertEqual(result.fragment.excerpt, excerpt)

    async def test_unarchived_wording_cannot_become_evidence(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "evidence-grounding"),
            name="evidence-grounding",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )

        with tempfile.TemporaryDirectory(prefix="longcycle-evidence-grounding-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document = await self._archive_html(
                repository=repository,
                archive=archive,
                source=source,
                html="<html><body><p>actual archived wording</p></body></html>",
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            with self.assertRaisesRegex(ValueError, "not present"):
                await recorder.record_excerpt(
                    document=document,
                    excerpt="model-invented wording",
                )

            self.assertEqual(repository.evidence, {})


if __name__ == "__main__":
    unittest.main()
