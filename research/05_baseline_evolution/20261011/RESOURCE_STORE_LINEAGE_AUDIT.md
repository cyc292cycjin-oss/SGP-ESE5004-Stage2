# Resource Store lineage audit

2026-10-11；A-02：**COMPLETE_WITH_EXPLICIT_UNKNOWNS**。只读源码、冻结NetCDF的静态字段/元数据、两个UNSD原始文件及既有残差摘要；没有创建PyPSA模型、扫描完整CSC、重跑工程测试或调用求解器。

**结论：807个账户不是上游807项独立资源潜力，也不是原生Store机制的全新发明。** 项目复用了PyPSA库存方程，但新建了“终端年度义务→商品份额→节点独占库存→单向meter→final obligation Load”结构。当前冻结网络没有上游solid biomass/biogas潜力Store与这些账户并行。首次候选解的资源/节点违规确实发生在此结构；尚未证明该结构必然导致全LP不可行或第二次INF_OR_UNBD。

证据等级与固定commit链接沿用[差异总账](UPSTREAM_TO_FULL_SC_CHANGE_REGISTER.md)。本页“已通过”仅指所引静态/历史检查，不提升第一次OPTIMAL / V4 NOT_ACCEPTED或第二次INF_OR_UNBD的资格。

## 1. 上游原本如何建资源Store

固定SC参考 `a3616a68ee44592af6527ca9024a90f1956646ae` 的[add_biomass](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L1118)：

| 内容 | 上游实现/有效含义 | 当前差异 |
|---|---|---|
| 资源量来源 | solid_biomass_potential、biogas_potential；参数TWh/a×10⁶→MWh（1189、1228行）；多节点按人口权重，单池取全部 | 当前Q来自被接受的终端需求，不来自独立技术/可持续供给潜力调查 |
| 有限/无限分支 | 有限且正数：Store e_nom=e_initial=Q；无限：可扩建Generator；零：不增加资源（1164–1238） | 807全部有限固定Store，无补给Generator |
| 空间 | biomass_transport=true为节点池，false为Earth solid biomass；biogas空间由gas设定（1004–1070） | 国家/节点/部门账户/商品分别隔离，禁止跨国或跨用途借用 |
| 用途/成本 | 上游biomass EOP等转换可用相应资源池；Store marginal_cost取solid biomass/biogas fuel价格（1197、1236、1245–1261） | 当前meter仅向其final obligation Bus；不供应额外电力、H2或其他部门，未知商品价与CO₂因子NULL |
| 初始/库存/循环 | 原生Store默认非循环、下界0、上界e_nom、standing_loss=0。有限资源是**预装初始库存**，不是每期重新流入Q | 当前保留该递推与固定库存概念，另明确discharge-only hook |

论文两份结果有效配置为360 TWh/a、0.5 TWh/a、biomass_transport=false；上游default为40/0.5且transport=true。不要把参数文件可能值当作每次论文实际组件清单。论文only_elec_network筛选仍可留下与电力相关的solid biomass/EOP等，不能称论文完全没有Store/H2。原论文结果全组件逐项拓扑未在本轮重新提取，相关完整同构关系UNKNOWN。

## 2. 原生方程与项目新增部分

本地参考PyPSA **0.30.3** 的 `optimization/constraints.py:858–929`、`component_attrs/stores.csv`已只读核SHA；见[SOURCE_LINEAGE_INDEX](evidence/SOURCE_LINEAGE_INDEX.json)。它用于交叉说明机制，不冒称本轮检查了云端安装文件。冻结矩阵/标签残差证据另来自已完成的Gate6审计。

在单年索引、零损耗、非循环、所有快照有效的这些资源账户上：

`e(i,0)=Q_i−w_0 p(i,0)`，`e(i,t)=e(i,t−1)−w_t p(i,t)`；`0≤e(i,t)≤Q_i`。

其中e、Q为MWh，p为MW，w_t=3h；p>0表示向资源Bus放电。一般有损Store是 `(1−standing_loss)^w × previous_e−w p=e`；循环Store首期接末期，e_initial被忽略。**这些原生定义没有被我们改写。** 储能效率在当前meter为1；没有把“3小时”再乘进效率。Store也不同于有独立inflow属性的StorageUnit，807账户没有额外自然入流。

项目新增/显式化部分：

- [carrier_architecture.py:250–256](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/carrier_architecture.py#L250)移除Store不支持的p_min_pu/p_max_pu输入并保存store_power_rules，289–303行真正增加 `Store-p≥0`。不能只看构造参数p_min_pu就宣称方向已生效；实际冻结LP的807个ResearchStoreDirection块已在先前矩阵审计确认。
- [assembly_components.py:94–113](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/assembly_components.py#L94)安装hooks；新增的是方向与资产/电池挂钩，不是私写库存递推。
- [fixed_accounts.py:38–67](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/fixed_accounts.py#L38)要求固定e_nom=e_initial=Q、非循环、无损耗、e_min=0/e_max=1，无其他供给/用途，单一正向二端口meter，效率1；对目标Bus也禁止额外源、库存或旁路。
- meter p_nom可扩建、p_nom_max=∞，未另强制某商品逐期固定释放曲线。**逐期Load必须满足，但组内不同商品的释放时序可以替代**；每个商品年度可用量仍分别受Q限制。固定资源的年度/前缀V4检查是解的验收层，不可全部冒称另加的LP行。

## 3. 807的真实生成链与时间

1. `reconstruct_base_accounts.py:57–85、148`保留UNSD源文件SHA/物理行号/商品/单位；TJ→MWh除0.0036；kton按冻结商品系数；0.90 GCV→NCV只用于明确的天然气源系列，不泛用到Biogases。商品热值仍是继承的数据假设，不是本轮重新测定。
2. `registry.json`接收2019基数、已批准2050增长/重叠处理，形成独立InputID。AEO8区域增长代理不等于每个国家/商品独立预测。
3. [allocate_assembly_inputs.py:49–78](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/allocate_assembly_inputs.py#L49)按同国作者2025**输入电负荷年量份额**分节点，燃料采用全年平坦时间形状；33个biomass账户的实际Manifest均记录 `AUTHOR_BASE_LOAD_ANNUAL_NODE_SHARES_FLAT_TIME`。这不是实际逐时生物质消费观测，也不是优化结果dispatch。现有allocations.npz SHA `931c24aac84be29eda6b2a1906a8e85ca0f3876b90c26cdb3b40e84ad8d3b2b9`复用，不重新扫描。
4. [build_research_assets.py:214–249](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/build_research_assets.py#L214)：
   `q(node,input)=Σ_t 3×d(node,input,t)`；按同国/账户的原始商品MWh份额 `s_commodity` 构造 `Q_i=q×s_commodity`。正年度节点才建账户，Store/meter源身份直接写入原始RowID。
5. `build_research_network.py:142–168`拒绝带旧Load的电力base，合并无Load配方后只绑定一次。`assembly_components.py:49–67`把同一数组送入唯一Load；Q与Load来自同一allocation，但分别经浮点累加/比例乘法生成。
6. 端口路径为 `Store(p,e) → resource Bus → meter Link(bus0消耗、bus1注入) → final obligation Bus → Load`。没有连接原solid biomass总池、其他需求Bus或电网的资源供应捷径。

| 时间/commit | 实际变化及为什么 |
|---|---|
| 2026-10-05 07:31 +08，`18eb5827e4e19588dc4f31b8355319818c5fb950` | 首次加入当前固定resource/meter配方（当时223–228行已有Q/e_initial/route）。为缺商品价/碳因子的生物质义务保留物理量并隔离额外用途；当时仍存在资格阻碍。不能说807是10月10日Gurobi微扰才创造。 |
| 10-06 01:27，`b21aa365a5ea750bc6a48b1424b09e9880caa07d` | 外置待核固定账方法，重新验证实际独占结构后允许物理装配；价格与排放报告仍不完整，并非把未知值科学上变成0。 |
| 10-06 08:46，`cfc7b531c221647bffe8dda46b3c8ef5b4e954f9` | 单独批准菲律宾工业Animal waste源账户，2050总量477,866.275143678…MWh；条件为结构验证及价格/因子继续NULL，未授权新技术。对应5个节点Store。 |
| 10-06 09:05，Manifest `4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce` | 最终冻结网络实际807/385；“807”是输入商品×正节点的产物，不是上游常数，也不是此commit新增807行代码。 |
| 10-06 13:10，`002f2a6dcbd4d57335653867e8f12a2b024c93ec` | 旧固定库存归一化；后有P2表达。改变求解坐标，不改变Q、义务或端口。 |

实际数量来自[RESOURCE_STATIC_LINEAGE](evidence/RESOURCE_STATIC_LINEAGE.json)：**61个原始RowID→33个2050国家/部门InputID→385个节点义务组→807个Store和807个meter**。Q总计约1,607,166,223.273845 MWh（1607.166TWh）、最小0.708180208 MWh、最大179,985,300.577287 MWh；无零Q。不能把该总量同上游360TWh技术潜力直接比较并宣称“超资源”，两者年份、用途和定义不同。

| 商品 | 固定账户数 | 首次候选失败账户 | 失败账户年度超用MWh |
|---|---:|---:|---:|
| Bagasse | 88 | 50 | 2,374,884.138508 |
| Biodiesel | 194 | 49 | 1,798,313.512984 |
| Biogases | 62 | 62 | 1,025,240.991287 |
| Biogasoline | 19 | 0 | 0 |
| Charcoal | 191 | 100 | 2,165,995.029676 |
| Fuelwood | 248 | 111 | 2,823,345.579708 |
| Animal waste | 5 | 5 | 54,035.887277 |
| 合计 | 807 | 377 | 10,241,815.139440 |

国家账户数：BN2、ID468、KH15、LA36、MM102、MY35、PH65、SG1、TH42、TL1、VN40。失败集中ID273、MM51、PH35、TH18。不要把不同国家节点数当不同原始数据观测数。

冻结Store carrier清单：battery98、home battery98、H2 100、上述资源807、Atmosphere1，共1104。**没有solid biomass、biogas公共潜力Store**。代码E130–134只复制电池类Store，H2/账户另建；因此当前是资源科学边界与供应路径的替换/细化，而非两套生物质供给叠加。原生库存数学机制是继承关系。

## 4. 年度义务与终态：直接行、隐含关系和验收不得混为一谈

以下为**解析推导D**，假设：零损耗、meter效率1、无旁路、p≥0、所有时段需求非负，且数学上严格满足 `Σ_i Q_i=Σ_t w_t d_t`。

由资源Bus平衡 `p_store_i=p_meter_i`、final Bus平衡 `Σ_i p_meter_i=d_t`、库存递推，得：

`Σ_i e_i,T=Σ_i Q_i−Σ_t w_t d_t=0`。

又因每个e_i,T≥0，所以每个e_i,T=0，年度释放各为Q_i；任意前缀释放≤Q_i。**终态归零在这组假设下是共同约束的推论，当前builder没有为这些Store写入独立e_set=0或e_cyclic=true。** 不能把V4的终态检查误记为后来新增了另一个物理终态限制。

同样，在meter无有限功率上限且容量可任意扩建时，可在理想实数算术中取 `p_i,t=(Q_i/ΣQ)d_t`，选择足够p_nom，构造满足这一个隔离资源组的轨迹。这说明“有限库存+固定年度需求”结构**不必然**自相矛盾。它不是对已冻结binary64常数的严格可行证书，更不是全LP可行证书。

实际Q经过比例运算、需求经过独立累加，年度等式有舍入差。既有精确源审计最大绝对差约 **9.816722013e−8 MWh**；普通float累加摘要范围−8.940696716e−8至1.490116119e−8 MWh，两者计算口径不同，不能混用。`fixed_accounts._same`为rtol1e−10/atol1e−6的结构检查，**通过isclose不是严格等式证明**。如果某组需求在精确常数意义上稍大于ΣQ，理想无误差LP可能有微小闭合冲突；必须按原行的精确常数证明，不能从汇总浮点符号直接定案，也不能把这个1e−7量级差称为10.24TWh的解释。本轮不改Q、不加松弛、不改V4。

## 5. 将已知违规接回实际生成路径

这些都是**第一次保存候选X**的违规；不是第二次P2返回了一个新解。P2没有候选解，原生Status4/SolCount0。既有全量审计确认旧点映射后原单位残差逐位保持；本轮只复用SHA和代表性记录。

### 5.1 印度尼西亚Charcoal库存

- 原始文件 `UNdata_Export_20250502_110403305.txt`，SHA `da54b258ffb4927f30834c01f4e9aff7c267dd70c5ef5760292dd21ef5802345`，物理行17044：Indonesia，2019，工业/建筑/非燃料工业Charcoal消费 **97.657千吨**。本轮核对原文件SHA及该原始行。
- 重构为799,810.83 MWh；采用冻结商品热值8190 MWh/千吨。对应源份额0.004311601085909803。
- 2050源InputID `ID:2050:Industry:IndustryFinalEnergy:biomass`，当前accepted总量560,703,926.2954203 MWh；基数185,502,047.63 MWh，采用561.0/185.6增长代理并保留获批重叠处理身份。
- 节点 `ID_Java-Bali1 0` 的组Q约201,045,255.05941087 MWh；乘商品份额得到Store Q=**866,826.940031169 MWh**。本次用现有组Q总和复核份额乘法，差2.33e−10 MWh；这是局部谱系一致性，不重做allocation。
- Store全名 `ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 0 Charcoal fixed resource`；来源RowID直连前述SHA:17044，e_initial=e_nom=Q，非循环，meter效率1。
- 原矩阵row **27,607,093**（0起始）、Store-fix-e-lower、末时段2919；候选e=**−551,995.6578811894 MWh**，因此真实库存下界违规。旧R=2⁻²⁸，新R=0.5；坐标变换没有制造这份物理超用。

### 5.2 缅甸微小Biogases账户

- 原文件 `UNdata_Export_20250502_110314760.txt`，SHA `b004f7bd486dbb8576935c5d17c2e49964e7687ea16b5d67ae57602981b5462c`，物理行11666：Myanmar，2019家庭Biogases消费 **1 TJ**。本轮原文件SHA/行核对；1/0.0036=277.777777…MWh，未使用天然气GCV0.90系数。
- 源账户 `MM:2050:Buildings:ResidentialFuel:biomass`，基数55,950,039.3641778 MWh，获批增长68.2/63.0，2050约60,568,137.85138 MWh。商品份额4.964746780064395e−6；节点MM2 14组Q约2,271,203.903991 MWh。
- Store `MM:2050:Buildings:ResidentialFuel:biomass@MM2 14 Biogases fixed resource`，Q=**11.275952269208819 MWh**。row **27,607,433**，末库存 **−8,625.81301103 MWh**；该资产2917个失败库存下界行已经在既有ACCOUNT_FAILED_ROW_LINKS中关联。
- 旧R=2⁻²²、新R=4096，旧数值空间违规约0.00205655、新空间35,331,330.093；同一原单位违规不变。小商品被节点细分后Q与组总量差距大，是直接量级事实；导致算法某种失败的因果仍未证明。

两条原始行、实际静态端口、SourceAccountID/RowID、registry与分配记录见[REPRESENTATIVE_SOURCE_ROWS](evidence/REPRESENTATIVE_SOURCE_ROWS.json)、[RESOURCE_STATIC_LINEAGE](evidence/RESOURCE_STATIC_LINEAGE.json)。原文件没有上传Git，原始行摘录与SHA足以复核定位。部分registry历史字段仍写Gate2Status=PENDING/TargetReady=false，但同记录后续CoverageStatus=PHYSICAL_ACCEPTED_AND_POSTED；不能仅凭一个早期流程字段推翻最终输入Manifest，也不能隐藏这种历史元数据层次。

### 5.3 252.027392 MW并非电力AC Bus

row **34,037,569**、时段28（2013-01-04 12:00，2050情景沿用2013索引），Bus为：

`ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 0 :: final obligation`。

它是**生物质最终能源义务Bus**。四个有效meter端口的原单位流入约1,910.434140、520.727012、161.966050、20,609.271772 MW，合计23,202.3989742250 MW；Load=22,950.3715821245 MW，过量252.027392100507 MW。对应原矩阵列2,917,379–2,917,382；meter由E247生成、Load由H65绑定。不能把这个数字报道为全国电力供需缺口。

旧R=2⁻²⁸，数值空间残差约9.38875e−7；新R=1仍是252.027392 MW。已有90位Decimal局部点积与独立NetCDF端口计算一致，缩放恒等差为0。于是此代表性违约**不是仅由NetCDF回映射或验收求和造成**；不代表所有其他后处理程序无错误。

### 5.4 汇总与避免重复计数

既有完整矩阵结果：Store-fix-e-lower **277,644行**、Bus-nodal_balance **324,120行**，合计601,764失败行；Store-energy_balance无一般矩阵预算失败，最大原单位残差约2.90e−6 MWh。库存动态大致跟着实际释放走，负库存说明释放超过初值，而不是“末库存由错误时间权重凭空生成”已被证明。

807账户中377失败、385需求组中111失败；现有组级复算总过供 **10,241,815.13943997 MWh**，欠供0，与失败账户年度超用 **10,241,815.13943985 MWh**在浮点汇总差内相符。即相同隔离义务链上的过供、负库存、年度超用、前缀失败互有关联，**不能把这些指标相加当多份缺口**。原始记录SHA索引：[REUSED_FORENSIC_SOURCES](evidence/REUSED_FORENSIC_SOURCES.json)；精确旧点/行证据的路径和SHA见S0 prior_audit_sources。

## 6. 风险与已通过内容分级

| 问题 | 分类 | 证据/本轮判断 |
|---|---|---|
| 807被称为上游技术潜力Store细分 | 已证实的概念差异，不是已证实代码bug | Q由需求派生；独占最终用途。论文360TWh与本账1607TWh不可不加条件直接比较。 |
| 新旧生物质资源双重供给 | 已核静态范围内未发现 | 上游潜力Store未复制；冻结Store carrier/807独占结构、没有旁路。未重复全网求解。 |
| 需求重复或资源总量重复 | 结构保护已通过；原统计口径仍有科学假设 | 无旧Load基底、bind once、source_account_id、组Q对年度Load；61原始行分配到807节点记录不等于原始资源复制807次。重叠处理依赖既有批准，非本轮重新证实真实消费。 |
| 单位、3h权重、端口符号错误造成代表性违约 | 本轮未发现该实现错误 | 原生e递推、w=3、meter效率1、存量与Load共用allocation；代表性原始源行和matrix/NetCDF同值。不能推广为每个源热值必然正确。 |
| 极小商品Q与大组量、无松弛年度闭合 | 直接结构事实；数值根因待证 | Q跨0.708…至1.80e8 MWh；细分份额可极小；旧R把大物理残差表达为小数值。没有条件数或唯一致因证明。 |
| 精确浮点年度差 | 直接舍入事实/潜在精确可行性风险 | 最大源差约9.82e−8 MWh；isclose不是等式。不可把舍入界当结果允许10.24TWh残差，也不自动修Q。 |
| 商品间时序替代、flat-time与电负荷空间代理 | 已证实模型假设；适用性待科学评判 | 33输入均flat-time；最终Bus按biomass聚合，逐期未指定商品结构。若研究需要独立商品时序，当前并未表达。不是未经比较即可判错。 |
| 未知资源成本/CO₂因子 | 已证实报告不完整 | 807价与物理因子NULL；实现零系数使账外常数不入优化。若严格固定Q且跨情景Q不变，未知成本可作为共同常数（条件推导）；当前非法超用候选不满足该前提，不能给其完整成本资格。 |
| 微扰虚构资源收益 | 获批V3例外已执行的历史证据 | 807Store/meter新增边际微扰已撤；不得又归因于已不存在的资源微扰。其余目标与Line/Link KKT失败是另一个证据链，不因本账闭合而消失。 |
| 为发电/H2挪用这些资源导致超用 | 与当前已核独占拓扑不符 | 该候选过供出现在固定义务Bus，资源组没有向电网/H2的出口。全电网其他失败不能据此排除。 |
| 新增CO₂ cap或Atmosphere终态造成停滞 | 无此有效上限，缺因果证据 | 既有碳矩阵审计无政策行；Atmosphere容量无限可扩、无末期归零。物质守恒仍存在，不等于碳政策。 |
| 第二次Presolve已证明哪条物理约束冲突 | UNKNOWN | 第二次INF_OR_UNBD、Barrier0、无候选/独立证书；不能从第一轮违规推导唯一矛盾行。 |

**已证实的是首次候选的物理违规与新建义务结构之间的明确定位关系；本轮未发现足以宣布“应修复某个代码错误即可恢复可行”的直接证据。** 也没有将旧缩放、无进展或INF_OR_UNBD称为严格数学不可行证明。

## 7. A-03建议边界与需用户判断事项

A-03已有代码、输入、代表性原始行和矩阵映射基础，可在复核后开始限定静态工作；本轮不自动启动。优先由用户/ChatGPT判断：

1. 当前807究竟要继续表达“固定最终消费核算义务”，还是未来研究要表达“独立供给潜力、可优化能源替代”？两种模型的Q来源与可行域不同。不能以求解失败为理由删除/放宽现有账户。
2. 接受“2019商品份额×2050增长代理×电力年量空间份额×全年平坦时序”的科学边界到何种研究结论？若需商品/节点特异供给、季节性或更细终端技术，必须另备数据及科学授权。
3. 对精确源舍入差是否需要仅以原文件做代表性精确闭合证明，再决定如何定义数值表达？不得直接改Q、改变库存终态、添加松弛或放宽V4。本轮已有证据不需重复9078万系数审计。

缺失的是独立资源潜力/价格/碳因子及更细时空真实需求依据、严格可行/不可行证书、上游所有论文实验的完整原生记录；不是不知道807从哪段代码来。前两次消费标记与结论永久保留，G6-05暂停。本审计结束后等待复核。
