# Parallel database and Google Drive data-plane protocol

This protocol extends the remote worker continuity contract for database-shaped artifacts. It
applies whenever two or more Longcycle workstreams may restore, transform, upload or consume a
DuckDB/SQLite capsule, a generated database snapshot or a PostgreSQL-derived export.

The invariant is simple:

```text
Git on refreshed main = current generation authority
Google Drive          = immutable byte transport
worker database       = private disposable workspace
serial integration    = the only generation promoter
```

Drive file names, folder listing order, local caches and chat are never current-version authority.
A database file already uploaded to Drive is immutable by policy even if Drive technically permits
replacement or editing.

This does not replace Longcycle's proven binary path. Generated databases still use the authorized
ChatGPT/Google Drive transfer used by the existing BLENREP receipts: keep the file private, upload a
new object to the recorded handoff folder, capture its Drive file id/name/MIME/size/SHA-256, download
it back by id, verify the outer bytes, and open/read the database locally. Large generated database
bytes do not move to GitHub merely because development is parallel. The rules below only add worker
isolation and single-owner promotion around that same path.

## 1. Roles and ownership

### Worker Agent

A worker may:

- restore an exact main-promoted base generation;
- verify it and open it read-only;
- copy it into workstream-private storage or create an isolated PostgreSQL database/schema;
- produce a deterministic change bundle or a new immutable candidate database;
- publish upload intent/outcome receipts under its reserved workstream;
- request serial promotion.

A worker may not:

- open one shared Drive-backed or local database for concurrent writes;
- overwrite an existing Drive file or infer identity from a file name;
- edit `.longcycle/handoff/data-plane.json` or promote its own candidate;
- allocate canonical migration numbers;
- treat an uploaded candidate as integrated product state.

### Data-plane integration Agent

The one `global_serial` integration lane owns:

- the bounded `database_generation_heads` pointers on refreshed main;
- ordering and replay of candidate changes;
- canonical migrations and schema compatibility;
- semantic conflict resolution through the owning capability/workstream;
- upload and round-trip verification of the integrated generation;
- compare-before-update promotion of the Git generation head.

There is no extra permanent coordinator hierarchy for this. Data-plane integration is a duty of the
existing serial integration role; a specialized temporary Agent may execute it while remaining
under that fence.

## 2. Download and restore transaction

Before download, the worker records or references this base descriptor:

```text
lane_id
base_generation_id
base_google_drive_file_id
base_drive_revision_id (when available)
base_sha256
base_size_bytes
base_schema_revision
main_pointer_sha
```

Then it:

1. refreshes main and reads the matching generation head;
2. downloads by exact Drive file id, not by file name or "latest" listing;
3. verifies revision identity when available, byte size and SHA-256;
4. restores to a private path derived from workstream id plus assignment epoch;
5. opens the restored DuckDB/SQLite base read-only;
6. copies it before transformation, or creates a workstream-isolated PostgreSQL database/schema.

A missing object, revision mismatch, digest mismatch or schema mismatch is `BLOCKED`. The worker
does not silently substitute another similarly named file and does not repair the main pointer.

Local downloads are disposable caches. They may speed up a returning Agent, but the next invocation
or a Fresh Agent must be able to reconstruct the same base from remote Git plus exact Drive identity.

## 3. Candidate shape

Prefer a deterministic change bundle over a whole database snapshot when the database engine and
semantics permit replay. A candidate receipt pins at least:

- candidate id and producing workstream/assignment epoch;
- exact producer branch and substantive head;
- base lane, generation, digest and schema revision;
- operation kind and deterministic replay entrypoint;
- candidate Drive file/revision id, SHA-256 and byte size;
- proposed schema/migration effect;
- affected semantic keys or declared conflict domain when knowable;
- verification head/refs, limitations and requested integration action.

A whole candidate database is acceptable when a change bundle would be misleading or cannot be
replayed safely. It is still only a candidate derived from an exact base, never a new current head.

## 4. Recoverable Drive upload

Drive upload is an external side effect and uses a two-receipt transaction.

The byte operation follows the already-proven sequence:

1. checkpoint/close the local database and compute SHA-256, size and schema/content counts;
2. upload a newly and uniquely named private file through the authorized ChatGPT/Drive path to the
   manifest's `google_drive_folder_id`;
3. capture the returned Drive file id and revision when available;
4. download the object back by exact file id;
5. recompute size/SHA-256 and open/read the DuckDB/SQLite capsule locally;
6. record `download_back_verified` plus the exact locator/integrity/schema facts in Git.

No sharing permission change is required. Git stores the receipt and locator, not the large bytes.

### Intent, pushed before upload

The bounded intent receipt contains:

```text
operation_id / stable idempotency key
workstream_id + assignment_epoch
producer_head_sha
base_generation_id + base_sha256
candidate_sha256 + candidate_size_bytes
operation_kind + exact target folder
verification method
```

The intent is pushed as S and acknowledged by H before the upload. A deterministic candidate name
may aid humans but never defines identity.

### Outcome, pushed after observation

After upload, the worker obtains the new Drive file id and revision identity when available,
downloads or otherwise reads back the stored bytes, verifies size and SHA-256, and pushes an outcome
receipt that links to the same operation id. H then acknowledges that outcome.

If interruption leaves intent without outcome, the next invocation runs the normal recovery gate
before new work. It inspects the exact handoff folder using the intent's unique candidate name and
expected digest, then downloads any match for verification. It must not assume that "no Git
outcome" means "no upload". If one verified object is found, write the missing outcome. Retry with
the same operation id only when a reliable query proves no object exists. If external state is
ambiguous, mark `BLOCKED` for integration review instead of creating another blind upload.

## 5. Serial integration and promotion

For each candidate, the integration Agent:

1. refreshes main and rereads the current generation head;
2. verifies producer/fence, candidate receipt and immutable Drive bytes;
3. compares the candidate's base generation/digest with the current head;
4. if current, applies or imports it in an isolated integration database;
5. if stale, deterministically replays it on the new head or rejects/routes a conflict;
6. applies candidates in an explicit order and allocates canonical migrations serially;
7. runs schema, semantic, point-in-time and product validation on the exact integration head;
8. closes the database, uploads a new immutable integrated object and round-trip verifies it;
9. writes an integration receipt with predecessor/current identities;
10. updates the Git generation head only if the expected predecessor is still current.

Step 10 is the compare-and-swap boundary. The normal fast-forward main/integration workflow is the
serialization mechanism. If main advanced, promotion restarts from step 1; it never overwrites the
newer pointer or declares the most recently uploaded Drive file to be current.

Database snapshots are not byte-merged. Independent candidates are replayed through their declared
operations. When both touch the same schema, semantic key or source-derived claim, the owning
capability/workstream resolves the meaning before integration.

## 6. Conflict classes

| Conflict | Prevention or resolution |
| --- | --- |
| Two workers upload the same name | Names are non-authoritative; every candidate is a new immutable Drive object with exact id/digest. |
| Two workers start from an old base | Candidate receipts pin the base; serial integration detects staleness and replays or rejects. |
| Two workers modify one local/remote DB | Each workstream uses a private file or isolated PostgreSQL database/schema. |
| Two migrations choose the same number | Workers submit proposals; the serial lane allocates canonical numbers. |
| Two candidates change the same meaning | Semantic owner resolves it; Drive/Git ordering cannot decide semantic truth. |
| Upload completes but the Agent is interrupted | Intent/outcome recovery queries the external effect before retry. |
| A Drive object changes after publication | Revision/digest verification fails closed; a successor object gets a new identity. |

## 7. Handoff and bounded lifetime

The cursor carries only exact active base/candidate/intent/outcome refs needed for its current task.
It does not copy database bytes, append upload history or keep every predecessor hot.

The global manifest holds at most eight active promoted generation heads. Each head contains one
lane's current Drive identity/digest/schema/predecessor and exact integration receipt. Superseded
generations and candidate chronology remain cold behind Git receipts and Drive identities. A later
Agent retrieves them only for a concrete repair, replay or audit.

This makes handoff cost depend on active database lanes and unresolved external effects, not project
age or the number of prior Agents.

## 8. Pilot rule

The first real Banking/Shipping candidate should exercise this protocol without inventing a generic
merge language in advance. Harden candidate and upload receipt body schemas only from the fields the
pilot actually needs. Remote identity, immutable bytes, isolated writes, base comparison, single
promotion ownership and truthful interruption recovery are hard requirements; wording, timing and
unneeded metadata are not.
