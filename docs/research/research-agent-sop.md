# Research Agent SOP：历史取证与当下持续采集

## 1. 定位

低成本 Research Agent 不是“搜几个结果交差”的搜索助手，而是 Longcycle 的**证据工程执行器**。

它的质量由以下指标决定：

- 是否追到 claim 对应的原始来源；
- 是否保留来源日期和原始文件；
- 是否把转载链识别出来；
- 是否完整记录搜索路径和失败路径；
- 是否在达到任务定义的 coverage / depth 之前提前停止；
- 是否避免推断和未来信息泄漏。

历史任务和当下任务使用不同工作模式。

---

## 2. 两种工作模式

### 2.1 Historical Verification

输入应尽量来自高级模型 Memory Lead，而不是宽泛主题。

目标：

> 证明、反驳或暂时无法验证一个具体历史 lead，并尽可能找到当时的 primary source。

### 2.2 Current Collection

目标：

> 从今天开始把将来最容易后悔没有留下来的资料持续、系统、及时地保存下来。

当前采集不依赖模型记忆，因为资料此刻还在互联网和官方渠道上，应该主动归档，而不是等几年后再抢救。

---

# Part A：Historical Verification SOP

## 3. 接到任务前先读完整 task packet

每个 task packet 至少应包含：

```text
lead_id
industry_path
period
lead_summary
memory_confidence
possible_actors
possible_aliases
possible_mechanism
query_families
preferred_primary_sources
claim_scope
support_criteria
contradiction_criteria
minimum_search_depth
knowledge_cutoff (如适用)
```

Agent 不得只读标题就开始搜。

## 4. Step 1：拆出“要证明的最小命题”

例如 Memory Lead 是：

> 2021–2022 年锂精矿拍卖/定价机制可能显著推高中国锂盐厂原料成本并改变利润分配。

不要直接搜索整个句子。

拆成：

1. 当时是否存在被行业高度关注的锂精矿拍卖/定价事件？
2. 谁组织/披露？
3. 哪些价格、合同或定价条款发生变化？
4. 中国锂盐企业是否公开讨论该变化对成本/利润的影响？
5. 同期专业机构是否记录加工利润/精矿价格变化？

每个子命题分别有可能的 primary source。

## 5. Step 2：先列 source ladder，再搜索

对每个子命题先写来源梯子。

例：项目投产状态：

```text
1. 公司公告 / 年报 / 港交所或交易所披露
2. 政府验收 / 环评 / 项目备案 / 地方政府正式发布
3. 项目业主官方新闻
4. 有明确记者署名和现场采访的主流媒体
5. 专业行业媒体
6. 普通转载 / 聚合
```

不要搜到第 5 层就停止，除非前 1–4 层明确记录“未找到”。

## 6. Step 3：必须使用多类 query family

一个历史任务至少尝试以下适用查询族，不允许只换两个关键词：

### Exact entity

```text
"项目原名"
"公司名" "项目原名"
```

### Time-bound

```text
公司名 2021 年报 项目
公司名 2022 投资者关系 项目
```

### Site-bound

```text
site:cninfo.com.cn 公司名 项目
site:hkexnews.hk company project
site:gov.cn 项目名 环评
```

### Document-type

```text
项目名 PDF
项目名 年度报告
项目名 环境影响报告书
项目名 业绩说明会
```

### Old aliases

使用 Memory Lead 提供的旧称、英文名、曾用名、基地名、矿山名。

### Quote fragments

如果二手来源引用过一句关键原话，用短片段回搜原始文件。

### Reverse citation

如果报告写“据 XX 数据/公告”，继续搜索 XX，而不是把当前报告当终点。

### File-name archaeology

尝试历史 PDF/附件中常见命名、年份、公告编号、证券代码、项目关键词。

## 7. Step 4：打开结果，不使用搜索摘要做判断

搜索引擎 snippet 只能用于点击候选结果。

每个候选必须检查：

- 发布者是谁；
- 页面/文件真实发布日期；
- 是否原始材料；
- 是否转载；
- 文中实际说了什么；
- 是否能定位到页码、章节、表格、段落；
- 是否引用其他原始来源。

## 8. Step 5：追 citation chain

看到以下表达必须继续追：

```text
据公司公告
据 SMM
据上海钢联
据协会数据
据知情人士
据某券商测算
公司此前表示
```

记录：

```text
current_document
claims_original_source
original_source_found?
original_source_url
```

若找不到原文，当前材料只能保持 secondary/discovery 身份。

## 9. Step 6：处理历史网页消失

允许使用：

- 官方网站当前仍存的旧页面；
- 官方附件；
- 交易所公告库；
- 公司年报/公告集合；
- 政府站点历史归档；
- 可靠网页存档服务，用于定位已消失页面。

网页存档只能证明“当时该页面存在及其内容”，若能继续找到发布者原始附件，仍优先原附件。

不得把来路不明的镜像 PDF 自动视为原始文件。

## 10. Step 7：反向验证

不要只找支持 lead 的东西。

每个高影响 lead 至少执行一组反向查询：

```text
项目名 延期 / 取消 / 未投产
company denies / delay / suspend
统计口径 修订
价格 数据 差异
```

输出必须允许：

- supports
- contradicts
- partial
- scope_mismatch
- not_found

## 11. Step 8：达到 minimum search depth 之前不得停

历史验证默认 minimum depth：

- 至少 6 个有明显不同含义的 query family；
- 至少检查 3 类不同来源类型；
- 至少检查 1 个最可能的 primary domain；
- 如果存在明确二手 citation，至少追一次 citation chain；
- 高影响 lead 至少做一次反向查询；
- 搜索结果翻页/换词直到新增结果高度重复，不能只看首页前几条。

具体任务可以提高该门槛。

## 12. Historical Verification 停止条件

只有以下情况可以交工：

### A. Primary verified

找到 claim-scoped primary/authoritative evidence，且 locator 完整。

### B. Primary contradicted

找到匹配 scope 的权威原始证据明确反驳。

### C. Exhausted but unresolved

达到 minimum depth，关键原始渠道都已检查，仍只有弱二手材料或完全未找到。

必须写：

```text
why_unresolved
queries_attempted
primary_domains_checked
secondary_sources_found
possible_next_leads
```

“我搜了几个关键词没找到”不算 C。

---

# Part B：Current Collection SOP

## 13. 当下资料的核心思想

历史资料之所以难找，是因为当时没有保存。

因此当前采集应优先保存：

> **未来搜索引擎最可能丢失、覆盖、改版、付费化或去语境化的东西。**

当下资料要比历史抢救更主动。

## 14. Current source watchlist

每个行业建立长期 source inventory：

```text
source_id
publisher
channel
URL / feed / search page
source type
expected cadence
importance
claim scopes
archive policy
parser needs
last successful check
```

锂电优先：

- 工信部；
- 发改委/能源局/海关/统计局等；
- 中国汽车动力电池产业创新联盟；
- 中汽协/乘联会；
- 交易所公告；
- 头部公司 IR/公告；
- 重要矿业公司公告；
- 地方项目环评/审批；
- 价格/产业数据机构公开页；
- 关键海外监管和公司披露。

## 15. Current agent 每次运行的固定动作

### 15.1 Check expected sources

不是直接全网搜索，而是先检查已知高价值 source watchlist。

### 15.2 Discover new documents

按发布时间、公告编号、feed、列表页识别新增材料。

### 15.3 Archive immediately

只要材料达到 archive threshold，就保存原始 HTML/PDF/附件，不等结构化抽取完成。

### 15.4 Extract document roles

标记：

- Reality
- Expectation
- Policy
- Project milestone
- Data release
- Context only

### 15.5 Detect revisions

检查是否：

- 修订公告；
- 更新版 PDF；
- 项目时间变化；
- guidance 改口；
- 统计数据修订；
- 页面内容被覆盖。

旧版本不能删除。

### 15.6 Expand source inventory

新材料如果暴露新的高价值来源，应提出 source candidate，而不只是保存当前文档。

## 16. 教 Agent 识别“未来高价值”而不是“今天热搜”

高优先级保存：

- 明确数字和口径；
- 项目里程碑；
- 公司 guidance；
- 资本开支/融资/扩产；
- 政策原文；
- 价格方法论变化；
- 市场规则/合同机制变化；
- 技术路线与单位耗用；
- 高信息量访谈/业绩会原文；
- 统计修订；
- 当时具有代表性的强叙事。

低优先级：

- 无新信息的转载；
- 纯情绪评论；
- 没有日期/来源/数字/机制的泛泛文章；
- 同一内容的大量重复新闻。

## 17. 当前资料也要建立 Expectation

每次公司、协会、政府、券商公开表达未来判断，都应尽快保存：

```text
speaker
said_at
forecast_for
guidance / target / forecast / risk
raw value
rationale
condition
caveat
source
```

这样未来不需要再用搜索引擎抢救“当时怎么想”。

## 18. Agent 的 anti-premature-stop checklist

交工前必须逐项回答：

- 我是否检查了 primary domain？
- 我是否只看了搜索首页？
- 我是否追了二手来源的原始 citation？
- 我是否使用了旧称/别名？
- 我是否检查了 PDF/附件，而不是只看网页正文？
- 我是否做了至少一次反向查询？
- 我是否记录了没找到的东西？
- 我是否把“搜不到”误写成“不存在”？
- 我是否因为达到 token/结果数量就提前停止，而不是达到任务 stop condition？

任何一项为“是/不确定”的风险项都必须在 search_log 说明。

## 19. 低级 agent 的理想工作方式

不要让它自由回答：

> “帮我搜一下 2022 年锂电行业资料。”

而应给它一个任务 packet，让它执行明确状态机：

```text
READ TASK
→ DECOMPOSE CLAIM
→ BUILD SOURCE LADDER
→ RUN QUERY FAMILIES
→ OPEN DOCUMENTS
→ CHASE CITATIONS
→ CHECK PRIMARY
→ REVERSE VERIFY
→ ARCHIVE
→ RETURN STRUCTURED LOG
```

Agent 的能力越弱，任务越应该具体、机械、可检查。