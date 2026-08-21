from __future__ import annotations

from longcycle.domain.models import SourceDefinition, stable_uuid_exact

from .postgres import PostgresSupport


class PostgresSourceRegistry(PostgresSupport):
    """Small catalog writer for publisher/source-connector registration."""

    async def register(self, source: SourceDefinition) -> SourceDefinition:
        if source.publisher_domain is None:
            raise ValueError("PostgreSQL source registration requires publisher_domain")

        publisher_id = stable_uuid_exact(
            "publisher-v1",
            source.name,
            source.publisher_domain,
        )
        async with self.connection() as connection:
            publisher_cursor = await connection.execute(
                """
                INSERT INTO evidence.publishers (
                    id, canonical_name, publisher_domain, source_kind,
                    quality_grade, independence_cluster
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (canonical_name, publisher_domain) DO UPDATE
                SET source_kind = EXCLUDED.source_kind,
                    quality_grade = EXCLUDED.quality_grade,
                    independence_cluster = EXCLUDED.independence_cluster
                RETURNING id
                """,
                (
                    publisher_id,
                    source.name,
                    source.publisher_domain,
                    source.kind.value,
                    source.quality_grade.value,
                    source.syndication_cluster,
                ),
            )
            publisher_row = await publisher_cursor.fetchone()
            if publisher_row is None:
                raise RuntimeError("publisher registration did not return an identity")

            connector_cursor = await connection.execute(
                """
                INSERT INTO evidence.source_connectors (
                    id, publisher_id, name, plugin_name, endpoint_base_url,
                    enabled, rate_limit_per_minute, config
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                SET publisher_id = EXCLUDED.publisher_id,
                    plugin_name = EXCLUDED.plugin_name,
                    endpoint_base_url = EXCLUDED.endpoint_base_url,
                    enabled = EXCLUDED.enabled,
                    rate_limit_per_minute = EXCLUDED.rate_limit_per_minute,
                    config = EXCLUDED.config,
                    updated_at = now()
                RETURNING id
                """,
                (
                    source.id,
                    publisher_row["id"],
                    source.name,
                    source.plugin,
                    f"https://{source.publisher_domain}",
                    source.enabled,
                    source.rate_limit_per_minute,
                    self.jsonb(source.config),
                ),
            )
            connector_row = await connector_cursor.fetchone()
            if connector_row is None:
                raise RuntimeError("source connector registration did not return an identity")

        registered_id = connector_row["id"]
        return source if registered_id == source.id else source.model_copy(update={"id": registered_id})
