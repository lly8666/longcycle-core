from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: marker already present: {marker}")
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


replace_once(
    "src/longcycle/application/reconciliation.py",
    "from longcycle.domain.enums import Decision, FactStatus, ValidTimeKind\n",
    "from longcycle.domain.enums import Decision, FactStatus, TemporalPrecision, ValidTimeKind\n",
)

replace_once(
    "src/longcycle/application/reconciliation.py",
    '    evaluator_version = "2.0.0"\n',
    '    evaluator_version = "2.1.0"\n',
)

replace_once(
    "src/longcycle/application/reconciliation.py",
    """        if not candidate.dimensions_complete:
            return self._review(candidate, score, "incomplete_dimensions")
        if candidate.valid_time_kind == ValidTimeKind.UNKNOWN:
            return self._review(candidate, score, "unknown_valid_time")

        supersession_issue = self._supersession_issue(candidate, existing)
""",
    """        if not candidate.dimensions_complete:
            return self._review(candidate, score, "incomplete_dimensions")
        source_supported_unknown_onset = (
            candidate.valid_time_kind == ValidTimeKind.UNKNOWN
            and candidate.valid_time.start is None
            and candidate.valid_time.end is None
            and candidate.valid_time_precision == TemporalPrecision.UNKNOWN
            and candidate.observed_at is not None
            and candidate.observed_at_precision != TemporalPrecision.UNKNOWN
            and candidate.observed_at <= candidate.known_at
        )
        if (
            candidate.valid_time_kind == ValidTimeKind.UNKNOWN
            and not source_supported_unknown_onset
        ):
            return self._review(candidate, score, "unknown_valid_time")

        supersession_issue = self._supersession_issue(candidate, existing)
""",
)

replace_once(
    "src/longcycle/application/reconciliation.py",
    """        reasons: list[str] = []
        if candidate.supersedes_id is not None:
            reasons.append("explicit_supersession")
""",
    """        reasons: list[str] = []
        if source_supported_unknown_onset:
            reasons.append("source_supported_unknown_onset")
        if candidate.supersedes_id is not None:
            reasons.append("explicit_supersession")
""",
)

replace_once(
    "tests/test_quality_and_reconciliation.py",
    """    MarketBasis,
    ValidTimeKind,
)
""",
    """    MarketBasis,
    TemporalPrecision,
    ValidTimeKind,
)
""",
)

replace_once(
    "tests/test_quality_and_reconciliation.py",
    """    def test_high_quality_fact_is_accepted(self) -> None:
        result = Reconciler().reconcile(assertion(), [])
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.status, FactStatus.TRUSTED)

""",
    """    def test_high_quality_fact_is_accepted(self) -> None:
        result = Reconciler().reconcile(assertion(), [])
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.status, FactStatus.TRUSTED)

    def test_unknown_valid_time_without_typed_observation_requires_review(self) -> None:
        candidate = assertion().model_copy(
            update={
                "valid_time_kind": ValidTimeKind.UNKNOWN,
                "valid_time": TimeRange(),
                "valid_time_precision": TemporalPrecision.UNKNOWN,
            }
        )

        result = Reconciler().reconcile(candidate, [])

        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("unknown_valid_time", result.reason_codes)

    def test_unknown_onset_with_typed_observation_can_use_quality_gate(self) -> None:
        candidate = assertion().model_copy(
            update={
                "valid_time_kind": ValidTimeKind.UNKNOWN,
                "valid_time": TimeRange(),
                "valid_time_precision": TemporalPrecision.UNKNOWN,
                "observed_at": datetime(2025, 1, 2, tzinfo=UTC),
                "observed_at_precision": TemporalPrecision.DAY,
                "observed_at_text": "as of 2025-01-02",
                "known_at": datetime(2025, 1, 3, tzinfo=UTC),
            }
        )

        result = Reconciler().reconcile(candidate, [])

        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.status, FactStatus.TRUSTED)
        self.assertIn("source_supported_unknown_onset", result.reason_codes)
        self.assertIn("quality_gate_passed", result.reason_codes)

    def test_unknown_onset_observed_after_known_time_requires_review(self) -> None:
        candidate = assertion().model_copy(
            update={
                "valid_time_kind": ValidTimeKind.UNKNOWN,
                "valid_time": TimeRange(),
                "valid_time_precision": TemporalPrecision.UNKNOWN,
                "observed_at": datetime(2025, 1, 4, tzinfo=UTC),
                "observed_at_precision": TemporalPrecision.DAY,
                "observed_at_text": "as of 2025-01-04",
                "known_at": datetime(2025, 1, 3, tzinfo=UTC),
            }
        )

        result = Reconciler().reconcile(candidate, [])

        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("unknown_valid_time", result.reason_codes)

""",
)

print("STATE_AS_OF_RECONCILIATION_PATCH_APPLIED")
