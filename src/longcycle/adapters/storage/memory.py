from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from longcycle.domain.enums import FactStatus, JobStatus
from longcycle.domain.models import (
    CollectionJob,
    DocumentArtifact,
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    ReconciliationResult,
    ReviewItem,
    SourceDefinition,
    SourceDocument,
)
from longcycle.ports.repository import LeaseLostError, ReconciliationEvaluator


class InMemoryResearchRepository:
    def __init__(self, sources: Sequence[SourceDefinition] = ()) -> None:
        self.sources = {source.id: source for source in sources}
        self.documents: dict[UUID, SourceDocument] = {}
        self.documents_by_hash: dict[tuple[UUID, str, str | None, str], UUID] = {}
        self.artifacts: dict[UUID, DocumentArtifact] = {}
        self.artifacts_by_identity: dict[tuple[UUID, str, str, str, str], UUID] = {}
        self.evidence: dict[UUID, EvidenceFragment] = {}
        self.extractions: dict[UUID, ExtractionEnvelope] = {}
        self.completed_processing: set[UUID] = set()
        self.assertions: dict[UUID, FactAssertion] = {}
        self._assertion_ingest_status: dict[UUID, FactStatus] = {}
        self.scope_index: dict[str, list[UUID]] = {}
        self.reconciliations: list[ReconciliationResult] = []
        self.reviews: dict[UUID, ReviewItem] = {}
        self._lock = asyncio.Lock()
        self._fact_locks: dict[str, asyncio.Lock] = {}

    async def get_source(self, source_id: UUID) -> SourceDefinition:
        return self.sources[source_id]

    async def save_document(self, document: SourceDocument) -> SourceDocument:
        async with self._lock:
            key = (
                document.source_id,
                document.canonical_url,
                document.external_id,
                document.content_sha256,
            )
            existing_id = self.documents_by_hash.get(key)
            if existing_id:
                existing = self.documents[existing_id]
                known_at = min(existing.first_known_at, document.first_known_at)
                published_candidates = [
                    value
                    for value in (existing.published_at, document.published_at)
                    if value is not None
                ]
                updated = existing.model_copy(
                    update={
                        "first_known_at": known_at,
                        "published_at": min(published_candidates) if published_candidates else None,
                        "retrieved_at": min(existing.retrieved_at, document.retrieved_at),
                    }
                )
                self.documents[existing_id] = updated
                return updated
            self.documents[document.id] = document
            self.documents_by_hash[key] = document.id
            return document

    async def document_by_hash(
        self,
        source_id: UUID,
        canonical_url: str,
        content_sha256: str,
        external_id: str | None = None,
    ) -> SourceDocument | None:
        document_id = self.documents_by_hash.get(
            (source_id, canonical_url, external_id, content_sha256)
        )
        return self.documents.get(document_id) if document_id else None

    async def save_artifact(self, artifact: DocumentArtifact) -> DocumentArtifact:
        async with self._lock:
            if artifact.document_id not in self.documents:
                raise KeyError(f"document version does not exist: {artifact.document_id}")
            key = (
                artifact.document_id,
                artifact.artifact_type,
                artifact.producer_name,
                artifact.producer_version,
                artifact.input_sha256,
            )
            existing_id = self.artifacts_by_identity.get(key)
            if existing_id is not None:
                existing = self.artifacts[existing_id]
                if existing.content_sha256 != artifact.content_sha256:
                    raise ValueError("parser artifact identity produced different content")
                return existing
            self.artifacts[artifact.id] = artifact
            self.artifacts_by_identity[key] = artifact.id
            return artifact

    async def save_evidence(self, fragments: Sequence[EvidenceFragment]) -> None:
        async with self._lock:
            for fragment in fragments:
                expected = EvidenceFragment.create(
                    fragment.document_id,
                    fragment.locator,
                    fragment.excerpt,
                    fragment.structured_payload,
                    artifact_id=fragment.artifact_id,
                )
                if expected.id != fragment.id or expected.fragment_sha256 != fragment.fragment_sha256:
                    raise ValueError("evidence fragment identity does not match its content")
                if fragment.artifact_id is not None:
                    artifact = self.artifacts.get(fragment.artifact_id)
                    if artifact is None or artifact.document_id != fragment.document_id:
                        raise ValueError("evidence references an unknown or unrelated parser artifact")
                self.evidence.setdefault(fragment.id, fragment)

    async def save_extraction(self, extraction: ExtractionEnvelope) -> ExtractionEnvelope:
        async with self._lock:
            return self.extractions.setdefault(extraction.run_id, extraction)

    async def get_extraction(self, run_id: UUID) -> ExtractionEnvelope | None:
        return self.extractions.get(run_id)

    async def processing_completed(self, run_id: UUID) -> bool:
        return run_id in self.completed_processing

    async def complete_processing(self, run_id: UUID) -> None:
        if run_id not in self.extractions:
            raise KeyError(f"extraction run does not exist: {run_id}")
        self.completed_processing.add(run_id)

    async def append_assertions(self, assertions: Sequence[FactAssertion]) -> None:
        async with self._lock:
            batch_ids = {assertion.id for assertion in assertions}
            if any(
                assertion.supersedes_id in batch_ids
                for assertion in assertions
                if assertion.supersedes_id is not None
            ):
                raise ValueError("one assertion batch cannot contain its own supersession target")
            available_ids = set(self.assertions)
            missing_supersession_targets = {
                assertion.supersedes_id
                for assertion in assertions
                if assertion.supersedes_id is not None
                and assertion.supersedes_id not in available_ids
            }
            if missing_supersession_targets:
                raise ValueError("assertion references an unknown supersession target")
            for assertion in assertions:
                if assertion.id in self.assertions:
                    continue
                self.assertions[assertion.id] = assertion
                self._assertion_ingest_status[assertion.id] = assertion.status
                self.scope_index.setdefault(assertion.scope_key, []).append(assertion.id)

    async def assertions_for_comparison(self, candidate: FactAssertion) -> Sequence[FactAssertion]:
        return tuple(self.assertions[item] for item in self.scope_index.get(candidate.scope_key, []))

    async def reconcile_assertion(
        self,
        candidate: FactAssertion,
        evaluator: ReconciliationEvaluator,
    ) -> ReconciliationResult:
        fact_lock = self._fact_locks.setdefault(candidate.scope_key, asyncio.Lock())
        async with fact_lock:
            stored = self.assertions.get(candidate.id)
            if stored is None:
                raise KeyError(candidate.id)
            if stored.model_copy(update={"status": candidate.status}) != candidate:
                raise ValueError("candidate does not match the persisted immutable assertion")
            duplicate = next(
                (
                    evaluation
                    for evaluation in self.reconciliations
                    if evaluation.assertion_id == candidate.id
                    and evaluation.evaluator_name == evaluator.evaluator_name
                    and evaluation.evaluator_version == evaluator.evaluator_version
                ),
                None,
            )
            if duplicate is not None:
                return duplicate
            existing = await self.assertions_for_comparison(stored)
            result = evaluator.reconcile(stored, existing).model_copy(
                update={
                    "evaluator_name": evaluator.evaluator_name,
                    "evaluator_version": evaluator.evaluator_version,
                }
            )
            return await self.save_reconciliation(result)

    async def save_reconciliation(self, result: ReconciliationResult) -> ReconciliationResult:
        result = ReconciliationResult.model_validate(result.model_dump(mode="python"))
        async with self._lock:
            duplicate = next(
                (
                    existing
                    for existing in self.reconciliations
                    if existing.assertion_id == result.assertion_id
                    and existing.evaluator_name == result.evaluator_name
                    and existing.evaluator_version == result.evaluator_version
                ),
                None,
            )
            if duplicate is not None:
                return duplicate
            self.reconciliations.append(result)
            self._refresh_assertion_statuses()
            return result

    def _refresh_assertion_statuses(self) -> None:
        latest: dict[UUID, ReconciliationResult] = {}
        for evaluation in self.reconciliations:
            latest[evaluation.assertion_id] = evaluation
        statuses = {
            assertion_id: (
                latest[assertion_id].status
                if assertion_id in latest
                else self._assertion_ingest_status[assertion_id]
            )
            for assertion_id in self.assertions
        }
        superseded_ids: set[UUID] = set()
        for successor_id, status in statuses.items():
            supersedes_id = self.assertions[successor_id].supersedes_id
            if status == FactStatus.TRUSTED and supersedes_id is not None:
                superseded_ids.add(supersedes_id)
        for superseded_id in superseded_ids:
            if statuses.get(superseded_id) == FactStatus.TRUSTED:
                statuses[superseded_id] = FactStatus.SUPERSEDED
        for assertion_id, status in statuses.items():
            self.assertions[assertion_id] = self.assertions[assertion_id].model_copy(
                update={"status": status}
            )

    async def enqueue_review(self, item: ReviewItem) -> None:
        async with self._lock:
            self.reviews.setdefault(item.id, item)


class InMemoryJobQueue:
    """At-least-once queue with leases and idempotent enqueue for contract tests."""

    def __init__(self) -> None:
        self.jobs: dict[UUID, CollectionJob] = {}
        self.idempotency_index: dict[str, UUID] = {}
        self.errors: dict[UUID, str] = {}
        self._lock = asyncio.Lock()

    async def enqueue(self, job: CollectionJob) -> CollectionJob:
        if job.status != JobStatus.QUEUED:
            raise ValueError("only queued jobs can be enqueued")
        async with self._lock:
            existing_id = self.idempotency_index.get(job.idempotency_key)
            if existing_id:
                return self.jobs[existing_id]
            self.jobs[job.id] = job
            self.idempotency_index[job.idempotency_key] = job.id
            return job

    async def claim(self, *, worker_id: str, limit: int, lease_seconds: int) -> Sequence[CollectionJob]:
        now = datetime.now(UTC)
        async with self._lock:
            for job_id, job in tuple(self.jobs.items()):
                expired_lease = (
                    job.status == JobStatus.LEASED
                    and job.lease_expires_at is not None
                    and job.lease_expires_at <= now
                )
                exhausted_waiting = job.status in {JobStatus.QUEUED, JobStatus.RETRY}
                if (
                    job.available_at <= now
                    and job.attempt >= job.max_attempts
                    and (expired_lease or exhausted_waiting)
                ):
                    self.jobs[job_id] = job.model_copy(
                        update={
                            "status": JobStatus.DEAD,
                            "lease_owner": None,
                            "lease_token": None,
                            "lease_expires_at": None,
                        }
                    )
                    self.errors[job_id] = (
                        "lease expired after maximum attempts"
                        if expired_lease
                        else "maximum attempts exhausted"
                    )
            eligible = [
                job
                for job in self.jobs.values()
                if job.available_at <= now
                and job.attempt < job.max_attempts
                and (
                    job.status in {JobStatus.QUEUED, JobStatus.RETRY}
                    or (
                        job.status == JobStatus.LEASED
                        and job.lease_expires_at is not None
                        and job.lease_expires_at <= now
                    )
                )
            ]
            eligible.sort(key=lambda job: (-job.priority, job.available_at, job.created_at))
            claimed: list[CollectionJob] = []
            for job in eligible[:limit]:
                leased = job.model_copy(
                    update={
                        "status": JobStatus.LEASED,
                        "lease_owner": worker_id,
                        "lease_token": uuid4(),
                        "lease_expires_at": now + timedelta(seconds=lease_seconds),
                        "attempt": job.attempt + 1,
                    }
                )
                self.jobs[job.id] = leased
                claimed.append(leased)
            return tuple(claimed)

    async def acknowledge(self, *, job_id: UUID, worker_id: str, lease_token: UUID) -> None:
        async with self._lock:
            job = self._owned_job(job_id, worker_id, lease_token)
            self.jobs[job_id] = job.model_copy(
                update={
                    "status": JobStatus.SUCCEEDED,
                    "lease_owner": None,
                    "lease_token": None,
                    "lease_expires_at": None,
                }
            )

    async def fail(
        self, *, job_id: UUID, worker_id: str, lease_token: UUID, error: str, retryable: bool
    ) -> None:
        now = datetime.now(UTC)
        async with self._lock:
            job = self._owned_job(job_id, worker_id, lease_token)
            dead = not retryable or job.attempt >= job.max_attempts
            delay = min(3600, 2 ** min(job.attempt, 10))
            self.jobs[job_id] = job.model_copy(
                update={
                    "status": JobStatus.DEAD if dead else JobStatus.RETRY,
                    "available_at": now + timedelta(seconds=delay),
                    "lease_owner": None,
                    "lease_token": None,
                    "lease_expires_at": None,
                }
            )
            self.errors[job_id] = error[:4000]

    async def heartbeat(
        self, *, job_id: UUID, worker_id: str, lease_token: UUID, lease_seconds: int
    ) -> None:
        async with self._lock:
            job = self._owned_job(job_id, worker_id, lease_token)
            self.jobs[job_id] = job.model_copy(
                update={"lease_expires_at": datetime.now(UTC) + timedelta(seconds=lease_seconds)}
            )

    def _owned_job(self, job_id: UUID, worker_id: str, lease_token: UUID) -> CollectionJob:
        job = self.jobs[job_id]
        if (
            job.status != JobStatus.LEASED
            or job.lease_owner != worker_id
            or job.lease_token != lease_token
            or job.lease_expires_at is None
            or job.lease_expires_at <= datetime.now(UTC)
        ):
            raise LeaseLostError("job lease is expired, stale, or no longer owned")
        return job
