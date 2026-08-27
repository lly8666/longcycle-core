# 2026-08-21 Memory Campaign 开发日志

> 本日志记录可公开、可复核的工程决策、实验观察、提示词版本变化、数据产出和下一步动作。它不记录模型私有推理链；详细内部思考不作为产品数据保存。

## 00:53 - 用户目标

开始真实运行新能源锂电池历史 Memory Exhaustion Campaign，同时：

- 研发过程持续提交到 GitHub；
- 历史采集优先榨取高级模型已有产业记忆，再逐条取证；
- 观察真实记忆输出，实时修改提示词/Schema/任务拆分；
- 解决锂电细分节点非常多、单次上下文有限、跨上下游又互相关联的问题；
- 为未来模型知识更新后的历史回补保留稳定接口。

## 01:00 - 决策：原子分片，不使用三个超大上/中/下游任务

### 问题

如果一次让高级模型回忆完整上游或完整中游：

1. 头部公司和著名事件会占据注意力，长尾节点容易消失；
2. 输出量大，单次聊天/调用存在上下文和执行时间不确定性；
3. 一个节点的输出会对后续节点形成提示锚定，降低独立召回价值；
4. 中途失败时难以判断哪些部分已完整覆盖。

### 方案

采用 `atomic shard -> seal -> stitch`：

```text
固定 ontology / period / protocol
        ↓
细分节点 A blind shard ──→ seal
细分节点 B blind shard ──→ seal
细分节点 C blind shard ──→ seal
        ...
        ↓
只读 lead index / coverage matrix
        ↓
bridge & stitching passes
        ↓
跨链关系 leads
```

Blind shard 之间：

- 不共享彼此实际输出；
- 只共享固定产业链结构、时间范围和统一 prompt protocol；
- 每个 shard 独立保存；
- 每完成一个 pass 就立即 commit，天然支持断点续跑。

### 跨链信息如何不丢

不在 blind 阶段强行让所有节点互相影响，而使用两类后置任务：

1. `bridge theme pass`：价格/定价、库存、资本开支、项目投产、技术替代、贸易、政策、能源成本等跨节点主题；
2. `stitch pass`：只读取已封存 lead 的压缩索引，寻找 predecessor/successor/possible_cause/possible_effect/cross_chain_link。

这样可以同时保留独立召回和跨产业链关联。

## 01:05 - 节点分层原则

不能把所有材料都当同等一级 shard，否则会迅速膨胀到几十个并行方向。

第一版分两层：

### Tier A：周期主节点，必须独立完整 recall

- 硬岩锂矿/锂辉石资源
- 盐湖/卤水锂资源
- 锂精矿与资源端定价/贸易
- 碳酸锂/氢氧化锂冶炼与转换
- LFP/磷酸铁
- 三元前驱体/三元正极
- 石墨负极/硅基负极
- 隔膜
- 电解液/LiPF6
- 电芯制造与 Pack
- 动力电池需求
- 储能电池需求
- 新能源汽车终端
- 电池回收/二次资源

### Tier B：卫星节点，先由主节点/bridge pass 触发，再决定是否升格

- 铜箔/铝箔
- PVDF/粘结剂
- 导电剂
- NMP
- 磷酸/铁源/镍钴锰化工中间品
- 电池设备
- BMS/热管理等 Pack 配套
- 两轮车/工具/消费电池等非车非储能需求

Tier B 若满足任一条件则升格独立 shard：

- 在某一周期成为供给瓶颈；
- 对成本/利润分配影响显著；
- 出现大规模资本开支/产能周期；
- 对当时市场叙事或需求预期影响显著；
- Memory Atlas 中出现多个高重要度 lead。

## 01:10 - 关于单次聊天/调用时限

不假设任何固定上限。系统设计必须允许任意一个 pass 在完成后立即持久化，并允许下一次调用只根据 `campaign_id + shard_id + pass_id + checkpoint` 继续。

原则：

- 不要求一个聊天完成整个行业；
- 不要求一个聊天完成一个大 shard；
- 单次 pass 应产生有限、原子化 lead；
- 每个 pass 输出独立文件并带 prompt/version/digest；
- 后续任务读取压缩 index，不需要重新加载所有原始文本。

## 01:15 - 第一轮实验计划

先跑最能暴露 prompt 问题的两个相邻 shard：

1. `UP-HARDROCK`：硬岩锂矿、锂辉石、澳洲/非洲/中国资源项目；
2. `UP-CHEMICALS`：碳酸锂/氢氧化锂转换、冶炼、成本、利润、产能和库存。

原因：两个 shard 关联很强，但事实语义不同，适合验证“独立 recall + 后置 stitch”是否有效。

第一轮先使用现有 protocol 的核心规则，然后根据输出观察是否出现：

- 只列著名事件；
- 一个 lead 塞太多 claim；
- 精确数字/日期伪精确；
- 记忆与推断混在一起；
- 缺少可搜索旧称/actor/source hook；
- 只给结论，没有可证伪条件。

发现问题后修改 prompt v2，再跑同类 pass 对比。

## 01:25 - 实验 1：UP-HARDROCK / recall-v1

首批 blind output 已落库前文件，共 30 条 Memory Lead，未使用网页或相邻 shard 结果。

明显有效的召回类型包括：

- Wodgina / Altura-Ngungaju / Bald Hill 等上一轮低谷退出与后续重启；
- Mt Cattlin 等因为公司主体更名导致的历史搜索断裂；
- Zimbabwe 本地加工政策、Arcadia/Bikita/Zulu/Sabi Star 等非洲资产；
- Goulamina/Manono 等政府、矿权、权益争议使巨大资源长期不能转化为供给；
- Snowway/德扯弄巴等国内资源争夺线索；
- 精矿公式定价滞后、concentrator train、品位/回收率等公开研报摘要不一定主动覆盖的机制。

结论：Memory-first 作为历史目录生成器有明显信息增益。

## 01:30 - Prompt v1 问题

真实输出暴露：

- 事件和因果机制仍会被塞进一条 lead；
- `recalled/inferred/mixed` 太粗；
- 所有权、日期、项目阶段等不确定项仍埋在自由文本；
- 只有支持性搜索，没有明确反证路径；
- 对“为什么普通搜索容易漏掉”缺少结构化字段；
- 宜春锂云母自然闯入硬岩 shard，说明 scope drift 有时是有价值的 satellite-shard 信号。

因此 prompt 升级到 v2，并新增 structured uncertainty / falsification / search archaeology。

## 01:40 - 实验 2：UP-CHEMICALS / recall-v2

第二个 blind shard 独立运行，不读取 UP-HARDROCK 输出，共 28 条。

v2 的改善：

- `uncertain_fields` 能明确指出 ownership/date/counterparty 等精确度风险；
- 每条都有 `disconfirmation_queries`，低级 agent 不再只能找支持材料；
- `why_search_may_miss_it` 对公司更名、合同不公开、地方环保文件、方法口径等很有用；
- `satellite_trigger` 自然产生多个后续节点：`SAT-LEPIDOLITE`、`UP-CONCENTRATE`、`LOOP-RECYCLING`、`BRIDGE-INVENTORY`、`BAT-CELL-PRICING` 等。

这验证了动态节点升级比一开始人为列出全部细分领域更合理。

## 01:45 - 首次真实 Schema failure

CH-008 把 `technical_specification` 输出到了 `lead_kind`；这个值实际属于 `claim_scope`。

重要结论：

> Prompt 再明确，也不能把模型 JSON 当可信结构化输入。

新正式路径：

```text
raw model JSONL
→ typed candidate validation
→ validation failure retained
→ structural-only repair prompt
→ validate again
→ accepted candidate set
→ persistence
```

禁止静默语义纠错。原始错误输出永久保留，以评估模型/提示词质量。

## 01:50 - 开发修正

已新增：

- migration `0016_memory_lead_recall_quality.sql`；
- `MemoryBasis` / `PrecisionRisk` / `EntityResolutionState`；
- `failure_dead_end` lead kind；
- `uncertain_fields`、旧称、搜索遗漏原因、反证查询、satellite trigger；
- campaign run 的 `shard_id`；
- typed `MemoryLeadCandidate` validator；
- structural repair prompt；
- 对应单元测试；
- recall prompt v3，显式枚举并要求 JSONL 逐条自检。

## 当前判断

从两次 blind run 看，最优采集结构不是固定‘上中下游树’，而是：

```text
Tier-A 主节点 blind shards
+ blind bridge themes
+ 动态 satellite triggers
+ validation/repair
+ seal
+ compressed-index stitching
+ 高级模型 self-verification
+ 低级 agent 逐 lead 取证
```

下一实验重点不再是单纯多产出 lead，而是验证 v3 的结构合规率，并决定哪些 satellite trigger 需要立即升格独立 shard。