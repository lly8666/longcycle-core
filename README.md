# Longcycle Core

行业长期记忆的数据库与采集内核。

Longcycle 的目标不是自动生成更多研报，而是保存一个行业最关键、最真实、可回放的历史：

```text
Reality      当时真实发生了什么
Expectation  当时的人认为未来会发生什么，为什么
Outcome      后来实际发生了什么，预期与现实为何偏离
```

同时允许高级模型已有知识进入一个**永远不可直接发布的历史侦察层**，用于尽可能恢复“我们应该去找哪些历史”，再由原始资料完成最终取证。

核心认识：

> **过去的资料恢复和今天的资料采集不是同一个问题。**
>
> 对历史：`memory-first, evidence-final`。
>
> 对当下：`source-first, archive-now`。

历史互联网天然残缺、旧网页难搜、附件丢失、术语变化、搜索结果偏新；因此不能指望低成本 Agent 从一个宽泛指令自动搜出完整历史。高级模型应先通过多轮正交 recall 尽可能建立产业历史目录和长尾线索，再让高级模型/低成本 Agent 逐条寻找 primary source。

对于今天仍在线的资料，则应主动持续归档，避免未来再做历史抢救。

当前仓库只做后端。网页端不在本仓库范围内。

## 核心原则

1. **原文先于结构化数据。** 所有可发布事实和判断都必须能回溯到归档原文和精确 locator。
2. **AI 只能产生候选。** AI 不能直接写可信事实，也不能把多人观点一致当成现实真相。
3. **事实与判断分开。** `FactAssertion` 保存“来源声称现实是什么”；Judgment 保存“某人在当时如何判断未来”。
4. **历史不可重写。** 修订、延期、改口、统计更新采用 append-only，不覆盖旧版本。
5. **不让后见之明污染历史。** 文档、事实、判断和派生结果都保留 point-in-time 时间语义。
6. **可比性优先于数据量。** 产品规格、地区、税费、运费、合同、单位、统计范围和时间口径不完整时，不自动互证或判冲突。
7. **理由是一等数据。** 预测数字之外，还保存 premise、mechanism、condition、risk 和 caveat。
8. **模型记忆可以挑战档案，但不能覆盖档案。** Memory Lead 永远不是 Fact/Judgment。
9. **搜不到不是反证。** 对历史任务，`not_found != false`；只能得到 `not_yet_verified`。
10. **搜索结果数量不是证据强度。** 十篇转载可能仍然只有一个原始信息源。
11. **权威必须与 claim scope 匹配。** 公司公告、政府统计、券商报告分别只对其有资格证明的问题具有高证明力。
12. **先保存历史，再做复杂分析。** 复杂预测模型不是当前优先级。

## 双轨研究架构

### A. Historical Recovery：高级模型先建立目录

```text
Memory Exhaustion Campaign
→ Sealed Blind Memory Atlas
→ High-model Self Verification
→ Delegated Verification Tasks
→ archived primary material
→ authority audit
→ Fact / Judgment
```

这里不是只问高级模型一次“你记得什么”。

模型需要通过多轮互相正交的 pass，持续激活不同知识区域：

- 时间切片；
- 产业链切片；
- actor exhaustion；
- metric exhaustion；
- 定价与合同机制；
- 有效供给工程瓶颈；
- 库存位置；
- 资本循环；
- 技术与单位耗用；
- 当时叙事；
- 旧称和历史检索词；
- 失败/取消/延期项目；
- reverse causality；
- 跨产业关联；
- counterfactual；
- negative space；
- saturation review。

第一阶段禁止看本轮搜索结果，封存 blind atlas；之后同一个高级模型可以进入新的 `self_verification` run 自己搜索，把模糊记忆转化成更准确的项目名、旧称、报告名和 primary-source 目标，但不能回头改写 blind recall。

低成本 Agent 的角色因此主要是**证据工程**，而不是自由研究。

### B. Current Collection：今天能保存的今天保存

```text
source watchlist
→ periodic/event-driven discovery
→ archive original HTML/PDF/attachment immediately
→ Reality / Expectation role detection
→ extract / reconcile / review
→ source inventory expansion
```

当前资料采集必须有细 SOP：检查固定高价值来源、识别新增文件、归档附件、追踪修订、保存 guidance/预测、更新 source watchlist。

目标是以后不再依赖搜索引擎抢救今天的历史。

## 数据架构

PostgreSQL 16+ 使用四个 schema：

```text
core      稳定身份、分类、产品、设施、单位和 predicate 语义
evidence  原文、抓取、Blob、文档版本、artifact、证据、来源 authority profile
research  Reality + Expectation + Outcome + unsourced Model Memory Leads
ops       队列、租约、断点、复核、验证任务、Outbox、成本和审计
```

### Reality

当前已经实现完整事实链：

```text
来源发现
→ 获取并归档原始字节
→ 证据片段
→ FactAssertion
→ 归一与可比性
→ 质量评分与冲突判断
→ Resolution
→ Canonical Fact Version
```

### Expectation

设计中的 point-in-time 认知链：

```text
JudgmentAssertion
→ Evidence
→ Rationale
→ Revision / Reaffirm / Withdraw
→ Expectation Snapshot
```

Judgment 保存谁在什么时候、对哪个未来时点、以什么形式作出判断，并保留理由和条件。

### Outcome

```text
prediction / guidance / target
        ↓
canonical outcome
        ↓
error / timing / direction / explanation
```

用于积累产业常识，而不是给分析师排名。

### Model Memory / Historical Lead Layer

```text
ModelMemoryCampaign
→ ModelPriorRun(s)
→ ModelMemoryLead(s)
→ LeadRelation graph
→ Campaign Seal / coverage map
→ Self Verification / delegated search
→ Evidence links / disagreement
```

无论模型有多强，Memory Lead 没有直接发布成 Fact 的路径。

如果模型记忆只和普通二手网页冲突，保持 unresolved 并继续找 primary source；若 matching primary source 明确反驳，则保留这次错误记忆并由正常 Evidence pipeline 建立历史；若权威一手来源彼此冲突，则保留 authoritative conflict。

## 模型更新后的回补

高级模型版本变化被视为新的 **research instrument vintage**，不是覆盖旧模型结果。

```text
Old Model Memory Atlas
→ New Model Memory Exhaustion Campaign
→ Lead Diff: known / refined / novel
→ Archive Gap Diff
→ Backfill Task Queue
```

每次记录模型/provider/version、声明 knowledge cutoff（若可得）、protocol、manifest 和原始输出。

新模型新增的历史记忆可以重新打开过去已经“做过”的年份；旧 atlas 和错误记忆都不删除。这样 Longcycle 可以随着基础模型训练资料更新逐步回补历史盲点。

## 第一真实行业：新能源锂电池

第一个完整样本确定为新能源锂电池产业链，中国为主，第一轮 `2019-01-01 → 2026-12-31`，必要时向 2015–2018 回填。

覆盖：

- 上游锂矿、盐湖、锂精矿和锂盐；
- LFP、三元、负极、隔膜、电解液等材料；
- 动力/储能电池和主要电池企业；
- 新能源汽车与储能；
- 项目宣布、审批、开工、延期、投产、爬坡、取消；
- 价格、利润、库存、产能、有效产能、产量、装车、销量、资本开支；
- 管理层、券商、协会、政府和产业参与者当时的判断与理由；
- 定价机制、合同变化、认证、设备、公用工程、库存位置等“普通行业数据库不容易保存”的机制历史。

锂电已经有一份固定 Memory Exhaustion Manifest，用于让当前高级模型以及未来新模型跑同一套记忆召回基准。

## 当前实现边界

已实现/已落库设计：

- PostgreSQL 四层数据模型；
- S3/R2/MinIO 或本地 SHA-256 内容寻址原文库；
- 可插拔 Source/Model/Repository/Queue/Checkpoint/EventSink；
- 原文归档 → Evidence → FactAssertion → normalization → reconciliation → trusted/conflict/review；
- predicate、维度 schema、单位换算和分 predicate 调和策略；
- PostgreSQL 至少一次任务队列、lease、heartbeat、retry、dead-letter、checkpoint；
- price/capacity/output/project/event/exposure/cycle 数据结构；
- Judgment / Expectation / Outcome 数据库设计；
- Model Prior / Memory Lead / authority / disagreement 数据库设计；
- Memory Campaign / Campaign Seal / Coverage / Model Refresh / Verification Task 数据库设计；
- deterministic memory-vs-evidence adjudication；
- blind/gap prompt isolation；
- memory-campaign saturation 与 verification-depth application primitives；
- 锂电采集协议、工作包、Memory Exhaustion Manifest 和机器回传 Schema。

尚未实现：

- 生产 AI connector；
- 通用 PDF/OCR/Excel parser；
- judgment extraction target 与 speaker resolution；
- expectation snapshot builder；
- judgment outcome evaluator；
- 生产 `MemoryPriorGateway` adapter 和完整 campaign orchestration；
- 高级模型 self-verification 的搜索/归档 orchestration；
- Current source watchlist 的完整 scheduler/connector 集合；
- source authority profile 管理工作流；
- 对外 API / Web；
- Outbox relay 和真实 telemetry。

`JsonFixtureGateway` 仍是离线黄金测试适配器，不是生产模型。

## 研究 Agent 的最低要求

历史验证任务不能因为“搜了几个结果”就结束。

默认 minimum search depth 包括：

- 至少 6 类不同 query family；
- 至少检查 3 类不同来源；
- 至少检查最可能的 primary domain；
- 二手来源有 citation 时必须追一次原始 citation；
- 高影响 lead 至少做一次反向查询；
- 只有 primary verified / primary contradicted / exhausted but unresolved 三类结果可以正常交工。

## 文档入口

- [总体架构](docs/architecture.md)
- [开发方案](docs/development-plan.md)
- [Schema 与时间契约](docs/schema-contracts.md)
- [锂电池历史资料采集方案](docs/research/lithium-battery-collection-plan.md)
- [Research Agent SOP](docs/research/research-agent-sop.md)
- [采集 Agent 基础契约](docs/research/agent-collection-contract.md)
- [高级模型记忆榨取协议](docs/research/model-memory-exhaustion-protocol.md)
- [模型记忆与历史缺口审计](docs/research/model-memory-audit.md)
- [模型更新后的历史回补](docs/research/model-refresh-backfill.md)
- [Claim-scoped 来源权威策略](docs/research/source-authority-policy.md)
- [锂电 Memory Exhaustion Manifest](docs/research/lithium-battery-memory-exhaustion-manifest.json)
- [锂电低成本 Agent 工作包](docs/research/lithium-battery-work-packages.json)
- [Agent 文档回传 Schema](docs/research/agent-document-record.schema.json)

## 当前下一步

1. 先用高级模型跑锂电 2019–2026 Memory Exhaustion Campaign，生成并封存第一版 Memory Atlas；
2. 让高级模型对 atlas 中高价值 lead 自己做第一轮 primary-source 定位；
3. 将剩余 lead 编译成严格 verification task packet，交给低成本 Agent 深挖；
4. 同时启动锂电 Current source watchlist，从今天开始主动保存未来历史；
5. 用第一批真实材料反推 judgment extraction、项目实体语义和来源 authority profile；
6. 以后每次高能力模型知识版本显著更新，重新跑 benchmark manifest，自动产生历史 backfill diff。

最终验收问题：

> **站在任意历史日期，只使用当时能知道的资料，我们能否理解当时为什么形成那些决策和预期；站在今天，我们是否还能看见这段历史中那些后来被搜索引擎、叙事和结果掩盖掉的关键机制？**

## 当前验证边界

离线测试覆盖现有事实采集、归一/调和、队列/worker、Memory Lead authority adjudication、blind/gap prompt isolation、Memory Campaign saturation 和低成本 Agent minimum search depth 规则。

真实 PostgreSQL/S3 集成测试仍是上线前关键工作；当前仓库也还没有 CI workflow 对这些新提交给出线上测试结果。