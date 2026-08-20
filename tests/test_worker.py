from __future__ import annotations

import asyncio
import unittest

from longcycle.adapters.storage.memory import InMemoryJobQueue
from longcycle.application.worker import Worker, WorkerConfig
from longcycle.domain.enums import JobStage, JobStatus
from longcycle.domain.models import CollectionJob
from longcycle.ports.repository import LeaseLostError


class _LeaseLosingQueue(InMemoryJobQueue):
    async def heartbeat(self, **kwargs: object) -> None:
        del kwargs
        raise LeaseLostError("lease was reclaimed")


class _ImmediateHeartbeatWorker(Worker):
    async def _heartbeat(self, job: CollectionJob) -> None:
        assert job.lease_token is not None
        await self.queue.heartbeat(
            job_id=job.id,
            worker_id=self.config.worker_id,
            lease_token=job.lease_token,
            lease_seconds=self.config.lease_seconds,
        )


class WorkerTest(unittest.IsolatedAsyncioTestCase):
    async def test_worker_does_not_claim_more_than_it_can_run(self) -> None:
        queue = InMemoryJobQueue()
        for index in range(5):
            await queue.enqueue(
                CollectionJob(stage=JobStage.FETCH, idempotency_key=f"{index:064x}")
            )

        async def handler(job: CollectionJob) -> None:
            del job

        worker = Worker(
            queue=queue,
            config=WorkerConfig(worker_id="worker-a", batch_size=5, max_concurrency=2),
            handlers={JobStage.FETCH: handler},
        )
        processed = await worker.run_once()

        self.assertEqual(processed, 2)
        self.assertEqual(sum(job.status == JobStatus.SUCCEEDED for job in queue.jobs.values()), 2)
        self.assertEqual(sum(job.status == JobStatus.QUEUED for job in queue.jobs.values()), 3)

    async def test_lease_loss_cancels_running_handler(self) -> None:
        queue = _LeaseLosingQueue()
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="f" * 64)
        await queue.enqueue(job)
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def handler(claimed: CollectionJob) -> None:
            del claimed
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        worker = _ImmediateHeartbeatWorker(
            queue=queue,
            config=WorkerConfig(worker_id="worker-a", batch_size=1, max_concurrency=1),
            handlers={JobStage.FETCH: handler},
        )
        processed = await asyncio.wait_for(worker.run_once(), timeout=1)

        self.assertEqual(processed, 1)
        self.assertTrue(started.is_set())
        self.assertTrue(cancelled.is_set())
        self.assertNotEqual(queue.jobs[job.id].status, JobStatus.SUCCEEDED)

    async def test_concurrent_run_once_calls_do_not_hold_idle_leases(self) -> None:
        queue = InMemoryJobQueue()
        for index in range(4):
            await queue.enqueue(
                CollectionJob(stage=JobStage.FETCH, idempotency_key=f"{index + 10:064x}")
            )

        started = 0
        first_batch_started = asyncio.Event()
        release = asyncio.Event()

        async def handler(job: CollectionJob) -> None:
            nonlocal started
            del job
            started += 1
            if started == 2:
                first_batch_started.set()
            await release.wait()

        worker = Worker(
            queue=queue,
            config=WorkerConfig(worker_id="worker-a", batch_size=2, max_concurrency=2),
            handlers={JobStage.FETCH: handler},
        )
        first = asyncio.create_task(worker.run_once())
        second = asyncio.create_task(worker.run_once())
        await asyncio.wait_for(first_batch_started.wait(), timeout=1)

        self.assertEqual(sum(job.status == JobStatus.LEASED for job in queue.jobs.values()), 2)
        self.assertEqual(sum(job.status == JobStatus.QUEUED for job in queue.jobs.values()), 2)

        release.set()
        self.assertEqual(await asyncio.gather(first, second), [2, 2])
        self.assertEqual(sum(job.status == JobStatus.SUCCEEDED for job in queue.jobs.values()), 4)


if __name__ == "__main__":
    unittest.main()
