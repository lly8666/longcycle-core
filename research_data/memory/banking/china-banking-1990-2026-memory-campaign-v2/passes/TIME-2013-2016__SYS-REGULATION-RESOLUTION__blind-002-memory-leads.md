# TIME-2013-2016 × SYS-REGULATION-RESOLUTION — blind-002 safety-net/perimeter challenge

Authority: **MEMORY_LEADS_ONLY**  
Model vintage: **GPT-5.6 Sol**  
Source visibility: **none**  
Allowed inputs: exploration-map revision 12 + memory-exhaustion manifest v2 + model internal memory only.  
No prior raw blind output was read.

Purpose: test deposit-insurance claimant semantics and interbank/perimeter regulation against actual institution-resolution state. All leads below are unsourced and require later verification.

## Deposit insurance: claimant protection versus institution status

1. **[new_category][H] Deposit insurance should be modeled first as a claimant-protection layer.** The existence of insurance changes expected depositor treatment without itself changing a bank's operating, license or legal-entity status.
2. **[useful_refinement][H] A covered depositor can be protected even if the bank is merged rather than liquidated.** Protection mechanism and terminal institution outcome therefore need separate fields.
3. **[new_category][H] Insured and uninsured portions of one depositor's claim may need separate state fields.** The remembered coverage ceiling implies partial-coverage semantics, but exact aggregation rules require evidence.
4. **[useful_refinement][H] Deposit-insurance fund support and depositor reimbursement are different actions.** A fund could potentially assist risk disposal without a visible cash payout; exact legal powers remain unverified.
5. **[new_category][M] Purchase-and-assumption or assisted transfer is a possible resolution-tool analogy.** Do not assume the Chinese regime used this exact form or terminology without sources.
6. **[useful_refinement][H] Reimbursement timing is a separate clock from intervention, license change and liquidation.** A payout/transfer can precede or follow legal-entity termination depending on the mechanism.
7. **[new_category][H] Insurance membership/perimeter is institution-specific.** Later verification should establish which licensed deposit-taking institutions are covered rather than infer from a generic 'bank' label.
8. **[useful_refinement][H] WMP claims should not be assumed insured deposits.** Product wrapper, legal claim and balance-sheet location matter even when sold through a bank channel.
9. **[useful_refinement][H] Interbank deposits/NCD claims likely sit outside ordinary retail-depositor protection semantics.** Exact statutory exclusions must be checked; this is only a claimant-perimeter lead.
10. **[duplicate][M] Explicit deposit insurance does not itself mean a bank has entered resolution.**

## Runs, liquidity support and confidence events

11. **[new_category][H] A bank-run episode is a useful stress test for the new safety-net semantics.** Run dynamics can reveal depositor expectations while the institution remains open.
12. **[useful_refinement][H] The remembered Sheyang rural-bank run/rumor case should be tested for continued operations rather than labeled a failure.** Verify institution identity, trigger, liquidity response and whether any license/entity change occurred.
13. **[new_category][H] Emergency liquidity/cash availability can stop a run without changing license or entity status.** Central-bank, correspondent, shareholder or local-government support should be separately attributed if later evidenced.
14. **[useful_refinement][M] Public reassurance, cash delivery or local coordination are confidence/liquidity measures, not claimant resolution.**
15. **[duplicate][M] A depositor run is not synonymous with insolvency or resolution.**

## Governance, capital support and consolidation

16. **[new_category][H] Governance remediation can be an early-intervention state years before any later restructuring.** Investigation, management replacement and control remediation should not inherit the semantics of a future resolution event.
17. **[useful_refinement][H] Hengfeng governance antecedents must not import the bank's later restructuring outcome backward into 2013-2016.** Exact chronology and official actions require evidence.
18. **[new_category][H] Policy consolidation and distress merger need separate merger-reason fields.** The same legal endpoint can reflect rural reform, scale-building, governance cleanup or genuine solvency stress.
19. **[useful_refinement][H] A predecessor license/entity can disappear in consolidation while all deposits transfer intact and no economic failure occurs.** Legal disappearance alone is not proof of insolvency.
20. **[new_category][H] Shareholder/local-government capital support is an owner action distinct from deposit-insurance-fund action.** Both may preserve continuity but have different authority and loss-allocation implications.
21. **[useful_refinement][H] The source of capital/support matters for resolution classification even if both preserve operating continuity.** State owner, local government, existing shareholders, new investors and insurance fund should not be collapsed.
22. **[new_category][H] Administrative intervention and court bankruptcy are independent legal-process dimensions.** A regulator may act without a court proceeding; court involvement should only be recorded when evidenced.
23. **[useful_refinement][H] License revocation, if it occurs, should be recorded separately from earlier takeover/business restrictions and later liquidation.**
24. **[new_category][H] Transfer of insured deposits at par can be a claimant-protection mechanism without cash reimbursement to depositors.** This possibility should remain distinct from depositor payout semantics until sourced.
25. **[useful_refinement][H] Shareholders, subordinated claims, senior wholesale claims and insured/uninsured deposits require separate loss/transfer fields.**

## Interbank / NCD / non-standard regulation versus distress

26. **[new_category][H] Interbank/non-standard enforcement can force balance-sheet recognition or funding changes without any institution-status change.**
27. **[useful_refinement][H] NCD funding stress or rule changes affect wholesale-liability conditions; they do not themselves establish insolvency.**
28. **[useful_refinement][H] Interbank-investment reclassification/capital treatment can expose hidden credit risk while the bank remains fully licensed.**
29. **[new_category][H] WMP implicit-guarantee expectations create a claimant-perception layer separate from legal deposit insurance.** A customer expecting a bank to make a product whole does not automatically hold an insured deposit claim.
30. **[useful_refinement][M] Any later policy effort to break implicit guarantees should not be projected into this slice without contemporaneous evidence.**
31. **[new_category][H] Perimeter tightening can trigger migration from one channel to another while preserving the same underlying borrower risk.** Regulatory response should therefore be tracked as a channel-state transition, not a resolution event.
32. **[useful_refinement][H] A non-standard-asset cap is a portfolio/composition constraint, not a resolution trigger.**
33. **[duplicate][M] Forced recognition, provisioning, capital charges or portfolio limits are not bank resolution.**

## Other balance-sheet and non-bank counterexamples

34. **[new_category][H] Local-government debt swap is an asset/obligor/instrument transformation rather than a bank-status event.**
35. **[useful_refinement][M] Risk can shift from direct LGFV credit toward municipal-bond duration/concentration without disappearing.**
36. **[new_category][H] P2P platform failure is a claimant-perimeter counterexample: large investor losses can occur outside the licensed-bank resolution system.**
37. **[useful_refinement][H] A bank's custody/depository/payment role for a platform does not automatically guarantee the platform's investors.** Exact contractual responsibilities need evidence.
38. **[new_category][M] Fraud or mis-selling involving bank channels requires claimant-perimeter analysis before it is treated as depositor loss.**
39. **[useful_refinement][H] Deposit insurance may affect confidence and run incentives even when the fund is never visibly used in a resolution.** This is an ex-ante safety-net effect, not evidence of a disposal case.

## Resolution-state model and negative space

40. **[new_category][H] Post-2015 resolution records should carry distinct clocks for stress, regulatory intervention, insurance-fund action, license/entity change and claimant settlement.**
41. **[useful_refinement][H] The continued absence of a high-confidence terminal licensed-bank failure in this blind challenge is material negative space, not proof of no distress.**
42. **[useful_refinement][H] Remaining 2013-2016 uncertainty is dominated by exact coverage exclusions, fund powers, rule texts and named-case state changes rather than missing top-level mechanisms.**
43. **[new_category][H] The next high-value regime is 2017-2019, when financial deleveraging and actual small-bank interventions should make the resolution layer more observable.**
44. **[duplicate][M] The exact statutory hierarchy of takeover, suspension, revocation, liquidation and bankruptcy remains unverified and should not be invented.**
45. **[useful_refinement][M] Later Evidence search should preserve native keys around 存款保险, 最高偿付限额, 风险处置, 射阳农商行, 恒丰银行, 同业业务, 同业存单 and 非标 rather than relying only on later resolution terminology.**

## Negative space / stop reason

- No high-confidence 2013-2016 licensed-bank terminal failure with a verified insured-depositor payout, license revocation and claimant waterfall emerged from blind memory.
- Exact deposit-insurance exclusions, aggregation rules, premium design, fund intervention powers and reimbursement mechanics are source-dependent.
- Exact Sheyang/Hengfeng operating, supervisory, ownership and license-state facts remain unverified.
- Exact 8号文/127号文/NCD/non-standard prudential details remain source-dependent and should not be guessed further.
- The safety-net challenge now separates claimant protection, liquidity support, shareholder support, prudential/perimeter correction, administrative intervention, license/entity change and court/claimant settlement sufficiently for blind planning.
- Highest-value next blind move is chronological: **TIME-2017-2019 × SYS-REGULATION-RESOLUTION**, where financial deleveraging and remembered Baoshang/Jinzhou/Hengfeng-era small-bank stress create materially different resolution observations.
