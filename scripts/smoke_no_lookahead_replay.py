from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import UUID

import duckdb


def run_replay(
    database: Path,
    cutoff: str,
    *,
    mode: str = "snapshot",
    previous_cutoff: str | None = None,
) -> dict[str, object]:
    command = [
        sys.executable,
        "scripts/replay_portable_evidence.py",
        "--database",
        str(database),
        "--cutoff",
        cutoff,
        "--mode",
        mode,
    ]
    if previous_cutoff is not None:
        command.extend(["--previous-cutoff", previous_cutoff])
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise TypeError("replay output must be a JSON object")
    return payload


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="longcycle-replay-smoke-") as directory:
        database = Path(directory) / "fixture.duckdb"
        connection = duckdb.connect(str(database))
        connection.execute(
            """
            CREATE TABLE evidence_timeline (
                fragment_key VARCHAR PRIMARY KEY,
                evidence_fragment_id UUID NOT NULL,
                document_version_id UUID NOT NULL,
                artifact_id UUID,
                locator VARCHAR NOT NULL,
                excerpt VARCHAR,
                claim_role VARCHAR NOT NULL,
                known_time_upper_bound TIMESTAMPTZ NOT NULL,
                known_time_precision VARCHAR NOT NULL,
                valid_effective_time JSON,
                expectation_horizon JSON
            )
            """
        )
        connection.executemany(
            "INSERT INTO evidence_timeline VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                [
                    "first-product-expectation",
                    UUID(int=1),
                    UUID(int=11),
                    None,
                    "text:1:2",
                    "expected first product in May",
                    "management_expectation_revision",
                    "2022-05-04T16:48:41+00:00",
                    "instant",
                    None,
                    json.dumps({"from": "2022-05-01", "to": "2022-05-31"}),
                ],
                [
                    "first-product-outcome",
                    UUID(int=2),
                    UUID(int=12),
                    None,
                    "text:3:4",
                    "achieved first product in July",
                    "outcome_milestone",
                    "2022-08-03T16:27:49+00:00",
                    "instant",
                    json.dumps({"from": "2022-07-01", "to": "2022-07-31"}),
                    None,
                ],
            ],
        )
        connection.close()

        before = run_replay(database, "2022-08-03T16:27:48Z")
        at = run_replay(database, "2022-08-03T16:27:49Z")
        frame = run_replay(database, "2022-08-03T16:27:49Z", mode="frame")
        transition = run_replay(
            database,
            "2022-08-03T16:27:49Z",
            mode="transition",
            previous_cutoff="2022-08-03T16:27:48Z",
        )

        before_evidence = before.get("evidence")
        at_evidence = at.get("evidence")
        if not isinstance(before_evidence, list) or not isinstance(at_evidence, list):
            raise TypeError("replay evidence must be a JSON array")
        before_keys = [item["fragment_key"] for item in before_evidence]
        at_keys = [item["fragment_key"] for item in at_evidence]
        if before_keys != ["first-product-expectation"]:
            raise AssertionError(before_keys)
        if at_keys != ["first-product-expectation", "first-product-outcome"]:
            raise AssertionError(at_keys)
        if "first-product-outcome" in json.dumps(before):
            raise AssertionError("future outcome leaked into pre-disclosure replay")
        if "hidden" in before or "future" in before:
            raise AssertionError("public replay exposed future-state metadata")

        frame_groups = frame.get("role_groups")
        if not isinstance(frame_groups, list):
            raise TypeError("replay frame role_groups must be a JSON array")
        if [group["claim_role"] for group in frame_groups] != [
            "management_expectation_revision",
            "outcome_milestone",
        ]:
            raise AssertionError(frame_groups)

        transition_groups = transition.get("new_evidence_groups")
        if not isinstance(transition_groups, list) or len(transition_groups) != 1:
            raise TypeError("replay transition must contain exactly one new role group")
        transition_keys = [
            item["fragment_key"]
            for item in transition_groups[0]["evidence"]
        ]
        if transition_keys != ["first-product-outcome"]:
            raise AssertionError(transition_keys)
        if "first-product-expectation" in json.dumps(transition):
            raise AssertionError("transition leaked retained evidence instead of only new evidence")

    print("NO_LOOKAHEAD_REPLAY_SMOKE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
