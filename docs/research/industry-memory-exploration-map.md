# Industry Memory Exploration Map v1

## Purpose

An Industry Memory Exploration Map is the bounded CAP-0006 control surface for answering:

1. which parts of a time-bounded industry have been deliberately probed;
2. where important blind-memory gaps or adjacent frontiers remain;
3. which single bounded probe should run next; and
4. whether one shard is eligible for a separate seal review.

It is not an industry truth graph, Evidence store, dense completion score or claim that the model
contains every relevant historical fact. Model-memory coverage and Evidence coverage remain
separate authority planes.

## State machine

An industry or shard moves only through explicit states:

```text
orientation_only
-> active_recall
-> low_novelty_confirmation
-> seal_candidate
-> sealed
-> evidence
```

`orientation_only` cannot transition directly to `sealed`. A historical seal is immutable; a later
model vintage, scope change or material omission creates an append-only correction/supersession and
a new active recall vintage rather than rewriting the sealed artifact.

## Sparse map, not a Cartesian task list

Time slices, shards and audit lenses describe possible coverage. They do not create an obligation
to run every time-by-shard-by-lens cell. The current map stores only:

- compact per-shard stage and recent novelty state;
- reviewed high-value regions and known major gaps;
- explicit deferred/out-of-scope regions;
- at most 64 open frontiers with unique priority ranks;
- one deterministic `next_probe` selected from the highest-ranked unblocked open frontier;
- exact pointers to the campaign, current prompt, bounded learning state and latest pass receipt.

Lower-value regions may be `deferred` with a reason. `reviewed_no_specific_memory` means that a cell
was deliberately probed but no sufficiently specific model-memory lead was retained. It is never
Evidence that nothing occurred and never means `false`.

Raw leads, old prompts, old maps and completed receipts remain cold append-only Git history. The
current map is a replaceable compact index, not a session diary.

The discoverable hot entrypoint is always `<campaign-root>/exploration-map.json`. It carries one
exact `learning_state_ref`, one current prompt ref, one latest pass-receipt ref and one selected
`next_probe`. An industry worker cursor retains exactly this one map path in `artifact_refs`; it does
not accumulate prior map revisions or raw pass paths. Moving the entrypoint requires an explicit
cursor update, so a Fresh Agent never guesses which of many files is current.

## One pass produces two kinds of learning

Every bounded blind pass produces:

1. **industry-memory output** — immutable unsourced leads plus honest novelty classification; and
2. **method observation** — at most one currently important activation failure or method hypothesis.

The method observation classifies the likely failure as one of:

- time-horizon truncation;
- shard/topology omission;
- prompt/audit-lens failure;
- salience or survivor bias;
- terminology/search-archaeology weakness;
- schema/atomicity failure; or
- scope drift that should become a satellite/bridge frontier.

A campaign-local prompt may change by one bounded hypothesis and be tested with a fresh orthogonal
probe. A local improvement becomes cross-industry method only after separate industries reproduce
the benefit and normal Method Core governance accepts it. Agents may not weaken blind/search,
Evidence, PIT/no-lookahead, sealed immutability, reservation or Baseline boundaries.

## Pass receipt

The durable pass receipt records only reproducible facts needed for continuation:

- campaign/shard/pass id and prompt version;
- exact allowed input/index digest and `source_visibility`;
- new-category, useful-refinement and duplicate counts;
- newly opened or closed frontiers;
- current method observation and proposed validation probe, when present;
- validation refs and whether the pass remains unverified;
- explicit statement that one pass cannot self-seal.

The raw output and receipt are pushed together as the substantive/WIP checkpoint `S`. The current
map is rebuilt or updated from receipts. The following cursor-only `H` points to the one current map
entrypoint and its accounted `S`; it does not list every period packet or raw lead file.

## Seal gate

`evaluate_campaign_saturation` is a fail-closed readiness check, not a model opinion. Eligibility
requires all of the following:

- stage is `seal_candidate`;
- no fresh-search contamination of the blind vintage;
- no major uncovered first-order block;
- required long-tail families are present;
- enough recent low-novelty passes exist;
- those recent passes use the configured number of distinct families;
- explicit negative-space review is complete; and
- an independent challenger review is complete.

High-importance novelty resets readiness. Three repetitions of the same prompt/lens do not count as
orthogonal confirmation. Coverage headings, a large lead count or a model statement that it has
"nothing else" never authorizes seal.

Seal is shard-local. Sealed shards may enter post-seal verification while independent unsealed
shards continue isolated blind recall.

Every new structured `seal` or `saturation` claim must carry exactly one `seal_decision_ref` using
`longcycle-memory-seal-decision/v1`. The decision binds the exact artifact path and SHA-256 digest,
the blind source-visibility state, three distinct pass ids/families/receipt refs, negative-space and
independent-challenger refs, coverage gaps, policy and the recomputed result. Worker CI recomputes
the decision; a self-declared green result cannot authorize itself.

A premature historical seal is not rewritten. Append one
`longcycle-memory-seal-supersession/v1` record that binds the exact old path and digest, names the
open replacement stage and points to the correction. This is the only compatibility route for a
pre-gate seal; prose saying "superseded" is informative but not machine-enforceable.

Minimal seal-decision shape (the sealed artifact itself carries `seal_decision_ref`):

```json
{
  "schema_version": "longcycle-memory-seal-decision/v1",
  "campaign_id": "...",
  "shard_id": "...",
  "model_vintage": "...",
  "sealed_artifact_path": "research_data/memory/.../atlas.json",
  "sealed_artifact_sha256": "...",
  "source_visibility": "none",
  "review": {
    "campaign_stage": "seal_candidate",
    "negative_space_review_complete": true,
    "negative_space_review_ref": "research_data/memory/.../negative-space-review.json",
    "independent_challenger_complete": true,
    "independent_challenger_ref": "research_data/memory/.../challenger-review.json",
    "fresh_search_used": false
  },
  "has_major_coverage_gaps": false,
  "required_long_tail_families_missing": [],
  "recent_outcomes": [
    {
      "pass_id": "...",
      "family": "...",
      "receipt_ref": "research_data/memory/.../pass-receipt.json",
      "novel_lead_count": 0,
      "duplicate_lead_count": 0,
      "high_importance_novel_count": 0
    }
  ],
  "declared_result": {
    "saturated": true,
    "reason_codes": ["orthogonal_passes_reached_low_marginal_novelty"]
  }
}
```

`recent_outcomes` must contain at least the three policy-required, distinct pass/family/receipt
observations; the shortened example shows one item only to document the item shape. A caller may
tighten the default policy but cannot lower the three-pass, three-family or high-importance safety
floors. Only the latest at most eight outcomes belong in the hot decision; older receipts remain in
Git history.

Minimal correction shape:

```json
{
  "schema_version": "longcycle-memory-seal-supersession/v1",
  "campaign_id": "...",
  "reason_code": "premature_orientation_seal",
  "replacement_stage": "orientation_only",
  "correction_ref": "research_data/memory/.../correction.json",
  "superseded_seals": [
    {
      "artifact_path": "research_data/memory/.../old-atlas.json",
      "artifact_sha256": "..."
    }
  ]
}
```

## Fresh-Agent and interruption recovery

The durable role is the Industry Campaign Lead; individual Agent instances are disposable.

Normal startup is:

```text
refresh remote main reservation + exact worker ref
-> derive CLEAN / RECOVERY_REQUIRED / BLOCKED
-> if needed, repair the prior S-without-H first
-> read the one current exploration-map entrypoint
-> load only its current campaign/prompt/learning/pass pointers
-> execute one next_probe
```

If interruption occurs after `S` but before `H`, the successor inspects the bounded remote delta,
validates or marks it partial, updates/rebuilds the map, and pushes the missing cursor acknowledgement
before new work. Unpushed work is repeated from the last remote `next_probe`.

The worker cursor keeps one exploration-map artifact pointer instead of appending all campaign files.
This preserves the existing eight-refs-per-kind and 24-total-ref continuity bounds as an industry
grows over years.

## Role boundary

- **Industry Campaign Lead:** owns the current sparse map, local prompt evolution and next-probe
  ranking inside its reservation.
- **Blind Probe Agent:** executes one isolated task packet and reports leads/observations; it cannot
  change scope or seal.
- **Saturation Challenger:** reads only the compact atlas/map and proposed seal record; it may veto
  seal but does not create a quota-filling history pass.
- **Coordinator/integration lane:** owns shared CAP-0006 rules, worker creation, shared changes and
  promotion of repeated cross-industry lessons.

Multiple writers never update one current map concurrently. Parallel probes use separately reserved
branches/paths and become visible through typed receipts; one Industry Campaign Lead incorporates
accepted receipts into the current map.
