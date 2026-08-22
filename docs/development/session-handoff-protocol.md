# Longcycle Session Handoff Protocol v5

> Normative operating protocol. Design rationale and failure history live in `docs/development/continuity-architecture.md`.

## 1. Goal

A zero-context Agent must recover without old chat history:

```text
terminal mission
+ cross-industry method
+ live medium/short goals
+ typed continuation cursor
+ minimum active context
+ live Git/CI state
+ exact binary assets required to continue
+ how to verify and open those assets
```

The handoff is deliberately split into a small Git control plane and a bounded external binary data plane.

## 2. Cold-start route

```text
main/FRESH_AGENT_BOOTSTRAP.md
→ issue #2 rendezvous
→ active PR / branch
→ active branch CONTINUE_HERE.md
→ Strategy + Method Core
→ first-pass mission reconstruction
→ mission-fidelity calibration
→ current.json
→ live HEAD / delta / CI refresh
→ bounded resume_read_set
→ data-plane.json only as required by the cursor
→ execute
```

The fixed transfer phrase remains task-free:

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

## 3. State ownership

| Layer | Canonical owner | Purpose |
| --- | --- | --- |
| terminal mission | `STRATEGIC_COMPASS.md` | why Longcycle exists / anti-drift |
| cross-industry method | `METHODOLOGY_CORE.md` | reusable research method |
| mission calibration | `.longcycle/continuity/mission-fidelity.json` | semantic challenge, not answers |
| dynamic control plane | `.longcycle/handoff/current.json` | goals, workstreams, cursor, live snapshot |
| binary data plane | `.longcycle/handoff/data-plane.json` | external asset IDs, hashes, restore contract |
| active context | handoff-referenced files | current benchmark/task details |
| history | Git + devlogs | rationale / old state |
| large bytes | verified external assets | portable DB/archive/runtime payloads |

One information class has one normal owner. Google Drive metadata is never a truth source for research state.

## 4. Mission assimilation

Read Strategy + Method Core first, then independently reconstruct the mission and method in the Agent's own words. Only then read the mission-fidelity contract and repair omissions. A high-capability transfer is not proven by repeating headings.

Do not persist private chain-of-thought. Persist only concise decisions, task hierarchy, reproducible constraints and verification results.

## 5. Authority planes

Strategic authority:

```text
new explicit user goal / constraint / decision
> Strategy Core
> Method Core
> dynamic strategic horizon
> deep historical narrative
```

Implementation/data freshness:

```text
live Git graph / HEAD / CI
+ canonical repository receipts
+ externally restored bytes that match repository SHA-256
> deterministic-derived state
> checkpoint snapshot
> narrative / Drive filename / Drive timestamp
```

A Drive file id is a locator. Its repository-pinned digest is the integrity authority.

## 6. Control plane contract

`current.json` uses `longcycle-session-handoff/v5` and contains:

- active repo/PR/branch;
- checkpoint base SHA;
- strategic horizon;
- continuation cursor;
- workstream graph;
- capability requirement;
- active context;
- bounded `resume_read_set` (8 files or fewer);
- `data_plane_manifest_path = .longcycle/handoff/data-plane.json`;
- live CI snapshot and explicit refresh instruction;
- ordered next actions and unresolved questions.

The cursor answers only what just finished, what resumes now, why, what ends it and what immediately follows. It is not a devlog.

## 7. Binary data plane contract

`data-plane.json` is the only normal owner of current external binary handoff assets. Each asset records:

- stable logical asset id and role;
- whether the current cursor requires it;
- transport (`google_drive` under the current environment constraint);
- Drive file id and filename;
- byte length and outer SHA-256;
- important inner components with byte length and SHA-256;
- concise content summary;
- deterministic restore instruction.

Current transport mode is `sandbox_google_drive_manual_relay`: large bytes move through the ChatGPT sandbox and Google Drive because Git text writes cannot carry them and GitHub Actions cannot consume Drive directly.

This is a transport limitation, not a reason to make Drive the database.

### Restore algorithm

```text
1. recover control plane first
2. decide which assets are required_for_current_task
3. fetch only those Drive file ids
4. verify outer size + SHA-256 before extraction
5. verify required inner component digests
6. restore compatible offline runtime only if needed
7. open research packs read-only by default
8. fail closed on missing asset, hash mismatch or ABI mismatch
```

If the Drive connector is unavailable, ask only for the exact repository-identified asset to be uploaded; never ask the user to reconstruct project background.

## 8. Database handoff boundary

Do not move a PostgreSQL cluster between sessions. PostgreSQL remains the transactional write/ops runtime for concurrent queues, leases, outbox and normal write semantics. Recreate it in GitHub Actions or another service-capable environment when those semantics are required.

Portable durable handoff uses:

```text
immutable content-addressed source/artifact bytes
+ repository machine receipts
+ reconciled DuckDB research/evidence packs
```

DuckDB is a read/replay materialization, not a replacement for raw evidence. The sandbox opens it read-only unless an explicitly designed pack-building task says otherwise.

Offline DuckDB runtime assets are ABI-specific. A wheel built for CPython 3.11 is not acceptable for a CPython 3.13 sandbox merely because both say DuckDB 1.5.5. Runtime assets therefore pin language ABI, architecture, version and SHA.

## 9. Capacity and pack policy

The current Drive capacity is limited, so handoff must be incremental and hot-pluggable rather than monolithic.

- Do not copy the whole multi-industry database at every session boundary.
- Keep only the active/recent immutable packset needed for continuation plus small runtime packs.
- Prefer bounded industry/time or task packs and content-addressed cold bundles.
- New immutable bytes get a new asset id/file id; never replace bytes behind an existing manifest entry.
- Old assets may be garbage-collected only after a verified successor exists and no current handoff references them.
- The Git manifest remains small even when total historical storage grows.

## 10. Workstreams and vertical alignment

Each active workstream declares `main_path`, `supporting_quality_gate` or `parallel_track` and its parent strategic goal. At least one main path exists.

Before a substantive subproblem and after each coherent subtask, verify:

```text
atomic task
↑ owning workstream / role
↑ short or medium goal
↑ terminal mission
```

Stop local optimization when `done_when` is met or marginal value collapses. Continuity infrastructure must return control to the research main path once transfer safety is demonstrated.

## 11. Capability-aware entry

The cursor declares `high_capability_reasoning` or `bounded_execution`. If a high-capability task cannot be reliably performed, obey `stop_and_escalate`; do not simulate confidence.

User goals and constraints are authoritative, but a user-proposed implementation method is still subject to independent technical judgment.

## 12. Micro-checkpoint lifecycle

After a coherent task boundary that changes what the next Agent should do:

```text
1. commit substantive work
2. run vertical alignment
3. if required binary state changed, create/verify/relay immutable assets
4. update data-plane.json
5. update current.json
6. set checkpoint_based_on_head_sha to the substantive-work commit
7. commit the handoff sync
8. refresh live CI when correctness is material
```

`.longcycle/handoff/current.json` and `.longcycle/handoff/data-plane.json` are handoff-mutable paths. Large binary bytes never enter Git.

If live HEAD differs from the checkpoint base, inspect intervening commits and fail closed into delta reconciliation rather than guessing.

## 13. Test pyramid

A handoff mechanism is not accepted from prose alone.

1. Static contracts: schema, bounded read set, path ownership, hashes, workstream/cursor validity.
2. Repository-only reconstruction: rebuild current state without chat history.
3. Binary roundtrip: Action/sandbox → Drive → fresh sandbox, outer + component SHA verification.
4. Offline runtime drill: install the pinned runtime in a clean venv with no network and open the required portable DB.
5. Artificial-ignorance drill: report current mission/state/task/data requirements using only the bounded bootstrap.
6. Genuine fresh-Agent transfer when useful.

A fresh Agent that recovers the task but cannot identify/open the required binary state has not fully passed v5 handoff.

## 14. Failure policy

Fail closed if any of these occur:

- checkpoint is stale relative to substantive commits;
- required resume/data path is missing;
- Drive asset missing or wrong size/hash;
- inner DB/receipt/runtime component hash mismatch;
- runtime ABI incompatible with sandbox;
- data package exists but cannot be opened read-only;
- reconstructed state contradicts canonical receipts/live Git;
- the Agent needs old chat text to know what to do next.

The user should never need to repeat already persisted background. A precise request for one missing binary asset is acceptable; a request to reconstruct project history is not.

## 15. Evolution rule

Material continuity changes require an observed failure or adversarial case, the smallest owning repair, typed schema update when semantics change, repository regression tests, an artificial-ignorance drill and a return to the product main path once safe.

The target remains minimum sufficient context: future Agents remember the right abstractions, recover the exact bytes they need, and continue without turning handoff engineering into the roadmap.
