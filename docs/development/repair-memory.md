# Longcycle Repair Memory

## Purpose

Long-running Agent development has a specific regression mode: a repair remains in the code, but the reason for the repair disappears from working memory. A later Agent then “simplifies” the code back toward the old shape and reintroduces the same failure.

A chronological maintenance diary does not solve this well. It grows without bound, duplicates Git history, and is unlikely to be read before a local edit. Longcycle therefore uses **bounded Repair Memory**:

```text
active invariant          = what must remain true and why
executable/structural guard = what prevents silent regression
Git history               = cold chronological repair history
```

Repair Memory is not a second devlog and not a replacement for tests.

## Promotion rule

Do **not** create an invariant for every bug. Ordinary defects should normally end as a code change plus regression test.

Promote a repair into Repair Memory only when at least one of these is true:

1. the same failure or near-failure has already recurred;
2. the fix establishes a non-obvious architectural/data-integrity rule that a future cleanup could plausibly reverse;
3. the failure can corrupt temporal truth, provenance, authority, evidence identity, continuity, or other high-value invariants;
4. the repair spans layers/adapters and a local test alone would not explain why the boundary exists;
5. there is a tempting but wrong simplification that future maintainers are likely to repeat.

The target is a **sparse set of high-value invariants**, not exhaustive memory.

## Storage model

Active cards live under:

```text
.longcycle/repair-memory/invariants/*.json
```

A compact generated index lives at:

```text
.longcycle/repair-memory/active-index.json
```

The index contains only routing metadata: id, title, severity, scope, tags and card path. It intentionally excludes full rationale. A fresh Agent first resolves intended code paths against the index and loads only matching cards.

Each card is size-bounded and contains only the current rule:

- failure signature;
- root cause;
- invariant that must remain true;
- common regressions to reject;
- path scope;
- concrete guards;
- conditions under which the invariant may legitimately be revisited;
- compact origin references.

Cards must not accumulate chronological history. When understanding changes, update or supersede the existing invariant. Git already preserves every prior version.

## Guard rule

A repair explanation is memory; a guard is enforcement.

Every active non-process invariant must point to at least one executable or structural guard such as a test, type boundary, schema constraint or runtime hard gate. Process invariants may use a normative protocol guard when the failure concerns authority or operating procedure.

Guard entries include a path and a small required marker. `scripts/repair_memory.py audit` verifies that the path and marker still exist. This is a tripwire against silently deleting the very guard that justified the repair; normal CI/tests still prove the behavior itself.

## Before editing

When a substantive edit has identifiable target paths, query Repair Memory first:

```bash
python scripts/repair_memory.py relevant \
  src/longcycle/domain/models.py \
  src/longcycle/adapters/storage/postgres.py
```

For a bug symptom whose code location is not yet known, search the compact cards by words from the failure:

```bash
python scripts/repair_memory.py query "evidence provenance"
```

No match means proceed normally. A match means read the returned invariant before modifying the scoped boundary.

This lookup is deliberately **path- and symptom-scoped**. Do not load every repair card into session context.

## After repairing

1. Fix the root cause.
2. Add or strengthen an executable/structural guard when possible.
3. Search Repair Memory before creating a new card.
4. If an existing invariant owns the same root cause, update that card instead of appending another story.
5. If promotion criteria are not met, do not create a card.
6. Rebuild and audit the compact index:

```bash
python scripts/repair_memory.py rebuild-index
python scripts/repair_memory.py audit
```

7. Run the normal test/CI gates.

## Lifecycle and bloat control

Repair Memory stays small by design:

- one current card per invariant, not one card per repair attempt;
- no chronological notes inside cards;
- per-card byte and text limits enforced by the audit;
- compact index contains routing metadata only;
- superseded/retired reasoning remains recoverable from Git history;
- default Agent context loads only cards matching the current edit;
- broad architectural truth remains owned by Strategy/Method/architecture documents rather than copied into repair cards.

If many cards start matching one ordinary file, scopes are too broad or invariants are too granular and must be consolidated.

## Authority

Repair Memory explains **why a local boundary exists**. It does not outrank new explicit user intent, Strategy, Method Core, live Git/CI truth, or a deliberately adopted replacement architecture.

An invariant is not “never change this.” It is “do not change this accidentally.” `revisit_when` defines what evidence would justify reopening the decision. When that condition is met, change the architecture deliberately, update the guard, and update/supersede the card in the same coherent repair.
