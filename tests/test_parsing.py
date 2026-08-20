from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from longcycle.adapters.parsers import CanonicalJsonParser
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.parsing import ArtifactPipeline
from longcycle.domain.models import RawPayload, SourceDocument
from longcycle.ports.parser import ParsedOutput


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
