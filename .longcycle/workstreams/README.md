# Longcycle Workstream Control Plane

Parallel workstreams are branch-local continuation units under the single global Architecture Baseline / Strategy / Capability Registry control plane.

See `docs/development/parallel-agent-development.md` for the full protocol.

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
    "domain_packs/banking"
  ],
  "integration_requests": [],
  "dependencies": []
}
```

The example SHA is illustrative only; real workstreams use the exact live `main` SHA from which their branch was created.

## Rules

- `parallel` workstreams are L1/L2 + `reuse/extend` only.
- `global_serial` is required for L3/L4 or `replace/new` semantic ownership.
- Parallel write scopes must be disjoint.
- Global Baseline/Strategy/Method, global handoff/admission/Change Contract, Capability cards/index, canonical `migrations/`, shared CI workflows, `pyproject.toml`, and the generated workstream active index are integration-lane resources.
- A parallel Agent records shared needs under `integration_requests` instead of claiming those paths.
- Workstream manifest, local Change Contract and local capability admission share the same `intent_id`.
- The integration/coordinator lane runs `python scripts/workstream_registry.py rebuild-index`; parallel branches normally run `python scripts/workstream_registry.py validate`.
