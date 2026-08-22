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

    def test_current_handoff_uses_split_binary_transport(self) -> None:
        checkpoint = self._checkpoint()
        manifest = self._manifest()

        self.assertEqual(checkpoint.schema_version, "longcycle-session-handoff/v5")
        self.assertEqual(checkpoint.data_plane_manifest_path, ".longcycle/handoff/data-plane.json")
        self.assertIn(checkpoint.data_plane_manifest_path, checkpoint.resume_read_set)
        self.assertEqual(manifest.schema_version, "longcycle-handoff-data-plane/v2")
        self.assertEqual(
            manifest.transport_mode,
            "github_release_sources_google_drive_generated",
        )
        self.assertEqual(manifest.missing_required_asset_action, "stop_and_report_integrity_blocker")

    def test_external_sources_use_release_and_generated_state_uses_drive(self) -> None:
        manifest = self._manifest()
        assets = {asset.asset_id: asset for asset in manifest.assets}

        source_pack = assets["evt005-fmc-counterexample-acquisition-run32572209653"]
        self.assertEqual(source_pack.role, "raw_source_acquisition_cache")
        self.assertEqual(source_pack.transport, "github_release")
        self.assertEqual(source_pack.release_tag, "longcycle-dev-binary-cache")
        self.assertIsNone(source_pack.google_drive_file_id)
        self.assertEqual(
            source_pack.sha256,
            "610e8ebd5d3bc1995fc748b1b9ab8809ac7be7674109a1b8a1477cbc71826cef",
        )

        evt003 = assets["evt003-judgment-replay-run32569365809"]
        evt004 = assets["evt004-contract-margin-replay-run32570715478"]
        self.assertEqual(evt003.transport, "google_drive")
        self.assertEqual(evt003.google_drive_file_id, "1BNbUKcB35-wExdLijs-eVbfPOpgVHN4b")
        self.assertEqual(evt004.transport, "google_drive")
        self.assertEqual(evt004.google_drive_file_id, "1RTvDPBH0xGkdTTtAn_MVZGFxNOfrLd0N")

        for asset in manifest.assets:
            if asset.role == "raw_source_acquisition_cache":
                self.assertEqual(asset.transport, "github_release")
            else:
                self.assertEqual(asset.transport, "google_drive")

    def test_manifest_does_not_treat_drive_snapshot_as_live_database_authority(self) -> None:
        manifest = self._manifest()
        self.assertIn("externally acquired", manifest.github_release_policy)
        self.assertIn("Longcycle-generated", manifest.google_drive_policy)
        self.assertIn("Do not transport a live PostgreSQL cluster", manifest.postgres_policy)
        self.assertIn("read/replay", manifest.duckdb_policy)
        self.assertIn("SHA-256", manifest.duckdb_policy)


if __name__ == "__main__":
    unittest.main()
