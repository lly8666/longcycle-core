from __future__ import annotations

import unittest
from pathlib import Path

from longcycle.application.handoff_data_plane import HandoffDataPlaneManifest
from longcycle.application.session_handoff import SessionHandoffCheckpoint

ROOT = Path(__file__).resolve().parents[1]


class HandoffDataPlaneTest(unittest.TestCase):
    def _checkpoint(self) -> SessionHandoffCheckpoint:
        return SessionHandoffCheckpoint.model_validate_json(
            (ROOT / ".longcycle" / "handoff" / "current.json").read_text(encoding="utf-8")
        )

    def _manifest(self) -> HandoffDataPlaneManifest:
        return HandoffDataPlaneManifest.model_validate_json(
            (ROOT / ".longcycle" / "handoff" / "data-plane.json").read_text(encoding="utf-8")
        )

    def test_current_handoff_uses_deferred_pdf_materialization_contract(self) -> None:
        checkpoint = self._checkpoint()
        manifest = self._manifest()

        self.assertEqual(checkpoint.schema_version, "longcycle-session-handoff/v5")
        self.assertEqual(checkpoint.data_plane_manifest_path, ".longcycle/handoff/data-plane.json")
        self.assertIn(checkpoint.data_plane_manifest_path, checkpoint.resume_read_set)
        self.assertEqual(manifest.schema_version, "longcycle-handoff-data-plane/v5")
        self.assertEqual(
            manifest.transport_mode,
            "google_drive_immutable_generations_pdf_locator_deferred_materialization",
        )
        self.assertIsNotNone(manifest.pdf_source_policy)
        assert manifest.pdf_source_policy is not None
        self.assertEqual(
            manifest.pdf_source_policy["states"],
            ["locator_verified", "content_verified", "materialized"],
        )
        self.assertIn("Do not create or run GitHub Actions", manifest.github_actions_pdf_policy or "")
        self.assertIn("not an integrity blocker", manifest.missing_required_asset_action)

    def test_current_assets_preserve_legacy_pdf_bytes_and_web_capture_without_new_download_gate(
        self,
    ) -> None:
        manifest = self._manifest()
        assets = {asset.asset_id: asset for asset in manifest.assets}

        pdf_cache = assets["adc-sv005-blenrep-pdf-acquisition-run32630536037"]
        self.assertEqual(pdf_cache.role, "legacy_materialized_pdf_source_cache")
        self.assertEqual(pdf_cache.transport, "github_release_legacy_materialization")
        self.assertEqual(
            pdf_cache.materialization_status,
            "materialized_legacy_reusable_not_new_default",
        )
        self.assertTrue(pdf_cache.release_tag)
        self.assertIsNone(pdf_cache.google_drive_file_id)

        web_capture = assets["adc-sv005-blenrep-web-capture-v1"]
        self.assertEqual(web_capture.role, "webpage_source_capture_capsule")
        self.assertEqual(web_capture.transport, "google_drive")
        self.assertTrue(web_capture.google_drive_file_id)
        self.assertIsNone(web_capture.release_tag)
        self.assertEqual(len(web_capture.sha256), 64)

    def test_transport_does_not_change_source_authority_or_live_database_boundary(self) -> None:
        manifest = self._manifest()
        assert manifest.pdf_source_policy is not None
        self.assertIn("Claim-scoped authority", manifest.pdf_source_policy["mainstream_source_rule"])
        self.assertIn("transport", manifest.pdf_source_policy["mainstream_source_rule"])
        self.assertIn("Do not transport a live PostgreSQL cluster", manifest.postgres_policy)
        self.assertIn("SQLite", manifest.duckdb_policy)
        self.assertIn("Google Drive", manifest.google_drive_policy)

    def test_parallel_database_handoff_declares_bounded_immutable_generation_heads(self) -> None:
        manifest = self._manifest()

        self.assertTrue(manifest.parallel_database_policy)
        self.assertTrue(manifest.drive_generation_policy)
        self.assertTrue(manifest.drive_upload_recovery_policy)
        self.assertLessEqual(len(manifest.database_generation_heads), 8)

    def test_locator_only_is_not_claim_evidence(self) -> None:
        manifest = self._manifest()
        assert manifest.pdf_source_policy is not None
        self.assertIn(
            "not sufficient to prove a claim",
            manifest.pdf_source_policy["locator_verified"],
        )
        self.assertIn(
            "sufficient to enter normal Evidence semantics",
            manifest.pdf_source_policy["content_verified"],
        )


if __name__ == "__main__":
    unittest.main()
