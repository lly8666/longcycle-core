# CONTINUE HERE — Longcycle Development Handoff

If this is a fresh chat/session and the user says “继续 Longcycle”, “继续处理”, or otherwise asks to resume this project, **do not ask them to reconstruct prior context**.

Use GitHub as the continuity source of truth — but recover **direction before task state**.

## Mandatory bootstrap

1. Confirm repository: `lly8666/longcycle-core` and resolve the active PR/branch through GitHub issue #2 when needed.
2. Read `STRATEGIC_COMPASS.md` **before reading the current TODO as an execution instruction**.
3. Read `docs/development/project-constitution.md`.
4. Read `.longcycle/handoff/current.json`.
5. Read `docs/development/session-handoff-protocol.md`.
6. Fetch the live state of the active PR/branch and compare HEAD with `checkpoint_based_on_head_sha`.
7. If HEAD moved, inspect/reconcile the delta before trusting checkpoint counters or CI state.
8. Fetch the latest CI for the live HEAD / active PR. CI recorded in the checkpoint is only a snapshot.
9. Read only the checkpoint `resume_read_set` needed for the immediate work.
10. Pass the **Strategic Alignment Gate** below before making substantive changes.
11. Continue `ordered_next_actions` only if they still serve the strategic hierarchy and have not been superseded by a newer user instruction or repository change.

## Strategic Alignment Gate

Before substantive work, be able to state from repository evidence:

1. Longcycle's end-state mission.
2. What the lithium benchmark must prove before generic platform expansion is justified.
3. Where the current phase sits in the chain from Memory Atlas to Evidence to Reality/Expectation/Outcome replay.
4. Why the immediate next action advances that benchmark rather than merely optimizing a tool.
5. What the next **larger** strategic step is after the current batch.

If these cannot be answered, do not blindly execute the TODO. Re-read `STRATEGIC_COMPASS.md` and re-rank the work.

## Current non-negotiable research guardrail

The lithium-battery Memory Atlas is in blind memory exhaustion. **Do not perform fresh web self-verification for an unsealed shard.** Model memory remains a search lead, never Evidence.

## Two precedence planes

Do not mix strategy authority with implementation freshness.

### Direction / strategy

```text
new explicit user instruction
> STRATEGIC_COMPASS.md
> project constitution / durable commitments
> current handoff ordered plan
> devlogs / old chat summaries
```

### Live implementation state

```text
live GitHub HEAD / commit graph / live CI
> canonical or deterministic repository artifacts
> current handoff checkpoint snapshot
> PR/README/devlog narrative
> old chat summaries
```

A technically fresh commit cannot silently redefine product direction; a strategic document cannot override live CI or current file contents about implementation facts.

## Why checkpoint HEAD will normally differ

`current.json` cannot contain the SHA of the commit that contains itself without circularity. It records the HEAD inspected immediately before its write. A small delta is expected; inspect it rather than treating it as an error.

For the full protocol, read `docs/development/session-handoff-protocol.md`.