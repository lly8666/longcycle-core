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

from longcycle.application.reality_projection import GroundedRealityProjectionSpec  # noqa: E402


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
    if not isinstance(raw, list) or not raw or any(not isinstance(item, str) or not item.strip() for item in raw):
        raise RJORequestPreflightError("execution_contract.reality_fact_keys must be a non-empty list of strings")
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
            "R/J/O request with reality_fact_keys must reference exactly one CAP-0003 Reality projection input"
        )
    return candidates[0]


def validate_request(*, root: Path, request_path: Path) -> bool:
    request = _load_json(request_path)
    if request.get("status") != "open":
        return False

    target_keys = _target_reality_keys(request)
    if not target_keys:
        return False

    projection_relative = _reality_projection_path(request)
    projection_path = _repo_path(root, projection_relative)
    projection = GroundedRealityProjectionSpec.model_validate(_load_json(projection_path))
    facts = {item.fact_key: item for item in projection.facts}

    missing = [key for key in target_keys if key not in facts]
    if missing:
        raise RJORequestPreflightError(
            f"request {request_path.name} requires canonical Reality keys absent from {projection_relative}: {missing}"
        )

    incomplete = [key for key in target_keys if not facts[key].dimensions_complete]
    if incomplete:
        raise RJORequestPreflightError(
            f"request {request_path.name} requires canonical Reality for {incomplete}, but the CAP-0003 projection marks "
            "those facts dimensions_complete=false. That flag means the fact itself lacks required statistical dimensions "
            "and will fail closed in reconciliation; do not use it merely to express cross-entity non-comparability. "
            "If each narrow fact is complete within its truthful statistical_scope/scope_guard, declare that completeness "
            "there and keep cross-entity comparability or related_milestone Outcome semantics separate."
        )
    return True


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
        description="Fail closed when an open R/J/O request demands canonical Reality from a projection that marks target facts dimension-incomplete."
    )
    parser.add_argument("workstream_id")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = preflight_workstream(root=args.root.resolve(), workstream_id=args.workstream_id)
    except (RJORequestPreflightError, ValueError) as exc:
        print(f"RJO_REQUEST_PREFLIGHT_FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
