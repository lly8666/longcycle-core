from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def select_projection_execution_fragments(
    execution: dict[str, Any],
    required_fragment_keys: Iterable[str],
) -> dict[str, dict[str, Any]]:
    """Select exactly the grounded-execution fragments cited by one projection.

    A grounded Evidence execution may intentionally contain heterogeneous fragments.
    Judgment and Reality projections must enforce claim-role / known-time requirements
    only on fragments they actually cite; unrelated fragments must not make an otherwise
    valid bounded projection fail merely because they carry different annotation needs.
    """

    required = tuple(dict.fromkeys(required_fragment_keys))
    required_set = set(required)
    if not required_set:
        raise ValueError("grounded projection must cite at least one evidence fragment")

    rows = execution.get("fragments")
    if not isinstance(rows, list):
        raise ValueError("grounded execution fragments must be a list")

    by_key: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("grounded execution fragment entries must be objects")
        key = row.get("fragment_key")
        if not isinstance(key, str) or not key:
            raise ValueError("grounded execution fragment is missing fragment_key")
        if key in by_key:
            raise ValueError(f"grounded execution has duplicate fragment_key: {key}")
        by_key[key] = row

    missing = sorted(required_set - set(by_key))
    if missing:
        raise ValueError(
            "grounded projection cites unavailable evidence fragments: " + ", ".join(missing)
        )

    selected: dict[str, dict[str, Any]] = {}
    for key in required:
        row = by_key[key]
        evidence_id = row.get("evidence_fragment_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError(f"grounded execution fragment {key} has no evidence_fragment_id")
        if evidence_id in selected:
            raise ValueError(
                "grounded projection selected duplicate evidence_fragment_id: " + evidence_id
            )
        selected[evidence_id] = row
    return selected
