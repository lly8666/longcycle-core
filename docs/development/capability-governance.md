# Longcycle Capability Governance

## Purpose

Long-running Agent development has a second memory failure mode beyond repaired bugs: the system already has a capability, but a later Agent no longer remembers that ownership and creates a near-duplicate implementation under a new name.

Longcycle therefore keeps a **sparse capability registry**. It records stable system responsibilities, not every function/class/helper.

```text
Capability Registry = what Longcycle already knows how to do + who owns each stable semantic
Repair Memory       = why a non-obvious invariant must not be accidentally regressed
Git history         = chronological development history
Architecture docs   = why the system is shaped this way
Handoff             = what matters now and what comes next
```

None replaces the others.

## Stable capability granularity

Create/update a capability card when a stable responsibility changes, for example:

- source acquisition/archive;
- Grounded Evidence;
- canonical Reality;
- Judgment/Outcome memory;
- point-in-time replay;
- memory campaigns;
- research orchestration;
- operational scheduling;
- session continuity.

Do **not** create a card for ordinary helpers, private classes, one more CLI flag, formatting changes, refactors that preserve ownership, or campaign-specific data.

A capability card answers:

- what user/system responsibility exists;
- which semantic keys it owns;
- where its application/port/CLI entrypoints are;
- what extension seams future work should use;
- what it explicitly does not own;
- which executable/structural guards protect it.

## Admission before material capability development

Before material product/architecture work, search the registry by intent:

```bash
python scripts/capability_registry.py relevant "researcher historical trajectory view"
```

Then classify the intended change:

```text
reuse
extend
replace
new
```

The default is **reuse or extend**.

`new` means a new semantic owner, not merely a new file or UI. Under the current `converging` mode it requires:

1. the closest existing capability/capabilities;
2. a concrete unmet requirement that cannot be truthfully handled by their extension seams;
3. evidence references showing the unmet need;
4. planned ownership paths;
5. a proposed capability id.

Architectural preference ("cleaner", "more generic", "future-proof") is not an unmet requirement.

The current material change is recorded in:

```text
.longcycle/capabilities/current-admission.json
```

This is **not a history ledger**. It stores only the current/latest admission decision; Git history preserves prior decisions.

## One semantic owner

Each active capability declares canonical `owned_semantics`.

The registry audit rejects exact duplicate active ownership. Names/aliases are only routing hints; they are not authoritative ownership.

Stable/core capabilities should expose extension seams so new entrypoints can delegate without creating another owner. A CLI, workflow, API or researcher view may multiply while the underlying semantic owner stays singular.

Example:

```text
typed point-in-time replay
    owns knowledge-cutoff / no-lookahead visibility
        ↑
researcher trajectory view
CLI table
future web timeline
```

Those views are extensions, not new replay engines.

## Maturity

Capability maturity:

```text
experimental
stable
core_locked
```

- `experimental`: shape may still consolidate.
- `stable`: prefer extension and explicit replacement.
- `core_locked`: new overlapping sibling ownership requires demonstrated truthful need or explicit supersession; convenience is insufficient.

Current repository governance mode is `converging`.

## Evolution horizon carried across handoff

The generated compact index includes this permanent governance horizon and is required in the default handoff read set.

### Short term

Every material capability change performs registry discovery, records `reuse/extend/replace/new`, keeps ownership/guards current, and runs the audit.

### Medium term

As product surfaces and industries grow, keep one semantic owner per stable capability. Expand cards only when stable responsibility changes. Tighten deterministic ownership/coverage checks where real duplicate-development failures appear.

### Long term

As architecture settles, promote mature owners to `core_locked`. Adding a near-duplicate capability should become exceptional: a real truthful-representation/product requirement must show why extension is insufficient, or the work must explicitly supersede an old owner.

This horizon evolves with the architecture in the registry/index itself rather than being copied into every session narrative.

## Handoff integration

Fresh sessions already recover long-, medium- and short-horizon work through the typed handoff.

Capability governance is attached without duplicating those horizons:

- `AGENTS.md` owns the permanent pre-development admission rule;
- `.longcycle/capabilities/active-index.json` is always in `resume_read_set`;
- the compact index carries governance mode + short/medium/long evolution horizon;
- the current handoff workstream/cursor mentions governance only when it is actually active work;
- `current-admission.json` records the latest material capability disposition;
- CI runs `capability_registry.py audit`.

Therefore capability governance remains visible after every handoff even when the current task changes, but it does not consume the project strategic horizon with repeated policy prose.

## Update lifecycle

After a material capability change:

1. update the owning card only if stable responsibility, entrypoint, extension seam, guard or maturity changed;
2. create a new card only for genuinely new semantic ownership;
3. update `current-admission.json`;
4. run:

```bash
python scripts/capability_registry.py rebuild-index
python scripts/capability_registry.py audit
```

5. run normal CI;
6. update handoff if the next Agent's task/horizon changed.

Internal refactors that preserve stable ownership should not churn the registry.

## Why similarity is not a hard gate

Text/embedding/LLM similarity may later improve `relevant` discovery, but it must not decide architectural identity.

Hard enforcement is based on explicit semantic ownership, entrypoints, scopes, lifecycle and guards. Similarity can remind an Agent that two capabilities may overlap; it cannot prove that they do.
