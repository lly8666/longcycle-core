# Longcycle Session Handoff Protocol

## 1. Why this exists

A development conversation can end because a chat window reaches its practical context limit. Longcycle must not depend on one conversation retaining all prior context.

The continuity source of truth is therefore the repository, not chat memory.

A fresh session must be able to recover:

- what the user is trying to build;
- the exact constraints and decisions already agreed;
- the current branch / PR / CI state;
- what work is in progress;
- what must not be done yet;
- why important decisions were made;
- the exact next executable actions;
- future phase commitments that must remain true even if the current session has not reached them yet.

This protocol preserves decisions and execution state. It does not attempt to preserve private model chain-of-thought. Durable rationale must be written as explicit, reviewable engineering reasoning.

## 2. Four continuity layers

### Layer A — Constitution

`docs/development/project-constitution.md`

Slow-changing project intent and non-negotiable epistemic rules. It should contain important user directives, including exact quotes where wording matters. It changes only when the project direction actually changes.

### Layer B — Live checkpoint

`.longcycle/handoff/current.json`

Fast-changing, machine-readable state. It contains active workstreams, campaign counters, CI snapshot, pending actions, forbidden shortcuts, future phase commitments and the minimal read set required to resume.

The checkpoint is a **snapshot**, never proof of current repository state.

### Layer C — Append-only rationale/history

`docs/devlog/` and optional `.longcycle/handoff/history/` artifacts.

Use this layer to record what changed, what was observed, why a decision changed and what remains unresolved. Do not rewrite history to make the current plan look inevitable.

### Layer D — Bootstrap entry points

`CONTINUE_HERE.md` and root `AGENTS.md`.

These provide a stable rendezvous point for a new chat or coding agent.

## 3. Fresh-session bootstrap algorithm

A fresh session receiving a request such as “继续 Longcycle” must execute this order before making substantive changes:

```text
1. Open CONTINUE_HERE.md, or locate the active branch through GitHub issue #2 when the bootstrap file is not on the default branch.
2. Fetch the active PR / branch live state from GitHub.
3. Read .longcycle/handoff/current.json.
4. Read docs/development/project-constitution.md.
5. Read only the checkpoint resume_read_set plus any files needed for the immediate task.
6. Compare live HEAD with checkpoint_based_on_head_sha.
7. If they differ, inspect/reconcile the intervening commits before trusting checkpoint counters or CI.
8. Fetch the latest CI for the live HEAD (or newest relevant PR run).
9. Correct stale checkpoint assumptions in working memory.
10. Continue the ordered next_actions without asking the user to repeat already-recorded context.
```

If repository state contradicts an older chat summary, repository state wins for implementation facts. If a newer explicit user directive contradicts the constitution, the user directive wins and the constitution/checkpoint must be updated.

## 4. The self-reference and provenance rule

A committed checkpoint cannot truthfully contain the SHA of the commit that contains itself without a circular reference.

Therefore `current.json` stores:

```text
checkpoint_based_on_head_sha
live_refresh_required = true
provenance_ordering = git_commit_graph
```

`checkpoint_based_on_head_sha` is the repository HEAD inspected immediately **before** the checkpoint write. A new session must fetch the live HEAD and reconcile every commit after that SHA.

Repository ordering is established by the Git commit graph, not by a manually entered checkpoint timestamp. Do not add or trust a hand-written checkpoint time as an ordering authority.

This is intentional. Never “fix” self-reference by pretending the checkpoint SHA is the current HEAD.

## 5. State authority classes

A fresh session must distinguish four kinds of recovered state instead of presenting all repository text as equally authoritative:

- **canonical / immutable** — Git commit graph, raw blind JSONL, archived original evidence, explicit user directives;
- **deterministic-derived** — raw lead counts, typed validation/index output, machine-reconstructed coverage, live CI outcomes;
- **curated research assessment** — novelty labels, gap severity, semantic importance, “6/6 new/useful”, proposed bridge/satellite promotion and similar human/model research judgments;
- **narrative** — PR descriptions, README summaries and devlog prose that explain state but may lag fast-moving machine state.

Never describe a curated assessment as mechanically proven merely because it is stored in JSON. Never let a stale narrative override canonical or deterministic-derived state.

## 6. Freshness classes

Information in the checkpoint is tagged conceptually as one of:

- **constitutional** — slow-changing intent/invariants;
- **snapshot** — CI counts, lead counts, active errors; must be refreshed from live sources;
- **ordered plan** — current next actions; may be superseded by commits or user instructions;
- **hard guardrail** — e.g. no fresh search before a blind shard is sealed;
- **future phase commitment** — an already-agreed method that must become active when its phase arrives, even if it is not part of today's immediate read set.

CI state is always `snapshot_not_authoritative`. A fresh session must never repeat an old green/red status without checking the live run.

## 7. Checkpoint update policy

Update `.longcycle/handoff/current.json` after any meaningful change to one of:

- project direction or user directive;
- active branch / PR;
- research phase or search visibility;
- campaign lead counts or shard sealing;
- CI correctness state;
- ordered next actions;
- known blockers or forbidden actions;
- future phase commitments.

For long bursts of repetitive data generation, checkpoint after a coherent batch rather than after every single lead.

Before voluntarily ending a long development session, write a final checkpoint even if no code changed.

## 8. Preserve wording that controls behavior

When a user sentence materially constrains the project, preserve the exact quote in the constitution/checkpoint rather than paraphrasing it away.

Examples for the current Longcycle work include:

> “把整个行业相关的最关键和真实的历史保存下来，拉长时间去看，其实不用太多分析也能用简单常识分析出当下的风险与机遇”

> “缺的是人站在当时的判断和预期。”

> “聊天轮次多了以后就会被切断当前聊天对话框，必须开新的，设计套系统如何让新开聊天系统能实时跟上开发进度，保证原汁原味执行我们的计划和任务”

These are durable product/execution requirements, not decorative quotations.

## 9. Phase-transition re-bootstrap

The minimal read set is intentionally small during routine continuation. That must not erase decisions needed in later phases.

Before crossing a major phase boundary, the active session must re-read the constitution plus the phase-specific research contracts relevant to that transition. In particular, it must recover these durable commitments:

- blind memory exhaustion precedes fresh search;
- after a shard seals, the high-capability model performs the first self-verification/search pass before lower-capability evidence agents are delegated work;
- lower-capability agents follow explicit evidence/search-depth contracts and do not become free-form analysts;
- current collection remains source-first/archive-now;
- model-vintage upgrades create a new immutable Memory Atlas vintage and historical backfill diff rather than overwriting old recall;
- bridge/satellite promotion depends on repeated independent triggers rather than a single shard tangent.

A phase transition is therefore a deliberate context expansion point, not a reason to preload every historical document into every session.

## 10. Handoff must not smuggle model memory into evidence

Session continuity does not weaken Longcycle’s epistemic boundaries.

For the current lithium Memory Atlas campaign:

- blind model memory remains unsourced search leads;
- fresh web search remains forbidden until the relevant blind shard is sealed;
- a handoff file cannot promote a Memory Lead into Evidence, Fact or Judgment;
- historical `not_found != false` still applies;
- raw model recall artifacts remain immutable; structural repair uses explicit overlays.

A new chat must inherit these constraints before continuing research.

## 11. Minimal-resume principle

Do not reload the entire repository or hundreds of raw Memory Lead records into a fresh chat.

Start with the checkpoint’s `resume_read_set`, compact indices and current failure/output files. Expand only when necessary. This preserves context capacity for actual development and research.

## 12. Failure modes this protocol is designed to prevent

- stale chat summary says CI is green when current HEAD is red;
- a fresh session starts web search before blind recall is sealed;
- a new model treats old Memory Leads as verified history;
- the user has to explain the project from scratch;
- repeated broad recall replaces the planned novelty-decay process;
- a later session silently changes a settled schema principle;
- current.json becomes a manually curated story that disagrees with Git history;
- PR/README prose becomes a second live-state store;
- a curated research judgment is accidentally treated as deterministic fact;
- a later phase forgets an already-agreed orchestration rule because that rule was not part of the immediate checkpoint read set.

The remedy is always the same: live repository state + typed checkpoint + explicit state authority + append-only rationale + explicit user directives.
