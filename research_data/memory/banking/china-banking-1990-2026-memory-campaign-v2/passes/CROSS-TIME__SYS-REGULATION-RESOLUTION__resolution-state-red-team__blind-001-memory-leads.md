# CROSS-TIME × SYS-REGULATION-RESOLUTION — Independent Resolution-State Red Team 001

- `authority`: `MEMORY_LEADS_ONLY`
- `family`: `independent_resolution_state_red_team_blind_challenge`
- `model_vintage`: `GPT-5.6 Sol`
- `session_date`: `2026-09-02`
- `period`: `1990-01-01` through `2026-08-31`
- `source_visibility`: `none`
- `allowed_input_digest`: `exploration-map.json@2512db49f1674622e67488ec4594c9fa029e54a8;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- `forbidden_inputs_observed`: Batch0 raw, every prior v2 raw blind output, other-shard raw, Banking Evidence/source material, fresh Banking search, database/Drive.
- `preexposure_carveout`: honored; no directly overlapping China Merchants Bank 2023-08-28 interim-results management discussion is counted as fresh blind novelty.

This independent red-team attacks the classifier rather than adding chronology. Each group asks what minimum facts are needed before assigning the stronger resolution label and what shortcuts create false positives.

## 1. Closure vs suspension / rectification

1. **[new_category][high] Minimum fact for `closure`.** Require an authoritative act ending ordinary licensed-bank operation beyond temporary rectification, plus a successor/liquidation path or explicit terminal disposition; a news report saying branches stopped serving customers is insufficient.
2. **[new_category][high] Minimum fact for `suspension`.** Record whether the institution remains licensed, whether rectification/reopening is contemplated, and whether deposits/contracts remain with the same legal person during the stop.
3. **[useful_refinement][high] False-positive trigger.** `停业`, `暂停业务`, bank-run-driven temporary closure of outlets, holiday shutdown, system outage or administrative rectification can all look like `关闭` in shorthand.
4. **[duplicate] Guardrail.** Do not infer corporate dissolution or bankruptcy merely from an operating stop.

## 2. Supervisory takeover vs liquidity support / management custody

5. **[new_category][high] Minimum fact for `formal takeover`.** Require an authoritative takeover decision transferring specified management/control powers to a regulator or designated takeover body for a defined institution.
6. **[new_category][high] Liquidity-support test.** Central-bank lending, emergency liquidity, interbank guarantees or market-stabilization facilities can occur while governance remains with the bank; support alone is not takeover.
7. **[useful_refinement][high] Management-custody test.** `托管` or an appointed operating team may provide management services without the statutory control transfer implied by `接管`; legal authority and scope must be identified.
8. **[duplicate] Guardrail.** A bank receiving public support is not automatically under resolution control.

## 3. Owner/public recapitalization vs resolution

9. **[new_category][high] Minimum fact for `resolution action`.** Capital injection becomes resolution-adjacent only when tied to a distress intervention that changes control, loss allocation, successor structure or legal/operating state; equity funding by itself is capital management.
10. **[new_category][high] Loss-allocation test.** Identify whether existing shareholders were diluted, written down, transferred or replaced and whether creditors were impaired; otherwise `bailout` is too strong a label.
11. **[useful_refinement][high] False-positive trigger.** Local-government special bonds, state financial-holding investment, rights issues or strategic investors can replenish capital without any bank exit.
12. **[useful_refinement] Counterexample rule.** Large-bank recapitalizations and small-bank special-bond capital replenishment should remain capital-state events unless stronger intervention facts exist.

## 4. Distress asset-liability transfer vs ordinary NPL / asset sale

13. **[new_category][high] Minimum fact for `distress transfer`.** Require that a successor assumes operating-bank assets and/or liabilities as part of institution-level risk disposal, not merely that bad loans or securities were sold.
14. **[useful_refinement][high] Liability-side test.** Transfer of customer deposits, payment obligations or wholesale liabilities is much stronger evidence of institutional resolution than an isolated asset sale.
15. **[useful_refinement][high] False-positive trigger.** AMC NPL sale, securitization, loan participation, collateral disposal or balance-sheet optimization can move assets without changing the bank's legal state.
16. **[duplicate] Guardrail.** Asset sale does not imply bank failure or successor-bank formation.

## 5. Absorption merger vs failure

17. **[new_category][high] Minimum fact for `distress merger`.** Establish material pre-merger distress or an explicit risk-disposal purpose plus the legal succession path; merger approval alone does not establish failure.
18. **[new_category][high] Solvent-merger test.** Strategic consolidation, regional reform, scale efficiency or sponsor simplification can terminate a bank legal person while all customer claims continue normally.
19. **[useful_refinement][high] Claimant test.** If deposits and ordinary obligations move to the surviving bank at par with no loss allocation, the legal-person exit may be important but should not be coded as depositor resolution loss.
20. **[useful_refinement] False-positive trigger.** Falling bank counts, `吸收合并` announcements and province-wide reform statistics can overstate distress exits.

## 6. Branch conversion vs bank exit

21. **[new_category][high] Minimum fact for `bank exit`.** A predecessor legal-person bank must lose/terminate its independent banking status; creation of a successor branch should be separately recorded rather than treated as continuing legal identity.
22. **[useful_refinement][high] Customer-successor test.** Identify the successor bank that becomes counterparty to deposits and loans; branch continuity can coexist with predecessor entity termination.
23. **[useful_refinement][high] False-positive trigger.** Outlet rebranding or branch-code change can look like `村改支` even when the legal-person bank still exists; require the actual merger/conversion approval.
24. **[duplicate] Guardrail.** `村改支` is not evidence of bankruptcy or statutory deposit-insurance payout.

## 7. Listing / delisting vs banking-license state

25. **[new_category][high] Minimum fact for `banking exit`.** Require a banking-license or operating/legal-person event; securities-market delisting alone changes neither deposit contracts nor permission to conduct banking business.
26. **[new_category][high] Privatization test.** Going private can alter shareholder composition while the same bank legal person, branches and deposit liabilities continue.
27. **[useful_refinement][high] False-positive trigger.** Headlines using `退市`, tender offer, scheme of arrangement or H-share cancellation can be mistaken for market exit in the banking-regulatory sense.
28. **[useful_refinement] Counterexample rule.** Treat Bank of Jinzhou-style privatization/delisting as securities/ownership state unless separate banking-license evidence exists.

## 8. Banking-license termination vs legal-person dissolution

29. **[new_category][high] Minimum fact for `license termination`.** Require regulator action cancelling/revoking the banking permit or otherwise ending authorized banking activity; merger intent or corporate resolution is not enough.
30. **[new_category][high] Minimum fact for `legal-person dissolution`.** Require merger-effectiveness, deregistration, liquidation completion or other corporate-law event ending the entity; a cancelled license may precede final dissolution.
31. **[useful_refinement][high] Sequence test.** Record license-stop date, operating-stop date, liquidation start, merger effective date and deregistration separately because they need not coincide.
32. **[useful_refinement] False-positive trigger.** A regulator approval to dissolve/merge can be reported before business-registry cancellation; do not collapse approval and completed entity death.

## 9. Customer deposit transfer vs statutory deposit-insurance payout

33. **[new_category][high] Minimum fact for `deposit transfer`.** Establish that a successor institution assumes the deposit liability and customer claim continues against the successor, whether or not the depositor ever loses access.
34. **[useful_refinement][high] Minimum fact for `deposit-insurance payout`.** Require an actual statutory insurance-trigger/payment or a clearly identified fund-financed insured-deposit reimbursement; fund participation elsewhere in the resolution is insufficient.
35. **[useful_refinement][high] False-positive trigger.** Government/local advance payments, successor-bank assumption, bridge-bank transfer and general statements that deposits are `保障` can all be mislabeled as deposit-insurance compensation.
36. **[duplicate] Guardrail.** Deposit-insurance membership is not proof of payout.

## 10. Shareholder / wholesale-creditor loss vs depositor loss

37. **[new_category][high] Minimum fact for `depositor loss`.** Identify a legally recognized deposit claim that is not fully transferred/repaid and specify insured versus uninsured treatment; equity or interbank losses do not establish this.
38. **[new_category][high] Creditor-class test.** Separate common equity, subordinated instruments, senior bonds, interbank claims, institutional deposits, retail deposits and other claims before describing a `haircut`.
39. **[useful_refinement][high] False-positive trigger.** Baoshang-like differentiated treatment of large wholesale creditors can be generalized incorrectly into `depositors took losses`.
40. **[useful_refinement] Loss-absorber rule.** Shareholder wipeout or subordinated-debt impairment can be consistent with complete ordinary-depositor continuity.

## 11. Licensed bank vs trust / securities / P2P / non-bank failure

41. **[new_category][high] Minimum fact for `bank failure`.** Establish that the entity was a licensed bank in the relevant period and that the terminal/intervention state applied to that banking legal person.
42. **[useful_refinement][high] Perimeter test.** Trust-and-investment companies, securities companies, financial leasing firms, local exchanges, guarantee firms and P2P platforms may take or intermediate money but belong to different failure regimes.
43. **[useful_refinement][high] False-positive trigger.** Old English translations using `financial institution`, `investment corporation`, `trust bank` or colloquial `bank-like` labels can import non-bank insolvencies into bank-failure datasets.
44. **[duplicate] Guardrail.** GITIC-scale systemic significance does not make the entity a commercial bank.

## 12. Fraud / access restriction vs bank insolvency

45. **[new_category][high] Minimum fact for `bank insolvency/distress`.** Establish that the bank legal person cannot meet recognized obligations or is subject to a formal prudential/resolution intervention; customer inability to access an app/account alone is insufficient.
46. **[new_category][high] Legal-deposit test.** Determine whether the customer claim is recorded on the bank's books as a deposit, is an off-book/fraud claim, or is against a third-party platform before invoking deposit-insurance or insolvency labels.
47. **[useful_refinement][high] False-positive trigger.** Payment-code restrictions, criminal asset freezes, platform fraud, channel disputes or local administrative controls can cause access loss without proving the bank itself is insolvent.
48. **[useful_refinement] Counterexample rule.** Henan village-bank-style access/fraud disputes require claimant characterization first; `frozen deposits` is too coarse a starting label.

## Blind novelty tally

- `new_category`: 20
- `useful_refinement`: 22
- `duplicate`: 6
- `novel_or_refining`: 42
- `high_importance_novel_or_refining`: 36
- `total_leads`: 48
- `classification`: `material_but_classifier_stabilizing_novelty_with_minimum_fact_resolution_tests`

## Red-team result

The classifier survives the challenge only if resolution labels are assigned from independent state dimensions rather than narrative shorthand. The strongest upgrade gates are: authoritative action; exact legal object (bank, branch, license, entity); operating continuity; successor counterparty; asset-and-liability scope; claimant class; and whether deposit-insurance **payment** actually occurred. A legal entity disappearing, a bank delisting, public capital arriving, customers losing app access, or a merger being announced is not enough on its own.

The negative-space conclusion remains plausible after attack: genuine PRC commercial-bank terminal cases appear sparse relative to recapitalization, takeover, merger and policy consolidation. This remains an unverified memory conclusion, not a factual claim. Exact examples and thresholds belong to later Evidence work.

The invocation's single campaign-local method observation remains `legal_entity_exit_requires_customer_successor_state_split` from the 2023-2026 small-bank challenge; no additional method observation is introduced here.
