# Longcycle Session Handoff Protocol

## 1. Why this exists

A development conversation can end because a chat window reaches its practical context limit. Longcycle must not depend on one conversation retaining all prior context.

The continuity source of truth is therefore the repository, not chat memory.

A fresh session must recover **two planes** before it acts:

- **strategic plane** — what the user is fundamentally trying to build, what the first real benchmark must prove, what is merely a tool, and what larger phase comes after the current one;
- **execution plane** — active branch / PR / CI state, current workstream, blockers, counters and exact next actions.

Recovering execution state without strategic direction is an incomplete handoff. It creates an Agent that can resume the last screw being tightened while forgetting what ship is being built.

This protocol preserves decisions and execution state. It does not attempt to preserve private model chain-of-thought. Durable rationale must be written as explicit, reviewable engineering reasoning.

## 2. Five continuity layers

### Layer 0 — Strategic compass

`STRATEGIC_COMPASS.md`

The cross-Agent steering layer. It records the end-state mission, lithium benchmark success criteria, means-vs-ends distinctions, anti-drift rules, major-phase direction and the Strategic Alignment Gate.

It must not duplicate fast-changing counts or CI state.

### Layer A — Constitution

`docs/development/project-constitution.md`

Slow-changing product intent and non-negotiable epistemic rules. It should contain important user directives, including exact quotes where wording matters. It changes only when the project direction actually changes.

### Layer B — Live checkpoint

`.longcycle/handoff/current.json`

Fast-changing, machine-readable state. It contains active workstreams, campaign counters, CI snapshot, pending actions, forbidden shortcuts, future phase commitments and the minimal read set required to resume.

The checkpoint is a **snapshot**, never proof of current repository state and never permission to override the strategic compass.

### Layer C — Append-only rationale/history

`docs/devlog/` and optional `.longcycle/handoff/history/` artifacts.

Use this layer to record what changed, what was observed, why a decision changed and what remains unresolved. Do not rewrite history to make the current plan look inevitable.

### Layer D — Bootstrap entry points

`CONTINUE_HERE.md`, root `AGENTS.md`, and GitHub issue #2.

These provide a stable rendezvous point for a new chat or coding agent.

## 3. Fresh-session bootstrap algorithm

A fresh session receiving a request such as “继续 Longcycle” must execute this order before making substantive changes:

```text
1. Use issue #2 / live GitHub to resolve the active PR and branch.
2. Read STRATEGIC_COMPASS.md.
3. Read docs/development/project-constitution.md.
4. Read .longcycle/handoff/current.json.
5. Read CONTINUE_HERE.md and this protocol.
6. Fetch live HEAD and compare with checkpoint_based_on_head_sha.
7. If they differ, inspect/reconcile intervening commits before trusting checkpoint counters or CI.
8. Fetch the latest CI for the live HEAD / relevant PR merge result.
9. Read only the checkpoint resume_read_set plus files required for the immediate task.
10. Pass the Strategic Alignment Gate.
11. Continue ordered_next_actions only if they still serve the strategic hierarchy.
```

A fresh session must be able to explain not only “what is next?” but also “why is that next?” and “what larger step follows it?”.

## 4. Two authority planes

Do not use one precedence order for both strategy and implementation state.

### Strategy / direction precedence

```text
new explicit user instruction
> STRATEGIC_COMPASS.md
> project constitution and durable research commitments
> current handoff ordered plan
> devlogs / old chat summaries
```

A local implementation convenience cannot silently rewrite the mission.

### Implementation / freshness precedence

```text
live GitHub commit graph / HEAD / live CI
> canonical or deterministic-derived repository artifacts
> current handoff snapshot
> curated research assessments
> PR/README/devlog narrative
> old chat summaries
```

A strategic document cannot claim CI is green; a live commit cannot by itself redefine product direction.

## 5. Strategic Alignment Gate

Before a fresh session makes substantive changes, and again at major phase transitions or after a long locally focused batch, it must recover from repository evidence:

1. the Longcycle end-state mission;
2. the first-principles success criterion for the lithium benchmark;
3. the current phase's position between Memory Atlas and point-in-time Reality/Expectation/Outcome replay;
4. why the immediate action advances that benchmark rather than only polishing a tool;
5. whether skipping the action would block the main path;
6. a more direct alternative, if one exists;
7. the next larger strategic phase after the immediate work.

If those answers are weak, do not blindly execute the TODO. Re-rank the work using `STRATEGIC_COMPASS.md`.

## 6. Local-optimum / drift rule

A technically valid action is not automatically a strategically valid action.

Strong drift signals include:

- generic platform work running far ahead of needs exposed by the lithium benchmark;
- Memory Lead volume becoming the objective instead of coverage → saturation → evidence;
- endless ontology/schema refinement without a real source or replay requirement;
- CI/lint/handoff refinement consuming the main research roadmap after correctness is already sufficient;
- deep work on one actor/material that no longer improves whole-cycle replay;
- historical recovery forgetting current source-first/archive-now collection;
- lithium-specific implementation being mistaken for the final product.

When a drift signal appears, stop expanding the local task and write/recover the task-to-strategy chain before proceeding.

## 7. The self-reference and provenance rule

A committed checkpoint cannot truthfully contain the SHA of the commit that contains itself without a circular reference.

Therefore `current.json` stores:

```text
checkpoint_based_on_head_sha
live_refresh_required = true
provenance_ordering = git_commit_graph
```

`checkpoint_based_on_head_sha` is the repository HEAD inspected immediately **before** the checkpoint write. A new session must fetch the live HEAD and reconcile every commit after that SHA.

Repository ordering is established by the Git commit graph, not by a manually entered checkpoint timestamp.

## 8. State authority classes

A fresh session must distinguish recovered state instead of presenting all repository text as equally authoritative:

- **canonical / immutable** — Git commit graph, raw blind JSONL, archived original evidence, explicit user directives;
- **deterministic-derived** — raw lead counts, typed validation/index output, machine-reconstructed coverage, live CI outcomes;
- **curated research assessment** — novelty labels, gap severity, semantic importance, proposed bridge/satellite promotion;
- **snapshot** — checkpoint CI observations and similar fast state, always refresh;
- **narrative** — PR descriptions, README summaries and devlog prose.

Never describe a curated assessment as mechanically proven merely because it is stored in JSON.

## 9. Checkpoint update policy

Update `.longcycle/handoff/current.json` after any meaningful change to project direction, active branch / PR, research phase, search visibility, campaign counts/seals, CI correctness, ordered next actions, blockers, forbidden actions or future phase commitments.

For long repetitive generation, checkpoint after a coherent batch rather than every lead.

The checkpoint `resume_read_set` must include `STRATEGIC_COMPASS.md`; context economy may remove detail, not the steering layer.

## 10. Preserve wording that controls behavior

When a user sentence materially constrains the project, preserve the exact quote in the compass/constitution/checkpoint rather than paraphrasing it away.

Examples include:

> “把整个行业相关的最关键和真实的历史保存下来，拉长时间去看，其实不用太多分析也能用简单常识分析出当下的风险与机遇”

> “缺的是人站在当时的判断和预期。”

> “聊天轮次多了以后就会被切断当前聊天对话框，必须开新的，设计套系统如何让新开聊天系统能实时跟上开发进度，保证原汁原味执行我们的计划和任务”

> “大海航行靠舵手……永远不要偏离航向。”

These are durable product/execution requirements, not decorative quotations.

## 11. Phase-transition re-bootstrap

The minimal read set is intentionally small during routine continuation. That must not erase decisions needed in later phases.

Before crossing a major phase boundary, the active session must re-read `STRATEGIC_COMPASS.md`, the constitution and the relevant phase-specific research contracts.

Durable commitments include:

- blind memory exhaustion precedes fresh search;
- after a shard seals, the high-capability model performs the first self-verification/search pass before lower-capability evidence agents are delegated work;
- lower-capability agents follow explicit evidence/search-depth contracts and do not become free-form analysts;
- current collection remains source-first/archive-now;
- model-vintage upgrades create a new immutable Memory Atlas vintage and historical backfill diff rather than overwriting old recall;
- bridge/satellite promotion depends on repeated independent triggers rather than a single shard tangent.

## 12. Handoff must not smuggle model memory into evidence

Session continuity does not weaken Longcycle’s epistemic boundaries.

For the current lithium Memory Atlas campaign:

- blind model memory remains unsourced search leads;
- fresh web search remains forbidden until the relevant blind shard is sealed;
- a handoff file cannot promote a Memory Lead into Evidence, Fact or Judgment;
- historical `not_found != false` still applies;
- raw model recall artifacts remain immutable; structural repair uses explicit overlays.

## 13. Minimal-resume principle

Do not reload the entire repository or hundreds of raw Memory Lead records into a fresh chat.

Start with `STRATEGIC_COMPASS.md`, the constitution, the checkpoint `resume_read_set`, compact indices and current failure/output files. Expand only when necessary.

## 14. Strategy change rule

A subsequent Agent must not silently mutate the compass because a different architecture feels cleaner.

A strategic change requires at least one of:

1. a newer explicit user directive;
2. a real benchmark result that falsifies an important assumption;
3. strong new evidence that the route cannot achieve the stated mission.

The change must be explicit in Git history/devlog, and affected constitution/checkpoint commitments must be updated. Local implementation friction is not sufficient evidence for a strategic pivot.

## 15. Failure modes this protocol is designed to prevent

- a fresh session resumes the exact TODO but forgets what product is being built;
- stale chat summary says CI is green when current HEAD is red;
- a fresh session starts web search before blind recall is sealed;
- a new model treats old Memory Leads as verified history;
- the user has to explain the project from scratch;
- repeated broad recall replaces the planned novelty-decay process;
- a later session silently changes a settled schema or research principle;
- a chain of agents optimizes crawler/CI/schema/handoff while never reaching historical replay;
- current.json becomes a manually curated story that disagrees with Git history.

The remedy is: **strategic compass + live repository state + typed checkpoint + append-only rationale + explicit user directives.**