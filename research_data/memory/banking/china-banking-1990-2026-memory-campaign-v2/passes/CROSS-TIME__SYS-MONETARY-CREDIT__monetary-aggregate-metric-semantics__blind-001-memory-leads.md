# CROSS-TIME / SYS-MONETARY-CREDIT / monetary-aggregate metric semantics / blind-001

**Authority:** `MEMORY_LEADS_ONLY`  
**Campaign:** `banking-china-1990-2026-v2`  
**Model vintage:** `GPT-5.6 Sol`  
**Period:** `1990-01-01` through `2026-08-31`  
**Allowed-input digest:** `exploration-map.json@2dce031b1cb44dcd366990e95e3e13e84f72dd57;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This isolated pass used only rev56 compact map, the manifest and model internal memory. It did not read Batch0 raw, prior v2 raw, sealed `SYS-REGULATION-RESOLUTION` raw, other-shard raw, Banking Evidence/source material, or fresh Banking search results. Directly overlapping CMB 2023-08-28 recollection is not counted as fresh novelty; this frontier does not depend on that preexposure.

Exact historical definition dates, official component formulas and statistical notices are intentionally **not asserted** here. Several definition-change fragments are medium/low-confidence search leads for later Evidence work after a valid seal.

## Memory leads

1. **M0 is not “all central-bank money”.** `M0 / 流通中货币` should be treated as a currency-in-circulation statistical object, distinct from banks' reserve balances and the broader monetary base/reserve-money concept. Verify whether vault cash treatment differs from ordinary public circulation in period-native tables.  
   Classification: `new_category` · Importance: high · Confidence: medium-high.

2. **Historical M1 was a transaction-money perimeter, not a timeless label.** Older-period Chinese M1 memory centers on M0 plus demand/current deposits of enterprise or institutional units; the precise unit-sector wording changed over time and should not be normalized silently.  
   Classification: `new_category` · Importance: high · Confidence: medium.

3. **Recent M1 definition expansion is a major PIT breakpoint.** Strong memory says the recent-period official M1 definition was broadened to capture household/personal demand deposits and payment-platform-related customer reserve balances that older M1 did not fully represent. Exact effective date, backcast policy and component wording require Evidence later.  
   Classification: `new_category` · Importance: high · Confidence: medium-high.

4. **Old-M1 and revised-M1 must coexist in point-in-time replay.** A 2023 or earlier analyst's observed M1 should not be silently replaced by a later reconstructed series using a newer definition. Store definition vintage separately from the observation value and any later backcast.  
   Classification: `new_category` · Importance: high · Confidence: high.

5. **M2 is a broad-money perimeter whose deposit components changed with the financial system.** The stable conceptual core is transaction money plus less-liquid deposit/quasi-money components, but exact sector/product inclusion cannot be assumed constant from the early 1990s to the 2020s.  
   Classification: `new_category` · Importance: high · Confidence: high.

6. **`准货币` / “quasi-money” is a period-native search key.** Older statistical and analytical vocabulary may describe the non-M1 portion of broad money through `准货币`, `货币和准货币`, savings deposits and time deposits rather than today's preferred narrative.  
   Classification: `new_category` · Importance: medium-high · Confidence: high.

7. **Enterprise/unit demand deposits versus household demand deposits are not interchangeable.** A household shift from cash or time deposit into a current account can have very different measured M1 effects under different definition vintages even if transaction capacity rises similarly.  
   Classification: `new_category` · Importance: high · Confidence: high.

8. **Deposit termization can mechanically widen an M1–M2 gap.** Moving balances from demand/current deposits into time deposits may suppress narrow money while leaving broad money roughly unchanged, so a falling M1/M2 relationship need not mean an equivalent contraction of total nominal liquidity.  
   Classification: `useful_refinement` · Importance: high · Confidence: high.

9. **The famous `M1-M2剪刀差` is a vintage-sensitive interpretation, not a timeless signal.** It was often used as a proxy for enterprise cash activation or activity versus saving preference, but its meaning depends on who is included in M1, deposit pricing, housing/wealth allocation and payment technology.  
   Classification: `new_category` · Importance: high · Confidence: high.

10. **Electronic/mobile payments weaken naive M0 interpretation.** Falling cash intensity can occur while transaction activity expands, so cross-decade M0 growth is partly a payments-technology signal rather than a pure monetary-stance measure.  
    Classification: `new_category` · Importance: high · Confidence: high.

11. **Digital payments also exposed the old-M1 household omission problem.** When households conduct more transactions from demand accounts or payment balances, an M1 definition focused on unit/enterprise demand deposits can lose representativeness even before the official definition changes.  
    Classification: `new_category` · Importance: high · Confidence: medium-high.

12. **Securities-market customer margin deposits appear to have triggered historical M2 statistical reconsideration.** Memory suggests early-2000s financial-market development led to at least one adjustment involving securities-company/client-margin balances. Treat this as a search lead only; exact inclusion mechanism and date are uncertain.  
    Classification: `new_category` · Importance: medium-high · Confidence: low-medium.

13. **Non-bank financial institution deposits are a recurring perimeter trap.** Deposits held by securities, fund, trust, insurance or other non-deposit-taking financial institutions at banks may be treated differently from nonfinancial-sector money holdings; exact classification changed or was refined over time.  
    Classification: `new_category` · Importance: high · Confidence: medium.

14. **Interbank deposits must be separated from broad money to avoid double counting.** One bank's deposit at another bank is funding within the deposit-taking system, not automatically a new nonfinancial-sector money balance. Period-native `同业存款`, `非银存款` and other institutional labels should not be collapsed.  
    Classification: `new_category` · Importance: high · Confidence: high.

15. **Government/fiscal deposits create a money-versus-reserves boundary.** Fiscal balances can drain or release banking-system reserves as taxes and spending move, while general-government/fiscal deposits need not belong to the same broad-money holder perimeter as household/corporate deposits. Exact statistical treatment requires later verification.  
    Classification: `useful_refinement` · Importance: high · Confidence: medium-high.

16. **Bank-reported deposit totals do not equal M2.** Total RMB deposits, customer deposits, fiscal deposits, interbank deposits, non-bank-financial deposits and broad-money components use different sector/instrument boundaries. Comparing a bank-industry deposit growth series directly with M2 can therefore be semantically wrong.  
    Classification: `new_category` · Importance: high · Confidence: high.

17. **`基础货币 / 储备货币` and M0 are distinct vocabularies.** Reserve/base money includes central-bank liabilities supporting bank settlement/reserves as well as currency, whereas M0 is the narrow cash-in-circulation object. A rising monetary base can coexist with weak broad-money transmission.  
    Classification: `useful_refinement` · Importance: high · Confidence: high.

18. **The `货币乘数` should be stored as a ratio/diagnostic, not a fixed causal coefficient.** Reserve requirements, excess reserves, cash/deposit preference, bank capital/liquidity constraints and credit demand all change the mapping from base money to M2.  
    Classification: `new_category` · Importance: high · Confidence: high.

19. **M2/GDP is structurally influenced by China's bank-centric intermediation and saving behavior.** A high or rising ratio can reflect financial deepening, deposit accumulation and financing structure, not simply a loose monetary stance. Cross-country or cross-decade interpretation needs perimeter and structure controls.  
    Classification: `new_category` · Importance: high · Confidence: high.

20. **Money-growth policy targets and actual definitions are separate objects.** Some historical policy vintages emphasized a target or expected growth rate for M2 or money supply; that contemporaneous target, the then-current definition and the later revised/backcast series must remain separate in replay. Exact targets and years are Evidence questions.  
    Classification: `new_category` · Importance: high · Confidence: medium-high.

21. **M2 and TSF answer different questions.** M2 is principally a money-holder/liability-side stock perimeter; TSF is financing to the real economy with flow/stock and instrument-perimeter issues. Government bonds, entrusted/trust loans, undiscounted acceptances or equity can affect TSF without mapping one-for-one into M2.  
    Classification: `duplicate` · Importance: high · Confidence: high. This boundary is already represented in compact TSF coverage and is retained only to prevent frontier drift.

22. **Loan growth and M2 growth are related but not an identity.** Bank lending can create deposits, but fiscal flows, loan repayment/write-off, securities purchases, FX transactions, non-bank financing and shifts among deposit sectors/products can make credit and money diverge.  
    Classification: `useful_refinement` · Importance: high · Confidence: high.

23. **NCDs are a holder-dependent perimeter problem.** Negotiable certificates of deposit are bank funding instruments, but whether a specific holding should be thought of as broad money depends on holder sector and statistical classification; `NCD funding growth` is not automatically `deposit/M2 growth`.  
    Classification: `useful_refinement` · Importance: medium-high · Confidence: medium.

24. **Money-market funds and WMP migration can change measured money without an equivalent change in household wealth or credit.** Movement from bank deposits into fund/WMP claims can reduce or reclassify deposit-based aggregates; memory also suggests official M2 treatment of some money-market-fund/non-bank balances was refined at some point. Exact rules are uncertain and need Evidence.  
    Classification: `new_category` · Importance: high · Confidence: medium-low for exact historical adjustment, high for the mechanism.

25. **Foreign-currency deposits and RMB-only versus broader currency scope need an explicit boundary.** Historical banking statistics may publish RMB money supply, RMB/FX deposit tables or combined financing objects with different currency scopes. Never assume a similarly named deposit aggregate is directly comparable to M2.  
    Classification: `useful_refinement` · Importance: medium · Confidence: medium.

26. **Seasonality/base effects can masquerade as semantic change.** Spring Festival cash demand, tax/payment dates, fiscal spending and prior-year base effects can move M0/M1/M2 growth rates even when the structural definition is unchanged; monthly headline interpretation needs stock/flow and seasonal context.  
    Classification: `new_category` · Importance: medium-high · Confidence: high.

27. **Revision/backcast provenance is itself a first-class metric semantic.** When an aggregate definition changes and history is reconstructed, Longcycle should preserve the value/definition an observer actually saw at the time alongside any later backcast. Current downloadable historical series must not overwrite old-release knowledge-time values.  
    Classification: `new_category` · Importance: high · Confidence: high.

## Cross-time search vocabulary / later Evidence keys

`M0`, `M1`, `M2`, `货币供应量`, `广义货币`, `狭义货币`, `流通中货币`, `货币和准货币`, `准货币`, `基础货币`, `储备货币`, `货币乘数`, `单位活期存款`, `单位定期存款`, `个人活期存款`, `储蓄存款`, `财政性存款`, `同业存款`, `非银行业金融机构存款`, `证券客户保证金`, `支付机构客户备付金`, `存款性公司概览`, `其他存款性公司`, `M1-M2剪刀差`.

Several labels above are candidate period-native keys rather than asserted timeless categories; Evidence should verify exact official wording and vintage.

## Negative space after this pass

This broad metric-semantics pass materially closes the gap at the category level but leaves an independent orthogonal challenge necessary. The strongest unresolved questions are: which sector/product boundary changes genuinely altered M1/M2 definitions; how old-release versus backcast series should be represented; how securities-margin/non-bank/MMF/payment-institution balances were treated at different vintages; and how to separate true economic signal shifts from statistical reclassification.

No material antecedent before 1990 was identified. No seal, Evidence transition or truth promotion is permitted from this pass.
