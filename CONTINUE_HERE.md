# CONTINUE HERE — Longcycle Development Handoff

If this is a fresh chat/session and the user says “继续 Longcycle”, “继续处理”, or otherwise asks to resume this project, **do not ask them to reconstruct prior context**.

Use GitHub as the continuity source of truth.

## Mandatory bootstrap

1. Confirm repository: `lly8666/longcycle-core`.
2. Fetch the live state of active PR #1 and branch `design/industry-memory` unless `.longcycle/handoff/current.json` says the active work moved elsewhere.
3. Read `.longcycle/handoff/current.json`.
4. Read `docs/development/project-constitution.md`.
5. Read `docs/development/session-handoff-protocol.md`.
6. Read only the checkpoint `resume_read_set` required for the active task.
7. Compare live HEAD with `checkpoint_based_on_head_sha`.
8. If HEAD moved, inspect/reconcile the delta before trusting checkpoint counters or CI state.
9. Fetch the latest CI for the live HEAD / active PR. CI recorded in the checkpoint is only a snapshot.
10. Continue `ordered_next_actions` unless a newer user instruction or repository change supersedes them.

## Current non-negotiable research guardrail

The lithium-battery Memory Atlas is in blind memory exhaustion. **Do not perform fresh web self-verification for an unsealed shard.** Model memory remains a search lead, never Evidence.

## Conflict order

When sources disagree about what to do next, use this precedence:

```text
new explicit user instruction
> live repository state / live CI
> project constitution and hard guardrails
> current handoff checkpoint
> append-only devlogs
> old chat summaries
```

A stale chat summary must never override current GitHub state.

## Why checkpoint HEAD will normally differ

`current.json` cannot contain the SHA of the commit that contains itself without circularity. It records the HEAD inspected immediately before its write. A small delta is expected; inspect it rather than treating it as an error.

For the full protocol, read `docs/development/session-handoff-protocol.md`.