from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from longcycle.adapters.storage.semantic_catalog import PostgresSemanticCatalog
from longcycle.domain.enums import EntityType
from longcycle.domain.models import FactAssertion, FactDimensions, QualityComponents, TimeRange


class StorageUnitSemanticsTest(unittest.TestCase):
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

    @staticmethod
    def _runtime():
        predicate = {
            "code": "storage.capacity_test",
            "schema_version": "1.0.0",
            "value_kinds": ["numeric"],
            "temporal_mode": "period",
            "dimension_schema_version": "fact-dimensions/v1",
            "required_dimensions": [],
            "allowed_dimensions": [],
            "canonical_unit_code": "B",
            "high_impact": False,
            "reconciliation_policy": {},
        }
        units = [
            {"code": code, "dimension": "digital_storage", "decimal_scale": 6}
            for code in (
                "bit", "kbit", "Mbit", "Gbit",
                "B", "kB", "MB", "GB", "TB",
                "KiB", "MiB", "GiB", "TiB",
            )
        ]
        conversions = [
            {"from_unit": "bit", "to_unit": "B", "multiplier": Decimal("0.125"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "kbit", "to_unit": "bit", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "Mbit", "to_unit": "kbit", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "Gbit", "to_unit": "Mbit", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "kB", "to_unit": "B", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "MB", "to_unit": "kB", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "GB", "to_unit": "MB", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "TB", "to_unit": "GB", "multiplier": Decimal("1000"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "KiB", "to_unit": "B", "multiplier": Decimal("1024"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "MiB", "to_unit": "KiB", "multiplier": Decimal("1024"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "GiB", "to_unit": "MiB", "multiplier": Decimal("1024"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "TiB", "to_unit": "GiB", "multiplier": Decimal("1024"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
        ]
        aliases = [
            {"alias": "b", "unit_code": "bit", "match_mode": "exact", "valid_from": None, "valid_to": None},
            {"alias": "kb", "unit_code": "kbit", "match_mode": "exact", "valid_from": None, "valid_to": None},
            {"alias": "Gb", "unit_code": "Gbit", "match_mode": "exact", "valid_from": None, "valid_to": None},
            {"alias": "gb", "unit_code": "Gbit", "match_mode": "exact", "valid_from": None, "valid_to": None},
            {"alias": "gigabyte", "unit_code": "GB", "match_mode": "casefold", "valid_from": None, "valid_to": None},
            {"alias": "gigabytes", "unit_code": "GB", "match_mode": "casefold", "valid_from": None, "valid_to": None},
        ]
        return PostgresSemanticCatalog.from_rows([predicate], conversions, units, aliases)

    def _fact(self, unit: str, value: str = "1") -> FactAssertion:
        return FactAssertion(
            entity_type=EntityType.INDUSTRY,
            entity_id=uuid4(),
            field_name="storage.capacity_test",
            value=value,
            value_type="number",
            normalized_number=Decimal("999"),
            normalized_unit=unit,
            dimensions=FactDimensions(),
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

    def test_sparse_graph_composes_decimal_binary_and_bit_byte_conversions(self) -> None:
        runtime = self._runtime()

        tb = runtime.normalizer.normalize(self._fact("TB"))
        tib = runtime.normalizer.normalize(self._fact("TiB"))
        gigabit = runtime.normalizer.normalize(self._fact("Gb"))
        gigabyte = runtime.normalizer.normalize(self._fact("GB"))
        word = runtime.normalizer.normalize(self._fact("GIGABYTES"))

        self.assertEqual(tb.normalized_number, Decimal("1000000000000"))
        self.assertEqual(tib.normalized_number, Decimal("1099511627776"))
        self.assertEqual(gigabit.normalized_number, Decimal("125000000"))
        self.assertEqual(gigabyte.normalized_number, Decimal("1000000000"))
        self.assertEqual(word.normalized_number, Decimal("1000000000"))
        self.assertTrue(all(item.normalized_unit == "B" for item in (tb, tib, gigabit, gigabyte, word)))
        self.assertTrue(all(item.dimensions_complete for item in (tb, tib, gigabit, gigabyte, word)))
        self.assertEqual(
            runtime.normalizer.unit_conversions[("TiB", "TB")].multiplier,
            Decimal("1.099511627776"),
        )

    def test_case_sensitive_symbols_do_not_silently_collapse_bit_and_byte(self) -> None:
        runtime = self._runtime()

        byte_value = runtime.normalizer.normalize(self._fact("GB"))
        bit_value = runtime.normalizer.normalize(self._fact("Gb"))
        lower_bit_value = runtime.normalizer.normalize(self._fact("gb"))
        ambiguous_case = runtime.normalizer.normalize(self._fact("gB"))
        ambiguous_k = runtime.normalizer.normalize(self._fact("KB"))

        self.assertEqual(byte_value.normalized_number, Decimal("1000000000"))
        self.assertEqual(bit_value.normalized_number, Decimal("125000000"))
        self.assertEqual(lower_bit_value.normalized_number, Decimal("125000000"))
        self.assertIsNone(ambiguous_case.normalized_unit)
        self.assertEqual(ambiguous_case.metadata["ambiguous_unit"], "gB")
        self.assertFalse(ambiguous_case.dimensions_complete)
        self.assertIsNone(ambiguous_k.normalized_unit)
        self.assertEqual(ambiguous_k.metadata["ambiguous_unit"], "KB")
        self.assertFalse(ambiguous_k.dimensions_complete)

    def test_inconsistent_conversion_cycle_fails_semantic_snapshot(self) -> None:
        units = [
            {"code": code, "dimension": "synthetic", "decimal_scale": 6}
            for code in ("a", "b", "c")
        ]
        conversions = [
            {"from_unit": "a", "to_unit": "b", "multiplier": Decimal("2"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "b", "to_unit": "c", "multiplier": Decimal("3"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
            {"from_unit": "a", "to_unit": "c", "multiplier": Decimal("5"), "offset": Decimal("0"), "valid_from": None, "valid_to": None},
        ]
        with self.assertRaisesRegex(ValueError, "inconsistent unit conversion graph"):
            PostgresSemanticCatalog.from_rows([], conversions, units)

    def test_casefold_alias_cannot_override_case_sensitive_symbol_family(self) -> None:
        units = [
            {"code": "GB", "dimension": "digital_storage", "decimal_scale": 6},
            {"code": "Gbit", "dimension": "digital_storage", "decimal_scale": 6},
        ]
        aliases = [
            {"alias": "Gb", "unit_code": "Gbit", "match_mode": "exact", "valid_from": None, "valid_to": None},
            {"alias": "gb", "unit_code": "Gbit", "match_mode": "casefold", "valid_from": None, "valid_to": None},
        ]
        with self.assertRaisesRegex(ValueError, "casefold unit alias collides"):
            PostgresSemanticCatalog.from_rows([], [], units, aliases)

    def test_alias_vocabulary_participates_in_semantic_fingerprint(self) -> None:
        base = self._runtime()
        units = [
            {"code": "B", "dimension": "digital_storage", "decimal_scale": 6},
        ]
        plain = PostgresSemanticCatalog.from_rows([], [], units)
        named = PostgresSemanticCatalog.from_rows(
            [],
            [],
            units,
            [{"alias": "byte", "unit_code": "B", "match_mode": "casefold", "valid_from": None, "valid_to": None}],
        )
        self.assertNotEqual(plain.fingerprint, named.fingerprint)
        self.assertNotEqual(base.fingerprint, plain.fingerprint)


if __name__ == "__main__":
    unittest.main()
