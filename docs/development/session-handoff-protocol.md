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
+ exact binary/data capsules required to continue
+ how to verify and restore those assets
```

The handoff is deliberately split into a small Git control plane and a bounded external data plane.

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
| data plane manifest | `.longcycle/handoff/data-plane.json` | asset identity, transport, hashes, restore contract |
| active context | handoff-referenced files | current benchmark/task details |
| history | Git + devlogs | rationale / old state |
| readable webpage capture | bounded local DB -> Google Drive during development | efficient faithful visible-text/provenance handoff |
| raw PDF source bytes | GitHub Actions -> GitHub Release during development | immutable raw-byte source transport/cache |
| Longcycle-generated binary state | Google Drive during development | replay/execution/runtime transport/cache |

One information class has one normal owner. Release/Drive metadata is never research truth by itself. A webpage capture capsule may contain source-derived text even though its transport is Drive; transport does not reclassify epistemic authority.

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
+ restored webpage capture DB matching repository SHA-256
+ restored raw PDF/source pack matching repository SHA-256
> deterministic-derived state
> checkpoint snapshot
> narrative / transport metadata
```

A Release filename/tag or Drive file id is a locator. Repository-pinned identity and digest control integrity. Neither locator nor transport changes claim-scoped source authority.

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

## 7. Data plane contract

`data-plane.json` uses `longcycle-handoff-data-plane/v3` and transport mode `github_release_pdf_sources_google_drive_webcapsules_generated`.

Each resume-relevant asset records:

- stable logical asset id and role;
- whether the current cursor requires it;
- transport;
- Release tag or Drive file id as appropriate;
- filename, byte length and outer SHA-256;
- important inner components when needed;
- concise content summary;
- deterministic restore instruction.

### 7.1 Webpage lane: interactive read -> local database -> Google Drive

For a readable webpage, default to the interactive research surface rather than starting an Action merely to archive HTML.

```text
read visible webpage content
→ preserve faithful visible text + source/provenance metadata
→ batch into bounded local DuckDB capture capsule
→ checkpoint/close and hash
→ upload immutable capsule to Google Drive
→ pin Drive id + SHA/schema/source count in Git control plane
```

Required capture metadata should include, where source-supported:

- original URL;
- upstream publisher/source identity;
- title and source-displayed date;
- capture/retrieval time;
- truthful `capture_mode`;
- faithful visible text;
- deterministic text/record digest;
- material limitations such as unreadable images or omitted non-visible structure.

Rules:

- do not create per-page Git commits when a bounded local DB + one Drive transfer is faster;
- do not invoke GitHub Actions merely to fetch HTML for a readable page;
- the capture DB is a source-capture/handoff envelope, not live PostgreSQL and not automatic Fact/Judgment publication;
- after restore, normal archive/Evidence/Assertion/Reconciliation semantics still apply;
- Drive transport neither upgrades nor downgrades source authority;
- a complete truthful visible-text capture must not be described as byte-identical original HTML;
- existing historical Release packs that contain HTML/web bytes are grandfathered immutable assets. Restore them when an existing receipt requires them, but do not copy that legacy route for new readable webpages.

### 7.2 PDF lane: GitHub Actions -> GitHub Release

Use the existing GitHub Actions acquisition lane for PDFs when raw source bytes are required.

Rules:

- fetch the public PDF in Actions;
- validate response/type and required source identity/semantic checks;
- compute raw SHA-256;
- package under a unique immutable filename;
- upload to GitHub Release;
- download the Release asset back and verify SHA-256;
- preserve retrieval host and upstream source identity separately from transport;
- Release transport never upgrades or downgrades source authority;
- re-grounding restores only the required PDF/source pack and then uses normal archive/parser/Evidence paths.

The interactive Agent's difficulty uploading Release assets is not a source-acquisition blocker; Actions owns this lane.

### 7.3 Google Drive lane: webpage capture DBs and Longcycle-generated binary state

Use Google Drive for:

- bounded webpage capture DuckDBs;
- DuckDB replay materializations;
- execution/reconciliation output packs;
- generated DB snapshots when explicitly needed;
- offline runtime packs.

Rules:

- Drive file id + repository-pinned digest define the object;
- successor state/capsule gets a new Drive file/id and manifest entry;
- webpage visible text inside a capture capsule remains source-derived material with its original provenance and authority;
- generated replay/execution packs are not source archives and must not inherit source authority;
- DuckDB/replay materializations open read-only by default after handoff/restore;
- raw PDF bytes needed for re-grounding are restored separately from Release.

### 7.4 Restore algorithm

```text
1. recover control plane first
2. inspect data-plane manifest
3. decide which assets are required_for_current_task
4. if none are required, do not restore old data-plane state
5. for required webpage capture capsules: fetch exact Drive file id, verify outer/component hashes, open read-only unless actively extending a new local generation
6. for required Release PDF/source packs: fetch exact tag/name, verify outer + raw hashes
7. for required generated Drive packs: fetch exact file id, verify outer + component hashes
8. restore compatible runtime only if actually needed
9. fail closed on missing asset, hash mismatch or ABI mismatch
```

If a required transport is unavailable, ask only for the exact repository-identified asset to be relayed/uploaded. Never ask the user to reconstruct project background.

## 8. Database handoff boundary

Do not move a live PostgreSQL cluster between sessions or place it in Release. PostgreSQL remains the transactional write/ops runtime for queues, leases, outbox and normal writes. Recreate it in GitHub Actions or another service-capable environment when those semantics are required.

For readable webpage acquisition, a bounded local DuckDB is intentionally different: it is a lightweight capture capsule written locally for batching and handoff efficiency. Before handoff, checkpoint/close it, record its schema/version/source count/size/SHA, upload it to Drive and treat the handed-off generation as immutable/read-only unless a new successor generation is created.

If a generated database snapshot is explicitly useful for handoff, it belongs in Google Drive and remains a snapshot, not live authority.

Portable durable handoff uses:

```text
Git control-plane receipts and identities
+ webpage capture DB from Drive when needed
+ immutable PDF bytes from Release when needed
+ generated DuckDB/execution/runtime state from Drive when needed
```

DuckDB capture/replay files are portable envelopes/materializations, not substitutes for Evidence semantics or live PostgreSQL.

Offline runtime assets are ABI-specific. Runtime mismatch fails closed and produces a new immutable generated runtime pack rather than forcing an incompatible binary.

## 9. Capacity and pack policy

Handoff must be incremental, batched and hot-pluggable rather than monolithic.

- Do not copy the whole multi-industry database at every session boundary.
- Do not restore old-industry binaries when the current cursor does not require them.
- Prefer bounded task/industry/time webpage-capture DBs and research packs.
- Prefer one local DB batch + one Drive handoff over hundreds of tiny webpage Git writes.
- New PDF source bytes get a new Release filename.
- New webpage capture DBs and generated bytes get new Drive files/ids.
- Existing HTML-containing Release assets remain immutable legacy assets; no migration churn is required.
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
3. if resume-relevant data state changed, materialize/upload/verify it on the correct transport
   - webpage capture DB -> Drive
   - PDF raw bytes/source pack -> Actions/Release
   - generated binary state -> Drive
4. update data-plane.json
5. update any durable completion/exit/rehearsal receipt
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
3. Data transport check when the current cursor requires bytes.
4. Offline runtime drill when a runtime pack is actually required.
5. Artificial-ignorance drill: report current mission/state/task/data requirements using only the bounded bootstrap.
6. Genuine fresh-Agent transfer when useful.

For the webpage/PDF routing rule, the artificial-ignorance drill must be able to answer from repository state alone:

```text
readable webpage -> local capture DB -> Drive
PDF raw bytes -> Action -> Release
no Action merely to archive readable webpage HTML
legacy HTML-containing Release packs remain valid but are not the new default
```

A transfer can pass without restoring any data pack when `required_for_current_task=false` for all assets and the cursor genuinely does not need old bytes.

## 14. Failure policy

Fail closed if any of these occur:

- checkpoint is stale relative to unclassified substantive commits;
- required resume/data path is missing;
- a new readable webpage is unnecessarily routed through Actions/Release by default;
- a required webpage capture DB is missing or has wrong hash;
- a required PDF source pack is on the wrong transport or has wrong hash;
- generated replay/runtime pack is on the wrong transport;
- required asset missing or wrong size/hash;
- inner component digest mismatch;
- runtime ABI incompatible;
- reconstructed state contradicts canonical receipts/live Git;
- the Agent needs old chat text to know what to do next.

The user should never need to repeat persisted background. A precise request for one missing data-plane asset is acceptable; asking the user to reconstruct project history is not.

## 15. Evolution rule

Material continuity changes require an observed failure or adversarial case, the smallest owning repair, typed schema update when semantics change, repository regression tests, an artificial-ignorance drill and a return to the product main path once safe.

The target remains minimum sufficient context: future Agents remember the right abstractions, capture readable webpages locally and hand them off efficiently through Drive, use Actions/Release for PDF raw-byte acquisition, restore only the exact bytes they need, and continue without turning handoff engineering into the roadmap.
