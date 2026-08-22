from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from longcycle.application.research_orchestration import (
    ResearchOrchestrationSpec,
    execution_phases,
    load_json_object,
    load_orchestration_spec,
    materialize_evidence_spec,
    sha256_file,
    snapshot_immutable_paths,
    verify_and_extract_source_pack,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one repository-owned Longcycle research orchestration contract: verify an "
            "immutable source pack, apply explicit Evidence-spec repairs, execute the existing "
            "Grounded Evidence path and optionally the existing Reality projection path."
        )
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--source-pack", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--skip-db-upgrade",
        action="store_true",
        help="Skip `longcycle --json db upgrade` when the caller has already migrated PostgreSQL.",
    )
    return parser


def _repo_path(repo_root: Path, relative_path: str) -> Path:
    candidate = (repo_root / relative_path).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"repository path escapes root: {relative_path}") from exc
    return candidate


def _clean_work_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError(f"work directory must be absent or empty: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _successful_evidence_result(
    *,
    output_path: Path,
    prepared_spec: dict[str, Any],
) -> dict[str, Any]:
    payload = load_json_object(output_path, label="Grounded Evidence execution")
    if payload.get("ok") is not True:
        raise ValueError("Grounded Evidence execution did not return ok=true")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("Grounded Evidence execution has no result object")

    documents = prepared_spec.get("documents")
    fragments = prepared_spec.get("fragments")
    acceptance = prepared_spec.get("acceptance")
    if not isinstance(documents, list) or not isinstance(fragments, list):
        raise ValueError("prepared Evidence spec has invalid documents/fragments")
    if not isinstance(acceptance, dict):
        raise ValueError("prepared Evidence spec has invalid acceptance")
    result_documents = result.get("documents")
    result_fragments = result.get("fragments")
    result_acceptance = result.get("acceptance")
    if not isinstance(result_documents, list) or len(result_documents) != len(documents):
        raise ValueError("Grounded Evidence execution document count does not match prepared spec")
    if not isinstance(result_fragments, list) or len(result_fragments) != len(fragments):
        raise ValueError("Grounded Evidence execution fragment count does not match prepared spec")
    if not isinstance(result_acceptance, dict):
        raise ValueError("Grounded Evidence execution has invalid acceptance result")
    expected_pairs = {
        "persisted_document_versions": acceptance.get("required_documents"),
        "persisted_evidence_fragments": acceptance.get("required_fragments"),
        "fact_assertions_created": acceptance.get("facts_created"),
        "judgment_assertions_created": acceptance.get("judgments_created"),
    }
    for result_key, expected in expected_pairs.items():
        if result_acceptance.get(result_key) != expected:
            raise ValueError(
                f"Grounded Evidence acceptance mismatch for {result_key}: "
                f"expected {expected!r}, got {result_acceptance.get(result_key)!r}"
            )
    return result


def _successful_reality_result(
    *,
    output_path: Path,
    reality_spec_path: Path,
) -> dict[str, Any]:
    result = load_json_object(output_path, label="Reality execution")
    verification = result.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("Reality execution has no verification object")
    reality_spec = load_json_object(reality_spec_path, label="Reality spec")
    facts = reality_spec.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("Reality spec must contain non-empty facts")
    expected_count = len(facts)
    if verification.get("fact_count") != expected_count:
        raise ValueError("Reality fact_count does not match Reality spec")
    if verification.get("canonical_reality_count") != expected_count:
        raise ValueError("Reality canonical row count does not match Reality spec")
    for key in (
        "all_reconciled_accept",
        "all_fact_evidence_ids_persisted",
        "all_known_times_derived_from_grounded_evidence",
        "stable_assertion_to_canonical_mapping",
        "valid_time_semantics_preserved",
        "observation_semantics_preserved",
    ):
        if verification.get(key) is not True:
            raise ValueError(f"Reality verification gate failed: {key}")
    return result


def _work_member(path: Path, work_dir: Path) -> str:
    return path.resolve().relative_to(work_dir.resolve()).as_posix()


def _execute(
    *,
    repo_root: Path,
    spec: ResearchOrchestrationSpec,
    source_pack_path: Path,
    work_dir: Path,
    skip_db_upgrade: bool,
) -> dict[str, Any]:
    before_immutable = snapshot_immutable_paths(repo_root, spec.immutable_paths)
    prepared_path = work_dir / "prepared-grounded-evidence-spec.json"
    prepared_spec, prepared = materialize_evidence_spec(
        repo_root=repo_root,
        evidence_spec_path=spec.evidence_spec_path,
        repair_paths=spec.evidence_repair_paths,
        destination=prepared_path,
    )
    material_root = work_dir / "material"
    materials = verify_and_extract_source_pack(
        source_pack_path=source_pack_path,
        source_pack_spec=spec.source_pack,
        evidence_spec=prepared_spec,
        material_root=material_root,
    )

    if not skip_db_upgrade:
        _run(["longcycle", "--json", "db", "upgrade"])

    evidence_output = work_dir / "grounded-evidence-execution.json"
    _run(
        [
            sys.executable,
            str(repo_root / "scripts" / "execute_grounded_evidence_spec.py"),
            str(prepared_path),
            "--material-root",
            str(material_root),
            "--output",
            str(evidence_output),
        ]
    )
    evidence_result = _successful_evidence_result(
        output_path=evidence_output,
        prepared_spec=prepared_spec,
    )

    reality_summary: dict[str, Any] | None = None
    if spec.reality_spec_path is not None:
        reality_spec_path = _repo_path(repo_root, spec.reality_spec_path)
        reality_output = work_dir / "reality-execution.json"
        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "execute_grounded_reality_projection.py"),
                str(reality_spec_path),
                str(evidence_output),
                "--output",
                str(reality_output),
            ]
        )
        reality_result = _successful_reality_result(
            output_path=reality_output,
            reality_spec_path=reality_spec_path,
        )
        reality_summary = {
            "spec_path": spec.reality_spec_path,
            "artifact_member": _work_member(reality_output, work_dir),
            "output_sha256": sha256_file(reality_output),
            "verification": reality_result["verification"],
        }

    after_immutable = snapshot_immutable_paths(repo_root, spec.immutable_paths)
    if before_immutable != after_immutable:
        changed = sorted(
            path
            for path in set(before_immutable) | set(after_immutable)
            if before_immutable.get(path) != after_immutable.get(path)
        )
        raise ValueError(f"immutable-path guard changed during orchestration: {changed}")

    return {
        "schema_version": "longcycle-research-orchestration-execution/v1",
        "task_id": spec.task_id,
        "phases": list(execution_phases(spec)),
        "source_pack": spec.source_pack.model_dump(mode="json"),
        "prepared_evidence_spec": {
            "artifact_member": _work_member(prepared_path, work_dir),
            "sha256": prepared.sha256,
            "repair_count": prepared.repair_count,
        },
        "materials": [item.model_dump(mode="json") for item in materials],
        "evidence": {
            "spec_path": spec.evidence_spec_path,
            "repair_paths": list(spec.evidence_repair_paths),
            "artifact_member": _work_member(evidence_output, work_dir),
            "output_sha256": sha256_file(evidence_output),
            "acceptance": evidence_result["acceptance"],
        },
        "reality": reality_summary,
        "immutable_paths": before_immutable,
    }


def main() -> int:
    args = _parser().parse_args()
    repo_root = Path.cwd().resolve()
    output_path = args.output.resolve()
    try:
        spec = load_orchestration_spec(args.spec.resolve())
        work_dir = _clean_work_dir(args.work_dir)
        source_pack_path = args.source_pack.resolve()
        result = _execute(
            repo_root=repo_root,
            spec=spec,
            source_pack_path=source_pack_path,
            work_dir=work_dir,
            skip_db_upgrade=bool(args.skip_db_upgrade),
        )
        payload: dict[str, Any] = {"ok": True, "result": result}
        exit_code = 0
    except Exception as exc:
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        exit_code = 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
