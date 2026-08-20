from __future__ import annotations

from datetime import UTC, datetime

from longcycle.application.scheduling import SchedulePolicy
from longcycle.domain.enums import Cadence
from longcycle.domain.models import CollectionJob, CollectionPolicy

from .postgres import PostgresJobQueue, PostgresSupport


class PostgresScheduler:
    """Atomically advances due policies and enqueues one idempotent discovery slot."""

    def __init__(self, dsn: str, policy: SchedulePolicy | None = None) -> None:
        self.database = PostgresSupport(dsn)
        self.policy = policy or SchedulePolicy()

    async def tick(self, *, limit: int = 100, now: datetime | None = None) -> tuple[CollectionJob, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        now = now or datetime.now(UTC)
        jobs: list[CollectionJob] = []
        async with self.database.connection() as connection:
            lock_cursor = await connection.execute(
                "SELECT pg_try_advisory_xact_lock(hashtextextended('longcycle-scheduler', 0)) AS acquired"
            )
            lock_row = await lock_cursor.fetchone()
            if not lock_row["acquired"]:
                return ()
            due_cursor = await connection.execute(
                """
                SELECT *
                FROM ops.collection_policies
                WHERE enabled AND next_run_at IS NOT NULL AND next_run_at <= %s
                ORDER BY next_run_at, id
                FOR UPDATE SKIP LOCKED
                LIMIT %s
                """,
                (now, limit),
            )
            for row in await due_cursor.fetchall():
                collection_policy = CollectionPolicy(
                    industry_id=row["industry_node_id"],
                    cadence=Cadence(row["cadence"]),
                    heat_score=row["heat_score"],
                    data_risk_score=row["data_risk_score"],
                    consecutive_low_days=row["consecutive_low_days"],
                    event_override_until=row["event_override_until"],
                    timezone=row["timezone"],
                )
                due_at = row["next_run_at"]
                job = self.policy.discovery_job(
                    policy=collection_policy,
                    source_id=row["connector_id"],
                    target_code=row["target_code"],
                    scheduled_for=due_at,
                    policy_version=row["policy_version"],
                )
                insert_cursor = await connection.execute(
                    """
                    INSERT INTO ops.collection_jobs (
                        id, pool, stage, source_connector_id, industry_node_id, payload,
                        status, priority, available_at, attempt_count, max_attempts,
                        idempotency_key, trace_id, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (idempotency_key) DO UPDATE
                    SET idempotency_key = EXCLUDED.idempotency_key
                    RETURNING *
                    """,
                    (
                        job.id,
                        str(job.payload.get("pool", "default")),
                        job.stage.value,
                        job.source_id,
                        job.industry_id,
                        self.database.jsonb(job.payload),
                        job.status.value,
                        job.priority,
                        job.available_at,
                        job.attempt,
                        job.max_attempts,
                        job.idempotency_key,
                        job.trace_id,
                        job.created_at,
                    ),
                )
                stored = await insert_cursor.fetchone()
                jobs.append(PostgresJobQueue._job_from_row(stored))
                next_run = self.policy.next_run(collection_policy, due_at)
                await connection.execute(
                    """
                    UPDATE ops.collection_policies
                    SET last_run_at = %s, next_run_at = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (due_at, next_run, now, row["id"]),
                )
        return tuple(jobs)
