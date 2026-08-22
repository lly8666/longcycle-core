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

    def test_current_handoff_explicitly_routes_binary_state_through_manifest(self) -> None:
        checkpoint = self._checkpoint()
        manifest = self._manifest()

        self.assertEqual(checkpoint.schema_version, "longcycle-session-handoff/v5")
        self.assertEqual(checkpoint.data_plane_manifest_path, ".longcycle/handoff/data-plane.json")
        self.assertIn(checkpoint.data_plane_manifest_path, checkpoint.resume_read_set)
        self.assertEqual(manifest.transport_mode, "sandbox_google_drive_manual_relay")
        self.assertEqual(manifest.missing_required_asset_action, "stop_and_report_integrity_blocker")

    def test_current_replay_pack_and_offline_runtime_are_both_manifested(self) -> None:
        manifest = self._manifest()
        assets = {asset.asset_id: asset for asset in manifest.assets}

        capsule = assets["kemerton-grounded-run28-capsule"]
        runtime = assets["duckdb-offline-runtime-py313-v1"]

        self.assertTrue(capsule.required_for_current_task)
        self.assertEqual(capsule.transport, "google_drive")
        self.assertEqual(capsule.sha256, "a568232b15b77696ce0a271b74fd32fb7066fb37476a58288bff68e59a00558f")
        capsule_components = {component.path: component for component in capsule.components}
        self.assertEqual(
            capsule_components["probe/kemerton-evidence.duckdb"].sha256,
            "98f01c54bcb5b3ded7c8e28974182f7aae8f6d1c32308b887df1091584a02a7e",
        )

        self.assertTrue(runtime.required_for_current_task)
        runtime_components = {component.path: component for component in runtime.components}
        wheel = next(
            component
            for path, component in runtime_components.items()
            if path.startswith("wheelhouse/duckdb-1.5.5-cp313-cp313-")
        )
        self.assertEqual(
            wheel.sha256,
            "078e6a60dd8eedde5832f45422ca5c4a6b8c837aeabd8a56ca0b7d933f588053",
        )

    def test_manifest_does_not_treat_drive_as_database_authority(self) -> None:
        manifest = self._manifest()
        self.assertIn("not the terminal archive", manifest.capacity_policy)
        self.assertIn("Do not transport a PostgreSQL cluster", manifest.postgres_policy)
        self.assertIn("read/replay", manifest.duckdb_policy)
        self.assertIn("SHA-256", manifest.duckdb_policy)


if __name__ == "__main__":
    unittest.main()
