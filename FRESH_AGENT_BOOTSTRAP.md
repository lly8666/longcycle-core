# Longcycle — Fresh Agent Bootstrap

This file is a **stable rendezvous pointer**, not project state.

If you are a fresh Agent asked to continue, audit, or understand Longcycle, **do not assume the default `main` branch is the active development state** and do not infer the current roadmap from `main` alone.

## Cold-start procedure

1. Inspect GitHub issue **#2 — `Longcycle live handoff / session bootstrap`** to resolve the currently active PR / development branch.
2. Switch all subsequent project reads to that active branch unless the user explicitly asks you to audit `main` itself.
3. On the active branch, follow `CONTINUE_HERE.md` and its bounded bootstrap. Recover long-term mission and methodology before executing current TODOs.
4. Refresh the active branch/PR live HEAD and CI; checkpoint CI is only a snapshot.
5. Do not ask the user to reconstruct context already persisted by the repository.

## Mutation rule

When a task authorizes only one report or other bounded mutation, write it to the **resolved active development branch**, not to `main`, unless the task explicitly names `main` as the mutation target.

## What belongs on `main`

This pointer may remain on `main` even while active work happens elsewhere. It intentionally contains no current industry, campaign count, branch name, CI run, task list, or research state. Those belong to the active branch handoff.

A fresh Agent failing to follow this pointer and treating stale `main` implementation docs as current project intent has **not completed Longcycle bootstrap**.
