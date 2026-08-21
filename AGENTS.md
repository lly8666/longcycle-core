# AGENTS.md

## Fresh-session rule

For any task that resumes existing Longcycle development, research, CI repair or Memory Atlas work, start with `CONTINUE_HERE.md` and **read `STRATEGIC_COMPASS.md` before treating the current TODO as an instruction**.

Do not ask the user to restate context already persisted in the handoff unless a genuinely unresolved ambiguity remains after reading the repository.

## Strategy before execution

A fresh Agent must recover two things separately:

1. **strategic direction** — why Longcycle exists, what the lithium benchmark must prove, and what the next larger phase is;
2. **execution state** — active branch/PR, current phase, counts, CI, blockers and immediate ordered actions.

The first comes from `STRATEGIC_COMPASS.md` and the constitution. The second comes from live GitHub plus the typed checkpoint.

Before substantive work, pass the Strategic Alignment Gate in `CONTINUE_HERE.md`. If the immediate task cannot be connected to the end-state mission and lithium end-to-end benchmark, do not keep drilling into it merely because it is technically interesting.

Important strategic anti-drift rules:

- Memory Atlas is a historical coverage instrument, not the product endpoint.
- Lithium is the first proof/benchmark, not the only industry.
- The benchmark is not complete until Reality + Expectation + Outcome can be replayed point-in-time from archived evidence.
- Generic crawler/RAG/agent/database/platform work should not outrun needs demonstrated by the real lithium benchmark.
- CI, handoff and schema work are support infrastructure; keep them strong enough to protect the main path, but do not let them become the main path.
- Current source-first/archive-now collection must survive even while historical recovery is the active research phase.

## Live-state rule

A handoff checkpoint is a snapshot. Always refresh the active PR/branch HEAD and relevant CI before reporting current implementation status.

If live repository state conflicts with an older chat summary, live repository state wins for implementation facts. For product direction, a newer explicit user directive wins; otherwise `STRATEGIC_COMPASS.md` and the constitution outrank local implementation convenience.

## Project intent

Read `docs/development/project-constitution.md` before changing core product/research semantics.

Important boundaries include:

- Longcycle is an evidence-backed, replayable industrial memory.
- Preserve Reality and point-in-time Expectation/Judgment separately.
- Model Memory / Memory Leads are not Evidence.
- Historical `not_found != false`.
- Do not overwrite historical source versions, model vintages or raw blind-recall artifacts.
- Preserve comparability semantics before corroborating values.

## Lithium Memory Atlas guardrail

While a shard is in blind memory exhaustion and unsealed:

- `source_visibility` / `search_visibility` must remain `none`;
- no fresh web self-verification may be used to stimulate or correct blind recall;
- structural JSON repair must use an explicit repair overlay instead of editing raw model output;
- a shard may seal only under the recorded saturation rule, not because the model says it has nothing else to add.

## Continuity maintenance

After a meaningful coherent work batch, update `.longcycle/handoff/current.json` if any live state changed materially: counts, search phase, CI, blockers, next actions, branch/PR or project directive.

Record major decision changes and their explicit rationale in `docs/devlog/` or an append-only handoff history artifact.

A strategy change requires more than a local implementation preference. It must come from a new explicit user direction or a benchmark result that falsifies a core assumption, and the change must be reflected in `STRATEGIC_COMPASS.md` plus the constitution/devlog.

Do not store private model chain-of-thought. Store decisions, observations, user directives, alternatives considered at a useful engineering level, and reasons needed to reproduce execution behavior.

## Context economy

Use the checkpoint `resume_read_set`, compact indices and targeted file reads. Do not preload the whole repository or all raw Memory Leads into a fresh session unless required.