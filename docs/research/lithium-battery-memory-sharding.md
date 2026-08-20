# 锂电池 Memory Campaign 分片与拼接设计

## 1. 目标

锂电产业链节点多、历史跨度长、跨链耦合强。Memory Exhaustion 不能依赖一个超长 prompt 或一次聊天完成。

核心设计：

> **局部 recall 要独立，跨链关系要后置；任何一步都能 checkpoint。**

## 2. 三类任务

### A. Atomic Shard Recall

每个细分节点独立运行 blind recall。输入只包含：

- 固定行业 ontology；
- 当前 shard 定义；
- 时间范围；
- prompt protocol；
- 不包含其他 shard 的实际输出。

目的是最大化该节点自身的长尾记忆召回，避免被邻近节点著名事件锚定。

### B. Bridge Theme Recall

跨节点但围绕一个机制独立运行：

- 价格形成/长协/拍卖/加工费；
- 库存位置与去补库；
- 项目公告→融资→设备→建设→投产→爬坡；
- 资本开支与融资；
- 技术路线与单位材料耗用；
- 贸易/出口/海外政策；
- 能源/化工/物流约束；
- 当时市场叙事。

Bridge pass 同样先做 blind recall，不读取 atomic shard 结果。

### C. Stitch / Gap Pass

只有 Atomic Shard 和 Bridge Theme 均封存后才执行。

输入不是所有原始输出，而是压缩 lead index：

```text
lead_id
shard_id
period
actor/entity hints
lead_kind
topic
one-line summary
confidence
importance
```

Stitch pass 只负责：

- 找跨节点 predecessor/successor；
- 找 possible_cause/possible_effect；
- 找同一 episode 的不同侧面；
- 找明显缺失的中间节点；
- 生成新的 cross_chain_link / negative_space lead。

它不能修改已封存的 blind lead。

## 3. 第一版 Tier A shards

| shard_id | 范围 | 与其他节点的主要桥 |
| --- | --- | --- |
| UP-HARDROCK | 硬岩锂矿、锂辉石、矿山建设/复产/停产 | 精矿价格、包销、转换成本 |
| UP-BRINE | 盐湖/卤水、提锂工艺、天气/资源禀赋/建设 | 锂盐供给、成本、项目周期 |
| UP-CONCENTRATE | 锂精矿贸易、拍卖、长协、定价 | 锂盐成本、矿端利润 |
| UP-CHEMICALS | 碳酸锂/氢氧化锂转换、产能、库存、成本 | 正极成本、现货价格 |
| MID-LFP | 磷酸铁/磷酸铁锂 | LFP电芯、锂盐、磷化工 |
| MID-TERNARY | 前驱体/NCM/NCA | 镍钴锰、氢氧化锂、电池体系 |
| MID-ANODE | 天然/人造石墨、硅基 | 针状焦/石油焦、电池快充 |
| MID-SEPARATOR | 湿法/干法隔膜、涂覆 | 电池扩产、设备、良率 |
| MID-ELECTROLYTE | 电解液/LiPF6/添加剂 | 锂盐、氟化工、电芯 |
| BAT-CELL | 电芯制造、Pack、产能、良率、客户认证 | 各材料、车企/储能客户 |
| DOWN-NEV | 新能源汽车终端、车型结构、渗透率 | 动力电池、材料需求 |
| DOWN-ESS | 储能、电网/独立储能、海外储能 | 储能电芯、LFP需求 |
| DOWN-OTHER | 消费、两轮车、工具等 | 电芯需求结构 |
| LOOP-RECYCLING | 回收、黑粉、梯次利用、再生锂镍钴 | 原生资源需求、材料供给 |

## 4. Tier B satellite promotion

卫星节点默认不独立消耗完整 recall budget。以下情况触发升级：

1. 至少 3 个独立高重要度 Memory Lead 指向该节点；
2. 它在某阶段成为明确供给瓶颈；
3. 它具有独立价格/利润/产能周期；
4. 对主链成本或技术路线产生显著冲击；
5. 多个相邻 shard 的 negative-space 都指向它。

候选包括铜箔/铝箔、PVDF、NMP、导电剂、电池设备、BMS/热管理、磷酸/铁源等。

## 5. 每个 Atomic Shard 的内部 pass

每个 shard 不一次性输出全部内容，而按固定 pass：

1. `timeline`：按年度/周期阶段；
2. `actors-projects`：公司、项目、失败者、旧称；
3. `metrics`：价格/产量/库存/产能/利润等；
4. `mechanisms`：定价、成本、瓶颈、资格认证、物流；
5. `expectations`：当时预期与叙事；
6. `failures`：延期、取消、减值、低利用率、错误叙事；
7. `terminology`：旧称、英文名、历史搜索键；
8. `self-gap`：只读取本 shard 的 lead index，找缺口；
9. `saturation`：评估新增 lead 是否趋近饱和。

每个 pass 完成后立即保存。

## 6. Lead 原子性

一个 lead 原则上只表达一个最小可验证命题或一个最小搜索方向。

不推荐：

> 2021-2022 澳洲锂矿拍卖推高精矿价格，挤压中国锂盐利润，导致企业锁矿并最终刺激非洲扩产。

应该拆成至少四个 lead：

- 某时期澳洲精矿拍卖/定价机制成为价格发现信号；
- 精矿涨价可能压缩无资源锂盐厂利润；
- 中国锂盐/电池企业增加包销、预付款或资源投资；
- 高价和融资可能加速非洲等新资源项目。

这样每个 lead 可独立支持、反驳或保持 unresolved。

## 7. 防止跨 shard 污染

### Blind 阶段允许共享

- 固定 ontology；
- 固定时间轴；
- 已知的 shard 名称和边界；
- prompt protocol。

### Blind 阶段禁止共享

- 其他 shard 实际 Memory Leads；
- 本轮互联网搜索结果；
- 后验验证结论；
- 为了“补齐故事”而生成的 stitch 关系。

## 8. 跨链拼接不要求事实一致

Stitch 发现的是候选关系，不是真值。例如：

```text
UP-HARDROCK lead: 精矿价格快速上行
UP-CHEMICALS lead: 转换利润被压缩
MID-LFP lead: 正极厂高价采购后库存风险上升
```

Stitch 可以生成：

> 可能存在“矿端议价权上移 → 锂盐加工利润下降 → 下游高价库存”的同一周期 episode。

但关系仍需分别找当时资料。

## 9. 上下文与执行时限设计

不依赖产品的具体会话时限。每个工作单元都必须满足：

- 独立输入可重建；
- 输出有限；
- prompt/version 固定；
- 每 pass 可单独 commit；
- checkpoint 指向下一个 pass；
- stitch 使用压缩 index 而不是重新载入全部原文。

因此无论一次运行只能处理一个 pass，还是可以处理多个 pass，研究结果都不会因会话结束而丢失。

## 10. 第一轮实验

先运行两个相邻、但不互相读取输出的 shard：

- `UP-HARDROCK`
- `UP-CHEMICALS`

目标不是马上证明历史，而是验证 prompt 是否能稳定产出：

- 长尾 actor/project；
- 可搜索旧称和 source hook；
- 机制型 lead；
- contemporaneous expectation；
- failure/dead-end；
- 明确不确定性；
- 足够原子的可验证命题。

根据实际输出升级 prompt 和 Memory Lead Schema，再扩大到其余 shard。