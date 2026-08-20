from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from longcycle.domain.enums import JobStage
from longcycle.domain.models import CollectionJob
from longcycle.ports.repository import JobQueue, LeaseLostError
from longcycle.ports.telemetry import NullTelemetry, Telemetry

JobHandler = Callable[[CollectionJob], Awaitable[None]]


class RetryableJobError(RuntimeError):
    pass


class PermanentJobError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    worker_id: str
    batch_size: int = 4
    lease_seconds: int = 120
    poll_seconds: float = 2.0
    max_concurrency: int = 4

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        if self.lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        if self.poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")


class Worker:
    def __init__(
        self,
        *,
        queue: JobQueue,
        config: WorkerConfig,
        handlers: dict[JobStage, JobHandler],
        telemetry: Telemetry | None = None,
    ) -> None:
        self.queue = queue
        self.config = config
        self.handlers = handlers
        self.telemetry = telemetry or NullTelemetry()
        self._stopping = asyncio.Event()
        self._semaphore = asyncio.Semaphore(config.max_concurrency)
        self._run_once_lock = asyncio.Lock()

    def stop(self) -> None:
        self._stopping.set()

    async def run_forever(self) -> None:
        while not self._stopping.is_set():
            processed = await self.run_once()
            if processed == 0:
                try:
                    await asyncio.wait_for(self._stopping.wait(), timeout=self.config.poll_seconds)
                except TimeoutError:
                    pass

    async def run_once(self) -> int:
        # A Worker instance owns one lease budget. Serializing public run_once
        # calls prevents a caller from claiming a second batch whose handlers
        # cannot start (and therefore cannot heartbeat) yet.
        async with self._run_once_lock:
            claim_limit = min(self.config.batch_size, self.config.max_concurrency)
            jobs = await self.queue.claim(
                worker_id=self.config.worker_id,
                limit=claim_limit,
                lease_seconds=self.config.lease_seconds,
            )
            if not jobs:
                return 0
            await asyncio.gather(*(self._run_job(job) for job in jobs))
            return len(jobs)

    async def _run_job(self, job: CollectionJob) -> None:
        async with self._semaphore:
            if job.lease_token is None:
                raise RuntimeError("claimed job has no lease token")
            handler = self.handlers.get(job.stage)
            if handler is None:
                await self._fail_if_owned(
                    job,
                    PermanentJobError(f"no handler registered for stage {job.stage}"),
                    retryable=False,
                )
                return
            handler_task = asyncio.create_task(self._invoke_handler(handler, job), name=f"handler:{job.id}")
            heartbeat_task = asyncio.create_task(self._heartbeat(job), name=f"heartbeat:{job.id}")
            try:
                done, _ = await asyncio.wait(
                    {handler_task, heartbeat_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if heartbeat_task in done:
                    heartbeat_error = heartbeat_task.exception()
                    handler_task.cancel()
                    await asyncio.gather(handler_task, return_exceptions=True)
                    if heartbeat_error is None:
                        raise RuntimeError("heartbeat stopped unexpectedly")
                    raise heartbeat_error

                await handler_task
                await self.queue.acknowledge(
                    job_id=job.id,
                    worker_id=self.config.worker_id,
                    lease_token=job.lease_token,
                )
                self.telemetry.increment("worker.jobs_succeeded", stage=job.stage.value)
            except PermanentJobError as exc:
                await self._fail_if_owned(job, exc, retryable=False)
            except RetryableJobError as exc:
                await self._fail_if_owned(job, exc, retryable=True)
            except LeaseLostError:
                handler_task.cancel()
                await asyncio.gather(handler_task, return_exceptions=True)
                self.telemetry.increment("worker.jobs_lease_lost", stage=job.stage.value)
            except Exception as exc:  # unknown failures are retried within the bounded attempt budget
                await self._fail_if_owned(job, exc, retryable=True)
            finally:
                heartbeat_task.cancel()
                if not handler_task.done():
                    handler_task.cancel()
                await asyncio.gather(handler_task, heartbeat_task, return_exceptions=True)

    async def _invoke_handler(self, handler: JobHandler, job: CollectionJob) -> None:
        with self.telemetry.span(
            "worker.job",
            job_id=str(job.id),
            trace_id=str(job.trace_id),
            stage=job.stage.value,
        ):
            await handler(job)

    async def _heartbeat(self, job: CollectionJob) -> None:
        assert job.lease_token is not None
        interval = max(0.1, self.config.lease_seconds / 3)
        while True:
            await asyncio.sleep(interval)
            await self.queue.heartbeat(
                job_id=job.id,
                worker_id=self.config.worker_id,
                lease_token=job.lease_token,
                lease_seconds=self.config.lease_seconds,
            )

    async def _fail(self, job: CollectionJob, exc: Exception, *, retryable: bool) -> None:
        assert job.lease_token is not None
        await self.queue.fail(
            job_id=job.id,
            worker_id=self.config.worker_id,
            lease_token=job.lease_token,
            error=f"{type(exc).__name__}: {exc}",
            retryable=retryable,
        )
        self.telemetry.increment(
            "worker.jobs_failed",
            stage=job.stage.value,
            retryable=str(retryable).lower(),
        )

    async def _fail_if_owned(self, job: CollectionJob, exc: Exception, *, retryable: bool) -> None:
        try:
            await self._fail(job, exc, retryable=retryable)
        except LeaseLostError:
            self.telemetry.increment("worker.jobs_lease_lost", stage=job.stage.value)
