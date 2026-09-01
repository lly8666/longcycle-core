# Longcycle 多 Agent 开发治理说明书

状态：`v1`，适用于 Architecture Baseline v1 之后的并行开发。

这是一份给人和新 Agent 使用的中文总路由说明，不另造一套规则。发生冲突时，`STRATEGIC_COMPASS.md`、`METHODOLOGY_CORE.md`、Architecture Baseline、能力卡、主分支 reservation、工作分支 cursor，以及本文件引用的各专项协议依次按其原有权威范围生效。

## 1. 一页大白话

Longcycle 不把一个聊天窗口当成一个长期员工。长期存在的是“角色和工作流”，Agent 只是随时可替换的一班人。

- 项目只有一个全局控制面：战略、方法、Baseline、能力归属、主分支、CI、数据库当前代际指针。
- 每个行业有一条独立工作流：自己的远端分支、写入范围、当前地图和游标。银行不能写航运，航运也不能写银行。
- 全局共享改动和数据库代际提升只有一条串行集成通道，避免多个 Agent 同时改地基。
- 每条工作分支同一时刻只能有一个写入者。不同工作分支可以真正并行。
- 聊天被截断没有关系。已经推送工作但没写交接，就在下次启动时先自动补交接；没有推送的工作不能假装恢复，只能从远端记录的上一步重做。
- 每次工作完成都采用 `S -> H`：先推送实质工作 `S`，再单独推送只包含游标的交接确认 `H`。
- 行业知识不是按目录标题“填满”。每个行业维护一张稀疏探索地图，每次只做一个信息价值最高的探针，用新颖度、负空间和独立挑战者判断何时停。
- 旧研究错误不删除、不改写原字节；用精确更正或 supersession 把它移出当前状态和 Evidence 入口。当前地图和游标是唯一热入口。
- 热交接只保留当前目标、一个下一步和少量指针。多年历史留在 Git、不可变收据和 Drive 对象里，按需查，不塞进每次启动上下文。
- 没有硬性的 25 分钟或 15 轮正确性门槛。应当让接班成本很小，但不能为了赶时间省略远端推送和交接确认。

本轮治理整理属于 `L2`：复用 `CAP-0006`、`CAP-0009`、`CAP-0010`，没有改变 Architecture Baseline。当前没有发现需要用户决策的 `L3/L4` 问题。

## 2. 权威、状态与优先级

### 2.1 哪些东西说了算

| 问题 | 权威来源 | 不可替代它的东西 |
| --- | --- | --- |
| 项目为何存在、最终要成为什么 | `STRATEGIC_COMPASS.md` | 某个 Agent 的聊天总结 |
| 研究认识论和 Reality/Judgment/Outcome 边界 | `METHODOLOGY_CORE.md` | 行业便利做法 |
| 不可随便改的系统地基 | Architecture Baseline 与 `.longcycle/baseline/current.json` | 临时提示词 |
| 一个能力由谁负责 | `.longcycle/capabilities/` | 新 Agent 自己造的重复模块 |
| 全局当前目标和串行集成状态 | 刷新后的 `origin/main` 与 `.longcycle/handoff/current.json` | 本地缓存、旧聊天、截图 |
| 一个行业允许写哪里、长期做到什么 | 刷新后主分支上的 `reservation.json` | 行业分支自行扩权 |
| 一个行业当前做到了哪、下一步是什么 | 该行业精确远端分支上的 `cursor.json` | 本地未推送文件 |
| 大文件当前有效代际 | 主分支 Git 数据代际指针 | Drive 修改时间或“最后上传的文件” |
| 工作是否真的通过 | 精确提交对应的远端 CI | 旧提交的绿灯或口头报告 |

所有 Agent 开工前都要先刷新远端。示例提交哈希只能帮助定位，不能覆盖已经变化的远端事实。

### 2.2 热、温、冷三层状态

- 热状态：当前 handoff、活动 reservation、当前 cursor、每个行业的一张探索地图。它必须有界。
- 温状态：最近的收据、集成请求、校验记录，只在当前决策需要时读取。
- 冷状态：Git 历史、旧地图、旧原始输出、已完成收据、Drive 不可变对象。只按明确线索查找。

接班 Agent 不需要“读懂项目所有历史”。它需要从热状态恢复宏大框架和一个正确下一步，再按问题路由到温/冷证据。

## 3. 治理拓扑

```text
用户（L3/L4 最终决策）
              |
              v
全局协调员 / global_serial 集成通道
  |           |                 |
  |           |                 +-- 数据代际提升职责（不是第二个控制面）
  |           +-- 按需共享功能工作流（满足创建门槛才开）
  |
  +-- 银行业负责人  <-> 自己的 reservation / branch / cursor / map
  +-- 航运业负责人  <-> 自己的 reservation / branch / cursor / map
  +-- 未来行业负责人 <-> 各自完全隔离的工作流

行业内可按需使用：一次性盲探针执行者、独立饱和挑战者、只读审阅者。
它们不是永久管理层；若需要写入，必须获得独立 reservation，或由行业负责人暂停写入后独占同一分支。
```

这套结构的关键不是“多设领导”，而是把三件事拆开：谁决定共享规则、谁拥有行业结果、谁拥有当前写入权。

## 4. 角色说明

### 4.1 用户 / 项目所有者

用户决定真正的地基变化，包括 `L3/L4` 事项、不可逆外部动作和项目方向取舍。正常 `L1/L2` 工作不应频繁打断用户。

### 4.2 全局协调员兼串行集成负责人

长期职责：

- 恢复终局、长期、中期、短期和下一大步，防止各行业局部最优。
- 刷新并审计所有活动工作流，只看有界状态和收据，不吞掉行业原始研究。
- 维护主分支 reservation、能力归属、共享协议、全局 handoff 和 CI。
- 接收行业提出的 typed integration request；只有共享改动真正合并并产生 completion receipt 后，行业才能消费它。
- 比较不同产业每轮最多一个方法观察。只有相同实质问题在独立行业重复出现，才考虑共享能力改动。
- 承担数据库代际提升职责；Drive 只运输不可变候选文件。
- 遇到 `L3/L4` 停止改变地基的部分，用大白话向用户说明。

明确不做：

- 不直接替行业做盲回忆或 Evidence 搜索。
- 不跨写行业目录，不在协调员分支修补银行/航运原始数据。
- 不为“以后也许有用”新增长期角色、密集本体、统一调度器或提示词配额。
- 不把每个行业的全部 cursor 复制进全局 handoff。

### 4.3 行业负责人 / Industry Campaign Lead

每个行业是一条长期工作流，但负责人 Agent 实例可以随时更换。它负责：

- 只在 reservation 允许的前缀内写入。
- 从全局短期目标推导自己的工作流目标、当前原子任务和 `done_when`。
- 维护一张稀疏探索地图，始终只选择一个 `next_probe`。
- 严格分开 Memory、Evidence、Reality、Judgment、Outcome；盲回忆阶段不偷看搜索或其他被禁输入。
- 每次探针写不可变原始输出、一个有界收据、更新同一地图，并完成 `S -> H`。
- 每轮最多提交一个 campaign-local 方法观察；不要一边研究一边另造共享框架。
- 如果需要共享功能，只提请求，不复制实现。

### 4.4 一次性盲探针执行者

适合隔离一个严格限定输入的盲回忆单元。默认只完成一个探针即退出。

- 输入必须列白名单，并记录模型/工具版本和输入摘要。
- 输出只能进入 Memory 轨道，不能自行升级为 Evidence 或真相。
- 不读其他探针原文，不读搜索结果，不自行扩大时段或系统切片。
- 若与行业负责人共用一条分支，二者不能同时写；更安全的方式是行业负责人停止写入并交出唯一写入权。

### 4.5 独立饱和挑战者

它是 seal gate 的独立反方，不是另一个永久负责人。

- 接受明确的地图、近期结果和负空间问题。
- 尝试证明“还有重要区域没探到”，不能只是给原负责人背书。
- 自己不批准 seal；它只出挑战结果。
- 需要写入时同样遵守 reservation 和单写入者规则。

### 4.6 共享功能负责人

只有满足下列条件之一才创建：

1. 至少两个独立行业出现同一个实质能力缺口；或
2. 一个已有能力 owner 明确需要扩展，且行业分支不能安全地各自实现；或
3. 用户批准了需要串行处理的 `L3/L4` 地基变化。

它先查能力注册表，默认 `reuse` 或 `extend`，不默认 `new`。任务完成并合并后可以关闭，不自动变成永久管理层。

### 4.7 只读审阅者 / 测试 Agent

它可以从干净远端环境重建目标、检查边界和运行高信号测试，但不能在未获写入 reservation 时“顺手修复”。发现问题后给出可复现事实和严重级别。

## 5. 什么时候创建新角色，什么时候只换新 Agent

### 5.1 只换 Agent 实例

出现以下情况时，不创建新角色：

- 聊天接近轮次限制；
- 当前 Agent 被系统截断；
- 同一职责需要新窗口继续；
- 想用全新上下文做独立检查。

做法是停止旧实例写入，给新实例粘贴对应角色提示词，让它刷新远端并运行 continuity audit。角色身份来自 reservation/cursor，不来自旧 Agent 的自我介绍。

### 5.2 创建新的行业工作流

当存在一个独立行业目标、可隔离写入范围和可验收结果时，由协调员在主分支：

1. 查 Repair Memory 和能力注册表；
2. 判定 `L1/L2/L3/L4` 及 `reuse/extend/replace/new`；
3. 建立唯一 `workstream_id`、远端分支和主分支 reservation；
4. 写清目标、`done_when`、允许写入前缀、依赖和集成通道；
5. 在工作分支建立 change contract、capability admission、cursor 和最小地图；
6. 运行边界/注册表检查，推送并确认精确远端状态；
7. 生成该角色的 Fresh-Agent 提示词。

行业 Agent 不能自行给自己增加写入前缀或创建平行的共享语义 owner。

### 5.3 创建共享功能工作流

行业先提交有类型的请求，至少包含：问题、现有 owner、为什么不能复用、需要的契约、禁止改变的 invariant、验收条件。协调员确认重复需要后创建一条共享工作流。共享功能只有合并收据，不以“另一个 Agent 说做好了”为可消费条件。

### 5.4 不该创建的角色

- 每个小功能一个永久 Agent；
- 每个时间片一个长期负责人；
- 一个专门把所有历史复制到新 handoff 的“记忆管理员”；
- 多个可以修改主分支/数据库指针的协调员；
- 同一行业分支上的并行写入者。

### 5.5 新角色提示词生成模板

以后每创建一个真实新角色，都用下面十段生成一份仓库内提示词；不要把旧聊天摘要直接当提示词：

```text
角色身份：<长期 role / workstream_id>；本窗口只是可替换实例。
远端权威：<main ref> + <worker ref>；本地缓存和旧聊天不具权威。
唯一写入权：<branch>；允许前缀 <...>；明确禁止 <...>；一分支一写入者。
固定启动集：Strategy / Method / mission fidelity / Baseline / global handoff /
             capability index + 自己的 reservation / contract / admission / cursor / 当前地图。
启动审计：<精确命令>；CLEAN 才工作；RECOVERY_REQUIRED 先补 H；BLOCKED 找协调员。
目标恢复：终局、长期、中期、短期、工作流、当前原子任务/完成条件/唯一下一步。
当前任务：只从刷新后的 cursor 读取；提示词中的任务名称只是回退示例。
执行边界：允许输入、禁止输入、产物、测试、停止条件、外部副作用收据。
交接：推 S，再推 cursor-only H，再刷新审计到 CLEAN；未推送的工作从远端下一步重做。
升级：共享需要走 typed request；L3/L4 停地基改动并用六项大白话请用户决定。
首次回复：远端头、审计状态、六层目标、边界、唯一下一步、L3/L4 判断。
```

若这些字段还不能填清楚，说明角色尚未具备可创建条件；不要先开 Agent 再让它自己猜职责。

## 6. 新 Agent 的统一启动协议

每个新 Agent 必须按以下顺序开始，旧 Agent 恢复时也一样。

### 第一步：确认身份与唯一写入权

- 说明自己是协调员、银行负责人或航运负责人中的哪一个。
- 说明自己的远端分支和允许写入范围。
- 确认前一个实例已经停止写入；不能确认时只读审计，不推送。
- 真正写入前使用只服务于该角色的干净隔离 worktree，并从精确远端 ref 快进/建立；不要复用另一个 Agent 正在使用的 checkout。

### 第二步：刷新远端，不信本地缓存

刷新 `origin/main` 和自己的精确 worker ref。协调员刷新所有活动 worker refs。Drive、本地数据库、旧聊天和附件都不是当前代码/游标权威。

### 第三步：有界读取宏大框架

先读启动集合：

1. `STRATEGIC_COMPASS.md`
2. `METHODOLOGY_CORE.md`
3. `.longcycle/continuity/mission-fidelity.json`
4. `CONTINUE_HERE.md`
5. `.longcycle/baseline/current.json`
6. `.longcycle/handoff/current.json`
7. `.longcycle/handoff/data-plane.json`
8. `.longcycle/capabilities/active-index.json`

行业 Agent 再读主分支自己的 `reservation.json`、精确工作分支自己的 `cursor.json`，以及 cursor 直接指向的当前地图。不要从第一天开始遍历全部 devlog 和研究历史。

### 第四步：恢复六层目标

开工前用自己的话写出：

1. 终局使命；
2. 长期方向；
3. 当前全局中期目标；
4. 当前全局短期目标；
5. 自己的工作流目标；
6. 当前原子任务、`done_when` 和唯一下一步。

如果当前原子任务不能解释怎样推动第 3—5 层，就停止或重新对齐，不能钻牛角尖式继续优化局部。

### 第五步：运行启动审计

行业工作流运行：

```text
python scripts/audit_workstream_continuity.py <workstream-id> --remote origin --main-branch main
```

只接受三种结果：

- `CLEAN`：可以执行 cursor 的当前任务。
- `RECOVERY_REQUIRED`：远端已有 `S`，但缺 `H`；先检查 `S`，补写 cursor-only `H`，重新审计到 `CLEAN`，才接新任务。
- `BLOCKED`：分支、reservation、提交图或写入边界冲突；停止写入，交给协调员处理。

协调员还要检查全局 handoff 相对当前 main 的新鲜度，并对全部活动行业执行相同审计。

### 第六步：只执行一个有界原子任务

先写清允许输入、禁止输入、允许路径、验收条件和停止条件。任务中若出现相关历史线索，再按 owner/invariant/origin 精确查冷历史。

## 7. 中断与交接：S -> H

### 7.1 正常完成

`S` 是实质提交：代码、测试、研究原始输出、收据、地图，或一个明确可恢复的 WIP 检查点。先提交并推送 `S`。

`H` 是随后单独的游标确认提交。对 worker 来说，`H` 只能更新自己的 `cursor.json`；它记录：

- `checkpoint_based_on_head_sha = S`；
- 已完成动作；
- 当前任务和为什么现在做；
- `task_done_when`；
- 唯一下一原子动作；
- 六层目标的父引用；
- 有界 artifact/receipt/verification 引用。

推送 `H` 后刷新远端并重跑审计，直到 `CLEAN`。不能只在聊天里说“已交接”。

### 7.2 被截断时的恢复表

| 截断位置 | 远端事实 | 下个 Agent 怎么做 |
| --- | --- | --- |
| `S` 之前 | 没有可验证的新工作 | 从上一个远端 cursor 的下一步重做；不能认领本地残片 |
| `S` 已推送、`H` 未推送 | audit 返回 `RECOVERY_REQUIRED` | 先审查 `S` 是否在范围内，再补 `H`；不接任何新任务 |
| `H` 已推送 | audit 返回 `CLEAN` | 直接执行 cursor 下一步 |
| 提交图/范围不一致 | audit 返回 `BLOCKED` | 停止推送，由协调员解决 |

同一个 Agent 自己继续和全新 Agent 接班走完全相同的流程，所以不依赖“它还记不记得刚才在想什么”。

### 7.3 外部副作用

上传 Drive、发布对象、数据库候选等不能只靠 `S -> H`。动作前先写 intent receipt，动作后写 outcome receipt；重试前先查询是否已经完成，使用稳定 idempotency key，避免重复上传或重复提升。

## 8. 并行开发如何不冲突

### 8.1 三条硬边界

1. 一条 worker 分支同一时刻一个写入者；禁止 force-push。
2. 每个 worker 只写 reservation 的 `exclusive_write_prefixes` 和自身控制文件。
3. 主分支共享规则、迁移、CI、reservation、全局 handoff 和数据库代际指针走 `global_serial`。

银行和航运可以同时研究，因为目录和分支互斥；它们不能同时“顺手”改公共 Memory Campaign 逻辑。

### 8.2 共享请求与收据

行业发现公共缺口时：

- 在自己的 cursor/receipt 中记录问题；
- 形成 typed integration request；
- 继续做不依赖该缺口的行业工作，或明确阻塞；
- 等协调员在共享分支完成、测试、合并并给 completion receipt；
- 只有收据对应的主分支提交才是可消费能力。

这避免“两个 Agent 都写了一个差不多的助手函数”，也避免口头依赖。

### 8.3 合并冲突的处理顺序

- 先判断是否越过 reservation；越界改动直接拆出或拒绝。
- 再判断是否重复能力 owner；优先复用或扩展。
- 最后才做机械合并。

不能用覆盖文件、强推或“最后提交者获胜”解决语义冲突。

## 9. Drive 与数据库大文件协议

ChatGPT 对话不能把大数据库直接交给 Git 时，Drive 只是字节运输层，不是版本权威。

### 9.1 下载

- 从主分支数据平面记录读取当前 generation、Drive file id、文件名、大小、SHA-256 和生产者信息。
- 下载到 worker 私有路径，校验 file id、大小和 SHA-256。
- 每个 worker 使用自己的只读 base 和隔离数据库/副本，绝不多人连接同一个可写文件。

### 9.2 上传候选

- worker 先写上传 intent receipt。
- 产生唯一、不可变的 candidate 名称；禁止覆盖现有对象。
- 上传后记录 Drive file id、大小、SHA-256、base generation、producer workstream 和 outcome receipt。
- 失败重试前先按 intent/outcome 和对象身份检查，不能盲目再传一份。

### 9.3 提升当前代际

只有协调员的 `global_serial` 通道可以：

1. 校验候选和它的 base generation；
2. 运行需要的迁移/合并与验证；
3. 用 compare-and-swap 确认主分支指针仍是预期 base；
4. 在 Git 更新唯一 current-generation 指针并通过 CI。

Drive 的“最新修改时间”、共享文件覆盖和 last-upload-wins 都不能决定当前数据库。

## 10. 行业知识递归榨取与自我精进

### 10.1 复现初代锂电 Agent 的核心，不复制它的固定答案

应继承的是工作法：先宽后深、按正交维度找盲区、每次用新结果重建下一探针、保存不确定性、让反例和负空间参与停止判断。不能把锂电目录直接当成所有行业的本体。

每个行业都需要一张自己的探索地图。地图表达“哪里探过、哪里仍未知、下一步为何值得”，不是宣称真实世界已经完整。

### 10.2 稀疏地图

热地图保持：

- 当前 campaign 阶段；
- 有界的开放 frontier；
- 最多八个近期 seal 相关结果；
- 已知负空间和高风险缺口；
- 恰好一个确定性的 `next_probe`；
- 指向冷原始输出/收据的引用，不复制它们全文。

开放 frontier 上限为 64。不要建立“每年 × 每子行业 × 每角色”的密集笛卡尔积来制造伪完成度。

### 10.3 每轮如何递归

1. 从地图选信息增益最高的一个 frontier。
2. 固定允许输入和禁止输入，执行一次盲探针。
3. 保存原始输出，不用后来搜索把它改写得更漂亮。
4. 对新颖度、重复度、覆盖缺口和负空间做诚实分类。
5. 向地图加入少量真正新 frontier，合并重复项，仍只选一个下一探针。
6. 产生行业成果，并且最多记录一个方法观察。
7. 进行纵向对齐：这一步是否仍推进工作流、全局短期和中期目标；若否就停。

### 10.4 什么时候停，什么时候 seal

“感觉懂了”“目录都写了”“连续几次输出很长”都不能 seal。最低条件包括：

- 阶段已经是 `seal_candidate`，不是 `orientation_only`；
- 最近至少三个相互正交的 pass family 都是低新颖度；
- 明确检查负空间；
- 独立挑战者没有找到重大开放缺口；
- 没有近期高新颖度结果；
- 盲探针没有被新搜索结果污染；
- 精确 artifact 的 seal decision 能重新计算为 green。

任何一个条件不满足就保持 unsealed。`reviewed-no-specific-memory` 只表示模型记忆覆盖状态，不表示真实世界不存在该事件。

### 10.5 Agent 还能不能自我精进

可以，但分两层：

- campaign-local：行业 Agent 可以调整自己的激活方式、探针排序和术语桥接，并在每轮收据里最多留一个方法观察。
- shared：只有同一改进在至少两个独立行业重复、且不破坏 Memory/Evidence 边界时，才由协调员通过 `CAP-0006` 评估共享扩展。

这样既不会把初代方法冻结成教条，也不会让每个新 Agent 都另起炉灶。

## 11. 银行与航运旧错误数据的简洁屏蔽

原则：保留原字节用于 provenance；当前状态只认精确更正、supersession、当前地图和 cursor；旧错误不得进入 Evidence。

| 行业 | 旧问题 | 当前处理 | 新 Agent 规则 |
| --- | --- | --- | --- |
| 银行 | 旧 Markdown 文本曾把 orientation 写成 saturation/seal；它本来就不是结构化 seal | `legacy-prose-state-correction-v1.json` 和 correction/verification 已把它解释为冷历史；当前地图仍为 `orientation_only` | 不把旧 prose seal 当 seal，不从旧 Batch0/其他 shard/Evidence 恢复；只从当前地图执行一个 probe |
| 航运 | `atlas.json#saturation` 与 pandemic `blind-orientation.json#seal` 曾过早结构化 seal | 两份旧 artifact 保持原字节，两份 `seal-supersession-v1.json` 以精确 SHA-256 重新打开；seal audit 已验证两项、零错误 | 不删除或改写旧 artifact，不把它们当有效 seal/Evidence；只从当前地图继续，保持两个 shard unsealed |

这比物理删除安全：删除会破坏“当时发生过错误、后来怎样纠正”的审计链。只有发现更正的精确摘要不匹配或当前地图重新指向旧 seal，才需要再改数据；否则不新增第二套屏蔽清单。

## 12. L1—L4 与用户升级

- `L1`：局部实现、文档或测试，不改变能力语义。
- `L2`：在现有能力 owner 和 Baseline 内扩展/治理，保持兼容。
- `L3`：修改 Baseline 级契约、跨域核心语义、主数据权威或不可轻易回滚的架构选择。
- `L4`：改变项目使命、核心认识论、安全边界，或造成重大不可逆外部影响。

遇到 `L3/L4` 时，Agent 停止需要改变地基的部分，但可以继续安全的只读核查。向用户只讲六件事：

1. 发生了什么；
2. 为什么它碰到地基；
3. 不改会怎样；
4. 改了有什么风险；
5. Agent 的建议；
6. 需要用户明确决定哪一项。

不要只抛术语或让用户读 diff 猜影响。

## 13. 轻量但高信号的验收

治理测试不追求脆弱的字数、提示词逐字匹配、固定 lead 数、固定本体大小或 25 分钟计时。每次按改动风险选择最小集合：

1. capability registry 与 Architecture Baseline 校验；
2. worker continuity audit：必须得到预期的 `CLEAN / RECOVERY_REQUIRED / BLOCKED`；
3. workstream boundary/registry 测试；
4. memory campaign 与 exact-artifact seal audit（涉及研究状态时）；
5. data-plane 测试（涉及数据库/Drive 时）；
6. 精确提交对应的远端 CI；
7. 至少一次 Fresh-Agent 从提示词 + 远端状态恢复六层目标和下一步，不给旧聊天。

审阅重点是四个问题：新 Agent 会不会越权写入、会不会漏补 `H`、会不会把 Memory 当 Evidence、会不会因为历史变长而加载越来越多内容。

## 14. 当前三个角色的替换方式

当前三个长期角色不变，只把三个旧 Agent 实例全部停止，然后分别在新窗口粘贴：

- `docs/development/prompts/coordinator-fresh-agent.md`
- `docs/development/prompts/banking-fresh-agent.md`
- `docs/development/prompts/shipping-fresh-agent.md`

建议启动顺序：协调员先只读刷新并确认两条 worker 都可接班；银行和航运随后并行启动。若三者几乎同时启动也安全，因为两个行业各写自己的分支，协调员不跨写行业分支。

当新 Agent 报告 `CLEAN` 和恢复出的六层目标后，才算接班成功。旧 Agent 不再继续写入。

## 15. 防止治理随开发年限爆炸

长期规模增长只能发生在冷层，不能发生在默认启动上下文：

- 每个活动 worker 始终一个 cursor、一个当前地图、一个下一步。
- 全局 handoff 只路由少量活动/集成通道，不镜像每个行业历史。
- 完成的工作流关闭 reservation，只留短 completion receipt。
- 原始研究、旧收据和旧地图 append-only 留在 Git/Drive，按线索查。
- 方法观察每轮最多一个；共享方法只在跨行业重复后升级。
- 临时探针和挑战者完成即退出，不形成无限管理树。

因此项目可以积累很多年，但一个新 Agent 的启动成本仍接近常数：读固定核心、一个 reservation、一个 cursor、一张地图，再做一个下一步。

## 16. 规范入口

- 总体开发操作系统：`docs/development/longcycle-development-operating-system.md`
- 并行 Agent：`docs/development/parallel-agent-development.md`
- 远端 worker 中断恢复：`docs/development/remote-worker-continuity.md`
- reservation / integration：`docs/development/workstream-reservation-integration.md`
- Drive 与数据库：`docs/development/parallel-data-plane.md`
- 全局会话交接：`docs/development/session-handoff-protocol.md`
- 行业探索地图：`docs/research/industry-memory-exploration-map.md`
- L3/L4：`docs/development/l3-l4-user-escalation.md`
- Fresh-Agent 最小入口：`FRESH_AGENT_BOOTSTRAP.md`
