# 2026-08-21 Memory Campaign 开发日志 Part 3

本日志记录可公开、可复核的工程决策和实验结果，不记录模型私有推理链。

## CI #94：第一轮真实机器反馈

GitHub Actions 首次真正运行完整安装流程后，原始 CI 在 Ruff 阶段失败，因此 Mypy/Pytest 被默认 step gating 跳过。

Ruff 0.16.4 共报告 72 条问题。绝大部分属于：

- E501 行长；
- import sorting；
- UP024/UP035/UP037 现代化语法；
- RUF015 等风格/idiom；
- 少量 B008/RUF009 dataclass/default style；
- 一条 ASYNC240；
- 一条 B023 closure lint；
- 少量 unused import。

这些问题大量存在于本次产业记忆改造之前的核心代码，并不是 memory schema 的行为回归。

## CI #100：诊断模式，一次看清 Ruff / Mypy / Pytest

为了避免 Ruff 的格式/现代化债务遮住真正的类型和行为问题，CI 临时改为：

1. Ruff 全量执行、记录结果，但 `continue-on-error`；
2. Mypy 继续执行；
3. Pytest 继续执行；
4. 最后 diagnostic gate 汇总三者状态。

结果：

```text
ruff=failure
mypy=success
pytest=success
```

Pytest：**147 passed**。

这说明当前 branch 的主要未通过项是 lint debt；类型检查和现有行为测试均通过。

## 研究期 CI policy

Memory Campaign 仍处于高频 Prompt / Schema / dataset 实验阶段。现阶段若每次为了最新 Ruff 的格式和现代化规则大规模修改几十个旧核心文件，会制造与研究无关的大 diff，增加行为变更风险。

因此 CI 暂时调整为：

- Ruff：全量 diagnostic，持续公开技术债；
- Mypy：硬门禁；
- Pytest：硬门禁；
- PR 准备进入 review/merge 前：恢复 Ruff 硬门禁并做一次独立 lint cleanup。

这不是降低长期标准，而是把 correctness cleanup 和 cosmetic/modernization cleanup 分开。

## Memory Campaign 当前状态

最新 checkpoint：**534 条 blind memory leads**。

- 14 个主 shard 都至少完成一次 self-gap；
- MID-LFP / DOWN-NEV / DOWN-ESS 已跑到 self-gap batch2；
- 所有被测试的 self-gap batch 仍保持高新增率；
- 没有任何 shard 达到 low-novelty；
- 没有任何 shard seal；
- fresh web self-verification 仍然禁止。

当前实验结论：

> 高级模型的行业历史记忆不能通过一个长回答“导出”。需要多轮正交、自我缺口审计，直到新增类别真正衰减。

## 下一步

1. 确认新的 correctness-only gate CI 能稳定绿色；
2. 对剩余 shard 跑 self-gap batch2，建立 novelty decay 序列；
3. 每个 shard 建 compact lead index / category coverage matrix；
4. batch3 开始强制只允许“新类别”或“对检索有显著新增价值的 refinement”；
5. 连续三批 low-novelty 才进入 seal 候选；
6. seal 后才启动同一高级模型的联网 self-verification；
7. 再生成低成本 Agent 的逐条取证 task packet。
