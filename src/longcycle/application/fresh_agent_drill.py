from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


DUMB_02_PAYLOAD_SHA256 = (
    "0bbc680131c1e5a9118bc2e76f8973cd7ef1f7e4d1582c9ffc7422dcf2a29557"
)
DUMB_03_PAYLOAD_SHA256 = (
    "1382a34b0aa8c3a946e2ae4ee85829580773453e04e494f6b1f478ee4c915551"
)
EXPECTED_CUE_DIGESTS = {
    "DUMB-02": DUMB_02_PAYLOAD_SHA256,
    "DUMB-03": DUMB_03_PAYLOAD_SHA256,
}

_REPORT_NAME = re.compile(r"^fresh-agent-external-(\d+)-([0-9a-f]{7})\.json$")
_HEAD_SHA = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class FreshAgentStageTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: Literal["DUMB-01", "DUMB-02", "DUMB-03"]
    cue_source: Literal["initial_user_message", "external_user_message"]
    cue_validated: bool
    executed_after_external_cue: bool
    received_payload: str | None = None
    cue_payload_sha256: str | None = None


class FreshAgentInvalidCueAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: Literal["DUMB-02", "DUMB-03"]
    received_summary: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class FreshAgentScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: Literal["DUMB-01", "DUMB-02", "DUMB-03"]
    answer_summary: str = Field(min_length=1)
    reads: tuple[str, ...]
    authority_refs: tuple[str, ...]
    pass_: bool = Field(alias="pass")
    failure_reason: str | None = None


class FreshAgentContinuityReportV3(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_version: Literal["longcycle-fresh-agent-continuity-report/v3"]
    mode: Literal["external_fresh_agent_black_box"]
    controller_protocol: Literal["FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3"]
    subject_protocol: Literal["FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3"]
    chat_history_allowed: Literal[False]
    subject_head: str
    continuity_sequence: int = Field(gt=0)
    stage_trace: tuple[FreshAgentStageTrace, ...]
    invalid_cue_attempts: tuple[FreshAgentInvalidCueAttempt, ...] = ()
    scenario_results: tuple[FreshAgentScenarioResult, ...]
    unexpected_reads: tuple[str, ...]
    overall_conclusion: Literal["PASS", "FAIL", "STALE_SUBJECT_HEAD"]
    controller_review_required: Literal[True]
    reporter_notes: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_protocol(self) -> "FreshAgentContinuityReportV3":
        if not _HEAD_SHA.fullmatch(self.subject_head):
            raise ValueError("subject_head must be a 40-character lowercase Git SHA")

        expected_order = ("DUMB-01", "DUMB-02", "DUMB-03")
        trace_order = tuple(row.scenario_id for row in self.stage_trace)
        if trace_order != expected_order:
            raise ValueError(f"stage_trace must be exactly {expected_order}")

        result_order = tuple(row.scenario_id for row in self.scenario_results)
        if result_order != expected_order:
            raise ValueError(f"scenario_results must be exactly {expected_order}")

        stage_1 = self.stage_trace[0]
        if stage_1.cue_source != "initial_user_message":
            raise ValueError("DUMB-01 must come from the initial user message")
        if not stage_1.cue_validated:
            raise ValueError("DUMB-01 launch must be validated")
        if stage_1.executed_after_external_cue:
            raise ValueError("DUMB-01 is not executed after an external cue")
        if stage_1.received_payload is not None or stage_1.cue_payload_sha256 is not None:
            raise ValueError("DUMB-01 must not claim a hidden cue payload")

        for row in self.stage_trace[1:]:
            if row.cue_source != "external_user_message":
                raise ValueError(f"{row.scenario_id} must come from an external user message")
            if not row.cue_validated or not row.executed_after_external_cue:
                raise ValueError(f"{row.scenario_id} must follow a validated external cue")
            payload = row.received_payload
            if payload is None or not payload.strip():
                raise ValueError(f"{row.scenario_id} requires the actual received payload")
            if payload.strip().lower() in {"cue", "next", "continue"}:
                raise ValueError(f"{row.scenario_id} cannot use a trigger word as the payload")
            digest = row.cue_payload_sha256
            if digest is None or not _HEX_64.fullmatch(digest):
                raise ValueError(f"{row.scenario_id} requires a lowercase SHA-256 digest")
            computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if computed != digest:
                raise ValueError(
                    f"{row.scenario_id} payload digest mismatch: declared={digest} computed={computed}"
                )
            expected = EXPECTED_CUE_DIGESTS[row.scenario_id]
            if digest != expected:
                raise ValueError(
                    f"{row.scenario_id} payload does not match the controller-owned canonical cue"
                )

        prohibited_reads: list[str] = []
        for result in self.scenario_results:
            for read in result.reads:
                normalized = read.replace("\\", "/")
                if "docs/development/fresh-agent-continuity-drill.md" in normalized:
                    prohibited_reads.append(read)
                if (
                    ".longcycle/handoff/rehearsals/" in normalized
                    and normalized.rstrip().endswith(".json")
                ):
                    prohibited_reads.append(read)
        if prohibited_reads:
            raise ValueError(f"prohibited pre-report reads recorded: {prohibited_reads}")

        if self.overall_conclusion == "PASS":
            failed = [row.scenario_id for row in self.scenario_results if not row.pass_]
            if failed:
                raise ValueError(f"PASS report contains failed scenarios: {failed}")

        return self


def load_fresh_agent_report(path: Path) -> FreshAgentContinuityReportV3:
    return FreshAgentContinuityReportV3.model_validate_json(path.read_text(encoding="utf-8"))


def validate_report_filename(
    report: FreshAgentContinuityReportV3,
    report_path: Path,
) -> None:
    match = _REPORT_NAME.fullmatch(report_path.name)
    if match is None:
        raise ValueError("report filename does not match the Fresh-Agent external report contract")
    sequence = int(match.group(1))
    short_head = match.group(2)
    if sequence != report.continuity_sequence:
        raise ValueError("report filename sequence does not match report continuity_sequence")
    if short_head != report.subject_head[:7]:
        raise ValueError("report filename subject-head prefix does not match report subject_head")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def validate_report_git_provenance(
    root: Path,
    report_path: Path,
    report: FreshAgentContinuityReportV3,
) -> None:
    relative = report_path.resolve().relative_to(root.resolve()).as_posix()
    creation_commit = _git(
        root,
        "log",
        "--diff-filter=A",
        "-1",
        "--format=%H",
        "--",
        relative,
    )
    if not creation_commit:
        raise ValueError("cannot resolve report creation commit")

    parent = _git(root, "rev-parse", f"{creation_commit}^")
    if parent != report.subject_head:
        raise ValueError(
            "report creation commit parent must equal the pre-report subject_head"
        )

    changed = tuple(
        line
        for line in _git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            creation_commit,
        ).splitlines()
        if line
    )
    if changed != (relative,):
        raise ValueError(
            f"Fresh-Agent report commit must be report-only; changed files={changed}"
        )


def validate_fresh_agent_report(
    root: Path,
    report_path: Path,
    *,
    require_git_provenance: bool = True,
) -> FreshAgentContinuityReportV3:
    report = load_fresh_agent_report(report_path)
    validate_report_filename(report, report_path)
    if require_git_provenance:
        validate_report_git_provenance(root, report_path, report)
    return report


def report_to_canonical_json(report: FreshAgentContinuityReportV3) -> str:
    return json.dumps(
        report.model_dump(mode="json", by_alias=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
