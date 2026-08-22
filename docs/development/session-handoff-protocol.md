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
+ how to verify and restore those assets
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
→ data-plane.json only as required by cursor
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
| binary data plane manifest | `.longcycle/handoff/data-plane.json` | asset identity, transport, hashes, restore contract |
| active context | handoff-referenced files | current benchmark/task details |
| history | Git + devlogs | rationale / old state |
| externally acquired source bytes | GitHub Release during development | immutable source transport/cache |
| Longcycle-generated binary state | Google Drive during development | replay/execution/runtime transport/cache |

One information class has one normal owner. Release/Drive metadata is never research truth by itself.

## 4. Mission assimilation

Read Strategy + Method Core first, then independently reconstruct the mission and method in the Agent's own words. Only then read the mission-fidelity contract and repair omissions. A high-capability transfer is not proven by repeating headings.

Product success is not Agent benchmark score. The Agent must understand that Longcycle should let an industry researcher quickly build a defensible mental model of an industry, with Reality, contemporaneous Judgment, later Outcome, source grounding, disagreement and unknowns. A machine-clean benchmark that leaves the researcher to reconstruct the field manually is a product failure.

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
+ externally restored bytes matching repository SHA-256
> deterministic-derived state
> checkpoint snapshot
> narrative / transport metadata
```

A Release filename/tag or Drive file id is a locator. Repository-pinned identity and digest control integrity.

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
- live CI snapshot plus refresh instruction;
- ordered next actions and unresolved questions.

The cursor answers only what just finished, what resumes now, why, what ends it and what immediately follows. It is not a devlog.

## 7. Binary data plane contract

`data-plane.json` uses `longcycle-handoff-data-plane/v2` and transport mode `github_release_sources_google_drive_generated`.

Each asset records:

- stable logical asset id and role;
- whether the current cursor requires it;
- transport;
- Release tag or Drive file id as appropriate;
- filename, byte length and outer SHA-256;
- important inner components when needed;
- concise content summary;
- deterministic restore instruction.

### 7.1 GitHub Release lane: externally acquired raw source

Use GitHub Release only for externally acquired immutable source payloads/source packs: PDF, HTML, filings, formal announcement bytes and bundles that contain them.

Rules:

- unique immutable filename; never overwrite a recorded asset;
- preserve retrieval host and upstream source identity separately from transport;
- Release transport never upgrades or downgrades source authority;
- re-grounding restores only the required source pack, verifies outer/raw hashes, then uses normal archive/parser/Evidence paths;
- raw source packs must never be classified as Longcycle-generated state merely because an Action packaged them.

### 7.2 Google Drive lane: Longcycle-generated binary state

Use Google Drive for Longcycle-generated binary state: DuckDB replay materializations, execution/reconciliation output packs, generated DB snapshots when explicitly needed, and offline runtime packs.

Rules:

- Drive file id + repository-pinned digest define the object;
- generated replay/execution packs are not source archives and must not inherit source authority;
- DuckDB/replay materializations open read-only by default;
- if raw source is needed, restore it separately from Release;
- successor generated state gets a new Drive file/id and repository manifest entry.

### 7.3 Restore algorithm

```text
1. recover control plane first
2. inspect data-plane manifest
3. decide which assets are required_for_current_task
4. if none are required, do not restore old binary state
5. for required Release source packs: fetch exact tag/name, verify outer + raw hashes
6. for required Drive generated packs: fetch exact file id, verify outer + component hashes
7. restore compatible runtime only if actually needed
8. open generated research packs read-only by default
9. fail closed on missing asset, hash mismatch or ABI mismatch
```

If a required transport is unavailable, ask only for the exact repository-identified asset to be relayed/uploaded. Never ask the user to reconstruct project background.

## 8. Database handoff boundary

Do not move a live PostgreSQL cluster between sessions or place it in Release. PostgreSQL remains the transactional write/ops runtime for queues, leases, outbox and normal writes. Recreate it in GitHub Actions or another service-capable environment when those semantics are required.

If a generated database snapshot is explicitly useful for handoff, it belongs in Google Drive and remains a snapshot, not live authority.

Portable durable handoff uses:

```text
Git control-plane receipts and identities
+ immutable source bytes from Release when needed
+ generated DuckDB/execution/runtime state from Drive when needed
```

DuckDB is a read/replay materialization, not a replacement for raw Evidence.

Offline runtime assets are ABI-specific. Runtime mismatch fails closed and produces a new immutable generated runtime pack rather than forcing an incompatible binary.

## 9. Capacity and pack policy

Handoff must be incremental and hot-pluggable rather than monolithic.

- Do not copy the whole multi-industry database at every session boundary.
- Do not restore old-industry binaries when the current cursor does not require them.
- Prefer bounded task/industry/time packs.
- New immutable source bytes get a new Release filename.
- New generated bytes get a new Drive file/id.
- The Git manifest remains small and resume-relevant; it is not required to enumerate every cold historical asset forever.

## 10. Workstreams and vertical alignment

Each active workstream declares `main_path`, `supporting_quality_gate` or `parallel_track` and its parent strategic goal. At least one main path exists.

Before a substantive subproblem and after each coherent subtask, verify:

```text
atomic task
↑ owning workstream / role
↑ short or medium goal
↑ terminal mission
```

Stop local optimization when `done_when` is met or marginal product value collapses. Continuity infrastructure must return control to the research main path once transfer safety is demonstrated.

## 11. Capability-aware entry

The cursor declares `high_capability_reasoning` or `bounded_execution`. If a high-capability task cannot be reliably performed, obey `stop_and_escalate`; do not simulate confidence.

User goals and constraints are authoritative, but a proposed implementation method is still subject to independent technical judgment.

## 12. Micro-checkpoint lifecycle

After a coherent task boundary that changes what the next Agent should do:

```text
1. commit substantive work
2. run vertical alignment
3. if resume-relevant binary state changed, create/upload/verify immutable assets on the correct transport
4. update data-plane.json
5. update any durable completion/exit receipt
6. update current.json
7. set checkpoint_based_on_head_sha to the last substantive/control-plane commit before current.json sync
8. commit the handoff sync
9. refresh live CI when correctness is material
10. run bounded artificial-ignorance rehearsal
```

Because `current.json` itself is committed after its checkpoint base, live HEAD may normally be one handoff-only commit ahead. Fresh Agents must inspect the delta and classify it; this is not automatically stale state.

## 13. Test pyramid

A handoff mechanism is not accepted from prose alone.

1. Static contracts: schema, bounded read set, asset-role/transport validity, hashes, workstream/cursor validity.
2. Repository-only reconstruction: rebuild current state without chat history.
3. Binary transport check when the current cursor requires bytes.
4. Offline runtime drill when a runtime pack is actually required.
5. Artificial-ignorance drill: report current mission/state/task/data requirements using only the bounded bootstrap.
6. Genuine fresh-Agent transfer when useful.

A transfer can pass without restoring any binary pack when `required_for_current_task=false` for all assets and the cursor genuinely does not need old bytes.

## 14. Failure policy

Fail closed if any of these occur:

- checkpoint is stale relative to unclassified substantive commits;
- required resume/data path is missing;
- source pack is on the wrong transport;
- generated replay/runtime pack is on the wrong transport;
- required asset missing or wrong size/hash;
- inner component digest mismatch;
- runtime ABI incompatible;
- reconstructed state contradicts canonical receipts/live Git;
- the Agent needs old chat text to know what to do next.

The user should never need to repeat persisted background. A precise request for one missing binary asset is acceptable; asking the user to reconstruct project history is not.

## 15. Evolution rule

Material continuity changes require an observed failure or adversarial case, the smallest owning repair, typed schema update when semantics change, repository regression tests, an artificial-ignorance drill and a return to the product main path once safe.

The target remains minimum sufficient context: future Agents remember the right abstractions, restore only the exact bytes they need, and continue without turning handoff engineering into the roadmap.
