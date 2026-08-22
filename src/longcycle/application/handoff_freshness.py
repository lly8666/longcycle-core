from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


HANDOFF_MUTABLE_PATHS = frozenset(
    {
        ".longcycle/handoff/current.json",
        ".longcycle/handoff/data-plane.json",
        "docs/devlog/2026-08-21-memory-campaign-part3.md",
    }
)


@dataclass(frozen=True)
class HandoffDeltaClassification:
    """Classify repository changes after a frozen substantive checkpoint."""

    mutable_paths: tuple[str, ...]
    substantive_paths: tuple[str, ...]

    @property
    def is_handoff_only(self) -> bool:
        return not self.substantive_paths


def classify_handoff_delta(
    changed_paths: Iterable[str],
    *,
    mutable_paths: frozenset[str] = HANDOFF_MUTABLE_PATHS,
) -> HandoffDeltaClassification:
    """Partition changed paths without weakening the frozen-checkpoint contract.

    A checked-in handoff may lag the commit that contains the substantive work by
    one synchronization commit. Any path outside ``mutable_paths`` means the
    checkpoint is stale and must be regenerated from a newer substantive base.
    """

    normalized = tuple(sorted(set(changed_paths)))
    mutable = tuple(path for path in normalized if path in mutable_paths)
    substantive = tuple(path for path in normalized if path not in mutable_paths)
    return HandoffDeltaClassification(
        mutable_paths=mutable,
        substantive_paths=substantive,
    )


def require_handoff_only_delta(changed_paths: Iterable[str]) -> None:
    """Raise when a frozen handoff is followed by substantive repository work."""

    classification = classify_handoff_delta(changed_paths)
    if classification.substantive_paths:
        paths = ", ".join(classification.substantive_paths)
        raise ValueError(
            "handoff checkpoint is stale; substantive paths changed after its base: "
            f"{paths}"
        )
