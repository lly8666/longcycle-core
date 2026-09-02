# China Banking Memory Campaign v2 — low-novelty confirmation blind-004

- probe_id: `CROSS-TIME__SYS-REGULATION-RESOLUTION__low-novelty-confirmation__blind-004`
- family: `bounded_low_novelty_confirmation`
- period: `1990-01-01` to `2026-08-31`
- model_vintage: `GPT-5.6 Sol`
- authority: `MEMORY_LEADS_ONLY`
- source_visibility: `none`
- fresh_search_used: `false`
- banking_evidence_used: `false`
- prior_v2_raw_used: `false`
- batch0_raw_used: `false`
- other_shard_raw_used: `false`
- database_or_drive_used: `false`
- preexposure_carveout_honored: `true`
- allowed_input_digest: `exploration-map.json@ae042d78b154ece489e56379563e0a672fc10f3d;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

## Bounded independent scan

This unit intentionally avoids chronology and named-case enumeration. It asks only whether the compact category map still misses a genuinely map-changing regulation/resolution category or material antecedent. Exact legal wording, ratios, dates, creditor ordering and named-bank implementation are deferred to later Evidence work.

| # | Memory lead / challenge | Class | Importance |
|---|---|---|---|
| 1 | A pre-resolution supervisory escalation ladder may need explicit representation: heightened supervision, corrective demands, restrictions or governance intervention can precede formal resolution without constituting resolution entry. This appears to refine the existing supervisory-intervention/state ladder rather than create a new top-level category. | useful_refinement | high |
| 2 | Resolution valuation should be temporally separated from later realized loss: an administrative or transaction valuation can guide action while ultimate recoveries and creditor losses remain unsettled. Exact valuation rules or dates are Evidence-only. | useful_refinement | high |
| 3 | Deposit-insurance or similar protection architecture can have an ex-ante fund/premium/reserve state distinct from an ex-post payout, bridge-funding or recovery/subrogation state. This refines the existing funding-role map rather than opening a new class. | useful_refinement | medium |
| 4 | Customer operational access should remain separate from legal claim status: payment-channel continuity, account usability or transfer of servicing can change before the underlying claim is finally settled. This is a claimant-state refinement, not a new resolution type. | useful_refinement | medium |
| 5 | Critical-function continuity does not imply preservation of the original licensed legal entity. | duplicate | high |
| 6 | Systemic-importance designation, recovery-plan existence and resolvability work do not imply distress or resolution activation. | duplicate | high |
| 7 | Issuance or eligibility of loss-absorbing instruments does not prove write-down, conversion or creditor loss. | duplicate | high |
| 8 | Liquidity support, solvency support, public/owner capital and resolution funding remain distinct roles even when provided by related public actors. | duplicate | high |
| 9 | A fund or public actor that advances cash is not automatically the ultimate loss bearer; recoverability and subrogation may move the final burden. | duplicate | high |
| 10 | Target-bank state must remain separate from market-wide contagion, counterparty repricing and system liquidity stabilization. | duplicate | high |
| 11 | Merger, asset transfer, ownership change, license termination and legal-entity dissolution are separate events and should not be collapsed into one `resolution_type`. | duplicate | high |
| 12 | Customer-visible balance/access, bank-ledger recognition, legal-deposit characterization, contractual counterparty and claimant settlement are separate states. | duplicate | high |
| 13 | Supervisory institution reorganization or regulatory-architecture change is not itself a bank resolution event. | duplicate | medium |
| 14 | Branch closure, service-point migration or business transfer should not be promoted into bank-level license termination without entity-level facts. | duplicate | medium |
| 15 | `living will`, `bail-in`, `bridge bank`, purchase-and-assumption and no-creditor-worse-off style vocabulary are comparative/search leads unless native PRC usage is independently supported; exact legal transplant would be source-like detail. | duplicate | medium |
| 16 | Exact insured-deposit thresholds, payout tiers, creditor rankings, trigger language and instrument eligibility remain source-detail questions rather than blind category novelty. | duplicate | medium |
| 17 | Named-bank transaction terms, investor identities, exact capital amounts or dates would be source-like detail and cannot count as fresh category novelty in this confirmation. | duplicate | medium |
| 18 | A routine plan refresh, simulation, tabletop exercise or operational test remains preparedness evidence; it is not evidence that a real recovery or resolution event occurred. | duplicate | medium |

## Long-tail / negative-space result

The scan did not recover a new institution class, actor class, terminal-exit state, claimant class, funding/backstop channel, loss-allocation class, preparedness class or material antecedent. The strongest remaining memory fragments are representational refinements inside already-covered categories: supervisory escalation before formal resolution, valuation-time versus realized-loss time, ex-ante protection-fund state versus ex-post payout, and customer operational access versus legal claim state.

Forgotten-actor and old-vocabulary prompts mostly collapse into already represented roles (supervisor, resolution authority, deposit-protection/funding actor, owner/public capital provider, transferee/continuing service provider) or comparative/source-like terminology. Counterexample prompts likewise reinforce existing non-promotion rules: preparedness is not activation; support is not final loss allocation; transfer is not entity death; customer access is not legal claim characterization; and system contagion is not target-bank resolution state.

## Novelty assessment

- new_category_count: `0`
- useful_refinement_count: `4`
- duplicate_count: `14`
- novel_lead_count: `4`
- high_importance_novel_count: `2`
- total_lead_count: `18`
- classification: `low_novelty_confirmation_restart_2_with_no_material_new_category`

This is duplicate-dominant and contains no map-changing category. It therefore qualifies as the second consecutive low-novelty confirmation after the preparedness-category reset. The shard must remain unsealed; one further consecutive low-novelty pass is still required by the manifest.