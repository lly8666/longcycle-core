from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from longcycle.adapters.parsers import CanonicalJsonParser, PdfTextParser
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.parsing import ArtifactPipeline
from longcycle.domain.models import RawPayload, SourceDocument
from longcycle.ports.parser import ParsedOutput


def _single_page_text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): font_ref}
            )
        }
    )
    stream = DecodedStreamObject()
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class ParsingTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_output_is_archived_versioned_and_idempotent(self) -> None:
        payload = RawPayload(
            content=b'{"b":2,"a":1}',
            content_type="application/json",
            canonical_url="https://example.test/data.json",
            retrieved_at=datetime(2026, 8, 20, tzinfo=UTC),
        )
        document = SourceDocument.from_payload(
            source_id=uuid4(),
            payload=payload,
            blob_key="raw/input",
        )
        repository = InMemoryResearchRepository()
        await repository.save_document(document)
        with tempfile.TemporaryDirectory() as directory:
            pipeline = ArtifactPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(Path(directory)),
            )
            first = await pipeline.parse(
                document=document,
                content=payload.content,
                parser=CanonicalJsonParser(),
            )
            second = await pipeline.parse(
                document=document,
                content=payload.content,
                parser=CanonicalJsonParser(),
            )

        self.assertEqual(first, second)
        self.assertEqual(len(repository.artifacts), 1)
        self.assertEqual(first[0].producer_version, "1.0.0")

    async def test_pdf_parser_emits_page_scoped_versioned_text_artifact(self) -> None:
        text = "Kwinana qualified lithium hydroxide by end of 2021"
        pdf = _single_page_text_pdf(text)
        payload = RawPayload(
            content=pdf,
            content_type="application/pdf",
            canonical_url="https://example.test/kwinana-2021.pdf",
            retrieved_at=datetime(2026, 8, 21, tzinfo=UTC),
        )
        document = SourceDocument.from_payload(
            source_id=uuid4(),
            payload=payload,
            blob_key="raw/pdf-input",
        )
        repository = InMemoryResearchRepository()
        await repository.save_document(document)

        with tempfile.TemporaryDirectory() as directory:
            archive = FileSystemArchiveStore(Path(directory))
            artifact = (
                await ArtifactPipeline(repository=repository, archive=archive).parse(
                    document=document,
                    content=pdf,
                    parser=PdfTextParser(),
                )
            )[0]
            artifact_bytes = await archive.get(artifact.blob_key)

        parsed = json.loads(artifact_bytes)
        self.assertEqual(artifact.artifact_type, "pdf-text-pages")
        self.assertEqual(artifact.content_type, "application/json")
        self.assertEqual(artifact.producer_name, "pypdf-text")
        self.assertEqual(artifact.producer_version, "1.0.0+pypdf-6.15.0")
        self.assertEqual(parsed["schema_version"], "longcycle-pdf-text/v1")
        self.assertEqual(parsed["page_count"], 1)
        self.assertEqual(parsed["pages"][0]["page"], 1)
        self.assertIn(text, parsed["pages"][0]["text"])

    async def test_parser_limits_and_media_type_fail_closed(self) -> None:
        class DuplicateParser:
            parser_name = "duplicate"
            parser_version = "1"
            supported_media_types = frozenset({"text/plain"})

            async def parse(self, document, content):  # type: ignore[no-untyped-def]
                del document, content
                return (
                    ParsedOutput("text", b"one", "text/plain"),
                    ParsedOutput("text", b"two", "text/plain"),
                )

        payload = RawPayload(
            content=b"input",
            content_type="text/plain",
            canonical_url="https://example.test/input",
            retrieved_at=datetime(2026, 8, 20, tzinfo=UTC),
        )
        document = SourceDocument.from_payload(
            source_id=uuid4(),
            payload=payload,
            blob_key="raw/input",
        )
        repository = InMemoryResearchRepository()
        await repository.save_document(document)
        with tempfile.TemporaryDirectory() as directory:
            pipeline = ArtifactPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(Path(directory)),
            )
            with self.assertRaisesRegex(ValueError, "duplicate artifact types"):
                await pipeline.parse(
                    document=document,
                    content=payload.content,
                    parser=DuplicateParser(),
                )
            with self.assertRaisesRegex(ValueError, "does not support"):
                await pipeline.parse(
                    document=document,
                    content=payload.content,
                    parser=CanonicalJsonParser(),
                )


if __name__ == "__main__":
    unittest.main()
