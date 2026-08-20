# 高级模型记忆榨取协议：先建立历史目录，再逐条取证

## 1. 核心判断

对历史产业研究，公开互联网不是一个完整、稳定、易检索的数据库。历史网页会消失，附件会换地址，搜索引擎偏向新内容，旧术语会失效，付费资料和 PDF 难以索引，大量当时重要但后来失去关注的信息不会排在搜索结果前面。

因此 Longcycle 对历史资料的默认路径不是：

```text
低成本 Agent 广搜互联网
→ 得到少量结果
→ 高级模型总结
```

而是：

```text
高级模型尽可能榨取已有产业记忆
→ 建立 Memory Atlas / Historical Lead Map
→ 高级模型自行做第一轮重点验证（可选但推荐）
→ 低成本 Agent 按 lead 逐条深挖、追原始来源、补证据
→ Evidence / Reality / Expectation
→ 高级模型再次做缺口扫描
```

原则：

> **历史阶段：Memory-first, evidence-final.**
>
> 模型记忆负责尽可能完整地告诉系统“应该去找什么”；原始证据负责决定“最终能确认什么”。

Memory Lead 仍然不能直接成为 Fact 或 Judgment。

## 2. 为什么“一次 blind recall”仍然不够

模型知识分布在大量不同关联中。一个宽泛问题会优先激活最显著、最常见的记忆，导致长尾信息被压住。

因此“输出全部记忆”不能理解成一个 prompt，而应理解成一个**多轮检索模型自身参数空间的协议**。

我们不能保证真正穷尽模型的全部知识，但可以通过正交分解、递归追问、反向检索和饱和度检查显著提高覆盖率。

## 3. Memory Exhaustion Campaign

一个行业/时期的高级模型记忆提取称为一个 `memory campaign`。

每个 campaign 由多组互相尽量独立的 pass 组成。第一阶段所有 pass 默认 `source_visibility=none`，不允许看到本轮互联网搜索结果。

### 3.1 Pass Family A：时间切片

不要一次问 2019–2026。

按半年、年度、周期阶段分别回忆：

- 当时最重要的价格变化；
- 供给变化；
- 需求变化；
- 库存变化；
- 公司行为；
- 政策；
- 项目；
- 市场叙事；
- 当时未兑现的预期。

对重大阶段再下钻到季度。

### 3.2 Pass Family B：产业链切片

对每个节点单独激活记忆：

```text
锂矿 / 盐湖
锂精矿
碳酸锂 / 氢氧化锂
正极 / 前驱体
负极
隔膜
电解液 / 六氟
电芯
Pack
新能源车
储能
回收
设备
```

不能只问“锂电行业发生了什么”。

### 3.3 Pass Family C：Actor Exhaustion

从“谁参与了这个周期”反向榨取：

- 头部公司；
- 当时很重要、后来边缘化或消失的公司；
- 矿山/项目；
- 政府/协会；
- 价格机构；
- 关键券商/研究团队；
- 设备商；
- 大客户；
- 海外关键供给方；
- 当时被市场频繁讨论但今天不再显眼的参与者。

对每个 actor 再问：

> 这个 actor 在该时期做过哪些可能改变供需、价格、成本、技术路线或市场预期的动作？

### 3.4 Pass Family D：Metric Exhaustion

从指标出发，而不是事件出发：

```text
价格
价差
加工费
矿价
产能
有效产能
产量
开工率
良率
库存
进口/出口
销量
装车量
排产
订单
资本开支
预付款
应收
现金成本
利润
单位材料耗用
项目建设周期
认证周期
```

逐个问：这个指标在各阶段有没有异常、口径变化、领先/滞后关系或市场曾高度关注的节点？

### 3.5 Pass Family E：Mechanism Exhaustion

强制模型只回忆“机制”，不列大事件：

- 价格如何形成；
- 利润如何在产业链分配；
- 高价如何刺激供给；
- 扩产从公告到有效供给的路径；
- 低价如何导致减产/停产/延迟；
- 库存如何在链条间转移；
- 技术变化如何改变单位耗用；
- 资本市场如何加速/阻断扩产；
- 客户认证如何延迟有效产能；
- 海外政策如何影响国内供需。

每个机制必须继续追问：

> 你记得哪些具体历史例子可能体现过这个机制？

### 3.6 Pass Family F：Contemporaneous Narrative Exhaustion

只回忆“当时人们在相信什么”，禁止用后来结果总结：

- 主流共识；
- 少数派观点；
- 高景气期乐观叙事；
- 低景气期悲观叙事；
- 当时流行的长期预测数字；
- 哪些项目被认为会按时/不会按时投产；
- 哪种技术被认为会替代谁；
- 哪些风险当时被忽略；
- 哪些风险当时被过度重视。

这些输出只能形成 Expectation 搜索 lead。

### 3.7 Pass Family G：Old Vocabulary / Lost Web

强制回忆当年的：

- 公司曾用名；
- 项目旧称；
- 矿山旧称/英文名；
- 旧技术名称；
- 旧指标名称；
- 当年媒体常用表达；
- 当时报告标题常出现的词；
- 可能存在于旧 PDF 文件名中的关键词。

这一轮的主要产物是搜索词，不是事实。

### 3.8 Pass Family H：Failure / Dead-end Memory

普通历史整理天然偏向成功者。单独追问：

- 宣布后取消的项目；
- 延期多年才投产的项目；
- 技术路线失败；
- 曾被看好但后来退出的公司；
- 产能建成但长期低利用率；
- 大规模减值、出售或停产；
- 当时市场热议但后来没有兑现的需求故事。

失败史对周期研究通常比成功史更重要。

### 3.9 Pass Family I：Reverse Causality

先给一个后来结果，只用于激活更早的潜在原因，不允许把结果写回过去：

例如：

> 2023 年锂价大幅下行。往前倒推 6、12、18、24、36 个月，你记得有哪些供给、库存、资本开支、需求预期和定价机制变化可能提前埋下了条件？

输出仍然只是 causal lead，随后必须回到当时资料验证。

### 3.10 Pass Family J：Cross-chain / Cross-industry

强制跳出当前节点：

- 哪个上游变化影响了下游？
- 哪个下游变化反向改变上游定价？
- 哪个非锂电行业因素改变了这一段周期？
- 哪些金融、物流、电力、环保、地产、汽车金融、贸易政策因素可能被纯产业链数据漏掉？

### 3.11 Pass Family K：Counterfactual Prompting

问模型：

> 如果某个著名解释其实不是主要原因，还有哪些当时存在的替代解释？

目的不是制造观点，而是避免记忆地图被最流行的后来叙事垄断。

### 3.12 Pass Family L：Negative Space

给模型当前 Memory Atlas 的目录（不是新搜索结果），问：

> 哪些空白让这段历史不像一个完整产业周期？

再针对每个空白递归展开。

## 4. Recursive Recall：每条重要 lead 再问四次

对于高重要度 lead，不立即搜索。先在 blind 阶段递归扩展：

1. **Who else?** 还有哪些 actor 与它相关？
2. **What preceded it?** 它之前通常有什么先行变化？
3. **What followed it?** 它之后可能出现什么行为或数据变化？
4. **What was it called then?** 当时会用什么词描述？

这四问经常能把一个宽泛记忆变成可搜索的历史坐标。

## 5. 强制去显著性：避免只输出“大家都知道的东西”

每个 pass 必须把输出分为：

- `obvious_landmarks`：著名历史节点；
- `long_tail_leads`：不一定著名但可能重要；
- `forgotten_actors`：今天很少提、当时可能重要；
- `mechanism_leads`：不是新闻事件，而是运行机制；
- `search_keys`：旧词、别名、报告标题词；
- `uncertain_fragments`：模型只有碎片记忆但认为值得追的内容。

至少一半 token budget 应优先给后五类，而不是重复常识。

## 6. 自我补漏轮

完成所有正交 pass 后，让同一高级模型只看已经生成的 Memory Atlas（仍不看互联网），执行三轮补漏：

### Round 1：重复压缩

把同义 lead 聚类，腾出上下文空间。

### Round 2：遗漏审查

逐个时间段 × 产业链 × 指标检查空格。

### Round 3：专家质疑

提示模型：

> 假设一位做了十几年该行业的老产业人士认为这份目录“太像公开研报摘要”，他最可能指出你漏掉哪些工程、合同、库存、项目、公司行为和当时口头叙事？

新生成的 lead 继续进入 atlas。

## 7. 什么时候算“榨得差不多了”

不能用“模型说没有更多了”作为停止条件。

使用近似 saturation：

- 连续 3 个正交 pass 新增的高重要度非重复 lead 很少；
- 时间 × 链条 × metric coverage matrix 已没有大面积空白；
- 新增内容主要是已有 lead 的同义表达；
- forgotten actors / failures / terminology / mechanism 等长尾类别不再快速增加。

记录 `stop_reason`，但永远允许新模型版本重新打开 campaign。

## 8. Sealed Blind Atlas

第一阶段完成后立即封存：

```text
model identity
model version
模型声明 knowledge cutoff（若可得）
protocol version
industry scope
period scope
所有 pass
原始输出
归一化 leads
lead relations
coverage matrix
stop reason
```

之后任何互联网搜索不得修改这份 atlas。

## 9. 高级模型可以自己搜索，但必须进入新阶段

推荐让同一个高级模型继续执行 `self_verify`，因为它理解自己生成 lead 时的关联背景，往往比低级 agent 更会设计第一轮检索。

但必须新建 run：

```text
Stage A: sealed blind recall
        ↓
Stage B: high-model self verification
        ↓
Stage C: delegated evidence search
```

Stage B 允许：

- 搜索 lead 的准确名称和旧称；
- 找 primary source；
- 判断网页是否只是重复转载；
- 发现更精确项目名/公司名/报告名；
- 为低级 agent 改写更具体的任务。

Stage B 不允许：

- 回头修改 blind recall，假装原本就记得；
- 把搜索摘要直接升级为 Fact；
- 因为搜不到就删除 lead；
- 因为大量二手文章一致就结束验证。

## 10. 低级 Agent 的角色因此改变

历史阶段低级 agent 不再主要接收“锂电 2021 年发生了什么”这样的宽任务。

它应主要接收：

```text
lead_id
模型记忆摘要
可能时间
可能 actor
旧称/别名
可能机制
建议 query families
目标 primary source 类型
什么证据算支持
什么证据算反驳
最低搜索深度
停止条件
```

也就是说：

> **高级模型负责生成历史目录与搜索假设，低级 agent 负责证据工程。**

## 11. 搜不到不是反证

历史资料检索中：

```text
not_found != false
```

只能得到：

```text
not_yet_verified
```

只有 claim-scoped authoritative/primary evidence 能明确反驳时，才允许 `primary_contradicts_lead`。

## 12. 输出目标

Memory Exhaustion Campaign 的成功标准不是 lead 数量，而是：

> 当把 atlas 给真正做过这个行业的人看时，他很难再轻易指出一个我们完全没想到、且对周期重要的大类历史。

然后才进入真正困难但更机械的工作：逐条寻找证据。