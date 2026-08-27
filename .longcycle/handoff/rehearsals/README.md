# Handoff rehearsals

This directory contains continuity drill reports. **Reports are immutable observations of the repository policy that existed at their tested head; they are not current project authority.**

Fresh Agents must resolve policy in this order:

1. `METHODOLOGY_CORE.md` / `STRATEGIC_COMPASS.md`;
2. `CONTINUE_HERE.md` + `.longcycle/handoff/current.json`;
3. `.longcycle/handoff/data-plane.json`;
4. current capability cards / active index;
5. rehearsal reports only as test evidence for the head they name.

## Supersession rule

A later rehearsal or harness revision may intentionally prove that an earlier routing/testing policy has been replaced. Never choose the older answer merely because its receipt is still present.

### Fresh-Agent drill v2 → v3

`fresh-agent-external-111-5f029d0.json` is preserved as a genuine v2 observation, but its self-declared `PASS` is **not an accepted continuity PASS**. The report records that DUMB-02 and DUMB-03 received only the literal word `cue`; the subject correctly refused to invent hidden questions, yet v2 had no cue-payload integrity gate and therefore allowed contentless stages to be marked complete.

V3 supersedes that harness behavior. Under `FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3` / `FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3`:

- a stage-2/3 cue must carry the actual question payload in a complete envelope;
- the subject must not see the payload before delivery, but **must read and answer it after valid delivery**;
- `cue`, `next`, `continue`, empty payloads and wrong-stage envelopes are `INVALID_CUE` and do not advance the stage;
- the v3 report stores the exact received payload and SHA-256;
- `scripts/validate_fresh_agent_drill_report.py` rejects PASS reports with non-canonical cue digests or invalid report-only provenance.

Do not edit the seq111 v2 report to make history look clean. Preserve it as the counterexample that motivated the v3 repair.

### PDF-routing history

- `sequence-64-webpage-pdf-routing-artificial-ignorance-v1.json` is a valid historical receipt for the then-current rule **PDF raw bytes → Actions → Release**. That routing is superseded and must not be used for new PDFs.
- `sequence-69-pdf-locator-deferred-materialization-artificial-ignorance-v1.json` tests the later `locator_verified → content_verified → materialized` policy in which raw PDF materialization is deferred and downloader Actions are not a prerequisite.
- Any newer rehearsal must be interpreted against its own tested head and current Core/handoff; it may supersede sequence 69 if the repository explicitly says so.

Do not edit old rehearsal results to make history look consistent. Preserve the old observation and route fresh Agents to the current policy.

## Drill discipline

- Same-Agent artificial-ignorance rehearsals may test whether bounded repository inputs are sufficient, but they must state that they do not prove independent fresh-Agent reasoning.
- External fresh-Agent reports must follow the current `docs/development/fresh-agent-continuity-drill.md` controller contract and `docs/development/fresh-agent-continuity-drill-subject.md` subject contract, and must not read earlier reports before completing their own scenarios.
- A report may advance the live branch by one report-only commit while recording the pre-report `subject_head` it actually tested.
- Do not copy report conclusions into Method Core, Capability Registry or Repair Memory unless a later maintainer independently verifies the architectural lesson.

## Scheduled cadence

`continuity_sequence` is the only scheduled Fresh-Agent drill counter. Every positive multiple of 10 is a genuine external/fresh-session drill boundary. The closing Agent must notice the proposed next handoff sequence itself and proactively raise or trigger the drill; this memory is not delegated to the user.

Manual or event-triggered drills may happen between boundaries, including immediately after a material continuity repair. They do not reset the fixed `10, 20, 30, ...` cadence. Same-Agent rehearsals also do not satisfy those scheduled boundaries. Report-only commits preserve the subject sequence and do not increment `continuity_sequence`.
