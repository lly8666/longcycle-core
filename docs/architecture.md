# Longcycle 数据与采集核心架构

本文描述 `longcycle-core` 当前代码和数据库迁移已经提供的能力，并说明新增采集源、存储、模型和任务阶段时必须遵守的边界。本文不把规划中的能力描述成已经上线的功能。

## 1. 当前定位

后端是一个面向行业周期研究的模块化 Python 核心，当前主要解决四件事：

1. 将来源发现和正文获取封装成可插拔的 `SourcePlugin`。
2. 先归档原文，再产生有原文定位的事实断言。
3. 对断言做单位归一、质量评分、冲突判断和复核分流。
4. 用带租约的至少一次任务队列和阶段检查点支持可恢复执行。

当前要求 Python 3.11 或更高版本。核心依赖只有 `httpx` 和 Pydantic；PostgreSQL 与 S3/R2 适配器是可选依赖。

## 2. 分层与依赖方向

代码遵循端口—适配器结构：

```text
domain                 不依赖基础设施的不可变领域模型
  ↑
ports                  Source、Archive、Model、Repository、Queue、Telemetry 等协议
  ↑
application            采集编排、归一、质量、调和、调度、Worker
  ↑
adapters               HTTP/本地来源、PostgreSQL、文件/S3、测试模型
```

依赖只能向领域层收敛。应用层不得直接依赖 boto3、psycopg、具体模型厂商或具体网站；这些实现都应位于 `adapters`，并通过 `ports` 注入。

主要扩展边界如下：

| 边界 | 协议 | 当前实现 |
| --- | --- | --- |
| 来源发现与获取 | `SourcePlugin` | `LocalFolderSource`、`HttpDocumentSource`、Python entry point 注册表 |
| 原文归档 | `ArchiveStore` | 本地内容寻址文件库、S3/R2 兼容对象库 |
| 结构化抽取 | `ModelGateway` | `JsonFixtureGateway` 用于离线测试和结构化 feed；`NoopModelGateway` 是占位类 |
| 研究数据持久化 | `ResearchRepository` | 内存、PostgreSQL |
| 任务队列 | `JobQueue` | 内存、PostgreSQL |
| 阶段检查点 | `CheckpointStore` | 内存、PostgreSQL |
| 事件落库 | `EventSink` | 内存、PostgreSQL Outbox；外部发布器尚未提供 |
| 可观测性 | `Telemetry` | `NullTelemetry`；真实遥测适配器尚未提供 |

`JsonFixtureGateway` 是确定性的测试/结构化输入适配器，不是生产 AI 连接器。`NoopModelGateway` 也不能替代生产连接器。生产模型供应商、OCR、通用 PDF/Excel/HTML 解析器目前没有实现。

## 3. 两条现有执行路径

### 3.1 同步单文档采集路径

`CollectionPipeline.ingest()` 是目前完整可运行的单文档路径。调用方先用插件执行发现，然后把一个 `DiscoveryItem` 交给管道：

```text
SourcePlugin.fetch
  → ArchiveStore.put_if_absent
  → ResearchRepository.save_document
  → 读取已有不可变 ExtractionEnvelope；没有时才调用 ModelGateway.extract
  → envelope 证据一致性校验
  → AssertionNormalizer.normalize
  → 原子选定并保存不可变 ExtractionEnvelope
  → 保存 EvidenceFragment / FactAssertion
  → Reconciler.reconcile
  → 保存 ReconciliationResult
  → 必要时创建 ReviewItem
```

这条路径已经实现抓取、归档、抽取、归一与调和，但不是数据库事务包裹的全有或全无工作流。各 Repository 写操作依赖自己的幂等语义来支持重放。

发现阶段不在 `CollectionPipeline.ingest()` 内。调用方负责：

1. 读取 `SourceDefinition`。
2. 由 `SourceRegistry` 创建插件。
3. 调用 `plugin.discover()`。
4. 为发现项创建任务，或直接调用 `ingest()`。

### 3.2 分阶段任务路径

`PipelineDispatcher` 提供通用的阶段执行、检查点和确定性 fan-out：

- `CollectionJob.stage` 指定阶段。
- 注册表为每个阶段提供 `(producer_version, handler)`。
- Dispatcher 根据阶段、payload、来源、行业和 producer version 计算输入哈希。
- 命中同一检查点时直接返回之前的 `StageResult`。
- `NextStage` 会生成稳定的子任务 ID 与幂等键，并继承父任务的 `trace_id`。

当前 `JobStage` 枚举包含：

```text
discover → fetch → archive → parse → extract → normalize → validate → reconcile → publish → derive
```

这些阶段的默认 handler 图尚未在项目中完成装配。配置 `PostgresOutboxEventSink` 后，Dispatcher 会把 `StageResult.emitted_events` 以稳定幂等键写入 `ops.outbox_events`；检查点重放也会补齐遗漏的下游任务和事件。将 Outbox 投递到外部消息系统的 relay 尚未实现，不能把“已落库”当成“已发布”。

`Worker` 已实现：

- 批量领取任务；
- 并发上限；
- 租约心跳；
- 成功确认；
- `RetryableJobError` 与 `PermanentJobError` 分流；
- 对未知异常做有界重试。

PostgreSQL 队列通过 `FOR UPDATE SKIP LOCKED` 抢占任务，并使用 `worker_id + lease_token` 防止过期 Worker 提交结果。

## 4. 数据库分区

SQL 迁移将数据划分为四个 schema。

### `core`

保存稳定目录与身份：分类体系、分类节点和边、实体、别名、标识符、实体关系版本、行业成员关系、产品和规格、设施、产线、上市证券、单位及换算版本。

组织、证券、设施和产线是不同实体，不能用一家上市公司的证券代码代替生产主体或工厂。

### `evidence`

保存来源和证据链：出版者、来源连接器、订阅、内容 Blob、逻辑文档、抓取记录、文档版本、衍生产物、证据片段、提示词版本、抽取 schema、模型定义和抽取运行。

对象正文不进入 PostgreSQL；`content_blobs` 保存对象库 bucket、key、SHA-256、长度和 MIME 元数据。文件系统与 S3/R2 适配器都使用：

```text
raw/sha256/<前两位>/<完整 sha256>
```

### `research`

保存事实与研究域：不可变断言、断言—证据关联、事实键、调和评估、冲突案例、解决决策、可信事实版本，以及指标序列、观测、产能项目、事件、财务敞口、行业关系和周期快照。

可信事实版本同时保存现实有效时间与系统记录时间。它与不可变断言分开，目的是保留“来源说过什么”和“系统当时采用了什么”两种历史。

### `ops`

保存运行控制：采集策略、发现运行、发现项、任务、尝试、死信、检查点、复核案例、触发事件、Outbox、成本台账、预算、热度快照、来源健康度和审计日志。

相关表和索引已由迁移创建。应用代码已经接入任务队列、检查点、PostgreSQL 调度器、Outbox 写入和研究 Repository 的主路径；Outbox 外部发布器、触发事件消费者、预算记账和来源健康聚合器仍是待实现的应用组件。

## 5. 阶段契约

### 5.1 来源契约

`SourcePlugin` 只负责发现和获取，不应写数据库、调用调和器或生成可信事实：

```python
class SourcePlugin(Protocol):
    plugin_name: str

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveryItem]: ...

    async def fetch(
        self, item: DiscoveryItem, context: FetchContext
    ) -> RawPayload: ...
```

`DiscoveryItem` 表示候选内容；`RawPayload` 表示这一次真正取回的字节。插件必须提供稳定的 `external_id` 或规范化 URL，否则发现幂等性只能依赖原始 URL。

### 5.2 抽取契约

`ModelGateway.extract()` 接收已归档文档的元数据、原始字节和 `ExtractionTarget`，返回 `ExtractionEnvelope`。Envelope 包含：

- 抽取运行 ID；
- extractor/prompt/model 版本；
- `EvidenceFragment` 集合；
- `FactAssertion` 候选；
- token 与微单位成本；
- 可选的原始响应对象 key。

`CollectionPipeline` 会拒绝以下结果：

- evidence 指向其他文档；
- assertion 指向其他文档；
- assertion 引用不在当前 envelope 内的 evidence；
- assertion 的 `extraction_run_id` 与 envelope 不一致；
- 证据为空、文本/HTML 摘录无法在原文中定位，或 JSON structured payload 与 locator 不一致；
- 同一 envelope 对同口径、重叠期间给出互相矛盾的候选值；
- 单文档断言超过 2,000、证据超过 5,000 条或证据载荷超过 10 MiB（均可配置）；
- 插件返回体超过 `FetchContext.maximum_bytes`，或归档回执的 SHA-256/长度/MIME 与原文不一致。

### 5.3 阶段处理器契约

```python
StageHandler = Callable[[CollectionJob], Awaitable[StageResult]]
```

`StageResult` 必须给出：

- `schema_version`：输出结构版本；
- `output_reference`：持久化输出的引用，不建议放大段原文；
- `next_stages`：确定性的后续任务；
- `emitted_events`：预留的事件数据。

handler 在返回前应先持久化结果。外部副作用必须幂等；检查点只能防止同一 job/stage/version 的正常重放，不能替代目标存储的唯一约束。

## 6. 幂等与重放

系统当前在多个层次提供幂等：

| 对象 | 当前键或稳定 ID |
| --- | --- |
| 发现项 | `sha256(source_id + external_id/url)` |
| Blob | 正文字节 SHA-256 |
| 文档版本 | `source_id + canonical_url + external_id-or-null + content_sha256` 的稳定 UUID；同一下载 URL 上的不同公告不会合并 |
| 逻辑文档 | PostgreSQL Repository 优先按 publisher + canonical URL + external ID 识别，同一出版者的多个连接器可汇合 |
| 抽取运行 | 文档版本 + 最早已知时间 + extractor/version + schema + prompt + model/target + normalizer/reconciler 版本的稳定 ID |
| 处理完成 | 抽取身份 + 文档最早已知时间 + normalizer/reconciler 版本；只有 completion 存在才跳过整条管道 |
| 证据片段 | `document_id + locator + fragment_hash` 的稳定 UUID |
| 断言 | 归一后按文档、证据、事实键、有效时间、value fingerprint、抽取运行、extractor 与 normalizer 版本生成稳定 UUID |
| 队列任务 | `idempotency_key` 唯一，调度器和 Dispatcher 同时生成稳定 job UUID |
| 阶段检查点 | `job_id + stage + input_hash + producer_version` 唯一；并发写入 first-writer-wins，调用方必须使用存储返回的权威结果 fan-out |

`AssertionNormalizer` 不信任 extractor 预填的 `normalized_*`，会从来源标量重新解析强类型值，并在单位解析后重算断言 ID。改变单位目录/换算、predicate profile、维度 schema、调和策略、extractor、normalizer 或阶段 producer 行为时，必须升级相应版本；不能静默复用旧版本号。未注册 predicate、未知单位和 schema 版本不匹配默认只能进入复核。

来源定义（包括质量等级）变化会形成新的 pipeline run 和新的断言，而不会改写旧断言及其历史裁决。同一断言、同一 evaluator 名称与版本只允许保存一次 evaluation；重复提交必须原样返回，不得继续创建冲突、resolution 或 canonical 副作用。来源降级不会自动撤销既有可信事实，撤销需要显式的重审/裁决流程。

仅存在 `extraction_run` 不代表文档处理完成：进程可能在保存抽取后、写断言前崩溃。`ops.document_processing_completions` 是最后提交的完成标记；没有它时会安全重放幂等写入，避免把半成品误判为“无需处理”。

PostgreSQL 迁移还为 Blob、抓取、文档版本、证据片段、事实断言、断言证据、调和评估和审计日志安装了禁止 UPDATE/DELETE 的触发器。修订数据应追加新版本，不应修改历史行。

## 7. 证据链与时间语义

一条断言的最短证据链为：

```text
publisher
  → source_connector
  → document_fetch
  → document_version
  → content_blob（对象库原文）
  → evidence_fragment（页码/单元格/字符等 locator）
  → extraction_run（extractor/prompt/model/schema/cost）
  → fact_assertion
  → reconciliation_evaluation
  → canonical_fact_version 或 review/conflict
```

领域模型区分：

- `valid_time`：事实在现实世界中的适用时间；
- `observed_at`：指标被观察的时间；
- `known_at`：系统首次知道该断言的时间；
- 数据库 `recorded_at/system_from/system_to`：系统记录与采用版本的时间。

归档必须发生在抽取之前。发布事实不能只保存 AI 摘要，必须保留 `document_id` 和 `evidence_fragment_id`。JSON excerpt 与 structured payload 都必须在 locator 指向的子树中成立；非 JSON 的 structured payload 在没有版本化 parser artifact lineage 时拒绝。

## 8. 质量与调和

当前质量分权重为：

```text
来源质量             30%
抽取确定性           20%
实体匹配             15%
时间/单位完整性      15%
独立交叉验证         15%
新鲜度                5%
- 冲突惩罚
```

来源等级、转载簇和 enabled 状态从 Repository 的持久化来源定义加载，调用方不能临时把 D 级来源伪装成 A 级。模型只提供候选值和抽取置信度；corroboration、freshness、实体是否经过目标约束、时间/单位/维度完整性由应用层重新计算。

默认门槛：

- 分数不低于 0.85：接受为 trusted；
- 0.65 至 0.85：进入 review；
- 低于 0.65：quarantine。

当前事实键按主体、predicate 和强类型 `FactDimensions.comparability_hash` 形成；有效时间只决定候选区间。Repository 必须在同一事实键锁/事务内读取可信基线、执行调和并保存权威 evaluation，不能开放“锁外读取后再保存”的组合给业务调用方。只有已经 trusted、维度完整、时间重叠、单位可比的历史断言才会成为互证或冲突基线；review/conflict/quarantine/superseded 不参与。数字容差可按 predicate 配置，默认 1%；非数字使用 value fingerprint。`source_cluster` 相同的转载只算一个独立簇。

显式 supersession 只允许同来源、同事实键、同完整有效区间、更新文档且时间不倒退的修订。接受后前序断言保留但派生状态为 `superseded`，resolution 同时记录 selected 后继和 rejected 前序。部分区间修订在实现区间化 lineage 前进入复核。

现实现中，只要高影响断言的来源质量达到 0.80，或者得到两个独立来源簇支持，即通过高影响证据前置检查；它之后仍要通过普通质量门槛。复杂的多值聚合、人工裁决写回和事实版本发布尚未形成独立应用服务。

## 9. 调度、租约与重试

`CollectionPolicy.priority` 当前固定为：

```text
0.7 × heat_score + 0.3 × data_risk_score
```

`SchedulePolicy` 使用以下规则：

- 事件覆盖期内：每日；
- priority ≥ 70：每日；
- 45 ≤ priority < 70：每三天；
- 更低优先级只有连续低位至少七天后才降为每周；
- 每周任务按 `industry_id.int % 7` 分散；
- 默认在配置时区早上 6 点产生下一次运行时间。

`SchedulerService` 支持调用方传入目标；`PostgresScheduler.tick()` 会在 advisory transaction lock 下读取到期的 `collection_policies`、幂等插入 discover job 并推进 `next_run_at`。触发事件消费者仍未实现。

内存和 PostgreSQL 队列都实现：

- 幂等 enqueue；
- 任务优先级；
- 租约和过期重领；
- 最大尝试次数；
- 指数退避，最大一小时；
- 永久失败或耗尽尝试后进入 dead 状态；
- PostgreSQL 实现额外记录 attempt 和 dead letter。

当前退避没有随机抖动，也没有按域名的运行时限流或 circuit breaker。`SourceDefinition.rate_limit_per_minute` 已建模，但尚无统一执行器。

## 10. 来源安全边界

内置 HTTP 插件已经实现：

- 只允许绝对 HTTP(S) URL；
- 规范化 scheme、host、默认端口并删除 fragment；
- 可配置域名 allowlist；
- DNS 解析后拒绝私网、环回、链路本地、多播、保留和未指定地址；
- 每次跳转重新执行 URL 与主机检查；
- 禁止自动跟随跳转并限制最多六次请求；
- 流式读取并执行 `FetchContext.maximum_bytes` 上限；
- 支持调用方传入条件请求头。

自定义 HTTP 插件必须提供同等级别的 SSRF、跳转和体积防护。当前代码没有 robots.txt、站点条款判断、域名级并发限制和凭证管理器，这些不能假定由框架自动完成。

本地文件插件会把配置根目录解析为绝对路径，并拒绝读取根目录之外的文件。

## 11. 当前未实现的边界

以下数据库结构或接口已经为扩展预留，但尚不能视为可用产品能力：

- 生产 AI/LLM 供应商适配器；
- OCR、PDF/Excel/HTML 通用解析和分块；
- 默认的 discover→derive 全阶段 handler 图；
- Outbox 发布器与事件触发消费者；
- 成本台账自动记账与预算强制执行；
- 来源游标推进、304 的标准阶段 handler 与来源健康聚合；抓取记录已经保存 ETag/Last-Modified/响应头，HTTP 插件会发出 `SourceNotModified`；
- 按域名限流、随机抖动、熔断与 `Retry-After` 策略；
- 真实 OpenTelemetry/Prometheus 适配器；
- 语义目录快照的热更新、灰度和 Worker 部署装配；
- 自动从数据库加载动态采集目标；
- 可信事实投影和周期快照派生服务；
- 人工复核 API 或后台界面。

实现这些能力时应扩展现有端口或新增窄端口，不应让 SourcePlugin 或 ModelGateway 直接操作多个数据库 schema。

## 12. 必须保持的系统不变量

后续开发至少应持续满足：

1. 同一正文字节只归档一次，重复获取可以留下新的 fetch 记录，但不复制 Blob。
2. 已发布事实必须能够回溯到归档原文、证据 locator 和抽取版本。
3. 来源断言不可被可信事实覆盖；冲突来源必须并存。
4. Worker 只有持有当前有效 lease token 才能确认或失败任务。
5. 阶段、提示词、schema、归一规则和调和规则的行为变化必须伴随版本变化。
6. 重放同一幂等任务不能产生第二份事实或第二个后续任务。
7. AI 输出先进入断言层，不能直接写入可信事实或周期快照。
8. 原始产能、有效产能、产量和利用率必须保持不同指标口径。

## 13. 当前验证入口

项目已经提供：

```bash
longcycle doctor
longcycle db upgrade
longcycle source plugins
longcycle schedule --industry-id <uuid> --heat 80 --risk 60
longcycle demo
pytest
```

`longcycle demo` 使用本地文件、文件归档、内存 Repository 和 `JsonFixtureGateway` 执行离线黄金路径，不访问真实外部来源或 AI 服务。
