# Calibrated researcher interpretation

## Why this changed

The tightening review found that Longcycle had correctly protected canonical truth, but some of those protections had been copied too literally into researcher presentation. Three distinct questions had been bundled together:

1. what the source directly proves;
2. what existing grounded structure deterministically entails;
3. what a model/researcher reasonably judges but cannot publish as source truth.

Treating all three as one binary `allowed / forbidden` decision reduced recall and made the product less useful than the underlying memory.

The correction is not to weaken Evidence, no-lookahead or canonical Reality. It is to make the authority class explicit.

```text
DIRECT
  source-grounded canonical semantics

ENTAILED
  deterministic, auditable interpretation from existing grounded premises
  never silently promoted into the canonical source claim

MODEL/JUDGMENT
  explicitly labelled research analysis with reasoning/confidence/context
  never canonical Reality, formal membership truth or backdated historical knowledge
```

No new schema or truth owner is introduced. CAP-0003 remains Reality owner, CAP-0004 remains Judgment/Outcome owner, CAP-0005 owns read/replay interpretation, and CAP-0006 owns research-only model hypotheses/judgments.

## 1. Role, importance and causality are no longer one blanket prohibition

The previous presentation boundary treated value-chain role, participant importance and causality as if they had the same epistemic status. They do not.

A role may sometimes be mechanically entailed from already-grounded structure. For example, a grounded product-state relation plus an unambiguous product/industry ontology can support a deterministic researcher role hint. That is not the same as a model deciding that a company is strategically important.

Participant importance is normally analytical. Causality is usually even more interpretive. Both may be useful and should not be hidden merely because they are not canonical Reality. They belong in the explicitly labelled CAP-0006 MODEL/JUDGMENT lane with reasoning/context/confidence and without truth promotion.

The current explicit-industry-scope discovery rule still does **not** assign a role by itself. Further structural role entailment requires an auditable rule and grounded premises; ambiguous cases stay model-labelled.

## 2. Canonical temporal precision stays strict; researcher time hints become useful

Canonical time remains source-supported. A source saying that a state was true in Q3 does not prove that the state began on July 1. An observation timestamp still does not become an onset timestamp.

Researcher presentation may now add a separate `researcher_time_hint`:

- direct source-supported instant/period;
- direct timeless state;
- entailed `state true as of observation; onset unknown`;
- unknown when no useful temporal premise exists.

The hint is for retrieval, orientation and narration. It cannot overwrite `valid_time`, manufacture an occurrence date or become a persisted Reality merely because it is convenient.

## 3. Related milestones are surfaced without satisfying the original target

CAP-0004 remains strict: a `related_milestone` Outcome is `indeterminate` and timing is not comparable. Mass production cannot silently satisfy a different target such as named-customer qualification.

CAP-0005 now makes the information value explicit. A related milestone can be shown as a positive/meaningful signal while the researcher summary also states that the original target remains not directly resolved.

This removes the old false choice between:

- incorrectly declaring the target realized; or
- hiding a useful later milestone.

## 4. Research-only model analysis is an allowed product lane

CAP-0006 already had immutable research hypotheses with confidence, reasoning, alternative explanations, falsification conditions and indirect Evidence links. That existing owner is now explicitly recognized as the MODEL/JUDGMENT lane for researcher analysis.

Allowed examples include:

- participant importance;
- causal hypotheses;
- ambiguous value-chain role.

The lane is explicitly labelled `model_judgment` / `research_only_current_state`. It cannot create canonical Reality, formal membership truth, or historical market knowledge.

## What did not change

The following remain hard:

- no-lookahead;
- Evidence provenance;
- claim-scoped source authority;
- source-independence semantics;
- Judgment does not become Reality;
- related milestone does not become direct realization;
- canonical temporal precision is not manufactured;
- model analysis is never silently promoted to source truth.

## Remaining deliberate audit item

Deterministic subject discovery still requires explicit `industry_node_id` on the grounded Reality/Judgment in its first rule. That is intentionally not treated as the final answer. The next tightening review should ask whether existing product/facility/entity/taxonomy structure can safely establish industry relevance without requiring every grounded record to repeat the industry tag.
