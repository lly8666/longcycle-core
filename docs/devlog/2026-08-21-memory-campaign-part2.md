# 2026-08-21 Memory Campaign 开发日志 Part 2

本日志继续记录可复核的工程决策、实验结果、Prompt 版本变化、Schema/数据问题和下一步动作。它不记录模型私有推理链。

## 07:25 - 第二轮策略：从 broad recall 转向 dimension-specific self-gap

第一轮主 shard + corrective pass 后，仍然持续出现大量此前未激活的高价值记忆。结论：

> 不能用“模型已经给了很多内容”判断记忆已经接近完整。

新增 Prompt v4：`research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/prompts/self-gap-v4.md`。

Self-gap 不再问“还有什么”，而是逐维检查：时间、actor、失败者、项目、指标、价格/合同、技术、预期、旧术语和跨边界 trigger。

每条新 lead 必须在 `recalled_details.gap_reason` 里说明为什么 earlier broad pass 容易漏掉它。

## 07:35 - LFP / NEV / ESS corrective pass

新增：

- MID-LFP corrective：14 leads
- DOWN-NEV corrective：14 leads
- DOWN-ESS corrective：14 leads

重要发现：

1. LFP 的历史不能只记材料吨产能；需要工艺路线、产品等级、客户绑定、前驱体/成品边界、动力/储能应用和技术预期修订。
2. NEV 总销量不能直接映射电池需求；需要 BEV/PHEV/REEV、车型级别、单车带电量、批发/零售/上险/出口和存量替换。
3. ESS 的 GW/GWh、AC/DC、时长、可用能量、并网状态、应用场景和收益模式必须分开。

## 07:45 - 结构错误再次出现：raw output 必须永远保留 + repair overlay

在 `DOWN-ESS/expectations-failures-metrics-v3.jsonl` 中，`ESS-C006.lead_kind` 输出了非法枚举 `capacity_cycle`，正确语义应为 `capital_cycle`。

按现有原则：

- 不改写 raw output；
- 新增 `expectations-failures-metrics-v3.repair.json`；
- ingestion 先应用 structural repair overlay，再做 typed validation；
- repair 禁止新增历史内容。

这再次证明模型 JSON 不能直接写入数据库。

## 07:55 - Self-gap v4 第一批实验

结果：

- MID-LFP batch1：10/10 useful/new
- DOWN-NEV batch1：8/8 useful/new
- DOWN-ESS batch1：8/8 useful/new
- BAT-CELL batch1：10/10 useful/new
- UP-CONCENTRATE batch1：10/10 useful/new
- MID-TERNARY batch1：10/10 useful/new
- MID-ANODE batch1：8/8 useful/new
- MID-SEPARATOR batch1：8/8 useful/new
- MID-ELECTROLYTE batch1：8/8 useful/new
- LOOP-RECYCLING batch1：8/8 useful/new
- DOWN-OTHER batch1：8/8 useful/new

结论：第一批 self-gap 仍然几乎没有出现明显边际衰减。

这意味着模型长尾知识不是“补几个遗漏”，而是不同提示角度会激活大量原本沉默的关联。

## 08:20 - Self-gap batch2 饱和度试验

为避免第一批高新增只是 Prompt 新鲜效应，对高价值 shard 继续 batch2，并明确禁止重复 batch1 已覆盖类别。

结果：

- MID-LFP batch2：6/6 new/useful
- DOWN-NEV batch2：6/6 new/useful
- DOWN-ESS batch2：6/6 new/useful

LFP batch2 仍新增：

- carbonate vs hydroxide product-demand mapping；
- FePO4 precursor / LFP capacity double-counting risk；
- overseas LFP patent/licensing archaeology；
- phosphorus-chemical byproduct economics；
- time-varying low-temperature/fast-charge performance frontier；
- competing explanations for LFP revival。

NEV batch2 仍新增：

- insurance / residual value / repair cost；
- fleet addition vs replacement sales；
- county/rural adoption path；
- battery asset ownership / BaaS；
- battery lifetime changes affecting future replacement/recycling；
- model-generation inventory clearance。

ESS batch2 仍新增：

- lifecycle augmentation demand；
- physical cell oversizing vs contractual usable MWh；
- PCS / transformer / grid interconnection bottlenecks；
- 2h -> 4h duration-mix expectation；
- project finance / bankability；
- liquid-cooling architecture transition。

结论：这些 shard 仍远未达到 saturation。

## 08:35 - 上游 self-gap 补齐

补跑：

- UP-HARDROCK batch1：8 leads
- UP-BRINE batch1：8 leads
- UP-CHEMICALS batch1：8 leads

新增可复用语义包括：

### Hard-rock

- ore grade / recovery / strip ratio / mine phase；
- capex revision；
- equity vs operator vs offtake role；
- first ore / first concentrate / first shipment / commercial production；
- infrastructure readiness；
- project-risk assumptions inside historical supply forecasts；
- mine stockpile vs shipments；
- PFS / DFS / permit / FID / construction maturity states。

### Brine

- resource LCE vs pumping/recoverable brine；
- water rights / community / social license；
- DLE process-route taxonomy；
- pond infrastructure as capacity inertia；
- price-linked royalty / government take；
- pilot/demo/commercial scale states；
- finished inventory vs pond WIP；
- Argentina macro/FX/import constraints。

### Lithium chemicals

- industrial-grade vs battery-grade product semantics；
- first production vs battery-grade qualification；
- spot / contract / futures / warehouse receipt markets；
- feedstock-specific unit consumption/recovery；
- lepidolite waste-disposal capacity；
- captive/offtake/external feedstock mix；
- competing long-run lithium-price theses；
- overseas converter geographic ramp risk。

## 08:45 - Campaign checkpoint

Blind lead total: **534**.

14 个主 shard 全部至少完成第一轮 broad recall；绝大多数已完成 corrective 或 self-gap；所有数据仍为 `source_visibility=none`，没有开始 fresh web self-verification。

当前最强跨链结构性发现：

```text
capacity != one number
price != one curve
inventory != one stock
sales != demand
project announced != supply
technology announced != adoption
source found != truth
```

## 08:50 - CI 状态

GitHub Actions `ci` workflow run #94 已正常触发，目前在执行 test job。

这是此前一直缺失的机器反馈。后续所有 Schema / domain / dataset changes 都应通过：

- install
- Ruff
- Mypy
- Pytest

Memory JSONL raw artifacts仍允许保留历史实验错误；只有 ingestion candidate/repaired datasets 需要 typed validation。

## 下一步

1. 等 CI #94 完成并修复真实失败；
2. 对高新增 shard 继续 batch2/batch3，测 novelty decay；
3. 给每个 shard 建 compact lead index，避免 saturation pass 重新加载完整 raw text；
4. 只有连续三批 low-novelty + gap matrix 无明显空白才 seal；
5. sealed shard 才进入 high-model self-verification；
6. self-verification 结果再生成低成本 Agent 的 claim-specific evidence task packet。
