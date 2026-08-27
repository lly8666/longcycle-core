from __future__ import annotations

import asyncio
import json
import os
import subprocess
from collections.abc import Sequence
from typing import Any

import smoke_postgres_open_states as legacy


async def main() -> None:
    """Preserve the deep historical smoke while updating the CLI default contract.

    The legacy smoke contains extensive source-independence, sealed-campaign and no-lookahead
    checks. Its first CLI invocation predates the current-workspace default and therefore expects
    historical-only output without a flag. During that legacy assertion only, inject the new
    explicit ``--historical-only`` spelling. Then independently prove that an unflagged CLI call
    now includes the current research-only overlay by default.
    """

    original_run = subprocess.run

    def compatibility_run(command: Sequence[str], *args: Any, **kwargs: Any):
        normalized = list(command)
        if (
            len(normalized) >= 4
            and normalized[0] == "longcycle"
            and "research" in normalized
            and "open-states" in normalized
            and "--include-current-research" not in normalized
            and "--historical-only" not in normalized
        ):
            normalized.append("--historical-only")
        return original_run(normalized, *args, **kwargs)

    legacy.subprocess.run = compatibility_run
    try:
        await legacy.main()
    finally:
        legacy.subprocess.run = original_run

    current_run = original_run(
        [
            "longcycle",
            "--json",
            "research",
            "open-states",
            str(legacy.INDUSTRY_ID),
            legacy.CUTOFF.isoformat(),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    outer = json.loads(current_run.stdout)
    if outer.get("ok") is not True:
        raise AssertionError(outer)
    result = outer["result"]
    overlay = result["current_research_overlay"]
    if overlay["included"] is not True:
        raise AssertionError("unflagged open-states command must include current research workspace")
    if overlay["is_historical_market_knowledge"] is not False:
        raise AssertionError("default current overlay was mislabeled as historical market knowledge")
    if overlay["cutoff_filter_applied"] is not False:
        raise AssertionError("current research overlay must not be backdated through historical cutoff")
    if not overlay["hypotheses"] or not overlay["disagreements"]:
        raise AssertionError("default current workspace failed to expose seeded research-only analysis")
    if result["boundary"]["current_research_overlay_is_explicitly_separate_from_historical_cutoff"] is not True:
        raise AssertionError(result["boundary"])

    print("POSTGRES_RESEARCHER_OPEN_STATES_WORKSPACE_DEFAULT_PASS")


if __name__ == "__main__":
    asyncio.run(main())
