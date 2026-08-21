# AGENTS.md

## Fresh-session rule

Resume Longcycle through `CONTINUE_HERE.md`. Do not ask the user to restate persisted context.

Read in this order:

1. `STRATEGIC_COMPASS.md` — long-term mission;
2. `METHODOLOGY_CORE.md` — cross-industry method;
3. `.longcycle/handoff/current.json` — current medium/short horizon and active context;
4. live Git HEAD / CI;
5. only the minimal task-specific `resume_read_set`.

Do **not** preload old industries, all devlogs or the full repository.

## Alignment before execution

Before substantive work, state internally:

- final mission;
- current medium-term goal;
- current short-term goal;
- next larger step.

A local task that cannot be connected through those levels should be re-ranked instead of deepened automatically.

## Stable ownership of information

- `STRATEGIC_COMPASS.md` owns mission and anti-drift direction.
- `METHODOLOGY_CORE.md` owns distilled cross-industry methods.
- `.longcycle/handoff/current.json` owns current horizon, workstreams and snapshot state.
- active context owns current industry / benchmark details.
- live Git/CI owns implementation freshness.
- devlogs own historical rationale only.

Never copy fast-changing industry facts into a long-term core. Never copy stable mission/methodology into every checkpoint.

## Core promotion rule

A lesson begins in the current context or devlog. It enters `METHODOLOGY_CORE.md` only after explicit user adoption or enough benchmark evidence that it should survive industry changes.

When adding to a Core, compress/replace existing wording rather than appending indefinitely.

## Epistemic boundaries

Follow `METHODOLOGY_CORE.md`: model memory is not Evidence; historical `not_found != false`; no-lookahead replay; claim-scoped authority; original versions and revisions are not overwritten; comparability comes before corroboration.

Current phase-specific guardrails come from the typed handoff and active context, not this file.

## Continuity maintenance

After a coherent work batch, update the handoff when medium/short goals, active context, blockers, phase, counts or ordered next actions materially change.

If a new user instruction changes mission or methodology, first record it as a pending directive, then update the appropriate Core with auditable rationale. Do not silently redefine strategy from a local implementation preference.

Do not store private model chain-of-thought. Store decisions, evidence, concise rationale and reproducible execution constraints.
