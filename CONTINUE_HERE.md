# CONTINUE HERE — Longcycle Fresh-Session Bootstrap

Fresh session 不需要重读项目历史，也不要让用户重新解释。

## 固定接力语句

用户只需要说：

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、Architecture Baseline、宏大/长期/中期/短期/当前目标和 live 状态，从 continuation cursor 继续；先做战略层级和防钻牛角尖校准，不要让我重复背景。**

这句话本身不携带当前任务事实；当前状态必须从仓库恢复。

## Fresh-session 正常流程

1. 先读 GitHub issue #2，只把它当 rendezvous：找到 active PR / branch / handoff 路径，不从 issue 正文推断 live task。
2. 刷新 active PR / `main` 的 exact live HEAD 与 CI；checkpoint 内 CI 永远只是 snapshot。
3. 读 `STRATEGIC_COMPASS.md` 和 `METHODOLOGY_CORE.md`，先用自己的话重建项目为什么存在、为什么要保存 Reality + contemporaneous Judgment + Outcome、为什么 point-in-time/no-lookahead 是第一性边界、Evidence 与模型记忆如何分工、为什么跨行业 benchmark 只是手段。
4. 再读 `.longcycle/continuity/mission-fidelity.json` 校准。遗漏哪一项，只定向重读对应 Core；不要把 rubric 当答案模板。
5. 读 `.longcycle/baseline/current.json` → versioned manifest → `ARCHITECTURE_BASELINE_V1.md`。Baseline 冻结的是“什么算正确”，**不是**替代 Strategy / Method Core，也不是冻结实现、行业或产品扩展。
6. 读 `.longcycle/handoff/current.json`，恢复五层目标：

```text
宏大/终局使命
↓
长期产品方向
↓
中期目标（strategic_horizon.medium_term_goal）
↓
短期里程碑（strategic_horizon.short_term_goal）
↓
当前原子任务（continuation_cursor.current_task / next_atomic_action）
```

   开工前必须能解释当前原子任务如何逐层服务每个父目标。
7. 比较 live HEAD 与 `checkpoint_based_on_head_sha`。若不同，先检查 intervening commits；不能因为 checkpoint 落后一两个控制面 commit 就要求用户重述背景。
8. 只读 `resume_read_set` 中当前任务需要的文件；`.longcycle/capabilities/active-index.json` 是永久 compact bootstrap 项。不要默认读取旧 devlog、旧行业、旧 rehearsal report 或全部 raw data。
9. material capability / product-surface / architecture 开发前，先写/更新 `.longcycle/change-contract/current.json` 的 `L1/L2/L3/L4`，再独立执行 Capability Registry admission：`reuse / extend / replace / new`。两个维度不可混用。
10. `current-admission.json.target_capability_ids` 是精确 owner 路由；必须直接加载对应 capability card、entrypoint/guard 和相关负例。默认 L1/L2 + reuse/extend，不能因为“更干净”新建第二个 semantic owner。
11. 修改已知代码路径前，用 Repair Memory 做 path-scoped invariant lookup；如果全新路径无命中，也不能推断“没有历史约束”。
12. 如果出现“以前是不是讨论过/修过这个”的 fuzzy cue，走 `docs/development/on-demand-history-recall.md`：owner → Repair Memory → exact origin refs → bounded Git/Issue/receipt/devlog history → 回到 live authority。不要 bulk-load 历史。
13. 只有 cursor 明确需要二进制状态时，才恢复 data-plane 中 `required_for_current_task=true` 的对象。
14. 做 whole-project review / architecture review / deliberate L3 change 时，额外读 `docs/development/longcycle-development-operating-system.md`；普通 L1/L2 Agent 不需要默认加载这份完整 reviewer manual。

## Handoff 的两层权威

```text
Git / current.json / receipts / data-plane manifest
    = control plane
    = 使命、状态、任务、source identity、locator、transport、digest、恢复规则

Google Drive / historical GitHub Release / later materialized files
    = development data-plane
    = 不改变 Evidence/source authority，也不替代数据库语义
```

## 1. 网页：优先本地数据库 → Google Drive

对当前 Agent 能完整读取的网页：

```text
读取网页可见内容
→ 忠实保存 claim-scoped visible text + source/provenance metadata
→ 批量写入 bounded local DuckDB/SQLite capture capsule
→ checkpoint / close / SHA-256
→ 上传 Google Drive
→ Git handoff 只保存 Drive file id + SHA + schema/source count + restore instruction
```

规则：

- 不要为了保存网页 HTML 而专门启动 GitHub Actions；
- 不要为了 handoff 把每一页网页正文逐页 commit 到 Git；
- 每条 capture 至少保留原始 URL、publisher/source identity、source-displayed date/title（有可靠支持时）、`captured_at`、truthful `capture_mode`、faithful visible text、文本/记录 digest，以及重要缺失说明；
- capture DB 是 capture/handoff envelope，不是 live PostgreSQL，也不是 Fact/Judgment 自动发布；
- Drive 只是 transport，不能改变 source authority；恢复后仍走正常 archive/Evidence 语义；
- 已经存在的历史 Release source pack 如果含 HTML/web bytes，保持 immutable、继续按旧 receipt 使用，不迁移、不重写。

## 2. PDF：先验证 locator / 内容，raw bytes 延后补全

**以后不要为了下载 PDF 而启动 GitHub Actions。** PDF 下载能力不再是研究主路径的前置门槛。

PDF 使用三个显式状态：

```text
locator_verified
→ content_verified
→ materialized
```

### `locator_verified`

确认：

- publisher/source identity；
- PDF/document identity；
- 原始下载 URL；
- 文件名（能确定时）；
- title/date（source-supported 时）；
- verification time/mode；
- `materialization_status`。

对于主流的官方、监管机构、上市公司/issuer、研究机构等站点上的 PDF，只要 document identity + locator 已确认，就把它当作**真实存在的合法 source document**，不要再为了证明 GitHub runner 能不能下载而消耗研究时间。

但要保留 epistemic boundary：**只确认链接存在、完全没读到 claim-relevant 内容，不能拿这个 locator 证明具体 claim。**

### `content_verified`

如果当前 Agent 已经通过可信交互界面实际读到 PDF 相关内容，并能保存 claim-scoped excerpt / page / section / readable representation，那么即使 raw PDF bytes 尚未归档，也可以进入正常 Grounded Evidence。

```text
source 是否说了 X
!=
我们是否已经保存了 byte-identical PDF 文件
```

前者决定 claim 能否 grounding；后者是完整性增强，不再阻塞开发。

主流网站上的 PDF 是否“权威”仍按 claim scope 判断。**不因为 `.pdf` 后缀或 transport 自动升级 authority。**

### `materialized`

以后有正常网络的 Agent 再做：

```text
按 recorded URL 下载
→ 验证 document identity / 已记录的 claim-relevant 内容
→ 补 raw byte size / SHA-256 / durable storage locator
→ 更新 owning receipt/materialization metadata
```

later materialization 若与 earlier content/source identity 冲突，fail closed，建立 integrity repair；不能静默覆盖。

已经存在的 GitHub Release PDF/source pack 属于**历史 materialized asset**，可以直接复用，但不再代表未来 PDF 的默认 acquisition 方式。

## 3. 其他生成型状态：Google Drive

Longcycle-generated binary state 放 Google Drive，例如：

- DuckDB replay materialization；
- generated execution / reconciliation output；
- generated database snapshot（如果确实需要）；
- offline runtime pack。

规则：

- manifest 中的 Drive file id + SHA-256 才定义对象；
- DuckDB/replay 默认 read-only；
- generated capsule 不能伪装成原始 Evidence archive；
- 网页 capture capsule 虽然走 Drive，但里面的可见文本是 source-derived capture；
- Drive 是 portable relay，不是 live PostgreSQL authority，也不是终局 archive。

## 4. PostgreSQL 不做 session 搬运

不要把 live PostgreSQL cluster 放 Release 或 Drive 当 session state。需要 transaction / lease / outbox / write semantics 时，在 GitHub Actions 或其他 service-capable runtime 重新建立 PostgreSQL，并走正常写入路径。

注意：**Actions 仍然可以用于 PostgreSQL/runtime execution；禁止的是为了下载新 PDF 而制造 acquisition Actions。**

## 5. Fail closed 的边界

以下情况 fail closed：

- claim 依赖某个 PDF 内容，但当前只有 locator、从未实际读到 claim-relevant 内容；
- later materialization 与 earlier content/source identity 冲突；
- required webpage/generated capsule 缺失或 digest 不匹配；
- runtime ABI / database integrity gate 失败。

以下情况**不再**构成 blocker：

- raw PDF bytes 尚未下载，但 PDF locator 已确认且 claim-relevant 内容已经 `content_verified`；
- GitHub runner 对某主流 source host 下载失败；
- 当前 Agent 无法上传 GitHub Release。

## 产品成功标准：研究员理解，而不是 Agent 跑分

Longcycle 的 benchmark 用来打脸架构，不是训练 Agent 应试。真正的验收是研究员能否快速获得可辩护的行业心智模型，包括 Reality、当时 Judgment、后来 Outcome、Evidence、争议和未知。

如果自动任务完成率更高，但研究员仍必须自己从 raw documents 重建行业结构，属于产品失败。

## Mission Calibration Gate

开始实质工作前必须能解释：

1. 为什么保存长期、真实、可比较的行业历史比又写一份当前报告更重要？
2. 为什么只保存最终事实会产生 hindsight，必须单独保存 contemporaneous cognition？
3. 为什么 later-known information 不能进入过去的 replay？
4. 为什么模型记忆和搜索只能发现线索，publishable truth 要受 claim-scoped Evidence 控制？
5. 为什么当前行业只是 cross-industry proving ground？
6. 为什么 researcher understanding 比 crawler/Agent/schema/benchmark 指标更接近产品终局？

## Strategic Hierarchy Gate

开工前必须回答：

1. 宏大/终局使命是什么？
2. 长期产品方向是什么？
3. 当前中期目标是什么？
4. 当前短期里程碑是什么？
5. 当前原子任务、`done_when` 和 `next_atomic_action` 是什么？
6. 当前原子任务怎样逐层推进上面五层？

只能背 slogan、不能解释因果链 = bootstrap 未完成。

## Vertical Alignment / 防钻牛角尖 Gate

开始新的 substantive 子问题、完成 coherent 子任务、准备扩大范围或新结果改变假设时，向上检查：

```text
当前原子任务
↑ 短期里程碑
↑ 中期能力证明
↑ 长期产品方向
↑ Longcycle 终局使命
```

同时问：

- done/stop condition 是否已经满足？
- 继续做是否改变父目标，还是只让局部数字/代码更漂亮？
- 新结果是否使当前任务失去优先级？
- 是不是因为局部问题有趣/容易量化才越做越深？
- 停下来会不会真的伤害父目标？

父目标边际价值已经很低时，停止或重排；不能因为“这个局部问题确实存在”就无限深挖。

## Independent Judgment Gate

用户决定目标、约束、偏好和风险取舍；Agent 仍必须独立判断方法是否科学。用户建议的方法若与使命、Baseline、Evidence/PIT、live state、stop condition 或成本收益冲突，Agent 应说明关键原因并收窄/改写/拒绝，而不是为了服从继续错误路线。

高能力任务如果当前 Agent 无法可靠综合判断，应停止并升级，而不是模仿高级语气给伪结论。

## Change Contract + Capability Gate

```text
L1/L2/L3/L4
= 变化离 Baseline 多近

reuse/extend/replace/new
= 哪个 semantic owner 负责
```

默认 L1/L2 + reuse/extend。改变 Baseline invariant 或 Baseline-critical test 的语义期望，必须先进入 L3；`更干净/更通用/future-proof` 不构成 L3 证据。真实重要 source-grounded counterexample 或 security/consistency defect 才有资格推进 L3。

## Handoff 更新纪律

完成一个会改变“下一 Agent 应做什么”的 coherent session 后：

```text
完成 substantive work
→ Vertical Alignment Loop
→ 更新 Change Contract / capability admission（如分类变化）
→ 必要时更新 capability card / Repair Memory
→ focused validation + required CI
→ commit substantive/control-plane work
→ 更新 data-plane / receipts / active context（如需要）
→ 更新 current.json strategic horizon / continuation cursor / workstreams / ordered actions
→ checkpoint_based_on_head_sha 对齐真实 completed work
→ commit handoff sync
→ 刷新 exact live HEAD / PR / CI
→ 从 live target ref 重新读取 final handoff / HEAD
→ 再交还控制权
```

不能拿 parent commit 的 green 当 exact-head green；不能让 next Agent 继续一个 intervening commit 已经完成的任务。

## Core 纪律

- `STRATEGIC_COMPASS.md`：终局使命、长期方向、真正成功标准、防偏航；
- `METHODOLOGY_CORE.md`：跨行业方法；
- `.longcycle/continuity/mission-fidelity.json`：语义校准问题，不存答案；
- `.longcycle/baseline/*`：冻结 semantic correctness 与 change-level contract；
- `.longcycle/capabilities/active-index.json` + cards：稳定 capability routing / owner；
- `.longcycle/change-contract/current.json`：当前 L1-L4 风险分类；
- `.longcycle/capabilities/current-admission.json`：当前 reuse/extend/replace/new owner disposition；
- `.longcycle/handoff/current.json`：中短期 live cursor；
- `.longcycle/handoff/data-plane.json`：resume-relevant source/data identity / transport / integrity / restore contract；
- `.longcycle/repair-memory/`：高复发风险 invariant；
- active context：当前行业/任务；
- devlog / old industry / old reports：按需追溯，不属于默认启动上下文。

whole-project / architecture review 额外读 `docs/development/longcycle-development-operating-system.md`。修改 handoff 机制再定向读 `docs/development/session-handoff-protocol.md` 与 `docs/development/continuity-architecture.md`。

## Handoff Semantic Reread Gate

> `HANDOFF_SEMANTIC_REREAD_V1`

Handoff 是每次 substantive session 末尾占比很小、但不能跳过的一环。**写完 JSON 不等于完成 handoff。** closing Agent 必须把最终 draft 从头到尾重新读一遍，再决定是否可以提交。

重读时按字段原始语义检查，而不是只看 schema 是否通过：

- `bootstrap_instruction` 只写恢复程序，不写 campaign/commit mini-devlog；
- `strategic_horizon.next_big_step` 保持里程碑尺度，不能退化成 `next_atomic_action` 的换句话说；
- `continuation_cursor` 是当前 task / done_when / next atomic action 的唯一即时 owner；
- 当前 cursor 所属 workstream 的 `next_actions` 应表达 lane queue/后续步骤，不重复维护同一个即时动作；
- `memory_campaign.next_research_actions` 保持 campaign/research 尺度，不当作 CI/workflow 操作清单；
- `ci` 只记录实际观察到的 snapshot，没观察到就明确 `unobserved`；
- `ordered_next_actions` 只承担必要的跨 workstream 顺序，不再写一份 cursor 故事。

同时检查更新节奏：使命/方法不因 session 重写；战略和 workstream 只在 milestone/lane 状态变化时更新；cursor 与重要 live state 每次 substantive handoff 都要重新验证。**必须检查不等于必须改值。**

完整 closing transaction：

```text
写 current.json draft
→ schema/static validation
→ 从头完整重读最终 draft
→ 检查字段粒度 / 重复 owner / stale live state
→ 检查当前 material change 是否仍落在 current-admission / Change Contract scope
→ 必要时触发 bounded history recall
→ normalize 后再 commit
→ 从 live target ref 重新读取最终 current.json / HEAD / CI
```

若重读后无法唯一回答“当前 task 是什么、next atomic action 是什么、next big step 为什么更高一层、哪个 workstream 拥有 cursor、哪些状态其实尚未观察”，handoff 还没写完。

## Fresh-Agent Drill Cadence

> `FRESH_AGENT_DRILL_CADENCE_V1`

不用新增第二个计数器。`continuity_sequence` 就是 handoff 次数的唯一 cadence source。

closing Agent 在写下一份 handoff 前先算 `next_sequence = current_sequence + 1`。当 `next_sequence` 是 10 的正整数倍时，Agent **必须主动告诉用户 Fresh-Agent drill 到期，并在有隔离 fresh session/Agent 能力时主动触发** `docs/development/fresh-agent-continuity-drill.md`，不能等用户自己记得。

- 固定节拍：10、20、30……；
- 任意 sequence 都可由用户或 Agent 手动触发；
- material continuity change / 重复历史召回失败也可以提前触发；
- 手动/提前 drill **不重置** 固定十次节拍；
- same-Agent artificial-ignorance rehearsal 可以用于当前修复自检，但**不能替代** genuine Fresh-Agent drill；
- drill 的 report-only commit 不增加 `continuity_sequence`。
