# Schema 与时间契约

这份文档是数据采集器、研究模型和未来 API 共同遵守的数据库契约。数据库不是把网页字段平铺成表，而是同时保存“来源原话”“系统结论”和“系统在某一时点知道什么”。

## 1. 四个 schema 的职责

| Schema | 保存内容 | 是否允许直接被 AI 写入 |
| --- | --- | --- |
| `core` | 分类树、实体、别名、标识符、组织关系、产品规格、设施、产线、证券、单位 | 否；只能提交候选，需消歧/审核 |
| `evidence` | 出版者、连接器、抓取、不可变 Blob、文档版本、解析产物、证据 locator、抽取运行 | 仅能通过受控采集管道追加 |
| `research` | 原子断言、调和、冲突、可信事实版本、指标序列、产能项目、事件、公司敞口、行业关系、周期快照 | 只能写断言；可信层由规则/审核发布 |
| `ops` | 频率策略、任务、租约、死信、断点、复核、Outbox、成本、预算、热度、来源健康、审计 | 否；由控制平面写入 |

正文存对象库，PostgreSQL 只存哈希、位置、版本和结构化信息。这样可以独立扩容，也避免把大 PDF/网页塞进事务型数据库。

## 2. 主数据身份

### 分类与行业

- `core.taxonomies` 表示一套分类口径，例如“研究自定义分类 v1”或申万层级。
- `core.taxonomy_nodes` 是稳定节点身份。
- `core.taxonomy_edges` 保存父子关系的有效时间，因此分类调整不会抹掉旧结构。
- 一个实际业务对象可以映射到多个分类体系，不能把展示路径写进事实主键。

### 实体、证券、工厂和产线

- 公司法人/品牌/组织使用 `core.entities`。
- 股票代码是 `core.security_listings`，不是公司身份。
- 工厂使用 `core.facilities`，产线使用 `core.production_lines`。
- 一家公司、证券、工厂、产线通过版本化关系关联；并购、改名、退市、工厂转手不会破坏历史。
- 历史中消失的玩家不删除，关闭其关系或状态有效期。

### 产品与规格

行业产品使用 `core.products`，可比规格使用 `core.product_specs`。例如同为维生素 A，不同 IU/g、饲料级/食品级不能仅靠自由文本区分。模型无法可靠匹配规格时保留原始文本并进入复核，不伪造 `product_spec_id`。

## 3. 证据不可变链

```text
publisher
  → source_connector
  → document_fetch
  → document + document_version
  → content_blob / artifact
  → evidence_fragment
  → extraction_run
  → fact_assertion
  → reconciliation_evaluation
  → fact_resolution
  → canonical_fact_version
```

重要区别：

- 同一逻辑文档可被多次抓取；每次抓取有独立 `document_fetch`。
- 正文字节相同只生成一个 `content_blob`；正文变化生成新的 `document_version`。
- parser 输出作为 `artifact` 单独版本化；身份由 document version、artifact type、producer、producer version 与 input hash 决定，内容哈希不一致时 fail closed。
- 直接引用原文的 evidence 可不带 `artifact_id`；PDF/OCR/表格产生的结构化 evidence 必须绑定同一 document version 下已持久化的 artifact。
- 同一文档可由不同 schema、prompt、模型或目标重复抽取，各自生成独立 `extraction_run`。
- `evidence_fragment.locator` 必须能定位页码、表格单元格、DOM 片段或 JSON 路径。
- 已发布事实不得只有 AI 摘要而没有证据片段。

## 4. 事实键与可比维度

事实键不是“公司 + 字段 + 日期”的字符串。正式定义为：

```text
fact_key = subject + predicate_code + comparability_hash
```

`comparability_hash` 来自版本化 `FactDimensions` 的规范 JSON，包含可能改变比较含义的口径：

- 产品规格；
- 地区编码体系与代码；
- 现货/长协/牌价/拍卖/指数/评估价；
- 合同口径；
- 含税/未税；
- 含运费/不含运费/出厂/到货；
- Incoterm；
- 币种；
- 日/周/月/季/年频率；
- 低价/高价/中间价/均价/结算价/收盘价；
- 统计范围。

缺少必需维度不是 wildcard。它可以保存，但 `dimensions_complete=false`，只能进入人工复核，不能与另一条数据自动互证或判冲突。

`core.predicate_definitions` 保存每个 predicate 或命名空间的值类型、时间模式、维度 schema、必需/允许维度、规范单位、高影响标记和调和策略。未注册的新 predicate 可以进入 assertion 层，但默认 `dimensions_complete=false`，不能自动发布。`PostgresSemanticCatalog.load_runtime()` 会一次性加载 active predicate、当前单位换算和单位目录，构造不可变的 normalizer/reconciler 快照；快照指纹同时进入两者版本和 pipeline 处理身份。未知 policy key、未注册规范单位或转换引用会 fail closed。部署层仍需明确装配该快照，当前没有热更新守护进程。

有效时间不进入 `comparability_hash`：同一价格序列的不同月份属于同一个事实口径，但断言身份仍包含有效期，避免不同时段的同值碰撞。

## 5. 三种时间与双时态

| 时间 | 含义 | 例子 |
| --- | --- | --- |
| `valid_from/valid_to` | 现实世界中事实适用的半开区间 `[from,to)` | 2025 年度产能 |
| `source_published_at` | 来源发布该资料的时间 | 年报披露日 |
| `first_known_at` / `market_known_at` | 系统或市场最早可知道的时间 | 用于防止回看偏差 |
| `system_from/system_to` | 数据库采用该版本的时间 | 2026-08-18 起采用修订值 |
| `vintage_at` | 同一统计期数据的发布批次 | 初值、修订值、终值 |

时间敏感事实使用 `valid_time_kind='period'`；明确永续的结构事实使用 `timeless`；无法确定时使用 `unknown` 并复核。区间端点相等视为不重叠，例如 `[2025-01-01, 2026-01-01)` 与 `[2026-01-01, 2027-01-01)`。

同一文档版本后来出现更早的可靠 `first_known_at` 回填时，最早时间会进入新的 pipeline run 身份，生成新的不可变 provenance 和系统时态版本；不能只更新文档元数据后沿用已经完成的旧断言。这样历史查询才能反映“当时已经可知道”，同时保留“系统何时完成这次回填”的 `system_from`。

查询“现在认为的当前事实”：

```sql
SELECT *
FROM research.trusted_fact_current
WHERE fact_key_id = $1
  AND (valid_from IS NULL OR valid_from <= $2)
  AND (valid_to IS NULL OR valid_to > $2);
```

查询“在 2024-12-31 当时，系统对 2024-06-30 的认识”：

```sql
SELECT *
FROM research.canonical_fact_versions
WHERE fact_key_id = $1
  AND (valid_from IS NULL OR valid_from <= timestamptz '2024-06-30 23:59:59+00')
  AND (valid_to IS NULL OR valid_to > timestamptz '2024-06-30 23:59:59+00')
  AND system_from <= timestamptz '2024-12-31 23:59:59+00'
  AND (system_to IS NULL OR system_to > timestamptz '2024-12-31 23:59:59+00');
```

数据库的排斥约束禁止同一事实键在相交的现实有效期和系统有效期上同时存在两条可信版本。新值只覆盖旧区间的一部分时，Repository 会把未覆盖的左右区间作为 carry-forward 版本保留。

## 6. 三层研究数据

### Assertion：来源声称什么

`research.fact_assertions` 是不可变原子断言。冲突值并存，不能用 UPDATE 把旧来源改成新来源。每条断言同时保存来源原值、规范 typed value、质量分量、来源簇、抽取运行、证据和可选 `supersedes_assertion_id`，避免单位归一后丢失来源表达或修订链。AI 提供的 typed hint 不被信任，normalizer 必须由非空 raw value 重算；未知原始单位保存在 metadata，规范单位置空并进入复核，不能直接撞数据库单位外键。

### Resolution：为什么采用或拒绝

`reconciliation_evaluations` 保存自动判断；`conflict_cases` 保存冲突集合；`fact_resolutions` 保存采用、拒绝和理由。人工裁决也必须产生 resolution，而不是直接改可信表。

### Canonical：系统当前采用什么

`canonical_fact_versions` 保存双时态可信版本。派生模型和未来网页默认读这一层，但必须允许用户下钻到断言和原文。

## 7. 指标序列与修订

`metric_definitions` 定义价格、产能、有效产能、产量、利用率、库存、利润、资本开支、订单、需求和运价等指标。`metric_series` 把指标绑定到稳定可比维度；`observation_assertions` 保存来源观测；`observation_versions` 保存采用值及 vintage。

两个视图用途不同：

- `observation_current_per_vintage`：保留每一个仍有效的发布批次。
- `observation_current`：每个统计期只取最新 vintage，适合默认图表。

不要把月产量累加后命名为产能，也不要用产量/设计产能替代系统已建模的有效产能。

## 8. 产能项目模型

产能不是单一数字，至少拆为：

```text
玩家/工厂/产线
  + 产品规格
  + 设计/名义/有效/获批/在建/宣布口径
  + 有效期
  + 项目里程碑
  + 当前阶段
  + 投产时间区间与成功概率
  + 分月爬坡假设
```

`capacity_projects` 保存项目身份；`project_milestone_assertions` 保存来源说法；`project_status_versions` 保存采用状态；`capacity_ramp_assumption_versions` 支持基准/乐观/悲观情景。关闭、延期、取消和重启都以新版本记录。

## 9. 玩家、事件、上市公司与行业网络

- 主流玩家、新进入者和历史退出者由实体、行业成员关系、工厂/产线、项目状态共同计算，不应是一个静态名单字段。
- `event_clusters` 聚合同一事件，`event_claims` 保留不同来源说法，`event_impact_versions` 保存方向、强度、滞后、持续期和机制。
- `company_exposure_versions` 使用收入/利润/成本/产能占比的上下界而非伪精确单值，并记录方法、报告期和置信度。
- `industry_relation_versions` 表示上下游、替代、共用原料/产能、联产品、副产品、需求代理等关系及滞后。
- `cycle_snapshots` 是有 `knowledge_cutoff`、模型版本、数据版本、概率、解释和证伪条件的可重放派生结果，不是人工覆盖的标签。

## 10. 迁移和兼容规则

1. 已执行的迁移文件永不修改；新增变更追加编号文件。
2. predicate、维度 schema、单位换算、normalizer、reconciler 行为变化必须升级版本。
3. 新增自由文本维度前先判断它是否影响可比性；影响则进入强类型 schema，否则放 metadata。
4. 外键身份不能靠名称猜测；无法消歧时保存候选并复核。
5. 任何删除/重写历史的维护动作必须经过备份、审计和显式变更流程。
