# MEMORY_LEADS_ONLY — TIME-2020-2022 / SYS-MONETARY-CREDIT / blind-002

## Control envelope

- campaign: `banking-china-1990-2026-v2`
- probe: `TIME-2020-2022__SYS-MONETARY-CREDIT__blind-002`
- family: `time_slice_orthogonal_blind_recall`
- period: `2020-01-01` through `2022-12-31`
- authority: `MEMORY_LEADS_ONLY`
- source visibility: none
- prior 2020-2022 blind-001 raw: not read
- fresh Banking search / Banking Evidence / Batch0 raw / any prior v2 raw / sealed regulation-resolution raw / other-shard raw: not used
- database / Drive: not used
- allowed-input digest: `exploration-map.json@f0c3ebc13fd79b9589ada74b80282d9079fd936c;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- preexposure carveout: honored

These are memory leads only. Exact dates, rates, ratios, program sizes, conversion deadlines, eligibility tests, deposit formulas, mortgage floors and source/legal wording remain deferred Evidence work.

## Orthogonal challenge leads

### 1. Direct-to-real-economy tools need a three-layer decomposition: PBOC incentive, bank action, borrower obligation
**Classification:** new_category  
**Importance:** high

The phrase `直达实体经济` can misleadingly sound like central-bank lending directly to firms. A robust reconstruction should distinguish the central-bank incentive/funding transaction with a bank, the bank's origination or extension decision, and the borrower's unchanged or modified legal debt obligation. Later Evidence should identify the exact balance-sheet entries for each tool.

### 2. Principal/interest deferral should be separated from maturity extension, renewal, forbearance and loss recognition
**Classification:** useful_refinement  
**Importance:** high

A payment holiday can preserve contractual principal while changing timing. Renewal can replace a maturing loan; forbearance can affect classification; write-off recognizes loss. Pandemic support should not be scored as one binary `relief` state. Exact asset-classification treatment belongs to Evidence and possibly other shards, but the monetary-credit transmission distinction is necessary here.

### 3. Small/micro credit-loan support may have used an incentive tied to qualifying incremental lending rather than wholesale risk purchase
**Classification:** new_category  
**Importance:** high

Memory suggests the central bank rewarded or supported banks that expanded qualifying unsecured small/micro loans, while banks continued to carry borrower credit risk. This should be challenged against any later source wording that resembles `purchase`: accounting form does not automatically imply permanent credit-risk transfer.

### 4. Temporary pandemic tools require explicit successor/expiry states
**Classification:** new_category  
**Importance:** high

Emergency programs can be extended, narrowed, converted into standing inclusive-finance tools or allowed to expire. A time-series ontology should retain `temporary`, `extended`, `converted/succeeded`, `expired`, and `regularized` rather than treating a named tool as continuously active through 2022.

### 5. Relending/rediscount and direct incentive tools are adjacent but not identical mechanisms
**Classification:** useful_refinement  
**Importance:** high

Relending supplies central-bank funds to eligible banks; rediscount involves eligible bills; direct incentive tools may reward qualifying lending behavior after the fact. Their funding, collateral, risk-bearing and timing differ. Later Evidence should avoid merging them because all were aimed at small/micro or epidemic-related credit.

### 6. Legacy floating-rate loan conversion involved an option/state transition, not an automatic universal repricing event
**Classification:** new_category  
**Importance:** high

Borrowers with eligible legacy floating-rate loans appear to have faced a choice or conversion arrangement between an LPR-linked basis and a fixed-rate basis. Preserve election/notification/default-route uncertainty. Do not assume all loans converted on one date or that all borrowers chose the same option.

### 7. Fixed add-point after conversion is distinct from the future LPR reset path
**Classification:** useful_refinement  
**Importance:** high

The converted loan's spread/add-point may be fixed from the conversion basis while the reference LPR resets on a defined cycle. Thus future borrower rates depend on both a reference-rate state and an invariant or separately governed spread. Exact formula, reference month and repricing date require Evidence.

### 8. Repricing cycle/date is a third mortgage state beyond `LPR-linked` and `fixed add-point`
**Classification:** new_category  
**Importance:** high

Two LPR-linked mortgages can react at different times if their repricing dates differ. A point-in-time analysis should capture reference tenor, fixed add-point, and next repricing date/cycle. This becomes especially important when comparing 2022 LPR changes with actual household cash-flow effects.

### 9. OMO, MLF, RRR and LPR span different balance-sheet and price/quantity dimensions
**Classification:** new_category  
**Importance:** high

OMO and MLF alter central-bank funding/reserves with different tenors; RRR changes required reserve demand/longer-term liquidity; LPR is a loan-pricing reference. A single `policy easing` field hides whether the action changes reserve quantity, marginal central-bank funding price, bank reserve opportunity cost or borrower reference pricing.

### 10. Emergency liquidity normalization can occur without withdrawing targeted credit support
**Classification:** new_category  
**Importance:** high

Money-market operations may normalize as panic/liquidity stress recedes while relending, small/micro incentives or structural facilities remain active. This guards against reading a smaller gross liquidity injection as equivalent to a tightening of every credit-support channel.

### 11. `Normal monetary policy` is partly a framework/expectation claim, not an instrument-setting variable
**Classification:** useful_refinement  
**Importance:** medium-high

The phrase can refer to retaining conventional positive-rate space and avoiding extraordinary foreign-style regimes while still easing domestically. It should be stored as contemporaneous policy vocabulary/intent separately from observed MLF/LPR/RRR settings.

### 12. Carbon-reduction support appears to be bank-mediated ex-post funding against qualifying green loans
**Classification:** new_category  
**Importance:** high

The structural mechanism likely involved banks first making eligible carbon-reduction loans and then receiving low-cost central-bank funding for a qualifying share. Key later questions: eligible institutions/projects, verification/disclosure, funding share, rate/tenor and bank risk retention. It is not equivalent to direct PBOC project finance.

### 13. Structural monetary tools create a dual mandate-like transmission layer: aggregate liquidity plus credit composition
**Classification:** new_category  
**Importance:** high

By 2021-2022, the central bank increasingly appears to have used facilities that changed not only total liquidity but the relative funding incentive for green, small/micro, technology or other favored categories. This is a monetary-credit allocation mechanism distinct from a broad rate cut, though exact later categories must remain period-native.

### 14. Deposit self-discipline reform and deposit beta should be represented separately
**Classification:** new_category  
**Importance:** high

One object is the industry/self-discipline pricing ceiling or benchmark convention; another is actual bank deposit repricing behavior. Banks may price below ceilings, use term/deposit-product mix or compete non-price dimensions. A changed formula does not mechanically equal an identical realized funding-cost reduction.

### 15. Deposit term structure can make asset-liability repricing asymmetric
**Classification:** useful_refinement  
**Importance:** high

Even if deposit price ceilings adjust, existing term deposits reprice only at maturity while floating/new loans can respond sooner. This creates lagged NIM effects and different transmission by deposit duration/franchise. Exact bank outcomes belong outside blind recall, but the mechanism is material.

### 16. Longer-tenor LPR, mortgage floor and fixed add-point are three distinct household-pricing layers
**Classification:** new_category  
**Importance:** high

For new mortgages, the LPR reference, regulatory/local floor and negotiated/fixed add-point need separate states. For converted stock mortgages, the add-point may follow a different historical rule. Do not back-project later 2023 stock-mortgage repricing into this 2020-2022 conversion/floor regime.

### 17. Household mortgage easing and developer/project credit easing are different policy channels
**Classification:** new_category  
**Importance:** high

Lower household mortgage pricing may support demand without resolving developer liquidity; project/guaranteed delivery financing can operate through separate bank or policy channels. Property weakness should not be represented as a single credit-price variable.

### 18. PBOC profit remittance should be decomposed through Treasury/fiscal deposits and subsequent reserve creation/use
**Classification:** new_category  
**Importance:** high

The accounting lead is that accumulated central-bank profits transferred to fiscal authorities can change government deposits at the central bank and, when spent, banking-system reserves/deposits. This is different from purchasing new government bonds, direct deficit financing or QE. Exact balance-sheet sequencing needs source confirmation.

### 19. Fiscal spending funded by central-bank profit remittance can add liquidity without being a conventional monetary operation
**Classification:** useful_refinement  
**Importance:** medium-high

This creates a fiscal-monetary interaction in reserve supply: the source of funds and policy authority differ from OMO/MLF/RRR even if later spending raises commercial-bank deposits/reserves. Preserve transaction-chain semantics rather than classify by final liquidity sign alone.

### 20. Policy-bank infrastructure support should preserve funding-source and risk-bearing layers
**Classification:** new_category  
**Importance:** high

Policy banks may fund infrastructure via loans or special instruments with fiscal capital/support, while commercial banks co-finance and the PBOC maintains aggregate liquidity. A later source task should trace each institution's asset/liability and avoid labeling all infrastructure credit as monetary-base expansion.

### 21. FX reserve-requirement or macroprudential FX tools are not substitutes for RMB RRR in measurement
**Classification:** new_category  
**Importance:** high

Foreign-currency reserve requirements affect banks' FX liquidity and potentially FX supply/demand; RMB RRR affects renminbi reserve demand. Similar names can create false equivalence. Exchange-rate policy signals and domestic monetary stance need separate balance-sheet objects.

### 22. TSF government-bond components can dominate flow swings without equivalent private-sector leverage change
**Classification:** useful_refinement  
**Importance:** high

High monthly/annual social-financing flow can reflect front-loaded government bond issuance. Private corporate, household and small/micro credit conditions may move differently. Historical comparison therefore needs period-native component definitions and sectoral decomposition.

### 23. Counterexample: LPR cuts do not guarantee immediate stock-mortgage cash-flow relief
**Classification:** new_category  
**Importance:** high

A stock mortgage's next reset date, tenor reference and fixed add-point can delay or alter pass-through. This is a useful operational counterexample against treating a policy-reference cut as instant household easing.

### 24. Counterexample: structural facility expansion is not proof of broad monetary re-acceleration
**Classification:** duplicate  
**Importance:** medium

This confirms the established quantity/composition distinction: targeted low-cost funding can expand while aggregate policy remains comparatively restrained or normalized. It does not add a new category.

## Orthogonal negative-space conclusion

- No material antecedent before 1990 and no new monetary-tool superclass is exposed.
- The pass materially deepens intermediary-risk, successor-state, repricing-cycle, reserve-accounting and structural-tool semantics but does not reveal a third 2020-2022 frontier requiring another same-slice ordinary blind pass.
- Exact direct-tool accounting, loan-conversion options/deadlines, structural-facility funding shares, deposit ceilings/formulas, mortgage floors/add-points, PBOC profit-remittance accounting entries and policy-bank program terms remain Evidence work.
- Legal resolution and institution-failure details remain isolated from this unsealed shard.

## Stop decision

2020-2022 now has broad plus independent orthogonal blind depth. Advance the sparse frontier to a broad 2023-2026 monetary-credit pass. Do not start that later slice in this four-probe invocation.