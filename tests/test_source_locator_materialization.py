from __future__ import annotations

import unittest
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from longcycle.adapters.storage.postgres_source_locators import PostgresSourceLocatorRegistry

ROOT = Path(__file__).resolve().parents[1]


class _Cursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    async def fetchall(self) -> list[dict[str, Any]]:
        return list(self._rows)


class _Connection:
    def __init__(self, publisher_id: UUID) -> None:
        self.publisher_id = publisher_id
        self.queries: list[str] = []
        self.pending_rows: list[dict[str, Any]] = []

    async def execute(self, query: str, params: Any = None) -> _Cursor:
        normalized = " ".join(query.split())
        self.queries.append(normalized)
        if "SELECT publisher_id FROM evidence.source_connectors" in normalized:
            return _Cursor([{"publisher_id": self.publisher_id}])
        if "INSERT INTO evidence.documents" in normalized:
            assert isinstance(params, dict)
            return _Cursor(
                [
                    {
                        "id": params["id"],
                        "canonical_url": params["canonical_url"],
                        "external_id": params["external_id"],
                        "logical_title": params["logical_title"],
                        "source_media_type": params["source_media_type"],
                        "source_capture_state": params["source_capture_state"],
                        "source_locator_metadata": params["source_locator_metadata"],
                        "locator_verified_at": params["locator_verified_at"],
                        "content_verified_at": params["content_verified_at"],
                        "materialized_at": None,
                    }
                ]
            )
        if "FROM evidence.documents" in normalized and "source_capture_state <> 'materialized'" in normalized:
            return _Cursor(self.pending_rows)
        raise AssertionError(f"unexpected SQL: {normalized}")


class _Registry(PostgresSourceLocatorRegistry):
    def __init__(self, connection: _Connection) -> None:
        super().__init__("postgresql://unused")
        self.fake_connection = connection

    @asynccontextmanager
    async def connection(self):  # type: ignore[override]
        yield self.fake_connection

    @staticmethod
    def jsonb(value: Any) -> Any:
        return value


class SourceLocatorMaterializationTest(unittest.IsolatedAsyncioTestCase):
    async def test_content_verified_pdf_registers_without_fetch_or_blob_rows(self) -> None:
        connection = _Connection(uuid4())
        registry = _Registry(connection)
        source_id = uuid4()
        verified_at = datetime(2026, 8, 23, 9, 0, tzinfo=UTC)

        row = await registry.register(
            source_id=source_id,
            canonical_url="https://regulator.example/report.pdf",
            external_id="REPORT-2020-001",
            logical_title="Official report",
            document_type="regulatory_notice",
            source_media_type="application/pdf",
            source_capture_state="content_verified",
            locator_metadata={
                "file_name": "report.pdf",
                "materialization_status": "pending_materialization",
                "content_verification_mode": "interactive_pdf_read",
            },
            verified_at=verified_at,
        )

        self.assertEqual(row.source_capture_state, "content_verified")
        self.assertEqual(row.locator_verified_at, verified_at)
        self.assertEqual(row.content_verified_at, verified_at)
        self.assertEqual(
            row.source_locator_metadata["materialization_status"],
            "pending_materialization",
        )
        sql = "\n".join(connection.queries)
        self.assertIn("INSERT INTO evidence.documents", sql)
        self.assertNotIn("document_fetches", sql)
        self.assertNotIn("content_blobs", sql)
        self.assertNotIn("document_versions", sql)

    async def test_locator_registry_refuses_to_manufacture_materialized_state(self) -> None:
        registry = _Registry(_Connection(uuid4()))
        with self.assertRaisesRegex(ValueError, "locator_verified/content_verified"):
            await registry.register(
                source_id=uuid4(),
                canonical_url="https://issuer.example/filing.pdf",
                source_capture_state="materialized",
                verified_at=datetime(2026, 8, 23, 9, 0, tzinfo=UTC),
            )

    async def test_pending_pdf_materializations_are_queryable_for_later_agents(self) -> None:
        connection = _Connection(uuid4())
        pending_id = uuid4()
        connection.pending_rows = [
            {
                "id": pending_id,
                "canonical_url": "https://issuer.example/filing.pdf",
                "external_id": "FILING-1",
                "logical_title": "Issuer filing",
                "source_media_type": "application/pdf",
                "source_capture_state": "locator_verified",
                "source_locator_metadata": {"file_name": "filing.pdf"},
                "locator_verified_at": datetime(2026, 8, 23, 9, 0, tzinfo=UTC),
                "content_verified_at": None,
                "materialized_at": None,
            }
        ]
        registry = _Registry(connection)

        rows = await registry.pending_pdf_materializations(limit=20)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].document_id, pending_id)
        self.assertEqual(rows[0].source_capture_state, "locator_verified")
        self.assertEqual(rows[0].source_locator_metadata["file_name"], "filing.pdf")

    def test_migration_preserves_one_document_identity_and_marks_later_versions_materialized(self) -> None:
        body = (ROOT / "migrations" / "0027_source_locator_materialization_state.sql").read_text(
            encoding="utf-8"
        )

        self.assertIn("ALTER TABLE evidence.documents", body)
        self.assertIn("locator_verified", body)
        self.assertIn("content_verified", body)
        self.assertIn("materialized", body)
        self.assertIn("source_locator_metadata jsonb", body)
        self.assertIn("AFTER INSERT ON evidence.document_versions", body)
        self.assertNotIn("CREATE TABLE evidence.source_locator", body)


if __name__ == "__main__":
    unittest.main()
