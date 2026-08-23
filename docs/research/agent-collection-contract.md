# Longcycle 历史资料采集 Agent 协议

本文定义外部/低成本采集 Agent 给 Longcycle 回传历史资料时必须遵守的规则。Agent 的职责是忠实恢复**当时存在的 source material、source identity、locator、时间和可读内容**，不是替 Longcycle 做最终研究判断。

## 1. 两种模式

### Mode A：Discovery

负责：

1. 找候选原始资料；
2. 确认 publisher、title、date、URL、document identity/type；
3. 判断材料可能包含 Reality / Judgment / Policy 等；
4. 标记值得复核的页码/章节/表格；
5. 如果 raw file 已实际下载，计算 SHA-256；
6. 如果 raw file 没下载但 locator/content 可确认，照实回传对应状态；
7. 返回访问失败、缺失和不确定项。

Discovery Agent 不得计算衍生指标、补缺失值、把后来结果写回早期材料、把搜索摘要当原文、或因为多个转载一致就制造“事实”。

### Mode B：Extract-light

只有任务明确要求时执行。在 Discovery 基础上摘录文档中的明确陈述，但仍不做 normalization/reconciliation。

每条 claim 必须带精确 locator。找不到 locator 就只回传文档，不回传结构化 claim。

## 2. PDF 三态是强制 source-completeness 语义

```text
locator_verified
→ content_verified
→ materialized
```

### `locator_verified`

确认 PDF/document identity 与 locator，例如：

- publisher/upstream identity；
- URL；
- file name（能确定时）；
- title/date/document number；
- verification mode/time。

对于主流官方、监管、issuer、机构站点，这足以说明“这份文档真实存在”。**不要为了证明 downloader 能不能工作而启动新的 GitHub Actions。**

但是：只看到链接、没实际读到 claim-relevant 内容时，不能回传 claim 作为可 Ground Evidence；此时 claims 应为空或明确保持 discovery-only。

### `content_verified`

Agent 已通过可信界面实际读到 claim-relevant PDF 内容，并保存了页码/章节/摘录或等价 faithful readable representation。

必须回传：

```text
source_media_type = application/pdf
source_capture_state = content_verified
materialization_status = pending_materialization
content_verification_mode
claim_relevant_content_preserved = true
readable_representation_sha256
```

此状态可以支持后续 Grounded Evidence，即使 `downloaded_file=null`、raw PDF SHA 未知。

不得把 readable representation 的 SHA 写成 raw PDF SHA，也不得把 representation content type 伪装成 `application/pdf`。

### `materialized`

只有 raw PDF bytes 实际取得并验证 document identity/content 后使用：

```text
source_capture_state = materialized
materialization_status = materialized
raw_materialized_sha256
raw_materialized_storage_locator (若已有 durable locator)
```

Later materialization 与 earlier content/identity 冲突时必须 fail closed。

## 3. 来源等级仍按 claim scope 判断

### Reality hint

| 等级 | 含义 | 典型来源 |
| --- | --- | --- |
| R1 | 一手/制度性原始记录 | 政府、监管、交易所、法定披露、审批/环评原文 |
| R2 | 稳定方法的原始生产者 | 协会、价格评估、专业数据库、研究机构原始统计 |
| R3 | 可靠二手整理 | 券商、主流媒体、行业媒体 |
| R4 | discovery only | 聚合、自媒体、论坛、无来源截图、AI summary |

### Judgment hint

| 等级 | 含义 | 典型来源 |
| --- | --- | --- |
| E1 | 判断主体自己的原始表达 | management guidance、券商自己的报告、协会自己的预测 |
| E2 | 可核验直接采访/演讲 | transcript、官方采访 |
| E3 | 可靠二手转述 | 主流媒体引用 |
| E4 | 无法核验原始说法 | 聚合/截图/AI summary |

这些只是 Agent hint。最终 authority 由 claim scope + upstream identity + provenance 决定。`.pdf`、下载 host、Drive/Release transport 都不会自动升级 authority。

## 4. 时间纪律

至少记录：

- `published_at`；
- `first_known_at`；
- `retrieved_at`；
- `knowledge_cutoff`（任务指定时）；
- `date_uncertain`。

不能用后来页面/报告替代历史原始 Judgment，也不能把当前 retrieval time 当历史 publication time。历史 known-time 不足时使用保守上界，不猜 exact timestamp。

## 5. 原文与转载

优先顺序：

1. 政府/监管/交易所/公司/协会原始页面或正式文档；
2. authoritative redistributor 保存的可核验正式公告/PDF；
3. 原始研究机构/数据生产者；
4. 主流媒体首发；
5. 普通转载。

Redistributor 必须同时保存：

```text
retrieval host
upstream publisher/document identity
```

同一 upstream PDF 的多个镜像是一个 evidence cluster。

## 6. 文档级 JSONL 回传

新记录使用 `docs/research/agent-document-record.schema.json` v2。示例：

```json
{
  "task_id": "LB-001",
  "mode": "extract-light",
  "industry_path": ["lithium_battery", "upstream"],
  "topic": "project_status",
  "title": "正式标题",
  "publisher": "正式发布者",
  "document_kind": "exchange_filing",
  "published_at": "2022-08-01T00:00:00+08:00",
  "first_known_at": "2022-08-01T00:00:00+08:00",
  "retrieved_at": "2026-08-23T18:00:00+08:00",
  "date_uncertain": false,
  "knowledge_cutoff": null,
  "url": "https://example.com/filing.pdf",
  "alternate_urls": [],
  "is_repost": false,
  "source_origin_role": "primary_original",
  "reality_rank": "R1",
  "expectation_rank": "E1",
  "material_roles": ["reality", "expectation"],
  "source_media_type": "application/pdf",
  "source_file_name": "filing.pdf",
  "source_capture_state": "content_verified",
  "materialization_status": "pending_materialization",
  "verification_mode": "official_document_link_and_identity",
  "content_verification_mode": "interactive_pdf_read",
  "claim_relevant_content_preserved": true,
  "readable_representation_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "raw_materialized_sha256": null,
  "raw_materialized_storage_locator": null,
  "downloaded_file": null,
  "sha256": null,
  "access_status": "ok",
  "claims": [],
  "notes": "Raw PDF bytes deferred; URL and readable content verified."
}
```

## 7. Claim 回传

### Reality

```json
{
  "claim_role": "reality",
  "subject_text": "项目/公司",
  "predicate_hint": "capacity|production|price|inventory|sales|commissioned_at|other",
  "raw_value": "原文值",
  "raw_unit": "原文单位",
  "valid_period_text": "原文时间",
  "statement": "短摘录",
  "locator": "page:12/table:3",
  "confidence": "high"
}
```

### Judgment

```json
{
  "claim_role": "judgment",
  "speaker_text": "判断主体",
  "speaker_role": "management",
  "judgment_kind": "guidance",
  "subject_text": "对象",
  "topic": "commissioning",
  "target_period_text": "2023Q4",
  "raw_expected_value": "计划投产",
  "probability_text": null,
  "statement": "短摘录",
  "locator": "page:8",
  "rationales": [],
  "confidence": "high"
}
```

`rationales` 只能放原文明确表达的 premise/mechanism/condition/risk/caveat/counterargument，不能放 Agent 自己的推理。

## 8. Search log

每个任务都必须回传实际搜索路径，即使没找到：

```json
{
  "task_id": "LB-001",
  "search_log": {
    "queries": ["实际 query"],
    "domains_checked": ["example.gov"],
    "date_range": ["2021-01-01", "2022-12-31"],
    "result": "found|partial|not_found|blocked",
    "missing_targets": [],
    "notes": "访问限制/异常"
  }
}
```

`not_found` 不等于 false。

## 9. 去重

有 raw bytes 时优先：

```text
upstream publisher/document identity + raw_materialized_sha256
```

未 materialized 时：

```text
upstream publisher + canonical URL + title/document number + published date
```

同一报告 initial/revised、同项目不同里程碑、同一主体不同时间的 guidance 都不得合并。

## 10. 绝对禁止

- 伪造 URL/title/page/date；
- 搜索 snippet 当原文；
- AI 回答当 source；
- `locator_verified` 冒充 claim Evidence；
- readable text representation 冒充 raw PDF；
- raw download 失败冒充 source 不存在；
- 为下载 PDF 创建新的 acquisition Action；
- later outcome 回写历史 Judgment；
- planned/actual、capacity/output、sales/demand 等语义混淆；
- 多个同源转载伪装成独立 corroboration。

Agent 的价值不是“把文件都下载下来”，而是**忠实地把可验证的历史 source identity、内容、locator 与完整性状态搬回来**。
