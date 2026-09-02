# TIME-2017-2019 x SYS-REGULATION-RESOLUTION — blind-002 state challenge

**Authority:** `MEMORY_LEADS_ONLY`  
**Model vintage:** `GPT-5.6 Sol`  
**Session date:** `2026-09-02`  
**Source visibility:** `none`  
**Fresh Banking search:** `forbidden / not used`  
**Banking Evidence:** `not read`  
**Prior v2 / Batch0 / other-shard raw:** `not read`  
**Allowed-input digest:** `exploration-map.json@2ad76d0e53d0d1242eb425fa52a30225378f1024;china-banking-1990-2026-memory-exhaustion-manifest-v2.json@f1614308cb83f2426bef4a55c35b7cc85c432c92`

This is an isolated orthogonal blind challenge. It does not retell the financial-deleveraging chronology. It tests whether three remembered 2019 small-bank episodes can be represented without collapsing funding stress, liquidity support, claimant protection, recapitalization, takeover, license/entity state and market contagion.

1. [REFINE][HIGH] 包商银行在2019最稳妥的状态标签是“监管接管中的持续营业银行”，不能从“接管”直接推出当日牌照撤销、法人终止或法院破产。
2. [NEW][HIGH] 包商案应把“接管权/治理权变化”与“所有权经济损失”分开：接管组可能代行经营治理权，但原股东法律权益如何处置是另一层。
3. [NEW][HIGH] 包商接管前的主要风险路径更像治理/关联授信和资产质量问题叠加批发融资依赖，而不是单纯存款挤兑。
4. [REFINE][HIGH] 包商事件触发的同业/NCD信用分层是目标银行以外的市场状态变化，不能把其他小银行融资成本上升标成这些银行被resolution。
5. [NEW][HIGH] 因此案例矩阵需要一个“third-party contagion / market repricing”维度，与目标银行 operating/license/entity/claimant state 并列。
6. [REFINE][HIGH] 包商处置中的央行流动性稳定操作应被视为system/market support；即使特定银行也获得流动性，也不能等同于资本注入或债务减记。
7. [NEW][HIGH] 存款保险基金参与包商风险处置的记忆强，但“保险赔付”“基金出资收购”“承接支持”“央行再贷款/流动性”可能是不同现金流，需要逐项核验。
8. [REFINE][HIGH] 普通个人存款、小微/普通企业存款、大额公司存款、同业存款/同业存单必须分别建 claimant class；“存款人全保”过于粗糙。
9. [NEW][HIGH] 包商案可能存在“按客户/债权类别而非银行整体统一比例”处理的记忆，因此 claimant treatment 不能只有 recovered_fraction 一个字段。
10. [REFINE][HIGH] 对大额机构债权的差异化保护或折价记忆高度重要，但具体保障比例、门槛与债权种类不能凭记忆确定。
11. [NEW][MED] 次级债、二级资本债或其他资本工具若存在，其损失承担逻辑与普通存款/同业负债不同；具体包商工具存量未知。
12. [NEW][HIGH] 包商接管发生后仍允许日常支付/存取款的记忆意味着 operating continuity 可能被政策刻意维持，这本身是处置工具而不是“没有问题”的证据。
13. [REFINE][MED] 接管期限、是否延长及接管结束方式属于精确法律/行政事实，blind memory不应猜。
14. [NEW][HIGH] 包商后续资产负债转移到新设/承接银行应归入2020后Outcome链；2019 contemporaneous state只记录“可能存在未来承接路径”，避免lookahead。
15. [REFINE][HIGH] 锦州银行2019更接近“市场融资/信任受损 + 股权/资本重组 + 持续营业”，与包商行政接管不同。
16. [NEW][HIGH] 锦州案如果没有正式接管，就应把监管强度、股东变化与经营状态分开；“被救助”不是规范动作标签。
17. [REFINE][MED] 锦州财报/审计延迟是治理与信息可信度信号，但不是牌照、资本或债权人处置动作本身。
18. [NEW][HIGH] 锦州可能通过国有机构入股、资产处置/坏账清理、资本补充等组合修复；这些动作可以并行但不自动改变法人连续性。
19. [REFINE][MED] 工银投资、中国信达、中国长城等名字可能对应不同轮次/不同身份，需后续Evidence逐交易拆分。
20. [NEW][HIGH] 锦州存款人是否经历支付限制/差异化赔付并无高置信记忆；negative-space 倾向于“持续营业且未触发显性存款保险赔付”，但不能当事实发布。
21. [REFINE][HIGH] 恒丰银行2019更接近“长期治理失效 + 管理层案件 + 股东/资本重构 + 持续营业”，同样不应套包商接管模板。
22. [NEW][HIGH] 恒丰的管理层刑事案件属于个人司法状态，银行本身的license/entity/court_action必须另列，避免“董事长被判刑→银行被司法处置”的错误推断。
23. [REFINE][HIGH] 恒丰中央汇金/地方国资/战略投资者入股的记忆应归入 ownership/capital_action，不应写成 claimant haircut。
24. [NEW][MED] 恒丰若长期未正常披露财报，其“信息不透明”是 governance/disclosure state，不等于“无法经营”。
25. [NEW][HIGH] 三案比较显示“接管、重组、注资、治理整改、资产处置”是不同组合，不存在一个线性的统一resolution ladder能靠记忆直接套用。
26. [REFINE][HIGH] 统一矩阵至少需要：funding_stress、liquidity_support、capital_action、ownership_change、governance_control、supervisory_action、operating_status、license_status、legal_entity_status、asset_transfer、court_action、claimant_treatment。
27. [NEW][HIGH] 还需要knowledge_time/valid_time：同一个案例在2019不同月份可能从市场传闻/审计延迟变成正式股权重组或行政动作，不能用全年最终状态覆盖早期。
28. [NEW][MED] “风险处置”是上位政策词，下面可能包含接管、托管、重组、注资、并购、资产转让等，后续Evidence应保留原生动作词而不是先规范成resolution。
29. [REFINE][MED] “托管”与“接管”在中国金融监管语境可能有不同法律强度；blind memory不能互换，尤其在银行/非银机构之间。
30. [NEW][MED] 非银行机构如安邦保险的接管可提供术语对照但属于其他监管对象；不能用其法律程序填补商业银行案例。
31. [NEW][HIGH] 包商之后小银行同业存单发行失败/利差上升如果出现，应作为市场传染Evidence任务，而不是其他银行的个体处置Evidence。
32. [REFINE][MED] 央行对中小银行流动性支持可能通过公开市场、MLF/SLF、再贴现或对特定交易提供增信等多种渠道；具体工具需证据化。
33. [NEW][HIGH] 2019中小银行处置可能同时追求两套政策目标：维持支付/存款稳定，以及让大额机构债权重新承担信用风险；这两套目标可以同时成立。
34. [REFINE][HIGH] “打破刚兑”在这里至少有两层：资管产品投资者风险自担与银行大额机构债权风险重定价，不能与存款保险的法定保障混成一个概念。
35. [NEW][HIGH] 对包商类案例应记录“claimant communication”作为研究线索：官方公告如何向个人、企业、同业债权人解释保障范围，可能直接影响市场传染。
36. [NEW][MED] 同业市场上的质押品偏好、交易对手限额、NCD评级/发行期限变化可能是更细的传染渠道，值得后续证据检索。
37. [REFINE][HIGH] 股东/国资注资与央行流动性支持的损失承担者不同：前者改变资本/所有权，后者主要解决流动性或市场功能；模型必须分开。
38. [NEW][MED] AMC购买不良资产若发生，是asset_transfer/cleanup；除非同步有股权或牌照动作，否则不能称为银行resolution。
39. [REFINE][HIGH] 地方政府协调存款、国企入股或风险资产处置是地方支持工具，不能直接推出中央存款保险基金参与。
40. [NEW][HIGH] 如果银行继续营业但旧股东被大幅稀释/退出，这属于“经济控制权重构但法人/牌照连续”的可能状态，应允许单独表示。
41. [NEW][HIGH] 如果银行被接管但存款人日常账户连续、支付系统连续，则“服务连续性”与“治理权连续性”可完全相反，状态模型必须允许这种组合。
42. [REFINE][MED] 2019三案中真正需要后续Evidence回答的是谁承担损失、谁获得保护、何时改变控制权、牌照/法人何时变化，而不是“有没有救助”。
43. [NEW][MED] 对接管/重组事件的时间轴应避免把后续2020重组完成、承接银行开业或旧法人清算结果回填到2019的Judgment。
44. [REFINE][MED] 当时市场“会不会扩散成系统性小银行危机”的预期本身是Judgment lead，后续可通过 contemporaneous research/official communication恢复，但本blind challenge不发布该预期。
45. [NEW][HIGH] 2019的小银行风险处置可能是中国存款保险制度首次大型可见压力测试之一；这是高价值研究假设，不是已证实的法律结论。
46. [REFINE][HIGH] 若存款保险基金承担超出简单限额赔付的风险处置功能，后续Evidence需要区分法律授权、政策安排和实际资金流，不能只引用制度简介。
47. [DUP][LOW] 普通审慎整改、资本注入和resolution不能合并。
48. [DUP][LOW] 存款保险claimant protection与银行license/entity state必须分开。
49. [DUP][LOW] 后续Outcome不能重写2019当时状态。
50. [DUP][LOW] 管理层个人司法案件不能等于银行法人破产。
51. [REFINE][MED] 同一2019事件应保留“target-bank state”和“system contagion state”两张表，防止把市场稳定措施错误挂到目标银行本身。
52. [NEW][HIGH] blind challenge的negative-space结论是：三案里只有包商被高置信召回为正式行政接管；锦州和恒丰更像资本/所有权/治理重组，说明“small-bank stress cluster”内部处置工具显著异质。

## Challenge result

- A single binary `resolved/not_resolved` label is inadequate for the 2019 cluster.
- Target-bank state and third-party/system contagion state must be represented separately.
- Baoshang is the only high-confidence remembered formal takeover among the three; Jinzhou and Hengfeng remain distinct recapitalization/governance-restructuring patterns in blind memory.
- Exact claimant protection, fund flows, takeover powers, investor terms, legal-entity outcomes and later 2020 transfer/closure events remain deferred to claim-scoped Evidence.
