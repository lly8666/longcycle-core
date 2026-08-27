# Prompt / Schema Observations

## Experiment 1 — UP-HARDROCK timeline+actors / recall-v1

### What worked

The first 30-lead blind pass surfaced useful long-tail categories without web search:

- previous-cycle failures and restarts (care-and-maintenance, administration, restarted assets);
- project/company rename and ownership-chain search problems;
- African project execution and local-beneficiation policy leads;
- domestic Chinese resource-auction / high-altitude / lepidolite leads;
- pricing-contract lag and effective-supply semantics;
- non-obvious comparability problems such as concentrate grade and concentrator-train capacity.

This supports the memory-first premise: the model can produce a much richer search directory than a broad instruction given directly to a low-cost search agent.

### Prompt weaknesses observed

1. **Atomicity is still weak.** Some records combine event + consequence + mechanism.
2. **`recalled | inferred | mixed` is too coarse.** A recalled actor name and a recalled event have different reliability profiles; an inferred mechanism should not look like an uncertain historical event.
3. **Uncertainty is buried in prose.** Ownership, exact timing, project stage and entity identity need structured `uncertain_fields`.
4. **No falsification contract.** Each lead should say what query/source could contradict it, not only how to support it.
5. **Search-miss reason is not explicit.** Historical retrieval value increases when the model explains whether the item is likely hidden by old names, ownership changes, dead links, local-language terminology, failed projects, or secondary citation chains.
6. **Scope drift occurred.** Yichun lepidolite appeared inside `UP-HARDROCK`; this is useful evidence that satellite-shard promotion must be automatic rather than treating scope drift only as an error.
7. **Famous actors still consume recall budget.** The next prompt should impose long-tail/failure quotas after a short anchor phase.
8. **Current JSON Schema does not match real output.** `failure_dead_end`, `precision_risk`, `memory_basis`, `uncertain_fields`, and disconfirmation search are absent. With `additionalProperties=false`, real v1 output is intentionally preserved as raw experiment data but is not schema-conformant.

## Prompt v2 decisions

### Separate recall basis from confidence

Use:

- `remembered_event`
- `remembered_actor_or_name`
- `remembered_mechanism`
- `associative_inference`
- `mixed`

`memory_confidence` remains recall strength only.

### Add precision risk

`precision_risk` answers a different question:

> Even if the broad memory is useful, how risky are the names/dates/numbers/ownership details?

A lead may therefore be `memory_confidence=0.9` and `precision_risk=high`.

### Add falsification fields

Every lead must include:

- `disconfirmation_queries`
- `disconfirmation_source_types`
- `uncertain_fields`

### Add search archaeology fields

Every non-obvious lead should include:

- `why_search_may_miss_it`
- `aliases_or_old_terms`
- `entity_resolution_state`

### Enforce proposition splitting

If one sentence contains a remembered event and a causal interpretation, emit two leads and connect them later through a relation.

### Treat scope drift as a promotion signal

If a recurring topic is outside the current shard but materially affects the cycle, emit a `satellite_trigger` in details and do not expand it inside the current pass.

## Expected v2 improvement test

Run `UP-CHEMICALS` with v2. Evaluate whether:

- at least 80% of leads are atomic without manual splitting;
- all uncertain entity/date/number details are structured;
- at least 25% are long-tail/failure/old-term leads rather than famous landmarks;
- every lead contains a disconfirmation path;
- scope drift becomes an explicit satellite trigger rather than a silently expanded tangent.