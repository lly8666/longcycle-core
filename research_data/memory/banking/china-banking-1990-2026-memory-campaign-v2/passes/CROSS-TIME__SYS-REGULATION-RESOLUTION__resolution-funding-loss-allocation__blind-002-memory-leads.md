# CROSS-TIME SYS-REGULATION-RESOLUTION funding/loss-allocation blind-002

- Campaign: `banking-china-1990-2026-v2`
- Probe family: `loss_bearer_vs_funding_role_blind_challenge`
- Model vintage: `GPT-5.6 Sol`
- Authority: `MEMORY_LEADS_ONLY`
- Source visibility: none
- Allowed-input digest: `exploration-map.json@553af17d688b43e5c2b7df61a05ee28ab5d80004;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- Fresh Banking search: no
- Banking Evidence/source material: no
- Batch0 raw: no
- Prior v2 raw: no
- Other-shard raw: no
- Database/Drive: no
- Preexposure carveout: honored.

All entries are unsourced memory leads. This pass deliberately avoids exact transaction amounts, legal ordering, creditor thresholds, recovery rates and named-case fund-flow claims.

## Ultimate loss bearer versus funding role

1. **[useful_refinement][high] Liquidity advance is a balance-sheet claim before it is a loss:** an emergency loan or relending exposure can be repaid, collateralized, refinanced or transferred; initial cash outflow is not evidence of final provider loss.
2. **[useful_refinement][high] Net public cost requires recovery accounting:** final fiscal/fund cost should conceptually equal support paid or value transferred minus repayments, recoveries, collateral proceeds, sale proceeds and other returned value, not the headline gross facility size.
3. **[useful_refinement][high] Guarantee capacity is contingent:** an announced guarantee/backstop ceiling creates risk-bearing capacity but no realized cash loss until drawn or economically crystallized.
4. **[new_category][high] Guarantee loss bearer versus guarantor identity:** a guarantor may pay first and later have recourse against the bank, shareholders, collateral or another public entity; the first payer and final loss bearer can differ.
5. **[new_category][high] Recovery-right holder as a required loss-allocation field:** whoever legally/economically owns recoveries after an advance or asset transfer determines whether initial support becomes subsidy, recoverable financing or shared loss.
6. **[useful_refinement][high] Capital injection can still be an investment:** new public/shareholder equity is at risk and may later recover value; amount injected is not automatically a realized fiscal loss.
7. **[new_category][high] Old-shareholder write-down versus new-investor risk:** incumbent equity can absorb historical losses while a new investor provides fresh capital for future operations. These are two separate economic allocations.
8. **[useful_refinement][high] Dilution is not the same as cash creditor loss:** existing owners can lose control and economic value through dilution even when no creditor claim is haircut.
9. **[useful_refinement][high] Equity cancellation/write-down versus legal-person exit:** shareholder value can be impaired in a continuing/restructured bank; equity loss does not imply license termination or depositor loss.
10. **[new_category][high] Capital-instrument conversion/write-down state:** AT1/T2 or other capital-like instruments may bear loss differently from common equity and senior liabilities. Exact PRC contractual/legal treatment must be verified case by case.
11. **[useful_refinement][high] Capital instrument is not generic wholesale debt:** regulatory capital claims need a separate claimant class from senior interbank funding, negotiable instruments and ordinary corporate deposits.
12. **[new_category][high] Senior unsecured wholesale loss as its own state:** institutional or wholesale claims can potentially be impaired, transferred or delayed without implying the same treatment for insured/ordinary retail deposits.
13. **[useful_refinement][high] Interbank claim treatment is distinct from depositor treatment:** system-contagion management can motivate special handling of interbank/financial-institution claims; exact policy thresholds cannot be guessed blind.
14. **[useful_refinement][high] Corporate deposit versus household deposit:** even both called `deposits`, claimant size, legal status and protection mechanics may differ; one outcome must not be generalized to the other.
15. **[new_category][medium] Operational continuity versus economic protection:** customers can retain uninterrupted account access through transfer/assumption even while a fund, successor, shareholder or other creditor absorbs economic loss elsewhere.
16. **[useful_refinement][high] Deposit transfer cost is not statutory insurance payout:** a successor can assume deposits with accompanying assets, cash, guarantees or support; depositor continuity alone does not identify the source or legal character of support.
17. **[new_category][high] Deposit-insurance fund recoverable support versus fund loss:** if a safety-net fund advances resources or supports a transfer and later obtains recoveries, gross deployment and eventual fund loss must be separate fields.
18. **[useful_refinement][high] Insurance payout versus subrogation/recovery:** after reimbursing protected claimants, a safety-net institution may acquire recovery rights against the failed estate or transferred assets; exact PRC mechanics remain source dependent.
19. **[useful_refinement][medium] Payout timing versus final cost:** fast depositor reimbursement can precede years of asset recovery; early cash protection does not establish final net loss.
20. **[new_category][high] Asset-sale discount crystallizes seller loss:** when impaired assets are sold below carrying value, part of the economic loss may be recognized by the selling bank/shareholders before the purchaser bears future recovery risk.
21. **[useful_refinement][medium] AMC purchase price and recovery loss are separate:** an AMC may later gain or lose relative to purchase price; its final result cannot be inferred from the seller's write-down.
22. **[useful_refinement][high] Transfer consideration can redistribute loss:** price paid for assets or liabilities affects who crystallizes losses at transfer, but exact valuation conventions require Evidence.
23. **[new_category][medium] Asset guarantee / loss-sharing arrangement:** an asset purchaser or successor may receive guarantees, put-backs, loss-sharing or other protection in some restructurings; internal memory is generic here, so only the category should be retained blind.
24. **[useful_refinement][high] Successor capitalization is separate from transaction price:** capital placed into a new/successor bank supports its solvency; consideration for transferred assets/liabilities determines transaction exchange. Combining them obscures both funding and loss allocation.
25. **[useful_refinement][medium] Successor can receive good assets plus protected liabilities while bad assets remain elsewhere:** the entity carrying customer obligations and the entity bearing impaired-asset recovery risk may differ.
26. **[new_category][high] Residual estate/vehicle as ultimate loss-bearing location:** after transfers, losses can remain in a residual legal entity, liquidation estate, AMC or special-purpose disposal vehicle rather than in the successor bank.
27. **[useful_refinement][high] Public support can shift rather than eliminate losses:** recapitalization, guarantees or asset purchases can move risk from private owners/creditors to public balance sheets without determining the eventual net loss before recoveries are known.
28. **[useful_refinement][medium] Local-versus-central public burden is a separate dimension:** local fiscal entities, central-bank balance sheet, deposit-insurance resources and central fiscal/stability mechanisms should not be merged into one `state bailout` bucket.
29. **[useful_refinement][medium] Time horizon matters for loss recognition:** intervention-day funding, restructuring-date valuation and final liquidation/recovery outcome can imply different apparent loss bearers at different vintages.
30. **[useful_refinement][high] A full case record needs both flow and stock views:** record cash/asset flows at intervention plus end-state claims/recoveries; either view alone can misidentify who ultimately bore loss.
31. **[useful_refinement][medium] Blind memory does not support a generic PRC statutory bail-in waterfall:** do not infer a routine EU-style creditor bail-in sequence from the existence of differentiated claimant treatment; exact ordering is an Evidence question.

## Explicit duplicates / false-positive controls

32. **[duplicate][medium] Gross facility amount is not net public loss.**
33. **[duplicate][medium] Deposit-insurance membership is not proof of payout or fund loss.**
34. **[duplicate][medium] Delisting or ownership change is not claimant loss allocation.**
35. **[duplicate][medium] Ordinary NPL sale is not automatically a resolution loss-sharing transaction.**
36. **[duplicate][medium] System-wide PBOC liquidity is not institution-specific resolution loss.**
37. **[duplicate][medium] Foreign `bail-in`, `bridge bank` or `purchase-and-assumption` vocabulary must not be treated as period-native PRC legal terminology without sources.**
38. **[duplicate][medium] Customer account continuity is not proof that the transaction imposed zero cost on funds, shareholders, creditors or public entities.**

## Probe outcome

- Total leads: **38**.
- New categories: **10**.
- Useful refinements: **21**.
- Duplicates: **7**.
- Novel/refining: **31**.
- High-importance novel/refining: **23**.
- Classification: `material_but_narrowing_novelty_with_final_loss_bearer_and_recoverability_separation`.
- The funding mechanism gap now has broad plus orthogonal blind coverage: actor/channel and gross-support roles are separated from ultimate loss bearer, recovery rights and claimant-specific outcomes.
- I do not recover another comparably large blind category from this bounded challenge. Remaining exact ordering, prices, recoveries and named-case allocations are source-detail questions.
- Because this pass still contains material refinements/new categories, it is **not** a low-novelty confirmation and cannot begin the manifest's three-pass low-novelty streak.
- The next blind step should be a deliberately bounded low-novelty confirmation that records only genuinely new categories/refinements and otherwise marks duplicates rather than inventing novelty.

No new campaign-local method observation is introduced; the invocation-level observation remains `saturation_requires_mechanism_coverage_not_just_state_classifier_stability`.
