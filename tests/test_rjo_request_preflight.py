from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight_rjo_requests.py"
WORKSTREAM_ID = "example-industry-v1"
REQUEST_PATH = ".longcycle/workstreams/example-industry-v1/requests/RJO-001.json"
PROJECTION_PATH = "domain_packs/example/trajectory/reality-projection.json"
CORE_ORCHESTRATION_PATH = ".longcycle/handoff/executions/RJO-001/research-orchestration-v2.json"
TRAJECTORY_PATH = ".longcycle/handoff/executions/RJO-001/epistemic-trajectory-v1.json"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "research-orchestration-once.yml"


def _write_json(root: Path, relative: str, payload: object) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _projection(*, dimensions_complete: bool = True, fact_key: str = "example-reality") -> dict[str, object]:
    return {
        "schema_version": "longcycle-reality-projection-spec/v1",
        "task_id": "EXAMPLE-RJO-REALITY",
        "source_evidence_task_id": "EXAMPLE-EVIDENCE",
        "allowed_claim_roles": ["historical_reality_candidate"],
        "subjects": [
            {
                "id": "3e2491ec-ea70-5ce6-9739-85fd1fc1fd5a",
                "entity_type": "organization",
                "canonical_name": "Example Issuer",
            }
        ],
        "facts": [
            {
                "fact_key": fact_key,
                "evidence_fragment_key": "example-fragment",
                "subject_entity_id": "3e2491ec-ea70-5ce6-9739-85fd1fc1fd5a",
                "predicate_code": "example.metric_direction",
                "value_text": "issuer-specific metric declined",
                "valid_time_kind": "period",
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2026-01-01T00:00:00Z",
                "valid_time_precision": "year",
                "valid_time_text": "2025",
                "statistical_scope": "Example Issuer reported metric",
                "dimensions_complete": dimensions_complete,
                "metadata": {
                    "scope_guard": {
                        "directly_supports": ["Example Issuer metric"],
                        "does_not_directly_support": ["cross-issuer comparison"],
                    }
                },
            }
        ],
    }


def _request(*, fact_keys: list[str] | None = None, status: str = "open") -> dict[str, object]:
    execution_contract: dict[str, object] = {}
    if fact_keys is not None:
        execution_contract["reality_fact_keys"] = fact_keys
    return {
        "request_id": "RJO-001",
        "status": status,
        "inputs": [
            {
                "path": PROJECTION_PATH,
                "role": "CAP-0003 grounded Reality projection spec",
            }
        ],
        "execution_contract": execution_contract,
    }


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), WORKSTREAM_ID, "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_orchestration(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--orchestration-spec",
            TRAJECTORY_PATH,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_trajectory(root: Path) -> None:
    _write_json(
        root,
        CORE_ORCHESTRATION_PATH,
        {
            "schema_version": "longcycle-research-orchestration/v2",
            "task_id": "RJO-001-CORE",
            "evidence_spec_path": "evidence.json",
            "evidence_repair_paths": [],
            "reality_spec_path": PROJECTION_PATH,
            "immutable_paths": [],
        },
    )
    _write_json(
        root,
        TRAJECTORY_PATH,
        {
            "schema_version": "longcycle-epistemic-trajectory/v1",
            "task_id": "RJO-001",
            "research_orchestration_spec_path": CORE_ORCHESTRATION_PATH,
            "judgment_spec_path": None,
            "judgment_context_spec_path": None,
            "outcome_evaluations": [],
            "replay": None,
        },
    )


def test_preflight_rejects_canonical_reality_request_with_incomplete_dimensions(tmp_path: Path) -> None:
    _write_json(tmp_path, REQUEST_PATH, _request(fact_keys=["example-reality"]))
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=False))

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "RJO_REQUEST_PREFLIGHT_FAIL" in result.stderr
    assert "example-reality" in result.stderr
    assert "dimensions_complete=false" in result.stderr
    assert "cross-entity non-comparability" in result.stderr


def test_preflight_accepts_complete_narrow_reality_scope(tmp_path: Path) -> None:
    _write_json(tmp_path, REQUEST_PATH, _request(fact_keys=["example-reality"]))
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=True))

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"checked_requests": 1, "ok": True, "workstream_id": WORKSTREAM_ID}


def test_preflight_rejects_request_for_missing_reality_key(tmp_path: Path) -> None:
    _write_json(tmp_path, REQUEST_PATH, _request(fact_keys=["missing-reality"]))
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=True))

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "missing-reality" in result.stderr
    assert "absent" in result.stderr


def test_preflight_ignores_unrelated_requests_without_reality_fact_keys(tmp_path: Path) -> None:
    _write_json(tmp_path, REQUEST_PATH, _request(fact_keys=None))
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=False))

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["checked_requests"] == 0


def test_preflight_ignores_closed_rjo_request(tmp_path: Path) -> None:
    _write_json(tmp_path, REQUEST_PATH, _request(fact_keys=["example-reality"], status="closed"))
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=False))

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["checked_requests"] == 0


def test_current_main_orchestration_guard_rejects_old_branch_projection(tmp_path: Path) -> None:
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=False))
    _write_trajectory(tmp_path)

    result = _run_orchestration(tmp_path)

    assert result.returncode == 1
    assert "RJO_REQUEST_PREFLIGHT_FAIL" in result.stderr
    assert "example-reality" in result.stderr
    assert "dimensions_complete=false" in result.stderr


def test_current_main_orchestration_guard_accepts_complete_projection(tmp_path: Path) -> None:
    _write_json(tmp_path, PROJECTION_PATH, _projection(dimensions_complete=True))
    _write_trajectory(tmp_path)

    result = _run_orchestration(tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["checked_reality_projection"] == PROJECTION_PATH
    assert payload["orchestration_spec"] == TRAJECTORY_PATH


def test_issue_execution_uses_current_main_guard_before_database_execution() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    guard_call = ".ci-main-control/scripts/preflight_rjo_requests.py"

    assert "Checkout current main control-plane guards" in workflow
    assert "path: .ci-main-control" in workflow
    assert guard_call in workflow
    assert '--orchestration-spec "$ORCHESTRATION_SPEC"' in workflow
    assert workflow.index(guard_call) < workflow.index("python -m pip install")
    assert workflow.index(guard_call) < workflow.index('longcycle --json research run "${args[@]}"')
