# Longcycle 产业记忆核心架构

本文定义 `longcycle-core` 的长期架构方向，并明确区分历史恢复、当前采集、证据、事实、预期和模型先验。

Longcycle 不是“爬虫 + LLM + 数据库”，也不是自动生成研报的系统。它的目标是建立一个可以跨十年以上时间回放的产业记忆。

核心时间线：

```text
Reality      当时真实发生了什么
Expectation  当时的人认为未来会发生什么，为什么
Outcome      后来实际发生了什么，预期与现实为何偏离
```

额外存在一个永远不可直接发布的研究侦察层：

```text
Model Prior / Memory Atlas
```

它保存高级模型今天对历史的模糊记忆、联想、旧术语和缺口判断，只用于告诉系统“应该去找什么”，不是历史证据。

---

## 1. 核心认识：过去与现在必须用不同采集架构

### 1.1 Historical Recovery

旧互联网不是完整数据库：历史网页消失、附件迁移、搜索引擎偏新、旧术语失效、付费资料不可索引、失败项目和边缘参与者逐渐退出公共叙事。

因此历史恢复默认：

```text
Memory-first
→ Evidence-final
```

完整路径：

```text
Memory Exhaustion Campaign
→ Sealed Blind Memory Atlas
→ High-model Self Verification
→ Delegated Verification Tasks
→ Source fetch/archive
→ Evidence
→ Fact / Judgment
```

### 1.2 Current Collection

对今天仍在线的资料，不能寄希望于未来模型记得，也不能等几年后再用搜索引擎抢救。

默认：

```text
Source-first
→ Archive-now
```

路径：

```text
Source Watchlist
→ scheduled/event discovery
→ fetch original HTML/PDF/attachment
→ archive immediately
→ detect role/revision
→ extract Fact/Judgment
→ update source inventory
```

---

## 2. 依赖方向

继续保持：

```text
domain
  ↑
ports
  ↑
application
  ↑
adapters
```

核心语义不能依赖具体数据库、对象存储、模型供应商或搜索服务。

### domain

保存：

- Fact/Time/Dimensions 等已有不可变领域对象；
- Memory Lead；
- claim scope；
- authority class；
- evidence stance；
- memory audit disposition。

### ports

保存可替换边界：

- SourcePlugin；
- ArchiveStore；
- ModelGateway；
- MemoryPriorGateway；
- MemorySelfVerificationGateway；
- ResearchRepository；
- Queue/Checkpoint/EventSink/Telemetry。

`MemoryPriorGateway` 只能做 prior-only recall，不应静默混入 fresh search。

`MemorySelfVerificationGateway` 是第二阶段 search-enabled 高级模型接口；它输出 candidate URL / refined query / possible primary source，仍然不是 Evidence。

### application

负责业务 primitive：

```text
archive_document
parse_document
extract_facts
extract_judgments
normalize_assertions
reconcile_facts
persist_judgments

run_memory_pass
assess_memory_saturation
seal_memory_campaign
self_verify_memory_leads
compile_verification_tasks
adjudicate_memory_lead

build_expectation_snapshot
evaluate_outcomes
```

同步 CLI、异步 worker 和未来 service 只能负责 orchestration，不能复制业务语义。

---

## 3. Evidence-first 真值边界

### 3.1 Evidence

任何可发布 Fact/Judgment 最终必须回到：

```text
publisher
→ source connector
→ fetch
→ immutable content blob/document version
→ parsing artifact
→ evidence fragment + locator
```

搜索摘要、模型回答、二手摘要、Memory Lead 都不能绕过这一层。

### 3.2 Fact

Fact 表达：

> 某来源声称现实世界是什么。

```text
Evidence
→ FactAssertion
→ normalize/comparability
→ reconcile
→ Resolution
→ CanonicalFactVersion
```

### 3.3 Judgment

Judgment 表达：

> 某个历史 actor 在某时点如何判断未来或不确定状态。

```text
Evidence
→ JudgmentAssertion
→ Rationale
→ Revision/Reaffirm/Withdraw
→ ExpectationSnapshot
```

多个 Judgment 一致只能形成更强 consensus，不能直接成为 Fact。

### 3.4 Outcome

目标期结束后：

```text
Judgment
↕
Canonical Reality
↓
OutcomeEvaluation
```

Outcome 允许重新计算，但不得修改原始 Judgment。

---

## 4. Model Memory 不是 Evidence

高级模型知识的价值在于：

- 广泛历史关联；
- 冷门 actor；
- 项目旧称；
- 当年术语；
- 定价和合同机制；
- 工程瓶颈；
- 库存位置；
- 资本循环；
- 跨行业影响；
- 对“时间线缺了什么”的异常感。

但模型无法可靠提供训练资料 provenance，也可能产生错误记忆。

因此：

```text
Memory Lead may challenge archive
Memory Lead may generate search
Memory Lead may open disagreement
Memory Lead may NEVER publish Fact/Judgment
```

---

## 5. Memory Exhaustion Campaign

“让高级模型输出几乎所有行业记忆”不能靠一个大 prompt。

一个 Campaign 由大量正交 Pass 组成。

### 5.1 Blind Pass families

锂电第一版包括：

- time slice；
- chain slice；
- actor exhaustion；
- metric exhaustion；
- mechanism exhaustion；
- contemporaneous narrative；
- old vocabulary；
- failure/dead-end；
- reverse causality；
- cross-industry；
- counterfactual；
- negative space；
- saturation review。

### 5.2 Recursive lead expansion

高重要度 lead 继续追问：

```text
Who else?
What preceded it?
What followed it?
What was it called then?
```

目标是把模糊记忆变成可验证历史坐标。

### 5.3 强制长尾

Recall 输出必须刻意区分：

```text
obvious_landmarks
long_tail_leads
forgotten_actors
mechanism_leads
search_keys
uncertain_fragments
```

避免所有 token 都被著名事件占满。

### 5.4 Saturation

不能接受模型说“没有更多了”。

application 通过近似规则判断：

- 最近若干正交 pass 是否仍产生大量高重要度新 lead；
- coverage matrix 是否仍有大块空白；
- failure/terminology/forgotten actor/mechanism 等长尾 family 是否缺失。

### 5.5 Seal

Campaign 创建后允许追加 pass；blind recall 完成后插入独立 immutable seal：

```text
model_memory_campaigns
        ↓
model_memory_campaign_runs
        ↓
coverage snapshots
        ↓
model_memory_campaign_seals
```

Seal 保存：

- stop reason；
- coverage summary；
- lead count；
- high-importance count；
- output digest。

后续搜索不能修改 Campaign/Run/Seal。

---

## 6. High-model Self Verification

同一个高级模型可以在 blind atlas 封存后自己搜索。

这是一个新的 `model_prior_run`：

```text
run_mode = self_verification
source_visibility = search_results
```

它的职责：

- 把模糊名称变成准确名称；
- 找旧称/英文名；
- 找原报告/原公告候选；
- 判断网页是否转载同源；
- 设计更加具体的 query family；
- 发现可能 primary source；
- 给低成本 agent 编译任务。

它不能：

- 回改 sealed blind atlas；
- 把搜索结果直接写成 Fact；
- 因为搜不到删除 lead；
- 用网页数量多数投票。

Candidate URL 必须进入正常 SourcePlugin/fetch/archive 才能成为 Evidence。

---

## 7. Delegated Verification Task

历史低成本 Agent 接收：

```text
ops.memory_verification_tasks
```

任务只能引用已经 seal 的 campaign。

Task packet 至少包含：

- lead id；
- claim scope；
- lead summary；
- actor/alias；
- query families；
- preferred primary source；
- support criteria；
- contradiction criteria；
- minimum search depth；
- knowledge cutoff。

默认 minimum depth：

```text
>= 6 query families
>= 3 source types
primary domain checked
citation chased when present
reverse query for high-impact lead
```

正常结束：

```text
primary_verified
primary_contradicted
unresolved
```

`not_found` 不是 contradiction。

---

## 8. Claim-scoped Authority

来源不是全局分数。

`evidence.source_authority_profiles` 绑定：

```text
source/publisher
+ claim_scope
+ authority_class
+ authority_basis
+ validity period
```

典型：

- 公司公告：对 legal disclosure/self statement 强；
- 公司 forecast：仍是 management guidance，不是未来事实；
- 政府统计：对其方法论/统计 vintage 强；
- 券商原报告：对该券商当时 Judgment 强；
- 主流媒体：可能是 reputable secondary；
- 搜索摘要/聚合/AI summary：discovery only。

同一个原始报道的多个转载用 independence cluster 去重。

---

## 9. Memory disagreement

```text
Memory Lead
↕
Candidate web material
↓
claim-scope authority audit
```

状态包括：

- secondary_only_support；
- secondary_only_contradiction；
- seek_primary；
- primary_supports_lead；
- primary_contradicts_lead；
- authoritative_conflict；
- scope_mismatch。

最终 Fact/Judgment 仍走正常 evidence pipeline。

错误 Memory Lead 保留，用于长期评价模型作为历史目录生成器的表现。

---

## 10. Model Refresh / Backfill

模型更新不是覆盖旧结果，而是新的 research instrument vintage。

```text
Old sealed campaign
vs
New sealed campaign
↓
model_memory_refreshes
↓
lead diff
```

Diff：

- known；
- refined；
- novel；
- possible_regression；
- ambiguous_match。

然后与 archive coverage 再比：

```text
novel/refined lead
× archive gap
→ historical backfill priority
```

新模型可以重新打开旧年份。

---

## 11. Current Collection

Current Collection 与历史 Memory Campaign 独立。

### 11.1 Watchlist

行业维护 machine-readable source watchlist：

- publisher；
- domain/channel；
- expected cadence；
- priority；
- material types；
- claim scopes；
- archive policy；
- stale threshold。

锂电第一版见：

`docs/research/lithium-battery-current-watchlist.json`

### 11.2 每次运行

```text
check due P0 sources
→ discover documents
→ fetch/archive immediately
→ detect attachments/revisions
→ classify Reality/Expectation/Policy/Project
→ extract candidates
→ expand source inventory
→ record source health
```

Current Collection 的核心不是“今天有什么热点”，而是：

> 哪些资料如果今天不保存，未来最容易后悔？

---

## 12. PostgreSQL 四 schema

### core

稳定 identity/semantics：

- taxonomy；
- entities/aliases；
- products/specs；
- facilities/lines；
- units；
- predicates/dimension schemas。

### evidence

原始世界：

- publisher/source connector/subscription；
- content blob/document/fetch/version；
- parsing artifact；
- evidence fragment；
- extraction run；
- source authority profile。

### research

研究历史：

- fact assertions / canonical fact versions；
- metrics/projects/events/exposures；
- judgment/rationale/relation；
- expectation snapshot；
- outcome evaluation；
- model prior runs；
- memory leads/relations；
- disagreement/evidence links；
- memory campaigns/runs/seals/coverage；
- model refresh/diff。

### ops

运行状态：

- jobs/leases/attempts/dead letters；
- checkpoint；
- review；
- outbox；
- cost/budget；
- source health；
- audit；
- memory verification tasks。

---

## 13. 幂等与不可变

### Immutable

至少：

- raw blobs；
- document versions；
- evidence fragments；
- fact assertions；
- judgments；
- reconciliation evaluations；
- model prior runs；
- memory leads/relations；
- campaign definitions/run membership/seals；
- refresh diff；
- audit log。

### Mutable operational state

例如：

- queue lease；
- retry count；
- verification task status；
- source health。

必须严格区分 research history 和 operational state。

---

## 14. 当前实现状态

### 已有生产方向代码

- fact collection pipeline；
- archive/repository abstractions；
- normalization/reconciliation；
- queue/worker/checkpoint；
- PostgreSQL/S3/file adapters；
- memory domain/audit rules；
- recall/gap/memory-campaign prompt primitives；
- saturation/minimum-search-depth rules；
- MemoryPriorGateway / MemorySelfVerificationGateway contracts。

### 已有数据库设计

- 0013 Judgment/Expectation/Outcome；
- 0014 Memory Lead/Authority/Disagreement；
- 0015 Campaign/Seal/Refresh/Verification Task。

### 尚未实现

- production model adapter；
- full memory campaign persistence/orchestration；
- self-verification search → archive orchestration；
- verification task agent runner/import；
- scheduled current watchlist connectors；
- judgment extraction production path；
- generic PDF/OCR/Excel；
- real telemetry/outbox relay/API/UI。

---

## 15. 第一行业架构验证：锂电

第一版不是用架构完整性验收，而是用一个真实问题验收：

> 能否重建 2019–2026 锂电上中下游的 Reality、Expectation 和 Outcome，并让高级模型/产业人士难以再指出一个我们完全没想到且周期上重要的大类历史？

如果真实材料反复撞坏现有 schema，就改 schema；不要为了维护抽象而扭曲产业事实。