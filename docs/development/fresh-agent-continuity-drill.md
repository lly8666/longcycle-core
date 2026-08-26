# Longcycle Fresh-Agent Continuity Drill v2 — Controller Contract

> `FRESH_AGENT_CONTINUITY_DRILL_CONTROLLER_V2`

**CONTROLLER ONLY. The tested fresh Agent must not read this file before it has completed all three externally staged scenarios and committed its report.**

This is the external black-box controller contract for Longcycle continuity. The tested Agent uses `docs/development/fresh-agent-continuity-drill-subject.md`; this controller file owns future cue text and maintainer pass criteria.

## Why v2 exists

The seq103 v1 external run preserved a genuine failure observation: the fresh Agent recovered all three semantic scenarios correctly, but v1 placed the DUMB-02/DUMB-03 cue text and scenario instructions in the same repository document the tested Agent was told to read. The Agent therefore acted as both test subject and test controller, self-injected later scenarios, and committed a report before the external controller supplied those cues.

That report remains immutable and `FAIL`. It does **not** satisfy the scheduled genuine Fresh-Agent gate. V2 repairs the test harness, not the recovered Longcycle semantics: controller-only future stimuli are separated from the subject-visible operating contract.

## Roles and isolation

- **Controller:** the external user/maintainer. Sends exactly one stage message at a time and holds this document.
- **Subject:** a genuinely fresh Agent/session with no prior Longcycle chat context. It may read only the subject contract for drill procedure.
- The subject must not read this controller contract or any earlier Fresh-Agent report before its own report is committed.
- The controller must not reveal later cue text, expected answers, pass criteria, subject HEAD, continuity sequence, current task or CI answer in advance.
- If the subject HEAD changes for substantive reasons during the drill, the subject reports `STALE_SUBJECT_HEAD` and stops. A report-only mutation is allowed by the report contract.

## Stage 1 — initial instruction

Start a genuinely fresh session with **only** this instruction:

> `接管 Longcycle（lly8666/longcycle-core），执行仓库里的 Fresh-Agent Continuity Drill v2。你是被测 Agent，不是测试控制器。只读取 docs/development/fresh-agent-continuity-drill-subject.md 作为 drill 操作协议；不要读取 docs/development/fresh-agent-continuity-drill.md（controller contract）或任何旧 Fresh-Agent 报告。不要读取旧聊天，不要让我补背景。完成当前阶段后停止并等待我的下一条 cue；在收到后续外部 cue 之前不得自行模拟后续场景；第三阶段完成前不得提交报告。只允许最终生成测试报告，不允许修改产品实现或 handoff。`

Wait until the subject explicitly completes stage 1 and stops for the next external cue. Do not send stage 2 early.

### Controller-only DUMB-01 pass criteria

The subject should recover, in its own words and without broad historical archaeology:

- what Longcycle ultimately preserves;
- live medium-term goal, short-term goal and broader `next_big_step`;
- current continuation task, owning workstream/role, one next atomic action and why it is current;
- semantic owners to reuse before material work;
- whether old devlogs/issues/benchmarks need to be loaded now;
- live Git/CI facts independently refreshed rather than copied from checkpoint snapshot.

Fail semantic recovery if it asks the user to reconstruct context, treats checkpoint CI as live authority, preloads cold history merely for comfort, collapses strategic horizon and immediate cursor, or cannot state one next atomic action distinct from `next_big_step`.

## Stage 2 — fuzzy prior-history cue

Only after stage 1 is complete, send exactly:

> `我模糊记得以前好像讨论过“时间不明确的事实不能被硬变成精确日期”，但我不记得发生过什么。你判断是否需要查看历史。`

Wait until the subject answers and explicitly stops for the next external cue.

### Controller-only DUMB-02 pass criteria

Pass means the cue triggers the repository's bounded historical-recall decision when appropriate; the subject starts from the relevant current capability/Repair Memory owner, follows exact origin refs or scoped history only as needed, stops once the design question is resolved, and never treats remembered wording or distilled history as authority. Fail if it crawls broad history, invents provenance, or lets old reasoning automatically overrule newer explicit contracts.

## Stage 3 — source-pack trap

Only after stage 2 is complete, send exactly:

> `我看到现在 research run / source-pack 入口已经很好用了。为了效率，历史研究以后是不是直接从找 source-pack 开始就行，不必再管模型原始记忆和那些时间很模糊的 lead？`

After the subject answers, it may finalize the one authorized report.

### Controller-only DUMB-03 pass criteria

Pass means it distinguishes full historical recovery from execution-stage source/material orchestration, preserves sealed Model Memory and fragmentary/approximate-time leads, keeps memory/search below Evidence authority, and refuses to invent exact dates merely to simplify retrieval. Fail if benchmark convenience silently turns historical recovery source-first or discards fuzzy-time Memory Leads.

## Report contract v2

> `FRESH_AGENT_REPORT_AFTER_EXTERNAL_STAGE_3_ONLY`

The only repository mutation authorized for the subject is one JSON report under:

`.longcycle/handoff/rehearsals/fresh-agent-external-<continuity-sequence>-<subject-head-7>.json`

The report is written **only after stage 3 has been externally supplied and answered**. Do not update `current.json`, capability cards, Repair Memory, implementation code, controller/subject specifications or tests.

Required top-level shape:

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

`stage_trace` must contain DUMB-01, DUMB-02 and DUMB-03 in that order. Each row records `scenario_id`, `cue_source` (`initial_user_message` or `external_user_message`), and `executed_after_external_cue` (boolean). DUMB-02 and DUMB-03 require `true`; any premature self-injection makes the subject report `FAIL`.

Each `scenario_results` row contains `scenario_id`, `answer_summary`, `reads`, `authority_refs`, `pass`, and `failure_reason`. `reads` is the actual read set, not an idealized one.

A subject-declared PASS is not final. A maintainer separately inspects semantic recovery, authority discipline, read boundaries, stage order and HEAD stability.

## Anti-gaming / harness rules

- Never send stages 2 and 3 together with the initial instruction.
- Never tell the subject expected answers or controller pass criteria.
- Reading this controller contract before report completion is a protocol failure for the subject.
- Do not read an earlier Fresh-Agent report before completing all three scenarios.
- Do not modify the product or handoff to make a run pass. Preserve failures and repair the harness/system afterward through CAP-0009's normal evolution rule.
- Do not score prose style. Score semantic recovery, authority discipline, bounded recall, staged isolation and architectural direction.

## Cadence

The fixed cadence remains based only on `.longcycle/handoff/current.json.continuity_sequence`: every positive multiple of 10 is a scheduled genuine Fresh-Agent boundary. Manual/event-triggered runs do not reset it. A same-Agent rehearsal never satisfies the scheduled boundary. A report-only commit does not increment continuity sequence.
