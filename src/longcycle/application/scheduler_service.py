from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from longcycle.domain.models import CollectionJob, CollectionPolicy
from longcycle.ports.repository import JobQueue

from .scheduling import SchedulePolicy


@dataclass(frozen=True, slots=True)
class ScheduledTarget:
    policy: CollectionPolicy
    source_id: UUID
    policy_version: str
    due_at: datetime
    target_code: str = "default"


class SchedulerService:
    def __init__(self, queue: JobQueue, policy: SchedulePolicy | None = None) -> None:
        self.queue = queue
        self.policy = policy or SchedulePolicy()

    async def dispatch_due(
        self,
        targets: list[ScheduledTarget],
        *,
        now: datetime | None = None,
    ) -> list[CollectionJob]:
        now = now or datetime.now(UTC)
        enqueued: list[CollectionJob] = []
        for target in targets:
            if target.due_at > now:
                continue
            job = self.policy.discovery_job(
                policy=target.policy,
                source_id=target.source_id,
                scheduled_for=target.due_at,
                policy_version=target.policy_version,
                target_code=target.target_code,
            )
            enqueued.append(await self.queue.enqueue(job))
        return enqueued
