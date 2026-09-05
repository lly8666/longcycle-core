from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

class RJORequestPreflightError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RJORequestPreflightError(f"referenced file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RJORequestPreflightError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RJORequestPreflightError(f"expected JSON object at {path}")
    return payload


def _repo_path(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise RJORequestPreflightError(f"unsafe repository path: {relative!r}")
    root = root.resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RJORequestPreflightError(f"path escapes repository root: {relative!r}") from exc
    return resolved


def _target_reality_keys(request: dict[str, Any]) -> tuple[str, ...]:
    contract = request.get("execution_contract")
    if not isinstance(contract, dict):
        return ()
    raw = contract.get("reality_fact_keys")
    if raw is None:
        return ()
    if (
        not isinstance(raw, list)
        or not raw
        or any(not isinstance(item, str) or not item.strip() for item in raw)
    ):
        raise RJORequestPreflightError(
            "execution_contract.reality_fact_keys must be a non-empty list of strings"
        )
    keys = tuple(item.strip() for item in raw)
    if len(set(keys)) != len(keys):
        raise RJORequestPreflightError("execution_contract.reality_fact_keys must be unique")
    return keys


def _reality_projection_path(request: dict[str, Any]) -> str:
    inputs = request.get("inputs")
    if not isinstance(inputs, list):
        raise RJORequestPreflightError("R/J/O request with reality_fact_keys must declare inputs")
    candidates: list[str] = []
    for item in inputs:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        path = item.get("path")
        if not isinstance(role, str) or not isinstance(path, str):
            continue
        role_lower = role.lower()
        if "cap-0003" in role_lower and "reality" in role_lower and "projection" in role_lower:
            candidates.append(path)
    if len(candidates) != 1:
        raise RJORequestPreflightError(
            "R/J/O request with reality_fact_keys must reference exactly one "
            "CAP-0003 Reality projection input"
        )
    return candidates[0]


def _incomplete_fact_keys(
    *,
    root: Path,
    projection_relative: str,
    target_keys: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    # Keep full current-schema validation in the same-ref worker-fast path.
    # The issue-entry path below intentionally uses a dependency-free JSON
    # inspection so an old branch is not judged against unrelated future model
    # additions from main.
    from longcycle.application.reality_projection import GroundedRealityProjectionSpec

    projection_path = _repo_path(root, projection_relative)
    projection = GroundedRealityProjectionSpec.model_validate(_load_json(projection_path))
    facts = {item.fact_key: item for item in projection.facts}

    if target_keys is not None:
        missing = [key for key in target_keys if key not in facts]
        if missing:
            raise RJORequestPreflightError(
                f"requested canonical Reality keys are absent from {projection_relative}: {missing}"
            )
        selected = tuple(facts[key] for key in target_keys)
    else:
        selected = tuple(facts.values())
    return tuple(item.fact_key for item in selected if not item.dimensions_complete)


def _explicitly_incomplete_fact_keys(*, root: Path, projection_relative: str) -> tuple[str, ...]:
    """Read only the stable contradiction this cross-ref guard owns.

    All other schema and semantic validation remains the responsibility of the
    exact target branch's normal executor.
    """

    projection = _load_json(_repo_path(root, projection_relative))
    raw_facts = projection.get("facts")
    if not isinstance(raw_facts, list):
        return ()

    incomplete: list[str] = []
    for index, item in enumerate(raw_facts):
        if not isinstance(item, dict) or item.get("dimensions_complete") is not False:
            continue
        raw_key = item.get("fact_key")
        key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else f"facts[{index}]"
        incomplete.append(key)
    return tuple(incomplete)


def _raise_incomplete_dimensions(*, context: str, incomplete: tuple[str, ...]) -> None:
    raise RJORequestPreflightError(
        f"{context} requires canonical Reality for {list(incomplete)}, but the CAP-0003 projection marks "
        "those facts dimensions_complete=false. That flag means the fact itself lacks required statistical "
        "dimensions and will fail closed in reconciliation; do not use it merely to express cross-entity "
        "non-comparability. If each narrow fact is complete within its truthful "
        "statistical_scope/scope_guard, "
        "declare that completeness there and keep cross-entity comparability or related_milestone Outcome "
        "semantics separate."
    )


def validate_request(*, root: Path, request_path: Path) -> bool:
    request = _load_json(request_path)
    if request.get("status") != "open":
        return False

    target_keys = _target_reality_keys(request)
    if not target_keys:
        return False

    projection_relative = _reality_projection_path(request)
    incomplete = _incomplete_fact_keys(
        root=root,
        projection_relative=projection_relative,
        target_keys=target_keys,
    )
    if incomplete:
        _raise_incomplete_dimensions(
            context=f"request {request_path.name}",
            incomplete=incomplete,
        )
    return True


def validate_orchestration(*, root: Path, orchestration_relative: str) -> dict[str, Any]:
    """Validate the exact execution spec with a current-main guard.

    Issue-triggered execution always loads this guard from ``main``.  That keeps
    long-lived worker branches created before the guard was introduced from
    bypassing the same deterministic request/projection check.
    """

    execution_path = _repo_path(root, orchestration_relative)
    execution = _load_json(execution_path)
    schema = execution.get("schema_version")
    if schema == "longcycle-epistemic-trajectory/v1":
        core_relative = execution.get("research_orchestration_spec_path")
        if not isinstance(core_relative, str) or not core_relative:
            raise RJORequestPreflightError(
                "epistemic trajectory must reference research_orchestration_spec_path"
            )
        core = _load_json(_repo_path(root, core_relative))
    elif schema in {
        "longcycle-research-orchestration/v1",
        "longcycle-research-orchestration/v2",
    }:
        core = execution
    else:
        raise RJORequestPreflightError(f"unsupported orchestration schema: {schema!r}")

    reality_relative = core.get("reality_spec_path")
    if reality_relative is None:
        return {
            "ok": True,
            "orchestration_spec": orchestration_relative,
            "checked_reality_facts": 0,
        }
    if not isinstance(reality_relative, str) or not reality_relative:
        raise RJORequestPreflightError("reality_spec_path must be a repository-relative string")

    incomplete = _explicitly_incomplete_fact_keys(
        root=root,
        projection_relative=reality_relative,
    )
    if incomplete:
        _raise_incomplete_dimensions(
            context=f"orchestration {orchestration_relative}",
            incomplete=incomplete,
        )
    return {
        "ok": True,
        "orchestration_spec": orchestration_relative,
        "checked_reality_projection": reality_relative,
    }


def preflight_workstream(*, root: Path, workstream_id: str) -> dict[str, Any]:
    request_dir = root / ".longcycle" / "workstreams" / workstream_id / "requests"
    if not request_dir.exists():
        return {"ok": True, "workstream_id": workstream_id, "checked_requests": 0}

    checked = 0
    for request_path in sorted(request_dir.glob("*.json")):
        if validate_request(root=root, request_path=request_path):
            checked += 1
    return {"ok": True, "workstream_id": workstream_id, "checked_requests": checked}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fail closed when an R/J/O execution demands canonical Reality from a projection "
            "that explicitly marks target facts dimension-incomplete."
        )
    )
    parser.add_argument("workstream_id", nargs="?")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--orchestration-spec",
        help="Validate one exact research/epistemic orchestration spec instead of scanning a workstream.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if (args.workstream_id is None) == (args.orchestration_spec is None):
        print(
            "RJO_REQUEST_PREFLIGHT_FAIL: provide exactly one workstream_id or --orchestration-spec",
            file=sys.stderr,
        )
        return 2
    try:
        if args.orchestration_spec is not None:
            result = validate_orchestration(
                root=args.root.resolve(),
                orchestration_relative=args.orchestration_spec,
            )
        else:
            assert args.workstream_id is not None
            result = preflight_workstream(
                root=args.root.resolve(),
                workstream_id=args.workstream_id,
            )
    except (RJORequestPreflightError, ValueError) as exc:
        print(f"RJO_REQUEST_PREFLIGHT_FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
