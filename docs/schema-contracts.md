# Schema 与时间契约

这份文档是采集器、抽取器、研究模型、Memory Campaign 和未来 API 共同遵守的数据契约。

Longcycle 同时保存四类不同性质的研究对象：

```text
Reality      来源声称现实发生了什么，系统后来采用了什么
Expectation  人在某一历史时点如何判断未来，以及为什么
Outcome      后来实际发生了什么，判断与现实如何偏离
Model Prior  高级模型今天对历史的未举证记忆/联想/缺口，只用于生成搜索线索
```

其中只有前三类最终可以进入对外研究结果；Model Prior 永远不能直接成为 Fact/Judgment。

---

## 1. 四个 schema 的职责

| Schema | 保存内容 | AI 可否直接写入可信结果 |
| --- | --- | --- |
| `core` | taxonomy、entity/alias、产品规格、设施、证券、单位、predicate/dimension semantics | 否 |
| `evidence` | publisher/source、抓取、Blob、文档版本、artifact、evidence locator、extraction run、source authority profile | 只能通过受控归档/抽取管道追加 |
| `research` | Fact、Canonical Fact、Judgment、Expectation、Outcome、Memory Lead、Campaign、Refresh | AI 只能生成候选/先验，不能越过 Evidence 发布可信事实 |
| `ops` | queue/lease/checkpoint/review/outbox/cost/source health/memory verification task | 否 |

正文/二进制原件放对象存储；PostgreSQL 保存身份、哈希、版本、locator 和结构化研究对象。

---

## 2. 时间语义

### 2.1 source time

文档至少区分：

- `published_at`：来源正式发布日期；
- `first_known_at`：市场/系统最早可合理知道该材料的时间；
- `retrieved_at`：Longcycle 实际拿到该文件的时间。

`retrieved_at` 不能代替历史 `published_at/first_known_at`。

### 2.2 valid time

Fact 的 `valid_time` 回答：

> 这个事实描述现实世界哪个时间段？

### 2.3 system/adoption time

Canonical Fact 需要保留系统什么时候采用/结束采用该版本，不能因为后来修订就覆盖过去采用过的结论。

### 2.4 Judgment time

Judgment 至少有：

```text
said/known time
forecast target time
```

例如 2022 年 6 月对 2025 年需求的预测，两者必须分开。

### 2.5 Knowledge cutoff

Expectation Snapshot、historical query 和 archive gap audit 必须保存 `knowledge_cutoff`。

任何 cutoff 之后公开的资料都不能进入当时 snapshot。

### 2.6 Model memory time

Memory Lead 有两套完全不同的时间：

```text
approximate historical period  模型认为线索大概发生在什么时候
model run created_at            模型什么时候回忆出这条线索
```

2028 年模型第一次想起 2021 年项目，不代表 2021 年的历史 knowledge time 是 2028，也不代表模型记忆能证明 2021 年发生过该事。

---

## 3. Evidence 契约

所有可发布 Fact/Judgment 必须能下钻到：

```text
content blob/document version
→ parsing artifact（若结构化/解析后）
→ evidence fragment
→ exact locator
```

禁止以下对象作为最终 Evidence：

- 搜索结果 snippet；
- 模型回答；
- Memory Lead；
- 没打开正文的搜索列表；
- 无法追溯的截图；
- 二手文章对原始统计的模糊转述（若 claim 要求 primary）。

`evidence_fragments` 必须有 excerpt 或 structured payload；结构化 locator 必须绑定持久化 artifact。

---

## 4. Fact 契约

`research.fact_assertions` 保存来源层现实断言。

Fact key 至少由：

```text
subject
predicate
comparability dimensions
```

组成。

时间区间决定比较/覆盖范围，不应被错误塞进 dimension hash。

### 4.1 dimensions

对价格/产能/产量/需求等必须尽量保存：

- product spec；
- geography；
- spot/contract/list/auction/index；
- tax/freight/incoterm；
- currency；
- frequency；
- statistical scope。

口径不完整时不得自动互证或冲突。

### 4.2 trusted fact

AI 不能直接写 `TRUSTED`。

```text
FactAssertion
→ quality/comparability
→ reconciliation evaluation
→ resolution
→ canonical_fact_version
```

高影响 predicate 可以要求更高来源质量和独立来源数量。

---

## 5. Judgment / Expectation 契约

`research.judgment_assertions` 与 Fact 分表。

保存：

- speaker entity/name/role/affiliation；
- subject；
- topic/predicate；
- judgment kind；
- target time；
- value/interval/date/direction/text；
- expressed probability（若原文明确）；
- source published/known time；
- extraction provenance。

### 5.1 rationale

`judgment_rationales` 允许：

```text
premise
mechanism
condition
risk
caveat
counterargument
```

只允许原文明确表达或有 Evidence 的 rationale 进入历史层；模型自己的后来解释不能伪装成当时理由。

### 5.2 revision

`judgment_relations` 用：

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

旧 Judgment 不更新。

### 5.3 expectation snapshot

Snapshot 是派生 artifact，不是 Fact。

必须保存：

- knowledge cutoff；
- target time；
- aggregation method/version；
- member judgments；
- weight；
- dispersion/confidence。

---

## 6. Outcome 契约

`judgment_outcome_evaluations` 连接：

```text
historical Judgment
↕
canonical Fact version
```

允许保存：

- numeric error；
- relative error；
- timing error；
- direction correctness；
- realization status；
- explanation。

Outcome Evaluation 可以随着 Canonical Fact 版本变化重新生成，但原始 Judgment 不变。

---

## 7. Model Prior 契约

### 7.1 model_prior_runs

每次模型记忆运行必须保存：

- industry；
- run mode；
- source visibility；
- provider/name/version；
- protocol version；
- declared model knowledge cutoff（若可得）；
- archive knowledge cutoff（如适用）；
- prompt/output digest；
- raw output。

允许 run mode：

```text
blind_recall
memory_exhaustion_pass
atlas_refinement
gap_audit
association_expansion
conflict_audit
self_verification
refresh_diff
```

`self_verification` 必须与 blind recall 分 run。

### 7.2 source visibility

```text
none
archive_only
archive_summary
search_results
```

只有 `none` 可以作为真正独立 blind prior。

看到过 `search_results` 的 run 不能回头被描述成 blind recall。

---

## 8. Memory Lead 契约

`research.model_memory_leads` 保存未举证线索。

典型 lead kind：

- landmark/missing event；
- actor/terminology；
- metric/mechanism；
- pricing rule/contract change；
- process bottleneck/project pattern；
- inventory pattern/capital cycle；
- policy/technology shift；
- cross-industry dependency；
- narrative/causal hypothesis/anomaly。

每条保存：

- approximate historical period；
- recalled details；
- suggested queries/source types；
- memory confidence；
- importance/novelty/searchability。

`memory_confidence` 只是“模型觉得自己多像记得”，不是事实概率。

Memory Lead 没有任何直接 FK/流程可把它发布成 Canonical Fact。

---

## 9. Memory Lead Relation

`model_memory_lead_relations` 保存探索图：

```text
associated_with
possible_cause
possible_effect
predecessor
successor
search_synonym
same_episode
cross_chain_link
possible_revision
```

这些边同样不是因果事实，只用于搜索和历史目录组织。

---

## 10. Claim-scoped Authority 契约

`evidence.source_authority_profiles` 不能只给网站一个全局等级。

Profile 至少绑定：

```text
publisher/source
claim_scope
authority_class
authority_basis
validity period
rationale
```

Claim scope 例如：

```text
legal_disclosure
official_statistic
self_statement
management_guidance
market_measurement
project_status
policy_text
third_party_fact
industry_expectation
technical_specification
```

Authority class：

```text
authoritative_primary
primary_self_statement
methodological_primary
reputable_secondary
secondary
discovery_only
```

“正规机构”也只对匹配 scope 的陈述有高证明力。

---

## 11. Memory disagreement 契约

Memory Lead 与 archived Evidence 比较后可产生：

```text
supports
contradicts
context
weak_match
unrelated
```

但是否能裁决还取决于：

- claim scope 是否匹配；
- authority class；
- independence cluster；
- 是否存在 authoritative conflict。

Resolution 允许：

```text
unresolved
seek_primary
primary_supports_lead
primary_contradicts_lead
authoritative_conflict
secondary_only_support
secondary_only_contradiction
scope_mismatch
retired
```

错误 Memory Lead 不删除。

---

## 12. Memory Campaign 契约

### 12.1 Campaign

`research.model_memory_campaigns` 保存：

- industry；
- historical period；
- campaign kind；
- model provider/name/version；
- declared knowledge cutoff；
- protocol/manifest version/digest；
- source visibility。

Campaign 本身 immutable。

### 12.2 Campaign Runs

`model_memory_campaign_runs` 把多个 `model_prior_run` 组织成一个 campaign：

- pass id/family；
- round；
- parent run；
- phase；
- new/duplicate/high-importance-new lead counts；
- coverage delta。

### 12.3 Coverage

`model_memory_coverage_cells` 是 versioned snapshot，不允许覆盖旧 coverage。

维度可包括：

- time；
- chain node；
- actor；
- metric；
- mechanism；
- narrative；
- terminology；
- failure；
- cross-industry；
- negative space。

### 12.4 Seal

Blind campaign 完成后新增 `model_memory_campaign_seals`。

Seal 是独立 immutable 事件，避免“先创建 Campaign 后又必须 UPDATE sealed=true”的生命周期冲突。

Seal 保存：

- sealed at；
- stop reason；
- coverage summary；
- lead counts；
- output digest。

---

## 13. Self Verification 契约

Search-enabled 高级模型只能在 blind atlas seal 后进入第二阶段。

`MemorySelfVerificationGateway` 可以返回：

- refined summary；
- candidate URLs；
- refined queries；
- possible primary sources；
- notes。

这些仍然是 Discovery Output。

Candidate URL 必须经过：

```text
Source fetch
→ ArchiveStore
→ SourceDocument
→ EvidenceFragment
```

才有资格进入 authority/evidence 判断。

---

## 14. Delegated Verification Task 契约

`ops.memory_verification_tasks` 只能引用 `model_memory_campaign_seals(campaign_id)`，也就是只有封存后才能正式派发历史验证任务。

Task 保存：

- lead；
- claim scope；
- actors/aliases；
- query families；
- preferred primary sources；
- support/contradiction criteria；
- minimum search depth；
- cutoff；
- operational status。

这是少数允许状态 UPDATE 的 operational object，不属于 immutable research history。

默认 completion gate 由 application 的 `verification_depth_satisfied()` 执行。

---

## 15. Model Refresh 契约

`model_memory_refreshes` 只允许比较**已经 sealed**的 baseline/refresh campaign。

`model_memory_refresh_lead_diffs`：

```text
known
refined
novel
possible_regression
ambiguous_match
```

并保存：

- baseline lead（若匹配）；
- semantic similarity；
- archive coverage state；
- refinement payload；
- backfill priority。

新模型输出不能覆盖旧模型输出。

---

## 16. Historical not-found 契约

对于历史任务：

```text
not_found != false
```

Agent/模型搜索失败只能产生：

```text
unresolved / not_yet_verified
```

只有 matching claim scope 的 authoritative/primary Evidence 明确反驳，才允许 `primary_contradicts_lead`。

---

## 17. Current Collection 契约

Current source watchlist 不是 Fact 表，而是采集操作配置。

每个 source 至少需要：

- stable source id；
- publisher/domain/channel；
- priority；
- expected cadence；
- expected materials；
- material roles；
- claim scopes；
- archive policy；
- stale threshold。

Agent 每次运行必须输出 due-source completion / failure / source-health 结果。

锂电第一版：`docs/research/lithium-battery-current-watchlist.json`。

---

## 18. 不可变与可变对象

### append-only / immutable

- raw content blob；
- document/fetch version；
- parsing artifact；
- evidence fragment；
- fact assertion；
- reconciliation evaluation；
- judgment/rationale/relation；
- outcome evaluation；
- model prior run；
- memory lead/relation/evidence link/disagreement resolution；
- memory campaign/run membership/seal/coverage snapshot；
- model refresh/diff；
- audit log。

### operational mutable

- collection job/lease；
- retry/heartbeat；
- memory verification task status；
- current source health；
- scheduler state。

历史研究对象与运行状态不能混成一张“方便更新”的表。

---

## 19. 幂等契约

幂等 key 应包含真正决定输出的版本：

- document hash；
- parser producer/version/input hash；
- extractor/model/prompt/schema；
- normalizer/reconciler/rule fingerprint；
- Memory Campaign manifest/protocol/model vintage；
- self-verification protocol；
- refresh comparator version。

同样输入/版本重放应得到同样 identity 或安全 no-op。

---

## 20. 第一行业的 Schema 验证原则

锂电历史是 schema 的压力测试，不是 schema 的展示样品。

如果真实资料暴露：

- 项目 identity 不够；
- 名义/有效产能不够；
- 旧称/actor 关系表达不了；
- Judgment target time 不够；
- 价格口径不够；
- Memory Lead 无法转成可执行搜索 task；

应修改 schema，而不是把真实产业信息硬塞进 `metadata`。