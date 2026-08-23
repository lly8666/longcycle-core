# Longcycle 产业记忆核心架构

本文定义 `longcycle-core` 的长期架构方向。Longcycle 不是“爬虫 + LLM + 数据库”，也不是自动研报系统；它要建立一个可以跨多年、按历史知识边界回放的产业记忆。

```text
Reality      当时真实发生了什么
Judgment     当时的人如何判断未来，为什么
Outcome      后来发生了什么，与此前 Judgment 有何关系

Model Prior / Memory Atlas
             研究侦察层，只回答“应该去找什么”
```

## 1. 历史恢复与当前采集是两条路线

### Historical Recovery

```text
Memory Exhaustion Campaign
→ sealed blind Memory Atlas
→ high-model self verification / search discovery
→ claim-scoped verification tasks
→ source identity + claim-relevant content verification
→ Evidence / Assertion / Reconciliation
→ optional later raw-byte materialization
```

Fresh search 不能污染未 seal 的 blind run；Memory Lead 永远不能直接发布 Fact/Judgment；`not_found != false`。

### Current Collection

```text
source watchlist
→ scheduled/event discovery
→ preserve readable content / source locator immediately
→ detect role + revision
→ Grounded Evidence
→ Reality / Judgment / Outcome
→ optional later raw-file materialization
```

“preserve now”要求今天可读、可定位、可证明的信息不要丢失；不要求因为 byte-identical PDF 下载困难而阻塞主路径。

## 2. 依赖方向

```text
domain
  ↑
ports
  ↑
application
  ↑
adapters
```

Domain/epistemic semantics 不能依赖 GitHub Release、Google Drive、某个数据库、某个模型供应商或某个下载 host。

- **domain**：Fact/Time/Dimensions、Judgment/Outcome、Memory Lead、source/evidence identity 等稳定语义。
- **ports**：SourcePlugin、ArchiveStore、ModelGateway、ResearchRepository、EpistemicMemoryReader、Queue/Checkpoint/EventSink。
- **application**：archive/preserve、Grounded Evidence、normalization/reconciliation、Judgment projection、memory campaign、replay、research orchestration。
- **adapters**：HTTP/local/materialized source、PostgreSQL、filesystem/S3、DuckDB、CLI/workflow。

## 3. Source document 不是“一个 URL + 一个 raw blob”

Longcycle 把 logical source document 与 material completeness 分开：

```text
logical document identity
├─ locator_verified
├─ content_verified
│   └─ one or more faithful readable/material representations
└─ materialized
    └─ explicitly verified raw upstream bytes
```

### `locator_verified`

确认 publisher/upstream document identity、URL、文件名/标题/日期等。对于主流官方、监管、issuer、机构站点，这足以接受 source document 真实存在。

Locator 本身不能证明尚未读到的 claim。

### `content_verified`

Agent 已实际读到 claim-relevant 内容并保存了 faithful representation、locator 与 provenance。该 representation 可以形成 immutable `content_blob/document_version` 和 Evidence lineage，即使 upstream raw PDF bytes 尚未 materialize。

必须保存 upstream media identity，例如：

```text
source_media_type = application/pdf
representation content_type = text/plain
source_capture_state = content_verified
raw_source_materialized = false
content_verification_mode = interactive_pdf_read
claim_relevant_content_preserved = true
```

这不是“把 txt 假装成 PDF”；恰恰相反，它显式保存“上游是 PDF、当前归档的是忠实 readable representation”。

### `materialized`

只有 raw upstream source bytes 被实际取得并完成 identity/content verification 后才进入。`document_version` 的存在本身不再意味着 raw materialized。

Migration 0028 移除了这种错误等价；0029 让 representation provenance 在 fetch/document persistence 时保持 `content_verified`；`PostgresSourceLocatorRegistry.mark_materialized()` 是显式、raw-version-scoped 的升级。

## 4. Evidence-first 真值边界

可发布 Reality/Judgment 必须回到实际被保存和验证的 source-derived content：

```text
publisher / upstream document identity
→ verified locator
→ preserved source-derived material
→ immutable document version / artifact
→ exact EvidenceFragment + locator
```

“preserved source-derived material”可以是：

- raw HTML/PDF/JSON/attachment；
- deterministic parser artifact；
- 已实际读到 PDF 内容形成的 truthful readable representation；
- readable webpage 的 faithful claim-scoped visible-text capture。

它不能是：

- 搜索摘要；
- AI 回答；
- 只确认存在但没读到内容的 PDF locator；
- 记者/平台二次加工字段冒充原公告原文。

### Fact / Reality

```text
Evidence
→ FactAssertion
→ normalize / comparability
→ reconcile
→ CanonicalFactVersion
```

### Judgment

```text
Evidence
→ JudgmentAssertion
→ rationale / condition / caveat
→ revision / reaffirm / withdraw
→ ExpectationSnapshot
```

### Outcome

```text
historical Judgment
↕ explicit semantic relation
later Canonical Reality
→ OutcomeEvaluation
```

多个 Judgment 一致不是 Fact；后来 Outcome 不得修改原 Judgment。

## 5. Claim-scoped authority

Authority 不由 host、`.pdf` 后缀、Drive/Release transport 或搜索排名决定。

同一 document 可对不同 claim scope 有不同 authority：

- 监管机构：对应 legal/regulatory state；
- issuer：自己的正式 self statement / management guidance；
- registry/statistical body：其制度定义的登记/统计字段；
- methodological producer：自己生产的市场 measurement；
- reliable media：secondary/corroboration，不能自动继承上游 primary authority。

Authoritative redistributor 可以作为 retrieval lane，但必须同时保存 retrieval host 与 upstream document identity；同一上游文档多个镜像仍是一个 evidence cluster。

## 6. 时间架构

至少分开：

```text
valid/effective time     世界里何时发生/适用
known time               当时观察者最晚何时能够知道
expectation target       Judgment 针对哪个未来区间
capture/retrieval time   Longcycle 今天何时取得材料
```

No-lookahead 使用保守 source-supported known-time upper bound。发生时间可以 month/quarter/range，不能为了排序制造 exact timestamp。

## 7. PostgreSQL 四 schema

### `core`

稳定 identity/taxonomy/entity/product/facility/unit/predicate/dimension semantics。

### `evidence`

- publishers / source connectors；
- logical documents；
- locator/content/materialization lifecycle metadata；
- content blobs / fetches / document versions；
- artifacts / EvidenceFragments；
- extraction/model/schema/prompt provenance；
- claim-scoped authority profiles。

### `research`

- FactAssertion / CanonicalFactVersion；
- Judgment / Rationale / ExpectationSnapshot；
- Outcome；
- project/event/domain series；
- Model Prior / Memory Lead / disagreement；
- campaign/seal/refresh/hypothesis assessment。

### `ops`

queue/lease/retry/dead letter/checkpoint/review/outbox/cost/source health/audit/verification tasks。

## 8. PostgreSQL / DuckDB / ArchiveStore

### PostgreSQL

当前 live transactional write/ops engine。负责 transaction、constraints、leases、outbox、source/evidence writes。Session handoff 不搬运 live cluster。

### ArchiveStore

保存实际进入 Longcycle 的 immutable material bytes：它可能是 raw upstream bytes，也可能是明确标注的 source-derived representation。ArchiveStore 证明“Longcycle 实际保存了哪些 bytes”，不自动证明这些 bytes 是 upstream raw source。

### DuckDB

用于 bounded portable research/replay materialization，也可作为网页 capture capsule。Handed-off generation 默认 read-only。DuckDB 不替代 live PostgreSQL，也不改变 Evidence authority。

## 9. Research orchestration

CAP-0007 只负责执行阶段，不负责历史发现或下载 transport。

### v2（当前默认）

```text
outer adapter / Agent prepares local material root
→ verify every material path + SHA declared by Evidence spec
→ explicit repair overlay if any
→ Grounded Evidence
→ optional Reality projection
→ receipt + immutable path guards
```

外层 material root 可以来自：

- webpage capture DB 导出；
- content-verified PDF readable representation；
- 已有 legacy Release raw source；
- later normal-network raw materialization；
- 其他明确、可验证 transport。

Execution contract 不要求 GitHub Release，也不要求新 PDF raw download。

### v1（legacy replay）

旧 `research-orchestration/v1` 仍验证 GitHub Release source-pack outer SHA 与内部 material SHA，以保持历史 receipt 可重放。它是兼容层，不是新架构默认。

## 10. Current Collection

每次 current collection：

```text
check due high-value sources
→ discover new/revised documents
→ preserve readable content or verified locator immediately
→ record source state
→ Ground claims only when content was actually read/preserved
→ track revisions / guidance / policy / projects
→ queue deferred raw materialization only when useful
```

PDF raw-byte下载失败不是 source absence，也不是默认 blocker。只有 claim 依赖未读内容、representation integrity 失败、或 later raw materialization 与 earlier verified content 冲突时 fail closed。

## 11. Immutability

不可静默覆盖：

- sealed blind memory output；
- raw source materializations；
- preserved readable representations；
- document versions / EvidenceFragments；
- FactAssertions / Judgments；
- reconciliation evaluations；
- historical replay receipts；
- source identity/provenance history。

状态升级是 append/enrichment；冲突进入 repair/reconciliation，不通过覆盖消失。

## 12. 架构演进原则

- 真实 benchmark 暴露 truthful representation gap 后再扩 schema；
- Capability Registry 保证一个稳定语义只有一个 owner；
- Repair Memory 保证高风险修复不被未来 cleanup 反向破坏；
- transport friction 不得变成产品 roadmap；
- researcher 能否恢复“当时发生什么、当时怎么想、后来怎样”比 crawler throughput 或下载成功率更接近最终成功标准。
