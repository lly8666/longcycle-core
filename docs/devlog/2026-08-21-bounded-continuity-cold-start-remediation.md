# 2026-08-21 — Bounded Continuity Cold-Start Remediation

## What the genuine fresh-Agent test found

A genuinely fresh Agent was asked to run the bounded-continuity audit using only the repository and the audit request.

It wrote its report to **default `main`**, not the active development branch, and audited the stale initial implementation state. Its conclusion was therefore a continuity failure: no Strategy Core, Method Core, live checkpoint, current medium/short horizon or bounded audit spec was discoverable from that default-branch tree.

The report commit on `main` is preserved as historical evidence:

- main commit: `ebfa0672b01f55a79cb944ef9411a336fab8fa7d`
- report path: `docs/devlog/2026-08-21-fresh-agent-bounded-continuity-audit-report.md`

This was a **real system failure**, not merely an Agent mistake.

## Why the Agent's behavior was reasonable

The previous design used GitHub issue #2 as a branch-independent rendezvous, but nothing on the default branch told a zero-context Agent that issue #2 existed or that `main` was stale.

The Agent deliberately avoided PRs/issues because it interpreted them as extra context outside the current tree. Given only the repository name, treating the default branch as the initial authority was a defensible cold-start policy.

The hidden assumption was wrong:

> “A fresh Agent will know to inspect issues/PRs before trusting `main`."

Continuity cannot rely on that guess.

## Remediation 1 — default-branch discovery pointer

A stable `FRESH_AGENT_BOOTSTRAP.md` now exists on `main` and is mirrored in the active branch.

Its only role is:

```text
default branch
→ issue #2 stable rendezvous
→ active PR/development branch
→ CONTINUE_HERE.md
```

It contains no current industry, campaign count, branch name, CI run or task state.

A report-only audit must write its single allowed mutation to the **resolved active branch**, unless the task explicitly targets `main`.

## Remediation 2 — semantic fidelity, not maximal compression

The same review exposed a second design risk: the first bounded Strategy Core had been shortened aggressively enough that it could preserve keywords while losing some of the founding causal logic.

The Strategy Core has therefore been expanded within a still-hard ceiling to preserve:

- the original reason for preserving long, true industry history;
- why final facts alone create hindsight;
- why contemporaneous Judgment/Expectation is first-class;
- the idea of making the already-known future unknown again;
- why point-in-time/no-lookahead matters;
- why long, comparable history can itself reveal cycle risk/opportunity through common-sense causal reasoning;
- why tools are means and replay is the product capability;
- why industry benchmarks are temporary proving grounds, not permanent product scope.

The CI contract now treats the Core byte/line budget as a **ceiling**, not a target, and checks semantic anchors representing this causal structure.

`METHODOLOGY_CORE.md` now explicitly defines the continuity objective as the balance of:

1. semantic fidelity;
2. context economy;
3. bounded growth.

## Internal artificial-ignorance result

A restricted same-model drill using only the normal bounded bootstrap recovered:

- mission semantic facets: 10/10;
- cross-industry method: 12/12;
- medium/short/next/parallel horizons: 4/4;
- old devlog/old industry requirement: none;
- anti-bloat/anti-overcompression steering mini-suite: 10/10.

This is not a substitute for a genuinely fresh Agent. The previous genuine test proved why external audits remain necessary.

## Next validation

Rerun the genuine bounded-continuity audit from only the repository name and audit instruction.

The new Agent must:

1. discover `FRESH_AGENT_BOOTSTRAP.md` from `main`;
2. resolve issue #2 / active development branch;
3. reconstruct the founding mission causally rather than quote slogans;
4. recover Method Core and dynamic horizons without old devlogs;
5. write only the audit report on the active branch.

If that succeeds, continuity work should stop being a main-path project and the active research/development roadmap should resume.
