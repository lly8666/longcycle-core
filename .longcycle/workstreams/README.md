# Longcycle Workstream Control Plane

Parallel workstreams are durable, repository-backed roles under one global Strategy / Architecture Baseline / Capability Registry control plane. Agent instances are disposable executors. A returning Agent and a genuinely Fresh Agent recover the same state from refreshed remote refs; chat and local-only work are not authority.

Read `docs/development/parallel-agent-development.md` for the role/lane model, `docs/development/remote-worker-continuity.md` for the remote startup/recovery transaction, and `docs/development/workstream-reservation-integration.md` for serial reservation/integration mechanics.

## v2 directory contract

```text
.longcycle/workstreams/<workstream-id>/
    reservation.json             # refreshed main owns intent and permission
    cursor.json                  # exact remote worker ref owns execution progress
    change-contract.json
    capability-admission.json
    requests/                    # typed cross-workstream/shared-control requests
    receipts/                    # verification, effect and completion pointers
    escalations/                 # only for unresolved L3/L4 decisions
```

Active workstreams must use v2. A historical `workstream.json` using `longcycle-workstream/v1` is accepted only when already `integrated` or `closed`; it is cold provenance, not an active continuation surface. Never place both formats in one workstream directory.

## Main-owned reservation

`reservation.json` uses `longcycle-workstream-reservation/v2`. The copy read directly from refreshed remote `main` is authoritative. An illustrative reservation is:

```json
{
  "schema_version": "longcycle-workstream-reservation/v2",
  "workstream_id": "banking-domain-v1",
  "kind": "industry",
  "lifecycle_state": "active",
  "integration_lane": "parallel",
  "branch": "workstream/banking-domain-v1",
  "base_main_sha": "0123456789abcdef0123456789abcdef01234567",
  "baseline": "architecture-v1",
  "intent_id": "BANKING-DOMAIN-V1-001",
  "reservation_revision": 1,
  "assignment_epoch": 1,
  "cursor_path": ".longcycle/workstreams/banking-domain-v1/cursor.json",
  "change_contract_path": ".longcycle/workstreams/banking-domain-v1/change-contract.json",
  "capability_admission_path": ".longcycle/workstreams/banking-domain-v1/capability-admission.json",
  "parent_goal_ref": ".longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
  "goal": "Build a banking Domain Pack on existing Evidence/PIT/Reality/Judgment semantics.",
  "done_when": "Representative banking trajectories replay without lookahead and every source-derived value remains traceable.",
  "target_capability_ids": ["CAP-0002", "CAP-0003", "CAP-0005"],
  "exclusive_write_prefixes": [
    "research_data/memory/banking",
    "domain_packs/banking",
    "tests/banking"
  ],
  "dependencies": []
}
```

The SHA is illustrative. `base_main_sha` records admission origin, not current merge freshness. `reservation_revision` changes when reserved intent/scope/dependencies change. `assignment_epoch` changes when the coordinator deliberately revokes or reassigns the single-writer fence, not for routine Fresh-Agent replacement.

The main reservation exclusively owns:

- identity, kind, branch, Baseline and integration lane;
- `lifecycle_state`: exactly `active`, `integrated` or `closed`;
- parent goal, workstream goal and workstream `done_when`;
- Change Contract, capability routing, dependencies and write prefixes;
- reservation revision, assignment epoch and cursor path.

A worker cannot grant itself permission, redefine success or declare itself integrated. Any material change to those facts is registered on the serial integration base first.

The causal route has six links: terminal mission -> long-term direction -> global medium-term goal -> global short-term goal -> reserved workstream milestone -> current atomic task. The five project-level horizons keep their existing owners; `reservation.json` adds execution ownership between global short term and the cursor rather than replacing the global short-term goal.

## Remote branch-local cursor

`cursor.json` uses `longcycle-workstream-cursor/v2`. The copy read directly from the exact remote worker ref is execution authority. It repeats only identity/fencing fields needed to acknowledge the main reservation and does not shadow reservation-owned goal/scope fields.

```json
{
  "schema_version": "longcycle-workstream-cursor/v2",
  "workstream_id": "banking-domain-v1",
  "branch": "workstream/banking-domain-v1",
  "reservation_revision": 1,
  "assignment_epoch": 1,
  "cursor_sequence": 3,
  "checkpoint_based_on_head_sha": "89abcdef0123456789abcdef0123456789abcdef",
  "parent_refs": [
    "terminal_mission=STRATEGIC_COMPASS.md#terminal-mission",
    "long_term_direction=STRATEGIC_COMPASS.md#long-term-product-direction",
    "medium_term_goal=.longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
    "short_term_goal=.longcycle/handoff/current.json#strategic_horizon.short_term_goal",
    "workstream_goal=.longcycle/workstreams/banking-domain-v1/reservation.json#goal",
    "methodology=METHODOLOGY_CORE.md"
  ],
  "last_completed_action": "Added the bounded first banking source packet.",
  "current_task": "Verify point-in-time replay for the first banking packet.",
  "why_now": "The source packet must prove the reserved no-lookahead acceptance before the next metric is added.",
  "task_done_when": "Focused replay tests pass on the checkpoint and every value resolves to source provenance.",
  "next_atomic_action": "Run the focused banking replay tests and inspect provenance failures.",
  "required_capability": "high_capability_reasoning",
  "insufficient_capability_action": "stop_and_escalate",
  "progress_state": "verifying",
  "partial_summary": null,
  "unverified": false,
  "verification_head_sha": "89abcdef0123456789abcdef0123456789abcdef",
  "verification_refs": [
    ".longcycle/workstreams/banking-domain-v1/receipts/replay-verification.json"
  ],
  "artifact_refs": [],
  "integration_request_refs": [],
  "receipt_refs": []
}
```

`progress_state` is exactly one of:

```text
planned | in_progress | partial | verifying
| ready_for_integration | blocked | paused | superseded
```

It reports work progress only. It must never store `CLEAN`, `RECOVERY_REQUIRED` or `BLOCKED`; those are derived on startup from refreshed reservation, exact remote history and durable refs.

The verification triple is explicit:

- `unverified` says whether the current checkpoint lacks sufficient observed verification;
- `verification_head_sha` is the exact checked commit and, when present, equals the checkpoint; it is `null` when no check was observed;
- `verification_refs` contains only exact, resolvable verification artifacts.

Non-empty verification refs require the matching checkpoint SHA; empty refs require a null verification SHA. When `unverified` is false, the matching SHA and non-empty refs are both required. When it is true, incomplete checks may still be referenced only against that same checkpoint. Partial or unverified state carries a bounded truthful `partial_summary`; never infer a pass from an old or absent check.

## Remote startup and recovery gate

Before accepting any new work, including a new user request, every worker refreshes remote `main` and the exact remote worker ref, validates reservation revision/assignment epoch, checks checkpoint ancestry and bounded changed paths, resolves hot refs, and derives:

- `CLEAN`: the remote continuation story is complete; execute the cursor.
- `RECOVERY_REQUIRED`: attributable substantive/WIP commits exist after the acknowledged checkpoint; perform no new feature work, inspect and verify or mark them unverified, push a cursor-only acknowledgement, refresh and rerun the gate.
- `BLOCKED`: identity/fence/ancestry/writer or durable facts conflict; preserve exact evidence and route it to the coordinator.

The same Agent returning after interruption and a zero-context replacement use this identical gate. Work never pushed to the remote is unknowable and is repeated from the last remote `next_atomic_action`; no handoff may claim it was recovered.

The stable audit entrypoint is:

```bash
python scripts/audit_workstream_continuity.py <workstream-id> --remote origin --main-branch main
```

It exits `0` for `CLEAN`, `1` for `RECOVERY_REQUIRED` and `2` for `BLOCKED`. Its bounded remote delta is at most 64 ancestry edges, 256 touched paths per edge and 1,024 paths total; overflow fails closed as `BLOCKED`.

## Turn-boundary S+H loop

There is no mandatory duration, dialogue count or fixed micro-push cadence. An S commit/push contains coherent substantive/WIP work and any new request/receipt artifact. H is a small follow-up that changes only `cursor.json`, pins the accounted S commit with `checkpoint_based_on_head_sha`, records the verification triple and names the next atomic action. Every completed atomic task gets H, and each invocation attempts H when it reaches a safe closing boundary.

If interruption occurs between S and H, the next invocation's mandatory startup derives `RECOVERY_REQUIRED`; either the same Agent or a Fresh Agent supplies the missing H from the real remote delta, rereads the ref and reaches `CLEAN` before continuing or accepting a newly supplied task. This recovery-first rule, rather than a timer, is the required continuity behavior.

## Worker boundaries and typed communication

- `parallel` workstreams are L1/L2 plus `reuse/extend` only.
- The parallel branch is exactly `workstream/<workstream-id>` and has one assignment-fenced writer at a time; pushes are fast-forward only and never force-pushed.
- Changed files stay inside main-reserved write prefixes plus mutable records in that workstream's own control directory. `reservation.json`, `change-contract.json` and `capability-admission.json` remain main/integration-owned.
- Global Strategy/Method/Baseline/handoff/admission/Change Contract, Capability cards/index, canonical `migrations/`, shared CI, `pyproject.toml` and the active-workstream index remain serial-lane resources.
- Shared needs become typed files under `requests/` and exact `integration_request_refs` in the cursor, not chat messages or unauthorized shared-path edits.
- Active dependencies are registered and acyclic. `ready_for_integration` requires every dependency to be integrated/closed, `unverified: false`, exact-head verification and the workstream `done_when` to be met.
- Worker branches are producer branches; they never merge directly to `main`.

A typed request states stable id/requester, requested result and parent value, input/semantic constraints, checkable acceptance, dependency consequence and status. A producer result becomes consumable only through a completion receipt merged by the serial integration lane. That receipt pins request id, producer head, integrated main SHA, result refs, exact verification head/refs, limitations and the smallest supported consumer entrypoint. Consumers read the receipt, not another Agent's chat or branch claim.

The v1 machine gate bounds these records and proves that their pointers resolve to blobs on the exact remote head; semantic body validation remains an integration-lane review until the first real Banking/Shipping pilot supplies stable request/receipt shapes. A present blob is not, by itself, a satisfied dependency.

## Parallel database data plane

Drive-hosted database capsules are never shared writable workspaces. A worker pins an exact
main-promoted generation by Drive file/revision identity, digest, size and schema revision; restores
it into workstream-private storage; verifies it; and opens the base read-only. Any DuckDB/SQLite
transformation starts from a private copy, and PostgreSQL work uses an isolated database/schema
derived from workstream identity plus assignment epoch.

The worker may push a deterministic change bundle or new immutable candidate. Before upload it
pushes an intent receipt with a stable operation key and expected digest; after upload and byte
verification it pushes an outcome receipt with the new Drive identity. Intent without outcome is
recovered by inspecting Drive before retry. The worker never overwrites an existing object or edits
the global generation head.

Only the `global_serial` integration lane may compare a candidate base with refreshed main, replay
or reject stale candidates, order schema/semantic changes, upload the verified integrated
generation and advance `.longcycle/handoff/data-plane.json`. See
`docs/development/parallel-data-plane.md`.

## L3/L4 escalation handoff

Every worker inherits `docs/development/l3-l4-user-escalation.md`. A credible potential/confirmed L3 or L4 issue stops the Baseline-changing portion before implementation. Explain it to the user through that document's six-question plain-language protocol, then persist:

```text
.longcycle/workstreams/<workstream-id>/escalations/<short-id>.md
```

Push the escalation as S and add its exact path to `cursor.json.integration_request_refs` in H. The global handoff carries only a bounded project-level pointer when continuation changes. A worker may continue truly independent L1/L2 work, but may not create a local semantic fork.

## Integration and bounded lifetime

One `global_serial` lane imports ready producer heads, checks their diffs against main reservations, resolves typed shared requests, writes completion receipts, updates `reservation.lifecycle_state`, rebuilds the active index, and runs full CI plus Architecture Baseline gates on the exact integration head.

Machine entrypoints are:

```bash
python scripts/workstream_registry.py validate
python scripts/workstream_registry.py rebuild-index
python scripts/workstream_registry.py audit
python scripts/validate_workstream_boundaries.py --base-ref <integration-ref> --branch workstream/<workstream-id> --base-branch <integration-branch> --head-ref HEAD
```

The coordinator/integration lane owns `rebuild-index`. Workers run the boundary check against the refreshed reservation base; a producer branch must not use `main` as its direct merge target.

Hot state remains bounded regardless of project age: reservation and cursor are each at most 16 KiB; one reservation has at most 16 dependencies, 32 write prefixes and 16 capability owners; a cursor has at most eight parent refs and eight refs of each kind, with at most 24 durable refs total; the active router is at most 64 KiB, contains routing metadata only and admits at most 64 active workstreams. Current cursor fields overwrite prior values rather than appending Agent/session history. After downstream dependencies are discharged, integrated/closed work leaves the active router and keeps a compact completion/closure receipt; detailed chronology remains cold in Git and large research/export payloads remain outside Git behind identities/digests.

The operating rule is:

> Reserve authority on remote main, execute and acknowledge on the exact remote worker ref, communicate through typed requests/completion receipts, and keep Agents disposable without making future recovery read the project's entire history.
