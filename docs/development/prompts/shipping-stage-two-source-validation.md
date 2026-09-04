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
- 启动时检查当前窗口是否有 ChatGPT Search/网页读取。P146 已 seal，因此本阶段明确恢复并授权旧方案中的 high-model self-verification/search discovery：Search 可用就直接使用，不得因为聊天模式或仓库只用 GitHub Connect 而禁用研究搜索。GitHub Connect 仍只负责仓库控制面。
- 完全沿用 `METHODOLOGY_CORE.md` M1/M3/M7、`docs/research/model-memory-exhaustion-protocol.md`、`docs/research/agent-collection-contract.md`、CAP-0001 与 CAP-0002 的既有 Evidence 标准，不新增任何固定网页数、来源数、下载数或更高认证门槛。
- 搜索结果、排名、snippet、ChatGPT 回答、AI 摘要和候选 URL 只属于 discovery material。必须打开并实际读取来源，再按 claim scope、upstream identity、retrieval host、publisher、时间和 locator 认证；搜索 citation 本身不是 Evidence。
- 继续使用旧三态：只确认 document identity/locator 是 `locator_verified`；实际读到并保存 claim-relevant 页码/章节/excerpt 或忠实 readable representation 后是 `content_verified`，可以进入正常 Grounded Evidence；只有实际取得并验证 raw bytes 才是 `materialized`。不得把 locator 当 claim Evidence，也不得把 readable representation 冒充 raw bytes；raw materialization 不是 content-verified Evidence 的前置条件。
- 对 unresolved claim 复用既有 query-family、source-type、primary-domain、reverse-query、citation-chase 和停止规则；权威原文已直接解决 claim 时按旧规则停止，不为凑数继续搜。`not_found != false`。
- 当前窗口若没有 Search/网页读取能力，记录 `CAPABILITY_BLOCKED_EXTERNAL_SOURCE` 并 H，交给有 Search 的全新聊天继续同一角色；工具缺失本身不得写成 bounded source gap。只有实际执行当时获授权且可用的 discovery/source 路径，并达到旧协议停止条件后，才可记录有界 source gap。
- Drive/数据库/网页 capture 或 raw materialization 仅在 live data-plane 和当前材料需要时使用既有路径；transport 不改变来源 authority，也不新增 Evidence 前置条件。

## 第二阶段授权接收

本阶段**沿用现有 reservation fence**。不要假定某个固定 revision 数字，也不要自行增加 `reservation_revision` 或 `assignment_epoch`；两者必须与 refreshed main 完全一致。当前阶段授权来自 refreshed main 的 reservation / Change Contract / capability admission / global handoff 与本提示词的组合，而不是 worker 自己扩大权限。

如果 worker cursor 仍停在 P146 的 sealed/CLEAN H，且它记录的 reservation revision / assignment epoch 与 refreshed main 一致：

1. 这不是 P147，也不是新研究 probe；先把它视为一次**阶段授权接收**。
2. 只更新自己 branch 的 `cursor.json`：保持 `reservation_revision` 和 `assignment_epoch` 与 refreshed main 完全一致，把 `current_task`、`why_now`、`task_done_when`、`next_atomic_action` 从 sealed-stop 状态改成下面这个唯一来源验证试点，并保留 P146 seal / receipt / map 作为阶段边界引用。
3. 不得在这次授权接收中写 Memory/raw/map/Evidence/Domain Pack，也不得改 main-owned reservation/change-contract/capability-admission/global handoff。
4. 该授权接收提交必须是 cursor-only；刷新 exact worker head，等待 `worker-fast` 成功并重新判定 CLEAN 后，才可开始试点的第一个 substantive S。
5. 若 revision/epoch/branch/writer/ancestry 事实不一致，按 continuity 协议停止或恢复；不要自行改 fence。

### 恢复被旧禁搜约束提前关闭的同一试点

若 refreshed worker cursor 已停在 `paused/bounded_source_gap`，并直接引用 `domain_packs/shipping/source-validation/container-pandemic-cycle-2020-2023-source-gap.json`，先核对该记录确实说明 `generic_web_used=false` 且结论只覆盖旧 GitHub-only 执行路径。

本 main-side Change Contract 明确作如下 supersession：旧 source-gap 原字节和“当时 GitHub-only 路径没有材料”的结论继续保留；仅撤销它对整个 stage-two pilot 的完成/停止效力。恢复 ChatGPT Search 后继续的是**原来同一个 pilot**，不是第二条 trajectory，也不是 P147。

1. 先只更新本角色 `cursor.json`，保留旧 gap 引用，记录它被 `restored_post_seal_chatgpt_search` 执行授权 supersede，并把唯一下一步设为对同一 2020–2023 container-pandemic pilot 做 high-model self-verification/source discovery。
2. 这次恢复授权仍必须 cursor-only，不得同时写来源、Memory、Evidence 或 Domain Pack。
3. 刷新 exact worker head，等待 `worker-fast` success/CLEAN；之后才开始新的 substantive S。
4. 不覆盖或删除旧 gap。后续若搜索仍不足，新结果必须区分“已搜索但 unresolved”与“工具不可用”，并按旧停止标准留下新的精确收据。

## 第二阶段唯一试点

范围只允许：**2020–2023 集装箱航运疫情周期（container-pandemic-cycle-2020-2023）中的一个代表性 claim cluster / trajectory**。不要重做全行业、不要扩成第二个 trajectory，也不要追求覆盖率。

从最小充分的 source archaeology 开始，选择一个能同时支撑下面链条的代表性历史问题：

1. **Source archaeology**：先由同一高能力 Agent 使用 sealed Memory 的 actor、旧称、approximate period、机制和 search keys，通过 ChatGPT Search 寻找 primary/authoritative 原始来源、反向材料和 citation chain；再确定最小充分的来源集合、logical source identity、版本/可读表示、来源在当时何时可知。来源必须通过既有 CAP-0001/CAP-0002 路径获得或确认。
2. **Claim-scoped Grounded Evidence**：每个可验证主张绑定精确 evidence fragment/locator；来源不足就缩小 claim，不得用 Memory 填空。
3. **Reality**：只从已 grounded 的 claim 重建当时世界状态；保留有效时间、观察时间和来源分歧，不把后见之明写回 Reality。
4. **Contemporaneous Judgment**：恢复一个当时参与者/研究者可合理持有的 Judgment 及其 rationale/known-at；必须与 Reality 分开，也不得用后来 Outcome 改写原 Judgment。
5. **Later Outcome**：用后来才可见的来源单独记录 Outcome，保持 known-at 晚于原 Judgment；Outcome 只用于评价，不反向污染 earlier snapshot。
6. **PIT/no-lookahead replay**：复用 CAP-0007 的 truth-bearing orchestration 组装 source → Evidence → Reality/Judgment → Outcome，再用 CAP-0005 在至少一个历史 cutoff 与一个 later cutoff 重放；任何 future-known Evidence/Outcome 泄漏到早期 cutoff 都必须 fail closed。

优先选择**来源可由 ChatGPT Search 实际读取并按现有 CAP-0001/CAP-0002 规则保存**、同时具备“当时判断 + 后来结果”的一个 claim cluster。不要为了故事完整性额外扩大来源面。如果最小来源集只能证明 Reality 而不能证明 contemporaneous Judgment，则把该候选判定为不适合本代表性试点，换一个仍在 2020–2023 集运周期内且通过允许来源路径可验证的 claim cluster；最多做必要的候选筛选，不产生多个完成态 trajectory。

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
- 若实际可用的旧搜索/来源路径按既有停止规则执行后仍无法取得材料、关键 known-at 无法建立、只能依靠 sealed Memory、或 no-lookahead 无法证明，安全结果是 bounded partial/source gap，不是假装完成。当前窗口根本没有 Search/网页读取能力时只记 capability blocker，不冒充搜索完成。
- 完成本**一个**代表性 trajectory 后停止并 H；不要自行授权下一条 Shipping 轨迹，也不要关闭整个 `shipping-domain-v1` reservation。是否继续第三阶段由 `global_serial` 重新评估。

启动时先简短报告：main/Shipping exact SHA、P146 seal/CLEAN 证据、main reservation revision/epoch、是否需要恢复旧禁搜 source-gap、是否已完成 cursor-only 阶段授权接收、六层目标、本试点唯一 claim-cluster 选择标准、当前 ChatGPT Search/网页读取能力、沿用的旧 Evidence 三态与 L3/L4 状态。满足 CLEAN 后不等待用户确认，执行上述同一个代表性来源验证试点。
