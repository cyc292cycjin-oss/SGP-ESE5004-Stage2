# IMPLEMENTATION_PLAN（R10；M08 实施计划，本步骤不改生产代码；已按补充 01 修订，2026-10-20）

所有修改均为 PROPOSED；实施顺序按"上游 → 下游"，每步一个提交 + 单元测试；每步之后重建网络的静态校验；最后本机 56×3h 冒烟一次（需另行授权）。

## 1. 修改顺序、配置键、脚本、测试、注册表行

| 步 | 修正 | 配置键（`configs/research/baseline.yaml`） | 脚本 | 单元测试（`tests/research/`） | 注册表行（`REGISTRY_ROWS_PROPOSED.csv`） |
|---|---|---|---|---|---|
| M08-1 | **R6.1 平减指数**（消除 +4.8 %） | `cost_layer.layers.technology_data_v0_15_0_2050_eur2020.rebase_index: hicp_ea`（新键；缺省沿用 gdp_deflator 以便对比） | `scripts_project/s2_0_cost_layer_v015.py` `rebase()`：读 Eurostat `prc_hicp_aind`（新源文件 `research_inputs/prices/sources/EUROSTAT_HICP_EA.csv`）；`LAYER_MANIFEST.json` 记录指数与因子 | `test_s2_0_cost_layer.py`：HICP 因子 × technology-data 自身升通胀因子 ≈ 1（±0.5 %）；非货币行不变 | `cost_layer_deflator_hicp` |
| M08-2 | **R6.3 核电同源**；R6.2 AEO8 价格年敏感性 | `nuclear.smr.cost_technology: nuclear SMR` 不变；`cost_layer.smr_cost_source: td_nuclear_x_aeo8_ratio`（新值） | `scripts_project/s2_costs.py`：SMR 行 = technology-data nuclear × 比值（投资 1.0667、FOM 1.37、VOM 0.43）；地热保留 AEO8 × FX 并加 `aeo8_price_year_factor`（缺省 1.0，敏感性 0.86） | `test_s2_costs.py`：SMR 投资 = nuclear × 1.0667；比值无量纲 | `nuclear_cost_rule`、`aeo8_cost_price_year` |
| M08-3 | **R3 LNG**：GEM 2025-09 表、取消 2.5×、码头成本 8,020、再气化加价 | `s3.gas.lng_terminals`（新 CSV）；`s3.gas.lng_expansion: capex_only`（新模式：`p_nom_max = inf`，capex 作用）；`s3.gas.lng_expansion_capital_cost_eur_per_mw_a: 8020.43`；`s3.gas.lng_regasification_adder_eur_per_mwh: 1.26` | `scripts_project/d1_lng_terminals.py`（读新表）、`s3_layers.py`（扩建模式）、`s2_costs.py`（加价加到 LNG import 边际成本） | `test_s3_1.py`：capex_only 下 `p_nom_max` 为 inf 且 `capital_cost` = 8,020；加价进入 `marginal_cost`；existing_only / cap_factor_cost 仍可选 | `lng_terminal_capacity_source`、`lng_terminal_cap_rule`、`lng_terminal_expansion_capex_main`、`fuel_price_lng_regasification_adder` |
| M08-4 | **R5 CO₂ 封存统一** | `co2.storage_potentials: research_inputs/co2_v5/CO2_STORAGE_POTENTIAL_UNIFIED.csv`（新表，列：country, potential_gt, p90, p10, source, locator, status） | `scripts_project/d1_co2_storage.py`（生成表）、`s2_layers.py`（读表：`e_nom_max = potential / storage_years`） | `test_s2_co2.py`：VN 上限 106.1 Mt、PH 1.34 Mt、LA/MM/SG 0、KH 1.8 Mt | `co2_storage_potential_*` 6 行 + `co2_sequestration_cost_price_year` |
| M08-5 | **R1 需求锚定（补充 01 §1–2：只锚活动量，不锚载体结构）** | `demand.growth_method: ats_anchor`（新值）；`demand.anchor_table: research_inputs/demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv`（人均 × 人口，TL 规则）；`demand.base_load_anchor: ats_buildings_agri`（新键：基础电力负荷 = ATS 国家电力 × 建筑 + 农业及其他份额）；`demand.transport_anchor: ats_service`（新键：交通服务量 = ATS 交通终端能耗 ÷ 现行载体效率，EV 份额按现行做法）；`demand.country_allocation` 保留旧值作敏感性；`s2.industry.physical_output_rule: gdp_elasticity_capped`、`physical_output_elasticity: 0.5`（敏感性 0.3–0.8）、`physical_output_base_year: 2024`、`physical_output_percap_caps: {cement: 1.0, steel: 0.6}`（t/人/年；敏感性 0.6–1.2 / 0.4–0.8）；`s2.industry.physical_output_plan_caps: research_inputs/demand_v5/INDUSTRY_OUTPUT_PLAN_CAPS.csv`（仅作上限） | `scripts_project/d1_demand_2050.py`（国家总量 = ATS 人均 × 人口；部门权重 = 2019 部门结构 × ATS 区域部门增长代理，归一化；交通服务量锚）、`s3_0_industry.py`（产量规则 min(增长, 人均, 规划)；基年表 `INDUSTRY_OUTPUT_BASE_2024.csv` 含来源列与 DATA_PENDING 标记）、`s2_layers.py`（基础负荷 = 锚值；工业电力不再固定，由有用热链路内生） | `test_d1_demand.py`：11 国基础电力负荷 = 锚（±1e-6）且 ≥ 0；TL 规则；居民电力 10 国合计与 AEO8 ATS 33.2 Mtoe 的偏差登记（本步 +11 %）；`test_s3_0_industry.py`：VN 水泥 107.0（人均上限绑定，规划 150 不绑定）、钢 40.7（增长规则；Decision 261 的 70 只作上限）；每国 = min(增长, 人均, 规划)；规划值不得抬高产量 | `demand_anchor_family_main/control`、`demand_anchor_tl_rule`、`demand_base_load_rule`、`demand_transport_anchor_rule`、`demand_industry_electricity_not_anchored`、`industry_output_rule_2050`、`industry_output_base_year`、`industry_output_elasticity`、`industry_percap_saturation_cement/steel`、`industry_output_plan_sensitivity_VN`、`industry_cement_2050_VN`、`industry_steel_2050_VN` |
| M08-6 | **R1.4 / R4 工业有用热与生物质溢出** | `s2.industry.other_bucket: useful_heat_bands`（新值；旧 `pypsa_eur_2050` 保留作敏感性）；`s2.industry.biomass_overflow_mode: useful_heat`（替代 `biomass_overflow_to_methane` / `cap_share`）；`s2.industry.heat_bands: {low: "<150C", medium: "150-400C", high: ">400C"}` | `scripts_project/s3_0_industry.py`（能耗回退桶 → 三段有用热需求，用 JRC-IDEES 温度分布，C 级）、`s2_layers.py`（新增 `industry heat medium` / `industry heat high` 母线，锅炉 / 热泵 / H₂ 锅炉 / 生物质锅炉链路，效率 0.90 / 0.99 / COP 3.2（仅低温）/ 0.90；溢出量以有用热量进入对应温度带） | `test_s2_industry_heat.py`：溢出有用热 = 溢出生物质 × 0.90；三段之和 = 原能耗 × 效率；固定生物质需求 ≤ 池；`biomass_overflow_cap_share` 键不再需要（保持可读、不生效时警告） | `industry_route_mode_proposed`、`biomass_overflow_rule` |
| M08-7 | **R2 可再生布局（补充 01 §3：主算只改光伏密度）** | 主算：`renewable.solar.capacity_per_sqkm: 5.1`（土地类别 `grid_codes [20,30,40,50,60,90,100]` 与 natura 排除不变，与 PyPSA-Eur 同型）；`renewable.solar.p_nom_max_scale: 1.108696`（= 5.1/4.6，直接缩放现有光伏候选上限，不重算栅格）；海上风电对齐 PyPSA-Eur：`renewable.offwind-*`：`max_depth 60`、新 `offwind-float`（60–1,000 m）、`ship_threshold 400`、`excluder_resolution 200`、`turbine NREL_ReferenceTurbine_2020ATB_5.5MW`、`correction_factor 0.8855`（需重算海上可用面积：GEBCO 2025、EEZ v11 已在作者缓存，航运密度栅格待下载 `USER_DOWNLOAD_LIST.md` A1）；`renewable.offwind_alpha: research_inputs/renewable_v5/OFFWIND_CALIBRATION_ALPHA.csv`（F9，DATA_PENDING 时 1.0）。敏感性：`renewable.layout_variant: s4r_openforest`（`grid_codes` 加 121–126，用缓存的 Copernicus 全球文件重算光伏可用面积；触发规则见 §2.1） | 主算：`s4a_layers.py` 对光伏候选 `p_nom_max` × 1.108696；海上：`scripts_project/s4a_profiles.py` 扩展（GEBCO、EEZ、航运密度），输出 `profiles_s4r_offshore_c3_3h.nc`；敏感性：同脚本加开阔林类重算光伏 | `test_s4r_layout.py`：光伏 `p_nom_max` = 旧值 × 1.108696（±1e-6）；11 国同一参数；海上三类的水深 / 航道掩膜；开阔林变体只在敏感性配置生效 | `renewable_capacity_per_sqkm_solar`、`renewable_landuse_rule_solar`（主算不变）、`renewable_openforest_sensitivity_trigger`、`renewable_offshore_rule`、`offwind_alpha_calibration_rule` |
| M08-8 | **R7 不互联定义登记 + 敏感性** | `cross_border.stock_mode: remove_all`（主，现行为）| `keep_stock_no_new`（敏感性） | `scripts_project/scenario_network.py`：敏感性时保留 `border_class == cross_border` 且 `s_nom > 0` 的线路 / 链路为不可扩建 | `test_scenario_network.py`：主模式删除 62 线 / 292 链；敏感性保留 24 电力边 + 3 条气管道存量 | `disconnected_definition_main/sensitivity` |
| M08-9 | **R8 GATES_V6** | `solver.acceptance: gates_v6`；`solver.interior.dual_tol_basis: max_optimality_barconv` | 新 `scripts_project/v5/gates_v6.py`（`acceptance_v6`）；`s2_solve.py` 调用；`s4o_c1_precision.py` 的 `acceptance` 改引 G1 + G2；`run_365x24h.sh` 停止条件改为 `NOT_ACCEPTED`；配置子集哈希写入网络 meta（`research_config_subset_sha256`） | `test_gates_v6.py`：D2 预算随 BarConvTol；G2.2 对 `solver.profiles` 不敏感、对 `cross_border` 敏感；D7/D9/D10 容差；标签逻辑 | `gates_v6_contract` |
| M08-10 | R6.5 报告货币、R6.6 WACC 表登记、R6.4 无来源常数登记 | `finance.report_currency: USD2020`、`finance.report_fx_usd_per_eur2020: 1.1422` | 账本导出加美元列（`s4d_ledger.py` 导出层） | `test_s4d_ledger.py`：美元列 = 欧元 × 1.1422 | `report_currency_rule`、`wacc_country_real_table`、`co2_sequestration_cost_price_year`、`lng_terminal_expansion_capex_main` |

## 2. 网络重建与本机 56×3h 冒烟

- 重建：M08-1 → M08-10 全部提交后，用 `scripts_project/build_research_network.py` 重建一体化 / 不互联（STEPS）两个 2920×3h 网络与 365×24h 网络（NZE 不再构建，第 124 项）；静态校验（B5 单一开关、B8 需求守恒、B11 路线、B13 单向进口、B16 进口价相同）全过；`BUILD_INPUT_CHANGES_*.json` 记录与 126110ff 包的差异。
- 冒烟（需另行授权，1 次本机 56×3h × 2 情景，档案 A，30 min 止损）：通过标准 = GATES_V6 标签 `ACCEPTED_LAYER2`；B6 符号为正；11 国基础电力负荷 = ATS 建筑 + 农业及其他锚（±1e-6）且非负，工业电力为内生变量；VN 水泥 107.0 / 钢 40.7 Mt；各国光伏上限 = 旧值 × 5.1/4.6（1.1087，±0.1 %；主算只改密度）；LNG 码头无上限绑定；VN 封存上限 106 Mt 生效；生物质溢出母线无固定甲烷需求。

### 2.1 开阔林敏感性的触发规则（补充 01 §3）

- 主算（密度 5.1、土地类别不变）完成 365×24h 两情景后，读取各国光伏候选上限的绑定状态（`p_nom_opt ≥ 0.999 × p_nom_max`）与上限约束的影子价格（第 118 项运行内对偶导出，不需重解）。
- **触发条件：** 某国光伏上限在任一情景绑定，且影子价格 × 绑定容量（即该上限对该国"不互联 − 一体化"差额的一阶影响）≥ 1 bn EUR2020/a。
- **动作：** 满足条件时把开阔林变体 `s4r_openforest` 升级为第三批的正式敏感性运行（两情景各一次），报告中并列主算与开阔林上界结果；不满足时只在附录记录绑定状态与影子价格。
- 登记为注册表行 `renewable_openforest_sensitivity_trigger`。

## 3. 分支整合顺序

1. `codex/s4q-tol-calibration-20261020`（#41，`FIXED_RUNS`、两个候选档案）：先合入 S4O 分支头（#40）——只改脚本与档案白名单，不改网络。
2. `codex/s4p-country-audit-20261020`（#42）与本分支 `codex/s4r-unification-plan-20261020`（叠在 #42）：只含报告与脚本（`work/` 镜像），无生产代码改动，可在 M08 之前随时合入。
3. M08 新分支 `codex/m08-unification-20261021` 自合并后的头开出；每步一个提交；draft PR 叠在 #42 / #41 之后。
4. 不合并 main；全部 draft。

## 4. 第三批（M10）范围建议与资源估计

| 运行 | 网络 | 档案 | 次数 | 预计（INFERENCE，按 S4N / S4O / S4Q 实测） |
|---|---|---|---|---|
| 修正后 365×24h 一体化、不互联（生产） | M08 新网络 | A（formal_barrier 1e-8） | 2 | 每次 1.5–3.5 h（试点 3.3 h 含重启；8481C r 0.836）；峰值 13–15 GiB |
| 1e-6 第二级（第 127 项） | 同上 | `formal_barrier_1e6`（T8）、`formal_barrier_1e6_t16` | 4 | 每次 1.3–2.6 h（S4Q WU 比 0.67–0.94）；T16 峰值 17–23 GiB |
| 2920×3h 探针 | 一体化 2920×3h 新网络，前 56 时段 | A | 1 | 约 10 min |
| 合计 | | | 7 | 约 10–20 h 串行；25 核 / 92 GiB 实例足够；上传整包约 270 MB（36 KB/s 时 2 h，4 MB/s 时 1 min）；费用 = 单价 × 实例时间（单价 DATA_PENDING） |

参照：C1 (b)(c) 的分国阈值用本批自己的"不互联 − 一体化"差额（`s4o_c1_precision.py reference + regrade`），不再用 S4N 试点（旧网络）。

## 5. 主算与敏感性划分（第 124 项总规则：主算只含统一口径、有出处的修正；其余作敏感性）

| 进主算 | 作敏感性 |
|---|---|
| R1 ATS 活动量锚定（建筑 + 农业及其他电力、交通服务量、物理产量 = min(增长 ε 0.5, 人均饱和, 规划上限)，基年 2024）+ 有用热路线（工业电力内生）；R2 密度 5.1（仅）+ PyPSA-Eur 海上规则；R3 GEM 2025-09 + 取消上限 + 8,020 码头 + 再气化加价；R4 有用热溢出；R5 ERIA P50；R6.1 HICP、R6.3 核电同源、R6.4 登记；R7 现行定义登记；R8 GATES_V6（k = 10，`GATES_V6_NOTES.md`） | R1 BAS 锚（上界）、`country_allocation` 其余三种、ε 0.3–0.8、饱和水平 0.6–1.2 / 0.4–0.8 t/人、VN 规划值（钢 65–70 Mt）作对照；R2 开阔林 121–126 上界（触发规则 §2.1）、ESMAP L1 × 5.1 上限对照、F9 海上 alpha（数据到位前 1.0）；R3 选项 (b) 项目上限、(c) 2.5×；R4 生物质跨境贸易；R5 ERIA P90 / P10、KH 45 Gt、TL Bayu-Undan 10 Mtpa；R6.2 AEO8 价格年 × 0.86、R6.6 分国 WACC（面谈）；R7 保留存量不新建；燃料换算路径 +7 % |
