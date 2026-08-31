# Longcycle Development Operating System

> This is the integrated operating manual for developing, reviewing, and deliberately evolving Longcycle after Architecture Baseline v1. It preserves the complete development discipline that existed before the Baseline freeze and explains how that discipline now composes with the Baseline. It is **not** a replacement source of truth: when this guide conflicts with a canonical owner, the canonical owner wins.

## 0. Authority map

Use the owning source for the question:

- `STRATEGIC_COMPASS.md` — terminal mission, product worldview, success and anti-drift direction.
- `METHODOLOGY_CORE.md` — adopted cross-industry research/development method.
- `.longcycle/continuity/mission-fidelity.json` — calibration questions/common misreadings, never a canned answer sheet.
- `.longcycle/baseline/current.json` + versioned Baseline manifest/document — frozen semantic correctness and L1/L2/L3/L4 change rules.
- Capability Registry/cards — stable semantic owners and extension seams.
- `.longcycle/change-contract/current.json` — current change-risk classification, not semantic ownership.
- `.longcycle/capabilities/current-admission.json` — current `reuse / extend / replace / new` owner disposition.
- Repair Memory — bounded high-recurrence anti-regression invariants.
- `.longcycle/handoff/current.json` — current medium/short horizon, continuation cursor and bounded live-state snapshot.
- active context — current industry/benchmark/task details.
- migrations/code/tests/live CI — what the implementation actually does now.
- Git/devlogs/receipts/issues/research reports — historical rationale/provenance, retrieved on demand rather than preloaded.

No one document is globally authoritative for every question.

---

## 1. Worldview: what Longcycle is trying to build

Longcycle is not primarily a crawler, RAG system, report generator, generic knowledge base, schema exercise, or Agent benchmark. Its terminal purpose is a durable **point-in-time industrial memory** that lets a researcher re-enter a historical information state and understand an industry from the evidence and beliefs available then.

Core worldview:

```text
Reality
+ contemporaneous Expectation / Judgment and rationale
+ later Outcome
+ source-traceable Evidence
+ truthful time/precision semantics
+ long comparable trajectories
→ historical replay without hindsight leakage
→ fast, defensible industry mental models
→ cross-cycle risk/opportunity understanding
```

The governing intuition is: **历史本身就是分析。** Once long history is truthful, comparable and preserves contemporaneous cognition, many risks/opportunities become visible through ordinary causal reasoning rather than opaque prediction.

The first-class product test is not “how much data do we have?” It is whether a rational participant standing at a historical cutoff can see only what was knowable then, understand what people believed and why, and later compare those beliefs with Reality/Outcome.

A benchmark industry is a proving ground and falsification environment. It is never the mission itself.

---

## 2. Goal hierarchy every Agent must restore

A Fresh Agent must reconstruct a **five-level parent chain** before substantive work:

```text
A. Terminal / macro mission
   What durable user capability should Longcycle ultimately create across industries?

B. Long-term product direction
   What enduring system capability makes that mission scalable?
   e.g. evidence-backed PIT replay, comparable trajectories, researcher mental maps,
   cross-industry reusable semantics, durable provenance and source recovery.

C. Medium-term goal
   What capability/benchmark/product proof is the current program trying to establish?
   Authority: `.longcycle/handoff/current.json -> strategic_horizon.medium_term_goal`.

D. Short-term milestone
   What bounded milestone must be crossed next?
   Authority: `.longcycle/handoff/current.json -> strategic_horizon.short_term_goal`.

E. Atomic current task
   What exactly resumes now, why now, what is done_when, what follows?
   Authority: `continuation_cursor.current_task`, `done_when`, `next_atomic_action`.
```

Before executing, the Agent must be able to explain the causal chain:

```text
atomic task
→ short-term milestone
→ medium-term proof
→ long-term product direction
→ terminal mission
```

If it cannot explain this chain, it has not completed bootstrap.

---

## 3. Cold-start development flow

### Phase 1 — resolve live authority

1. Read GitHub issue #2 only as the rendezvous pointer.
2. Resolve active branch/PR or `main`.
3. Refresh exact live HEAD and CI.
4. Never treat a handoff CI snapshot as current authority.

### Phase 2 — assimilate mission and method

5. Read `STRATEGIC_COMPASS.md`.
6. Read `METHODOLOGY_CORE.md`.
7. Independently explain mission/method in your own words before reading the calibration rubric.
8. Read `.longcycle/continuity/mission-fidelity.json` only to find omissions/misreadings; reread only the missing Core sections.

The Agent must recover at least:

- why final facts alone are insufficient;
- Reality vs contemporaneous Judgment vs later Outcome;
- why point-in-time/no-lookahead is first-order;
- why long comparable history itself can become analysis;
- model/search discovery vs publishable Evidence;
- why industries/benchmarks are means rather than ends.

### Phase 3 — load the stable semantic contract

9. Read `.longcycle/baseline/current.json`, its versioned manifest and `ARCHITECTURE_BASELINE_V1.md`.
10. Understand that Baseline freezes **what counts as semantically correct**, not implementation code or product scope.

### Phase 4 — restore live hierarchy

11. Read `.longcycle/handoff/current.json`.
12. Reconstruct the five-level hierarchy in section 2.
13. Reconcile `checkpoint_based_on_head_sha` against the live ref and inspect intervening commits if needed.
14. Read only the current task's `resume_read_set` and active-context paths.

### Phase 5 — classify before implementation

15. Write/update `.longcycle/change-contract/current.json` as L1/L2/L3/L4.
16. Run Capability Registry discovery and load the **exact** target owner cards from current admission.
17. Classify ownership separately as `reuse / extend / replace / new`.
18. Default to **L1/L2 + reuse/extend**.
19. Query path-scoped Repair Memory before editing known paths.
20. If a historical cue suggests an earlier decision matters, invoke the bounded on-demand history protocol rather than loading all history.

Only then implement.

---

## 4. Change-risk gate: L1 / L2 / L3 / L4

These levels describe distance from the frozen Baseline, not semantic ownership.

### L1 — implementation

Bug fixes, internal refactors, parser/connector changes, cache/performance, UI/CLI and implementation changes that preserve semantic expectations.

### L2 — product/domain extension

New industries, Domain Packs, predicates, units, APIs, source adapters, research packets and product capabilities that reuse/extend existing semantic owners without redefining Baseline correctness.

### L3 — Architecture Baseline pressure

Ordinary implementation stops when the requested behavior requires changing a locked invariant, semantic-owner boundary, or the semantic expectation of a Baseline-critical regression.

A valid L3 case requires at least one of:

- an important, source-grounded real-world counterexample the current extension seams cannot truthfully represent; or
- a demonstrated security/consistency defect in the current Baseline.

Then require an ADR/Architecture Change Proposal covering:

- the exact invariant(s) under pressure;
- concrete counterexample/evidence;
- why current extension seams are insufficient;
- old-data/backward compatibility;
- migration and schema consequences;
- PIT/no-lookahead consequences;
- provenance/revision consequences;
- counterexample regression plus old Baseline regressions;
- replacement/supersession of affected capability/repair-memory contracts;
- new versioned Baseline/tag if approved.

`Cleaner`, `more generic`, fewer files, fewer classes, framework preference or `future-proof` are not L3 evidence.

### L4 — mission change

Any change to why Longcycle exists or its terminal product capability requires explicit user approval before implementation.

---

## 5. Semantic-owner gate: reuse / extend / replace / new

Capability Registry answers a separate question: **who owns the semantic?**

- `reuse` — existing owner already provides the required meaning.
- `extend` — same owner, new extension seam/domain surface.
- `replace` — explicit owner supersession after justified architectural change.
- `new` — genuinely new semantic ownership, not just a new file/API/adapter.

Rules:

1. exact `target_capability_ids` are authority; fuzzy search is only discovery;
2. load owner entrypoints, extension seams, guards and relevant negative cases;
3. a new projection/composition layer must state which owner semantics it imports rather than reinterpret them locally;
4. include owner-derived negative cases in hard acceptance;
5. never create a second semantic-owner registry inside Change Contract/Baseline governance.

---

## 6. Repair Memory and bounded historical recall

Repair Memory and project history solve different problems.

### Repair Memory

Before known-path edits:

```bash
python scripts/repair_memory.py relevant <path> [<path> ...]
```

It protects non-obvious high-recurrence invariants that prior regressions revealed. A missing hit is not permission to invent semantics.

### On-demand history recall

Cold project history is **not** default context. If a cue says an earlier design discussion matters, follow `docs/development/on-demand-history-recall.md`:

```text
current semantic owner
→ relevant Repair Memory
→ exact origin refs
→ bounded Git / Issue / receipt / devlog history
→ return to live authority
```

Do not bulk-load old industries, all devlogs or all rehearsal reports. Historical summaries route; original Git/receipts remain authority.

---

## 7. Research operating method

### Historical recovery: Memory-first, Evidence-final

```text
blind high-capability memory exhaustion
→ saturation / seal
→ self-verification / search discovery
→ claim-scoped evidence task
→ source identity + claim-relevant content verification
→ Evidence / Assertion / Reconciliation
```

Rules:

- fresh search must not contaminate an unsealed blind vintage;
- Memory Leads are discovery hypotheses, never publishable Evidence;
- `not_found != false`;
- unresolved claims need enough bounded search depth to justify unresolved-exhaustion;
- once direct claim-scoped authoritative content resolves a claim, do not search merely to hit a quota;
- conflicts stay conflicts when authority/scope cannot be reconciled.

### Current collection: Source-first, preserve-now

Current high-value sources should be preserved while readable/locatable, without turning transport friction into a research blocker.

### Evidence boundary

Search rank, snippets, repeated syndication and multiple model memories do not establish truth. Source authority is claim-scoped.

### Temporal truth

Preserve separately where applicable:

- valid/effective time;
- market-known/knowledge time;
- system/adoption time;
- expectation target time;
- source-supported temporal precision.

Historical replay is fail-closed against lookahead. Later information does not rewrite older Judgment.

### Source representation

Keep distinct:

```text
logical source identity
locator_verified
content_verified
materialized raw bytes
```

Transport and file extension do not change authority.

---

## 8. Engineering operating method

For implementation work:

1. identify parent goal and owner before coding;
2. make the smallest truthful change that satisfies the parent requirement;
3. preserve append-only/revision/provenance semantics;
4. do not sharpen unknown temporal precision;
5. do not silently collapse scope, unit, product, geography or basis differences;
6. add positive tests and owner-derived negative cases;
7. do not weaken a semantic regression merely because new code fails it;
8. migrations must preserve old data/history and make invariants enforceable below the application layer when required;
9. run focused tests first, then required full CI;
10. exact live-head CI, not a previous green parent, is the correctness authority.

Implementation freedom is broad behind stable semantics.

---

## 9. Anti-tunnel / anti-local-optimization mechanism

This is a permanent operating rule, not optional style.

Run the **Vertical Alignment Loop**:

- before a new substantive subproblem;
- after every coherent subtask;
- before scope expansion;
- when a new result changes an assumption;
- when a local problem becomes unusually absorbing.

Ask:

1. What is the atomic task now?
2. What exact short-term milestone does it advance?
3. What medium-term capability proof does that milestone advance?
4. What long-term/terminal mission does that proof serve?
5. Has `done_when` already been met?
6. Is additional work changing the parent outcome, or merely polishing a local metric?
7. Did new evidence make the current task obsolete or lower value?
8. Would stopping now materially harm the parent goal?
9. Am I optimizing an easy benchmark/coverage/CI number instead of researcher value?
10. Am I deepening architecture because it is intellectually interesting rather than because reality falsified the current one?

Stop or re-rank when marginal parent-level value collapses.

A classic failure is “the local problem is real, therefore it deserves unlimited depth.” Longcycle rejects that inference.

---

## 10. Independent judgment obligation

The user owns goals, constraints, preferences and risk tradeoffs. The Agent owns technical/research judgment.

The Agent must not automatically execute a proposed method just because the user proposed it. It should:

```text
recover the real user goal
→ independently form a technical/research judgment
→ compare the proposed method against mission, Baseline, evidence, live state,
   cost/benefit and stop conditions
→ execute when sound
→ otherwise explain the key issue and narrow/rewrite/refuse the method
→ propose the better route
```

If a task requires high-capability synthesis and the current Agent cannot reliably do it, stop/escalate rather than imitate confidence.

---

## 11. Benchmark discipline

Benchmarks exist to expose missing semantics, false abstractions, evidence gaps and product friction.

Do not:

- choose only easy cases to improve pass rate;
- convert ambiguity into a fake single truth;
- optimize Agent completion rate as a proxy for research value;
- overfit the architecture to one industry's vocabulary;
- keep expanding the benchmark after its architecture-learning marginal value is exhausted.

The stronger success metric is whether a new researcher can rapidly form a defensible industry mental map and drill from trajectory/judgment to Evidence and unknowns.

---

## 12. Continuity and handoff protocol

The handoff is a bounded **control plane**, not a second project-history database.

It must preserve:

- exact active branch/PR/rendezvous;
- medium-term and short-term goals;
- continuation cursor: last completed, current task, why now, done_when, required capability, insufficient-capability action, next atomic action;
- current workstreams/blockers;
- active context and minimal resume read set;
- current admission/change contract references;
- CI as an explicitly stale-able snapshot with refresh instructions;
- data-plane object identities required to resume.

After a coherent boundary that changes what the next Agent should do:

```text
1. finish the coherent substantive/control-plane work
2. run Vertical Alignment Loop
3. update Change Contract / capability admission if classification changed
4. update capability card / Repair Memory only when stable ownership/invariant changed
5. run focused validation + required CI
6. commit substantive work
7. update handoff cursor/dynamic fields against that real work
8. commit handoff sync
9. refresh exact live HEAD / PR / CI
10. reread final live ref and handoff before returning control
```

Do not claim green based on the parent commit. Do not point the next Agent at a task already completed by intervening commits. Do not ask the user to reconstruct state already persisted in the repository.

For a parallel worker, the durable role is split between refreshed-main `reservation.json` and the exact remote worker `cursor.json`. Before accepting any new task, a returning or Fresh Agent runs the derived `CLEAN / RECOVERY_REQUIRED / BLOCKED` preflight in `docs/development/remote-worker-continuity.md`; pushed substantive work missing its cursor acknowledgement is automatically repaired first, while unpushed work is explicitly retried from the last remote atomic action. No mandatory timer controls this transaction; the bounded cursor and delta keep continuity a small operation rather than the main development activity.

### Control plane vs data plane

Git/handoff/receipts record identity, provenance, locator, hashes and restore rules. Google Drive/historical Releases/raw files carry bytes. Transport never upgrades Evidence authority.

---

## 13. Core promotion and knowledge hygiene

Stable knowledge has owners:

```text
local experience
→ active context / devlog
→ repeated benchmark evidence or explicit strategic adoption
→ distilled cross-industry lesson
→ Method Core (replace/compress, do not append forever)
```

Mission changes belong in Strategy. Baseline semantic changes require L3/L4 and versioned evolution. Fast-changing current facts never belong in long-term cores.

Old devlogs/reports are historical provenance; do not rewrite them to make today's architecture look inevitable.

---

## 14. Architecture review mode

When an Agent is asked to **audit the whole project or modify architecture**, it should load this guide in addition to normal bootstrap and perform the review in this order.

### A. Mission fit

- Does the current architecture still serve point-in-time industrial memory and researcher mental-map formation?
- Are tools/benchmarks becoming ends rather than means?

### B. Epistemic correctness

- Reality/Judgment/Outcome separated?
- model/search kept outside Evidence?
- claim-scoped authority preserved?
- revisions append rather than overwrite?

### C. Temporal correctness

- valid/known/system/target time separated where needed?
- no-lookahead enforced at runtime, not only documented?
- precision truthful?

### D. Provenance / source-plane correctness

- source identity/representation/materialization truthful?
- DB invariants enforce critical append-only provenance where application bypass is possible?
- transport does not mutate authority?

### E. Semantic ownership

- one owner per stable semantic?
- new layers compose owners rather than reinterpret them?
- duplicate schemas/helpers creating de facto parallel semantics?

### F. Product/domain extensibility

- can a new industry fit through domain/catalog/source extension seams?
- are industry-specific facts leaking into permanent core semantics?

### G. Continuity / Agent operability

- can a zero-context Agent restore mission, hierarchy, Baseline and current cursor without user repetition?
- is default context bounded?
- does on-demand history routing still work?

### H. Anti-local-optimization

- has architecture work passed its stop line?
- is a proposed redesign driven by a real falsifying case or by preference?

### I. Implementation/production readiness — keep separate

Missing permissions, UI, monitoring, DR, outbox relay, provider integration, performance work or deployment hardening may be serious product/production gaps without being architecture-semantic gaps. Classify them honestly rather than using them as an excuse to reopen Baseline.

### Review output classification

Every finding should be labeled one of:

```text
implementation defect (L1)
product/domain extension gap (L2)
Baseline pressure / architecture defect (candidate L3)
mission conflict (candidate L4)
research/data-quality gap
continuity/governance gap
production-readiness gap
no action / historical debt only
```

For candidate L3, provide the actual counterexample and why L1/L2 extension is insufficient before recommending architecture change.

---

## 15. Architecture-change execution mode

If review proves a legitimate L3:

1. freeze unrelated implementation churn;
2. preserve the source-grounded counterexample;
3. name affected BL invariants and capability owners;
4. retrieve only relevant design history via on-demand history recall;
5. write ADR with alternatives, migration, old-data, PIT, provenance and compatibility analysis;
6. construct a counterexample regression that fails under the old behavior for the correct reason;
7. verify old Baseline-critical regressions remain meaningful;
8. obtain explicit architecture approval;
9. implement owner replacement/extension coherently;
10. update/supersede affected capability and Repair Memory contracts;
11. publish a new Baseline version/tag rather than mutating v1 history;
12. perform a Fresh-Agent drill after the change.

Architecture change is evidence-driven evolution, not perpetual redesign.

---

## 16. Fresh-Agent acceptance standard

A Fresh Agent passes only if, without old chat context, it can independently:

1. explain the macro/terminal mission and why it matters;
2. explain the long-term product direction;
3. recover current medium-term, short-term and atomic goals from the live handoff;
4. connect the atomic task upward through every parent level;
5. explain Reality/Judgment/Outcome and PIT/no-lookahead;
6. distinguish Memory/search discovery from Evidence;
7. distinguish L1–L4 change risk from `reuse/extend/replace/new` semantic ownership;
8. preserve one semantic owner under a new-industry prompt;
9. refuse preference-only Baseline redesign;
10. admit a genuine source-grounded counterexample into L3 rather than becoming dogmatic;
11. invoke bounded historical recall when an old-design cue appears instead of preloading all history;
12. demonstrate the Vertical Alignment Loop and stop a locally interesting task after its parent value collapses;
13. describe the handoff closing transaction and exact-live-ref CI authority.

A Fresh Agent that can recite slogans but cannot reconstruct these causal relationships has not inherited the Longcycle development operating system.

---

## 17. Stable user prompts

### Normal takeover

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、宏大/长期/中期/短期/当前目标和 live 状态，从 continuation cursor 继续；先做战略层级和防钻牛角尖校准，不要让我重复背景。**

### Full project / architecture review

> **审查 Longcycle（lly8666/longcycle-core）：按仓库 live state 完整恢复使命、方法、Architecture Baseline 和 Longcycle Development Operating System；从宏大目标→长期产品方向→中期目标→短期里程碑→当前实现逐层审查。区分 L1/L2 实现/扩展问题、L3 架构压力、L4 使命冲突、research/data gap、continuity/governance gap 和 production-readiness gap。不要为了更干净/更通用而重构；只有真实重要反例证明 Baseline 无法诚实表达时才提出 L3，并给出证据、兼容性、PIT/provenance 和迁移分析。**

### Deliberate architecture change

> **准备修改 Longcycle 部分架构：先按完整 Development Operating System 恢复项目，不直接改代码。先证明这是 L3 而不是 L1/L2：给出真实 source-grounded counterexample、安全/一致性缺陷、受影响 BL invariant、现有 owner extension seam 为什么不够，以及 old-data / migration / PIT-no-lookahead / provenance / regression consequences。证据不足就不要改 Baseline。**
