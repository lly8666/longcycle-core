# SYS-MONETARY-CREDIT low-novelty confirmation A — blind-001

- campaign_id: `banking-china-1990-2026-v2`
- workstream_id: `banking-domain-v1`
- shard_id: `SYS-MONETARY-CREDIT`
- model_vintage: `GPT-5.6 Sol`
- period: `1990-01-01` through `2026-08-31`
- family: `policy_regime_instrument_transmission_low_novelty_confirmation`
- authority: `MEMORY_LEADS_ONLY`
- source_visibility: `none`
- one_pass_cannot_self_seal: `true`
- allowed_input_digest_ordered:
  1. `research_data/memory/banking/china-banking-1990-2026-memory-campaign-v2/exploration-map.json@62184df0b22ea87310fbceb1a9b7f9374eb7718d`
  2. `research_data/memory/banking/china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- forbidden inputs were not used: saturation-review raw/control artifact, prior v2 raw/review/challenger outputs, Batch0 raw, sealed regulation-resolution raw, other-shard raw, Banking Evidence/source material, fresh Banking search.
- CMB 2023-08-28 directly overlapping recollection is excluded from novelty credit under the manifest carveout.

## Independent bounded recall

The purpose of this pass is not to reconstruct the prior raw atlas. It re-attacks the compact policy-regime / instrument / transmission coverage from internal memory and classifies each recollection against the current compact map.

1. **duplicate** — Early-1990s monetary control plausibly depended heavily on credit plans / loan-scale controls, administrative interest rates, central-bank relending and other quantity-oriented controls rather than a single market policy rate.
2. **duplicate** — The late-1990s transition away from direct loan quotas did not imply disappearance of administrative guidance; aggregate targets, window guidance and bank balance-sheet constraints could coexist with emerging indirect tools.
3. **duplicate** — Reserve requirements are not interchangeable with settlement balances or excess reserves; their transmission depends on how required and usable liquidity interact with bank funding and payment needs.
4. **useful_refinement** — A reserve-requirement cut should not be interpreted as a fixed mechanical increase in lendable funds. Its dominant transmission carrier can change with excess-reserve conditions, market funding stress, loan demand, capital/risk constraints and bank risk appetite: in some regimes the effect is more about usable liquidity or funding-cost/liquidity confidence than a binding quantity multiplier. This refines heterogeneous transmission rather than opening a new category.
5. **duplicate** — FX intervention / foreign-exchange-position changes can create or drain domestic base liquidity, making sterilization and autonomous-liquidity accounting necessary for reading stance.
6. **duplicate** — Central-bank bills, repo/reverse-repo style open-market operations and later term facilities belong to different maturity/counterparty/collateral layers even when all affect liquidity.
7. **duplicate** — Shibor, repo rates, central-bank operation rates, administered benchmark rates, LPR quotations and realized bank loan rates are distinct price objects; quotation/reference does not equal transaction rate or operating target.
8. **duplicate** — The first-generation LPR and the post-2019 LPR framework should not be treated as one unchanged instrument; the later framework altered the loan-pricing transmission chain and must remain vintage-aware.
9. **duplicate** — SLF/MLF/PSL and targeted relending/rediscount-type facilities differ by term, access, collateral/eligibility and policy purpose; exact historical design is Evidence work rather than a new blind ontology category.
10. **duplicate** — Macroprudential constraints such as differentiated reserve treatment / later MPA-type controls can move in a different dimension from aggregate monetary easing or tightening, so a one-dimensional stance label can mislead.
11. **duplicate** — Bank transmission is heterogeneous: capital, NPL burden, deposit/funding costs, wholesale-market access, internal FTP, risk appetite and borrower quality can block or redirect an apparently accommodative central-bank action.
12. **duplicate** — Crisis or weak-demand periods can exhibit easier policy settings alongside reluctant bank lending or weak borrower demand; policy action and realized credit creation are separate states.
13. **duplicate** — Monetary aggregates such as M0/M1/M2 require definition-vintage and holder-sector discipline; the same label or growth rate need not have identical signal content across decades.
14. **duplicate** — Government-bond issuance, fiscal-deposit movements and FX flows can change reserve conditions independently of headline policy operations and therefore belong in liquidity-plumbing interpretation.
15. **duplicate** — Structural support tools may redirect marginal credit toward selected sectors while aggregate policy is neutral or restrictive; structural and aggregate policy vectors should not be collapsed.
16. **duplicate** — Borrower outcomes such as mortgage/corporate/SME credit pricing and volume sit downstream of central-bank signals and bank balance-sheet transmission; they cannot be read directly from an instrument announcement.

## Measured novelty

- new_category: **0**
- useful_refinement: **1**
- duplicate: **15**
- novel_or_refining: **1**
- high_importance_novel_or_refining: **1**
- material_omitted_category_found: **false**
- material_missing_antecedent_found: **false**
- pre_1990_horizon_extension_required: **false**

## Stop / qualification assessment

This bounded confirmation did not recover a new category-level frontier. The one useful refinement tightens interpretation of RRR transmission under heterogeneous reserve/funding/demand conditions but fits the already-covered regime/instrument/transmission ontology. The pass therefore qualifies as one low-novelty confirmation candidate, subject to the campaign's canonical recomputation and subsequent orthogonal confirmations. It does **not** seal the shard, enable Evidence, or promote any recollection to historical truth.
