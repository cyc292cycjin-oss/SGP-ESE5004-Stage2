# A-03 — Final obligation and Bus implementation audit

2026-10-11。**COMPLETE_WITH_EXPLICIT_UNKNOWNS**。范围为已冻结的385个生物质最终义务组及807个资源Store/meter；继续按固定终端能源核算边界理解，不把Q改称独立供给潜力。G6-05保持 **PAUSED_BY_USER**。

**核心结论：111组过供与377账户超用构成同一组内能量链的关联违规；没有发现可归因于重复Load、meter方向、3h权重或旁路的实现错误。** 冻结常数存在微小的精确年度闭合差，但其量级及分组分布均不能解释首次候选的10.24 TWh违规。该候选仍为OPTIMAL / V4 NOT_ACCEPTED，第二次仍为INF_OR_UNBD；本审计不是全LP可行性证明。

证据等级：**VERIFIED**为原件、源码或已保存独立核算；**DERIVATION**为有明确假设的数学推导；**RISK**为尚未证明的风险；**UNKNOWN**为现有证据不能决定。本轮没有连接AutoDL、重新构模、求解或扫描9078万CSC系数；没有重扫X/Pi/RC。通过SHA核对后复用既有X派生残差，仅新增组件拓扑和385条负荷序列的局部核对。

## 1. 三个基准的真实连接差异

| 基准 | 实际Bus、Load、Store、Link关系 | 科学与数学含义 |
|---|---|---|
| 上游Sector Coupling，`a3616a68ee44592af6527ca9024a90f1956646ae` | `add_biomass:1118–1265`由独立potential配置建立有限初始Store；`add_industry:1883–1916`创建solid biomass for industry Bus、年需求/8760的Load、从资源池到工业Bus的效率1 Link；CC条件分支另有多端口技术 | 工业最终能源Bus与Load本来已有，不能记为我们发明；有限池同时可供EOP等用途，资源量不由这一终端Load倒推 |
| 论文两份实际结果网络，嵌入commit `5bacad702ccfed17ad19ab510fa710651e966f2c` | 本轮读取其静态组件表：两份均488个Load，只含AC96、industry electricity98、EV98、rail electricity98、agriculture electricity98；**没有最终生物质燃料Load**。均有Earth solid biomass Store，e_nom=e_initial=360,000,000 MWh，非循环、下界0；biomass EOP Link分别98/100条通往电力节点 | 已生效only_elec_network筛选保留电力相关SC设施，但去除工业生物质终端需求。不能拿通用SC函数等同论文最终已保留组件，也不能把论文理解为完全无Store/SC |
| 当前Full-SC，科学源码 `b9be7d0ab788a4151346c098d2e657c7e94a22da`，冻结构模记录 `4b5611dc2dbc3ebcc2ae69b3782b338d2a18b6ce` | 每组一条Load位于独占final obligation Bus；每商品一条预装Q的固定Store，经资源Bus、正向效率1 meter进入该最终Bus。385个Load、807个Store、807个meter；原公共solid biomass/biogas潜力Store不并存 | 是终端需求核算边界的重建与隔离，不是原潜力池简单扩为807份。该资源不能用于电力、H2或别的义务组；商品之间只在同组有时序替代 |

上游具体代码：[工业最终需求与端口](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L1883)、[有限资源Store](https://github.com/pypsa-meets-earth/pypsa-asean/blob/a3616a68ee44592af6527ca9024a90f1956646ae/scripts/prepare_sector_network.py#L1189)、[论文版本筛选执行](https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/scripts/final_asean_adjustment.py#L377)。两份结果网络SHA复用原已核索引，静态表本轮读取，未重复下载或全文件散列；见[A03_UPSTREAM_RESULT_TOPOLOGY.json](evidence/A03_UPSTREAM_RESULT_TOPOLOGY.json)。Store保存的边际系数13.65793583262765是结果网络有效系数，不冒称未扰动科学原价。

当前生成与核验路径：

| 代码位置 | 实际作用 |
|---|---|
| [allocate_assembly_inputs.py:49–78](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/allocate_assembly_inputs.py#L49) | 同国作者2025输入电负荷年量份额分配节点，33个生物质InputID全部采用平坦时序；并非商品潜力或逐时消费观测 |
| [build_research_assets.py:214–249](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/build_research_assets.py#L214) | 年度节点Load积分，乘同国/部门源商品MWh份额得到Q；建立独占Bus、e_nom=e_initial=Q的Store及meter；保存SourceRow/route |
| [assembly_components.py:49–67](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/assembly_components.py#L49) | 同一allocation数组绑定唯一Load，禁止已有Load/owner；不是再叠加作者旧Load |
| [carrier_architecture.py:250–303](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/carrier_architecture.py#L250) | Store不支持p_min_pu，故转为discharge_only元数据与真正的Store-p≥0 hook；Link保留明确端口和效率 |
| [fixed_accounts.py:18–67](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/blob/b9be7d0ab788a4151346c098d2e657c7e94a22da/scripts_project/fixed_accounts.py#L18) | 权重、Q、初始库存、方向、唯一源与meter、最终Bus无旁路验证；年度相等检查是isclose，非精确有理等式 |

上述物理源码与冻结归档的SHA对应复用[FROZEN_SOURCE_LINKAGE.json](evidence/FROZEN_SOURCE_LINKAGE.json)；后来的执行授权gate变化不等于重写物理连接。

## 2. 全部385/807的静态实施核对

冻结网络SHA：`238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`。本轮复用既有身份回执，读取静态表和385条Load序列；未复制网络、未创建PyPSA对象。

- 每组恰好一个Load；最终Bus没有Generator、Store或StorageUnit；所有接入Link恰好是本组meter的bus1。
- 每资源Bus恰好一个所属Store和一个meter的bus0；没有Load、Generator、StorageUnit、其他Link、Line或Transformer旁路。
- 所有meter为二端口、效率1、p_min_pu=0、容量可扩且没有有限p_nom_max；无跨组出口。Store固定、非循环、初值Q、e_min=0/e_max=1、零损耗、discharge_only；原生Store正号和Load负号一致。
- snapshots的stores/generators/objective权重均为3小时，2920时段、全年8760小时。385条Load非负且各自全年平坦，无Store/Link时间序列覆盖或e_set终态强制。
- Q与已保存账户逐项相符；所有807个科学价格与物理CO₂因子仍NULL。没有用虚构新价格补齐数据。

**所列拓扑/字段检查异常为0。** 缺省字段按已有PyPSA 0.30.3属性定义解释，不把NetCDF未存字段直接当零。结果摘要见[A03_OBLIGATION_AUDIT_SUMMARY](evidence/A03_OBLIGATION_AUDIT_SUMMARY.json)；逐组见[A03_GROUP_CROSSWALK](evidence/A03_GROUP_CROSSWALK.json)，逐账户见[A03_ACCOUNT_CROSSWALK](evidence/A03_ACCOUNT_CROSSWALK.json)。这是指定结构范围的通过，不证明原统计源没有跨部门重叠，也不证明所有Full-SC组件无缺陷。

## 3. 年度、逐期和终态的三个精度层次

### 理想实数关系（DERIVATION）

记p为Store放电、f为meter bus0取能，bus1变量为−f；Load d≥0。无旁路、效率1时：

`p_i,t=f_i,t`；`Σ_i f_i,t=d_t`；`e_i,t=e_i,t−1−3p_i,t`；`e_i,−1=Q_i`；`0≤e_i,t≤Q_i`；`p_i,t≥0`。

若严格满足 `Σ_iQ_i=Σ_t3d_t`，则 `Σ_i e_i,T=0`，由非负性推出每个末库存0、每个商品年度释放Q。**末库存0是这组条件的推论，不是另加的e_set=0约束；Store也没有每期流入Q。** 前缀释放上限是库存下界的等价后果。

不存在逐商品规定好的释放曲线：meter可扩建，商品在同一最终biomass Bus按MWh聚合，可改变各商品释放时序。它是既定终端核算假设，不是发现了无约束能源。若要求商品各自逐时消费或真实转换设备/季节供应，就需另行科学建模授权，本轮不实施。

### 冻结binary64常数（VERIFIED）

利用已验证平坦Load，对每组以精确有理数算 `δ_g=8760×d_g−Σ_iQ_i`，保留分子/分母；不是普通浮点累加后判断符号。全部385组与旧精确源审计的差为0：

| 精确差符号 | 组数 | 其中首次义务验收失败 | 其中通过 |
|---|---:|---:|---:|
| δ>0，需求稍大于库存 | 180 | 56 | 124 |
| δ<0，库存稍大于需求 | 205 | 55 | 150 |
| δ=0 | 0 | 0 | 0 |

最大绝对差 **9.816722013056278×10⁻⁸ MWh**。旧普通float求和得到137个正差，与本次精确常数180个正差是计算口径差异，不是模型改动。最大差组是ID工业Java-Bali1 0，δ=`−3373/34359738368` MWh，方向是库存略多；该组却严重过供。因此小舍入差的符号不能解释失败组归属。

若把这些binary64常数当精确实数，并且实际LP严格具有上面的隔离关系，δ>0违反该子系统的精确年度必要条件；δ<0则允许留下总库存−δ，不强迫每个库存严格归零。这是**条件解析风险**。本轮没有重取全部LP精确常数并构造不可行证书，不能将180组直接宣判为Gurobi不可行根因或把整个LP标为数学INFEASIBLE。

### 返回解与V4预算（既有验收，不变更）

一般原单位预算仍按V4；资源账户仍为 `B_i=min(0.001+1e−7Q_i,1e−6Q_i)` MWh，组检查用ΣB_i，并保留逐期/前缀、年度、终态、累计绝对残差。源常数舍入误差、源运算误差界与求解结果可接受残差是三个不同量；不能互相替换，也不允许事后放宽以使候选通过。已有源舍入上界/组结果预算最大比例约1.30×10⁻⁵，仅是量级比较。

## 4. 111组与377账户的完整对应

本轮核对既有独立X/NetCDF/矩阵残差文件SHA后逐组联结，未重新扫描向量或CSC：

- **67组各3个失败账户 + 44组各4个失败账户 = 111组、377账户。** 失败组的全部所属账户均失败；274个通过组的430账户均通过。没有失败账户落入通过组，没有失败组缺少失败账户。
- 每个失败组均有2920个失败时段；`111×2920=324120`，与已保存Bus失败行总数一致。账户关联库存下界失败行合计277644。
- 377账户失败检查恰好是annual、terminal、stock_lower、all_cumulative_release_caps四项；全部807的逐期递推、累计绝对递推残差、meter匹配与非负释放等其余既有检查通过。
- 组总过供 **10,241,815.139439970 MWh**、欠供0；失败账户正超用 **10,241,815.139439851 MWh**。差约1.19×10⁻⁷ MWh，仅为不同汇总口径下的微小差。

定义 A_g 为Store年释放，L_g为Load年量，O_g为meter供给−Load的年净过供。理想关系是：

`A_g−Q_g = O_g + (L_g−Q_g)`；`(A_g−Q_g)+Σe_i,T=0`。

对候选点，第一式需计入meter与Store差，第二式需计入库存递推残差；不能当作返回解严格满足。用已保存双精度汇总量核算，前者最大闭合差 **1.2922100722789764×10⁻⁸ MWh**，后者 **1.2782402336597443×10⁻⁶ MWh**。不是有理精确等式证明，但远低于相关组预算和百万MWh超用量。

因此，负库存、年度超用、前缀超限、最终Bus过供在这里是同一能量错误链的不同表现。**不能把10.24 TWh过供再加10.24 TWh资源超用报告为20.48 TWh问题。** 也不能因为库存递推通过就说物理可行：递推可以一致地走到负库存。

### 代表性实际生成路径与原始点证据

`ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 0 :: final obligation`由build_research_assets创建，Load由assembly_components绑定。其4个商品账户为Bagasse、Biodiesel、Charcoal、Fuelwood，本轮均联结为失败。组Q=201,045,255.05941087 MWh，Load=22,950.371582124517 MW；年过供2,207,759.954800436 MWh、末库存和−2,207,759.9548016284 MWh。

已保存的独立高精度证明在时段28、矩阵row **34037569**（0起始）给出：meter原单位注入23,202.3989742250235 MW，Load22,950.3715821245169 MW，残差 **252.02739210050666 MW**。列2917379–2917382与四个meter对应；NetCDF按−p1计算、CSC点积、90位Decimal局部核算一致。旧行缩放R=2⁻²⁸后为约9.38875×10⁻⁷；物理违约不是仅由回映射造出，且这里的MW是**生物质最终能源**，不是AC电力缺口。

该组Charcoal Store末库存−551,995.6578811894 MWh对应row27607093；源UNSD行、Q计算和代码链已在[RESOURCE_STORE_LINEAGE_AUDIT](RESOURCE_STORE_LINEAGE_AUDIT.md)核明。小账户例 `MM2 14 Biogases` 的Q=11.275952269208819 MWh、末库存约−8625.81301103 MWh同样保留于账户清单。原点证据路径及SHA见[A03_EVIDENCE_INDEX](evidence/A03_EVIDENCE_INDEX.json)。

## 5. Q的科学含义与证据分级

Q生成链为 **原消费源行→2050固定终端需求→节点份额→商品份额→固定账户**，而非“当地可持续资源潜力→可选择消费”。它可检查在既定需求核算边界内不透支库存、端口守恒、年度和前缀义务；不能独立证明实际资源充足、可持续供应、经济最优商品替代、季节可得性或完整成本/碳排放。未知价和因子仍NULL；优化中的零系数不是已认定资源真实免费。

| 分类 | 本轮结论及证据等级 |
|---|---|
| 已证实实现错误 | **未发现本轮所查重复Load、反向meter、重复3h权重、额外源或旁路错误。** 不能推广为全模型无bug；原输入统计重叠未重审 |
| 已证实结构/科学假设变化 | VERIFIED：由独立潜力与多用途资源池转为需求派生独占账户；全年平坦、用电年量空间代理；同组商品时序可替代。是否适合后续科学问题需用户判断，不自动判错 |
| 输入常数冲突风险 | VERIFIED微小δ，DERIVATION精确年度必要条件；180正差/205负差，最大9.82×10⁻⁸ MWh。未改Q，未将其等同10.24TWh根因 |
| 已证实数值现象 | VERIFIED：旧候选物理过供/负库存、缩放后残差减小、独立高精度与NetCDF一致；377账户的递推基本闭合但非负库存失败 |
| 尚未证明的数值因果 | RISK/UNKNOWN：缩放、极小商品Q、大组量及退化是否导致整个算法停滞或第二次Presolve INF_OR_UNBD。本轮没有新求解或因果试验 |
| 需求/资源统计科学冲突 | UNKNOWN：2019商品份额、2050代理、行业重叠及热值是否足以代表真实2050需求/供给；需要对应原数据和研究定义，不能由候选违约决定 |

**没有证据支持现在删除、放宽或改写资源义务来“修复可行性”。** 本轮未取得可直接更正即恢复合格解的实现bug证据，也未证明全LP可行。最有价值的后续科学问题是：固定终端核算边界能否支撑拟研究结论，以及原数据/时空代理是否一致；这些属于另行授权的B阶段，不自动启动。

## 6. 台账、发布与停止

A-03在现有证据范围完成；未知项明确保留。B物理约束与输入一致性、C365日时间分辨率诊断、D完整2920时段Gate6验收、E跨境氢气等扩展、F可比互联/独立成本实验，均只记计划。未启动A-04或任何下一次求解。

审计分支继续为 `audit/stage2-baseline-lineage-20261011`，不改main、不合并PR。随本次提交交付全部Markdown台账/报告及轻量JSON的ZIP，保留相对路径、文件大小/SHA清单并核CRC/成员完整性；不含大矩阵、X/Pi/RC、许可证或凭据。请将ZIP上传到ChatGPT供联合审阅。提交SHA、GitHub链接及ZIP绝对路径由本轮发布回执和最终回复记录。
