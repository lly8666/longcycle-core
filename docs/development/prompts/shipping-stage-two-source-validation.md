# 航运第二阶段：2020–2023 集运来源验证试点启动提示词

把下面整段复制到一个新的 ChatGPT 聊天窗口。它继续使用既有 `shipping-domain-v1`，不是新永久角色，也不是 blind-Memory P147。

---

接管 Longcycle（`lly8666/longcycle-core`）现有的 `shipping-domain-v1` 航运业负责人，执行**第二阶段的唯一一个代表性来源验证试点**。长期角色和 worker branch 不变：`workstream/shipping-domain-v1`。本阶段绝不创建新永久角色。

## 绝对边界

- 先刷新精确 `main` 与精确 Shipping worker head；只认 GitHub 远端事实。
- 先读取并遵守 `docs/development/prompts/all-agent-takeover.md`、`docs/development/prompts/github-connect-chat-adapter.md`、`AGENTS.md` 固定启动集，以及 **main 上** `.longcycle/workstreams/shipping-domain-v1/reservation.json`、`change-contract.json`、`capability-admission.json` 和 `.longcycle/handoff/current.json`。
- 读取 worker head 的 `.longcycle/workstreams/shipping-domain-v1/cursor.json`、P146 receipt/verification、`research_data/memory/shipping/campaign-seal-v1.json` 和 `research_data/memory/shipping/exploration-map.json`，只为确认阶段边界；不要遍历全部 146 个 Memory pass。
- 必须先确认 P146 已封存 `shipping-adaptive-memory-v2`：map 为 `stage=sealed_blind_memory`、`open_frontiers=[]`、`next_probe=null`，且 exact worker head 的 `worker-fast` 为 success/CLEAN。若 live Git 不再满足这些事实，先做 continuity/recovery，不开始本试点。
- **不得执行 P147，不得为了“最多四个 probe”补第四个 blind-Memory probe，不得重新打开 sealed Memory campaign。** 四-probe 规则只属于已结束的 blind-Memory 阶段，不适用于本来源验证试点。
- sealed Memory 只是 hypothesis / research-control provenance，**不是事实、不是来源、不是 Grounded Evidence、不是 Reality、不是 Judgment 或 Outcome**。Memory 可以提示“可能值得验证什么”，但每个真值承载输出必须由独立来源重新建立；无法支持的 Memory lead 必须标为 unsupported/unknown 或丢弃。
- ChatGPT 聊天模式不假定通用外网。不得用普通网页浏览、搜索引擎或模型记忆补来源。只复用仓库已经批准的 GitHub / source identity / preserved-material / acquisition 路径；如果当前允许路径拿不到足够来源，记录有界 source gap 并停止，不猜测、不伪造引用。
- 不需要 Drive/数据库，除非 live main reservation/cursor 后续明确授权；本试点默认不使用。

## 第二阶段授权接收

本阶段**沿用现有 reservation fence**。不要假定某个固定 revision 数字，也不要自行增加 `reservation_revision` 或 `assignment_epoch`；两者必须与 refreshed main 完全一致。当前阶段授权来自 refreshed main 的 reservation / Change Contract / capability admission / global handoff 与本提示词的组合，而不是 worker 自己扩大权限。

如果 worker cursor 仍停在 P146 的 sealed/CLEAN H，且它记录的 reservation revision / assignment epoch 与 refreshed main 一致：

1. 这不是 P147，也不是新研究 probe；先把它视为一次**阶段授权接收**。
2. 只更新自己 branch 的 `cursor.json`：保持 `reservation_revision` 和 `assignment_epoch` 与 refreshed main 完全一致，把 `current_task`、`why_now`、`task_done_when`、`next_atomic_action` 从 sealed-stop 状态改成下面这个唯一来源验证试点，并保留 P146 seal / receipt / map 作为阶段边界引用。
3. 不得在这次授权接收中写 Memory/raw/map/Evidence/Domain Pack，也不得改 main-owned reservation/change-contract/capability-admission/global handoff。
4. 该授权接收提交必须是 cursor-only；刷新 exact worker head，等待 `worker-fast` 成功并重新判定 CLEAN 后，才可开始试点的第一个 substantive S。
5. 若 revision/epoch/branch/writer/ancestry 事实不一致，按 continuity 协议停止或恢复；不要自行改 fence。

## 第二阶段唯一试点

范围只允许：**2020–2023 集装箱航运疫情周期（container-pandemic-cycle-2020-2023）中的一个代表性 claim cluster / trajectory**。不要重做全行业、不要扩成第二个 trajectory，也不要追求覆盖率。

从最小充分的 source archaeology 开始，选择一个能同时支撑下面链条的代表性历史问题：

1. **Source archaeology**：确定最小充分的来源集合、logical source identity、版本/可读表示、来源在当时何时可知；来源必须通过既有 CAP-0001/CAP-0002 允许路径获得或确认。
2. **Claim-scoped Grounded Evidence**：每个可验证主张绑定精确 evidence fragment/locator；来源不足就缩小 claim，不得用 Memory 填空。
3. **Reality**：只从已 grounded 的 claim 重建当时世界状态；保留有效时间、观察时间和来源分歧，不把后见之明写回 Reality。
4. **Contemporaneous Judgment**：恢复一个当时参与者/研究者可合理持有的 Judgment 及其 rationale/known-at；必须与 Reality 分开，也不得用后来 Outcome 改写原 Judgment。
5. **Later Outcome**：用后来才可见的来源单独记录 Outcome，保持 known-at 晚于原 Judgment；Outcome 只用于评价，不反向污染 earlier snapshot。
6. **PIT/no-lookahead replay**：复用 CAP-0007 的 truth-bearing orchestration 组装 source → Evidence → Reality/Judgment → Outcome，再用 CAP-0005 在至少一个历史 cutoff 与一个 later cutoff 重放；任何 future-known Evidence/Outcome 泄漏到早期 cutoff 都必须 fail closed。

优先选择**来源可被现有仓库采集路径可靠取得**、同时具备“当时判断 + 后来结果”的一个 claim cluster。不要为了故事完整性额外扩大来源面。如果最小来源集只能证明 Reality 而不能证明 contemporaneous Judgment，则把该候选判定为不适合本代表性试点，换一个仍在 2020–2023 集运周期内且通过允许来源路径可验证的 claim cluster；最多做必要的候选筛选，不产生多个完成态 trajectory。

## 允许写入

严格以 refreshed main reservation 为准。当前预期仍只有：

- `research_data/memory/shipping/**`：仅可新增第二阶段的 source-archaeology/研究控制辅助记录；不得改写 sealed Memory campaign 的 raw、seal 或 map 以重新开放它。
- `domain_packs/shipping/**`：本试点的 source manifest / Grounded Evidence / Reality / Judgment / Outcome / replay 组合与有界结果。
- `tests/shipping/**`：只添加本试点所需的高信号验证。
- `.longcycle/workstreams/shipping-domain-v1/**` 中 worker 自己可变的 cursor/request/receipt/verification/escalation。

永远禁止 worker 修改 main-owned reservation/change-contract/capability-admission、全局 handoff、active-index、Capability Registry、`src/**`、`migrations/**`、共享 CI、Banking 路径或默认 main。

## 执行与停止

- 这不是 blind probe 循环；**只有一个 stage-two pilot**。
- substantive work 仍按远端 `S -> cursor-only H -> CLEAN`。如果 pilot 需要多个安全 checkpoint，可以做多个 S/H，但它们都必须属于同一个代表性 trajectory；不得把下一个新来源问题当成“第二个 pilot”。
- 每次 substantive S 后做相称验证；最终必须证明 source identity/material integrity、claim-scoped Evidence、Reality/Judgment/Outcome 分离、known-at/valid-time 正确和 PIT/no-lookahead fail-closed。
- 优先直接复用 CAP-0005 与 CAP-0007 的现有 entrypoints/脚本/契约；如果发现必须修改共享 `src/**` 或语义 owner，写 typed request 给 `global_serial` 并停止越界部分，不能在 Shipping 分支复制实现。
- 若来源路径不可用、关键 known-at 无法建立、只能依靠 sealed Memory、或 no-lookahead 无法证明，安全结果是 bounded partial/source gap，不是假装完成。
- 完成本**一个**代表性 trajectory 后停止并 H；不要自行授权下一条 Shipping 轨迹，也不要关闭整个 `shipping-domain-v1` reservation。是否继续第三阶段由 `global_serial` 重新评估。

启动时先简短报告：main/Shipping exact SHA、P146 seal/CLEAN 证据、main reservation revision/epoch、是否已完成 cursor-only 阶段授权接收、六层目标、本试点唯一 claim-cluster 选择标准、允许的来源/路径、通用外网不可用边界以及 L3/L4 状态。满足 CLEAN 后不等待用户确认，执行上述一个代表性来源验证试点。
