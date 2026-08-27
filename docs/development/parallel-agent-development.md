# Parallel Agent Development on Architecture Baseline v1

Longcycle may run multiple industry/product Agents concurrently after Architecture Baseline v1, but concurrency must not create multiple competing sources of truth for mission, Baseline semantics, semantic ownership or mainline continuation state.

The design is deliberately asymmetric:

```text
ONE global control plane
    Strategy / Method Core
    Architecture Baseline
    Capability Registry cards
    main branch + required CI
    global handoff/current.json

MANY branch-local workstream control planes
    one branch per workstream
    one workstream manifest/cursor
    one local Change Contract
    one local capability admission
    disjoint autonomous write scope

ONE serial integration lane
    shared/global control-plane edits
    canonical migration numbering
    capability-card changes
    L3/L4 architecture or mission work
    final mainline handoff sync
```

This keeps Agent concurrency in product/domain construction while preserving one definition of correctness.

## 1. Why the global handoff must stop being every Agent's cursor

A single mutable `.longcycle/handoff/current.json` works for one active Agent, but it becomes a write hotspot with concurrent development:

```text
Banking Agent updates current task
Shipping Agent updates current task
Product Agent updates current task
→ last writer wins
→ unrelated Agents erase each other's continuation state
```

Therefore the main handoff changes role after parallel development starts:

- it remains the **project-level horizon/integration cursor**;
- it summarizes active workstreams and priorities;
- it is updated by the integration/mainline Agent when project-level direction changes or workstreams integrate;
- ordinary parallel Agents do **not** continuously rewrite it.

Detailed continuation state belongs in the workstream itself.

## 2. Per-workstream files

Each concurrent workstream uses a dedicated directory:

```text
.longcycle/workstreams/<workstream-id>/
    workstream.json
    change-contract.json
    capability-admission.json
```

`workstream.json` is the branch-local handoff/cursor. It declares:

- workstream id/kind/status;
- its branch and the `main` SHA it started from;
- current Architecture Baseline id;
- one `intent_id` shared by all three files;
- parent goal, goal, `done_when`, next atomic action;
- required Agent capability;
- existing target Capability Registry owners;
- autonomous `exclusive_write_prefixes`;
- `integration_requests` for shared/global paths;
- dependencies on other workstreams;
- `parallel` or `global_serial` integration lane.

The workstream registry validates these manifests and generates `.longcycle/workstreams/active-index.json` as a compact project-wide view.

## 3. Parallel lane rules

A normal concurrent workstream must satisfy all of the following:

```text
change level = L1 or L2
capability disposition = reuse or extend
integration lane = parallel
branch != main
exclusive write scope does not overlap another active parallel workstream
```

A parallel Agent may read the whole repository but should autonomously modify only its declared exclusive write prefixes.

It may not own global control-plane paths such as:

- Architecture Baseline manifests/documents;
- Strategy / Method Core;
- global `.longcycle/handoff/current.json`;
- global current capability admission / Change Contract;
- Capability Registry cards/index;
- canonical `migrations/` numbering;
- shared mainline CI workflows.

When a workstream discovers that one of those must change, it records an `integration_request` instead of silently editing the shared control plane.

## 4. Serial integration lane

Only one active `global_serial` workstream is allowed.

The serial lane handles:

- L3/L4 changes;
- `replace` / `new` semantic-owner work;
- shared Capability Registry card changes;
- canonical migration numbering;
- global CI/rules/governance changes;
- resolving integration requests from multiple branches;
- final main handoff/current-admission/current Change Contract sync.

This is intentionally a bottleneck for correctness-sensitive shared state. Product/domain research remains parallel; the definition of correctness remains serialized.

## 5. Migration rule for multiple Agents

Parallel Agents must not independently guess the next global migration number.

Bad:

```text
Banking branch  → migrations/0040_bank_schema.sql
Shipping branch → migrations/0040_shipping_schema.sql
```

Instead:

1. the workstream records `integration_requests: ["migrations"]`;
2. it may keep a local schema/migration proposal under its own workstream/domain path;
3. when ready for integration, the serial integration Agent rebases/merges latest `main` and assigns the next canonical migration number;
4. PostgreSQL migration/integration tests run on the resulting exact branch head before merge.

Domain knowledge that does not require database capability change should prefer versioned Domain Pack/catalog releases rather than global schema migrations.

## 6. Integration lifecycle

### Start

Coordinator/integration Agent:

1. refreshes live `main` and Baseline;
2. creates a branch from exact `main`;
3. creates the workstream directory + local Change Contract + local capability admission;
4. declares disjoint write scopes and dependencies;
5. rebuilds/audits workstream active index.

### Develop

Workstream Agent:

1. boots from global Strategy/Method/Baseline;
2. reads only its workstream manifest + local contract/admission as dynamic task state;
3. works inside declared write scope;
4. runs focused tests;
5. records shared-path needs as integration requests;
6. updates only its own branch-local workstream cursor at coherent boundaries.

### Ready for integration

The workstream becomes `ready_for_integration` only when:

- `done_when` is met;
- its local tests are green;
- unresolved integration requests are explicit;
- it has not silently modified Baseline semantics;
- live main drift has been inspected.

### Integrate

Integration Agent:

1. refreshes latest main;
2. integrates/rebases the workstream against current main;
3. resolves integration requests and canonical migration numbering;
4. detects semantic/path conflicts with other workstreams;
5. runs Architecture Baseline Gate + full CI on exact integration head;
6. merges normally;
7. marks the workstream integrated/closed and rebuilds active index;
8. updates project-level handoff only when the integrated result changes what the next project-level Agent should do.

## 7. How new industries should parallelize

Different industries are naturally parallel when their writes are mostly domain-local:

```text
workstream/banking
    domain/research/catalog assets for banking

workstream/shipping
    domain/research/catalog assets for shipping

workstream/pharma
    domain/research/catalog assets for pharma
```

All import the same locked semantics:

```text
Evidence
Reality / Judgment / Outcome
PIT / no-lookahead
source authority
provenance/versioning
```

They must not fork those semantics into industry-specific copies.

If two industries independently reveal the same missing reusable product capability, do not let both invent it. Open a separate product/platform workstream with one existing semantic owner and make the industry workstreams depend on it.

## 8. How Agents derive new functionality from the Baseline

A new feature should normally be an L1/L2 **extension surface**, not a new architecture.

Examples:

```text
new valuation UI             → product workstream, L2 + reuse/extend
banking Domain Pack          → industry workstream, L2 + reuse/extend
new source connector         → platform/product workstream, L1/L2 + reuse
new forecast module          → product/domain workstream, L2 + extend
new research workspace view  → product workstream, L2 + reuse/extend
```

Every feature workstream must answer:

1. Which existing Capability Registry owner supplies each stable semantic?
2. What is genuinely new: UI, domain catalog, calculation, adapter, workflow or research surface?
3. Which Baseline invariants must remain unchanged?
4. What negative tests prove the feature did not reinterpret Evidence/PIT/provenance?
5. What paths can this Agent own without colliding with other active workstreams?

A feature Agent may compose existing semantics; it may not copy them into a second local truth system.

### Promotion rule

A useful pattern discovered inside one industry remains domain-local first.

Promote it into a reusable product/platform capability only when there is concrete reuse pressure (for example a second independent domain needs the same semantic operation) or clear product value. Promotion still routes through the existing Capability Registry owner. Do not move concepts into Core merely because abstraction appears possible.

## 9. Escalation to L3

Parallel development stops if a feature or industry discovers that the Baseline cannot truthfully represent a real important case.

Then:

```text
parallel workstream
→ preserve counterexample/evidence
→ record integration request
→ stop Baseline-changing implementation
→ open one global_serial L3 workstream
→ ADR + compatibility/PIT/provenance analysis + independent review
```

The original industry workstream may continue unrelated L1/L2 work, but it must not locally fork the Baseline to work around the unresolved case.

## 10. Operational principle

The concurrency rule is:

> Parallelize facts, industries, product surfaces and implementation. Serialize semantic ownership, Architecture Baseline changes and shared integration state.

This lets many Agents move quickly without turning Longcycle into many subtly different Longcycles.
