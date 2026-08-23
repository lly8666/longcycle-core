# Longcycle storage runtime boundary

Status: adopted after real grounded-evidence/replay benchmarks and refined by the PDF transport/materialization correction.

This decision separates **what Longcycle knows/preserves** from **where bytes happen to travel**.

## Decision

Longcycle has four distinct storage responsibilities:

1. **Logical source identity + completeness state** — PostgreSQL `evidence.documents` tracks the upstream document and its `locator_verified → content_verified → materialized` lifecycle.
2. **Immutable preserved material** — `ArchiveStore` stores the exact bytes Longcycle actually used/preserved. Those bytes may be upstream raw source or a truthful source-derived readable representation; representation provenance must say which.
3. **Transactional collection / operational state** — PostgreSQL owns migrations, source registration, document/evidence writes, queues, leases, outbox and concurrent write semantics.
4. **Portable research / replay state** — DuckDB is the durable bounded replay/handoff format for typed industrial memory and may also be used for webpage capture capsules. It is not live transactional authority.

## Raw source bytes are not synonymous with Evidence material

Old shorthand used:

```text
raw source -> parser artifact -> Evidence
```

That remains a strong path when raw bytes are available, but it is **not the only truthful path**. The current architecture is:

```text
upstream source identity
→ locator/content verification
→ exact preserved source-derived material
→ Grounded Evidence
→ optional later raw-source materialization
```

For a PDF whose claim-relevant content was actually read but whose bytes cannot currently be downloaded:

```text
source_media_type = application/pdf
source_capture_state = content_verified
representation_content_type = text/plain (or another truthful representation)
raw_source_materialized = false
```

The representation bytes go through the normal immutable archive/document-version path. Their presence proves exactly those preserved bytes existed in Longcycle; it does **not** prove byte-identical PDF materialization.

Migration 0028 removes the old generic “document version means raw materialized” trigger. Migration 0029 preserves explicit content-verified representation state from trusted adapter provenance. A later raw PDF is marked `materialized` only through an explicit verified transition tied to the raw document version.

## PostgreSQL

PostgreSQL remains the normal live write engine because Longcycle needs:

- transactional Evidence/Fact/Judgment writes;
- source/document identity constraints;
- migration discipline;
- leases/retries/outbox;
- reconciliation and audit semantics.

A live PostgreSQL cluster is never session-handoff authority. Recreate it in a service-capable runtime when needed. A generated snapshot may be transported through Drive, but remains a snapshot.

## ArchiveStore

ArchiveStore is content-addressed preservation, not an authority classifier.

It may contain:

- upstream raw HTML/PDF/JSON/attachments;
- parser artifacts;
- faithful webpage visible-text captures;
- content-verified PDF readable representations;
- generated execution artifacts when a caller explicitly stores them there.

Every stored object must retain enough lineage to distinguish source bytes, source-derived representation and generated output.

## DuckDB / SQLite capture capsules

### Typed replay

Portable DuckDB replay packages contain typed Reality/Judgment/Outcome/evidence indexes needed for point-in-time reads. They open read-only by default after handoff.

### Web capture

Readable webpages can be batched into a bounded DuckDB/SQLite capsule containing faithful claim-scoped visible text and provenance, then handed off through Google Drive. This is source capture, not Fact/Judgment publication.

Raw webpage HTML is not required merely because a tool could fetch it; the capture mode must state what was actually preserved.

## PDF handoff/materialization

Default new-PDF path:

```text
verify document identity + locator
→ if content unread: locator_verified only
→ if claim content read/preserved: content_verified + Grounded Evidence allowed
→ later normal-network Agent optionally downloads raw PDF
→ verify identity/content
→ record raw size/SHA/storage locator
→ explicit materialized transition
```

Do not create GitHub Actions just to download new PDFs. Existing GitHub Release source packs remain immutable historical materializations and may be reused.

## Research orchestration boundary

`research-orchestration/v2` consumes an already prepared local material root and verifies the per-document SHA declared by the Grounded Evidence spec. It does not care whether those bytes arrived from Drive, a legacy Release, local capture, or later raw materialization.

`research-orchestration/v1` remains supported only for replay of old source-pack-based executions.

Transport restore therefore remains outside epistemic execution:

```text
transport / restore / representation preparation
             ↓
verified local material root
             ↓
Grounded Evidence / Reality / replay
```

## Fail-closed boundaries

Fail closed when:

- a claim relies on PDF content that was never actually read/preserved;
- representation bytes do not match their declared digest;
- representation provenance pretends text is raw PDF;
- later raw materialization contradicts earlier source identity/content;
- PostgreSQL / replay integrity gates fail.

Do **not** fail merely because raw PDF bytes are pending after `content_verified`.

## Canonical row reconciliation

Portable DuckDB data is not authoritative because it was copied. Export/replay must remain deterministic and typed, preserve source/evidence identities, and reproduce required canonical row semantics/digests. Storage convenience never bypasses Evidence/Reconciliation.
