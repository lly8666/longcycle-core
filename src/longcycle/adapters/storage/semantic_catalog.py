from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from longcycle.application.normalization import (
    AssertionNormalizer,
    PredicateProfile,
    UnitRule,
)
from longcycle.application.quality import QualityGate
from longcycle.application.reconciliation import Reconciler, ReconciliationPolicy
from longcycle.domain.enums import FactValueKind, ValidTimeKind
from longcycle.domain.models import canonical_json

from .postgres import PostgresSupport


@dataclass(frozen=True, slots=True)
class SemanticRuntime:
    """One immutable, versioned semantic snapshot for a worker deployment."""

    normalizer: AssertionNormalizer
    reconciler: Reconciler
    fingerprint: str


class PostgresSemanticCatalog(PostgresSupport):
    """Loads predicate, unit and reconciliation behavior as one snapshot."""

    async def load_runtime(self) -> SemanticRuntime:
        async with self.connection() as connection:
            predicate_cursor = await connection.execute(
                """
                SELECT code, schema_version, value_kinds, temporal_mode,
                       dimension_schema_version, required_dimensions,
                       allowed_dimensions, canonical_unit_code, high_impact,
                       reconciliation_policy, unit_dimension_name
                FROM core.predicate_definitions
                WHERE active
                ORDER BY code, schema_version
                """
            )
            conversion_cursor = await connection.execute(
                """
                SELECT from_unit, to_unit, multiplier, additive_offset AS offset,
                       valid_from, valid_to
                FROM core.unit_conversion_versions
                WHERE (valid_from IS NULL OR valid_from <= current_date)
                  AND (valid_to IS NULL OR valid_to > current_date)
                ORDER BY from_unit, to_unit, valid_from NULLS FIRST
                """
            )
            unit_cursor = await connection.execute(
                "SELECT code, dimension, decimal_scale FROM core.units ORDER BY code"
            )
            predicate_rows = await predicate_cursor.fetchall()
            conversion_rows = await conversion_cursor.fetchall()
            unit_rows = await unit_cursor.fetchall()
        return self.from_rows(predicate_rows, conversion_rows, unit_rows)

    @staticmethod
    def from_rows(
        predicate_rows: Sequence[Mapping[str, Any]],
        conversion_rows: Sequence[Mapping[str, Any]],
        unit_rows: Sequence[Mapping[str, Any]],
    ) -> SemanticRuntime:
        registered_units = frozenset(str(row["code"]) for row in unit_rows)
        if not registered_units:
            raise ValueError("semantic catalog has no registered units")
        if len({code.lower() for code in registered_units}) != len(registered_units):
            raise ValueError("unit codes must be unique under case-insensitive resolution")

        profiles: dict[str, PredicateProfile] = {}
        policies: dict[str, ReconciliationPolicy] = {}
        unit_dimensions = {
            str(row["code"]): str(row["dimension"])
            for row in unit_rows
        }
        for row in predicate_rows:
            code = str(row["code"])
            canonical_unit = row.get("canonical_unit_code")
            if canonical_unit is not None and canonical_unit not in registered_units:
                raise ValueError(f"predicate {code} uses an unregistered canonical unit")
            allowed_dimensions = frozenset(row["allowed_dimensions"] or ())
            unit_dimension_name = row.get("unit_dimension_name")
            if canonical_unit is not None and unit_dimension_name is not None:
                raise ValueError(f"predicate {code} has two competing unit bindings")
            if (
                unit_dimension_name is not None
                and unit_dimension_name not in allowed_dimensions
            ):
                raise ValueError(f"predicate {code} binds unit to a disallowed dimension")
            profiles[code] = PredicateProfile(
                required_dimensions=frozenset(row["required_dimensions"] or ()),
                allowed_dimensions=allowed_dimensions,
                temporal_mode=ValidTimeKind(row["temporal_mode"]),
                value_kinds=frozenset(
                    FactValueKind(value) for value in row["value_kinds"]
                ),
                canonical_unit=canonical_unit,
                high_impact=bool(row["high_impact"]),
                dimension_schema_version=str(row["dimension_schema_version"]),
                unit_dimension_name=unit_dimension_name,
            )
            policies[code] = PostgresSemanticCatalog._policy_from_payload(
                row.get("reconciliation_policy") or {}
            )

        conversions: dict[tuple[str, str], UnitRule] = {}
        for row in conversion_rows:
            from_unit = str(row["from_unit"])
            to_unit = str(row["to_unit"])
            if from_unit not in registered_units or to_unit not in registered_units:
                raise ValueError("unit conversion references an unregistered unit")
            if unit_dimensions[from_unit] != unit_dimensions[to_unit]:
                raise ValueError("unit conversion crosses incompatible dimensions")
            conversion_key = (from_unit.lower(), to_unit.lower())
            if conversion_key in conversions:
                raise ValueError("multiple active unit conversions share one unit pair")
            conversions[conversion_key] = UnitRule(
                canonical_unit=to_unit,
                multiplier=Decimal(row["multiplier"]),
                offset=Decimal(row["offset"]),
            )

        fingerprint_payload = {
            "predicates": [dict(row) for row in predicate_rows],
            "conversions": [dict(row) for row in conversion_rows],
            "units": [dict(row) for row in unit_rows],
        }
        fingerprint = hashlib.sha256(
            canonical_json(fingerprint_payload).encode("utf-8")
        ).hexdigest()
        version = f"2.1.0+catalog.{fingerprint[:16]}"
        return SemanticRuntime(
            normalizer=AssertionNormalizer(
                normalizer_version=version,
                predicate_profiles=profiles,
                unit_conversions=conversions,
                registered_units=registered_units,
            ),
            reconciler=Reconciler(
                predicate_policies=policies,
                evaluator_version=version,
            ),
            fingerprint=fingerprint,
        )

    @staticmethod
    def _policy_from_payload(payload: Mapping[str, Any]) -> ReconciliationPolicy:
        supported = {
            "numeric_relative_tolerance",
            "high_impact_min_source_quality",
            "high_impact_min_independent_sources",
            "auto_publish_threshold",
            "review_threshold",
        }
        unknown = set(payload) - supported
        if unknown:
            raise ValueError(
                f"unsupported reconciliation policy keys: {', '.join(sorted(unknown))}"
            )
        defaults = ReconciliationPolicy()
        gate = QualityGate(
            auto_publish=float(
                payload.get("auto_publish_threshold", defaults.gate.auto_publish)
            ),
            review=float(payload.get("review_threshold", defaults.gate.review)),
        )
        return ReconciliationPolicy(
            gate=gate,
            numeric_relative_tolerance=Decimal(
                str(
                    payload.get(
                        "numeric_relative_tolerance",
                        defaults.numeric_relative_tolerance,
                    )
                )
            ),
            high_impact_min_source_quality=float(
                payload.get(
                    "high_impact_min_source_quality",
                    defaults.high_impact_min_source_quality,
                )
            ),
            high_impact_min_independent_sources=int(
                payload.get(
                    "high_impact_min_independent_sources",
                    defaults.high_impact_min_independent_sources,
                )
            ),
        )
