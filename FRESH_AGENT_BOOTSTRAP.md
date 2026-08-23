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
7. Recover the development source/data-plane rule before making acquisition decisions:
   - **Readable webpage:** interactive read → faithful claim-scoped visible text + provenance → bounded local DB capture capsule → Google Drive. Do **not** start GitHub Actions merely to archive webpage HTML.
   - **PDF:** default to locator/content verification, **not download automation**. Record publisher/source identity, title/date when supported, original PDF URL, file name when known, verification time/mode and materialization status. If the current Agent can actually read the relevant PDF content, claim-scoped Evidence may proceed from the verified readable content even while raw PDF bytes remain `pending_materialization`. If the Agent can verify only that a PDF/link exists but cannot read the claim-relevant content, record a `verified_source_locator` but do not use it to prove the claim.
   - PDFs hosted by mainstream official/regulatory/issuer/institutional publishers are accepted as legitimate source documents once document identity and locator are verified; do not burn research time proving that GitHub Actions can download the bytes. Source authority remains claim-scoped and comes from the publisher/document role, not from the transport or the `.pdf` suffix.
   - Raw PDF materialization is deferred enrichment for a later normal-network Agent: download the recorded locator, verify identity/content, add byte size/SHA/storage locator, and fail closed only if the later materialization contradicts the earlier verified content/identity.
   - Existing immutable GitHub Release PDF/source packs remain valid historical/materialized assets and may be reused; they are no longer the default template for new PDF acquisition.
8. Distinguish the **current Agent tool surface** from **Longcycle system capability**. An interactive Agent being awkward at Git writes, binary uploads or a particular host is not itself a product capability gap. Preserve readable information and verified locators instead of manufacturing Actions workflows around transport friction.
9. Refresh the active branch/PR live HEAD and CI; checkpoint CI is only a snapshot.
10. Do not ask the user to reconstruct context already persisted by the repository.

## mutation rule

When a task authorizes only one report or other bounded mutation, write it to the **resolved active development branch**, not to `main`, unless the task explicitly names `main` as the mutation target.

## What belongs on `main`

This pointer may remain on `main` even while active work happens elsewhere. It intentionally contains no current industry, campaign count, branch name, CI run, task list, or research state. Those belong to the active branch handoff.

A fresh Agent failing to follow this pointer, failing to recover stable capability ownership, failing to use bounded historical recall when a core semantic decision has a plausible prior history, sending new readable webpages through Actions/Release by default, treating raw PDF download as a prerequisite after claim-relevant PDF content is already readable/verified, confusing its current tool limitations with Longcycle's source capabilities, or treating stale `main` implementation docs as current project intent has **not completed Longcycle bootstrap**.
