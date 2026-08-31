# Post-Baseline Development

Architecture Baseline v1 changes Longcycle's default engineering posture from architecture exploration to product/domain construction on a stable semantic foundation.

## Before material work

### Single/integration-lane work

1. Read `.longcycle/baseline/current.json` and the referenced manifest/document.
2. Write/update `.longcycle/change-contract/current.json` with the current `intent_id`, goal, `L1/L2/L3/L4`, affected Baseline invariants and acceptance criteria.
3. Run existing Capability Registry admission separately and ensure the Change Contract `intent_id` equals `.longcycle/capabilities/current-admission.json -> intent_id`.
4. Prefer existing owner extension seams. A new industry normally changes Domain Pack/catalog/source/research content, not Evidence/PIT/Reality/Judgment architecture.
5. Query path-scoped Repair Memory before editing known paths.

### Parallel industry/product work

Do **not** let every concurrent Agent rewrite the global current handoff/admission/Change Contract. Create one workstream directory per branch:

```text
.longcycle/workstreams/<workstream-id>/
    reservation.json
    cursor.json
    change-contract.json
    capability-admission.json
```

The refreshed `main` copy of `reservation.json` owns branch, starting `main` SHA, parent goal, `done_when`, existing semantic owners, dependencies, assignment fence and disjoint autonomous write prefixes. The exact remote worker copy of `cursor.json` owns only bounded execution progress and typed request/receipt pointers. This separation prevents a worker from redefining its goal or authority while updating its handoff.

Run:

```bash
python scripts/workstream_registry.py audit
```

The generated `.longcycle/workstreams/active-index.json` is a routing-only global view. See `docs/development/parallel-agent-development.md` for concurrency/integration and `docs/development/remote-worker-continuity.md` for the remote-only startup/recovery/turn-boundary loop. Historical v1 `workstream.json` files are accepted only as already-integrated/closed cold provenance.

Change level and capability disposition answer different questions:

```text
change_level           = how close this change is to the frozen Baseline
capability disposition = which existing semantic owner handles the capability
```

Examples:

```text
L1 + reuse    parser bug or implementation refactor
L2 + extend   new industry predicate, unit, API or Domain Pack
L3 + replace  proposed Baseline semantic-owner change after a real counterexample
L4            mission change; explicit user decision required
```

## L1 / L2 normal path

Agents may implement autonomously. They must keep Baseline-critical semantic regressions green and must not change those tests' expected meaning merely to accommodate new code.

A Change Contract answers:

```text
Intent id:
Goal:
Baseline/version:
Change level:
Existing capability admission / owners:
Baseline impact:
Affected invariant ids:
Schema impact:
Architecture change ref / counterexamples / compatibility / approval (L3/L4 only):
Acceptance:
```

Change Contracts are **one-task authorizations**. Their `intent_id` must match the referenced capability admission. A previous L3 contract cannot remain in place as a standing permission for a later task.

Implementation freedom remains broad: adapters, parsers, UI/CLI/API, domain catalogs, research packets, performance, caches and internal composition may change when the locked semantics remain true.

## L3 architecture pressure

If a real requirement appears to require changing Evidence, Reality/Judgment/Outcome separation, known/valid/system time, no-lookahead, provenance/revision semantics, source authority, source representation states or semantic-owner boundaries:

1. stop ordinary implementation;
2. preserve the concrete source-grounded counterexample or demonstrate the security/consistency defect;
3. identify the Baseline invariant under pressure;
4. show why current extension seams cannot truthfully represent the case;
5. write an Architecture Change Proposal/ADR covering old-data compatibility, migration, PIT/no-lookahead and provenance consequences;
6. obtain explicit architecture review before changing the Baseline and its semantic regressions;
7. release a new Baseline version if approved.

The machine gate requires an L3 contract to name `architecture_change_ref`, non-empty `counterexample_refs`, non-empty `affected_invariants` and `compatibility_plan_ref`. If protected Baseline semantics are actually modified, an `approval_ref` is also required. These fields prove the process exists; independent review still decides whether the real-world evidence is actually sufficient.

`Cleaner`, `more generic`, `future-proof`, framework preference, fewer classes or one industry convenience are not architecture evidence.

## L4 mission pressure

If the proposal changes why Longcycle exists—for example replacing point-in-time industrial memory with a generic RAG/report platform—stop and obtain an explicit user decision before architecture work. L4 carries an explicit approval/user-decision reference.

## Multiple Agents and derived functionality

Parallelize **industries, product surfaces, research packets and implementation**, not the definition of correctness.

Normal concurrent workstreams are limited to:

```text
L1/L2
+
reuse/extend existing Capability Registry owners
+
disjoint branch/path write scopes
```

Shared state is serialized. Baseline files, Strategy/Method, global handoff/admission/Change Contract, Capability Registry cards, canonical migration numbering and shared CI changes belong to the integration lane. A parallel Agent records an `integration_request` instead of directly creating a competing global truth.

New functionality on top of the Baseline should identify what is actually new—UI, calculation, Domain Pack, connector, workflow, forecast/valuation module—while importing stable Evidence/PIT/provenance semantics from existing owners. If two industries independently need the same reusable operation, create a dedicated product/platform workstream rather than letting both invent separate implementations of the same semantic.

## Tests

Baseline-critical tests are part of the contract at the level of **semantic expectation**, not frozen file bytes. Mechanical fixture/import updates are permitted under L1/L2. Changing what a protected regression says is correct requires L3/L4.

The focused `.github/workflows/architecture-baseline.yml` gate validates the Baseline manifest/change contract, capability ownership, parallel-workstream registry and a compact Baseline-critical regression set. `longcycle/full-ci` remains the complete correctness gate.

## Documentation ownership after the freeze

- `STRATEGIC_COMPASS.md`: terminal mission and success criteria.
- `METHODOLOGY_CORE.md`: adopted cross-industry research method.
- `ARCHITECTURE_BASELINE_V1.md` + `.longcycle/baseline/*`: frozen semantic contract and change policy.
- Capability Registry: semantic owners and extension seams.
- `.longcycle/change-contract/current.json`: current **integration-lane** change risk classification only.
- `.longcycle/capabilities/current-admission.json`: current **integration-lane** semantic routing only.
- `.longcycle/handoff/current.json`: project-level horizon/integration cursor, not every parallel Agent's cursor.
- `.longcycle/workstreams/*/reservation.json`: main-owned parallel intent, scope, dependencies, acceptance and writer fencing.
- `.longcycle/workstreams/*/cursor.json`: exact remote worker progress, checkpoint, verification and typed request/receipt pointers.
- `.longcycle/workstreams/active-index.json`: generated compact view of active parallel workstreams.
- code/migrations/tests/live CI: actual implementation state.
- old devlogs, research reports, rehearsal reports and PR discussions: historical provenance; do not rewrite them to match current doctrine.

## Database evolution

Migration `0039` is the schema ceiling **at the v1 tag**, not the last migration forever. The Baseline validator checks the migration ceiling at `architecture-baseline-v1.0.0`; later HEAD migrations are allowed under L1/L2 when they preserve locked semantics.

For concurrent Agents, canonical migration numbering is an integration-lane resource. Parallel workstreams should record a migration integration request rather than independently choosing the same next number. Over time, industry knowledge releases should be separated from global schema capability where useful; that cleanup is normal post-Baseline engineering and is not a freeze prerequisite.
