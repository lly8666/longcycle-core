# CMB Judgment candidate — 2023-08-28 NIM / deposit-cost outlook

- status: `CONTENT_VERIFIED_SOURCE_IDENTIFIABLE`
- evidence_class: `MANAGEMENT_RECORD_JUDGMENT_CANDIDATE`
- active_scope: `PRC_DOMESTIC_BANKING_ONLY`
- subject: `招商银行`
- cycle_ref: `research_data/memory/banking/cmb-deposit-termization-nim-compression-cycle-memory-v1.md`
- memory_vintage_ref: `banking-china-orientation-v1`
- outcome_attached: `false`

## Claim

在 2023 年 8 月 28 日招商银行中期业绩交流会上，管理层对当时净息差与存款成本的判断可保守概括为：

1. 2023 年上半年招行净息差已经明显承压，负债端的一个重要结构因素是活期占比下降、定期占比上升；季度间存款成本仍在上升，定活比变化在招行更明显。
2. 管理层判断接下来 NIM 管控压力仍然较大，理由包括 LPR 下调仍可能继续、存量房贷利率调整大概率实施等资产端压力。
3. 同时管理层认为存在缓冲因素，其中包括商业银行在存款利率市场化机制下继续下调存款利率，以及利率自律机制约束过低贷款定价。
4. 对当期存款成本上升，管理层解释主要来自零售端及存款结构变化，并称部分成本上升属于为支持零售客群/AUM而有计划、有预算的产品供给，而非无序追求存款增长。

以上属于 **2023-08-28 当时的 management Judgment / explanation**，不是后来 NIM 实际结果，也没有使用 2024 年或之后的 Outcome 去修正其含义。

## Claim-scoped content verification

### A. Source identity / event identity

内容文件标题为《招商银行 2023 年中期业绩交流会——问答环节实录（根据录音整理）》。文件载明：

- 会议时间：2023-08-28 09:30–11:45（北京时间）；
- 会议方式：现场 + 视频会议；
- 招行出席管理层包括王良、朱江涛、钟德胜、王颖、彭家文等；
- 外部参会人员为境内外投资者、分析师；
- 记录人为“招商银行董事会办公室投资者关系管理团队”。

招商银行官方 Investor Relations 的 Events & Webcasts 页面同时列有 `Information of 2023 interim results conference` 及对应 `Press Release`，用于确认该场官方中期业绩交流活动的存在。

### B. Relevant content locations in the transcript

内容核验点：

- transcript P15–P16：管理层说明上半年 NIM 2.23%，并把息差收窄拆为结构与定价因素；负债端明确提到活期占比下降、定期占比上升，招行表现更明显。
- transcript P17：管理层说明二季度与一季度之间存款成本仍在上升，定活比变化更明显。
- transcript P18–P20：管理层进一步解释上半年存款成本上升主要来自零售端，定活比变化是主要原因之一；部分零售存款成本上升属于预算内、有计划的产品供给。
- transcript P20：管理层对下一步 NIM 给出前瞻判断，认为管控压力仍大，并把 LPR、存量房贷利率调整列为压力，同时把存款利率继续下调和自律机制约束列为正面因素。

本记录只保存 claim-relevant paraphrase，不复制大段原文。

## Source facts

### Source 1 — official CMB event index

- publisher: `招商银行 / China Merchants Bank`
- page: `Events & Webcasts`
- URL: `https://english.cmbchina.com/cmbir/ProductInfo.aspx?id=event`
- relevant listing: `Information of 2023 interim results conference` with `Press Release`
- role: official event existence / source-family confirmation
- claim_content_authority: `insufficient_alone`

### Source 2 — source-identifiable transcript mirror

- document: `招商银行 2023 年中期业绩交流会 问答环节实录（根据录音整理）`
- URL: `https://pdf.dfcfw.com/pdf/H2_AN202311161611024954_1.pdf`
- internal source identity: `招商银行董事会办公室投资者关系管理团队`
- meeting date: `2023-08-28`
- role: claim content verification
- source status: `SOURCE_IDENTIFIABLE_MANAGEMENT_RECORD_MIRROR`
- exact official-hosted transcript URL: `UNRESOLVED`

The official event index plus the internally identified transcript make this claim usable as a bounded source-identifiable management record. It is **not** yet marked `OFFICIAL_HOST_PRIMARY_FILE_VERIFIED` because the exact CMB-hosted transcript file URL has not been resolved.

## PIT / known-time treatment

- effective/event time: `2023-08-28 09:30–11:45 Asia/Shanghai`
- earliest possible known time: during the live management conference as statements were made; exact minute for this answer is unresolved.
- conservative attendee-known time: `2023-08-28 11:45 Asia/Shanghai` (by the end of the conference, attendees had been exposed to the statements).
- exact official web-publication time for the full transcript: `UNRESOLVED`
- public-market-wide adoption rule: **do not** use 2023-08-28 11:45 as a universal public-web known time unless the webcast/public dissemination path is separately verified; it is currently valid only as a conservative conference-attendee known-time boundary.
- system adoption time: the timestamp of the Longcycle artifact/commit that introduces this record.

This distinction prevents an attendee information set from being silently upgraded into a universal market information set.

## Evidence boundary

- This record is post-seal and therefore does not modify the sealed Memory vintage.
- The Memory packet did not supply the claim; it supplied only the search lead.
- Search snippets and secondary commentary were used for discovery only and are not promoted as authority.
- Later realized NIM, deposit-cost or 2024+ management commentary is not attached here as Outcome.
- Exact official-host transcript resolution remains an explicit open item rather than being guessed.

## Verification result

`PASS_WITH_BOUNDED_SOURCE_STATUS`

One dated management NIM/deposit-cost Judgment is content-verified from a source-identifiable management record, its source identity and conservative known-time are preserved, and later Outcome has not been backdated into the contemporaneous view.
