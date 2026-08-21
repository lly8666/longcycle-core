# CONTINUE HERE — Longcycle Fresh-Session Bootstrap

Fresh session 不需要重读项目历史，也不要让用户重新解释。

## 固定接力语句

用户只需要说：

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

这句话本身不携带当前任务事实；当前状态必须从仓库恢复。

## Fresh-session 正常流程

1. 通过 GitHub issue #2 找到 live PR / branch。
2. 先读 `STRATEGIC_COMPASS.md` 和 `METHODOLOGY_CORE.md`。
3. **不要立刻照抄 Core。** 先用自己的话内部重建项目为什么存在、核心认知缺口、point-in-time 意义、Evidence 边界、跨行业终局和工具/目标区别。
4. 再读 `.longcycle/continuity/mission-fidelity.json` 做 semantic calibration；遗漏哪一项，只定向重读对应 Core 段落并纠偏。
5. 再读 `.longcycle/handoff/current.json`，获得**当前中期目标、短期目标、下一大步、continuation cursor、active context 和 ordered actions**。
6. 刷新 live HEAD / commit delta / CI；checkpoint 中的 CI 只是快照。
7. 只加载 `resume_read_set` 中当前任务需要的文件，通过 Vertical Alignment Gate 后，从 cursor 的当前/下一原子动作继续。

**不要默认读取旧 devlog、旧行业包、全部 raw data 或整个仓库。** 需要追溯理由时，再按 `deep_reference_paths` 定向展开。

## Mission Calibration Gate

Agent 的第一遍理解必须先自己生成，再拿 semantic contract 校准。

通过标准不是“出现了几个关键词”，而是能用自己的话解释关键因果。发现缺口时，先纠偏再执行，不要把错误理解带进具体任务。

不要持久化私有思维链。需要记录时，只保存简洁的 alignment 结论、任务层级、决策和可复现约束。

## Vertical Alignment Gate

开始新的实质子问题、完成一个 coherent 子任务、准备扩大范围或遇到改变假设的新结果时，都重新向上检查：

1. 我现在具体在做什么原子任务？
2. 它推进哪个短期里程碑？
3. 这个短期里程碑推进哪个中期能力证明？
4. 这个中期目标如何服务 Longcycle 最终使命？
5. 当前任务的 `done_when` 是否已经满足？继续投入的边际价值还高吗？

如果只能说出当前 TODO，却无法连接父目标，或者任务已经达到 stop/done 条件，就应该停止或重排，而不是继续钻深。

## 实时 handoff 边界

完成一个会改变“下一 Agent 应该做什么”的 coherent 小任务后：

```text
完成实质工作并 commit
→ Vertical Alignment Gate
→ 更新 current.json 的 continuation cursor / 动态状态
→ checkpoint_based_on_head_sha 指向该实质工作 commit
→ commit handoff sync
```

如果会话在同步前意外结束，新 Agent 必须根据 live HEAD 与 checkpoint base 的差异检查 intervening commits，再决定如何恢复，不能猜。

## 两种权威不要混淆

**战略方向：**

```text
new explicit user instruction
> STRATEGIC_COMPASS.md
> METHODOLOGY_CORE.md
> current handoff strategic horizon
> deep references / old narrative
```

**实现新鲜度：**

```text
live Git HEAD / CI / canonical artifacts
> deterministic-derived state
> checkpoint snapshot
> narrative
```

## Core 纪律

- `STRATEGIC_COMPASS.md`：只存使命和防偏航原则；
- `METHODOLOGY_CORE.md`：只存跨行业方法；
- `.longcycle/continuity/mission-fidelity.json`：只存使命语义检查问题/误读，不存标准答案；
- `current.json`：只存中短期状态和实时 continuation cursor；
- active context：只存当前行业/任务细节；
- devlog：只存历史，不属于默认启动上下文。

具体行业经验只有在被提炼成跨行业方法后，才允许进入 Method Core。

如果任务是修改 handoff 机制本身，再读 `docs/development/session-handoff-protocol.md` 和 `docs/development/continuity-architecture.md`。否则不要为了“理解得更完整”主动加载全部历史。
