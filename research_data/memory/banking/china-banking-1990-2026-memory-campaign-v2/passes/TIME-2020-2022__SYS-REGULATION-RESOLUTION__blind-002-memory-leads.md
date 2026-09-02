# TIME-2020-2022 x SYS-REGULATION-RESOLUTION — blind-002 claimant/access state challenge

**Authority:** `MEMORY_LEADS_ONLY`  
**Model vintage:** `GPT-5.6 Sol`  
**Session date:** `2026-09-02`  
**Source visibility:** `none`  
**Fresh Banking search:** `forbidden / not used`  
**Banking Evidence:** `not read`  
**Prior v2 / Batch0 / other-shard raw:** `not read`  
**Allowed-input digest:** `exploration-map.json@22e7eb826b1dc6e9cd80ae561d1687bf900d8080;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This is an isolated orthogonal blind challenge. It does not broadly retell the pandemic or property downturn. The primary test is whether the remembered 2022 Henan village-bank episode and provincial-bank consolidation can be represented without collapsing claimant legal status, access status, criminal/fraud allegations, support payments, deposit insurance, bank operating/license/entity state and merger/transfer mechanics.

1. [NEW][HIGH] 河南村镇银行事件中“APP/小程序/线上账户显示余额”只是 customer-visible record；它不单独证明相同金额已作为持牌银行表内存款入账。
2. [NEW][HIGH] 因此 claimant state 至少要分 `customer_recorded_balance`、`bank_ledger_recognition`、`contractual_counterparty`、`fund_flow_destination` 和 `legal_deposit_status`，后续Evidence不能只看客户截图。
3. [NEW][HIGH] 第三方互联网平台可能承担导流、展示、开户跳转、支付或数据接口角色；平台参与不自动使资金变成非存款，也不自动证明银行已真实入账，必须逐交易识别。
4. [NEW][HIGH] 涉嫌新财富集团等外部控制/犯罪网络的记忆意味着 `criminal_actor_state` 与 `licensed_bank_state` 必须拆开；犯罪团伙利用银行渠道不等于银行法人本身被法院认定为犯罪主体。
5. [NEW][HIGH] “账外业务”如果成立，关键不是简单标记 fraud=true，而是确认资金是否进入银行资产负债表、谁签约、谁控制系统、谁最终占有资金。
6. [NEW][HIGH] 客户无法提现/转账应单列 `access_status`；它可能来自技术暂停、银行风控、监管措施、刑事冻结、渠道中断或其他原因，不能推导 `operating_status=closed`。
7. [NEW][HIGH] 柜面是否营业、银行卡/支付是否可用、线上渠道是否可用可能在同一银行同时呈现不同状态；“银行无法取款”需要渠道级粒度。
8. [NEW][HIGH] 河南地方后续“垫付”最安全的 blind 标签是 `advance_payment/support`，不是 `deposit_insurance_reimbursement`；付款主体、资金来源和法律依据必须另证。
9. [NEW][HIGH] 分档垫付若按客户金额推进，仍不能由档位数值反推存保50万元限额是其法律依据；相同或接近数字可能只是政策设计巧合。
10. [NEW][HIGH] 对已垫付客户，`cash_received=true` 也不能自动等于原债权已完成法律清偿；是否债权转让、代位、追偿或保留剩余请求权需后续Evidence。
11. [NEW][HIGH] 刑事追赃退赔与地方垫付可在时间上并存；它们的损失承担者、追偿权和 claimant settlement 状态不同。
12. [NEW][HIGH] 存款保险适格性应以“是否为被保险存款机构吸收的受保存款及其法定范围”为研究问题，而不是以客户主观认知“我买的是存款”直接决定。
13. [NEW][HIGH] 即便客户资金最终被认定为真实存款，也还需分保险限额内/外、同一存款人聚合规则及是否触发正式保险赔付程序；blind memory不提供这些结论。
14. [NEW][HIGH] 若资金被认定为涉嫌犯罪形成的账外资金，其最终补偿可能主要来自地方垫付、追赃或其他安排，而非标准存保路径；这是待证假设。
15. [NEW][HIGH] 事件中地方公安/司法调查、地方金融监管、银保监系统、银行自身和可能的存保机构是不同 actor；一个 actor 的公告不能自动代表其他 actor 的法定动作。
16. [NEW][HIGH] 健康码争议应记录为 `local_administrative/social_control_action`，与 bank access/legal-deposit/insurance state 平行，避免将其写成银行冻结账户的技术原因。
17. [NEW][HIGH] 河南四家或若干村镇银行可能共享股东/实际控制/系统渠道风险，但每家银行的牌照、资产负债表、发起行、客户和最终处置必须逐机构拆分。
18. [NEW][HIGH] “村镇银行”本身是持牌银行类型，不应因存在涉嫌诈骗就降格成普通互联网平台；相反也不能因有银行牌照就推断所有关联线上资金均为表内存款。
19. [NEW][HIGH] 对主发起银行，应单独记录股权/治理责任、技术系统/渠道关系和是否承担资金补偿；主发起身份不等于自动承担所有村镇银行负债。
20. [NEW][HIGH] 河南事件最终是否涉及吸收合并、股权重组、牌照注销或继续独立经营，在blind memory中不够清晰，因此必须保留 `license_status=unknown` / `entity_outcome=unknown` 而非补齐故事。
21. [NEW][HIGH] 河南事件的核心不是一个单一“bank run”模型：客户访问限制发生时，可能同时存在犯罪调查、账簿争议、线上渠道问题和社会稳定型垫付，传统流动性挤兑框架不足。
22. [NEW][HIGH] 省域整合的对照测试表明：蒙商银行更像包商处置后的承接/新设实体；辽沈银行/山西银行则可能更多体现区域整合或多行合并，不能共享同一个 `resolution_type`。
23. [NEW][HIGH] 新银行开业日期、资产负债承接日期、旧银行停止营业日期、旧牌照注销日期和旧法人注销日期可能不同，必须允许五个独立时间点。
24. [NEW][HIGH] 客户账户/存单迁移到承接银行可能实现服务与债权连续，但这不代表原法人或原牌照连续；customer continuity 与 entity continuity可相反。
25. [NEW][MED] 若地方专项债或地方国资在合并前后补资本，应记录为 public-capital/ownership action；它与法律合并、资产转让和债权人待遇没有必然一一对应关系。
26. [NEW][MED] 多家城商行组成新银行时，原股东换股、现金退出、稀释或由地方国资接盘可能各不相同；blind memory不应用统一“政府接管”描述。
27. [NEW][MED] 辽沈银行若承接辽阳银行、营口沿海银行等机构，需核验究竟是吸收合并、资产负债承接还是其他重组；名字同时出现不足以证明法律动作。
28. [NEW][MED] 山西银行的形成可作为“多家城市商业银行合并新设/吸收”的搜索键，但各原银行是否同日注销、客户合同如何承继属于source-like细节。
29. [NEW][MED] 省域整合与危机处置可能重叠：即使某参与行有资产质量问题，也不能因此把整个区域合并定义为resolution；需要机构级触发原因。
30. [NEW][MED] 村镇银行改革化险可能采用主发起行增持、吸收合并、改制支行或退出等多种路径；这些更系统化动作可能主要发生在2023以后，2022只保留未来追踪线索。
31. [NEW][MED] 河南事件可推动后续对互联网存款、异地存款、村镇银行股东治理和科技系统的监管收紧，但不能把后续政策反应当成事件发生前已存在的因果事实。
32. [NEW][MED] 对客户的官方称呼如果出现“客户”“储户”“涉案资金”等差异，可能反映法律定性变化；后续Evidence应保留原词而不是统一改写成 depositor。
33. [REFINE][HIGH] claimant treatment 字段需要拆为 `access_restored`、`advance_paid`、`insurance_paid`、`criminal_recovery_paid`、`claim_transferred/subrogated`、`residual_claim_status`，不能只有“已兑付”。
34. [REFINE][HIGH] 银行状态需要同时记录 operating、payment-channel、license、legal-entity、ownership/governance 与 court/criminal action；河南事件尤其不能从 access_status 推断其他状态。
35. [REFINE][HIGH] “真实存款/账外资金”不是简单二元标签：可能存在银行真实开户但资金被转移、伪造后台记录、第三方代销误导等多种机制，具体分类必须证据化。
36. [REFINE][HIGH] 第三方平台导流与银行官方渠道之间的界线应通过域名/APP主体、合同、支付路径、银行流水与监管公告核对，而不能凭界面品牌感判断。
37. [REFINE][HIGH] 地方垫付与存保的主要区别之一是付款依据和追偿机制；后续Evidence应追“谁付款、凭什么付款、付款后原债权归谁”。
38. [REFINE][HIGH] 如果客户收到分档垫付但银行牌照仍存续，这说明 claimant support 与 institution exit 可以完全脱钩。
39. [REFINE][HIGH] 如果后续村镇银行被合并/重组，那也是垫付之后的另一阶段；时间模型必须允许 claimant payment 早于 entity resolution/consolidation。
40. [REFINE][HIGH] 省域银行整合不能用“新银行成立”作为旧行全部状态终点；旧行可能先持续营业、后业务迁移、再终止牌照/法人。
41. [REFINE][HIGH] 承接银行继受客户债权债务与存款保险关系可能需要新的 membership/insured-institution 时间段，不能假设保险身份自动无缝继承。
42. [REFINE][HIGH] 资本补充与资产负债承接可以先后发生：补资本用于稳定旧行并不等于旧行将继续长期独立，反之新行承接也不证明发生过亏损吸收。
43. [REFINE][HIGH] 对蒙商/辽沈/山西等案例应分别记录“为什么重组”的 contemporaneous reasons，而不是以后来整合结果反推所有原行都已资不抵债。
44. [REFINE][HIGH] `new_entity_formation`、`merger_by_absorption`、`business_transfer`、`license_termination` 和 `legal_entity_dissolution` 必须是五类动作，不应统一叫“合并”。
45. [REFINE][MED] 河南事件的客户跨省分布使 local-jurisdiction 与 bank-home-jurisdiction 可能不同，后续公告/诉讼/垫付主体要带 jurisdiction 字段。
46. [REFINE][MED] 客户通过互联网渠道购买“存款产品”时，营销名称、底层合同和最终资金去向三者可能不同，产品名不能作为法律定性的唯一依据。
47. [REFINE][MED] 刑事案件追回资产若用于补偿客户，需区分追回的是犯罪所得还是银行资产；否则会混淆银行损失与犯罪受害人损失。
48. [REFINE][MED] 对村镇银行的主发起行或股东处罚/整改属于 governance/owner state，不自动改变银行客户债权的法律性质。
49. [REFINE][MED] 省域整合中的客户“无感迁移”是服务连续性证据候选，但不等于原合同相对人从法律上从未变化。
50. [REFINE][MED] 2020-2022同片剩余高价值问题已从宽泛监管史收敛到个案法律/交易状态；继续盲猜数字、名单和付款依据的边际价值低。
51. [DUP][LOW] 账户无法访问不等于银行破产或牌照撤销。
52. [DUP][LOW] 地方垫付不等于存款保险赔付。
53. [DUP][LOW] 新银行成立、资产承接、旧行合并、牌照注销和法人消灭不是一个动作。
54. [DUP][LOW] 后续2023-2026的村镇银行改革化险结果不能倒填为2022已知状态。

## Challenge result

- The Henan village-bank episode requires a claimant/legal-characterization layer before any deposit-insurance conclusion: visible balance, bank-book recognition, contractual counterparty, fund flow, access state, alleged criminal/off-book mechanism and payment source are distinct.
- `advance_payment` and `deposit_insurance_reimbursement` must remain separate until the paying entity and legal basis are evidenced.
- Provincial small-bank consolidation requires separate event types for new entity formation, capitalization/ownership change, asset-liability transfer, merger, license termination, legal-entity dissolution and customer continuity.
- Remaining 2020-2022 uncertainty is predominantly exact legal, transaction, payout and institution-status detail; blind repetition in this slice has diminishing returns.
