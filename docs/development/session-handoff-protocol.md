# Longcycle Session Handoff Protocol v4

> Normative operating protocol. Design rationale, failure history and future evolution live in `docs/development/continuity-architecture.md`.

## 1. Goal

Longcycle may pass through many chat windows, Agents, model vintages and industries. Every new Agent must recover, without old chat history:

```text
terminal mission
+ cross-industry methodology
+ current medium-term goal
+ current short-term goal
+ current atomic continuation cursor
+ required Agent capability class
+ only the active context needed now
+ live implementation state
```

Old industry/devlog history is recoverable cold storage, not default memory.

## 2. Cold-start entry

The default branch root must contain `FRESH_AGENT_BOOTSTRAP.md`.

It resolves:

```text
default branch
→ issue #2 rendezvous
→ active PR / development branch
→ active branch CONTINUE_HERE.md
```

The pointer must not embed live industry, task, branch, campaign, count or CI facts.

## 3. State ownership

| Layer | Canonical owner | Purpose |
| --- | --- | --- |
| terminal mission | `STRATEGIC_COMPASS.md` | why Longcycle exists / terminal capability / anti-drift |
| cross-industry method | `METHODOLOGY_CORE.md` | adopted reusable operating method |
| mission calibration | `.longcycle/continuity/mission-fidelity.json` | semantic questions + common misreadings, never full answers |
| dynamic handoff | `.longcycle/handoff/current.json` | horizon, workstreams, capability requirement, cursor, live snapshot |
| active context | paths referenced by handoff | current benchmark/task details |
| history | Git + `docs/devlog/` | decisions, failures, old state, audits |

One information class has one normal owner.

## 4. Mission assimilation — think first, calibrate second

Fresh Agent sequence:

```text
read Strategy + Method Core
→ independently reconstruct mission/method in own words
→ only then read mission-fidelity.json
→ compare against required semantic facets / misreadings
→ targeted reread and repair if needed
```

A pass requires causal explanation, not keyword repetition.

Do not store private chain-of-thought. Persist only concise alignment conclusions or decisions when they materially affect project state.

## 5. Independent judgment and user-advice handling

User intent and user-proposed method are different authority classes.

- The user owns goals, preferences, constraints and risk tradeoffs.
- The Agent has a duty to make an independent technical/research judgment from the mission, evidence, live state and available capability.
- A user-proposed method is not automatically the best method.
- If a method is materially unsound, strategically weak, contradicted by evidence, or already beyond a stop condition, the Agent should explain why and refuse/narrow/rewrite it.
- This is not a license for reflexive contrarianism or claims that the model is generally superior to the user. Model status is not evidence.

The desired behavior is non-sycophantic, evidence-grounded and goal-respecting.

## 6. Capability-aware task entry

The continuation cursor declares one of two capability classes:

- `high_capability_reasoning` — independent synthesis, contradiction checking, strategic judgment, ambiguous tradeoffs or high-value conflict resolution;
- `bounded_execution` — explicit inputs, bounded source/task scope, clear stop condition and little freedom to redefine conclusions.

If the active task requires `high_capability_reasoning` and the current Agent cannot reliably perform that level of work, it must obey `insufficient_capability_action = stop_and_escalate`.

It must not imitate confidence and produce a surface-complete result.

This is also the reserved future entry point for lower-cost Agent orchestration. No full dispatcher is implied by the current protocol.

## 7. Fresh-session algorithm

```text
1. default root → FRESH_AGENT_BOOTSTRAP.md
2. issue #2 → active PR / branch
3. switch reads to active branch
4. read STRATEGIC_COMPASS.md + METHODOLOGY_CORE.md
5. produce first-pass mission/method reconstruction
6. calibrate with .longcycle/continuity/mission-fidelity.json
7. read current.json strategic horizon + continuation cursor
8. check required capability / escalate if insufficient
9. refresh live HEAD / commit delta / CI
10. load only minimal resume_read_set / active context needed by cursor
11. run Vertical Alignment Gate
12. execute current/next atomic action
```

`resume_read_set` remains bounded at 8 files or fewer.

## 8. Vertical Alignment Gate

Run before a new substantive subproblem and after every coherent subtask.

A simple main-path task follows:

```text
atomic task
↑ main-path workstream
↑ short-term milestone
↑ medium-term capability proof
↑ terminal mission
```

Not every legitimate task is main-path work. A task may be a temporary `supporting_quality_gate` or a permanent `parallel_track`. Therefore each workstream also declares:

- `role`: `main_path`, `supporting_quality_gate` or `parallel_track`;
- `parent_goal_ref`: the strategic horizon goal it serves.

This prevents a support task from silently redefining the current product milestone merely because it is the active cursor.

Then ask:

1. Is this still a high-value action relative to the workstream's declared role and parent goal?
2. Is `done_when` already satisfied?
3. Is local scope growing only because the problem is interesting/easy to optimize?
4. Did new evidence change or obsolete the parent task?
5. Would stopping now materially reduce parent-level progress?
6. If this is a support workstream, has the quality/blocker condition already been cleared so the Agent should return to `main_path`?

If the task cannot be connected upward or marginal value has collapsed, stop/re-rank instead of deepening automatically.

## 9. Continuation cursor and workstream contract

`current.json.continuation_cursor` must contain:

- `parent_workstream_id`;
- `last_completed_action`;
- `current_task`;
- `why_now`;
- `done_when`;
- `required_capability`;
- `insufficient_capability_action`;
- `next_atomic_action`.

Every active workstream must declare its `role` and `parent_goal_ref`; at least one `main_path` workstream must exist.

The cursor is not a devlog. It answers only:

```text
what just finished?
what should resume now?
why is it current?
what capability does it require?
what happens if this Agent is not capable enough?
what role does its workstream play?
which parent goal does that workstream serve?
what ends it?
what comes immediately after?
```

## 10. Real-time micro-checkpoint lifecycle

After a coherent task boundary that changes what the next Agent should do:

```text
1. commit substantive work
2. run Vertical Alignment Gate
3. update continuation cursor and materially changed dynamic fields
4. set checkpoint_based_on_head_sha = substantive-work commit SHA
5. commit handoff sync
6. refresh live CI when correctness is material
```

Do not checkpoint cosmetic edits that do not change continuation.

If a session ends before sync, live HEAD will differ from checkpoint base; the next Agent must reconcile intervening commits before acting.

## 11. Canonical fixed transfer phrase

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The phrase must remain task-free. Repository state owns the current task.

## 12. Core growth rule

Core files have CI ceilings but ceilings are not brevity targets.

Failure extremes:

```text
overcompression → slogans survive, causal mission disappears
overgrowth      → startup becomes project archaeology
```

Current target: high semantic fidelity + bounded growth + minimum sufficient context.

Specific industry facts never enter long-term Core. Reusable lessons enter Method Core only after explicit user adoption or sufficient cross-benchmark evidence.

## 13. Authority planes

Strategic authority:

```text
new explicit user goal / constraint / decision
> Strategy Core
> Method Core
> dynamic strategic horizon
> deep historical narrative
```

A user suggestion about implementation method is still subject to independent technical judgment; it is not the same thing as a user-owned goal or constraint.

Implementation freshness:

```text
live Git graph / HEAD / CI
> canonical / deterministic-derived artifacts
> checkpoint snapshot
> narrative
```

New code cannot silently redefine mission. Old checkpoint state cannot outrank live Git.

## 14. Protocol evolution

Material continuity changes require:

1. observed failure/adversarial case;
2. identified violated invariant;
3. smallest-owner repair;
4. schema version bump when semantics change;
5. repository-only regression test;
6. artificial-ignorance drill;
7. genuine fresh-Agent report-only audit when useful;
8. concise devlog of failure and remediation;
9. return to product main path when continuity is safe.

Continuity is infrastructure, not the product roadmap.

## 15. Repository-only checks

CI should verify at minimum:

- Core byte/line bounds;
- active-context exclusion from long-term cores;
- mission semantic contract exists and contains no current-industry data;
- bootstrap order requires first-pass synthesis before semantic calibration;
- typed strategic horizon and continuation cursor are complete;
- current cursor declares capability requirement and stop/escalate behavior;
- workstream roles and parent-goal references are valid, with at least one main path;
- resume set is bounded;
- campaign/context paths derive from active context rather than a hard-coded industry;
- raw/canonical campaign state agrees with checkpoint where applicable;
- stale checkpoint scenarios are detected.

## 16. External fresh-Agent audit

A true external audit starts from repository name or the fixed transfer phrase only. The Agent must independently discover active state, reconstruct mission/method, calibrate itself, recover the continuation cursor, evaluate its own capability for the cursor, and report-only audit the mechanism without repairing it unless explicitly authorized.

Not remembering irrelevant old industry details is a success.

A report that resolves paths correctly but merely repeats repository instructions without independent judgment is not sufficient evidence that a high-capability transfer succeeded.
