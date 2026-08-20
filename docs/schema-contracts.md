# Schema 与时间契约

这份文档是采集器、抽取器、研究模型和未来 API 共同遵守的数据契约。

Longcycle 数据库不是把网页字段平铺成表，而是保存三类不同性质的历史：

```text
Reality      来源声称现实发生了什么，系统后来采用了什么
Expectation  人在某一历史时点如何判断未来，以及为什么
Outcome      后来实际发生了什么，判断与现实如何偏离
```

三类对象都必须能回溯到当时可获得的原始证据，但它们不能共享同一套真值语义。

## 1. 四个 schema 的职责

| Schema | 保存内容 | AI 可否直接写入可信结果 |
| --- | --- | --- |
| `core` | 分类、实体、别名、标识符、关系、产品规格、设施、产线、证券、单位、predicate 语义 | 否 |
| `evidence` | 出版者、来源、抓取、Blob、文档版本、解析 artifact、证据 locator、抽取运行 | 只能通过受控管道追加 |
| `research` | 事实断言、可信事实、指标、项目、事件、判断、预期、共识、后验评价 | AI 只能产生候选断言/判断 |
| `ops` | 任务、租约、断点、复核、Outbox、成本、预算、健康度、审计 | 否 |

正文保存在对象存储，PostgreSQL 保存身份、哈希、locator、版本和结构化研究数据。

## 2. 数据库的三个真值层次

### 2.1 来源表达

来源表达是不可变历史，包括：

- `research.fact_assertions`：来源声称现实是什么；
- `research.judgment_assertions`：来源中的某个说话者如何判断未来或不确定状态。

来源后来改口不能修改旧行，只能追加新行并建立 revision relation。

### 2.2 系统采用

只有事实可以经过 reconciliation / resolution 进入 `canonical_fact_versions`。

观点、预测和目标不能因为来源质量高或多人一致直接进入 canonical fact。

### 2.3 派生研究

`expectation_snapshots`、`judgment_outcome_evaluations`、`cycle_snapshots` 等都是可重放的派生结果，必须保存输入 cutoff 和 producer version。

## 3. 主数据身份

### 分类与行业

- `core.taxonomies` 表示一套分类体系；
- `core.taxonomy_nodes` 是稳定节点身份；
- 分类结构和行业成员关系必须版本化；
- 历史中消失的公司或行业参与者不得删除。

### 实体、证券、工厂和产线

- 组织/公司使用 `core.entities`；
- 股票代码使用 `core.security_listings`；
- 工厂使用 `core.facilities`；
- 产线使用 `core.production_lines`。

证券代码不能代替生产主体，公司也不能代替具体工厂和产线。

### Speaker 身份

Judgment 的 speaker 可以是：

- 管理层个人；
- 公司或机构作为整体；
- 券商分析师；
- 行业协会；
- 政府部门；
- 产业人士；
- 来源无法唯一识别的署名人物。

`judgment_assertions.speaker_entity_id` 优先绑定 `core.entities`。无法可靠消歧时保留 `speaker_name_text`，不能为了结构化而伪造实体。

`speaker_affiliation_entity_id` 表示当时所属机构。个人后来换机构不应改变旧 judgment。

## 4. 证据不可变链

事实链：

```text
publisher
→ source_connector
→ document_fetch
→ document / document_version
→ content_blob / artifact
→ evidence_fragment
→ extraction_run
→ fact_assertion
→ reconciliation_evaluation
→ fact_resolution
→ canonical_fact_version
```

判断链：

```text
publisher
→ source_connector
→ document_version / artifact
→ evidence_fragment
→ extraction_run
→ judgment_assertion
→ judgment_rationale / judgment_relation
→ expectation_snapshot
→ judgment_outcome_evaluation
```

重要约束：

- 原始字节先归档，再产生结构化对象；
- parser/OCR/表格产物必须独立版本化；
- evidence 必须能定位页码、DOM、表格单元格或 JSON 路径；
- 结构化 evidence 必须绑定对应 artifact；
- 已发布事实和 judgment 不得只有 AI 摘要而没有原文证据；
- extraction、normalizer 或 schema 版本变化必须形成新的处理身份。

## 5. Reality：事实键与可比维度

事实键继续定义为：

```text
fact_key = subject + predicate_code + comparability_hash
```

`comparability_hash` 来自版本化 `FactDimensions`，用于表达会改变比较含义的口径，例如：

- 产品规格；
- 地区；
- 现货/长协/指数/牌价；
- 税费；
- 运费和交货口径；
- Incoterm；
- 币种；
- 日/月/季/年频率；
- 低价/高价/均价/结算价；
- 统计范围。

缺少必需维度时 `dimensions_complete=false`，不能与其他事实自动互证或判冲突。

`core.predicate_definitions` 保存 predicate 的值类型、时间模式、维度 schema、规范单位、高影响标记和调和策略。

## 6. Expectation：Judgment 契约

`research.judgment_assertions` 是一等研究对象，不是 `fact_assertions.metadata`。

一个 judgment 表示：

> 某个 speaker 在 `first_known_at` 时点，对某个 subject/topic 的未来或不确定状态表达了一项判断。

### 6.1 Judgment kind

允许的核心类型：

| kind | 含义 |
| --- | --- |
| `forecast` | 对未来结果的预测 |
| `target` | 主体希望达到的目标 |
| `guidance` | 管理层或机构正式指引 |
| `scenario` | 条件化情景 |
| `probability` | 明确概率判断 |
| `risk` | 风险方向/可能性判断 |
| `thesis` | 逻辑或机制判断 |
| `commitment` | 主体承诺采取的行动 |
| `consensus_statement` | 来源直接描述的市场共识 |

“计划达到 100 万吨”和“预计需求达到 100 万吨”必须是不同 kind。

### 6.2 Subject 与 topic

Judgment 必须绑定一个实体或行业节点，并保存 `topic_code`。

如果判断可以映射到现有事实 predicate，例如“2027 年需求 120 万吨”，则同时保存：

```text
predicate_code
a comparable dimension set
target period
```

这样未来才能与 Reality 自动配对。

纯定性 thesis/risk 可以没有 `predicate_code`，但必须有稳定 `topic_code`。

### 6.3 判断的目标时间

判断发表时间和判断针对的时间必须分离。

例如：

```text
first_known_at = 2024-06-15
target_from    = 2026-01-01
target_to      = 2027-01-01
```

这表示“2024 年 6 月作出的对 2026 年的判断”。

`target_time_kind` 包含：

- `instant`；
- `period`；
- `timeless`；
- `unknown`。

未知 horizon 不得猜测。

### 6.4 Judgment value

判断可以保存：

- numeric point；
- numeric range；
- text；
- boolean；
- date；
- entity；
- json；
- direction。

数值区间优先于把“约 100–120”伪装成一个精确点值。

明确表达的概率保存在 `expressed_probability`，不能把 extractor confidence 当成 speaker probability。

### 6.5 原文 summary 与证据

`summary` 只是规范化后的简短命题，不是证据。

`research.judgment_evidence` 必须至少能保存 statement evidence，并可额外标记：

- rationale；
- condition；
- caveat；
- context。

## 7. Judgment rationale：为什么这样判断

`research.judgment_rationales` 把理由作为一等对象保存。

类型包括：

- `premise`：事实前提；
- `mechanism`：因果机制；
- `condition`：成立条件；
- `risk`：主要风险；
- `caveat`：限定条件；
- `counterargument`：反方逻辑。

Rationale 可以连接：

- 原始 evidence；
- 一个 `fact_assertion`；
- 另一个 `judgment_assertion`。

因此可以形成：

```text
需求预测
  ├─ premise: 出口继续增长
  ├─ premise: 渗透率提升
  ├─ mechanism: 单位用量稳定
  └─ risk: 新技术降低单位耗用量
```

后验复盘要尽可能评价哪一条 premise 或 mechanism 失败，而不是只记录最终误差。

## 8. Judgment revision：观点如何变化

`research.judgment_relations` 保存 judgment 之间的历史关系：

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

例如同一家公司连续三次调整投产时间，应保留三条 judgment，并用 `revises` 连接。

禁止 UPDATE 旧 judgment 的 target date。

## 9. Consensus：共识是派生对象

`research.expectation_snapshots` 表示在某个 `knowledge_cutoff` 下，根据一组 judgment 计算出的共识。

每个 snapshot 必须保存：

- subject / topic / predicate；
- target time；
- `knowledge_cutoff`；
- aggregation method；
- producer name/version；
- 聚合值或区间；
- member count；
- dispersion；
- confidence；
- system time。

`expectation_snapshot_members` 保存具体纳入的 judgment 和权重。

这意味着“2024-06-30 的市场预期”与“2024-09-30 的市场预期”是两个历史对象，不能用一行不断覆盖。

多个 speaker 同意一件事，只能提高 consensus 强度，不能自动提高 Reality 的 truth score。

## 10. Outcome：预期与现实的配对

`research.judgment_outcome_evaluations` 将 judgment 与后来的 canonical reality 配对。

可以保存：

- `evaluation_status`；
- numeric error；
- relative error；
- timing error days；
- direction correct；
- 后验解释；
- evaluator version。

典型状态：

```text
realized
partially_realized
not_realized
not_yet_evaluable
invalidated
```

Outcome evaluation 是可重复计算的派生记录。canonical fact 后来修订时，新增 evaluation，不修改原 judgment。

## 11. 时间语义

### 11.1 Reality 时间

| 字段 | 含义 |
| --- | --- |
| `valid_from/valid_to` | 现实事实适用时间 |
| `source_published_at` | 来源发布时间 |
| `first_known_at/market_known_at` | 当时最早可知时间 |
| `system_from/system_to` | 系统采用版本的时间 |
| `vintage_at` | 同一统计期的发布批次 |

### 11.2 Expectation 时间

| 字段 | 含义 |
| --- | --- |
| `first_known_at` | 这项判断何时进入历史信息集 |
| `target_at` | 判断针对的未来瞬时点 |
| `target_from/target_to` | 判断针对的未来期间 |
| `knowledge_cutoff` | 派生共识允许使用的信息截止时间 |
| `system_from/system_to` | 派生 snapshot 在系统中的版本时间 |

永远不能用 target time 代替 known time。

## 12. Point-in-time 查询契约

任何历史研究查询都必须显式区分：

```text
observation_date / target_date
knowledge_cutoff
system_as_of
```

例如“站在 2024-12-31 看 2025 年需求预期”应满足：

```sql
SELECT *
FROM research.judgment_assertions
WHERE first_known_at <= timestamptz '2024-12-31 23:59:59+00'
  AND target_from < timestamptz '2026-01-01 00:00:00+00'
  AND (target_to IS NULL OR target_to > timestamptz '2025-01-01 00:00:00+00');
```

使用 expectation snapshot 时还必须：

```text
snapshot.knowledge_cutoff <= requested_cutoff
```

未来测试必须专门验证无 look-ahead leakage。

## 13. 指标序列与修订

`metric_definitions`、`metric_series`、`observation_assertions`、`observation_versions` 继续负责可比较指标历史。

价格、产能、有效产能、产量、利用率、库存、利润、资本开支、需求等必须是不同指标。

不要：

- 用月产量替代产能；
- 用设计产能替代有效产能；
- 用当前最终修订值覆盖当年最初公布值。

历史 vintage 本身具有研究价值。

## 14. 项目历史

`capacity_projects` 只是项目身份。

项目历史应由事实和判断共同构成：

```text
Reality:
项目宣布 / 获批 / 开工 / 完工 / 试产 / 投产 / 达产 / 取消

Expectation:
管理层预计投产时间
分析师预计投产时间
成功概率判断
爬坡速度判断
延期原因判断
```

`project_status_versions` 表示系统采用的项目状态；未来计划/预测本身应优先保存为 judgment，而不是只留下最终 adopted status。

## 15. 行业事件与公司行为

- `event_clusters` 聚合同一现实事件；
- `event_claims` 保存来源对事件的事实说法；
- 对事件未来影响的预测应进入 judgment；
- `company_exposure_versions` 保存系统采用的公司产业敞口；
- 管理层对订单、需求、价格和资本开支的 future guidance 应进入 judgment；
- `cycle_snapshots` 是带 `knowledge_cutoff` 的派生结果，不是“历史真相标签”。

## 16. 不可变与幂等

以下对象必须 append-only：

- 原始 Blob；
- document fetch/version；
- artifact；
- evidence fragment；
- extraction run；
- fact assertion；
- judgment assertion；
- judgment evidence/rationale/relation；
- reconciliation evaluation；
- outcome evaluation；
- audit log。

所有 handler 必须假设至少一次执行。

同一处理输入、producer version 和稳定身份必须可安全重放。

## 17. 迁移规则

1. 已执行的迁移永不修改，只追加新编号；
2. predicate、维度、单位换算和 reconciliation 行为改变必须升级版本；
3. judgment extraction schema、speaker resolution、rationale parser 改变必须升级版本；
4. expectation 聚合方法改变必须生成新的 producer version；
5. outcome evaluator 改变不得覆盖旧 evaluation；
6. 无法可靠消歧的 speaker、subject、单位、时间和维度宁可进入复核，不猜；
7. 任何可能让历史查询读到未来信息的 schema 或应用改动都必须视为高风险变更。

## 18. Schema 设计的最终判断标准

新增字段或表前先问：

> 十年以后回看今天，如果没有保存这项信息，我们是否会失去理解当时行为和判断所需的关键上下文？

如果答案是否定的，它通常不应该优先进入 Longcycle Core。
