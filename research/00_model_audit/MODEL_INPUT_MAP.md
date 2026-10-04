# PyPSA-ASEAN 输入审计（A1）

审计日期：2026-09-30。固定代码：`ce327bfae2abe5526d4c1976173f0f8d08366ba5`。
范围：读取 Windows `audit_repo/` 固定检出及 WSL 原运行目录的既有输入、前处理网络和三个教程结果；没有求解、修改参数、下载新版数据或覆盖旧报告。当前用户任务取代旧 `NEXT_REPRO_STEPS.md` 中先跑 2025 基准的建议，本轮不执行该建议。

证据分级：**直接读取**＝代码、配置、既有文件内容；**推导**＝依据公式得到；**推断**＝尚未以完整测试证明；**待确认**＝原始来源或人工选择未闭合。读取成功不表示数据已获研究使用确认。

## 结论与重要缺口

1. **直接读取**：当前教程实际求解的是经过 `final_asean_adjustment` 裁剪的电力相关系统，保留燃料/氢转换、储能和 CO₂ 记账，但没有完整终端部门耦合需求。此前 `CURRENT_PROGRESS.md`、`REPO_AUDIT.md` 中依据 sector 开关而作的范围描述应以本报告和 `SECTOR_COUPLING_MAP.md` 为准，旧文件作为历史保留。
2. **直接读取**：三个年份节点工业需求表各有 48 行、10 个数据列，480 个单元格全部为空，并重复出现 `low-temperature heat` 列名；最终工业电力需求为零。不能将其解释为真实工业零需求。见 `LEDGER_VALIDATION.json` 与输入副本。
3. **直接读取**：需求增长表包含 DEFAULT、MA、NA、US，无 ASEAN 国家行；代码会使用 DEFAULT。它是原模型行为，不是本轮认可的 ASEAN 参数。
4. **直接读取**：成本不是单一 DEA 数据。先读取 technology-data v0.13.2，再以 AEO8 覆盖若干技术的 investment/FOM/VOM，最后进行单位、币种、缺失值和年化处理。电解槽投资的来源字段包含 private communications/IEA，不能统一归为丹麦目录。
5. **已找到但仍待版本对齐**：本地IOP论文及用户DEA目录已取得。论文§3.1明确是电力案例、其他部门仅计电力需求；§3.3区分无显式排放上限baseline与区域绝对上限DEC。用户Renewable Fuels文件属性为Version August 2026、sheet为80 AEC 100 MW，模型来源描述却为86 AEC 100 MW。论文代码SHA、冻结DEA原工作簿、AEO8摘录口径、默认值适用性和已知拓扑损失仍未闭合。所有台账行均为UNVERIFIED/PENDING，Final_Value和Verified_By为空。

## 输入链路

下表路径相对固定模型仓库；R 表示运行名 `baseline-aims-3H-tutorial`。源码入口的文件/函数名为可检索定位点，完整固定版本链接见文末。

| 输入族 | 来源与实际入口 | 转换和进入模型的位置 | 当前值/版本证据 | 未闭合项 |
|---|---|---|---|---|
| 电力时序需求 | `data/demand/forecasts_on_historical_period.parquet`，DemandCast；`Snakefile:build_demand_profiles`，`build_demand_profiles.py:read_demcast_load` | 取天气年2013、ISO3→ISO2、国家负荷按区域人口/GDP映射；写 `resources/R/demand_profiles.csv`，`add_electricity` 加 Load | `load_options.source=demcast`；教程数据包链接在 `configs/bundle_config.yaml:demandcast_asean_tutorial` | 训练/发布版本及原始小时单位、国家缺失处理、与论文一致性；不是最终用电总量 |
| 电力总量与国家分配 | `final_adjustment.total_elec_demand` 引用 AEO8；`elec_per_capita`/`industry_share` 注释引用 IEA；`data/worldbank_pop_forecast.csv` | `include_electricity_growth` 以人口×人均量分配 ASEAN 总量，随后 `redistribute_industrial_load` | 2030目标1.6588e9、2040目标2.2646e9、2050目标3.0363e9 MWh；人口下载函数实际指向 UN WPP2024，文件名不是来源证明 | 版本/原始表；TL industry share 0.01明确注释“Data not available”；目标与实际加权需求不一致，见部门报告 |
| 存量电厂/容量 | powerplantmatching 配置匹配 GPD/GEM/EESI；`build_powerplants` → `resources/R/powerplants.csv` | 地理清洗/匹配母线，`add_electricity` 附加常规、可再生及水电；`add_existing_baseyear` 按投产/寿命分组，后期 `add_brownfield` 继承 | 实际CSV已复制、哈希；EESI配置注明非欧洲无数据，不能声称对 ASEAN 实际贡献 | 各数据库原始快照、匹配冲突/缺失寿命、已有容量守恒；既有简化损失尚未解决 |
| 气象与可再生出力 | ERA5/Atlite；`cutouts/asean-2013-era5-tutorial.nc` → `build_renewable_profiles` | 资源转换、时序容量因子、空间聚合；Generator p_max_pu、水电 inflow | 教程2013-03-01至03-07右开，3h；在指定 cutout 目录只发现教程文件 | 全年原始 cutout、来源版本、文件哈希/地理覆盖、设备曲线；短窗按8760权重不能代替全年 |
| 可再生潜力 | Copernicus LC100 v3.0.1 2019、GEBCO2025、natura raster、GADM/海域/自定义形状；`renewable` 参数 | 可利用面积×容量密度、排除掩膜/水深/距离 → profile文件 p_nom_max；`add_electricity`、聚类 | `Snakefile:build_renewable_profiles`列明文件；`build_natura_raster=false`不等于“不使用natura输入” | 原始包/许可/哈希、土地口径；屋顶与地面是否重叠，不能用新地图替换 |
| 屋顶潜力 | 完整ASEAN配置 `use_building_size=true`；教程false | Microsoft建筑轮廓方法或人口×面积×kW/m²，`add_electricity_distribution_grid` 加低压侧 Generator | 教程用人口法；非教程建筑输入未验收 | 屋顶面积、安装比例、建筑数据版本及地区适用性 |
| 水电资源 | HydroBASINS、`hydro_capacities.csv`、EIA年发电量、`IRENA_Statistics_Extract_2025H2.xlsx`、电厂位置 | `inputs_hydro`/`build_renewable_profiles` → inflow、径流/水库/PHS | 工作流引用已定位；既有水电profile已列清单 | 年代、容量和发电量校准口径/原始文件对应关系 |
| 电网 | `electricity.base_network=osm-plus-prebuilt`，0.1.1；实际路径 `data/osm-plus-prebuilt/0.1.1/` | `base_network` → 项目线 → simplify → cluster → prepare_network；Line交流、Link直流/B2B | 版本/代码读取；`scenario.ll=v2.0`；跨境端点 country 才是身份依据 | 原始GIS、端点765→缺失766、方向性AIMS再分配；不可按单列line.country判断跨境 |
| 输电项目 | `data/transmission_projects/AIMS`、`ID_SuperGrid` | build/add_transmission_projects，状态筛选、投产年、new_link_capacity；末段又按AIMS表调整既有交流联络线 | AIMS/ID_SuperGrid均true；delay_construction=0；`readjust_existing_interconnections=true` | 原始项目表版本、重复项目及正反端点匹配；本轮不研究延迟 |
| 技术与燃料价格 | technology-data v0.13.2、AEO8 D15/D17/D18 | pre_costs → append_cost_data → costs → process_cost_data 的 elec/sec 两种输出 → 各组件 | 2030/2040/2050原机成本文件复制，逐行台账；详见下节 | 原始文献/工作簿、汇率数据版本、HHV/LHV、discount rate和容量口径 |
| 燃料供应/外部商品 | `prepare_sector_network.py:add_carrier_buses` | fuel Bus + 可扩张 Generator，燃料 marginal_cost；Store储存；常规机组转多端Link排碳 | gas/oil/coal供给Generator存在；没有因此获得国内生产/进口来源分解 | 模型中的供给入口可解释为外部可得燃料，但不能直接把全部输出记成“实测进口” |
| 基年部门需求 | UNSD能源统计，`data/demand/unsd/paths/Energy_Statistics_Database.xlsx`指向原始txt；2019基年 | build_base_energy_totals分类交易/燃料、质量/能量→TWh，居民、服务、道路、铁路、航运、航空、农业等 | 原机UNdata_Export_20250502*.txt已列清单；`energy_totals_base.csv`复制 | 下载日期≠统计年；燃料转换因子、缺失/地区映射需确认 |
| 未来部门需求 | `data/demand/{growth_factors_cagr,efficiency_gains_cagr,fuel_shares,district_heating}.csv` | prepare_energy_totals: base×(1+CAGR)^(year−2019)，燃料/电动化分配，最后fillna(0) | effective demand scenario=DEC（旧scenario.demand迁移后）；DEFAULT回填 | 默认值来源与缺失转零是研究阻断项，不得作为确认值使用 |
| 工业需求 | build_base_industry_totals、industrial_database、分布权重、industry_growth_cagr、USGS氨产量 | build_industry_demand → `industrial_energy_demand_per_node...csv`；列头MWh/a(tCO2/a)，add_industry除8760建立Load | 三年节点表全空；prenetwork工业负荷已为零，非仅最后裁剪造成 | 上游UNSD工业交易、节点分配、化工/氨扣分配及空值根因，不能推测具体修复 |
| 热/交通负荷曲线 | energy_totals、人口布局、温度/热需求/COP、交通availability/DSM | build_heat_demand/COP + prepare_heat_data；prepare_transport_data/input；进prepare_sector_network | 路陆transport教程false；完整配置true；热构建后被裁剪 | 地区热需求模型、车辆参数、需求统计边界、民用/工业电力避免重复 |
| 港口/机场 | WPI；教程用本地GDB转换CSV；OurAirports机场/跑道CSV | prepare_ports/airports按地理/权重将航运航空需求分配到节点 | WPI CSV和provenance原样复制；此前原ZIP哈希在证据中 | 论文WPI版本与正式机场快照；源码“dummy data”注释不能单凭注释判定真实来源 |
| 生物质/碳存储 | sector.solid_biomass_potential=360 TWh/a引用论文；biogas=0.5继承默认；co2_sequestration_potential=200 Mt继承欧洲说明 | add_biomass按空间人口分配/燃料Store；solve_network另加CO₂封存约束 | 配置直接读取；CO₂不是仅检查global_constraints表即可穷尽 | ASEAN原始资源资料、区域总量分配、默认值适用性，尤其standalone不得各复制总量 |

## 成本来源、转换与具体例子

固定入口：`Snakefile:614–675`；`append_cost_data.py`；`process_cost_data.py:load_costs/prepare_costs`；`prepare_sector_network.py`组件赋值。

1. 下载路径模板为 `https://raw.githubusercontent.com/PyPSA/technology-data/v0.13.2/outputs/costs_{year}.csv`，本次复用原机 `pre_costs_*.csv`，没有重新下载或替换。
2. AEO8 D15：技术名映射；资本/FOM/VOM先按2020 USD→EUR汇率转换。D17按年对资本乘 `(1−Capex decline)`、VOM乘 `(1−Opex decline)`；FOM用固定运维绝对值除投资×100计算。D18 regional_factor当前false，实际因子1。代码会覆盖映射到的三类参数，不覆盖所有技术全部字段。注释“资本→投资用寿命”不是实际公式，不能照抄注释。
3. process_cost_data对 `/kW`（含/kWh）乘1000；汇率函数固定参考年2020；读入/透传currency_year不等于已独立做通胀核对。缺失字段按fill_values回填，例如efficiency=1、lifetime=25、investment=0、discount rate=0.07；项目已声明0.071也不能代替逐行实际discount rate核验。
4. 年化：`fixed=(annuity(lifetime,r)+FOM/100)*investment*Nyears`，`Nyears=Σw_generators/8760`；边际系数通常`VOM+fuel/efficiency`，实际多载能Link须避免与燃料Generator重复算燃料。MW电输出、MW输入和MWh储能容量必须分别核对。
5. 求解预处理 `noisy_costs` 会加小扰动（边际成本、Line/Link长度相关成本）；台账processed成本不等于最终组件系数。现有结果包含这些差别，需在未来成本分解中显式处理。

**直接读取的2030示例（未人工确认）**：electrolysis效率0.6217、FOM 4%/年、寿命25年，来源字段指向 `inputs/data_sheets_for_renewable_fuels.xlsx`，描述sheet `86 AEC 100 MW`；投资1500 EUR/kW_e来源字段为 private communications 和 IEA E-fuels报告。原机sec表fixed及教程电解Link资本系数为188715.7758309984（需按输入容量和模型期间解读）。DEA效率行原始HHV/LHV单元格仍未取得，不能靠“看起来合理”确认。

模型来源字段指向的DEA相关原始工作簿还包括 `technology_data_for_el_and_dh.xlsx`、`technology_data_catalogue_for_energy_storage.xlsx`。用户本地6份工作簿的文件名/哈希/版本线索见USER_SOURCE_INVENTORY.json；尚不能替代这些冻结输入。官方目录页面只能证明目录入口存在，不能证明某个最新版就是当前输入：[DEA目录](https://ens.dk/en/analyses-and-statistics/technology-catalogues)。冻结编译库入口：[technology-data v0.13.2](https://github.com/PyPSA/technology-data/tree/v0.13.2)。本次仅核查入口，不采用新值。

## 台账与资料可得性

`DATA_LEDGER.csv`包含规定字段及附加的原编译值、AEO8覆盖后值、处理后单位、值阶段、币年、国家/节点和SHA256。Raw_Value仅在实际读取原模型输入单元格时填写；“原模型输入”仍不等于“原出版物”。成本原文单元格未核实时留空，编译值单列保存。Final_Value始终留空，不暗示候选已选定。

本轮覆盖三年成本逐行、派生fixed/marginal_cost、运行元数据、基年/未来部门需求、工业空表、需求假设表和AEO8摘录。电网/气象/电厂等以输入族映射和清单登记，**不是整个模型每个地理像元/每条设备记录的全面数值验收**。大型文件没有全部复制或计算哈希，原始文献未全部找到；未完成“所有原始资料双方持有”的放行要求。

复核附件：`AUDIT_RUNTIME_EVIDENCE.json`、`INPUT_INVENTORY.json`、`LEDGER_VALIDATION.json`、`input_snapshot/`。小型副本原样保存并有哈希；下载包与大栅格留在原机，清单中空哈希明确标记待归档。提取时PyPSA导入出现PROJ资源路径警告，但三份网络读取及表提取完成；本轮未做任何地理重计算，不把该次读取当作环境完全验收。

固定源码：[模型仓库ce327bfa](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/tree/ce327bfae2abe5526d4c1976173f0f8d08366ba5)。更多待提供资料见 `USER_INPUT_NEEDED.md`。
