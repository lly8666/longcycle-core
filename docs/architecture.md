# Longcycle 产业记忆核心架构

本文定义 `longcycle-core` 的长期架构方向，并明确区分当前已实现能力与下一阶段建设目标。

Longcycle 不是“爬虫 + LLM + 数据库”，也不是自动生成研报的系统。它的目标是建立一个可以跨十年以上时间回放的产业记忆：既保存现实发生了什么，也保存人在当时对未来怎么判断、为什么这样判断，以及后来结果如何。

## 1. 核心问题

周期研究最危险的偏差不是缺数据，而是后见之明。

如果数据库只保存最终结果，研究者回看历史时会自然产生错觉：

> 既然后来结果如此明显，当时为什么没有人看到？

真正可复盘的历史至少需要三条时间线：

```text
Reality      当时真实发生了什么
Expectation  当时的人认为未来会发生什么，为什么
Outcome      后来实际发生了什么，预期与现实为何偏离
```

因此 Longcycle 的首要目标不是“分析得更复杂”，而是让这三条时间线足够真实、连续、可比较、可追溯和可回放。

## 2. 架构原则

### 2.1 原文先于结构化数据

所有可发布事实和判断都必须能回溯到已归档原文和精确 locator。AI 总结不能成为唯一证据。

### 2.2 来源表达与系统结论分离

来源说过什么是历史事实，系统采用什么是研究结论。两者必须分表保存。

事实层继续使用：

```text
fact_assertion
→ reconciliation
→ resolution
→ canonical_fact_version
```

认知层使用：

```text
judgment_assertion
→ rationale / relation
→ expectation_snapshot
→ outcome_evaluation
```

一个 judgment 不能因为很多人都这么认为就被升级为 canonical fact。

### 2.3 point-in-time 是硬约束

系统必须能够回答：

> 站在某一个历史日期，只使用当时已经公开或市场可知的信息，可以看到什么？

因此：

- 文档有 `first_known_at`；
- 事实有现实有效时间与系统记录时间；
- judgment 有 `first_known_at` 和未来目标时间；
- 共识 snapshot 有 `knowledge_cutoff`；
- 派生研究不得读取 cutoff 之后的数据。

### 2.4 历史只追加，不覆盖

事实修订、项目延期、预测修正、观点撤回都必须以新版本或新关系表示。

例如：

```text
2024-03 管理层：预计 2025Q2 投产
2024-11 管理层：延期至 2025Q4
2025-08 管理层：再次延期至 2026Q1
2026-02 Reality：实际投产
```

四条记录都必须永久存在。

### 2.5 可比性优先于覆盖量

同一个名词不代表同一个事实。现货/长协、含税/未税、设计产能/有效产能、不同规格、不同地区和不同统计范围不能自动互证。

十年不可比的数据不如三年严格可比的数据。

### 2.6 先保存产业记忆，再做复杂分析

上层第一阶段只需要简单、可解释的比较：

```text
当时预期 - 后来实际
新增产能 - 实际投产
利润位置 - 后续资本开支
库存位置 - 后续价格变化
项目公告时间 - 实际达产时间
```

只有当历史样本足够真实后，才值得做更复杂模型。

## 3. 总体分层

代码仍采用端口—适配器结构：

```text
domain
  不依赖基础设施的不可变领域对象

ports
  Source / Archive / Model / Repository / Queue / Checkpoint / EventSink / Telemetry

application
  采集、归档、抽取、归一、事实调和、判断保存、共识聚合、后验评价、调度

adapters
  HTTP/本地来源、PostgreSQL、文件/S3、模型供应商、解析器、遥测
```

数据库按责任继续划分为四个 schema：

```text
core      稳定身份和语义目录
evidence  原文、版本、解析产物和证据
research  Reality + Expectation + Outcome
ops       任务、审计、成本、复核和运行控制
```

其中 `research` 不再只表示“可信事实”，而是完整的产业研究记忆层。

## 4. 数据流

长期主路径：

```text
来源发现
  ↓
获取原文
  ↓
内容寻址归档
  ↓
解析 / OCR / 表格结构化
  ↓
证据片段
  ├───────────────┐
  ↓               ↓
事实抽取          判断/预期抽取
  ↓               ↓
归一与可比性      speaker / horizon / rationale 归一
  ↓               ↓
事实调和          judgment append-only 保存
  ↓               ↓
可信事实版本      point-in-time expectation snapshot
  └───────┬───────┘
          ↓
   Reality vs Expectation
          ↓
   outcome evaluation
          ↓
简单可解释的周期研究
```

AI 可以参与“读”和“提取”，不能直接决定 truth，也不能直接改写历史判断。

## 5. Reality：事实时间线

当前事实主路径已经基本实现。

### 5.1 已实现

`CollectionPipeline.ingest()` 当前完成：

```text
SourcePlugin.fetch
→ ArchiveStore.put_if_absent
→ save_document
→ ModelGateway.extract
→ evidence consistency validation
→ AssertionNormalizer.normalize
→ save immutable extraction
→ save EvidenceFragment / FactAssertion
→ Reconciler.reconcile
→ review / conflict / trusted
→ processing completion
```

系统已经具备：

- SHA-256 内容寻址归档；
- 不可变 extraction / evidence / assertion；
- 可比维度；
- valid time；
- predicate-specific reconciliation policy；
- high-impact 事实复核；
- stable identity 与幂等重放；
- PostgreSQL queue / lease / checkpoint / outbox 基础设施。

### 5.2 Reality 的长期重点

优先把真正决定周期的历史做深，而不是增加大量弱相关字段：

- 价格和价差；
- 产能、有效产能、产量和利用率；
- 库存；
- 需求、订单和出口；
- 行业利润和成本；
- 项目宣布、审批、开工、延期、投产、爬坡和退出；
- 资本开支；
- 供给事故、政策、贸易和技术变化；
- 企业与产业链关系。

## 6. Expectation：认知时间线

这是下一阶段最重要的新增能力。

### 6.1 Judgment 不是 Fact

`research.judgment_assertions` 保存“某人在某一时点表达的判断”。

一个 judgment 至少包含：

```text
speaker
speaker role / affiliation
first_known_at
subject / industry
topic
judgment kind
future target time
point/range/date/direction/text value
expressed probability
source evidence
```

`judgment_kind` 区分：

- forecast：预测；
- target：目标；
- guidance：管理层指引；
- scenario：情景假设；
- probability：概率判断；
- risk：风险判断；
- thesis：逻辑判断；
- commitment：行动承诺；
- consensus_statement：来源直接表达的“市场共识”。

这一区分非常重要。例如“计划 2027 年达到 100 万吨产能”不是“预测市场 2027 年需要 100 万吨”。

### 6.2 判断的理由必须结构化

`judgment_rationales` 保存：

- premise：事实前提；
- mechanism：因果机制；
- condition：成立条件；
- risk：风险；
- caveat：限定条件；
- counterargument：反方论据。

每个 rationale 可以连接原始 evidence、已有 FactAssertion 或其他 Judgment。

这样未来复盘可以回答：

> 判断错在数字，还是错在某个假设？

### 6.3 判断修订不覆盖

`judgment_relations` 表示：

```text
revises
reaffirms
withdraws
narrows
widens
depends_on
supports
contradicts
```

一个人的观点历史本身就是产业历史。

## 7. 共识不是事实

多个观点可以聚合形成 `expectation_snapshots`，但 snapshot 仍是派生研究对象。

每个 snapshot 必须保存：

- `knowledge_cutoff`；
- 聚合方法和 producer version；
- 纳入的 judgment；
- 权重；
- 点值/区间/方向；
- 离散度；
- 置信度。

禁止直接保存一个“当前市场预期”并不断 UPDATE，因为这样会失去共识随时间演变的历史。

## 8. Outcome：后来到底发生了什么

当目标时间过去，并且 Reality 层形成可信事实后，系统可以产生 `judgment_outcome_evaluations`。

评价对象保持独立，因为 canonical facts 未来仍可能修订。

可保存：

- numeric error；
- relative error；
- timing error；
- direction correct；
- realized / partially realized / not realized；
- 后验解释。

Outcome 的目标不是给人打分，而是积累产业常识。

例如：

```text
某公司项目投产 guidance 平均乐观 7 个月
高利润阶段行业需求共识平均高估 6 个百分点
某类审批项目从公告到有效供给的中位时长为 31 个月
```

这些结论必须可以下钻回最初的原文和当时的 judgment。

## 9. 双时间系统

Longcycle 至少存在四种不能混淆的时间：

### Reality

- `valid_from / valid_to`：现实事实适用时间；
- `source_published_at`：来源发布时间；
- `first_known_at / market_known_at`：当时最早可知时间；
- `system_from / system_to`：系统采用该 canonical 版本的时间。

### Expectation

- `first_known_at`：判断何时进入当时信息集；
- `target_at` 或 `target_from / target_to`：判断针对哪个未来时点；
- `knowledge_cutoff`：共识或派生分析允许使用的信息截止时间。

因此一句“2024 年 6 月预计 2026 年需求达到 100”必须同时保留 2024 和 2026 两个时间语义。

## 10. 同步 Pipeline 与分阶段 Pipeline

当前有两条执行方式：

1. `CollectionPipeline.ingest()`：完整可运行的同步单文档路径；
2. `PipelineDispatcher`：带 checkpoint 和 fan-out 的分阶段路径。

长期原则是：**不能形成两套业务实现。**

应逐步抽出共享、幂等的 application primitives：

```text
archive_document
parse_document
extract_facts
extract_judgments
normalize_fact_assertions
reconcile_facts
persist_judgments
build_expectation_snapshot
evaluate_outcomes
```

同步 pipeline 和 worker/dispatcher 都只做 orchestration。

## 11. 当前实现边界

截至本设计：

### 已实现

- `core/evidence/research/ops` 四层数据库；
- 原文内容寻址；
- fact assertion / evidence / reconciliation / canonical fact；
- 价格、指标、产能项目、事件、公司敞口和周期快照表；
- PostgreSQL queue、lease、checkpoint、scheduler、outbox；
- 本地与受限 HTTP SourcePlugin；
- 离线测试 ModelGateway；
- 主要幂等和不可变约束。

### 本分支新增数据库设计

- `judgment_assertions`；
- `judgment_evidence`；
- `judgment_rationales`；
- `judgment_relations`；
- `expectation_snapshots`；
- `expectation_snapshot_members`；
- `judgment_outcome_evaluations`。

### 尚未实现的应用能力

- 生产 AI 连接器；
- 通用 PDF/OCR/Excel 解析；
- judgment extraction target 与 normalizer；
- speaker identity resolution；
- expectation snapshot builder；
- outcome evaluator；
- 默认完整 stage handler graph；
- 外部 API / 网页；
- Outbox relay 与真实 telemetry。

数据库结构先定义长期语义，但应用实现必须通过真实行业样本驱动，而不是继续空想扩展。

## 12. 下一阶段的架构验收标准

不是“模块是否足够多”，而是一个真实行业能否完成以下复盘：

1. 选择一个历史日期 T；
2. 只读取 `known_at <= T` 的事实和判断；
3. 展示当时价格、利润、库存、产能、项目和需求状态；
4. 展示当时主要管理层、分析师和产业参与者对未来的判断；
5. 展示这些判断背后的理由；
6. 向前推进时间，看到观点如何修订；
7. 最后与实际结果比较；
8. 所有结论都能回到原文证据。

如果这条路径跑不通，再多基础设施都不能算 Longcycle 的核心能力完成。
