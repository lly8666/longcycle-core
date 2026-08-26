from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md"
SUBJECT = ROOT / "docs" / "development" / "fresh-agent-continuity-drill-subject.md"


DUMB_02_CUE = "我模糊记得以前好像讨论过“时间不明确的事实不能被硬变成精确日期”"
DUMB_03_CUE = "我看到现在 research run / source-pack 入口已经很好用了"


def test_fresh_agent_v2_separates_controller_future_cues_from_subject_contract() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    subject = SUBJECT.read_text(encoding="utf-8")

    assert "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V2" in controller
    assert "FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V2" in subject
    assert "FRESH_AGENT_SUBJECT_NO_CONTROLLER_READ" in subject
    assert "FRESH_AGENT_SUBJECT_NO_REPORT_BEFORE_STAGE_3" in subject

    assert DUMB_02_CUE in controller
    assert DUMB_03_CUE in controller
    assert DUMB_02_CUE not in subject
    assert DUMB_03_CUE not in subject


def test_fresh_agent_v2_subject_has_machine_stable_stage_gates() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    subject = SUBJECT.read_text(encoding="utf-8")

    assert "FRESH_AGENT_SUBJECT_STAGE_1_WAIT_REQUIRED" in subject
    assert "FRESH_AGENT_SUBJECT_STAGE_2_WAIT_REQUIRED" in subject
    assert "FRESH_AGENT_SUBJECT_STAGE_3_REPORT_ALLOWED_AFTER_EXTERNAL_CUE" in subject
    assert "FRESH_AGENT_STAGE_1_COMPLETE_WAITING_FOR_EXTERNAL_CUE" in subject
    assert "FRESH_AGENT_STAGE_2_COMPLETE_WAITING_FOR_EXTERNAL_CUE" in subject
    assert "FRESH_AGENT_REPORT_AFTER_EXTERNAL_STAGE_3_ONLY" in controller
