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

MANY worker control planes
    one reserved workstream id/scope on main
    one deterministic workstream/<id> producer branch
    one branch-local live cursor
    one local Change Contract
    one local capability admission

ONE serial integration lane
    worker reservation changes
    shared/global control-plane edits
    canonical migration numbering
    capability-card changes
    L3/L4 architecture or mission work
    main-bound integration PRs
```

The detailed reservation/integration mechanics are defined in `docs/development/workstream-reservation-integration.md`.

## 1. Global handoff vs workstream handoff

A single mutable `.longcycle/handoff/current.json` works for one active Agent, but it becomes a write hotspot with concurrent development. The global handoff therefore remains only the **project-level horizon/integration cursor**. It summarizes project direction, active workstreams and the current integration lane.

Ordinary worker Agents do not continuously rewrite the global handoff. Detailed continuation state belongs in `.longcycle/workstreams/<workstream-id>/workstream.json` on that worker's branch.

## 2. Reservation authority and branch-local cursor

Each workstream uses:

```text
.longcycle/workstreams/<workstream-id>/
    workstream.json
    change-contract.json
    capability-admission.json
```

There are two copies with different roles during parallel development:

```text
integration-base/main copy  = reservation authority
worker branch copy          = live continuation cursor
```

Before implementation begins, the coordinator serially registers the workstream on `main` (or the current integration base), including its branch, Baseline, semantic-owner routing, dependencies and exclusive write prefixes. Then the worker branch `workstream/<workstream-id>` is created or synchronized from that registered base.

The worker may update progress/cursor state inside its own workstream directory, but it may not expand reserved identity/scope/dependencies in the same implementation change. Scope or dependency changes are registered on the integration base first.

This prevents a worker from editing its own permission manifest and using that edit as immediate authority.

## 3. Parallel lane rules

A normal concurrent worker must satisfy all of the following:

```text
change level = L1 or L2
capability disposition = reuse or extend
integration lane = parallel
branch = workstream/<workstream-id>
reservation already exists on integration base
actual diff stays inside reserved write prefixes
exclusive write scope does not overlap another active parallel workstream
```

A parallel Agent may read the whole repository but may autonomously modify only:

```text
base-reserved exclusive_write_prefixes
+
.longcycle/workstreams/<workstream-id>/
```

It may not own global control-plane paths such as Architecture Baseline files, Strategy/Method Core, global handoff/admission/Change Contract, Capability Registry cards/index, canonical `migrations/`, shared CI workflows, `pyproject.toml`, or the generated workstream active index.

When one of those must change, the worker records an `integration_request` instead of editing shared state.

## 4. Serial integration lane

Only one active `global_serial` workstream is allowed.

The serial lane handles:

- registering/changing worker reservations;
- L3/L4 changes;
- `replace` / `new` semantic-owner work;
- shared Capability Registry card changes;
- canonical migration numbering;
- global CI/rules/governance changes;
- resolving integration requests from multiple workers;
- rebuilding global workstream indexes;
- final main-bound integration and project-level handoff sync.

This bottleneck is intentional. Product/domain construction stays parallel; shared definitions and mainline integration stay serialized.

## 5. Dependency graph

Dependencies are part of the reservation because they determine reusable capability ownership and integration order.

Machine rules require:

- every active dependency id to have a registered workstream manifest;
- active dependency edges to be acyclic;
- a workstream marked `ready_for_integration` to depend only on workstreams already `integrated` or `closed`.

If Banking and Shipping both need the same reusable Scenario Engine, register one product/platform workstream and make both industry workstreams depend on it. Do not let both build local copies.

## 6. Migration rule for multiple Agents

Parallel Agents must not independently guess the next global migration number.

Bad:

```text
Banking worker  → migrations/0040_bank_schema.sql
Shipping worker → migrations/0040_shipping_schema.sql
```

Instead:

1. the worker records `integration_requests: ["migrations"]`;
2. it may keep a schema/migration proposal inside its reserved domain/workstream path;
3. the serial integration Agent refreshes latest `main` and allocates the next canonical migration number;
4. PostgreSQL migration/integration tests run on the exact integration head before merge.

Domain knowledge that does not require database capability change should prefer versioned Domain Pack/catalog releases rather than global schema migrations.

## 7. Lifecycle

### Reserve

Coordinator/integration Agent:

1. refreshes live `main` and Baseline;
2. chooses workstream id, deterministic `workstream/<id>` branch, existing semantic owners, dependencies and the smallest useful write scope;
3. creates the workstream manifest + local Change Contract + local capability admission in a serial registration change;
4. rebuilds/audits the active workstream index;
5. merges the reservation normally to `main`;
6. creates/synchronizes the worker branch from the registered main state.

### Develop

Worker Agent:

1. boots from global Strategy/Method/Baseline plus its own workstream files;
2. works only inside the reserved scope;
3. runs focused tests and the worker boundary gate;
4. records shared-path needs as integration requests;
5. updates its own branch-local cursor at coherent boundaries;
6. does not directly target `main` for merge.

### Ready for integration

A worker may become `ready_for_integration` only when:

- `done_when` is met;
- local/focused tests are green;
- unresolved integration requests are explicit;
- actual diff still fits the base reservation;
- all declared dependencies are integrated/closed;
- Baseline semantics have not been silently reinterpreted.

### Integrate

The one active integration Agent:

1. refreshes latest `main`;
2. verifies worker diffs against registered reservations;
3. imports one or more ready worker outputs into the global-serial integration branch;
4. resolves shared integration requests and canonical migration numbering;
5. updates workstream status and generated active index in the same integration change;
6. runs Architecture Baseline Gate + full CI on exact integration head;
7. merges normally to `main`;
8. updates project-level handoff only when integration changes the next project-level task or direction.

Worker branches are producer branches. The final main-bound PR belongs to the serial integration lane.

## 8. New industries

Different industries are naturally parallel when writes remain domain-local:

```text
workstream/banking-domain-v1
    research/domain assets for banking

workstream/shipping-domain-v1
    research/domain assets for shipping

workstream/pharma-domain-v1
    research/domain assets for pharma
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

## 9. New functionality derived from Baseline v1

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
3. Which Baseline invariants remain unchanged?
4. What negative tests prove the feature did not reinterpret Evidence/PIT/provenance?
5. What paths can this Agent reserve without colliding with active workstreams?

A useful pattern remains domain-local first. Promote it into a reusable product/platform capability only when a second independent domain needs the same operation or there is clear product value. Promotion still routes through existing semantic ownership; it does not become Core merely because abstraction is possible.

## 10. Escalation to L3

Parallel development stops only for the Baseline-changing portion when a real important case cannot be truthfully represented.

```text
parallel workstream
→ preserve source-grounded counterexample/evidence
→ record integration request
→ stop Baseline-changing implementation
→ open one global_serial L3 workstream
→ ADR + compatibility/PIT/provenance analysis + independent review
```

The worker may continue unrelated L1/L2 work inside its reservation, but it must not create a local semantic fork.

## Operational principle

> Parallelize facts, industries, product surfaces and implementation. Reserve authority before work starts. Serialize semantic ownership, scope changes and mainline integration.

This allows many Agents to move quickly without turning Longcycle into many subtly different Longcycles.
