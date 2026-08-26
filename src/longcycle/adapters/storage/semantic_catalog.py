from __future__ import annotations

import hashlib
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
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
            alias_cursor = await connection.execute(
                """
                SELECT alias, unit_code, match_mode, valid_from, valid_to
                FROM core.unit_alias_versions
                WHERE (valid_from IS NULL OR valid_from <= current_date)
                  AND (valid_to IS NULL OR valid_to > current_date)
                ORDER BY alias, match_mode, valid_from NULLS FIRST
                """
            )
            predicate_rows = await predicate_cursor.fetchall()
            conversion_rows = await conversion_cursor.fetchall()
            unit_rows = await unit_cursor.fetchall()
            alias_rows = await alias_cursor.fetchall()
        return self.from_rows(predicate_rows, conversion_rows, unit_rows, alias_rows)

    @staticmethod
    def from_rows(
        predicate_rows: Sequence[Mapping[str, Any]],
        conversion_rows: Sequence[Mapping[str, Any]],
        unit_rows: Sequence[Mapping[str, Any]],
        alias_rows: Sequence[Mapping[str, Any]] = (),
    ) -> SemanticRuntime:
        unit_codes = [str(row["code"]) for row in unit_rows]
        registered_units = frozenset(unit_codes)
        if not registered_units:
            raise ValueError("semantic catalog has no registered units")
        if len(registered_units) != len(unit_codes):
            raise ValueError("semantic catalog contains duplicate unit codes")

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

        exact_aliases, casefold_aliases, ambiguous_casefolds = (
            PostgresSemanticCatalog._build_alias_catalog(
                registered_units,
                alias_rows,
            )
        )
        conversions = PostgresSemanticCatalog._build_conversion_closure(
            conversion_rows,
            registered_units,
            unit_dimensions,
        )

        fingerprint_payload = {
            "predicates": [dict(row) for row in predicate_rows],
            "conversions": [dict(row) for row in conversion_rows],
            "units": [dict(row) for row in unit_rows],
            "aliases": [dict(row) for row in alias_rows],
        }
        fingerprint = hashlib.sha256(
            canonical_json(fingerprint_payload).encode("utf-8")
        ).hexdigest()
        version = f"2.2.0+catalog.{fingerprint[:16]}"
        return SemanticRuntime(
            normalizer=AssertionNormalizer(
                normalizer_version=version,
                predicate_profiles=profiles,
                unit_conversions=conversions,
                registered_units=registered_units,
                unit_aliases_exact=exact_aliases,
                unit_aliases_casefold=casefold_aliases,
                ambiguous_unit_casefolds=ambiguous_casefolds,
            ),
            reconciler=Reconciler(
                predicate_policies=policies,
                evaluator_version=version,
            ),
            fingerprint=fingerprint,
        )

    @staticmethod
    def _build_alias_catalog(
        registered_units: frozenset[str],
        alias_rows: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, str], dict[str, str], frozenset[str]]:
        exact_aliases: dict[str, str] = {}
        casefold_aliases: dict[str, str] = {}
        targets_by_fold: dict[str, set[str]] = {}

        for code in registered_units:
            targets_by_fold.setdefault(code.casefold(), set()).add(code)

        for row in alias_rows:
            alias = str(row["alias"])
            unit_code = str(row["unit_code"])
            match_mode = str(row["match_mode"])
            if unit_code not in registered_units:
                raise ValueError("unit alias references an unregistered unit")
            if not alias or alias != alias.strip():
                raise ValueError("unit alias must be non-empty and trimmed")
            if match_mode == "exact":
                canonical_collision = alias if alias in registered_units else None
                if canonical_collision is not None and canonical_collision != unit_code:
                    raise ValueError("exact unit alias collides with a canonical unit code")
                existing = exact_aliases.get(alias)
                if existing is not None and existing != unit_code:
                    raise ValueError("multiple active exact unit aliases share one token")
                exact_aliases[alias] = unit_code
                targets_by_fold.setdefault(alias.casefold(), set()).add(unit_code)
            elif match_mode == "casefold":
                folded = alias.casefold()
                existing = casefold_aliases.get(folded)
                if existing is not None and existing != unit_code:
                    raise ValueError("multiple active casefold unit aliases share one token")
                casefold_aliases[folded] = unit_code
            else:
                raise ValueError(f"unsupported unit alias match mode: {match_mode}")

        # A case-fold alias claims every casing of its token. It is therefore unsafe
        # if canonical/exact case-sensitive spellings in the same family mean
        # different units (for example GB versus exact alias Gb -> Gbit).
        for folded, unit_code in casefold_aliases.items():
            existing_targets = targets_by_fold.get(folded, set())
            if existing_targets and existing_targets != {unit_code}:
                raise ValueError("casefold unit alias collides with case-sensitive unit semantics")
            targets_by_fold.setdefault(folded, set()).add(unit_code)

        ambiguous = frozenset(
            folded for folded, targets in targets_by_fold.items() if len(targets) > 1
        )
        return exact_aliases, casefold_aliases, ambiguous

    @staticmethod
    def _build_conversion_closure(
        conversion_rows: Sequence[Mapping[str, Any]],
        registered_units: frozenset[str],
        unit_dimensions: Mapping[str, str],
    ) -> dict[tuple[str, str], UnitRule]:
        # Graph edges are exact affine transforms y = x*m + o. Fractions make
        # consistency checks exact even after inverse and transitive composition.
        graph: dict[str, list[tuple[str, Fraction, Fraction]]] = {
            code: [] for code in registered_units
        }
        direct_pairs: set[tuple[str, str]] = set()

        for row in conversion_rows:
            from_unit = str(row["from_unit"])
            to_unit = str(row["to_unit"])
            if from_unit not in registered_units or to_unit not in registered_units:
                raise ValueError("unit conversion references an unregistered unit")
            if unit_dimensions[from_unit] != unit_dimensions[to_unit]:
                raise ValueError("unit conversion crosses incompatible dimensions")
            pair = (from_unit, to_unit)
            if pair in direct_pairs:
                raise ValueError("multiple active unit conversions share one unit pair")
            direct_pairs.add(pair)

            multiplier = Fraction(Decimal(row["multiplier"]))
            offset = Fraction(Decimal(row["offset"]))
            if multiplier == 0:
                raise ValueError("unit conversion multiplier cannot be zero")

            graph[from_unit].append((to_unit, multiplier, offset))
            graph[to_unit].append(
                (
                    from_unit,
                    Fraction(1, 1) / multiplier,
                    -offset / multiplier,
                )
            )

        conversions: dict[tuple[str, str], UnitRule] = {}
        for source in sorted(registered_units):
            transforms: dict[str, tuple[Fraction, Fraction]] = {
                source: (Fraction(1, 1), Fraction(0, 1))
            }
            queue: deque[str] = deque([source])
            while queue:
                current = queue.popleft()
                current_multiplier, current_offset = transforms[current]
                for target, edge_multiplier, edge_offset in graph[current]:
                    candidate = (
                        current_multiplier * edge_multiplier,
                        current_offset * edge_multiplier + edge_offset,
                    )
                    existing = transforms.get(target)
                    if existing is None:
                        transforms[target] = candidate
                        queue.append(target)
                    elif existing != candidate:
                        raise ValueError(
                            "inconsistent unit conversion graph: multiple paths imply different transforms"
                        )

            for target, (multiplier, offset) in transforms.items():
                if target == source:
                    continue
                conversions[(source, target)] = UnitRule(
                    canonical_unit=target,
                    multiplier=PostgresSemanticCatalog._fraction_to_decimal(multiplier),
                    offset=PostgresSemanticCatalog._fraction_to_decimal(offset),
                )
        return conversions

    @staticmethod
    def _fraction_to_decimal(value: Fraction) -> Decimal:
        with localcontext() as context:
            context.prec = 100
            return Decimal(value.numerator) / Decimal(value.denominator)

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
