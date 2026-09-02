# MEMORY LEADS ONLY — China Banking 1990–1994 / SYS-MONETARY-CREDIT / blind-002

- campaign_id: `banking-china-1990-2026-v2`
- probe_id: `TIME-1990-1994__SYS-MONETARY-CREDIT__blind-002`
- family: `time_slice_orthogonal_blind_recall`
- model_vintage: `GPT-5.6 Sol`
- period: `1990-01-01` through `1994-12-31`
- authority: `MEMORY_LEADS_ONLY`
- source_visibility: `none`
- fresh_search_used: `false`
- banking_evidence_used: `false`
- prior_v2_raw_used: `false`
- allowed_input_digest: `exploration-map.json@e3132301c89d40fe92f8966888d4e0115453e70c;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This pass uses only the compact rev38 coverage statement, the manifest and internal model memory. It does not inspect blind-001 raw. All items remain unsourced search leads.

## Orthogonal leads and challenges

### MC-O90-001 — Loan-scale accounting itself needs period-specific semantics
- lead_kind: metric_semantics
- claim_scope: `贷款规模` / `信贷规模` may refer to an approved increment, a balance ceiling, a plan allocation, or another administrative control quantity rather than one stable modern metric.
- approximate_period: 1990–1994
- recalled_mechanism: Banks could be described as `规模内` or `超规模`, but the denominator/control object likely varied by plan and institution.
- period_vocabulary_search_keys: `贷款规模`, `信贷规模`, `规模内贷款`, `超规模贷款`, `贷款限额`, `新增贷款`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- semantic_guard: Do not compare a remembered `规模` number across years until the stock/flow/limit meaning is reconstructed.

### MC-O90-002 — Policy-credit exceptions may have made aggregate tightening structurally selective
- lead_kind: mechanism_refinement / counterexample
- claim_scope: Even during aggregate tightening, some policy-priority lending could continue or receive protected funding, so total monetary stance and sectoral credit availability could diverge.
- approximate_period: especially 1993–1994
- possible_actors: State Council, PBOC, specialized banks, priority SOEs/projects
- period_vocabulary_search_keys: `保重点`, `压一般`, `调整信贷结构`, `重点建设`, `政策性贷款`
- memory_confidence: medium-high
- importance: high
- novelty: useful_refinement
- searchability: medium-high

### MC-O90-003 — Grain/cotton/oil procurement finance may be a distinct policy-credit and central-bank-funding channel
- lead_kind: long_tail_institutional_mechanism
- claim_scope: Agricultural procurement finance (`粮棉油收购资金` or similar) likely had special funding and repayment arrangements that were not equivalent to ordinary commercial working-capital credit.
- approximate_period: 1990–1994, with institutional transition around 1994
- possible_actors: Agricultural Bank, PBOC, fiscal authorities, grain/cotton procurement entities; later Agricultural Development Bank
- recalled_mechanism: Seasonal or policy procurement credit could create dedicated central-bank/fiscal funding needs and became a candidate function for policy-bank separation.
- period_vocabulary_search_keys: `粮棉油收购贷款`, `收购资金`, `农副产品收购`, `政策性收购资金`, `农业发展银行`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- boundary_guard: Exact product names, funding shares and transfer timing require Evidence.

### MC-O90-004 — Trust/investment institutions may have been an important off-plan credit leakage channel
- lead_kind: long_tail_actor / failure-dead-end
- claim_scope: Trust and investment companies and other non-bank institutions may have intermediated bank or interbank funds into investment/property/securities channels outside ordinary bank loan-scale controls.
- approximate_period: early 1990s, especially pre/post 1993 rectification
- possible_actors: trust and investment companies, bank-affiliated/local financial institutions, specialized banks, PBOC branches
- period_vocabulary_search_keys: `信托投资公司`, `信托贷款`, `委托贷款`, `金融机构拆借`, `乱集资`, `资金体外循环`
- memory_confidence: medium
- importance: high
- novelty: new_category
- searchability: high
- uncertainty: `委托贷款` and specific vehicles should not be assumed to have one modern legal meaning in this period.

### MC-O90-005 — Preferential/sector-specific loan rates complicate the “administered rate” category
- lead_kind: price_semantics / mechanism
- claim_scope: Administered lending rates may have included term-, sector-, policy- or project-specific preferential rates rather than a single uniform lending price.
- approximate_period: 1990–1994
- possible_actors: PBOC/State Council, specialized banks, policy borrowers, fiscal authorities
- recalled_mechanism: Price allocation could be segmented by official categories, and fiscal interest subsidies may have further separated borrower cost from bank yield.
- period_vocabulary_search_keys: `优惠利率`, `差别利率`, `贷款利率档次`, `贴息贷款`, `财政贴息`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- semantic_guard: Separate posted bank rate, borrower effective cost and any fiscal subsidy.

### MC-O90-006 — M0/M1/M2 labels may have changed definition or official prominence during the transition
- lead_kind: metric_semantics / old_vocabulary
- claim_scope: Monetary-supply statistics were becoming more prominent, but the exact composition and official use of M0/M1/M2 should be reconstructed by vintage rather than assumed stable.
- approximate_period: early-to-mid 1990s
- possible_actors: PBOC statistical/monetary-policy departments
- period_vocabulary_search_keys: `流通中现金`, `货币供应量`, `M0`, `M1`, `M2`, `准货币`
- memory_confidence: medium
- importance: high
- novelty: new_category
- searchability: high
- semantic_guard: Do not backfill current aggregate definitions into earlier data releases.

### MC-O90-007 — Central-bank lending could be differentiated by purpose, not just one generic relending pool
- lead_kind: instrument_semantics
- claim_scope: `中央银行贷款` / `再贷款` likely contained ordinary liquidity support, plan-related funding and special-purpose or sectoral lending with different transmission implications.
- approximate_period: 1990–1994
- possible_actors: PBOC and specialized banks
- period_vocabulary_search_keys: `中央银行贷款`, `专项贷款`, `再贷款`, `支农再贷款`, `流动资金贷款`
- memory_confidence: medium
- importance: high
- novelty: useful_refinement
- searchability: high
- caution: Some later standardized relending names may be anachronistic; verify period-native labels.

### MC-O90-008 — Reserve and settlement balances may have been institutionally/accountingly separate
- lead_kind: metric_semantics_refinement
- claim_scope: Required reserve (`存款准备金`) and payment/settlement reserve (`备付金` or related balances) should be treated as separate candidate states unless period documents prove equivalence.
- approximate_period: 1990–1994
- possible_actors: PBOC, specialized banks
- period_vocabulary_search_keys: `存款准备金`, `备付金`, `结算资金`, `准备金账户`
- memory_confidence: medium-high
- importance: high
- novelty: useful_refinement
- searchability: high

### MC-O90-009 — Cash issuance, credit plan and broad-money monitoring were overlapping but non-identical control planes
- lead_kind: mechanism_refinement / metric_semantics
- claim_scope: `现金投放/回笼`, planned bank credit and monetary aggregates each described different parts of monetary conditions and should not be collapsed into one stance measure.
- approximate_period: 1990–1994
- period_vocabulary_search_keys: `现金投放`, `现金回笼`, `货币发行`, `信贷收支`, `货币供应量`
- memory_confidence: high
- importance: medium-high
- novelty: useful_refinement
- searchability: high

### MC-O90-010 — Interbank “拆借” should not be mapped directly to the later national interbank market
- lead_kind: old_vocabulary / market-structure refinement
- claim_scope: Early-1990s `拆借` could include heterogeneous bilateral/local or institutionally restricted funding relationships; later national market conventions should not be projected backward.
- approximate_period: 1990–1994
- possible_actors: specialized banks, local financial institutions, trust/investment companies, PBOC branches
- period_vocabulary_search_keys: `资金拆借市场`, `同业拆借`, `拆借资金`, `拆借中心`, `融资中心`
- memory_confidence: medium-high
- importance: high
- novelty: useful_refinement
- searchability: high

### MC-O90-011 — Specialized-bank headquarters and local branches were separate implementation layers
- lead_kind: actor_refinement
- claim_scope: A national credit plan could be decomposed through bank headquarters and territorial branches, so transmission depended on both institution type and branch-level allocation/implementation.
- approximate_period: 1990–1994
- possible_actors: specialized-bank headquarters/provincial branches, PBOC head office/branches, local governments
- period_vocabulary_search_keys: `总行信贷计划`, `分行贷款规模`, `人民银行分行`, `信贷资金调度`
- memory_confidence: medium-high
- importance: high
- novelty: useful_refinement
- searchability: medium

### MC-O90-012 — Planning/economic agencies may have influenced credit allocation independently of the PBOC
- lead_kind: forgotten_actor / institutional mechanism
- claim_scope: Project and investment approval by planning/economic authorities could determine which borrowers were eligible or prioritized for bank credit, making monetary transmission a multi-agency process.
- approximate_period: 1990–1994
- possible_actors: State Planning Commission or predecessor planning bodies, State Council, sector ministries, PBOC, specialized banks
- period_vocabulary_search_keys: `计划委员会`, `重点项目`, `投资计划`, `信贷计划衔接`, `基本建设贷款`
- memory_confidence: medium
- importance: medium-high
- novelty: useful_refinement
- searchability: medium
- caution: Exact agency names and authority boundaries changed; preserve as actor-search leads.

### MC-O90-013 — Loan authorization, funding availability and credit-plan quota were separate gates
- lead_kind: mechanism_semantics
- claim_scope: A project or enterprise could be approved for lending yet still face funding or quota constraints; conversely, a quota did not necessarily imply a specific loan would be made.
- approximate_period: 1990–1994
- recalled_mechanism: Administrative allocation involved multiple gates: plan/project eligibility, bank approval, credit-scale availability, central-bank funding and local implementation.
- memory_confidence: high
- importance: high
- novelty: useful_refinement
- searchability: medium

### MC-O90-014 — Tightening could shift credit composition without immediately shrinking aggregate balance-sheet credit
- lead_kind: contemporaneous_intent_vs_outcome / counterexample
- claim_scope: A policy described as tight may have worked through slower increments, structural redirection or withdrawal from speculative uses rather than an immediate fall in outstanding loans.
- approximate_period: 1993–1994
- period_vocabulary_search_keys: `压缩贷款`, `控制增量`, `调整结构`, `清理收回`, `支持重点`
- memory_confidence: medium-high
- importance: high
- novelty: useful_refinement
- searchability: high

### MC-O90-015 — Foreign-exchange and RMB credit channels should be separated at specialized-bank level
- lead_kind: cross-boundary actor_semantics
- claim_scope: Bank of China and other institutions may have had foreign-exchange credit/funding channels with different plan and balance-sheet treatment from ordinary RMB credit, complicating aggregate transmission analysis.
- approximate_period: 1990–1994
- possible_actors: BOC, PBOC/foreign-exchange administration, trade enterprises
- period_vocabulary_search_keys: `外汇贷款`, `外汇信贷计划`, `人民币贷款`, `外汇资金`
- memory_confidence: medium
- importance: medium
- novelty: useful_refinement
- searchability: medium-high
- cross_shard_guard: Detailed FX institutions belong in CROSSBORDER-FX-OFFSHORE.

### MC-O90-016 — Credit-plan dominance is a duplicate of the compact broad map, but remains a core period anchor
- lead_kind: duplicate_anchor
- claim_scope: Quantity/loan-scale administration remained central to monetary control.
- approximate_period: 1990–1994
- memory_confidence: high
- importance: high
- novelty: duplicate

### MC-O90-017 — 1993–1994 financial-order rectification is a duplicate event-mechanism anchor
- lead_kind: duplicate_anchor
- claim_scope: Tightening included administrative discipline and control of alternative funding/leakage channels.
- approximate_period: 1993–1994
- memory_confidence: high
- importance: high
- novelty: duplicate

### MC-O90-018 — Policy-bank creation is a duplicate transition anchor, with no new exact institutional claim added here
- lead_kind: duplicate_anchor
- claim_scope: The 1994-era policy-bank split marks a transition in policy/commercial credit boundaries.
- approximate_period: 1994
- memory_confidence: high
- importance: high
- novelty: duplicate

### MC-O90-019 — Mixed-instrument stance is a duplicate counterexample anchor
- lead_kind: duplicate_anchor
- claim_scope: No single rate/reserve/credit measure is sufficient to characterize stance in this administrative mixed regime.
- approximate_period: 1990–1994
- memory_confidence: high
- importance: high
- novelty: duplicate

## Negative space / orthogonal conclusions

- Do not read `贷款规模` as one timeless statistical field; reconstruct stock/flow/limit semantics by vintage.
- Do not treat `中央银行贷款` as one homogeneous liquidity facility.
- Do not collapse statutory reserve, settlement reserve and other `备付` balances.
- Do not assume all bank credit faced the same administered lending rate or borrower effective cost.
- Do not treat policy-priority procurement/project lending as evidence that aggregate tightening was absent.
- Do not treat trust/interbank/off-plan channels as automatically illegal or speculative; classify the actual institutional form only after Evidence.
- Do not assume M0/M1/M2 definitions or official target status were stable across the slice.
- Do not equate early `拆借` with the later standardized national interbank market.
- Do not infer realized transmission from announced tightening language.

## Novelty summary

- new_category: 5
- useful_refinement: 10
- duplicate: 4
- total_leads: 19
- high_importance_novel_or_refining: 11
- classification: `high_novelty_orthogonal_same_slice_with_material_semantic_refinement`
- material_map_changing_category_found: true
- material_missing_antecedent_found: false

The orthogonal challenge materially deepens instrument/metric semantics and long-tail leakage/policy-credit channels but does not reveal a missing pre-1990 antecedent. The 1990–1994 slice can therefore be marked broad-plus-orthogonal complete for now, while the next sparse blind frontier should advance to the 1995–1999 monetary-credit time slice rather than keep polishing the same period.