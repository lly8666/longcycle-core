from __future__ import annotations

from typing import Any

from longcycle.domain.models import CollectionJob

from .postgres import PostgresSupport


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: dict[str, tuple[CollectionJob, dict[str, Any]]] = {}

    async def emit(
        self,
        *,
        job: CollectionJob,
        event: dict[str, Any],
        idempotency_key: str,
    ) -> None:
        self.events.setdefault(idempotency_key, (job, event))


class PostgresOutboxEventSink(PostgresSupport):
    async def emit(
        self,
        *,
        job: CollectionJob,
        event: dict[str, Any],
        idempotency_key: str,
    ) -> None:
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            raise ValueError("outbox event requires a non-empty event_type")
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO ops.outbox_events (
                    idempotency_key, aggregate_type, aggregate_id, event_type,
                    payload, correlation_id, causation_id
                ) VALUES (%s, 'collection_job', %s, %s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (
                    idempotency_key,
                    job.id,
                    event_type,
                    self.jsonb(event),
                    job.trace_id,
                    job.parent_job_id,
                ),
            )
