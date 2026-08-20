from __future__ import annotations

from uuid import UUID

from longcycle.application.workflow import StageResult

from .postgres import PostgresSupport


class PostgresCheckpointStore(PostgresSupport):
    async def get(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
    ) -> StageResult | None:
        async with self.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT output_reference
                FROM ops.pipeline_checkpoints
                WHERE job_id = %s AND stage = %s AND input_hash = %s AND producer_version = %s
                """,
                (job_id, stage, input_hash, producer_version),
            )
            row = await cursor.fetchone()
        return StageResult.model_validate(row["output_reference"]) if row else None

    async def save(
        self,
        *,
        job_id: UUID,
        stage: str,
        input_hash: str,
        producer_version: str,
        result: StageResult,
    ) -> StageResult:
        async with self.connection() as connection:
            await connection.execute(
                """
                INSERT INTO ops.pipeline_checkpoints (
                    job_id, stage, input_hash, output_reference, producer_version
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (job_id, stage, input_hash, producer_version) DO NOTHING
                """,
                (job_id, stage, input_hash, self.jsonb(result.model_dump(mode="json")), producer_version),
            )
            cursor = await connection.execute(
                """
                SELECT output_reference
                FROM ops.pipeline_checkpoints
                WHERE job_id = %s AND stage = %s AND input_hash = %s AND producer_version = %s
                """,
                (job_id, stage, input_hash, producer_version),
            )
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError("checkpoint insert completed without a readable row")
            return StageResult.model_validate(row["output_reference"])
