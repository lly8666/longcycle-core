# AGENTS.md

## Fresh-session rule

For any task that resumes existing Longcycle development, research, CI repair or Memory Atlas work, start with `CONTINUE_HERE.md` and `.longcycle/handoff/current.json` before making substantive changes.

Do not ask the user to restate context already persisted in the handoff unless a genuinely unresolved ambiguity remains after reading the repository.

## Live-state rule

A handoff checkpoint is a snapshot. Always refresh the active PR/branch HEAD and relevant CI before reporting current implementation status.

If live repository state conflicts with an older chat summary, live repository state wins for implementation facts.

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

Do not store private model chain-of-thought. Store decisions, observations, user directives, alternatives considered at a useful engineering level, and reasons needed to reproduce execution behavior.

## Context economy

Use the checkpoint `resume_read_set`, compact indices and targeted file reads. Do not preload the whole repository or all raw Memory Leads into a fresh session unless required.