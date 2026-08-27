# Source Authority Policy：来源权威必须与问题匹配

## 1. 目的

搜索引擎排序、网页数量、转载次数和模型自信程度都不能决定 Longcycle 的事实。

Longcycle 对来源采用 **claim-scoped authority**：

> 不是问“这个网站权不权威”，而是问“这个来源有没有资格证明我们正在判断的这件事”。

因此同一来源对不同 claim 可以具有完全不同的证明力。

## 2. Search Result 不是 Evidence

以下对象永远不能直接进入事实调和：

- 搜索引擎 snippet；
- AI 搜索摘要；
- 聚合页自动摘要；
- 没有打开并归档的网页标题；
- 无法定位原文的转述。

它们都是 discovery material，只能帮助找到真正的 source document。

## 3. Claim Scope

第一版定义以下 scope：

| Claim scope | 要证明的问题 |
| --- | --- |
| `legal_disclosure` | 公司/主体正式披露了什么法定信息 |
| `official_statistic` | 某官方统计口径发布的数值是什么 |
| `self_statement` | 某人/机构当时是否说过某句话 |
| `management_guidance` | 管理层当时给出的目标、预测或 guidance |
| `market_measurement` | 当时市场价格、库存、产量等测量值 |
| `project_status` | 项目审批、建设、投产、停产等状态 |
| `policy_text` | 某项政策/法规正式规定了什么 |
| `third_party_fact` | 关于第三方主体的现实事实 |
| `industry_expectation` | 某机构/群体当时如何判断未来 |
| `technical_specification` | 产品、设备、工艺的明确技术规格 |
| `other` | 尚未进入强类型范围的 claim |

所有证据比较之前先确定 claim scope。scope 不一致时不能互相覆盖。

## 4. Authority Class

### 4.1 `authoritative_primary`

对指定 claim scope 具有法定、官方或直接记录地位。

典型情况：

- 交易所/法定公司公告证明 `legal_disclosure`；
- 国家/政府统计发布证明其 `official_statistic`；
- 正式行政批复、环评批复证明对应 `project_status`；
- 法规/政策原文证明 `policy_text`；
- 有明确制度地位的交易所成交/仓单数据证明对应市场数据。

它仍然只能证明自己的 scope。

### 4.2 `primary_self_statement`

说话者自己的原始表达。

典型情况：

- 公司 IR 记录；
- 业绩会 transcript；
- 券商自己的研究报告；
- 协会自己的预测报告；
- 官方采访全文。

它对 `self_statement`、`management_guidance`、`industry_expectation` 很强。

但“公司预计明年投产”只能证明公司当时这样预计，不能证明项目后来真的按时投产。

### 4.3 `methodological_primary`

来源是该测量/估算的原始生产者，并公开或稳定使用一套方法。

典型情况：

- 专业价格评估机构自己的价格序列；
- 行业协会自己的统计；
- 专业数据机构自己的调查数据；
- 研究机构自己的供需模型。

它通常适合 `market_measurement` 或该机构自己的 `industry_expectation`，但不能因为“专业”就自动成为其他 scope 的 authoritative truth。

### 4.4 `reputable_secondary`

具有编辑核验、记者署名或研究流程的可靠二手来源。

例如主流财经媒体、严肃研究机构对外部事实的报道。

它可以强力 corroborate，也可以在原始资料消失时保留历史线索，但高影响争议若能继续找 primary source，不应在这里停止。

### 4.5 `secondary`

普通二手整理、研究报告引用第三方数据、行业媒体转述等。

可以发现线索和交叉检查，不用于单独裁决重大冲突。

### 4.6 `discovery_only`

- 自媒体；
- 论坛；
- 无来源截图；
- 大量转载聚合；
- 搜索摘要；
- AI 回答。

不能裁决 model prior 与 archive 的冲突。

## 5. 同一个来源可以同时有不同 Authority

例 1：公司年报

```text
“本公司截至年末产能为 X”
→ legal_disclosure / authoritative_primary

“预计行业未来三年增长 30%”
→ management_guidance 或 industry_expectation / primary_self_statement

“行业总规模为 Y（引用第三方）”
→ third_party_fact / secondary，继续追原始统计
```

例 2：券商深度报告

```text
“我们预计 2023 年锂需求 80 万吨 LCE”
→ industry_expectation / primary_self_statement

“2021 年中国碳酸锂产量为 X（引自 SMM）”
→ official/market measurement 不是券商自己的 primary；应追 SMM
```

例 3：政府新闻稿

```text
“本部门统计 2024 年行业产量为 X”
→ official_statistic / authoritative_primary

“预计行业将保持高速增长”
→ government expectation；是政府自己的判断原文，但不是未来事实
```

## 6. Model Memory 与 Web Material 冲突时的裁决阶梯

### 情况 A：只有 discovery / secondary 网页反驳模型记忆

结论：

```text
secondary_only_contradiction
```

动作：

- 保留 model memory lead；
- 不采信模型；
- 也不采信网页为最终事实；
- 生成 targeted search，继续找 claim-scoped primary。

### 情况 B：多个二手来源一致反驳模型记忆

仍然不能简单多数投票。

先检查这些网页是否互相转载、是否都引用同一篇原始资料。`independence_cluster` 相同的十篇转载只算一个来源簇。

如果确实存在多个独立 `reputable_secondary`，可以降低 lead 的搜索优先级，但高影响事实仍尽量追原始资料。

### 情况 C：匹配 scope 的 primary source 反驳模型记忆

模型 lead 记为：

```text
primary_contradicts_lead
```

但真正的 Fact/Judgment 必须由该原始资料经过正常 extraction/reconciliation 管道产生，不能从 memory audit 直接发布。

### 情况 D：primary source 支持模型记忆

lead 记为：

```text
primary_supports_lead
```

这只说明模型成功帮助发现了一段历史。事实仍来自原文。

### 情况 E：两个 claim-scoped primary source 冲突

结论：

```text
authoritative_conflict
```

不得自动选择“级别看起来更高”的一个。先排查：

- 时间不同；
- 统计口径不同；
- initial vs revised vintage；
- 公司主体/项目主体不同；
- planned vs actual；
- nominal vs effective；
- 全国 vs 样本企业；
- 发布错误后是否有勘误。

无法解释时进入人工 conflict case。

## 7. “正规机构”也不能脱离时间

历史研究要保存来源当时的版本。

例如官方统计后来修订：

```text
2023-03 初值：100
2023-09 修订：96
```

不能因为 96 是后来官方终值，就把站在 2023-04 的 point-in-time snapshot 改成 96。

Longcycle 同时保存：

- 当时市场能看到的 initial vintage；
- 后来的 revised vintage；
- 今天默认采用的 current version。

## 8. 权威来源也可能有利益立场

`authority` 与 `bias` 是两个不同维度。

公司对“自己是否发布了某个扩产计划”是最权威来源，同时它可能系统性高估进度。

这不是降低其作为 `self_statement` 的真实性，而是 Longcycle 长期要统计的产业经验：

```text
公司历次 guidance
        vs
后来实际 outcome
        ↓
延期分布 / 实现率 / 偏差模式
```

所以不要因为管理层历史上经常乐观，就删除它当时的原始 guidance。恰恰应该完整保存。

## 9. Agent 执行规则

低级采集 Agent 只做初步 authority hint，不做最终裁决。

每份材料至少返回：

```text
publisher
source_kind
document_kind
reality_rank
expectation_rank
claimed_primary_source
is_repost
```

高影响 claim 进入 extraction 后，再由规则/人工确定：

```text
claim_scope
authority_class
authority_basis
scope_match
independence_cluster
```

禁止 Agent 因“这是某某大媒体”直接标 `authoritative_primary`。

## 10. 锂电池具体例子

### 锂盐价格

优先证据：

- 价格评估机构自己的历史序列；
- 交易所正式行情/交割/仓单；
- 企业实际采购/销售披露（注意不是整个市场价格）。

普通新闻里“今日碳酸锂价格 XX 万元”若没有明确引用口径，只是线索。

### 矿山/锂盐项目投产

不同 claim 分开：

```text
公司宣布计划 2023Q4 投产
→ 公司公告对“计划”是 primary

地方政府称项目已进入试生产
→ 政府原文对对应 project status 很强

公司年报确认当年产量已经产生
→ 对实际生产进一步 corroborate
```

不能用最初规划公告证明后来实际投产。

### 动力电池装车

联盟原始月报对其统计口径是 methodological/official-like primary；媒体转载只能用于找原月报。

### 当时市场预期

券商自己的原报告是该券商 judgment 的 E1 / primary self-statement。

今天某篇文章写“当年市场普遍认为锂会长期短缺”，只能作为 lead。要重建“普遍认为”，需要多个当时独立 judgment 或严格定义的 expectation snapshot。

## 11. 最终原则

Longcycle 不做：

> 模型 vs 互联网，谁票多谁赢。

Longcycle 做：

> 模型提出历史线索；互联网负责找到档案；档案按 claim scope 和 authority 判断证明力；真正事实由可追溯原文裁决。
