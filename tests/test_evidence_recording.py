from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.application.source_archive import DocumentArchiver
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import (
    DiscoveryItem,
    DocumentArtifact,
    RawPayload,
    SourceDefinition,
    SourceDocument,
    stable_uuid,
)
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
    ) -> SourceDocument:
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

    async def _pdf_document_and_artifact(
        self,
        *,
        repository: InMemoryResearchRepository,
        archive: FileSystemArchiveStore,
        source: SourceDefinition,
    ) -> tuple[SourceDocument, DocumentArtifact]:
        raw_pdf = b"%PDF-1.4 fixture bytes"
        raw_receipt = await archive.put_if_absent(
            content=raw_pdf,
            content_type="application/pdf",
        )
        document = SourceDocument.from_payload(
            source_id=source.id,
            payload=RawPayload(
                content=raw_pdf,
                content_type="application/pdf",
                canonical_url="https://example.com/primary/kwinana-2021.pdf",
                retrieved_at=datetime(2026, 8, 21, 15, 10, tzinfo=UTC),
            ),
            blob_key=raw_receipt.key,
            title="Kwinana 2021 result PDF",
            published_at=datetime(2021, 8, 30, 8, 0, tzinfo=UTC),
        )
        await repository.save_document(document)

        artifact_payload = {
            "schema_version": "longcycle-pdf-text/v1",
            "page_count": 2,
            "pages": [
                {"page": 1, "text": "general corporate overview"},
                {
                    "page": 2,
                    "text": (
                        "Kwinana is targeting qualified lithium hydroxide by the end of 2021 "
                        "and nameplate capacity during the fourth quarter of 2022."
                    ),
                },
            ],
        }
        artifact_bytes = json.dumps(
            artifact_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        artifact_receipt = await archive.put_if_absent(
            content=artifact_bytes,
            content_type="application/json",
        )
        artifact = DocumentArtifact.create(
            document_id=document.id,
            artifact_type="pdf-text-pages",
            producer_name="pypdf-text",
            producer_version="1.0.0+pypdf-6.15.0",
            input_sha256=document.content_sha256,
            content_sha256=artifact_receipt.sha256,
            blob_key=artifact_receipt.key,
            byte_length=artifact_receipt.size,
            content_type=artifact_receipt.content_type,
        )
        artifact = await repository.save_artifact(artifact)
        return document, artifact

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

    async def test_pdf_excerpt_is_grounded_to_one_persisted_page_artifact(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "pdf-evidence"),
            name="pdf-evidence",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        excerpt = "qualified lithium hydroxide by the end of 2021"

        with tempfile.TemporaryDirectory(prefix="longcycle-pdf-evidence-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document, artifact = await self._pdf_document_and_artifact(
                repository=repository,
                archive=archive,
                source=source,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            first = await recorder.record_pdf_page_excerpt(
                document=document,
                artifact=artifact,
                page=2,
                excerpt=excerpt,
            )
            second = await recorder.record_pdf_page_excerpt(
                document=document,
                artifact=artifact,
                page=2,
                excerpt=excerpt,
            )

            self.assertEqual(first.fragment.id, second.fragment.id)
            self.assertEqual(first.fragment.artifact_id, artifact.id)
            self.assertEqual(first.fragment.locator, "$.pages[1].text")
            self.assertEqual(first.fragment.structured_payload["page"], 2)
            self.assertEqual(
                first.fragment.structured_payload["parser_version"],
                "1.0.0+pypdf-6.15.0",
            )
            self.assertEqual(len(repository.evidence), 1)
            self.assertEqual(repository.assertions, {})

    async def test_pdf_evidence_fails_closed_on_wrong_page_or_artifact(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "pdf-evidence-fail"),
            name="pdf-evidence-fail",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )

        with tempfile.TemporaryDirectory(prefix="longcycle-pdf-evidence-fail-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document, artifact = await self._pdf_document_and_artifact(
                repository=repository,
                archive=archive,
                source=source,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            with self.assertRaisesRegex(ValueError, "not present"):
                await recorder.record_pdf_page_excerpt(
                    document=document,
                    artifact=artifact,
                    page=1,
                    excerpt="qualified lithium hydroxide by the end of 2021",
                )

            other_document = document.model_copy(
                update={"id": stable_uuid("document", "unrelated")}
            )
            with self.assertRaisesRegex(ValueError, "different source document"):
                await recorder.record_pdf_page_excerpt(
                    document=other_document,
                    artifact=artifact,
                    page=2,
                    excerpt="qualified lithium hydroxide by the end of 2021",
                )

            self.assertEqual(repository.evidence, {})


if __name__ == "__main__":
    unittest.main()
