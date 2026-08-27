# Deterministic researcher discovery broadening

## Why this changed

A researcher-entry defect exposed an over-tight certainty rule: CAP-0005 first required an entity to have a visible `core.industry_entity_memberships` row, and only then asked the typed memory reader for that entity's Reality / Judgment / Outcome. A missing membership projection could therefore hide already-grounded industrial memory.

That is the wrong failure mode. Lack of one dedicated catalog predicate is not evidence that the entity is irrelevant to the industry.

## Semantic correction

Researcher **discoverability** now has two deterministic provenance classes:

1. **direct** — a visible source-grounded `industry.membership` catalog projection;
2. **entailed** — already-grounded Reality or Judgment explicitly carries the target `industry_node_id`, so the entity is mechanically discoverable for that industry at the same knowledge cutoff.

The second class is a recall entailment, not a truth promotion. It does not create an `industry.membership` Fact, assign a value-chain role, rank importance, assert causality, manufacture controversy, or invent historical timing.

The direct / entailed distinction is preserved in the researcher output through `discovery_certainty` and `discovery_bases`.

## Architecture

Before:

```text
industry membership row
    -> subject universe
        -> typed memory snapshot
            -> orientation / open states
```

After:

```text
direct membership -----------+
                              +-> CAP-0005 subject universe
industry-scoped grounded ----+       -> typed memory snapshot
Reality / Judgment                   -> orientation / open states
```

CAP-0003 remains the owner of accepted Reality and membership truth. CAP-0004 remains the owner of Judgment. CAP-0005 owns only the deterministic researcher discovery/read composition.

## No-lookahead

Both direct and entailed discovery use the same researcher `knowledge_cutoff`. A future-known membership or future-known grounded memory record cannot make a subject visible before it was knowable.

## Known remaining conservatism

This repair removes the dedicated-membership-row gate, but the first entailed rule still requires **explicit industry scope** on the grounded record. It does not yet claim that arbitrary product/state facts can always be mapped to an industry through common-sense ontology reasoning.

That remaining boundary should be audited deliberately. Candidate future relaxations should distinguish:

- deterministic structural entailment, such as a grounded product/facility relation whose existing ontology unambiguously maps to one industry;
- genuinely ambiguous semantic classification, which may require a model and must remain labelled as such.

The objective is not maximum strictness. The objective is high recall with auditable reasoning and no silent promotion of inference into source fact.
