# SYS-MONETARY-CREDIT low-novelty confirmation B — blind-001

- campaign_id: `banking-china-1990-2026-v2`
- workstream_id: `banking-domain-v1`
- shard_id: `SYS-MONETARY-CREDIT`
- model_vintage: `GPT-5.6 Sol`
- period: `1990-01-01` through `2026-08-31`
- family: `funding_reserve_balance_sheet_low_novelty_confirmation`
- authority: `MEMORY_LEADS_ONLY`
- source_visibility: `none`
- one_pass_cannot_self_seal: `true`
- allowed_input_digest_ordered:
  1. `research_data/memory/banking/china-banking-1990-2026-memory-campaign-v2/exploration-map.json@61dbfa0384748a053228fcefe6e68cab47a71dfb`
  2. `research_data/memory/banking/china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- forbidden inputs were not used: confirmation-A raw/receipt, saturation-review artifact, prior v2 raw/review/challenger outputs, Batch0 raw, sealed regulation-resolution raw, other-shard raw, Banking Evidence/source material, fresh Banking search.
- CMB 2023-08-28 directly overlapping recollection is excluded from novelty credit.

## Independent bounded funding/reserve/balance-sheet recall

1. **duplicate** — Required reserves, excess reserves and payment/settlement balances should not be treated as one interchangeable stock; regulatory immobilization, settlement use and discretionary liquidity are different balance-sheet states.
2. **duplicate** — A reserve-requirement change can alter both usable liquidity and bank funding economics, while realized lending still depends on demand, capital, asset quality and risk appetite.
3. **duplicate** — Foreign-exchange purchases or sales can inject or drain domestic base liquidity; sterilization operations can offset gross FX-driven reserve changes.
4. **useful_refinement** — Fiscal cash-flow timing can create large intra-period reserve swings even when a monthly or quarterly net fiscal position looks similar. Tax payments or government-bond settlement can first move bank reserves into fiscal deposits, while subsequent government spending returns reserves to banks. Interpreting money-market conditions from only a period-end fiscal balance can therefore miss the actual reserve path. This refines autonomous-liquidity plumbing rather than opening a new category.
5. **duplicate** — Central-bank bill issuance, repo/reverse-repo operations and term lending facilities affect liquidity through different asset exchanges, maturities and rollover profiles; gross operation size is not automatically net reserve injection.
6. **duplicate** — Repayment or replacement of maturing central-bank funding can offset a headline liquidity injection; gross RRR release or facility provision should be separated from simultaneous drains when reading net conditions.
7. **duplicate** — Repo funding is collateralized while unsecured interbank funding is not; rates from these venues can diverge because counterparty and collateral risks differ.
8. **duplicate** — Central-bank facility access can depend on eligible counterparties, collateral and operational frictions, so the announced facility rate is not identical to universal bank funding availability.
9. **duplicate** — Interbank negotiable certificates of deposit are wholesale bank liabilities and are economically distinct from customer certificates/deposits; funding segmentation can therefore change monetary transmission across bank types.
10. **duplicate** — Large banks, small banks, rural institutions and policy banks can face different funding access and liquidity constraints; aggregate reserve abundance does not imply identical marginal funding conditions.
11. **duplicate** — Deposit repricing, termization and realized deposit beta influence bank marginal funding cost and internal transfer pricing, shaping whether policy-rate changes reach loan pricing.
12. **duplicate** — Bank capital, provisioning/NPL pressure and internal risk limits can bind even when reserves are ample; reserve sufficiency is not the same constraint as balance-sheet capacity to extend risky credit.
13. **duplicate** — Policy-bank funding and central-bank or fiscal support channels should not be collapsed into ordinary deposit-bank reserve mechanics; the actor and balance-sheet route determine who bears funding and credit risk.
14. **duplicate** — Central-bank profit remittance or other fiscal-central-bank transfers can reach banking-system liquidity through fiscal-account movements rather than being equivalent to asset-purchase-style monetary expansion.
15. **duplicate** — Government-bond issuance can drain reserves around settlement and later spending can re-inject them; government-bond inclusion in broad financing aggregates does not by itself imply the same bank-loan or reserve impulse.
16. **duplicate** — Collateral scarcity, maturity mismatch and wholesale-funding tiering can turn a system-wide liquidity operation into heterogeneous bank-level transmission rather than a uniform balance-sheet response.

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

The pass found no new category-level frontier. The sole useful refinement concerns timing inside fiscal-to-reserve plumbing and fits the map's autonomous-liquidity / balance-sheet semantics. The pass therefore qualifies as the second consecutive low-novelty confirmation candidate from a family orthogonal to confirmation A, subject to canonical recomputation. It does not seal the shard, enable Evidence or promote any recollection to historical truth.
