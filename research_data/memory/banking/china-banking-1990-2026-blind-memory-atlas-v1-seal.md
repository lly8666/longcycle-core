# 中国银行业 1990–2026 Blind Memory Atlas v1 — Seal Manifest

- status: `SEALED_MEMORY_ATLAS`
- memory_vintage: `banking-china-1990-2026-v1`
- active_scope: `PRC_DOMESTIC_BANKING_ONLY`
- approximate_time_range: `1990-01-01/2026-08-31`
- structural_saturation: `true`
- evidence_authority: `NONE`
- seal_rule: seal 后不得修改四个 blind pass 来吸收新搜索、新证据或后来 Outcome；任何新信息只能进入 post-seal research/evidence artifact。

## 1. Sealed components

### Pass 01 — 一级行业骨架

- path: `research_data/memory/banking/china-banking-1990-2026-blind-memory-atlas-v1-pass01.md`
- introducing_commit: `e9e466d84c62a870bb6f3371288ef799147d66c9`
- blob_sha: `1d37b3108bcd403d4c799ffa9d5bd46a058fad32`
- role: 行业结构、资产负债表、盈利、存款、地产、城投、影子银行、资管、资本、流动性、历史分段、机制、指标、Judgment/Outcome、unknowns。

### Pass 02 — 改革、制度、机构与风险事件

- path: `research_data/memory/banking/china-banking-1990-2026-blind-memory-atlas-v1-pass02-history-institutions.md`
- introducing_commit: `4b8d470f12132f80b494aa96db428bca06fa65bd`
- blob_sha: `96a42774f034eb82b369896654012bb6c390a15c`
- role: 1990s–2026 改革/监管/信用周期、影子银行、地产、化债、中小银行风险和代表机构时间线线索。

### Pass 03 — 语义、商业模式与反例

- path: `research_data/memory/banking/china-banking-1990-2026-blind-memory-atlas-v1-pass03-semantics-business-models.md`
- introducing_commit: `4f15efd78fa703f09b9d35a2c006e656c71486a2`
- blob_sha: `dd4a06a3b1cdc0f68b4c39754b9eb8403d47016a`
- role: 会计/监管可比性、客户经济学、资金/外汇、治理、区域、运营科技、估值、财政边界、综合金融与反例。

### Pass 04 — negative-space exhaustion

- path: `research_data/memory/banking/china-banking-1990-2026-blind-memory-atlas-v1-pass04-negative-space.md`
- introducing_commit: `be680ded958123ece14affbdf692e77982faa83a`
- blob_sha: `2afd31a8b0d10b127606ac391323d2b9657a4eef`
- role: 农村金融、政策金融、信用卡/消费金融、案件风险、并购重组、政策型信贷、跨境、人口、主权/地方债与宏观 regime，最后测试是否仍有新的一级结构。

## 2. Saturation decision

四轮 blind recall 使用了不同的切面，而不是重复同一种时间线：

1. top-down 行业骨架；
2. historical/institutional chronology；
3. semantic/business-model/contrarian cross-section；
4. negative-space audit。

Pass 04 的新增主题均能挂回前三轮形成的既有顶层分类，没有再产生一个必须新建的一级行业域。因此对“约 1990–2026 中国银行业的研究心智地图”判断为 `STRUCTURAL_BLIND_SATURATION`。

这不是“模型记住了所有银行事实”。它只表示继续自由召回的边际产出主要会是：更多年份、更多个案、更多银行、更多指标细节，而不是改变顶层研究结构。那些细节以后仍可通过 post-seal 模型自检产生新的 research leads，但不能回写本 vintage。

## 3. Critical contamination carve-out

本 vintage **不能声称整个会话从未见过任何中国银行资料**。

在用户将 Banking 战略明确重置为“先全行业模型提取，再联网核查”之前，本 workstream 已经完成过一个小型招商银行方法试运行，并读取过与 `2023-08-28` 招商银行中期业绩交流会相关的来源可识别内容。

因此：

- `招商银行 2023-08-28 NIM / 存款成本 Judgment` 及其直接衍生细节标记为 `PREEXPOSED_NOT_BLIND`；
- 四个 pass 中若出现与该已见材料重合的具体招行 2023-08-28 观点，不得把“模型能回忆出来”计为 blind Memory evidence；
- 该预暴露不改变 Atlas 的行业结构 saturation 判断，因为顶层银行结构并不依赖这一条招行证据；
- 自本次全行业 campaign 启动以后，没有再进行新的国内银行事实/证据联网搜索；
- 后续 Evidence-final 阶段仍可正常使用此前招行 artifact，但必须保持其已有 provenance，而不是伪装成本 vintage 的 blind lead。

## 4. Evidence boundary

整个 Atlas 的 authority 均为 `MEMORY_LEADS_ONLY`：

- 不能发布为 Fact / Reality；
- 不能发布为 contemporaneous Judgment；
- 不能因为模型重复多次就变成 corroboration；
- 不能把常见历史叙事当成准确日期或数字；
- `not_found != false`；
- 任何具体 claim 都需要 seal 后 claim-scoped source identity + content verification。

## 5. Temporal boundary

Atlas 中所有历史日期默认遵守原 pass 的 approximate precision。后续 Evidence-final 至少区分：

1. event/effective time；
2. source first-known / conservative known-time；
3. Longcycle system adoption time；
4. Judgment 的 expectation target period。

后来结果不得回写旧 Judgment。

## 6. Post-seal evidence program — high-level ordering

seal 后不应该随机搜银行新闻，而应按“先建立全行业长期 backbone，再下钻代表银行”的顺序：

### Wave A — 1990–2026 制度与宏观银行史 backbone

优先验证：

- 1990s 专业银行商业化与政策性银行分离；
- 大行资本补充、AMC 不良剥离、股份制改革；
- 银行业监管机构演变；
- 利率市场化；
- 存款保险；
- 资本/流动性/资产分类规则主要代际变化；
- 2008 后信用扩张；
- 2010s 同业/理财/资管监管；
- 2020s 房地产、化债、低息差相关制度环境。

这一层主要使用央行、金融监管、国务院/财政部等官方历史源。

### Wave B — 行业长期数据 backbone

按可比口径构建：

- 银行业总资产/贷款/存款；
- NIM / 盈利；
- 不良与拨备；
- 资本；
- 银行类型结构；
- 关键政策利率/贷款定价制度变量。

若历史统计口径变化，宁可分段保存，也不强拼一条伪连续曲线。

### Wave C — 代表银行 trajectories

从大行、股份行、城商行、农商行各选代表机构，保存：

- Reality；
- 当期管理层 Judgment；
- 后来 Outcome；
- 关键指标；
- 重大策略修订。

### Wave D — 机制/风险专题

例如：

- 信贷刺激→后续不良；
- 影子银行→去杠杆；
- 房地产；
- 城投化债；
- 存款定期化/NIM；
- 中小银行风险处置；
- 零售/财富；
- 科技与支付。

## 7. First post-seal atomic claim family

从 1990 起做长期数据时，最高信息增益不是马上回到招行 2024H1，而是先验证最早的制度 backbone：

> **1990s 中国银行体系从专业银行/政策性功能混合状态向现代商业银行体系迁移的关键制度节点是什么？**

第一组 claim-scoped Evidence 应优先确认：

- 政策性银行建立/职能分离；
- 商业银行基础法律框架；
- 1997–1999 前后银行资本/不良资产风险治理；
- AMC 建立及其 claim-scoped官方来源。

确认这些后，2000s 大行改制上市的 Reality/Judgment 才有正确历史起点。

## 8. Seal declaration

`banking-china-1990-2026-v1` 从本 manifest 提交后冻结。

任何后续新网络材料、模型新记忆、来源冲突、精确日期修正或 Outcome 都必须：

- 新建 post-seal artifact；
- 保留 Evidence / research-only 权威等级；
- 不修改四个 blind pass 以制造“模型原本就知道”的假象。

Seal conclusion: `STRUCTURAL_BLIND_SATURATION_WITH_EXPLICIT_PREEXPOSURE_CARVEOUT`.
