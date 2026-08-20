# Lithium Battery Memory Exhaustion Prompt v4 — Self-Gap Pass

Purpose: extract additional UNSOURCED model-memory leads from one already-recalled shard without fresh web search and without reading other shards' raw outputs.

## Inputs allowed

- fixed industry ontology and historical period;
- this shard's own compact lead index / coverage summary;
- protocol and schema definitions.

## Inputs forbidden

- fresh web search results;
- current search snippets;
- other shards' raw lead text;
- evidence archive contents not already included in the shard coverage summary.

## Core rule

Do NOT answer “what else do you know?” broadly. Audit the shard through missing dimensions. Every new lead must state why it was not naturally activated in the earlier pass.

## Gap matrix

Check each dimension independently:

1. time gaps — early/late cycle, transition quarters, temporary bottlenecks;
2. actor gaps — second-tier players, failed entrants, renamed/acquired actors;
3. project gaps — cancelled, delayed, restarted, low-utilization or stranded projects;
4. metric gaps — hidden denominators, methodology changes, inventory locations, utilization/qualification states;
5. pricing/contract gaps — formula pricing, long-term agreements, captive supply, prepayments, rebates, premiums/discounts;
6. technology gaps — pilot vs mass production, qualification, product-generation changes;
7. expectation gaps — consensus, minority view, long-dated forecasts, management guidance revisions;
8. terminology gaps — historical names, aliases, old PDF/search vocabulary, former company/project names;
9. failure gaps — stories that were important then but disappeared because they failed;
10. cross-boundary triggers — important tangent that belongs in a separate satellite/bridge, not expanded here.

## Anti-duplication rules

- Do not restate an existing lead with different words.
- A refinement is allowed only when it adds a new actor, mechanism, historical name, falsification path, or point-in-time expectation vintage.
- Famous headline events have lower priority unless a previously missing mechanism or revision chain is added.
- Separate remembered event/mechanism from associative inference.
- Never invent citations or false precision.

## Required additional field in reasoning notes

For each candidate include inside `recalled_details`:

`gap_reason`: why earlier broad recall likely missed this lead.

## Stopping logic

Run in small batches. After each batch classify each lead as:

- new category;
- useful refinement;
- duplicate/near-duplicate.

A shard approaches saturation only after three consecutive self-gap batches produce very few high-importance new-category leads and the gap matrix has no obvious empty cells.
