# CROSS-TIME__BANK-STATE-OWNED__saturation-review__blind-005 — MEMORY_LEADS_ONLY

- campaign: `banking-china-1990-2026-v2`
- shard: `BANK-STATE-OWNED`
- family: `cross_time_metric_semantics_expectations_counterexample_saturation_blind_recall`
- period: `1990-01-01..2026-08-31`
- authority: `MEMORY_LEADS_ONLY`
- inputs: rev95 compact exploration map + exhaustion manifest + current model internal memory/reasoning only
- fresh Banking search/source/Evidence: **not used**
- completed BANK-STATE-OWNED raw/receipts: **not read**
- truth status: unverified semantic leads; exact accounting-rule dates, formulas, bank definitions and reported values require Evidence.

## Saturation result

This independent semantic/expectation challenge produced useful refinements but **no material new category**. Most recovered issues are measurement lenses on categories already represented by the compact map: asset quality, capital, profitability, customer/franchise, group perimeter, governance and business-model evolution. The pass therefore qualifies as a first low-novelty saturation confirmation rather than reopening a gap.

## A. Scope and denominator semantics

1. `[refinement]` Bank-only versus consolidated-group figures can change assets, revenue, fee income, capital, RWA, impairment and employee/branch productivity interpretations.
2. `[duplicate-pattern]` Group-perimeter changes are already a covered structural category; the semantic challenge adds no new entity class.
3. `[refinement]` Period-end assets/deposits/loans can diverge from average balances and can exaggerate period-end management effects.
4. `[refinement]` Growth calculated from restated versus originally reported comparatives can differ after accounting reclassifications.
5. `[refinement]` ROA/ROE depend on average versus period-end denominators and on whether attributable profit or broader profit concepts are used.
6. `[refinement]` Per-employee or per-branch productivity can change mechanically when staffing or outlet definitions change.
7. `[duplicate-pattern]` Legal-entity versus internal-unit distinctions are already covered by the group-perimeter recovery.

## B. Asset-quality vocabulary

8. `[refinement]` NPL ratio is a stock ratio; it does not directly show new NPL formation, cures, upgrades, write-offs, sales or denominator growth.
9. `[refinement]` NPL balances can fall through disposal/write-off even while underlying borrower stress remains elevated.
10. `[refinement]` Rapid loan growth can dilute an NPL ratio denominator without improving old-vintage asset quality.
11. `[refinement]` Overdue, special-mention, restructured and impaired-loan concepts overlap but are not interchangeable.
12. `[new-minor]` Migration matrices or vintage/cohort views, where available, would be more diagnostic than point-in-time NPL ratios for seasoning risk; this is a measurement refinement, not a new shard category.
13. `[refinement]` Corporate, retail, mortgage, card and geographically segmented NPL ratios have different denominator composition and cannot be compared casually.
14. `[duplicate-pattern]` Loan seasoning and delayed recognition are already covered by primary time-slice work.
15. `[refinement]` “Bad loan disposal” can combine write-offs, recoveries, transfers and restructuring; gross and net economic loss are not equivalent.
16. `[new-minor]` Recoveries on previously written-off assets can affect later profit/credit-cost interpretation and should be separated from current-vintage performance if material.

## C. Provisioning and impairment semantics

17. `[refinement]` Provision coverage is a stock of allowances relative to NPL stock; it is not the same as period credit cost.
18. `[refinement]` Credit cost is a flow concept whose denominator may be average loans or another exposure base; definitions must be pinned bank by bank.
19. `[refinement]` Allowance/NPL coverage can rise because allowances rise, NPLs fall, or both.
20. `[refinement]` Accounting expected-loss approaches can shift recognition timing relative to older incurred-loss-like concepts; exact transition dates and staging rules need Evidence.
21. `[new-minor]` Stage-like impairment buckets, where applicable, may create semantic discontinuity even when headline NPL classification is unchanged.
22. `[duplicate-pattern]` Provisioning as a capital/profitability buffer is already represented in existing coverage.
23. `[refinement]` Write-offs lower both gross problem assets and allowances; post-write-off ratios can look cleaner without eliminating economic loss.

## D. Capital, RWA and return metrics

24. `[refinement]` Capital adequacy ratios depend on both numerator capital and denominator RWA; improvement can come from retained earnings, issuance, asset mix or methodology changes.
25. `[refinement]` CET1/core-like labels are not safely comparable across all historical regimes without point-in-time rule mapping.
26. `[refinement]` RWA density can change with asset mix, collateral/guarantee treatment, model/rule changes and off-balance-sheet exposures.
27. `[new-minor]` Capital consumption per unit of reported asset can be a useful business-mix lens but is not a new business category.
28. `[refinement]` ROE can fall after recapitalization even when profit rises because equity grows faster.
29. `[duplicate-pattern]` Capital injections/listings/subordinated or loss-absorbing instruments are already represented by prior state-bank coverage.
30. `[refinement]` Dividend policy changes retained capital and future ROE mechanically; shareholder-return interpretation should distinguish payout from operating performance.

## E. NIM, spread and pricing semantics

31. `[refinement]` NIM is not simply “loan rate minus deposit rate”; earning-asset mix, non-loan assets, funding composition and average balances matter.
32. `[refinement]` Loan yield can fall while NIM is stable if funding cost also falls, or vice versa.
33. `[refinement]` Deposit cost can be obscured by mix shift from demand to term even if posted rates fall.
34. `[refinement]` Asset repricing and liability repricing occur on different schedules, making contemporaneous policy-rate changes imperfect guides to reported NIM.
35. `[duplicate-pattern]` FTP, deposit beta and repricing mechanisms are already covered by earlier blind work and targeted transaction-franchise recovery.
36. `[new-minor]` Comparing “spread” language across older annual reports may require careful reconstruction because management may use different numerator/denominator conventions.

## F. Fee, AUM, custody and customer metrics

37. `[refinement]` Fee income categories can be reorganized across cards, settlement, agency, custody, wealth or advisory lines over time.
38. `[refinement]` AUM/customer-assets/custody-assets are not equivalent: one may represent distributed products, another assets under management, another assets merely safeguarded.
39. `[refinement]` Wealth subsidiary creation can move manufacturing economics while bank distribution/customer ownership remains.
40. `[duplicate-pattern]` Group perimeter and wealth manufacturing/distribution separation are already covered categories.
41. `[refinement]` Customer counts depend on active/inactive, retail/corporate, account/customer and digital-registration definitions.
42. `[new-minor]` “Active customer” thresholds can materially affect digital-transformation narratives even if total registered users grow.
43. `[refinement]` Transaction volume can rise because of digital migration without proportional fee or relationship-profitability growth.
44. `[duplicate-pattern]` Transaction franchise/customer primacy itself is already recovered and does not reappear here as a new gap.

## G. Cost, branch and digital productivity semantics

45. `[refinement]` Cost-income ratio can improve because revenue rises rather than cost falls; cyclical fee/trading revenue can therefore distort structural-efficiency claims.
46. `[refinement]` Branch counts can change through closure, merger, upgrade/downgrade or reclassification of outlets; “outlet” definitions need pinning.
47. `[refinement]` Digital transaction share can rise mechanically as routine activity migrates online, without proving stronger customer acquisition or better economics.
48. `[new-minor]` Cost per active customer or per transaction, if consistently defined, may be a better digital-efficiency lens than channel share alone.
49. `[duplicate-pattern]` Branch-versus-digital channel economics are already represented in customer/franchise coverage.

## H. Management narratives and expectation vintages

50. `[refinement]` Listing-era expectations that governance reform would mechanically produce commercial behavior should be separated from later evidence of persistent policy mandates and internal incentive complexity.
51. `[refinement]` Retail-transformation narratives may overstate diversification if mortgages dominate retail assets or if fee/customer engagement does not deepen.
52. `[refinement]` Digital-transformation narratives may confuse app registrations or transaction migration with durable franchise economics.
53. `[refinement]` Wealth/AUM narratives may understate fee compression, product-risk transfer or deposit cannibalization.
54. `[duplicate-pattern]` Policy-support versus listed-bank commercial accountability is already a covered governance/business-model tension.
55. `[refinement]` Internationalization narratives should distinguish overseas asset growth, customer-flow support, profitability and capital/risk consumption; full cross-border detail belongs elsewhere.

## Novelty classification

- `new_category = 8` — all are minor measurement lenses, none forms a material missing ontology/category.
- `useful_refinement = 31`
- `duplicate = 16`
- `high_importance_novel_or_refining = 12`
- `material_gap_found = false`

## Confirmation decision

`counts_as_low_novelty_confirmation = true`

`low_novelty_confirmation = 1/3`

Reason: the pass stress-tested multiple semantic families and expectation vintages without discovering a new actor, mechanism, institutional perimeter, customer-franchise layer or other material category. New items are measurement refinements that can be resolved later through Evidence and point-in-time definition pinning.

Do **not** seal. Select a distinct sixth cross-time challenge so the manifest can test whether low novelty persists independently.
