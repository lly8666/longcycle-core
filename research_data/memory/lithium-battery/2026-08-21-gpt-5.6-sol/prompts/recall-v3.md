# Recall Prompt v3

This prompt keeps v2's epistemic rules and adds a strict generation contract.

You are generating UNSOURCED MODEL-MEMORY LEADS for one atomic lithium-battery shard. You have not seen fresh web results, archive results, or neighboring shard outputs.

## Purpose

Use latent model knowledge as a historical search-index generator. Do not write an industry report. Surface recoverable historical leads, especially long-tail items ordinary broad search may miss.

## Truth boundary

A Memory Lead is never Evidence, Fact, Judgment, or Canonical Truth. Do not invent citations, URLs, report titles, page numbers, exact dates, exact ownership, or exact numbers when not strongly recalled.

## Atomicity rule

One object = one minimum proposition or one minimum search direction.

If you remember:

> event A happened and therefore mechanism B caused outcome C

emit separate objects for A, B/C, and connect them later through `relations` only after validation. Do not bundle them.

## Allowed enums — use only these exact strings

### lead_kind

- landmark
- missing_event
- actor
- terminology
- metric
- mechanism
- pricing_rule
- contract_change
- process_bottleneck
- project_pattern
- inventory_pattern
- capital_cycle
- policy_shift
- technology_shift
- cross_industry_dependency
- narrative
- causal_hypothesis
- anomaly
- failure_dead_end

### claim_scope

- legal_disclosure
- official_statistic
- self_statement
- management_guidance
- market_measurement
- project_status
- policy_text
- third_party_fact
- industry_expectation
- technical_specification
- other

### memory_basis

- remembered_event
- remembered_actor_or_name
- remembered_mechanism
- associative_inference
- mixed

### precision_risk

- low
- medium
- high
- unknown

### entity_resolution_state

- stable
- partially_resolved
- ambiguous
- unresolved

## Mandatory uncertainty fields

Always populate:

- `precision_risk`
- `entity_resolution_state`
- `uncertain_fields`

A high-confidence broad memory may still have high precision risk.

## Mandatory search archaeology

Always populate:

- `aliases_or_old_terms`
- `why_search_may_miss_it`
- `suggested_queries`
- `suggested_source_types`

For obscure leads, explain whether the retrieval problem is caused by renamed companies/projects, failed firms, ownership transfer, old terminology, dead IR pages, local-language names, PDF-only material, or citation chains.

## Mandatory falsification

Always populate:

- `disconfirmation_queries`
- `disconfirmation_source_types`

Do not generate a lead with no plausible way to prove it wrong.

## Scope control

If an important tangent belongs outside the shard, do not expand it. Put the target shard/bridge in `satellite_trigger`.

## Long-tail budget

Use no more than 20% of output for obvious anchor events. At least 30% should target one of:

- failed/cancelled/delayed projects;
- forgotten actors;
- ownership/name changes;
- old terminology;
- contract/pricing mechanisms;
- engineering/qualification/logistics constraints;
- minority historical narratives;
- facts awkward for the standard retrospective story.

## Output format

Return JSONL only, one JSON object per line, no Markdown and no commentary.

Required keys on every object:

`lead_id`, `shard_id`, `pass_id`, `lead_kind`, `claim_scope`, `memory_basis`, `summary`, `approximate_period`, `memory_confidence`, `importance_score`, `novelty_score`, `searchability_score`, `precision_risk`, `entity_resolution_state`, `uncertain_fields`, `aliases_or_old_terms`, `why_search_may_miss_it`, `recalled_details`, `possible_actors`, `suggested_queries`, `disconfirmation_queries`, `suggested_source_types`, `disconfirmation_source_types`, `satellite_trigger`, `relations`.

Before emitting each line, self-check that all enum fields exactly match the allowed lists above. If no perfect `lead_kind` exists, prefer the least committal valid kind (`mechanism`, `anomaly`, or `missing_event`) instead of inventing a new enum.