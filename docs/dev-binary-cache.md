# Development source and binary storage

Longcycle uses a split development-stage data plane so readable source content, deferred raw-file materialization and Longcycle-generated state do not block one another unnecessarily.

## Readable webpages: local database -> Google Drive

For a readable webpage, the default path is:

```text
interactive read
→ faithful claim-scoped visible-text capture + provenance metadata
→ bounded local DuckDB/SQLite capture capsule
→ checkpoint / SHA-256
→ Google Drive handoff
→ Git stores only the compact asset locator/digest/restore contract
```

Do **not** start GitHub Actions merely to fetch or archive HTML for a webpage whose visible content can already be read faithfully in the interactive research surface.

A webpage capture row/capsule should preserve, as applicable:

- original URL and upstream publisher/source identity;
- title and source-displayed date when supported;
- `captured_at` / retrieval context;
- truthful `capture_mode`;
- faithful visible text needed for the bounded claim;
- SHA-256 of the captured text/record or other deterministic integrity fields;
- material capture limitations.

The local database is a **capture/handoff envelope**, not live PostgreSQL authority and not automatic Fact/Judgment publication. Drive transport does not upgrade source authority. After restore, normal archive/Evidence semantics still apply.

## PDFs: locator/content verification first, raw bytes later

Raw PDF download is **not a prerequisite for research progress**.

Use three explicit states:

```text
locator_verified
→ content_verified
→ materialized
```

### `locator_verified`

The Agent has verified the PDF's publisher/document identity and locator. Record:

- original PDF URL;
- publisher/source identity;
- document title/date when source-supported;
- filename when known;
- verification time/mode;
- `materialization_status = pending_materialization` unless bytes already exist.

For PDFs on mainstream official, regulator, issuer or institutional publisher sites, this is enough to accept the document as a legitimate source identity. Do not spend cycles proving that a particular GitHub runner or interactive network path can download the bytes.

**But locator existence alone does not prove a claim whose content has not been read.**

### `content_verified`

If the current Agent can actually read the relevant PDF content in a trustworthy interactive surface, preserve the claim-scoped excerpt/page/section or equivalent readable grounding plus truthful representation provenance. That material may enter normal Evidence semantics even if raw PDF bytes have not yet been downloaded or SHA-pinned.

This separates two questions:

1. Did the source say the claim-relevant thing?
2. Have we already materialized the byte-identical original file?

The first is required for claim grounding; the second is completeness/integrity enrichment.

### `materialized`

A later Agent with normal network access may download the recorded PDF URL and append:

- raw byte size;
- SHA-256;
- durable storage locator/receipt;
- identity/content verification against the earlier record.

If later bytes contradict the earlier verified source identity or claim-scoped readable content, fail closed and open an integrity repair. Never silently replace the earlier record.

## GitHub Actions / Release

Do **not** create GitHub Actions merely to download new PDF source files.

Actions remain valid for service-capable execution such as PostgreSQL integration/runtime probes. Existing immutable GitHub Release source packs remain valid historical materializations and may be reused when already available; they are not the default pattern for new PDFs.

Historical Release packs may also contain HTML/web/JSON or mixed source payloads because they predate the current representation-specific rules. Keep them immutable under their existing receipts; do not migrate them for cosmetic consistency.

## Other Longcycle-generated state: Google Drive

- DuckDB replay materializations, generated execution/reconciliation output, generated database snapshots and offline runtimes are relayed through Google Drive during development.
- Generated Drive assets remain identity/digest pinned and are restored on demand.
- A webpage capture capsule is source-derived capture material, not a model-generated research conclusion.
- Deferred PDF materialization may use whatever durable development file/object transport its owning receipt specifies; no single transport is required merely to let Evidence work proceed.

## Git control plane

Git contains task specs, source locators, document identities, claim-scoped authority/provenance, readable Evidence captures, optional raw-byte hashes/materialization metadata, Evidence/Reality/Judgment/Outcome receipts, replay metadata and handoff/data-plane manifests.

Do not create hundreds of per-page Git capture commits and do not manufacture downloader workflows just to satisfy transport mechanics.

Neither Google Drive nor GitHub Release is the final production archive. This is a development-stage arrangement. Future production storage may move to selected server/object-store/database infrastructure without changing epistemic or temporal semantics.
