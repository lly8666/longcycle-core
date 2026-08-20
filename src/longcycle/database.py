from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AppliedMigration:
    version: str
    filename: str
    checksum: str


class MigrationRunner:
    def __init__(self, dsn: str, migrations_dir: Path) -> None:
        self.dsn = dsn
        self.migrations_dir = migrations_dir.resolve()

    async def upgrade(self) -> list[AppliedMigration]:
        if not self.migrations_dir.is_dir():
            raise FileNotFoundError(f"migration directory does not exist: {self.migrations_dir}")
        migrations = sorted(self.migrations_dir.glob("*.sql"))
        if not migrations:
            raise RuntimeError(f"no SQL migrations found in {self.migrations_dir}")

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("install longcycle-core[postgres] to run migrations") from exc

        connection = await psycopg.AsyncConnection.connect(self.dsn, autocommit=True, row_factory=dict_row)
        applied_now: list[AppliedMigration] = []
        try:
            await connection.execute("CREATE SCHEMA IF NOT EXISTS ops")
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ops.schema_migrations (
                    version text PRIMARY KEY,
                    filename text NOT NULL,
                    checksum char(64) NOT NULL,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            await connection.execute(
                "SELECT pg_advisory_lock(hashtextextended('longcycle-schema-migrations', 0))"
            )
            try:
                cursor = await connection.execute("SELECT version, filename, checksum FROM ops.schema_migrations")
                applied: dict[str, dict[str, Any]] = {row["version"]: row for row in await cursor.fetchall()}
                for migration in migrations:
                    version = migration.name.split("_", 1)[0]
                    body = migration.read_bytes()
                    checksum = hashlib.sha256(body).hexdigest()
                    if version in applied:
                        if applied[version]["checksum"] != checksum:
                            raise RuntimeError(f"applied migration was modified: {migration.name}")
                        continue
                    async with connection.transaction():
                        await connection.execute(body.decode("utf-8"))
                        await connection.execute(
                            "INSERT INTO ops.schema_migrations (version, filename, checksum) VALUES (%s, %s, %s)",
                            (version, migration.name, checksum),
                        )
                    applied_now.append(AppliedMigration(version, migration.name, checksum))
            finally:
                await connection.execute(
                    "SELECT pg_advisory_unlock(hashtextextended('longcycle-schema-migrations', 0))"
                )
        finally:
            await connection.close()
        return applied_now
