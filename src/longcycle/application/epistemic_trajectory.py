from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from longcycle.application.research_orchestration import (
    ORCHESTRATION_V2,
    ResearchOrchestrationSpec,
    execute_research_orchestration,
    load_orchestration_spec,
    sha256_file,
)
from longcycle.domain.enums import OutcomeSemanticRelation


_KEY_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"


class OutcomeEvaluationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1, pattern=_KEY_PATTERN)
    judgment_key: str = Field(min_length=1)
    reality_fact_key: str | None = None
    semantic_relation: OutcomeSemanticRelation


class ReplaySubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: UUID | None = None
    industry_node_id: UUID | None = None

    @model_validator(mode="after")
    def exactly_one_subject_key(self) -> "ReplaySubject":
        if (self.entity_id is None) == (self.industry_node_id is None):
            raise ValueError("replay subject requires exactly one entity_id or industry_node_id")
        return self


class ReplayCounts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reality: int = Field(ge=0)
    judgments: int = Field(ge=0)
    outcomes: int = Field(ge=0)


class ReplayCutoff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1, pattern=_KEY_PATTERN)
    knowledge_cutoff: datetime
    expected_counts: ReplayCounts | None = None

    @model_validator(mode="after")
    def aware_cutoff(self) -> "ReplayCutoff":
        if self.knowledge_cutoff.utcoffset() is None:
            raise ValueError("knowledge_cutoff must be timezone-aware")
        return self


class IntegratedReplayPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subjects: tuple[ReplaySubject, ...]
    cutoffs: tuple[ReplayCutoff, ...]
    expected_manifest_counts: ReplayCounts | None = None

    @model_validator(mode="after")
    def bounded_replay_contract(self) -> "IntegratedReplayPlan":
        if not self.subjects:
            raise ValueError("integrated replay requires at least one subject")
        if not self.cutoffs:
            raise ValueError("integrated replay requires at least one cutoff")

        subject_keys = [
            (
                str(item.entity_id) if item.entity_id is not None else None,
                str(item.industry_node_id) if item.industry_node_id is not None else None,
            )
            for item in self.subjects
        ]
        if len(set(subject_keys)) != len(subject_keys):
            raise ValueError("integrated replay subjects must be unique")

        cutoff_keys = [item.key for item in self.cutoffs]
        if len(set(cutoff_keys)) != len(cutoff_keys):
            raise ValueError("integrated replay cutoff keys must be unique")
        cutoff_times = [item.knowledge_cutoff for item in self.cutoffs]
        if cutoff_times != sorted(cutoff_times) or len(set(cutoff_times)) != len(cutoff_times):
            raise ValueError("integrated replay cutoffs must be unique and strictly increasing")
        return self


class EpistemicTrajectorySpec(BaseModel):
    """CAP-0007 composition above transport-neutral research-orchestration/v2.

    The inner contract owns preserved-material verification, Grounded Evidence and optional Reality.
    This outer bounded contract only composes already-owned Judgment, Outcome and portable replay
    executors. It does not duplicate their epistemic semantics.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    task_id: str = Field(min_length=1)
    research_orchestration_spec_path: str = Field(min_length=1)
    judgment_spec_path: str | None = None
    outcome_evaluations: tuple[OutcomeEvaluationPlan, ...] = ()
    replay: IntegratedReplayPlan | None = None

    @model_validator(mode="after")
    def valid_trajectory_shape(self) -> "EpistemicTrajectorySpec":
        if self.schema_version != "longcycle-epistemic-trajectory/v1":
            raise ValueError("unsupported epistemic trajectory schema_version")
        if self.outcome_evaluations and self.judgment_spec_path is None:
            raise ValueError("outcome evaluation requires judgment_spec_path")
        keys = [item.key for item in self.outcome_evaluations]
        if len(set(keys)) != len(keys):
            raise ValueError("outcome evaluation keys must be unique")
        return self


def _resolved_under(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository/work root: {relative_path}") from exc
    return candidate


def _clean_work_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError(f"work directory must be absent or empty: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _work_member(path: Path, work_dir: Path) -> str:
    return path.resolve().relative_to(work_dir.resolve()).as_posix()


def load_epistemic_trajectory_spec(path: Path) -> EpistemicTrajectorySpec:
    return EpistemicTrajectorySpec.model_validate_json(path.read_text(encoding="utf-8"))


def trajectory_phases(
    spec: EpistemicTrajectorySpec,
    *,
    core_has_reality: bool,
) -> tuple[str, ...]:
    phases: list[str] = ["grounded_evidence"]
    if core_has_reality:
        phases.append("reality_projection")
    if spec.judgment_spec_path is not None:
        phases.append("judgment_persistence")
    if spec.outcome_evaluations:
        phases.append("outcome_evaluation")
    if spec.replay is not None:
        phases.extend(("seal_integrated_memory", "point_in_time_replay"))
    return tuple(phases)


def _validate_judgment_execution(
    *,
    output_path: Path,
    judgment_spec_path: Path,
) -> dict[str, Any]:
    payload = _load_json(output_path, label="Judgment execution")
    if payload.get("schema_version") != "longcycle-grounded-judgment-persistence/v1":
        raise ValueError("unexpected Judgment execution schema")
    judgment_spec = _load_json(judgment_spec_path, label="Judgment projection spec")
    rows = judgment_spec.get("judgments")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Judgment projection spec must contain non-empty judgments")
    verification = payload.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("Judgment execution has no verification object")
    if verification.get("judgment_count") != len(rows):
        raise ValueError("Judgment persistence count does not match projection spec")
    for key in (
        "idempotent_reappend_passed",
        "all_first_known_times_derived_from_grounded_evidence",
        "target_precision_preserved",
    ):
        if verification.get(key) is not True:
            raise ValueError(f"Judgment verification gate failed: {key}")
    return payload


def _validate_outcome_execution(
    *,
    output_path: Path,
    plan: OutcomeEvaluationPlan,
) -> dict[str, Any]:
    payload = _load_json(output_path, label=f"Outcome execution {plan.key}")
    if payload.get("schema_version") != "longcycle-grounded-outcome-evaluation-execution/v2":
        raise ValueError("unexpected Outcome execution schema")
    if payload.get("judgment_key") != plan.judgment_key:
        raise ValueError(f"Outcome {plan.key} judgment_key mismatch")
    if plan.reality_fact_key is not None and payload.get("reality_fact_key") != plan.reality_fact_key:
        raise ValueError(f"Outcome {plan.key} reality_fact_key mismatch")
    if payload.get("semantic_relation") != plan.semantic_relation.value:
        raise ValueError(f"Outcome {plan.key} semantic_relation mismatch")
    verification = payload.get("verification")
    if not isinstance(verification, dict):
        raise ValueError(f"Outcome {plan.key} has no verification object")
    for key in (
        "postgres_persistence_completed",
        "idempotent_reappend_passed",
        "canonical_reality_linked",
        "outcome_evidence_linked",
        "outcome_known_time_preserved",
        "semantic_relation_explicit",
        "non_direct_never_claims_realization",
        "no_fake_day_level_timing_error",
    ):
        if verification.get(key) is not True:
            raise ValueError(f"Outcome {plan.key} verification gate failed: {key}")
    evaluation = payload.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ValueError(f"Outcome {plan.key} has no evaluation object")
    if plan.semantic_relation != OutcomeSemanticRelation.DIRECT_MATCH:
        if evaluation.get("evaluation_status") != "indeterminate":
            raise ValueError(f"Outcome {plan.key} non-direct relation became determinate")
        if evaluation.get("timing_relation") != "not_comparable":
            raise ValueError(f"Outcome {plan.key} non-direct relation gained timing comparison")
    return payload


def _validate_memory_manifest(
    *,
    manifest_path: Path,
    expected_counts: ReplayCounts | None,
) -> dict[str, Any]:
    payload = _load_json(manifest_path, label="sealed memory manifest")
    if payload.get("schema_version") != "longcycle-sealed-industrial-memory/v1":
        raise ValueError("unexpected sealed industrial-memory manifest schema")
    if payload.get("typed_round_trip") is not True:
        raise ValueError("sealed industrial-memory typed round-trip gate failed")
    counts = payload.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("sealed industrial-memory manifest has no counts")
    for key in ("reality", "judgments", "outcomes"):
        value = counts.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"sealed industrial-memory count is invalid: {key}")
    if expected_counts is not None:
        expected = expected_counts.model_dump(mode="json")
        if {key: counts.get(key) for key in expected} != expected:
            raise ValueError(
                f"sealed industrial-memory counts mismatch: expected {expected}, got {counts}"
            )
    return payload


def _parse_aware(value: str, *, label: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed


def validate_replay_snapshot(
    payload: dict[str, Any],
    cutoff: ReplayCutoff,
) -> ReplayCounts:
    if payload.get("schema_version") != "longcycle-integrated-no-lookahead-replay/v2":
        raise ValueError(f"replay {cutoff.key} has unexpected schema")
    actual_cutoff_raw = payload.get("knowledge_cutoff")
    if not isinstance(actual_cutoff_raw, str):
        raise ValueError(f"replay {cutoff.key} has no knowledge_cutoff")
    actual_cutoff = _parse_aware(actual_cutoff_raw, label=f"replay {cutoff.key} cutoff")
    if actual_cutoff != cutoff.knowledge_cutoff:
        raise ValueError(f"replay {cutoff.key} cutoff mismatch")

    boundary = payload.get("boundary")
    if not isinstance(boundary, dict) or not boundary:
        raise ValueError(f"replay {cutoff.key} has no boundary object")
    if any(value is not True for value in boundary.values()):
        raise ValueError(f"replay {cutoff.key} boundary gate failed")

    layers = {
        "reality": payload.get("reality"),
        "judgments": payload.get("judgments"),
        "outcomes": payload.get("outcomes"),
    }
    for layer, rows in layers.items():
        if not isinstance(rows, list):
            raise ValueError(f"replay {cutoff.key} layer {layer} is not a list")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"replay {cutoff.key} layer {layer} contains non-object row")
            known_raw = row.get("known_at")
            if not isinstance(known_raw, str):
                raise ValueError(f"replay {cutoff.key} layer {layer} row has no known_at")
            if _parse_aware(known_raw, label=f"{layer}.known_at") > cutoff.knowledge_cutoff:
                raise ValueError(f"replay {cutoff.key} leaked future {layer} row")

    counts = ReplayCounts(
        reality=len(layers["reality"]),
        judgments=len(layers["judgments"]),
        outcomes=len(layers["outcomes"]),
    )
    if cutoff.expected_counts is not None and counts != cutoff.expected_counts:
        raise ValueError(
            f"replay {cutoff.key} counts mismatch: "
            f"expected {cutoff.expected_counts.model_dump(mode='json')}, "
            f"got {counts.model_dump(mode='json')}"
        )
    return counts


def validate_replay_sequence(payloads: tuple[dict[str, Any], ...]) -> None:
    """Require additive no-lookahead snapshots; already-known typed rows may not be rewritten."""

    identity_fields = {
        "reality": "canonical_fact_version_id",
        "judgments": "judgment_id",
        "outcomes": "evaluation_id",
    }
    for earlier, later in zip(payloads, payloads[1:]):
        for layer, identity_field in identity_fields.items():
            earlier_rows = earlier.get(layer)
            later_rows = later.get(layer)
            if not isinstance(earlier_rows, list) or not isinstance(later_rows, list):
                raise ValueError(f"replay sequence has invalid {layer} layer")
            earlier_by_id = {
                str(row[identity_field]): row
                for row in earlier_rows
                if isinstance(row, dict) and row.get(identity_field) is not None
            }
            later_by_id = {
                str(row[identity_field]): row
                for row in later_rows
                if isinstance(row, dict) and row.get(identity_field) is not None
            }
            if len(earlier_by_id) != len(earlier_rows) or len(later_by_id) != len(later_rows):
                raise ValueError(f"replay sequence {layer} rows lack unique typed identity")
            missing = sorted(set(earlier_by_id) - set(later_by_id))
            if missing:
                raise ValueError(f"replay sequence lost previously-known {layer} rows: {missing}")
            rewritten = sorted(
                row_id
                for row_id, row in earlier_by_id.items()
                if later_by_id[row_id] != row
            )
            if rewritten:
                raise ValueError(f"replay sequence rewrote previously-known {layer} rows: {rewritten}")


def _subject_args(plan: IntegratedReplayPlan) -> list[str]:
    args: list[str] = []
    for subject in plan.subjects:
        if subject.entity_id is not None:
            args.extend(["--subject-id", str(subject.entity_id)])
        else:
            assert subject.industry_node_id is not None
            args.extend(["--industry-node-id", str(subject.industry_node_id)])
    return args


def execute_epistemic_trajectory(
    *,
    repo_root: Path,
    spec: EpistemicTrajectorySpec,
    material_root_path: Path,
    work_dir: Path,
    skip_db_upgrade: bool = False,
) -> dict[str, Any]:
    """Execute CAP-0007's bounded Evidence -> cognition -> Outcome -> replay composition."""

    repo_root = repo_root.resolve()
    work_dir = _clean_work_dir(work_dir)
    core_spec_path = _resolved_under(repo_root, spec.research_orchestration_spec_path)
    core_spec: ResearchOrchestrationSpec = load_orchestration_spec(core_spec_path)
    if core_spec.schema_version != ORCHESTRATION_V2:
        raise ValueError(
            "epistemic trajectory v1 requires transport-neutral research-orchestration/v2; "
            "legacy v1 remains replayable through the existing core runner"
        )
    if spec.outcome_evaluations and core_spec.reality_spec_path is None:
        raise ValueError("outcome evaluation requires a Reality phase in the core orchestration")
    if spec.replay is not None and core_spec.reality_spec_path is None and spec.judgment_spec_path is None:
        raise ValueError("integrated replay requires at least one Reality or Judgment projection")

    core_dir = work_dir / "core"
    core_result = execute_research_orchestration(
        repo_root=repo_root,
        spec=core_spec,
        material_root_path=material_root_path,
        work_dir=core_dir,
        skip_db_upgrade=skip_db_upgrade,
    )
    evidence_output = core_dir / "grounded-evidence-execution.json"
    reality_output = core_dir / "reality-execution.json"

    judgment_summary: dict[str, Any] | None = None
    judgment_output: Path | None = None
    if spec.judgment_spec_path is not None:
        judgment_spec_path = _resolved_under(repo_root, spec.judgment_spec_path)
        judgment_output = work_dir / "judgment-execution.json"
        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "execute_grounded_judgment_persistence.py"),
                str(judgment_spec_path),
                str(evidence_output),
                "--output",
                str(judgment_output),
            ]
        )
        judgment_payload = _validate_judgment_execution(
            output_path=judgment_output,
            judgment_spec_path=judgment_spec_path,
        )
        judgment_summary = {
            "spec_path": spec.judgment_spec_path,
            "artifact_member": _work_member(judgment_output, work_dir),
            "output_sha256": sha256_file(judgment_output),
            "verification": judgment_payload["verification"],
        }

    outcome_summaries: list[dict[str, Any]] = []
    if spec.outcome_evaluations:
        if judgment_output is None:
            raise ValueError("outcome evaluation has no Judgment execution")
        if not reality_output.is_file():
            raise ValueError("outcome evaluation has no Reality execution")
        for plan in spec.outcome_evaluations:
            outcome_output = work_dir / f"outcome-{plan.key}.json"
            command = [
                sys.executable,
                str(repo_root / "scripts" / "execute_grounded_outcome_evaluation.py"),
                str(judgment_output),
                str(reality_output),
                "--judgment-key",
                plan.judgment_key,
                "--semantic-relation",
                plan.semantic_relation.value,
                "--output",
                str(outcome_output),
            ]
            if plan.reality_fact_key is not None:
                command.extend(["--reality-fact-key", plan.reality_fact_key])
            _run(command)
            outcome_payload = _validate_outcome_execution(
                output_path=outcome_output,
                plan=plan,
            )
            outcome_summaries.append(
                {
                    "key": plan.key,
                    "judgment_key": plan.judgment_key,
                    "reality_fact_key": outcome_payload.get("reality_fact_key"),
                    "semantic_relation": plan.semantic_relation.value,
                    "artifact_member": _work_member(outcome_output, work_dir),
                    "output_sha256": sha256_file(outcome_output),
                    "verification": outcome_payload["verification"],
                }
            )

    replay_summary: dict[str, Any] | None = None
    if spec.replay is not None:
        database_path = work_dir / "integrated-memory.duckdb"
        manifest_path = work_dir / "integrated-memory-manifest.json"
        subject_args = _subject_args(spec.replay)
        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "export_integrated_replay_duckdb.py"),
                str(database_path),
                *subject_args,
                "--manifest-output",
                str(manifest_path),
            ]
        )
        manifest = _validate_memory_manifest(
            manifest_path=manifest_path,
            expected_counts=spec.replay.expected_manifest_counts,
        )

        replay_payloads: list[dict[str, Any]] = []
        snapshot_summaries: list[dict[str, Any]] = []
        for cutoff in spec.replay.cutoffs:
            replay_output = work_dir / f"replay-{cutoff.key}.json"
            _run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "replay_integrated_history.py"),
                    str(database_path),
                    cutoff.knowledge_cutoff.isoformat(),
                    *subject_args,
                    "--output",
                    str(replay_output),
                ]
            )
            replay_payload = _load_json(replay_output, label=f"replay {cutoff.key}")
            counts = validate_replay_snapshot(replay_payload, cutoff)
            replay_payloads.append(replay_payload)
            snapshot_summaries.append(
                {
                    "key": cutoff.key,
                    "knowledge_cutoff": cutoff.knowledge_cutoff.isoformat(),
                    "artifact_member": _work_member(replay_output, work_dir),
                    "output_sha256": sha256_file(replay_output),
                    "counts": counts.model_dump(mode="json"),
                }
            )
        validate_replay_sequence(tuple(replay_payloads))
        replay_summary = {
            "database_member": _work_member(database_path, work_dir),
            "database_sha256": sha256_file(database_path),
            "database_size_bytes": database_path.stat().st_size,
            "manifest_member": _work_member(manifest_path, work_dir),
            "manifest_sha256": sha256_file(manifest_path),
            "manifest": manifest,
            "snapshots": snapshot_summaries,
            "no_lookahead_sequence_verified": True,
        }

    return {
        "schema_version": "longcycle-epistemic-trajectory-execution/v1",
        "task_id": spec.task_id,
        "phases": list(
            trajectory_phases(
                spec,
                core_has_reality=core_spec.reality_spec_path is not None,
            )
        ),
        "core_orchestration_spec_path": spec.research_orchestration_spec_path,
        "core_orchestration": core_result,
        "judgment": judgment_summary,
        "outcomes": outcome_summaries,
        "replay": replay_summary,
    }


def execute_epistemic_trajectory_receipt(
    *,
    repo_root: Path,
    spec_path: Path,
    material_root_path: Path,
    work_dir: Path,
    output_path: Path,
    skip_db_upgrade: bool = False,
) -> dict[str, Any]:
    output_path = output_path.resolve()
    try:
        spec = load_epistemic_trajectory_spec(spec_path.resolve())
        result = execute_epistemic_trajectory(
            repo_root=repo_root,
            spec=spec,
            material_root_path=material_root_path,
            work_dir=work_dir,
            skip_db_upgrade=skip_db_upgrade,
        )
        payload: dict[str, Any] = {"ok": True, "result": result}
    except Exception as exc:
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return payload
