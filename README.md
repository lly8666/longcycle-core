# Longcycle Core

行业长期记忆的数据库与采集内核。

Longcycle 的目标不是自动生成更多研报，而是保存一个行业最关键、最真实、可回放的历史：

```text
Reality      当时真实发生了什么
Expectation  当时的人认为未来会发生什么，为什么
Outcome      后来实际发生了什么，预期与现实为何偏离
```

拉长时间以后，研究者应能依靠可比较的历史、当时的预期和简单常识识别当前风险与机会，而不是依赖不可解释的黑盒预测。

当前仓库只做后端。网页端不在本仓库范围内。

## 核心原则

1. **原文先于结构化数据。** 所有可发布事实和判断都必须能回溯到归档原文和精确 locator。
2. **AI 只能产生候选。** AI 不能直接写可信事实，也不能把多人观点一致当成现实真相。
3. **事实与判断分开。** `FactAssertion` 保存“来源声称现实是什么”；Judgment 保存“某人在当时如何判断未来”。
4. **不让后见之明污染历史。** 文档、事实、判断和派生结果都保留 point-in-time 时间语义。
5. **修订只追加，不覆盖。** 项目延期、数据修订、观点改口和预测撤回都形成新版本或关系。
6. **可比性优先于数据量。** 产品规格、地区、税费、运费、合同、单位、统计范围和时间口径不完整时，不自动互证或判冲突。
7. **理由是一等数据。** 预测数字之外，还要保存 premise、mechanism、condition、risk 和 caveat。
8. **先保存历史，再做复杂分析。** 复杂模型不是当前优先级。

## 数据架构

PostgreSQL 16+ 使用四个 schema：

```text
core      稳定身份、分类、产品、设施、单位和 predicate 语义
evidence  原文、抓取、Blob、文档版本、artifact、证据、抽取运行
research  Reality + Expectation + Outcome
ops       队列、租约、断点、复核、Outbox、成本和审计
```

### Reality

当前已经实现完整的事实链：

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

可信事实保留现实有效时间与系统采用时间；来源断言和系统采用结论分别保存。

### Expectation

本设计新增 point-in-time 认知模型：

```text
JudgmentAssertion
→ Evidence
→ Rationale
→ Revision / Reaffirm / Withdraw
→ Expectation Snapshot
```

Judgment 保存谁在什么时候、对哪个未来时点、以什么形式作出判断，并保留其理由和条件。

### Outcome

目标期结束后，可以把历史 Judgment 与后来的可信 Reality 配对：

```text
prediction / guidance / target
        ↓
canonical outcome
        ↓
error / timing / direction / explanation
```

这个过程的目标不是给分析师排名，而是积累产业常识，例如项目通常延期多久、景气高点需求预期通常高估多少、哪些前提最容易失效。

## 当前实现边界

已实现：

- PostgreSQL 四层数据模型；
- S3/R2/MinIO 或本地 SHA-256 内容寻址原文库；
- 可插拔 `SourcePlugin`、`ModelGateway`、Repository、Queue、Checkpoint 和 EventSink；
- 本地文件与受限 HTTP 采集源；
- 原文归档 → 证据 → 抽取 → FactAssertion → 归一 → 调和 → 可信事实/冲突/复核；
- predicate、维度 schema、单位换算和分 predicate 调和策略快照；
- PostgreSQL 至少一次任务队列、租约、心跳、重试、死信、断点和确定性 fan-out；
- 价格、产能、产量、项目、事件、上市公司敞口、上下游关系和周期快照数据库结构；
- point-in-time Judgment / Expectation / Outcome 的数据库迁移设计；
- 新能源锂电池第一行业样本的采集协议、搜索方案、任务包和机器回传 Schema。

尚未实现：

- 生产 AI 连接器；
- 通用 PDF/OCR/Excel 解析器；
- judgment extraction target 与 speaker resolution；
- expectation snapshot builder；
- judgment outcome evaluator；
- 默认全阶段 handler 装配；
- 对外 API 或网页；
- Outbox relay 和真实 telemetry。

`JsonFixtureGateway` 仍然只是离线黄金测试适配器，不是生产模型。

## 代码结构

```text
migrations/                   PostgreSQL 迁移；数据库是真实结构化数据源
src/longcycle/domain/         不可变领域对象与枚举
src/longcycle/ports/          可替换端口契约
src/longcycle/application/    采集、归一、调和、调度、Worker、工作流
src/longcycle/adapters/       HTTP/本地源、PostgreSQL、S3/文件、测试模型
docs/                         架构、Schema、开发路线、采集 SDK、运维说明
tests/                        无网络确定性测试
```

## 本地快速验证

要求 Python 3.11+：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
longcycle doctor
longcycle source plugins
longcycle demo
python -m unittest discover -s tests -v
```

`longcycle demo` 当前运行事实采集链：本地 JSON → 原文归档 → 事实抽取 → 归一 → 调和。

## PostgreSQL 与对象存储

开发环境：

```powershell
Copy-Item .env.example .env
docker compose up -d postgres minio minio-init
docker compose run --rm migrate
```

或连接已有 PostgreSQL 16+：

```powershell
$env:LONGCYCLE_DATABASE_URL='postgresql://longcycle:longcycle@localhost:5432/longcycle'
pip install -e ".[postgres,s3]"
longcycle db upgrade
longcycle doctor --check-database
longcycle scheduler-tick
```

迁移使用会话级 advisory lock、逐文件事务和 SHA-256 校验；已应用迁移被修改时会拒绝继续。

## 当前第一行业：新能源锂电池

第一个真实行业样本已经确定为新能源锂电池产业链，中国为主，第一轮重建 `2019-01-01 → 2026-12-31`。

范围覆盖：

- 上游锂资源和锂盐；
- LFP、三元、负极、隔膜、电解液等中游材料；
- 动力/储能电池和头部电池企业；
- 新能源汽车与储能需求；
- 项目宣布、审批、开工、延期、投产和爬坡；
- 管理层、券商、协会和政府在各历史时点的预期与理由。

第一批采集不是让 Agent 写行业结论，而是让它们忠实寻找原始材料，并按统一协议回传。

## 下一阶段

当前优先工作变成：

1. 用第一批 Agent 建立锂电池 `Reality` 连续历史骨架；
2. 重建 2021–2023 周期关键阶段的 `Expectation` 时间线；
3. 挑高影响项目建立 `宣布 → 预计投产 → 修订 → 实际投产` revision chain；
4. 用真实采集结果反推 judgment extraction 和实体/项目语义，不继续无样本地扩平台；
5. 开始建立可重复的 historical snapshot，验证任一 cutoff 下都不会读到未来资料。

验收问题：

> **站在任意历史日期，只使用当时已经知道的信息，我们能否理解当时为什么会形成那些决策和预期，并在后来解释它为什么对或错？**

## 文档入口

- [总体架构](docs/architecture.md)
- [Schema 与时间契约](docs/schema-contracts.md)
- [开发方案：产业记忆优先](docs/development-plan.md)
- [锂电池历史资料采集方案](docs/research/lithium-battery-collection-plan.md)
- [采集 Agent 协议](docs/research/agent-collection-contract.md)
- [锂电池 Agent 工作包](docs/research/lithium-battery-work-packages.json)
- [Agent 文档回传 JSON Schema](docs/research/agent-document-record.schema.json)
- [采集插件 SDK](docs/collector-sdk.md)
- [运行、成本与安全](docs/operations.md)

## 当前验收

无需网络或数据库即可运行的单元测试覆盖内容寻址归档、来源安全、断言归一与可比性、冲突分流、同文档不同目标抽取、队列租约与死信、Worker 并发、断点重放和 Outbox 幂等。

真实 PostgreSQL/S3 集成测试仍然是上线前必须补齐的关键工作，特别是并发 reconciliation、lease 接管、部分提交、对象存储/数据库跨边界失败恢复，以及 point-in-time 无未来信息泄漏测试。
