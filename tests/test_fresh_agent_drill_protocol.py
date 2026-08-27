from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from longcycle.application.fresh_agent_drill import (
    DUMB_02_PAYLOAD_SHA256,
    DUMB_03_PAYLOAD_SHA256,
    FreshAgentContinuityReportV3,
)


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md"
SUBJECT = ROOT / "docs" / "development" / "fresh-agent-continuity-drill-subject.md"


def _controller_payload(controller: str, scenario_id: str) -> str:
    anchor = f"scenario_id={scenario_id}\n"
    anchor_index = controller.index(anchor)
    block = controller[anchor_index:]
    payload_start_marker = "payload_begin\n"
    payload_end_marker = "\npayload_end"
    payload_start = block.index(payload_start_marker) + len(payload_start_marker)
    payload_end = block.index(payload_end_marker, payload_start)
    return block[payload_start:payload_end]


def _valid_report_payload(controller: str) -> dict[str, object]:
    cue_2 = _controller_payload(controller, "DUMB-02")
    cue_3 = _controller_payload(controller, "DUMB-03")
    return {
        "schema_version": "longcycle-fresh-agent-continuity-report/v3",
        "mode": "external_fresh_agent_black_box",
        "controller_protocol": "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3",
        "subject_protocol": "FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3",
        "chat_history_allowed": False,
        "subject_head": "a" * 40,
        "continuity_sequence": 111,
        "stage_trace": [
            {
                "scenario_id": "DUMB-01",
                "cue_source": "initial_user_message",
                "cue_validated": True,
                "executed_after_external_cue": False,
                "received_payload": None,
                "cue_payload_sha256": None,
            },
            {
                "scenario_id": "DUMB-02",
                "cue_source": "external_user_message",
                "cue_validated": True,
                "executed_after_external_cue": True,
                "received_payload": cue_2,
                "cue_payload_sha256": DUMB_02_PAYLOAD_SHA256,
            },
            {
                "scenario_id": "DUMB-03",
                "cue_source": "external_user_message",
                "cue_validated": True,
                "executed_after_external_cue": True,
                "received_payload": cue_3,
                "cue_payload_sha256": DUMB_03_PAYLOAD_SHA256,
            },
        ],
        "invalid_cue_attempts": [],
        "scenario_results": [
            {
                "scenario_id": "DUMB-01",
                "answer_summary": "Recovered bounded live state.",
                "reads": ["STRATEGIC_COMPASS.md", ".longcycle/handoff/current.json"],
                "authority_refs": ["STRATEGIC_COMPASS.md", ".longcycle/handoff/current.json"],
                "pass": True,
                "failure_reason": None,
            },
            {
                "scenario_id": "DUMB-02",
                "answer_summary": "Used bounded history recall only as needed.",
                "reads": ["docs/development/on-demand-history-recall.md"],
                "authority_refs": ["docs/development/on-demand-history-recall.md"],
                "pass": True,
                "failure_reason": None,
            },
            {
                "scenario_id": "DUMB-03",
                "answer_summary": "Kept Memory-first recovery distinct from source execution.",
                "reads": ["METHODOLOGY_CORE.md"],
                "authority_refs": ["METHODOLOGY_CORE.md"],
                "pass": True,
                "failure_reason": None,
            },
        ],
        "unexpected_reads": [],
        "overall_conclusion": "PASS",
        "controller_review_required": True,
        "reporter_notes": "Synthetic protocol fixture.",
    }


def test_fresh_agent_v3_keeps_future_payloads_controller_only_until_delivery() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    subject = SUBJECT.read_text(encoding="utf-8")

    assert "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3" in controller
    assert "FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3" in subject
    assert "FRESH_AGENT_SUBJECT_NO_CONTROLLER_READ" in subject
    assert "FRESH_AGENT_SUBJECT_NO_REPORT_BEFORE_VALID_STAGE_3" in subject

    cue_2 = _controller_payload(controller, "DUMB-02")
    cue_3 = _controller_payload(controller, "DUMB-03")
    assert hashlib.sha256(cue_2.encode("utf-8")).hexdigest() == DUMB_02_PAYLOAD_SHA256
    assert hashlib.sha256(cue_3.encode("utf-8")).hexdigest() == DUMB_03_PAYLOAD_SHA256
    assert cue_2 not in subject
    assert cue_3 not in subject
    assert DUMB_02_PAYLOAD_SHA256 in subject
    assert DUMB_03_PAYLOAD_SHA256 in subject


def test_fresh_agent_v3_subject_distinguishes_pre_delivery_secrecy_from_post_delivery_answering() -> None:
    subject = SUBJECT.read_text(encoding="utf-8")

    assert "FRESH_AGENT_SUBJECT_READ_DELIVERED_CUE_PAYLOAD" in subject
    assert "must read that payload and answer it" in subject.lower()
    assert "The word `cue` alone is **not** a valid cue" in subject
    assert "invalid cue **does not advance the stage**" in subject.lower()
    assert "FRESH_AGENT_V3_INVALID_CUE_WAITING_FOR_DUMB_02" in subject
    assert "FRESH_AGENT_V3_INVALID_CUE_WAITING_FOR_DUMB_03" in subject
    assert "FRESH_AGENT_V3_STAGE_1_COMPLETE_WAITING_FOR_DUMB_02" in subject
    assert "FRESH_AGENT_V3_STAGE_2_COMPLETE_WAITING_FOR_DUMB_03" in subject


def test_fresh_agent_v3_valid_report_accepts_exact_controller_payloads() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    report = FreshAgentContinuityReportV3.model_validate(_valid_report_payload(controller))

    assert report.overall_conclusion == "PASS"
    assert report.stage_trace[1].cue_payload_sha256 == DUMB_02_PAYLOAD_SHA256
    assert report.stage_trace[2].cue_payload_sha256 == DUMB_03_PAYLOAD_SHA256


def test_fresh_agent_v3_literal_cue_cannot_be_reported_as_pass() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    payload = _valid_report_payload(controller)
    payload["stage_trace"][1]["received_payload"] = "cue"  # type: ignore[index]

    with pytest.raises(ValidationError, match="trigger word|payload digest mismatch"):
        FreshAgentContinuityReportV3.model_validate(payload)


def test_fresh_agent_v3_wrong_payload_cannot_be_reported_as_pass() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    payload = _valid_report_payload(controller)
    payload["stage_trace"][2]["received_payload"] = "wrong question"  # type: ignore[index]

    with pytest.raises(ValidationError, match="payload digest mismatch"):
        FreshAgentContinuityReportV3.model_validate(payload)


def test_fresh_agent_v3_rejects_controller_or_prior_report_reads() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    payload = _valid_report_payload(controller)
    payload["scenario_results"][1]["reads"] = [  # type: ignore[index]
        "docs/development/fresh-agent-continuity-drill.md"
    ]

    with pytest.raises(ValidationError, match="prohibited pre-report reads"):
        FreshAgentContinuityReportV3.model_validate(payload)
