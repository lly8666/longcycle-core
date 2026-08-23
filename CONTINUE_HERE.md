# CONTINUE HERE — Longcycle Fresh-Session Bootstrap

Fresh session 不需要重读项目历史，也不要让用户重新解释。

## 固定接力语句

用户只需要说：

> **接管 Longcycle（lly8666/longcycle-core）：按仓库实时 handoff 恢复使命、方法、当前目标和 live 状态，然后从 continuation cursor 继续；不要让我重复背景。**

这句话本身不携带当前任务事实；当前状态必须从仓库恢复。

## Fresh-session 正常流程

1. 先读 GitHub issue #2，只把它当 rendezvous：找到 active PR / branch / handoff 路径，不从 issue 正文推断 live task。
2. 刷新 active PR 的 live HEAD。
3. 读 `STRATEGIC_COMPASS.md` 和 `METHODOLOGY_CORE.md`，先用自己的话重建项目为什么存在、为什么要保存 Reality + contemporaneous Judgment + Outcome、为什么 point-in-time/no-lookahead 是第一性边界、Evidence 与模型记忆如何分工、为什么跨行业 benchmark 只是手段。
4. 再读 `.longcycle/continuity/mission-fidelity.json` 校准。遗漏哪一项，只定向重读对应 Core；不要把 rubric 当答案模板。
5. 读 `.longcycle/handoff/current.json`，获取当前中期目标、短期目标、continuation cursor、active context、ordered actions 与 `.longcycle/handoff/data-plane.json` 路径。
6. 比较 live HEAD 与 `checkpoint_based_on_head_sha`。若不相同，先检查 intervening commits；handoff-only commit 可以在确认无 substantive drift 后继续，不能因为 checkpoint 落后一两个控制面 commit 就要求用户重述背景。
7. 刷新 live CI。checkpoint 内 CI 永远只是 snapshot。
8. 只读 `resume_read_set` 中当前任务需要的文件；`.longcycle/capabilities/active-index.json` 是永久 compact bootstrap 项。不要默认读取旧 devlog、旧行业或全部 raw data。
9. 开始 material capability / product-surface / architecture 开发前，先运行 capability admission/relevant lookup；默认 reuse/extend，不能因为“更干净”新建第二个 semantic owner。
10. 修改已知代码路径前，才用 Repair Memory 做 path-scoped invariant lookup。
11. 只有 cursor 明确需要二进制状态时，才恢复 data-plane 中 `required_for_current_task=true` 的对象。

## Handoff 的两层权威

```text
Git / current.json / receipts / data-plane manifest
    = control plane
    = 使命、状态、任务、source identity、locator、transport、digest、恢复规则

Google Drive / historical GitHub Release / later materialized files
    = development data-plane
    = 不改变 Evidence/source authority，也不替代数据库语义
```

## 1. 网页：优先本地数据库 → Google Drive

对当前 Agent 能完整读取的网页：

```text
读取网页可见内容
→ 忠实保存 claim-scoped visible text + source/provenance metadata
→ 批量写入 bounded local DuckDB/SQLite capture capsule
→ checkpoint / close / SHA-256
→ 上传 Google Drive
→ Git handoff 只保存 Drive file id + SHA + schema/source count + restore instruction
```

规则：

- 不要为了保存网页 HTML 而专门启动 GitHub Actions；
- 不要为了 handoff 把每一页网页正文逐页 commit 到 Git；
- 每条 capture 至少保留原始 URL、publisher/source identity、source-displayed date/title（有可靠支持时）、`captured_at`、truthful `capture_mode`、faithful visible text、文本/记录 digest，以及重要缺失说明；
- capture DB 是 capture/handoff envelope，不是 live PostgreSQL，也不是 Fact/Judgment 自动发布；
- Drive 只是 transport，不能改变 source authority；恢复后仍走正常 archive/Evidence 语义；
- 已经存在的历史 Release source pack 如果含 HTML/web bytes，保持 immutable、继续按旧 receipt 使用，不迁移、不重写。

## 2. PDF：先验证 locator / 内容，raw bytes 延后补全

**以后不要为了下载 PDF 而启动 GitHub Actions。** PDF 下载能力不再是研究主路径的前置门槛。

PDF 使用三个显式状态：

```text
locator_verified
→ content_verified
→ materialized
```

### `locator_verified`

确认：

- publisher/source identity；
- PDF/document identity；
- 原始下载 URL；
- 文件名（能确定时）；
- title/date（source-supported 时）；
- verification time/mode；
- `materialization_status`。

对于主流的官方、监管机构、上市公司/issuer、研究机构等站点上的 PDF，只要 document identity + locator 已确认，就把它当作**真实存在的合法 source document**，不要再为了证明 GitHub runner 能不能下载而消耗研究时间。

但要保留一条 epistemic boundary：**只确认链接存在、完全没读到 claim-relevant 内容，不能拿这个 locator 证明具体 claim。**

### `content_verified`

如果当前 Agent 已经通过可信交互界面实际读到 PDF 相关内容，并能保存 claim-scoped excerpt / page / section / readable representation，那么即使 raw PDF bytes 尚未归档，也可以进入正常 Grounded Evidence。

这里要明确区分：

```text
source 是否说了 X
!=
我们是否已经保存了 byte-identical PDF 文件
```

前者决定 claim 能否 grounding；后者是完整性增强，不再阻塞开发。

主流网站上的 PDF 是否“权威”仍按 claim scope 判断：监管机构对监管状态、issuer 对自身声明、registry 对登记字段等各自有权威范围。**不因为 `.pdf` 后缀或 transport 自动升级 authority。**

### `materialized`

以后有正常网络的 Agent 再做：

```text
按 recorded URL 下载
→ 验证 document identity / 已记录的 claim-relevant 内容
→ 补 raw byte size / SHA-256 / durable storage locator
→ 更新 owning receipt/materialization metadata
```

如果后来下载到的 bytes 与之前 `content_verified` 的内容/身份冲突，fail closed，建立 integrity repair；不能静默覆盖。

已经存在的 GitHub Release PDF/source pack 属于**历史 materialized asset**，可以直接复用，但不再代表未来 PDF 的默认 acquisition 方式。

## 3. 其他生成型状态：Google Drive

Longcycle-generated binary state 放 Google Drive，例如：

- DuckDB replay materialization；
- generated execution / reconciliation output；
- generated database snapshot（如果确实需要）；
- offline runtime pack。

规则：

- manifest 中的 Drive file id + SHA-256 才定义对象；
- DuckDB/replay 默认 read-only；
- generated capsule 不能伪装成原始 Evidence archive；
- 网页 capture capsule 虽然走 Drive，但里面的可见文本是 source-derived capture；
- Drive 是 portable relay，不是 live PostgreSQL authority，也不是终局 archive。

## 4. PostgreSQL 不做 session 搬运

不要把 live PostgreSQL cluster 放 Release 或 Drive 当 session state。需要 transaction / lease / outbox / write semantics 时，在 GitHub Actions 或其他 service-capable runtime 重新建立 PostgreSQL，并走正常写入路径。

注意：**Actions 仍然可以用于 PostgreSQL/runtime execution；禁止的是为了下载新 PDF 而制造 acquisition Actions。**

## 5. Fail closed 的新边界

以下情况 fail closed：

- claim 依赖某个 PDF 内容，但当前只有 locator、从未实际读到 claim-relevant 内容；
- later materialization 与 earlier content/source identity 冲突；
- required webpage/generated capsule 缺失或 digest 不匹配；
- runtime ABI / database integrity gate 失败。

以下情况**不再**构成 blocker：

- raw PDF bytes 尚未下载，但 PDF locator 已确认且 claim-relevant 内容已经 `content_verified`；
- GitHub runner 对某主流 source host 下载失败；
- 当前 Agent 无法上传 GitHub Release。

## 产品成功标准：研究员理解，而不是 Agent 跑分

Longcycle 的 benchmark 用来打脸架构，不是训练 Agent 应试。真正的验收是研究员能否快速获得可辩护的行业心智模型，包括 Reality、当时 Judgment、后来 Outcome、Evidence、争议和未知。

如果自动任务完成率更高，但研究员仍必须自己从 raw documents 重建行业结构，属于产品失败。

## Mission Calibration Gate

开始实质工作前必须能解释：

1. 为什么保存长期、真实、可比较的行业历史比又写一份当前报告更重要？
2. 为什么只保存最终事实会产生 hindsight，必须单独保存 contemporaneous cognition？
3. 为什么 later-known information 不能进入过去的 replay？
4. 为什么模型记忆和搜索只能发现线索，publishable truth 要受 claim-scoped Evidence 控制？
5. 为什么当前行业只是 cross-industry proving ground？
6. 为什么 researcher understanding 比 crawler/Agent/schema/benchmark 指标更接近产品终局？

## Vertical Alignment Gate

开始新的 substantive 子问题、完成 coherent 子任务、准备扩大范围或新结果改变假设时，向上检查：

```text
当前原子任务
↑ 短期里程碑
↑ 中期能力证明
↑ Longcycle 最终使命
```

如果当前任务已经达到 done/stop condition，或者继续投入只是让局部 benchmark 更好看，停止或重排。

## Handoff 更新纪律

完成一个会改变“下一 Agent 应做什么”的 coherent session 后：

```text
完成 substantive work 并 commit
→ 如有新的 resume-relevant binary asset，按正确 transport 保存并验证
→ PDF locator/content verification 即使尚未 materialize，也要写进 owning receipt/control plane
→ 更新 data-plane.json
→ 更新 durable receipt / active context
→ 更新 current.json continuation cursor / workstreams / ordered actions
→ checkpoint_based_on_head_sha 指向最后一个 substantive/control-plane commit
→ commit handoff sync
→ 刷新 live CI（需要时）
→ 用 bounded cold-start rehearsal 验证 fresh Agent 能恢复任务
```

## Core 纪律

- `STRATEGIC_COMPASS.md`：最终使命、真正成功标准、防偏航；
- `METHODOLOGY_CORE.md`：跨行业方法；
- `.longcycle/continuity/mission-fidelity.json`：语义校准问题，不存答案；
- `.longcycle/capabilities/active-index.json`：稳定 capability routing；
- `.longcycle/handoff/current.json`：中短期 live cursor；
- `.longcycle/handoff/data-plane.json`：resume-relevant source/data identity / transport / integrity / restore contract；
- receipts：已完成 benchmark / source / replay / exit 等可审计结果；
- `.longcycle/repair-memory/`：高复发风险 invariant；
- active context：当前行业/任务；
- devlog / old industry：按需追溯，不属于默认启动上下文。

如果任务本身是在修改 handoff 机制，再定向读 `docs/development/session-handoff-protocol.md` 与 `docs/development/continuity-architecture.md`；不要因此预加载整个开发历史。
