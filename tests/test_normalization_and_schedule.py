from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from longcycle.adapters.storage.semantic_catalog import PostgresSemanticCatalog
from longcycle.application.normalization import AssertionNormalizer
from longcycle.application.scheduling import SchedulePolicy
from longcycle.domain.enums import (
    Cadence,
    EntityType,
    FactStatus,
    FactValueKind,
    FreightBasis,
    MarketBasis,
    ObservationFrequency,
    PriceComponent,
    TaxBasis,
)
from longcycle.domain.models import (
    CollectionPolicy,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    TimeRange,
)


class NormalizationAndScheduleTest(unittest.TestCase):
    @staticmethod
    def _quality() -> QualityComponents:
        return QualityComponents(
            source_quality=1,
            extraction_certainty=1,
            entity_match=1,
            time_unit_completeness=1,
            corroboration=1,
            freshness=1,
        )

    def test_unit_conversion_and_stable_assertion_id(self) -> None:
        item = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="capacity.nameplate",
            value="2.5 万吨",
            value_type="number",
            normalized_number=Decimal("2.5"),
            normalized_unit="万吨",
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=0.9,
            quality=QualityComponents(
                source_quality=1,
                extraction_certainty=1,
                entity_match=1,
                time_unit_completeness=1,
                corroboration=0,
                freshness=1,
            ),
        )
        normalizer = AssertionNormalizer()
        first = normalizer.normalize(item)
        second = normalizer.normalize(item.model_copy(update={"id": uuid4()}))
        rerun = normalizer.normalize(
            item.model_copy(
                update={
                    "id": uuid4(),
                    "extraction_run_id": uuid4(),
                }
            )
        )
        self.assertEqual(first.normalized_number, Decimal("25000.0"))
        self.assertEqual(first.normalized_unit, "t")
        self.assertEqual(first.id, second.id)
        self.assertNotEqual(first.id, rerun.id)

    def test_price_comparability_dimensions_and_time_identity_are_separate(self) -> None:
        base = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="price.market",
            value="100",
            value_type="number",
            normalized_number=Decimal("100"),
            normalized_unit="CNY",
            dimensions=FactDimensions(
                product_spec_id=uuid4(),
                geography_scheme="internal",
                geography_code="east-china",
                market_basis=MarketBasis.SPOT,
                tax_basis=TaxBasis.INCLUDED,
                freight_basis=FreightBasis.DELIVERED,
                currency_code="cny",
                frequency=ObservationFrequency.DAILY,
                price_component=PriceComponent.AVERAGE,
            ),
            valid_time=TimeRange(
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 1, 2, tzinfo=UTC),
            ),
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=1,
            quality=QualityComponents(
                source_quality=1,
                extraction_certainty=1,
                entity_match=1,
                time_unit_completeness=1,
                corroboration=1,
                freshness=1,
            ),
        )
        normalizer = AssertionNormalizer()
        first = normalizer.normalize(base)
        next_period = normalizer.normalize(
            base.model_copy(
                update={
                    "valid_time": TimeRange(
                        start=datetime(2026, 1, 2, tzinfo=UTC),
                        end=datetime(2026, 1, 3, tzinfo=UTC),
                    )
                }
            )
        )
        contract = normalizer.normalize(
            base.model_copy(
                update={
                    "dimensions": base.dimensions.model_copy(update={"market_basis": MarketBasis.CONTRACT})
                }
            )
        )

        self.assertTrue(first.dimensions_complete)
        self.assertEqual(first.scope_key, next_period.scope_key)
        self.assertNotEqual(first.id, next_period.id)
        self.assertNotEqual(first.comparability_hash, contract.comparability_hash)

    def test_unregistered_predicate_cannot_auto_publish(self) -> None:
        item = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="experimental.new_metric",
            value="1",
            value_type="number",
            normalized_number=Decimal("1"),
            normalized_unit="unit",
            valid_time=TimeRange(start=datetime(2026, 1, 1, tzinfo=UTC)),
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=1,
            quality=QualityComponents(
                source_quality=1,
                extraction_certainty=1,
                entity_match=1,
                time_unit_completeness=1,
                corroboration=1,
                freshness=1,
            ),
        )
        normalized = AssertionNormalizer().normalize(item)
        self.assertFalse(normalized.dimensions_complete)

    def test_typed_fact_values_are_normalized_and_fingerprinted(self) -> None:
        base = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="event.is_operational",
            value="是",
            value_type="boolean",
            valid_time_kind="timeless",
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=1,
            quality=QualityComponents(
                source_quality=1,
                extraction_certainty=1,
                entity_match=1,
                time_unit_completeness=1,
                corroboration=0,
                freshness=1,
            ),
        )
        normalized = AssertionNormalizer().normalize(base)
        self.assertEqual(normalized.value_type, FactValueKind.BOOLEAN)
        self.assertIs(normalized.normalized_boolean, True)
        self.assertNotEqual(
            normalized.value_fingerprint,
            normalized.model_copy(update={"normalized_boolean": False}).value_fingerprint,
        )

    def test_normalizer_recomputes_all_typed_values_from_raw_value(self) -> None:
        common = {
            "entity_type": EntityType.INDUSTRY,
            "entity_id": uuid4(),
            "field_name": "experimental.typed",
            "source_id": uuid4(),
            "document_id": uuid4(),
            "evidence_fragment_id": uuid4(),
            "extraction_run_id": uuid4(),
            "extractor_name": "test",
            "extractor_version": "1",
            "confidence": 1,
            "quality": self._quality(),
        }
        entity_value = uuid4()
        cases = (
            (
                FactAssertion(
                    **common,
                    value="100 kg",
                    value_type="number",
                    normalized_number=Decimal("999"),
                    normalized_unit="kg",
                ),
                "normalized_number",
                Decimal("100"),
            ),
            (
                FactAssertion(
                    **common,
                    value="否",
                    value_type="boolean",
                    normalized_boolean=True,
                ),
                "normalized_boolean",
                False,
            ),
            (
                FactAssertion(
                    **common,
                    value="2026-08-20",
                    value_type="date",
                    normalized_date=datetime(2000, 1, 1).date(),
                ),
                "normalized_date",
                datetime(2026, 8, 20).date(),
            ),
            (
                FactAssertion(
                    **common,
                    value=str(entity_value),
                    value_type="entity",
                    normalized_entity_id=uuid4(),
                ),
                "normalized_entity_id",
                entity_value,
            ),
            (
                FactAssertion(
                    **common,
                    value='{"v":1}',
                    value_type="json",
                    normalized_json={"v": 999},
                ),
                "normalized_json",
                {"v": 1},
            ),
        )
        normalizer = AssertionNormalizer()
        for item, attribute, expected in cases:
            with self.subTest(attribute=attribute):
                self.assertEqual(getattr(normalizer.normalize(item), attribute), expected)

    def test_unknown_unit_is_preserved_for_review_not_written_as_canonical(self) -> None:
        item = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="price.market",
            value="100 mystery-unit",
            value_type="number",
            normalized_number=Decimal("999"),
            normalized_unit="mystery-unit",
            dimensions=FactDimensions(
                product_spec_id=uuid4(),
                geography_scheme="internal",
                geography_code="china",
                market_basis=MarketBasis.SPOT,
                tax_basis=TaxBasis.INCLUDED,
                freight_basis=FreightBasis.DELIVERED,
                currency_code="CNY",
                frequency=ObservationFrequency.DAILY,
                price_component=PriceComponent.AVERAGE,
            ),
            valid_time=TimeRange(start=datetime(2026, 8, 20, tzinfo=UTC)),
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=1,
            quality=self._quality(),
        )

        normalized = AssertionNormalizer().normalize(item)

        self.assertEqual(normalized.normalized_number, Decimal("100"))
        self.assertIsNone(normalized.normalized_unit)
        self.assertFalse(normalized.dimensions_complete)
        self.assertEqual(normalized.metadata["unregistered_unit"], "mystery-unit")

    def test_database_semantic_snapshot_versions_normalizer_and_reconciler(self) -> None:
        predicate = {
            "code": "capacity.nameplate",
            "schema_version": "1.0.0",
            "value_kinds": ["numeric"],
            "temporal_mode": "period",
            "dimension_schema_version": "fact-dimensions/v2",
            "required_dimensions": [],
            "allowed_dimensions": [],
            "canonical_unit_code": "t",
            "high_impact": True,
            "reconciliation_policy": {"numeric_relative_tolerance": "0.02"},
        }
        conversions = [
            {
                "from_unit": "kg",
                "to_unit": "t",
                "multiplier": Decimal("0.001"),
                "offset": Decimal("0"),
                "valid_from": None,
                "valid_to": None,
            }
        ]
        units = [
            {"code": "kg", "dimension": "mass", "decimal_scale": 6},
            {"code": "t", "dimension": "mass", "decimal_scale": 6},
        ]
        runtime = PostgresSemanticCatalog.from_rows([predicate], conversions, units)
        base = FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="capacity.nameplate",
            value="2500 kg",
            value_type="number",
            normalized_number=Decimal("999"),
            normalized_unit="kg",
            dimensions=FactDimensions(schema_version="fact-dimensions/v2"),
            valid_time=TimeRange(start=datetime(2026, 1, 1, tzinfo=UTC)),
            source_id=uuid4(),
            document_id=uuid4(),
            evidence_fragment_id=uuid4(),
            extraction_run_id=uuid4(),
            extractor_name="test",
            extractor_version="1",
            confidence=1,
            quality=self._quality(),
        )
        normalized = runtime.normalizer.normalize(base)
        old_schema = runtime.normalizer.normalize(
            base.model_copy(
                update={"dimensions": FactDimensions(schema_version="fact-dimensions/v1")}
            )
        )
        existing = normalized.model_copy(update={"status": FactStatus.TRUSTED})
        nearby = runtime.normalizer.normalize(
            base.model_copy(
                update={
                    "id": uuid4(),
                    "value": "2530 kg",
                    "source_id": uuid4(),
                    "document_id": uuid4(),
                    "evidence_fragment_id": uuid4(),
                }
            )
        )

        self.assertEqual(normalized.normalized_number, Decimal("2.500"))
        self.assertEqual(normalized.normalized_unit, "t")
        self.assertTrue(normalized.dimensions_complete)
        self.assertFalse(old_schema.dimensions_complete)
        self.assertEqual(
            runtime.normalizer.normalizer_version,
            runtime.reconciler.evaluator_version,
        )
        self.assertEqual(runtime.reconciler.reconcile(nearby, [existing]).decision.value, "accept")

        changed = dict(predicate, dimension_schema_version="fact-dimensions/v3")
        changed_runtime = PostgresSemanticCatalog.from_rows([changed], conversions, units)
        self.assertNotEqual(runtime.fingerprint, changed_runtime.fingerprint)

        unsupported = dict(predicate, reconciliation_policy={"silent_rule": True})
        with self.assertRaisesRegex(ValueError, "unsupported reconciliation policy"):
            PostgresSemanticCatalog.from_rows([unsupported], conversions, units)

        with self.assertRaisesRegex(ValueError, "multiple active unit conversions"):
            PostgresSemanticCatalog.from_rows(
                [predicate],
                [*conversions, dict(conversions[0])],
                units,
            )

    def test_priority_thresholds_and_downgrade_hysteresis(self) -> None:
        industry_id = uuid4()
        policy = SchedulePolicy()
        now = datetime(2026, 8, 18, 0, 0, tzinfo=UTC)
        hot = CollectionPolicy(
            industry_id=industry_id,
            cadence=Cadence.WEEKLY,
            heat_score=90,
            data_risk_score=50,
        )
        self.assertEqual(policy.cadence_for(hot, now), Cadence.DAILY)
        cooling = CollectionPolicy(
            industry_id=industry_id,
            cadence=Cadence.DAILY,
            heat_score=20,
            data_risk_score=20,
            consecutive_low_days=3,
        )
        self.assertEqual(policy.cadence_for(cooling, now), Cadence.DAILY)
        cooled = cooling.model_copy(update={"consecutive_low_days": 7})
        self.assertEqual(policy.cadence_for(cooled, now), Cadence.WEEKLY)
