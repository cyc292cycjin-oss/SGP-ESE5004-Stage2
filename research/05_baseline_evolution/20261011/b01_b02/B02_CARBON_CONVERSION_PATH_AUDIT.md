# B-02 碳与能源转换实际路径审计

2026-10-12；**B02_COMPLETE_WITH_EXPLICIT_LIMITS**。冻结模型有真实碳物质守恒，Baseline年度CO₂政策上限关闭。SMR CC不是独立的永久封存路径，捕集CO₂必须在本地由FT消耗。未发现这些可选转换自身构成强制需求矛盾的证据。

## 1. 实际多端口而非名称推断

身份沿用[B01四对象](B01_RESOURCE_DEMAND_FEASIBILITY_AUDIT.md#1-四个身份与适用范围)。[B02_MULTIPORT_AND_CARBON_BALANCE.json](evidence/B02_MULTIPORT_AND_CARBON_BALANCE.json)列出全部100个captured-CO₂、100个H₂、100个oil Bus的**完整非零Link入射端口**、连接Store/Generator/Load及容量方向。国家来自Bus.country/确定的Bus.location，不按名字猜测。

令Link-p为正向入口量，正系数为产出、负系数为同时输入；所有下表转换p_min=0、p_nom_min=0、p_nom可扩建且max=∞。单位：能量端口MW，CO₂端口t/h；三个小时权重用于累计能量/质量。所有100节点系数一致；精确binary64分数在JSON中。

| 实际技术 | 输入 | 输出 | 核查结论 |
|---|---|---|---|
| SMR CC | gas −1 | H₂ +0.69；大气 +0.019799999999999998；本地captured-CO₂ +0.17820000000000003 | bus2为未捕集排放，bus3为转移；捕集不是负排放credit。 |
| SMR | gas −1 | H₂ +0.76；大气 +0.198 | 直接本地供氢，不使用captured-CO₂。 |
| Electrolysis | 本地电 −1 | H₂ +0.6994 | AC和DC节点均按真实端口覆盖，不能漏掉2个DC节点。 |
| FT | H₂ −1；captured-CO₂ −0.20542290000000002；本地电 −0.005275056518462698 | oil +0.799 | CO₂和电力是必需共输入，不是FT“发出”CO₂或电力。 |
| Fuel cell | H₂ −1 | 本地电 +0.5 | 可回电，但电解—燃料电池乘积约0.3497<1，不是免费能源循环。 |
| H₂ tank | Store功率可充放；库存动态 | 100个循环、零损失、容量可扩建的本地库存 | 初始缓冲/期内转移不能提供全年净H₂；没有外部H₂ Generator或固定H₂ Load。 |

没有地质CO₂ Store、CO₂进口Generator、captured-CO₂ Load或额外旁路。H₂无跨境运输；本地消费为100 FT和100 Fuel Cell，供给为100电解、100 SMR、100 SMR CC及期内储存。没有凭氨/甲醇等候选参数添加新端口。

## 2. 没有CO₂库的必要联动关系

每个捕集Bus恰有两条Link：SMR CC正输出a、FT负输入b。**DERIVATION，直接由完整静态入射集与Bus等式：**每时段

`a s_t − b f_t = 0`，其中`s_t=SMR_CC气输入`、`f_t=FT氢输入`。

精确binary64：`a=1605082907194845/9007199254740992`，`b=3700569983573467/18014398509481984`，所以

`f_t/s_t = 3210165814389690/3700569983573467 ≈ 0.8674787475008873`（s>0时）。

每1 MWh气进入SMR CC，关联FT需0.8674787475 MWh H₂，而CC自身仅产0.69，因此还需约**0.1774787475 MWh H₂**，来自本地非CC SMR、电解或当期库存释放；同一FT额外用电约**0.00457599942 MWh**，产油约**0.69311551925 MWh**。FT本身没有足够端口让SMR CC单独闭合。H₂循环库存只能移时，不能补全年净缺口。若还运行Fuel Cell，其H₂需求继续增加。

这是100节点独立精确Fraction推导，不是调用求解器或假定某个实际调度。各Bus消元结果由[独立核验回执](evidence/B_INDEPENDENT_CHECK_RECEIPT.json)复核。

**因此没有地质库并非“没有碳平衡限制”**：CC无法长期单独制氢，必须跟随FT及其油品消纳。也不能据此宣布全模型不可行：CC/FT最低出力与最低容量均0，存在外部化石oil及其他H₂生产路径，没有固定必须使用CC的义务。

## 3. FT油、外部油与最终Load不重复计量

100个oil Bus均无Store、无直接Load，具有一个本地external oil Generator和一个FT；输出为最终oil meter，另有8个存量oil发电Link分布在其中。819个最终oil Load在各自独占义务Bus，由效率1的meter连接，而不是在源oil Bus重复挂同一Load。

每个节点的实际oil平衡为：

`0.799 f_t + external_oil_t = Σ final_oil_meter_t + Σ existing_oil_power_input_t`。

所有相关流量单向非负，最终meter被其独占Bus固定Load约束；存量oil电厂容量有限。故局部必要上限为

`0.799 f_t ≤ 本地固定oil需求_t + 存量oil电厂最大燃料输入`。

结合上节，可给出每节点SMR CC的有限必要流量上限，尽管CC/FT名义投资上限为∞。[B02_LOCAL_OIL_SINK_LIMITS.json](evidence/B02_LOCAL_OIL_SINK_LIMITS.json)保存100节点每条Load/电厂、精确上限及公式；100节点均有正消纳上界，没有推得某节点FT/CC被迫恒零。该上界不是实际可达到的联合发电/电网方案。

这说明：FT油可替代同Bus的外部油，不会再制造第二个必须满足的最终Load；但当前oil需求也不能无限吸收FT产物。没有发现无限油品排空、免费氢源或captured-CO₂无限丢弃路径。没有将此有限路径审计扩大为全网络不存在任何经济循环的证明。

碳账方面，FT将CO₂带入油品，最终燃料meter或oil电厂在使用时报告CO₂；外部oil与合成oil共享同一商品Bus。这是物理排放事件的统一记账，不是永久封存。混合来源的政策归属资格沿A06继续待决；**本轮没有新增负排放或净零认证**。小数端口源值及其微小binary64算术差保留，不静默“修正”系数。

## 4. 大气核算与政策边界

1748条实际Link的大气端口均正系数且p_min=0；没有通过反向转换从大气提取能源。唯一大气Store为可扩建、e_nom_max=∞、e_min_pu=−1、e_max_pu=1、e_initial=0、非循环、无损失；其可选容量允许累积排放，不构成有限年度cap。大气Store是显式报告账户，不是地质库，不能当成能源供给或负排放技术。

复用A06与旧LP局部容量行证据：实际GlobalConstraint只有`lv_limit`，没有生效年度CO₂政策上限或碳价；没有DEC新情景。**碳守恒≠碳政策，更不等于net-zero**。807终端固定资源的NULL排放因子仍为待核资格，不能用当前物理记账范围声称完整全系统排放已量化。

## 5. 科学含义与历史异常

- VERIFIED/DERIVATION：缺地质库使CC捕集与FT共用需求强联动，限制技术可达运行范围。若未来要求大量CC或净零，这个边界需科学审议；本轮保持不变。
- VERIFIED：当前终端oil/gas/coal有外部市场直达路径，固定biomass独占，电力有本地CCGT。因此不能把关闭CO₂库或非电跨境直接定为当前固定需求失供原因。
- NOT_PROVEN：这项联动是否导致第一次10.24TWh资源超用、第二次INF_OR_UNBD或其他数值停滞。没有新实际解、对照实验或完整新LP证据支持该因果关系。
- 未改变V3/P2数值表达、V4标准、Scheme A、旧证书和历史结果；没有新优化、构模、AutoDL操作或G6-05恢复。

本轮到此完成；后续科学判断与剩余联合可行性风险见[B_PHYSICAL_FEASIBILITY_RISK_REGISTER.md](B_PHYSICAL_FEASIBILITY_RISK_REGISTER.md)，等待联合审阅。
