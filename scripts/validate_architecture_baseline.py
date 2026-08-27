from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE_ROOT = ROOT / ".longcycle" / "baseline"
POINTER_PATH = BASELINE_ROOT / "current.json"
CHANGE_CONTRACT_PATH = ROOT / ".longcycle" / "change-contract" / "current.json"

EXPECTED_INVARIANTS = {f"BL-{index:03d}" for index in range(1, 13)}
CHANGE_LEVELS = {"L1", "L2", "L3", "L4"}

# These files define the Baseline contract or the semantic expectations that protect it.
# Implementation files may move/refactor under L1/L2 as long as these expectations remain green.
PROTECTED_PATHS = {
    "ARCHITECTURE_BASELINE_V1.md",
    ".longcycle/baseline/current.json",
    ".longcycle/baseline/v1.0.0.json",
    "STRATEGIC_COMPASS.md",
    "METHODOLOGY_CORE.md",
    ".longcycle/continuity/mission-fidelity.json",
    "tests/test_fact_temporal_precision.py",
    "tests/test_historical_replay.py",
    "tests/test_judgments.py",
    "tests/test_judgment_replay.py",
    "tests/test_outcome_evaluation.py",
    "tests/test_source_authority.py",
    "tests/test_source_locator_materialization.py",
    "tests/test_fact_provenance.py",
    "tests/test_capability_registry.py",
    "tests/test_session_handoff.py",
}


class BaselineValidationError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineValidationError(f"cannot read valid JSON {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BaselineValidationError(f"{path.relative_to(ROOT)} must contain an object")
    return payload


def _require_file(raw: Any, *, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise BaselineValidationError(f"{label} must be a nonblank repository path")
    path = ROOT / raw
    if not path.is_file():
        raise BaselineValidationError(f"{label} does not exist: {raw}")
    return raw


def _latest_migration_prefix() -> str:
    prefixes = []
    for path in (ROOT / "migrations").glob("[0-9][0-9][0-9][0-9]_*.sql"):
        prefixes.append(path.name[:4])
    if not prefixes:
        raise BaselineValidationError("no migrations found")
    return max(prefixes)


def validate_repository_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    pointer = _load(POINTER_PATH)
    manifest_path = ROOT / str(pointer.get("manifest", ""))
    manifest = _load(manifest_path)

    if pointer.get("schema_version") != "longcycle-architecture-baseline-pointer/v1":
        raise BaselineValidationError("unsupported baseline pointer schema")
    if manifest.get("schema_version") != "longcycle-architecture-baseline/v1":
        raise BaselineValidationError("unsupported baseline manifest schema")
    for key in ("current_baseline", "version", "tag"):
        expected_key = "baseline_id" if key == "current_baseline" else key
        if pointer.get(key) != manifest.get(expected_key):
            raise BaselineValidationError(f"baseline pointer/manifest mismatch for {key}")
    if manifest.get("commit_resolution") != "git_tag_target":
        raise BaselineValidationError("baseline commit must resolve through the immutable Git tag")

    if manifest.get("schema_through") != _latest_migration_prefix():
        raise BaselineValidationError(
            f"baseline schema_through={manifest.get('schema_through')} does not match latest migration={_latest_migration_prefix()}"
        )

    for field in (
        "strategy_path",
        "methodology_path",
        "mission_fidelity_path",
        "capability_index_path",
        "baseline_document_path",
    ):
        _require_file(manifest.get(field), label=field)

    locked = manifest.get("locked_invariants")
    if not isinstance(locked, list):
        raise BaselineValidationError("locked_invariants must be a list")
    ids = [item.get("id") for item in locked if isinstance(item, dict)]
    if len(ids) != len(locked) or set(ids) != EXPECTED_INVARIANTS or len(ids) != len(set(ids)):
        raise BaselineValidationError(
            f"locked invariant ids must be exactly {sorted(EXPECTED_INVARIANTS)}"
        )
    for item in locked:
        if not isinstance(item.get("semantic"), str) or not item["semantic"].strip():
            raise BaselineValidationError(f"{item.get('id')} must declare a semantic key")

    policy = manifest.get("change_policy")
    if not isinstance(policy, dict) or set(policy.get("levels", [])) != CHANGE_LEVELS:
        raise BaselineValidationError("manifest must declare change levels L1/L2/L3/L4")
    if policy.get("baseline_change_level") != "L3" or policy.get("mission_change_level") != "L4":
        raise BaselineValidationError("manifest L3/L4 policy is invalid")

    contexts = manifest.get("required_status_contexts")
    if not isinstance(contexts, list) or {
        "longcycle/full-ci",
        "longcycle/architecture-baseline",
    } - set(contexts):
        raise BaselineValidationError("baseline required status contexts are incomplete")

    contract = _load(CHANGE_CONTRACT_PATH)
    if contract.get("schema_version") != "longcycle-change-contract/v1":
        raise BaselineValidationError("unsupported change contract schema")
    if contract.get("baseline") != manifest.get("baseline_id"):
        raise BaselineValidationError("change contract baseline does not match current manifest")
    level = contract.get("change_level")
    if level not in CHANGE_LEVELS:
        raise BaselineValidationError(f"invalid change_level {level!r}")
    if contract.get("admission_ref") != ".longcycle/capabilities/current-admission.json":
        raise BaselineValidationError("change contract must route semantic ownership through current admission")
    _require_file(contract.get("admission_ref"), label="change contract admission_ref")
    acceptance = contract.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance or not all(
        isinstance(item, str) and item.strip() for item in acceptance
    ):
        raise BaselineValidationError("change contract requires non-empty acceptance criteria")
    return manifest, contract


def _changed_paths(base_ref: str) -> set[str]:
    command = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    try:
        result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        raise BaselineValidationError(f"cannot diff baseline gate against {base_ref}: {exc.stderr}") from exc
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def validate_change_level(*, base_ref: str | None, contract: dict[str, Any]) -> None:
    if not base_ref:
        return
    changed = _changed_paths(base_ref)
    protected_changed = sorted(changed & PROTECTED_PATHS)
    if not protected_changed:
        return

    # Initial v1 creation is itself the explicitly reviewed L3 freeze. After v1 exists on
    # the base branch, any modification of the contract or protected semantic expectations
    # requires L3/L4 before implementation/test expectations move together.
    base_has_manifest = subprocess.run(
        ["git", "cat-file", "-e", f"{base_ref}:.longcycle/baseline/current.json"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    if base_has_manifest and contract.get("change_level") not in {"L3", "L4"}:
        raise BaselineValidationError(
            "L1/L2 change modifies Baseline contract or Baseline-critical semantic tests; "
            f"declare L3/L4 and follow the architecture-change procedure first: {protected_changed}"
        )
    if not base_has_manifest and contract.get("change_level") != "L3":
        raise BaselineValidationError("initial Architecture Baseline freeze must be L3")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Longcycle Architecture Baseline")
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    try:
        manifest, contract = validate_repository_contract()
        validate_change_level(base_ref=args.base_ref, contract=contract)
    except BaselineValidationError as exc:
        print(f"ARCHITECTURE_BASELINE_ERROR: {exc}")
        return 2
    print(
        "ARCHITECTURE_BASELINE_PASS "
        f"baseline={manifest['baseline_id']} version={manifest['version']} "
        f"schema_through={manifest['schema_through']} change_level={contract['change_level']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
