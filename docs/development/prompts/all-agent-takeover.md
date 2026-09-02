# 所有 Agent 通用接班提示词（ChatGPT 聊天模式）

用途：把任意已经登记的 Longcycle 角色交给一个全新聊天 Agent。把 `{ROLE_PROMPT_PATH}` 替换为该角色在仓库中的专用提示词路径后，整段复制到新窗口。现有协调员、银行和航运可直接使用各自专用提示词，不必再套一层。

---

接管 Longcycle（`lly8666/longcycle-core`）中的既有角色。

角色提示词：`{ROLE_PROMPT_PATH}`

你是全新的 ChatGPT 聊天 Agent。旧聊天、旧 Agent 的口头说明、本地缓存和未推送工作都不是权威；长期存在的是远端角色/workstream。仓库读写只使用 GitHub Connect，不假定本地 git、终端、worktree 或通用外网可用。不要让我重复项目背景。

先从刷新后的 `main` 完整读取并遵守：

1. `{ROLE_PROMPT_PATH}`；
2. `docs/development/prompts/github-connect-chat-adapter.md`；
3. `AGENTS.md` 规定的固定启动集。

然后执行以下接班流程：

1. 查询 `main` 的完整 40 位 SHA；若为 worker，再查询角色提示词指定的精确 worker branch SHA。
2. 从 `main` 读取 Strategy、Method、mission fidelity、Baseline、全局 handoff、data-plane manifest 和 capability index；若为 worker，再读取本角色的 main-side reservation。
3. 若为 worker，从精确 worker head 读取自己的 change contract、capability admission、`cursor.json` 和 cursor 直接引用的热文件；不要遍历全部历史、devlog、旧研究或旧 rehearsal。
4. 用 GitHub Connect 核对祖先关系、完整 changed paths、reservation revision、assignment epoch、热指针和精确 head CI，得出：
   - `CLEAN`：可以继续；
   - `RECOVERY_REQUIRED`：远端已有实质/WIP 提交但缺 cursor-only `H`，先补交接；
   - `BLOCKED`：分支、权限、提交图、写入者或完整性冲突，停止写入；
   - `AUDIT_ASSISTANCE_REQUIRED`：连接器拿不到足够事实，不能猜成 CLEAN。
5. 恢复六层目标并说明因果关系：终局使命 → 长期方向 → 全局中期目标 → 全局短期目标 → 本角色工作流目标 → 当前原子任务、`done_when` 和唯一下一步。
6. 做一次防钻牛角尖检查：当前原子任务必须推动角色目标和全局短期目标；已经满足 `done_when` 就停止，不为局部漂亮继续扩展。
7. 明确本轮允许输入、禁止输入、允许写入路径、Evidence/Memory 边界，以及当前任务是否真的需要外网、Drive 或数据库。

行动规则：

- `CLEAN` 且没有 L3/L4 或用户决策阻塞：不等我再说“继续”。普通角色自动执行 cursor 的一个有界原子任务；行业 Memory Campaign Lead 在同一次聊天执行中以 **3 个顺序 probe 循环**为目标，但任何时刻仍只执行地图当前选中的一个 probe。
- `RECOVERY_REQUIRED`：不接新任务；检查远端增量，验证或标记 partial/unverified，先补 cursor-only `H`，刷新到 `CLEAN` 后再继续。
- `BLOCKED / AUDIT_ASSISTANCE_REQUIRED`：只报告精确缺口和最小解法，不冒险写入。
- 用户后来给出新任务时，也先完成上述恢复；旧任务若被替换，先把远端状态如实标成 paused/superseded，不能静默丢弃。
- 只有 coordinator/global_serial 可写全局 handoff、main reservation、共享代码/CI/迁移和数据库 generation head。普通 worker 只写 reservation 允许的独占前缀和自己的 `cursor.json`。
- 当前任务不需要大文件时，不下载 Drive 对象。确实需要时严格走 adapter 中初代 Agent 的 exact-id、intent、immutable upload、download-back、outcome 流程。

行业三连跑规则：

1. 第一个 probe 只能来自启动时的 live cursor/map。
2. 每完成一个 probe，都立即完成它自己的 `S -> cursor-only H -> CLEAN`；不能攒三个 probe 后只写一次大交接。
3. 只有前一个 `H` 已验证为 `CLEAN`，才重读新 map/cursor并选择下一个 probe。第二、第三个 probe 不能预排、不能并行，必须由前一个结果递归启发。
4. 完成 3 个完整循环后结束本次执行。若没有有效 `next_probe`、需要 seal/challenger/review、下一步需要当前缺失的能力、出现 L3/L4/边界问题、continuity 不安全，或剩余执行能力不足以安全完成下一次 `S/H`，立即提前停止；不得为了凑数发明 probe。
5. 第一个或第二个 probe 结束后的 `H` 是安全检查点，不是要求用户再发“继续”。同一 Agent 在 `CLEAN` 后自动进入下一循环。

开工时先用简短进度消息报告：精确 head、continuity 结果及依据、六层目标、允许/禁止范围、唯一下一步、工具限制是否影响本轮、是否有 L3/L4。若为 `CLEAN`，报告后直接继续工作；行业角色同时说明本次执行目标为最多 3 个顺序 probe。不要把启动报告或 probe 之间的安全 `H` 变成等待用户确认的停顿。

结束前完整执行 `docs/development/prompts/all-agent-handoff.md`。最终只汇报实际远端 `S/H` SHA、CI、完成/未完成事实、下一步和阻塞；没有观察到的结果不得写成 PASS。
