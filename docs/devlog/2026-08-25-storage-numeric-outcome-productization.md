# Storage numeric Outcome productization

## Source-grounded representation gap

The storage-semiconductor production packet contains a directly comparable Gartner sequence: a 3.5% worldwide PC shipment-growth forecast in February 2024, 2.4% revisions in March and May, and a later Gartner preliminary full-year measurement of 1.3% growth for calendar 2024. The existing domain/database model already owns numeric Judgment values, typed Fact normalization/comparability, and numeric Outcome error columns, but the bounded grounded projection helpers only exposed text values and the bounded Outcome executor only wired temporal milestone comparisons.

## Owner decision

This is an extension of existing owners, not a new capability. CAP-0003 continues to own numeric Reality normalization, canonical unit/catalog semantics and FactDimensions comparability. CAP-0004 continues to own contemporaneous Judgment, revision context and immutable later Outcome evaluation. No schema shape or semantic-owner split is introduced.

## Canonical percentage representation

Longcycle's initial normalizer already defines `%` and `percent` as source-facing aliases that multiply by `0.01` into the canonical `ratio` unit. Migration `0003_research_domains.sql` also already seeds `ratio` into `core.units`; therefore YoY semantics belong in the predicate `market.pc_shipments_yoy_growth`, not in an ad-hoc unit code. Migration 0035 only validates that existing unit and registers the new claim-specific predicate against it.

The typed values are stored as 3.5% = `0.035 ratio`, 2.4% = `0.024 ratio`, and 1.3% = `0.013 ratio`; the source-facing percentage text remains preserved in summaries/metadata.

The first production attempt used `pct_yoy`, which correctly failed the repository's registered-unit guard on a fresh PostgreSQL database. The first repair attempt then overreached by trying to reseed the full base unit catalog; CI correctly exposed that `0003` already owned those rows (`day` is seeded there with dimension `time`). The bounded repair therefore reuses the existing catalog rather than duplicating or redefining it.

## Capability-admission correction

`disposition=extend` remains correct because CAP-0003/CAP-0004 already own the semantics. `unmet_requirement` is therefore `null`: the missing numeric helper wiring and predicate registration are extension work, not evidence that existing semantic owners are fundamentally insufficient.

## Guards

- Numeric Judgment and Reality must share the same predicate, complete typed dimensions and normalized unit before direct comparison.
- `numeric_error` is deterministic `realized - judgment`; it does not imply a correctness threshold.
- Direct numeric comparisons default to `indeterminate` evaluation status unless a separately justified policy supplies a classification.
- Gartner's January 2025 PC measurement remains explicitly preliminary and cannot be visible in a 2024 replay.
- The February, March and May forecasts remain separate immutable vintages; later values do not overwrite earlier cognition.
- The May 2024 2.4% PC forecast is typed as reaffirming the March 2024 2.4% vintage; the February→March cross-packet revision remains visible by vintage and can receive a cross-execution relation later without blocking numeric Outcome.
- Server DDR5 enablement/qualification/shipment Evidence remains separate from device-demand Outcome and is not used to infer DRAM bit-demand onset.
