# Longcycle Continuity Architecture

## 1. Why this subsystem exists

Longcycle must survive many chat windows, Agents, model vintages and industry benchmarks without asking the user to reconstruct project history.

Continuity therefore has five jobs:

1. preserve the founding mission with high semantic fidelity;
2. preserve distilled cross-industry methodology without dragging old-industry narrative into every session;
3. expose a live typed continuation cursor under a strategic goal/workstream hierarchy;
4. keep long-running Agents vertically aligned so local optimization and benchmark gaming do not replace product progress;
5. identify exactly which external binary bytes are required, where they live, how to verify them and whether the current cursor needs them at all.

The target is **minimum sufficient context + minimum sufficient bytes**.

## 2. Control plane versus data plane

The repository owns meaning and identity; external stores move bytes.

```text
Git control plane
  issue #2 rendezvous
  Strategy / Method / calibration
  current.json
  data-plane.json
  receipts / code / CI
        ↓ identifies transport + hashes
external development data plane
  GitHub Release = externally acquired immutable source payloads
  Google Drive   = Longcycle-generated replay/execution/runtime state
```

The control plane is authoritative for what an asset is, why it matters and which digest it must have. Release and Drive are transport/cache layers, not research truth.

## 3. Why the data plane is split

Earlier continuity work treated Google Drive as the single large-file lane. Real source-acquisition and replay work exposed a category error: externally acquired Evidence bytes and Longcycle-generated analytical state are not the same kind of object.

The corrected boundary is semantic, not cosmetic:

### GitHub Release

For externally acquired immutable source material:

- PDF / HTML / filing / formal announcement bytes;
- deterministic source-acquisition bundles containing those bytes.

Release works well because GitHub Actions can acquire, hash, publish and later restore these bounded source packs directly. A Release asset remains transport only: retrieval host, upstream publisher identity, claim-scoped authority and raw hash still have to be preserved separately.

### Google Drive

For Longcycle-generated state:

- DuckDB replay materializations;
- execution/reconciliation output packs;
- generated DB snapshots when explicitly useful;
- offline runtime packs.

A generated pack can summarize or replay archived Evidence but must never be mistaken for the original source archive.

This split prevents two dangerous confusions:

1. putting source bytes into a generic generated-state cache and losing their acquisition/authority identity;
2. putting generated DB/replay state into a source-oriented Release lane and encouraging future Agents to treat derived state as source truth.

## 4. Database role separation

```text
Archive/source lane
  externally acquired raw source identity
  → development transport via GitHub Release when needed

PostgreSQL
  transactional collection/write/ops runtime
  → recreated in service-capable environments

DuckDB / execution packs
  portable generated read/replay state
  → development transport via Google Drive when needed
```

Do not transport a live PostgreSQL cluster between sessions. If a generated DB snapshot is genuinely useful, it is a Drive asset and is explicitly labeled as a snapshot, not live authority.

DuckDB remains a read/replay materialization, not a substitute for raw Evidence.

## 5. State layers and ownership

```text
issue #2 / FRESH_AGENT_BOOTSTRAP
    stable rendezvous
        ↓
STRATEGIC_COMPASS.md
    terminal mission + researcher-understanding success criterion
        ↓
METHODOLOGY_CORE.md
    cross-industry method
        ↓
.longcycle/continuity/mission-fidelity.json
    semantic calibration
        ↓
.longcycle/handoff/current.json
    live goals / workstreams / cursor
        ↓
.longcycle/handoff/data-plane.json
    resume-relevant binary identity / transport / digest / restore contract
        ↓
active context / receipts
    current benchmark facts and decisions
        ↓
verified external bytes only when required
```

Old devlogs, old industries and old packs are not default memory.

## 6. Product-centered continuity

Continuity is successful only if the next Agent recovers the product meaning, not merely the task ID.

A fresh Agent must understand that Longcycle is not optimizing for crawler coverage, schema elegance, Agent throughput or benchmark score. The terminal product should let an industry researcher quickly build a defensible mental model of an industry: structure, actors, key variables, historical branches, contemporaneous expectations and disputes, later outcomes, source grounding and material unknowns.

Therefore artificial-ignorance tests must ask both:

- “what do I do next?” and
- “why is that next action valuable to a researcher?”

## 7. Workstream graph and anti-tunnel loop

A continuation cursor belongs to a typed workstream (`main_path`, `supporting_quality_gate`, `parallel_track`) which points upward to a strategic goal.

At each coherent task boundary:

```text
atomic task
↑ owning workstream / role
↑ short or medium goal
↑ terminal mission
```

Then test `done_when` and marginal product value. A benchmark that has already exposed enough primitives should be frozen rather than extended for count. Continuity infrastructure itself should stop once the handoff passes.

## 8. Binary packset behavior

A fresh session never restores “the database” by default. It restores only a **packset selected by the current cursor**.

If all manifest assets have `required_for_current_task=false`, the correct action is to restore nothing.

When bytes are required:

- source task → exact Release source pack + hash verification;
- replay/execution/runtime task → exact Drive generated pack + hash verification;
- if re-grounding needs both, restore them separately so source authority and generated state remain distinct.

The manifest is resume-relevant rather than an exhaustive historical inventory.

## 9. Runtime is part of usable generated state

A generated DuckDB pack is unusable if the sandbox cannot open it. Runtime packs therefore pin ABI, architecture, version and SHA.

ABI mismatch fails closed and produces a new Drive runtime asset. It is never solved by forcing an incompatible wheel.

## 10. Micro-checkpoint lifecycle

```text
substantive work
→ substantive commit
→ vertical alignment
→ upload/verify any new resume-relevant asset on the correct transport
→ update data-plane.json
→ update completion/exit receipt if the research state changed materially
→ update current.json with checkpoint base = latest substantive/control-plane commit before current.json
→ handoff-only commit
→ refresh CI
→ artificial-ignorance rehearsal
```

Because the checkpoint base predates the `current.json` commit, live HEAD can normally be one handoff-only commit ahead. Fresh Agents classify the delta instead of treating any mismatch as automatic corruption.

## 11. Failure modes discovered by real drills

### Stale cursor despite repository progress

A previous `current.json` lagged many substantive commits and still described work already completed.

Repair: every substantive session advances the repository handoff; fresh Agents compare checkpoint base with live HEAD and inspect intervening commits.

### Storage-category drift

The implementation schema and manifest diverged between Drive-only and Release-only concepts, causing CI failures and ambiguous restore behavior.

Repair: data-plane v2 makes transport role explicit and type-checked: raw source acquisition packs must use Release; Longcycle-generated binary assets must use Drive.

### Bootstrap prose drift

Even after the typed manifest was corrected, `CONTINUE_HERE.md` and protocol/design prose still described Drive-only transport. A fresh Agent could therefore pass schema validation but follow the wrong operational rule.

Repair: bootstrap, normative protocol, design architecture, schema and regression tests are updated together.

### Database bytes without compatible runtime

A valid DuckDB pack can still be unusable under a different Python ABI.

Repair: runtime compatibility is first-class generated asset state; mismatch fails closed.

### External-store metadata mistaken for integrity

Filename, tag, Drive id and timestamps are insufficient.

Repair: repository-pinned outer SHA-256 and important inner hashes are mandatory.

## 12. Test pyramid

1. **Static contract** — schemas, bounded resume set, unique assets, SHA shapes, workstream/cursor validity and role/transport matching.
2. **Repository-only reconstruction** — no chat history; recover mission, current goals, current industry and cursor from bounded Git state.
3. **Transport check when required** — restore only required Release/Drive objects and verify exact bytes.
4. **Offline usability when required** — clean environment, pinned runtime, open generated DB read-only.
5. **Artificial ignorance** — answer mission/current state/next task/storage requirements using only the cold-start read set.
6. **Genuine fresh session** — separate Agent/session when useful.

A pass requires semantic fidelity and operational usability. A current cursor that requires no old binary state should explicitly pass by restoring none.

## 13. Stop condition for continuity work

Continuity is infrastructure. Once a fresh Agent can recover:

- why Longcycle exists and who it serves;
- the current industry and why it was selected;
- what was just completed;
- the exact next atomic action and its stop condition;
- whether any binary asset is currently required;
- the Release(raw source) / Drive(generated state) boundary;

without chat history, the continuity task is complete and the main path returns to research.
