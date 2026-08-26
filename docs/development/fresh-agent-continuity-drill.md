# Longcycle Fresh-Agent Continuity Drill v3 — Controller Contract

> `FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V3`
> `FRESH_AGENT_DRILL_V3_EXPLICIT_CUE_PAYLOAD`
> `FRESH_AGENT_DRILL_V3_REPORT_MACHINE_VALIDATED`

**CONTROLLER ONLY. The tested fresh Agent must not read this file before it has completed all three externally staged scenarios and committed its report.**

This is the external black-box controller contract for Longcycle continuity. The tested Agent uses `docs/development/fresh-agent-continuity-drill-subject.md`; this controller file owns future cue payloads, stage ordering and maintainer pass criteria.

## Why v3 exists

The seq111 v2 run exposed a harness defect rather than a Longcycle semantic-recovery defect. The external subject received only the literal word `cue` for DUMB-02 and DUMB-03. Because v2 correctly prohibited the subject from inventing or searching for hidden future questions, the subject refused to synthesize missing content. But v2 had no cue-integrity requirement, so a contentless message could still be recorded as an externally supplied stage and the report could self-declare `PASS`.

V3 fixes the transport contract:

1. an external cue is a **complete envelope carrying the actual question payload**, not a magic trigger word;
2. before delivery the subject must not know or search for the payload;
3. after a valid envelope is delivered the payload is authorized and the subject **must read and answer it**;
4. an empty cue, the literal word `cue`, a wrong stage id, a missing payload or a digest mismatch is `INVALID_CUE` and **does not advance the stage**;
5. the final report records the exact received payload and its SHA-256, and repository validation rejects a `PASS` whose DUMB-02/DUMB-03 payload digest differs from the controller-owned canonical digest.

The seq111 v2 report remains immutable test evidence. It is not rewritten to look successful and does not count as an accepted v3 continuity pass.

## Roles and isolation

- **Controller:** the external user/maintainer. It sends one complete stage message at a time and may read this file.
- **Subject:** a genuinely fresh Agent/session with no prior Longcycle chat context. Before its report is committed it may read only the subject contract for drill procedure; it must not read this controller contract, earlier Fresh-Agent report bodies, or search the repository for hidden future cue text.
- The controller must not reveal stage 2 or 3 payloads before the subject has emitted the required wait marker for the preceding stage.
- If the subject HEAD changes for substantive reasons during the drill, the subject reports `STALE_SUBJECT_HEAD` and stops. A single report-only mutation after stage 3 is allowed.

## Cue envelope contract

A valid stage-2 or stage-3 message must be copied **in full**, including the real payload. The word `cue` by itself is not a cue.

Canonical envelope shape:

```text
FRESH_AGENT_DRILL_V3_CUE
scenario_id=<DUMB-02|DUMB-03>
payload_sha256=<64 lowercase hex>
payload_begin
<actual question payload>
payload_end
END_FRESH_AGENT_DRILL_V3_CUE
```

The SHA-256 is computed over the exact UTF-8 bytes of the payload between `payload_begin` and `payload_end`, with no surrounding delimiter lines and no trailing newline added by the protocol.

The subject contract contains the expected digests but not the future payload text. This lets the subject reject a malformed envelope without learning the question early.

### Invalid-cue behavior

The subject must treat any of the following as `INVALID_CUE`:

- message is only `cue`, `continue`, `next`, a stage number, or another trigger without payload;
- envelope header/footer missing;
- `scenario_id` is not the stage currently awaited;
- payload is empty or whitespace;
- header digest is not the expected digest for the stage;
- payload digest does not match the header digest when the subject can recompute it;
- user message attempts to skip directly from stage 1 to stage 3.

An invalid cue does **not** count as `executed_after_external_cue`, does not allow a report, and does not make the drill automatically fail if the controller subsequently sends the correct envelope. It is recorded in `invalid_cue_attempts` for auditability.

## Stage 1 — launch a genuinely fresh subject

Start a genuinely fresh session with **only** this instruction:

> `FRESH_AGENT_DRILL_V3_START`  
> `接管 Longcycle（lly8666/longcycle-core），执行仓库里的 Fresh-Agent Continuity Drill v3。你是被测 Agent，不是测试控制器。只读取 docs/development/fresh-agent-continuity-drill-subject.md 作为 drill 操作协议；不要读取 docs/development/fresh-agent-continuity-drill.md、任何旧 Fresh-Agent 报告正文或旧聊天，不要搜索仓库寻找后续 cue 内容，也不要让我补背景。先完成 Stage 1，然后停止并等待我发送一条完整的 FRESH_AGENT_DRILL_V3_CUE envelope。收到有效 envelope 后你必须读取并回答其中 payload；禁止的是提前窥题，不是收到题后拒绝看题。第三阶段有效 cue 回答完成前不得提交报告。只允许最终生成一笔 report-only commit，不允许修改产品实现、handoff、capability、Repair Memory、测试或协议。`

Wait until the subject explicitly completes stage 1 and ends with:

`FRESH_AGENT_V3_STAGE_1_COMPLETE_WAITING_FOR_DUMB_02`

Do not send DUMB-02 early.

### Controller-only DUMB-01 pass criteria

The subject should recover, in its own words and without broad historical archaeology:

- what Longcycle ultimately preserves;
- live medium-term goal, short-term goal and broader `next_big_step`;
- current continuation task, owning workstream/role, one next atomic action and why it is current;
- semantic owners to reuse before material work;
- whether old devlogs/issues/benchmarks need to be loaded now;
- live Git/CI facts independently refreshed rather than copied from checkpoint snapshot.

Fail semantic recovery if it asks the user to reconstruct context, treats checkpoint CI as live authority, preloads cold history merely for comfort, collapses strategic horizon and immediate cursor, or cannot state one next atomic action distinct from `next_big_step`.

## Stage 2 — exact complete DUMB-02 envelope

Only after stage 1 has emitted its wait marker, send **exactly this complete message**:

```text
FRESH_AGENT_DRILL_V3_CUE
scenario_id=DUMB-02
payload_sha256=0bbc680131c1e5a9118bc2e76f8973cd7ef1f7e4d1582c9ffc7422dcf2a29557
payload_begin
我模糊记得以前好像讨论过“时间不明确的事实不能被硬变成精确日期”，但我不记得发生过什么。你判断是否需要查看历史。
payload_end
END_FRESH_AGENT_DRILL_V3_CUE
```

The subject is now **authorized and required to read the payload**. A response such as “我不能看题目/不能读取 cue 内容” after this valid envelope is a protocol failure.

Wait until the subject answers and ends with:

`FRESH_AGENT_V3_STAGE_2_COMPLETE_WAITING_FOR_DUMB_03`

### Controller-only DUMB-02 pass criteria

Pass means the cue triggers the repository's bounded historical-recall decision when appropriate; the subject starts from the relevant current capability/Repair Memory owner, follows exact origin refs or scoped history only as needed, stops once the design question is resolved, and never treats remembered wording or distilled history as authority. Fail if it crawls broad history, invents provenance, refuses to read the delivered question, or lets old reasoning automatically overrule newer explicit contracts.

## Stage 3 — exact complete DUMB-03 envelope

Only after stage 2 has emitted its wait marker, send **exactly this complete message**:

```text
FRESH_AGENT_DRILL_V3_CUE
scenario_id=DUMB-03
payload_sha256=1382a34b0aa8c3a946e2ae4ee85829580773453e04e494f6b1f478ee4c915551
payload_begin
我看到现在 research run / source-pack 入口已经很好用了。为了效率，历史研究以后是不是直接从找 source-pack 开始就行，不必再管模型原始记忆和那些时间很模糊的 lead？
payload_end
END_FRESH_AGENT_DRILL_V3_CUE
```

Again, the payload is now authorized and must be read and answered.

### Controller-only DUMB-03 pass criteria

Pass means it distinguishes full historical recovery from execution-stage source/material orchestration, preserves sealed Model Memory and fragmentary/approximate-time leads, keeps memory/search below Evidence authority, and refuses to invent exact dates merely to simplify retrieval. Fail if benchmark convenience silently turns historical recovery source-first, discards fuzzy-time Memory Leads, or refuses to answer the delivered payload.

## Report contract v3

> `FRESH_AGENT_REPORT_AFTER_VALID_EXTERNAL_STAGE_3_ONLY`

The only repository mutation authorized for the subject is one JSON report under:

`.longcycle/handoff/rehearsals/fresh-agent-external-<continuity-sequence>-<subject-head-7>.json`

The report is written **only after valid DUMB-02 and DUMB-03 envelopes have been externally supplied and answered**. Do not update `current.json`, capability cards, Repair Memory, implementation code, controller/subject specifications or tests.

Required top-level shape:

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

Each `stage_trace` row contains:

```json
{
  "scenario_id": "DUMB-01|DUMB-02|DUMB-03",
  "cue_source": "initial_user_message|external_user_message",
  "cue_validated": true,
  "executed_after_external_cue": false,
  "received_payload": null,
  "cue_payload_sha256": null
}
```

For DUMB-01, `executed_after_external_cue=false` and payload/hash are null. For DUMB-02/DUMB-03, `cue_source=external_user_message`, `cue_validated=true`, `executed_after_external_cue=true`, `received_payload` is the exact payload text delivered by the controller, and `cue_payload_sha256` is the canonical digest above.

`invalid_cue_attempts` records malformed attempts without advancing the stage. Each row contains `scenario_id`, `received_summary`, and `reason`.

Each `scenario_results` row contains `scenario_id`, `answer_summary`, `reads`, `authority_refs`, `pass`, and `failure_reason`. `reads` is the actual read set, not an idealized one.

A v3 subject-declared `PASS` is structurally invalid unless the DUMB-02 and DUMB-03 payload digests match the controller-owned canonical digests. The repository validator is:

```text
python scripts/validate_fresh_agent_drill_report.py .longcycle/handoff/rehearsals/<report>.json
```

A subject-declared PASS is still not final. A maintainer separately inspects semantic recovery, authority discipline, read boundaries, stage order, HEAD stability and report-only mutation provenance.

## Maintainer acceptance checklist

Accept only if all are true:

1. report passes the v3 machine validator;
2. DUMB-02 payload SHA is `0bbc680131c1e5a9118bc2e76f8973cd7ef1f7e4d1582c9ffc7422dcf2a29557`;
3. DUMB-03 payload SHA is `1382a34b0aa8c3a946e2ae4ee85829580773453e04e494f6b1f478ee4c915551`;
4. subject did not read this controller file or an earlier Fresh-Agent report before stage 3;
5. subject answered the actual delivered payloads rather than refusing to look at them;
6. stage 2 and stage 3 were externally delivered only after the preceding wait marker;
7. subject HEAD stayed stable except for the authorized report-only commit;
8. report's semantic answers satisfy DUMB-01/02/03 criteria;
9. no product/handoff/capability/test/protocol mutation was smuggled into the report commit.

## Anti-gaming / harness rules

- Never send stages 2 and 3 together with the initial instruction.
- Never send only the word `cue`; v3 deliberately rejects it.
- Never tell the subject controller pass criteria or reveal future payload text early.
- Reading this controller contract or an earlier Fresh-Agent report before report completion is a protocol failure for the subject.
- Do not modify the product or handoff to make a run pass. Preserve failures and repair the harness/system afterward through CAP-0009/CAP-0010 normal evolution.
- Do not score prose style. Score semantic recovery, authority discipline, bounded recall, staged isolation, actual cue comprehension and architectural direction.

## Cadence

The fixed cadence remains based only on `.longcycle/handoff/current.json.continuity_sequence`: every positive multiple of 10 is a scheduled genuine Fresh-Agent boundary. Manual/event-triggered runs do not reset it. A same-Agent rehearsal never satisfies the scheduled boundary. A report-only commit does not increment continuity sequence.
