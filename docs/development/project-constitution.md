# Longcycle Project Constitution

This file preserves slow-changing project intent and non-negotiable execution rules so a new session can resume without reconstructing the project from chat history.

## Product north star

Longcycle exists to preserve the most important and trustworthy history of an industry over long time spans, with enough semantic fidelity that simple common-sense comparison across cycles becomes useful.

User directive:

> “把整个行业相关的最关键和真实的历史保存下来，拉长时间去看，其实不用太多分析也能用简单常识分析出当下的风险与机遇”

The product thesis is:

> **历史本身就是分析。**

Longcycle is not primarily a crawler, generic RAG system, report generator or short-horizon prediction engine. It is an evidence-backed, replayable industrial memory.

## Reality is not enough

User directive:

> “缺的是人站在当时的判断和预期。”

Longcycle must preserve both:

1. what actually happened;
2. what actors believed, expected, feared, planned or assumed at each historical point.

The system should make it possible to ask both:

- “现在回头看，2024 年真实发生了什么？”
- “站在 2024 年当时，我们能知道什么、相信什么、预期什么？”

The second query must not leak information published later.

## Core epistemic layers

- **Reality** — evidence-backed claims about what happened or was true.
- **Expectation / Judgment** — source-attributed historical beliefs, forecasts, plans, targets, interpretations and risk judgments.
- **Outcome** — later realized state used to evaluate prior expectations.
- **Model Prior / Memory Atlas** — unsourced model recollection or inference used only to discover what should be researched.

A strong model memory is not Evidence. A Memory Lead can challenge the archive and trigger search, but cannot publish or overwrite a Fact or Judgment.

## Historical recovery rule

Historical recovery is:

```text
blind high-capability memory exhaustion
→ seal
→ high-capability self-verification/search discovery
→ delegated claim-scoped evidence search
→ archive original source
→ normal Evidence / Assertion / Reconciliation pipeline
```

Fresh search must not contaminate an unsealed blind shard.

`not_found != false`: inability to recover a historical source is not evidence that the event or claim was false.

## Current collection rule

Current collection is source-first and archive-now. Material that exists today should be archived proactively instead of becoming a future historical-recovery problem.

Preserve original versions and later revisions; never overwrite history with the newest understanding.

## Time semantics

Preserve at least the distinction between:

- `valid_time`: when a statement applies or an event occurred in the world;
- `known_time`: when the information became knowable to Longcycle / the historical observer.

For expectations also preserve the future period being forecast. `known_at` and `forecast_for` are not interchangeable.

The system must support point-in-time replay: standing at a past date, the future should become uncertain again.

## Comparability before quantity

Long histories are useless if semantically incomparable observations are merged.

Durable rules include:

```text
capacity != one number
price != one curve
inventory != one stock
sales != demand
project announced != supply
technology announced != adoption
```

Units, product specification, geography, market/contract basis, tax/freight boundary, statistical scope, valid time, project state and qualification state matter before corroboration or conflict logic.

## Preserve trajectories, not only endpoints

For projects and technology adoption, preserve state transitions such as:

```text
announce
→ approve
→ finance / FID
→ construction
→ first production
→ qualification / commissioning
→ ramp
→ commercial / full operation
```

and failure/revision states such as delay, suspend, cancel, impairment, redesign, restart and missed guidance.

A later actual date must not erase earlier promised dates.

## Stated belief and revealed belief

What actors do can reveal beliefs more strongly than what they say. Longcycle should eventually connect:

```text
belief / expectation
→ action / commitment
→ realized outcome
```

Examples of actions include capex approval, inventory build, contracts, financing, hedging, buybacks and shutdowns.

## Research quality over volume

Prefer fewer deeply traceable, comparable and replayable trajectories over a large pile of shallow snippets.

Search rank, repeated syndication, snippet count and web popularity do not establish truth. Source authority is claim-scoped.

## Model-vintage rule

A new or materially improved high-capability model is a new research instrument vintage. Do not overwrite older Memory Atlas output. Diff the new vintage against the old one and use novel/refined leads to reopen historical gaps.

False memories are also retained as historical model-output artifacts after they are identified; they are not silently deleted.

## Research orchestration commitments

These execution choices are part of the product method and must survive session changes even when the current workstream has not reached them yet:

- Historical recovery is **memory-first, evidence-final**: a high-capability model first builds and exhausts a Memory Atlas before claim-scoped evidence collection begins.
- A shard must seal before fresh search touches it. After sealing, the high-capability model should perform the first self-verification/search pass because it best understands its own vague recollections, aliases and cross-chain associations.
- Bounded/lower-cost agents default to evidence engineering. They receive explicit Memory Leads, source targets, contradiction queries and stop conditions, and they do not acquire authority merely by producing fluent prose. They **may** perform deterministic local reasoning, propose clearly labelled research candidates/hypotheses, refine queries and flag possible cross-links when useful. Those outputs remain research aids, not canonical Reality/Judgment or final high-impact industry conclusions; genuinely ambiguous high-impact synthesis must escalate to an appropriate reasoning/review tier. Missing search results never become falsity.
- Fragmentary Memory Leads may enter the Atlas before their delegated-search plan is complete. Search/delegation readiness is a later execution boundary, not an admission requirement for preserving a useful unsourced recollection.
- Search-depth defaults prevent premature `not_found`/exhaustion claims; they are not query/source-count quotas after claim-scoped authoritative content already resolves a claim.
- Cross-chain topology should emerge from independently recalled shard triggers. Repeated independent bridge/satellite triggers may promote a topic; one model tangent should not explode the task graph.
- Current collection is **source-first, archive-now** and follows a maintained source/watchlist discipline rather than retrospective broad search.
- When a stronger model vintage becomes available, rerun blind memory extraction as a new immutable vintage, diff it against prior atlases and create backfill tasks from novel/refined leads instead of overwriting old model output.

## Session continuity requirement

User directive:

> “聊天轮次多了以后就会被切断当前聊天对话框，必须开新的，设计套系统如何让新开聊天系统能实时跟上开发进度，保证原汁原味执行我们的计划和任务”

Therefore development continuity is repository-backed. A fresh chat must bootstrap from `CONTINUE_HERE.md` and `.longcycle/handoff/current.json`, refresh live HEAD/CI, reconcile any delta, and continue recorded next actions without asking the user to restate context already persisted here.

The repository preserves explicit decisions and rationale, not private model chain-of-thought.
