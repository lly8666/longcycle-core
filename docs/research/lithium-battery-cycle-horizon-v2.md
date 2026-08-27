# Lithium-battery benchmark horizon v2 — 2015–2026

## Decision

The primary benchmark horizon is revised from `2019-01-01 → 2026-12-31` to:

```text
2015-01-01 → 2026-12-31
```

Earlier history remains **selective antecedent backfill**, not a requirement to make every series exhaustive before 2015.

This revision supersedes the first-round time-window recommendation in `docs/research/lithium-battery-collection-plan.md` for current work. The older plan is kept unchanged as historical design provenance.

## Why 2019 is too late

Starting at 2019 captures a downturn baseline, but it cuts off much of the causal setup that created that downturn. Longcycle needs a complete enough cycle to compare what actors knew and expected before, during and after turning points.

The 2015–2026 window is intended to cover, without assigning hindsight labels as facts:

```text
2015–2016  early demand / policy / investment acceleration and supply response setup
2017–2018  high-price / high-expectation phase, project commitments and the beginning of reversal
2018–2020  supply release, demand/policy changes, inventory and profitability pressure
2021–2022  new shortage / price / capex extreme
2023–2026  supply release, expectation revision, lower-price response and the next balance
```

The important point is not that these labels are already proven. The point is that a 2019 start prevents the archive from asking a first-principles question:

> Which expectations, contracts, projects and capital decisions made during the previous upswing created the Reality observed in 2019–2020?

That question is central to `Reality → Expectation → Outcome` replay.

## Anti-scope rule

The revision does **not** mean "collect everything since 2015 before continuing".

Use three scopes:

1. **Primary horizon — 2015–2026**: the benchmark should eventually support comparable point-in-time replay across this window.
2. **Selective antecedents — before 2015**: include only events needed to explain a material actor, project, contract, technology, policy or metric already inside the primary horizon.
3. **No automatic ancient-history expansion**: an interesting older story is not enough reason to widen the benchmark.

## Memory Campaign implication

The existing 600 blind leads remain valid unsourced research artifacts; they are not rewritten.

The horizon change creates an explicit negative-space test for batch3:

```text
For each high-value shard:
existing compact index
→ ask specifically what 2015–2018 causal setup is missing
→ classify output as new_category / useful_refinement / duplicate
→ measure novelty decay separately from ordinary batch3
```

Do not expose fresh web search. `search_visibility=none` remains mandatory until an individual shard satisfies its seal rule.

## Priority for the first pre-2019 batch3 passes

Start where the earlier cycle can most strongly explain later supply/demand outcomes:

1. `UP-HARDROCK` — project sanctioning, expansions, offtakes, cost curve and supply response;
2. `UP-CHEMICALS` — converter buildout, carbonate/hydroxide product structure and margins;
3. `DOWN-NEV` — subsidy/policy-driven demand expectations, vehicle mix and battery demand formation;
4. `MID-LFP` / `MID-TERNARY` — chemistry-share expectations and the route assumptions later reversed;
5. `BAT-CELL` — early capacity commitments, customer nomination and technology expectations.

Other shards follow based on compact-index gap density rather than calendar completeness.

## Evidence-stage implication

When shards later seal, historical evidence search should explicitly include original material from the 2015–2018 setup period. The goal is not to prove that 2018 was "the low" or "the top" from hindsight; it is to reconstruct what prices, projects, inventories, demand expectations and management actions looked like *at the time*.
