# Phase 3B-1：Road / rail 独立源码核查

日期：2026-10-02。状态：只读审计；没有修改模型、运行模型、下载或补造输入。以下 `U/`、`P/` 均指本目录 `source/U/`、`source/P/` 的冻结副本。`U` 的工程修复不能倒推为论文当时行为。直接观察、公式推导、待检验推断分别标明。

## 1. 可验证的来源与计算链

| 环节 | 源码证据（冻结相对路径:行） | 直接观察 / 限制 |
|---|---|---|
| 原始能源平衡入口 | U/Snakefile:1717–1748；U/scripts/build_base_energy_totals.py:366–445 | UNSD 链接登记工作簿 → 原始分号分隔 txt → 国家ISO2映射。更新失败可走固定 Google Drive archive；未从此代码确定实际运行采用哪次下载快照。 |
| 基准年、国家 | U/config.default.yaml:687–690；U/scripts/build_base_energy_totals.py:450–462 | 默认2019，显式按年份与国家筛选。不得把后续2030预测量称为2019观测。 |
| 单位 | U/scripts/build_base_energy_totals.py:108–132；U/scripts/_helpers.py:1837–1889 | 百万kWh÷1000；TJ÷3600；千吨/千立方米乘燃料系数，产物TWh。燃料系数只给统一映射，HHV/LHV及国家燃料差异尚未由该段源码核实。 |
| road aggregate | U/scripts/build_base_energy_totals.py:59–62,203–222 | 按 Commodity - Transaction 含road筛选，全部Quantity_TWh相加为total road，另生成road electricity/gas/biomass/oil。不存在客运/货运/二轮车/汽车/公交的服务量分解。 |
| rail aggregate | U/scripts/build_base_energy_totals.py:246–260 | total rail只汇总Gas Oil/Diesel Oil、Biodiesel、Electricity；electricity rail单独汇总Electricity。铁路交通服务量、客货运与线路空间并未建模。 |
| 增长与效率 | U/scripts/prepare_energy_totals.py:35–44,63–109,260–270；U/data/demand/growth_factors_cagr.csv:1–2；efficiency_gains_cagr.csv:1–2 | (1+CAGR)^(目标年−基准年)；缺国家或字段用DEFAULT。检查这两份CSV未见11个ASEAN国家专属行。road先以ICE/FCEV/EV外生share加权各效率增长，再乘road增长。不是优化器内生选择车种。 |
| 缺失值 | U/scripts/prepare_energy_totals.py:296；U/scripts/prepare_transport_data.py:78,117–126 | 能源预测输出fillna(0)；节点能源fillna(0)；缺车辆国家reindex为0辆、其零效率用全表均值。源码存在填补行为，不构成研究接受；文件中的零不能自动解读为无该需求。 |
| 车辆数 | U/scripts/prepare_transport_data_input.py:37–112,162–199 | WHO GHO RS_194注册车辆为主，Wikipedia补国家；任一车辆/CO₂下载为空即复制硬编码transport_data.csv。字段命名number cars不能证明全是乘用车。代码没有选择统一车辆年份、增长车辆存量或保留每行年/车种来源。 |
| 硬编码车辆表 | U/data/temp_hard_coded/transport_data.csv:1,25,67,81,89,100,116,133,147–148,161,166 | 11国均有行，仅country/number cars/average fuel efficiency三列；原始年份、车辆分类、源文件、单位链未随行保留。车辆数量不等于车辆公里。 |
| 所谓燃油效率 | U/scripts/prepare_transport_data_input.py:115–140 | 从归档World Bank EN.CO2.TRAN.ZS的2014运输CO₂占燃烧CO₂比例得到(100−share)/100。此运算直接产生无量纲比例，不能据此推出MWh/100km或kWh/km。脚本注释反称要估计MWh/100km，尚无物理转换。 |
| 行驶及插电周曲线 | U/data/emobility/traffic.tex:6–13；KFZ__count:1–3；Pkw__count:1–3；U/scripts/prepare_transport_data.py:44–63,84–111,183–211 | 德国BASt 2010–2015数据，文件2016生成；KFZ count作道路形状，Pkw count作插电availability，重复168小时并取国家第一个时区。读取count而不读取n_counts。不是ASEAN交通调查或国别充电曲线。 |
| 工作流文件路径 | U/Snakefile:1328–1332,1583–1613 | resources/…/energy_totals_{year}.csv、transport_data.csv、人口份额、气温、两份德国曲线 → transport/avail/dsm/nodal_transport_data四类CSV。仅有名字相近的data/energy_totals_DF_2030.csv不证明它被消费为需求值；build_base_energy_totals:459–461仅取其列名。 |

上述来源能恢复**模型现有逻辑**，不等于参数已获研究接受。当前不要求用户重新寻找所有国家分车型数据；优先解决必要的需求口径与EV转换链。

## 2. 单位与公式的独立判断

设节点年能源 E_road、E_rail、E_rail_e 单位TWh，f_t为按generator权重归一的交通曲线（Σw_t f_t=1），Y=Σw_t/8760。`U/scripts/prepare_transport_data.py:97–111,128–180,247–248` 实际执行：

- 非custom：E_land = E_road + E_rail − E_rail_e；g = average_fuel_efficiency / (0.2 × charge_efficiency)；q_t = 1e6 × Y × E_land × f_t × (1+dd_EV,t)/(g × ICE_correction)。
- custom：q_t = 1e6 × Y × E_road × f_t，不做上述燃油效率/气温转换；本开关不会自动引入另一套车辆公里数据。
- 默认0.2在 `U/config.default.yaml:873` 注释为Tesla Model S **kWh/km**；代码变量名虽含efficiency，不能把它当无量纲效率。原始燃油代理g的分子却是CO₂比例变换，量纲不能闭合。旧注释MWh/100km与kWh/km也需要明确换算，而源码没有。
- 因此q被后续Load当作MW消费是**模型行为**；其物理意义只能暂称“代码生成的陆运能源代理”，不能标成经验证的useful mobility、passenger-km、tonne-km或有证据支持的全国EV用电。不可通过给字段重命名掩盖。
- road油/气/生物质差异在E_land聚合后消失；`road electricity`没有从E_land扣去，也没有作为历史已电气化份额单独使用。

**铁路重复路径（条件成立的代码推断）**：land与rail均启用、custom=false、非电rail>0时，非电rail已进入E_land，同时`add_rail_transport`又添加原非电rail固定油Load。pre-strip full-SC因此存在重复表示。该推断不等于所有作者final文件都重复：final剥离非电rail。当前教程land=false也不触发此双路径。

**时间与工程细节**：P/prepare_transport_data.py:96–97用普通列求和，U:97–111改为snapshot权重；U/prepare_sector_network.py:2260–2308,2361–2376将需求/availability按均值、DSM约束按最大值对齐。只确认两版行为，未回跑。EV负荷是q_t与循环前1、2个**时间步**的均值（U/prepare_sector_network.py:2430–2438；U/_helpers.py:1632–1641），并非固定3小时物理充电模型。另U/prepare_transport_data.py:31–39严格不等式未覆盖恰等15或20°C；等值点会保留原温度数值。这是待验证的局部实现问题，未统计实际数据命中次数，不据此重开全面数据收集。

## 3. Road / rail 网络表示、灵活性与成本

`U/scripts/prepare_sector_network.py:2388–2412`：s_EV、s_FCEV取外生scenario/year值（dynamic模式则按opts取值），s_ICE=1−s_EV−s_FCEV。相同share同时缩放能源代理与车辆数，源码没有证明它严格等于销量、存量、里程或服务份额。prepare_energy_totals:93–99仍读取普通share，不看dynamic开关，未来若启用dynamic需核对两处一致；本轮不改开关。

| 对象 | 当前U中的构造（行号均为prepare_sector_network.py） | 解释 |
|---|---|---|
| EV battery Bus + EV Load | 2417–2447；Li ion Bus、land transport EV Load=q的三步平均×s_EV | Load位于电池侧，不是电网充电输入。 |
| BEV charger Link | 2449–2469；p_nom=number cars×0.011 MW/car×s_EV；η=0.9；availability p_max_pu | 固定容量，不可扩张；函数内没有有效vehicle/charger投资成本，相关extendable/cost行被注释。 |
| V2G Link | 2471–2482；反向Link、相同p_nom/availability/η | v2g开关仅创建反向边；并不独自保证有时间迁移储能。 |
| EV Store | 2484–2502；e_nom=number cars×0.05 MWh/car×0.5×s_EV，e_cyclic，DSM e_min_pu | bev_dsm开关控制固定存储量；不优化车数/电池投资；U carrier为EV battery storage。 |
| FCEV | 2504–2518；H₂ Load=s_FCEV×q/0.5，受H₂ reference-removal条件控制 | 固定H₂需求；燃料电池转换未作为可扩张车辆技术Link。 |
| ICE | 2520–2548；oil Load=s_ICE×q/0.3，另co₂负Load | 全部残余归到oil，无柴油/汽油/气/生物燃料车辆的独立优化。 |
| rail | 3696–3739；静态electricity Load=E_rail_e×1e6/8760，oil Load=(E_rail−E_rail_e)×1e6/8760 | 固定平坦用电和用油；没有rail扩容、车型选择、内生电气化或轨道网络。函数自身未增加铁路排放负Load；整体燃料排放是否闭合须另查共同燃料/碳账户。 |

默认`v2g=true`,`bev_dsm=true`,`bev_energy=0.05`,`bev_availability=0.5`在U/config.default.yaml:885–890，属于假设参数不是ASEAN实证。电网供电、上游制氢/燃料供给、发电网络储能可进入系统成本，但这不能补成车辆投资总成本。单看这些函数，未来国家“transport investment”不能解释为车队全成本。

## 4. 电力边界：未看到历史电力转移扣除

已完整检查`add_land_transport`和`add_rail_transport`，它们只添加组件，没有从原AC Load减去历史道路或铁路电力。road electricity字段在本链后续不被消费；land的“−electricity rail”只是避免把电铁路并入陆运代理，**不是从A*父电力账户扣除电铁路**。

U/prepare_sector_network.py:3462把AC负荷乘通用损耗因子，3464–3476将负荷及EV边搬到低压侧，均不是运输电力扣除。之后residential会改写AC等其他边界行为由主审计汇合。因此只能判定运输函数没有显式父账户转移合同；总电量是否已内含运输必须在共同比较电力账户中闭合，不能仅凭函数没有扣除便声称某文件已确定重复多少TWh。

## 5. Pre-strip、final、tutorial、作者输出分别判断

- Current U ASEAN配置启用land/rail（U/configs/config.asean.yaml:198–208），DEC EV shares 0→0.05→0.2→0.45→0.7→0.85→1、FCEV全0（216–231）；`scenario.demand:[DEC]`旧键由U/_helpers.py:235–259迁到demand_data.scenario，不能只看default AB键就认定实际为AB。未来研究不得自动接受这些share。
- Tutorial明示land=false（U/configs/tutorials/config.asean.yaml:30–32），不是transport source或EV模型通过验证。
- Final ASEAN `only_elec_network=true`（U/configs/config.asean.yaml:262），调用strip见U/final_asean_adjustment.py:419–421。白名单保留rail transport electricity、Li ion、land transport EV、BEV charger、V2G（41,62–65），不保留land transport oil/fuel cell、rail transport oil。
- P的EV Store carrier为battery storage（P/prepare_sector_network.py:1999–2008）；U为EV battery storage（U:2492–2501）。两者均不在final白名单。`strip_network`第141行针对组件实际使用全局carrier_to_keep筛选，故两版此路径均丢失EV Store。**只看到V2G Link不能报告最终网络具有EV跨时储能灵活性。**
- Final的`elec_carrier`第86行缺逗号，将agriculture electricity与rail transport electricity拼成一个字符串；include_electricity_growth:199及redistribute_industrial_load:244因此不选中实际铁路电力。EV被87行显式排除在增长选择之外。AEO重标定不能直接证明含EV/rail的全电力总量等于指定AEO数。

### 已有网络文件的只读观察

据主任务生成的`NETWORK_TRANSPORT_EVIDENCE.json`，本子任务再次检查其selected_components（没有重新导入网络或求解）：

| 证据角色 | EV / rail electricity Load | BEV / V2G Link | EV Store |
|---|---|---|---|
| 作者baseline 2025 final | 各98；EV电池侧14.928884 TWh，rail5.111434 TWh（主任务按权重提取） | 各98；全部固定p_nom、η=0.9、capital_cost=0 | 0 |
| 作者decarbonize2050 final | 各98；EV电池侧68.846262 TWh，rail12.857958 TWh（主任务按权重提取） | 各98；全部固定p_nom、η=0.9、capital_cost=0 | 0 |
| 教程2030 pre-strip | 无EV；rail electricity48，rail oil48 | 无BEV/V2G | 0 |
| 教程2030 final | 无EV；rail electricity48，oil已删除 | 无BEV/V2G | 0 |

作者两个选定final文件的BEV marginal_cost范围0.00901023–0.01098075，V2G为0.00900033–0.01097174（网络中的小正值；本子任务不猜测来源）。因此“函数没设置成本”不能写成“实际最终Link的marginal_cost为0”。全部EV相关Store为空是实际文件观察，与源码剥离预测相符。

这两份作者网络只是选定reference outputs，不代表每个scenario都核验过，不是独立复现。EV电池侧Load不能直接叫grid charging；从Load÷0.9推成净网侧量还要求无其他流入流出/循环等条件，本轮不以代数推算替代实际Link flow核验。

## 6. 最小重大缺口与有限推进建议（非冻结决定）

1. **第一优先：能源/服务/EV输入端单位闭合。** 可先采用有来源的aggregate road final-energy账户；不要把CO₂份额代理效率或统一Tesla消费率直接变成11国所有车种的可接受EV转换。是否只保留非灵活外生transport电量，是研究边界选择，需要人审；不是要求立即补齐完整车队数据库。
2. **父电力账户与road/rail子账户排重。** 必须说明历史transport electricity保留在哪，未来转换用电在哪里内生生成；非电rail退出land aggregate还是退出独立rail只能选一个合乎定义的边界，并保持integrated/disconnected一致。本轮不实施。
3. **灵活性开关不能由默认true升级为研究事实。** 第一基准可提议不赋予未经证实的DSM/V2G灵活性；之后只在接入率、容量和曲线有证据并且对研究重要时再开放。未接受参数不是零潜力。
4. **确认实际source snapshot与合适增长假设。** UNSD原始2019记录、DEFAULT CAGR来源、车队表年份都尚未闭合；可先冻结能源原始账户而把预测/车队灵活性留待定，不把所有缺项都当同级全系统阻断。
5. **框架能力不等于final结果。** 当前U可构造full pre-strip道路燃料/EV/H₂和rail；作者final选择性保留电力需求，删除非电运输和EV存储。第一FullSC必须明确是提出新研究边界，不能称照搬已验证paper FullSC。

未新增数据，未修改任何参数，未运行正式或小规模求解。上面所有现实参数仍UNVERIFIED/PENDING；代码阅读确认只说明模型“做了什么”。
