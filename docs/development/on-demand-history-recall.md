# Longcycle On-demand Historical Recall Protocol v1

> `HISTORICAL_RECALL_PROTOCOL_V1`
>
> This is a retrieval protocol for cold project history, not a new source of truth and not a default bootstrap document.

## Goal

Longcycle sessions are intentionally short and repeatedly handed to fresh Agents. The normal handoff must stay bounded, but a future Agent must still be able to recover an old design discussion, benchmark lesson or rejected alternative when the current task makes that history relevant.

The target behavior is **latent project memory**:

```text
normal session
  → do not preload old history

historical cue appears
  → retrieve only the smallest relevant memory pointer
  → drill into original Git / Issue / receipt when needed
  → return to the current task
```

This protocol must never turn old summaries into a second authority plane.

## What stays hot, warm and cold

**Hot / default bootstrap**

- `STRATEGIC_COMPASS.md`
- `METHODOLOGY_CORE.md`
- `.longcycle/handoff/current.json`
- `.longcycle/capabilities/active-index.json`
- bounded current active context

**Warm / selectively loaded distilled memory**

- matching Capability cards: what the system already owns and where it may be extended;
- matching Repair Memory cards: validated invariants and known regression traps;
- current admission / explicit deferred design-pressure artifacts when the cursor points to them.

**Cold / never preloaded just to feel safer**

- Git commits and diffs;
- GitHub issues/comments and old one-shot receipts;
- old handoffs and devlogs;
- old benchmark receipts and industry artifacts not needed by the current cursor.

Git history and canonical repository artifacts remain the authority for what actually happened. Warm memory is a routing/distillation layer only.

## Recall triggers

Run bounded historical recall when at least one of these is true:

1. the Agent or user has a fuzzy signal that the same design question, failure or benchmark may have been discussed before;
2. a proposed change touches a `core_locked` capability's owned semantics, migration boundary or non-goal;
3. current evidence appears to contradict an existing Method Core rule, Capability owner or Repair invariant;
4. an admission decision is leaning toward `new` or `replace` and historical rationale could show why the current owner exists;
5. a legacy artifact/schema behaves differently from the current implementation and provenance is needed before deciding whether to support, upgrade or retire it.

Ordinary implementation work inside an established extension seam does not require historical archaeology.

## Bounded retrieval route

Use this order and stop as soon as the design question is resolved:

```text
1. capability registry relevant/query
      ↓ identify semantic owner + extension seams + guards
2. repair-memory relevant/query
      ↓ recover active invariant + origin_refs
3. follow exact origin refs / scoped paths
      ↓ migration / commit / issue / benchmark receipt
4. only if still unresolved: bounded Git/Issue search
      ↓ narrow keywords + owner paths + approximate time window
5. read the smallest matching original material
```

Do not crawl all devlogs, all issues or the full repository history as a default recall strategy.

When a card has `origin_refs`, prefer those pointers over fuzzy keyword search. If a pointer is stale or incomplete, fix the distilled card after verifying the original history rather than teaching future Agents to compensate with broader crawling.

## Authority and contamination rules

- A remembered phrase from chat or an Agent's vague recollection is only a **retrieval cue**, never project truth.
- A Capability/Repair summary is a current distilled contract, but original Git/Issue/receipt history is consulted when the question is specifically "why was this chosen?" or "what alternatives were rejected?".
- Old design reasoning does not automatically overrule a newer explicit user decision, Method Core revision, superseding Capability/Repair card or real benchmark evidence.
- Do not paste large historical narratives into `current.json`; handoff remains a live cursor, not long-term memory storage.
- Do not automatically summarize every session into a permanent memory item. Most history should stay cold in Git.

## Promotion rule

After historical recall, persist something into the warm/hot path only when forgetting it again would plausibly cause architectural drift or repeated expensive failure:

```text
one-off historical detail
  → leave in Git / receipt / devlog

repeatable regression invariant
  → Repair Memory

stable system responsibility / extension seam
  → Capability Registry

cross-industry long-term method
  → Method Core

current next action / blocker
  → handoff current.json
```

Prefer updating an existing owner/card over creating another memory object.

## Why there is no separate long-term-memory database in v1

The repository already has durable cold history plus two compact semantic indexes. A new vector store or continuously rewritten project summary would add synchronization, stale-summary and authority problems before there is evidence that deterministic routing is insufficient.

If future project scale makes deterministic lookup too weak, semantic/embedding retrieval may be added as a **candidate router over repository pointers**. It must never become the authority for history, and retrieval results must still resolve to exact repository/Issue/receipt origins before they influence a core architectural change.
