from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_architecture_baseline.py"
SPEC = importlib.util.spec_from_file_location("architecture_baseline_validator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


def test_current_baseline_contract_is_self_consistent() -> None:
    manifest, contract = baseline.validate_repository_contract()
    assert manifest["baseline_id"] == "architecture-v1"
    assert manifest["version"] == "1.0.0"
    assert manifest["schema_through"] == "0039"
    assert manifest["commit_resolution"] == "git_tag_target"
    assert {item["id"] for item in manifest["locked_invariants"]} == baseline.EXPECTED_INVARIANTS
    assert contract["change_level"] == "L3"


def test_l1_l2_cannot_change_protected_baseline_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"METHODOLOGY_CORE.md"})

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        # Simulate a post-freeze base where the current baseline pointer already exists.
        assert command[:3] == ["git", "cat-file", "-e"]
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(baseline.subprocess, "run", fake_run)
    with pytest.raises(baseline.BaselineValidationError, match="declare L3/L4"):
        baseline.validate_change_level(base_ref="origin/main", contract={"change_level": "L2"})


def test_l3_can_explicitly_propose_baseline_change(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"ARCHITECTURE_BASELINE_V1.md"})
    monkeypatch.setattr(
        baseline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    baseline.validate_change_level(base_ref="origin/main", contract={"change_level": "L3"})


def test_initial_freeze_requires_l3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"ARCHITECTURE_BASELINE_V1.md"})
    monkeypatch.setattr(
        baseline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
    )
    with pytest.raises(baseline.BaselineValidationError, match="initial Architecture Baseline freeze must be L3"):
        baseline.validate_change_level(base_ref="origin/main", contract={"change_level": "L2"})
