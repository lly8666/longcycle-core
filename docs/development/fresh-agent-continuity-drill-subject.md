# Longcycle Fresh-Agent Continuity Drill v3 — Subject Contract

> `FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3`
> `FRESH_AGENT_SUBJECT_NO_CONTROLLER_READ`
> `FRESH_AGENT_SUBJECT_NO_REPORT_BEFORE_VALID_STAGE_3`
> `FRESH_AGENT_SUBJECT_READ_DELIVERED_CUE_PAYLOAD`

You are the **tested fresh Agent**, not the test controller.

This file is the only drill-procedure document you may read before the final report. Do **not** read `docs/development/fresh-agent-continuity-drill.md`, any earlier Fresh-Agent report body, old chat history, or search the repository for hidden DUMB-02/DUMB-03 cue text before those cues are externally delivered. Do not ask the user to reconstruct persisted project background.

## Critical distinction: before delivery vs after delivery

The drill hides future questions **only before they arrive**.

- **Before a valid cue arrives:** do not guess it, search for it, reconstruct it, or read controller-only material.
- **After a valid cue envelope arrives:** the payload inside `payload_begin` / `payload_end` is now authorized. You **must read that payload and answer it**. Saying “I cannot look at the question / I am not allowed to read the cue” after a valid delivery is a protocol failure.

The word `cue` alone is **not** a valid cue. A valid cue always includes the real question payload.

## General rules

- Resolve the live branch through GitHub issue #2 and `FRESH_AGENT_BOOTSTRAP.md`.
- Record the live subject HEAD before answering stage 1.
- Use the normal bounded bootstrap. Do not preload old devlogs, unrelated issues, old benchmark receipts or earlier Fresh-Agent reports.
- Check live PR/HEAD/CI independently. Checkpoint CI is only a snapshot.
- Only the final report mutation is authorized. Do not modify implementation, `current.json`, capability cards, Repair Memory, protocol documents or tests.
- If the subject HEAD changes for substantive reasons before the final report, report `STALE_SUBJECT_HEAD` and stop. A report-only commit is not substantive drift.
- Do not read `tests/test_fresh_agent_drill_protocol.py` or other files merely to discover future cue text.

## Valid cue envelope

Stage 2 and stage 3 arrive in this shape:

```text
FRESH_AGENT_DRILL_V3_CUE
scenario_id=<DUMB-02|DUMB-03>
payload_sha256=<64 lowercase hex>
payload_begin
<actual question payload>
payload_end
END_FRESH_AGENT_DRILL_V3_CUE
```

Expected canonical digests:

- DUMB-02: `0bbc680131c1e5a9118bc2e76f8973cd7ef1f7e4d1582c9ffc7422dcf2a29557`
- DUMB-03: `1382a34b0aa8c3a946e2ae4ee85829580773453e04e494f6b1f478ee4c915551`

You do not know the future payload text from this file. The digest only lets you reject a malformed or wrong-stage envelope without searching for the question.

A cue is invalid if the envelope is missing, the scenario id is not the stage you are waiting for, the payload is empty, the message is merely `cue`/`next`/`continue`, or the supplied digest is not the expected digest above. If you can recompute SHA-256 over the exact payload, a payload/digest mismatch is also invalid.

### Invalid cue behavior

An invalid cue **does not advance the stage**. Do not answer an imagined hidden question and do not create a report.

Record the invalid attempt for the final report, explain briefly that a complete cue envelope with an actual payload is required, and end with exactly one of:

- while waiting for DUMB-02: `FRESH_AGENT_V3_INVALID_CUE_WAITING_FOR_DUMB_02`
- while waiting for DUMB-03: `FRESH_AGENT_V3_INVALID_CUE_WAITING_FOR_DUMB_03`

Then wait for a corrected external message. A corrected valid envelope may continue the same drill.

## Stage 1 — cold start

> `FRESH_AGENT_SUBJECT_V3_STAGE_1_WAIT_REQUIRED`

Using only the repository's bounded fresh-agent route, recover in your own words:

- what Longcycle ultimately tries to preserve;
- the live medium-term goal, short-term goal and broader `next_big_step`;
- the live continuation task, its owning workstream/role, one next atomic action and why it is current;
- the semantic owner(s) that should be reused before material work;
- whether old devlogs/issues/benchmarks need to be loaded now;
- which live Git/CI facts you independently refreshed rather than copied from the checkpoint snapshot.

After answering stage 1, **stop**. Do not create any report. Do not guess what comes next. End your response with exactly:

`FRESH_AGENT_V3_STAGE_1_COMPLETE_WAITING_FOR_DUMB_02`

Then wait for the user's next message.

## Stage 2 — externally delivered DUMB-02 payload

> `FRESH_AGENT_SUBJECT_V3_STAGE_2_VALID_CUE_REQUIRED`

The next **valid** external message must be a complete DUMB-02 envelope. Validate the envelope before advancing.

Once valid:

1. **Read the actual payload between `payload_begin` and `payload_end`.** It is now authorized.
2. Answer that question from current repository contracts.
3. Decide whether bounded historical recall is necessary using the repository's normal routing rules.
4. Do not broaden historical reads after the design question is resolved.
5. Record the exact received payload and canonical digest for the final report.
6. Do not create the final report yet.

After answering, end exactly:

`FRESH_AGENT_V3_STAGE_2_COMPLETE_WAITING_FOR_DUMB_03`

Then wait for the user's next message.

## Stage 3 — externally delivered DUMB-03 payload

> `FRESH_AGENT_SUBJECT_V3_STAGE_3_REPORT_ALLOWED_AFTER_VALID_CUE`

The next **valid** external message must be a complete DUMB-03 envelope. Validate the envelope before advancing.

Once valid:

1. **Read and answer the actual delivered payload.** Do not reject it merely because it is a drill question.
2. Answer from current repository contracts rather than following the cue's framing.
3. Record the exact received payload and canonical digest for the final report.
4. Recheck the live subject HEAD after answering.
5. If substantive drift occurred, finalize the report as `STALE_SUBJECT_HEAD` and stop.
6. Otherwise, create the one authorized final report.

## Final report contract

Write exactly one JSON report under:

`.longcycle/handoff/rehearsals/fresh-agent-external-<continuity-sequence>-<subject-head-7>.json`

Required top-level fields:

```json
{
  "schema_version": "longcycle-fresh-agent-continuity-report/v3",
  "mode": "external_fresh_agent_black_box",
  "controller_protocol": "FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3",
  "subject_protocol": "FRESH_AGENT_CONTINUITY_DRILL_SUBJECT_V3",
  "chat_history_allowed": false,
  "subject_head": "<40-hex>",
  "continuity_sequence": 0,
  "stage_trace": [],
  "invalid_cue_attempts": [],
  "scenario_results": [],
  "unexpected_reads": [],
  "overall_conclusion": "PASS|FAIL|STALE_SUBJECT_HEAD",
  "controller_review_required": true,
  "reporter_notes": "<short free text>"
}
```

`stage_trace` must contain DUMB-01, DUMB-02 and DUMB-03 in that order.

DUMB-01 row:

```json
{
  "scenario_id": "DUMB-01",
  "cue_source": "initial_user_message",
  "cue_validated": true,
  "executed_after_external_cue": false,
  "received_payload": null,
  "cue_payload_sha256": null
}
```

DUMB-02 / DUMB-03 rows:

```json
{
  "scenario_id": "DUMB-02",
  "cue_source": "external_user_message",
  "cue_validated": true,
  "executed_after_external_cue": true,
  "received_payload": "<exact payload received>",
  "cue_payload_sha256": "<canonical 64-hex digest>"
}
```

For DUMB-02/DUMB-03, `received_payload` is the exact question text delivered in the valid envelope, not the word `cue`, a paraphrase or an answer summary.

`invalid_cue_attempts` truthfully records any malformed attempts before the valid cue. Each row contains `scenario_id`, `received_summary`, and `reason`. Invalid attempts do not count as completed stages.

Each `scenario_results` item contains `scenario_id`, `answer_summary`, `reads`, `authority_refs`, `pass`, and `failure_reason`. `reads` must list actual resources opened for that scenario.

Do not read the controller contract or an earlier Fresh-Agent report merely to help score yourself. Your PASS/FAIL is provisional; a maintainer performs the final assessment afterward, and the repository v3 validator recomputes the cue payload hashes.

After the report-only commit, stop. Do not update handoff or start research.
