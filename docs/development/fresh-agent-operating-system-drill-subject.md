# Fresh Agent Operating-System Drill — Subject Protocol

This protocol tests whether a completely fresh Agent can inherit the **full Longcycle development operating system** from the repository without old chat context.

## Isolation rules

You are the drill subject.

- Start from zero conversational context about Longcycle.
- Do **not** ask the user to restate project history or current work.
- Do **not** read any existing Fresh-Agent rehearsal/assessment report.
- Do **not** read `docs/development/fresh-agent-operating-system-drill-controller.md`.
- Do not modify the repository, issues, PRs, branches, tags, workflows, reports or data. This drill is read-only.
- Resolve current state from GitHub issue #2, live branch/PR/main, canonical bootstrap files and handoff.
- Do not preload all devlogs, old industries or repository history.

## Stage 1 — cold-start reconstruction

Use only the normal repository bootstrap path.

When ready, respond with the exact marker:

`LONGCYCLE_OS_DRILL_STAGE1_READY`

Then provide, in your own words:

1. the current live ref/PR and why it is authoritative;
2. the macro/terminal mission;
3. the long-term product direction;
4. the current medium-term goal;
5. the current short-term milestone;
6. the current atomic task, `done_when`, and next atomic action;
7. the causal chain connecting atomic task → short → medium → long-term → terminal mission;
8. why Reality, contemporaneous Judgment and later Outcome are separate;
9. why point-in-time/no-lookahead is first-order;
10. model/search vs publishable Evidence;
11. what Architecture Baseline v1 freezes and what it does not freeze;
12. the difference between `L1/L2/L3/L4` and `reuse/extend/replace/new`;
13. the Vertical Alignment / anti-tunnel mechanism and its trigger points;
14. when to use bounded on-demand history recall instead of preloading history;
15. the authority split among Strategy, Method Core, Baseline, Handoff, Capability Registry, Repair Memory, code/tests/CI and history.

Do not begin any implementation.

## Stage 2 — scenario responses

After Stage 1, the controller/user will send scenario prompts one at a time. For every scenario:

- make an independent recommendation;
- classify the change/risk where relevant;
- identify the relevant owner/invariant/authority;
- say whether to continue, stop, re-rank, escalate or enter L3/L4;
- do not mutate the repo.

## Stage 3 — final report

After all scenario prompts, produce one report with these sections:

```text
A. Live state recovered
B. Five-level goal hierarchy
C. Mission/method/worldview reconstruction
D. Baseline + change-risk understanding
E. Capability-owner / Repair-Memory / history-recall understanding
F. Vertical Alignment and independent judgment
G. Scenario decisions
H. Handoff closing transaction
I. Remaining ambiguities / confidence
J. Files actually read
```

For `J`, list only paths actually read. Explicitly state that no rehearsal/assessment report and no controller protocol was read.

End with exactly one of:

`SUBJECT_SELF_ASSESSMENT: PASS`

or

`SUBJECT_SELF_ASSESSMENT: FAIL`

This self-assessment is not the maintainer verdict.