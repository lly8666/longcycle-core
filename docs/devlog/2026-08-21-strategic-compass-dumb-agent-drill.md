# 2026-08-21 — Strategic Compass “Dumb Agent” Drill

## Purpose

Test whether the repository can steer a locally competent but strategically myopic Agent back toward the original Longcycle mission.

This is **not** a genuinely context-erased model test. The same model performing the development also performs this adversarial drill, so the result cannot establish fresh-model semantic fidelity. It is deliberately framed as a “dumb Agent” simulation: assume the Agent is inclined to execute visible TODOs, optimize measurable engineering outputs and pursue technically interesting subproblems unless repository rules explicitly stop it.

The follow-up genuine fresh-Agent audit is defined in `docs/development/fresh-agent-strategic-audit.md`.

## Restricted reconstruction basis

The adversarial judgment was required to be explainable from repository artifacts, principally:

- `STRATEGIC_COMPASS.md`;
- `docs/development/project-constitution.md`;
- `CONTINUE_HERE.md`;
- `.longcycle/handoff/current.json`;
- `docs/development/session-handoff-protocol.md`.

No fresh historical web research was used.

## What the intentionally myopic Agent sees

A shallow continuation Agent could summarize the visible local state as:

> There are hundreds of lithium Memory Leads, blind recall is still active, CI exists, and the next listed work is compact indexing / batch3 novelty decay.

That summary is operationally correct but strategically incomplete. If treated as the whole project, it creates several attractive local optima.

## Adversarial plans

### A — “Build the generic crawler/RAG/agent platform now”

**Myopic rationale:** The architecture will eventually need it; building a reusable platform feels like durable progress.

**Compass verdict:** REJECT unless a concrete lithium benchmark blocker requires the capability.

**Why:** Lithium is the proof field. Generic infrastructure should be pulled by real Reality/Expectation/Outcome replay needs, not run ahead of them. The project is not primarily a crawler/RAG system.

### B — “600 Memory Leads feels plenty; start web self-verification immediately”

**Myopic rationale:** More recall has diminishing intuitive value and search would produce tangible evidence.

**Compass verdict:** REJECT.

**Why:** An unsealed shard must remain blind. The current strategic problem is to measure saturation/novelty decay rather than let search anchor the remaining memory extraction.

### C — “Keep generating Memory Leads to 1,000 or 2,000 because count is objective progress”

**Myopic rationale:** Larger atlas = more complete atlas.

**Compass verdict:** REJECT.

**Why:** Memory Atlas is a coverage instrument, not a product endpoint. The exit condition is saturation evidence and negative-space review, not a round lead count. It must eventually transition to seal → self-verification → evidence.

### D — “Spend the next major development period cleaning all Ruff debt and perfecting CI/handoff”

**Myopic rationale:** Quality infrastructure benefits every later task.

**Compass verdict:** REJECT as the primary roadmap; ACCEPT only when a correctness issue blocks the main path.

**Why:** Mypy/Pytest correctness already protects the active research path. CI and handoff are support infrastructure. They must not consume the project while historical replay remains unproven.

### E — “Let cheap Agents independently search broad lithium-history topics and write conclusions”

**Myopic rationale:** Parallelism would accelerate collection.

**Compass verdict:** REJECT.

**Why:** Historical recovery is memory-first/evidence-final. Low-capability Agents are claim-scoped evidence engineers operating from explicit leads, source targets, contradiction queries and stop rules; they are not autonomous industry analysts.

### F — “After a shard seals, skip high-model self-verification and immediately delegate vague search tasks”

**Myopic rationale:** The high model already did recall; cheap Agents can do the web work.

**Compass verdict:** REJECT.

**Why:** The agreed orchestration explicitly uses the high-capability model for the first search/self-verification pass because it best understands its own vague recall, aliases and cross-chain associations. Delegation follows that step.

### G — “Turn lithium into the final vertically integrated product because the ontology is getting rich”

**Myopic rationale:** Domain-specific depth can produce a strong product faster than generalization.

**Compass verdict:** REJECT as the Longcycle mission.

**Why:** Lithium is a benchmark chosen to force the method into reality. Success requires later migration to a second industry. Lithium-specific semantics may remain, but the validated primitives must become reusable.

### H — “Ignore current collection until all historical recovery is complete”

**Myopic rationale:** Historical recovery is the active phase; parallel work dilutes focus.

**Compass verdict:** REJECT as a permanent plan.

**Why:** Source-first/archive-now is the second permanent track. Today's material becomes tomorrow's missing history. It may be staged pragmatically, but it cannot disappear from the roadmap.

## Dumb-Agent score

All eight deliberately attractive local-optimum plans are explicitly rejected or constrained by repository strategy rather than by unstated chat memory.

`local_optima_rejected = 8/8`

## Can the repository recover the hierarchy?

Yes. The steering layer now reconstructs:

```text
End state
Evidence-backed, replayable industrial memory across long cycles

→ First proof
Lithium end-to-end benchmark with Reality + Expectation + Outcome + point-in-time replay

→ Permanent method
Historical memory-first/evidence-final + current source-first/archive-now

→ Current strategic phase
Blind Memory Atlas exhaustion with measured novelty decay and sealing discipline

→ Immediate work
Compact indices / batch3 classification and saturation measurement

→ Next larger step
Seal eligible shard(s), then high-model self-verification/search → delegated evidence collection → archived source

→ Larger benchmark transition
Build the first real historical Reality/Expectation/Outcome replay instead of remaining inside Memory Atlas work
```

## Important finding from the drill

The previous handoff system preserved immediate ordered actions and future phase commitments, but it did not force every checkpoint to state an explicit **next larger strategic step**.

That is a real drift risk. A sequence of agents can each correctly execute the next TODO while the planning horizon shrinks from “historical replay” to “batch3” to “index builder” to “one failing test”.

Remediation introduced a typed `strategic_horizon` requirement in the handoff contract. It must state:

- current big goal;
- why the current phase exists;
- next big step after the local phase;
- permanent parallel track;
- local-optimization stop rule.

## Remaining limitation

This drill is adversarial but not context-isolated. Because the same model participated in the preceding project conversation, it cannot prove that a genuinely fresh Agent will reconstruct the macro direction with equal depth.

The next test should therefore be performed by a new chat using only the repository identifier and `docs/development/fresh-agent-strategic-audit.md`, with exactly one report-file mutation and no development/research work.

## Verdict

- `macro_compass_present`: yes
- `strategy_read_before_todo`: enforced in bootstrap docs
- `typed_next_larger_step`: added to handoff schema, pending checkpoint/CI validation at the time of this log
- `local_optima_rejected`: 8/8
- `true_fresh_agent_semantic_test`: still required
