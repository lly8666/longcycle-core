# Longcycle storage runtime boundary

Status: adopted after the first real Kwinana grounded-evidence benchmark.

This decision records what the benchmark proved. It is intentionally narrower than a full repository rewrite.

## Decision

Longcycle separates three storage responsibilities instead of forcing one database to own all of them:

1. **Immutable source archive** — original HTML/PDF/attachments and deterministic parser artifacts remain in the content-addressed `ArchiveStore` (filesystem or object storage). Raw source bytes are not copied into analytical database files merely for convenience.
2. **Transactional collection / operational state** — the current normal write path may continue to use PostgreSQL for migrations, source registration, document versioning, evidence writes, queues, leases and other concurrent operational semantics. PostgreSQL remains an adapter-backed runtime choice rather than the terminal product.
3. **Portable research / evidence replay package** — DuckDB is the adopted portable durable bundle format for bounded research/evidence handoff, point-in-time replay and local analytical reads. A bundle contains canonical row mirrors, evidence/document indexes and derived hot parser text, while raw source bytes stay in the immutable archive.

This is a **hybrid boundary**, not a declaration that every existing PostgreSQL repository must immediately be rewritten as DuckDB-native.

## Why this boundary exists

The terminal Longcycle mission is temporally truthful industrial memory, not database standardization. Storage is correct when it preserves evidence identity, known-time / valid-time semantics and portable replay with low operational burden.

The EVT-001 Kwinana benchmark executed four real historical source vintages through the normal PostgreSQL archive/evidence path, persisted two versioned PDF parser artifacts and nine grounded EvidenceFragments, created zero FactAssertions and zero Judgments, then exported the exact bounded evidence state into DuckDB 1.5.5.

The resulting DuckDB bundle:

- re-opened successfully in read-only mode after the writer closed;
- contained canonical mirrors for every selected PostgreSQL evidence row;
- verified per-table row counts and canonical SHA-256 digests;
- had zero broken document references and zero broken artifact references;
- preserved queryable `claim_role`, known-time upper bound/precision, valid/effective time and expectation horizon;
- embedded deterministic page text for hot PDF review while keeping original PDFs outside the database;
- supported a point-in-time cutoff query directly from the portable file.

The authoritative machine receipt is:

`research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/self_verification/UP-CHEMICALS/run-001/tasks/EVT-001-kwinana-execution-receipt-v1.json`

## Canonical row reconciliation rule

A portable DuckDB bundle is not authoritative merely because rows were copied into it. Export is accepted only when the selected PostgreSQL rows are canonicalized deterministically and the DuckDB mirror reproduces the same row digests and table digests.

The current bundle schema uses:

- `canonical_rows` — canonical JSON row mirror plus row SHA-256;
- `document_index` — portable source-version identity, archive locator and source/retrieval provenance;
- `evidence_index` — fragment identity, locator and first-class temporal/claim context;
- `page_text` — deterministic parser output for bounded hot review;
- `evidence_timeline` — point-in-time-oriented analytical view.

A bundle must fail closed on digest mismatch or broken document/artifact references.

## Publisher authority is not retrieval transport

Historical recovery may retrieve a publisher's original bytes through a third-party archival transport. The publisher/source authority and the retrieval route must remain distinguishable.

For example, the Kwinana 2018/2019 Tianqi pages were unavailable from the GitHub runner's direct route but their exact original Tianqi pages were recoverable from verified Internet Archive captures. Tianqi remains the publisher whose wording carries the claim; Internet Archive is retrieval/capture provenance. The archive capture timestamp must not be substituted for historical `known_time`.

## Time semantics remain above storage

Neither PostgreSQL nor DuckDB determines historical truth. Evidence must preserve separately when information was knowable, when a milestone applied or became effective, and what future horizon an expectation targeted.

Storage must not collapse:

- source/body dateline into exact first-publication time;
- archival capture time into historical known-time;
- milestone effective date into disclosure time;
- month-level forward expectation into a day-level outcome declaration;
- commissioning, continuous operation, commercial-production capability, customer qualification and nameplate capacity into one status.

## Operational boundary

Do not now add a generic DuckDB write repository, distributed orchestration layer or cross-database synchronization service merely because the portable bundle worked.

The next benchmark work should reuse the proven path:

`primary source -> immutable archive -> grounded EvidenceFragment -> portable reconciled DuckDB bundle/replay`

Add further storage abstraction only when a real industry trajectory exposes a concrete repeated need. The next mainline task is EVT-002 Kemerton, followed by the first small no-lookahead replay fixture.
