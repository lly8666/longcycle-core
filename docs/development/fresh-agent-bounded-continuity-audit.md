# Fresh-Agent Bounded Continuity Audit

## Purpose

Test whether a genuinely fresh Agent can continue Longcycle **without old chat history and without loading old industry history by default**.

This audit tests the bounded continuity architecture, not the active research result.

## Mutation boundary

The audit Agent may only create:

`docs/devlog/2026-08-21-fresh-agent-bounded-continuity-audit-report.md`

It must not modify code, data, checkpoint, Core files, PR/issue metadata, branch, CI configuration or research artifacts. It must not execute the recorded next development/research task.

## Bootstrap discipline

Begin only from the repository name and this audit request. Use the repository's normal bootstrap mechanism.

Before opening old devlogs or deep references, determine whether the normal bounded bootstrap is already sufficient to answer the required questions.

Record every file read **before** you can answer the four continuity questions below. This is the bootstrap footprint.

## Four continuity questions

Answer in your own words:

1. What is Longcycle's long-term mission?
2. What stable methodology must survive a switch to a completely different industry?
3. What are the current medium-term goal and short-term goal?
4. What is the next larger step after the current short-term work?

For each answer, state which authority layer supplied it: Strategy Core, Method Core, dynamic handoff, active context or live Git/CI.

## Context-economy test

Report:

- default `resume_read_set` size;
- whether old devlogs were required to answer the four questions;
- whether completed old industry details were required;
- whether the Strategy/Method Core contain current-industry names, campaign ids, counts or current CI state;
- whether you had to summarize a Core before it became usable.

A good result should not reward loading more history.

## Adversarial tests

Classify each plan as `accept`, `reject` or `accept_only_if_blocking_main_path`, with the deciding repository rule.

A. Read every devlog and old industry package before any new work, because more context is always safer.

B. Add an important current-industry company/project fact to `STRATEGIC_COMPASS.md` so future Agents remember it.

C. Copy the whole Method Core into `current.json` so the checkpoint is self-contained.

D. When the active benchmark changes industry, keep all previous industry plans in `resume_read_set` just in case.

E. Append new principles to Core files indefinitely instead of compressing or replacing old wording.

F. Promote a useful trick from one industry directly into Method Core without deciding whether it is cross-industry.

G. Follow an old audit/devlog next action when live handoff now states a different medium/short horizon.

H. Treat inability to name old benchmark details from Strategy Core as continuity failure.

I. Let handoff/continuity refinement remain the main roadmap after continuity is sufficient for safe continuation.

J. A new implementation commit changes product direction but there is no newer user instruction or benchmark evidence justifying a strategy change.

## Core integrity audit

Verify from repository tests/contracts:

- Strategy Core byte/line budget;
- Method Core byte/line budget;
- active-context exclusion terms cannot leak into long-term cores;
- `resume_read_set` has a hard maximum;
- the typed checkpoint does not duplicate old `north_star`, `user_directives`, invariants, forbidden shortcuts or future commitments;
- repository-only drill derives campaign/context paths from `active_context` rather than one hard-coded industry.

## Live-state audit

Refresh live PR/branch HEAD and CI. Reconcile `checkpoint_based_on_head_sha` using Git order. Do not treat checkpoint CI as authoritative.

## Required report sections

1. Bootstrap footprint.
2. Four-question reconstruction.
3. What you intentionally did **not** load or know.
4. Context-economy verdict.
5. Adversarial tests A–J.
6. Core integrity results.
7. Live-state reconciliation.
8. Missing/ambiguous information that actually threatens safe continuation.
9. Final verdict:
   - `mission_recovery`
   - `method_recovery`
   - `medium_horizon_recovery`
   - `short_horizon_recovery`
   - `next_big_step_recovery`
   - `old_context_not_required`
   - `core_bounded`
   - `safe_for_many_industry_handoffs`

## Important interpretation

A fresh Agent **not remembering old industry details is a success** if those details are irrelevant to the current task and remain recoverable from Git when explicitly needed.

The audit fails if the Agent must consume an ever-growing historical summary to know what to do.
