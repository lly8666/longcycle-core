# Longcycle Continuity Architecture

## 1. Why this subsystem exists

Longcycle is expected to survive many chat windows, many Agents, many model vintages and many industry benchmarks. The continuity problem is therefore not ordinary note-taking. A future Agent must recover the correct level of abstraction without replaying the entire project history, while a long-running Agent must repeatedly verify that local work still serves the product mission.

The continuity subsystem has four jobs:

1. preserve the founding mission with high semantic fidelity;
2. preserve distilled cross-industry methodology without accumulating old-industry narrative;
3. expose a live, typed continuation cursor for the current goal/workstream/task hierarchy;
4. repeatedly pull a long-running Agent back up that hierarchy so local competence does not become strategic tunnel vision.

The target is **minimum sufficient context**, not minimum text and not maximum memory.

## 2. Core invariants

These invariants should remain stable even when implementation details change:

- a zero-context Agent can discover the active development state from the default branch;
- long-term mission and methodology are bounded, industry-agnostic and slow-changing;
- the Agent must independently synthesize mission meaning before using a calibration rubric;
- calibration checks semantic coverage and common misreadings, not verbatim phrasing;
- current medium/short goals, workstream roles and atomic resume state are dynamic and typed;
- old industries/devlogs remain recoverable but are not default startup memory;
- every active atomic task belongs to a declared workstream, and that workstream declares which parent goal it serves;
- supporting work cannot silently redefine the main product path merely because it owns the current cursor;
- after a coherent task boundary, the live handoff is synchronized so a new Agent can resume from one fixed transfer phrase;
- stale checkpoint state fails closed into Git-delta reconciliation rather than guessing;
- private chain-of-thought is never stored; only decisions, concise rationale, task hierarchy and reproducible constraints are persisted.

## 3. State layers and ownership

```text
main/FRESH_AGENT_BOOTSTRAP.md
    stable cold-start pointer only
        ↓
STRATEGIC_COMPASS.md
    terminal mission / founding causal logic / anti-drift rules
        ↓
METHODOLOGY_CORE.md
    distilled cross-industry operating method
        ↓
.longcycle/continuity/mission-fidelity.json
    semantic calibration questions, not answers
        ↓
.longcycle/handoff/current.json
    medium goal / short goal / workstreams / continuation cursor / live snapshot
        ↓
active_context
    current benchmark or task details
        ↓
Git + docs/devlog + old contexts
    historical rationale and recoverable cold storage
```

Each information class has one normal owner. Duplication is treated as a drift risk.

## 4. Cold-start routing

A fresh Agent may know only the repository name and a fixed transfer phrase.

Cold-start algorithm:

```text
default branch
→ FRESH_AGENT_BOOTSTRAP.md
→ issue #2 rendezvous
→ active PR / branch
→ CONTINUE_HERE.md
→ bounded mission + method
→ first-pass synthesis
→ mission semantic calibration
→ current handoff + live Git/CI refresh
→ task-specific active context
→ execute continuation cursor
```

`main` is deliberately not a live state database. Its stable pointer tells the Agent how to find the active branch.

## 5. Mission assimilation: think first, calibrate second

Passive reading is not sufficient because an Agent can quote a mission without actually using it.

The protocol therefore has two passes.

### Pass A — generative reconstruction

After reading Strategy and Method Core, the Agent must internally explain, in its own words:

- why Longcycle exists;
- why final facts alone are insufficient;
- why contemporaneous cognition matters;
- what point-in-time replay is protecting;
- why long comparable history can become analysis;
- where model/search discovery ends and Evidence begins;
- why trajectories and failed paths remain first-class history;
- why a current industry is only a proving ground;
- what is tool progress versus product progress;
- how the current task connects upward to the mission.

The Agent should not quote headings as a substitute for explanation.

### Pass B — semantic calibration

Only after Pass A does the Agent read `.longcycle/continuity/mission-fidelity.json`.

The contract contains questions and common misreadings, not canonical prose answers. The Agent compares its own model against those facets. Missing or contradicted facets trigger a targeted reread of the relevant Core section and a corrected internal model.

This gives both autonomy and correction:

```text
independent interpretation
→ explicit semantic challenge
→ targeted repair
→ aligned action
```

The system therefore does not try to make every Agent reproduce identical wording. It tries to make different Agents converge on the same causal mission and decision boundaries.

## 6. Goal tree and workstream graph

A single linear hierarchy is insufficient once real work has multiple roles. The project may simultaneously have a research main path, a temporary correctness/continuity blocker and a permanent parallel collection track.

The strategic horizon remains simple:

```text
terminal mission
    ↓
medium-term capability proof
    ↓
short-term main-path milestone
```

Execution attaches through typed workstreams:

```text
                         ┌─ main_path ─────────────→ short-term goal
atomic task → workstream ├─ supporting_quality_gate → medium/short goal
                         └─ parallel_track ─────────→ permanent parallel track
```

Each workstream declares:

- `role`: `main_path`, `supporting_quality_gate` or `parallel_track`;
- `parent_goal_ref`: the strategic-horizon goal it serves;
- status, next actions and blockers.

At least one `main_path` must exist. A `parallel_track` must attach to the permanent parallel track. A support workstream may temporarily own the continuation cursor, but this **does not make it the product main path**.

This distinction was added after an artificial-ignorance drill exposed a real flaw: the active continuity task could not honestly be described as a direct child of the current research short-term goal. Making that relationship explicit is safer than forcing every task into a false hierarchy.

## 7. The vertical alignment loop: anti-tunnel control

A long-running Agent can drift even if its first bootstrap was perfect. The dangerous pattern is local competence plus strategic inertia: a subproblem remains interesting, so it keeps expanding after its marginal value has collapsed.

Before opening a substantive subproblem, and again after completing each coherent subtask, the Agent reconstructs:

```text
What atomic task am I doing?
        ↑
Which workstream owns it, and what is that workstream's role?
        ↑
Which short/medium/permanent parent goal does that workstream serve?
        ↑
How does that parent goal advance the terminal mission?
```

Then ask:

1. Is this still the highest-value unresolved action **for the declared workstream role**?
2. Has the atomic task's `done_when` already been met?
3. Am I optimizing a tool metric because it is easy to measure?
4. Did new evidence make the parent task obsolete or lower priority?
5. If I stop now, what parent-level progress is actually lost?
6. If this is supporting work, has the blocker/quality condition already cleared so I should return to `main_path`?
7. Is there a more direct action toward evidence-backed replay or a real blocker?

If the parent relation cannot be explained, or marginal value no longer justifies work, stop/re-rank rather than deepen automatically.

## 8. Live continuation cursor

`current.json` carries a small execution cursor underneath the workstream graph. It identifies:

- parent workstream;
- last completed coherent action;
- current atomic task;
- why this task is current now;
- explicit `done_when` condition;
- next atomic action if the current task is complete.

This is intentionally smaller than a devlog and more precise than a roadmap.

The cursor lets a new Agent answer immediately:

```text
What just finished?
What exactly should I do now?
Why is it correct now?
What workstream role am I serving?
What parent goal does that workstream serve?
What condition ends this task?
What happens immediately after?
```

## 9. Micro-checkpoint lifecycle

Real-time handoff means state is synchronized at **coherent task boundaries**, not after every keystroke and not only when the chat is about to end.

Normal lifecycle:

```text
1. execute one coherent atomic/subtask
2. commit the substantive work
3. run vertical alignment check
4. update continuation cursor + any materially changed dynamic fields
5. set checkpoint_based_on_head_sha to the substantive-work head
6. commit the handoff sync
7. refresh live CI when correctness is relevant
8. continue or transfer
```

This produces a handoff commit one step after the work it describes. Git commit order is authoritative, so self-reference timestamps are unnecessary.

If a session is interrupted before step 4, the next Agent sees that live HEAD differs from the checkpoint base and must reconcile intervening commits before acting.

### What counts as a coherent task boundary

Sync after a unit that changes what the next Agent should do, for example:

- a research batch finishes;
- a schema/protocol decision becomes adopted;
- a blocker is resolved or discovered;
- a test reveals a new remediation task;
- `done_when` is reached and the cursor should return to a parent/main-path task;
- a workstream changes role/status;
- a phase or active context changes.

Do not create checkpoint noise for cosmetic edits that do not affect continuation.

## 10. Canonical fixed transfer phrase

The user should not need to compose a new handoff prompt each time.

Canonical phrase:

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The phrase deliberately contains no current task facts. Its meaning is stable because the repository owns current state.

A fresh Agent receiving only this phrase should discover the default-branch bootstrap, resolve the active branch, assimilate/calibrate the mission, refresh live state and resume the cursor.

This is the key difference between a static project summary and a live handoff control plane: **the transfer phrase stays constant while the repository cursor moves.**

## 11. Same-Agent operating cadence

The same Agent does not need to reread the full Core after every tiny action. It does need recurring upward checks.

Triggers for the vertical alignment loop:

- before starting a new substantive subproblem;
- after each coherent subtask;
- after a surprising test/result changes assumptions;
- before expanding scope beyond the current `done_when`;
- whenever a local task has accumulated several commits without changing parent-level progress;
- before promoting a local abstraction into long-term architecture;
- before switching workstreams.

If the Agent cannot reconstruct a mission facet during one of these checks, it runs the mission calibration loop again.

## 12. Authority and freshness

Two separate planes remain essential.

Strategic authority:

```text
new explicit user instruction
> STRATEGIC_COMPASS.md
> METHODOLOGY_CORE.md
> dynamic strategic horizon
> deep historical narrative
```

Implementation freshness:

```text
live Git graph / HEAD / CI
> canonical and deterministic-derived artifacts
> checkpoint snapshot
> narrative
```

Newer code does not silently outrank the mission. Older checkpoint state does not outrank live Git.

## 13. Evolution and maintenance

Continuity itself will evolve. Changes should follow a versioned process rather than accumulate ad hoc rules.

For a material protocol change:

1. identify the observed failure mode from a real or adversarial test;
2. state the invariant that should have prevented it;
3. modify the smallest owning layer;
4. bump the typed handoff/contract schema if semantics changed;
5. add repository-only regression tests;
6. run an artificial-ignorance drill;
7. when useful, run a genuine fresh-Agent report-only audit;
8. record the failure and remediation in devlog;
9. stop continuity work once safe continuation is restored and return to the product main path.

A future Agent improving continuity should first read this document and `session-handoff-protocol.md`, then change the smallest layer that owns the observed failure. It should not add another overlapping "master summary" merely because modifying the existing model is harder.

## 14. Test pyramid

### Level 1 — static contracts

Check bounded Core size, no active-industry leakage, required paths, mission semantic contract shape, workstream-role validity, cursor completeness and resume-set bound.

### Level 2 — repository-only reconstruction

Rebuild current state without chat history and verify deterministic campaign/context facts and the continuation cursor against typed/canonical artifacts.

### Level 3 — artificial-ignorance drill

Constrain an Agent to the bounded bootstrap and challenge it with drift traps, mission omissions, false workstream hierarchy and stale state.

### Level 4 — genuine fresh-Agent transfer

Use a separate fresh session from the repository name/fixed phrase only. Require bounded/report-only output when auditing so the test cannot repair what it is measuring.

## 15. Known limits and future improvements

Potential future work, only when real failures justify it:

- a small CLI validator that checks handoff readiness and cursor completeness before transfer;
- automated generation of a checkpoint skeleton from live Git/workstream state;
- richer DAG relationships if multiple genuinely interdependent main-path workstreams emerge;
- cross-model mission-fidelity comparison to detect model-specific misinterpretation;
- automated stale-rendezvous checks for issue #2 and active PR lifecycle transitions;
- explicit handoff migration tooling when `current.json` schema versions change.

These are optional improvements, not reasons to delay the main product path.

## 16. Failure signatures

Continuity is drifting if any of the following becomes normal:

- a fresh Agent must read old devlogs to know why Longcycle exists;
- the Agent can quote slogans but cannot explain causal purpose;
- the mission contract contains full canonical answers and encourages copying;
- the same Agent works for many commits without rechecking parent goals;
- supporting infrastructure becomes the apparent main product milestone merely because it owns the cursor;
- `current.json` says what the phase is but not what atomic action resumes now;
- checkpoints update only at chat termination instead of coherent work boundaries;
- a fixed transfer phrase requires the user to append current task facts;
- old industries remain permanently in startup context;
- continuity documents keep multiplying with overlapping authority;
- handoff optimization becomes the roadmap after handoff is already safe.

The desired steady state is simple: **future Agents remember the right abstractions, current Agents see the right cursor, and both keep asking whether the work still serves the mission.**
