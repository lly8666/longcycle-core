# Research Agent SOP：历史取证与当下持续采集

Research Agent 是 Longcycle 的**证据工程执行器**，不是“搜几个结果交差”的搜索助手，也不是 downloader benchmark。

质量由以下问题决定：

- 是否追到 claim 对应的 upstream/source identity；
- 是否实际读到 claim-relevant 内容；
- 是否保存 source date / locator / provenance；
- 是否区分 Reality 与 contemporaneous Judgment；
- 是否识别转载链和 independence cluster；
- 是否保留失败/不可达路径；
- 是否满足 search depth / stop condition；
- 是否避免 hindsight。

**raw PDF 是否已经下载不是研究质量的默认门槛。**

---

## Part A — Historical Verification

### 1. 先读完整 task packet

至少包括：

```text
lead_id
period
lead_summary
possible actors / aliases
query families
preferred primary sources
claim scope
support / contradiction criteria
minimum search depth
knowledge cutoff
```

不要只读任务标题就开始搜索。

### 2. 拆成最小可证明命题

一个 Memory Lead 往往包含多件事。把它拆成每条都能对应 source ladder 的命题，例如：

```text
是否发生某事件？
谁正式披露？
当时状态/数字是什么？
当时管理层如何判断下一步？
后来 Outcome 与此前 Judgment 是什么关系？
```

### 3. 先写 source ladder

典型梯子：

```text
regulator / exchange / statutory filing
→ company / project-owner direct statement
→ methodological producer / association
→ reputable secondary
→ ordinary secondary / discovery only
```

Authority 最终按 claim scope，不按网站“名气”或 `.pdf` 后缀。

### 4. 使用多类 query family

默认至少覆盖适用的：

- exact entity/title；
- time-bound；
- site/domain-bound；
- document-type；
- old aliases；
- quote fragments；
- reverse citation；
- file/document-number archaeology；
- contradiction-oriented query。

搜索摘要只能用于发现候选。

### 5. 打开 source，检查内容

每个候选要检查：

- publisher/upstream identity；
- title/date/document number；
- original vs repost/redistributor；
- 文中实际说了什么；
- locator/page/section；
- 是否引用其他 source；
- 当前能读到什么、不能读到什么。

### 6. PDF 使用三态，不做 downloader 死循环

```text
locator_verified
→ content_verified
→ materialized
```

#### locator_verified

如果主流官方/监管/issuer/机构站点明确存在 PDF：记录 URL、文件名、title/date/文档号、publisher、verification mode。

如果正文没读到，停止在 locator：

```text
source exists = yes
claim proven = no
raw materialization = pending
```

不要为了把 pending 变绿而创建 GitHub Actions 下载任务。

#### content_verified

如果可信界面已经能实际读取 claim-relevant PDF 内容：保存 claim-scoped excerpt / page / section 或 faithful readable representation，并记录：

```text
source_media_type = application/pdf
source_capture_state = content_verified
raw_source_materialized = false
content_verification_mode
claim_relevant_content_preserved = true
representation digest
```

这已经可以进入 Grounded Evidence。

#### materialized

以后有正常网络的 Agent 可批量补：

```text
recorded URL
→ download raw PDF
→ verify document identity + earlier content
→ raw SHA / size / durable storage locator
→ explicit materialized transition
```

Later raw bytes 若与 earlier content/identity 冲突，fail closed。

### 7. Citation chain / redistributor

看到“据公司公告/监管文件/某数据机构”时继续追 upstream。

若最终从 redistributor 取得完整正式文档，可使用，但必须同时保存：

```text
actual retrieval host
upstream original publisher/document identity
```

多个镜像不算多个独立 source。

### 8. 反向验证

高影响 lead 至少做一次反向查询，例如：

```text
delay / cancel / withdraw / deny / revised / correction
```

允许结果：

```text
supports
contradicts
partial
scope_mismatch
not_found
```

`not_found != false`。

### 9. Minimum search depth

默认：

- >= 6 个明显不同 query families；
- >= 3 类来源；
- 最可能的 primary domain 至少检查一次；
- 有 citation 时至少追一层；
- 高影响 lead 至少一次 reverse query；
- 换词/翻页直到新增结果高度重复。

### 10. Historical stop condition

只有三类正常结束：

#### A. Primary/content verified

找到 claim-scoped primary/authoritative source，并实际读到支持/反驳该 claim 的内容。Raw PDF 可以仍 pending。

#### B. Primary contradicted

匹配 scope 的 authoritative content 明确反驳。

#### C. Exhausted but unresolved

达到 minimum depth 仍只有 locator-only、弱 secondary、blocked/paywalled 或完全未找到。必须保留：

```text
queries attempted
primary domains checked
source locators found
what content remains unread
possible next leads
```

---

## Part B — Current Collection

### 11. 核心目标

今天仍容易读到的资料，未来可能消失、覆盖、付费或失去语境，因此要主动 preserve。

优先保留：

- 法规/公告/正式披露；
- 项目 milestone；
- guidance / forecast / target / risk；
- 原始统计/价格方法；
- 技术/合同/认证/机制变化；
- 高信息量 transcript / IR；
- revision/correction；
- 当时具有代表性的强叙事。

### 12. 固定动作

```text
CHECK WATCHLIST
→ DISCOVER NEW/REVISED DOCUMENTS
→ VERIFY SOURCE IDENTITY
→ PRESERVE READABLE CONTENT OR LOCATOR
→ CLASSIFY ROLE
→ GROUND CLAIMS ONLY FROM ACTUALLY READ CONTENT
→ TRACK REVISION
→ EXPAND SOURCE INVENTORY
→ QUEUE OPTIONAL RAW MATERIALIZATION
```

### 13. 网页

Readable webpage：

```text
interactive read
→ faithful claim-scoped visible text + provenance
→ bounded local DuckDB/SQLite capture DB
→ Drive handoff
```

不为了 HTML 再开 Actions，不要求每页正文进 Git。

### 14. PDF

和 Historical Verification 使用同一个 locator/content/materialized 三态。Current collection 的优先级也是“先别丢信息”，不是“先把所有附件下载齐”。

### 15. Judgment 必须当时保存

管理层、政府、协会、券商等对未来的公开判断，应单独保存：

```text
speaker
said_at / known time
judgment kind
target period
raw expected value/direction
rationale / condition / caveat
source + locator
```

以后不能用 Outcome 覆盖它。

---

## 16. Anti-premature-stop checklist

交工前问：

- primary domain 检查了吗？
- 只看搜索首页了吗？
- citation chain 追了吗？
- old alias 用了吗？
- PDF/附件至少确认 locator/内容状态了吗？
- 是否把“下载失败”误写成“source 不存在”？
- 是否把 locator-only 当 claim Evidence？
- 是否做了 reverse query？
- 是否记录了没找到/没读到的东西？
- 是否因为 downloader/tool friction 偏离了研究主问题？

理想执行状态机：

```text
READ TASK
→ DECOMPOSE CLAIM
→ BUILD SOURCE LADDER
→ RUN QUERY FAMILIES
→ OPEN DOCUMENTS
→ CHASE CITATIONS
→ VERIFY CONTENT / RECORD LOCATOR
→ REVERSE VERIFY
→ PRESERVE
→ RETURN STRUCTURED LOG
```

Agent 的价值是**恢复可审计的历史信息**，不是把下载成功率做高。
