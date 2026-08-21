# Longcycle Session Handoff Protocol v2

## 1. 目标

Longcycle 会经历很多聊天窗口、Agent、模型版本和行业 benchmark。连续性系统的目标不是让未来 Agent “记住所有过去”，而是让它始终准确恢复：

```text
长期使命（为什么做、最终用户能力是什么）
+ 跨行业方法论（怎么做、为什么这样做）
+ 当前中期目标
+ 当前短期目标 / 下一大步
+ 当前任务所需的局部 context
+ live 实现状态
```

旧行业流水账、旧 devlog 和旧实验不属于默认记忆。

连续性追求的是**最小充分上下文**：足够高保真地复刻使命和方法，又不把几十轮历史全部搬进新 Agent。

## 2. Cold start 先解决“去哪找当前项目”

真正失忆的 Agent 只知道 repository 名时，默认分支未必是当前开发状态。

因此默认分支根目录必须长期存在：

`FRESH_AGENT_BOOTSTRAP.md`

它只负责：

```text
default branch
→ issue #2 stable rendezvous
→ resolve active PR / development branch
→ active branch CONTINUE_HERE.md
```

它不得复制当前行业、campaign、branch 名、CI、TODO 或其他 live state。

**不能假设 fresh Agent 会主动猜到应该看 PR/issue。** 如果它从 stale `main` 推断当前路线，说明 cold-start bootstrap 尚未完成。

## 3. 单一职责的五个状态层

| 层 | 权威文件 | 保存什么 | 绝不保存什么 |
| --- | --- | --- | --- |
| Long-term mission | `STRATEGIC_COMPASS.md` | 最终使命、使命因果、成功标准、防偏航 Gate | 行业、日期、任务、CI、计数 |
| Method core | `METHODOLOGY_CORE.md` | 已采用的跨行业方法及其理由 | 单行业技巧、当前 Prompt、当前工具限制 |
| Dynamic handoff | `.longcycle/handoff/current.json` | 中期/短期目标、next big step、active context、工作流、快照 | 长期使命和方法论的复制品 |
| Active context | handoff 指向的当前目录/文件 | 当前行业、benchmark、campaign、数据和局部规则 | 其他旧行业的历史 |
| History | Git + `docs/devlog/` | 决策过程、失败、旧状态、审计报告 | 默认启动上下文 |

**同一类信息只能有一个正常权威归属。** 其他文件引用它，不复制它。

## 4. Fresh-session 算法

```text
1. default root → FRESH_AGENT_BOOTSTRAP.md
2. issue #2 → resolve live PR / branch
3. switch reads to active branch
4. read STRATEGIC_COMPASS.md
5. read METHODOLOGY_CORE.md
6. read current.json
7. refresh live HEAD / delta / CI
8. load only resume_read_set / active context needed by the task
9. pass mission-fidelity + four-question Alignment Gate
10. execute ordered next actions
```

默认不读旧 devlog、旧 benchmark、整个 repository 或全部 raw data。

`resume_read_set` 最多 8 个文件；正常目标应更少。

## 5. Mission fidelity gate

“知道使命”不等于能背出一句 slogan。

新 Agent 应能用自己的话解释至少以下因果：

1. 为什么保存长时间、关键且真实的产业历史有价值；
2. 为什么最终事实不足以重建当时决策；
3. 为什么 contemporaneous Expectation/Judgment 必须与 Reality 分开保存；
4. 为什么 point-in-time / no-lookahead 是核心，否则会变成 hindsight database；
5. 为什么真实、可比、足够长的历史能够通过常识和简单因果暴露周期风险/机会；
6. 为什么模型记忆和搜索负责发现，而 Evidence 才决定可发布历史；
7. 为什么失败、延期、修订和错误判断必须留在轨迹里；
8. 为什么单个行业只是证明环境，最终方法必须可迁移。

如果 Core 被压缩到 Agent 只能背关键词、不能解释“为什么”，属于 continuity failure。

## 6. Four-question Alignment Gate

Agent 还必须知道：

1. 最终使命是什么；
2. 当前中期目标是什么；
3. 当前短期任务为什么推进中期目标；
4. 完成后下一大步是什么。

第一题来自 Compass；第 2–4 题来自 handoff。不要把动态答案写回 Compass。

## 7. Core 有硬预算，但预算不是压缩目标

长期 Core 必须保持职责清晰、增长有界：

- Compass 有 byte / line CI ceiling；
- Method Core 有 byte / line CI ceiling；
- CI 同时检查使命关键语义是否存在，不能只检查文件够短；
- active-context exclusion terms 不得出现在两个 Core；
- 加入长期原则时，应优先压缩、合并或替换旧表达，不能无限 append。

两个失败极端都要避免：

```text
过度压缩 → 只剩 slogan，使命因果丢失
过度膨胀 → Core 变百科全书，新 Agent 先做摘要才能工作
```

目标是**高保真 + 有界**，不是最短。

## 8. 经验如何跨行业传递

正常路径只有这一条：

```text
行业事实 / 局部经验
→ active context / devlog
→ 在真实 benchmark 中被验证
→ 判断是否跨行业成立
→ 提炼成稳定方法
→ METHODOLOGY_CORE.md
```

没有经过提炼的旧行业经验不进入下一行业的默认上下文。

Method promotion 需要至少满足一项：

1. 用户明确采用为长期方法；
2. 多个真实 benchmark 支持；
3. 单个 benchmark 暴露的是明显跨行业的基础认识论约束，并有可审计理由。

单次实现方便、单个行业术语、某模型的临时能力和某工具限制不能自动升级为长期方法。

## 9. Active context 必须可替换

`current.json.active_context` 描述当前工作环境，并提供：

- context id / kind / label；
- root path；
- 当前 campaign / coverage 路径（若适用）；
- deep context paths；
- `core_exclusion_terms`。

切换行业或 benchmark 时，正常操作是**替换 active context**，不是把新行业继续追加到 Compass/Method Core/resume set。

旧 context 留在 Git 中，需要时可追溯，但不再自动加载。

## 10. Handoff 本身也不能变成牛角尖

Handoff 的成功指标是：新 Agent 能以很小的 bootstrap context 高保真恢复使命、方法、中短期目标和 live 状态，并安全继续工作。

它不是独立产品。除非真实 fresh-session audit 发现阻塞性失真，否则连续性优化不能长期压过主项目。

## 11. Live freshness 与战略权威分开

战略：

```text
new explicit user instruction
> STRATEGIC_COMPASS.md
> METHODOLOGY_CORE.md
> handoff strategic horizon
> deep references
```

实现事实：

```text
live Git commit graph / HEAD / CI
> canonical & deterministic-derived artifacts
> checkpoint snapshot
> narrative
```

checkpoint 记录 `checkpoint_based_on_head_sha`，并永久要求 live refresh；Git commit graph 决定顺序，不使用手工时间戳作为 provenance authority。

## 12. 新用户指令的稳定吸收

如果用户给出新的重要方向：

1. 先判断它属于 mission、method、dynamic horizon 还是 active context；
2. 只修改对应权威层；
3. 如果无法在同一 coherent batch 完成归属，再临时进入 `pending_user_directives`；
4. 完成后清空已吸收的 pending directive；
5. 写 concise devlog 记录改变原因。

不要把同一句用户要求复制到所有层。

## 13. Repository-only 自测

CI 的 handoff drill 必须能在不知道聊天历史的情况下：

- 从 active context 路径重建当前 campaign（若存在）；
- 对拍 raw / coverage / checkpoint；
- 检查 long-term cores 是否保留使命因果和跨行业方法；
- 检查 active industry/context 词是否泄漏进 Core；
- 检查 resume set 是否仍然有界；
- 检查 strategic horizon 是否完整；
- 人为构造 stale checkpoint 时必须能报错。

Repository-only fidelity 只证明可机械恢复的状态一致，不代表 curated research judgment 自动成为事实。

## 14. Fresh-Agent 外部测试

内部 CI 不能证明新模型真正理解航向。重大 continuity 变更后可以用完全新会话做 report-only audit：

- 只给 repository 名和审计任务；
- 必须先从默认分支发现 bootstrap pointer，再解析 active branch；
- 不提供历史聊天；
- 要求用自己的话恢复使命因果、方法、中期、短期、next big step；
- 测试它是否需要加载无关旧行业或 devlog；
- 只允许在 active branch 新增审计报告，不允许修代码。

报告回来后，由当前会话与 live repository 对拍。

## 15. 机制失效的典型信号

- fresh Agent 停留在 default branch，并把 stale implementation 当 current roadmap；
- Core 每个行业都增加一章；
- Core 为了短而删掉“为什么”，Agent 只能复述 slogan；
- checkpoint 又开始复制 north star / methods；
- resume set 超过预算并不断加入 devlog；
- 新 Agent 必须知道很多旧行业细节才能继续新行业；
- 不同文件对同一使命或方法有不同版本；
- Agent 能说出当前 TODO，却不知道中期和下一大步；
- Agent 为了“完整理解”先加载整个仓库；
- handoff 优化本身连续占据主路线。

出现这些信号时，优先做**入口修复、归属修正和语义压缩/补足**，而不是再加一份无限增长的总结。
