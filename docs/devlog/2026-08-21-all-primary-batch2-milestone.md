# 2026-08-21 — All Primary Memory Shards Through Batch2

## Milestone

The blind lithium-battery Memory Atlas has reached a clean campaign milestone:

- 600 raw Memory Leads;
- 14 primary shards;
- all 14 primary shards have completed at least two self-gap batches;
- every observed batch2 produced 6/6 new or useful structural leads;
- 0 sealed shards;
- `search_visibility = none`.

This means the campaign has not yet produced evidence of saturation. The next phase must therefore measure **third-pass novelty decay**, not begin fresh search.

## Four final batch2 shards

The last batch1-only primary shards were completed without web search.

### UP-BRINE

New dimensions included:

- aquifer drawdown and well-field interference;
- time-varying brine chemistry and impurity-driven reagent intensity;
- weather-driven evaporation throughput;
- DLE freshwater and reinjection material balance;
- potash/boron co-product economics;
- shared-aquifer interaction across legal project boundaries.

### UP-CHEMICALS

New dimensions included:

- physical limits on carbonate/hydroxide product switching;
- sulfuric acid, soda ash, caustic and energy cost bridges;
- mother-liquor/rework loops and single-pass versus total yield;
- tolling/processing ownership semantics;
- packaging and customer-delivery quality constraints;
- process-stage, grade and ownership-aware inventory.

### DOWN-OTHER

New dimensions included:

- battery energy per device as a time-varying demand intensity;
- industrial mobility/AGV/forklift lead-to-lithium substitution;
- data-center UPS as a separate backup-power demand mechanism;
- shared cylindrical-cell capacity across end applications;
- transport/safety certification as a market-access constraint;
- AI/robotics/new-device demand narratives requiring explicit unit-to-battery conversion assumptions.

### LOOP-RECYCLING

New dimensions included:

- generated retirement volume versus collected versus plant-delivered feedstock;
- SOC/discharge/safe transport and preprocessing constraints;
- preprocessing/black-mass/hydromet process-stage capacity double counting;
- element-specific recovery and battery-grade product yield;
- cross-border black-mass/waste policy;
- direct cathode regeneration expectations versus commercial qualification.

## Validation

The 600-lead state was calibrated in `coverage-index.json` and `.longcycle/handoff/current.json` and then independently reconstructed by the CI checkout.

GitHub Actions run #226 completed with:

- Mypy: success, no issues in 55 source files;
- Pytest: 127 passed;
- final correctness gate: success;
- Ruff: 61 findings, diagnostic-only during the Memory Campaign.

The hard Pytest gate includes the repository-only handoff isolation drill. Therefore the 600-lead checkpoint, per-shard raw-derived counts, bootstrap/constitution state and stale-checkpoint detection remained mutually consistent on that checkout.

## What changes next

The campaign should stop treating `batch2 completion` as the objective. The next experiment is:

```text
raw blind recall + typed repair overlays
→ deterministic compact shard indices
→ rank unresolved/high-value gaps
→ selective batch3 blind recall
→ classify each output as new_category / useful_refinement / duplicate
→ measure novelty decay
```

A shard still cannot seal until it has three consecutive low-novelty batches **and** a negative-space/gap-matrix review finds no material uncovered dimension.

Fresh historical web self-verification remains forbidden for every primary shard at this milestone.
