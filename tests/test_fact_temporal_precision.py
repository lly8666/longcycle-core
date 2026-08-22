from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from longcycle.domain.enums import EntityType, FactValueKind, TemporalPrecision, ValidTimeKind
from longcycle.domain.models import FactAssertion, QualityComponents, TimeRange


def _fact_payload() -> dict[str, object]:
    return {
        "id": UUID(int=1),
        "entity_type": EntityType.EVENT,
        "entity_id": UUID(int=2),
        "field_name": "project.first_product_status",
        "value": "achieved first product",
        "value_type": FactValueKind.TEXT,
        "dimensions_complete": True,
        "valid_time_kind": ValidTimeKind.PERIOD,
        "valid_time": TimeRange(
            start=datetime(2022, 7, 1, tzinfo=UTC),
            end=datetime(2022, 8, 1, tzinfo=UTC),
        ),
        "valid_time_precision": TemporalPrecision.MONTH,
        "valid_time_text": "July 2022",
        "source_published_at": datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
        "known_at": datetime(2022, 8, 3, 16, 27, 49, tzinfo=UTC),
        "source_id": UUID(int=3),
        "document_id": UUID(int=4),
        "evidence_fragment_id": UUID(int=5),
        "extraction_run_id": UUID(int=6),
        "extractor_name": "grounded-reality-projection",
        "extractor_version": "1.0.0",
        "confidence": 1.0,
        "quality": QualityComponents(
            source_quality=1.0,
            extraction_certainty=1.0,
            entity_match=1.0,
            time_unit_completeness=1.0,
            corroboration=0.8,
            freshness=1.0,
        ),
    }


def test_month_precision_is_preserved_without_claiming_first_day() -> None:
    fact = FactAssertion.model_validate(_fact_payload())

    assert fact.valid_time_precision == TemporalPrecision.MONTH
    assert fact.valid_time_text == "July 2022"
    assert fact.metadata["_longcycle_valid_time_precision"] == "month"
    assert fact.metadata["_longcycle_valid_time_text"] == "July 2022"


def test_precision_restores_from_persisted_metadata() -> None:
    payload = _fact_payload()
    payload.pop("valid_time_precision")
    payload.pop("valid_time_text")
    payload["metadata"] = {
        "_longcycle_valid_time_precision": "month",
        "_longcycle_valid_time_text": "July 2022",
    }

    fact = FactAssertion.model_validate(payload)

    assert fact.valid_time_precision == TemporalPrecision.MONTH
    assert fact.valid_time_text == "July 2022"


def test_approximate_precision_requires_original_time_text() -> None:
    payload = _fact_payload()
    payload["valid_time_precision"] = TemporalPrecision.APPROXIMATE
    payload["valid_time_text"] = None

    with pytest.raises(ValueError, match="preserve the source time text"):
        FactAssertion.model_validate(payload)


def test_bounded_precision_requires_period_valid_time() -> None:
    payload = _fact_payload()
    payload["valid_time_kind"] = ValidTimeKind.UNKNOWN
    payload["valid_time"] = TimeRange()

    with pytest.raises(ValueError, match="requires period valid_time_kind"):
        FactAssertion.model_validate(payload)
