from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from longcycle.application.session_handoff import SessionHandoffCheckpoint


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / ".longcycle" / "handoff" / "current.json"


def test_pre_campaign_checkpoint_rejects_campaign_paths() -> None:
    payload = json.loads(HANDOFF.read_text(encoding="utf-8"))
    assert payload["memory_campaign"] is None

    payload["active_context"]["campaign_root"] = "research_data/memory/example"
    payload["active_context"]["coverage_path"] = "research_data/memory/example/coverage-index.json"

    with pytest.raises(
        ValidationError,
        match="pre-campaign handoff must not retain active-context campaign_root or coverage_path",
    ):
        SessionHandoffCheckpoint.model_validate(payload)
