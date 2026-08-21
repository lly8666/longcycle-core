# Longcycle Session Handoff Protocol v3

> Normative operating protocol. Design rationale, failure history and future evolution live in `docs/development/continuity-architecture.md`.

## 1. Goal

Longcycle may pass through many chat windows, Agents, model vintages and industries. Every new Agent must recover, without old chat history:

```text
terminal mission
+ cross-industry methodology
+ current medium-term goal
+ current short-term goal
+ current atomic continuation cursor
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
| dynamic handoff | `.longcycle/handoff/current.json` | medium/short horizon, continuation cursor, workstreams, live snapshot |
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

## 5. Fresh-session algorithm

```text
1. default root → FRESH_AGENT_BOOTSTRAP.md
2. issue #2 → active PR / branch
3. switch reads to active branch
4. read STRATEGIC_COMPASS.md + METHODOLOGY_CORE.md
5. produce first-pass mission/method reconstruction
6. calibrate with .longcycle/continuity/mission-fidelity.json
7. read current.json strategic horizon + continuation cursor
8. refresh live HEAD / commit delta / CI
9. load only minimal resume_read_set / active context needed by cursor
10. run Vertical Alignment Gate
11. execute current/next atomic action
```

`resume_read_set` remains bounded at 8 files or fewer.

## 6. Vertical Alignment Gate

Run before a new substantive subproblem and after every coherent subtask:

```text
atomic task
↑ short-term milestone
↑ medium-term capability proof
↑ terminal mission
```

Then ask:

1. Is this still a high-value main-path action?
2. Is `done_when` already satisfied?
3. Is local scope growing only because the problem is interesting/easy to optimize?
4. Did new evidence change or obsolete the parent task?
5. Would stopping now materially reduce parent-level progress?

If the task cannot be connected upward or marginal value has collapsed, stop/re-rank instead of deepening automatically.

## 7. Continuation cursor contract

`current.json.continuation_cursor` must contain:

- `parent_workstream_id`;
- `last_completed_action`;
- `current_task`;
- `why_now`;
- `done_when`;
- `next_atomic_action`.

The cursor is not a devlog. It answers only:

```text
what just finished?
what should resume now?
why is it current?
what ends it?
what comes immediately after?
```

## 8. Real-time micro-checkpoint lifecycle

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

## 9. Canonical fixed transfer phrase

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The phrase must remain task-free. Repository state owns the current task.

## 10. Core growth rule

Core files have CI ceilings but ceilings are not brevity targets.

Failure extremes:

```text
overcompression → slogans survive, causal mission disappears
overgrowth      → startup becomes project archaeology
```

Current target: high semantic fidelity + bounded growth + minimum sufficient context.

Specific industry facts never enter long-term Core. Reusable lessons enter Method Core only after explicit user adoption or sufficient cross-benchmark evidence.

## 11. Authority planes

Strategic authority:

```text
new explicit user instruction
> Strategy Core
> Method Core
> dynamic strategic horizon
> deep historical narrative
```

Implementation freshness:

```text
live Git graph / HEAD / CI
> canonical / deterministic-derived artifacts
> checkpoint snapshot
> narrative
```

New code cannot silently redefine mission. Old checkpoint state cannot outrank live Git.

## 12. Protocol evolution

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

## 13. Repository-only checks

CI should verify at minimum:

- Core byte/line bounds;
- active-context exclusion from long-term cores;
- mission semantic contract exists and contains no current-industry data;
- bootstrap order requires first-pass synthesis before semantic calibration;
- typed strategic horizon and continuation cursor are complete;
- resume set is bounded;
- campaign/context paths derive from active context rather than a hard-coded industry;
- raw/canonical campaign state agrees with checkpoint where applicable;
- stale checkpoint scenarios are detected.

## 14. External fresh-Agent audit

A true external audit starts from repository name or the fixed transfer phrase only. The Agent must independently discover active state, reconstruct mission/method, calibrate itself, recover the continuation cursor and report-only audit the mechanism without repairing it.

Not remembering irrelevant old industry details is a success.
