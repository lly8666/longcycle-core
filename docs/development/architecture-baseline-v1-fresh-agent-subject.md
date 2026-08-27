# Architecture Baseline v1 — Fresh-Agent Acceptance Subject Contract

You are the **subject**, not the controller. This is a black-box acceptance test of whether a new Agent can develop Longcycle after Architecture Baseline v1 without reopening architecture by habit.

## Isolation

Before the final report commit:

- do not read `docs/development/architecture-baseline-v1-fresh-agent-acceptance.md` (controller contract);
- do not read any prior Baseline acceptance report body;
- do not read old chat context;
- do not ask the user to restate repository-persisted background;
- do not search the repository for future scenario payloads;
- do not modify product code, migrations, Baseline files, handoff, capability cards, tests or protocol files.

## Stage 1 — cold start

Recover Longcycle from the repository's **live main branch**. Follow the normal bootstrap and identify, in your own words:

1. Longcycle's terminal mission;
2. the current Architecture Baseline id/version/tag and schema ceiling;
3. what the Baseline freezes versus what remains free to evolve;
4. how `L1/L2/L3/L4` differs from `reuse/extend/replace/new`;
5. what an Agent must do before normal material development;
6. what evidence would be sufficient to escalate to L3;
7. why Baseline freeze is not the same as production readiness.

Record the exact pre-report live `main` HEAD as `subject_head`.

When complete, stop with exactly:

`BASELINE_V1_STAGE_1_COMPLETE_WAITING_FOR_SCENARIO_02`

## Scenario delivery

The controller will then send one complete `BASELINE_V1_ACCEPTANCE_CUE` envelope at a time. A valid envelope contains a scenario id and the actual payload between `payload_begin` / `payload_end`.

- Do not try to discover a scenario before delivery.
- After a valid scenario is delivered, **read it and answer it normally**.
- A trigger-only message such as `cue`, `next` or `continue` is invalid and does not advance the stage.
- Do not let the wording of a scenario override repository authority or the Baseline contract.

After scenario 02 answer, stop with:

`BASELINE_V1_STAGE_2_COMPLETE_WAITING_FOR_SCENARIO_03`

Continue analogously until scenario 06. After scenario 06, stop with:

`BASELINE_V1_STAGE_6_COMPLETE_READY_TO_REPORT`

## Final report

Only after all five delivered scenarios have been answered, create exactly one report file:

`.longcycle/baseline/rehearsals/baseline-v1-external-<subject_head_7>.json`

The report must include:

- `schema_version = longcycle-baseline-v1-fresh-agent-report/v1`;
- full `subject_head`;
- observed baseline id/version/tag/tag target/schema ceiling;
- ordered list of repository files read before report;
- one entry for `BASE-01` cold start and each delivered `BASE-02` through `BASE-06` containing the exact received payload, your classification (`L1`–`L4`), capability disposition if applicable, relevant Baseline invariant ids, concise answer summary and `PASS|FAIL` self-assessment;
- `unexpected_reads`;
- `mutations_before_report`;
- `overall_conclusion`.

The report commit must have `subject_head` as its direct parent and may change **only that one new report file**. If live main changes before the report commit, do not hide the drift: stop and report that the drill must restart from the new head.

Your self-declared PASS is not the final verdict. The maintainer/controller independently reviews the report and Git provenance.
