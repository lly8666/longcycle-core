# 2026-08-25 — Restore strict search/Agent boundaries; expose noncanonical Reality candidates

## User correction

The historical over-strictness audit produced two relaxations that the user explicitly rejected:

1. historical verification search depth must remain a hard anti-premature-stop gate because a model must not turn a shallow failed search into a self-declared exhaustive `not_found`;
2. bounded/lower-capability research Agents must remain evidence-engineering executors rather than free-form industry analysts; tasks requiring independent high-capability synthesis stop and escalate.

These are restored as hard operating rules. The separate Memory Lead fix remains: fragmentary unsourced memory may be preserved before its delegated-search packet is complete, but actual delegated historical verification still receives explicit search/depth requirements.

## Search-depth behavior — final calibrated rule

The first attempted restore made `VerificationDepth` a common gate for every normal stop state. A real external Fresh-Agent takeover test exposed that this wording/implementation was itself over-strict: the new Agent correctly learned the anti-premature-stop intent but then concluded that even claim-scoped authoritative original content directly answering a claim could never stop before satisfying the generic fixed query/source counts.

The final rule separates **unresolved exhaustion** from **authoritative resolution**:

- before declaring `unresolved-exhaustion`, the full configured query-family count, source-type count, primary-domain check, reverse query and required citation chase are mandatory;
- `unresolved-exhaustion` remains unresolved, not false and not proof of world-state absence;
- if the Agent actually reads claim-scoped authoritative original content that directly answers the claim, verifies source identity and scope, the claim may resolve without mechanically satisfying the generic unresolved-exhaustion query/source counts;
- high-impact resolved claims retain the configured reverse-query guard;
- citation chains, scope ambiguity, source conflict, or content that does not directly answer the claim require continued search;
- source count never substitutes for claim-scoped authority.

So the strictness remains where the user intended it: a model cannot casually search twice and announce that history has been exhausted. But search depth is not turned into a corroboration/search-count KPI after direct authoritative content has already resolved the claim.

Plain-language rule:

> **对“没找到/仍 unresolved”要求搜得够深；对“找到了”要求证据够直接、scope 对得上。多搜不是目标；有足够理由得出你声称的结论才是目标。**

## Agent authority restored

The project constitution / Method Core / research-agent SOP retain the strict capability split: bounded Agents execute explicit claim-scoped evidence tasks and do not freely publish industry conclusions. When a task requires independent high-capability synthesis beyond their reliable role, they stop and escalate rather than imitating a higher-capability conclusion.

The search-depth calibration above does not loosen that authority boundary. It changes when an explicit evidence-search task has sufficient evidence to stop, not who is allowed to perform independent synthesis.

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

## Fresh-Agent continuity finding

The real external takeover recovered the project mission, live branch/HEAD discipline, capability ownership, no-lookahead/Evidence rules, strict bounded-Agent role and correct live-CI-before-domain-work ordering without prior chat context. It scored 91/100 before remediation. Its one material semantic error was the fixed-quota search interpretation above, which demonstrated that repository continuity was strong but the search-stop contract itself was inconsistent across layers.

The detailed assessment is recorded in `docs/development/fresh-agent-takeover-assessment-2026-08-25.md`.

## Semantic owner decision

Repository-history recall found no need for a new capability. Reuse/extend:

- CAP-0003 — owns Fact assertion/reconciliation status;
- CAP-0005 — owns researcher point-in-time read projections;
- CAP-0006 — owns blind/sealed historical verification and the calibrated unresolved-exhaustion depth rule;
- CAP-0009 — owns handoff and Fresh-Agent continuity validation;
- CAP-0010 — records the scoped extension/reuse decision.

## Safety boundary

Longcycle network behavior remains limited to benign public-source industrial research and evidence preservation. Do not add unauthorized access, credential acquisition, scanning/exploitation, evasion/persistence, malware, exfiltration, denial-of-service, or unsolicited security-testing capabilities.
