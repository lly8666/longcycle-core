# Longcycle 历史资料采集 Agent 协议

本文定义外部/低成本采集 Agent 给 Longcycle 回传历史资料时必须遵守的规则。目标不是让 Agent 做研究，而是让它稳定地找到**当时存在的原始材料**，并把材料的时间、来源、定位和角色描述清楚。

## 1. Agent 的职责边界

采集 Agent 分两种模式。

### Mode A：Discovery

只负责：

1. 找到候选原始资料；
2. 确认标题、发布者、发布日期、URL、文档类型；
3. 判断资料主要包含 Reality、Expectation 或两者；
4. 下载原文件时计算 SHA-256；
5. 标记可能有价值的页码/章节/表格位置；
6. 返回搜索失败、访问受限和不确定项。

Discovery Agent **不得**：

- 计算同比、环比、供需缺口、利润；
- 推断没有明确写出的产能、投产时间或市场份额；
- 把新闻记者总结改写成公司原话；
- 用后来发生的结果解释早期材料；
- 把多个来源拼成一个“事实”；
- 因为多个观点相同就写成事实；
- 为缺失日期、单位、规格或口径自行补值。

### Mode B：Extract-light

只有任务明确要求时才执行。在 Discovery 基础上，可以摘录文档中的明确陈述，但仍然不做调和、归一或后验判断。

允许提取：

- 明确数值、区间、日期、方向；
- 明确的项目里程碑；
- 明确的 forecast / guidance / target / commitment；
- 明确写出的理由、条件、风险、反方观点；
- 明确的修订、延期、撤回、重申。

每条摘录都必须带 locator。找不到精确 locator 就只返回文档，不返回结构化 claim。

## 2. 两套来源等级

来源质量必须根据“我们在保存什么”判断，不能使用一个全局等级。

### 2.1 Reality 来源等级

| 等级 | 含义 | 典型来源 |
| --- | --- | --- |
| R1 | 一手、可核验、直接描述现实状态 | 政府统计/公告、交易所披露、公司法定报告、招股书、环评/审批文件、海关/交易所原始数据 |
| R2 | 有稳定方法和持续发布机制的专业来源 | 行业协会、价格评估机构、专业数据库、交易平台、研究机构原始统计 |
| R3 | 二手整理或引用 | 券商报告、主流财经媒体、行业媒体、会议纪要转述 |
| R4 | 仅用于发现线索 | 自媒体、论坛、无来源截图、聚合转载、AI 摘要 |

R3/R4 可以帮助定位原始来源，但高影响 Reality 不应只依赖 R3/R4 发布。

### 2.2 Expectation 来源等级

| 等级 | 含义 | 典型来源 |
| --- | --- | --- |
| E1 | 判断主体自己的原始表达 | 公司业绩会/调研纪要/公告中的 guidance，券商自己的研究报告，政府规划原文，协会原始预测 |
| E2 | 有记录的直接采访/演讲 | 会议实录、官方采访、可核验录音/文字稿 |
| E3 | 可靠二手转述 | 主流财经媒体引用管理层/专家判断，其他研究报告引用原报告 |
| E4 | 无法确认原始说法 | 聚合转载、自媒体转述、无日期截图、AI 总结 |

一份券商报告可能是 Reality 的 R3，但同时是“该券商当时判断”的 E1。Agent 必须分别标记。

## 3. 时间纪律：禁止未来信息泄漏

Longcycle 最重要的规则之一是 point-in-time。

每份材料至少记录：

- `published_at`：来源正式发布时间；
- `first_known_at`：在没有更早证据时等于 `published_at`；
- `retrieved_at`：Agent 今天找到材料的时间；
- `knowledge_cutoff`：如果任务指定历史截面，材料必须不晚于该时间。

例如任务要求重建 `2022-06-30` 当时对 2023 年锂需求的预期：

- 可以在 2026 年使用搜索引擎寻找 2022 年旧报告；
- 不能把 2022-07-01 以后发布的材料加入这个 snapshot；
- 不能因为现在知道 2023 年结果而修改 2022 年报告的含义；
- 若后来的材料说“我们去年曾预计……”，它只能作为寻找原报告的线索，不能替代原报告进入 E1。

找不到精确发布日期时标记 `date_uncertain=true`，不得猜日期。

## 4. 原文优先和反转载规则

搜索结果出现转载时按以下顺序追原文：

1. 政府/交易所/公司/协会官方网站；
2. 原始 PDF、公告附件、投资者关系记录；
3. 原始研究机构或数据提供商页面；
4. 主流媒体首发；
5. 转载。

如果只能找到转载：

- 返回转载链接；
- 写明 `is_repost=true`；
- 写明它声称的原始发布者；
- 不把转载站当作原始 publisher；
- 不伪造原始 URL。

同一文件多个镜像只保留一个主候选，其余写入 `alternate_urls`。

## 5. 文档级回传格式

每行一个 JSON 对象（JSONL）。Discovery 最低要求：

```json
{
  "task_id": "LB-001",
  "mode": "discover",
  "industry_path": ["lithium_battery", "upstream", "lithium_chemical"],
  "topic": "battery_grade_lithium_carbonate",
  "title": "原始标题，不改写",
  "publisher": "发布者原名",
  "document_kind": "government_release|annual_report|ir_record|broker_report|association_data|eia|approval|news|other",
  "published_at": "2022-08-01T00:00:00+08:00",
  "first_known_at": "2022-08-01T00:00:00+08:00",
  "date_uncertain": false,
  "knowledge_cutoff": null,
  "url": "https://...",
  "alternate_urls": [],
  "is_repost": false,
  "claimed_original_publisher": null,
  "reality_rank": "R1",
  "expectation_rank": "E3",
  "material_roles": ["reality", "expectation"],
  "speakers": [],
  "target_periods": [],
  "locators_to_review": ["第 15 页 产能规划", "表 7"],
  "downloaded_file": null,
  "sha256": null,
  "access_status": "ok|paywalled|login_required|missing|broken",
  "notes": "只写检索和文档本身的信息，不写研究结论"
}
```

如果 Agent 下载文件，必须回传文件名和 SHA-256；无法下载但网页可读时保持 `downloaded_file=null`。

## 6. Extract-light 回传字段

轻量摘录可以在文档对象增加 `claims`。每个 claim 必须明确区分 Reality 与 Judgment。

### 6.1 Reality claim

```json
{
  "claim_role": "reality",
  "subject_text": "项目/公司/行业原始名称",
  "predicate_hint": "capacity|production|price|inventory|sales|commissioned_at|other",
  "raw_value": "原文值，不换算",
  "raw_unit": "原文单位",
  "valid_period_text": "原文描述的适用时间",
  "statement": "不超过 40 个汉字的原文关键摘录",
  "locator": "page:12/table:3/row:磷酸铁锂",
  "confidence": "high|medium|low"
}
```

### 6.2 Judgment claim

```json
{
  "claim_role": "judgment",
  "speaker_text": "谁作出判断",
  "speaker_role": "management|analyst|government|association|industry_expert|customer|other",
  "judgment_kind": "forecast|guidance|target|scenario|risk|thesis|commitment",
  "subject_text": "判断针对的对象",
  "topic": "demand|price|capacity|commissioning|technology|policy|other",
  "target_period_text": "预测针对的未来时点/期间",
  "raw_expected_value": "点值/区间/日期/方向/原文文本",
  "probability_text": null,
  "statement": "不超过 40 个汉字的原文关键摘录",
  "locator": "page:8/section:行业展望",
  "rationales": [
    {"kind": "premise", "text": "原文明确写出的理由", "locator": "page:8"}
  ],
  "confidence": "high|medium|low"
}
```

禁止把 Agent 自己总结出的逻辑放进 `rationales`。只有原文明确表达的理由才能进入。

## 7. 搜索失败也必须回传

没有找到不是空结果。每个任务都要返回 search log：

```json
{
  "task_id": "LB-001",
  "search_log": {
    "queries": ["实际使用过的检索词"],
    "domains_checked": ["miit.gov.cn", "cninfo.com.cn"],
    "date_range": ["2021-01-01", "2022-12-31"],
    "result": "found|partial|not_found|blocked",
    "missing_targets": ["仍未找到的资料类型"],
    "notes": "访问限制或异常"
  }
}
```

这样后续可以区分“没有发生”与“没有搜到”。

## 8. 去重规则

同一材料优先通过以下组合判重：

```text
publisher + exact title + published_at + file sha256
```

没有文件时使用：

```text
publisher + canonical URL + published_at
```

以下情况不要合并：

- 同一报告的初版和修订版；
- 同一项目不同日期的环评/批复/开工/延期公告；
- 同一公司不同季度对同一问题的 guidance；
- 同一券商不同日期的预测，即使数字相同。

这些“重复”本身就是历史变化。

## 9. 优先保留哪些材料

对周期研究价值从高到低：

1. 会改变供给、需求、成本或时间节奏的原始材料；
2. 当时市场/管理层对未来的明确数字或日期预期；
3. 对前述预期的理由、约束、风险和修订；
4. 能形成稳定历史序列的数据；
5. 重要政策、技术路线切换和项目里程碑；
6. 泛泛行业评论。

不要为了数量大量收集观点重复、没有数据、没有时间锚点的新闻。

## 10. 绝对禁止项

- 不伪造 URL、标题、页码、发布日期；
- 不把搜索引擎摘要当原文；
- 不把 AI 回答作为资料来源；
- 不把现在的页面更新时间当历史文档发布日期；
- 不把计划产能当现有产能；
- 不把产量当产能；
- 不把出货量、销量、装车量混成同一指标；
- 不把电池级碳酸锂、工业级碳酸锂混为一条价格；
- 不把动力电池、储能电池、消费电池混为一个需求口径；
- 不自行判断“行业见底”“供给过剩”“需求爆发”；
- 不用后来结果修改当时预期。

Agent 的价值是**忠实地把历史材料搬回来**。研究判断由后续层完成。
