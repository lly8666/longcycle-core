from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fresh_agent_continuity_drill_stays_black_box_and_bounded() -> None:
    drill = (ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md").read_text(
        encoding="utf-8"
    )
    bootstrap = (ROOT / "FRESH_AGENT_BOOTSTRAP.md").read_text(encoding="utf-8")

    assert "FRESH_AGENT_CONTINUITY_DRILL_V1" in drill
    assert "DUMB-01" in drill
    assert "DUMB-02" in drill
    assert "DUMB-03" in drill
    assert "external_fresh_agent_black_box" in drill
    assert "chat_history_allowed" in drill
    assert "unexpected_reads" in drill
    assert "Do not read an earlier fresh-agent drill report" in drill
    assert "Do not modify the system to make the drill pass" in drill
    assert "only repository mutation authorized" in drill
    assert "write it to the **resolved active development branch**" in bootstrap
