# CONTINUE HERE — Longcycle Fresh-Session Bootstrap

Fresh session 不需要重读项目历史，也不要让用户重新解释。

## 固定接力语句

用户只需要说：

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

这句话本身不携带当前任务事实；当前状态必须从仓库恢复。

## Fresh-session 正常流程

1. 先读 GitHub issue #2，只把它当 rendezvous：找到 active PR / branch / handoff 路径，不从 issue 正文推断 live task。
2. 刷新 active PR 的 live HEAD。
3. 读 `STRATEGIC_COMPASS.md` 和 `METHODOLOGY_CORE.md`，先用自己的话重建项目为什么存在、为什么要保存 Reality + contemporaneous Judgment + Outcome、为什么 point-in-time/no-lookahead 是第一性边界、Evidence 与模型记忆如何分工、为什么跨行业 benchmark 只是手段。
4. 再读 `.longcycle/continuity/mission-fidelity.json` 校准。遗漏哪一项，只定向重读对应 Core；不要把 rubric 当答案模板。
5. 读 `.longcycle/handoff/current.json`，获取当前中期目标、短期目标、continuation cursor、active context、ordered actions 与 `.longcycle/handoff/data-plane.json` 路径。
6. 比较 live HEAD 与 `checkpoint_based_on_head_sha`。若不相同，先检查 intervening commits；handoff-only commit 可以在确认无 substantive drift 后继续，不能因为 checkpoint 落后一两个控制面 commit 就要求用户重述背景。
7. 刷新 live CI。checkpoint 内 CI 永远只是 snapshot。
8. 只读 `resume_read_set` 中当前任务需要的文件；旧行业、旧 devlog、全部 raw data、全部 Repair Memory 默认不加载。
9. 修改已知代码路径前，才用 `.longcycle/repair-memory/active-index.json` 或 `python scripts/repair_memory.py relevant <paths...>` 做 path-scoped invariant lookup。
10. 只有 cursor 明确需要二进制状态时，才恢复 data-plane 中 `required_for_current_task=true` 的对象。

## Handoff 的两层权威

```text
Git / current.json / receipts / data-plane manifest
    = control plane
    = 使命、状态、任务、资产身份、transport、SHA、恢复规则

GitHub Release + Google Drive
    = development data plane transports
    = 不改变 Evidence/source authority，也不替代数据库语义
```

### 1. GitHub Release：外部获得的原始来源

开发期内，**externally acquired immutable source payloads** 放 GitHub Release，例如：

- PDF / HTML / filing / formal announcement bytes；
- 含这些 raw source bytes 的 source-acquisition pack。

规则：

- Release asset 必须唯一命名、不可静默覆盖；
- manifest 保存 Release tag、filename、outer SHA-256；receipt 再保存需要的 raw document hash / upstream identity；
- Release 只是 transport/cache，不让转载站自动变成原始发行人，也不改变 claim-scoped authority；
- 需要重新 grounding 时，只恢复当前任务所需 source pack，验 hash 后进入正常 archive/parser/Evidence 路径；不要把整个历史 source 库搬进 session。

### 2. Google Drive：Longcycle 自己生成的二进制状态

**Longcycle-generated binary state** 放 Google Drive，例如：

- DuckDB replay materialization；
- generated execution / reconciliation output；
- generated database snapshot（如果确实需要）；
- offline runtime pack。

规则：

- manifest 中的 Drive file id + SHA-256 才定义对象；文件名、分享链接、修改时间都不是完整性依据；
- DuckDB/replay 默认 read-only；
- generated capsule 不能伪装成原始 Evidence archive；真正需要原始 source bytes 时，从 Release 单独恢复；
- Drive 是 portable generated-state relay，不是 live PostgreSQL authority，也不是终局 archive。

### 3. PostgreSQL 不做 session 搬运

不要把 live PostgreSQL cluster 放 Release 或 Drive 当 session state。需要 transaction / lease / outbox / write semantics 时，在 GitHub Actions 或其他 service-capable runtime 重新建立 PostgreSQL，并走正常写入路径。

如果未来确有 handoff 用的**生成型 DB snapshot**，它属于 Drive，且必须明确是 snapshot，不是 live authority。

### 4. Fail closed

Required asset 缺失、outer SHA 不匹配、内部 component digest 不匹配、runtime ABI 不兼容时，按 `stop_and_report_integrity_blocker` 处理；不能从聊天记忆、文件名或旧网盘对象猜。

## 产品成功标准：研究员理解，而不是 Agent 跑分

Longcycle 的 benchmark 用来**打脸架构**，不是训练 Agent 应试。

真正的验收问题是：一个有基本研究能力、但刚进入该行业的研究员，能否快速获得一个可辩护的行业心智模型，包括：

- 行业/技术/价值链结构；
- 关键对象不能如何混淆；
- 关键变量、参与者和历史分叉；
- 当时可知的 Reality、Expectation/Judgment、争议和理由；
- 后来的 Outcome；
- 每个高影响结论能追到什么 Evidence；
- 哪些地方仍然未知、冲突或不可比。

如果 Agent benchmark 更漂亮、自动任务完成率更高，但研究员仍必须自己从一堆 raw documents 重建行业结构，属于产品失败。

## Mission Calibration Gate

开始实质工作前必须能解释，而不是背关键词：

1. 为什么“保存长期、真实、可比较的行业历史”比又写一份当前报告更重要？
2. 为什么只保存最终事实会产生 hindsight，必须单独保存 contemporaneous cognition？
3. 为什么 later-known information 不能进入过去的 replay？
4. 为什么模型记忆和搜索只能发现线索，publishable truth 要受 archived claim-scoped Evidence 控制？
5. 为什么当前行业只是 cross-industry proving ground？
6. 为什么 researcher understanding 比 crawler/Agent/schema/benchmark 指标更接近产品终局？

## Vertical Alignment Gate

开始新的 substantive 子问题、完成 coherent 子任务、准备扩大范围或新结果改变假设时，向上检查：

```text
当前原子任务
↑ 短期里程碑
↑ 中期能力证明
↑ Longcycle 最终使命
```

如果当前任务已经达到 done/stop condition，或者继续投入只是让局部 benchmark 更好看，停止或重排。

## Handoff 更新纪律

完成一个会改变“下一 Agent 应做什么”的 coherent session 后：

```text
完成 substantive work 并 commit
→ 如有新的 resume-relevant binary asset，先上传正确 transport 并验证 hash
→ 更新 data-plane.json
→ 更新 durable receipt / active context
→ 更新 current.json continuation cursor / workstreams / ordered actions
→ checkpoint_based_on_head_sha 指向最后一个 substantive/control-plane commit（不要求指向 current.json 自己的 commit）
→ commit handoff sync
→ 刷新 live CI
→ 用 bounded cold-start rehearsal 验证 fresh Agent 能恢复任务
```

因此 live HEAD 通常可能比 `checkpoint_based_on_head_sha` 多一个 handoff-only commit。Fresh Agent 应比较 commit delta 并确认其性质，而不是把这个正常形态误判为丢失状态。

## Core 纪律

- `STRATEGIC_COMPASS.md`：最终使命、真正成功标准、防偏航；
- `METHODOLOGY_CORE.md`：跨行业方法；
- `.longcycle/continuity/mission-fidelity.json`：语义校准问题，不存答案；
- `.longcycle/handoff/current.json`：中短期 live cursor；
- `.longcycle/handoff/data-plane.json`：resume-relevant binary identity / transport / integrity / restore contract；
- receipts：已完成 benchmark / source / replay / exit 等可审计结果；
- `.longcycle/repair-memory/`：高复发风险 invariant；
- active context：当前行业/任务；
- devlog / old industry：按需追溯，不属于默认启动上下文。

如果任务本身是在修改 handoff 机制，再定向读 `docs/development/session-handoff-protocol.md` 与 `docs/development/continuity-architecture.md`；不要因此预加载整个开发历史。
