from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

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


class LeaseLostError(PermissionError):
    """The worker no longer owns the queue lease and must not mutate the job."""


class ReconciliationEvaluator(Protocol):
    evaluator_name: str
    evaluator_version: str

    def reconcile(
        self,
        candidate: FactAssertion,
        existing: Sequence[FactAssertion],
    ) -> ReconciliationResult: ...


class ResearchRepository(Protocol):
    async def get_source(self, source_id: UUID) -> SourceDefinition: ...

    async def save_source(self, source: SourceDefinition) -> SourceDefinition: ...

    async def save_document(self, document: SourceDocument) -> SourceDocument: ...

    async def save_artifact(self, artifact: DocumentArtifact) -> DocumentArtifact: ...

    async def document_by_hash(
        self,
        source_id: UUID,
        canonical_url: str,
        content_sha256: str,
        external_id: str | None = None,
    ) -> SourceDocument | None: ...

    async def save_evidence(self, fragments: Sequence[EvidenceFragment]) -> None: ...

    async def save_extraction(self, extraction: ExtractionEnvelope) -> ExtractionEnvelope: ...

    async def get_extraction(self, run_id: UUID) -> ExtractionEnvelope | None: ...

    async def processing_completed(self, run_id: UUID) -> bool: ...

    async def complete_processing(self, run_id: UUID) -> None: ...

    async def append_assertions(self, assertions: Sequence[FactAssertion]) -> None: ...

    async def reconcile_assertion(
        self,
        candidate: FactAssertion,
        evaluator: ReconciliationEvaluator,
    ) -> ReconciliationResult:
        """Read the trusted baseline, evaluate and persist under one fact-key lock."""
        ...

    async def enqueue_review(self, item: ReviewItem) -> None: ...


class JobQueue(Protocol):
    async def enqueue(self, job: CollectionJob) -> CollectionJob: ...

    async def claim(self, *, worker_id: str, limit: int, lease_seconds: int) -> Sequence[CollectionJob]: ...

    async def acknowledge(self, *, job_id: UUID, worker_id: str, lease_token: UUID) -> None: ...

    async def fail(
        self, *, job_id: UUID, worker_id: str, lease_token: UUID, error: str, retryable: bool
    ) -> None: ...

    async def heartbeat(
        self, *, job_id: UUID, worker_id: str, lease_token: UUID, lease_seconds: int
    ) -> None: ...
