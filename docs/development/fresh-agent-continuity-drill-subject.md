# Longcycle Fresh-Agent Continuity Drill v2 — Subject Contract

> `FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V2`
> `FRESH_AGENT_SUBJECT_NO_CONTROLLER_READ`
> `FRESH_AGENT_SUBJECT_NO_REPORT_BEFORE_STAGE_3`

You are the **tested fresh Agent**, not the test controller.

This file is the only drill-procedure document you may read before the final report. Do **not** read `docs/development/fresh-agent-continuity-drill.md`, any earlier Fresh-Agent report, or old chat history before your own report is committed. Do not ask the user to reconstruct persisted project background.

The test is staged by external user messages. You must not invent, simulate, search for, or self-inject future test cues.

## General rules

- Resolve the live branch through GitHub issue #2 and `FRESH_AGENT_BOOTSTRAP.md`.
- Record the live subject HEAD before answering stage 1.
- Use the normal bounded bootstrap. Do not preload old devlogs, unrelated issues, old benchmark receipts or earlier Fresh-Agent reports.
- Check live PR/HEAD/CI independently. Checkpoint CI is only a snapshot.
- Only the final report mutation is authorized. Do not modify implementation, `current.json`, capability cards, Repair Memory, protocol documents or tests.
- If the subject HEAD changes for substantive reasons before the final report, report `STALE_SUBJECT_HEAD` and stop. A report-only commit is not substantive drift.

## Stage 1 — cold start

> `FRESH_AGENT_SUBJECT_STAGE_1_WAIT_REQUIRED`

Using only the repository's bounded fresh-agent route, recover in your own words:

- what Longcycle ultimately tries to preserve;
- the live medium-term goal, short-term goal and broader `next_big_step`;
- the live continuation task, its owning workstream/role, one next atomic action and why it is current;
- the semantic owner(s) that should be reused before material work;
- whether old devlogs/issues/benchmarks need to be loaded now;
- which live Git/CI facts you independently refreshed rather than copied from the checkpoint snapshot.

After answering stage 1, **stop**. Do not create any report. Do not guess what comes next. End your response with exactly:

`FRESH_AGENT_STAGE_1_COMPLETE_WAITING_FOR_EXTERNAL_CUE`

Then wait for the user's next message.

## Stage 2 — external cue only

> `FRESH_AGENT_SUBJECT_STAGE_2_WAIT_REQUIRED`

The next user message after stage 1 is the DUMB-02 cue. You must not know or reconstruct it before it arrives.

When it arrives:

1. Answer the cue from current repository contracts.
2. Decide whether bounded historical recall is necessary using the repository's normal routing rules.
3. Do not broaden historical reads after the design question is resolved.
4. Do not create the final report yet.

End your response with exactly:

`FRESH_AGENT_STAGE_2_COMPLETE_WAITING_FOR_EXTERNAL_CUE`

Then wait for the user's next message.

## Stage 3 — external cue only

> `FRESH_AGENT_SUBJECT_STAGE_3_REPORT_ALLOWED_AFTER_EXTERNAL_CUE`

The next user message after stage 2 is the DUMB-03 cue. Do not search the repository for likely cue text or expected answers before it arrives.

When it arrives:

1. Answer from current repository contracts rather than following the cue's framing.
2. Recheck the live subject HEAD after answering.
3. If substantive drift occurred, finalize the report as `STALE_SUBJECT_HEAD` and stop.
4. Otherwise, create the one authorized final report.

## Final report contract

Write exactly one JSON report under:

`.longcycle/handoff/rehearsals/fresh-agent-external-<continuity-sequence>-<subject-head-7>.json`

Required top-level fields:

```json
{
  "schema_version": "longcycle-fresh-agent-continuity-report/v2",
  "mode": "external_fresh_agent_black_box",
  "controller_protocol": "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V2",
  "subject_protocol": "FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V2",
  "chat_history_allowed": false,
  "subject_head": "<40-hex>",
  "continuity_sequence": 0,
  "stage_trace": [],
  "scenario_results": [],
  "unexpected_reads": [],
  "overall_conclusion": "PASS|FAIL|STALE_SUBJECT_HEAD",
  "reporter_notes": "<short free text>"
}
```

`stage_trace` must list DUMB-01, DUMB-02 and DUMB-03 in order. Each row contains:

```json
{
  "scenario_id": "DUMB-01|DUMB-02|DUMB-03",
  "cue_source": "initial_user_message|external_user_message",
  "executed_after_external_cue": true
}
```

For DUMB-02 and DUMB-03, `executed_after_external_cue` must truthfully indicate whether you waited for the user's external message. If you self-injected either later scenario, the overall conclusion must be `FAIL`.

Each `scenario_results` item must contain `scenario_id`, `answer_summary`, `reads`, `authority_refs`, `pass`, and `failure_reason`. `reads` must list actual resources opened for that scenario.

Do not read the controller contract or an earlier Fresh-Agent report merely to help score yourself. Your PASS/FAIL is provisional; a maintainer performs the final assessment afterward.
