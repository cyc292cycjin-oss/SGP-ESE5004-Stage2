# A-06 科学假设与待决事项总账

2026-10-12。**已核实现、历史科学接受、未来研究选择分别记录。** 本轮只读授权不是对新政策/技术/价格的批准。VERIFIED=文件/源码/回执直接证据；DERIVATION=注明前提的解析结果；RISK=有具体结构依据但因果未证；UNKNOWN=证据缺失；PROPOSED=尚未实施建议。

| ID | 假设/改变 | 实际证据与审批状态 | 可行域/目标影响与下一决策 |
|---|---|---|---|
| A06-P01 | Baseline无年度CO₂cap | VERIFIED：两生产flag=false、LP无预算块；Phase3记录Baseline关闭。作者2025同样关闭，作者2050为100Mt | 不是net-zero；未来启用任何cap须单独确定范围/数值/可归属事件，不自动拷贝作者2050 |
| A06-P02 | PolicyPower与ReportingFullSystem分离 | VERIFIED代码，历史CARBON_SCOPE_FREEZE目标架构；200政策归属待定 | 当前off不形成隐藏约束；未来Power cap启用被pending阻断。归属方法仍需科学批准，不能给SMR/FT任意分摊 |
| A06-P03 | 捕集≠负排放，利用≠永久封存 | VERIFIED本地端口、源码事件；地质库未实际生成 | 国家内captured平衡可限制技术联合利用（RISK）；没有证据归因为求解异常。若研究封存须真实潜力/成本/非回提规则，不用欧洲200Mt模板 |
| A06-C01 | EUR2020共同价格年 | VERIFIED冻结price layer、`GATE4-20261006-FIXED-ACCOUNTS-EUR2020#B`及生产meta | 已记载接受；不重复平减。保留PENDING非EUR候选，不能凭出版年编价格年 |
| A06-C02 | 配置RES小额费用、DC旧噪声撤回、FT VOM接线 | VERIFIED：selected_closure_decisions ApprovalStatus=HUMAN_ACCEPTED；生产字段吻合 | 是目标变化/实现修正。历史“未批准”提案被后续具名决定限定替代，不覆盖旧报告 |
| A06-C03 | SCOPE_V3作者式噪声及最小范围例外 | 用户已批准；实际SHA及有效台账VERIFIED | 10,628,915列改变最优排序；不是原价最优性保证。其他有符号Store残余微扰没有被本轮证明无所有经济偏好，不新增试验 |
| A06-C04 | 既有FOM与固定offset一次计费 | VERIFIED固定列、3368项offset旧核算、实际双成本回执 | 8.2244911256bn FOM已含；不能追加。只验证当前目标核算，不认定失败候选为可信成本 |
| A06-R01 | 807终端商品Q源于需求而非独立潜力 | VERIFIED A02/A03生成路径；本轮按用户已明确的固定终端核算边界 | 不支持“807独立生物质潜力”研究解释；未来要改变为潜力模型是另一次科学设计，禁止直接恢复360TWh池 |
| A06-R02 | 807价格/排放因子NULL外账 | VERIFIED 807/807 NULL及FullSystemCost/EmissionsComplete=false；原边界保留 | 缺少完整成本/排放。情景抵消需完整不变性条件；未来决定priced subset还是补来源，不能NULL=0 |
| A06-R03 | 400外部化石供给，无有限产量上限 | VERIFIED每燃料100、源价与独立Bus；baseline接受无限扩容的外部市场表示 | 不是国内资源潜力，也不是免费燃料；运输/关税等是否在来源价格内UNKNOWN。作为未来经济比较假设需明确披露/确认 |
| A06-R04 | 国家内非电物理边界 | VERIFIED A05国别/端口；国内转换保留，共同物理池撤回，跨境非电路径关闭 | 改变可达性/可行域；当前固定终端义务的供应充分性待B，不自动启用运输 |
| A06-N01 | 2050沿用2025电网输入集合 | VERIFIED锁定参考SHA及118资产/端口；不继承优化容量的工程理由明确 | 未纳入作者2050多15跨境项目；逐项科学舍弃理由UNKNOWN。需用户决定研究基线的候选集，不自动恢复 |
| A06-N02 | 作者2050项目是真实输入兼历史结果 | VERIFIED实际建造年/名义/扩展/优化容量；新/升级源码机制 | 原AC项目逐行源映射、升级1043→491.4MW中间链UNKNOWN。不得把历史最优容量作为现存或必建规模 |
| A06-T01 | 2050存量采用source-qualified surviving stock | VERIFIED生产meta决定`GATE4-20261006-FINAL-CLOSURE#C`；745源单位、187400.4MW记为合格源覆盖 | 不等于所有2050实际存量完整。未合格存量排除、局部潜力与固定需求可能冲突，待B必要条件核查 |
| A06-S01 | 方案A最小源常数修复 | 用户与ChatGPT已接受；PR #4 SCHEME_A_STATIC_ACCEPTED；385/385 D≤Q′、180Q、720同步字段、Load不变 | 改变极小精确库存常数/可行域，不是坐标缩放；尚未进入新NetCDF/LP。旧不可行证书仍对旧LP成立 |
| A06-V01 | V3/P2/V4三者性质 | VERIFIED：目标变化／等价坐标／独立数值验收；旧两次结果明确 | 不修复物理结构、不为未知价格补值；V4通过不能自动证明有理最优或原价最优 |
| A06-E01 | Integrated/Disconnected经济干预 | A05确认两配置目前空身份；无正式成对结果 | 比较前必须定义仅切断何种跨境资产、共同预算处理及固定项不变性；当前UNDEFINED，不是本轮可执行任务 |

## A阶段闭环

S0、A01–A06完成各自授权的现有证据审计；“完成”指事实与UNKNOWN已入账，**不是所有科学决策都已批准**。A03旧LP至少一组完整精确矛盾已证；方案A只关闭源级D>Q问题，尚无新完整LP证明。10.24TWh超用与P2 Presolve INF_OR_UNBD的根因不能由微小源差、无地质库或未来线路缺失中的任一项单独断言。

建议下一阶段B只在用户授权后围绕冻结需求、可用供应、库存/转换/网络必要条件核查。进入B不要求先选新求解器；也不要求把本表所有长期研究未知项先填造为数值。正式情景计算前需确定N01、R02/R03、E01及将来的政策范围；若保持无cap研究，P02归属未完成应披露而非假装net-zero。

B—F未启动；G6-05 PAUSED_BY_USER。方案A、V3/V4/P2、历史结论及消费标记未改。

证据入口：[主报告](A06_POLICY_COST_RESOURCE_AUDIT.md)、[成本口径](A06_COST_COMPARABILITY_ASSESSMENT.md)、[源代码与历史决策](evidence/A06_SOURCE_CODE_AND_SAFE_CONFIG.json)、[资源边界](evidence/A06_RESOURCE_CARBON_BOUNDARIES.json)、[验收回执](evidence/A06_VALIDATION_RECEIPT.json)。
