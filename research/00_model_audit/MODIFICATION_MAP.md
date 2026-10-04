# 可修改项地图（A3，设计说明，未执行）

基线：固定模型提交ce327bfa。所有入口按该版本源码确认；“config-only”只表示入口形式简单，不表示科学影响小、数据已确认或可以立即运行。文件路径相对模型仓库。本轮未生成可执行实验override。

| 修改项 | 分类与入口 | 预期影响/科学问题 | 可复现性与必须核验 |
|---|---|---|---|
| 国家电力互联on/off | **config-only候选**：`scenario.opts`里的`ATKc`；`prepare_network.py:enforce_autarky(only_crossborder=True)`。完整SC隔离需要**project script/workflow change** | 电力阶段删不同国家端点间Line及Link；不会禁止所有后续燃料供给。`ATK`会删所有Line/DC，连国内网也变，不能用作国家standalone替代 | 中等。ATKc在sector构建前执行，后续H₂/CO₂/共享资源仍须检查；跨境按bus0/bus1的国家判断；分开跟踪国内岛际线 |
| 输电扩建上限 | **config-only**：`scenario.ll`，`lines`/`links`上下界；prepare_network:set_transmission_limit | v为容量×长度约束，c为成本约束，l为逐线倍数；v2.0不是“每条线翻倍”，也不等于“仅跨境线翻倍” | 高（键值可归档），科学可比性中等；上限通常同时包含国内和跨境网，删边后需记录参考ref、capacity minima和约束RHS |
| 输电项目集合 | **config-only/data change**：`transmission_projects.include/status/skip/new_link_capacity/set_by_build_year`及AIMS、ID_SuperGrid目录 | 改变可用线路及存量；关闭AIMS不等于删除全部现有跨国线 | 高，但需固定项目CSV与年份；readjust_existing_interconnections会再改存量，需要保存前后表 |
| 国内网处理 | **config-only + project script**：`lines/links`、`subregion`、聚类busmap；按两端国家筛选 | 铜板化、删除国内线或改变国内扩建都会改变互联收益归因 | 必须冻结国家内busmap/网络与潜力，不能把ATK当standalone；跨境与岛内/岛际国内线分别验收 |
| Sector switches | **config-only候选**：`sector.enable.*`、`ammonia.enable`、氢/CO₂网络、`final_adjustment.only_elec_network` | 从论文电力范围扩展到完整SC，改变需求、可行域、成本和排放边界 | 中等/待验收。当前部门开关true仍被裁剪；关闭裁剪不保证工业输入有效；字符串筛选缺陷若修复则单列source-code engineering/data/model影响审查 |
| Demand | **config-only/data change**：load_options、snapshots、demand_data、final_adjustment.total_elec_demand/人均/industry_share；data/demand、工业需求输入 | 改变负荷总量、形状、电气化份额和国家权重，是科学假设 | 入口多，需最终逐国逐部门时序/总量对账；不得静默回填DEFAULT、空值转0；国家单跑不得各继承ASEAN总量 |
| Renewable potentials | **config-only/data change**：renewable masks/capacity density、排除数据、屋顶参数和建筑GIS | 改变资源可用量与空间分布，影响出口比较优势 | 固定资源栅格、CRS、版本、busmap；不能仅归档一个最终p_nom_max而丢失面积与转换链 |
| Storage | **config-only/data change**：electricity.extendable_carriers、storage_techs/max_hours、sector.tes/home_battery/hydrogen.underground_storage；成本行 | 功率/能量是否独立扩张、时长、效率/循环/地理潜力改变灵活性 | 数据/技术可用性须共同确认；现有H₂回电组件白名单问题先查；本轮不启用新技术 |
| Technology availability | **config-only**：electricity renewable/conventional/extendable carriers、sector hydrogen.production_technologies、methanation/helmeth/cc/dac等；新行为才**source-code change** | 影响转换路线与投资组合；外生份额≠内生技术替代 | 需检查最终组件清单和非零需求/连接；不以列表中存在技术认定参与求解 |
| Planning horizons/foresight | **config-only**：scenario.planning_horizons、foresight；add_existing_baseyear/add_brownfield | myopic每期继承寿命/存量；改变起始年会改变基年和路径依赖 | 高，但国家与整体必须同基年、资产继承、投资期间；不能把不同年份objective直接求和当NPV |
| Temporal resolution | **config-only**：snapshots、scenario.sopts中的3h、opts中的时间选项；atlite.default/cutout | 影响需求/资源波动与储能，短时窗不同于全年 | 固定时间窗、3类权重、年归一化；当前6天权重合计8760依旧不是全年 |
| Spatial clustering | **config-only/data change**：scenario.clusters、clustering.focus_weights、subregion、custom_busmap | 改变国内瓶颈、资源集中及小国表示 | 对照实验优先复用整体模型国家内节点映射；独立重聚类会把空间差异混入收益 |
| 11国standalone | **config-only候选**：countries=[国家]；或final_adjustment.drop_country；可靠研究边界需**project script/workflow change** | 单国选择会重建形状、聚类、潜力、需求归一化、区域有限资源/碳约束，远不只是删跨境线 | 中低（尚未实现）。建议先定义同源完整网络的国家切片和共享节点规则；drop_country可能按subregion而非ISO2处理，需专门验证，不能直接交付11条命令 |
| External commodity imports | **data/config + project script候选**：add_carrier_buses的fuel Generator、行业油/气供给、spatial_*；export是H₂出口设置 | 保留原边界的燃料可得性；去掉燃料Generator会变为自给问题 | 没有一个已确认“外部进口总开关”。逐carrier记录供给价格/上限/来源含义，国内与进口若未区分则不能报告真实进口量 |
| Carbon constraint | **config-only入口，但当前有键名冲突**：co2.budget.base_value/year/enable、opts Co2L/Ep、solve_network封存限制 | 未启用baseline与区域绝对排放路径是不同情景；从电力变全SC须确认碳统计边界 | 阻断：co2base_value与base_value不一致；不得自动迁移/选国家预算。见CARBON_IMPLEMENTATION_NOTE |
| 技术成本/燃料价 | **data change + config-only**：冻结pre_costs、AEO8覆盖、costs overrides | 改变成本序、转换技术竞争及国家收益 | 逐行Source→Raw→转换→模型值→候选→确认；不自动更新技术目录 |
| 工程兼容与已知缺陷 | **source-code change（另批实施）**：country聚类、PROJ环境、白名单字符串、拓扑/缺失值传播等 | 修复可能恢复原意，但若改变负荷/容量/约束就有科学影响 | 单独fix提交，明确engineering fix/data correction/model change；固定原样结果，校验前后守恒；本次不实施 |

## 未来实验设计的最小逻辑（仅方案）

先冻结同一套经确认的SC输入、节点/时序、技术、价格、存量、规划路径和排放口径。然后定义“关掉哪些跨国连接”：至少交流Line、DC/B2B；H₂/CO₂/生物质等按基线是否存在及研究边界逐项决定。保留原边界允许的外部商品供应。

国家切片必须处理区域共享Bus/Store（燃料、有限生物质、CO₂）与区域约束；按相同规则分配有限资源，不把完整ASEAN额度复制11次。通过输入守恒、跨境连接清单、区域总量加总、成本账和国家标签验收后才设计正式求解批次。

概念指标 `Σ C_i(standalone,SC) − C_ASEAN(integrated,SC)`成立需要两边采用相同服务需求和成本边界。若整体可共享区域碳预算、国家却用固定预算，差额同时包含排放额度协作效应，应在解释中明确，不能全部归因于电力互联。国家价格/市场收入不是未经论证的welfare替代。

可以进入**有明确待决项的实验设计讨论**；当前不能冻结可执行正式实验。无正式求解命令、无新override、无新技术、无碳政策变更。
