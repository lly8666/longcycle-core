from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fresh_agent_continuity_drill_stays_black_box_and_bounded() -> None:
    drill = (ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md").read_text(
        encoding="utf-8"
    )
    bootstrap = (ROOT / "FRESH_AGENT_BOOTSTRAP.md").read_text(encoding="utf-8")

    assert "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V2" in drill
    assert "DUMB-01" in drill
    assert "DUMB-02" in drill
    assert "DUMB-03" in drill
    assert "external_fresh_agent_black_box" in drill
    assert "chat_history_allowed" in drill
    assert "unexpected_reads" in drill
    assert "Do not read an earlier Fresh-Agent report" in drill
    assert "Do not modify the product or handoff to make a run pass" in drill
    assert "only repository mutation authorized" in drill
    assert "write it to the **resolved active development branch**" in bootstrap


def test_fresh_agent_drill_uses_handoff_sequence_as_fixed_cadence() -> None:
    drill = (ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md").read_text(
        encoding="utf-8"
    )
    continue_here = (ROOT / "CONTINUE_HERE.md").read_text(encoding="utf-8")
    rehearsals = (
        ROOT / ".longcycle" / "handoff" / "rehearsals" / "README.md"
    ).read_text(encoding="utf-8")
    handoff = json.loads(
        (ROOT / ".longcycle" / "handoff" / "current.json").read_text(encoding="utf-8")
    )

    assert "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V2" in drill
    assert "every positive multiple of 10" in drill
    assert "continuity_sequence" in drill
    assert "Manual/event-triggered runs do not reset it" in drill
    assert "A same-Agent rehearsal never satisfies the scheduled boundary" in drill
    assert "Agent **必须主动告诉用户 Fresh-Agent drill 到期" in continue_here
    assert "不重置" in continue_here
    assert "Same-Agent rehearsals also do not satisfy" in rehearsals

    sequence = int(handoff["continuity_sequence"])
    next_boundary = ((sequence // 10) + 1) * 10
    assert next_boundary > sequence
    assert next_boundary % 10 == 0


def test_dumb_01_checks_planning_scale_and_live_refresh() -> None:
    drill = (ROOT / "docs" / "development" / "fresh-agent-continuity-drill.md").read_text(
        encoding="utf-8"
    )

    assert "live medium-term goal, short-term goal and broader `next_big_step`" in drill
    assert "one next atomic action" in drill
    assert "owning workstream/role" in drill
    assert "independently refreshed" in drill
    assert "distinct from `next_big_step`" in drill
