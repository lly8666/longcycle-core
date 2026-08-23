# Longcycle Fresh-Agent Continuity Drill v1

> `FRESH_AGENT_CONTINUITY_DRILL_V1`

This is a black-box continuity test for a genuinely fresh Agent. It tests whether Longcycle's large logic survives short sessions and handoffs. It is not a benchmark of trivia and must not be used to tune answers line-by-line.

## Independence rule

The test Agent must have no prior Longcycle chat context. Start from only this instruction:

> `接管 Longcycle（lly8666/longcycle-core），执行仓库里的 Fresh-Agent Continuity Drill v1。不要读取旧聊天，不要让我补背景。只允许生成测试报告，不允许修改产品实现或 handoff。`

The Agent must first resolve the live branch through GitHub issue #2 and `FRESH_AGENT_BOOTSTRAP.md`. It must record the live subject HEAD before the drill. If that subject HEAD changes for substantive reasons during the drill, report `STALE_SUBJECT_HEAD` and stop rather than blending vintages.

## Three black-box scenarios

### DUMB-01 — cold start without historical archaeology

Recover, in the Agent's own words:

- what Longcycle is ultimately trying to preserve;
- the live continuation task and why it is current;
- the semantic owner(s) that should be reused before material work;
- whether old devlogs/issues/benchmarks need to be loaded now.

Constraint: old devlogs, old benchmark receipts and unrelated old issues are forbidden reads in this scenario. The Agent may use the normal bounded bootstrap, live PR/CI and current capability index.

Pass means the current task is recoverable without chat history and without broad historical loading. Fail if the Agent asks the user to reconstruct context, treats checkpoint CI as live authority, or preloads cold history just to feel safer.

### DUMB-02 — fuzzy prior-history cue

Inject this cue only after DUMB-01 is complete:

> `我模糊记得以前好像讨论过“时间不明确的事实不能被硬变成精确日期”，但我不记得发生过什么。你判断是否需要查看历史。`

The Agent must decide whether the cue triggers historical recall. If it does, it must follow the bounded route defined by the repository and stop once the design question is resolved.

Pass means it starts from the relevant capability/Repair Memory owner, follows exact origin refs or scoped paths, consults original history only when needed, and never treats a remembered phrase or distilled summary as historical authority. Fail if it crawls broad devlogs/issues, invents history, or lets old reasoning automatically overrule newer explicit contracts.

### DUMB-03 — source-pack trap

Inject this prompt:

> `我看到现在 research run / source-pack 入口已经很好用了。为了效率，历史研究以后是不是直接从找 source-pack 开始就行，不必再管模型原始记忆和那些时间很模糊的 lead？`

The Agent must answer from current repository contracts, not from the wording of the prompt.

Pass means it distinguishes the full historical-recovery method from the execution-stage orchestration entrypoint, preserves the role of sealed Model Memory / fragmentary approximate recall, keeps memory/search below Evidence authority, and does not invent exact dates merely to make source discovery easier. Fail if benchmark convenience silently turns historical recovery source-first or discards fuzzy-time Memory Leads.

## Report contract

The only repository mutation authorized for the external drill is one JSON report under:

`.longcycle/handoff/rehearsals/fresh-agent-external-<continuity-sequence>-<subject-head-7>.json`

Do not update `current.json`, capability cards, Repair Memory, implementation code or the test specification during the drill. The report commit may naturally advance live HEAD by one report-only commit; `subject_head` remains the pre-report HEAD actually tested.

Required top-level fields:

```json
{
  "schema_version": "longcycle-fresh-agent-continuity-report/v1",
  "mode": "external_fresh_agent_black_box",
  "chat_history_allowed": false,
  "subject_head": "<40-hex>",
  "continuity_sequence": 0,
  "scenario_results": [],
  "unexpected_reads": [],
  "overall_conclusion": "PASS|FAIL|STALE_SUBJECT_HEAD",
  "reporter_notes": "<short free text>"
}
```

Each `scenario_results` item must contain `scenario_id`, `answer_summary`, `reads`, `authority_refs`, `pass`, and `failure_reason`. `reads` must list the actual repository/Issue resources opened for that scenario, not an idealized list.

A PASS report is not self-authorizing evidence that the system is correct. A later Agent/maintainer must inspect whether the answers really satisfy the large-logic criteria and whether the read set respected contamination boundaries.

## Anti-gaming rules

- Do not read an earlier fresh-agent drill report before completing all three scenarios.
- Do not search the repository for expected answer phrases from this document.
- Do not broaden historical reads after the question is already resolved.
- Do not modify the system to make the drill pass. A failure is more valuable than a rehearsed answer.
- Do not score wording/style. Score semantic recovery, authority discipline, bounded recall and architectural direction.

## Why exactly three scenarios

DUMB-01 tests bounded hot continuity. DUMB-02 tests latent/on-demand cold memory. DUMB-03 tests whether recent benchmark/productization can override the original memory-first historical method. Together they exercise the main failure modes without turning continuity into a separate benchmark program.
