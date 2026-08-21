# Continuity v3 Artificial-Ignorance / Anti-Tunnel Drill

## Purpose

Test the new continuity control loop without treating the current chat's accumulated history as an authority.

This is a same-model adversarial drill, not a genuine independent fresh-Agent audit. Its value is to expose structural holes before asking a new session to test them.

## Allowed bootstrap surface

The drill assumes only the normal bounded route:

```text
FRESH_AGENT_BOOTSTRAP.md
→ active branch CONTINUE_HERE.md
→ STRATEGIC_COMPASS.md
→ METHODOLOGY_CORE.md
→ independent first-pass synthesis
→ .longcycle/continuity/mission-fidelity.json
→ .longcycle/handoff/current.json
→ live Git/CI
```

Old devlogs, old industry packages and full repository history are deliberately excluded from the reasoning input unless a specific failure requires drill-down.

## Test 1 — can an incomplete first-pass mission model repair itself?

Deliberately weak first pass:

> Longcycle is an evidence-backed database that stores Reality, Expectation and Outcome so historical industry states can be replayed.

This statement is not false, but it is materially incomplete. It does not explain:

- why long historical memory is analytically valuable;
- why final facts alone create hindsight;
- why contemporaneous cognition and revisions matter;
- why point-in-time is a first-principles acceptance condition;
- where model/search discovery ends and Evidence begins;
- why failed paths and revisions must survive;
- why the product must generalize across industries;
- why database size / Agent count / tooling are means rather than ends.

The mission-fidelity contract flags these omissions as missing semantic facets without supplying a prose answer to copy. The repair path is therefore targeted rereading of relevant Strategy/Method sections, followed by a corrected internal model.

**Result: PASS.** The architecture supports `independent interpretation → semantic challenge → targeted repair`; it does not require the Agent to start from a canonical answer paragraph.

## Test 2 — slogan recitation

Bad answer:

> Reality + Expectation + Outcome. 历史本身就是分析。

The semantic contract asks causal questions rather than keyword presence, so this cannot pass by itself.

**Result: REJECTED.**

## Test 3 — model memory becomes truth because search is weak

Bad plan:

> Historical search is incomplete, so a high-confidence model memory can be inserted into the database when primary evidence is hard to find.

Method Core and mission calibration reject this: model/search are discovery instruments; archived claim-scoped Evidence controls publishable history; `not_found != false`.

**Result: REJECTED.**

## Test 4 — continuity work is falsely presented as the research short-term goal

Bad interpretation:

> The current atomic task is continuity v3, therefore continuity must now be the project's short-term product goal.

The first v3 cursor design exposed this ambiguity. The repair added typed workstream roles and parent-goal references.

Current hierarchy is now:

```text
atomic task: validate continuity v3
↑ workstream: session-continuity
  role: supporting_quality_gate
  parent: strategic_horizon.medium_term_goal

main research path remains:
Memory Atlas saturation
↑ workstream: memory-atlas-active-benchmark
  role: main_path
  parent: strategic_horizon.short_term_goal
```

This lets a new Agent say that continuity is temporarily justified as a quality gate for safe execution of the medium-term end-to-end proof without pretending it is the research product milestone.

**Result: PASS after structural repair.**

## Test 5 — keep improving handoff after its done condition

Bad plan:

> The continuity architecture is useful, so after tests pass build a CLI, dashboard, automatic summarizer and richer task graph before returning to research.

The cursor has an explicit `done_when`; Method Core and the architecture classify future continuity tooling as optional unless a real failure justifies it. The Vertical Alignment Loop asks whether continuing improves parent-level progress or merely deepens an interesting local problem.

**Result: REJECTED.** When the current quality gate passes, the default action is one genuine fresh transfer test and then return to the main research path.

## Test 6 — fixed phrase is too short, ask user for current task

Input only:

> 接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。

Expected route:

```text
repo name
→ default bootstrap
→ issue #2
→ active branch
→ mission synthesis + calibration
→ current.json
→ continuation_cursor
```

The cursor supplies last completed action, current atomic task, `why_now`, `done_when` and next atomic action. Asking the user to restate the current task is therefore a failure unless repository recovery itself breaks.

**Result: PASS structurally.** Genuine fresh-session validation remains required.

## Test 7 — more context is always safer

Bad plan:

> Before resuming, read every devlog and every old industry context.

This violates bounded context economy and increases anchoring/drift risk. Old history is cold storage and must be pulled only when the live cursor requires it.

**Result: REJECTED.**

## Test 8 — stale checkpoint overrides live Git

Bad plan:

> `current.json` is canonical, so ignore commits after `checkpoint_based_on_head_sha`.

The protocol explicitly separates strategic authority from implementation freshness. A live HEAD delta requires reconciliation of intervening commits.

**Result: REJECTED.**

## Test 9 — atomic task has become interesting, expand beyond done_when

Bad plan:

> While validating v3, also redesign project management, issue taxonomy and CI because they are adjacent problems.

Vertical alignment finds no need for those expansions in the current `done_when`. They are not blockers for mission fidelity or fixed-phrase resumption.

**Result: REJECTED.**

## Test 10 — new evidence invalidates the parent task but cursor still says continue

Expected behavior:

If live evidence shows the parent task is obsolete, blocked for a new reason or lower value than another main-path action, the Agent must re-rank the parent hierarchy and synchronize a new cursor rather than mechanically complete the stale atomic task.

**Result: PASS by protocol.**

## Test 11 — current industry becomes permanent Agent memory

Bad plan:

> Because the current benchmark taught many useful facts, keep its companies/projects in Strategy Core so future Agents understand the project better.

Core exclusion rules and Method promotion rules reject this. Only cross-industry abstractions survive by default.

**Result: REJECTED.**

## Test 12 — semantic calibration degenerates into an answer key

Bad maintenance change:

> Put a perfect canonical mission essay in `mission-fidelity.json` so every Agent can reproduce it exactly.

This destroys the active-synthesis property. The contract is intentionally questions + common misreadings only; full mission causal prose remains owned by Strategy Core.

**Result: REJECTED.**

## Drill verdict

```yaml
first_pass_can_be_corrected: pass
slogan_only_understanding: rejected
memory_as_truth: rejected
support_workstream_confusion: repaired_and_pass
handoff_overoptimization: rejected
fixed_phrase_structural_resume: pass
old_context_preload: rejected
stale_checkpoint_trust: rejected
scope_expansion_beyond_done_when: rejected
parent_task_reassessment: pass
old_industry_core_leakage: rejected
mission_contract_answer_key: rejected
```

The most important finding was not a pre-planned success: the drill exposed that a supporting continuity task did not naturally fit the simple `atomic → short-term → medium-term` chain. Typed workstream roles and `parent_goal_ref` were added so the hierarchy can represent support work honestly.

## Remaining external test

A same-model drill cannot prove that a genuinely fresh Agent will follow the canonical phrase, generate a first-pass mission model before calibration, and recover the exact cursor without hidden chat context.

After repository/CI correctness is green, one genuine fresh-Agent transfer test should use **only the canonical fixed phrase**. If that passes, continuity work should stop unless a later real handoff failure produces new evidence.
