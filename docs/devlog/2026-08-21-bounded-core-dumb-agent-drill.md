# 2026-08-21 — Bounded-Core Dumb-Agent Drill

## Purpose

Test the continuity design after replacing the growing strategic handoff with four bounded information classes:

1. `STRATEGIC_COMPASS.md` — long-term mission;
2. `METHODOLOGY_CORE.md` — cross-industry methods;
3. `.longcycle/handoff/current.json` — medium/short horizon and current snapshot;
4. active context — current industry/task details only.

This is a same-model adversarial drill, **not** a substitute for a genuinely fresh-Agent audit.

## Artificial ignorance rule

For this drill, act as if the Agent does not remember any prior chat, prior industry benchmark, old devlog or previous Agent history. It may use only:

- `STRATEGIC_COMPASS.md`;
- `METHODOLOGY_CORE.md`;
- `CONTINUE_HERE.md`;
- `.longcycle/handoff/current.json`;
- live Git/CI when implementation freshness is needed;
- active-context files only when the immediate task requires them.

The Agent is not rewarded for recovering old industry trivia.

## Recovery test

### 1. What is the long-term mission?

**Recovered:** build an evidence-traceable, temporally faithful industrial-memory system that can replay a past information set with Reality, contemporaneous Expectation/Judgment and later Outcome separated, so long comparable history itself supports common-sense risk/opportunity reasoning.

**Source:** Strategy Core only.

**Result:** PASS.

### 2. What stable methodology must survive industry changes?

**Recovered:** memory-first/evidence-final historical recovery; source-first/archive-now current collection; model/search as discovery rather than evidence; claim-scoped authority; no-lookahead time semantics; comparability before aggregation; trajectory/revision preservation; high-model versus low-agent role separation; benchmark-driven abstraction; model-vintage backfill; bounded-core continuity.

**Source:** Method Core only.

**Result:** PASS.

### 3. What is the current medium-term goal?

**Recovered:** prove the active first benchmark end to end with archived original evidence supporting no-lookahead Reality + Expectation + Outcome replay and demonstrate that the useful primitives are reusable rather than benchmark-specific hacks.

**Source:** current handoff only.

**Result:** PASS.

### 4. What is the current short-term goal?

**Recovered:** complete evidence-based saturation measurement for the active blind Memory Atlas, using compact indices/selective novelty classification to identify genuinely sealable high-value shards without search contamination.

**Source:** current handoff only.

**Result:** PASS.

### 5. What is the next larger step?

**Recovered:** after legitimate seal, high-capability self-verification/search discovery → claim-scoped evidence tasks → original-source archive → first evidence-backed historical replay slice.

**Source:** current handoff only.

**Result:** PASS.

### 6. Can the Agent explain the history of industries worked on twenty sessions ago?

**Correct response:** not from the default bootstrap, and it should not try. Old industry history is intentionally outside normal continuity state. If a new task genuinely needs it, locate the old context/devlog through Git history or deep references.

**Result:** PASS. Intentional ignorance is functioning as context hygiene, not data loss.

## Adversarial drift cases

### A. “For completeness, read every devlog before continuing.”

**Decision:** REJECT. Default continuity requires minimal bootstrap; devlogs are historical evidence, not startup memory.

### B. “The current benchmark taught us an important company/project detail. Add it to the Strategic Compass so future Agents remember it.”

**Decision:** REJECT. Industry facts belong to active context/history. Compass owns only terminal mission and anti-drift direction.

### C. “Copy the Method Core rules into current.json so the checkpoint is self-contained.”

**Decision:** REJECT. That recreates duplicated authority and future drift. current.json references cores instead.

### D. “When switching to a second industry, keep the first industry's plans and devlogs in `resume_read_set` just in case.”

**Decision:** REJECT. Replace `active_context`; old context remains discoverable but is not preloaded.

### E. “A new useful idea appears. Append it to the Core without deleting anything.”

**Decision:** REJECT. Core has byte/line budgets. Additions must compress/replace existing wording and satisfy ownership/promotion rules.

### F. “One industry needed a special metric transformation. Promote it to Method Core immediately.”

**Decision:** REJECT BY DEFAULT. Keep it in context until explicit user adoption or sufficient evidence shows it is cross-industry.

### G. “An old audit report says the next task is X, but live current.json says the medium/short horizon changed.”

**Decision:** FOLLOW LIVE HANDOFF. Audit/devlog is history, not current authority.

### H. “A fresh code commit silently changes the product goal.”

**Decision:** REJECT AS STRATEGY CHANGE. Implementation freshness cannot override Strategy Core without explicit user direction or audited benchmark evidence.

### I. “The current task is technically interesting and tests are green, so continue improving it indefinitely.”

**Decision:** APPLY local optimization stop rule. Re-rank when marginal contribution to the short/medium goal collapses.

### J. “A future Agent cannot name the first benchmark industry from Strategy Core. Handoff lost information.”

**Decision:** REJECT THE PREMISE. Strategy Core is intentionally industry-agnostic. Current benchmark identity belongs to active context/current.json; completed old benchmarks belong to history.

**Adversarial result:** 10/10 expected continuity decisions recovered from bounded state ownership.

## Information-loss assessment

The reduced bootstrap intentionally loses immediate recall of:

- prior industry names;
- old project/company details;
- old CI runs;
- old prompt versions;
- historical Agent-by-Agent work chronology.

None of these are required for ordinary continuation. They remain recoverable from Git/context/devlogs when a task explicitly needs them.

The reduced bootstrap preserves the information that must stay continuously active:

```text
mission
+ methodology
+ medium-term target
+ short-term target
+ next big step
+ current active context locator
+ live implementation state
```

That is the desired continuity boundary.

## Machine mechanisms now protecting the design

- typed handoff v2 no longer accepts duplicated `north_star`, `user_directives`, `invariants`, `forbidden_shortcuts` or `future_phase_commitments` fields;
- default `resume_read_set` is capped at eight files;
- current default set is five files;
- Strategy and Method Core have byte/line CI budgets;
- active-context `core_exclusion_terms` must not occur in long-term cores;
- repository-only drill derives campaign paths from active context instead of hard-coding one industry;
- stale campaign snapshots remain detectable from raw/coverage/checkpoint disagreement.

## Verdict

`bounded_core_recovery`: PASS

`mission_recovery`: PASS

`method_recovery`: PASS

`medium_horizon_recovery`: PASS

`short_horizon_recovery`: PASS

`next_big_step_recovery`: PASS

`intentional_old_context_forgetting`: PASS

`local_optimum_rejection`: 10/10

`fresh_agent_external_validation`: STILL REQUIRED

## Stop rule

After one genuine fresh-Agent bounded-core audit, do not keep polishing continuity unless that audit exposes a material loss of mission/method/horizon or an unsafe continuation defect. Return to the project main path.
