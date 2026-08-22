from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise TypeError("command output must be a JSON object")
    return payload


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="longcycle-judgment-replay-smoke-") as directory:
        root = Path(directory)
        projection = root / "projection.json"
        database = root / "judgments.duckdb"
        projection.write_text(
            json.dumps(
                {
                    "schema_version": "longcycle-grounded-judgment-projection/v1",
                    "task_id": "judgment-replay-smoke",
                    "source_evidence_task_id": "evidence-smoke",
                    "source_database_sha256": "0" * 64,
                    "judgments": [
                        {
                            "judgment_key": "original-late-2021",
                            "judgment_id": "00000000-0000-0000-0000-000000000001",
                            "subject_entity_id": "00000000-0000-0000-0000-000000000010",
                            "speaker_name_text": "Management",
                            "topic_code": "project.completion",
                            "judgment_kind": "guidance",
                            "target_time_kind": "unknown",
                            "target_at": None,
                            "target_from": None,
                            "target_to": None,
                            "target_precision": "approximate",
                            "target_text": "late 2021",
                            "value_kind": "text",
                            "value_text": "completion expected in late 2021",
                            "summary": "Completion expected in late 2021.",
                            "first_known_at": "2021-02-19T16:37:48+00:00",
                            "evidence": [
                                {
                                    "evidence_fragment_id": "00000000-0000-0000-0000-000000000101"
                                }
                            ],
                        },
                        {
                            "judgment_key": "later-revision",
                            "judgment_id": "00000000-0000-0000-0000-000000000002",
                            "subject_entity_id": "00000000-0000-0000-0000-000000000010",
                            "speaker_name_text": "Management",
                            "topic_code": "project.completion",
                            "judgment_kind": "guidance",
                            "target_time_kind": "period",
                            "target_at": None,
                            "target_from": None,
                            "target_to": "2022-04-01T00:00:00+00:00",
                            "target_precision": "quarter",
                            "target_text": "by the end of Q1 2022",
                            "value_kind": "text",
                            "value_text": "completion now expected by end Q1 2022",
                            "summary": "Completion was revised to no later than end Q1 2022.",
                            "first_known_at": "2021-08-04T16:25:25+00:00",
                            "evidence": [
                                {
                                    "evidence_fragment_id": "00000000-0000-0000-0000-000000000102"
                                }
                            ],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        build = run("scripts/build_judgment_replay_duckdb.py", str(projection), str(database))
        if build.get("judgment_count") != 2:
            raise AssertionError("judgment overlay did not preserve both source judgments")

        before = run(
            "scripts/replay_portable_judgments.py",
            "--database",
            str(database),
            "--cutoff",
            "2021-08-04T16:25:24Z",
        )
        at = run(
            "scripts/replay_portable_judgments.py",
            "--database",
            str(database),
            "--cutoff",
            "2021-08-04T16:25:25Z",
        )
        before_judgments = before.get("judgments")
        at_judgments = at.get("judgments")
        if not isinstance(before_judgments, list) or not isinstance(at_judgments, list):
            raise TypeError("judgment replay output must contain arrays")
        before_keys = [item["judgment_key"] for item in before_judgments]
        at_keys = [item["judgment_key"] for item in at_judgments]
        if before_keys != ["original-late-2021"]:
            raise AssertionError(before_keys)
        if at_keys != ["original-late-2021", "later-revision"]:
            raise AssertionError(at_keys)
        if "later-revision" in json.dumps(before):
            raise AssertionError("future judgment leaked into pre-disclosure replay")
        first = before_judgments[0]
        if first["target_precision"] != "approximate" or first["target_text"] != "late 2021":
            raise AssertionError("coarse target precision was not preserved")
        if first["target_from"] is not None or first["target_to"] is not None:
            raise AssertionError("approximate target acquired fabricated date bounds")

    print(json.dumps({"ok": True, "result": "NO_LOOKAHEAD_JUDGMENT_REPLAY_SMOKE_PASS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
