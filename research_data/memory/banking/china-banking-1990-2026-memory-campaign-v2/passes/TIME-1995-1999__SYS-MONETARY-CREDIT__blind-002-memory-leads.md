# MEMORY LEADS ONLY — China Banking 1995–1999 / SYS-MONETARY-CREDIT / blind-002

- campaign_id: `banking-china-1990-2026-v2`
- probe_id: `TIME-1995-1999__SYS-MONETARY-CREDIT__blind-002`
- family: `time_slice_orthogonal_blind_recall`
- model_vintage: `GPT-5.6 Sol`
- period: `1995-01-01` through `1999-12-31`
- authority: `MEMORY_LEADS_ONLY`
- source_visibility: `none`
- fresh_search_used: `false`
- banking_evidence_used: `false`
- prior_v2_raw_used: `false`
- allowed_input_digest: `exploration-map.json@b16d46d93d6ef1d827e48157ac2b6bb83af58988;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This pass uses only the compact rev40 coverage statement, the manifest and internal model memory. It does not inspect the broad 1995–1999 raw output. All items remain unsourced search leads.

## Orthogonal leads and challenges

### MC-O9599-001 — Required reserve, excess reserve and payment balances need three-way vintage reconstruction
- lead_kind: metric_semantics
- claim_scope: Late-1990s reserve reform should not be represented by a single RRR field; statutory reserve, usable excess reserve and settlement/payment balances may have different account, remuneration and liquidity meanings.
- approximate_period: 1995–1999
- possible_actors: PBOC, commercial banks
- period_vocabulary_search_keys: `法定存款准备金`, `超额准备金`, `备付金`, `准备金存款`, `支付清算`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- semantic_guard: A lower statutory ratio does not identify the amount of freely lendable liquidity without the other reserve-account states.

### MC-O9599-002 — Reserve remuneration may have altered the opportunity cost of holding central-bank balances
- lead_kind: long_tail_instrument_semantics
- claim_scope: Interest paid or not paid on different reserve balances could materially affect banks' desired liquidity holdings and the transmission of a reserve reform.
- approximate_period: 1995–1999
- possible_actors: PBOC, banks
- period_vocabulary_search_keys: `准备金存款利率`, `超额准备金利率`, `备付金利率`, `存款准备金付息`
- memory_confidence: low-medium
- importance: medium-high
- novelty: new_category
- searchability: medium-high
- uncertainty: Preserve as a search lead only; exact remuneration regime is not recalled confidently.

### MC-O9599-003 — Monetary-aggregate target misses may reflect classification/financial-deepening effects, not only policy failure
- lead_kind: metric_semantics / counterexample
- claim_scope: Changes in deposit composition, quasi-money and new financial channels could move M1/M2 differently from bank credit or nominal activity, complicating interpretation of aggregate target misses.
- approximate_period: 1995–1999
- possible_actors: PBOC statistics/monetary-policy functions, banks, households and firms
- period_vocabulary_search_keys: `准货币`, `定期存款`, `货币供应量`, `M1 M2`, `货币流通速度`, `金融深化`
- memory_confidence: medium
- importance: high
- novelty: useful_refinement
- searchability: high
- semantic_guard: Separate definition change, portfolio shift, target miss and transmission failure.

### MC-O9599-004 — Open-market operations depended on eligible securities, counterparties and settlement capacity
- lead_kind: market_plumbing / implementation_limit
- claim_scope: Early OMO effectiveness depended on the stock and liquidity of government/policy-bank securities, which institutions could trade with PBOC, and whether repo/outright settlement infrastructure could support repeated operations.
- approximate_period: later 1990s
- possible_actors: PBOC, commercial banks, policy banks, interbank settlement/trading infrastructure
- period_vocabulary_search_keys: `公开市场业务一级交易商`, `国债`, `政策性金融债`, `回购`, `现券`, `结算`
- memory_confidence: medium
- importance: high
- novelty: new_category
- searchability: high
- caution: The remembered term `一级交易商` may have later-vintage formalization; verify period-native counterpart labels.

### MC-O9599-005 — Outright purchases/sales and repo-like OMO should be separate state types
- lead_kind: instrument_semantics_refinement
- claim_scope: A central-bank bond transaction can alter liquidity with different duration/counterparty implications depending on whether it is an outright trade or a repo/reverse-repo style transaction.
- approximate_period: 1995–1999
- period_vocabulary_search_keys: `现券买卖`, `回购`, `逆回购`, `公开市场业务`
- memory_confidence: medium
- importance: medium-high
- novelty: useful_refinement
- searchability: high
- anachronism_guard: Do not assume today's transaction names or maturities were already standardized.

### MC-O9599-006 — Commercial-bill authenticity and market depth may have constrained rediscount transmission
- lead_kind: failure_dead_end / market_plumbing
- claim_scope: Rediscount policy required genuine trade bills, bank acceptance/discount activity and reliable bill circulation; weak standardization or non-trade financing could limit its usefulness as a clean monetary instrument.
- approximate_period: 1995–1999
- possible_actors: PBOC, commercial banks, enterprises, bill-market participants
- period_vocabulary_search_keys: `商业汇票`, `银行承兑汇票`, `票据贴现`, `再贴现`, `票据市场`, `真实贸易背景`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high

### MC-O9599-007 — Bank exit from or restriction in exchange bond trading may be part of the interbank-bond-market origin story
- lead_kind: market_structure / uncertain_fragment
- claim_scope: A late-1990s regulatory/market-structure change may have shifted commercial-bank bond activity away from stock exchanges and into a separate interbank bond market, creating durable market segmentation.
- approximate_period: later 1990s
- possible_actors: PBOC, commercial banks, securities exchanges, bond-market infrastructure
- period_vocabulary_search_keys: `商业银行退出交易所`, `银行间债券市场`, `交易所债券`, `国债交易`
- memory_confidence: medium
- importance: high
- novelty: new_category
- searchability: high
- uncertainty: Exact cause, date and rule must be sourced; do not assert that the change was a direct response to one specific speculation episode.

### MC-O9599-008 — Interbank funding rates were market signals but not yet universal monetary-policy prices
- lead_kind: price_semantics / counterexample
- claim_scope: An interbank rate could reveal marginal wholesale liquidity conditions while official deposit/lending prices, relending terms and credit guidance remained separately administered.
- approximate_period: 1995–1999
- possible_actors: banks, non-bank market participants, PBOC
- period_vocabulary_search_keys: `同业拆借利率`, `银行间利率`, `资金价格`, `法定存贷款利率`
- memory_confidence: high
- importance: high
- novelty: useful_refinement
- searchability: high
- counterexample_guard: Do not call the interbank rate “the policy rate” merely because it was market-determined.

### MC-O9599-009 — Cancellation of loan limits changed the binding constraint from quota to a bundle of balance-sheet and approval gates
- lead_kind: mechanism_semantics
- claim_scope: After direct loan ceilings receded, realized credit could still be constrained by bank risk appetite, branch authorization, asset-liability ratios, borrower quality, funding and qualitative guidance.
- approximate_period: late 1990s
- possible_actors: PBOC, bank headquarters/branches, borrowers
- period_vocabulary_search_keys: `取消贷款限额`, `资产负债比例管理`, `授权授信`, `贷款责任制`, `信贷指导`
- memory_confidence: high
- importance: high
- novelty: useful_refinement
- searchability: high

### MC-O9599-010 — “惜贷” must be decomposed into lender reluctance, weak eligible demand and borrower deleveraging
- lead_kind: transmission_failure_semantics
- claim_scope: The period label `惜贷` may mix several mechanisms: banks avoiding risky loans, firms lacking profitable projects/qualifying collateral, SOE restructuring, and households/private firms not demanding credit on the expected terms.
- approximate_period: 1998–1999 especially
- possible_actors: state commercial banks, SOEs, private/SME borrowers, households, PBOC
- period_vocabulary_search_keys: `惜贷`, `有效信贷需求不足`, `贷款难`, `信贷需求`, `贷款风险`
- memory_confidence: high
- importance: high
- novelty: new_category
- searchability: high
- outcome_guard: Do not infer supply rationing from weak aggregate lending alone.

### MC-O9599-011 — Private/SME credit access may be a revealing counterexample to aggregate easing
- lead_kind: long_tail_transmission / counterexample
- claim_scope: Aggregate monetary easing could coexist with persistent financing difficulty for private or smaller firms if bank incentives favored larger/state borrowers or collateralized lending.
- approximate_period: late 1990s
- possible_actors: state commercial banks, urban/rural financial institutions, private/SME firms
- period_vocabulary_search_keys: `中小企业贷款难`, `民营企业融资`, `信贷结构`, `所有制歧视`, `商业银行信贷`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- cross_shard_guard: Borrower/business detail belongs partly in ASSET-CORPORATE-SME; retain here as monetary-transmission heterogeneity.

### MC-O9599-012 — Postal savings may have been a non-bank household-liability channel affecting banking-system liquidity
- lead_kind: forgotten_actor / long_tail_liquidity
- claim_scope: Postal savings gathered household deposits under an arrangement in which funds may have been redeposited with or otherwise centralized through the central bank rather than intermediated like an ordinary commercial bank, affecting regional/banking liquidity flows.
- approximate_period: 1995–1999
- possible_actors: postal savings system, PBOC, households, commercial banks
- period_vocabulary_search_keys: `邮政储蓄`, `邮政储蓄转存款`, `转存人民银行`, `邮储资金`
- memory_confidence: medium
- importance: medium-high
- novelty: new_category
- searchability: high
- uncertainty: Exact transfer/deposit arrangement and remuneration need Evidence.

### MC-O9599-013 — Rural/cooperative relending may have transmitted policy differently from large-bank easing
- lead_kind: forgotten_actor / targeted_liquidity
- claim_scope: PBOC funding to rural credit cooperatives or agriculture-related channels could operate under different objectives and balance-sheet constraints from liquidity supplied to major commercial banks.
- approximate_period: 1995–1999
- possible_actors: PBOC branches, rural credit cooperatives, Agricultural Development Bank/Agricultural Bank where relevant
- period_vocabulary_search_keys: `农村信用社再贷款`, `支农再贷款`, `农村金融`, `中央银行贷款`
- memory_confidence: medium
- importance: medium-high
- novelty: useful_refinement
- searchability: high
- caution: Exact facility names may be later formalizations.

### MC-O9599-014 — Central-bank lending to a stressed institution is not automatically aggregate monetary easing
- lead_kind: counterexample / instrument_state
- claim_scope: Liquidity or rescue-like central-bank credit to a particular institution may support payment/financial stability without representing a broad easing impulse to ordinary bank lending.
- approximate_period: 1995–1999
- possible_actors: PBOC, stressed financial institutions
- period_vocabulary_search_keys: `再贷款`, `金融机构风险处置`, `流动性支持`, `中央银行贷款`
- memory_confidence: high
- importance: high
- novelty: useful_refinement
- searchability: medium-high
- boundary_guard: Do not import named failure cases from the sealed regulation shard into this blind pass.

### MC-O9599-015 — Interest-rate bands/floating permissions could matter even while benchmark rates remained administered
- lead_kind: price_semantics
- claim_scope: Banks may have had bounded discretion around official lending-rate categories, so “administered rates” should not be represented as a single invariant price with zero bank-level variation.
- approximate_period: 1995–1999
- possible_actors: PBOC, commercial banks, borrowers
- period_vocabulary_search_keys: `贷款利率浮动`, `利率浮动幅度`, `基准利率`, `优惠利率`
- memory_confidence: medium
- importance: high
- novelty: useful_refinement
- searchability: high
- uncertainty: Exact permitted bands and borrower categories require Evidence.

### MC-O9599-016 — Consumer/housing-credit encouragement may have become a transmission channel during demand support
- lead_kind: transmission_channel / long_tail
- claim_scope: Late-1990s policy efforts to expand domestic demand may have encouraged housing/consumer credit, creating a household channel distinct from traditional SOE/working-capital lending.
- approximate_period: late 1990s
- possible_actors: PBOC, commercial banks, households, housing-system reform actors
- period_vocabulary_search_keys: `住房消费信贷`, `个人住房贷款`, `消费信贷`, `扩大内需`
- memory_confidence: medium-high
- importance: high
- novelty: new_category
- searchability: high
- cross_shard_guard: Product-level mortgage history belongs in ASSET-MORTGAGE-RETAIL; retain here only the policy-transmission channel.

### MC-O9599-017 — Direct-control retreat, market infrastructure growth and weak transmission are duplicate compact-map anchors
- lead_kind: duplicate_anchor
- claim_scope: The slice is a transition toward indirect instruments without a fully market-based transmission mechanism.
- approximate_period: 1995–1999
- memory_confidence: high
- importance: high
- novelty: duplicate

### MC-O9599-018 — Asian-crisis/deflation context is a duplicate macro anchor
- lead_kind: duplicate_anchor
- claim_scope: External regional stress and domestic weak demand/deflation jointly shaped the late-1990s policy mix.
- approximate_period: 1997–1999
- memory_confidence: high
- importance: high
- novelty: duplicate

### MC-O9599-019 — Surviving qualitative credit guidance after loan-limit retreat is a duplicate institutional anchor
- lead_kind: duplicate_anchor
- claim_scope: Administrative influence continued even as mandatory quantity limits lost centrality.
- approximate_period: late 1990s
- memory_confidence: high
- importance: high
- novelty: duplicate

## Negative space / orthogonal conclusions

- Do not encode reserve reform as only “RRR down”; preserve required/excess/payment-reserve account distinctions and possible remuneration effects.
- Do not treat an early interbank rate as a universal policy rate.
- Do not infer OMO effectiveness from the existence of an announced operation; eligible securities, counterparties and settlement matter.
- Do not treat rediscount as scalable without reconstructing the underlying bill market.
- Do not equate elimination of loan quotas with elimination of authorization, risk, asset-liability or guidance constraints.
- Do not use `惜贷` as a single-cause label; separate credit supply, eligible demand and borrower behavior.
- Do not infer broad easing from institution-specific central-bank support.
- Do not collapse fiscal infrastructure stimulus, household credit encouragement and ordinary corporate bank lending into one transmission channel.
- Exact launch dates, rates/ratios, formal counterparty systems, bill rules, postal-savings arrangements and policy documents remain future Evidence work only after this shard is sealed.

## Novelty summary

- new_category: 8
- useful_refinement: 8
- duplicate: 3
- total_leads: 19
- high_importance_novel_or_refining: 13
- classification: `high_novelty_orthogonal_transition_slice_with_market_plumbing_and_transmission_heterogeneity`
- material_map_changing_category_found: true
- material_missing_antecedent_found: false

The orthogonal pass materially deepens reserve-account semantics, OMO/bill-market plumbing, loan-limit replacement constraints and heterogeneous credit transmission while adding overlooked postal/rural/household channels. No pre-1990 antecedent is required. The 1995–1999 slice can be marked broad-plus-orthogonal complete for now; the next sparse frontier should advance to 2000–2004 broad monetary-credit recall.