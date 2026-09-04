from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import workstream_registry as registry

ROOT = Path(__file__).resolve().parents[1]
RESERVATION_PATH = re.compile(r"^\.longcycle/workstreams/([^/]+)/reservation\.json$")
SET_LIKE_FIELDS = {
    "exclusive_write_prefixes",
    "target_capability_ids",
    "dependencies",
}
AUTHORITY_FIELDS = tuple(
    field for field in registry.RESERVATION_FIELDS if field != "reservation_revision"
)


class ReservationTransitionError(ValueError):
    pass


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ReservationTransitionError(f"git {' '.join(args)}: {detail}")
    return completed.stdout


def _json_at_ref(ref: str, path: str) -> dict[str, Any] | None:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ReservationTransitionError(f"{path} on {ref} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ReservationTransitionError(f"{path} on {ref} must contain an object")
    return payload


def _normalized(field: str, value: Any) -> Any:
    if field in SET_LIKE_FIELDS and isinstance(value, list):
        return sorted(value)
    return value


def changed_authority_fields(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    return [
        field
        for field in AUTHORITY_FIELDS
        if _normalized(field, previous.get(field)) != _normalized(field, current.get(field))
    ]


def validate_transition(
    *,
    path: str,
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> None:
    if previous is None:
        if current is None:
            return
        revision = current.get("reservation_revision")
        if revision != 1:
            raise ReservationTransitionError(
                f"{path}: a new reservation must start at reservation_revision=1, got {revision!r}"
            )
        return

    if current is None:
        if previous.get("lifecycle_state") == "active":
            raise ReservationTransitionError(
                f"{path}: an active reservation may not be deleted; transition lifecycle_state first"
            )
        return

    previous_revision = previous.get("reservation_revision")
    current_revision = current.get("reservation_revision")
    if not isinstance(previous_revision, int) or not isinstance(current_revision, int):
        raise ReservationTransitionError(f"{path}: reservation_revision must be an integer")

    changed_fields = changed_authority_fields(previous, current)
    if changed_fields:
        expected = previous_revision + 1
        if current_revision != expected:
            raise ReservationTransitionError(
                f"{path}: main-owned reservation authority changed fields={changed_fields} but "
                f"reservation_revision did not advance exactly once; "
                f"previous={previous_revision} current={current_revision} expected={expected}"
            )
        return

    if current_revision != previous_revision:
        raise ReservationTransitionError(
            f"{path}: reservation_revision changed from {previous_revision} to {current_revision} "
            "without any main-owned authority change"
        )


def changed_reservation_paths(*, base_ref: str, head_ref: str) -> list[str]:
    output = _git(
        "diff",
        "--name-only",
        "--diff-filter=ACDMRTUXB",
        f"{base_ref}...{head_ref}",
        "--",
        ".longcycle/workstreams",
    )
    paths = [line.strip() for line in output.splitlines() if line.strip()]
    return sorted(path for path in paths if RESERVATION_PATH.fullmatch(path))


def validate(*, base_ref: str, head_ref: str = "HEAD") -> None:
    paths = changed_reservation_paths(base_ref=base_ref, head_ref=head_ref)
    for path in paths:
        validate_transition(
            path=path,
            previous=_json_at_ref(base_ref, path),
            current=_json_at_ref(head_ref, path),
        )
    print(f"RESERVATION_TRANSITION_PASS changed={len(paths)} base={base_ref} head={head_ref}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Require every main-owned reservation authority mutation to advance "
            "reservation_revision exactly once."
        )
    )
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", default="HEAD")
    args = parser.parse_args()

    try:
        validate(base_ref=args.base_ref, head_ref=args.head_ref)
    except ReservationTransitionError as exc:
        print(f"RESERVATION_TRANSITION_FAIL {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
