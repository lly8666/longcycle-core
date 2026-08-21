# Blind Memory Batch3 v5 — 2015–2018 causal setup

## Purpose

This is a blind memory-exhaustion pass for one atomic lithium-battery shard. It extends the active benchmark horizon to `2015-01-01 → 2026-12-31` by specifically testing what causal setup from `2015-01-01 → 2018-12-31` is missing from the existing shard index.

This is **not** evidence collection and must not use fresh web/search results.

## Inputs allowed

- the fixed shard ontology and shard id;
- the deterministic compact index for the same shard only;
- `docs/research/lithium-battery-cycle-horizon-v2.md`;
- this prompt.

Do not read neighboring shard raw outputs. Do not read fresh search results. Do not use post-recall evidence to repair memory.

## Task

Generate a small batch of atomic Memory Leads that recover the **pre-2019 causal setup** needed to explain later outcomes.

Prioritize:

1. projects, capex, contracts and technology commitments made before later supply became visible;
2. contemporaneous demand / price / scarcity / chemistry-share expectations;
3. early signs of oversupply, inventory, margin pressure, policy change or project slippage that were observable at the time;
4. old company/project/product names or statistical vocabulary that later searches may miss;
5. mechanisms that link 2015–2018 decisions to 2019–2020 Reality.

Do not merely restate famous headlines already represented in the compact index. Prefer propositions that add a new causal dimension.

## Batch3 classification

Inside `recalled_details`, include:

- `gap_reason`: why this dimension was missing or weak in prior passes;
- `batch3_classification`: one of `new_category`, `useful_refinement`, `duplicate`;
- `cycle_link`: what later Reality this earlier setup may help explain, without asserting the causal link as proven.

A `duplicate` is allowed if the memory genuinely adds no new semantic dimension; do not force novelty.

## Exact enums

`lead_kind` must be one of:

`landmark`, `missing_event`, `actor`, `terminology`, `metric`, `mechanism`, `pricing_rule`, `contract_change`, `process_bottleneck`, `project_pattern`, `inventory_pattern`, `capital_cycle`, `policy_shift`, `technology_shift`, `cross_industry_dependency`, `narrative`, `causal_hypothesis`, `anomaly`, `failure_dead_end`.

`claim_scope` must be one of:

`legal_disclosure`, `official_statistic`, `self_statement`, `management_guidance`, `market_measurement`, `project_status`, `policy_text`, `third_party_fact`, `industry_expectation`, `technical_specification`, `other`.

`memory_basis` must be one of:

`remembered_event`, `remembered_actor_or_name`, `remembered_mechanism`, `associative_inference`, `mixed`.

`precision_risk`: `low`, `medium`, `high`, `unknown`.

`entity_resolution_state`: `stable`, `partially_resolved`, `ambiguous`, `unresolved`.

## Output discipline

- JSONL only.
- One object = one minimum proposition/search direction.
- Preserve uncertainty explicitly.
- Every lead needs at least one disconfirmation query and disconfirmation source type.
- Search terms are archaeology hints only; they are not sources.
- `memory_confidence` is confidence in recollection strength, never truth probability.
- Raw output is immutable after commit; structural schema errors use typed repair overlays.
