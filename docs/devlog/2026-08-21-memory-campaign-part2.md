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

## 09:15 - batch2 继续：总量推进到 552

继续对三个不同性质的高价值 shard 做第二批 novelty-decay 测试：

- BAT-CELL batch2：6/6 new/useful；
- UP-CONCENTRATE batch2：6/6 new/useful；
- MID-TERNARY batch2：6/6 new/useful。

因此 blind raw lead 总量从 534 增加到 **552**。

新增维度仍然不是同义复述：

- BAT-CELL：多级库存、OEM 自供/JV、干电极、ASP product mix、送样→定点→SOP、营运资金；
- UP-CONCENTRATE：杂质规格、floor/cap 长协、天气/港口发运、低品位产品 mix、副产品信用、贸易商货权；
- MID-TERNARY：前驱体/正极双计、高电压中镍、LME 镍与硫酸镍基差、共沉淀工艺、环保约束、客户资格认证。

结论仍然是：没有出现可支持 seal 的 novelty decay。

## 09:25 - Compact Memory Index

新增 `src/longcycle/application/memory_index.py` 和对应测试。

原则：后续 saturation/self-gap pass 不再反复加载数百条完整 raw JSONL，而是读取确定性 compact index，只保留可审计目录字段和 coverage counters。

压缩过程不使用另一个模型进行摘要，避免“为了节省上下文又引入一次模型失真”。

## 09:30 - CI #116 暴露真实契约问题

此前聊天中的旧状态曾把 Mypy/Pytest 描述成通过；新的完整诊断 run #116 证明这一状态已经过期：

- Mypy：26 errors / 10 files；
- Pytest：114 passed / 3 failed；
- Ruff：72 findings。

三个 Pytest failure 分别是：

1. structural repair overlay 已存在但 dataset validation 没真正应用；
2. same-shard satellite 的 candidate 语义和 promotion 实现不一致；
3. Research Agent SOP 没有显式写出 `not_found != false`。

这成为 Session Handoff 设计的直接证据：**新会话不能相信旧聊天总结，必须刷新 live HEAD 和 CI。**

## 09:35 - CI correctness repair

已提交的修复包括：

- repair overlay 真正接入 typed candidate validation，同时 raw JSONL 保持不可改写；
- repeated same-shard satellite 可成为 research candidate，但不会因缺乏独立 shard 自动 promote；
- SOP 明文写入 `not_found != false`；
- 修复 Pydantic datetime validator、value fingerprint 等 strict typing；
- ModelGateway `model_name` 类型显式化；
- SourcePlugin async-generator protocol 修正；
- workflow checkpoint 类型从 Any 收紧；
- S3 body 返回值显式验证为 bytes；
- pipeline `_validate_envelope` 使用明确 `ExtractionEnvelope`；
- CI 安装 `dev,postgres,s3` 全部 optional adapters。

Ruff 暂时维持 diagnostic-only；Mypy/Pytest 是硬 correctness gate。

## 09:42 - Session Handoff v1

用户提出新的持续执行要求：

> “聊天轮次多了以后就会被切断当前聊天对话框，必须开新的，设计套系统如何让新开聊天系统能实时跟上开发进度，保证原汁原味执行我们的计划和任务”

因此新增 repository-backed 四层 continuity：

1. `docs/development/project-constitution.md` — 慢变化的项目北极星、用户原话和不可违背规则；
2. `.longcycle/handoff/current.json` — 快变化、机器可读的实时 checkpoint；
3. `docs/devlog/` — 追加式决策/实验历史；
4. `CONTINUE_HERE.md` + `AGENTS.md` — 新聊天/新 agent 的稳定启动入口。

同时新增：

- `docs/development/session-handoff-protocol.md`；
- `src/longcycle/application/session_handoff.py` typed contract；
- `tests/test_session_handoff.py`，让 handoff 本身成为 CI 契约。

关键设计：checkpoint 只记录 `checkpoint_based_on_head_sha`，不能假装包含自身 commit SHA。新会话必须：

```text
read checkpoint
→ fetch live HEAD
→ reconcile delta
→ fetch live CI
→ correct stale snapshot
→ continue ordered next actions
```

CI 状态在 checkpoint 中永远标为 `snapshot_not_authoritative`。

## 09:45 - Coverage checkpoint refresh

`coverage-index.json` 已从过期的 534 更新到 **552**，并显式记录：

- 14 个主 shard；
- 0 sealed；
- `search_visibility = none`；
- BAT-CELL / UP-CONCENTRATE / MID-TERNARY 已进入 self-gap batch2；
- 六个已测试 batch2 shard 仍为 6/6 new/useful；
- fresh web self-verification 继续禁止，直到对应 shard seal。

## 当前下一步

1. 获取 Session Handoff 首个 checkpoint head 后的最新 CI，确认 residual Mypy/Pytest；
2. 修完真正剩余 correctness failures，不能用旧 #116 推测；
3. CI 通过后更新 `.longcycle/handoff/current.json` 的 CI snapshot；
4. 用 compact index 继续剩余 shard 的 batch2 / 高新增 shard 的 batch3；
5. 只有连续三批 low-novelty + negative-space gap matrix 完整，才允许 seal；
6. seal 后才进入 high-model fresh-web self-verification 和低成本 Agent evidence task。
