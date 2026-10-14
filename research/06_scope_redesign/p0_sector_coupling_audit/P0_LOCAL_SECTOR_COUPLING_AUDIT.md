# 第 0 阶段：部门耦合现状只读审计

**只读审计：未构建、未求解，没有修改任何源码、配置、数据或历史结果。**

## 结论摘要

1. 当前 Full-SC 模型中，**除电力外，所有终端部门都是按载体外生固定的终端能源量**；没有任何"服务需求 + 可替代技术"。上游的 add_heat、add_land_transport、add_industry、add_shipping、add_aviation 在研究入口中一个都没有调用（VERIFIED）。
2. 7,724 TWh 的 oil/gas/coal final-energy accounting Link 由 `build_research_assets.build_fragment()` 生成，固定负荷由 `assembly_components.bind_loads()` 加入。改成可替代的最小改动点也在这两处，同时需要放宽 5 个静态校验（VERIFIED / INFERENCE）。
3. 氢路径：电解、SMR、SMR CC、燃料电池、FT、储氢罐都已建好且可扩展，但优化结果为 0。原因有五：没有任何 H2 需求、没有 CO₂ 约束、化石燃料无限量、捕集的 CO₂ 无处封存、没有 H2 管网。`only_elec_network` 和 `final_asean_adjustment.py` **只作用于原作者的参考网络**，研究配置已把它们覆盖并禁用，不是氢路径未开放的原因（VERIFIED）。
4. CCS 封存、DAC、BECCS、工业过程排放都没有建；状态为 DEFERRED，不是"计为 0"。国际燃料舱按 2019 常数固定，排放全额计入报告视图（VERIFIED）。
5. 制冷嵌在固定的 Astar 电力里，没有独立的量（VERIFIED）。
6. 807 个生物质账户是**需求推导的义务量**（UNSD 2019 × 增长比 × 节点份额），不是资源潜力；仓库里没有东盟的潜力数据。400 项化石供应价格固定、数量无上限，**模型里没有任何 LNG 接收站**，lignite 在 registry 中缺少价格记录（VERIFIED）。
7. 新口径与 Phase3 冻结决定有 26 条需要对照：冲突 21 条、性质改变或待定 3 条、兼容 2 条（第 9 节）。
8. 规模估算（INFERENCE）：部门组件按 100 节点全量建，中档约 4,170 万列、1.93 亿非零，求解内存约 71–77 GiB，顶到 122 的 75 GiB RSS 保护线；高档约 98–106 GiB，超过 90 GiB 的 cgroup 上限。若非电部门只建在 11 个国家枢纽上，中档约 1,280 万列、约 24 GiB。

## 证据说明

| 缩写 | 含义 |
|---|---|
| 代码、配置、组装记录 | 研究仓库提交 `2adde292c53f0aac6aebfe3b18eb34540321171d`（D 阶段分支头，Gate6/D 阶段实际使用的代码）：`scripts_project/`、`configs/`、`scripts/`（上游 PyPSA-Earth）、`Snakefile`、`workflow/`、`research/04_model_assembly/`、`research_inputs/` |
| P3 | Phase3 研究记录，提交 `d1c2790281b8768228ee369aeb81dd543654af4a`（分支 `codex/remaining-sector-phase3c`）的 `research/02_sector_coupling/` |
| 上游默认 | `config.default.yaml`，与上游原版仓库 `pypsa-asean/config.default.yaml` 逐字节一致 |
| 网络事实 | D-5 已求解的 2920 网络与 D-7b 只读统计（`work/d_stage_2920_20261013/evidence/D7B_*.json`） |

证据由 4 个并行的只读审计任务收集，其中关键行号（`config.asean.yaml:262`、`baseline.yaml:17-20,29-42,70-71,82-104`、`build_research_assets.py:185-213,229-236`、`fixed_accounts.py:44-45`、`build_research_network.py:69,93-104`、registry 的价格条目）由我逐条亲自复核。

## 1. 部门 × 表示方式矩阵

机器可读版本见 `P0_SECTOR_MATRIX.csv`，下表为摘要。

| 部门 | 需求表示 | 已开的技术 | 写了但关着 / 未调用 | 证据 |
|---|---|---|---|---|
| 电力（Astar，终端电力父账） | 外生固定：96 个 AC Load；2050 = AEO8 BAS 225 Mtoe × 11.63 TWh/Mtoe × 2019 份额；时序取作者参考网络 base-load 形状。建筑、工业、农业、铁路和道路 EV 的用电都嵌在其中 | 光伏、屋顶光伏、陆上/海上风电（候选）；745 台存续机组；OCGT/CCGT；电池与户用电池；配电网；DC/B2B（24 条跨境边） | H2 turbine、Sabatier、helmeth 只在蓝图选项中 | `build_research_assets.py:86-134,207-211,229-230`；`baseline.yaml:94`；`carrier_architecture.py:81-85` |
| 建筑：居民/商业燃料（采暖、热水、炊事） | 外生固定，按 oil/gas/coal/biomass 分账户；2050 = 2019 × 增长代理；时间上平坦 | 无（没有热母线，也没有热泵、锅炉、CHP、储热、太阳能集热） | 上游 add_heat/add_residential/add_services 未调用；`sector.enable.heat: true` 不被研究入口读取 | `baseline.yaml:20`（`heat_without_accepted_service: embedded`）；`demand_buildings.py:15-27` |
| 建筑：制冷 | 嵌入 Astar | 无 | 上游本身没有制冷 | 第 5 节 |
| 陆路交通：道路 | 外生固定 RoadResidualFuel（oil/gas/biomass）；EV 用电嵌入 Astar，不单独物化 | 无（没有 BEV、FCEV、V2G） | `land_transport_*_share` 不被读取；`demand_accounting.road_energy()` 写了但未调用；`validate_fullsc_final.py:91` 禁止 EV Load | `baseline.yaml:91,96-99`；`demand_transport.py:14-44` |
| 铁路 / 交通 NEC | 铁路用电嵌入 Astar；非电部分按 2019 常数固定 | 无 | — | `demand_transport.py:24-34` |
| 航运：国内 / 国际燃料舱 | 外生固定 oil，按 2019 常数；按港口权重分配到节点 | oil 母线可由 FT 供油 | 上游 add_shipping 未调用；`shipping_hydrogen_share` 全为 0 | `baseline.yaml:96,100-101`；P3 `phase3c/FULLSC_SECTOR_CARRIER_MATRIX.csv:7-8` |
| 航空：国内 / 国际燃料舱 | 外生固定 oil，按 2019 常数；按机场权重分配 | 同上 | 上游 add_aviation 未调用 | 同上，`:9-10` |
| 工业（钢铁、水泥、化工、氨均未拆分） | Mode A：单一 IndustryFinalEnergy 账户，按载体固定；只取 UNSD 制造业父账；2050 = 2019 × 561.0/185.6 | 无 | 上游 add_industry/add_ammonia 未调用；热和 H2 两行为 PENDING | `demand_industry_agriculture.py:11-32`；P3 `phase3c/INDUSTRY_FIRST_FULLSC_BOUNDARY.md:3-29` |
| 工业过程排放 | 未建模（DEFERRED） | — | 上游 `build_industry_demand.py:260-300` 和 `prepare_sector_network.py:2088-2130` 未用 | P3 `phase3c/CARBON_SCOPE_FREEZE.md:7,15` |
| 农业 | 外生固定 oil/coal/biomass；用电嵌入 Astar | 无 | 上游 add_agriculture 未调用 | `demand_industry_agriculture.py:33-42` |
| 非能源用途 | 不在模型中，只作为 `nonenergy_reference` 记录 | — | — | `reconstruct_base_accounts.py:128-130` |
| H2 与合成燃料（供给侧） | 没有 H2 需求，只是中间载体 | 每节点可扩展：电解、SMR、SMR CC（cc 0.9）、燃料电池、FT、储氢罐，D-5 求解后全为 0 | H2 turbine、Sabatier、DAC、封存、NH3、甲醇，以及跨境 H2/gas/CO₂ | `build_research_assets.py:195-213`；`build_research_network.py:69,93-104` |
| 生物质 | 385 个终端母线，每个由固定资源 Store 一对一供给（807 个账户） | 只有固定 Store 加计量 Link | 上游 add_biomass/BECCS 未用；360 TWh 区域池被明确禁止恢复 | `build_research_assets.py:236-249`；`fixed_accounts.py:44-57` |

**需求真正的来源**（VERIFIED）：进入网络的需求来自 `research_inputs/assembly_v1/registry.json` 与 `allocations.npz`。2050 年 Kind=DEMAND 的记录合计为 oil 4,937.0 + gas 910.2 + coal 1,876.7 = 7,723.9 TWh，与网络中 accounting Link 的流量一致；另有 biomass 1,607.2 TWh、Astar 电力 2,617.8 TWh。`research_inputs/demand/` 下的 6 张 CSV 只是 Gate2 观测表，其 README 写明"not accepted model inputs"。

## 2. 终端燃料固定的机制

**构建链**（VERIFIED）：`workflow/research_final_assembly.smk` 依次执行三步。
1. `research_final_allocate`（:5-19）→ `allocate_assembly_inputs.py`
2. `research_final_assets`（:21-49）→ `build_complete_assembly.py:57` 调用 `build_research_assets.build_fragment()`
3. `research_final_complete_unsolved`（:51-73）→ `build_research_network.build()`

**具体代码**（VERIFIED）：
- `build_research_assets.py:231-232` 为每个账户和节点创建 `... :: final obligation` 母线，carrier 为 `{fuel} final energy`。
- `:233-235` 对 oil/gas/coal 创建 `... final-fuel meter` Link：bus0 为节点燃料母线，bus1 为终端母线，bus2 为大气；efficiency 1，efficiency2 取燃料的 CO₂ 强度；可扩展；p_min_pu 0。
- `assembly_components.bind_loads()`（:49-67）在 `:65` 用 `n.add('Load', p_set=...)` 加入固定负荷，由 `build_research_network.py:153-155` 调用。
- D-7b 附录 A 已核实：这类 Link 并没有被参数锁死，而是"每个终端母线只有一个固定 Load，没有别的供给"这一拓扑把流量固定了。

**它对应上游的哪些功能**（INFERENCE，按上游代码结构判断）：它把上游 `prepare_sector_network.py` 中各部门函数里的"固定燃料 Load + 排放"统一成了一种计量形式：
- add_residential（3238 起）、add_services（3024 起）
- add_industry（1840-2132）
- add_land_transport（2298-2538）
- add_shipping（1684-1839）、add_aviation（1546-1631）
- add_agriculture（3133 起）、add_rail_transport（3673 起）

研究模型丢掉的主要是：
- add_heat 的内生供热技术；
- add_land_transport 的 BEV、DSM 和 V2G；
- add_industry 的 CC 和 H2 选项；
- add_ammonia、add_dac；
- Sabatier 和 helmeth。

**改成可替代的最小改动点**（INFERENCE，依据下列 VERIFIED 的约束点）：
1. `build_research_assets.py:220-250`：把选定账户的 `X final energy` 终端母线改成服务母线，Load 设为燃料量 × 原技术效率；在 `:233-235` 旁边并联新的 Link，例如 AC→服务、H2→服务，原燃料→服务的那条保留 CO₂ 端口。
2. registry 中的数值和载体，以及 `allocate_assembly_inputs.py:58-73` 的时序形状（例如 EV 不应再用平坦曲线）。
3. 需要一并放宽的校验：
   - `assembly_components.py:62`：终端母线的 carrier 白名单；
   - `build_research_network.py:93-104`：耦合路径白名单；
   - `:88-90`：新 Link 必须进入碳图；
   - `:106-122` 和 `fixed_accounts.py:44-45,67`：生物质的排他性；
   - `validate_fullsc_final.py:55,70-72,91`。
4. 避免重复计算：道路 EV、建筑、工业的用电现在嵌在 Astar 里，内生化之前必须先从 Astar 扣出。已经写好但从未调用的 `demand_accounting.apply_astar_transfers`（:183-211）可以复用。

## 3. 氢路径现状

**结论**：氢路径已组装但没有"开放"。原因不是被开关关掉，而是缺少需求和政策信号，再加上结构上的限制。

| 组成 | 上游开关与默认值 | 本模型取值 | 实际网络 | 证据 |
|---|---|---|---|---|
| 电解、SMR、SMR CC | `sector.hydrogen.production_technologies`（787-790） | 继承上游 | 每节点 1 套，可扩展，结果为 0 | `build_research_assets.py:195-203` |
| 燃料电池 | 上游无条件添加（687-699） | — | 100 条，结果为 0 | `:204` |
| 氢轮机 | `hydrogen.h2_turbine: true`（746） | 合并后的配置为 true，但研究构建器不读这个键 | **无** | `build_research_assets.py:195-213` 中没有 |
| 储氢 | 储罐无条件添加；`underground_storage: false`（747-748） | 储氢罐 e_cyclic | 100 个，结果为 0 | `:212-213` |
| H2 网络 | `hydrogen.network: true`（741） | `config.asean.yaml:210-211` 设为 false；`baseline.yaml:29` 设 `cross_border_h2: false` | **无**，国内 H2 网络也没有 | `carrier_architecture.py:13,40-45`；`build_research_network.py:55-68` |
| FT | `fischer_tropsch: true` | p_min_pu 0 | 100 条，结果为 0 | `:206` |
| H2 需求 | 工业、航运、FCEV 用氢 | 份额全为 0；研究需求层不映射 H2 | **无任何 H2 Load** | `build_research_assets.py:229-250`；`config.asean.yaml:216-239` |

**`only_elec_network` 和 `final_asean_adjustment.py` 的真实作用**（VERIFIED）：
- `config.asean.yaml:262` 设 `only_elec_network: true`，但研究配置 `baseline.yaml:70-71` 把它覆盖为 false，`:82` 又规定 `legacy_final_adjustment: forbidden`。
- `final_asean_adjustment.py` 只在上游 Snakefile 中运行（`Snakefile:1567-1580`），作用对象是原作者的参考网络：用 `strip_network` 裁掉不在保留清单里的组件，并重设跨境线路容量。
- 研究模型只从参考网络中提取电力部分（`build_research_assets.py:56-134`），H2 组件由研究代码自己重建。因此，这两项**不是**研究模型中氢路径未开放的原因。
- 附带发现：
  - 保留清单里写的是小写 "H2 fuel cell"，会把上游大写的 "H2 Fuel Cell" 裁掉（INFERENCE）；
  - 第 86 行漏了逗号，把两个 carrier 名拼成了一个字符串（VERIFIED 代码缺陷，只影响参考网络）。

**真正让氢路径不起作用的五个原因**（VERIFIED）：
1. 没有 H2 需求；
2. 没有 CO₂ 约束或价格：`co2.budget.enable: false`；`research_carbon.policy_enabled: false`；`check_global_constraints` 拒绝 co2 类约束（`assembly_components.py:9-10`）；
3. 化石燃料无限量、固定价；
4. co2 captured 只能从 SMR CC 流到 FT，没有封存；
5. 没有 H2 网络。

据此推断（INFERENCE）：结果为 0 是经济上的选择，不是开关强制为 0（`ACTIVE_SECTOR_COUPLING_FINAL.csv` 中 ForcedUtilisation 为 false）。

相关的 Phase3 冻结决定：P3 `phase3c/HYDROGEN_FUEL_BOUNDARY.md:5-21`，以及 `PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md:20-23`。

## 4. 碳相关

| 项目 | 上游键与默认值 | 本模型 | 证据 |
|---|---|---|---|
| CO₂ 网络 | `co2_network: true`（996） | 关闭：`config.asean.yaml:255`；`baseline.yaml:31` | — |
| 封存潜力 | `co2_sequestration_potential: 200` Mt/a（注释说明是欧洲值）；成本 10 EUR/t | 合并后的配置仍是 200，但**不起作用**：研究层 `geological_storage_asset: false`，校验器发现 co2 sequestered Store 就报错，所以 `add_co2_sequestration_limit` 根本不会生成 | `baseline.yaml:104`；`build_research_network.py:69`；`solve_network.py:939-954`；`gate3/PHASE4_CO2_PHYSICAL_ARCHITECTURE.md:13-15` |
| 捕集 | `cc: true`，`cc_fraction: 0.9` | 只有 SMR CC，捕集的 CO₂ 只能进 FT；`carbon_storage()` 写了但从未调用 | `carrier_architecture.py:137-145` |
| DAC | `dac: true`；上游 add_dac 依赖热母线 | 不建 | `carrier_architecture.py:88-89` |
| BECCS | 上游有生物质 CHP CC 和工业生物质 CC | 不可能：生物质被锁定在固定义务上 | `build_research_network.py:105-122` |
| 工业过程排放 | 上游按设施容量估算，并建 process emissions 母线 | 未建模，状态 DEFERRED（不是计为 0）；`FullSystemEmissionsComplete=false` | `CARBON_SCOPE_FREEZE.md:7,15` |
| 国际燃料舱 | `international_bunkers: false`（上游只计国内份额的排放） | 作为独立固定 oil 账户，按 2019 常数（各 22 条）；排放**全额**计入报告视图，政策权重为 0；`bunker_sensitivity_required: true` | `baseline.yaml:100-101`；`build_research_assets.py:221,233-235`；`bunker_accounting.csv` |
| 碳约束 | `co2.budget` 区域总量 | 无。GlobalConstraint 只有 lv_limit；大气 Store 只用于报告 | D-7b 附录 A |

## 5. 制冷

制冷没有独立表示，隐含在固定的 Astar 电力里，没有可单独识别的量，也没有任何技术或灵活性（VERIFIED）。
- P3 `buildings_heat/COOLING_ACCOUNTING_TRACE.md:3-41`：
  - 没有独立的制冷服务模块，也无法从总电力负荷反推出制冷量；
  - 没有制冷母线或负荷、没有冷水机组、没有区域供冷、没有冷储能；
  - 上游的热泵只单向供热。
- `demand_buildings.py:15-21`：居民和商业的 Cooling 行标为 `IncludedInAstar=True`。
- 冻结决定：
  - `buildings_heat/phase3a7/BUILDINGS_MINIMUM_DEFENSIBLE_BASELINE.md:23`：首个基准不建制冷灵活性；
  - `BUILDINGS_MATERIALITY_REGISTER.csv:14`（M13）：列为后续敏感性候选。
- 上游 PyPSA-Earth 本身也没有制冷表示。按新口径做显式制冷需要自建代码和数据（INFERENCE）。

## 6. 生物质：807 个固定账户

**来源链**（VERIFIED）：
1. UNSD Energy Statistics 2019 年导出数据，SHA 冻结在 `research_inputs/assembly_v1/sources/UNSD_2019_SOURCE_CAPSULE.json`。
2. 用冻结的热值系数换算（`FROZEN_UPSTREAM_CONVERSIONS.json`）。
3. `reconstruct_base_accounts.py:13-22,37-52,124-171` 重建 2019 年的账户。
4. `rebuild_assembly_targets.py:37-47` 乘以增长比，得到 2050 年的值（`GATE4_CONTINUE_DECISIONS.json:8-28`）。
5. `allocate_assembly_inputs.py:56,72-73` 按作者参考网络的电力负荷份额分到节点。
6. `build_research_assets.py:236-249` 按 2019 年的商品构成拆分，每项建一个 Store（e_nom = e_initial = 义务量）和一条计量 Link。
7. 校验见 `fixed_accounts.py:17-79`。

分布：
- 按商品：Fuelwood 248、Biodiesel 194、Charcoal 191、Bagasse 88、Biogases 62、Biogasoline 19、Animal waste 5；
- 按国家：ID 468、MM 102、PH 65，其余国家较少。

**为什么是"固定账户"**（VERIFIED）：`GATE4_RESUME_REQUEST.txt:416-445`（第 12 节）规定，本地生物质供应上限 = 已接受的固定需求义务，原文强调这"不是说国家潜力等于需求"；同时禁止恢复 360 TWh 的免费区域池。相关记录还有 `GATE4_RESUME_DECISIONS.json:48-49` 和 `baseline.yaml:32,39,103`。A06 审计也确认这 807 项是终端核算边界，不是资源潜力。

**改造成"资源潜力"需要的东西：**
- 数据：分国家（最好分节点）、分品类的 2050 年可持续技术潜力，品类包括林业残余、农作物残余（甘蔗渣、稻壳、棕榈 EFB/POME）、畜禽粪便、城市废弃物、能源作物；东盟本地的供应成本；生物碳核算规则；BECCS 的捕集率。仓库里没有这些数据。价格层里只有欧洲来源的候选单价，例如 solid biomass 13.65 EUR/MWh（`gate4/MODEL_COSTS_EUR2020.csv:1497`），且已被判定为"未核实"。
- 可利用的现成接口：上游 `add_biomass`（`prepare_sector_network.py:1119-1275`，总潜力按人口分配）；本项目预留的 `carrier_architecture.allocate_finite_resource`（:123-134，从未调用）。
- 需要放宽的代码：`fixed_accounts.py:44,45,52,54,57,60`，`build_research_network.py:109-120`，`build_research_assets.py:236-249`。还需要用户修订 Gate4 第 12 节的人工决定。

## 7. 外部商品供应

- **生成方式**（VERIFIED）：`build_research_assets.py:185-188` 对 100 个节点 × {gas, oil, coal, lignite} 各调用一次 `external_import`。`carrier_architecture.py:93-120` 把它建成可扩展、`p_nom_max=inf`、`marginal_cost=price` 的单向 Generator，没有年度上限。决定原文见 `GATE4_RESUME_REQUEST.txt:390-413`：这是模型边界，"not a statement that real infrastructure is unlimited"。
- **价格来源**（VERIFIED）：technology-data v0.13.2，经 `price_basis.py` 统一为 EUR2020，逐项溯源见 `gate4/PRICE_REBASE_PROVENANCE.csv`：

  | 燃料 | 价格（EUR2020/MWh_th） | 原始来源 |
  |---|---|---|
  | coal | 9.5542 | DIW 2013 |
  | gas | 24.568 | DIW 2013 |
  | oil | 52.9111 | IEA WEM2017（97 USD/boe） |
  | lignite | 3.2985 | DIW 2013（`:541`） |

  价格在时间上恒定，各国相同，不含运输或再气化费用，也没有敏感性分析。
- **缺口**（VERIFIED）：registry.json 只有 coal、gas、oil 三条 `Cost2050:*:fuel` 记录，没有 lignite 的任何条目，但代码照样建了 100 台 lignite Generator。
- **LNG 接收站和入口**（VERIFIED）：模型中没有任何表示。上游也没有这项能力：`prepare_ports.py` 只用港口规模给航运燃料分配节点，`prepare_gas_network.py` 只处理管道，`add_export.py` 只处理 H2 出口。仓库里没有接收站的位置和容量数据集。按新口径实现"经接收站进口、扩建上限 2.5 倍、只进不出"，需要新增接收站数据和再气化成本，并把每节点无上限的 Generator 改成接收站节点上有容量上限的进口组件（PROPOSED）。

## 8. 差距表

完整版本见 `P0_GAP_TABLE.csv`（21 行，含工作量和数据需求两列）。工作量分 S/M/L 三档（小/中/大）；数据需求分三类：A = 直接来源，B = 推导，C = 假设。

| ID | 能力 | 上游已有能力 | 当前状态 | 新口径需要的改动 | 工作量 | 数据 |
|---|---|---|---|---|---|---|
| G01 | 建筑热服务 | add_heat（heat、district_heating、tes 等） | 嵌入，按载体固定 | 服务需求 + 内生热技术，从 Astar 扣出电力部分 | L | B |
| G02 | 制冷 | 无 | 嵌入 Astar | 显式制冷服务（需新写代码） | L | B |
| G03 | 道路交通 | add_land_transport（外生份额） | 固定燃料，EV 嵌入 | 车公里需求 + 内生 BEV/FCEV/ICE | M | B |
| G04 | 航运 | add_shipping | 固定 oil | 内生燃料选择；燃料舱单独报告并做敏感性 | M | B |
| G05 | 航空 | add_aviation | 固定 oil | 内生燃料选择（含合成航煤） | M | B |
| G06 | 工业分子行业 | add_industry | Mode A | 钢铁、水泥、化工、氨分路线 | L | B |
| G07 | 过程排放 | 有 | 未建 | 分国家、分行业的过程 CO₂ 及捕集 | M | B |
| G08 | 氨 | add_ammonia | 推迟 | NH3 全链路，以及进口和跨境 | M | A/B |
| G09 | 甲醇 | 无 | 推迟 | 全链路（需新写代码） | L | B |
| G10 | H2 网络 | hydrogen.network | 关闭 | 互联情景内生建设 | M | A/B |
| G11 | 氢轮机、地下储氢 | 有 | 未建 | 加入 | S | A/B |
| G12 | H2 需求用途 | 工业、航运、FCEV | 无 | 作为内生选项 | M | B |
| G13 | 天然气网络与 LNG | 只有管道 | 无 | 互联情景的 gas/LNG 网络；接收站进口（扩建上限 2.5 倍） | L | A/B |
| G14 | 外部进口 | 无上限的 Generator | 400 项无上限，lignite 缺登记 | 分子类载体按世界价格从接收站进口，价格 ±20% | M | A/C |
| G15 | CO₂ 网络与封存 | co2_network、sequestration | 无 | 各国封存潜力，CO₂ 运输 | M | B |
| G16 | DAC | add_dac（依赖热母线） | 未建 | DAC，用热和用电都计成本 | S | A |
| G17 | BECCS | 有 | 不可能 | 基于生物质潜力的 BECCS | M | B |
| G18 | 生物质潜力 | add_biomass | 固定义务量 | 分国家、分品类的潜力和成本 | L | B |
| G19 | 排放约束 | 区域总量 budget | 无约束 | 2050 每国净零，覆盖全部能源 CO₂ | M | A |
| G20 | 跨境电力 | transmission_projects | 24 条边；Disconnected 开关尚未实现 | 不互联情景关闭全部跨境设施 | S | A |
| G21 | 需求侧技术选择 | 上游多为外生份额 | 全部固定 | 终端账户改为服务需求加并联技术 | L | B |

## 9. 口径变更表：Phase3 冻结决定 vs 新口径

文件路径前缀 P3 = `research/02_sector_coupling/`（提交 d1c27902）。

| # | Phase3 冻结决定要点（出处） | 新口径 | 关系 | 受影响的文件与登记表 |
|---|---|---|---|---|
| F1 | 唯一的核心干预是跨境 AC/DC；H2、gas、CO₂、NH3、甲醇的跨国通道两组都关（P3 `phase3c/CROSS_BORDER_INTERVENTION_CONTRACT.md:5-14`） | 互联情景 7 种载体的网络内生优化；不互联情景不允许任何跨境设施 | 冲突 | `configs/research/baseline.yaml:24-45`、`integrated.yaml`、`disconnected.yaml`（都为空）；`carrier_architecture.py:13,40-45`；`build_research_network.py:55-68`；`gate4/ELECTRICITY_INTERCONNECT_CONTROL_SET.csv`；`final_validation/PHASE5_INTERVENTION_CONTROL_SET.csv`；`gate3/PHASE4_HIDDEN_CROSSBORDER_PATHS.csv` |
| F2 | 跨境 H2 关闭，禁止共享 H2 池（`HYDROGEN_FUEL_BOUNDARY.md:9,11`） | 互联情景允许 H2 网络 | 冲突 | `config.asean.yaml:210-211`；`gate3/PHASE4_HYDROGEN_ARCHITECTURE.md` |
| F3 | 不建跨境 gas 和 CO₂ 网络（`PHASE3_RESEARCH_MODEL_DESIGN_CLOSEOUT.md:22`） | 互联情景允许 LNG/gas 和 CO₂ 网络 | 冲突 | `baseline.yaml:30-31`；`config.asean.yaml:255`；`gate3/PHASE4_CO2_PHYSICAL_ARCHITECTURE.md` |
| F4 | 合成燃料不得跨国（`FULLSC_CARRIER_INVENTORY.md:14`） | 合成燃料可在互联情景中跨境 | 冲突 | `baseline.yaml:33`；`PHASE4_SYSTEM_BLOCKER_REGISTER.csv`（P4-05） |
| F5 | NH3、甲醇推迟或关闭（`HYDROGEN_FUEL_BOUNDARY.md:19-21`） | 作为可跨境、可进口的载体 | 冲突，甲醇还需新写代码 | `baseline.yaml:34-35`；`industry_accounting.csv` |
| F6 | 外部 H2/NH3/甲醇进口推迟；外部供给只限 4 种化石燃料且单向（`EXTERNAL_COMMODITY_SUPPLY_BOUNDARY.md:11,16`） | 分子类载体按世界价格经接收站进口，只进不出 | 冲突（"单向、两组相同"这部分兼容） | `carrier_architecture.py:55,93-120`；`gate3/PHASE4_FUEL_SUPPLY_ARCHITECTURE.md` |
| F7 | 外部化石市场不设容量上限（`baseline.yaml:102`） | 经接收站进口，扩建上限 2.5 倍 | 冲突 | 同 F6；接收站数据需新增 |
| F8 | Disconnected 仍保留区域共享的电力碳上限（`CROSS_BORDER_INTERVENTION_CONTRACT.md:30-34`） | 2050 每国净零，两组相同 | 冲突 | `gate3/PHASE4_CARBON_ACCOUNTING_ARCHITECTURE.md:18` |
| F9 | PolicyCO2_Power 只管电力，轨迹 1000→100 Mt；禁止全系统上限（`CARBON_SCOPE_FREEZE.md:5-7`；`baseline.yaml:49,61`） | 全部能源相关 CO₂ 纳入每国净零 | **根本冲突** | `carbon_architecture.py`；`gate6_baseline/DEC_ATTRIBUTION_ITEMS.csv`；`gate4/PHASE4_ACTUAL_CARBON_ATTRIBUTION.csv`；`configs/research/gate6_baseline_3h.json`；`final_validation/POLICY_ACTIVATION_READINESS.md` |
| F10 | SMR 共享 H2 和捕集排放的政策归属待决（`gate6_baseline/CURRENT_DECISION_INDEX.json`） | 全系统净零下，电力份额归属基本不再需要；但跨境贸易下需要按国家归属排放 | 性质改变 | `DEC_ATTRIBUTION_ITEMS.csv`；`DEC_ATTRIBUTION_REVIEW.md` |
| F11 | 国际燃料舱按 2019 常数固定，不入政策，只报告；4 国缺数（`gate2/BUNKER_GATE2_ACCOUNTING.md:3`；`CARBON_SCOPE_FREEZE.md:14`） | 计入净零、单独报告，另做不计入的敏感性；缺数自下而上补齐 | 冲突 | `gate4/ASSEMBLY_V1_2050_METHOD_REGISTER.csv`；`bunker_accounting.csv` |
| F12 | 工业 Mode A（`INDUSTRY_FIRST_FULLSC_BOUNDARY.md:3-29`） | 需求侧技术选择内生 | 冲突 | `demand_industry_agriculture.py`；`industry_accounting.csv`；`gate2/RESEARCH_DEMAND_LEDGER.csv` |
| F13 | 过程排放另立账户、推迟，缺失不当 0（`CARBON_SCOPE_FREEZE.md:7,15`） | 必须覆盖过程排放 | 冲突（目前未建） | manifest `O_PENDING_FIXED_ACCOUNTS` |
| F14 | FCEV 和船用 H2 不启用；EV 的 DSM/V2G 推迟；道路 EV 嵌入 Astar（`HYDROGEN_FUEL_BOUNDARY.md:7`；`transport/phase3b2/TRANSPORT_MINIMUM_DEFENSIBLE_BASELINE.md:9,15`） | 需求侧技术内生 | 冲突 | `config.asean.yaml:216-239`；`transport_accounting.csv`；`demand_transport.py` |
| F15 | 航运、航空为固定燃料义务，FT 只是供给选项（`TRANSPORT_MINIMUM_DEFENSIBLE_BASELINE.md:12-14`） | 燃料选择内生 | 冲突 | 同上 |
| F16 | 建筑供热嵌入、制冷嵌入电力、不建区域供热；Astar 为终端电力父账（`buildings_heat/phase3a7/BUILDINGS_MINIMUM_DEFENSIBLE_BASELINE.md:21-25`；`RESEARCH_ELECTRICITY_BOUNDARY_FREEZE.md:7-9`） | 需求侧技术内生 | 冲突（另外，上游 DAC 依赖热母线） | `buildings_accounting.csv`；`electricity_parent.csv`；`gate2/BUILDINGS_GATE2_ACCOUNTING.md` |
| F17 | 农业用电嵌入、燃料固定（`AGRICULTURE_FIRST_FULLSC_BOUNDARY.md:3`） | 需求侧内生 | 冲突（较轻） | `agriculture_accounting.csv` |
| F18 | 不建地质封存，不采用 200 Mt，不自动建 DAC（`baseline.yaml:104`；`gate3/PHASE4_CO2_PHYSICAL_ARCHITECTURE.md:15,17`） | 允许 CCS、BECCS、DAC，只用技术潜力 | 冲突，需要各国封存潜力 | `carrier_architecture.py:137-145`；`build_research_network.py:69` |
| F19 | 生物质只用于固定义务，不跨国（`gate3/PHASE4_BIOMASS_ARCHITECTURE.md:3-7`；`baseline.yaml:32,103`；`GATE4_RESUME_REQUEST.txt` 第 12 节） | 需要 BECCS 和内生用途；跨境仍可关闭（INFERENCE） | 冲突（用途方面） | `ASSEMBLY_V1_FINAL_COVERAGE_DECISIONS.md:37-39`；`BIOFUEL_COMMODITY_PARAMETER_REVIEW.csv` |
| F20 | 只批准 4 条耦合路径（`build_research_network.py:93-104`；`gate4/ACTIVE_SECTOR_COUPLING_FINAL.csv`） | 需新增合成氨、裂解、甲醇、DAC、BECCS、CCS、Sabatier、再气化等路径 | 冲突 | `ACTIVE_SECTOR_COUPLING_FINAL.csv`；`PHASE4_ACTIVE_SECTOR_COUPLING_PATHWAYS.csv` |
| F21 | 不新增 H2 出口（`HYDROGEN_FUEL_BOUNDARY.md:11`） | 只进不出 | **兼容** | — |
| F22 | 国内 H2 网络不建（`HYDROGEN_FUEL_BOUNDARY.md:9`） | 新口径没有说明国内网络是否内生 | 待定（需要决定） | 同 F2 |
| F23 | 保留 Baseline 与 DEC 两个情景（`CURRENT_DECISION_INDEX.json`） | 只比较互联 vs 不互联，两组都是净零 | 冲突 | `config.asean.yaml:34-35`；`gate6_baseline_3h.json` |
| F24 | 缺失数据不补 0、不编造（`EXTERNAL_COMMODITY_SUPPLY_BOUNDARY.md:14`；`ASSEMBLY_V1_FINAL_COVERAGE_DECISIONS.md:18`） | 缺失数据用可复现的自下而上推导补齐 | 冲突（处理策略相反） | `REMAINING_ACCOUNT_DECISIONS.csv`；`UNSD_MISSING_MEMO_REQUESTS.csv` |
| F25 | 需求采用 AEO8_BAS 加固定增长代理，国内运输和铁路按 2019 常数（`baseline.yaml:89-100`） | 内生选技术要求需求按服务口径，新口径未明说 | 可能冲突（需要决定） | `ASSEMBLY_V1_2050_METHOD_REGISTER.csv` |
| F26 | 2050 单年；Disconnected 用同一模型（`baseline.yaml:78`） | 2050 净零 | **兼容** | — |

另外，Phase4 阻断登记 P3 `phase3c/PHASE4_SYSTEM_BLOCKER_REGISTER.csv:2-10`（P4-01 至 P4-09）的验收条件都是按旧口径（隔离 + 电力范围）写的；其中 P4-05 和 P4-06 需要按新口径重写。

## 10. 计算规模预估（只估算，不构建）

**基准**（VERIFIED，`P0_SCALE_BASELINE.json`）：
- 当前 2920 模型每个时段有 6,703 个时变变量，合计 1,957 万列、4,830 万行、9,078 万非零。
- 其中外生固定块占 3,677 个（55%）：1,256 条 accounting Link、807 条 meter，以及 807 个固定资源 Store 的 e/p 变量 1,614 个。新口径下这一块会被技术链取代，所以先扣除。

**外推方法**（INFERENCE，`p0_scale_estimate.py`）：
- 按上游各部门函数的组件结构，假设每节点每时段新增的时变变量为低 57 / 中 111 / 高 165 个。各部门的假设写在脚本里。
- 行/列比、非零/列比、内存/非零比、时间系数都取自 D-1、D-5 和 Gate6 首次运行的实测回执。
- 互联情景另加 24 条跨境边 × 6 种分子载体的变量，影响可以忽略。

| 布局与档位 | 列 | 行 | 非零 | 构建 RSS | 求解 RSS | Barrier 时间（线性 ~ 1.5 次幂） |
|---|---|---|---|---|---|---|
| 100 节点，低 | 2,590 万 | 6,400 万 | 1.20 亿 | 33 GiB | 44–48 GiB | 2.9–4.1 h |
| 100 节点，中 | 4,170 万 | 1.03 亿 | 1.93 亿 | 54 GiB | **71–77 GiB** | 4.7–8.3 h |
| 100 节点，高 | 5,750 万 | 1.42 亿 | 2.67 亿 | 74 GiB | **98–106 GiB** | 6.5–13.4 h |
| 11 个国家枢纽（电力仍 100 节点），中 | 1,280 万 | 3,170 万 | 5,950 万 | 17 GiB | 22–24 GiB | 1.4 h |

122 实例的上限：cgroup 90 GiB，RSS 保护线 75 GiB，Gurobi SoftMemLimit 65 GB；D-5 的原生时限为 14,400 s。

**判断**（INFERENCE）：
- 全量 100 节点的中档已经顶到 75 GiB 保护线，高档超过 90 GiB 的 cgroup 上限。
- Crossover 的时间无法外推。D-5 中 Crossover 用了约 7,270 s，占总时间的 57%。按这个比例，100 节点中档的单次求解很可能超过 14,400 s。
- 而且需要两个情景，再加价格 ±20% 和燃料舱两组敏感性。

**可选方向**（PROPOSED，由用户决定）：
- 非电部门的载体只建在国家枢纽上（电力保持 100 节点）；
- 降低时间分辨率；
- 只跑 Barrier、不跑 Crossover，并重新制定验收规则；
- 更换内存更大的实例。

注意：原有的块分解（C08/C09）依赖固定生物质块；新口径下这个块会消失，所以这项加速手段不再适用（INFERENCE）。

## 附：本目录文件

| 文件 | 内容 |
|---|---|
| `P0_LOCAL_SECTOR_COUPLING_AUDIT.md` | 本报告 |
| `P0_SECTOR_MATRIX.csv` | 部门矩阵 |
| `P0_GAP_TABLE.csv` | 差距表 |
| `P0_SCALE_BASELINE.json`、`p0_scale_baseline.py` | 规模基准统计，只读 |
| `P0_SCALE_ESTIMATE.json`、`p0_scale_estimate.py` | 规模外推，只估算 |
| `P0_CLAUDE_CODE_INSTRUCTION.md` | 本任务指令 |
