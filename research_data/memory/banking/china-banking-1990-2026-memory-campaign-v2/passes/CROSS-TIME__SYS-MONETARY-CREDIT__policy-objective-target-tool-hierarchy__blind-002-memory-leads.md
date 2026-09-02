# SYS-MONETARY-CREDIT Policy Objective / Target / Tool Hierarchy — blind-002 orthogonal

- Authority: `MEMORY_LEADS_ONLY`
- Campaign: `banking-china-1990-2026-v2`
- Shard: `SYS-MONETARY-CREDIT`
- Period: `1990-01-01` through `2026-08-31`
- Model vintage: `GPT-5.6 Sol`
- Allowed input digest: `exploration-map.json@3541fa4df8acae4c6a5dc68966cfdb57aeb87477;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- Source visibility: none
- Hierarchy blind-001 raw: not read
- Independent-challenger raw/control artifact: not read
- Other prior v2 raw/review outputs: not read
- Banking Evidence/source material: not read
- Fresh Banking search: not used
- Sealed `SYS-REGULATION-RESOLUTION` raw: not read
- Other-shard raw: not read
- CMB 2023-08-28 preexposure carveout: honored; directly overlapping recollection is excluded from fresh novelty.

## Orthogonal challenge leads

1. **Target owner and instrument operator can be different actors** — `new_category`, high importance. A macro objective or financing-growth expectation can originate in broader government policy while the central bank operates liquidity/rate/credit tools. Store actor ownership separately at each hierarchy layer.

2. **Announcement variable versus implementation variable** — `new_category`, high importance. A publicly announced monetary/credit objective can coexist with a different day-to-day operating variable. Announcement salience does not prove operational control.

3. **Target/reference/fixing/realized value are distinct states** — `new_category`, high importance. A target rate, reference rate, quoted fixing and actually traded/loan rate can all differ. This is especially important for interbank references, administered benchmarks, LPR-style quotes and realized loan pricing.

4. **Policy horizon mismatch** — `new_category`, medium-high importance. Final objectives may be annual or medium-term while operating targets and instruments act daily/monthly. A temporary liquidity operation should not be interpreted as a same-horizon change in the final objective.

5. **Stock target versus flow target versus growth-rate target** — `useful_refinement`, high importance. Credit, money and financing objectives can be stated as levels, increments or growth rates. Even before Evidence fixes exact wording, the ontology should preserve this type distinction.

6. **Hard target versus expected/indicative reference** — `useful_refinement`, high importance. Period-native policy language may shift from quota-like or mandatory control toward expected/indicative objectives. Do not equate every published number with an enforceable target.

7. **Operating corridor boundary versus observed market rate** — `useful_refinement`, high importance. A corridor floor/ceiling candidate, central-bank operation rate and observed DR/R-style market rate can occupy different semantic roles; realized trades may deviate from the intended operating zone.

8. **Reserve remuneration can affect the effective price floor** — `new_category`, medium-high importance. Interest paid on reserves or similar balance-sheet remuneration may matter for banks' opportunity cost and the lower bound of short-term rates; exact regime details are Evidence work.

9. **Reserve maintenance rule versus reserve target** — `useful_refinement`, high importance. Required-reserve calculation/maintenance conventions are institutional rules, not necessarily the operating target itself. Required, excess and settlement reserve balances remain states.

10. **Facility eligibility is an allocation filter, not a stance target** — `useful_refinement`, high importance. Access rules/collateral/eligible borrowers or loans determine who receives facility liquidity; they are part of instrument design and structural allocation rather than the final objective.

11. **Instrument maturity versus policy-horizon signal** — `useful_refinement`, medium-high importance. Overnight/7-day/monthly/longer-tenor facilities can carry funding and signaling content at different horizons. Tenor alone does not identify hierarchy layer.

12. **FX/exchange-rate objective can constrain domestic operating choices** — `new_category`, high importance. When RMB/external stability matters, domestic liquidity/rate settings may partly respond to FX conditions. That creates multi-objective tradeoffs rather than a single domestic price target.

13. **Fiscal cash path can move the operating variable without objective change** — `useful_refinement`, high importance. Tax collection, government deposits, bond issuance/spending and treasury cash flows can shift bank reserves/liquidity and trigger offsetting operations without implying a change in final stance.

14. **Macroprudential tightening plus monetary easing is a valid mixed state** — `useful_refinement`, high importance. Credit/risk constraints can tighten while aggregate liquidity or rates ease. The ontology must allow policy-family vectors rather than one scalar stance.

15. **Sectoral credit restriction plus structural support elsewhere is a valid mixed state** — `useful_refinement`, high importance. Property or other risk-sensitive credit can face restraint while SME/green/agriculture/technology channels receive support. Aggregate labels cannot replace allocation-layer states.

16. **Window guidance can be both communication and administrative control** — `new_category`, high importance. The same interaction may signal desired behavior and impose practical pressure. Record communication role and control role separately when Evidence later permits.

17. **Market expectation is not the policy signal itself** — `useful_refinement`, high importance. Bond/repo/FX/loan markets may infer future easing/tightening from communications or operations; expectation is a market Judgment layer downstream of the official signal.

18. **Bank internal transfer pricing is a transmission layer** — `new_category`, medium-high importance. Central-bank funding/reference rates reach borrower prices through bank liability costs, FTP, capital/risk charges and competitive strategy; internal pricing is neither policy target nor borrower outcome.

19. **Credit supply and credit demand can offset each other** — `useful_refinement`, high importance. Weak loan growth after easing may reflect bank risk appetite/capital or borrower demand. Realized aggregate financing cannot be read backward as the central bank's target without mechanism evidence.

20. **Quantity control can bind at institution or sector level** — `useful_refinement`, high importance. Loan pacing, quota or guidance can be heterogeneous across banks/regions/sectors. Aggregate credit growth can therefore mask binding micro-level controls.

21. **Policy-bank/quasi-fiscal financing interface is a transmission boundary** — `new_category`, high importance. Policy/development-bank balance sheets or government-backed programs can amplify targeted financing while not being ordinary PBOC operating instruments. Exact institutional responsibility belongs to later Evidence/other shards.

22. **Realized inflation/growth/credit outcomes are evaluation variables, not retroactive targets** — `useful_refinement`, high importance. Ex-post outcomes can evaluate the effectiveness of a policy hierarchy but cannot be used to rewrite what the contemporaneous target or signal was.

23. **Regime labels may overlap during transition** — `useful_refinement`, high importance. A period can simultaneously retain monetary-aggregate guidance, administered benchmarks, market-rate signals, structural tools and administrative credit influence. Avoid a single switch date unless source evidence later proves one.

24. **Duplicate control: instrument inventory is already broad** — `duplicate`, medium importance. More tool names do not create a new hierarchy category.

25. **Duplicate control: exact official designation belongs to Evidence** — `duplicate`, medium importance. Whether a particular rate was formally named the policy rate or operating target at a precise date cannot be established by blind memory.

## Orthogonal synthesis

The broad hierarchy survives independent challenge. The key representation should permit multiple actors, multiple objectives, hybrid quantity/price regimes, several time horizons and mixed policy vectors. At minimum, preserve:

`objective owner + final-objective set`
→ `intermediate anchor/target (hard vs indicative; stock/flow/growth)`
→ `operating target or short-horizon signal`
→ `instrument design (rate/quantity/eligibility/maturity/admin control)`
→ `autonomous liquidity + market expectation + market price`
→ `bank funding/FTP/capital/risk transmission`
→ `borrower/sector/aggregate financing outcome`
→ `later macro outcome/evaluation`.

No second material category-level omission emerged. The remaining uncertainty is mainly exact historical role assignment, wording and transition timing, which belongs to Evidence rather than another ordinary blind frontier.

## Novelty summary

- total leads: 25
- new categories: 8
- useful refinements: 15
- duplicates: 2
- novel/refining: 23
- high-importance novel/refining: 20
- classification: `orthogonal_actor_ownership_state_type_hybrid_regime_and_transmission_hierarchy_follow_through`

## Negative space / unresolved

- Exact State Council/PBOC mandate and actor responsibility wording remain source/legal Evidence work.
- Exact target bands, rate corridor definitions, reserve-remuneration regimes, facility rules and official transition dates remain Evidence work.
- No second material blind category emerged.
- No material pre-1990 antecedent requires horizon extension.
- The hierarchy frontier now has independent broad + orthogonal blind depth.

## Stop / next control

Mark `CROSS-TIME__SYS-MONETARY-CREDIT__POLICY-OBJECTIVE-TARGET-TOOL-HIERARCHY` broad+orthogonal complete. The next safe control is one independent-challenger rerun from a fresh CLEAN handoff using only the compact map + manifest, not either hierarchy raw. Do not run that challenger inside this probe, do not count this pass toward low-novelty seal qualification, and do not begin saturation, seal or Evidence.
