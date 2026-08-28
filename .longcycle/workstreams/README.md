# Longcycle Workstream Control Plane

Parallel workstreams are branch-local continuation units under one global Architecture Baseline / Strategy / Capability Registry control plane.

See `docs/development/parallel-agent-development.md` for the broader model and `docs/development/workstream-reservation-integration.md` for the machine-enforced reservation/integration lifecycle.

## Directory template

```text
.longcycle/workstreams/<workstream-id>/
    workstream.json
    change-contract.json
    capability-admission.json
```

Example `workstream.json`:

```json
{
  "schema_version": "longcycle-workstream/v1",
  "workstream_id": "banking-domain-v1",
  "kind": "industry",
  "status": "active",
  "integration_lane": "parallel",
  "branch": "workstream/banking-domain-v1",
  "base_main_sha": "0123456789abcdef0123456789abcdef01234567",
  "baseline": "architecture-v1",
  "intent_id": "BANKING-DOMAIN-V1-001",
  "change_contract_path": ".longcycle/workstreams/banking-domain-v1/change-contract.json",
  "capability_admission_path": ".longcycle/workstreams/banking-domain-v1/capability-admission.json",
  "parent_goal_ref": "strategic_horizon.medium_term_goal",
  "goal": "Build a banking Domain Pack on existing Evidence/PIT/Reality/Judgment semantics.",
  "done_when": "Representative banking trajectories replay without lookahead and all source-derived values remain traceable.",
  "next_atomic_action": "Ground the first bounded banking source/metric packet.",
  "required_capability": "high_capability_reasoning",
  "target_capability_ids": ["CAP-0002", "CAP-0003", "CAP-0005"],
  "exclusive_write_prefixes": [
    "research_data/memory/banking",
    "domain_packs/banking",
    "tests/banking"
  ],
  "integration_requests": [],
  "dependencies": []
}
```

The SHA is illustrative only. `base_main_sha` records the main commit from which the workstream was admitted/started; live merge freshness is still checked at integration time.

## Reservation-first rule

A parallel worker does not grant itself write authority. Before implementation starts, the coordinator/integration lane registers the workstream manifest + local contract/admission on `main` (or the current integration base) and rebuilds the active index. Only then is the deterministic worker branch `workstream/<workstream-id>` created/synchronized.

The integration-base manifest is the reservation authority for:

- workstream id and kind;
- worker branch name;
- Architecture Baseline id;
- integration lane;
- `exclusive_write_prefixes`;
- target Capability Registry owners;
- dependencies.

The worker copy remains the live cursor for progress fields such as status, `done_when`, next action and integration requests. If the worker needs a larger write scope, different owner routing or dependency change, that reservation changes on the integration base first; the worker cannot expand its own authority in the same implementation diff.

## Worker rules

- `parallel` workstreams are L1/L2 + `reuse/extend` only.
- Parallel worker branch name is exactly `workstream/<workstream-id>`.
- Actual changed files must stay inside the base-reserved `exclusive_write_prefixes` plus that workstream's own `.longcycle/workstreams/<id>/` control directory.
- Parallel write scopes must remain disjoint across active workstreams.
- Global Baseline/Strategy/Method, global handoff/admission/Change Contract, Capability cards/index, canonical `migrations/`, shared CI workflows, `pyproject.toml`, and the generated workstream active index are integration-lane resources.
- A parallel Agent records shared needs under `integration_requests` instead of claiming those paths.
- Active dependencies must be registered and acyclic. A workstream cannot become `ready_for_integration` while a dependency is still planned/active/blocked/ready.
- Worker branches are producer branches; they do not merge directly to `main`.

## Integration rule

One `global_serial` integration workstream owns the main-bound integration step. It takes one or more ready worker outputs, refreshes latest `main`, resolves shared migrations/capability/global-control requests, rebuilds the workstream active index, runs full CI + Architecture Baseline gates on the exact integration head, and merges normally.

This keeps industry/product implementation parallel while keeping semantic ownership and shared repository state serial.
