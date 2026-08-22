# Longcycle Continuity Architecture

## 1. Why this subsystem exists

Longcycle is expected to survive many chat windows, Agents, model vintages and industry benchmarks. Continuity therefore has to preserve both **meaning** and **usable state** without requiring an Agent to replay project history or requiring the user to reconstruct it.

The continuity subsystem has five jobs:

1. preserve the founding mission with high semantic fidelity;
2. preserve distilled cross-industry methodology without old-industry narrative growth;
3. expose a live typed continuation cursor under a strategic goal/workstream hierarchy;
4. keep long-running Agents vertically aligned so local optimization does not replace product progress;
5. tell a fresh Agent exactly which external binary research state it needs, how to verify it, and how to open it in a constrained sandbox.

The target is **minimum sufficient context plus minimum sufficient bytes**, not minimum text and not a monolithic database copy.

## 2. Control plane versus data plane

The original repository-backed handoff solved the control-plane problem well but assumed that implementation/research state was text-addressable. Real grounded-evidence benchmarks exposed a second problem: the useful state includes DuckDB packs, original evidence bytes and sometimes an offline runtime, none of which belongs in Git text.

The architecture is therefore split:

```text
Git control plane
  FRESH_AGENT_BOOTSTRAP.md
  issue #2 rendezvous
  Strategy / Method / calibration
  current.json
  data-plane.json
  receipts / code / CI
        ↓ identifies + hashes
external binary data plane
  Google Drive under the current environment constraint
  immutable bounded research/evidence/runtime assets
```

The control plane is authoritative for **what** an asset is and **which digest** it must have. The external store is only a byte transport/cache.

## 3. Why Google Drive is not the database

Current ChatGPT constraints make `sandbox ↔ Google Drive` the practical high-bandwidth path for large files, while GitHub text writes cannot carry them and GitHub Actions cannot directly pull from Drive. That creates a relay topology, not a storage philosophy.

Drive has bounded capacity and may eventually disappear from the product architecture. Therefore:

- no semantic identity depends on Drive path/name/timestamp;
- every required asset is immutable and hash-pinned from Git;
- fresh sessions restore only required packs rather than the whole corpus;
- changing infrastructure later requires changing transport locators, not research identity;
- original content hashes, parser artifact hashes and research pack hashes remain portable across backends.

## 4. Database role separation

The handoff architecture follows the proven storage boundary:

```text
ArchiveStore
  original HTML/PDF + deterministic artifacts

PostgreSQL
  transactional collection/write/ops runtime

DuckDB
  portable bounded research/evidence replay materialization
```

Moving PostgreSQL clusters between sessions would couple handoff to server state, database binaries and mutable operational tables. It would also waste the limited Drive budget. PostgreSQL is therefore recreated when transactional semantics are needed.

DuckDB packs are appropriate handoff units because they are single-file, analytical, verifiable and can be opened read-only. They are not substitutes for original evidence bytes.

## 5. Runtime is part of usable state

A binary database file is not a complete handoff if the new sandbox cannot open it. The first real Drive drill demonstrated this directly: a DuckDB 1.5.5 CPython 3.11 wheel was perfectly valid but unusable in the current CPython 3.13 sandbox.

Therefore runtime compatibility is first-class handoff metadata:

- Python major/minor ABI;
- architecture;
- runtime/version;
- wheel/binary byte size and SHA-256;
- offline install instruction;
- clean-venv smoke test.

ABI mismatch fails closed and produces a new immutable runtime asset. It is never solved by forcing an incompatible wheel.

## 6. State layers and ownership

```text
main/FRESH_AGENT_BOOTSTRAP.md
    stable cold-start pointer
        ↓
STRATEGIC_COMPASS.md
    terminal mission
        ↓
METHODOLOGY_CORE.md
    cross-industry method
        ↓
.longcycle/continuity/mission-fidelity.json
    semantic calibration
        ↓
.longcycle/handoff/current.json
    live goals / workstreams / cursor / data-plane pointer
        ↓
.longcycle/handoff/data-plane.json
    required external asset identities + hashes + restore contract
        ↓
active context / receipts
    current benchmark facts
        ↓
verified external bytes
    portable DB/archive/runtime assets
```

Old devlogs and old packs are cold storage, not default memory.

## 7. Mission assimilation and authority

Fresh Agent sequence remains think-first, calibrate-second. Strategy and Method are read before the semantic calibration contract so the Agent must generate its own causal understanding instead of copying an answer key.

Strategic authority:

```text
new explicit user instruction
> Strategy
> Method Core
> dynamic horizon
> old narrative
```

Implementation/data freshness:

```text
live Git/CI + repository receipts + hash-verified external bytes
> deterministic-derived state
> checkpoint snapshot
> narrative / external-store metadata
```

Private chain-of-thought is never persisted.

## 8. Workstream graph and anti-tunnel loop

A continuation cursor belongs to a typed workstream (`main_path`, `supporting_quality_gate`, `parallel_track`) which points upward to a strategic goal. Supporting infrastructure may temporarily own the cursor but cannot silently become the product roadmap.

At each coherent task boundary ask:

```text
atomic task
↑ owning workstream / role
↑ short or medium goal
↑ terminal mission
```

Then test whether `done_when` has been met and whether additional local work still has meaningful parent-level value.

## 9. Binary packset behavior

A fresh session does not restore “the database.” It restores a **packset** selected by the current cursor.

Examples of pack roles:

- current research/evidence capsule;
- portable DuckDB industry/time/task pack;
- content-addressed cold archive bundle;
- offline runtime pack.

An asset may contain multiple verified components, such as a DuckDB file plus execution receipt and archived blobs. `data-plane.json` pins the outer object and the important inner components.

When the project spans dozens of industries, this design scales by adding bounded immutable packs and loading only the active subset. It avoids full-corpus copies on every 20–30 minute development handoff.

## 10. Capacity and supersession

Under the current ~15 GB Drive constraint:

- active/recent packs stay hot;
- historical packs can be removed from Drive after verified successor/cold-storage migration;
- Git manifests remain tiny;
- assets are never mutated in place;
- a new version receives a new logical asset id and external file id;
- garbage collection is explicit and cannot delete something referenced by the current handoff.

The sandbox's larger local disk is working space, not durable authority.

## 11. Micro-checkpoint lifecycle

```text
substantive work
→ substantive commit
→ vertical alignment
→ produce/verify any new required binary asset
→ relay asset through sandbox to Drive when needed
→ verify Drive→sandbox roundtrip
→ update data-plane.json
→ update current.json with checkpoint base = substantive commit
→ handoff-only commit
→ refresh CI
```

Both handoff JSON files are mutable handoff state. Binary assets are outside Git.

## 12. Failure modes discovered by real drills

### Stale cursor despite repository progress

A repository-only recovery found `current.json` still claiming Kwinana was blocked on missing PostgreSQL even though live Git had completed Kwinana and Kemerton. This proved that path resolution alone does not prove handoff freshness.

Repair: sequence/cursor must be synchronized after coherent substantive work and fresh Agents must reconcile live Git against checkpoint base.

### Database bytes without compatible runtime

Drive roundtrip preserved the DuckDB capsule perfectly, but the sandbox lacked DuckDB. The first offline runtime pack used CPython 3.11 and was unusable under Python 3.13.

Repair: runtime ABI/version becomes first-class asset state; a Python 3.13 runtime pack is separately verified.

### External-store metadata mistaken for integrity

A filename can survive even if bytes change. Therefore external metadata is insufficient.

Repair: outer and important inner SHA-256 checks are mandatory before use.

## 13. Test pyramid

1. **Static contract** — schemas, bounded files, unique assets, SHA shapes, workstream/cursor validity.
2. **Repository-only reconstruction** — no chat history; recover mission, current goals and cursor from bounded Git state.
3. **Binary transport roundtrip** — Action/sandbox → Drive → sandbox with exact outer/component SHA.
4. **Offline usability** — clean venv, no network, install pinned runtime and open required DB read-only.
5. **Artificial ignorance** — use only the cold-start read set and report current state/data requirements.
6. **Genuine fresh session** — separate Agent/session when useful.

A pass requires both semantic fidelity and operational usability.

## 14. Stop condition for continuity work

Continuity is infrastructure. Once a fresh Agent can recover the mission/current cursor, obtain only required binary assets, verify them, and open the current research pack without chat history, the quality gate is complete.

Further handoff optimization must stop and return to the main product path unless a new real failure appears.
