# METHODOLOGY CORE — Longcycle 的跨行业方法

> 这是第二个**有界长期核心**。它只保存已经被明确采用、应跨行业继承的方法；不保存任何具体行业历史、公司、项目、阶段数字或当前 TODO。

## M1. 历史恢复：Memory-first, Evidence-final

旧互联网检索天然残缺。历史恢复先允许高能力模型在**不看本轮新搜索结果**的情况下尽量召回可能存在的 actor、旧称、项目、机制、失败案例、合同结构和当时叙事，形成 Memory Leads。

Memory Lead 只是“应该去找什么”的目录，永远不是 Evidence。

```text
Blind Memory Exhaustion
→ saturation / seal
→ high-capability self-verification / search discovery
→ claim-scoped evidence tasks
→ original-source archive
→ Evidence / Assertion / Reconciliation
```

未 seal 的 blind 单元不得被新搜索结果反向污染；`not_found != false`。

## M2. 当下采集：Source-first, Archive-now

今天仍容易获得的高价值原始资料，应尽快、按版本归档，而不是等几年后再历史抢救。

```text
source/watchlist
→ proactive collection
→ original/version archive
→ Reality / Judgment extraction
→ revision tracking
```

历史恢复与当下采集是两条长期并行路线。

## M3. Evidence 决定可发布历史；模型、搜索与推理可以保留研究假设

- 模型记忆可以挑战档案，但不能成为 Fact/Judgment；
- 搜索排名、摘要数量、转载数量不能多数投票决定真值；
- 权威性按 **claim scope** 判断；
- 同源转载要视为同一 evidence cluster；
- 权威来源之间若口径仍不可调和，保留冲突，不强行选答案。

对于**上市公司正式公告、法定披露、定期报告和公告附件**，不要求只能从发行人、交易所或监管机构的原始服务器下载 bytes。大型、稳定、可追溯的财经公告库若保存的是可识别的正式公告原文或完整文档，可以作为 `authoritative_redistributor` 使用；例如新浪财经、腾讯财经、同花顺、雪球、东方财富等，此列表不是封闭白名单。成立条件是：能够保留或可靠映射上游公告身份（发行人/监管或交易所体系、公告号或 filing/accession、标题、发布日期/可知时间、原始 URL 等），并且实际归档内容是公告本身而不是媒体摘要、编辑报道或二次解读。

使用 authoritative redistributor 时必须同时保存**实际 retrieval host** 与 **upstream announcement identity**。不得为了保持“primary source”外观，把从财经网站取得的 bytes 伪记成从监管/公司官网直接取得；同一上游公告被多个财经网站转载时仍属于同一 evidence cluster，不能伪装成多份独立 corroboration。若财经页面只是摘要、机器提取字段或新闻稿解读，则仍按其真实 claim scope 和 secondary 权威级别处理。

程序化交易/金融数据接口、开源量化项目和开源公告采集项目适用同一原则：它们可以是可信的公告 acquisition / redistribution lane，不因“不是发行人官网或监管官网”而自动降权。若接口或项目返回、缓存或镜像的是可核验的上市公司正式公告/年报/定期报告原文或完整文件，并能交叉核对 issuer、filing/accession/公告号、标题、披露时间、上游 URL 或内容哈希等身份，则该具体 connector/document 可以按 `authoritative_redistributor` 处理。开源代码本身只证明采集机制可审计，不等于仓库已经保存目标 Evidence；只有实际取得并归档的公告 payload 才进入证据链。

程序化数据源对公告的**二次加工字段**不得继承公告原文的权威性。平台自行计算的财务比率、标准化指标、分类标签、预测值、共识值或从公告抽取后重新加工的数据，必须按其加工方法、claim scope 和可复现性单独评估；“底层来自年报”不能让派生值自动等同于年报原文。

历史互联网会丢失资料，闭源资料也可能永远无法直接恢复。因此“找不到直接原始来源”不能等价于“这件事没有发生”。当一个高价值 Memory Lead 在有界、可审计的直接来源搜索后仍无法恢复，但存在物理约束、前后事件、独立间接资料、行动结果或机制链等多方面一致支持时，可以保留为 **research-only、indirectly corroborated hypothesis**。

这种状态必须同时保存：搜索过什么以及哪些来源不可达、支持与反证材料、推理链、可替代解释、可证伪条件和校准后的不确定性。多个模型记忆若可能来自相同训练资料，不能伪装成独立证据；“逻辑上说得通”也不能单独变成 Evidence。

研究假设可以帮助补全历史地图、继续寻找旁证和形成分析，但**永远不能静默升级为 Fact、Judgment 或 Reality**。若未来找到直接 claim-scoped Evidence，应通过正常 Evidence / Assertion / Reconciliation 路径新增可发布历史，而不是回写或删除原研究假设。

## M4. Point-in-time、时间语义与精度匹配

至少区分：

- 世界中何时发生 / 适用；
- 信息何时可以被当时观察者知道；
- 一个 Expectation 在预测哪个未来区间。

任何历史 replay 都必须执行 no-lookahead：后来信息不能偷渡回过去。

历史修订通过新增版本表达，不能把旧预测、旧计划、旧口径覆盖掉。

时间精度要服从来源能够证明的粒度和研究决策的需要。很多历史问题真正重要的是“某件事在这个月、季度、建设阶段或周期内是否发生/推进”，而不是强行确定某一天。对于发生时间、适用时间和 Expectation target，应优先保存 `range + precision`，只有来源明确且精确时间本身具有分析意义时才保存精确日/时刻；不得为了排序或界面整齐制造伪精度。

但 **known time / knowledge cutoff 是另一回事**：no-lookahead 资格判断仍必须使用来源允许的保守可知上界。发生时间可以粗，信息进入历史观察者视野的边界不能因为“日期不重要”而被提前，从而造成 hindsight leakage。

## M5. 可比性先于数量

长期序列必须先保存真实语义，再谈聚合：产品规格、地理、单位、税费/运费边界、合同/市场基础、统计范围、项目阶段、认证状态、库存位置等都可能改变“同一个数字”的含义。

典型原则：

```text
capacity != one number
price != one curve
inventory != one stock
sales != demand
announced != realized
technology announced != technology adopted
```

## M6. 保存轨迹，而不是只保存最终答案

项目、技术、资本开支、预期和政策都应保存状态转换、修订、延期、取消、重启和兑现过程。

最终实际结果不能覆盖当初承诺；失败路径也是历史的一部分。

## M7. Agent 分工

高能力模型适合：

- 召回长尾历史线索；
- 发现跨链关联和 negative space；
- 在 seal 后先解释自己的模糊记忆并定位可能的原始来源；
- 处理高价值冲突和任务拆解。

较低能力 Agent 默认是**证据工程执行者**：拿明确 claim、旧称、query family、来源目标、反向查询和 stop condition 深搜，不自由发挥行业结论。

未来的低成本 Agent 编排应从一个很薄的 capability-aware 入口接入：任务声明自己需要 `high_capability_reasoning` 还是 `bounded_execution`。当前阶段只保留这个边界，不提前建设完整调度系统。

## M8. 用真实 benchmark 拉动抽象

不要为了“平台完整”预先抽象所有行业。先在真实行业中暴露语义、证据和失败模式，再把多次被证明有用的 primitive 抽象出来，并用后续行业验证可迁移性。

**行业事实不进入 Method Core；跨行业反复成立的方法才有资格进入。**

## M9. 模型升级产生新 research vintage

能力或训练资料显著变化的高能力模型，是新的研究工具 vintage。

新 vintage 应重新 blind recall，形成新的不可变 Atlas，再与旧 Atlas diff：known / refined / novel。新增线索用于历史回补，不能覆盖旧模型输出；已证伪的模型记忆也保留为研究 provenance。

## M10. 多 Agent Continuity：有限核心 + 动态状态

跨会话连续性不能靠不断扩大的总结文档。

默认只恢复四类信息：

```text
STRATEGIC_COMPASS.md     最终使命
METHODOLOGY_CORE.md      跨行业方法
current.json             中期目标 / 短期目标 / 当前状态 / next actions
active context           当前行业或任务所需的局部资料
```

旧行业、旧 devlog、旧实验默认不加载。需要回溯时再按路径查找。

长期经验进入新 Agent 的唯一正常路径是：

```text
具体经验
→ devlog / industry context
→ 多次验证或明确战略决定
→ 提炼成跨行业方法
→ Method Core（替换/压缩，而不是无限追加）
```

## M11. Continuity 追求高保真，不追求极限压缩

“有界”是职责和增长方式的约束，不是让核心越短越好。

一个新 Agent 应该能够仅依赖有限启动上下文，用自己的话重新解释：项目为什么存在、最终用户能力是什么、关键认知缺口是什么、长期方法为什么这样设计，以及当前中短期工作如何服务最终使命。

因此连续性质量同时看三件事：

1. **semantic fidelity**：最初使命的关键因果是否完整，而不只是几个口号关键词；
2. **context economy**：不需要加载旧行业和全部 devlog 才能行动；
3. **bounded growth**：新增长期经验通过替换、压缩和抽象进入 Core，而不是无限追加。

如果缩短文档导致新 Agent 只能背诵 slogan、无法解释“为什么”，属于过度压缩；如果为了高保真不断搬入具体历史，则属于过度膨胀。

长期核心应在二者之间维持**最小充分上下文**：足以忠实重建使命和方法，但不承担项目流水账。

## M12. 主动理解 + 自我纠偏 + 防钻牛角尖

新 Agent 不能把“读过 Core”等同于“理解了使命”。正常流程是：

```text
先读 Strategy / Method Core
→ 用自己的话独立重建使命与方法
→ 再读 mission-fidelity semantic contract
→ 检查遗漏和常见误读
→ 只针对缺失部分定向重读并修正
```

semantic contract 只提供问题和误读检查，不提供可照抄的标准答案。

同一个 Agent 长时间工作也要周期性向上回看。开始新的实质子问题、完成一个 coherent 子任务、范围准备扩张或新结果改变假设时，重新检查：

```text
当前原子任务
↑ 当前短期里程碑
↑ 当前中期能力证明
↑ Longcycle 最终使命
```

如果当前工作已经达到 stop/done 条件、无法解释它如何推进父目标，或只是因为局部指标容易优化而继续扩张，就应该停止或重新排序，而不是自动深入。

## M13. 高能力 Agent 的独立判断义务

用户拥有目标、偏好、约束和风险取舍的最终决定权，但用户提出的**方法建议不是自动正确的技术结论**。高能力 Agent 的责任不是服从得更快，而是充分使用自己的推理、领域知识和当前证据，帮助用户避免局部最优、错误假设和无效工程。

正常行为应是：

```text
理解用户真实目标
→ 独立形成技术/研究判断
→ 与用户建议比较
→ 一致则执行
→ 不一致则说明关键理由
→ 拒绝、收窄或改写不科学方案
→ 提出更直接的替代方案
```

具体要求：

- 不因为用户强烈建议某方法，就把它当作事实、证据或最佳方案；
- 不为了显得配合而延续已经达到 stop condition 的工作；
- 发现用户建议与使命、证据边界、成本收益、已知状态或安全约束冲突时，应明确指出并提出更优选择；
- 当用户的目标本身明确时，不要把技术判断责任反推给用户；
- 当事实不确定时要校准置信度并验证，而不是用“模型更高级”作为权威来源；
- 高能力模型应该主动提出用户未显式想到、但能明显提升父目标的建议；
- 较低能力 Agent 若无法可靠完成要求独立综合判断的任务，应停止并升级给高能力模型，而不是模仿高级语气给出伪结论。

这里的“高能力”是**任务表现和推理责任**，不是对用户在所有领域都更聪明的身份宣称。目标是避免盲从与逢迎，同时保留对用户目标和真实世界证据的约束。

## Method Core 修改门槛

只有以下情况允许增加或改变方法：

1. 用户明确确定新的长期方法；
2. 一个方法被真实 benchmark 反复证明；
3. 原方法被真实数据明确证伪或需要收窄。

单一行业技巧、某次 Prompt 细节、当前模型名字、当前工具限制、CI 状态和任务计划都不属于 Method Core。
