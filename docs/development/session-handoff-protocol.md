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
- the exact next executable actions.

This protocol preserves decisions and execution state. It does not attempt to preserve private model chain-of-thought. Durable rationale must be written as explicit, reviewable engineering reasoning.

## 2. Four continuity layers

### Layer A — Constitution

`docs/development/project-constitution.md`

Slow-changing project intent and non-negotiable epistemic rules. It should contain important user directives, including exact quotes where wording matters. It changes only when the project direction actually changes.

### Layer B — Live checkpoint

`.longcycle/handoff/current.json`

Fast-changing, machine-readable state. It contains active workstreams, campaign counters, CI snapshot, pending actions, forbidden shortcuts and the minimal read set required to resume.

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
1. Open CONTINUE_HERE.md.
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

## 4. The self-reference rule

A committed checkpoint cannot truthfully contain the SHA of the commit that contains itself without a circular reference.

Therefore `current.json` stores:

```text
checkpoint_based_on_head_sha
live_refresh_required = true
```

`checkpoint_based_on_head_sha` is the repository HEAD inspected immediately **before** the checkpoint write. A new session must fetch the live HEAD and reconcile every commit after that SHA.

This is intentional. Never “fix” it by pretending the checkpoint SHA is the current HEAD.

## 5. Freshness classes

Information in the checkpoint is tagged conceptually as one of:

- **constitutional** — slow-changing intent/invariants;
- **snapshot** — CI counts, lead counts, active errors; must be refreshed from live sources;
- **ordered plan** — current next actions; may be superseded by commits or user instructions;
- **hard guardrail** — e.g. no fresh search before a blind shard is sealed.

CI state is always `snapshot_not_authoritative`. A fresh session must never repeat an old green/red status without checking the live run.

## 6. Checkpoint update policy

Update `.longcycle/handoff/current.json` after any meaningful change to one of:

- project direction or user directive;
- active branch / PR;
- research phase or search visibility;
- campaign lead counts or shard sealing;
- CI correctness state;
- ordered next actions;
- known blockers or forbidden actions.

For long bursts of repetitive data generation, checkpoint after a coherent batch rather than after every single lead.

Before voluntarily ending a long development session, write a final checkpoint even if no code changed.

## 7. Preserve wording that controls behavior

When a user sentence materially constrains the project, preserve the exact quote in the constitution/checkpoint rather than paraphrasing it away.

Examples for the current Longcycle work include:

> “把整个行业相关的最关键和真实的历史保存下来，拉长时间去看，其实不用太多分析也能用简单常识分析出当下的风险与机遇”

> “缺的是人站在当时的判断和预期。”

> “聊天轮次多了以后就会被切断当前聊天对话框，必须开新的，设计套系统如何让新开聊天系统能实时跟上开发进度，保证原汁原味执行我们的计划和任务”

These are durable product/execution requirements, not decorative quotations.

## 8. Handoff must not smuggle model memory into evidence

Session continuity does not weaken Longcycle’s epistemic boundaries.

For the current lithium Memory Atlas campaign:

- blind model memory remains unsourced search leads;
- fresh web search remains forbidden until the relevant blind shard is sealed;
- a handoff file cannot promote a Memory Lead into Evidence, Fact or Judgment;
- historical `not_found != false` still applies;
- raw model recall artifacts remain immutable; structural repair uses explicit overlays.

A new chat must inherit these constraints before continuing research.

## 9. Minimal-resume principle

Do not reload the entire repository or hundreds of raw Memory Lead records into a fresh chat.

Start with the checkpoint’s `resume_read_set`, compact indices and current failure/output files. Expand only when necessary. This preserves context capacity for actual development and research.

## 10. Failure modes this protocol is designed to prevent

- stale chat summary says CI is green when current HEAD is red;
- a fresh session starts web search before blind recall is sealed;
- a new model treats old Memory Leads as verified history;
- the user has to explain the project from scratch;
- repeated broad recall replaces the planned novelty-decay process;
- a later session silently changes a settled schema principle;
- current.json becomes a manually curated story that disagrees with Git history.

The remedy is always the same: live repository state + typed checkpoint + append-only rationale + explicit user directives.