from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import RawPayload, SourceDefinition, SourceDocument, stable_uuid


class EvidenceClaimContextTest(unittest.IsolatedAsyncioTestCase):
    async def test_context_is_persisted_in_fragment_identity_without_promoting_assertions(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "claim-context-test"),
            name="claim-context-test",
            kind=SourceKind.MANUAL,
            plugin="fixture",
            quality_grade=QualityGrade.A,
        )
        excerpt = "production is expected to ramp from December 2022"
        html = f"<html><body><p>{excerpt}</p></body></html>".encode()

        with tempfile.TemporaryDirectory(prefix="longcycle-claim-context-") as temporary:
            archive = FileSystemArchiveStore(Path(temporary))
            receipt = await archive.put_if_absent(content=html, content_type="text/html")
            payload = RawPayload(
                content=html,
                content_type="text/html",
                canonical_url="https://example.com/kwinana",
                retrieved_at=datetime(2026, 8, 21, 18, 0, tzinfo=UTC),
            )
            document = SourceDocument.from_payload(
                source_id=source.id,
                payload=payload,
                blob_key=receipt.key,
                first_known_at=datetime(2022, 12, 3, 23, 59, 59, tzinfo=UTC),
            )
            repository = InMemoryResearchRepository([source])
            await repository.save_document(document)
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            context = {
                "claim_role": "expectation",
                "known_time": {
                    "upper_bound": "2022-12-03",
                    "precision": "day",
                },
                "expectation_horizon": {
                    "from": "2022-12-01",
                    "precision": "month",
                },
            }
            result = await recorder.record_excerpt(
                document=document,
                excerpt=excerpt,
                claim_context=context,
            )
            self.assertEqual(result.fragment.structured_payload, {"claim_context": context})
            self.assertEqual(repository.assertions, {})
            self.assertEqual(repository.extractions, {})

            changed = await recorder.record_excerpt(
                document=document,
                excerpt=excerpt,
                claim_context={**context, "claim_role": "project_status"},
            )
            self.assertNotEqual(result.fragment.id, changed.fragment.id)
            self.assertEqual(len(repository.evidence), 2)

            with self.assertRaisesRegex(ValueError, "non-empty JSON object"):
                await recorder.record_excerpt(
                    document=document,
                    excerpt=excerpt,
                    claim_context={},
                )


if __name__ == "__main__":
    unittest.main()
