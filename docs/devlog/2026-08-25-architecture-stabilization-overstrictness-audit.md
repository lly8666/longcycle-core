# Architecture stabilization: historical over-strictness audit

Status: in progress

## Goal

This is the final pre-freeze review of rules that were tightened during Longcycle's lithium-battery, innovative-drug and storage-semiconductor development. The question is not whether a rule is strict. The question is whether it blocks researcher discovery beyond what the owning truth semantic requires.

The governing principle is:

> Fail-closed limits what Longcycle may assert as truth. It must not unnecessarily limit what a researcher may discover as a clearly labeled candidate, entailment, Judgment or research-only hypothesis.

This audit reuses CAP-0005, CAP-0007 and CAP-0010. It creates no new semantic owner. RI-0006 remains authoritative: projection/composition must reuse existing truth owners and their negative cases.

## Stable certainty split

- **DIRECT** — source/Evidence directly supports the semantic relation.
- **ENTAILED** — accepted facts plus an explicit deterministic rule make the semantic answer unambiguous.
- **MODEL / JUDGMENT** — genuinely ambiguous analytical candidate; research-only and never source Evidence.

The system forbids inference masquerading as source fact. It does not forbid inference itself.

## Audit results so far

### 1. Optional researcher enrichment capability declaration — RELAXED

Previous behavior treated a reader that did not expose a `capabilities` attribute as a programming defect. That was stricter than the actual owner contract: deterministic subject discovery is optional enrichment, while the truth-bearing industry catalog is the required read.

New rule:

- missing optional capability declaration = unsupported optional enrichment;
- explicit supported capability returning zero rows = available, empty result;
- typed expected provider unavailability = degraded researcher enrichment;
- malformed declarations, unknown claimed capabilities and implementation defects still fail closed.

This restores the CAP-0007 distinction between truth-path failure and optional researcher enrichment failure.

### 2. Membership semantic execution mode alias — REMOVED

A durable membership semantic decision can be supported by multiple model runs, including standard and deep reasoning. Presenting one `semantic_decision_mode` suggested a durable decision itself had exactly one execution mode.

Researcher audit output now exposes only:

- `semantic_decision_supporting_run_count`;
- `semantic_decision_latest_reasoning_mode`.

Model executions remain provenance, never source Evidence or canonical Reality.

### 3. Partial-period supersession — KEEP canonical strictness; do not confuse REVIEW with absence

`Reconciler` rejects a partial-period correction as an automatic global supersession because current lineage retires an entire predecessor assertion. Without interval-level lineage, accepting the correction would erase valid history outside the corrected slice.

This is not an over-strict truth rule. The correction remains a REVIEW assertion and must not be narrated as false or absent. Architecture should only add interval-level supersession if a real benchmark demonstrates that the existing review/candidate path is insufficient; do not weaken global supersession semantics first.

### 4. Entity/product/facility graph propagation into industry discovery — DO NOT auto-entail yet

`core.entity_relation_versions` is generic and does not constrain relation vocabulary strongly enough for every relation to mean industry membership. Automatic graph propagation across arbitrary relations would create a new local definition of industry relevance and could also create historical visibility errors if relation provenance is not source-known-time equivalent.

Current safe boundary remains:

- explicit Evidence-backed industry membership = DIRECT;
- grounded Reality/Judgment carrying explicit `industry_node_id` = ENTAILED discovery;
- graph/model associations without a deterministic audited rule may be shown only in MODEL/JUDGMENT research lanes.

The remaining explicit-industry-scope requirement is therefore conservative but not presently demonstrated as an architecture defect. Do not invent a generic relation allowlist without a source-grounded case and owner-defined relation semantics.

### 5. Model-memory hypothesis promotion thresholds — KEEP

`MemoryHypothesisAssessment` does not block discovery: unresolved and mixed hypotheses can be retained as research state. The stronger label `INDIRECTLY_CORROBORATED` requires bounded direct-source search outcome, archived indirect Evidence, alternative explanations, falsification conditions and a search receipt.

That strictness is appropriate because it governs a stronger research label, not promotion to Fact/Judgment. `may_publish_as_fact` remains permanently false.

### 6. Capability governance — KEEP, scoped

CAP-0010 applies to material capability/product/architecture work, not ordinary helpers. It forces reuse/extend/replace/new classification and unique semantic ownership. A new capability requires a demonstrated unmet requirement; fuzzy similarity is discovery help, not authority.

This is architecture anti-duplication, not an information-suppression rule. Keep it hard, but do not expand it into per-function bureaucracy.

## Previously audited standards retained

The following remain hard truth boundaries:

- no-lookahead and separate valid/known/target time;
- `not_found != false`;
- claim-scoped source authority and source-independence/syndication rules;
- locator/content-verified/materialized source lifecycle;
- exact claim locator/material Evidence for promotion into Evidence;
- Reality / Judgment / Outcome separation;
- lifecycle distinctions such as sampling, mass production, customer supply, platform shipment, market availability and qualification;
- sealed blind-memory immutability and seal-bounded coverage provenance.

Research-layer relaxations already accepted and retained:

- deterministic researcher discovery can be ENTAILED rather than requiring literal membership rows;
- deterministic role may be entailed when an explicit auditable rule makes it unambiguous;
- ambiguous role, importance and causality remain labeled MODEL/JUDGMENT rather than being hidden or promoted;
- time hints/ranges may be shown to researchers when clearly labeled without manufacturing canonical precision;
- related milestones may be surfaced without pretending they realize the target Outcome;
- archive absence is research coverage, not a world-state false/unknown assertion;
- current research overlay is available by default in current workspace while historical replay remains historical-only;
- optional researcher enrichment may degrade gracefully while truth-bearing reads remain fail-closed;
- multiple equivalent membership source rows preserve all supporting Evidence and earliest source-known time.

## Freeze criterion

Architecture can move to a stable/core-locked posture when:

1. the exact-head hard CI is green;
2. the current storage benchmark still passes real-source orientation and no-lookahead acceptance;
3. no remaining audited rule suppresses researcher discovery without a truth-owner reason;
4. the final handoff records the freeze boundary and remaining work as data/evidence/productization work rather than speculative schema expansion.
