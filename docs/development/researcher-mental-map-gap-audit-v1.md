# Researcher Industry Mental-Map Gap Audit v1

## Purpose

This is the bounded product-gap audit required by the live continuation cursor after the researcher-readable point-in-time trajectory proof.

The acceptance standard comes from `STRATEGIC_COMPASS.md`: a first-time researcher should be able to build a defensible industry mental map quickly — structure and participants, real drivers and constraints, historical trajectories, contemporaneous disputes/Judgments, later Outcomes, evidence boundaries, and explicit unknowns — without first reconstructing the industry manually from raw artifacts.

This audit does **not** create new source research, promote Memory Leads/search discovery into Evidence, or admit a new semantic owner merely because a researcher-facing composition is missing.

## Authority and observation boundary

- Capability ownership is taken from `.longcycle/capabilities/active-index.json` and the owning cards.
- Product behavior is checked against the current `longcycle research replay` CLI and `build_researcher_trajectory_view` surface.
- The lithium `UP-CHEMICALS-SV-001` discovery run is used only as a **non-pharma observation fixture**. Its own manifest says the output is discovery-complete but Evidence is not archived, and it forbids Fact/Judgment/publishable-truth promotion. Nothing in that discovery artifact is treated here as publishable industry truth.
- BLENREP/ADC is not used to justify another subject-storyline extension.

## Mental-map requirement audit

| Researcher requirement | Status | Existing owner(s) | What is already true | Product gap |
| --- | --- | --- | --- | --- |
| Value-chain / participant structure | **Partially served** | CAP-0003 + CAP-0005 | Longcycle has typed entities/industry subjects and can replay Reality for explicitly selected subjects. Fact values can also retain entity identity when the source supports an entity-valued assertion. | The product entrypoint does not discover or name the important subjects for an industry, expose their roles/relationships, or let a first-time researcher start from an industry and learn what to inspect. `research replay` requires the caller to already supply subject/industry-node UUIDs. |
| Key drivers and constraints | **Partially served** | CAP-0003 + CAP-0004 | Reality can hold grounded state; Judgment rationale supports premise/mechanism/condition/risk/caveat/counterargument and links back to facts/evidence. | There is no industry-level read projection that assembles already-grounded driver/constraint context across subjects. Presentation must not infer causality merely from co-occurrence or predicate names. |
| Long historical trajectories | **Served for selected subjects** | CAP-0005 | Typed no-lookahead replay, knowledge progression, and researcher trajectory entries are implemented and runtime-proven. | The researcher still needs to know which subjects matter before this capability becomes useful as an industry entry experience. |
| Contemporaneous Judgment, disagreement and revision | **Partially served at industry level** | CAP-0004 + CAP-0005 | Judgment identity, rationale, `revises`/`contradicts`/other typed relations, and immutable historical storylines exist. | The current surface is Judgment-centered after subject selection; there is no industry orientation that surfaces where the important disputes/revision chains are across the relevant subject set. |
| Later Outcome | **Served for selected Judgments** | CAP-0004 + CAP-0005 | Outcome semantics, direct-vs-related distinction, timing comparability, and no-rewrite presentation are implemented and proven. | Same orientation gap: Outcomes are useful once the researcher has already found the relevant historical Judgment/subject. |
| Evidence drill-down | **Partially served** | CAP-0001 + CAP-0002 + CAP-0003/4/5 | Grounded Evidence owns claim-scoped source linkage, and replay preserves EvidenceFragment IDs on Reality/Judgment/Outcome records. | `research replay` exposes identifiers, not a researcher-oriented source/evidence drill-down path with source identity and claim-scoped readable context. The semantic owner already exists; this is a read/composition gap, not a reason to duplicate Evidence semantics. |
| Explicit unknowns / controversy | **Partially served in primitives; missing as a product projection** | CAP-0003 + CAP-0004 + CAP-0006 | Contradicting/caveat Evidence roles, Judgment counterarguments/contradiction relations, conflict/research mechanisms, and research-only unresolved questions exist in their owning layers. | The researcher surface does not give one truthful industry-level view of: archived contradiction, unresolved typed conflict, research-only open question, and simple absence of coverage. These states must remain distinct; `not_found != false`. |

## Non-pharma transfer observation: lithium UP-CHEMICALS

`UP-CHEMICALS-SV-001` is useful precisely because it is **not** a completed publishable trajectory. The bounded discovery run already contains the kinds of structure a researcher needs to reason about an industry:

- Kwinana and Kemerton project expectation-revision chains;
- distinctions among construction completion, commissioning, qualification, first product, stable commercial output and nameplate ramp;
- a contemporaneous hydroxide/high-nickel thesis plus a negative revision and competing scenario framing;
- effective-supply-vs-nameplate mechanisms and a reverse/counterexample search;
- contract-vintage / margin-timing questions;
- explicit supporting tests, contradicting tests and unresolved questions.

But these are organized as query-family research artifacts. A researcher must still manually stitch actors, projects, mechanisms, disputes and unknowns into an industry map before deciding which Evidence-backed trajectories to inspect. That friction survives outside pharma and therefore is not an ADC-specific presentation complaint.

The observation also sets an important boundary: an industry orientation surface must never display these discovery summaries as if they were canonical Reality. It may surface research-only unknowns or discovery leads only with their authority class intact.

## Highest-value product gap

The single highest-value cross-industry gap is:

> **Industry-level researcher orientation above subject-level replay.**

Today the strongest product surface begins after the researcher already knows the subject UUIDs worth replaying. The missing step is the one a first-time researcher needs first: “What are the important things in this industry, what kind of historical memory do we have for each, where are the main grounded disputes/unknowns, and where should I drill down?”

This is more important than adding another CAP-0005 storyline field because it shortens the path from an unfamiliar industry to a defensible mental model.

## Capability admission decision

**Classification: EXTEND CAP-0005; do not create a new capability yet.**

Reasoning:

1. The missing behavior is a researcher-facing, read-only projection/navigation layer over already-owned semantic records.
2. CAP-0005 explicitly owns researcher-readable projections over an already-filtered typed snapshot and permits new read-only CLI/API/UI projections that do not reimplement knowledge visibility.
3. CAP-0001/2/3/4 remain the truth owners for source identity, Evidence, Reality, Judgment and Outcome. CAP-0006 remains the owner of research-only Memory/verification state.
4. A new capability would be justified only if implementation proves that an essential cross-industry semantic fact — for example, source-grounded participant role/relationship identity — cannot be represented truthfully by any existing owner. The presentation gap alone is not that proof.

## Exactly one next implementation target

Extend CAP-0005 with a **read-only industry orientation projection and researcher entrypoint** that starts from an industry identity rather than a pre-known subject UUID list.

The first bounded contract should answer, without inference:

1. Which named/typed subjects are available for the industry at the requested knowledge cutoff, and how much typed Reality/Judgment/Outcome memory is available for each?
2. Which already-typed Judgment revision/contradiction chains or Reality conflict markers deserve attention?
3. Which Evidence references are available for drill-down?
4. Which explicit unknown/open states can be shown **only when an owning typed artifact actually records them**, keeping archived conflict, research-only open question, and lack of coverage separate?
5. Which subject IDs link directly into the existing CAP-0005 trajectory replay?

### Hard boundaries

- Do not infer value-chain roles, causal drivers, participant importance, consensus, controversy, or unknowns from filenames, row counts, co-occurrence, or prose-generation heuristics.
- Do not move source/Evidence/Reality/Judgment/Outcome authority into CAP-0005.
- Do not create a second knowledge-cutoff filter; orientation must consume the existing typed no-lookahead boundary.
- Do not require raw PDF materialization when claim-relevant content is already truthfully content-verified.
- Do not collect new sources merely to make the orientation demo richer.
- If a truthful industry-to-subject discovery relation is absent from existing semantics, stop at that demonstrated semantic gap instead of fabricating a relation in presentation code.

## Done / stop condition for this audit

This audit is complete because every Strategic Compass mental-map requirement is classified against an owner, a non-pharma observation demonstrates the researcher friction, and exactly one next implementation target has been admitted without inventing a parallel semantic owner.
