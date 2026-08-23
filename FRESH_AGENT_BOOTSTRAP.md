# Longcycle — Fresh Agent Bootstrap

This file is a **stable rendezvous pointer**, not project state.

If you are a fresh Agent asked to continue, audit, or understand Longcycle, **do not assume the default `main` branch is the active development state** and do not infer the current roadmap from `main` alone.

## Canonical zero-context transfer phrase

A user may give only this stable sentence:

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

The sentence deliberately contains no current task facts. The repository must supply them.

## Cold-start procedure

1. Inspect GitHub issue **#2 — `Longcycle live handoff / session bootstrap`** to resolve the currently active PR / development branch.
2. Switch all subsequent project reads to that active branch unless the user explicitly asks you to audit `main` itself.
3. On the active branch, follow `CONTINUE_HERE.md` and its bounded bootstrap. Recover and semantically calibrate long-term mission/methodology before executing current TODOs.
4. Read the typed continuation cursor to recover what just finished, what resumes now, why it is current, what ends it, and what follows.
5. Ensure the bounded `resume_read_set` includes and loads `.longcycle/capabilities/active-index.json`; before material capability/product/architecture work, discover the existing semantic owner and obey the `reuse / extend / replace / new` admission gate rather than relying on chat memory.
6. Do **not** preload old devlogs/issues/benchmarks. If the user/Agent has a fuzzy signal that a design was discussed before, or a change touches `core_locked` semantics / migration boundaries, use `docs/development/on-demand-history-recall.md`: capability owner → Repair Memory → exact origin refs → bounded Git/Issue history. Historical summaries are routing aids, never authority by themselves.
7. Recover the development data-plane rule before making acquisition decisions. For a readable **webpage**, prefer reading the page in the interactive research surface, preserving the faithful visible text plus source/provenance metadata in a bounded local database capture capsule, then hand that capsule off through Google Drive. Do **not** start GitHub Actions merely to archive webpage HTML. For a **PDF**, use the existing GitHub Actions acquisition lane when raw bytes are needed: fetch, hash, package and publish an immutable source asset to GitHub Release. Existing historical Release packs that contain HTML/web bytes remain valid legacy assets; they do not define the default path for new webpage captures.
8. Distinguish the **current Agent tool surface** from **Longcycle system capability**. An interactive Agent being awkward at Git writes or binary uploads is not itself a product capability gap. Use local batching plus the correct handoff transport rather than forcing per-page Git commits or unnecessary Actions workflows.
9. Refresh the active branch/PR live HEAD and CI; checkpoint CI is only a snapshot.
10. Do not ask the user to reconstruct context already persisted by the repository.

## mutation rule

When a task authorizes only one report or other bounded mutation, write it to the **resolved active development branch**, not to `main`, unless the task explicitly names `main` as the mutation target.

## What belongs on `main`

This pointer may remain on `main` even while active work happens elsewhere. It intentionally contains no current industry, campaign count, branch name, CI run, task list, or research state. Those belong to the active branch handoff.

A fresh Agent failing to follow this pointer, failing to recover stable capability ownership, failing to use bounded historical recall when a core semantic decision has a plausible prior history, sending new readable webpages through Actions/Release by default, confusing its current tool limitations with Longcycle's acquisition capabilities, or treating stale `main` implementation docs as current project intent has **not completed Longcycle bootstrap**.
