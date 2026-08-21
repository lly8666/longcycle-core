# Longcycle Session Handoff Protocol v2

## 1. 目标

Longcycle 会经历很多聊天窗口、Agent、模型版本和行业 benchmark。连续性系统的目标不是让未来 Agent “记住所有过去”，而是让它始终准确恢复：

```text
长期使命
+ 跨行业方法论
+ 当前中期目标
+ 当前短期目标 / 下一大步
+ 当前任务所需的局部 context
+ live 实现状态
```

旧行业流水账、旧 devlog 和旧实验不属于默认记忆。

## 2. 单一职责的五个状态层

| 层 | 权威文件 | 保存什么 | 绝不保存什么 |
| --- | --- | --- | --- |
| Long-term mission | `STRATEGIC_COMPASS.md` | 最终使命、成功标准、防偏航 Gate | 行业、日期、任务、CI、计数 |
| Method core | `METHODOLOGY_CORE.md` | 已采用的跨行业方法 | 单行业技巧、当前 Prompt、当前工具限制 |
| Dynamic handoff | `.longcycle/handoff/current.json` | 中期/短期目标、next big step、active context、工作流、快照 | 长期使命和方法论的复制品 |
| Active context | handoff 指向的当前目录/文件 | 当前行业、benchmark、campaign、数据和局部规则 | 其他旧行业的历史 |
| History | Git + `docs/devlog/` | 决策过程、失败、旧状态、审计报告 | 默认启动上下文 |

**同一类信息只能有一个正常权威归属。** 其他文件引用它，不复制它。

## 3. Fresh-session 最小算法

```text
1. issue #2 → resolve live PR / branch
2. read STRATEGIC_COMPASS.md
3. read METHODOLOGY_CORE.md
4. read current.json
5. refresh live HEAD / delta / CI
6. load only current resume_read_set / active context needed by the task
7. pass the four-question Alignment Gate
8. execute ordered next actions
```

默认不读旧 devlog、旧 benchmark、整个 repository 或全部 raw data。

`resume_read_set` 最多 8 个文件；正常目标应更少。

## 4. Four-question Alignment Gate

Agent 必须知道：

1. 最终使命是什么；
2. 当前中期目标是什么；
3. 当前短期任务为什么推进中期目标；
4. 完成后下一大步是什么。

第一题来自 Compass；第 2–4 题来自 handoff。不要把动态答案写回 Compass。

## 5. Core 有硬预算

长期 Core 必须保持小而稳定：

- Compass 有 byte / line CI budget；
- Method Core 有 byte / line CI budget；
- active-context exclusion terms 不得出现在两个 Core；
- 加入一条长期原则时，应优先压缩、合并或替换旧表达，不能无限 append。

如果核心越来越长到“Agent 需要总结核心才能使用”，说明机制失败。

## 6. 经验如何跨行业传递

正常路径只有这一条：

```text
行业事实 / 局部经验
→ active context / devlog
→ 在真实 benchmark 中被验证
→ 判断是否跨行业成立
→ 提炼成一句稳定方法
→ METHODOLOGY_CORE.md
```

没有经过提炼的旧行业经验不进入下一行业的默认上下文。

Method promotion 需要至少满足一项：

1. 用户明确采用为长期方法；
2. 多个真实 benchmark 支持；
3. 单个 benchmark 暴露的是明显跨行业的基础认识论约束，并有可审计理由。

单次实现方便、单个行业术语、某模型的临时能力和某工具限制不能自动升级为长期方法。

## 7. Active context 必须可替换

`current.json.active_context` 描述当前工作环境，并提供：

- context id / kind / label；
- root path；
- 当前 campaign / coverage 路径（若适用）；
- deep context paths；
- `core_exclusion_terms`。

切换行业或 benchmark 时，正常操作是**替换 active context**，不是把新行业继续追加到 Compass/Method Core/resume set。

旧 context 留在 Git 中，需要时可追溯，但不再自动加载。

## 8. Handoff 本身也不能变成牛角尖

Handoff 的成功指标是：新 Agent 能以很小的 bootstrap context 正确恢复使命、方法、中短期目标和 live 状态，并安全继续工作。

它不是独立产品。除非真实 fresh-session audit 发现阻塞性失真，否则连续性优化不能长期压过主项目。

## 9. Live freshness 与战略权威分开

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

## 10. 新用户指令的稳定吸收

如果用户给出新的重要方向：

1. 先记录到 `pending_user_directives`（如果不能在同一 coherent batch 内完成归属）；
2. 判断它属于 mission、method、dynamic horizon 还是 active context；
3. 只修改对应权威层；
4. 完成后清空已吸收的 pending directive；
5. 写 concise devlog 记录改变原因。

不要把同一句用户要求复制到所有层。

## 11. Repository-only 自测

CI 的 handoff drill 必须能在不知道聊天历史的情况下：

- 从 active context 路径重建当前 campaign（若存在）；
- 对拍 raw / coverage / checkpoint；
- 检查 long-term cores 是否包含使命和方法；
- 检查 active industry/context 词是否泄漏进 Core；
- 检查 resume set 是否仍然有界；
- 检查 strategic horizon 是否完整；
- 人为构造 stale checkpoint 时必须能报错。

Repository-only fidelity 只证明可机械恢复的状态一致，不代表 curated research judgment 自动成为事实。

## 12. Fresh-Agent 外部测试

内部 CI 不能证明新模型真正理解航向。重大 continuity 变更后可用一个完全新会话做 report-only audit：

- 不提供历史聊天；
- 只给 repository 名和审计任务；
- 要求它用 bootstrap 恢复使命、方法、中期、短期、next big step；
- 故意测试它是否会加载无关旧行业或钻入局部最优；
- 只允许新增审计报告，不允许修代码。

报告回来后，由当前会话与 live repository 对拍。

## 13. 机制失效的典型信号

- Core 每个行业都增加一章；
- checkpoint 又开始复制 north star / invariants / methods；
- resume set 超过预算并不断加入 devlog；
- 新 Agent 必须知道很多旧行业细节才能继续新行业；
- 不同文件对同一使命或方法有不同版本；
- Agent 能说出当前 TODO，却不知道中期和下一大步；
- Agent 为了“完整理解”先加载整个仓库；
- handoff 优化本身连续占据主路线。

出现这些信号时，优先做**归属修正和压缩**，而不是再加一份总结。
