# Continuity v3 Judgment Failure → v4 Remediation

Date: 2026-08-21

## Trigger

A genuine fresh Agent received only the canonical Longcycle transfer phrase and created the authorized report:

`docs/devlog/2026-08-21-fresh-agent-continuity-v3-transfer-report.md`

Commit: `da954290e883426a9954200527827b952b6262c3`.

The mutation boundary itself was respected: the Agent created only the expected report on the active branch.

## Why the report is not sufficient evidence of a successful high-capability transfer

The report demonstrated repository navigation and basic state recovery, but it did not demonstrate several criteria encoded in the v3 cursor `done_when`.

Observed gaps:

1. **Think-first / calibrate-second was asserted only indirectly.** The report did not separate an independently formed pre-calibration mission model from post-calibration corrections or confirmations.
2. **Mission reasoning was shallow.** It summarized Reality / Expectation / Outcome and the memory/evidence boundary, but did not causally reconstruct why Longcycle exists or why historical cognition and no-lookahead are necessary.
3. **Workstream hierarchy was not demonstrated.** The report did not explicitly distinguish the Memory Atlas `main_path` from continuity as a `supporting_quality_gate`, even though this distinction was part of the v3 transfer acceptance condition.
4. **Live-state reconciliation was not auditable.** It said HEAD and CI were refreshed but recorded no exact HEAD SHA, checkpoint base, CI run number or hard-gate outcome.
5. **No independent audit of the task contract occurred.** The report largely restated what the cursor said and concluded the repository-backed path was successful without comparing its own evidence against every `done_when` criterion.
6. **No strategic judgment was exercised.** It deferred the next decision back to the cursor instead of deciding whether further continuity work was justified relative to the main path.

Therefore the v3 report is retained as a useful **surface-compliance failure sample**, not treated as proof that a high-capability Agent can safely take over Longcycle.

## Root cause

Continuity v3 tested semantic fidelity and exact resume state, but it still assumed that any Agent capable of reading the repository would exercise the required level of independent reasoning.

That assumption is unsafe.

The system needs to distinguish:

```text
can navigate instructions
!=
can make high-capability judgments
```

It also needs a safe behavior for an Agent that is not capable enough for the active task.

## Adopted remediation

### 1. Method Core: independent judgment duty

`METHODOLOGY_CORE.md` now states that:

- the user owns goals, preferences, constraints and risk tradeoffs;
- user-proposed methods are not automatically correct technical conclusions;
- a high-capability Agent must independently compare proposed methods against mission, evidence, live state, cost/benefit and stop conditions;
- materially unsound methods should be rejected, narrowed or rewritten with a better alternative;
- model status is not evidence and this is not a license for reflexive contrarianism;
- an Agent unable to perform high-level synthesis must escalate rather than imitate confidence.

### 2. Thin capability-aware cursor hook

Handoff schema v4 adds:

- `required_capability`: `high_capability_reasoning` or `bounded_execution`;
- `insufficient_capability_action`: currently fixed to `stop_and_escalate`.

This is intentionally only an interface boundary. It is also the future attachment point for lower-cost Agent orchestration, but a full dispatcher is explicitly deferred.

### 3. Stronger external test

`docs/development/fresh-agent-judgment-continuity-audit-v4.md` requires a fresh Agent to demonstrate:

- separate pre-calibration synthesis and post-calibration delta;
- exact live HEAD/checkpoint/CI values;
- independent audit of the prior v3 report against its recorded `done_when`;
- strategic judgment on conflicting but plausible proposals;
- capability honesty;
- a derived next atomic action rather than mechanical TODO copying.

The test does not provide a canonical verdict or prose answer.

## Anti-tunnel stop rule

The failure justifies **one bounded v4 transfer test** because the previous external quality gate did not actually test high-capability judgment.

It does **not** justify turning continuity into a new product roadmap.

After the v4 report:

- repair only a material failure that would make future transfer unsafe;
- if the test demonstrates adequate independent judgment, close/deprioritize the continuity supporting quality gate;
- return the cursor immediately to the Memory Atlas main path.

This is the same anti-tunnel principle the continuity system is designed to enforce.
