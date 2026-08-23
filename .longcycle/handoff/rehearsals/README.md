# Handoff rehearsals

This directory contains continuity drill reports. **Reports are immutable observations of the repository policy that existed at their tested head; they are not current project authority.**

Fresh Agents must resolve policy in this order:

1. `METHODOLOGY_CORE.md` / `STRATEGIC_COMPASS.md`;
2. `CONTINUE_HERE.md` + `.longcycle/handoff/current.json`;
3. `.longcycle/handoff/data-plane.json`;
4. current capability cards / active index;
5. rehearsal reports only as test evidence for the head they name.

## Supersession rule

A later rehearsal may intentionally prove that an earlier routing policy has been replaced. Never choose the older answer merely because its receipt is still present.

Known PDF-routing history:

- `sequence-64-webpage-pdf-routing-artificial-ignorance-v1.json` is a valid historical receipt for the then-current rule **PDF raw bytes → Actions → Release**. That routing is superseded and must not be used for new PDFs.
- `sequence-69-pdf-locator-deferred-materialization-artificial-ignorance-v1.json` tests the later `locator_verified → content_verified → materialized` policy in which raw PDF materialization is deferred and downloader Actions are not a prerequisite.
- Any newer rehearsal must be interpreted against its own tested head and current Core/handoff; it may supersede sequence 69 if the repository explicitly says so.

Do not edit old rehearsal results to make history look consistent. Preserve the old observation and route fresh Agents to the current policy.

## Drill discipline

- Same-Agent artificial-ignorance rehearsals may test whether bounded repository inputs are sufficient, but they must state that they do not prove independent fresh-Agent reasoning.
- External fresh-Agent reports must follow `docs/development/fresh-agent-continuity-drill.md` and must not read earlier reports before completing their own scenarios.
- A report may advance the live branch by one report-only commit while recording the pre-report `subject_head` it actually tested.
- Do not copy report conclusions into Method Core, Capability Registry or Repair Memory unless a later maintainer independently verifies the architectural lesson.
