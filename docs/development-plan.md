# Longcycle 开发方案：产业记忆优先

## 1. 产品目标

Longcycle 的目标不是尽可能多地采集行业数据，也不是自动生成更多分析结论。

核心目标：

> **保存一个行业最关键、最真实、可回放的历史，同时保存人在每一个历史时点对未来的判断、预期和理由。**

系统长期回答：

1. **Reality**：当时真实发生了什么？
2. **Expectation**：当时的人认为未来会发生什么，为什么？
3. **Outcome**：后来实际发生了什么，预期与现实为什么偏离？
4. **Missing History**：今天看起来完整的历史，其实还漏掉了哪些当时重要的机制、actor、失败项目、定价规则和叙事？

## 2. 新的采集总原则

历史恢复与当前采集必须拆成两条路线。

### 2.1 历史：Memory-first, evidence-final

互联网对旧资料的检索能力有限。低成本 Agent 如果只收到宽泛主题，天然会找到少量显著结果后提前交工。

因此历史研究默认改为：

```text
高级模型 Memory Exhaustion Campaign
→ Sealed Blind Memory Atlas
→ 高级模型 Self Verification
→ 低成本 Agent 逐条 Evidence Verification
→ archived source
→ Fact / Judgment
```

高级模型负责尽可能建立“应该找什么”的目录；原始资料负责决定“最终能确认什么”。

### 2.2 当下：Source-first, archive-now

今天仍在公开渠道上的原始资料不应该等几年后再抢救。

```text
high-value source watchlist
→ 定期/事件触发检查
→ 新文件即时归档
→ 事实/判断抽取
→ revision detection
→ source inventory 扩展
```

当前采集的目标是把未来最难找的历史今天就保存下来。

## 3. 第一原则

### 3.1 历史不可重写

Fact、Judgment、Memory Lead、原始文档、模型 campaign 都采用可回放语义。后来的修订、模型更新、搜索验证通过新增对象表达，不覆盖旧记录。

### 3.2 不让后见之明污染过去

所有历史 snapshot 受 `knowledge_cutoff` 约束。

对于模型 memory：blind recall 的运行时间可以是今天，但它只能生成“今天模型记得的历史线索”，不能自动声称“当年市场就知道这些”。只有 timestamped historical source 能建立当时可知性。

### 3.3 Fact、Judgment、Model Prior 三分

```text
Fact      来源声称现实世界是什么
Judgment  某个说话者当时怎样判断未来/不确定状态
ModelPrior 模型今天模糊记得或推测可能存在的历史线索
```

三个对象永远不能通过简单转换互相升级。

### 3.4 搜不到不是不存在

历史检索的 `not_found` 只能表示当前检索路径没有找到。

不能据此：

- 删除 Memory Lead；
- 反向建立“没有发生”Fact；
- 认为二手网页的说法胜出。

### 3.5 权威按 claim scope 判断

来源是否有资格证明某件事，比来源网站名气更重要。

例如：

- 公司公告对“公司当时披露了什么”强；
- 对“行业未来一定怎样”只是公司自己的 Judgment；
- 券商原报告对“券商当时如何预测”是 primary；
- 对第三方历史 actual 通常不是最终权威；
- 政府/协会统计对自己的统计口径强，但不能自动替代其他口径。

### 3.6 可比性优先于数量

价格、产能、产量、库存、需求、利润、装车等序列必须先解决规格、范围、单位、时间和统计口径，再谈长期比较。

## 4. 第一行业：新能源锂电池

第一真实行业：新能源锂电池产业链，中国为主。

第一轮时间：

```text
2019-01-01 → 2026-12-31
```

必要时向 2015–2018 回填上一轮周期背景。

范围：

```text
锂矿/盐湖
→ 精矿
→ 碳酸锂/氢氧化锂
→ LFP/三元/负极/隔膜/电解液
→ 电芯/Pack
→ 新能源汽车/储能
→ 回收
```

并纳入：

- 设备；
- 能源/电力；
- 物流；
- 融资/资本市场；
- 海外供给与政策；
- 项目审批与客户认证。

## 5. Phase 1：先榨高级模型的产业历史记忆

### 5.1 不做一次性大 Prompt

“把你知道的锂电历史都说出来”只会召回显著内容。

第一版必须按 `docs/research/lithium-battery-memory-exhaustion-manifest.json` 运行多轮正交 pass。

至少包括：

- 时间切片；
- 产业链切片；
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

### 5.2 重要 lead 要递归扩展

每条高重要度 lead blind 阶段继续问：

```text
Who else?
What preceded it?
What followed it?
What was it called then?
```

目的是把“模糊记得一个事情”扩展成可以搜索的 actor、旧称、时间范围和机制链。

### 5.3 强制挖长尾

模型输出必须区分：

- obvious landmarks；
- long-tail leads；
- forgotten actors；
- mechanism leads；
- search keys；
- uncertain fragments。

至少一半有效输出预算给后五类，避免全部变成著名行业大事。

### 5.4 Saturation 而不是模型自称“没了”

停止条件：

- 连续多个正交 pass 高重要度新 lead 显著下降；
- 时间 × 链条 × metric coverage 没有大面积空白；
- failures / old vocabulary / forgotten actors / mechanisms / negative space 等类别不再快速增加。

第一版实现已经提供 deterministic saturation primitive。

### 5.5 封存 Blind Memory Atlas

封存内容：

```text
model provider/name/version
声明 knowledge cutoff（如有）
protocol/manifest version
所有 pass 原始输出
normalized leads
relations
coverage matrix
stop reason
```

任何后续搜索不得修改该 blind atlas。

## 6. Phase 2：高级模型自己做第一轮搜索印证

高级模型理解自己 recall 时的语义和关联，所以比低成本 Agent 更适合先做**高价值 lead 的第一轮研究型检索**。

但必须开启新 run：

```text
blind_recall sealed
→ self_verification(search enabled)
```

高级模型负责：

- 找更精确项目名/公司名；
- 找历史旧称；
- 找原报告标题；
- 判断普通网页是否转载同源；
- 定位最可能 primary domain；
- 设计适合低成本 Agent 的 task packet；
- 对重大冲突自己继续追 primary source。

仍然不能：

- 因为搜索不到就删除 lead；
- 把搜索摘要写成 Fact；
- 用网页数量多数投票；
- 修改 blind recall 让自己看起来“原本就知道”。

## 7. Phase 3：低成本 Agent 做证据工程

低成本 Agent 的输入从“大概主题”升级成具体 task packet：

```text
lead_id
claim scope
lead summary
possible actors
possible aliases
query families
preferred primary sources
support criteria
contradiction criteria
minimum search depth
knowledge cutoff
```

### 7.1 默认最低搜索深度

历史高价值任务：

- ≥ 6 类 query family；
- ≥ 3 类来源类型；
- 检查最可能 primary domain；
- 有 citation 时至少追一次；
- 至少做一次反向查询；
- 需要时翻页/换旧称/找附件，直到结果高度重复。

只允许三种正常结束：

```text
primary_verified
primary_contradicted
exhausted_but_unresolved
```

具体 SOP：`docs/research/research-agent-sop.md`。

## 8. Phase 4：建立 Current Collection

历史抢救的同时，从今天开始建立锂电 source watchlist。

### 8.1 优先 source

- 工信部、发改委、能源局、统计/海关等；
- 动力电池联盟；
- 中汽协、乘联会；
- 交易所公告；
- 头部电池/材料/锂资源公司 IR；
- 关键海外矿业公司披露；
- 地方政府环评/审批；
- 价格机构公开原始资料；
- 行业协会和政策原文。

### 8.2 当前资料优先保存什么

- 明确数字与统计口径；
- 项目里程碑；
- guidance/forecast/target；
- 资本开支、融资、并购；
- 政策；
- 定价/合同/市场规则改变；
- 统计修订；
- 技术路线和单位耗用；
- 高信息量 IR/业绩会/会议实录。

当前资料的原则：

> 能今天归档，就不要寄希望于未来模型记得。

## 9. Phase 5：Judgment Extraction

从真实锂电历史资料反推 Judgment schema/抽取，而不是先构建通用 NLP 平台。

最小能力：

- speaker resolution；
- said_at / target_period；
- forecast/guidance/target/risk/scenario；
- 数值/范围/日期/方向；
- rationale/condition/caveat；
- revision/reaffirm/withdraw；
- evidence locator。

## 10. Phase 6：Reality vs Expectation vs Outcome

第一版研究不需要复杂模型，只做可解释查询：

```text
当时预计需求多少？实际多少？
当时预计哪些项目投产？实际什么时候形成有效供给？
当时缺货/过剩的理由是什么？
哪些 premise 最后失效？
市场什么时候开始修订预期？
```

## 11. Phase 7：模型更新后的历史回补

未来高级模型训练资料或能力更新时，不覆盖旧 Memory Atlas。

每个新 model vintage 重新跑固定 benchmark manifest：

```text
old atlas
vs
new atlas
→ known / refined / novel
→ archive gap
→ backfill queue
```

新增旧称、actor、机制、项目名都可以产生 refinement，即使事件本身以前已经有 lead。

长期可以统计不同模型作为历史目录生成器的：

- novel verified lead yield；
- false memory rate；
- terminology yield；
- mechanism yield；
- forgotten actor yield；
- primary-source search yield；
- archive coverage uplift。

详细设计：`docs/research/model-refresh-backfill.md`。

## 12. 数据库路线

### 已增加

- `0013_judgments_and_expectations.sql`
- `0014_memory_leads_and_authority.sql`
- `0015_memory_campaigns_and_model_refresh.sql`

新增对象覆盖：

```text
Judgment / rationale / expectation snapshot / outcome evaluation
Model Prior Run / Memory Lead / Lead Relation
source authority profile
memory disagreement
Memory Campaign / Run membership / Seal / Coverage
Model Refresh / Lead Diff
Verification Task Packet
```

## 13. 工程路线

### 13.1 业务 primitive 统一

同步 pipeline 和阶段化 worker 最终应调用同一组业务 primitive：

```text
archive_document
parse_document
extract_facts
extract_judgments
normalize_assertions
reconcile_facts
persist_judgments
run_memory_campaign
seal_memory_atlas
self_verify_memory_leads
compile_verification_tasks
build_expectation_snapshot
evaluate_outcomes
```

### 13.2 下一步实现优先级

1. Memory Campaign persistence/orchestration；
2. 生产高级模型 `MemoryPriorGateway` adapter；
3. self-verification 搜索结果进入 archive 的桥接；
4. verification task packet → agent execution/import；
5. Current source watchlist + scheduler；
6. judgment extraction；
7. PostgreSQL/S3 集成和故障测试。

## 14. 测试优先级

- Campaign 封存后不能被搜索结果修改；
- 同一个 lead 允许被新 model vintage 重新召回；
- model refresh 只 append，不覆盖 baseline；
- `not_found` 永远不能自动变成 contradiction；
- verification agent 未达到 minimum depth 不能正常完成任务；
- primary-source conflict 不能多数投票；
- point-in-time snapshot 不能读 cutoff 之后资料；
- 并发 reconciliation / lease takeover / partial commit / object-store failure。

## 15. 研究 KPI

不以文档条数为主。

更重要：

- 关键历史事件覆盖率；
- 长尾 Memory Lead 验证率；
- novel lead → primary source 转化率；
- forgotten actor / failed project 覆盖率；
- old vocabulary 搜索收益；
- project revision-chain 完整度；
- Judgment 可追溯率；
- historical snapshot future-leak rate；
- 当前 source watchlist 漏采率；
- model refresh 带来的 archive coverage uplift。

## 16. 判断新功能值不值得做

先问：

1. 它能否帮助保存未来最容易后悔没留下来的历史？
2. 它能否让历史更真实、可比、可回放？
3. 它能否帮助高级模型想起普通搜索流程不会想到的东西？
4. 它能否让低成本 Agent 少做自由研究、多做可检查的证据工程？
5. 它能否在未来模型升级时重新打开旧历史缺口？

如果大部分答案是否，就不应优先进入 core。