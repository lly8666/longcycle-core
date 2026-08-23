from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capability_registry.py"


def _load_registry_module():
    spec = importlib.util.spec_from_file_location("longcycle_capability_registry_script", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load capability registry script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapabilityRegistryTest(unittest.TestCase):
    def test_audit_passes_for_repository_state(self) -> None:
        registry = _load_registry_module()
        output = StringIO()
        with redirect_stdout(output):
            registry.audit()
        self.assertIn("CAPABILITY_REGISTRY_AUDIT_PASS", output.getvalue())

    def test_trajectory_intent_routes_to_existing_point_in_time_replay_owner(self) -> None:
        registry = _load_registry_module()
        output = StringIO()
        with redirect_stdout(output):
            registry.relevant("researcher historical trajectory replay knowledge cutoff")
        rendered = output.getvalue()
        self.assertIn("[CAP-0005] Typed point-in-time industrial-memory replay", rendered)
        self.assertIn("Researcher-readable trajectory/table/graph views", rendered)

    def test_active_semantic_ownership_is_unique(self) -> None:
        registry = _load_registry_module()
        owners: dict[str, str] = {}
        for _, card in registry.load_cards():
            if card["status"] != "active":
                continue
            for semantic in card["owned_semantics"]:
                self.assertNotIn(semantic, owners)
                owners[semantic] = card["id"]
        self.assertGreaterEqual(len(owners), 20)

    def test_new_capability_requires_real_unmet_requirement_and_evidence(self) -> None:
        registry = _load_registry_module()
        active = {
            card["id"]: card
            for _, card in registry.load_cards()
            if card["status"] == "active"
        }
        base = json.loads(registry.ADMISSION_PATH.read_text(encoding="utf-8"))
        base.update(
            {
                "intent_id": "SYNTHETIC-NEW",
                "intent": "Create another replay engine",
                "disposition": "new",
                "target_capability_ids": [],
                "closest_existing_capability_ids": ["CAP-0005"],
                "rationale": "Synthetic rejection test.",
                "unmet_requirement": None,
                "evidence_refs": [],
                "planned_paths": ["src/longcycle/application/another_replay.py"],
                "proposed_capability_id": "CAP-9999",
            }
        )
        original = registry.ADMISSION_PATH
        try:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "admission.json"
                path.write_text(json.dumps(base), encoding="utf-8")
                registry.ADMISSION_PATH = path
                with self.assertRaisesRegex(
                    registry.CapabilityRegistryError,
                    "new admission requires a demonstrated unmet_requirement",
                ):
                    registry.validate_admission(active)
        finally:
            registry.ADMISSION_PATH = original

    def test_handoff_always_loads_compact_capability_index(self) -> None:
        payload = json.loads(
            (ROOT / ".longcycle" / "handoff" / "current.json").read_text(encoding="utf-8")
        )
        self.assertIn(
            ".longcycle/capabilities/active-index.json",
            payload["resume_read_set"],
        )

    def test_zero_context_rehearsal_recovers_owner_and_current_admission(self) -> None:
        registry = _load_registry_module()
        fresh_bootstrap = (ROOT / "FRESH_AGENT_BOOTSTRAP.md").read_text(encoding="utf-8")
        continue_bootstrap = (ROOT / "CONTINUE_HERE.md").read_text(encoding="utf-8")
        handoff = json.loads(
            (ROOT / ".longcycle" / "handoff" / "current.json").read_text(encoding="utf-8")
        )
        index = json.loads(
            (ROOT / ".longcycle" / "capabilities" / "active-index.json").read_text(
                encoding="utf-8"
            )
        )
        admission = json.loads(
            (ROOT / ".longcycle" / "capabilities" / "current-admission.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(".longcycle/capabilities/active-index.json", fresh_bootstrap)
        self.assertIn("capability admission/relevant lookup", continue_bootstrap)
        self.assertIn(
            ".longcycle/capabilities/active-index.json",
            handoff["resume_read_set"],
        )
        replay_owner = next(item for item in index["active"] if item["id"] == "CAP-0005")
        self.assertIn("trajectory view", replay_owner["aliases"])
        self.assertIn(admission["disposition"], registry.DISPOSITIONS)

        active_ids = {item["id"] for item in index["active"]}
        targets = admission["target_capability_ids"]
        if admission["disposition"] in {"reuse", "extend", "replace"}:
            self.assertTrue(targets)
            self.assertTrue(set(targets).issubset(active_ids))

        # Current admission already carries exact owner IDs. Fresh-agent recovery must use
        # those exact IDs directly; fuzzy relevant() search is discovery help, not authority.
        for target in targets:
            card_path = ROOT / ".longcycle" / "capabilities" / "cards" / f"{target}.json"
            self.assertTrue(card_path.exists())
            card = json.loads(card_path.read_text(encoding="utf-8"))
            self.assertEqual(card["id"], target)
            self.assertEqual(card["status"], "active")

        output = StringIO()
        with redirect_stdout(output):
            registry.relevant(admission["intent"])
        self.assertIn("CAPABILITY_RELEVANT", output.getvalue())

    def test_governance_owner_guards_all_cold_start_entrypoints(self) -> None:
        card = json.loads(
            (ROOT / ".longcycle" / "capabilities" / "cards" / "CAP-0010.json").read_text(
                encoding="utf-8"
            )
        )
        protocol_paths = {
            guard["path"]
            for guard in card["guards"]
            if guard["kind"] == "protocol"
        }
        self.assertEqual(
            protocol_paths,
            {"AGENTS.md", "CONTINUE_HERE.md", "FRESH_AGENT_BOOTSTRAP.md"},
        )

    def test_registry_carries_governance_short_medium_long_horizon(self) -> None:
        index = json.loads(
            (ROOT / ".longcycle" / "capabilities" / "active-index.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(index["governance_mode"], "converging")
        self.assertEqual(
            set(index["governance_horizon"]),
            {"short_term", "medium_term", "long_term"},
        )
        self.assertIn("core_locked", index["governance_horizon"]["long_term"])


if __name__ == "__main__":
    unittest.main()
