# Package A governance rationale — 2026-08-25

This note carries the long-form rationale behind the bounded current capability admission. The admission JSON intentionally stores only a compact summary and points here for details.

## User-approved ordering

Package A is ordered to remove engineering ambiguity before expanding research semantics:

1. classify optional research enrichment as AVAILABLE, UNAVAILABLE_EXPECTED or DEFECT; empty results remain AVAILABLE;
2. make capability support explicit instead of inferring it from method presence;
3. make capability cards the canonical governance source and active-index.json a deterministic generated artifact checked, not silently rewritten, by CI;
4. make current-research overlay mode explicit at application call sites and visually/time-semantically separate it from historical cutoff state;
5. split every model membership judgment run from the durable semantic decision it may support, with deterministic deep-reasoning triggers plus model self-escalation.

These changes are intended to improve provenance, debugging and researcher comprehension without relaxing CAP-0002/3/4 truth ownership, no-lookahead, source Evidence requirements or canonical membership source constraints.

## Deliberately deferred work

Known-universe coverage semantics comes after Package A. Weak-source discovery leads, coarse locators, budgeted hypothesis-to-task routing and broader selective deep reasoning are later independent packages. Partial conflict decomposition and candidate relationship graphs remain deferred until real benchmarks demonstrate a truthful need.

## Governance principle

Hard gates should prevent high-risk semantic corruption. Derived metadata should be generated deterministically from its canonical source so humans and Agents do not maintain two copies of the same truth. Long-form rationale belongs in referenced artifacts; bounded admission/handoff state should remain resumable rather than becoming prose storage.
