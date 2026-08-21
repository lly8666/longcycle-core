# 2026-08-21 Horizon gap / compact-index decision log

> This log records auditable product and engineering rationale, experiment state and execution decisions. It does not record private chain-of-thought.

## Context

The lithium-battery blind Memory Atlas reached 636 raw leads after the first targeted 2015–2018 batch3 pass. The benchmark horizon is now 2015–2026, with pre-2015 history treated as selective antecedent backfill.

CI #420 established a clean hard-gate baseline: Mypy succeeded and Pytest passed 91 tests. Ruff still reports diagnostic debt and remains non-blocking during the active memory campaign.

## Product decision: do not build the full low-cost web-agent dispatcher yet

The historical evidence stage cannot safely use low-cost web agents before an individual shard is sealed. A complete dispatcher therefore does not unblock the current historical main path.

Keep only the bounded-execution capability hook. Build the full dispatcher when either:

1. a sealed shard produces substantial claim-scoped verification workload; or
2. the source-first / archive-now current-collection path develops a stable repeated bounded-web workload that becomes a real bottleneck.

This keeps tooling behind demonstrated product demand rather than ahead of it.

## Horizon decision: 2015–2026 is the primary cycle window

The earlier 2019 start was too late because it captured a downturn without enough of the decisions and expectations that created it. The 2015–2018 setup is needed to reconstruct the previous expansion, 2017–2018 high-expectation phase and the transition into the 2018–2020 supply / inventory / margin adjustment.

The change does not authorize blanket collection of every shard back to 2015. Pre-2019 work must be selected by causal information gain.

## Remaining pre-2019 gap priority

A new decision artifact, `analysis/horizon-gap-priority-v1.json`, ranks remaining shards by:

- ability to explain 2019–2020 Reality from 2015–2018 decisions / expectations;
- project and capital lead time;
- relevance to lithium price / effective supply / chemistry-demand interpretation;
- current weakness of explicit pre-2019 causal setup;
- cross-shard bridge value.

Current order:

1. `UP-BRINE` — run now;
2. `UP-CONCENTRATE` — run now;
3. `DOWN-ESS` — run if marginal novelty remains healthy;
4. `LOOP-RECYCLING` — hold for a marginal-novelty check;
5. other remaining shards — defer unless negative space becomes first-order.

The stop rule is novelty decay, not equal shard counts.

## Method boundary: do not inspect target-shard raw output before the next blind pass

The v5 prompt allows the deterministic compact index for the same shard, not raw recall and not neighboring-shard output. Reading target raw JSONL manually would make the next pass less auditable even though no web search was used.

Therefore a small deterministic artifact path was added instead of building a new research platform:

- `scripts/build_memory_compact_indexes.py` rebuilds one compact index per shard from immutable raw JSONL plus explicit repair overlays;
- CI builds these indexes as a hard gate;
- CI uploads them as a replaceable `memory-compact-indexes` artifact;
- later blind passes may read the same-shard compact derivative only.

The compact representation intentionally excludes search queries, disconfirmation queries and source hints. Raw recall remains authoritative; the artifact is disposable and reproducible.

## CI semantics correction

The previous workflow combined `continue-on-error` with a later check of raw step `outcome` for Mypy/Pytest. That made the workflow semantics internally inconsistent: a check described as hard was also allowed to continue and then re-decided later.

The corrected rule is simpler:

- Ruff: diagnostic, `continue-on-error`;
- Mypy: native hard gate;
- Pytest: native hard gate;
- compact-index build: native hard gate;
- final summary: reporting only, no secondary correctness decision.

## Next execution

After the compact-index artifact is produced successfully:

1. inspect `UP-BRINE` compact index only and run one pre-2019 v5 blind pass;
2. classify each new lead as `new_category`, `useful_refinement` or `duplicate`;
3. repeat for `UP-CONCENTRATE`;
4. compare marginal novelty before deciding whether `DOWN-ESS` and then `LOOP-RECYCLING` deserve another pass;
5. keep `search_visibility=none` and `0 sealed` until the explicit shard seal criteria are actually satisfied.
