# Workstream Reservation and Serial Integration

This document tightens the post-Baseline multi-Agent model without introducing distributed locks, schedulers or a second semantic-owner registry.

The core distinction is:

```text
main / integration base = reservation authority
worker branch           = live implementation cursor
integration branch      = only main-bound shared-state writer
```

The purpose is to make parallel Agent autonomy real while preventing an Agent from defining its own write authority after work has started.

## 1. Why declaration alone is insufficient

A branch-local cursor cannot define its own construction zone. For example, an old combined manifest could say:

```text
exclusive_write_prefixes = [domain_packs/banking]
```

but unless CI compares the actual diff with authority outside that worker's control, the worker could also change `domain_packs/shipping` or expand its own scope in the same PR.

Therefore v2 separates the files: refreshed-main `reservation.json` is identity/scope/goal authority, while exact-remote-worker `cursor.json` is bounded execution state. A historical copy of `reservation.json` present in a long-lived producer branch is not a second authority.

## 2. Reservation lifecycle

Before a parallel worker starts:

1. Refresh exact `main` and current Architecture Baseline.
2. Choose a stable workstream id.
3. Choose deterministic branch `workstream/<workstream-id>`.
4. Define existing Capability Registry owners, dependencies and the smallest practical exclusive write prefixes.
5. Add main-owned `reservation.json`, an initial worker `cursor.json`, the local Change Contract and local capability admission through the serial coordinator/integration lane.
6. Rebuild `.longcycle/workstreams/active-index.json` and merge that reservation normally to `main`.
7. Create the worker branch from the main state containing reservation revision 1.

This tiny reservation step is intentionally serial. It is the equivalent of assigning construction zones before multiple crews begin work.

## 3. Reservation and cursor ownership

`reservation.json` on refreshed `main` is entirely coordinator-owned. A worker cannot change these facts and use the change as authority in the same implementation diff:

- `workstream_id`;
- `kind`;
- `lifecycle_state`;
- `branch`;
- `base_main_sha`;
- `baseline`;
- `intent_id` and contract/admission paths;
- `integration_lane`;
- `parent_goal_ref`, `goal` and `done_when`;
- `exclusive_write_prefixes`;
- `target_capability_ids`;
- `dependencies`;
- `reservation_revision`, `assignment_epoch` and `cursor_path`.

Two version fields have distinct meanings:

- `reservation_revision` is the version of the complete main-owned authority contract. Any change to a reservation authority field must advance it by exactly one. A same-revision mutation is invalid, and a revision bump without an authority change is also invalid.
- `assignment_epoch` is the writer-fence generation. It changes only when the coordinator deliberately revokes or reassigns the writer fence. A normal task/stage change does not require an epoch change, although an epoch mutation is itself reservation authority and therefore also requires a new reservation revision.

A task-stage constraint is not automatically a workstream reservation change. If the durable workstream goal/acceptance/scope remains the same, narrow the current stage through the Change Contract, capability admission, dedicated prompt and worker cursor `task_done_when`. Do not rewrite `reservation.done_when` merely to express the next atomic phase.

This is especially important for scope expansion. A worker may discover that it needs a shared module, migration or Capability card, but it must record that as an integration request rather than silently extending its own write zone.

## 4. Branch-local cursor state

The worker updates `cursor.json` on the exact remote producer branch. It may acknowledge the reservation identity/fence and update only bounded progress state, including:

- `reservation_revision` and `assignment_epoch` acknowledged from refreshed main;
- `cursor_sequence` and the acknowledged substantive/WIP checkpoint SHA;
- last completed action, current task, why-now, task-level `task_done_when` and next atomic action;
- progress/partial summary and exact-head verification state;
- typed integration-request, receipt and artifact pointers.

Task-level `task_done_when` may narrow one atomic action but cannot replace the reservation's workstream acceptance. The local Change Contract and capability admission remain intent-bound and still must obey the L1/L2 + reuse/extend policy for parallel work. Startup and interrupted-work repair follow `docs/development/remote-worker-continuity.md`.

## 5. Versioned reservation authority transition

Changing an active reservation is a two-phase transaction, not an in-place edit shared across branches.

### Phase A — main authorization

The serial integration lane:

1. refreshes exact `main` and the worker cursor;
2. changes only the required main-owned reservation authority;
3. advances `reservation_revision` from `N` to exactly `N+1`;
4. changes `assignment_epoch` only when the writer fence is deliberately revoked/reassigned;
5. runs the main-bound reservation-transition gate and exact PR-head CI;
6. merges the new authority to `main`.

After this merge, a worker cursor that still acknowledges revision `N` is expected to stop with an authority-update-pending/fence mismatch. That is a safe transition state, not permission to continue substantive work.

### Phase B — worker adoption

The worker then:

1. refreshes exact `main` and its exact remote worker ref;
2. reads the authoritative reservation from refreshed main rather than treating its branch-local historical copy as authority;
3. updates only `cursor.json` to acknowledge revision `N+1` and the current assignment epoch;
4. pushes the cursor-only acknowledgement;
5. requires exact-head worker continuity/boundary checks to become CLEAN before substantive work resumes.

The worker never edits `reservation.json`, `change-contract.json` or `capability-admission.json` to perform this acknowledgement.

Long-lived producer branches created before this hardening may still contain older verifier/workflow code. Do not blindly advance their reservation revision. Before their first future authority transition, the integration lane must verify that the branch's execution tooling supports base-authority acknowledgement; tool compatibility must not be confused with reservation authority or used to cross-write worker cursor/research state.

## 6. Actual diff gate

For a worker branch, CI reads the authoritative reservation from the refreshed integration base and computes the worker-side changed files against that base. It permits only:

```text
base-reserved exclusive_write_prefixes
+
.longcycle/workstreams/<workstream-id>/
```

The worker cursor must acknowledge the refreshed main `reservation_revision` and `assignment_epoch`. A stale reservation file inherited in branch history is not itself treated as a worker authority mutation; an actual worker commit that changes a main-owned reservation/control file still fails the changed-path gate.

Examples:

```text
reserved: domain_packs/banking
changed:  domain_packs/banking/metrics.json      PASS
changed:  domain_packs/shipping/metrics.json     FAIL
changed:  migrations/0042_bank.sql               FAIL
changed:  .github/workflows/ci.yml               FAIL
```

A shared-path need becomes an `integration_request`.

## 7. Dependency rules

Dependencies are part of the reservation because they influence merge order and reusable capability ownership.

Machine rules:

- every active dependency id must have a registered main-side reservation;
- active dependency edges must be acyclic;
- a workstream cannot be `ready_for_integration` while any dependency is not `integrated` or `closed`.

If Banking and Shipping both discover the same Scenario Engine requirement, the coordinator registers one product/platform workstream and both industry workstreams depend on it. They do not build two local Scenario Engines.

## 8. Worker branches are producer branches

`workstream/<id>` does not merge directly to `main`.

That rule prevents worker PRs from becoming accidental writers of:

- generated active indexes;
- canonical migration numbering;
- global Capability cards;
- global handoff/admission/Change Contract;
- shared CI configuration;
- other integration-only state.

Worker pushes receive the Architecture Baseline/workstream boundary checks. A worker may also target an integration branch for review, but the final main-bound PR is owned by the one active `global_serial` integration lane.

## 9. Integration lifecycle

When one or more workers are ready:

1. The integration Agent refreshes exact `main`.
2. It verifies that worker diffs still fit the registered reservations and that dependencies are satisfied.
3. It creates/uses the one active global-serial integration branch.
4. It imports the ready worker changes.
5. It resolves typed request files referenced by worker `integration_request_refs`.
6. It allocates canonical migration numbers only now.
7. It updates global Capability cards/control-plane files only when required by the admitted integration task.
8. Any active reservation authority mutation uses the versioned transaction in section 5.
9. It updates workstream status and rebuilds `active-index.json` in the same integration change when required.
10. It runs Architecture Baseline + full CI on the exact integration head.
11. It merges normally to `main`.
12. It closes/integrates completed workstreams and updates the project-level handoff only when project direction or the next integration task changes.

## 10. New functionality on Baseline v1

Feature/domain workers default to composition of existing semantic owners:

```text
Evidence / PIT / provenance / Reality-Judgment-Outcome
                     ↓
         domain or product extension
```

They may add parsers, domain packs, calculations, source adapters, research views, forecast/valuation surfaces or other L1/L2 functionality inside reserved paths.

Cross-domain reuse pressure creates a product/platform workstream, not a new Core definition.

Only a real source-grounded counterexample or a demonstrated consistency/security defect can escalate the shared semantic model to L3.

## 11. Failure and recovery

If a worker discovers it needs a path outside its reservation:

```text
stop that edit
→ record integration_request
→ preserve the reason/evidence
→ coordinator decides whether to expand reservation, create a shared product workstream, or handle it in integration
```

If two reserved scopes collide, do not add a runtime lock. Resolve the ownership boundary in the registry before work continues.

If `main` advances without changing this worker's reservation revision/fence, workers refresh/recheck normally. If the reservation revision/fence changes, the worker performs the phase-B cursor acknowledgement before substantive work. Repository strict/up-to-date required checks remain the final hosting-level protection against merging a previously green but now stale main-bound integration PR.

## Governing rule

> Main owns versioned reservation authority. Workers acknowledge that authority through the cursor, implement only inside reserved zones, and may never redefine their own authority in the same step. Shared state enters main only through the serial integration lane.
