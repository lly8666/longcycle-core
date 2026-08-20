from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from longcycle.domain.enums import FactValueKind, ValidTimeKind
from longcycle.domain.models import FactAssertion, canonical_json, stable_uuid


@dataclass(frozen=True, slots=True)
class UnitRule:
    canonical_unit: str
    multiplier: Decimal = Decimal("1")
    offset: Decimal = Decimal("0")


DEFAULT_UNIT_RULES = {
    "tonne": UnitRule("t"),
    "tonnes": UnitRule("t"),
    "metric ton": UnitRule("t"),
    "mt": UnitRule("t"),
    "万吨": UnitRule("t", Decimal("10000")),
    "kt": UnitRule("t", Decimal("1000")),
    "kg": UnitRule("kg"),
    "g": UnitRule("kg", Decimal("0.001")),
    "%": UnitRule("ratio", Decimal("0.01")),
    "percent": UnitRule("ratio", Decimal("0.01")),
}

DEFAULT_REGISTERED_UNITS = frozenset(
    {"t", "kg", "lb", "m3", "unit", "day", "ratio", "CNY", "USD"}
)

_NUMERIC_TOKEN = re.compile(
    r"[-+]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
)


@dataclass(frozen=True, slots=True)
class PredicateProfile:
    required_dimensions: frozenset[str] = frozenset()
    allowed_dimensions: frozenset[str] | None = None
    temporal_mode: ValidTimeKind = ValidTimeKind.PERIOD
    value_kinds: frozenset[FactValueKind] = frozenset(FactValueKind)
    canonical_unit: str | None = None
    high_impact: bool = False
    dimension_schema_version: str = "fact-dimensions/v1"
    unit_dimension_name: str | None = None


DEFAULT_PREDICATE_PROFILES = {
    "price.*": PredicateProfile(
        required_dimensions=frozenset(
            {
                "product_spec_id",
                "geography_scheme",
                "geography_code",
                "market_basis",
                "tax_basis",
                "freight_basis",
                "currency_code",
                "frequency",
                "price_component",
            }
        ),
        allowed_dimensions=frozenset(
            {
                "product_spec_id",
                "geography_scheme",
                "geography_code",
                "market_basis",
                "contract_basis",
                "tax_basis",
                "freight_basis",
                "incoterm",
                "currency_code",
                "frequency",
                "price_component",
                "statistical_scope",
            }
        ),
        value_kinds=frozenset({FactValueKind.NUMERIC}),
        high_impact=True,
        dimension_schema_version="fact-dimensions/v1",
    )
}


@dataclass(slots=True)
class AssertionNormalizer:
    normalizer_name: str = "assertion_normalizer"
    normalizer_version: str = "2.0.0"
    unit_rules: dict[str, UnitRule] = field(default_factory=lambda: dict(DEFAULT_UNIT_RULES))
    unit_conversions: dict[tuple[str, str], UnitRule] = field(default_factory=dict)
    registered_units: frozenset[str] = DEFAULT_REGISTERED_UNITS
    predicate_profiles: dict[str, PredicateProfile] = field(
        default_factory=lambda: dict(DEFAULT_PREDICATE_PROFILES)
    )

    def normalize(self, assertion: FactAssertion) -> FactAssertion:
        profile = self._profile_for(assertion.field_name)
        # Extractor-provided normalized_* fields are hints, never authority.
        # Derive the typed value from the source-facing scalar every time.
        number: Decimal | None = None
        normalized_boolean: bool | None = None
        normalized_date: date | None = None
        normalized_entity_id: UUID | None = None
        normalized_json: Any = None
        try:
            if assertion.value_type == FactValueKind.NUMERIC:
                number = self._parse_number(assertion.value)
            elif assertion.value_type == FactValueKind.BOOLEAN:
                normalized_boolean = self._parse_boolean(assertion.value)
            elif assertion.value_type == FactValueKind.DATE:
                normalized_date = date.fromisoformat(assertion.value.strip())
            elif assertion.value_type == FactValueKind.ENTITY:
                normalized_entity_id = UUID(assertion.value.strip())
            elif assertion.value_type == FactValueKind.JSON:
                normalized_json = json.loads(assertion.value)
                if normalized_json is None:
                    raise ValueError("JSON null is not a supported fact value")
        except (InvalidOperation, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid {assertion.value_type.value} fact value: {assertion.value}") from exc

        metadata = dict(assertion.metadata)
        unit = assertion.normalized_unit
        unit_valid = True
        if assertion.value_type == FactValueKind.NUMERIC and number is not None and unit is not None:
            normalized_unit_key = unit.strip().lower()
            rule = None
            if profile is not None and profile.canonical_unit is not None:
                rule = self.unit_conversions.get(
                    (normalized_unit_key, profile.canonical_unit.lower())
                )
            rule = rule or self.unit_rules.get(normalized_unit_key)
            if rule:
                number = number * rule.multiplier + rule.offset
                unit = rule.canonical_unit
            registered_lookup = {code.lower(): code for code in self.registered_units}
            registered_code = registered_lookup.get(unit.strip().lower())
            if registered_code is None:
                metadata["unregistered_unit"] = assertion.normalized_unit
                unit = None
                unit_valid = False
            else:
                unit = registered_code
                metadata.pop("unregistered_unit", None)
        elif assertion.value_type == FactValueKind.NUMERIC:
            unit_valid = False
        elif unit is not None:
            metadata["unexpected_unit"] = unit
            unit = None
            unit_valid = False
        valid_time_kind = self._valid_time_kind(assertion, profile)
        dimensions_complete = self._dimensions_complete(
            assertion,
            profile,
            valid_time_kind,
            normalized_unit=unit,
            unit_valid=unit_valid,
        )
        provisional = assertion.model_copy(
            update={
                "normalized_number": number,
                "normalized_boolean": normalized_boolean,
                "normalized_date": normalized_date,
                "normalized_entity_id": normalized_entity_id,
                "normalized_json": normalized_json,
                "normalized_unit": unit,
                "valid_time_kind": valid_time_kind,
                "dimensions_complete": dimensions_complete,
                "normalizer_name": self.normalizer_name,
                "normalizer_version": self.normalizer_version,
                "high_impact": assertion.high_impact or bool(profile and profile.high_impact),
                "metadata": metadata,
            }
        )
        stable_id = self._stable_id(provisional)
        return provisional.model_copy(update={"id": stable_id})

    @staticmethod
    def _parse_number(value: str) -> Decimal:
        tokens = _NUMERIC_TOKEN.findall(value.strip())
        if len(tokens) != 1:
            raise ValueError("numeric value must contain exactly one scalar")
        return Decimal(tokens[0].replace(",", ""))

    @staticmethod
    def _parse_boolean(value: str) -> bool:
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "是"}:
            return True
        if normalized in {"false", "0", "no", "否"}:
            return False
        raise ValueError("boolean value is not recognized")

    def _profile_for(self, predicate: str) -> PredicateProfile | None:
        exact = self.predicate_profiles.get(predicate)
        if exact is not None:
            return exact
        wildcard_matches = [
            (key[:-1], profile)
            for key, profile in self.predicate_profiles.items()
            if key.endswith("*") and predicate.startswith(key[:-1])
        ]
        if not wildcard_matches:
            return None
        return max(wildcard_matches, key=lambda item: len(item[0]))[1]

    @staticmethod
    def _stable_id(assertion: FactAssertion) -> UUID:
        return stable_uuid(
            "assertion-v2",
            str(assertion.document_id),
            str(assertion.evidence_fragment_id),
            assertion.scope_key,
            canonical_json(assertion.valid_time.model_dump(mode="json")),
            assertion.valid_time_kind.value,
            assertion.value_fingerprint,
            str(assertion.extraction_run_id),
            assertion.extractor_name,
            assertion.extractor_version,
            assertion.normalizer_name,
            assertion.normalizer_version,
            str(assertion.metadata.get("unregistered_unit") or ""),
        )

    @staticmethod
    def _valid_time_kind(
        assertion: FactAssertion,
        profile: PredicateProfile | None,
    ) -> ValidTimeKind:
        has_boundary = assertion.valid_time.start is not None or assertion.valid_time.end is not None
        if has_boundary:
            return ValidTimeKind.PERIOD
        if assertion.valid_time_kind == ValidTimeKind.TIMELESS:
            return ValidTimeKind.TIMELESS
        if profile and profile.temporal_mode == ValidTimeKind.TIMELESS:
            return ValidTimeKind.TIMELESS
        return ValidTimeKind.UNKNOWN

    @staticmethod
    def _dimensions_complete(
        assertion: FactAssertion,
        profile: PredicateProfile | None,
        valid_time_kind: ValidTimeKind,
        *,
        normalized_unit: str | None,
        unit_valid: bool,
    ) -> bool:
        if profile is None:
            # New predicates are allowed into the assertion layer, but they
            # cannot auto-publish until a versioned semantic profile exists.
            return False
        dimensions = assertion.dimensions.model_dump()
        has_required = all(dimensions.get(name) is not None for name in profile.required_dimensions)
        populated_dimensions = {name for name, value in dimensions.items() if value is not None}
        populated_dimensions.discard("schema_version")
        has_only_allowed = (
            profile.allowed_dimensions is None
            or populated_dimensions <= profile.allowed_dimensions
        )
        value_kind_allowed = assertion.value_type in profile.value_kinds
        canonical_unit_complete = (
            profile.canonical_unit is None
            or (
                normalized_unit is not None
                and normalized_unit.lower() == profile.canonical_unit.lower()
            )
        )
        dimension_bound_unit_complete = True
        if profile.unit_dimension_name is not None:
            dimension_unit = dimensions.get(profile.unit_dimension_name)
            dimension_bound_unit_complete = (
                dimension_unit is not None
                and normalized_unit is not None
                and str(dimension_unit).lower() == normalized_unit.lower()
            )
        temporal_complete = valid_time_kind == profile.temporal_mode
        dimension_schema_complete = (
            assertion.dimensions.schema_version == profile.dimension_schema_version
        )
        return (
            has_required
            and has_only_allowed
            and value_kind_allowed
            and canonical_unit_complete
            and temporal_complete
            and dimension_schema_complete
            and unit_valid
            and dimension_bound_unit_complete
        )
