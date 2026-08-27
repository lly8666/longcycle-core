# AGENTS.md

## Fresh-session rule

Resume Longcycle through `FRESH_AGENT_BOOTSTRAP.md` / `CONTINUE_HERE.md`. Do not ask the user to restate persisted context.

Read in this order:

1. `STRATEGIC_COMPASS.md` — terminal mission;
2. `METHODOLOGY_CORE.md` — cross-industry method;
3. independently reconstruct mission/method in your own words;
4. `.longcycle/continuity/mission-fidelity.json` — calibration only;
5. `.longcycle/baseline/current.json` → referenced manifest + `ARCHITECTURE_BASELINE_V1.md` — frozen semantic contract;
6. `.longcycle/handoff/current.json` — current horizon/cursor;
7. `.longcycle/capabilities/active-index.json` and current admission — semantic-owner routing;
8. live Git HEAD / CI;
9. only the minimal task-specific resume set.

Do **not** preload old industries, all devlogs, old rehearsal reports or the full repository.

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

Read `docs/development/post-baseline-development.md` for the complete post-freeze workflow. The focused Architecture Baseline Gate prevents L1/L2 changes from redefining protected semantics merely to make new code pass.

## Mission assimilation before execution

Reading Core files is not enough. Before substantive work:

1. explain why Longcycle exists and what terminal capability it must deliver;
2. distinguish Reality from contemporaneous Judgment and later Outcome;
3. explain why point-in-time/no-lookahead matters;
4. explain why long comparable history can itself produce analysis;
5. explain model/search versus Evidence boundaries;
6. explain why the current industry/task is a proving ground or means rather than the mission;
7. only then use `mission-fidelity.json` to challenge omissions.

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

## Capability admission gate

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

## Vertical alignment loop

Before a substantive subproblem and after a coherent subtask, check:

```text
atomic task
↑ short-term milestone
↑ medium-term capability proof
↑ terminal mission
```

Stop/re-rank when the task has met its done condition, no longer advances the parent goal, or scope expands only because it is interesting/easy to measure. Baseline freeze is specifically intended to stop repeated open-ended architecture optimization after the semantic foundation has already met its proof burden.

## Stable ownership of information

- `STRATEGIC_COMPASS.md`: terminal mission / anti-drift direction.
- `METHODOLOGY_CORE.md`: adopted cross-industry research method.
- `.longcycle/continuity/mission-fidelity.json`: semantic calibration prompts, not answers.
- `.longcycle/baseline/current.json` + versioned manifest/document: frozen semantic contract and L1–L4 change rules.
- Capability Registry/cards: stable semantic owners and extension seams.
- `.longcycle/change-contract/current.json`: current change-risk classification, not semantic ownership.
- `.longcycle/handoff/current.json`: current horizon/cursor/workstreams/snapshot state.
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

1. commit substantive work;
2. run vertical alignment;
3. update current admission/change contract if classification/ownership changed;
4. update the handoff cursor/dynamic fields;
5. point `checkpoint_based_on_head_sha` to the final substantive/control-plane commit as defined by the handoff protocol;
6. commit handoff sync;
7. refresh live CI when correctness state is material;
8. reread the final live ref before returning control.

Do not create checkpoint churn for cosmetic edits. If live HEAD differs from checkpoint base, reconcile intervening commits before acting.

## Core promotion / Baseline evolution

A lesson begins in active context/devlog. It enters `METHODOLOGY_CORE.md` only after explicit adoption or enough cross-industry evidence. Once a method is covered by the current Architecture Baseline, changing its locked meaning is L3 rather than a silent Core edit.

Approved L3 evolution creates an explicit ADR and a new versioned Baseline manifest/tag. Do not rewrite `v1.0.0` or move its tag to make history cleaner.

## Fixed transfer phrase

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The phrase carries no current task facts. Repository state owns the task.
