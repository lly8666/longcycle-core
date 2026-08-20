# 采集系统运行与扩展

本文说明如何把当前核心装配成持续采集系统，并区分已经实现的机制和上线前仍需补齐的组件。

## 1. 推荐部署单元

初期使用模块化单体，不急于拆微服务：

```text
scheduler      原子读取到期策略并创建 discover 任务
worker-io      discover / fetch / archive
worker-parse   parse / extract / normalize / validate
worker-core    reconcile / publish / derive
review         人工复核 API（待实现）
outbox-relay   发布事务 Outbox（待实现）
PostgreSQL     目录、事实、任务、成本、审计
S3/R2/MinIO    原文、解析产物、模型原始响应
```

代码允许按 pool 独立横向扩容；不改变领域模型也可以把某一阶段迁到独立服务。至少一次执行意味着每个阶段必须先设计幂等键，再设计副作用。

## 2. 标准任务图

数据库和枚举支持：

```text
discover → fetch → archive → parse → extract
                               ↓
                       normalize → validate
                                      ↓
                           reconcile → publish → derive
```

`CollectionPipeline.ingest()` 已提供单文档黄金路径，可用于早期采集和插件验收。`PipelineDispatcher` 已提供检查点、确定性 fan-out 和 Outbox 幂等写入，但默认十阶段 handler 仍需按具体解析器和模型装配。

检查点命中后仍会重放确定性的下游 enqueue 和 Outbox 写入，因此即使“本阶段结果已提交、进程在 fan-out 前崩溃”，再次执行也不会丢下游任务。

单文档黄金路径同样采用尾部 completion marker。抽取运行已落库但断言/调和尚未全部完成时，重试不会因“文档与抽取已存在”而提前跳过；只有 `document_processing_completions` 已写入才视为完成。

## 3. 采集频率

每个行业与来源目标形成一条 `collection_policy`：

```text
priority = 0.7 × heat_score + 0.3 × data_risk_score
```

- 事件覆盖期，或 priority ≥ 70：每日。
- 45 ≤ priority < 70：每三天。
- 更低时，连续低位至少七天后降为每周。
- 周任务按行业 UUID 分散到七天，默认当地时间 06:00。

这满足“热点每日、非热点每周”，同时避免热度刚越过阈值就频繁升降。正式环境应再增加：来源原生发布日期、交易日历、静默时段、失败退避和域名预算。

## 4. 便宜 AI 的分层路由

建议按任务风险而非行业热度单独决定模型：

| 层级 | 任务 | 建议 |
| --- | --- | --- |
| 0 | 下载、去重、MIME、正文提取、表格定位 | 规则与开源解析器，不用模型 |
| 1 | 文档分类、相关性、候选实体/事件、简单字段 | 便宜小模型，严格 JSON Schema |
| 2 | 复杂表格、单位/口径解释、公司业务分部映射 | 中档模型，保留逐字段 evidence |
| 3 | 高影响冲突、跨文档调和建议 | 强模型或人工；仍不能直接发布 |

模型路由输入应包含风险级别、文档长度、字段价值、历史错误率和预算余额。低置信结果不自动“再问同一个便宜模型多次取多数”，而是进入独立来源交叉验证或升级模型。

每次运行记录 `tokens_in/out`、微单位成本、provider、model、industry 和 source。预算表支持按模型、行业、来源或全局设置月/日限额；自动强制执行器仍待实现。

## 5. 来源策略

优先顺序建议：

1. 交易所、监管、政府、协会和公司公告等一手来源。
2. 有合同许可的数据 API/数据商。
3. 公司官网和明确允许访问的公开页面。
4. 新闻与研究作为事件发现，不单独成为高影响事实的最终依据。

每个连接器独立配置 publisher、独立来源簇、质量等级、速率、robots 策略、认证 secret 引用和订阅目标。转载同一稿件的十个网站只能算一个来源簇；未显式配置簇时，PostgreSQL 适配器按 publisher 身份回退，手工来源按持久化 publisher domain 回退，不能按 connector 数量虚增独立信源。

HTTP 适配器已做基础 SSRF 防护，但 DNS 解析和连接之间仍可能发生 rebinding。生产环境必须再使用网络出口代理/防火墙，只允许 80/443 公网目标，并阻断云 metadata、RFC1918、环回、链路本地和内部 DNS。凭证使用 Secret Manager，绝不写入数据库 config、URL、日志或模型 prompt。

304 Not Modified 是成功且无新正文的结果。阶段 handler 应捕获 `SourceNotModified`，更新来源健康和下次调度后确认任务，不能当作失败重试。

## 6. 重试、租约与死信

- Worker 只领取其立即可执行的并发数，避免任务拿着租约排队。
- `worker_id + lease_token + 未过期时间` 三者同时匹配才允许 ack/fail/heartbeat。
- 心跳失去租约会取消 handler，阻止旧 Worker 提交 stale completion。
- 领取时增加 attempt；最后一次 attempt 崩溃后，下次 claim 只把任务收敛到 dead，不再多执行一次。
- 低于上限的过期租约被重领时，旧 attempt 关闭为 retry，新 attempt 独立记录。

建议错误分类：

- 永久：非法配置、被拒绝域名、超安全上限、不支持的 schema、无法解析的固定格式。
- 可重试：超时、429、5xx、对象存储/数据库瞬时错误。
- 需要复核：文档本身有效，但字段口径、实体、时间或冲突不明确。

上线时为退避增加 full jitter、尊重 `Retry-After`，并按域名实施并发限制和 circuit breaker。死信只能显式重放，重放要保留原任务、错误、操作者和新 trace。

## 7. 数据质量闸门

建议至少追踪：

- 抓取成功率、304 比率、变化率、重复率、P95 延迟、限流率；
- 解析覆盖率、空正文率、表格识别率；
- 每文档断言数、schema 失败率、证据 locator 缺失率；
- 文本证据 grounding 失败率、证据哈希不一致率；
- 完整维度率、单位可换算率、实体匹配率；
- 自动接受/复核/冲突/隔离比例；
- 人工推翻率，按 source、extractor、predicate 分组；
- 数据新鲜度、历史补齐率、行业覆盖完整度；
- 每个可信事实的独立信源数和证据可访问率。

质量下降时优先停自动发布，不应停原文归档。原文和候选保留下来，修复 parser/normalizer 后可用新版本重放。

## 8. 容量与成本规划

把三个量分开估算：

```text
对象库增长 = 原文 + 解析产物 + 必要的模型原始响应
数据库增长 = 文档元数据 + 证据 locator + 断言/版本 + 运行日志
模型成本   = 文档变化率 × 相关率 × 需模型处理的字节/页数 × 单价
```

内容哈希先于抽取；不可变 extraction envelope 一旦持久化，半程崩溃后的恢复会直接读取它，不再重新询问可能产生不同答案的模型。同正文换目标/schema/model/normalizer/reconciler 时允许新抽取。若进程在模型返回后、envelope 首次持久化前崩溃，重试仍会再次产生一次模型成本，但不会把两个输出混入同一 run。大文档先做确定性分块与相关页筛选。原始响应若含完整受版权保护正文或敏感信息，应采用更短保留期或只存必要审计字段。

PDF/OCR/HTML 表格等解析结果先按内容寻址写入对象库，再以 `DocumentArtifact` 登记 parser 名称、版本、输入哈希和输出哈希。相同解析身份产生不同输出会被拒绝；结构化 evidence 通过 `artifact_id` 绑定产物，不能只靠模型声称某个单元格存在。

## 9. 备份、保留与灾难恢复

生产最低要求：

- PostgreSQL 开启 PITR，定期做可恢复性演练，而不只看备份成功日志。
- 对象桶开启 versioning；高价值原文启用对象锁或独立归档复制。
- 数据库和对象库跨对象校验：`content_blobs.sha256/byte_length` 与对象实际值一致。
- 加密传输和静态加密；密钥轮换不改变内容身份。
- 审计日志和已发布事实的保留期长于普通运行日志。
- 删除请求采用受控 tombstone/访问撤销流程；不要直接破坏仍被事实引用的证据。

建议恢复演练顺序：恢复数据库到时间点 → 恢复/挂载对象版本 → 抽样验证哈希 → 重启 scheduler → 只重放未确认或 dead-letter 审核通过的任务。

## 10. 上线阶段

### 阶段 A：黄金样本

选择 3–5 个结构差异大的行业，每类接入一手价格、产能项目、公司公告和协会/监管来源。人工标注 100–300 份文档作为 extractor 与 reconciler 回归集。

### 阶段 B：影子运行

持续采集但不自动发布；比较人工结论和系统断言，校准维度、来源质量、容差和成本。运行 PostgreSQL 并发、租约丢失、对象存储失败、备份恢复测试。

### 阶段 C：有限自动发布

只开放高质量、低歧义 predicate；高影响产能、事故、公司敞口和冲突仍复核。监控人工推翻率并设自动熔断阈值。

### 阶段 D：扩行业

新行业通过数据包加入：分类节点、产品/规格、predicate profile、单位、来源订阅、解析模板和黄金样本。核心代码不应为每个行业增加 if/else。

## 11. 当前还必须补齐的生产组件

- PostgreSQL 与 S3/MinIO 的真实集成和故障注入测试。
- 通用 HTML/PDF/Excel/OCR parser 及版本化 artifact。
- 语义目录快照的热更新、灰度发布、回滚与 Worker 装配。
- 一个生产 `ModelGateway` 和风险/预算路由器。
- 十阶段默认 handler 图、域名限流器、304 状态持久化、cursor 管理。
- Outbox relay、触发事件消费者、成本/预算强制执行器、真实遥测。
- 人工复核 API、权限、审计和可信事实发布服务。
- 目录/实体/规格的导入、消歧和批量回填工具。

在这些组件完成前，当前代码是一个经过单元验证的可扩展内核和离线黄金路径，不应被描述成已经无人值守运行的完整生产系统。

迁移 `0008` 的证据材料约束使用 `NOT VALID`：新写入立即受保护，历史行不会阻断升级。上线前应先审计旧的空白 excerpt/空 structured payload，完成受控修复后执行 `VALIDATE CONSTRAINT evidence_fragments_material_check`；不得为了验证而删除仍被事实引用的原始证据。
