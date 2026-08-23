# Researcher Industry Mental-Map Gap Audit v2

## Purpose

This audit supersedes the decision state of `researcher-mental-map-gap-audit-v1.md` without erasing it. It asks one question after the orientation, Evidence drilldown and explicit open-state surfaces have all been full-CI proven:

> Is Longcycle now complete enough to stop adding researcher UI/projection features and use a second real industry to expose the next truthful cross-industry gap?

The acceptance standard remains the Strategic Compass: a first-time researcher should be able to build a defensible industry mental map quickly — structure and participants, real drivers/constraints, long historical trajectories, contemporaneous Judgment/disagreement, later Outcomes, Evidence boundaries and explicit unknowns — while preserving point-in-time truth and `not_found != false`.

## Current proven researcher path

The current product path is now:

```text
industry identity + historical cutoff
→ source-grounded industry orientation
→ subject Reality / Judgment / Outcome coverage
→ subject point-in-time trajectory replay
→ EvidenceFragment drilldown
→ historical controversy / Judgment contradiction
→ optional current research-only open-state overlay
```

These are composition/read surfaces over existing semantic owners. They do not create a second source, Evidence, Reality, Judgment, Outcome, conflict or cutoff authority.

## Requirement re-audit

| Researcher requirement | v2 status | What is now true | Remaining truthful gap |
| --- | --- | --- | --- |
| Value-chain / participant structure | **Usable, still semantically bounded** | Industry orientation starts from an industry id and exposes only source-grounded, cutoff-visible members with stable subject ids and canonical current labels. | Longcycle still does not infer role, importance or relationship. Those may be shown only when an owning Fact/relationship record actually supports them. A second industry should test whether current Fact semantics are sufficient before adding any role graph. |
| Key drivers and constraints | **Partially served; benchmark needed** | Reality stores grounded state; Judgment rationale can explicitly own premise, mechanism, condition, risk, caveat and counterargument. A researcher can inspect the underlying trajectories and Evidence. | There is no generic industry-level mechanism/driver synthesis. Presentation is not allowed to infer causality from co-occurrence or predicate names. This is the main remaining product question, but it is not yet proof of a missing semantic owner. |
| Long historical trajectories | **Served** | Typed no-lookahead replay and researcher trajectory views are implemented and proven. | No generic product gap demonstrated. New industries should test temporal/comparability edge cases. |
| Contemporaneous Judgment, disagreement and revision | **Served for explicit typed records** | Judgment revisions/contradictions/counterarguments are replayable; historical source disagreement is visible when distinct sources conflict at the cutoff. | Missing records remain missing; presentation must not synthesize consensus or controversy. |
| Later Outcome | **Served** | Outcomes remain distinct from Judgment and are revealed through existing replay without rewriting the historical Judgment. | No generic product gap demonstrated. |
| Evidence drilldown | **Served** | Evidence id + cutoff returns claim-scoped readable content, source/publisher identity, historical known-time and truthful current preservation/materialization state. | No generic product gap demonstrated. |
| Explicit unknowns / controversy | **Served when explicitly owned** | Historical multi-source Reality disagreement and typed Judgment controversy are separated from current Memory disagreement/hypothesis/model-memory coverage gaps. Current research state is opt-in and explicitly non-historical. | Simple absence remains absence. `not_found != false`; the product still must not manufacture an unknown state from missing rows. |

## Closed gaps from v1

The following v1 gaps are retired and must not be reopened for polish without a concrete cross-industry failure:

1. **Industry entry/orientation** — closed by the source-grounded industry orientation surface.
2. **Researcher Evidence inspection** — closed by the typed Evidence drilldown surface.
3. **Explicit negative-space/open-state visibility** — closed by the dual-lane historical-vs-current open-state surface.

A future benchmark may reveal a semantic defect in one of these surfaces, but the burden of proof is now on the benchmark, not on speculative feature design.

## What remains genuinely uncertain

Two questions remain, and neither justifies immediate architecture work:

### 1. Are industry roles/relationships already representable enough?

The orientation surface deliberately refuses to infer role or importance. A new industry should test whether source-grounded entity-valued Facts and existing taxonomy/membership semantics are enough for a researcher to understand producer/customer/product/technology relationships. If not, the benchmark must identify the exact relation that cannot be represented truthfully before any schema or owner is added.

### 2. Are drivers/constraints a composition problem or a semantic-owner problem?

Judgment rationales already own explicit mechanisms/conditions/risks, and Reality owns grounded states. The missing experience may be only a read composition across these records. But if a new industry repeatedly requires a first-class mechanism identity that cannot be expressed without flattening provenance or causality, that would be a demonstrated semantic gap. Until then, do not invent one.

## Readiness decision

**Decision: READY FOR A SECOND CROSS-INDUSTRY BENCHMARK. Do not add another researcher feature first.**

Reasoning:

- The researcher now has a complete navigation loop from industry → subject → historical trajectory → Evidence → explicit controversy/open state.
- Remaining gaps are precisely the kind that a different industry should pressure-test; continuing to polish lithium risks encoding lithium-specific intuitions as generic architecture.
- Strategic Compass explicitly says benchmarks exist to expose missing abstractions and evidence failures, not to optimize internal completion scores.
- No known remaining gap prevents truthful point-in-time research. The main uncertainty is whether the current abstractions remain sufficient under a very different industrial cycle.

## Second benchmark selection

The next benchmark is **DRAM memory semiconductors**, with HBM treated as a DRAM product/technology/capacity-allocation branch rather than a separate AI-news topic. NAND is outside the core industry boundary and enters only where it directly affects shared capital allocation, cleanroom/fab decisions or company-level memory economics.

Initial historical window:

```text
2016-01-01 → 2026-08-24
```

Material first known after 2026-08-24 belongs to current collection, not to this initialized historical window.

Why DRAM:

- repeated commodity price/inventory/capex cycles;
- technology-node and bit-per-wafer transitions;
- a concentrated supplier structure plus a newer Chinese entrant;
- long customer qualification and product-generation transitions;
- clear distinction between wafer capacity, bit output, product mix and effective sellable supply;
- HBM creates a strong test of capacity trade-offs, packaging constraints and mix-driven economics without abandoning the long-cycle DRAM frame;
- the period spans multiple up/down cycles rather than only the current AI phase.

## Architecture budget rule for the DRAM benchmark

The DRAM benchmark is a **conformance test**, not permission to generalize every memory-semiconductor term into core schema.

Do not change product architecture merely because DRAM uses different nouns. Change architecture only if a source-grounded DRAM case demonstrates that an important Reality/Judgment/Outcome/Evidence/identity/time/comparability relation cannot be represented truthfully by an existing owner.

In particular:

- do not add a generic `driver` table from analyst prose;
- do not infer supplier importance from market-share rank or row counts;
- do not treat HBM demand commentary as conventional DRAM Reality;
- do not merge wafer capacity, wafer starts, bit growth, die output, package output and sellable product supply;
- do not backdate later product qualification or yield knowledge into earlier snapshots;
- do not make current Memory/search leads publishable Evidence.

## Next action

Initialize a bounded DRAM research campaign under existing CAP-0006 methodology, preserving the sealed blind-recall → verification → Evidence-final sequence. The initial campaign should first produce industry boundary, historical snapshots, orthogonal query/pass families and explicit comparability hazards. Product code remains frozen until that benchmark demonstrates a concrete cross-industry failure.
