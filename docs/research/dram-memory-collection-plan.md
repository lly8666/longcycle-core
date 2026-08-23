# DRAM 存储半导体历史研究与采集计划

## 1. 第二个真实行业 benchmark

Longcycle 的第二个跨行业 benchmark 选择：**DRAM 存储半导体**。

核心不是写一份“AI 存储景气报告”，而是重建一段可以 point-in-time 回放的 DRAM 产业历史，用它检验 Longcycle 在完全不同于锂电的产业里是否仍能保存：

- Reality：价格、库存、wafer/bit supply、产能、工艺、产品、资本开支、客户认证与实际出货；
- Judgment：管理层、客户、行业机构和研究者当时对供需、价格、节点迁移、HBM、资本开支的判断；
- Outcome：后来实际供需、价格、产品 ramp、份额/利润与当时 Judgment 如何分叉。

第一阶段主时间范围：

```text
2016-01-01 → 2026-12-31
```

2016 作为上一轮大周期前的基线；2017–2018 覆盖强景气与紧缺；2019 覆盖下行；2020–2021 覆盖疫情冲击、数字化需求与供应约束；2022–2023 覆盖库存/价格深度调整；2024–2026 覆盖 AI/HBM 对 DRAM 产品结构、产能分配和资本开支的重塑。

不预先把任何阶段写成“超级周期”“结构性短缺”等结论。那些词只有在保存当时 Judgment 时才能作为当时认知进入。

## 2. 行业边界

### 2.1 Core：DRAM

第一阶段纳入：

- commodity/server DRAM：DDR4、DDR5 及代际迁移；
- mobile DRAM：LPDDR4X、LPDDR5/5X 及代际迁移；
- graphics / high-performance DRAM：GDDR 在影响产品 mix 时进入；
- HBM：HBM2/2E、HBM3/3E、HBM4 等，作为 DRAM 产品/工艺/封装/产能配置分支；
- DRAM wafer capacity、wafer starts、node mix、bit output、yield/ramp、sellable product supply；
- 与 DRAM 直接相关的先进封装、TSV、base die、stacking/qualification bottleneck。

### 2.2 Boundary：NAND

**NAND 不作为第二行业核心。** 只有下列情况进入：

- 同一公司在 DRAM/NAND 之间重新分配资本开支、cleanroom 或设备；
- company-level memory economics 需要拆分 DRAM/NAND；
- NAND 变化直接改变 DRAM 供应策略或管理层 Judgment。

NAND 价格、层数、SSD 产品史本身不在本 campaign 展开。

### 2.3 Downstream boundary

下游只保存直接影响 DRAM 需求与认证的部分：

- server / cloud / AI accelerator；
- PC；
- smartphone；
- graphics；
- automotive / industrial 在成为可见需求变量时进入。

不把服务器、GPU、手机各自扩成完整行业。

## 3. 第一批 actor

核心供给方：

- Samsung Electronics；
- SK hynix；
- Micron Technology；
- CXMT / 长鑫存储。

边界/反例 actor：

- Nanya Technology：用于观察小规模 DRAM 厂在周期、节点迁移和资本开支中的不同反应；
- Winbond 等 specialty DRAM 厂仅在能形成有用反例或供给边界时进入。

下游 actor 不预设“重要性排名”。只有在 source-grounded 资料表明某客户、平台或认证事件改变 DRAM 需求/产品 ramp 时才建立关系。

## 4. 第一轮真正要保存的问题

### A. 价格与定价口径

优先保存：

- contract vs spot；
- DDR4 / DDR5；
- server / PC / mobile 的产品差异；
- HBM 与 conventional DRAM 价格/价值量不要直接拼接；
- 同一价格序列的 density、speed、package、region、currency、frequency 和 source methodology。

核心原则：**同名“DRAM price”不是天然可比序列。**

### B. Supply：从 wafer 到 sellable bit

必须分开：

```text
fab / cleanroom capacity
→ wafer capacity / wafer starts
→ process-node mix
→ die / bit output
→ yield / qualification
→ package / stack output
→ sellable product supply
```

不得把“新增 fab”“wafer capacity”“bit growth”“HBM stack output”当成同一种产能。

### C. 库存

尽量拆：

- supplier inventory；
- channel / module inventory；
- customer inventory；
- days of inventory / absolute value / management commentary；
- inventory correction 的开始、持续、结束 Judgment。

不同公司的财务库存值不能直接当行业 bit inventory。

### D. Demand

按 application 保存当时可得口径：

- server units / memory content；
- PC units / content；
- smartphone units / content；
- AI accelerator / HBM demand；
- graphics / automotive 等边界需求。

把“units growth”和“DRAM bit demand growth”分开。单机 memory content 是重要桥梁变量，但必须有来源。

### E. Process node / technology migration

保存：

- 各厂 DRAM node 名称和量产/ramp；
- 当时管理层对 node transition、cost per bit、yield、EUV 使用的 Judgment；
- 实际 ramp 与原计划的差异；
- node transition 对 bit-per-wafer、成本和有效供给的影响。

厂商自己的 `1a/1b/1c/1α/1β/1γ` 等命名不能假设横向等价。

### F. Capex / fab / equipment

保存：

- company memory/DRAM capex；
- fab/cleanroom 建设、扩建、设备 move-in；
- wafer-capacity 增减；
- production cuts / utilization changes；
- 工艺迁移带来的设备需求；
- 从宣布到真正贡献 bit supply 的时间差。

资本开支金额、WFE 支出、fab 建筑投资和产能贡献必须分开。

### G. HBM 结构变量

HBM 是本 benchmark 的关键压力点，但不单独变成新闻专题。重点保存：

- HBM generation / stack / capacity；
- qualification 与量产时间；
- DRAM die / wafer trade-off；
- packaging / TSV / base-die / advanced-packaging bottleneck；
- HBM 对 conventional DRAM bit supply、product mix、ASP、margin 和 capex 的影响 Judgment；
- 当时的 HBM supply/demand 预测及后续修订。

必须区分：sample、customer qualification、mass production、mass shipment、revenue contribution、mature yield。

### H. Supplier behavior

跟踪：

- production cuts；
- capex cut / increase；
- inventory write-down；
- node migration acceleration/delay；
- product mix changes；
- long-term agreements；
- capacity reservation；
- fab acquisition / greenfield decisions。

### I. 政策与供应链约束

只在影响 DRAM Reality/Judgment 时进入：

- export controls；
- semiconductor industrial policy；
- equipment/material restrictions；
- regional fab incentives；
- trade restrictions / customer access changes。

政策原文和监管文件优先于新闻转述。

### J. 当时 Judgment 与 revision chain

重点寻找：

- “下一季/下一年价格何时触底或上涨”；
- supplier 对 bit demand / bit supply growth 的 forecast；
- inventory normalization timing；
- capex discipline / supply discipline；
- node transition cost-down；
- HBM TAM / growth / qualification / share；
- conventional server DRAM 与 HBM 是否互相挤占供给；
- 中国 DRAM 新增供给的影响；
- bull/base/bear 情景和明确 caveat。

同一主体同一问题优先做 revision chain，而不是只保存最后一次预测。

### K. Outcome

Outcome 不用后来结果重写 Judgment。应保存：

- forecasted price direction vs actual comparable price series；
- forecasted inventory normalization vs later company/customer disclosures；
- planned node/HBM ramp vs actual shipment/production milestones；
- planned supply/capex vs later bit-output and financial outcomes；
- forecasted demand vs later application/bit demand observations。

## 5. 历史 snapshot

第一轮使用半年快照，重大转折再增加季度点：

```text
2016-12-31
2017-06-30
2017-12-31
2018-06-30
2018-12-31
2019-06-30
2019-12-31
2020-06-30
2020-12-31
2021-06-30
2021-12-31
2022-06-30
2022-12-31
2023-06-30
2023-12-31
2024-06-30
2024-12-31
2025-06-30
2025-12-31
2026-06-30
```

每个 snapshot 尽量回答同一组问题：

1. 当时可见的 DRAM 价格和变化方向是什么，口径是什么？
2. 供应商库存、客户库存和渠道库存分别知道多少？
3. 当时预计未来 12–24 个月 bit demand / bit supply 如何变化？
4. 各厂当时在做什么 capex、cut、node transition 和 product-mix 调整？
5. server / PC / mobile / AI 等需求各自被如何判断？
6. 当时 HBM 对 DRAM supply/mix 的影响已经知道多少，而不是后来知道多少？
7. 哪些判断有明确反方或 caveat？
8. 哪些问题当时仍未知？

## 6. 第一轮 source map

### 6.1 公司 primary sources

优先级最高：

- Samsung Electronics IR、regulatory disclosures、earnings releases、Memory Business product/technology announcements；
- SK hynix IR / newsroom / annual and quarterly disclosures；
- Micron Investor Relations、10-K/10-Q、earnings prepared remarks；
- CXMT / 长鑫存储官网产品、公司历史和正式发布；
- Nanya IR / annual reports 在反例需要时进入。

公司资料同时可能承载 Reality 与 Judgment：已发生的出货/产能/财务事实和 forward-looking guidance 必须分开标注。

### 6.2 Standards / industry institutions

- JEDEC：DDR / LPDDR / HBM 等标准定义，用于产品 identity/technology boundary，不用于证明市场份额或商业量产；
- WSTS：半导体/Memory 宏观市场历史，用于大类市场背景和口径检查。

### 6.3 Pricing / market research

可发现并在权限允许时保存：

- TrendForce / DRAMeXchange；
- Omdia、TechInsights、Counterpoint 等历史市场研究；
- 其他明确说明 methodology 的 DRAM price / bit supply-demand 数据。

付费资料不得绕过权限。只保留可公开验证部分、locator、metadata 和人工补齐需求。不同机构序列不可未经校准直接拼接。

### 6.4 Policy / regulatory

- US BIS / Department of Commerce；
- Korea government / regulatory disclosures；
- China MIIT 及相关政策原文；
- Japan METI 等在设备/材料限制直接影响 DRAM 时进入。

### 6.5 Downstream primary sources

当需求问题需要时，优先使用：

- CPU/GPU/platform vendors 的正式产品/财务材料；
- hyperscaler / server OEM / smartphone OEM 的正式披露；
- 只在能够建立 claim-scoped link 时使用。

不要因为下游公司很知名就自动把其所有 AI capex 当成 DRAM demand Reality。

## 7. 当前已验证的 benchmark boundary

截至 campaign 初始化时，公开 primary/current source 已足以确认：

- Samsung 把 HBM、server DDR5 等作为其 DRAM/Memory 产品组合的一部分，并明确讨论 AI demand、有限供给和产品 mix；
- SK hynix 同时讨论 HBM、AI server DRAM、价格、长期供货与产能/工艺安排；
- Micron 明确把 HBM generation、DRAM node、bit supply、cleanroom constraint 和 product-mix economics 放在同一 supply/demand 逻辑里；
- CXMT 官方定位为 DRAM 设计、制造、销售和研发厂商，已有 DDR5、LPDDR5/5X、DDR4、LPDDR4X 产品；
- JEDEC 将 DDR SDRAM 与 HBM 都归于 Main Memory 标准领域。

这只用于定义 research scope，不是把 2026 的公开材料倒灌成历史事实。

## 8. Comparability hazards

DRAM benchmark 必须重点测试以下语义：

1. **price comparability**：spot/contract、density、generation、application 不同；
2. **capacity comparability**：fab area、wafer/month、wafer starts、bit output、stack/package output 不同；
3. **technology comparability**：不同厂 node 名称不是同一物理尺寸；
4. **inventory comparability**：financial inventory value、days、channel units、customer inventory 不同；
5. **demand comparability**：device units、memory content、bit demand、revenue demand 不同；
6. **HBM/conventional mix**：高价值量产品 mix 改变 revenue/ASP，不等于总 bit demand 同比例变化；
7. **known-time**：qualification、yield、customer acceptance 后来才知道的信息不能回写到 sample/announcement 时点；
8. **company scope**：company Memory segment 可能混合 DRAM/NAND，必须避免直接当 DRAM 指标。

## 9. Memory-first / Evidence-final execution

历史恢复遵循现有 CAP-0006：

```text
Stage A: sealed blind memory exhaustion
→ Stage B: high-capability self verification
→ Stage C: delegated claim-scoped Evidence search
→ Evidence / Reality / Judgment / Outcome
```

Stage A 不看本轮互联网搜索结果。当前这份计划中的公开-source scope verification 不得作为 blind-recall 内容注入模型。

第一轮 blind pass 至少覆盖：

- time slices；
- actor exhaustion；
- metric exhaustion；
- mechanism exhaustion；
- contemporaneous narratives；
- old vocabulary / lost web；
- failures / dead ends；
- reverse causality；
- cross-industry effects；
- counterfactual explanations；
- negative space。

## 10. Stop rule

第二行业的第一里程碑不是“搜够多少网页”，而是：

- blind campaign 达到现有 saturation rule 并封存；
- 形成时间 × actor/product × metric coverage matrix；
- 识别一批高价值 Memory Leads、反例、失败史和 revision chains；
- 再进入 self-verification，不修改 blind atlas；
- 只有 Evidence-final 后才允许形成 publishable Reality/Judgment；
- 如果 DRAM 暴露现有产品/语义无法真实表达的关系，先形成具体 semantic-gap note，再决定是否动架构。

本 benchmark 的首要作用是**证明 Longcycle 能迁移到另一种产业机制，或准确暴露不能迁移的地方**，不是追求资料数量。
