# Longcycle Core

Longcycle 是一个**可按历史时点回放的产业长期记忆系统内核**。目标不是自动生成更多研报，也不是把网页抓取数量当成果，而是长期保存：

```text
Reality      当时真实发生了什么
Judgment     当时的人如何判断未来、为什么
Outcome      后来发生了什么，和此前 Judgment 有何关系
```

核心认识：

> **历史本身就是分析。**
>
> 对历史恢复：`memory-first, Evidence-final`。
>
> 对当下采集：`source-first, preserve-now`。

## 第一性边界

1. **Evidence 决定可发布历史。** 搜索结果、AI 摘要和 Model Memory 只能发现线索，不能直接成为 Fact/Judgment。
2. **Reality 与 Judgment 分开。** “公司当时预计 X”是真实的历史 Judgment，不等于 X 后来真的发生。
3. **No-lookahead。** 历史 replay 只能使用当时已经可知的信息；后来结果不能回填早期判断。
4. **权威按 claim scope 判断。** 监管机构、issuer、行业机构、媒体各自只能在适合的 claim 范围内提供证明力。
5. **同源不等于独立 corroboration。** 同一原始公告/PDF 的多个镜像仍属于一个 evidence cluster。
6. **时间精度服从来源。** 不制造伪精度；known-time 仍使用保守、可证明的上界。
7. **运输方式不改变 authority。** GitHub Release、Google Drive、本地文件、对象存储只是 transport / materialization 手段。

## 历史恢复

```text
Blind Memory Exhaustion
→ saturation / seal
→ high-capability self-verification / search discovery
→ claim-scoped evidence tasks
→ source identity + claim-relevant content verification
→ Evidence / Assertion / Reconciliation
→ deferred raw-byte materialization where useful
```

Blind Memory Atlas 在 seal 前不能被本轮 fresh search 污染；`not_found != false`。Memory Lead 永远低于 Evidence。

## 当下采集

```text
source/watchlist
→ proactive collection
→ faithful content/version capture or verified source locator
→ Reality / Judgment extraction
→ revision tracking
→ raw-file materialization when useful/available
```

`preserve-now` 的第一要求是**不要丢失现在可读、可定位、可证明的 source information**，而不是为了 byte-identical 下载阻塞研究。

## PDF：identity / content / raw bytes 分开

PDF 使用三个显式状态：

```text
locator_verified
→ content_verified
→ materialized
```

### `locator_verified`

已经确认 publisher/document identity、原始 URL、文件名（能确定时）、title/date/文档号等。对于主流官方、监管、issuer、机构网站，这足以承认“这份 source document 确实存在”，不需要再证明某个 GitHub runner 能下载它。

**但只确认链接存在不能证明具体 claim。**

### `content_verified`

当前 Agent 已通过可信界面实际读到 claim-relevant 内容，并保存了页码/章节/摘录或等价的忠实 readable representation。此时可以进入 Grounded Evidence，即使 raw PDF bytes 尚未下载。

忠实文本表示必须保留：

- upstream PDF identity / URL；
- `source_media_type = application/pdf`；
- truthful `content_verification_mode`；
- `claim_relevant_content_preserved = true`；
- representation byte/text digest；
- 不能把 text representation 伪装成 raw PDF。

### `materialized`

以后有正常网络的 Agent 再下载 raw PDF，验证 document identity 与此前 content，补 raw size / SHA-256 / durable storage locator。这个状态是 completeness/integrity enrichment，不是 Evidence 的前置条件。

如果 later raw bytes 与 earlier `content_verified` 身份/内容冲突，必须 fail closed，不能静默覆盖。

**不要创建 GitHub Actions 仅仅为了下载新 PDF。** Actions 仍然可以用于 PostgreSQL、CI、runtime execution。已经存在的 Release source packs 是可复用的历史 materialization，但不是新 PDF 的默认 acquisition 路径。

## 网页：本地 capture DB → Google Drive

对当前 Agent 可以完整读取的网页：

```text
interactive read
→ faithful claim-scoped visible text + provenance
→ bounded local DuckDB/SQLite capture capsule
→ checkpoint / SHA-256
→ Google Drive handoff
```

网页 capture DB 是 source-derived capture/handoff envelope，不是 live PostgreSQL，也不会自动发布 Fact/Judgment。不要为了网页 HTML 专门启动 Actions，也不要为每一页正文制造 Git commit。

## 数据与存储架构

PostgreSQL 使用四个 schema：

```text
core      稳定身份、分类、产品、设施、单位、predicate
evidence  publisher/source/document/material/artifact/Evidence/provenance
research  Reality + Judgment + Outcome + Model Memory
ops       queue/lease/checkpoint/review/outbox/audit
```

长期语义上需要区分：

```text
logical source document
├─ verified locator
├─ one or more preserved readable/material representations
└─ optional verified raw-source materialization
```

一个 readable representation 可以形成 `document_version` / Evidence lineage，但这**不等于** raw PDF 已 materialized。Migration 0028/0029 与 `PostgresSourceLocatorRegistry` 专门守住这个区别。

### Grounded Evidence

```text
preserved source-derived material
→ immutable archived representation/version
→ exact locator / artifact verification
→ EvidenceFragment
```

Evidence 阶段本身创建 **0 FactAssertions / 0 Judgments**；Reality/Judgment 必须由后续显式 projection/reconciliation 产生。

### Reality

```text
Evidence
→ FactAssertion
→ normalize / comparability
→ reconciliation
→ CanonicalFactVersion
```

### Judgment / Outcome

```text
Evidence
→ JudgmentAssertion + rationale / revision
→ Expectation snapshot
→ later Reality
→ OutcomeEvaluation
```

Outcome 不能改写原 Judgment。

## Research orchestration

`research-orchestration/v2` 是 transport-neutral execution contract：调用方先准备一个本地 material root，里面可以混合：

- Drive webpage capsule 导出的 claim-scoped readable material；
- 已存在的 legacy Release raw files；
- 直接保存的 content-verified readable representation；
- later normal-network Agent materialized 的 raw files。

然后执行：

```bash
longcycle --json research run \
  path/to/research-orchestration-v2.json \
  --material-root path/to/prepared-material \
  --work-dir .longcycle/run-work \
  --output .longcycle/run-receipt.json
```

Longcycle 会验证 Evidence spec 声明的每份 material SHA-256，再执行 Grounded Evidence / optional Reality projection。transport restore 不进入 epistemic authority。

历史 `research-orchestration/v1` + `--source-pack` 仍然支持，以保证旧 Release-based receipts 可重放；它是 **legacy compatibility**，不是新研究必须经过的入口。

## 当前实现方向

已经具备的核心能力包括：

- PostgreSQL 四层 schema 与 migration runner；
- immutable/archive abstraction；
- Grounded Evidence 与 exact locator integrity；
- Fact normalization / reconciliation / canonical Reality；
- Judgment / Expectation / Outcome；
- Model Memory campaign / seal / post-seal verification；
- point-in-time no-lookahead replay；
- PostgreSQL ↔ portable DuckDB replay materialization；
- source locator/content/materialized lifecycle；
- repository-backed session handoff、Capability Registry、Repair Memory；
- transport-neutral research orchestration v2 与 legacy v1 replay。

当前行业 benchmark 只是跨行业架构的 proving ground，不是 Longcycle 的终局。

## Fresh session

新的 Agent 不应从 README 猜 live task。按以下入口恢复：

1. `FRESH_AGENT_BOOTSTRAP.md`
2. `CONTINUE_HERE.md`
3. `.longcycle/handoff/current.json`
4. live PR HEAD / CI

不要让用户重复已经持久化的背景。
