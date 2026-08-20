from __future__ import annotations

import asyncio
import unittest

from longcycle.adapters.storage.checkpoints import InMemoryCheckpointStore
from longcycle.adapters.storage.memory import InMemoryJobQueue
from longcycle.adapters.storage.outbox import InMemoryEventSink
from longcycle.application.workflow import NextStage, PipelineDispatcher, StageResult
from longcycle.domain.enums import JobStage
from longcycle.domain.models import CollectionJob


class CountingJobQueue(InMemoryJobQueue):
    def __init__(self, *, fail_on_enqueue_call: int | None = None) -> None:
        super().__init__()
        self.enqueue_calls = 0
        self.fail_on_enqueue_call = fail_on_enqueue_call

    async def enqueue(self, job: CollectionJob) -> CollectionJob:
        self.enqueue_calls += 1
        if self.enqueue_calls == self.fail_on_enqueue_call:
            raise RuntimeError("simulated enqueue failure")
        return await super().enqueue(job)


class WorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_checkpoint_writers_fan_out_the_persisted_winner(self) -> None:
        calls = 0
        second_started = asyncio.Event()

        async def handler(job: CollectionJob) -> StageResult:
            nonlocal calls
            del job
            calls += 1
            invocation = calls
            if invocation == 1:
                await second_started.wait()
                await asyncio.sleep(0.02)
            else:
                second_started.set()
            winner = invocation == 2
            return StageResult(
                schema_version="stage-v1",
                output_reference={"winner": winner},
                next_stages=(
                    NextStage(stage=JobStage.EXTRACT, payload={"winner": winner}),
                ),
            )

        queue = InMemoryJobQueue()
        dispatcher = PipelineDispatcher(
            queue=queue,
            checkpoint_store=InMemoryCheckpointStore(),
            handlers={JobStage.FETCH: ("fetch-v1", handler)},
        )
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="b" * 64)

        first, second = await asyncio.gather(
            dispatcher.process(job),
            dispatcher.process(job),
        )

        self.assertEqual(first, second)
        self.assertEqual(first.output_reference, {"winner": True})
        self.assertEqual(len(queue.jobs), 1)
        child = next(iter(queue.jobs.values()))
        self.assertIs(child.payload["winner"], True)

    async def test_checkpoint_replays_outbox_idempotently(self) -> None:
        async def handler(job: CollectionJob) -> StageResult:
            return StageResult(
                schema_version="stage-v1",
                output_reference={"document": str(job.id)},
                emitted_events=({"event_type": "document.archived", "document": str(job.id)},),
            )

        sink = InMemoryEventSink()
        dispatcher = PipelineDispatcher(
            queue=InMemoryJobQueue(),
            checkpoint_store=InMemoryCheckpointStore(),
            handlers={JobStage.ARCHIVE: ("archive-v1", handler)},
            event_sink=sink,
        )
        job = CollectionJob(stage=JobStage.ARCHIVE, idempotency_key="a" * 64)

        await dispatcher.process(job)
        await dispatcher.process(job)

        self.assertEqual(len(sink.events), 1)

    async def test_checkpoint_prevents_duplicate_side_effects_and_fanout(self) -> None:
        calls = 0

        async def handler(job: CollectionJob) -> StageResult:
            nonlocal calls
            calls += 1
            return StageResult(
                schema_version="stage-v1",
                output_reference={"document": str(job.id)},
                next_stages=(NextStage(stage=JobStage.EXTRACT, payload={"document": str(job.id)}),),
            )

        queue = InMemoryJobQueue()
        checkpoints = InMemoryCheckpointStore()
        dispatcher = PipelineDispatcher(
            queue=queue,
            checkpoint_store=checkpoints,
            handlers={JobStage.FETCH: ("fetch-v1", handler)},
        )
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="d" * 64)
        first = await dispatcher.process(job)
        second = await dispatcher.process(job)
        self.assertEqual(first, second)
        self.assertEqual(calls, 1)
        self.assertEqual(len(queue.jobs), 1)

    async def test_checkpoint_replays_fanout_after_enqueue_crash(self) -> None:
        calls = 0

        async def handler(job: CollectionJob) -> StageResult:
            nonlocal calls
            calls += 1
            return StageResult(
                schema_version="stage-v1",
                output_reference={"document": str(job.id)},
                next_stages=(NextStage(stage=JobStage.EXTRACT, payload={"document": str(job.id)}),),
            )

        queue = CountingJobQueue(fail_on_enqueue_call=1)
        checkpoints = InMemoryCheckpointStore()
        dispatcher = PipelineDispatcher(
            queue=queue,
            checkpoint_store=checkpoints,
            handlers={JobStage.FETCH: ("fetch-v1", handler)},
        )
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="c" * 64)

        with self.assertRaisesRegex(RuntimeError, "simulated enqueue failure"):
            await dispatcher.process(job)

        result = await dispatcher.process(job)

        self.assertEqual(result.output_reference, {"document": str(job.id)})
        self.assertEqual(calls, 1)
        self.assertEqual(queue.enqueue_calls, 2)
        self.assertEqual(len(queue.jobs), 1)

    async def test_cached_result_repeats_fanout_idempotently(self) -> None:
        calls = 0

        async def handler(job: CollectionJob) -> StageResult:
            nonlocal calls
            calls += 1
            return StageResult(
                schema_version="stage-v1",
                output_reference={"document": str(job.id)},
                next_stages=(NextStage(stage=JobStage.EXTRACT, payload={"document": str(job.id)}),),
            )

        queue = CountingJobQueue()
        dispatcher = PipelineDispatcher(
            queue=queue,
            checkpoint_store=InMemoryCheckpointStore(),
            handlers={JobStage.FETCH: ("fetch-v1", handler)},
        )
        job = CollectionJob(stage=JobStage.FETCH, idempotency_key="e" * 64)

        await dispatcher.process(job)
        await dispatcher.process(job)

        self.assertEqual(calls, 1)
        self.assertEqual(queue.enqueue_calls, 2)
        self.assertEqual(len(queue.jobs), 1)
