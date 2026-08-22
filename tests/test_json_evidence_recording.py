from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.evidence_recording import ArchivedEvidenceRecorder
from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import (
    DocumentArtifact,
    RawPayload,
    SourceDefinition,
    SourceDocument,
    canonical_json,
    stable_uuid,
)


class JsonEvidenceRecordingTest(unittest.IsolatedAsyncioTestCase):
    async def _document_and_artifact(
        self,
        *,
        repository: InMemoryResearchRepository,
        archive: FileSystemArchiveStore,
        source: SourceDefinition,
    ) -> tuple[SourceDocument, DocumentArtifact]:
        payload = {
            "protocolSection": {
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "Seagen, a wholly owned subsidiary of Pfizer",
                    },
                    "collaborators": [{"name": "RemeGen Co., Ltd."}],
                }
            },
            "a/b": {"~key": [True, 1]},
        }
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        raw_receipt = await archive.put_if_absent(content=raw, content_type="application/json")
        document = SourceDocument.from_payload(
            source_id=source.id,
            payload=RawPayload(
                content=raw,
                content_type="application/json",
                canonical_url="https://clinicaltrials.gov/api/v2/studies/NCT05911295",
                retrieved_at=datetime(2026, 8, 22, 15, 43, tzinfo=UTC),
            ),
            blob_key=raw_receipt.key,
            title="NCT05911295",
            published_at=None,
        )
        await repository.save_document(document)

        artifact_bytes = canonical_json(payload).encode("utf-8")
        artifact_receipt = await archive.put_if_absent(
            content=artifact_bytes,
            content_type="application/json",
        )
        artifact = DocumentArtifact.create(
            document_id=document.id,
            artifact_type="canonical-json",
            producer_name="canonical-json",
            producer_version="1.0.0",
            input_sha256=document.content_sha256,
            content_sha256=artifact_receipt.sha256,
            blob_key=artifact_receipt.key,
            byte_length=artifact_receipt.size,
            content_type=artifact_receipt.content_type,
        )
        artifact = await repository.save_artifact(artifact)
        return document, artifact

    async def test_records_exact_json_pointer_value_with_artifact_lineage(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "json-evidence"),
            name="json-evidence",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )
        pointer = "/protocolSection/sponsorCollaboratorsModule/leadSponsor/name"
        expected = "Seagen, a wholly owned subsidiary of Pfizer"

        with tempfile.TemporaryDirectory(prefix="longcycle-json-evidence-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document, artifact = await self._document_and_artifact(
                repository=repository,
                archive=archive,
                source=source,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            first = await recorder.record_json_pointer_value(
                document=document,
                artifact=artifact,
                json_pointer=pointer,
                expected_value=expected,
                claim_context={"claim_role": "trial_sponsor", "known_time": "current"},
            )
            second = await recorder.record_json_pointer_value(
                document=document,
                artifact=artifact,
                json_pointer=pointer,
                expected_value=expected,
                claim_context={"claim_role": "trial_sponsor", "known_time": "current"},
            )

            self.assertEqual(first.fragment.id, second.fragment.id)
            self.assertEqual(first.fragment.artifact_id, artifact.id)
            self.assertEqual(first.fragment.locator, f"json-pointer:{pointer}")
            self.assertEqual(first.fragment.excerpt, expected)
            self.assertEqual(first.fragment.structured_payload["value"], expected)
            self.assertEqual(first.fragment.structured_payload["json_pointer"], pointer)
            self.assertEqual(len(repository.evidence), 1)
            self.assertEqual(repository.assertions, {})

    async def test_json_pointer_fails_closed_on_wrong_type_or_missing_path(self) -> None:
        source = SourceDefinition(
            id=stable_uuid("source", "json-evidence-fail"),
            name="json-evidence-fail",
            kind=SourceKind.MANUAL,
            plugin="fixture_source",
            quality_grade=QualityGrade.A,
        )

        with tempfile.TemporaryDirectory(prefix="longcycle-json-evidence-fail-") as temporary:
            repository = InMemoryResearchRepository([source])
            archive = FileSystemArchiveStore(Path(temporary))
            document, artifact = await self._document_and_artifact(
                repository=repository,
                archive=archive,
                source=source,
            )
            recorder = ArchivedEvidenceRecorder(repository=repository, archive=archive)

            with self.assertRaisesRegex(ValueError, "does not match"):
                await recorder.record_json_pointer_value(
                    document=document,
                    artifact=artifact,
                    json_pointer="/a~1b/~0key/0",
                    expected_value=1,
                    claim_context={"claim_role": "type-check"},
                )
            with self.assertRaisesRegex(ValueError, "does not exist"):
                await recorder.record_json_pointer_value(
                    document=document,
                    artifact=artifact,
                    json_pointer="/protocolSection/missing",
                    expected_value="anything",
                    claim_context={"claim_role": "missing-path"},
                )

            self.assertEqual(repository.evidence, {})


if __name__ == "__main__":
    unittest.main()
