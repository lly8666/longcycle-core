# 2026-08-21 — Fresh-chat handoff remediation

## Trigger

A genuinely fresh chat audited the repository using only the repository identifier plus the handoff bootstrap request and wrote `docs/devlog/2026-08-21-fresh-chat-handoff-audit.md` as its only mutation.

The audit successfully reconstructed the active branch/PR, checkpoint delta, live CI, project north star, epistemic guardrails, 600-lead lithium Memory Campaign state, zero sealed shards, `search_visibility=none`, latest coherent milestone and ordered next actions without asking the user to restate context.

## Defects found by the fresh chat

The report found three real continuity defects:

1. PR #1 body duplicated fast-moving campaign/CI state and had drifted to an older 576-lead / older-CI snapshot.
2. `coverage-index.json` mixed research coverage with a stale CI-status annotation.
3. `checkpoint_generated_at` was manually entered and inconsistent with Git commit ordering; it must not be treated as provenance authority.

The report correctly treated `checkpoint_based_on_head_sha != live HEAD` as expected self-reference behavior rather than a defect.

## Additional defect found during remediation review

The deterministic repository drill's `fidelity=1.0` verifies fields that can be mechanically reconstructed, but does not prove curated research judgments such as `6/6 new/useful`, gap severity, semantic importance or bridge/satellite promotion.

A fresh session must therefore distinguish:

- canonical / immutable state;
- deterministic-derived state;
- curated research assessment;
- narrative state.

Internal consistency or a passing CI test must not upgrade a curated research assessment into a deterministic fact.

## Remediation

- PR #1 now contains stable design context only and explicitly points dynamic state to issue #2, the typed checkpoint, campaign artifacts and live GitHub CI.
- `coverage-index.json` no longer stores a CI run snapshot and now declares authority classes for counts versus novelty/priority assessments.
- the typed handoff contract removes the manually authored checkpoint timestamp and uses `provenance_ordering = git_commit_graph`;
- the handoff protocol explicitly defines state-authority classes and Git commit ordering;
- the project constitution now preserves future-phase orchestration commitments, including high-model self-verification after seal, lower-agent evidence-only delegation, dynamic topology promotion, source-first current collection and model-vintage backfill;
- the fresh-chat audit protocol now separately asks for deterministic-state fidelity and semantic-plan recovery confidence.

## Why this matters

The goal is not merely that a fresh chat can quote the right current number. It must also know which numbers are machine-derived, which conclusions are research judgments, which prose is only narrative, and which future methods have already been settled even though the current workstream has not reached them.

This makes the continuity target two-dimensional:

```text
operational reconstruction
+ semantic / methodological reconstruction
```

Both are required for "原汁原味" continuation.
