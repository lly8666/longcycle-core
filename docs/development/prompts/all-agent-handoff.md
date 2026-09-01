# 所有 Agent 通用交接提示词（ChatGPT 聊天模式）

用途：当前 Agent 完成一个原子任务、准备结束窗口、被要求切换任务，或希望在安全边界停下时，复制下面整段。它不会为每个 Agent 新建一套 handoff；worker 更新自己的一个 cursor，协调员更新一个全局 cursor。

---

现在为你当前承担的 Longcycle 角色执行远端交接。不要开始新的功能、研究探针或范围扩展。仓库操作只使用 GitHub Connect；远端事实优先于当前聊天记忆。

先判断角色类型：

- `parallel worker`：交接文件只能是自己 workstream 的 `cursor.json`；不得写全局 handoff。
- `coordinator / global_serial`：共享实质工作走独立 feature branch/PR；全局交接文件是 `.longcycle/handoff/current.json`，不得代写 worker cursor。
- `read-only reviewer`：没有 reservation 就只出报告，不制造 `S/H`。

按顺序完成：

1. **重新对齐**：复述六层目标，判断本原子任务是 completed、partial、paused、superseded 还是 blocked。若 `done_when` 已满足，停止继续打磨。
2. **刷新写入权**：重新查询精确目标 branch SHA、reservation revision、assignment epoch 和最近远端变化。发现竞争写入、越界路径或非预期分叉就停止并报 `BLOCKED`。
3. **处理外部副作用**：Drive 上传、发布或数据库候选必须已有远端 intent receipt；动作后必须有 outcome receipt。只有 intent 时先查外部对象，不盲目重复执行。
4. **提交 S**：把已经完成的代码/研究 raw/测试/receipt/map，或诚实标记的可恢复 WIP，通过 GitHub Connect 顺序写到明确指定的分支。新原始文件使用唯一 append-only 路径；更新已有文件前重读 blob SHA；绝不写默认 main、覆盖原始文件或 force-update。最后一个实质提交的完整 SHA 记为 `S`。
5. **验证 S**：重读远端 branch，确认 `S` 真正成为 head 或其可证明祖先；核对 changed paths 都在 reservation 内。只记录实际观察到的 CI/verification；未完成就设 `unverified=true`。
6. **提交 H**：
   - worker：单独一次只更新自己的 `cursor.json`；`checkpoint_based_on_head_sha=S`，如实记录完成/partial 状态、验证三元组、有界引用、当前任务、`why_now`、`task_done_when` 和唯一下一动作。
   - coordinator：单独一次只更新 `.longcycle/handoff/current.json`，保持战略层级分工；checkpoint 指向 `S`，不把各行业历史复制进全局 handoff。若拟议 `continuity_sequence` 是 10 的正倍数，只记录并触发现有全局 v3，不另建计数器。
7. **验证 H**：重读精确远端 head；比较 `S..H`，只能出现对应 cursor/handoff；等待该精确 `H` 必需的远端 CI/status。成功才报告 `CLEAN`。

特殊情况：

- 没有任何远端实质变化且 continuation 也没变：不要制造空 `S/H`，报告 `NO_MUTATION`。
- 在 `S` 前被截断：未推送内容不可恢复，下次从旧 cursor 的下一步重做。
- `S` 已推、`H` 未推：下次自动得到 `RECOVERY_REQUIRED`，必须先审查并补 `H`。
- 只能保存安全 WIP：允许 H 标记 `progress_state=partial`、`unverified=true` 和一个明确恢复动作，不能伪装完成。
- L3/L4：停止受影响实现，按六问大白话向用户说明；worker 把升级记录留在自己的 `escalations/` 并由 cursor 指向，不能自行改地基。

最后输出一份短交接收据：角色/workstream、目标 branch、`S` SHA、`H` SHA、continuity 结果、实际验证、完成状态、唯一下一步、外部 intent/outcome 状态、阻塞或 L3/L4。不要粘贴长历史，也不要声称聊天中的未推送思路已经交接。
