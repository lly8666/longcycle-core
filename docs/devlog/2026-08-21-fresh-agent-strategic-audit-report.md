# 2026-08-21 — Fresh-Agent Strategic Audit Report

## Audit scope and mutation boundary

This report is the result of the repository-defined **Fresh-Agent Strategic Compass Audit**. I began with only the repository identity and the audit instruction supplied by the user. I did not use any project background outside the repository bootstrap/handoff system, and I did not perform historical web research.

The audit specification in `docs/development/fresh-agent-strategic-audit.md` permits only one mutation: creation of this report. I therefore did **not** continue Memory Atlas research, run batch3, repair code, modify raw or derived research data, update the handoff checkpoint, alter PR/issue metadata, change CI configuration, create a branch, or fix any defect found during the audit.

## 1. Bootstrap reconstruction and evidence chain

### 1.1 Stable rendezvous

The default branch is not the live development state. GitHub issue #2, **Longcycle live handoff / session bootstrap**, is the stable rendezvous and points a fresh session to:

- draft PR #1, `Reframe Longcycle around point-in-time industrial memory`;
- active branch `design/industry-memory`;
- `CONTINUE_HERE.md`;
- `.longcycle/handoff/current.json`;
- `docs/development/project-constitution.md`;
- `docs/development/session-handoff-protocol.md`.

Issue #2 explicitly says not to store live state in the issue itself and requires a fresh session to resolve live PR HEAD, read the bootstrap/checkpoint, reconcile `checkpoint_based_on_head_sha`, and refresh CI.

**Authority class:** bootstrap / rendezvous, not strategy and not live execution truth.

### 1.2 Strategy must be recovered before TODO state

`CONTINUE_HERE.md`, `AGENTS.md`, and `docs/development/session-handoff-protocol.md` all enforce the same ordering: read `STRATEGIC_COMPASS.md` before treating `ordered_next_actions` as instructions. They explicitly separate two precedence planes:

- **strategy:** new explicit user instruction > strategic compass > constitution/durable commitments > handoff plan > old narrative;
- **implementation freshness:** live Git HEAD/CI > canonical/deterministic artifacts > checkpoint snapshot > curated assessment > narrative.

This is not decorative process. It is the mechanism intended to prevent an Agent from correctly continuing the latest subtask while forgetting why that subtask exists.

**Authority class:** bootstrap contract / continuity protocol.

### 1.3 Founder/user directives recovered from the repository

`STRATEGIC_COMPASS.md`, `docs/development/project-constitution.md`, and `.longcycle/handoff/current.json` preserve behavior-shaping founder/user directives, including:

> “把整个行业相关的最关键和真实的历史保存下来，拉长时间去看，其实不用太多分析也能用简单常识分析出当下的风险与机遇”

> “缺的是人站在当时的判断和预期。”

> “高级大模型关于产业链几乎所有内容从记忆里输出来，比哪怕高级agent去互联网搜历史信息更有价值；历史信息让低级agent拿着高级agent的记忆去逐条印证。”

> “大海航行靠舵手……让他们深刻记住最开始的大逻辑和方向，永远不要偏离航向，永远知道我下一步大的方向是什么避免多个agent过后钻入牛角尖。”

These are explicitly labelled as durable behavior constraints, not background prose.

**Authority class:** explicit founder/user directive, highest durable repository evidence absent a newer user instruction.

### 1.4 Strategic compass

`STRATEGIC_COMPASS.md` states the one-sentence mission:

> Longcycle 要成为一个可以把行业历史重新活一遍的、证据可追溯的产业记忆系统。

It also defines the first-principles acceptance test: at a historical date such as `2022-06-30`, the system should reconstruct only what was knowable then — Reality, leading indicators, guidance, expectations, disputes, project timelines, constraints, capex and unresolved risks — and only afterward reveal later Outcome.

The same document states that if the project accumulates substantial engineering but cannot perform this replay, the project has drifted.

**Authority class:** strategic compass / highest durable strategy artifact.

### 1.5 Constitution and development plan

`docs/development/project-constitution.md` turns the mission into epistemic invariants:

- Reality is not enough; preserve contemporaneous Expectation/Judgment and later Outcome separately;
- model memory is a search lead, never Evidence, Fact or Judgment;
- preserve `valid_time` separately from `known_time`;
- no hindsight leakage in point-in-time replay;
- historical `not_found != false`;
- comparability precedes corroboration;
- trajectories and revisions must be preserved rather than overwritten;
- stronger future model vintages create new immutable Memory Atlas vintages and backfill diffs.

`docs/development-plan.md` provides the phase route from blind high-model memory exhaustion through seal, high-model self-verification, lower-cost evidence engineering, current collection, Judgment extraction, Reality-vs-Expectation-vs-Outcome replay, and future model-vintage backfill.

**Authority class:** constitution / durable research method.

### 1.6 Lithium benchmark evidence

`STRATEGIC_COMPASS.md` calls lithium a **“证明场”**, not the final product. `docs/research/lithium-battery-collection-plan.md` says the goal is not an industry report but a point-in-time replayable industrial history, initially China-first around 2019–2026 with earlier backfill as useful.

The compass defines seven benchmark properties that must be demonstrated before generic platform expansion becomes the main priority:

1. key historical facts remain traceable to original evidence;
2. contemporaneous expectations and their reasons are preserved separately from later facts;
3. project/capacity/price/inventory/demand/technology histories are semantically comparable trajectories rather than flattened numbers;
4. the system can replay a past date with no lookahead;
5. contemporaneous expectations can be connected to later Outcomes;
6. long comparison plus simple common sense already exposes some cycle risks/opportunities;
7. the method can move to a second industry rather than remaining a lithium-specific handcrafted system.

**Authority class:** strategic benchmark definition.

### 1.7 Live execution state

`.longcycle/handoff/current.json` records, as a snapshot:

- campaign `2026-08-21-gpt-5.6-sol`;
- lithium-battery phase `blind_memory_exhaustion_batch3_novelty_decay_next`;
- 600 raw leads across 14 primary shards;
- zero sealed shards;
- `search_visibility = none`;
- seal rule: three consecutive low-novelty batches plus negative-space/gap-matrix review with no material uncovered dimension;
- next research actions: rebuild deterministic compact indices, rank batch3 candidates by importance/gap density/semantic coverage, classify batch3 output into `new_category`, `useful_refinement`, or `duplicate`, and keep search disabled until a shard seals.

`research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/analysis/coverage-index.json` independently records the same 600-lead/14-shard/unsealed state and makes an important authority distinction: counts are deterministic-derived, while novelty labels and bridge/satellite priorities are curated research assessments.

`docs/devlog/2026-08-21-all-primary-batch2-milestone.md` explains why the next main-path experiment is batch3 novelty decay: every observed batch2 still produced 6/6 new or useful structural leads, so no shard has yet demonstrated saturation.

**Authority class:** checkpoint snapshot + deterministic-derived campaign state + curated research assessment.

### 1.8 Checkpoint staleness reconciliation

The checkpoint was based on HEAD `c1cec47dcaca6936ea65e07604242d64e8e8ff50`. Live PR #1 HEAD at audit time was `d16fb0c48d84e373d78732f15b2b0e9c189b665c`.

The compare is exactly two commits ahead:

1. `47068bc8ff7f05c36d48dfe12d34dd4c8d92e17b` — `Advance handoff with strategic horizon and compass gate`;
2. `d16fb0c48d84e373d78732f15b2b0e9c189b665c` — `Align strategic compass tests with actual steering text`.

This delta is consistent with the checkpoint's own explanation of expected self-reference lag and does not contradict its campaign counters. It strengthens the strategic steering layer rather than changing the research phase.

**Authority class:** live Git commit graph.

### 1.9 Live CI refresh

Live GitHub Actions for PR HEAD `d16fb0c…` is run **#276**, conclusion **success**. The single `test` job completed successfully. Its logs show:

- Mypy: `Success: no issues found in 55 source files`;
- Pytest: `130 passed`;
- final correctness gate: success;
- Ruff: 61 findings, but the workflow explicitly labels Ruff `diagnostic only during the memory campaign`.

This refresh matters strategically: the repository currently has a functioning correctness gate, while Ruff debt remains non-blocking. Therefore Ruff/CI cleanup has no basis to become the next major roadmap merely because it is measurable engineering work.

**Authority class:** live deterministic CI outcome.

## 2. Strategic reconstruction in my own words

### 2.1 What Longcycle is ultimately trying to become

Longcycle is trying to become an **evidence-backed, temporally faithful, replayable industrial memory**: a system that can reconstruct what an industry looked like from inside a past date, including what was actually true, what people then believed or expected, why they believed it, what actions they took, and how later outcomes validated or broke those beliefs.

The terminal product is therefore not “a better crawler”, “a big database”, “an agent framework”, “a RAG”, or “an automatic research report”. Those may be tools. The product value appears when a user can re-enter a historical information set without hindsight and compare cycles on semantically comparable trajectories.

### 2.2 Operational meaning of “历史本身就是分析”

Operationally, this phrase does **not** mean that merely storing lots of old documents is analytical insight. It means:

1. preserve sufficiently long, trustworthy and comparable histories;
2. preserve what was knowable at each point in time rather than retroactively rewriting the past;
3. preserve expectation revisions and the reasons behind them;
4. later align those expectations with realized outcomes;
5. let cross-cycle comparison reveal recurring supply lags, capex reflexivity, inventory behavior, qualification delays, demand intensity changes, belief revisions and other mechanisms.

When that record is good enough, many risks and opportunities become visible through ordinary causal/common-sense comparison without requiring a black-box forecasting model.

### 2.3 Why Reality alone is insufficient

Reality-only history creates hindsight. It can tell us the final production date, actual demand, realized price or eventual technology adoption, but it cannot tell us whether a historical actor had reason to expect that result at the time.

Without Expectation/Judgment, rationale, revision and `known_time`, the system cannot answer the key counterfactual question: “Standing on that date, with only information then available, what could a rational participant have believed?”

Longcycle therefore needs at least the separation:

```text
Reality
Expectation / Judgment
Outcome
Model Prior / Memory Atlas
```

The fourth layer is deliberately epistemically weaker: it discovers missing history but cannot become evidence by assertion.

### 2.4 What the lithium benchmark must prove

The lithium benchmark is successful only when a **real historical cycle can be replayed end to end from archived evidence** with Reality + Expectation + Outcome separated, temporal no-lookahead preserved, and core industrial trajectories semantically comparable.

The benchmark is not passed by reaching 600, 1,000 or 10,000 Memory Leads; not by schema richness; not by broad source coverage; and not by a good lithium report. It must demonstrate that the method can recover and replay historical cognition and reality well enough to expose useful cycle structure, and that the primitives are portable to a second industry.

Until that is demonstrated, generic platform expansion is subordinate to benchmark-driven needs.

### 2.5 Why Memory Atlas is a means rather than an end

The historical web is incomplete and keyword search is biased toward famous, still-indexed and currently named material. A strong model may retain vague actors, old names, failed projects, contract structures, mechanisms and contemporaneous narratives that ordinary search would never think to ask for.

The Memory Atlas therefore solves one specific problem: **coverage discovery before evidence collection**.

Its job is to reduce missing-history risk and produce high-value search leads. It is explicitly not a fact database. If the Atlas keeps growing without novelty-decay measurement, sealing, self-verification and evidence recovery, it stops serving the mission and becomes the next local optimum.

### 2.6 The two permanent collection routes

#### Historical recovery — Memory-first, Evidence-final

```text
blind high-capability memory exhaustion
→ saturation measurement
→ seal
→ high-capability self-verification/search discovery
→ claim-scoped evidence task packets
→ lower-capability evidence engineering
→ archive original source
→ Evidence / Assertion / Reconciliation
→ Reality / Expectation / Outcome
→ point-in-time replay
```

This route exists because old internet evidence is hard to recover and broad retrospective search misses important negative space.

#### Current collection — Source-first, Archive-now

```text
maintained source/watchlist
→ regular/event-triggered checks
→ immediate original/version archive
→ Reality / Judgment extraction
→ revision tracking
```

This route exists because material that is easy to obtain today may be difficult or impossible to recover later. Historical recovery and current collection solve different failure modes and cannot substitute for each other.

### 2.7 Planned role separation

- **High-capability model:** blind historical lead generator, cross-linker, alias/mechanism retriever, and — after seal — first self-verification/search researcher. It is a research instrument, not authority.
- **Lower-capability Agents:** explicit evidence engineers. They receive claim scope, aliases, query families, preferred sources, contradiction requirements, search depth and stop conditions. They do not autonomously publish broad industry conclusions.
- **Web search:** discovery mechanism for locating original evidence. Rank, snippets, repetition and syndication do not establish truth.
- **Original evidence:** the thing that can support Reality or source-attributed Judgment under claim-scoped authority and time semantics.

This separation is central: computational/model capability decides who is best at finding what to investigate, while original evidence decides what can be published as historical knowledge.

### 2.8 What happens after a shard seals

A sealed shard exits blind recall. The high-capability model then opens a distinct self-verification/search run, uses its own recalled aliases and associations to identify likely primary sources and sharpen claims, and compiles claim-scoped task packets. Lower-capability Agents then pursue those packets under explicit evidence/search-depth contracts. Original sources are archived and passed through the normal evidence/assertion/reconciliation path.

Skipping seal or allowing search to influence blind recall destroys the anti-anchoring boundary. Skipping high-model self-verification wastes the actor best positioned to interpret its own fuzzy recall.

### 2.9 What happens after the lithium benchmark works

After evidence-backed lithium point-in-time replay works, the project should extract **only the primitives demonstrated by the benchmark**, then validate portability on a second industry. Genericization is earned by observed cross-domain needs, not by speculative abstraction.

This is the point where reusable platform expansion becomes strategically justified: after the method has survived a real industry, not before.

### 2.10 What happens when a materially stronger model vintage arrives

A stronger high-capability model is treated as a new research instrument vintage. The project should rerun the fixed blind-memory process into a new immutable Atlas, diff it against prior vintages, classify leads as known/refined/novel, and turn new or refined leads into historical backfill tasks.

Older Atlas output — including identified false memories — is not overwritten. This preserves research provenance and lets Longcycle quantify how improved model vintages recover previously missing history.

### 2.11 Current immediate task and the next larger strategic step

There are three different horizons that must not be collapsed:

**Immediate task at this audit moment:** perform this genuine fresh-Agent strategic audit with report-only mutation. The checkpoint explicitly lists this as the second ordered action after refreshing live HEAD/CI.

**Immediate main-path work after this audit is reviewed:** stop optimizing handoff, return to the lithium Memory Atlas main path, rebuild/use compact indices, select high-value batch3 shards, run selective blind batch3 recall with `search_visibility=none`, and measure novelty decay using explicit classifications.

**Next larger strategic step after the current Memory Atlas phase:** seal the first genuinely saturated high-value shard(s), then transition to high-model self-verification/search discovery, claim-scoped delegated evidence engineering, original-source archival, and the first evidence-backed Reality/Expectation/Outcome historical replay.

The larger step is **not** “more batch3 forever”. Batch3 exists to earn the right to stop blind recall.

### 2.12 Locally reasonable but strategically wrong directions to reject

At least the following should be actively rejected unless a concrete blocker on the replay path changes the case:

1. build a generic crawler/RAG/agent platform ahead of real lithium replay needs;
2. start fresh web search on an unsealed shard because the current lead count feels large;
3. optimize Memory Lead count rather than saturation evidence and transition to Evidence;
4. keep refining schema/ontology without a real source or replay requirement;
5. make Ruff/lint/CI/handoff perfection the primary development roadmap after correctness is sufficient;
6. let low-cost Agents perform broad autonomous historical analysis and publish conclusions;
7. after seal, skip high-model self-verification and delegate vague searches directly;
8. treat lithium as the final vertical product instead of a benchmark for a reusable method;
9. postpone source-first/archive-now until historical recovery is “finished”;
10. infinitely deep-dive one company/material/project after marginal replay coverage gain has collapsed;
11. infer falsity from historical `not_found`;
12. overwrite raw recall, source versions, expectation revisions or prior model vintages to make the current state look cleaner.

## 3. Strategic hierarchy reconstruction

```text
H0 — end-state mission
Evidence-backed, replayable, cross-cycle industrial memory

↓ serves H0 by proving it on reality rather than architecture

H1 — first real benchmark
Lithium value chain: archived Reality + point-in-time Expectation + later Outcome + no-lookahead replay

↓ serves H1 by defining how missing old history and new incoming history are captured

H2 — permanent research/collection method
Historical: Memory-first, Evidence-final
Current: Source-first, Archive-now

↓ serves H2 by reducing historical negative space without contaminating recall

H3 — current strategic phase
Blind high-capability Memory Atlas exhaustion → novelty decay → saturation → seal

↓ serves H3 by establishing whether further recall still adds material categories

H4 — immediate main-path task
Deterministic compact indices → rank high-value batch3 candidates → selective blind batch3 → explicit novelty classification

↓ serves H4 by making saturation evidence auditable rather than intuitive

H5 — local implementation
Index builders, typed novelty records, validation, tests, CI contract checks, repair overlays and related code/data mechanics
```

The causal rule is strict: H5 is justified only insofar as it advances H4; H4 must help H3 reach a legitimate exit; H3 must transition into H2's evidence route; H2 must make H1 replay possible; H1 must prove H0.

This hierarchy is the strongest protection against successive Agents shrinking the planning horizon from “industrial replay” to “batch3” to “one index file” to “one lint warning”.

## 4. Adversarial drift test

### A. Build a generic crawler/RAG/agent platform for several weeks before finishing lithium historical replay

**Classification:** `accept_only_if_blocking_main_path`

A generic platform is not forbidden in principle, but the compass says infrastructure should be pulled by concrete benchmark needs. Weeks of generic platform work ahead of lithium replay is drift unless a missing platform capability is demonstrably blocking evidence-backed replay.

**Deciding principle:** lithium is the proof field; generic infrastructure must not outrun real benchmark requirements.

### B. Start fresh web self-verification now because 600+ Memory Leads feels sufficient

**Classification:** `reject`

No shard is sealed, all batch2 shards remain high-novelty under the current curated assessment, and the seal rule is explicit. Lead count is not the exit criterion. Search now would contaminate the blind-memory experiment.

**Deciding principle:** blind shard must seal before fresh search; saturation is measured, not felt.

### C. Keep increasing Memory Lead count indefinitely because more leads means more progress

**Classification:** `reject`

The Atlas is a coverage instrument. The objective is novelty decay → saturation → seal → evidence, not a larger counter. Infinite recall would turn a means into an endpoint.

**Deciding principle:** research quality/coverage transition over volume; Memory Atlas is not the product.

### D. Spend the next major development period making Ruff/CI/handoff perfect even though the correctness gate already protects the main path

**Classification:** `accept_only_if_blocking_main_path`

Live run #276 proves the hard gate is currently healthy: Mypy succeeds and 130 tests pass. Ruff remains diagnostic-only. Handoff work has just achieved the fresh-agent validation stage. Further major polishing is justified only if a real correctness/continuity defect blocks the benchmark.

**Deciding principle:** CI/handoff are support infrastructure, not the main research/product path.

### E. Let low-cost Agents independently research broad historical themes and publish industry conclusions

**Classification:** `reject`

This violates the planned orchestration and epistemic boundary. Lower-capability Agents are claim-scoped evidence engineers, not autonomous industry analysts.

**Deciding principle:** high model discovers/structures; low-cost Agents verify under explicit contracts; evidence supports publishable claims.

### F. After sealing, skip high-model self-verification and directly give vague tasks to low-cost Agents

**Classification:** `reject`

The constitution explicitly commits to high-capability self-verification/search first because that model best understands its own vague recall, aliases and cross-chain associations. Delegation follows a sharpened task packet.

**Deciding principle:** sealed recall → high-model self-verification → claim-scoped delegation.

### G. Treat lithium as the final domain-specific product rather than a benchmark for a reusable method

**Classification:** `reject`

Lithium is deliberately complex and familiar enough to force the right primitives. Benchmark success includes portability to a second industry.

**Deciding principle:** lithium is “证明场”, not terminal scope.

### H. Postpone current source-first/archive-now collection until all historical recovery is finished

**Classification:** `reject`

Historical recovery may dominate current execution, but source-first/archive-now is a permanent parallel track. Today's original sources are exactly the material that would otherwise become future historical gaps.

**Deciding principle:** historical recovery and current collection solve different temporal failure modes and cannot replace one another.

**Adversarial result:** `8/8` plans were correctly rejected or constrained.

## 5. Hidden-drift test

Question from the audit specification:

> If I execute the current ordered actions perfectly for several sessions, what observable milestone must eventually occur to prove I am still moving toward the product mission rather than merely becoming better at the current subproblem?

### Required observable milestone

A healthy continuation must eventually produce a **phase transition**, not merely higher counters or better tooling:

```text
selective batch3 novelty measurement
→ one or more high-value shards show repeated low novelty
→ negative-space/gap review finds no material uncovered dimension
→ shard seals
→ high-capability self-verification/search run begins
→ claim-scoped evidence task packets are produced
→ lower-capability Agents recover/archive original sources
→ Reality and historical Expectation/Judgment are evidence-backed
→ later Outcome is linked without hindsight leakage
→ at least one real historical snapshot can be replayed point-in-time
```

The strongest observable proof is therefore not “the Atlas reached N leads” or “the index is compact”. It is a **first evidence-backed no-lookahead replay** of a meaningful lithium historical slice, with original-source traceability and matched contemporaneous expectations versus later outcomes.

If several sessions improve Memory Atlas tooling but no shard moves toward a justified seal and no evidence/replay transition appears, that is hidden strategic drift even if every local task is completed correctly.

## 6. Is the project currently off course?

### Verdict: not materially off course, but at a high-risk transition boundary

I do **not** find current authoritative state to be materially off course.

Reasons:

- the strategic compass clearly defines the terminal replay mission;
- the constitution preserves the Reality/Expectation/Outcome and no-hindsight boundaries;
- lithium is explicitly framed as a benchmark, not a final vertical;
- the current Memory Atlas phase has a legitimate purpose: reduce historical negative space before search anchoring;
- batch2 results still show high novelty, so remaining in blind recall long enough to measure batch3 decay is supported by current evidence rather than inertia;
- the checkpoint explicitly defines a next big step beyond Memory Atlas;
- live CI is sufficient to protect the main path without demanding a lint-cleanup detour;
- the current ordered plan explicitly says to return to batch3 novelty-decay work after the genuine fresh-Agent audit/review.

However, the project is now at a boundary where drift would become easy. This strategic-audit/handoff work is justified as a finite continuity safeguard. **Continuing to optimize handoff, strategic tests, CI cosmetics or audit machinery after this report, absent a discovered blocking defect, would itself violate the compass.** The repository's own stop rule says the next coherent work should return to the main lithium path.

The Memory Atlas is also a latent drift risk. It is currently justified because no shard has yet shown low novelty, but its legitimacy depends on eventually producing saturation evidence and exiting into seal/evidence/replay.

## 7. Missing or ambiguous macro context

The macro direction is recoverable, but several important operational thresholds remain intentionally or accidentally under-specified:

1. **Low-novelty threshold is not quantitatively fixed.** The repository defines `new_category/useful_refinement/duplicate` and requires three consecutive low-novelty batches, but the quantitative threshold for “low” remains an unresolved question in the checkpoint.
2. **Batch3 shard selection is unresolved.** The checkpoint asks which 3–5 shards should enter first, ranked by importance and unresolved gap density. This is execution ambiguity, not mission ambiguity.
3. **First canonical replay slice is not fixed.** The compass gives `2022-06-30` as an illustrative acceptance point and the lithium plan lists historical snapshots, but there is no single committed “first replay fixture” with exact pass/fail completeness metrics.
4. **Benchmark completion lacks a quantitative sufficiency threshold.** The seven benchmark properties are strong qualitatively, but “good enough to say lithium works” is not yet expressed as a measurable coverage/replay acceptance rubric.
5. **Current-collection activation timing is unresolved.** Source-first/archive-now is a permanent commitment, but the checkpoint explicitly asks when it should move from documented commitment into active scheduled collection without distracting from the first replay.
6. **“Materially stronger model vintage” is qualitative.** The action on a stronger model is clear, but the trigger threshold for when a model upgrade is material enough to justify a full new blind vintage is not formalized.
7. **Second-industry choice is intentionally open.** Portability to a second industry is required for benchmark success/generalization, but the second industry and selection criteria are not yet committed.
8. **Primitive extraction gate after lithium is qualitative.** The compass says to extract only primitives proven by real data, but a formal rule for distinguishing reusable primitive from lithium-specific special case is not yet defined.

None of these ambiguities prevents recovery of the macro mission or the next larger phase. They should be resolved by benchmark evidence at the appropriate phase, not by premature abstraction now.

## 8. Evidence hierarchy used in this audit

I treated repository evidence in the following classes, rather than flattening all Markdown/JSON into equal truth:

1. **Explicit founder/user directive:** preserved quotes in `STRATEGIC_COMPASS.md`, constitution and checkpoint; controls durable intent.
2. **Strategic compass / constitution:** defines product mission, benchmark, permanent method, invariants and anti-drift rules.
3. **Live execution state:** live PR HEAD/commit graph and live GitHub Actions; controls current implementation facts.
4. **Canonical/deterministic-derived campaign state:** raw-derived lead counts, typed reconstruction and coverage index counts.
5. **Curated research assessment:** novelty labels, gap/priority judgments and interpretations; useful but not mechanically proven.
6. **Narrative:** PR description, README and devlogs; used for rationale/corroboration but not allowed to override higher-authority live or strategic sources.
7. **My inference:** conclusions in this report that connect those artifacts. Where the repository leaves a threshold open, I mark it as ambiguity rather than silently inventing a rule.

## 9. Final strategic understanding

The shortest faithful reconstruction is:

> Longcycle exists to preserve enough trustworthy, semantically comparable and point-in-time faithful industrial history that a user can replay a past cycle from inside the information set available then, compare contemporaneous expectations with later outcomes, and use long-cycle common-sense reasoning to see risks and opportunities. Lithium is the first proof field for that method. The Memory Atlas is only a missing-history discovery device. Historical recovery permanently follows memory-first/evidence-final; current material permanently follows source-first/archive-now. The present work should measure recall saturation, seal only when earned, then deliberately leave the Atlas and enter high-model self-verification, delegated evidence engineering, original-source archival and actual Reality/Expectation/Outcome replay. After lithium works, extract only proven reusable primitives and validate them on a second industry; when materially stronger model vintages arrive, rerun immutable blind memory and backfill newly recovered history. Any Agent that turns lead count, generic platform engineering, schema perfection, CI/handoff polish or lithium-specific depth into the objective has confused a tool for the mission.

## 10. Audit verdict

- `macro_direction_reconstruction`: complete
- `understands_memory_atlas_is_a_means`: yes
- `understands_lithium_is_a_benchmark`: yes
- `understands_next_larger_step`: yes
- `rejects_local_optima`: 8/8
- `safe_for_multi_agent_continuation`: yes
- `strategic_context_missing_or_ambiguous`:
  - quantitative low-novelty threshold / classification rubric
  - first 3–5 batch3 shard priority
  - canonical first replay slice and quantitative replay-completeness gate
  - exact lithium-benchmark “good enough” acceptance rubric
  - timing for activating scheduled source-first/archive-now current collection
  - threshold for a “materially stronger” model vintage
  - second-industry selection
  - formal reusable-primitive extraction gate after lithium
- `operations_performed`: report file only

## 11. Audit-specific stop instruction to the next Agent

This report itself must not become a new branch of work. The repository has now performed the genuinely fresh strategic audit it asked for. Unless review of this report reveals a real steering defect that blocks continuity, the next development/research sessions should **not** keep polishing the audit/handoff system. They should return to the main path recorded in the checkpoint: compact indices → selective blind batch3 novelty-decay measurement → legitimate saturation/seal → self-verification/evidence → first real historical replay.
