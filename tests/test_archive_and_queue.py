from __future__ import annotations

import hashlib
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryJobQueue, InMemoryResearchRepository
from longcycle.domain.enums import JobStage, JobStatus
from longcycle.domain.models import (
    CollectionJob,
    DocumentArtifact,
    EvidenceFragment,
    RawPayload,
    SourceDocument,
    stable_uuid,
    stable_uuid_exact,
)
from longcycle.ports.repository import LeaseLostError


class ArchiveAndQueueTest(unittest.IsolatedAsyncioTestCase):
    async def test_stable_identity_preserves_opaque_case_and_part_boundaries(self) -> None:
        self.assertNotEqual(
            stable_uuid_exact("opaque", "ABC"),
            stable_uuid_exact("opaque", "abc"),
        )
        self.assertNotEqual(
            stable_uuid_exact("opaque", "a|b", "c"),
            stable_uuid_exact("opaque", "a", "b|c"),
        )

    async def test_evidence_requires_material_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonblank excerpt or structured payload"):
            EvidenceFragment.create(uuid4(), "page:1", None)
        with self.assertRaisesRegex(ValueError, "nonblank excerpt or structured payload"):
            EvidenceFragment.create(uuid4(), "page:1", "   ")

    async def test_external_id_is_part_of_document_version_identity(self) -> None:
        source_id = uuid4()
        payload = RawPayload(
            content=b"same body",
            content_type="text/plain",
            canonical_url="https://example.test/download",
            retrieved_at=datetime(2026, 8, 18, tzinfo=UTC),
        )
        first = SourceDocument.from_payload(
            source_id=source_id,
            payload=payload,
            blob_key="raw/first",
            external_id="announcement-a",
        )
        second = SourceDocument.from_payload(
            source_id=source_id,
            payload=payload,
            blob_key="raw/second",
            external_id="announcement-b",
        )
        repository = InMemoryResearchRepository()

        await repository.save_document(first)
        await repository.save_document(second)

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(len(repository.documents), 2)
        self.assertEqual(
            await repository.document_by_hash(
                source_id,
                payload.canonical_url,
                payload.sha256,
                "announcement-a",
            ),
            first,
        )
        self.assertEqual(
            await repository.document_by_hash(
                source_id,
                payload.canonical_url,
                payload.sha256,
                "announcement-b",
            ),
            second,
        )

    async def test_document_and_locator_case_are_identity_significant(self) -> None:
        source_id = uuid4()
        retrieved_at = datetime(2026, 8, 18, tzinfo=UTC)
        upper = RawPayload(
            content=b"same body",
            content_type="text/plain",
            canonical_url="https://example.test/Report/A",
            retrieved_at=retrieved_at,
        )
        lower = upper.model_copy(update={"canonical_url": "https://example.test/Report/a"})
        first = SourceDocument.from_payload(
            source_id=source_id,
            payload=upper,
            blob_key="raw/upper",
            external_id="ABC",
        )
        second = SourceDocument.from_payload(
            source_id=source_id,
            payload=lower,
            blob_key="raw/lower",
            external_id="abc",
        )
        self.assertNotEqual(first.id, second.id)
        self.assertNotEqual(
            EvidenceFragment.create(first.id, "Cell:A1", "same").id,
            EvidenceFragment.create(first.id, "Cell:a1", "same").id,
        )

    async def test_out_of_order_duplicate_preserves_earliest_known_time(self) -> None:
        source_id = uuid4()
        later = datetime(2026, 8, 18, tzinfo=UTC)
        earlier = later - timedelta(days=10)
        payload = RawPayload(
            content=b"unchanged",
            content_type="text/plain",
            canonical_url="https://example.test/report",
            retrieved_at=later,
        )
        first = SourceDocument.from_payload(
            source_id=source_id,
            payload=payload,
            blob_key="raw/report",
            external_id="report-1",
            first_known_at=later,
        )
        backfill = SourceDocument.from_payload(
            source_id=source_id,
            payload=payload.model_copy(update={"retrieved_at": earlier}),
            blob_key="raw/report",
            external_id="report-1",
            first_known_at=earlier,
        )
        repository = InMemoryResearchRepository()

        await repository.save_document(first)
        stored = await repository.save_document(backfill)

        self.assertEqual(stored.first_known_at, earlier)
        self.assertEqual(repository.documents[first.id].first_known_at, earlier)

    async def test_same_excerpt_at_two_locations_is_distinct_evidence(self) -> None:
        document_id = uuid4()
        first = EvidenceFragment.create(document_id, "page:1", "same sentence")
        second = EvidenceFragment.create(document_id, "page:2", "same sentence")
        self.assertEqual(first.fragment_sha256, second.fragment_sha256)
        self.assertNotEqual(first.locator_sha256, second.locator_sha256)
        self.assertNotEqual(first.id, second.id)

    async def test_parser_artifact_is_immutable_and_grounds_structured_evidence(self) -> None:
        source_id = uuid4()
        payload = RawPayload(
            content=b"<table><tr><td>100</td></tr></table>",
            content_type="text/html",
            canonical_url="https://example.test/table",
            retrieved_at=datetime(2026, 8, 20, tzinfo=UTC),
        )
        document = SourceDocument.from_payload(
            source_id=source_id,
            payload=payload,
            blob_key="raw/table",
        )
        parsed = b'{"cells":[[100]]}'
        artifact = DocumentArtifact.create(
            document_id=document.id,
            artifact_type="table-json",
            producer_name="html-table-parser",
            producer_version="1",
            input_sha256=document.content_sha256,
            content_sha256=hashlib.sha256(parsed).hexdigest(),
            blob_key="artifacts/table.json",
            byte_length=len(parsed),
            content_type="application/json",
        )
        repository = InMemoryResearchRepository()
        await repository.save_document(document)
        stored = await repository.save_artifact(artifact)
        fragment = EvidenceFragment.create(
            document.id,
            "$.cells[0][0]",
            None,
            {"value": 100},
            artifact_id=stored.id,
        )
        await repository.save_evidence((fragment,))

        changed = artifact.model_copy(
            update={
                "content_sha256": hashlib.sha256(b"different").hexdigest(),
                "blob_key": "artifacts/different.json",
            }
        )
        with self.assertRaisesRegex(ValueError, "different content"):
            await repository.save_artifact(changed)

        self.assertEqual(repository.evidence[fragment.id].artifact_id, artifact.id)

    async def test_evidence_cannot_claim_an_unpersisted_parser_artifact(self) -> None:
        repository = InMemoryResearchRepository()
        fragment = EvidenceFragment.create(
            uuid4(),
            "$.value",
            None,
            {"value": 100},
            artifact_id=uuid4(),
        )
        with self.assertRaisesRegex(ValueError, "unknown or unrelated"):
            await repository.save_evidence((fragment,))

    async def test_repository_rejects_forged_evidence_identity(self) -> None:
        repository = InMemoryResearchRepository()
        fragment = EvidenceFragment.create(uuid4(), "page:1", "reported 100")
        forged = fragment.model_copy(update={"id": uuid4()})
        with self.assertRaisesRegex(ValueError, "identity does not match"):
            await repository.save_evidence((forged,))

    async def test_content_addressed_archive_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = FileSystemArchiveStore(Path(directory))
            first = await store.put_if_absent(content=b"same", content_type="text/plain")
            second = await store.put_if_absent(content=b"same", content_type="text/plain")
            self.assertTrue(first.created)
            self.assertFalse(second.created)
            self.assertEqual(first.key, second.key)
            self.assertEqual(await store.get(first.key), b"same")

    async def test_content_addressed_archive_detects_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = FileSystemArchiveStore(Path(directory))
            archived = await store.put_if_absent(content=b"original", content_type="text/plain")
            (Path(directory) / archived.key).write_bytes(b"tampered")
            with self.assertRaises(IOError):
                await store.get(archived.key)
            with self.assertRaises(IOError):
                await store.put_if_absent(content=b"original", content_type="text/plain")

    async def test_queue_enqueue_lease_and_stale_token(self) -> None:
        queue = InMemoryJobQueue()
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="a" * 64, priority=80)
        first = await queue.enqueue(job)
        duplicate = await queue.enqueue(job.model_copy(update={"id": uuid4()}))
        self.assertEqual(first.id, duplicate.id)
        claimed = await queue.claim(worker_id="worker-a", limit=1, lease_seconds=30)
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0].status, JobStatus.LEASED)
        assert claimed[0].lease_token is not None
        with self.assertRaises(PermissionError):
            await queue.acknowledge(job_id=job.id, worker_id="worker-a", lease_token=uuid4())
        await queue.acknowledge(job_id=job.id, worker_id="worker-a", lease_token=claimed[0].lease_token)
        self.assertEqual(queue.jobs[job.id].status, JobStatus.SUCCEEDED)

    async def test_enqueue_rejects_a_preleased_job(self) -> None:
        queue = InMemoryJobQueue()
        job = CollectionJob(
            stage=JobStage.FETCH,
            status=JobStatus.LEASED,
            idempotency_key="f" * 64,
            lease_owner="forged",
            lease_token=uuid4(),
            lease_expires_at=datetime.now(UTC) + timedelta(seconds=30),
        )
        with self.assertRaisesRegex(ValueError, "only queued"):
            await queue.enqueue(job)

    async def test_expired_lease_can_be_reclaimed(self) -> None:
        queue = InMemoryJobQueue()
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="b" * 64)
        await queue.enqueue(job)
        first = (await queue.claim(worker_id="old", limit=1, lease_seconds=30))[0]
        queue.jobs[job.id] = first.model_copy(update={"lease_expires_at": datetime.now(UTC) - timedelta(seconds=1)})
        second = (await queue.claim(worker_id="new", limit=1, lease_seconds=30))[0]
        self.assertNotEqual(first.lease_token, second.lease_token)
        assert first.lease_token is not None
        with self.assertRaises(PermissionError):
            await queue.acknowledge(job_id=job.id, worker_id="old", lease_token=first.lease_token)

    async def test_expired_lease_at_attempt_limit_becomes_dead(self) -> None:
        queue = InMemoryJobQueue()
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="c" * 64, max_attempts=1)
        await queue.enqueue(job)
        claimed = (await queue.claim(worker_id="worker-a", limit=1, lease_seconds=30))[0]
        queue.jobs[job.id] = claimed.model_copy(
            update={"lease_expires_at": datetime.now(UTC) - timedelta(seconds=1)}
        )

        reclaimed = await queue.claim(worker_id="worker-b", limit=1, lease_seconds=30)

        self.assertEqual(reclaimed, ())
        self.assertEqual(queue.jobs[job.id].status, JobStatus.DEAD)
        self.assertEqual(queue.jobs[job.id].attempt, 1)
        self.assertIsNone(queue.jobs[job.id].lease_token)

    async def test_expired_lease_cannot_be_acknowledged_failed_or_renewed(self) -> None:
        for index, operation in enumerate(("ack", "fail", "heartbeat"), start=1):
            with self.subTest(operation=operation):
                queue = InMemoryJobQueue()
                job = CollectionJob(stage=JobStage.FETCH, idempotency_key=f"{index:064x}")
                await queue.enqueue(job)
                leased = (await queue.claim(worker_id="worker-a", limit=1, lease_seconds=30))[0]
                queue.jobs[job.id] = leased.model_copy(
                    update={"lease_expires_at": datetime.now(UTC) - timedelta(seconds=1)}
                )
                assert leased.lease_token is not None

                with self.assertRaises(LeaseLostError):
                    if operation == "ack":
                        await queue.acknowledge(
                            job_id=job.id,
                            worker_id="worker-a",
                            lease_token=leased.lease_token,
                        )
                    elif operation == "fail":
                        await queue.fail(
                            job_id=job.id,
                            worker_id="worker-a",
                            lease_token=leased.lease_token,
                            error="late failure",
                            retryable=True,
                        )
                    else:
                        await queue.heartbeat(
                            job_id=job.id,
                            worker_id="worker-a",
                            lease_token=leased.lease_token,
                            lease_seconds=30,
                        )
