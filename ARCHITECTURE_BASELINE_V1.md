# Longcycle Architecture Baseline v1

Longcycle Architecture Baseline v1 defines the stable semantic and data-contract foundation of the system. Feature development, industry expansion, source coverage, product surfaces and implementation quality are expected to continue. Baseline invariants are not reopened merely because a different abstraction looks cleaner or more general.

## Baseline locator

- Baseline id: `architecture-v1`
- Version: `1.0.0`
- Canonical tag: `architecture-baseline-v1.0.0`
- Baseline commit: the commit resolved by that Git tag; the manifest does not self-embed its own commit SHA.
- Schema ceiling at freeze: migration `0039`
- Machine manifest: `.longcycle/baseline/v1.0.0.json`
- Current pointer: `.longcycle/baseline/current.json`
- Required correctness contexts: `longcycle/full-ci` and `longcycle/architecture-baseline`

The tag identifies the historical immutable checkpoint. This document explains the contract. The JSON manifest makes the contract machine-readable.

## Locked invariants

| ID | Locked semantic | Contract |
| --- | --- | --- |
| BL-001 | Evidence boundary | Model memory, search results, snippets and model answers may discover claims but cannot by themselves publish Reality or Judgment. Publishable history must resolve to claim-scoped source-derived Evidence. |
| BL-002 | Historical recovery order | Historical recovery remains Memory-first and Evidence-final: blind recall/exhaustion must be sealed before fresh search can influence that memory vintage. Current collection may remain source-first/preserve-now. |
| BL-003 | Reality / Judgment / Outcome separation | What happened, what contemporaries believed, and what later happened are distinct durable semantics. Agreement between judgments does not create Reality. |
| BL-004 | Outcome non-rewrite | Later Outcomes evaluate or relate to historical Judgments; they never rewrite the old Judgment into hindsight. |
| BL-005 | Temporal separation | Valid/effective time, market-known/knowledge time, system/adoption time and expectation target time remain distinct where applicable. |
| BL-006 | PIT / no-lookahead | Historical replay may expose only information eligible at the requested knowledge cutoff. Later-known information cannot leak into the past. |
| BL-007 | Temporal precision fidelity | Source-supported precision is preserved. Unknown/month/quarter/range timing cannot be silently sharpened into invented exact dates or timestamps. |
| BL-008 | Append-only provenance | Historical execution, evidence and judgment provenance is not silently mutated or deleted. Reaffirmation and additional corroboration accumulate; audit history remains recoverable. |
| BL-009 | Revision by version | Canonical revisions and changed expectations are represented as new versions/relations, not UPDATE-in-place erasure of prior adopted states. |
| BL-010 | Claim-scoped authority | Authority is evaluated for the claim scope. Retrieval host, file extension, source popularity or repeated syndication cannot automatically confer authority. |
| BL-011 | Source representation boundary | Logical source identity, `locator_verified`, `content_verified` readable representation and raw `materialized` bytes remain separate states. Transport does not change authority. |
| BL-012 | One semantic owner / reuse first | Stable cross-industry semantics have one canonical capability owner. New industries and product surfaces extend/reuse owners by default; a parallel owner requires a demonstrated truthful unmet requirement or explicit supersession. |

These invariants describe what counts as correct. Implementations may change freely while continuing to satisfy them.

## What is not frozen

Baseline v1 does **not** freeze:

- UI, CLI, API shape or presentation;
- model/provider/vendor choices or agent implementation;
- parser, connector, crawler, cache or performance implementation;
- orchestration ergonomics or deployment topology;
- industry-specific predicate/metric catalogs, taxonomies, units or source adapters;
- research packets, Domain Packs, benchmark coverage or valuation/forecast modules;
- production-readiness work such as permissions, outbox relay, DR, monitoring or review surfaces;
- implementation refactors behind existing semantic extension seams.

A new industry is normally a Domain Pack problem, not an invitation to redesign Evidence, Reality, Judgment, Outcome or PIT semantics.

## Change levels

Every material change records a `change_level` in the existing capability admission. Change level is orthogonal to `reuse / extend / replace / new`:

- **L1 — implementation change.** Bug fixes, parser/connector work, performance, cache, UI/CLI and internal refactors that preserve stable semantics. Agents may implement autonomously and run normal CI.
- **L2 — product/domain extension.** New industries, predicates, units, APIs, Domain Packs and product capabilities that reuse/extend the Baseline. Agents may implement autonomously, but must name existing semantic owners and preserve Baseline-critical regressions.
- **L3 — Baseline change.** Any intended change to a locked invariant, its semantic owner boundary, or the expected meaning of a Baseline-critical regression test. Normal implementation stops first. An Architecture Change Proposal/ADR must present a concrete important source-grounded case or a demonstrated security/consistency defect that the current Baseline cannot truthfully handle, plus compatibility/no-lookahead/provenance consequences.
- **L4 — mission change.** A change to Longcycle's terminal product mission or the role of point-in-time industrial memory. This requires an explicit user decision before implementation.

`Cleaner`, `more generic`, `less code`, `future-proof`, framework preference or one isolated industry convenience are not sufficient reasons for L3.

## Baseline-critical tests

L1/L2 work may mechanically update test imports/fixtures when implementation moves, but it may not change the semantic expectation protected by Baseline-critical tests in order to make new code pass. If the desired behavior requires changing those expectations, the work is L3 before the test and implementation are changed together.

The Architecture Baseline Gate protects the manifest/documents and a compact set of semantic regression tests. Full CI remains the implementation correctness gate.

## Architecture-change procedure

For L3:

1. stop ordinary implementation;
2. identify the locked invariant(s) under pressure;
3. preserve the real counterexample/source evidence and explain why existing extension seams cannot truthfully express it;
4. write an ADR/Architecture Change Proposal including compatibility, migration, PIT/no-lookahead, provenance and old-data consequences;
5. obtain explicit review/approval for the Baseline change;
6. implement against both the counterexample and existing Baseline-critical regressions;
7. release a new Baseline version/tag rather than silently rewriting v1.

For L4, step 0 is explicit user approval of the mission change.

## Authority by question

Do not use one global document ranking for every question. Use the owning source:

- Why Longcycle exists / terminal success: `STRATEGIC_COMPASS.md`
- Cross-industry research method: `METHODOLOGY_CORE.md`
- What architecture semantics are frozen and how they may change: this Baseline + machine manifest
- Who owns a stable semantic / extension seam: Capability Registry and active capability cards
- What work is live now: `.longcycle/handoff/current.json` + current admission + live Git/CI
- What the implementation actually does: migrations, code, executable tests and live runtime/CI
- Why an old decision was made: Git history, devlogs, receipts and historical reports

Historical documents remain immutable evidence of development history; a Baseline freeze does not rewrite them to look as if v1 was known from the start.

## Post-Baseline development rule

The default question is no longer “what architecture would be nicer?” It is:

> What is the smallest truthful L1/L2 extension inside Architecture Baseline v1, which existing semantic owner should handle it, and which Evidence/PIT/provenance regressions prove that it did not change what correctness means?

Real benchmarks may still falsify the Baseline. After v1, the burden of proof belongs to the proposed architecture change rather than to the established foundation.
