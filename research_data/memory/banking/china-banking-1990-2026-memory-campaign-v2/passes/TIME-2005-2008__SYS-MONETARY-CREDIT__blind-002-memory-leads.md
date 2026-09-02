# China Banking Memory Campaign v2 — TIME-2005-2008 / SYS-MONETARY-CREDIT / blind-002

**Authority:** `MEMORY_LEADS_ONLY`  
**Family:** time-slice orthogonal blind recall  
**Model vintage:** GPT-5.6 Sol  
**Source visibility:** none  
**Prior 2005-2008 broad raw:** not read  
**Batch0/prior v2/sealed regulation-resolution/other-shard raw:** not read  
**Banking Evidence/source material / fresh search:** not used  
**Allowed-input digest:** `exploration-map.json@480431f3d5369eff9066aab68f61b6410b727ee8;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This pass challenges only the compact rev44 coverage statement using model internal memory. It does not verify the broad pass and does not promote recollection to Evidence, Reality, Judgment or Outcome. Exact dates, bands, rates, ratios, document titles and transaction terms remain unresolved.

## Orthogonal omissions and semantic boundaries

### MC-2005-08-O01 — central parity, transaction band and intervention are separate exchange-rate objects
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high as a semantic distinction
- A managed RMB regime should be reconstructed with at least three separate objects: the official daily/reference central parity, the permitted market trading range around it, and actual central-bank/authorized-market intervention.
- A changing central parity does not by itself identify the quantity of intervention or the effective monetary injection.

### MC-2005-08-O02 — FX settlement actors matter for domestic-liquidity transmission
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** medium-high
- Commercial banks handling foreign-exchange settlement and the foreign-exchange administration system sat between exporters/investors and the PBOC balance sheet.
- Changes in settlement/surrender rules can alter how external flows become RMB deposits/reserves even if gross balance-of-payments flows are unchanged.
- Exact rule changes and institutional mandates are source-detail work.

### MC-2005-08-O03 — reserve accumulation, foreign-exchange position and sterilized reserve money must not be conflated
- **Novelty:** useful_refinement
- **Importance:** high
- **Confidence:** high
- `外汇储备`, `外汇占款`, PBOC foreign assets, base/reserve money and bank excess reserves are related but different statistical/accounting objects.
- Sterilization can allow foreign assets to rise while reserve-money growth is partly offset by central-bank liabilities or reserve requirements.

### MC-2005-08-O04 — sterilization had a maturity and carry structure
- **Novelty:** useful_refinement
- **Importance:** high
- **Confidence:** medium-high
- Central-bank bills of different maturities and repeated rollover created a term/carry problem; the relevant cost was not just issuance volume but yield, maturity, rollover frequency and what banks would otherwise hold.
- A higher central-bank-bill yield can both improve absorption and alter bank portfolio incentives.

### MC-2005-08-O05 — reserve-requirement tightening interacted with reserve remuneration
- **Novelty:** useful_refinement
- **Importance:** high
- **Confidence:** medium-high
- Raising required reserves changes the quantity of usable bank liquidity, but its balance-sheet cost also depends on remuneration of required and excess reserves.
- The effective burden therefore differs from a non-interest-bearing reserve tax and can vary across banks with different excess-liquidity positions.

### MC-2005-08-O06 — repeated reserve hikes could create heterogeneous marginal constraints
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high at mechanism level
- Large deposit-rich banks and smaller/fast-growing banks need not experience the same marginal constraint from the same required-reserve increase.
- This is a counterexample to treating the national reserve ratio as a uniform bank-level liquidity shock.

### MC-2005-08-O07 — Shibor fixing is a quotation construct, not the same as transaction-weighted funding cost
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high at semantic level
- Shibor should be stored with fixing methodology/panel/maturity semantics and separated from repo rates and actual bilateral unsecured transactions.
- Its emergence improved the reference-rate vocabulary without making it a direct PBOC administered policy rate.

### MC-2005-08-O08 — repo and unsecured interbank rates represent different collateral/liquidity channels
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high structurally
- Repo funding embeds collateral availability and haircut/market-infrastructure conditions; unsecured interbank quotations embed bank credit and counterparty risk.
- Comparing them can reveal segmentation, but later-period `DR007` policy-framework language should not be projected backward automatically.

### MC-2005-08-O09 — large-bank reform could deepen interbank liquidity asymmetry
- **Novelty:** new_category
- **Importance:** medium-high
- **Confidence:** medium
- Better-capitalized, listed large banks may have become stronger liquidity suppliers and more active market counterparties than smaller institutions.
- Thus monetary operations first reaching large counterparties could transmit unevenly across the banking system.

### MC-2005-08-O10 — directed credit pacing must be separated from formal system-wide loan quotas
- **Novelty:** useful_refinement
- **Importance:** high
- **Confidence:** high as a classification requirement
- `窗口指导`, annual/quarterly loan pacing, sector instructions and any explicit quantitative constraints should be separately classified rather than all called `贷款规模`.
- This distinction is especially important around 2007-2008 when market-oriented banks still faced strong administrative macro-control signals.

### MC-2005-08-O11 — targeted central-bank-bill or liquidity absorption is a distributional instrument
- **Novelty:** useful_refinement
- **Importance:** medium-high
- **Confidence:** medium-low on exact instrument form
- If `定向央票` or similar bank-specific absorption was used, its significance is that liquidity removal could be concentrated on institutions with stronger excess reserves/loan growth rather than system-wide.
- Exact mandatory/auction character and recipient criteria require Evidence.

### MC-2005-08-O12 — special treasury-bond / sovereign-investment-vehicle operations require transaction-chain accounting
- **Novelty:** useful_refinement
- **Importance:** high
- **Confidence:** medium
- The monetary effect of the special treasury-bond/foreign-asset transfer episode depends on who bought the bonds, whether the PBOC held or transacted them, how FX assets were transferred, and which balance-sheet entries were sterilized.
- `Treasury issued bonds` alone is insufficient to infer a liquidity injection or withdrawal.

### MC-2005-08-O13 — inflation composition matters for real-rate and policy-intent interpretation
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high as analytic boundary
- Food/structural price shocks and broader demand inflation need not imply identical monetary responses.
- Real deposit/lending rates should be matched to the relevant inflation concept and time horizon rather than subtracting one headline CPI number mechanically.

### MC-2005-08-O14 — household asset migration can weaken deposit-rate transmission
- **Novelty:** useful_refinement
- **Importance:** medium-high
- **Confidence:** medium-high
- If deposit returns lag inflation or asset-market expectations, households may shift balances toward equities/property/funds, changing bank deposit composition without a proportional change in aggregate household financial saving.
- Deposit migration is therefore a liability-channel mechanism as well as an asset-price story.

### MC-2005-08-O15 — SME/private-borrower credit could tighten more than headline loan growth suggested
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** medium-high
- Administrative tightening, risk-based pricing and bank preference for large/state borrowers may cause smaller/private firms to experience tighter effective credit even while aggregate bank lending remains large.
- This is a transmission-heterogeneity lead; detailed borrower evidence belongs to later asset shards.

### MC-2005-08-O16 — 2008 policy should be represented as multiple knowledge-time states, not one annual switch
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** very high conceptually
- The year likely progressed through tightening/inflation concern, growing external-risk concern, then explicit easing/growth support as the global shock intensified.
- Later replay should preserve announcement/knowledge/effective dates and lagged bank response separately; an annual `2008=easing` label would create lookahead.

### MC-2005-08-O17 — reserve cuts and rate cuts during the reversal need not have identical bank-type effects
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** medium-high
- Reserve reductions release balance-sheet liquidity; benchmark-rate cuts alter borrower pricing and bank margins; relaxation of credit guidance changes quantity constraints. These channels can move at different speeds and affect banks differently.
- A multi-instrument easing package should not be collapsed into one scalar stance variable.

### MC-2005-08-O18 — `社会融资规模` is unsafe as a contemporaneous aggregate for this slice
- **Novelty:** new_category
- **Importance:** high
- **Confidence:** high as a temporal-semantic warning
- The later official `社会融资规模` framework should not be casually back-projected as if 2005-2008 policymakers were already targeting/observing it in its later standardized form.
- Period-native aggregates should center on money, RMB loans and then-available financing indicators; later reconstructed TSF series must be marked as later statistical representation if used.

### MC-2005-08-O19 — broad RMB appreciation/external-liquidity feedback is already present in the compact map
- **Novelty:** duplicate
- **Importance:** medium
- The general category is duplicate; the incremental content is the central-parity/trading-band/intervention and settlement-chain decomposition above.

### MC-2005-08-O20 — broad within-2008 tightening-to-easing reversal is already present in the compact map
- **Novelty:** duplicate
- **Importance:** medium
- The regime reversal itself is duplicate. The incremental requirement is to split it into point-in-time policy states and distinguish reserve, rate and credit-guidance channels.

## Negative-space / counterexample conclusions

- No missing pre-1990 antecedent or new top-level regime requires horizon extension.
- Orthogonal additions materially deepen operating semantics rather than changing the broad regime categories: exchange-rate objects, FX settlement actors, sterilization carry, reserve remuneration/heterogeneity, Shibor fixing, secured/unsecured funding, targeted absorption, transaction-chain fiscal-FX accounting, real-rate semantics, borrower heterogeneity and point-in-time 2008 state transitions.
- Modern `DR007 policy rate`, `MLF/SLF`, `LPR`, `MPA` and contemporaneous `TSF-target` language remain unsafe projections into 2005-2008 unless later Evidence establishes a period-native antecedent.
- With broad plus this orthogonal pass, 2005-2008 is suitable to mark `broad_plus_orthogonal_complete` for now and advance to 2009-2012. This is not saturation or seal of SYS-MONETARY-CREDIT.
- Exact bands, rates, RRR steps, Shibor fixing rules, directed-tool terms, special treasury-bond transaction details and policy-label dates remain future Evidence/source-detail work after a valid shard seal.
