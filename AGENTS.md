# AGENTS.md

## Fresh-session rule

Resume Longcycle through `CONTINUE_HERE.md`. Do not ask the user to restate persisted context.

Read in this order:

1. `STRATEGIC_COMPASS.md` — long-term mission;
2. `METHODOLOGY_CORE.md` — cross-industry method;
3. independently reconstruct the mission/method in your own words;
4. `.longcycle/continuity/mission-fidelity.json` — semantic calibration questions and common misreadings;
5. `.longcycle/handoff/current.json` — current medium/short horizon, continuation cursor and active context;
6. live Git HEAD / CI;
7. only the minimal task-specific `resume_read_set`.

Do **not** preload old industries, all devlogs or the full repository.

## Mission assimilation before execution

Reading Core files is not enough. Before substantive work:

1. form an independent internal explanation of why Longcycle exists and what terminal capability it must deliver;
2. distinguish final facts from contemporaneous cognition, and explain why point-in-time/no-lookahead matters;
3. explain why long comparable history can itself produce analysis;
4. explain the model/search versus Evidence boundary;
5. explain why the current industry/task is a proving ground or means rather than the mission;
6. only then use `mission-fidelity.json` to challenge that interpretation.

If any required facet is missing or contradicted, reread only the relevant Core section and correct the interpretation before acting.

Do not persist private chain-of-thought. Persist only concise decisions, alignment conclusions, task hierarchy and reproducible constraints when project state materially changes.

## Independent judgment — do not confuse user intent with method truth

The user owns goals, preferences, constraints and risk tradeoffs. The Agent still owns the duty to make the strongest technical/research recommendation it can from available evidence and capability.

Do not automatically execute a user-proposed method merely because the user proposed it. First compare it against the mission, evidence boundaries, live state, cost/benefit, stop conditions and better alternatives. If it is materially unsound or locally optimal but strategically weak, say so concisely, refuse/narrow/rewrite the method, and recommend a better path.

Do not use model status as authority. The standard is calibrated reasoning, evidence and task performance. If a task requires independent high-level synthesis and the current Agent cannot reliably provide it, stop and escalate rather than imitate confidence.

Current task capability requirements come from the continuation cursor. `high_capability_reasoning` tasks require independent synthesis, adversarial checking and strategic judgment. `bounded_execution` tasks are suitable for lower-capability Agents operating under explicit inputs, source targets and stop conditions.

## Repair Memory gate — do not rediscover old regressions blindly

Before a substantive edit whose target paths are known, query the bounded Repair Memory for those paths:

```bash
python scripts/repair_memory.py relevant <path> [<path> ...]
```

If investigating a bug before its owning path is known, query a few symptom/root-cause terms:

```bash
python scripts/repair_memory.py query "evidence provenance"
```

Read only matching cards under `.longcycle/repair-memory/invariants/`. They explain non-obvious repairs that future cleanups must not accidentally reverse and point to the executable/schema/type guards that enforce them.

Do not preload every repair card. Do not create a card for every bug. Promotion, size limits, lifecycle and deduplication rules live in `docs/development/repair-memory.md`. A repeated repair updates the existing invariant when it has the same root cause; chronological history belongs to Git, not to growing card prose.

If an invariant must change because the architecture genuinely changed, do so deliberately: satisfy its `revisit_when`, update/supersede the card and its guards in the same coherent change. Repair Memory is an anti-accident mechanism, not a ban on better architecture.

## Vertical alignment loop — anti-tunnel rule

Before starting a new substantive subproblem and after completing every coherent subtask, internally restate this parent chain:

```text
atomic task
↑ short-term milestone
↑ medium-term capability proof
↑ terminal mission
```

Then check:

- is the atomic task still the highest-value unresolved action on the main path?
- has its `done_when` or stop condition already been met?
- is scope expanding only because the local problem is interesting or easy to measure?
- did a new result change the parent task or make the current task obsolete?
- would stopping now materially harm parent-level progress?

A local task that cannot be connected through those levels, or whose marginal value has collapsed, should be stopped/re-ranked instead of deepened automatically.

## Stable ownership of information

- `STRATEGIC_COMPASS.md` owns mission and anti-drift direction.
- `METHODOLOGY_CORE.md` owns distilled cross-industry methods.
- `.longcycle/continuity/mission-fidelity.json` owns semantic calibration prompts, not answers.
- `.longcycle/handoff/current.json` owns current horizon, continuation cursor, workstreams and snapshot state.
- active context owns current industry / benchmark details.
- live Git/CI owns implementation freshness.
- devlogs own historical rationale only.

Never copy fast-changing industry facts into a long-term core. Never copy stable mission/methodology into every checkpoint.

## Core promotion rule

A lesson begins in the current context or devlog. It enters `METHODOLOGY_CORE.md` only after explicit user adoption or enough benchmark evidence that it should survive industry changes.

When adding to a Core, compress/replace existing wording rather than appending indefinitely.

## Epistemic boundaries

Follow `METHODOLOGY_CORE.md`: model memory is not Evidence; historical `not_found != false`; no-lookahead replay; claim-scoped authority; original versions and revisions are not overwritten; comparability comes before corroboration.

Current phase-specific guardrails come from the typed handoff and active context, not this file.

## Real-time continuity maintenance

`current.json.continuation_cursor` must tell a fresh Agent what just finished, what atomic task resumes now, why it is current, what `done_when` means, what capability class it requires, what to do if capability is insufficient, and what comes next.

After a coherent work boundary that changes what the next Agent should do:

1. commit the substantive work;
2. run the vertical alignment loop;
3. update the continuation cursor and any materially changed dynamic handoff fields;
4. set `checkpoint_based_on_head_sha` to the substantive-work commit;
5. commit the handoff sync;
6. refresh live CI when correctness state is material.

Do not create checkpoint churn for cosmetic edits that do not change continuation.

If a new user instruction changes mission or methodology, first record it as a pending directive, then update the appropriate Core with auditable rationale. Do not silently redefine strategy from a local implementation preference.

If live HEAD differs from the checkpoint base, reconcile intervening commits before acting; do not assume the snapshot is current.

## Fixed transfer phrase

A zero-context Agent should be able to resume from this single stable user phrase:

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The phrase carries no current task facts. Repository state owns the task.
