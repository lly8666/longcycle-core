# 2026-08-25 — Restore strict search/Agent boundaries; expose noncanonical Reality candidates

## User correction

The historical over-strictness audit produced two relaxations that the user explicitly rejected:

1. historical verification search depth must remain a hard anti-premature-stop gate because a model must not decide for itself that one apparently decisive result means it searched thoroughly enough;
2. bounded/lower-capability research Agents must remain evidence-engineering executors rather than free-form industry analysts; tasks requiring independent high-capability synthesis stop and escalate.

These are restored as hard operating rules. The separate Memory Lead fix remains: fragmentary unsourced memory may be preserved before its delegated-search packet is complete, but actual delegated historical verification still requires the full search/depth contract.

## Search-depth behavior restored

`VerificationDepth` is again a common stop gate. `verification_stop_decision` now rejects *all* normal stop states until the required query-family count, source-type count, primary-domain check, reverse query and required citation chase are satisfied. An authoritative-looking result does not bypass this gate.

This strictness exists to control model search behavior, not to change truth semantics: `not_found != false`, and search depth still cannot turn absence into contradiction.

## Agent authority restored

The project constitution / Method Core / research-agent SOP are restored to the prior strict capability split: bounded Agents execute explicit claim-scoped evidence tasks and do not freely publish industry conclusions. When a task requires independent high-capability synthesis beyond their reliable role, they stop and escalate rather than imitating a higher-capability conclusion.

## Reality candidate visibility gap

A separate, genuine over-strictness remained: CAP-0003 already preserves source-backed Fact assertions that reconcile to REVIEW or QUARANTINE, including Evidence, score/reasons and timestamps, but canonical Reality correctly publishes only trusted/accepted facts. The missing piece was researcher visibility.

The fix does **not** lower canonical thresholds and creates no new truth owner. CAP-0003 continues to own reconciliation; CAP-0005 gains a read-only research projection:

```text
source-backed Fact assertion
+ point-in-time reconciliation decision = review/quarantine
+ source Evidence
+ source_known_at <= cutoff
+ decision_known_at <= cutoff
→ research-only Reality candidate
```

Every candidate is explicitly `canonical=false` and `research_only=true`, carries Evidence IDs, reconciliation score/reason codes, source-known time and decision-known time, and is omitted if either time lies after the requested knowledge cutoff. `conflict` remains in the existing conflict/open-state lane rather than being duplicated here.

## Semantic owner decision

Repository-history recall found no need for a new capability. Reuse/extend:

- CAP-0003 — owns Fact assertion/reconciliation status;
- CAP-0005 — owns researcher point-in-time read projections;
- CAP-0006 — retains strict post-seal verification depth plus Memory Lead preservation;
- CAP-0009 — owns handoff and Fresh-Agent continuity validation;
- CAP-0010 — records the scoped extension/reuse decision.

## Safety boundary

Longcycle network behavior remains limited to benign public-source industrial research and evidence preservation. Do not add unauthorized access, credential acquisition, scanning/exploitation, evasion/persistence, malware, exfiltration, denial-of-service, or unsolicited security-testing capabilities.
