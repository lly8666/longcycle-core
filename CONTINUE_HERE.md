# CONTINUE HERE — Longcycle Fresh-Session Bootstrap

Fresh session 不需要重读项目历史，也不要让用户重新解释。

## 只做这五步

1. 通过 GitHub issue #2 找到 live PR / branch。
2. 先读 `STRATEGIC_COMPASS.md` 和 `METHODOLOGY_CORE.md`。
3. 再读 `.longcycle/handoff/current.json`，获得**当前中期目标、短期目标、下一大步、active context 和 ordered actions**。
4. 刷新 live HEAD / commit delta / CI；checkpoint 中的 CI 只是快照。
5. 只加载 `resume_read_set` 中当前任务需要的文件，然后执行仍符合航向的 next action。

**不要默认读取旧 devlog、旧行业包、全部 raw data 或整个仓库。** 需要追溯理由时，再按 `deep_reference_paths` 定向展开。

## 四问 Alignment Gate

开始重要工作前必须能回答：

1. Longcycle 最终使命是什么？
2. 当前中期大目标是什么？
3. 当前短期任务为什么推进中期目标？
4. 完成当前任务后，下一大步是什么？

第 2–4 题来自 live handoff，不允许写进长期 Compass。

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
- `current.json`：只存中短期状态；
- active context：只存当前行业/任务细节；
- devlog：只存历史，不属于默认启动上下文。

具体行业经验只有在被提炼成跨行业方法后，才允许进入 Method Core。

如果任务是修改 handoff 机制本身，再读 `docs/development/session-handoff-protocol.md`。否则不要为了“理解得更完整”主动加载全部历史。
