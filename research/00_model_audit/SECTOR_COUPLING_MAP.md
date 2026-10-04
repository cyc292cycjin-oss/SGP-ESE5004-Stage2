# Sector-coupling审计（A2）

固定版本、证据分级和输入族ID沿用 `MODEL_INPUT_MAP.md`。本报告最高优先结论：**框架支持完整部门耦合，但当前ASEAN配置最后裁剪为电力相关系统；已保存教程也确实经过该裁剪。**不能把框架能力、开关或母线数量当作完整sector-coupled研究证据。

## 四种范围必须分开

| 范围 | 已核实内容 | 结论边界 |
|---|---|---|
| Framework capability | prepare_sector_network有热、工业、道路/铁路、航运/航空、农业、居民/服务、生物质、氢/氨及合成燃料函数 | 支持不等于数据完整或真实投入优化 |
| Current ASEAN config | heat/biomass/industry/shipping/aviation/land_transport/rail_transport/agriculture/residential/services全true；氨继承true；氢网络false、CO₂网络false、生物质运输false；only_elec_network=true | 先构建、后裁剪；未运行完整ASEAN配置的新网络 |
| Tutorial config + saved networks | 覆盖land_transport=false、屋顶建筑面积法false；2030/2040/2050已保存输出均只有4类终端Load，其中工业为零 | 是裁剪后电力相关系统，附带燃料/氢/碳与储能结构；不是完整SC基准，也不宜笼统称“纯电力单carrier” |
| Published paper config | 已读本地IOP论文，§3.1（PDF第5页/印刷第4页）明确电力部门案例、其他部门仅纳入电力需求；100节点、3h；§4 myopic 2025—2050每5年 | **论文未实施完整终端SC案例**；§6将超越电力的sector coupling列为未来工作。作者SHA→有效配置→输入/结果映射仍未闭合 |

论文为 Andreyana等（2026），IOP Conf. Ser.: Earth Environ. Sci.1654 012020，DOI 10.1088/1755-1315/1654/1/012020。本地文件在 `C:/Users/20122/Desktop/ASEAN政策文件/Andreyana_2026_IOP_Conf._Ser.__Earth_Environ._Sci._1654_012020.pdf`，证据见PAPER_EVIDENCE.json。摘要对框架的“sector-coupled”描述不能替代§3.1的实际实验边界。

实际流程：电力网络 → prepare_sector_network → add_export产生pre_adjusted → final_asean_adjustment产生export → add_existing_baseyear/add_brownfield → solve_network_myopic。见 `Snakefile:1435,1567,2387,2449,2495` 附近规则。

## Sector → carrier → technology → component → cost → source → switch

下表“可扩张”描述框架构建逻辑，最终仍须看裁剪和已有资产；“费用”指组件的投资/运行系数，而不是单独国家welfare。B=Bus、G=Generator、L=Link、S=Store、D=Load、SU=StorageUnit。

| Sector | Carrier/技术耦合 | 组件及可扩张性 | 费用及需求来源 | 开关/代码入口 | 当前教程终态 |
|---|---|---|---|---|---|
| Electricity | AC/DC/low voltage；风光、水电、化石发电、配电、储能 | B/G/D、Line、DC/B2B L；风光可扩张；水电等既有SU/G；常规多端L | 年化投资、VOM、燃料供应、输配电；DemandCast + AEO8/人口再分配 | electricity、renewable、ll；add_electricity、final_asean_adjustment | 核心保留 |
| Hydrogen | 电解：electricity→H₂；SMR/SMR CC：gas→H₂(+CO₂)；fuel cell/H₂ turbine回电；Sabatier/helmeth/Fischer-Tropsch | B、可扩张转换L、H₂ tank S；管网有构建能力 | fixed、燃料、效率、储存；工业/航运/交通可用H₂需求 | add_hydrogen自动调用；production_technologies、hydrogen.network；methanation/helmeth/fischer_tropsch | 电解/SMR/SMR CC/合成保留；没有H₂终端Load、无H₂管网；Fuel Cell/Turbine未留存 |
| Heat | electricity/gas/biomass→heat；heat pump、resistive heater、boiler、CHP、solar thermal | 热B/D、可扩张L/G、TES S/充放L | fixed/VOM、燃料、热网/储热；UNSD热总量 + 地理/温度/COP | enable.heat；tes/boilers/chp；add_heat | prenetwork有热负荷；终态热需求与热技术被裁剪 |
| Industry | electricity/H₂/gas/solid biomass/coal/oil/low-temperature heat；过程排放、氨 | D/B、供能转换L，部分CC；不是所有工业生产工艺都内生可替代 | 部门能耗/排放来自工业输入；转换fixed/燃料/捕碳 | enable.industry、cc、ammonia.enable；add_industry/add_ammonia | 48个industry electricity D保留但全零；其余需求移除。工业原始节点表全空 |
| Ammonia | H₂+electricity→NH₃，合成及储存 | B/D、可扩张Haber-Bosch L、S | 成本与USGS产量/工业分配，扣除相关原工业能耗需核对 | sector.ammonia；add_ammonia | 构建后删除；不能因enable=true声称氨参与最终优化 |
| Road transport | electricity→EV，H₂→FCEV，oil→ICE；BEV charger/V2G/DSM | D、充电/V2G L、Li ion S；容量受车队及share，不能统称全部自由扩张 | UNSD道路总量、车辆参数、availability/DSM；外生电动车/燃料电池份额 | enable.land_transport、land_transport_*_share、v2g/bev_dsm | 教程关闭；当前完整配置开启但最后仅白名单电动相关成分可留下 |
| Rail | electricity/oil→铁路需求 | D；燃料供应共享 | UNSD→nodal_energy_totals；无单独“铁路投资”自动加入 | enable.rail_transport；add_rail_transport | 电力D48个、33个非零；oil需求删除 |
| Shipping | oil/H₂→航运（可选液氢） | D/B、液化L/S与燃料供应 | UNSD navigation + WPI空间权重；液化fixed、燃料；H₂ share外生 | enable.shipping、shipping_hydrogen_share=0、international_bunkers=false | 航运油/H₂ D均被删除 |
| Aviation | oil→kerosene需求；潜在合成油供给 | D、油供应和合成燃料共享组件 | UNSD aviation + OurAirports跑道/机场权重；燃料及上游转换成本 | enable.aviation、airport_sizing_factor；add_aviation | kerosene D删除；保留Fischer-Tropsch不等于航空部门还在 |
| Agriculture | electricity/oil→农业需求 | D、共用供能 | UNSD→nodal_energy_totals | enable.agriculture；add_agriculture | 电力D48个、37个非零；oil D删除 |
| Residential | AC/low voltage、heat、oil/gas/biomass；煤转电 | D/B、共享热技术/配电/屋顶/家用电池 | UNSD、CAGR/份额和人口；配电/屋顶/储能/转换成本 | enable.residential、coal.shift_to_elec；add_residential | 非电需求删除；AC不能直接全等同于可独立识别的居民需求 |
| Services | electricity、heat、oil/gas/biomass | D及共享技术 | UNSD/未来份额、人口；供给/转换成本 | enable.services；add_services | 实际`services electricity`也删除：白名单写`service electricity`，存在字符串不一致 |
| Biomass | solid biomass/biogas→power/heat/gas/industry | 资源S、可扩张L、可选运输L | 潜力×分配、fuel、EOP/CHP/CC投资 | enable.biomass、biomass_transport=false | solid biomass库存/biomass EOP保留；热/工业用途裁剪 |
| Carbon | emission→atmosphere，捕集→co₂ stored，CO₂ pipeline/DAC | B/S、多端L；封存另有求解约束 | 封存10 EUR/t配置；CC/DAC成本；排放系数见成本表 | co2.*、co2_network=false、dac/cc | 记账和封存结构保留，不能等同“有净排放上限” |

## 现有教程的实际组件与需求证据

来自 `AUDIT_RUNTIME_EVIDENCE.json`，三个结果快照权重 objective/generators/stores各合计8760，实际只覆盖6天、48个3h快照。下列能量是**既有模型权重下的推导量**，不是全年观测需求。

| 终态Load carrier | 2030条数/非零数 | 2030加权TWh | 2040加权TWh | 2050加权TWh |
|---|---:|---:|---:|---:|
| AC | 46/46 | 802.598414 | 1088.583738 | 1449.431369 |
| industry electricity | 48/0 | 0 | 0 | 0 |
| agriculture electricity | 48/37 | 13.690059 | 16.493763 | 19.871660 |
| rail transport electricity | 48/33 | 6.147076 | 8.890380 | 12.857958 |

2030上述总量为822.435550 TWh，而配置2030 ASEAN目标为1658.8 TWh。代码 `elec_carrier` 中 `"agriculture electricity" "rail transport electricity"` 缺逗号，会被Python拼成一个字符串；工业输入本来为空，随后工业重分配仍会给非工业乘(1−industry_share)。**这些机制与需求不守恒一致，但本轮没有重新执行修复或把全部差额归因于某一行。**未来需按阶段/国家做守恒验收，不能把零工业需求当作参数确认。

另一个直接代码问题：`strip_network(n, carriers)`选Bus/Carrier时使用参数carriers，但组件筛选使用全局 `carrier_to_keep`；配置扩展白名单未一致应用到组件。氢燃料电池实际carrier为`H2 Fuel Cell`，全局表为`H2 fuel cell`，大小写不一致；结果中无Fuel Cell，H₂ turbine也不在全局表。当前保留氢不代表存在完整H₂→电回路。代码未改。

2030实际扩张入口：48个H₂ Electrolysis、SMR、SMR CC、Sabatier、helmeth、Fischer-Tropsch各全部可扩张；48个配电Link；50组大电池及48组家用电池功率Link/能量Store；48个H₂ Tank；15条DC Link全部可扩张，3条B2B不可扩张。煤73、褐煤10、油33个发电Link均不可扩张；CCGT105个中27个可扩张。燃料供给Generator可扩张不等于相应发电技术可扩张。更多年份按证据JSON对应行读取，不以2030数量外推。

## Objective与互联影响的解释边界

**源码结构**：投资成本系数作用于可扩张Generator/Link/Line/Store/SU容量；带时序权重的边际成本作用于运行变量；燃料Generator收费与转换Link VOM分开，Store能量容量与Link功率容量分开。存量固定容量的历史资本成本未必全在优化目标中，需核对objective_constant、年化、brownfield继承和noisy_costs后才可定义报告成本。Load本身不是额外投资费用。未来SC成本必须覆盖所有已确认部门的供给/转换/储存/网络，而非仅筛选AC组件。

**推断（待实验检验）**：跨境电力可改变风光/电池/氢供给位置、配电与国内网、热泵/电锅炉/CHP、工业用能与合成燃料的选择；外生燃料份额不一定随价格改变。若部门被裁剪、需求为零或技术被冻结，该通道不能实现。没有在本轮估计收益符号/大小。

跨国网络与共享商品池要分别审计：H₂/CO₂网络关闭仍可能保留区域共用的lignite、生物质或碳存储Bus。要得到11个真正独立问题，不能只移除AC Line而保留跨国共享有限资源。也不能因此禁止原本允许的外部商品供应。

正式SC基准需要先确认部门需求和统计范围、修复/解释空工业表、选择是否关闭末端裁剪，并验证Load守恒、所有Link端口、国家归属、成本/排放记账。`only_elec_network=false`是候选入口，不是已批准、已验证的充分操作。
