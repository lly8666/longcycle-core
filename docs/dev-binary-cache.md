# Development binary storage

Longcycle uses a split development-stage binary data plane so external source material and Longcycle-generated state do not share the same transport.

## External source bytes: GitHub Release

- Release tag: `longcycle-dev-binary-cache`
- External PDFs, HTML, filing payloads, announcement payloads, and immutable acquisition/source packs downloaded from the public internet by GitHub Actions go directly to this Release.
- These assets remain outside Git history and outside Google Drive.
- Every source asset has a unique immutable filename and recorded SHA-256. The producing Action downloads the Release asset back and verifies SHA-256 before the upload is accepted.
- A test/research run restores only the required source asset to the Actions runner or ChatGPT sandbox, verifies SHA-256, and uses the local copy as materialized input.

## Longcycle-generated state: Google Drive

- DuckDB databases, replay capsules, generated manifests/reports, database snapshots or other Longcycle-produced research state are relayed through the connector to the Longcycle Drive handoff/cache folder.
- Hermetic/offline runtimes needed by the sandbox also live on Drive rather than in the Release because they are generated execution support, not externally acquired evidence.
- Generated Drive assets remain SHA-pinned and are restored on demand to a sandbox or Action runtime.
- Do not put external source PDFs/HTML into Drive merely because a generated replay depends on them; keep source identity/hash in Git and retrieve source bytes from the Release when re-grounding is required.

## Git control plane

Git contains task specs, source identity, authority/provenance, SHA-256 values, Evidence/Reality/Judgment/Outcome receipts, replay metadata and the handoff/data-plane manifests. Large binaries stay outside Git.

Neither GitHub Release nor Google Drive is the final production archive. This split is an explicit development-stage arrangement. After Longcycle is operational, move durable source/archive bytes and production databases to the selected server/object-store/database infrastructure without changing epistemic or temporal semantics.
