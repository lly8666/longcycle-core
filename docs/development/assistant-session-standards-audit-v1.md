# Assistant-authored work standards audit v1

## Purpose

This is a retrospective conformance audit of the work added after the researcher-readable replay checkpoint and before the third-industry storage benchmark starts blind recall. It exists because local CI success is not enough: a projection can be internally green while still drifting from an already-owned epistemic semantic.

Audit baseline: `1a642aef3a537eef690c11905edf7c979a0e9e98`.

Primary pre-audit checkpoint: `e3d1b0190c56d8ff21e40414c7da0f15c16e6d28` / `longcycle/full-ci` run `32661384312`.

Standards checked:

- Strategic Compass: point-in-time industrial memory, not a report generator;
- Reality / Judgment / Outcome remain separate;
- no lookahead: historical visibility uses what was knowable by the cutoff;
- Memory-first, Evidence-final for historical recovery;
- Source-first, Preserve-now for current collection;
- `not_found != false`;
- source representation != raw materialization;
- claim-scoped/source-independence semantics must be reused from their existing owners;
- campaign/model-vintage provenance must remain explicit and append-only;
- capability governance must prefer existing owners over parallel semantics;
- live Git/CI outrank prose snapshots;
- bounded handoff must remain truthful about global project history.

## Executive finding

The broad architecture is not invalid and should not be rolled back. Industry orientation and Evidence drilldown are directionally and semantically compliant. The storage benchmark initialization is also compliant after the lineage/scope corrections.

However, the assistant-authored open-state projection contained **three substantive conformance defects**. All three came from a new read/projection layer partially reimplementing semantics already owned elsewhere. Two of the defects were reinforced by tests/smoke that encoded the wrong behavior, demonstrating that a green CI run cannot substitute for semantic-owner review.

The three defects are being repaired without a migration, new truth owner, generic unknown state or new capability semantics.

## MUST-FIX findings

### A1 — Reality disagreement used connector identity instead of CAP-0003 source independence

**Pre-audit behavior**

`PostgresOpenStateReader` selected `fact_assertions.source_connector_id` as `source_id` and required two distinct connector ids before presenting a `RealitySourceDisagreementRecord`.

**Why this violates the standard**

The existing Fact/Reconciler owner already defines independence using `source_cluster` with connector/source id only as a fallback. Two connectors can represent the same upstream/syndicated source. Treating them as independent creates a second source-independence semantic and can manufacture a researcher-facing “multi-source disagreement”.

**Repair**

- preserve `source_cluster` on the typed conflict assertion read model;
- derive an independence key exactly as the existing Reconciler does: `source_cluster` when present, connector id only as fallback;
- require two independent keys, not two connectors;
- unit regression rejects different connectors in one cluster;
- PostgreSQL smoke now creates a real conflict from two connectors sharing one cluster and requires the researcher projection to omit it.

**Architecture effect**

No new owner. CAP-0003 remains the source-independence/reconciliation owner; the open-state projection stops shadowing it.

### A2 — “Current” research overlay was silently narrowed by historical membership cutoff

**Pre-audit behavior**

`build_researcher_open_state_view` first selected industry memberships visible at the historical cutoff, converted those into entity ids, and passed that list into `CurrentResearchOpenStateReader`. The output simultaneously claimed `cutoff_filter_applied=false`.

**Why this violates the standard**

The current overlay is explicitly present/current research state, not historical market knowledge. A subject that entered the industry after a 2023 cutoff can still have a valid unresolved research state today. Filtering the current lane through the 2023 membership population made the label and behavior disagree and mixed historical scope ownership into current Memory provenance.

**Repair**

- remove historical entity ids from the current research reader contract;
- scope current Memory disagreement/hypothesis rows by their own explicit industry subject or producing `model_prior_runs.industry_node_id`;
- keep historical orientation membership only for the historical lane;
- unit and PostgreSQL tests use a subject whose membership is first knowable after the historical cutoff and require the opt-in current overlay to retain it.

**Architecture effect**

No new owner. CAP-0005 continues to own historical/current separation; CAP-0006 current research state now uses its own provenance instead of CAP-0005 historical membership as a hidden filter.

### A3 — model-memory coverage mixed campaign vintages and admitted unsealed campaigns

**Pre-audit behavior**

`_current_coverage_gaps` ranked coverage cells across all campaigns for an industry by dimension and row creation time. It did not select a campaign first and did not require a campaign seal. The original PostgreSQL smoke inserted coverage into an unsealed campaign and expected it to appear.

**Why this violates the standard**

Migration 0015 explicitly models model-memory campaigns as instrument vintages, makes sealing a separate immutable event and keeps coverage cells campaign-owned/append-only. Combining cells from different campaigns can create a synthetic coverage map that no model run ever produced; admitting unsealed coverage treats unfinished recall as a final current coverage view.

**Repair**

- select the latest **sealed** campaign for the industry first;
- rank versioned coverage cells only within that one campaign;
- return no coverage rows when no sealed campaign exists;
- PostgreSQL smoke now seeds a sealed campaign with `thin` coverage plus a newer unsealed campaign with `dense` coverage for the same dimension, and requires only the sealed campaign to appear.

**Architecture effect**

No new owner. CAP-0006 campaign/seal/vintage provenance remains authoritative; the projection stops synthesizing a cross-vintage state.

## Previously fixed process/continuity defects

### P1 — benchmark lineage drift

The assistant incorrectly narrated the project as lithium battery → DRAM and repeatedly called storage the second industry, despite the actual sequence being:

```text
锂电 → 创新药 → 存储半导体
```

Root cause: current handoff/PR prominence was mistaken for complete project history, and “second transfer test” was conflated with “second industry”. A failed search for innovative-drug context was also treated too much like absence, contrary to `not_found != false`.

Status: fixed in storage plan/manifest and handoff. Future lineage statements must be retrieved from explicit project history or remain unresolved; they must not be inferred from whichever benchmark dominates the current handoff.

### P2 — handoff sequence 79 exceeded the cold-start budget

The DRAM manifest was added as a ninth bootstrap read despite the eight-file bound. Pytest caught the error.

Status: fixed by leaving benchmark manifests in deep/on-demand context instead of increasing the bootstrap budget.

### P3 — task-specific governance tests were hard-coded as permanent rules

Capability-registry rehearsal temporarily hard-coded the preceding admission/task. This made a later legitimate `reuse` admission fail because the test encoded historical task state rather than governance semantics.

Status: fixed by making the rehearsal follow the current valid admission.

### P4 — exact-head language occasionally blurred implementation commit vs verified checkpoint

Some user-facing summaries called a later all-green checkpoint the “implementation head” even when the final commit itself was only a test/index/control-plane adjustment. Git ancestry made the statement technically defensible but less traceable than it should be.

Status: wording rule going forward: distinguish **implementation landed across commits** from **verified checkpoint SHA / CI run**.

## Compliant work confirmed by this audit

### C1 — Researcher Evidence drilldown

No substantive conformance defect found.

- Evidence id + cutoff fails closed when `first_known_at` is later than the requested cutoff.
- Historical source timing is distinct from current preservation/materialization state.
- A readable content-verified representation remains the Evidence representation even when raw source bytes are materialized later.
- Locator-only state is not promoted to claim Evidence.
- Presentation does not invent source authority or claim truth.

This remains aligned with CAP-0001/CAP-0002 and Repair Memory RI-0005.

### C2 — Industry orientation

No demonstrated no-lookahead defect found.

- membership requires resolution/Evidence-backed records;
- membership visibility uses source-known time and valid time;
- `system_from` is not used as historical knowledge time and only breaks ties among already-knowable curated versions;
- Reality/Judgment/Outcome visibility remains delegated to the typed epistemic snapshot at the same cutoff;
- current canonical labels are explicitly not historical-name replay;
- presentation does not infer importance or causality.

**Wording hardening note:** this surface is best understood as an **archive-reconstructed membership view from cutoff-knowable source-backed facts**, not proof that a contemporaneous research team had already curated the same catalog row. Current code does not use `system_from` as market knowledge, so this is a precision/communication hardening item rather than a demonstrated architecture defect.

### C3 — Repair Memory invariants

No substantive weakening found in the touched invariants.

- RI-0001 still gives live Git/CI authority over prose snapshots and requires live re-read after mutation.
- RI-0005 still distinguishes locator/content-verified/materialized states, permits readable source-derived representation as Evidence when actually content-verified, forbids locator-only claim proof and forbids later raw materialization from relabelling an earlier representation.

### C4 — Methodology Core

The assistant changed the bounded methodology core during this broader phase. The current text still preserves the required cross-industry methods and epistemic boundaries; no semantic regression was found.

**Process note:** constitution/core compaction should normally be isolated from product feature implementation and accompanied by an explicit semantic-equivalence check. Combining it with feature work increased review risk even though the resulting core remains aligned.

### C5 — Storage benchmark initialization

Current storage benchmark setup is compliant after correction:

- benchmark lineage is lithium battery → innovative drugs → storage semiconductors;
- DRAM + NAND are co-core; HBM is inside DRAM;
- shared supplier/capital-cycle behavior is a research hypothesis, not preloaded Reality;
- DRAM/NAND prices, inventory, bit supply, technology and demand metrics remain non-merged;
- historical scope stops at 2026-08-24;
- blind recall has not started in the contaminated initialization context;
- CAP-0006 is reused; no semiconductor-specific core schema was added.

## What the green CI did and did not prove

The pre-audit open-state implementation had a successful full-CI checkpoint. That did **not** mean it met all standards because the tests themselves encoded two wrong assumptions: connector-distinctness as source independence, and unsealed campaign coverage as displayable current coverage.

The durable lesson is:

> CI proves conformance to the encoded contract. Semantic-owner review proves whether the encoded contract is the right one.

For projection/read layers, a new hard gate should preferentially exercise the existing owner’s negative cases, not only the happy path of the new surface.

## Remaining non-blocking risks

1. **Orientation reconstruction wording** — clarify archive reconstruction vs contemporaneous catalog curation when product copy becomes user-facing. No current no-lookahead defect is demonstrated.
2. **Commit granularity/noise** — connector-based one-file GitHub mutations produced many tiny commits. This is operationally understandable but increases history-reading cost. Prefer grouped mutations when the tool surface safely supports them.
3. **PR narrative staleness** — PR body still emphasizes the first lithium benchmark and contains old unfinished-work prose. Live handoff is correctly authoritative, so this is not a runtime semantic defect, but the PR narrative should eventually be refreshed or deliberately kept clearly non-live.

## Acceptance before storage blind recall resumes

Storage Stage A remains paused until the open-state repair has:

1. full Mypy/Pytest success;
2. real PostgreSQL open-state smoke success with the three negative provenance cases;
3. capability/Repair Memory audits green;
4. exact-head `longcycle/full-ci` success;
5. a new handoff checkpoint restoring the next task to `MEMORY-SEMICONDUCTORS-001` fresh-context blind recall.

No new product feature should be opened during this repair.
