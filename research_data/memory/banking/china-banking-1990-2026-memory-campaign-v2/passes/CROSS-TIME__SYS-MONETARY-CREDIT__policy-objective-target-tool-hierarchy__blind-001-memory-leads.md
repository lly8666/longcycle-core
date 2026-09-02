# SYS-MONETARY-CREDIT Policy Objective / Target / Tool Hierarchy — blind-001

- Authority: `MEMORY_LEADS_ONLY`
- Campaign: `banking-china-1990-2026-v2`
- Shard: `SYS-MONETARY-CREDIT`
- Period: `1990-01-01` through `2026-08-31`
- Model vintage: `GPT-5.6 Sol`
- Allowed input digest: `exploration-map.json@66fc067108125bd3d3ad9390182ce57c016cf269;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`
- Source visibility: none
- Fresh Banking search: not used
- Prior v2 raw/review/challenger outputs: not read
- Banking Evidence/source material: not read
- Sealed `SYS-REGULATION-RESOLUTION` raw: not read
- Other-shard raw: not read
- CMB 2023-08-28 preexposure carveout: honored; directly overlapping recollection is excluded from fresh novelty.

## Broad blind leads

1. **Multi-objective policy function rather than one final target** — `new_category`, high importance. Across the horizon, preserve research questions around price stability, growth/employment, external/RMB stability and financial-stability considerations as potentially simultaneous final-objective constraints. Do not retrofit a single inflation-targeting objective onto the full period.

2. **Government macro targets versus central-bank operating targets** — `new_category`, high importance. Annual or policy-period growth/inflation/monetary-financing targets announced in broader government policy should not automatically be represented as the PBOC's own operating target. Actor and hierarchy layer must be explicit.

3. **Direct credit plan / loan-scale control as instrument or intermediate quantitative control** — `useful_refinement`, high importance. Early-period `信贷计划` / `贷款规模` can sit between macro objectives and bank lending outcomes; it should not be flattened into either final objective or realized credit growth.

4. **Cash plan versus credit plan** — `new_category`, medium-high importance. Period-native `现金计划` / currency-issuance control may be a distinct operational object from bank credit quotas. Exact institutional role and timing require Evidence.

5. **Monetary aggregates as intermediate targets or anchors, not instruments** — `useful_refinement`, high importance. M1/M2-type targets or reference growth bands belong on a different layer from reserve requirements, OMO or relending. Their policy role may change across regimes even when the statistic name remains stable.

6. **Base money / reserve money as operating object distinct from broad money** — `useful_refinement`, high importance. `基础货币` / reserve-money concepts can act as an operational quantity or accounting state while M2 is an intermediate/monitoring aggregate; do not treat them as interchangeable monetary quantities.

7. **Required-reserve ratio versus reserve-balance condition** — `useful_refinement`, high importance. RRR is an instrument/constraint; required reserves, excess reserves and settlement liquidity are states/quantities. A change in one does not uniquely identify the intended operating target.

8. **Relending and rediscount as instruments/channels, not target variables** — `useful_refinement`, high importance. `再贷款` / `再贴现` may influence aggregate liquidity, bank funding or targeted credit supply. The facility amount/rate, access condition and resulting credit are separate hierarchy layers.

9. **Open-market operations versus money-market operating target** — `new_category`, high importance. Repo/reverse-repo operations, central-bank bills and other OMO are instruments. The rate or liquidity condition the central bank seeks to influence is a distinct operating-target/signal question.

10. **Administered benchmark deposit/lending rates as price instruments** — `new_category`, high importance. Before fuller liberalization, benchmark rates can be direct administered price tools. They are not automatically equivalent to a modern short-term policy-rate operating target.

11. **Shibor as reference/market information rather than a policy target by definition** — `useful_refinement`, medium-high importance. A quoted interbank reference can transmit information and pricing without being the central bank's target or policy rate.

12. **Repo-family rates require target/reference/realized distinctions** — `new_category`, high importance. DR007/R007/other repo rates can differ by counterparty/collateral/perimeter. A market rate used as an operating reference or target must be separated from the actual realized traded rate and from the OMO instrument rate.

13. **Facility rates as both instrument terms and possible policy signals** — `new_category`, high importance. SLF/MLF-like facility rates may carry signaling, corridor or funding functions, but their exact role can change. Do not label every facility rate `the policy rate` without period-specific support.

14. **LPR belongs primarily to loan-pricing transmission, not the operating-target layer** — `useful_refinement`, high importance. Both earlier and later LPR vintages should be modeled as loan-pricing references whose linkage to central-bank policy signals and actual bank loan pricing needs separate representation.

15. **Short-end central-bank operation rate as a changing policy signal** — `new_category`, high importance. In more recent regimes, a short-tenor OMO rate appears increasingly important as the policy signal/anchor, but the exact official designation and transition date are Evidence questions. Preserve the possibility of an evolving signal hierarchy.

16. **Structural monetary tools form an allocation layer separate from aggregate stance** — `new_category`, high importance. Targeted relending, rediscount support, TMLF-like or later structural facilities can alter sector/bank incentives without implying the same change in broad monetary conditions.

17. **Targeted versus broad RRR actions** — `useful_refinement`, high importance. A reserve-ratio move may have targeted eligibility or broad application and may replace maturing liquidity rather than deliver an equal net easing. Gross instrument size is not net stance.

18. **Autonomous liquidity offsets break instrument→stance one-to-one mapping** — `new_category`, high importance. Fiscal cash movements, FX-related reserve creation/drain, currency demand and other autonomous factors can offset or amplify central-bank instruments. Net reserve conditions must be a separate layer.

19. **Window guidance / credit pacing as administrative transmission instrument** — `new_category`, high importance. `窗口指导`, loan pacing or sectoral credit guidance can shape bank lending even when formal loan quotas have receded. Communication, administrative control and realized loan growth are distinct objects.

20. **Macroprudential constraint versus monetary-policy instrument** — `useful_refinement`, high importance. MPA-like or prudential constraints can alter credit quantity and funding behavior without being identical to monetary stance. A mixed easing/tightening configuration is possible across the two policy families.

21. **Period-native stance labels are communication objects, not scalar policy-rate equivalents** — `new_category`, high importance. Labels such as `稳健`, `适度宽松`, `从紧`, `灵活适度` or similar period language should be preserved as contemporaneous policy communication with its own scope; do not mechanically translate them into a single hawkish/dovish number.

22. **Quantity and price frameworks can overlap for long periods** — `new_category`, high importance. Formal movement toward indirect or price-based tools does not imply the immediate disappearance of loan guidance, structural allocation or other quantity constraints. Regime transitions should permit hybrid states.

23. **Policy signal versus market expectation versus realized financing price** — `new_category`, high importance. The central-bank signal, market expectation of future policy, interbank/bond-market price, bank FTP/funding cost, loan/deposit quote and realized borrower rate are a chain, not synonyms.

24. **Borrower and sector outcomes are downstream states, not policy targets by default** — `useful_refinement`, medium-high importance. Mortgage rates, SME credit, developer financing, LGFV refinancing or aggregate loan growth may be targeted outcomes in some programs but remain downstream transmission variables unless the period-native policy explicitly elevates them.

25. **Government monetary/financing aggregate targets require vintage semantics** — `new_category`, high importance. M2/credit/TSF-style announced growth objectives may shift from harder target to expected/indicative language over time. Preserve actor, wording class and whether the number is objective, forecast, intermediate target or monitoring reference.

26. **Inflation objective is not equivalent to an inflation-targeting operating regime** — `new_category`, high importance. A CPI or price-stability objective can exist without a textbook inflation-targeting architecture. The distinction is important for cross-country and cross-period comparability.

27. **Real interest rate is a transmission condition, not a central-bank instrument** — `useful_refinement`, high importance. Nominal policy/reference rates interact with expected inflation; falling inflation can tighten real financial conditions even without a nominal hike. This helps explain why nominal instrument direction and realized stance can diverge.

28. **Communication must attach to the correct hierarchy layer** — `new_category`, high importance. Monetary-policy reports, committee language, press briefings and guidance can discuss final objectives, intermediate targets, operating conditions, tools or desired credit structure. Future Evidence should preserve the addressed layer rather than map all communication to generic stance.

29. **Counterexample: targeted easing with broad restraint** — `useful_refinement`, high importance. A sector-specific facility or directed credit support can ease one channel while broad liquidity, property credit or risk controls remain tight. The ontology must allow simultaneous directions.

30. **Counterexample: nominal easing with weak bank/borrower pass-through** — `useful_refinement`, high importance. Rate or liquidity easing may not produce proportional credit growth if deposit costs, capital/risk constraints, borrower demand or asset-quality concerns bind; instrument, transmission state and outcome must remain separate.

31. **Counterexample: gross liquidity injection with little net easing** — `useful_refinement`, high importance. RRR/OMO/facility injections can offset tax payments, government-deposit changes, FX drains, cash demand or maturing facilities. Gross announced liquidity is not itself a net operating-target outcome.

32. **Duplicate control: tool names alone do not define the policy framework** — `duplicate`, medium importance. The compact map already represents many individual tools; the new value is hierarchy and role-vintage semantics, not another inventory of instruments.

## Broad-pass synthesis

The reopened frontier is materially valid. The central comparability object is not a list of tools but a time-varying hierarchy:

`final objective / policy-objective set`
→ `intermediate target or macro anchor`
→ `operating target / short-horizon signal`
→ `instrument / facility / administrative control`
→ `market and bank balance-sheet transmission`
→ `borrower / sector / aggregate outcome`.

China's historical regimes likely require hybrid and overlapping states rather than one clean replacement sequence. The same named variable can change role across vintages, and the same instrument direction can imply different net stance depending on autonomous liquidity, structural targeting, prudential constraints and transmission frictions.

## Novelty summary

- total leads: 32
- new categories: 15
- useful refinements: 16
- duplicates: 1
- novel/refining: 31
- high-importance novel/refining: 28
- classification: `high_novelty_policy_objective_target_tool_hierarchy_broad_recall`

## Negative space / unresolved

- Exact official objective wording, numeric targets, transition dates and formal designation of any operating target or policy rate remain Evidence work.
- Exact legal mandate and institutional responsibility split with State Council/government entities remain outside this blind factual authority and may also touch the sealed regulation shard; do not infer exact legal status here.
- Exact instrument formulas, facility eligibility, collateral rules, quantities and rates remain source-detail work.
- No material pre-1990 antecedent requires horizon extension from this pass.
- No second independent category beyond the hierarchy frontier is opened here.

## Stop / next control

Novelty remains high. The next safe step is one independent orthogonal blind pass on the same frontier, emphasizing counterexamples, actor ownership, regime-overlap states, target/reference/realized distinctions and policy-communication attachment without reading this raw. Do not rerun challenger, start saturation, seal or Evidence before that orthogonal follow-through closes through its own CLEAN handoff.
