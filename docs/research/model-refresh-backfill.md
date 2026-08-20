# 模型更新后的历史回补机制

## 1. 为什么需要专门设计

高级模型的知识不是静态资产。未来模型可能：

- 训练资料更新；
- 知识时间截点前移；
- 对旧行业资料记忆更完整；
- 对某些冷门公司/项目/术语新增记忆；
- 推理和联想能力提升；
- 也可能在某些旧知识上退化。

Longcycle 不能把“换了更强模型”理解成覆盖旧结果。

正确做法是把每个模型版本视为一个新的 **research instrument vintage**。

## 2. 模型版本也是 point-in-time artifact

每次 Memory Exhaustion Campaign 必须记录：

```text
provider
model_name
model_version / snapshot（若可得）
declared_knowledge_cutoff（若可得）
protocol_version
prompt manifest version
industry scope
period scope
created_at
```

旧模型输出 append-only 保存。

新模型重新跑同一行业时，不能删除旧 lead。

## 3. Refresh 的正确流程

```text
Old Model Memory Atlas
        ↓
New Model Memory Exhaustion Campaign
        ↓
semantic / entity / period dedup
        ↓
Lead Diff
   ┌────┼────┐
   │    │    │
known  refined  novel
            │
            ↓
       Archive Gap Diff
            ↓
      Backfill Task Queue
```

### 3.1 known

新模型只是再次想起数据库已经有充分原始证据覆盖的历史。

不重复派搜索任务，只记录新模型也召回了该 lead。

### 3.2 refined

新模型给出了新的：

- 旧称；
- actor；
- 时间范围；
- 机制细节；
- 项目名称；
- 搜索关键词；
- 可能 primary source。

即使旧 lead 已存在，这些新增信息也可能显著提高历史检索成功率，因此生成 `lead_refinement`。

### 3.3 novel

以前模型和 archive 都未覆盖的重要 lead。

进入 backfill priority queue。

## 4. 不以模型升级日期作为历史发生日期

例如 2028 年的新模型第一次让我们想起一个 2021 年项目。

必须保存：

```text
historical_period = 2021
model_recalled_at = 2028
```

找到 2021 年原始资料以后，Fact/Judgment 的 `known_at` 仍按历史资料本身的 point-in-time 语义处理；不能因为 2028 才被 Longcycle 找到，就污染 2021 历史世界。

## 5. Knowledge Cutoff 与 Search Cutoff 分开

高级模型可能声明一个训练/知识 cutoff，也可能无法可靠提供。

系统分别记录：

- `declared_knowledge_cutoff`：模型/供应商声明的知识截点；
- `campaign_created_at`：我们实际运行时间；
- `archive_knowledge_cutoff`：gap audit 允许看到的 Longcycle 档案截点；
- `search_started_at`：验证阶段开始时间。

模型声明 cutoff 不作为事实来源，只用于解释为什么不同 vintage 召回内容不同。

## 6. 固定 Benchmark Manifest

每个行业保留一套长期不轻易改变的 memory recall benchmark。

锂电例如固定包含：

- 2019–2020；
- 2021–2022；
- 2023–2024；
- 2025–2026；
- 全周期；
- 价格机制；
- 失败项目；
- 库存；
- 资本周期；
- 技术路线；
- 当时叙事；
- forgotten actors；
- old vocabulary。

每次新模型至少重复这套 benchmark，才能比较不同模型版本。

新的 protocol 可以增加 pass，但不能悄悄改变旧 benchmark 后声称新模型“记得更多”。

## 7. 模型之间也可以互相发现盲点

对于高价值行业，允许多个高级模型独立运行 blind campaign。

输出做：

```text
intersection
model-A-only
model-B-only
archive-covered
archive-missing
```

`model-A-only` 不代表正确，但非常适合成为高优先级搜索 lead。

模型共识同样不是真值。

## 8. Model Recall Quality 的长期评价

当越来越多 lead 被原始资料验证后，可以统计每个 model vintage：

- high-importance lead precision；
- novel verified leads；
- false-memory rate；
- primary-source search yield；
- terminology lead yield；
- mechanism lead yield；
- forgotten-actor yield；
- duplicate rate；
- archive coverage uplift。

这些指标不是评价模型回答“聪不聪明”，而是评价它作为**产业历史目录生成器**是否有价值。

## 9. 回补优先级

新模型产生的 novel lead 不是全部立刻搜索。

优先级建议：

```text
historical_importance
× archive_gap
× expected_search_value
× source_decay_risk
× point_in_time_value
```

其中 `source_decay_risk` 很重要：

- 公司旧 IR 页面；
- 地方政府附件；
- 会议纪要；
- 旧项目网页；
- 媒体原始采访；

这些更应该优先抢救。

## 10. 当前资料与模型更新的关系

模型更新主要用来**补历史缺口**，不应替代当前采集。

对于今天的新资料：

> 能今天归档，就不要寄希望于未来更强模型“记得”。

Current Collection 是主动保存；Model Refresh Backfill 是历史补洞。

两者长期共同作用：

```text
Today: source-first continuous archive
Past: model-memory-first historical recovery
Future model update: reopen past gaps
```

## 11. 最终原则

> **模型知识升级不是数据库升级，而是一次新的历史侦察机会。**

数据库的可信历史仍然只能由可追溯 Evidence 建立。