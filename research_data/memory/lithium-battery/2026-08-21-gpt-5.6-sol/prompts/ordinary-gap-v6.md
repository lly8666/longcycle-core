# Lithium Battery Memory Exhaustion Prompt v6 — Matrix-Driven Ordinary Gap Probe

Purpose: measure marginal blind-memory novelty on one first-order replay gap selected by the repository negative-space matrix. This is not a quota-filling recall pass and not a fresh-search task.

## Inputs allowed

- the selected shard's deterministic compact index only;
- that shard's row in `analysis/negative-space-gap-matrix-v1.json`;
- `prompts/self-gap-v4.md` as the fixed gap-lens boundary;
- fixed campaign ontology, schema, horizon and methodology.

## Inputs forbidden

- fresh web/search results or snippets;
- evidence archives or current-source material;
- neighboring shards' raw Memory Leads;
- hidden replacement research intended to make shard counts symmetric.

## Core rule

Audit only the matrix-selected first-order replay gap. Recover mechanisms, expectation vintages, failed paths or measurement semantics that could materially change a no-lookahead explanation of the benchmark cycle.

Do not broaden into an industry history. Do not repeat old leads merely to create a full batch.

## Effective-quantity discipline

When the selected gap concerns supply or demand translation, distinguish the relevant state chain instead of treating a headline quantity as realized economic supply/demand. Examples include:

- nameplate -> commissioned -> ramped -> qualified -> utilized -> saleable/shipped;
- ore mined -> stockpiled -> processed -> recovered -> product-grade output -> accepted/shipped;
- reported activity -> inventory/channel adjustment -> unit intensity -> realized material demand.

Preserve timing, ownership, product/metric basis, and contemporaneous expectation revisions when material.

## Novelty classification is mandatory

For every candidate, classify it in `recalled_details.batch_classification` as exactly one of:

- `new_category` — introduces a materially missing replay dimension;
- `useful_refinement` — adds a new actor/mechanism/state/expectation vintage/falsification path to an existing dimension;
- `duplicate` — materially repeats an existing compact lead or adds no decision-relevant information.

Duplicates are valid observations. Do not suppress them just to keep novelty high. A duplicate candidate should remain clearly marked rather than rewritten until it appears novel.

## Required reasoning notes

Each candidate must include:

- `gap_reason`: why the compact layer did not already resolve it;
- `batch_classification`;
- `replay_link`: how the candidate could change or test the point-in-time Reality/Expectation replay;
- uncertainty and disconfirmation queries; no invented citation or false precision.

## Batch and stopping logic

- Keep the probe small: normally 3-6 candidates, fewer if recall is exhausted.
- Do not target a fixed number of non-duplicates.
- After the probe, count `new_category`, `useful_refinement`, and `duplicate` separately.
- A high-novelty result resets the shard's consecutive-low-novelty streak to zero.
- A low-novelty result is only one observation; seal eligibility still requires three consecutive low-novelty batches plus explicit negative-space review with no material uncovered dimension.
- One productive probe does not automatically authorize the next-ranked shard. Return to the matrix and re-rank.

## Search boundary

`search_visibility=none` remains mandatory. Memory is discovery input, never evidence. Fresh self-verification/search begins only after the referenced shard legitimately seals.
