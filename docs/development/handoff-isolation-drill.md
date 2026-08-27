# Context-Isolated Handoff Drill

## Purpose

Longcycle development must survive a forced new chat without asking the user to reconstruct project context. This drill measures how much of the current project state can be reconstructed from the repository alone.

It is intentionally stricter than reading a prose summary. The drill reads repository artifacts and derives current research counts from raw blind-memory files instead of trusting the checkpoint count.

## What is isolated

The automated drill in `src/longcycle/application/handoff_drill.py` is allowed to read only repository files from the checkout. It does not receive conversation history, previous assistant summaries, or manually supplied current-state facts.

It reconstructs:

- repository / active branch / active PR from the typed checkpoint;
- campaign identity, industry, phase and search visibility;
- actual raw Memory Lead count by scanning blind JSONL files;
- shard count and per-shard counts;
- sealed-shard state;
- user directives and north-star principles;
- forbidden shortcuts;
- ordered next actions.

It then cross-checks `current.json`, `coverage-index.json`, raw campaign files, `CONTINUE_HERE.md`, and the project constitution.

## What remains live-only

A repository checkout cannot prove that it is the newest remote state. Therefore the drill does **not** replace the mandatory fresh-session live refresh:

1. resolve the active PR/branch through the rendezvous issue if necessary;
2. fetch live PR/branch HEAD;
3. compare live HEAD with `checkpoint_based_on_head_sha`;
4. inspect the delta when they differ;
5. fetch the newest CI run for live HEAD.

Git HEAD and live CI remain authoritative over checkpoint snapshots.

## Fidelity score

The repository-only drill reports a score from 0 to 1 over deterministic checks. A score of `1.0` means the checked repository artifacts agree with the raw campaign state and contain enough bootstrap intent to resume work. It does **not** mean the remote branch has no newer commits; live HEAD reconciliation is still required.

The test suite also constructs a deliberately stale checkpoint with an incorrect lead count. The drill must detect the mismatch without using chat context while still recovering the actual lead count from raw JSONL.

## Failure interpretation

A failure should be treated as a handoff-system defect, not as a reason to ask the user to restate project history. Fix the repository checkpoint, coverage, bootstrap contract, or delta-reconciliation logic and rerun the drill.
