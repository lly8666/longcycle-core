# 存储半导体（DRAM + NAND）历史研究与采集计划

## 1. 第三个真实行业 benchmark

Longcycle 的行业 benchmark 顺序现在明确为：

```text
锂电 → 创新药 → 存储半导体
```

第三个 benchmark 选择：**Memory Semiconductors / 存储半导体**，核心同时覆盖 **DRAM + NAND Flash**。

这不是写一份“AI/HBM 景气报告”或“SSD 报告”，而是重建一段可以 point-in-time 回放的存储产业历史，用它检验 Longcycle 能否在同一批公司、两条高度相关但不可混算的产品线中真实保存：

- Reality：价格、库存、wafer/bit supply、产能、工艺/层数、产品、资本开支、客户认证与实际出货；
- Judgment：管理层、客户、行业机构和研究者当时对供需、价格、库存、技术迁移、HBM、SSD/NAND、资本开支的判断；
- Outcome：后来实际供需、价格、产品 ramp、份额/利润与当时 Judgment 如何分叉。

第一阶段历史恢复范围：

```text
2016-01-01 → 2026-08-24
```

2016 作为上一轮大周期前的基线；2017–2018 覆盖强景气与供给紧张；2019 覆盖下行；2020–2021 覆盖疫情需求迁移与供应约束；2022–2023 覆盖库存/价格深度调整；2024–2026-08-24 覆盖 AI/HBM、enterprise SSD、产品结构和资本配置变化。

`2026-08-24` 之后只能进入 current source watch；未来材料不得提前进入历史 campaign。

不预先把 DRAM 与 NAND 定义成“完全同步的一个周期”。本 benchmark 把“二者高度相关、公司资本配置与库存周期相互影响”作为需要历史验证的机制假设：用同一时间轴和共享公司视角观察 lead/lag、分叉与重新收敛。

## 2. 行业边界

### 2.1 Core A：DRAM

纳入：

- commodity/server DRAM：DDR4、DDR5 及代际迁移；
- mobile DRAM：LPDDR4X、LPDDR5/5X 及代际迁移；
- graphics / high-performance DRAM：GDDR 在影响产品 mix 时进入；
- HBM：HBM2/2E、HBM3/3E、HBM4 等，作为 DRAM 产品/工艺/封装/产能配置分支；
- DRAM wafer capacity、wafer starts、node mix、bit output、yield/ramp、sellable product supply；
- 与 DRAM 直接相关的先进封装、TSV、base die、stacking/qualification bottleneck。

### 2.2 Core B：NAND Flash

纳入：

- raw NAND / NAND wafer 与 3D NAND generations；
- TLC / QLC 等 bits-per-cell 迁移及其成本、性能、yield、产品适配影响；
- client SSD、enterprise SSD、mobile storage（UFS/eMMC）在需求/产品 mix/认证上形成可见变量时进入；
- NAND wafer capacity、wafer starts、layer/stack architecture、bit output、yield/ramp、sellable die/product supply；
- controller、firmware、package/SSD qualification 只在成为有效供给或客户采用瓶颈时进入；
- production cuts、utilization、inventory、capex、fab/cleanroom 与 equipment decisions。

### 2.3 Shared-company / shared-cycle frame

DRAM 与 NAND 共同放进同一个研究 frame，因为：

- Samsung、SK hynix、Micron 等大厂同时经营两条存储产品线，company-level memory capex、库存、利润和供给纪律经常需要拆分后理解；
- cleanroom、设备投资、资本预算、供应商行为和下游终端周期存在共同驱动；
- 但产品价格、技术路径、客户认证、有效供给与需求结构不同，不能把“Memory”聚合指标直接当成任一子行业 Reality。

共享公司不等于完全相同 actor 集。NAND-only / DRAM-only 参与者必须保留自己的产品线身份，不能为了“公司差不多”而抹平。

### 2.4 Downstream boundary

只保存直接影响存储需求、产品 mix 或认证的部分：

- server / cloud / AI accelerator；
- PC；
- smartphone；
- graphics；
- enterprise/client storage；
- automotive / industrial 在成为可见需求变量时进入。

不把服务器、GPU、手机、SSD controller 各自扩成完整行业。

## 3. 第一批 actor

共享核心供给方：

- Samsung Electronics；
- SK hynix（NAND 侧包括其 NAND/SSD 资产与相关主体）；
- Micron Technology。

DRAM 关键边界/反例：

- CXMT / 长鑫存储；
- Nanya Technology；
- Winbond 等 specialty DRAM 厂在能形成有用反例时进入。

NAND 关键边界/反例：

- Kioxia；
- Western Digital / SanDisk 相关 NAND/flash 业务；
- YMTC / 长江存储；
- 其他独立或历史 NAND actor 在周期、技术或退出/整合史中形成有效反例时进入。

下游 actor 不预设“重要性排名”。只有 source-grounded 资料表明某客户、平台或认证事件改变具体 DRAM/NAND 需求或产品 ramp 时才建立关系。

## 4. 第一轮真正要保存的问题

### A. 价格与定价口径

DRAM：

- contract vs spot；
- DDR4 / DDR5；
- server / PC / mobile；
- HBM 与 conventional DRAM 价值量不可直接拼接。

NAND：

- NAND wafer / die、contract / spot、不同 density / generation；
- client SSD、enterprise SSD、mobile storage 等成品价格与 raw NAND price 不可混算；
- TLC / QLC、capacity point、interface、form factor、region、currency、frequency 和 source methodology 要明确。

核心原则：**同名“memory price”没有天然可比性；DRAM 与 NAND 更不能直接拼成一条价格序列。**

### B. Supply：从 fab 到 sellable bit/product

共同拆分：

```text
fab / cleanroom capacity
→ wafer capacity / wafer starts
→ technology mix
→ die / bit output
→ yield / qualification
→ package / module / SSD / stack output
→ sellable product supply
```

DRAM 特别区分 node、HBM stack 与 conventional die；NAND 特别区分 layer/stack architecture、bits-per-cell、raw NAND 与 SSD 成品。不得把“新增 fab”“wafer capacity”“bit growth”“HBM stack output”“SSD shipment”当成同一种产能。

### C. 库存

尽量拆：

- supplier inventory；
- channel / module inventory；
- customer inventory；
- NAND controller/SSD 成品与 raw NAND 库存差异；
- days of inventory / absolute value / write-down / management commentary；
- inventory correction 的开始、持续、结束 Judgment。

company-level financial inventory 不能直接当行业 bit inventory，也不能自动拆成 DRAM/NAND。

### D. Demand

按 application 保存当时可得口径：

- server/cloud：DRAM memory content、HBM 与 enterprise SSD/NAND demand 分开；
- PC：DRAM content 与 client SSD capacity/content 分开；
- smartphone：LPDDR 与 NAND/UFS content 分开；
- AI accelerator：HBM demand 与训练/推理基础设施带来的 SSD/NAND demand 分开；
- graphics / automotive / industrial 等边界需求。

把“device units growth”“memory content growth”“DRAM bit demand”“NAND bit demand”分开。

### E. Technology migration

DRAM 保存：

- 各厂 DRAM node 名称、量产/ramp、cost per bit、yield、EUV Judgment；
- 厂商 `1a/1b/1c/1α/1β/1γ` 等命名不假设横向等价。

NAND 保存：

- layer count、string/stack/deck architecture、TLC/QLC 迁移、量产/ramp、yield 与 cost per bit；
- 不同厂“xxx-layer”或 generation label 不能假设等价；
- layer 数增加不自动等于有效 bit supply 同比例增加。

### F. Capex / fab / equipment

保存：

- company memory capex 与可拆分的 DRAM/NAND capex；
- fab/cleanroom 建设、扩建、equipment move-in；
- wafer-capacity 增减；
- production cuts / utilization changes；
- technology migration 设备需求；
- 从宣布到真正贡献 sellable bit 的时间差；
- 同一公司在 DRAM/NAND/HBM/SSD 之间的资本与产能优先级 Judgment。

资本开支金额、WFE 支出、fab 建筑投资和产能贡献必须分开。

### G. HBM 与 NAND/SSD 结构变量

HBM 是 DRAM 侧关键结构变量：generation、stack、qualification、TSV/base die、advanced packaging、wafer trade-off、conventional DRAM supply/mix 影响。

NAND 侧重点：enterprise SSD、client SSD、mobile storage、TLC/QLC mix、controller/firmware/qualification、raw NAND → finished SSD 的价值链与有效供给转换。

两边都必须区分：sample / qualification / mass production / mass shipment / revenue contribution / mature yield。

### H. Supplier behavior and cross-product discipline

跟踪：

- production cuts；
- capex cut / increase；
- inventory write-down；
- technology migration acceleration/delay；
- product mix changes；
- long-term agreements / capacity reservation；
- fab acquisition / greenfield / JV decisions；
- shared company 在 DRAM/NAND 之间的预算、utilization、设备和 cleanroom 分配。

### I. 政策与供应链约束

只在影响存储 Reality/Judgment 时进入：

- export controls；
- semiconductor industrial policy；
- equipment/material restrictions；
- regional fab incentives；
- trade restrictions / customer access changes。

政策原文和监管文件优先于新闻转述。

### J. 当时 Judgment 与 revision chain

重点寻找：

- DRAM 与 NAND 各自“下一季/下一年价格何时触底或上涨”；
- bit demand / bit supply growth forecast；
- inventory normalization timing；
- capex discipline / supply discipline；
- node/layer transition cost-down；
- HBM TAM / qualification / share；
- enterprise SSD / client SSD / mobile storage demand Judgment；
- 中国 DRAM/NAND 新增供给影响；
- “DRAM/NAND 是否同周期、谁领先谁滞后”的当时观点；
- bull/base/bear 情景和明确 caveat。

同一主体同一问题优先做 revision chain，而不是只保存最后一次预测。

### K. Outcome

Outcome 不用后来结果重写 Judgment。保存：

- forecasted DRAM/NAND price direction vs later comparable series；
- forecasted inventory normalization vs later company/customer disclosures；
- planned node/layer/HBM/SSD ramp vs actual shipment/production milestones；
- planned supply/capex vs later bit-output and financial outcomes；
- forecasted application demand vs later DRAM/NAND demand observations；
- “共同周期/lead-lag” Judgment vs 后续两条产品线实际分叉。

## 5. 历史 snapshot

第一轮使用同一半年快照，重大转折再增加季度点：

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
2026-08-24
```

每个 snapshot 尽量回答同一组问题：

1. 当时可见的 DRAM 与 NAND 价格分别是什么、口径是什么、方向是否一致？
2. 两条产品线的 supplier/customer/channel inventory 分别知道多少？
3. 当时预计未来 12–24 个月 DRAM bit demand/supply 与 NAND bit demand/supply 如何变化？
4. 同一公司当时在做什么 capex、cut、utilization、technology transition 和 product-mix 调整？
5. server / PC / mobile / AI / enterprise SSD 等需求各自被如何判断？
6. HBM 与 SSD/NAND 结构变量当时已经知道多少，而不是后来知道多少？
7. DRAM/NAND 当时是同步、lead-lag 还是明显分叉？支持这个判断的口径是什么？
8. 哪些判断有明确反方/caveat，哪些问题仍未知？

## 6. 第一轮 source map

### 6.1 公司 primary sources

优先：

- Samsung Electronics IR、regulatory disclosures、earnings releases、Memory Business product/technology announcements；
- SK hynix IR / newsroom / annual and quarterly disclosures，以及与 NAND/SSD 业务直接相关的正式主体资料；
- Micron Investor Relations、10-K/10-Q、earnings prepared remarks；
- Kioxia、Western Digital/SanDisk 相关公开 IR/filings/technology announcements；
- CXMT、YMTC 官方产品、公司历史和正式发布；
- Nanya 等边界 actor 的 IR / annual reports。

公司资料同时可能承载 Reality 与 Judgment：已发生事实和 forward-looking guidance 必须分开标注。Company Memory segment 若同时包含 DRAM/NAND，不得自动拆分。

### 6.2 Standards / industry institutions

- JEDEC：DDR / LPDDR / HBM 等标准定义，用于 DRAM identity/technology boundary；
- NAND/SSD 接口、form factor、protocol 的标准或行业组织资料，仅用于产品 identity/compatibility；
- WSTS：Memory 宏观市场历史，用于大类背景和口径检查，不替代 DRAM/NAND 子行业拆分。

### 6.3 Pricing / market research

可发现并在权限允许时保存：

- TrendForce / DRAMeXchange 等历史 DRAM/NAND price 与供需资料；
- Omdia、TechInsights、Counterpoint 等历史市场研究；
- 其他明确说明 methodology 的 price / bit supply-demand 数据。

付费资料不得绕过权限。只保留可公开验证部分、locator、metadata 和人工补齐需求。不同机构序列不可未经校准直接拼接。

### 6.4 Policy / regulatory

- US BIS / Department of Commerce；
- Korea government / regulatory disclosures；
- China MIIT 及相关政策原文；
- Japan METI 等在设备/材料限制直接影响存储时进入。

### 6.5 Downstream primary sources

当需求问题需要时，优先使用：

- CPU/GPU/platform vendors；
- hyperscaler / server OEM；
- PC/smartphone OEM；
- storage/SSD customer 的正式披露；
- 只在能够建立 claim-scoped link 时使用。

不要因为 AI capex 很显眼就自动把全部云资本开支当成 HBM 或 NAND demand Reality。

## 7. Comparability hazards

本 benchmark 必须重点测试：

1. **price comparability**：DRAM/NAND 不同；spot/contract、density、generation、application、raw die/finished product 不同；
2. **capacity comparability**：fab area、wafer/month、wafer starts、bit output、HBM stack、SSD shipment 不同；
3. **technology comparability**：DRAM node label 与 NAND layer/generation label 各自都不可跨厂直接等价；
4. **inventory comparability**：financial inventory value、days、raw die、module/SSD、channel/customer inventory 不同；
5. **demand comparability**：device units、memory content、DRAM bit demand、NAND bit demand、revenue demand 不同；
6. **product mix**：HBM/enterprise SSD 等高价值产品改变 ASP/revenue，不等于总 bit demand 同比例变化；
7. **known-time**：qualification、yield、customer acceptance 后来才知道的信息不能回写早期 snapshot；
8. **company scope**：Memory segment 聚合不能未经拆分就当 DRAM 或 NAND 指标；
9. **cycle comparability**：共同宏观周期不等于每个转折点同步；必须允许 lead/lag、product-specific shortage/oversupply 与库存差异。

## 8. Memory-first / Evidence-final execution

历史恢复继续复用 CAP-0006：

```text
Stage A: sealed blind memory exhaustion
→ Stage B: high-capability self verification
→ Stage C: delegated claim-scoped Evidence search
→ Evidence / Reality / Judgment / Outcome
```

Stage A 不看本轮互联网搜索结果。当前 scope 初始化阶段看过的公开-source 观察不得作为 blind-recall 内容注入模型。

第一轮 blind pass 至少覆盖：

- shared time slices；
- DRAM / NAND product-track exhaustion；
- shared-company actor exhaustion；
- product-specific actor exhaustion；
- metric exhaustion；
- mechanism exhaustion；
- contemporaneous narratives；
- old vocabulary / lost web；
- failures / dead ends；
- reverse causality；
- cross-product / cross-industry effects；
- counterfactual explanations；
- negative space。

## 9. Stop rule

第三行业的第一里程碑不是“搜够多少网页”，而是：

- blind campaign 达到现有 saturation rule 并封存；
- 形成时间 × actor × product-line × metric coverage matrix；
- 识别 DRAM/NAND 共振、lead-lag、分叉、资本配置与库存传导的 Memory Leads；
- 识别高价值反例、失败史和 revision chains；
- 再进入 self-verification，不修改 blind atlas；
- 只有 Evidence-final 后才允许形成 publishable Reality/Judgment；
- 如果存储 benchmark 暴露现有产品/语义无法真实表达的关系，先形成具体 semantic-gap note，再决定是否动架构。

本 benchmark 的首要作用是**证明 Longcycle 能同时处理相关产品线的共性和不可混算差异，或准确暴露不能处理的地方**，不是追求资料数量。
