from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from longcycle.domain.enums import (
    JudgmentEvidenceRole,
    JudgmentKind,
    JudgmentTargetTimeKind,
    JudgmentValueKind,
)
from longcycle.domain.judgments import JudgmentAssertion, JudgmentEvidenceRef


def base_payload() -> dict[str, object]:
    return {
        "id": UUID(int=1),
        "speaker_name_text": "Albemarle management",
        "subject_entity_id": UUID(int=2),
        "topic_code": "project.first_product_timing",
        "judgment_kind": JudgmentKind.GUIDANCE,
        "target_time_kind": JudgmentTargetTimeKind.PERIOD,
        "target_from": datetime(2022, 5, 1, tzinfo=UTC),
        "target_to": datetime(2022, 6, 1, tzinfo=UTC),
        "value_kind": JudgmentValueKind.TEXT,
        "value_text": "first product expected in May 2022",
        "summary": "Kemerton I first product is expected in May 2022.",
        "source_published_at": datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        "first_known_at": datetime(2022, 5, 4, 16, 48, 41, tzinfo=UTC),
        "extraction_run_id": UUID(int=3),
        "source_connector_id": UUID(int=4),
        "extractor_name": "grounded-judgment-projection",
        "extractor_version": "1.0.0",
        "extraction_confidence": 1.0,
        "evidence": (
            JudgmentEvidenceRef(
                evidence_fragment_id=UUID(int=5),
                evidence_role=JudgmentEvidenceRole.STATEMENT,
            ),
        ),
    }


def test_valid_judgment_matches_period_guidance_contract() -> None:
    judgment = JudgmentAssertion.model_validate(base_payload())

    assert judgment.target_time_kind == JudgmentTargetTimeKind.PERIOD
    assert judgment.value_text == "first product expected in May 2022"
    assert judgment.evidence[0].evidence_role == JudgmentEvidenceRole.STATEMENT


def test_numeric_range_uses_one_value_representation() -> None:
    payload = base_payload()
    payload.update(
        {
            "value_kind": JudgmentValueKind.NUMERIC_RANGE,
            "value_text": None,
            "value_low": Decimal("40000"),
            "value_high": Decimal("50000"),
            "unit_code": "t",
        }
    )

    judgment = JudgmentAssertion.model_validate(payload)

    assert judgment.value_low == Decimal("40000")
    assert judgment.value_high == Decimal("50000")


def test_judgment_requires_exactly_one_subject_identity() -> None:
    payload = base_payload()
    payload["subject_industry_node_id"] = UUID(int=6)

    with pytest.raises(ValueError, match="exactly one subject"):
        JudgmentAssertion.model_validate(payload)


def test_period_target_cannot_be_empty() -> None:
    payload = base_payload()
    payload["target_from"] = None
    payload["target_to"] = None

    with pytest.raises(ValueError, match="period judgment target"):
        JudgmentAssertion.model_validate(payload)


def test_judgment_rejects_competing_value_representations() -> None:
    payload = base_payload()
    payload["value_numeric"] = Decimal("1")

    with pytest.raises(ValueError, match="exactly one representation"):
        JudgmentAssertion.model_validate(payload)


def test_judgment_requires_statement_evidence() -> None:
    payload = base_payload()
    payload["evidence"] = (
        JudgmentEvidenceRef(
            evidence_fragment_id=UUID(int=5),
            evidence_role=JudgmentEvidenceRole.CONTEXT,
        ),
    )

    with pytest.raises(ValueError, match="statement evidence"):
        JudgmentAssertion.model_validate(payload)


def test_judgment_rejects_naive_known_time() -> None:
    payload = base_payload()
    payload["first_known_at"] = datetime(2022, 5, 4, 16, 48, 41)

    with pytest.raises(ValueError, match="timezone"):
        JudgmentAssertion.model_validate(payload)
