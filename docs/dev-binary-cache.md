# Development binary storage

Longcycle uses a split development-stage data plane so webpage capture, raw PDF source bytes and Longcycle-generated state use the transport that is cheapest and most faithful for that representation.

## Readable webpages: local database -> Google Drive

For a readable webpage, the default path is:

```text
interactive read
→ faithful visible-text capture + provenance metadata
→ bounded local DuckDB capture capsule
→ checkpoint / SHA-256
→ Google Drive handoff
→ Git stores only the compact asset locator/digest/restore contract
```

Do **not** start GitHub Actions merely to fetch or archive HTML for a webpage whose visible content can already be read faithfully in the interactive research surface.

A webpage capture row/capsule should preserve, as applicable:

- original URL and upstream publisher/source identity;
- title and source-displayed date when supported;
- `captured_at` / retrieval context;
- truthful `capture_mode` such as visible-text transcription;
- faithful visible text needed for the bounded capture;
- SHA-256 of the captured text/record or other deterministic integrity fields;
- material capture limitations, including unreadable images or omitted non-visible structure.

The local database is a **capture/handoff envelope**, not live PostgreSQL authority and not automatic Fact/Judgment publication. Drive transport does not upgrade source authority. After restore, normal archive/Evidence semantics still apply.

Batch many webpage captures into a bounded task/industry/time DuckDB when that is faster than per-page Git writes. Before handoff, checkpoint/close the DB, record its schema/version/source count/size/SHA-256, upload an immutable copy to Drive, and pin the Drive file id plus digest in `data-plane.json` or the owning receipt.

## PDFs: GitHub Actions -> GitHub Release

- Release tag: `longcycle-dev-binary-cache`
- PDFs that need raw source-byte preservation are fetched by the existing GitHub Actions acquisition lane.
- The Action validates the response, computes hashes, packages the bytes under a unique immutable filename, uploads the source pack to GitHub Release, downloads it back and verifies SHA-256.
- These raw PDF assets remain outside Git history and outside Google Drive by default.
- A test/research run restores only the required PDF/source pack, verifies the recorded hashes, and uses the local copy as materialized input.

Existing historical Release packs may contain HTML/web/JSON or mixed source payloads because they predate the webpage-local-DB rule. They remain immutable and valid under their existing receipts. Do not migrate or rewrite them merely to make old assets resemble the new default.

## Other Longcycle-generated state: Google Drive

- DuckDB replay materializations, generated execution/reconciliation output, generated database snapshots and offline runtimes are relayed through the connector to the Longcycle Drive handoff/cache folder.
- Generated Drive assets remain SHA-pinned and are restored on demand to a sandbox or Action runtime.
- A webpage capture capsule is also carried through Drive, but its captured visible text remains source-derived material with provenance; it must not be mislabeled as a generated research conclusion.
- Raw PDF bytes stay on the Action -> Release lane unless an explicit future architecture decision changes that rule.

## Git control plane

Git contains task specs, source identity, authority/provenance, SHA-256 values, Evidence/Reality/Judgment/Outcome receipts, replay metadata and the handoff/data-plane manifests. Do not create hundreds of per-page Git capture commits when a bounded local database + one Drive handoff is the more efficient representation.

Neither GitHub Release nor Google Drive is the final production archive. This split is an explicit development-stage arrangement. After Longcycle is operational, move durable source/archive bytes and production databases to the selected server/object-store/database infrastructure without changing epistemic or temporal semantics.
