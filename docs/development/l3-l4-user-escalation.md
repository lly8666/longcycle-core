# L3/L4 User Escalation Protocol

> `LONGCYCLE_L3_L4_USER_ESCALATION_V1`

Architecture Baseline v1 is stable by default. Every Longcycle Agent — worker, coordinator, integration Agent, reviewer, fresh-session Agent or future role — must treat L3/L4 as a user decision boundary rather than an implementation detail.

## Trigger

Enter this protocol when an Agent has credible evidence that the requested work may:

- change a locked Architecture Baseline invariant;
- change what a Baseline-critical test means rather than mechanically adapting its API/fixture shape;
- change Evidence, Reality/Judgment/Outcome, PIT/no-lookahead, temporal precision, provenance/revision, source authority, canonical identity/versioning or stable semantic-owner boundaries;
- require `replace` / `new` semantic ownership because existing extension seams cannot truthfully represent an important real case;
- change Longcycle's terminal mission or long-term product direction;
- or has material uncertainty whether the change is L2 versus L3 and the cost of guessing wrong is architectural drift.

A real source-grounded counterexample or demonstrated security/consistency defect may justify L3. `Cleaner`, `more elegant`, `less code`, `more generic`, `future-proof`, framework preference or local implementation convenience do not.

## Immediate behavior

1. **Stop the Baseline-changing portion before implementation.** Do not edit the protected semantic expectation and then ask for approval afterward.
2. Preserve the real counterexample, evidence and exact current limitation.
3. Continue unrelated L1/L2 work only when it is genuinely independent and cannot prejudge the L3 decision.
4. Report the decision to the user in plain language before opening an implementation path.
5. Technical details may follow, but they do not replace the plain-language report.

## Mandatory plain-language report

The first user-facing L3/L4 escalation must answer these six questions without requiring the user to understand database/framework terminology:

1. **发生了什么？** — the concrete real-world case or defect.
2. **为什么这可能碰到地基？** — which existing Longcycle rule appears insufficient, in ordinary language.
3. **如果不改，会发生什么？** — can we truthfully handle the case another way, defer it, or will the system become wrong/incomplete?
4. **如果改，主要风险是什么？** — historical compatibility, PIT/no-lookahead, Evidence/provenance, old data, other industries, operational risk.
5. **我的建议是什么？** — keep Baseline, use an L2 extension, or deliberately enter L3/L4; state the recommended option and why.
6. **现在需要你决定什么？** — one explicit user decision. Do not bury the ask in an engineering essay.

After that plain-language section, the Agent may attach a technical appendix containing affected BL invariants, source/counterexample refs, owner seams, migration/compatibility plan, regression consequences and proposed ADR.

## No silent approval

- L3 does not begin implementation merely because the Agent believes the architecture change is correct.
- L4 always requires an explicit user decision before implementation.
- For L3, the Agent may perform bounded analysis sufficient to classify the issue and prepare an ADR/counterexample packet, but implementation of the Baseline change waits for the repository's required approval path and the user's explicit risk decision when the change materially affects research truth, compatibility or project direction.
- Silence, an old approval, a stale Change Contract, an earlier handoff or a previous Agent's preference is not approval for a new L3/L4 case.

## Worker handoff persistence

Parallel workers do not write the global handoff. When a worker encounters a potential/confirmed L3 or L4 issue:

1. create a concise workstream-local record under:

   `.longcycle/workstreams/<workstream-id>/escalations/<short-id>.md`

2. the record must contain the six plain-language questions above plus a short technical appendix with source refs and affected owner/Baseline candidates;
3. add that repository-relative escalation path to the workstream's `integration_requests`;
4. set the branch-local `next_atomic_action` so a fresh worker knows whether unrelated L1/L2 work may continue or the workstream is blocked on user/integration decision;
5. do **not** expand main-reserved scope, owner routing or dependencies from the worker branch to solve the issue locally.

Because `integration_requests` is part of the workstream cursor, the next fresh worker and the serial integration Agent inherit the unresolved escalation without the user restating it.

## Coordinator / integration behavior

The coordinator or serial integration Agent must:

- deduplicate related escalation requests from multiple workers;
- challenge whether the issue is actually L3 rather than an L2 extension;
- translate the issue into the mandatory plain-language user report;
- keep at most one active global-serial architecture-change lane;
- refuse to create parallel industry-specific semantic forks while a shared L3 decision is pending;
- after the user decision, record the decision and route the work through the normal Change Contract / Capability admission / ADR / Baseline process.

The coordinator may continue registering and integrating unrelated L1/L2 workstreams when doing so cannot bias or depend on the unresolved L3 decision.

## Global handoff rule

The global `.longcycle/handoff/current.json` should not duplicate the whole escalation report. At a coherent project-level boundary it records only:

- that an L3/L4 user decision is pending or resolved;
- the authoritative workstream-local escalation path / ADR reference;
- the affected workstream(s);
- the current decision/blocking status and next project-level action.

The detailed escalation file remains the durable handoff artifact. This keeps global continuity bounded while preserving the full decision context.

## Decision principle

> Agents may autonomously implement inside the Baseline. They may discover and explain reasons to change the Baseline. They may not silently decide that a new definition of correctness is now in force.
