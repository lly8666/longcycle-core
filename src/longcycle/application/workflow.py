from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from longcycle.domain.enums import JobStage
from longcycle.domain.models import CollectionJob, canonical_json, stable_uuid
from longcycle.ports.checkpoint import CheckpointStore
from longcycle.ports.events import EventSink
from longcycle.ports.repository import JobQueue


class NextStage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: JobStage
    pool: str = "default"
    payload: dict[str, Any] = Field(default_factory=dict)
    priority_delta: float = Field(default=0, ge=-100, le=100)


class StageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    output_reference: dict[str, Any]
    next_stages: tuple[NextStage, ...] = ()
    emitted_events: tuple[dict[str, Any], ...] = ()


StageHandler = Callable[[CollectionJob], Awaitable[StageResult]]


class PipelineDispatcher:
    """Executes one immutable stage, persists a checkpoint and fans out deterministic next jobs."""

    def __init__(
        self,
        *,
        queue: JobQueue,
        checkpoint_store: CheckpointStore,
        handlers: dict[JobStage, tuple[str, StageHandler]],
        event_sink: EventSink | None = None,
    ) -> None:
        self.queue = queue
        self.checkpoint_store = checkpoint_store
        self.handlers = handlers
        self.event_sink = event_sink

    async def process(self, job: CollectionJob) -> StageResult:
        try:
            producer_version, handler = self.handlers[job.stage]
        except KeyError as exc:
            raise KeyError(f"no stage handler for {job.stage.value}") from exc
        input_hash = hashlib.sha256(
            canonical_json(
                {
                    "stage": job.stage.value,
                    "payload": job.payload,
                    "source": str(job.source_id) if job.source_id else None,
                    "industry": str(job.industry_id) if job.industry_id else None,
                    "producer_version": producer_version,
                }
            ).encode()
        ).hexdigest()
        checkpoint = await self.checkpoint_store.get(
            job_id=job.id,
            stage=job.stage.value,
            input_hash=input_hash,
            producer_version=producer_version,
        )
        if checkpoint is None:
            result = await handler(job)
            saved = await self.checkpoint_store.save(
                job_id=job.id,
                stage=job.stage.value,
                input_hash=input_hash,
                producer_version=producer_version,
                result=result,
            )
            result = cast(StageResult, saved)
        else:
            result = cast(StageResult, checkpoint)

        # Fan-out is deliberately replayed when a checkpoint is found. A worker
        # can fail after saving the stage result but before all child jobs have
        # been enqueued. Child idempotency keys make this replay safe and allow
        # a retry to fill in any missing children.
        for index, next_stage in enumerate(result.next_stages):
            key_payload = {
                "parent": str(job.id),
                "index": index,
                "stage": next_stage.stage.value,
                "payload": next_stage.payload,
                "schema": result.schema_version,
            }
            idempotency_key = hashlib.sha256(canonical_json(key_payload).encode()).hexdigest()
            await self.queue.enqueue(
                CollectionJob(
                    id=stable_uuid("job", idempotency_key),
                    stage=next_stage.stage,
                    source_id=job.source_id,
                    industry_id=job.industry_id,
                    payload={"pool": next_stage.pool, **next_stage.payload},
                    priority=max(0, min(100, job.priority + next_stage.priority_delta)),
                    idempotency_key=idempotency_key,
                    parent_job_id=job.id,
                    trace_id=job.trace_id,
                )
            )
        if result.emitted_events and self.event_sink is None:
            raise RuntimeError("stage emitted events but no event sink is configured")
        for index, event in enumerate(result.emitted_events):
            event_key = hashlib.sha256(
                canonical_json(
                    {
                        "job": str(job.id),
                        "index": index,
                        "event": event,
                        "schema": result.schema_version,
                    }
                ).encode()
            ).hexdigest()
            assert self.event_sink is not None
            await self.event_sink.emit(job=job, event=event, idempotency_key=event_key)
        return result
