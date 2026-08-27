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


def _current_contract() -> dict[str, object]:
    return baseline._load(baseline.CHANGE_CONTRACT_PATH)


def _valid_l3_contract(*, approval: str | None = "receipt:architecture-review") -> dict[str, object]:
    contract = dict(_current_contract())
    contract.update(
        {
            "change_level": "L3",
            "architecture_change_ref": "ARCHITECTURE_BASELINE_V1.md",
            "counterexample_refs": ["commit:source-grounded-counterexample"],
            "affected_invariants": ["BL-001"],
            "compatibility_plan_ref": "docs/development/post-baseline-development.md",
            "approval_ref": approval,
        }
    )
    return contract


def test_current_baseline_contract_is_self_consistent() -> None:
    manifest, contract = baseline.validate_repository_contract()
    admission = baseline._load(ROOT / contract["admission_ref"])
    assert manifest["baseline_id"] == "architecture-v1"
    assert manifest["version"] == "1.0.0"
    assert manifest["schema_through"] == "0039"
    assert manifest["commit_resolution"] == "git_tag_target"
    assert {item["id"] for item in manifest["locked_invariants"]} == baseline.EXPECTED_INVARIANTS
    assert contract["change_level"] == "L2"
    assert contract["intent_id"] == admission["intent_id"]


def test_repository_contract_uses_frozen_tag_migration_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def frozen_prefix(ref: str) -> str:
        seen.append(ref)
        return "0039"

    monkeypatch.setattr(baseline, "_latest_migration_prefix_at_ref", frozen_prefix)
    manifest, _ = baseline.validate_repository_contract()
    assert seen == [manifest["tag"]]


def test_repository_contract_rejects_frozen_tag_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(baseline, "_latest_migration_prefix_at_ref", lambda _ref: "0040")
    with pytest.raises(baseline.BaselineValidationError, match="frozen tag"):
        baseline.validate_repository_contract()


def test_change_contract_cannot_reuse_stale_intent() -> None:
    manifest = baseline._load(ROOT / ".longcycle/baseline/v1.0.0.json")
    contract = dict(_current_contract())
    contract["intent_id"] = "STALE-ARCHITECTURE-FREEZE-INTENT"
    with pytest.raises(baseline.BaselineValidationError, match="stale change authorization"):
        baseline._validate_contract(contract, manifest=manifest)


def test_l3_requires_counterexample_and_architecture_metadata() -> None:
    manifest = baseline._load(ROOT / ".longcycle/baseline/v1.0.0.json")
    contract = dict(_current_contract())
    contract["change_level"] = "L3"
    with pytest.raises(baseline.BaselineValidationError, match="architecture_change_ref"):
        baseline._validate_contract(contract, manifest=manifest)


def test_complete_l3_contract_validates_before_protected_change() -> None:
    manifest = baseline._load(ROOT / ".longcycle/baseline/v1.0.0.json")
    baseline._validate_contract(_valid_l3_contract(), manifest=manifest)


def test_l1_l2_cannot_change_protected_baseline_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"METHODOLOGY_CORE.md"})

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        assert command[:3] == ["git", "cat-file", "-e"]
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(baseline.subprocess, "run", fake_run)
    with pytest.raises(baseline.BaselineValidationError, match="declare L3/L4"):
        baseline.validate_change_level(base_ref="origin/main", contract={"change_level": "L2"})


def test_l3_protected_change_requires_review_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"ARCHITECTURE_BASELINE_V1.md"})
    monkeypatch.setattr(
        baseline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    with pytest.raises(baseline.BaselineValidationError, match="approval_ref"):
        baseline.validate_change_level(
            base_ref="origin/main",
            contract=_valid_l3_contract(approval=None),
        )


def test_reviewed_l3_can_change_protected_baseline_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"ARCHITECTURE_BASELINE_V1.md"})
    monkeypatch.setattr(
        baseline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )
    baseline.validate_change_level(
        base_ref="origin/main",
        contract=_valid_l3_contract(),
    )


def test_initial_freeze_requires_l3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline, "_changed_paths", lambda _base: {"ARCHITECTURE_BASELINE_V1.md"})
    monkeypatch.setattr(
        baseline.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
    )
    with pytest.raises(baseline.BaselineValidationError, match="initial Architecture Baseline freeze must be L3"):
        baseline.validate_change_level(base_ref="origin/main", contract={"change_level": "L2"})
