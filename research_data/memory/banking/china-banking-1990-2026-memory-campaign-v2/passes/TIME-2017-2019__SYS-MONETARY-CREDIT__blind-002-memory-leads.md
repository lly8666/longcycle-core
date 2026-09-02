# MEMORY_LEADS_ONLY — TIME-2017-2019 / SYS-MONETARY-CREDIT / blind-002

## Control envelope

- campaign: `banking-china-1990-2026-v2`
- probe: `TIME-2017-2019__SYS-MONETARY-CREDIT__blind-002`
- family: `time_slice_orthogonal_blind_recall`
- period: `2017-01-01` through `2019-12-31`
- authority: `MEMORY_LEADS_ONLY`
- source visibility: none
- prior 2017-2019 blind-001 raw: not read
- fresh Banking search / Banking Evidence / Batch0 raw / any prior v2 raw / sealed regulation-resolution raw / other-shard raw: not used
- database / Drive: not used
- allowed-input digest: `exploration-map.json@9de57bfb30702b396deba01676261ef4d1f2f6dd;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- preexposure carveout: honored

These are memory leads only. Exact dates, rates, ratios, parameter sets, facility rules, quotation-bank rosters, mortgage floors and legal/regulatory wording remain deferred Evidence work.

## Orthogonal challenge leads

### 1. MPA's credit perimeter likely reached beyond ordinary on-balance-sheet loans
**Classification:** new_category  
**Importance:** high

The key orthogonal question is what `广义信贷` meant in each MPA vintage. Memory suggests the macroprudential frame was meant to reduce incentives to shift credit into off-balance-sheet or interbank forms, but the exact inclusion of WMP, entrusted/trust exposures, bond investment or interbank assets changed or is uncertain. Later Evidence must recover parameter vintages rather than impose one final perimeter backward.

### 2. MPA broad-credit growth and Social Financing are not interchangeable aggregates
**Classification:** useful_refinement  
**Importance:** high

MPA is a bank/institution assessment perimeter; TSF is financing to the real economy. They may overlap but answer different questions. A bank can alter assets or interbank positions without a one-for-one TSF effect, and TSF can include financing outside a bank's MPA balance-sheet object. Keep the two schemas separate.

### 3. NCD issuance should be decomposed into liability funding, maturity structure and investor/counterparty distribution
**Classification:** new_category  
**Importance:** high

NCDs were not simply another policy-rate series. They were negotiable wholesale liabilities whose cost and tenor could transmit money-market pressure into bank asset growth. Later research should ask who issued, who held, how maturities clustered and how NCD pricing related to Shibor/repo/MLF without assuming a fixed spread.

### 4. DR007, R007, exchange repo and Shibor represent different market objects
**Classification:** new_category  
**Importance:** high

A period-native rate map should separate depository-institution repo rates, broader interbank repo rates, exchange-market collateralized repo rates and unsecured offered/transaction indicators. Treating all `7-day money-market rates` as one series can erase the very segmentation that deleveraging exposed. Exact naming/vintage needs source verification.

### 5. Collateral and counterparty eligibility can make aggregate liquidity unevenly distributable
**Classification:** new_category  
**Importance:** high

Even when the central bank injects reserves, weaker institutions may face collateral haircuts, counterparty limits or a lack of unsecured lines. This turns the repo/unsecured split and collateral hierarchy into part of monetary transmission. Small-bank stress can therefore coexist with system-wide aggregate liquidity that looks ample.

### 6. Late-period small-bank funding tiering is a refinement of the broader heterogeneity principle
**Classification:** useful_refinement  
**Importance:** high

The new detail is not merely `small banks pay more`; it is that counterparty credit events can reprice NCD, repo collateral acceptance, unsecured lines and rollover risk differently. Keep legal resolution mechanics outside this shard, but preserve the funding-tiering transmission lead.

### 7. RRR cuts require gross-release, MLF-repayment/replacement and net-injection accounting
**Classification:** new_category  
**Importance:** high

A reserve cut can release a large gross amount while part of the effect replaces maturing MLF or other central-bank funding. For monetary analysis the relevant objects include required reserves released, central-bank claims repaid, net reserve addition and duration/cost change. Do not label the gross headline amount as net stimulus without decomposition.

### 8. Targeted/tiered RRR should be modeled as institution-eligibility policy rather than a single system ratio
**Classification:** useful_refinement  
**Importance:** high

Banks may have faced different reserve requirements according to size, inclusive-finance performance or other criteria. This means a single `RRR` field can be misleading. Later Evidence should preserve institution class, qualifying conditions and whether the measure was targeted or broad.

### 9. TMLF and MLF differ by eligibility/intent even if both are medium-term central-bank funding
**Classification:** new_category  
**Importance:** medium-high

The targeted facility appears to have conditioned access or pricing on support for private/small firms, while ordinary MLF was a broader liquidity instrument. Exact tenor, rates and eligible institutions are uncertain. The research point is to separate structural credit incentive from general medium-term liquidity management.

### 10. Relending/rediscounting should preserve intermediary risk-bearing and use-of-funds conditions
**Classification:** new_category  
**Importance:** high

Central-bank relending provides funds to banks; it is not necessarily a central-bank credit decision on the final borrower. A later evidence task should recover whether banks retained credit risk, what loan categories qualified, how pricing incentives worked and whether funds were pre- or post-linked to qualifying loans.

### 11. Private-enterprise credit-risk-mitigation support is not automatically a government guarantee
**Classification:** new_category  
**Importance:** medium-high

Credit-risk mitigation warrants/tools or support facilities around private-enterprise bonds may have absorbed a limited tranche or provided market signaling rather than guaranteeing full principal. Later reconstruction should identify issuer, protection seller, loss-sharing trigger and whether the mechanism primarily improved issuance access or lowered spreads.

### 12. Central-bank bills swap around bank perpetual bonds is a liquidity/collateral mechanism, not obvious capital injection
**Classification:** new_category  
**Importance:** medium-high

The swap-like arrangement appears designed to improve the liquidity or collateral usability of bank perpetual bonds, supporting issuance demand. It should be distinguished from outright central-bank purchase, fiscal recapitalization or free capital. This is an important false-positive guard for monetary-capital support narratives.

### 13. FX, government deposits, tax dates and cash demand remain autonomous reserve factors
**Classification:** useful_refinement  
**Importance:** high

A late-period OMO or MLF operation may offset FX outflow pressure, fiscal deposit movements, tax payments, cash withdrawal or maturity rather than signal a discrete stance change. Reconstruct reserve-supply accounting by autonomous factor and discretionary operation where possible.

### 14. Reformed LPR is a quotation/reference object before it is a realized loan price
**Classification:** new_category  
**Importance:** high

The published LPR is a reference generated from bank quotations under a new mechanism; actual borrowers receive transaction rates with spreads reflecting risk, collateral, capital and competition. A decline in LPR should not be treated as proof that every loan's realized rate fell by the same amount.

### 15. The pre-2019 LPR and reformed LPR need explicit vintage identities
**Classification:** useful_refinement  
**Importance:** high

The same English/Chinese label hides a mechanism break. Historical data should preserve `old LPR quotation regime` versus `2019-reformed LPR`, rather than splice the series as if institutional meaning were unchanged. Exact quotation methodology belongs in Evidence.

### 16. MLF-linked LPR transmission is directional, not a mechanical pricing formula
**Classification:** useful_refinement  
**Importance:** high

MLF provides a policy/funding anchor, but quotation spreads and final loan spreads reflect bank-specific liability cost, liquidity, credit risk, capital and competition. This gives a multi-stage pass-through chain: central-bank funding price → quotation reference → bank internal transfer/pricing → borrower transaction.

### 17. Existing floating-rate loans remained a separate transition population after the 2019 reform
**Classification:** new_category  
**Importance:** high

A point-in-time 2019 view should not assume all legacy loans instantly repriced to the reformed LPR. New loans and old benchmark-linked stock coexisted until a later conversion process. The later mass conversion belongs to 2020-era chronology and must not leak backward.

### 18. Mortgage pricing requires LPR tenor, regulatory floor and fixed add-point state
**Classification:** new_category  
**Importance:** high

Residential mortgage pricing after the reform should be represented as a separate transmission branch. The longer-tenor LPR may serve as a reference, but local/national minimums and fixed add-points can create asymmetric pass-through. Exact floors and start dates are deferred.

### 19. Deposit-rate stickiness can weaken or delay LPR-to-loan repricing
**Classification:** useful_refinement  
**Importance:** high

Banks cannot price assets independently of liabilities. Deposit competition, benchmark/self-discipline conventions and NCD/wholesale costs can keep marginal funding expensive even as policy references decline. Track deposit beta and repricing lags by bank type.

### 20. Shadow-credit contraction changed TSF composition before it necessarily changed total borrower funding one-for-one
**Classification:** new_category  
**Importance:** high

Trust/entrusted/bill/non-standard channels may contract while formal loans, bonds or government-linked financing rise. Later Evidence should preserve component vintages and avoid reading aggregate TSF slowdown as a uniform credit rationing event across all borrowers.

### 21. Counterexample: abundant reserves can coexist with credit contraction in constrained channels
**Classification:** duplicate  
**Importance:** medium

This repeats a cross-period mechanism already covered: reserve abundance does not erase capital, risk appetite, collateral, borrower-quality, interbank counterparty or regulatory constraints. It confirms rather than extends the category set.

## Orthogonal negative-space conclusion

- No new institution class, monetary-tool class or material antecedent outside the existing 2017-2019 broad categories is required.
- The orthogonal challenge materially refines operational semantics but does not expose a third same-slice blind frontier that would justify staying in 2017-2019.
- Exact MPA indicators, TSF component lists/vintages, repo-rate prints, facility terms, gross/net RRR amounts, support-tool legal structures, LPR quotation rules, mortgage floors and stock-loan conversion dates remain deferred Evidence/source-detail work.
- Legal details of small-bank resolution remain isolated in the sealed regulation/resolution shard.

## Stop decision

2017-2019 now has broad plus independent orthogonal blind depth. Advance the sparse frontier to a broad 2020-2022 monetary-credit pass rather than over-polishing this slice.