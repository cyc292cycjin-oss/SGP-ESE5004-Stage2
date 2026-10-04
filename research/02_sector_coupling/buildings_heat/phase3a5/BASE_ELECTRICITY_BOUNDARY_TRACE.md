# Base electricity 计量边界追踪

Material Passport: academic-research-suite / fact-check; Phase3A5 v1; 2026-10-02。源码观察与数值核对为 VERIFIED OBSERVATION；统计适用性仍 UNVERIFIED；研究方法为 PROPOSED。不代表模型输入获得人工接受。

**结论：真实 A* 尚不能冻结。** 沿用 Phase3A4 已接受的共同 country/year/meter/time-grid 会计结构；本轮没有重定义 A*，也没有改动任何模型缩放。需要先把源统计电量、网络负荷和 Buildings 终端电量对齐，不能用变量名 `total_elec_demand` 代替计量证据。

## 1. 固定版本和实际来源不同

| 层 | 固定提交 | 原始电力曲线及时间含义 |
|---|---|---|
| Paper Reference P | `5bacad702ccfed17ad19ab510fa710651e966f2c` | GEGIS，`ssp2-2.6/2030/era5_2013/Asia.nc` 等洲文件；预测年2030、天气年2013。ASEAN覆盖配置使用 LA←KH、TL←ID 替代曲线，并设置替代缩放。**没有 DemandCast reader**。|
| Upstream SC U | `a3616a68ee44592af6527ca9024a90f1956646ae` | `configs/config.asean.yaml:118` 选择 `demcast`；读取 `Forecast load (MW)`，按 `Time (UTC)` 的2013年筛选；DemandCast reader不使用 `prediction_year=2030`。|
| Buildings validation V | `50a73d8f531132c5459174a55cac412d5f684462` | 与U相同DemandCast入口；继承已接受E1/E2/E4；没有E3。|
| Future research model R | U同一提交 | 未获得新的科学数据或E3实现。不能以V工程验收代替科学基准接受。|

证据：[逐文件SHA与工作树身份](evidence/CODE_IDENTITY.json)、[P/U差异](evidence/P_U_DEMAND_CODE.diff)、[函数位置与AST身份](data/processed/buildings/BOUNDARY_SOURCE_CHECKS.json)、[既有论文有效配置](../../../01_baseline_construction/evidence/PAPER_EFFECTIVE_CONFIG.yaml)。此处是固定源码/配置链，不是新运行得到的网络结果。过去教程不能证明论文输入相同。

GEGIS官方说明将国家年需求与归一化小时形状区分：SSP人口/经济背景用于预测年总量，机器学习生成小时形状。原包的年度统计版本、各国供电/终端计量口径和发电侧损耗尚未由固定文件metadata闭合；现代说明只能解释方法，不能证明P打包输入的确切生产版本。[GlobalEnergyGIS作者说明](https://github.com/niclasmattsson/GlobalEnergyGIS)。P的bundle链接与预期文件保留于 `evidence/source_snapshot/P/configs/bundle_config.yaml:197–213`，不是用户需要重新提供的代码入口。

## 2. DemandCast 链恢复到了哪里

1. [DemandCast论文v1](https://arxiv.org/html/2510.08000v1)：归一化小时形状与年尺度分开；年用电/人来自Ember。论文引用代码v0.9.0。
2. 已取得该版本四个相关源码文件，逐一对照Git tree验证blob。tree为 `fe8454093c776138df78ae59b30db8e3c89ec7fa`；`ETL/download_annual_electricity_data.py:110–156` 从Ember年度表取 `Demand` 和 `Demand per capita`。该CSV URL不固定历史发布日期。
3. [模型指定Zenodo记录18374352](https://zenodo.org/records/18374352)：发布2026-01-26，version1.0.0，历史预测2000–2024，CC BY4.0；完整parquet 390,009,152 bytes、MD5 `be6b47c118d547fccf22245ec7cd8323`。**元数据没有证明完整导出来自上述v0.9.0 SHA**，也没有各国终端/损耗拆分。
4. 本地保留的教程parquet为1,005,362 bytes，SHA256 `ade3a79fa50602434adcf6bc2954a297cd229165659263089ab073337466ef8c`，11国×8760=96,360行，2013 UTC全年。它不是完整archive的同字节副本；没有比较全包，不能声称已验证为它的精确子集。[本地metadata](evidence/LOCAL_DEMANDCAST_METADATA.json)。本轮没有为此下载390MB全包。
5. 本轮取得的[Ember方法v1.6](https://files.ember-energy.org/public-downloads/ember_electricity_data_methodology.pdf) PDF9将Demand表述为生产加净进口；PDF10说明发电数据目标采用gross口径并保留国家例外。它支持“不能默认final-meter”的判断，**不证明DemandCast当时Ember版本及每国own-use/loss口径已核实**。

源码/原件/版本/许可/用途/哈希见 [SOURCE_REGISTRY](data/raw/buildings/SOURCE_REGISTRY.json)。当前DemandCast与P的GEGIS都不提供可直接扣除的R/S历史电热字段。

## 3. 同一电量经过哪些改写

| 步骤 | 当前源码可直接确认的动作 | 对E3的含义 |
|---|---|---|
| `build_demand_profiles` | 选曲线、国别scale、按国家分配；多节点用GDP0.6与population0.4组合权重。 | 这是总电力节点权重，不是space/water份额，更不是批准的Buildings空间方案。|
| `add_electricity.attach_load` | 把曲线直接写到Load的`p_set`；没有R/S/end-use观测拆分。 | 此时“base”不是纯Residential。|
| `prepare_sector_network` | 原AC负荷标为AC；`add_residential` 用 `electricity residential` 目标覆写原曲线。`add_services` 新增 `services electricity` Load，继承归一化R形状。 | **R替换、S叠加**；代码未保存一个经过核实的O残差。|
| `prepare_energy_totals` / `prepare_heat_data` | 电热相关列含燃料转电假设；`electric_heat_supply`被构造但扣电语句注释掉。 | 这些列不是D/E历史观测；不能取消注释当作E3修复。|
| `add_electricity_distribution_grid` | 配电Link被创建为`efficiency=1`；配置`efficiency_static=0.97`实际乘在**AC负荷**上，然后AC与electricity Loads移到低压bus。 | 不是给全部国家供电量统一做有证据的3%损耗对齐；S不被同样乘0.97。源码注释所引欧洲数据口径不能证明ASEAN损耗。|
| `include_electricity_growth` | 总量按国家人口×人均用电权重分配；人口缓存名虽为worldbank，缺缓存时下载UN WPP2024。六个年份区域目标来自配置AEO8 BAS。 | 即使不裁成power-only也执行；可能覆盖之前的部门总量/损耗效果。|
| `redistribute_industrial_load` | 按配置industry share在被选Load之间再分配。 | 在工业/非工业均存在、分母非零、权重适用等条件下才保留被选总量；不代表整网O+B+C闭合。|

精确入口见三层快照的函数定位JSON。U关键行：`prepare_sector_network.py:3033,3247,3402,3413–3469`；`prepare_heat_data.py:177–212`；`final_asean_adjustment.py:83,175–293,419–426`。

**额外代码事实：** `elec_carrier` 中 `"agriculture electricity" "rail transport electricity"` 缺逗号，Python把它们拼成一个字符串。实际列表是AC、industry electricity、agriculture electricityrail transport electricity，且没有services electricity。P/U/V均保留该行为。此处只报告，未修复，也未开展其他部门研究。V的E4修正了保留列表中的Services命名，不等于Services已进入增长/重分配列表。

增长函数先用objective权重计算动态年量，再以**未加权**曲线均值归一；静态项使用8760，而新均值除以objective权重和。均匀完整年权重下可得到预期被选总量；不均匀权重或截短年不能直接保证相同恒等式。未来物理能量应沿用Phase3A4物理snapshot权重契约，本轮不改函数。

## 4. AEO8 目标的关键核对

固定配置P/U/V均有 `2050:3.0363e9` MWh。AEO8原PDF82/印刷80 Figure3.25标题为2050 ASEAN **Electricity Generation**，BAS=3,036.3 TWh，数值完全对应。November2024勘误PDF3更新该图，**BAS总量仍3,036.3 TWh**，本轮已目视核查。

AEO8 PDF48/印刷46：BAS住宅/商业设备效率按最新年份保持，clean cooking access与electrification按各国2005–2022平均年增速发展。PDF49/印刷47：供电满足需求，own-use与losses保持最新统计占比。因此BAS也包含既有电气化增长假设；它不是可直接再叠加未来所有内生电热用电的纯外生直接电量。[AEO8与勘误官方入口](https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/)。

已核实2050数值与图对应；**没有把六个年份均称为原始年表已核实**。AEO8当时覆盖ASEAN10；配置权重分配覆盖11国含TL，需要单独说明总量地域桥。总量数值的对应不是作者原始提取工作表的完整恢复。

## 5. 十个边界问题的答案

| 问题 | 结果 |
|---|---|
| 原始源 | P=GEGIS；U/V=DemandCast；后续年目标=AEO8+人口/人均权重；R/S=UNSD衍生能源总量。|
| final-meter还是供电 | AEO8核对的是发电量；DemandCast/GEGIS不能由现存元数据证明为共同终端边界。网络Bus位置不决定统计口径。|
| 输配损耗、自用电 | AEO8方法显式含这些假设；Ember当前方法为生产+净进口。固定每国/年损耗、own-use及原输入版本未闭合。|
| cooling/cooking/heating | 综合用电理论上涵盖相应用电，但源文件无足够用途分解；“包含多少、与UNSD是否同域”仍待核实，不凭代码假设精确包含关系。|
| 年量/小时 | P GEGIS预测总量+形状，U/V DemandCast历史小时预测；后续被AEO总量再次缩放。|
| 最终缩放 | 固定区域目标按人口×人均用电分国家，只缩放被选carrier；S遗漏及拼接问题见上。|
| 配电效率 | 0.97乘AC Load，Link初始化1；没有发现后续把该Link设为0.97的消费调用。不能把它称为已验证ASEAN meter bridge。|
| R/S | R覆写原AC；S新增；未有证据闭合的O。|
| 工业重分配 | 再改被选Load的部门占比；条件性被选总量守恒不等于整个模型闭合。|
| 未来隐含电气化 | AEO8 BAS有；各国/用途增量未剥离，存在与内生转换叠算风险，不能量化为已发生的真实模型误差。|

**停止点：** 保留已接受的 `D_accepted=A*−h_R−h_S`，历史电热只扣一次；不能从gross target减一个统一3%就声明A*已建立，也不能将未核实的AEO隐含电气化当额外直接负荷。待证据与人工选择完成后才讨论E3实现。
