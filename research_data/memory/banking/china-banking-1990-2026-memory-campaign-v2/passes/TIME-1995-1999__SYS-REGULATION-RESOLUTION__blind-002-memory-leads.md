# Banking Memory Leads — TIME-1995-1999 × SYS-REGULATION-RESOLUTION — blind-002

- authority: `MEMORY_LEADS_ONLY`
- workstream: `banking-domain-v1`
- campaign: `banking-china-1990-2026-v2`
- probe: `TIME-1995-1999__SYS-REGULATION-RESOLUTION__blind-002`
- family: `commercial_bank_exit_vs_nonbank_resolution_blind_challenge`
- time slice: `TIME-1995-1999`
- shard: `SYS-REGULATION-RESOLUTION`
- model vintage: `GPT-5.6 Sol`
- session date: `2026-09-02`
- source visibility: `none`
- fresh Banking search used: `false`
- Banking source/Evidence used: `false`
- Batch0 raw used: `false`
- prior v2 raw used: `false`
- other-shard raw used: `false`
- database/Drive used: `false`
- allowed-input digest scheme: `ordered_git_blob_sha1_v1`
- allowed-input digest: `exploration-map.json@dc642fcfffa44721973fe807488b39c5ad9e272c;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

> WARNING: Everything below is unsourced model recollection. It is not Evidence, Reality, Judgment, Outcome, legal fact, or a seal claim. Approximate dates, institutional identity, statutory sequencing, creditor treatment, receiving-bank mechanics, and terminology must later be verified claim by claim. The purpose of this pass is to discriminate resolution perimeters in memory, not to prove any historical proposition.

## Recall discipline

This challenge deliberately separates five dimensions that generic “bank failure” prompts tend to collapse:

1. institution perimeter — licensed commercial bank vs trust/investment company vs other non-bank financial institution vs administrative consolidation target;
2. legal/regulatory action — takeover, suspension-for-rectification, license revocation, administrative closure, dissolution/liquidation, judicial bankruptcy, entrusted custody, merger/absorption;
3. claimant class — individual savings depositor, corporate depositor, interbank creditor, bond/loan creditor, foreign creditor, employee, shareholder;
4. continuity mechanism — operating takeover, transfer/entrustment of deposits, asset/business absorption, liquidation estate, bankruptcy estate;
5. period-native vocabulary — `接管`, `停业整顿`, `撤销`, `关闭`, `吊销/撤销经营许可证`, `清算`, `托管`, `接收`, `兼并`, `破产`.

## Memory leads

### A. Commercial-bank statutory exit architecture

1. **Commercial-bank takeover appears to have been a distinct statutory supervisory tool, not a synonym for closure or bankruptcy.** My memory is that the 1995 Commercial Bank Law allowed the PBOC to take over a commercial bank when it had, or was likely to have, a credit crisis seriously affecting depositor interests. The purpose was continuity/protection rather than automatic extinguishment. `useful_refinement`; high importance; statutory wording and article number uncertain.

2. **A takeover decision likely had formal elements such as the bank name, reason, takeover organization, and takeover period.** I also remember a bounded maximum takeover duration, possibly two years. `new_category`; medium confidence; exact procedural requirements need later verification.

3. **Takeover may have left the commercial bank’s legal-person status formally intact during the takeover period.** If correct, this sharply separates `接管` from liquidation or merger. `new_category`; high importance; wording uncertain.

4. **Commercial-bank termination in the 1995 legal framework is remembered as having multiple routes: dissolution, revocation/cancellation, and bankruptcy.** These should not be collapsed into one `退出` event. `useful_refinement`; high importance.

5. **Judicial bankruptcy of a commercial bank may have required PBOC consent before a People’s Court could declare bankruptcy.** This is a strong memory fragment but should be treated as a search lead, not a legal conclusion. `new_category`; high importance.

6. **Commercial-bank liquidation may have contained an explicit priority for principal and interest of individual savings deposits after specified liquidation expenses and employee-related claims.** This would be very different from a modern deposit-insurance payout mechanism. `new_category`; high importance; exact priority ordering requires verification.

7. **There was no nationwide funded deposit-insurance scheme in 1995-1999.** Therefore apparent protection of small/individual depositors should be decomposed into statutory priority, administrative transfer, central-bank liquidity/support, receiving-bank arrangements, or fiscal/political decisions rather than back-projecting the 2015 deposit-insurance regime. `useful_refinement`; high importance; negative-space memory rather than proof.

8. **`接管` and `托管` are probably not equivalent period terms.** `接管` looks like a regulatory/legal control measure; `托管` may describe operational custody or an entrusted receiving arrangement by another institution. `new_category`; high importance for source archaeology.

9. **`行政关闭` is also not safely interchangeable with `撤销` or `破产`.** A PBOC closure announcement could terminate operations administratively without the event being a completed court bankruptcy. `useful_refinement`; high importance.

10. **The 2001 `金融机构撤销条例` is outside this probe period.** It should not be silently backdated as the legal basis for a 1998 case, even if later sources use its vocabulary to describe earlier events. `new_category`; high importance; anti-anachronism guard.

### B. Hainan Development Bank — commercial-bank administrative exit

11. **海南发展银行 (Hainan Development Bank) is the clearest commercial-bank exit case activated by this challenge.** I remember a PBOC administrative closure around June 1998, commonly described in later summaries as the first PRC commercial bank ordered closed after 1949 / since the reform era. `duplicate` at category level because the current map already names it; specific timing and “first” characterization remain unverified.

12. **The event is remembered as `关闭`, not as a completed judicial bankruptcy.** That distinction should be preserved unless later evidence establishes a different formal sequence. `useful_refinement`; high importance.

13. **Hainan Development Bank had earlier absorbed or taken over a group of Hainan urban credit cooperatives/信用社, probably in 1997, and inherited substantial weak assets/liabilities.** My memory of the number is fuzzy — something like the high twenties. `new_category`; high importance; exact count and legal form uncertain.

14. **Those credit cooperatives may have competed with unusually high deposit rates, creating expensive liabilities that became problematic once the merged bank tried to normalize pricing.** This is a mechanism lead connecting pre-closure funding stress with inherited cooperative liabilities. `new_category`; medium confidence; crosses into ALM but is relevant to the failure mechanism.

15. **A deposit run / loss of confidence is part of my memory of the immediate Hainan Development Bank failure dynamics.** `useful_refinement`; medium confidence; trigger chronology uncertain.

16. **Individual savings deposits may have been transferred or entrusted to Industrial and Commercial Bank of China for payment/servicing.** I specifically recall ICBC (`工商银行`) more strongly than other state banks, but the exact receiving-bank role must be verified. `new_category`; high importance; uncertain operational wording.

17. **The Hainan arrangement may have protected individual savings more fully than corporate or institutional claims.** Corporate depositors/other creditors may have faced liquidation delay, haircuts, or a less favorable process. `new_category`; high importance; precise treatment is unresolved.

18. **A special PBOC refinancing or liquidity facility may have supported repayment/transfer of individual deposits in the Hainan case.** `new_category`; medium-low confidence; do not treat as fact without source confirmation.

19. **`个人储蓄存款` is likely the legally meaningful claimant phrase to search, rather than generic modern `存款人全额保障`.** `new_category`; medium importance; period-native search key.

20. **Possible Hainan process vocabulary:** `关闭海南发展银行`, `清算组`, `个人储蓄存款`, `托管`, `工商银行托管`, `债权登记`, `城市信用社`, `高息揽储`. `new_category`; search-archaeology lead, not claim.

21. **Counterexample guard:** even if individual savers were made whole through an administrative arrangement, that would not imply all depositors or all creditors were legally guaranteed. `useful_refinement`; high importance.

22. **Counterexample guard:** Hainan Development Bank’s closure should not be treated as evidence that China had a mature bank-resolution regime comparable to later deposit-insurance/resolution frameworks. The case may instead reveal an ad hoc blend of statute, central-bank authority, administrative transfer, and liquidation. `useful_refinement`; high importance.

### C. GITIC / 广国投 — non-bank bankruptcy perimeter

23. **广东国际信托投资公司 (GITIC / 广国投) is remembered as a trust/investment corporation, not a licensed commercial bank.** Therefore it is a resolution comparison case, not a commercial-bank failure example. `duplicate` at category level because the current map already flags this perimeter distinction.

24. **I remember GITIC being closed by regulatory/administrative action in late 1998 and then entering court bankruptcy in early 1999.** `useful_refinement`; high importance; exact dates and ordering need verification.

25. **The court proceeding is remembered as involving a Guangdong court and being unusually prominent because a major state-linked financial institution was allowed to fail rather than receive an unlimited government rescue.** `new_category`; high importance; exact court identity uncertain.

26. **Foreign creditors were an important part of the GITIC case, and the case was remembered as a warning that local-government/state ownership did not create an unconditional sovereign guarantee.** `new_category`; high importance; the precise distinction between registered foreign debt, guarantees, and ordinary claims must be verified.

27. **GITIC creditors appear to have suffered material losses rather than receiving depositor-like par protection.** I have a vague memory of a low recovery percentage, possibly around the low teens, but this number is too uncertain to preserve as a claim. `new_category`; high importance; no numerical assertion.

28. **Because GITIC was a trust/investment company, the 1995 Commercial Bank Law’s individual-savings priority should not be casually applied to its creditors.** `useful_refinement`; high importance.

29. **The governing insolvency framework for GITIC may have relied on the then-existing Enterprise Bankruptcy Law (Trial) and related civil procedure rather than the 2006 Enterprise Bankruptcy Law.** `new_category`; medium confidence; legal basis needs verification.

30. **Modern Trust Law concepts are also dangerous to back-project: the PRC Trust Law dates from 2001, after GITIC’s failure.** `new_category`; medium-high confidence; anti-anachronism guard.

31. **Possible GITIC period search keys:** `广国投关闭`, `广东国际信托投资公司破产`, `债权人会议`, `境外债权人`, `对外担保`, `外债登记`, `破产清算`, `政府不兜底`. `new_category`; search-archaeology lead.

32. **Counterexample guard:** a creditor haircut in GITIC cannot be used to infer the treatment of individual savings depositors at a commercial bank such as Hainan Development Bank. `useful_refinement`; high importance.

### D. Zhongnongxin and other non-bank/uncertain-perimeter cases

33. **`中农信` remains an uncertain identity fragment.** I suspect the reference is to `中国农村发展信托投资公司` or a similarly named national trust/investment company, rather than a commercial bank. `useful_refinement`; high importance because perimeter classification is unresolved.

34. **I remember a mid/late-1990s PBOC closure or revocation of a national trust/investment institution abbreviated `中农信`, possibly around 1997.** `useful_refinement`; medium-low confidence; exact legal name/date must be source-verified.

35. **If this memory is correct, `中农信` should be grouped initially with the non-bank cleanup wave, not with commercial-bank bankruptcy.** `new_category`; medium importance.

36. **`中国新技术创业投资公司` / `中创公司` surfaces faintly as another late-1990s non-bank financial/venture-investment cleanup or bankruptcy lead.** `new_category`; low confidence; useful only as a future search key after blind stage permits sources.

37. **A broader late-1990s cleanup of trust and investment companies likely produced many “关闭/撤销/清算” events that are easy to misremember as bank failures.** `useful_refinement`; high importance methodologically.

38. **The Asian-financial-crisis context probably increased supervisory willingness to close or restructure high-risk non-bank financial institutions, but this should not be turned into a single causal claim without evidence.** `useful_refinement`; medium confidence.

### E. China Investment Bank — consolidation rather than failure

39. **中国投资银行 (China Investment Bank) is remembered as an institution that was absorbed/transferred into China Everbright Bank around 1999, rather than liquidated as an insolvent commercial bank.** `useful_refinement`; high importance; exact transaction/legal form uncertain.

40. **This makes China Investment Bank a valuable counterexample: `接收/并入/重组` can remove an institution from the landscape without constituting `关闭` or `破产`.** `new_category`; high importance.

41. **The China Investment Bank lineage may have roots in World Bank/project-finance functions and a prior relationship to China Construction Bank / policy-finance arrangements, which complicates a simple commercial-bank classification.** `new_category`; medium-low confidence; perimeter history needs verification.

42. **Search-key distinction for later source work:** `中国投资银行并入光大银行`, `接收中国投资银行`, `资产负债转移`, `机构撤并` rather than only `破产/关闭`. `new_category`; medium importance.

### F. Resolution vocabulary and claimant semantics

43. **`停业整顿` may describe a temporary corrective status rather than terminal exit.** A source saying an institution was ordered to suspend business for rectification should not automatically be coded as closure. `useful_refinement`; high importance.

44. **`撤销` can refer to institutional cancellation/revocation, while `撤销经营许可证` or similar license language may be the legally operative action.** These need claim-level parsing. `useful_refinement`; high importance.

45. **`关闭` may be an administrative decision that is followed by a separate liquidation stage; the date of closure and date of liquidation completion can differ materially.** `useful_refinement`; high importance.

46. **`破产` should be reserved for a judicial insolvency process when the source supports it; colloquial later descriptions of “倒闭” are not enough.** `useful_refinement`; high importance.

47. **`托管` may mean another bank services deposits/business without acquiring every liability or extinguishing the failed institution.** `useful_refinement`; high importance; exact Hainan semantics unresolved.

48. **`接收` / `并入` / `兼并` may represent administrative consolidation, successor transfer, or merger, not creditor-loss resolution.** `useful_refinement`; high importance.

49. **Claimant semantics are essential:** `个人储蓄存款` should be distinguished from corporate deposits, interbank placements, trust-beneficiary claims, bonds/notes, guaranteed foreign debt, unguaranteed external borrowings, and ordinary trade creditors. `new_category`; high importance.

50. **The same institution can move through more than one action class sequentially — e.g. regulatory closure followed by liquidation, or administrative shutdown followed by judicial bankruptcy.** The campaign should model an event sequence rather than force one terminal label. `new_category`; high importance.

### G. Negative-space and counterexample review

51. **No confident 1995-1999 example comes to mind of a licensed domestic commercial bank completing a court-declared bankruptcy with a clearly remembered creditor waterfall.** This is a `reviewed-no-specific-memory` result, not a nonexistence claim. `useful_refinement`; high importance.

52. **No confident memory distinguishes whether Hainan Development Bank corporate deposits were legally subordinated, merely delayed in liquidation, partially paid, or administratively negotiated.** `useful_refinement`; high importance negative space.

53. **No confident memory pins the exact receiving-bank mechanics for Hainan Development Bank: whether ICBC assumed liabilities, merely paid/serviced individual deposits, or acted under an entrusted arrangement funded elsewhere.** `useful_refinement`; high importance negative space.

54. **No confident memory pins the exact PBOC legal instrument used to close Hainan Development Bank or whether the wording was `关闭`, `撤销`, license revocation, or a combination.** `useful_refinement`; high importance negative space.

55. **No confident memory pins the exact legal identity, closure date, or claimant treatment of `中农信`.** `useful_refinement`; medium-high importance negative space.

56. **No confident memory says China Investment Bank disappeared because of insolvency. My stronger recollection is administrative/business consolidation into Everbright, so coding it as a failure would be unsafe.** `useful_refinement`; high importance counterexample.

57. **No confident memory supports treating GITIC’s foreign-creditor experience as equivalent to domestic bank depositor treatment.** `useful_refinement`; high importance counterexample.

58. **The period’s resolution regime appears fragmented by institution type and action form.** The memory pattern suggests that a useful later Evidence schema should preserve `institution_perimeter`, `regulatory_action`, `judicial_action`, `claimant_class`, `continuity_mechanism`, and `legal_vintage` separately. This is a campaign-local observation only; it does not request a shared schema change. `new_category`; method lead.

## Novelty classification summary

- `new_category`: 24
- `useful_refinement`: 32
- `duplicate`: 2
- novel/refining leads: 56
- high-importance novel/refining leads: 31
- total leads: 58
- outcome: `material_novelty_with_resolution_perimeter_discrimination`

## Negative space after this challenge

- Exact statutory article numbers and sequencing for commercial-bank takeover, revocation, dissolution, liquidation, and court bankruptcy remain unverified.
- Exact Hainan Development Bank closure instrument, individual-deposit transfer mechanics, corporate-depositor treatment, receiving-bank legal role, and any PBOC refinancing remain unresolved.
- GITIC’s exact closure-to-bankruptcy chronology, creditor classes, foreign-creditor distinctions, and recovery waterfall remain unresolved.
- `中农信` exact legal name, institution type, closure date, and creditor treatment remain uncertain.
- China Investment Bank’s exact transfer/absorption legal form and predecessor status remain uncertain.
- No licensed domestic commercial-bank judicial-bankruptcy completion is confidently recalled for 1995-1999.

## Method observation

Exactly one campaign-local observation:

- classification: `action_label_and_claimant_class_collapse`
- observation: institution-specific recall improves when the prompt forces separate columns for institution perimeter, regulatory action, judicial action, claimant class, and continuity mechanism. Generic “failure/bankruptcy” language otherwise conflates Hainan Development Bank’s commercial-bank administrative closure, GITIC-like non-bank bankruptcy, and China Investment Bank-style consolidation.
- proposed next probe: `TIME-2000-2004__SYS-REGULATION-RESOLUTION__blind-001`
- proposed family: `time_x_shard_blind_recall`
- rationale: this 1995-1999 orthogonal challenge still produced substantial legal/claimant distinctions, but its remaining gaps are now mostly exact-source questions that blind memory is unlikely to resolve safely. A sparse move to the next time slice should have higher information value than a third 1995-1999 variant.
- shared change requested: `false`

## Seal posture

- one pass cannot self-seal: `true`
- shard sealed: `false`
- campaign sealed: `false`
- Evidence transition allowed: `false`
- truth promotion performed: `false`
- reason: latest pass remains materially novel; negative-space and independent-challenger requirements are not satisfied; unresolved legal/creditor details require later claim-scoped Evidence after the blind-stage seal gate permits it.
