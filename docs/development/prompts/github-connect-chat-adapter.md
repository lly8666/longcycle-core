# ChatGPT 聊天 Agent 远端操作协议

本项目所有长期 Agent 都运行在 ChatGPT 聊天模式。统一边界是：

```text
GitHub Connect      = 仓库、分支、提交、PR、CI 和交接控制面
ChatGPT Search      = seal 后的来源发现与原文读取通道（当前窗口可用时）
ChatGPT 临时沙箱    = 当前会话内的文件整理、哈希和数据库私有副本（可用时）
Google Drive        = 大文件的不可变上下载运输（任务需要且连接可用时）
模型内部知识        = blind Memory probe 的输入之一，不是 Evidence
搜索/网页读取能力   = 启动时按当前窗口实际工具判断；不因聊天模式一概禁用
```

Agent 不运行本地 `git`、终端脚本或 worktree 命令，也不能声称运行了它没有的工具。仓库所有读写都通过 GitHub Connect 完成；ChatGPT Search 只承担研究来源发现/读取，不承担仓库写入或 Evidence 认证。

## 1. 每次启动

1. 在 `lly8666/longcycle-core` 查询 `main` 和自己 worker branch 的完整 40 位 head SHA。
2. 从 `main` 读取固定核心、全局 handoff、data-plane manifest 和自己的 `reservation.json`。
3. 从精确 worker head 读取自己的 change contract、capability admission、`cursor.json`，以及 cursor 直接指向的当前地图/verification/receipt。
4. 不遍历全部历史；只有当前文件给出具体 owner、invariant、commit 或 artifact 线索时才查冷历史。
5. 查询精确 head 的远端 CI/status。旧提交的绿灯不能替代当前 head。

## 2. 用 GitHub Connect 判定能否接班

比较 `cursor.checkpoint_based_on_head_sha` 到精确 worker head，核对祖先关系和完整 changed filenames：

- `CLEAN`：checkpoint 与 head 相同，或 checkpoint 到 head 只修改该 worker 自己的 `cursor.json`；reservation、cursor 和热指针一致；精确 head 必需的 worker CI 成功。
- `RECOVERY_REQUIRED`：checkpoint 是 head 的祖先，但 delta 含 raw、receipt、map、代码或其他实质路径。说明远端已有 `S/WIP` 但缺少 `H`；先恢复，不能接新任务。
- `BLOCKED`：checkpoint 不是可证明的祖先，branch/epoch/revision 不一致，出现 reservation 外路径、分叉、写入者冲突或失败的完整性检查。
- `AUDIT_ASSISTANCE_REQUIRED`：GitHub Connect 返回截断比较、拿不到祖先/路径/CI/热指针等关键事实。它不等于 `CLEAN`，不要硬猜。

规范脚本仍是 CI 中的实现。聊天 Agent 通过精确 worker-fast/PR CI 收取消费它的结果，不伪装在本地运行 Python。

## 3. GitHub Connect 写入：S -> H

写入前再次查询 branch head，确认旧 Agent 已停止且只有自己写这条分支。每个写调用必须显式指定目标 worker/feature branch；绝不能省略 branch 写到默认 `main`，也不能 force-update。

`S` 阶段：

1. 新 raw 和 receipt 使用唯一 append-only 路径，已存在就停，不覆盖。
2. 更新 map/cursor 前读取当前 blob SHA；同一路径只做顺序更新，不并行。
3. 若 GitHub Connect 只能逐文件提交，就按 `raw -> receipt -> map` 顺序写。每次写后重读 branch head；最后一个实质提交的完整 SHA 是 `S`。
4. 中途截断时，远端已有的部分自动成为下一轮 `RECOVERY_REQUIRED` 的 WIP，不删除、不假装完成。

`H` 阶段：

1. 读取最新 cursor 与 blob SHA。
2. 令 `checkpoint_based_on_head_sha` 精确等于 `S`，如实记录完成或 partial、`unverified`、唯一下一步和有界引用。
3. 单独提交一次只修改本 worker `cursor.json` 的更新，该提交是 `H`。
4. 重读 branch head并比较 `S..H`，只能出现 cursor；等待精确 `H` 的远端 CI/status 成功，再报告 `CLEAN`。

若 `S` 前截断，从旧 cursor 下一步重做。若 `S` 后截断，下轮先补 `H`。若只完成安全 WIP，H 如实写 `progress_state=partial` 和 `unverified=true`；越界或无法判断则 `BLOCKED`。

## 4. ChatGPT Search 与旧 Evidence 执行边界

先按 live cursor 判断阶段，再决定是否搜索；“聊天模式”本身既不授权搜索污染 blind Memory，也不禁止 seal 后的正常来源研究。

### Blind Memory 阶段

只使用 cursor/map 允许的仓库输入和模型当前内部记忆，保留模糊时间与不确定性，输出始终标为 Memory：

- 不用 ChatGPT Search、GitHub 全站搜索、旧 Evidence、其他 shard 或被禁止 raw 补答案。
- 不把内部记忆写成来源，不伪造引文。
- 不把 Memory 升级为 Evidence、Reality、Outcome 或 seal。

### Seal 后 self-verification / source discovery / Evidence 阶段

沿用 `METHODOLOGY_CORE.md` M1/M3/M7、`docs/research/model-memory-exhaustion-protocol.md` 和 `docs/research/agent-collection-contract.md` 的既有执行方案，不另设更严门槛：

1. 启动时查看当前 ChatGPT 窗口是否有 Search/网页读取能力；可用就直接使用，不需要额外角色或新的架构批准。
2. 高能力 Agent 先用 sealed Memory 的 actor、旧称、approximate period、机制和 search keys 做 self-verification，追 primary/authoritative source、反向查询、citation chain 与同源转载关系。
3. 搜索结果、排名、snippet、AI 摘要和候选 URL 都只是 discovery material。必须打开并实际读取来源，按 claim scope 判断 authority；`not_found != false`。
4. 完全沿用既有三态：只确认 document identity/locator 是 `locator_verified`；实际读到 claim-relevant 原文并保存精确页码/章节/excerpt 或忠实 readable representation 后可记为 `content_verified`；取得并核验 raw bytes 后才是 `materialized`。Raw byte materialization 不是已经 content-verified Evidence 的前置条件。
5. Grounded Evidence 继续要求 claim-scoped content、source identity、实际 retrieval host/URL、publisher、时间和精确 locator；随后才进入 Reality、Judgment、Outcome 与 PIT/no-lookahead。搜索工具及其 citation 本身不获得 Evidence authority。
6. unresolved 搜索的最低深度、权威原文已直接解决时的停止规则、高影响 claim 的反向查询，继续复用现有 `verification_stop_decision` 语义；不得另加固定网页数、固定来源数或下载配额。
7. 网页可读内容、PDF readable representation、原始 bytes 和大文件需要交接时，继续走 `.longcycle/handoff/data-plane.json` 已有的 provenance/Drive/延迟 materialization 路径；transport 不改变来源等级。

若当前窗口没有 Search/网页读取能力，而 live cursor 需要外部来源，报告 `CAPABILITY_BLOCKED_EXTERNAL_SOURCE` 并完成交接，交给有该能力的新聊天窗口继续同一角色。工具缺失本身不是 `bounded_source_gap`，也不是现实世界的 `not_found`。只有实际执行了当时获授权且可用的 discovery/source 路径，并达到旧协议的停止条件后，才可以如实记录 bounded source gap。

## 5. 沿用初代 Agent 的 Drive 上下载路径

只有当前 cursor 明确需要数据库/二进制资产时才恢复；`required_for_current_task=false` 的历史对象一律不下载。

### 下载恢复

1. 从刷新后的 `.longcycle/handoff/data-plane.json` 读取精确 generation、Drive file id/revision、size、SHA-256、schema 和 restore instruction。
2. 按 file id 下载到当前 ChatGPT 会话的私有沙箱，不按文件名或“最新”查找。
3. 校验 revision（若有）、size、SHA-256，并实际打开/读取数据库。
4. 原 base 默认只读；需要改动先复制成当前 workstream 私有副本。禁止多个 Agent 共用一个可写数据库。

### 上传候选

1. 关闭/checkpoint 数据库，计算 candidate 的 SHA-256、大小、schema/content count。
2. 先通过 GitHub Connect 向自己的 worker 分支推送 bounded upload intent receipt，并完成它的 `H`。intent 固定 operation id、workstream/epoch、producer head、base generation/digest、candidate digest/size、唯一文件名和 data-plane manifest 中的 Drive folder id。
3. 通过已授权的 ChatGPT/Google Drive 路径上传一个全新私有对象；永不覆盖 base，也不需要改变分享权限。
4. 记录返回的 file id/revision/name/MIME/size，然后按精确 file id 下载回来。
5. 重新核对 size/SHA-256，并实际打开/读取数据库。
6. 再通过 GitHub Connect 推送关联同一 operation id 的 outcome receipt，写明 `download_back_verified=true`，随后完成 cursor-only `H`。

若中断后只有 intent 没有 outcome，下一轮先在精确 folder 中按唯一名称查对象，再按 digest 下载验证。确认已有正确对象就补 outcome；只有可靠证明不存在才用同一 operation id 重试；状态含糊则 `BLOCKED`，禁止盲目重复上传。

Drive 只是字节运输，当前数据库代际仍由刷新后的 main Git 指针决定。worker 只能交 candidate；只有现有 `global_serial` 协调通道在核对 predecessor、逐个重放、验证并 round-trip 后才能 compare-and-swap 提升 generation head。

如果当前聊天没有 Drive 连接，而 cursor 又确实需要该对象，报告 `CAPABILITY_BLOCKED_DRIVE` 并请用户在有 Drive 连接的聊天窗口继续同一角色；这不是 L3/L4，也不能改用 GitHub 塞大文件。

## 6. 启动报告与自动继续

先用简短进度消息报告：main/worker 精确 SHA、continuity 状态及依据、六层目标、允许/禁止输入、唯一下一步、当前 Search/网页读取/Drive 能力是否影响该任务、是否存在 L3/L4。

- 状态为 `CLEAN` 且没有用户决策阻塞：报告后在同一轮自动执行唯一下一步，不把启动报告变成等待用户回复的关卡。
- 状态不安全：只恢复或上报，不开始新任务。
- 结束前执行 `docs/development/prompts/all-agent-handoff.md`；被截断时由下一轮通过同一个启动审计自动补完缺失的 `H`。

行业 Memory Campaign Lead 只有在 live cursor 仍处于 blind Memory 阶段时，才以最多 4 个**顺序** probe 为软目标。每个 probe 都单独完成 `S -> H -> CLEAN`，然后重读地图动态选择下一个；不并行、不预排、不把四个 probe 合成一个无中间检查点的大任务。上一轮被截断时，下一轮第一动作永远是恢复旧 probe/缺失的 `H`，达到 `CLEAN` 后再继续。seal 后的搜索/Evidence 阶段按 cursor 的一个有界 source/claim task 执行，不继承四-probe 配额。没有安全下一步或无法保证下一次完整交接时可以提前结束。
