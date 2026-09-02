# ChatGPT 聊天 Agent 远端操作协议

本项目所有长期 Agent 都运行在 ChatGPT 聊天模式。统一边界是：

```text
GitHub Connect      = 仓库、分支、提交、PR、CI 和交接控制面
ChatGPT 临时沙箱    = 当前会话内的文件整理、哈希和数据库私有副本（可用时）
Google Drive        = 大文件的不可变上下载运输（任务需要且连接可用时）
模型内部知识        = blind Memory probe 的输入之一，不是 Evidence
通用外网            = 不假定可用
```

Agent 不运行本地 `git`、终端脚本或 worktree 命令，也不能声称运行了它没有的工具。仓库所有读写都通过 GitHub Connect 完成。

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

## 4. 无外网研究边界

当前 Banking 和 Shipping 任务都是 blind Memory probe，聊天 Agent 可以执行：只使用 cursor/map 允许的仓库输入和模型当前内部记忆，保留模糊时间与不确定性，输出始终标为 Memory。

- 不用 GitHub 全站搜索、旧 Evidence、其他 shard 或被禁止 raw 补答案。
- 不把内部记忆写成来源，不伪造引文。
- 不把 Memory 升级为 Evidence、Reality、Outcome 或 seal。
- 若以后 cursor 明确需要外部 Evidence，而本会话没有对应访问能力，报告 `CAPABILITY_BLOCKED_EXTERNAL_SOURCE` 并交接；不能用猜测代替。

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

先用简短进度消息报告：main/worker 精确 SHA、continuity 状态及依据、六层目标、允许/禁止输入、唯一下一步、当前外网/Drive 能力是否影响该任务、是否存在 L3/L4。

- 状态为 `CLEAN` 且没有用户决策阻塞：报告后在同一轮自动执行唯一下一步，不把启动报告变成等待用户回复的关卡。
- 状态不安全：只恢复或上报，不开始新任务。
- 结束前执行 `docs/development/prompts/all-agent-handoff.md`；被截断时由下一轮通过同一个启动审计自动补完缺失的 `H`。

行业 Memory Campaign Lead 的一次聊天执行默认目标是最多 3 个**顺序** probe。每个 probe 都单独完成 `S -> H -> CLEAN`，然后重读地图动态选择下一个；不并行、不预排、不把三个 probe 合成一个无中间检查点的大任务。没有安全下一步或无法保证下一次完整交接时可以提前结束。
