# Model Memory Audit：用模型记忆寻找历史缺口

## 1. 定位

Longcycle 允许使用基础模型已有知识作为**历史线索生成器**，但绝不把模型记忆当成证据。

原则：

> **Model memory may challenge the archive, but may never overwrite the archive.**
>
> 模型记忆可以质疑档案、提醒遗漏、生成搜索方向，但不能直接成为 Fact、Judgment 或 Canonical Truth。

模型并不能访问一个可查询的“训练资料数据库”，也不能可靠指出某条记忆来自哪篇训练材料。因此 model prior 的价值不是 provenance，而是：

- 广泛关联；
- 模糊历史记忆；
- 冷门术语与旧称；
- 跨产业链联想；
- 对时间线“缺了什么”的异常感；
- 生成一般检索 Agent 很难主动想到的搜索线索。

数据库使用 `model_prior_runs`、`model_memory_leads`、`model_memory_lead_relations` 保存这类过程；这些对象与 `fact_assertions`、`judgment_assertions` 永久分层。

## 2. 为什么必须先 blind recall

如果模型先看到今天的搜索结果，再让它“回忆历史”，它很容易被当前网页锚定，所谓交叉验证会退化成复述搜索结果。

因此每个重要行业阶段至少做一次：

```text
Blind Recall（不看本轮搜索结果）
        ↓
Model Memory Leads
        ↓
与已采集 archive 做 Gap Diff
        ↓
生成 targeted search tasks
        ↓
归档原始材料
        ↓
Authority-aware adjudication
```

`model_prior_runs.source_visibility` 必须记录运行时模型看到了什么：

- `none`：真正盲回忆；
- `archive_only`：可看已归档原文；
- `archive_summary`：只看已有结构化覆盖地图；
- `search_results`：已经暴露本轮搜索结果，不得再把该 run 当独立 prior。

第一遍原则上使用 `none`。

## 3. 不要只问“你记得哪些大事”

普通 prompt 只会得到著名事件，价值有限。Longcycle 的 memory audit 必须多遍、换观察视角，主动逼出隐性关联。

### Pass A：历史地标

问题：

> 如果要向一个真正做过这个行业的人证明我们没有漏掉一个周期，哪些时间节点、公司动作、价格阶段、政策或项目必须出现？

输出：`landmark` / `missing_event`。

### Pass B：旧术语与检索词重建

很多历史资料今天搜不到，是因为当年的叫法不同。

要求模型回忆：

- 当年的行业术语；
- 项目旧名、基地名、矿山名；
- 公司曾用名；
- 当时媒体常用标题词；
- 数据指标过去的名字；
- 英文/中文别名；
- 市场口头简称；
- 过去流行、今天已经不常用的技术路线名称。

输出：`terminology` / `actor`，重点是 `suggested_queries`。

### Pass C：交易与定价机制

只看价格曲线会漏掉价格形成机制。要求回忆：

- 现货、长协、公式价、拍卖、加工费、折扣/升水；
- 原料与成品之间的定价传导；
- 合同周期是否改变；
- 谁掌握议价权；
- 极端景气时是否出现锁量、预付款、包销、最低采购等安排；
- 某个指数/评估价是什么时候开始成为市场锚。

输出：`pricing_rule` / `contract_change`。

### Pass D：真正决定有效供给的工程约束

名义产能往往不是周期核心。要求模型从工程/运营角度回忆：

- 设备交期；
- 环评/能评/矿权/采矿许可；
- 建设周期；
- commissioning；
- 良率；
- 回收率；
- 品位；
- 爬坡；
- 客户认证；
- 产品一致性；
- 副产品处置；
- 电力/天然气/蒸汽/水等公用工程；
- 运输、港口、危险品物流等瓶颈。

输出：`process_bottleneck` / `project_pattern`。

### Pass E：库存究竟在哪里

总库存数字常常解释不了周期。要求按链条位置展开：

```text
矿山
→ 港口/精矿
→ 锂盐厂原料
→ 锂盐成品
→ 正极原料/成品
→ 电芯原材料
→ 电芯成品
→ Pack
→ OEM
→ 经销/终端
```

同时问：

- 是主动补库还是被动累库？
- 是否有渠道库存转移？
- 价格下跌时谁最先去库存？
- 某段历史是否存在统计上看不到但行业普遍讨论的隐性库存？

输出：`inventory_pattern`。

### Pass F：资本循环与融资约束

要求模型回忆：

- 高利润后多久出现扩产公告；
- 公告到募资、设备订单、开工、投产分别多久；
- 再融资/IPO/定增是否推动某轮扩产；
- 行业低谷是否出现取消、延期、减值、资产出售；
- working capital、应收、预付款如何变化；
- 上游资源并购和长期包销是否跟随价格周期。

输出：`capital_cycle`。

### Pass G：技术替代和单位耗用变化

周期研究不能只看终端销量。要求模型寻找：

- 技术路线切换；
- 单位产品原材料用量变化；
- 能量密度变化；
- LFP/NCM 结构变化；
- 硅碳、钠电、固态等技术预期曾否影响资本行为；
- 制造工艺进步是否改变良率、成本或单位耗用；
- 回收料比例是否改变原生资源需求。

输出：`technology_shift` / `mechanism`。

### Pass H：跨行业依赖

要求跳出本产业链：

- 电力与能源价格；
- 化工原料；
- 矿业设备；
- 航运与港口；
- 汽车金融；
- 光伏/风电/储能政策；
- 电网消纳；
- 海外补贴与贸易政策；
- 汇率与融资成本；
- 环保、安全生产和地方财政。

目标是发现“锂电数据库内部永远看不出来”的外部驱动。

输出：`cross_industry_dependency`。

### Pass I：当时的叙事，而不是后来总结

要求模型回忆“当时大家用什么理由解释未来”，例如：

- 长期资源短缺；
- 技术改变资源约束；
- 新能源车渗透率 S 曲线；
- 储能成为第二需求曲线；
- 某类产能宣布很多但真正能投出来很少；
- 价格高会自然刺激供给；
- 某种技术路线将替代另一种路线。

这些只能生成 `narrative` lead。必须继续寻找当时有日期的原始报告、管理层表达或正式采访，不能把模型回忆直接写入 Expectation。

### Pass J：Negative Space

这是最重要的一遍之一。

给模型一份“目前已经采到的历史目录”，问：

> 如果这真是一份完整历史，哪些缺失会让你觉得不自然？

例如已经有：

```text
锂价暴涨
→ 大量扩产公告
→ 2023 锂价下跌
```

模型应该追问：

- 扩产公告到实际供给之间发生了什么？
- 精矿价格和锂盐利润如何分配？
- 库存在哪里积累？
- 电池厂排产是否先转弱？
- 项目设备订单什么时候见顶？
- 当时市场为何仍相信需求能消化这些产能？

输出：`anomaly` / `missing_event`。

## 4. 每个 Memory Lead 必须长什么样

模型不得输出“事实表”，而输出搜索线索：

```json
{
  "lead_kind": "pricing_rule",
  "claim_scope": "market_measurement",
  "summary": "模型模糊记得 2021-2022 年锂精矿定价和拍卖机制曾显著影响锂盐成本预期",
  "approximate_period": ["2021-01-01", "2022-12-31"],
  "memory_confidence": 0.66,
  "importance_score": 0.85,
  "novelty_score": 0.78,
  "searchability_score": 0.72,
  "recalled_details": {
    "possible_actors": ["澳洲锂矿企业", "中国锂盐企业"],
    "possible_mechanism": "精矿价格变化改变锂盐边际成本和利润分配"
  },
  "suggested_queries": [
    "lithium spodumene auction 2021 China converter",
    "锂精矿 拍卖 2021 锂盐 成本",
    "锂精矿 长协 定价 2022"
  ],
  "suggested_source_types": [
    "矿业公司公告/季度报告",
    "锂盐公司投资者关系记录",
    "当期专业价格机构资料"
  ]
}
```

`memory_confidence` 只表示模型对“自己似乎记得这件事”的强弱，不是真值概率。

`search_priority` 由 importance、novelty、searchability、memory confidence 组成，用于决定先查什么，不用于决定相信什么。

## 5. 联想图，而不是独立 checklist

真正稀缺的信息通常藏在关系里，因此模型应同时给出 lead relations：

```text
锂价上涨
  → 精矿定价权上移
  → 锂盐厂利润受压
  → 上游资源并购/包销增加
  → 扩矿激励增强
  → 设备/工程订单增加
  → 18-30 个月后有效供给释放
```

每一条箭头都只是 `possible_cause` / `possible_effect`，直到找到资料。

这允许后续 Agent 从一个线索顺藤摸瓜，而不是只做关键词平搜。

## 6. Model Prior 与互联网结果冲突时怎么处理

禁止使用：

```text
Google/Bing 排名高 → 网页是真的 → 模型记错了
```

也禁止：

```text
模型很有把握 → 网页错了 → 按模型写数据库
```

正确流程：

```text
Memory Lead
   ↕ conflict
Web material
   ↓
先判断 claim scope
   ↓
再判断来源是否有资格证明这个 scope
   ↓
找 claim-scoped primary source
   ↓
仍冲突则保留 disagreement case
```

如果只有转载、自媒体、聚合站、搜索摘要或普通二手文章与模型记忆冲突：

- 不撤销 memory lead；
- 不写 Fact；
- 标记 `secondary_only_contradiction`；
- 继续搜索原始资料。

如果找到真正匹配 claim scope 的权威一手来源：

- 原始公告/统计支持模型记忆：lead 标记 `primary_supports_lead`；真正的数据仍由 evidence → assertion pipeline 产生；
- 原始公告/统计反驳模型记忆：lead 标记 `primary_contradicts_lead`；保留这次错误记忆以便评估模型，不删除；
- 两个权威一手来源互相矛盾：`authoritative_conflict`，进入人工复核，不能挑自己喜欢的来源。

## 7. 权威也必须按范围理解

“正规机构”不等于对所有问题都是真理。

例如：

- 公司公告是“公司在这天宣布了 100 GWh 规划”的强证据；
- 它不是“100 GWh 一定会按时形成有效产能”的证据；
- 券商原报告是“该团队当时预测锂价会怎样”的最强原始来源；
- 它不是后来实际锂价的权威来源；
- 政府统计是该官方统计口径的强证据；
- 若统计口径发生修订，必须保存 vintage 和 methodology，不用新口径改写旧口径历史。

详见 `source-authority-policy.md`。

## 8. 锂电池第一轮 Memory Audit 顺序

第一轮建议在低级 Agent 返回基础资料后执行四次：

### Audit 1：2019-2020 周期底部/起点

重点回忆：

- 上一轮过剩从哪里来；
- 哪些项目退出/延期；
- LFP 技术预期如何变化；
- 当时市场为什么没有预期随后锂价大涨。

### Audit 2：2021-2022 短缺与高价

重点回忆：

- 锂精矿与锂盐定价权；
- 资源包销、并购、拍卖；
- 电池厂/车企锁资源；
- 产能宣布到实际释放的工程瓶颈；
- 当时的“长期短缺”叙事与需求预测。

### Audit 3：2023-2024 反转与去库存

重点回忆：

- 库存在哪一层先累积；
- 排产、终端销量与原料采购的先后关系；
- 高价期间宣布项目何时集中释放；
- 哪些市场预期修订最明显。

### Audit 4：2025-2026 新平衡

重点回忆：

- 储能边际需求；
- 资源端成本曲线和停复产；
- 海外贸易/政策；
- 技术变化对单位锂耗的影响；
- 上一轮低价是否已经开始改变未来资本开支。

## 9. 验收标准

Memory Audit 的好坏不看“模型猜对率”，而看：

1. 是否发现了原采集计划未覆盖的重要历史材料；
2. 是否产生了低级 Agent 自己不容易想到的有效搜索词；
3. 是否补出了跨产业链关系；
4. 是否发现了已有数据之间的异常或口径冲突；
5. 是否在搜索结果与模型 prior 冲突时坚持寻找 claim-scoped primary source；
6. 是否始终没有把模型记忆直接写入 Fact/Judgment。

如果 memory audit 最后只生成著名新闻摘要，它就是失败的。
