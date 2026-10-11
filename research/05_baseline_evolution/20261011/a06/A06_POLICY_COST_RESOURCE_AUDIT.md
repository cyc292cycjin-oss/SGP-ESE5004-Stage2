# A-06 碳政策、成本与资源边界审计

2026-10-12 · **A06_COMPLETE_WITH_EXPLICIT_UNKNOWNS**。只读审计完成，不是模型可行性、净零或经济比较认证。G6-05维持PAUSED_BY_USER；未构模、调用求解器、修改科学文件或操作AutoDL。

当前冻结2050 Full-SC是**无年度碳政策上限的Baseline**，不能称net-zero。它采用2025参考电网的输入集合、重新核定的2050技术/成本和新增终端需求；不是作者2050脱碳结果网络的完整复现。807个生物质账户是固定终端核算边界，400个化石供给是有价但无有限供应上限的外部来源。方案A只修订派生源常数，尚无新完整网络或LP。

## 1. 六种身份，不混用证据

| 对象 | 已核身份 | 可以证明／不能证明 |
|---|---|---|
| 作者2025实际结果 | `5bacad702ccfed17ad19ab510fa710651e966f2c`；NetCDF SHA `06152be56ee41f64bfdca42fd24aeaf363ab61f931fec7b5e4bc12f6d6456ecb` | baseline-aims-3H；已求解文件的输入字段可能含noisy_costs；不能称未扰动原始配置 |
| 作者2050实际结果 | 同一运行源码；NetCDF SHA `3ac28875630cffbf8b7f3b1e80dbc7eb293d36e7f62efd1578beec457d54d745` | decarbonize-aims-3H；myopic历史投资与结果容量；不能照搬为当前既有库存 |
| 上游Sector Coupling能力 | `a3616a68ee44592af6527ca9024a90f1956646ae` | 功能源码，不等于作者结果中全部启用；论文release参考`99159edb7298b847fea517bf05c3f388493501c9`亦不替代实际运行commit |
| 冻结Full-SC NetCDF | 科学源码`b9be7d0ab788a4151346c098d2e657c7e94a22da`；构建manifest代码`4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce`；网络SHA `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d` | 2050目标年，100地理节点，2920×3h；区别于已求解网络 |
| Gate6 V3/P2 | V3 SHA `6dffbe0e687fdd85f161c132d96ac846266e0a5864c5daacd3772dbeae2486b4`；P2表达SHA `ff3db589f82c8f68b23868f6c7186fb35ac6bf77d9171c21a9edeb146c24a227`；V4 SHA `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f` | V3改变求解目标，P2为α=1正对角幂二坐标变换；两者不同。第一次OPTIMAL/V4不通过；第二次INF_OR_UNBD、无解，不改写历史 |
| 方案A新配方 | PR #4交付`8883de6fb3e15767c632ac92f535e8a423e90b69`；版本manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720` | SCHEME_A_STATIC_ACCEPTED：180Q、720同步字段；385组精确D≤Q′。未组装，不能用来解释旧运行已修复 |

来源：[网络静态回读](evidence/A06_NETWORK_STATIC_READOUT.json)、[复用身份与验收](evidence/A06_PRIOR_ACCEPTANCE_AND_IDENTITY.json)、[A05身份索引](../a05/evidence/A05_SOURCE_AND_DECISION_EVIDENCE.json)。大文件SHA复用已验索引；本轮仅新增读取静态字段和三套小权重向量，没有重新扫描CSC或解向量。

## 2. 碳政策：值、范围、单位与实际实现

| 对象 | NetCDF中的GlobalConstraint | 实际含义 |
|---|---|---|
| 作者2025 | 仅`lv_limit ≤353746853.52332264` | 输电容量×长度，MW·km；`co2_budget.enable=false` |
| 作者2050 | 同一lv_limit；`CO2Limit ≤100000000`，type=primary_energy，carrier_attribute=co2_emissions | 100 MtCO₂/年；不是0，也不是全经济所有GHG净零。源码按1e9×0.1×8760/8760形成该值 |
| 当前Full-SC | 仅同一lv_limit；policy_enabled=false、policy_cap_actually_enabled=false | 真正生效的碳cap不存在。配置2050的100Mt轨迹是关闭状态，不能当作0排放或已安装约束 |

**VERIFIED。** 三个网络的objective/generators/stores权重均2920个3小时，总8760小时。作者`prepare_sector_network.py:2973–3009`和`prepare_network.py:152–159`没有按终端Power用途过滤；该通用primary_energy约束依赖carrier排放因子、Generator流和非循环Store库存变化。在作者仅保留电力系统的网络中，它是该系统的碳汇总约束，而非可直接扩展到Full-SC的部门分摊契约。作者CO₂ carrier因子−1与atmosphere库存承担排放核算；不能只按化石Generator名字识别范围。源码记录见[固定源码](evidence/A06_SOURCE_CODE_AND_SAFE_CONFIG.json)。

**重要证据边界。** 作者`solve_network.py:898–913`还会对`co2 stored`末期库存求和施加`co2_sequestration_limit`；实际配置值200×1e6 tCO₂，代码仍带欧洲潜力TODO。这是额外的Linopy运行时hook，不必成为NetCDF GlobalConstraint表的一行。两份结果确有co2 stored Store，代码调用链和配置支持该hook；本轮没有作者原生LP/约束回执，故“运行时该行逐值存在”标为NOT_REVERIFIED_FROM_AUTHOR_LP，不能凭NetCDF只列1/2行而宣称不存在其他约束。200Mt是封存库存潜力，不是排放cap；配置10 EUR/t是源码Store容量费用，不是碳税。不能无依据复制为各国地质潜力。

当前模型的“无cap”证据比表格更强：复用既有1037块冻结LP审计，未见CO₂预算/DEC政策块；唯一全局行0-based **45945301**有115项，分别105 AC Line的s_nom×length及10 DC Link的p_nom×length。它限制输电扩建，不是碳预算。完整矩阵审计原件SHA见[外部证据索引](evidence/A06_EXTERNAL_EVIDENCE_INDEX.json)，本轮不重扫。既有`independent_checks.json`未找到的限制保留，不能伪称读过；使用已绑定的GATE6_PREFLIGHT、配置和实际LP证据。

### 2.1 Carbon守恒、报告与政策不是同一件事

- **物理层VERIFIED：** 本地燃料转换经CO₂端口进入报告atmosphere；captured CO₂须在本地Bus守恒。当前carrier.co2_emissions被置零，避免通用carrier再次重复核算；并不表示实际排放为零。
- **报告层VERIFIED：** `carbon_architecture.py:53–140`按事件分配Power与FullSystem视图；capture transfer自身不发放负排放信用，FT回排单独记录；生物质生命周期吸收不凭空补入。807账户的未知排放因子使FullSystemEmissionsComplete=false。
- **政策层VERIFIED：** `install_power_policy:143–180`在enabled=false直接返回；未来开启须有完整、已批准的Power归属权重。既有记录有200项政策归属待定。没有将全部终端碳流无条件放入原Power cap，也没有自动国家配额。
- **设计与生产对照：** Phase3 CARBON_SCOPE_FREEZE规定Baseline关闭、DEC保留Power轨迹，符合当前Baseline；但把历史“2050脱碳”或未来Integrated/Disconnected共同Power预算直接当作当前事实不成立。DEC文件名不是当前政策激活证据。

### 2.2 CCS、SMR CC、FT、封存与负排放

| 机制 | 上游/作者 | 当前冻结Full-SC及边界 |
|---|---|---|
| captured CO₂ | 无CO₂管道时仍有共同Earth co2 stored池，可连接多国并供FT/Sabatier | 国家/节点本地captured Bus；没有共享物理碳池 |
| SMR CC | 作者98个；捕集为技术流 | 当前100个，效率0.69；每MWh气输入约0.1782t进入captured，0.0198t进atmosphere。不是已永久封存 |
| FT | 作者98个；H₂+CO₂转油并耗电 | 当前100个；H₂−1、oil+0.799、CO₂−0.2054229、电−0.005275056518462698；回收后燃烧不能称永久负排放 |
| 地质封存 | 上游可建Store及200Mt总库存hook | 当前没有captured/geological Store；geological_storage_asset=false。本地捕集不能借助不存在的地质库消纳 |
| DAC/负排放 | 配置dac=true是能力；作者最终保留由静态资产决定 | 当前无DAC资产及反向atmosphere提取路径；CO₂端口没有凭空的负排放奖励。不能把SMR CC或FT标签当负排放 |
| Atmosphere | 统计库存 | 当前e_nom可扩展、上限∞、e_min_pu=−1、e_initial=0、noncyclic，无终期归零，无科学成本；不构成隐藏碳上限 |

解析边界：当前对任何有限atmosphere轨迹，可选E≥max|e_t|满足其±E界；旧矩阵5841项容量关联及2920状态行已回读。此结论仅针对碳库存cap，不表示任意能源调度都可行。证据：[资源碳静态字段](evidence/A06_RESOURCE_CARBON_BOUNDARIES.json)、[已有Atmosphere矩阵补证](evidence/BASELINE_CARBON_CAPACITY_SUPPLEMENT.json)、A05实际端口审计。

## 3. 成本谱系与目标：重要差异

详见[成本可比性报告](A06_COST_COMPARABILITY_ASSESSMENT.md)。已证实：

1. 作者成本来自technology-data v0.13.2和ASEAN AEO8追加数据；资本年化含寿命、折现率与FOM，运行费用按时段权重。作者网络meta的electricity costs.year=2030不能解读为所有2050技术都使用2030参数；sector处理入口按当期cost文件，2050 FT资本已与2025不同。原始报价全链和每项外部价格的独立代表性不在本轮重新评估。
2. 当前统一EUR2020层SHA `81ed8c8468f5d2d2e1f0568bb2fc85bec393b63cdb3d7b5d247657412a2b9ec7`：既已上游平减的investment/VOM/fuel不再重复平减；既有FOM为8,224,491,125.573893 EUR/年，冻结LP固定列计一次。
3. 当前原科学网络清除了13 DC/B2B继承的边际噪声，资本重算；100 FT的真实VOM接线为1.7842469 EUR2020/MWh输入，而作者结果约0.009–0.011主要为噪声；保留配置solar0.01、on/offwind0.015为明确模型费用，不冒称来源化技术VOM。
4. V3再加入作者式辅助成本，但排除12有符号DC/B2B、98有符号配电、Atmosphere及807 Store+807 meter；10,628,915列改变，offset−12,788,967.997821666 EUR。单向DC仍可有扰动。**目标改变已批准，但不是数学等价缩放，也不保证原未扰动目标最优。**
5. 400外部化石源每燃料100个；煤9.5542、气24.568、褐煤3.2985、油52.9111 EUR2020/MWh输入，投资费用0但燃料收费；p_nom可扩展、max∞。燃料费在源Generator计，转换Link加VOM×效率，不应再次叠加同份燃料。
6. 807未知价格保留NULL并外账Q×unknown；零LP系数不等于免费资源。不得宣称全系统成本完整，也不能在尚无成对可接受解时假定未知项自动抵消。

## 4. 资源、技术与电网边界

**共同池→隔离账户是实质科学变化。** 作者Earth solid biomass Store为360TWh有限库存，连接多国电力相关用途；lignite有共同可扩展供给+循环Store，不能把其e_initial=0理解为零资源；co2 stored为共享物理碳池。当前807账户按国家/部门/商品/节点独占，经meter接385个最终需求，Q由终端需求分配而来，不能称独立资源潜力。外部化石源则无有限年度供给量约束。统一这些边界的科学合理性不能由优化返回状态决定。

**为何2050继承2025电网。** `build_research_assets.py:41–83`锁定2025参考SHA，复制电力输入资产/边界并只保留输电GlobalConstraint；`clean_table`排除优化结果。技术成本重算到2050，存量采用另行接受的source-qualified survivor规则，而非照搬作者myopic优化投资。当前118个Line/DC/B2B ID和端口与作者2025相同（A05已验）；对应收益是避免继承内生结果，代价是未自动纳入作者2050项目集。**逐项排除15个跨境项目的科学批准理由仍UNKNOWN**，不能由上述工程机制反推用户逐项接受。

作者2050比2025多22个电力输入资产：7 AC+15 DC，其中跨境15项、国内7 DC。本轮仅为15跨境项补读历史优化容量，不把国内项混入跨境总数。七AC都有2027–2030建造年和可扩展标志；八DC含一项升级、其余新建/规划/考虑中项目。所有15项在实际2050网络中已激活，非仅配置候选；同时均保存历史优化输出，二者可以并存。

| 代表项 | 输入名义容量MW | 作者结果容量MW | 可证明的分类 |
|---|---:|---:|---|
| AC 29（ID–SG，A05端口判定） |167.58|15497.058655876626|实际项目输入+历史扩建结果；原始CSV行映射仍UNKNOWN |
| Peranap–Singapore |1600|7254.536869143658|AIMS规划新Link；不是当前既有7254MW |
| Plentong–Woodlands DC |525|525.0122922246894|AIMS in_planning，2030；不能把0.012的浮点差当新工程事实 |
| 250878579-2_0_upgraded |491.4|491.41208190150036|源码有升级/退役调整机制；原AIMS upgraded行1043MW到此491.4MW的完整中间变换未取到，不能声称容量逐项复现 |

全部15项含原始字段/源CSV候选及不确定性见[项目分类](evidence/A06_AUTHOR2050_PROJECT_CLASSIFICATION.json)。名称仅用于定位，国别沿用已验Bus.country/location；未靠名字判跨境。没有恢复任何线路。

## 5. A阶段综合判定与进入B前最小事项

| 类别 | 已确定结果 | 尚不能推出 |
|---|---|---|
| 物理/数据变化 | Full-SC需求恢复、独占807/385、国内载体边界、400外部源、source-qualified存量、2025电网集合+2050技术参数 | 全LP可行、各关闭路径是失败原因 |
| 目标变化 | EUR2020、固定FOM一次、真实VOM接线、明确配置费用、V3获批扰动和例外 | 完整成本、未扰动目标严格最优、正式情景节约 |
| 纯数值/验收 | P2正对角幂二坐标、Gurobi参数、V4数值资格 | 不改变精确可行域的操作能消除旧源常数矛盾 |
| 已通过 | A03完整局部不可行证书；A04需求谱系有限检查；方案A源静态验收；A05端口核查；本轮17项证据一致性检查 | 新Scheme A完整LP已经通过 |
| 具体风险 | 旧LP精确D>Q；存量/供给边界、未继承未来电网、无地质消纳与固定终端需求的联合能力待B核查 | 微小源差导致10.24TWh超用/INF_OR_UNBD的因果已确定 |

进入B前需要用户确认审计范围，并保留以下输入证据：①2025电网作为2050基线的候选集合决定（包括15项目的逐项取舍或继续明确排除）；②外部无上限化石供给与固定终端生物质核算的比较语义；③若研究转向脱碳，Power/FullSystem范围与200项归属、地质潜力及生物质排放/价格的证据；④经济比较所需未知固定项是否不变的规则。前三项不能通过本轮静默修改。原作者项目中间映射缺口不阻断读取当前网络开展已授权B必要条件审计，但须保留为上游溯源UNKNOWN。

建议下一步**仅提交B阶段范围审批**，以方案A配方及不变拓扑做物理约束/输入一致性审计；不自动构模或求解。A阶段的“审计完成”保留UNKNOWN，不等于科学边界全部终审通过。

本轮修改仅在独立A06审计分支；PR #3/#4/#5及旧科学记录保留。最终真实提交、PR和ZIP见台账发布记录与包内manifest。
