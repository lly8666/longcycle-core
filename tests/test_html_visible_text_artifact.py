from __future__ import annotations

import hashlib
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.parsers import HtmlVisibleTextParser
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.application.parsing import ArtifactPipeline
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import RawPayload, SourceDefinition, SourceDocument, stable_uuid


class HtmlVisibleTextArtifactTest(unittest.IsolatedAsyncioTestCase):
    async def _document(
        self,
        *,
        repository: InMemoryResearchRepository,
        archive: FileSystemArchiveStore,
        source: SourceDefinition,
        content: bytes,
        label: str,
    ) -> SourceDocument:
        receipt = await archive.put_if_absent(content=content, content_type="text/html")
        document = SourceDocument.from_payload(
            source_id=source.id,
            payload=RawPayload(
                content=content,
                content_type="text/html",
                canonical_url="https://www.sec.gov/Archives/example.htm",
                retrieved_at=datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
            ),
            blob_key=receipt.key,
            external_id=label,
            first_known_at=datetime(2019, 8, 7, 16, 57, 18, tzinfo=UTC),
        )
        await repository.save_document(document)
        return document

    async def test_hidden_transport_injection_changes_raw_but_not_visible_text_artifact(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "sec-artifact-test"),
            name="SEC artifact test",
            kind=SourceKind.COMPANY,
            plugin="fixture",
            quality_grade=QualityGrade.A,
        )
        body = "<main>Train 1 commissioning target is 18 March 2021.</main>"
        first_html = (
            '<html><head><script>bazadebezolkohpepadr="76822753"</script></head>'
            f'<body>{body}<noscript><img src="/akam/pixel_a?token=one"></noscript></body></html>'
        ).encode()
        second_html = (
            '<html><head><script>bazadebezolkohpepadr="221246243"</script></head>'
            f'<body>{body}<noscript><img src="/akam/pixel_b?token=two"></noscript></body></html>'
        ).encode()
        self.assertNotEqual(hashlib.sha256(first_html).digest(), hashlib.sha256(second_html).digest())

        with tempfile.TemporaryDirectory(prefix="longcycle-html-artifact-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            first = await self._document(
                repository=repository,
                archive=archive,
                source=source,
                content=first_html,
                label="first",
            )
            second = await self._document(
                repository=repository,
                archive=archive,
                source=source,
                content=second_html,
                label="second",
            )
            pipeline = ArtifactPipeline(repository=repository, archive=archive)
            first_artifact = (
                await pipeline.parse(
                    document=first,
                    content=first_html,
                    parser=HtmlVisibleTextParser(),
                )
            )[0]
            second_artifact = (
                await pipeline.parse(
                    document=second,
                    content=second_html,
                    parser=HtmlVisibleTextParser(),
                )
            )[0]

            self.assertNotEqual(first.content_sha256, second.content_sha256)
            self.assertEqual(first_artifact.content_sha256, second_artifact.content_sha256)
            self.assertEqual(
                await archive.get(first_artifact.blob_key),
                b"Train 1 commissioning target is 18 March 2021.",
            )

            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)
            recorded = await recorder.record_html_visible_text_excerpt(
                document=first,
                artifact=first_artifact,
                excerpt="commissioning target is 18 March 2021",
                claim_context={
                    "claim_role": "contract_schedule",
                    "known_time": {"upper_bound": "2019-08-07T16:57:18Z"},
                },
            )
            self.assertEqual(recorded.fragment.artifact_id, first_artifact.id)
            self.assertTrue(recorded.fragment.locator.startswith("text:"))
            self.assertEqual(len(repository.evidence), 1)
            self.assertEqual(repository.assertions, {})

    async def test_html_artifact_evidence_fails_closed_on_wrong_artifact_type(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "html-wrong-artifact-test"),
            name="HTML wrong artifact test",
            kind=SourceKind.COMPANY,
            plugin="fixture",
            quality_grade=QualityGrade.A,
        )
        content = b"<html><body>archived wording</body></html>"
        with tempfile.TemporaryDirectory(prefix="longcycle-html-artifact-fail-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document = await self._document(
                repository=repository,
                archive=archive,
                source=source,
                content=content,
                label="wrong-type",
            )
            artifact = (
                await ArtifactPipeline(repository=repository, archive=archive).parse(
                    document=document,
                    content=content,
                    parser=HtmlVisibleTextParser(),
                )
            )[0].model_copy(update={"artifact_type": "other"})
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)
            with self.assertRaisesRegex(ValueError, "html-visible-text"):
                await recorder.record_html_visible_text_excerpt(
                    document=document,
                    artifact=artifact,
                    excerpt="archived wording",
                )


if __name__ == "__main__":
    unittest.main()
