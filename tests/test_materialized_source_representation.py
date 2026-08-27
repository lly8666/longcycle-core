from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from longcycle.adapters.sources.materialized import MaterializedDocumentSource
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import DiscoveryItem, SourceDefinition
from longcycle.ports.source import FetchContext


class MaterializedSourceRepresentationTest(unittest.IsolatedAsyncioTestCase):
    def _source(self) -> SourceDefinition:
        return SourceDefinition(
            id=uuid4(),
            name="synthetic material source",
            kind=SourceKind.GOVERNMENT,
            plugin="materialized_file",
            quality_grade=QualityGrade.A,
            publisher_domain="regulator.example",
        )

    async def test_content_verified_pdf_representation_emits_truthful_internal_markers(self) -> None:
        source = self._source()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = b"claim-relevant text read from page 7"
            path = root / "report-page-7.txt"
            path.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            item = DiscoveryItem(
                source_id=source.id,
                url="https://regulator.example/report.pdf",
                metadata={
                    "material_path": path.name,
                    "material_expected_sha256": digest,
                    "material_content_type": "text/plain; charset=utf-8",
                    "retrieval_provenance": {
                        "source_media_type": "application/pdf",
                        "source_capture_state": "content_verified",
                        "raw_source_materialized": False,
                        "content_verification_mode": "interactive_pdf_read",
                        "claim_relevant_content_preserved": True,
                    },
                },
            )

            payload = await MaterializedDocumentSource(source, material_root=root).fetch(
                item,
                FetchContext(source=source),
            )

            self.assertEqual(payload.content, content)
            self.assertEqual(payload.content_type, "text/plain; charset=utf-8")
            self.assertEqual(payload.headers["x-longcycle-raw-source-materialized"], "false")
            self.assertEqual(payload.headers["x-longcycle-source-capture-state"], "content_verified")
            self.assertEqual(payload.headers["x-longcycle-source-media-type"], "application/pdf")
            self.assertEqual(payload.headers["x-longcycle-claim-content-preserved"], "true")

    async def test_non_raw_representation_fails_without_claim_content_guard(self) -> None:
        source = self._source()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = b"text"
            path = root / "report.txt"
            path.write_bytes(content)
            item = DiscoveryItem(
                source_id=source.id,
                url="https://regulator.example/report.pdf",
                metadata={
                    "material_path": path.name,
                    "material_expected_sha256": hashlib.sha256(content).hexdigest(),
                    "material_content_type": "text/plain",
                    "retrieval_provenance": {
                        "source_media_type": "application/pdf",
                        "source_capture_state": "content_verified",
                        "raw_source_materialized": False,
                        "content_verification_mode": "interactive_pdf_read",
                    },
                },
            )

            with self.assertRaisesRegex(ValueError, "claim_relevant_content_preserved=true"):
                await MaterializedDocumentSource(source, material_root=root).fetch(
                    item,
                    FetchContext(source=source),
                )

    async def test_raw_materialized_file_emits_explicit_true_marker(self) -> None:
        source = self._source()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = b"%PDF-synthetic"
            path = root / "report.pdf"
            path.write_bytes(content)
            item = DiscoveryItem(
                source_id=source.id,
                url="https://regulator.example/report.pdf",
                metadata={
                    "material_path": path.name,
                    "material_expected_sha256": hashlib.sha256(content).hexdigest(),
                    "material_content_type": "application/pdf",
                },
            )

            payload = await MaterializedDocumentSource(source, material_root=root).fetch(
                item,
                FetchContext(source=source),
            )

            self.assertEqual(payload.headers["x-longcycle-raw-source-materialized"], "true")
            self.assertEqual(payload.headers["x-longcycle-transport"], "materialized_file")


if __name__ == "__main__":
    unittest.main()
