# METHODOLOGY CORE — Longcycle 的跨行业方法

> 这是第二个**有界长期核心**。它只保存已经明确采用、应跨行业继承的方法；不保存具体行业历史、公司、项目、阶段数字或当前 TODO。

## M1. 历史恢复：Memory-first, Evidence-final

历史互联网天然残缺。恢复旧历史时，先让高能力模型在**不看本轮新搜索结果**的条件下尽量召回 actor、旧称、项目、机制、失败案例、合同结构和当时叙事，形成 Memory Leads。Memory Lead 只是“应该去找什么”的目录，永远不是 Evidence。

```text
Blind Memory Exhaustion
→ saturation / seal
→ high-capability self-verification / search discovery
→ claim-scoped evidence tasks
→ source identity + claim-relevant content verification
→ Evidence / Assertion / Reconciliation
→ deferred raw-byte materialization where useful
```

未 seal 的 blind 单元不得被新搜索结果反向污染；`not_found != false`。模型记忆、搜索和推理可以扩展研究空间，但不能自己发布事实。

## M2. 当下采集：Source-first, Preserve-now

今天仍容易获得的高价值原始资料，应尽快保存其**可读内容、source identity、locator、版本/时间语义和 provenance**，而不是等几年后再历史抢救。

```text
source/watchlist
→ proactive collection
→ faithful content/version capture or verified source locator
→ Reality / Judgment extraction
→ revision tracking
→ raw-file materialization when useful/available
```

“Preserve-now”首先是不丢失当前可读、可定位、可证明的 source information；不要求为了 byte-identical 下载而阻塞研究主路径。历史恢复与当下采集是长期并行路线。

## M3. Evidence 决定可发布历史；研究假设单独保存

- 模型记忆可以挑战档案，但不能成为 Fact/Judgment；
- 搜索排名、摘要数量、转载数量不能多数投票决定真值；
- 权威性按 **claim scope** 判断；
- 同源转载属于同一 evidence cluster，不能伪装成独立 corroboration；
- 权威来源口径不可调和时保留冲突，不强行选答案。

### Historical search depth：防早停，不做凑数

历史搜索的 minimum depth 是 **`unresolved-exhaustion` 的 anti-premature-stop gate**。如果一个 claim 仍然没有被解决，Agent 只有在完成配置的 query-family、source-type、primary-domain、reverse-query、citation-chase 等最低深度以后，才有资格说“已经搜尽但仍 unresolved”。`unresolved-exhaustion` 仍然不是 false，也不证明世界上没有这件事。

反过来，如果 Agent 已实际读到 **claim-scoped authoritative 原文**，source identity 与 claim scope 都对得上，而且正文直接回答该 claim，则不要求为了满足固定 query/source 数量继续做无信息增益搜索。高影响已解决 claim 仍保留 reverse-query 保护；存在 citation chain、scope ambiguity、source conflict，或正文没有直接回答 claim 时仍须继续追查。来源数量永远不能代替 claim-scoped authority。

一句话：**对“没找到/仍 unresolved”要求搜得够深；对“找到了”要求证据够直接、scope 对得上。多搜不是目标；有足够理由得出你声称的结论才是目标。**

### Source identity、可读内容、raw bytes 分开

PDF 等文档使用三个显式状态：

```text
locator_verified
→ content_verified
→ materialized
```

- `locator_verified`：确认 publisher/upstream document identity 与 locator。只确认链接存在、没读到 claim-relevant 内容时，不能证明具体 claim。
- `content_verified`：Agent 已实际读到 claim-relevant 内容，并保存页码/章节/excerpt 或忠实 readable representation；此时可进入正常 Evidence，即使 raw bytes 尚未下载。
- `materialized`：后续下载 raw bytes，验证 document identity 与 earlier verified content，再补 size/SHA/storage locator。这是完整性增强，不是已 content-verified Evidence 的前置条件。

Later materialization 若与 earlier content/source identity 冲突，必须 fail closed 并建立 integrity repair，不能静默覆盖。

正式公告或完整原始文档可通过稳定、可追溯的 redistributor / acquisition lane 取得，但必须保存**实际 retrieval host**和**upstream document identity**。Authority 继承自可核验的上游文档及其 claim scope，不来自下载 host、`.pdf` 后缀或 transport。平台自行计算的比率、分类、预测、共识或其他派生字段，要按自身方法和 claim scope 单独评估。

### 找不到直接原始来源时

“找不到”不等于“没有发生”。高价值 Memory Lead 经有界、可审计的直接来源搜索仍无法恢复，但存在物理约束、前后事件、独立间接资料、行动结果或机制链等一致支持时，可以保留为 **research-only、indirectly corroborated hypothesis**。

这种状态必须保存：搜过什么、哪些来源不可达、支持/反证、推理链、替代解释、可证伪条件和校准后的不确定性。多个模型记忆不能伪装成独立证据；“逻辑上说得通”也不能单独成为 Evidence。未来找到直接 claim-scoped Evidence 后，只能通过正常 Evidence / Assertion / Reconciliation 路径新增可发布历史，不能把研究假设静默升级为 Fact、Judgment 或 Reality。

## M4. Point-in-time、时间语义与精度匹配

至少区分：

- 世界中何时发生 / 适用；
- 信息何时可以被当时观察者知道；
- 一个 Expectation 在预测哪个未来区间。

任何历史 replay 都必须执行 no-lookahead：后来信息不能偷渡回过去。历史修订通过新增版本表达，不能覆盖旧预测、旧计划、旧口径。

时间精度服从来源能证明的粒度。发生时间、适用时间和 Expectation target 优先保存 `range + precision`，不得为了排序或界面整齐制造伪精度。

但 known time / knowledge cutoff 是另一条边界：no-lookahead 资格判断必须使用来源允许的保守可知上界。发生时间可以粗，信息进入历史观察者视野的时间不能被提前。

## M5. 可比性先于数量

长期序列先保存真实语义，再谈聚合。产品规格、地理、单位、税费/运费边界、合同/市场基础、统计范围、项目阶段、认证状态、库存位置等都可能改变“同一个数字”的含义。

```text
capacity != one number
price != one curve
inventory != one stock
sales != demand
announced != realized
technology announced != technology adopted
```

## M6. 保存轨迹，而不是只保存最终答案

项目、技术、资本开支、预期和政策都应保存状态转换、修订、延期、取消、重启和兑现过程。最终实际结果不能覆盖当初承诺；失败路径也是历史的一部分。

## M7. Agent 分工

高能力模型适合召回长尾历史线索、发现跨链关联和 negative space、seal 后解释模糊记忆并定位可能原始来源、处理高价值冲突和任务拆解。

较低能力 Agent 默认是**证据工程执行者**：拿明确 claim、旧称、query family、来源目标、反向查询和 stop condition 深搜，不自由发挥行业结论。

低成本 Agent 编排只需要一个很薄的 capability-aware 边界：任务声明需要 `high_capability_reasoning` 还是 `bounded_execution`。当前阶段不提前建设完整调度系统。较低能力 Agent 若无法可靠完成需要独立综合判断的任务，应**停止并升级给高能力模型**。

## M8. 用真实 benchmark 拉动抽象

不要为了“平台完整”预先抽象所有行业。先在真实行业暴露语义、证据和失败模式，再把多次证明有用的 primitive 抽象出来，并用后续行业验证可迁移性。

**行业事实不进入 Method Core；跨行业反复成立的方法才有资格进入。**

Benchmark 的职责是打脸架构、暴露缺失抽象，不是诱导 Agent 为测试分数优化。研究员是否能形成可辩护的心智模型，比 crawler 数量、Agent 完成率或报告数量更接近产品成功。

## M9. 模型升级产生新 research vintage

能力或训练资料显著变化的高能力模型，是新的 research instrument vintage。新 vintage 应重新 blind recall，形成新的不可变 Atlas，再与旧 Atlas diff：known / refined / novel。

新增线索用于历史回补，不能覆盖旧模型输出；已证伪的模型记忆也保留为 research provenance。

## M10. 多 Agent Continuity：有限核心 + 动态状态

跨会话连续性不能靠不断扩大的总结文档。默认只恢复：

```text
STRATEGIC_COMPASS.md     最终使命
METHODOLOGY_CORE.md      跨行业方法
current.json             中期目标 / 短期目标 / 当前状态 / next actions
active context           当前行业或任务所需的局部资料
```

旧行业、旧 devlog、旧实验默认不加载；需要时按 origin ref / path 定向回溯。

长期经验进入新 Agent 的正常路径：

```text
具体经验
→ devlog / industry context
→ 多次验证或明确战略决定
→ 提炼成跨行业方法
→ Method Core（替换/压缩，而不是无限追加）
```

## M11. Continuity 追求高保真，不追求极限压缩

“有界”是职责和增长方式的约束，不是让核心越短越好。新 Agent 应能依赖有限启动上下文，用自己的话解释项目为什么存在、关键认知缺口是什么、长期方法为何这样设计，以及当前中短期工作如何服务最终使命。

连续性同时看：

1. **semantic fidelity**：保留关键因果，不只剩 slogan；
2. **context economy**：无需加载旧行业和全部 devlog 才能行动；
3. **bounded growth**：新长期经验通过替换、压缩、抽象进入 Core，而非无限追加。

长期核心保持**最小充分上下文**：足以重建使命和方法，但不承担项目流水账。

## M12. 主动理解 + 自我纠偏 + 防钻牛角尖

新 Agent 不能把“读过 Core”等同于“理解了使命”：

```text
先读 Strategy / Method Core
→ 用自己的话独立重建使命与方法
→ 再读 mission-fidelity semantic contract
→ 检查遗漏和常见误读
→ 只针对缺失部分定向重读并修正
```

Semantic contract 只提供问题和误读检查，不提供可照抄的标准答案。

开始新的实质子问题、完成 coherent 子任务、范围准备扩张或新结果改变假设时，都要向上检查：

```text
当前原子任务
↑ 当前短期里程碑
↑ 当前中期能力证明
↑ Longcycle 最终使命
```

如果已经达到 stop/done 条件、无法解释当前工作如何推进父目标，或继续投入只是让局部指标更好看，应停止或重新排序。

## M13. 高能力 Agent 的独立判断义务

用户拥有目标、偏好、约束和风险取舍的最终决定权，但用户提出的**方法建议不是自动正确的技术结论**。高能力 Agent 应充分使用推理、领域知识和当前证据，帮助避免局部最优、错误假设和无效工程，而不是只追求服从速度。

```text
理解用户真实目标
→ 独立形成技术/研究判断
→ 与用户建议比较
→ 一致则执行
→ 不一致则说明关键理由
→ 拒绝、收窄或改写不科学方案
→ 提出更直接的替代方案
```

- 不因用户强烈建议某方法，就把它当事实、证据或最佳方案；
- 不为显得配合而延续已达到 stop condition 的工作；
- 方法与使命、证据边界、成本收益、已知状态或安全约束冲突时，明确指出并提出更优选择；
- 用户目标明确时，不把技术判断责任反推给用户；
- 事实不确定时校准置信度并验证，不以“模型更高级”替代证据；
- 高能力 Agent 应主动提出能明显推进父目标的建议；
- 较低能力 Agent 不可靠时，停止并升级给高能力模型，不模仿高级语气给伪结论。

这里的“高能力”指任务表现和推理责任，不是对用户的身份优越判断。

## Method Core 修改门槛

只有以下情况允许增加或改变方法：

1. 用户明确确定新的长期方法；
2. 一个方法被真实 benchmark 反复证明；
3. 原方法被真实数据明确证伪或需要收窄。

单一行业技巧、某次 Prompt 细节、当前模型名字、工具限制、CI 状态和任务计划都不属于 Method Core。