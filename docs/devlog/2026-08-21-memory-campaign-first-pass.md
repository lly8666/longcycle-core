# 2026-08-21 锂电 Memory Campaign：第一轮主干完成

> 本日志记录可公开复核的研发决策、实验现象、Prompt/Schema 调整与下一步。它不记录模型私有推理链。

## 第一轮状态

在完全禁止新鲜互联网搜索、各 blind shard 不读取其他 shard 实际输出的条件下，已经完成新能源锂电第一轮主干召回：

- UP-HARDROCK：30 leads，v1
- UP-BRINE：20 leads，v3
- UP-CONCENTRATE：18 leads，v3
- UP-CHEMICALS：28 leads，v2
- MID-LFP：20 leads，v3
- MID-TERNARY：20 leads，v3
- MID-ANODE：18 leads，v3
- MID-SEPARATOR：18 leads，v3
- MID-ELECTROLYTE：20 leads，v3
- BAT-CELL：20 leads，v3
- DOWN-NEV：20 leads，v3
- DOWN-ESS：20 leads，v3
- DOWN-OTHER：18 leads，v3
- LOOP-RECYCLING：20 leads，v3

累计：290 条 unsourced blind Memory Leads。

当前没有任何 shard seal，也没有启动 fresh-web self verification。

## 第一轮最重要的架构发现

### 1. “产能”必须升级为统一的多层语义

多个完全独立 shard 都自然召回同一个问题：名义产能不能等于有效供给。

但不同节点折扣原因不同：

- 矿山：品位、回收率、剥采、选矿、天气、许可、运输；
- 盐湖：池体在制品、卤水化学、季节、回收率、合同/配额；
- 精矿：品位、包销锁量、在途、合同定价；
- 锂盐：原料来源、转化路线、产品等级、客户认证；
- 正极/负极/隔膜/电解液：产品规格、良率、工序、客户认证；
- 电芯：化学体系、尺寸、良率、客户平台、动力/储能认证；
- 回收：原料形态、化学体系、工艺路线、实际原料获取。

因此未来数据库/分析应优先支持：

```text
nameplate
→ technically_available
→ qualified_for_product/customer
→ economically_operable
→ actually_operated/output
```

不是给每个行业单独发明一个“有效产能率”。

### 2. Inventory 是跨链一等对象，而不是一个行业总数

独立 shard 在矿山/精矿/锂盐/LFP/三元/电芯/负极/隔膜/电解液/回收/终端都触发库存问题。

需要长期保留：

```text
physical location
ownership
form/product
valuation basis
active restocking vs passive accumulation
in-transit state
```

否则 2022-2023 的反转会被错误压成“需求突然变差”。

### 3. Price 不是曲线，而是合同语义

精矿、三元、隔膜、电解液、回收黑粉独立触发：

```text
product/spec
location
FOB/CIF/EXW
contract vs spot
formula/index
pricing lag
floor/cap
tax/freight
system boundary
```

结论：Longcycle 必须把价格口径和合同语义一起保存。

### 4. Model Memory 最有价值的部分不是著名事件

第一轮真正新增架构价值的内容主要来自：

- 旧称/项目别名；
- 失败、延期、低利用率；
- 小辅材的临时瓶颈；
- 工艺中间层；
- 合同和定价传导；
- 客户认证；
- 在途/半成品库存；
- 当时被广泛相信、后来失效的叙事；
- 跨行业因素（电力、航运、炼化、镍钴、政策、零售库存、电力市场）。

因此第二轮不能只“再多列大事件”。

## Prompt 演进

### v1 问题

UP-HARDROCK 第一轮证明模型可以召回大量长尾 actor/project，但：

- 一条 lead 容易同时包含事实、机制和结果；
- 不确定字段不够清楚；
- 很难区分“强烈记得大概发生过”与“具体数字/股权可能记错”。

### v2 改进

新增：

- memory_basis
- precision_risk
- uncertain_fields
- entity_resolution_state
- old aliases
- why_search_may_miss_it
- disconfirmation queries/source types

真实运行又暴露模型偶发 enum/field 漂移。

### v3 改进

新增 typed candidate validation + structural-only repair 原则。

原始模型输出必须保存；修复只允许修结构和枚举，禁止借 repair 增加历史内容。

第一轮 v3 在完全不同的 ternary/ESS/concentrate/recycling/anode/separator/electrolyte/non-EV shards 上表现稳定，说明该输出契约可以作为下一阶段基础。

## Dynamic topology 的实验结果

没有预先把所有辅材画成一级节点，而是允许 shard 输出 `satellite_trigger`。

目前重复独立触发并值得升格的典型包括：

- SAT-LEPIDOLITE
- SAT-SODIUM-ION
- SAT-DLE
- SAT-NICKEL-INDONESIA
- SAT-GRAPHITIZATION
- SAT-SILICON-ANODE
- SAT-ELECTROLYTE-ADDITIVES
- SAT-LIFSI
- SAT-SOLID-STATE
- SAT-TWO-WHEELERS
- SAT-POWER-TOOLS
- SAT-CONSUMER-ELECTRONICS
- SAT-SECOND-LIFE

第一轮证明：产业 ontology 应允许从历史数据中生长，而不是一次设计完。

## 下一阶段：Corrective Exhaustion，而不是重复第一轮

第二轮优先：

1. UP-HARDROCK：用 v3 修正原子性，专门追 failures / forgotten actors / old names / ownership revisions；
2. UP-CHEMICALS：修复 v2 结构问题，专门追转换项目、锂云母、外购矿加工利润、产品等级和失败扩产；
3. UP-BRINE：项目级 timeline + DLE expectations/failures；
4. BAT-CELL：客户绑定、产线产品不可替代、失败基地、技术叙事；
5. MID-LFP：失败项目、磷化工 satellite、当时 LFP vs high-nickel expectations；
6. DOWN-NEV：当时需求预期、价格战、出口、库存和单车带电量；
7. DOWN-ESS：实际利用率、收入机制、失败示范项目和安全事故。

每个 corrective pass 必须显式禁止重复第一轮 obvious landmarks，优先 long-tail/failure/terminology。

## Seal 标准调整

第一轮 broad pass 不是 seal 条件。

一个 shard 至少需要：

- v3-compatible validated candidates；
- actor/project coverage；
- failure/dead-end pass；
- old terminology/alias pass；
- expectation/mechanism coverage（适用时）；
- self-gap pass；
- saturation review；
- 连续多个 pass 高重要度新类别显著减少。

Seal 后才允许 fresh-web self verification。

## 当前研究纪律

- 290 条 Memory Lead 仍全部是 UNSOURCED；
- 不因模型 confidence 高就升级事实；
- 不因未来网页搜不到就删除 lead；
- 不让第二轮 blind shard 阅读其他 shard 的完整输出；
- bridge/stitch 只使用压缩 lead index；
- self verification 必须引用 sealed blind artifact；
- 原始资料仍是最终 Evidence。
