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
+ exact source/data identities required to continue
+ how to restore or defer materialization safely
```

The handoff is deliberately split into a small Git control plane and a bounded external data plane.

## 2. Cold-start route

```text
main/FRESH_AGENT_BOOTSTRAP.md
→ issue #2 rendezvous
→ active PR / branch
→ active branch CONTINUE_HERE.md
→ Strategy + Method Core
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
| mission calibration | `.longcycle/continuity/mission-fidelity.json` | semantic challenge |
| dynamic control plane | `.longcycle/handoff/current.json` | goals, workstreams, cursor, live snapshot |
| data plane manifest | `.longcycle/handoff/data-plane.json` | source/data identity, transport, materialization status, hashes where available |
| readable webpage capture | bounded local DB -> Google Drive | faithful visible-text/provenance handoff |
| PDF source locator/content | Git control plane + claim-scoped readable representation | Evidence can proceed before raw bytes |
| deferred PDF raw bytes | later normal-network Agent / owning receipt | optional completeness/integrity enrichment |
| Longcycle-generated binary state | Google Drive | replay/execution/runtime transport |
| history | Git + devlogs | rationale / old state |

One information class has one normal owner. Transport metadata is never research truth by itself.

## 4. Authority planes

Strategic authority:

```text
new explicit user goal / constraint / decision
> Strategy Core
> Method Core
> dynamic strategic horizon
> deep historical narrative
```

Evidence/content integrity:

```text
claim-relevant content actually read + preserved provenance
+ canonical repository receipts
+ source/document identity + locator
+ restored capture/materialized object matching recorded digest when one exists
> deterministic-derived state
> checkpoint snapshot
> narrative / transport metadata
```

A locator can establish source identity but **not an unread claim**. A raw-file hash can establish byte integrity but **not source authority**. Claim authority remains scoped to publisher/document role.

## 5. Control plane contract

`current.json` uses `longcycle-session-handoff/v5` and contains active repo/PR/branch, checkpoint base SHA, strategic horizon, continuation cursor, workstreams, capability requirement, active context, bounded resume set, data-plane path and CI snapshot.

The cursor answers what just finished, what resumes now, why, what ends it and what immediately follows. It is not a devlog.

## 6. Data plane contract

`data-plane.json` uses `longcycle-handoff-data-plane/v4` and transport mode `google_drive_webcapsules_generated_pdf_locator_deferred_materialization`.

### 6.1 Readable webpage lane

```text
interactive read
→ faithful claim-scoped visible text + provenance
→ bounded local DuckDB/SQLite capture capsule
→ checkpoint/close/hash
→ Google Drive
→ pin Drive id + digest/schema/source count in Git
```

Do not use Actions merely to fetch HTML. Capture DB is not live PostgreSQL and not automatic Fact/Judgment publication.

### 6.2 PDF lane: locator/content first

Do **not** create or run GitHub Actions merely to download new PDF source bytes.

PDF state machine:

```text
locator_verified
→ content_verified
→ materialized
```

`locator_verified` records publisher/upstream identity, document title/date/id when supported, original PDF URL, filename when known, verification time/mode and pending materialization status.

For PDFs on mainstream official/regulatory/issuer/institutional publishers, verified document identity + locator is sufficient to accept the PDF as a legitimate source document. Do not test downloadability as a research gate.

`content_verified` means an Agent actually read the claim-relevant PDF content in a trustworthy surface and preserved a page/section/excerpt or equivalent faithful readable representation. **This state is sufficient for normal Evidence semantics without raw PDF bytes.**

A Grounded Evidence spec may materialize that readable PDF representation as source-derived `text/plain` (or another truthful representation) while keeping the upstream/original media type and PDF locator in retrieval provenance. The SHA then pins the captured readable representation, not the unseen raw PDF. Do not label such a representation byte-identical PDF.

`materialized` is later enrichment. A normal-network Agent downloads the recorded locator, verifies identity/content against earlier records, then appends raw byte size, SHA and storage identity. Contradiction creates an integrity repair.

Only `locator_verified` with unread claim content is insufficient for claim Evidence.

### 6.3 Existing GitHub Release assets

Existing immutable Release PDF/source packs remain valid historical materializations and may be reused. They are not the template for new PDF acquisition. Existing HTML/mixed Release packs are likewise grandfathered.

Actions may still execute PostgreSQL, replay, runtime or other service-capable jobs. The prohibition is **source-download Actions used merely to obtain new PDF bytes**.

### 6.4 Google Drive lane

Use Drive for bounded webpage capture DBs and Longcycle-generated replay/execution/runtime/database-snapshot packs. Drive identity + recorded digest controls the object. Drive transport never changes source authority.

Deferred PDF raw materialization has no mandatory transport in this protocol; its owning receipt records whatever durable storage identity is chosen later.

### 6.5 Restore algorithm

```text
1. recover Git control plane first
2. inspect required source/data state
3. restore required webpage/generated Drive capsules and verify recorded hashes
4. for PDF claims:
   a. if content_verified representation already exists, use it; raw bytes are optional
   b. if only locator_verified exists, do not claim-ground unread content
   c. if a legacy/materialized raw PDF already exists and is useful, restore and verify it
5. recreate PostgreSQL only when execution semantics need it
6. fail closed on actual content/identity contradiction, corrupted required capsule or runtime incompatibility
```

Missing raw PDF bytes alone are **not** a blocker when claim-relevant content is already `content_verified`.

## 7. Database handoff boundary

Do not transport live PostgreSQL between sessions. PostgreSQL remains the transactional write/ops runtime and is recreated in service-capable execution when needed.

Webpage/PDF-readable captures may use bounded local DuckDB/SQLite envelopes for efficient handoff. A handed-off generation is immutable/read-only by default; successor capture gets a new generation.

A source-derived readable PDF capture is not the same thing as raw PDF bytes, but it can be Evidence if its representation/provenance are truthful and the claim-relevant content was actually read.

## 8. Capacity policy

- Do not copy the whole multi-industry database at every handoff.
- Do not restore old binaries when the current cursor does not require them.
- Prefer bounded task/industry/time capture DBs and research packs.
- Do not create per-page Git commits for capture payloads.
- Do not create downloader workflows merely because one Agent/network cannot fetch a PDF file.
- Preserve verified PDF locators so a later normal-network Agent can materialize them in batch.
- The Git manifest remains resume-relevant, not a permanent inventory of every cold historical asset.

## 9. Capability and vertical alignment

Before substantive work, recover the existing capability owner. Default to reuse/extend rather than creating a second semantic owner.

After coherent subtasks, check:

```text
atomic task
↑ owning workstream
↑ short/medium goal
↑ terminal mission
```

Stop local optimization when marginal product value collapses. Transport engineering must not become the roadmap.

## 10. Micro-checkpoint lifecycle

After a coherent task boundary:

```text
1. commit substantive work
2. preserve new source state
   - webpage readable content -> local DB -> Drive
   - PDF -> locator/content verification now; raw materialization later if useful
   - generated binary state -> Drive
3. update data-plane/owning receipts
4. update current.json
5. commit handoff sync
6. refresh CI when correctness is material
7. run bounded artificial-ignorance rehearsal for material continuity changes
```

## 11. Artificial-ignorance test

A fresh Agent must be able to reconstruct this rule without chat history:

```text
readable webpage -> local capture DB -> Drive
PDF -> verify source locator/document identity
if claim-relevant PDF content is readable -> Evidence may proceed from truthful readable representation
raw PDF bytes -> deferred materialization by a later normal-network Agent
no GitHub Actions merely to download new PDF bytes
existing Release packs remain valid legacy materializations
```

The Agent must also state the safety boundary:

```text
locator exists but claim content unread
!=
claim is evidenced
```

## 12. Failure policy

Fail closed if:

- checkpoint is stale relative to unclassified substantive commits;
- required webpage/generated capsule is missing or digest-mismatched;
- a claim is promoted from a PDF locator whose relevant content was never read;
- later PDF materialization contradicts earlier verified document identity/content;
- a source-derived text capture is falsely described as raw PDF bytes;
- generated/runtime state is corrupted or ABI-incompatible;
- reconstructed state contradicts canonical receipts/live Git;
- a fresh Agent needs old chat to know what to do.

Do **not** fail merely because raw PDF bytes are pending after content verification, a host rejects one downloader, or the current Agent cannot upload Release assets.

## 13. Evolution rule

Material continuity changes require an observed failure or adversarial case, the smallest owning repair, repository-backed contract updates, an artificial-ignorance drill and a return to the research main path.

The target is minimum sufficient context: preserve what was actually readable and verifiable, distinguish evidence truth from byte-archive completeness, defer low-value transport work, and continue the industrial-memory research without sacrificing claim-scoped provenance or no-lookahead semantics.
