# Longcycle — Fresh Agent Bootstrap

This file is a stable zero-context rendezvous pointer, not live project state.

## Canonical transfer phrase

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、宏大/长期/中期/短期/当前目标和 live 状态，从 continuation cursor 继续；先做战略层级和防钻牛角尖校准，不要让我重复背景。**

## Post-Baseline cold start

Rule: do not assume the default `main` branch is the active development state. Resolve GitHub issue **#2** first as the stable rendezvous for the active PR / development branch and live handoff; when no temporary active branch is declared there, continue from live `main`.

Stable rendezvous remains GitHub issue #2, **Longcycle Live Handoff / Session Bootstrap**. From that rendezvous, follow `CONTINUE_HERE.md` and the handoff's **typed continuation cursor** rather than reconstructing current work from chat or historical reports.

1. Refresh live `main`/active-PR HEAD and CI; snapshots in handoff are never live authority.
2. Read `STRATEGIC_COMPASS.md` and `METHODOLOGY_CORE.md`, reconstruct mission/method in your own words, then use `.longcycle/continuity/mission-fidelity.json` only to challenge omissions/misreadings.
3. Before interpreting the TODO, explicitly reconstruct the goal hierarchy:
   - **macro / terminal mission** — the durable cross-industry user capability;
   - **long-term product direction** — the enduring system capability that makes that mission scalable;
   - **medium-term goal** — from `handoff.strategic_horizon.medium_term_goal`;
   - **short-term milestone** — from `handoff.strategic_horizon.short_term_goal`;
   - **atomic current task** — from `continuation_cursor.current_task` / `next_atomic_action`.
   Be able to explain how the atomic task advances every parent level.
4. Read `.longcycle/baseline/current.json`, then its referenced manifest and `ARCHITECTURE_BASELINE_V1.md`. Treat the locked invariants as the default definition of semantic correctness; Baseline does not replace Strategy or Method Core.
5. Read `.longcycle/handoff/current.json` for the current horizon/cursor and `.longcycle/capabilities/active-index.json` for stable semantic ownership. Reconcile `checkpoint_based_on_head_sha` with the live ref before acting.
6. **before material capability/product/architecture work, discover the existing semantic owner** through the Capability Registry; write/update `.longcycle/change-contract/current.json` with `L1/L2/L3/L4`, then run current admission separately as `reuse / extend / replace / new`. Exact admission target IDs are authority; fuzzy capability search is discovery help only. Load every exact target card and its entrypoints/guards before implementation.
7. Default to L1/L2 + reuse/extend. A new industry is normally a Domain Pack/catalog/source/research extension, not a new Fact/Evidence/PIT architecture.
8. If the proposed change touches a locked Baseline invariant or changes the semantic expectation of a Baseline-critical regression, stop ordinary implementation and enter the L3 architecture-change procedure. `Cleaner`, `more generic` and `future-proof` are not sufficient evidence.
9. If a real source-grounded important case cannot be truthfully expressed through existing extension seams, preserve that counterexample and escalate it; Baseline v1 is stable by default, not dogmatically immune to evidence.
10. Query path-scoped Repair Memory before editing known paths. Do not infer that a new path has no semantic constraints merely because no repair card matches it.
11. If a fuzzy cue suggests “we discussed/designed this before”, do **not** preload project history. Do **not** preload old devlogs/issues/benchmarks. Use `docs/development/on-demand-history-recall.md`: semantic owner → relevant Repair Memory → exact origin refs → bounded Git/Issue/receipt/devlog history → return to live authority.
12. Run the Vertical Alignment Loop before a substantive subproblem, after a coherent subtask, before scope expansion, or when new evidence changes an assumption:

```text
atomic task
↑ short-term milestone
↑ medium-term capability proof
↑ long-term product direction
↑ terminal mission
```

Stop/re-rank if `done_when` is already met, parent-level value has collapsed, the work is only polishing an easy metric, or architecture is expanding because it is interesting rather than falsified by reality.
13. Read only the minimal task-specific resume set. Do not preload old industries, old devlogs, old rehearsal reports or the full repository.

Detailed operational/source acquisition rules remain in `CONTINUE_HERE.md`; post-Baseline development rules live in `docs/development/post-baseline-development.md`.

For a **whole-project review or deliberate architecture change**, additionally read `docs/development/longcycle-development-operating-system.md`. Normal implementation agents should not load that full review manual unless the task actually requires broad audit/architecture reasoning.

## Authority by question

- terminal mission: `STRATEGIC_COMPASS.md`
- cross-industry research method: `METHODOLOGY_CORE.md`
- frozen semantic contract/change levels: `.longcycle/baseline/current.json` → manifest + `ARCHITECTURE_BASELINE_V1.md`
- complete review/architecture-change operating discipline: `docs/development/longcycle-development-operating-system.md`
- semantic owner/extension seam: Capability Registry/cards
- anti-regression invariant: Repair Memory
- current work and hierarchy: live Git + `.longcycle/handoff/current.json` + current admission/change contract
- actual implementation: migrations/code/tests/live CI
- historical rationale: Git/devlogs/receipts, routed through `docs/development/on-demand-history-recall.md`

## Independent judgment

The user owns goals, preferences, constraints and risk tradeoffs. The Agent still owes independent technical/research judgment. A user-proposed method is not automatically the correct method. Compare it against mission, Baseline, Evidence/PIT boundaries, live state, cost/benefit, stop conditions and better alternatives. If materially unsound, explain the key issue and narrow/rewrite/refuse it rather than optimizing for obedience.

If a task requires high-capability synthesis and the current Agent cannot reliably perform it, stop/escalate rather than imitate confidence.

## Source/data-plane reminder

Do not confuse Baseline freeze with frozen acquisition implementation. Preserve the existing epistemic rules while transports evolve:

- historical recovery remains Memory-first / Evidence-final;
- current collection remains source-first / preserve-now;
- readable webpage capture, PDF `locator_verified → content_verified → materialized`, Drive/Release transport and runtime data-plane decisions do not change claim-scoped authority;
- current Agent tool friction is not itself a reason to redesign Longcycle semantics.

## Mutation rule

When a task authorizes only one report or other bounded mutation, write it to the **resolved active development branch** unless the task explicitly names another target; make no other mutation. Do not use an acceptance/audit task as permission to repair product code, Baseline files, handoff, capability cards or tests.

A Fresh Agent has not completed bootstrap if it can repeat the mission but cannot reconstruct the five-level goal hierarchy, cannot connect the current atomic task to its parents, cannot identify the current Baseline, cannot distinguish L1–L4 from capability disposition, cannot explain the Vertical Alignment Loop, treats source-pack convenience as permission to rewrite historical methodology, bulk-loads history instead of using on-demand recall, creates parallel semantic owners for a new industry, or changes Baseline-critical test meaning to make its implementation pass.
