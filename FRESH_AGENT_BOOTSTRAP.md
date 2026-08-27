# Longcycle — Fresh Agent Bootstrap

This file is a stable zero-context rendezvous pointer, not live project state.

## Canonical transfer phrase

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

## Post-Baseline cold start

Architecture exploration is no longer the default development mode. Start from the repository's live `main` branch unless GitHub issue #2 explicitly points to a temporary active PR/branch for current work.

1. Refresh live `main`/active-PR HEAD and CI; snapshots in handoff are never live authority.
2. Read `STRATEGIC_COMPASS.md` and `METHODOLOGY_CORE.md`, reconstruct mission/method in your own words, then use `.longcycle/continuity/mission-fidelity.json` only to challenge omissions/misreadings.
3. Read `.longcycle/baseline/current.json`, then its referenced manifest and `ARCHITECTURE_BASELINE_V1.md`. Treat the locked invariants as the default definition of semantic correctness.
4. Read `.longcycle/handoff/current.json` for the current horizon/cursor and `.longcycle/capabilities/active-index.json` for stable semantic ownership.
5. Before material development, write/update `.longcycle/change-contract/current.json` with `L1/L2/L3/L4`, then run the existing Capability Registry admission separately as `reuse / extend / replace / new`.
6. Default to L1/L2 + reuse/extend. A new industry is normally a Domain Pack/catalog/source/research extension, not a new Fact/Evidence/PIT architecture.
7. If the proposed change touches a locked Baseline invariant or changes the semantic expectation of a Baseline-critical regression, stop ordinary implementation and enter the L3 architecture-change procedure. `Cleaner`, `more generic` and `future-proof` are not sufficient evidence.
8. If a real source-grounded important case cannot be truthfully expressed through existing extension seams, preserve that counterexample and escalate it; Baseline v1 is stable by default, not dogmatically immune to evidence.
9. Query path-scoped Repair Memory before editing known paths. Do not infer that a new path has no semantic constraints merely because no repair card matches it.
10. Read only the minimal task-specific resume set. Do not preload old industries, old devlogs, old rehearsal reports or the full repository.

Detailed operational/source acquisition rules remain in `CONTINUE_HERE.md`; post-Baseline development rules live in `docs/development/post-baseline-development.md`.

## Authority by question

- terminal mission: `STRATEGIC_COMPASS.md`
- cross-industry research method: `METHODOLOGY_CORE.md`
- frozen semantic contract/change levels: `.longcycle/baseline/current.json` → manifest + `ARCHITECTURE_BASELINE_V1.md`
- semantic owner/extension seam: Capability Registry/cards
- current work: live Git + `.longcycle/handoff/current.json` + current admission/change contract
- actual implementation: migrations/code/tests/live CI
- historical rationale: Git/devlogs/receipts, read only on demand

## Source/data-plane reminder

Do not confuse Baseline freeze with frozen acquisition implementation. Preserve the existing epistemic rules while transports evolve:

- historical recovery remains Memory-first / Evidence-final;
- current collection remains source-first / preserve-now;
- readable webpage capture, PDF `locator_verified → content_verified → materialized`, Drive/Release transport and runtime data-plane decisions do not change claim-scoped authority;
- current Agent tool friction is not itself a reason to redesign Longcycle semantics.

## Mutation rule

When a task authorizes only a report or other bounded mutation, make only that mutation on the resolved target branch. Do not use an acceptance/audit task as permission to repair product code, Baseline files, handoff, capability cards or tests.

A Fresh Agent has not completed bootstrap if it can repeat the mission but cannot identify the current Baseline, cannot distinguish L1–L4 from capability disposition, treats source-pack convenience as permission to rewrite historical methodology, creates parallel semantic owners for a new industry, or changes Baseline-critical test meaning to make its implementation pass.
