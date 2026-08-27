# AGENTS.md

## Fresh-session rule

Resume Longcycle through `FRESH_AGENT_BOOTSTRAP.md` / `CONTINUE_HERE.md`. Do not ask the user to restate persisted context.

Read in this order:

1. `STRATEGIC_COMPASS.md` — terminal mission and long-term product direction;
2. `METHODOLOGY_CORE.md` — cross-industry method;
3. independently reconstruct mission/method in your own words;
4. `.longcycle/continuity/mission-fidelity.json` — calibration only;
5. `.longcycle/baseline/current.json` → referenced manifest + `ARCHITECTURE_BASELINE_V1.md` — frozen semantic contract;
6. `.longcycle/handoff/current.json` — current medium/short horizon and atomic cursor;
7. `.longcycle/capabilities/active-index.json` and current admission — semantic-owner routing;
8. live Git HEAD / CI;
9. only the minimal task-specific resume set.

Do **not** preload old industries, all devlogs, old rehearsal reports or the full repository.

For a whole-project audit, architecture review, or deliberate L3 change, additionally read `docs/development/longcycle-development-operating-system.md`. Normal L1/L2 agents should not preload that full reviewer manual.

## Five-level strategic hierarchy — mandatory before execution

A Fresh Agent must recover and be able to explain:

```text
macro / terminal mission
↓
long-term product direction
↓
medium-term goal
↓
short-term milestone
↓
atomic current task
```

Authority is split intentionally:

- terminal mission + long-term direction: `STRATEGIC_COMPASS.md`;
- medium + short horizon: `.longcycle/handoff/current.json -> strategic_horizon`;
- atomic task / why-now / done-when / next action: `continuation_cursor`.

Before substantive work, explain how the atomic task advances every parent level. If the Agent can repeat the slogan but cannot reconstruct this causal chain, bootstrap is incomplete.

## Architecture Baseline gate — classify before coding

Architecture exploration is closed by default. Before material product/capability/domain work, write or update `.longcycle/change-contract/current.json` and classify the change:

```text
L1 implementation
L2 product/domain extension
L3 Architecture Baseline change
L4 terminal mission change
```

This is orthogonal to the existing Capability Registry disposition:

```text
reuse | extend | replace | new
```

Default to **L1/L2 + reuse/extend**. A new industry, source, metric, predicate, unit, API or Domain Pack does not by itself justify a new Fact/Evidence/PIT architecture.

If a requested behavior changes a locked Baseline invariant or the semantic expectation of a Baseline-critical regression, ordinary implementation stops. L3 requires a real important source-grounded counterexample that the current Baseline cannot truthfully express through existing extension seams, or a demonstrated security/consistency defect, plus an ADR/Architecture Change Proposal covering compatibility, migration, PIT/no-lookahead, provenance and counterexample tests. `Cleaner`, `more generic`, `less code`, `future-proof` and framework preference are not L3 evidence.

L4 requires an explicit user decision before implementation.

Read `docs/development/post-baseline-development.md` for the post-freeze workflow. The focused Architecture Baseline Gate prevents L1/L2 changes from redefining protected semantics merely to make new code pass.

## Mission assimilation before execution

Reading Core files is not enough. Before substantive work:

1. explain why Longcycle exists and what terminal capability it must deliver;
2. distinguish Reality from contemporaneous Judgment and later Outcome;
3. explain why point-in-time/no-lookahead matters;
4. explain why long comparable history can itself produce analysis;
5. explain model/search versus Evidence boundaries;
6. explain why the current industry/task is a proving ground or means rather than the mission;
7. reconstruct the five-level strategic hierarchy above;
8. only then use `mission-fidelity.json` to challenge omissions.

Do not persist private chain-of-thought. Persist concise decisions, task hierarchy, reproducible constraints and auditable rationale when project state materially changes.

## Independent judgment

The user owns goals, preferences, constraints and risk tradeoffs. The Agent still owes independent technical/research judgment. Do not execute a suggested method merely because it was suggested; compare it with mission, Baseline, evidence boundaries, live state, stop conditions, cost/benefit and better alternatives.

Do not use model status as authority. If the continuation cursor requires `high_capability_reasoning` and the current Agent cannot reliably synthesize/adversarially check the work, stop and escalate rather than imitate confidence. `bounded_execution` is appropriate only under explicit inputs and stop conditions.

## Repair Memory gate

Before substantive edits to known paths:

```bash
python scripts/repair_memory.py relevant <path> [<path> ...]
```

For an unresolved bug with unknown owner, use bounded symptom/root-cause queries. Read only matching cards. Repair Memory protects non-obvious high-recurrence invariants; Git owns chronology; the Baseline owns frozen semantic correctness.

A missing path-scoped repair hit is not permission to invent new semantics. If a Repair Memory invariant itself must change because an approved L3 architecture change supersedes it, update/supersede the card and guards deliberately in the same coherent change.

## On-demand history recall

If a cue suggests an old design decision matters, follow `docs/development/on-demand-history-recall.md` instead of bulk-loading project history:

```text
current semantic owner
→ relevant Repair Memory
→ exact origin refs
→ bounded Git / Issue / receipt / devlog history
→ return to live authority
```

Historical summaries route; original Git/receipts remain authority.

## Capability admission gate — do not create parallel semantic owners blindly

Before material capability/product/architecture work:

```bash
python scripts/capability_registry.py relevant "<researcher/system need>"
```

Read exact matching owner cards and classify `.longcycle/capabilities/current-admission.json` as `reuse`, `extend`, `replace`, or `new`. Default to reuse/extend. `new` means genuinely new semantic ownership and requires a truthful unmet requirement that current extension seams cannot satisfy; a new file/UI/CLI/API/adapter does not imply new ownership.

After a material stable capability change, update the owning card only if its responsibility/entrypoints/extension seams/guards/maturity changed, then run:

```bash
python scripts/capability_registry.py rebuild-index
python scripts/capability_registry.py audit
```

Do not build a second semantic-owner registry inside Change Contract/Baseline governance.

## Baseline-critical tests

L1/L2 may mechanically update protected tests when imports/fixtures/API shapes move, but may not change what they define as semantically correct. If an implementation only passes by changing the expected meaning of Evidence grounding, Reality/Judgment/Outcome separation, no-lookahead, temporal precision, provenance/revision, source authority/representation or semantic-owner uniqueness, classify as L3 before touching both implementation and expectation.

Agents do not get to change both the question and the answer under an L1/L2 label.

## Vertical Alignment Loop — permanent anti-tunnel rule

Run it before a substantive subproblem, after every coherent subtask, before scope expansion, when a new result changes assumptions, or when a local problem becomes unusually absorbing.

```text
atomic task
↑ short-term milestone
↑ medium-term capability proof
↑ long-term product direction
↑ terminal mission
```

Ask whether `done_when` is already met, whether additional work changes the parent result or only polishes a local metric, whether new evidence changed priorities, whether the work is deepening only because it is interesting/easy to measure, and whether stopping now would materially harm the parent goal.

Stop/re-rank when parent-level marginal value has collapsed. A real local problem does not automatically deserve unlimited depth.

## Stable ownership of information

- `STRATEGIC_COMPASS.md`: terminal mission / long-term direction / anti-drift.
- `METHODOLOGY_CORE.md`: adopted cross-industry research/development method.
- `.longcycle/continuity/mission-fidelity.json`: semantic calibration prompts, not answers.
- `.longcycle/baseline/current.json` + versioned manifest/document: frozen semantic contract and L1–L4 change rules.
- `docs/development/longcycle-development-operating-system.md`: integrated reviewer/architecture-change operating manual, not a replacement authority.
- Capability Registry/cards: stable semantic owners and extension seams.
- `.longcycle/change-contract/current.json`: current change-risk classification, not semantic ownership.
- `.longcycle/handoff/current.json`: current medium/short horizon, cursor, workstreams and snapshot state.
- Repair Memory: high-recurrence anti-regression invariants.
- live migrations/code/tests/CI: actual implementation state.
- active context: current industry/benchmark details.
- old devlogs/research/rehearsals/PR discussions: immutable historical rationale/provenance, read on demand.

There is no single document ranking for every question; use the owner for the question.

## Epistemic boundaries

Follow `METHODOLOGY_CORE.md` and Architecture Baseline v1: historical recovery remains Memory-first/Evidence-final; model memory/search are not Evidence; `not_found != false`; no-lookahead; claim-scoped authority; temporal precision fidelity; original Judgments/versions are preserved; source representation/materialization states remain truthful.

Current source/data-plane mechanics may evolve under L1/L2 without changing these semantics.

## Continuity maintenance

`current.json.continuation_cursor` must tell a Fresh Agent what just finished, what resumes now, why, what `done_when` means, required capability, insufficient-capability action and what follows.

After a coherent boundary that changes continuation:

1. finish coherent substantive/control-plane work;
2. run Vertical Alignment Loop;
3. update current admission/change contract if classification/ownership changed;
4. update capability/Repair Memory only when stable ownership/invariant changed;
5. run focused validation and required CI;
6. commit substantive work;
7. update handoff cursor/dynamic fields against the actual completed work;
8. commit handoff sync;
9. refresh exact live HEAD / PR / CI;
10. reread the final live ref and handoff before returning control.

Do not create checkpoint churn for cosmetic edits. If live HEAD differs from checkpoint base, reconcile intervening commits before acting. Parent green is not exact-head green.

## Core promotion / Baseline evolution

A lesson begins in active context/devlog. It enters `METHODOLOGY_CORE.md` only after explicit adoption or enough cross-industry evidence. Once a method is covered by the current Architecture Baseline, changing its locked meaning is L3 rather than a silent Core edit.

Approved L3 evolution creates an explicit ADR and a new versioned Baseline manifest/tag. Do not rewrite `v1.0.0` or move its tag to make history cleaner.

## Fixed transfer phrases

Normal takeover:

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、宏大/长期/中期/短期/当前目标和 live 状态，从 continuation cursor 继续；先做战略层级和防钻牛角尖校准，不要让我重复背景。**

Whole-project / architecture review:

> **审查 Longcycle（lly8666/longcycle-core）：按仓库 live state 完整恢复使命、方法、Architecture Baseline 和 Longcycle Development Operating System；从宏大目标→长期产品方向→中期目标→短期里程碑→当前实现逐层审查。区分 L1/L2、L3、L4、research/data、continuity/governance 与 production-readiness；只有真实重要反例证明 Baseline 无法诚实表达时才提出 L3。**

Deliberate architecture change:

> **准备修改 Longcycle 部分架构：先按仓库 live state 和 `docs/development/longcycle-development-operating-system.md` 完整恢复项目，不直接改代码。先证明这是 L3 而不是 L1/L2：给出真实 source-grounded counterexample 或 security/consistency defect、受影响 BL invariant、现有 owner extension seam 为什么不够，以及 old-data / migration / PIT-no-lookahead / provenance / regression consequences。证据不足就不要改 Baseline。**

The phrases carry no current task facts. Repository state owns the task.
