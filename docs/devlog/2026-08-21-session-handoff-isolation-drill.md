# 2026-08-21 — Session Handoff Isolation Drill

## Why this exists

The user explicitly asked whether Longcycle could test cross-chat handoff fidelity with context isolated. The project cannot rely on a long chat remaining open, so a new session must reconstruct intent and execution state from the repository rather than asking the user to retell the project.

The closest deterministic isolation available in the current development environment is a CI process that receives the repository checkout but no conversation history. It is intentionally not allowed to trust the checkpoint's campaign count; it derives the raw Memory Lead count from `blind/*/*.jsonl` and cross-checks other repository state against that result.

## Drill contract

`src/longcycle/application/handoff_drill.py` reconstructs and checks:

- repository, active branch and PR;
- campaign identity, industry and phase;
- search visibility and sealed shards;
- raw Memory Lead total and per-shard counts derived from JSONL;
- north-star principles and persisted user directives;
- forbidden shortcuts;
- ordered next actions;
- bootstrap references to the live checkpoint and mandatory live refresh.

A deliberately stale checkpoint fixture must be rejected without using chat history.

Live GitHub HEAD and CI remain a separate mandatory layer because a checkout cannot prove that no newer remote commit exists.

## What the drill actually caught

The first CI execution did not pass. Repository-only fidelity was `0.9`, not `1.0`.

The total Memory Lead count was already correct at 570 and the major continuation semantics were recoverable, but `coverage-index.json` did not agree with the raw JSONL on per-shard allocation. A diagnostic revision exposed the exact mismatch:

- `BAT-CELL`: coverage said 54, raw JSONL said 52;
- `UP-CHEMICALS`: coverage said 52, raw JSONL said 54.

The two errors offset each other, so a total-only check would never have found them. This is precisely the failure class the isolation drill is intended to prevent: a fresh chat could otherwise inherit a globally plausible but locally wrong project state.

The coverage allocation was corrected and CI run #194 then completed with:

- Mypy: no issues in 55 source files;
- Pytest: 125 passed;
- final correctness gate: success.

Because `test_repository_only_reconstruction_matches_current_campaign` requires `fidelity_score == 1.0`, this validates all ten deterministic repository-only checks on that checkout. The stale-checkpoint negative test also passed.

## Design correction learned from the drill

Early handoff tests hard-coded the evolving lead count (`552`, then `570`). That created a second copy of fast-changing state and forced tests to be edited whenever research advanced.

That pattern has now been removed. The durable contract is:

```text
raw blind JSONL
    ↓ derive
actual campaign counts
    ↓ compare
coverage-index.json + current.json
```

Tests validate agreement rather than storing their own copy of the current count.

## Research continued during the drill

Blind recall remained isolated from web search throughout. After the 570-lead checkpoint, `UP-HARDROCK` self-gap batch2 added six further structural leads, taking the raw campaign to 576. The new dimensions include ore-domain/blending variability, DSO versus SC6 product semantics, mining-services constraints, financing-linked offtake, dry/wet-tonne pricing basis, and price-driven mine-plan/cut-off-grade supply elasticity.

No shard has met the seal rule. `search_visibility` remains `none`.

## Remaining limitation

This drill is context-isolated at the repository/CI-process level, but it is not literally a separately spawned language model with erased conversation memory. A future multi-agent harness should add a second-stage semantic reconstruction benchmark: give a fresh model only the rendezvous issue and repository access, ask it a fixed continuation questionnaire, and compare its reconstructed answer with the typed checkpoint and live GitHub state.

Until such an agent-spawn capability exists, the required handoff chain remains:

```text
repository-only deterministic drill
+ live HEAD delta reconciliation
+ live CI refresh
```
