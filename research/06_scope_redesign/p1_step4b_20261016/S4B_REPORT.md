# S4B 报告：补做第 70–73 项，落实第 74–81 项，重跑冒烟，更新云端部署包

**背景（如实记录）：** S4A 执行时，D 盘上的 `S4A_CLAUDE_CODE_INSTRUCTION.md` 是未并入第 70–73 项的旧版（13:31），审阅端写好的 S4A-0（第 70–73 项）没有同步到 D 盘；这是审阅端的失误，S4A 本身按所读到的指令执行无误。因此本步先补做第 70–73 项（S4B-0）。

分支 `codex/s4b-fixes-calibration-20261016`（自 S4A 最终提交 a58ca3fa 开出，已核实 = PR #25 最新提交）；draft PR #26 叠在 #25 上。指令 v1 的 SHA256 `52f1b758…dbc51` 开始前核对一致。求解器 Gurobi 12.0.3、`formal_barrier` + 缩放（第 69 项），止损同 S3B。结论分级 VERIFIED / EXACT / INFERENCE / PROPOSED。冒烟结果均为 SMOKE_TEST_ONLY（第 47 项：云端试算前无科学含义）。

## 摘要（≤10 行）

（全部完成后填写）

---

## 0. S4B-0：补做第 70–73 项（提交 3afb044d；冒烟见 0.6）

### 0.1 部门开关与 PyPSA-Eur 对齐（第 70 项；VERIFIED / EXACT）

对照表 `research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv`（79 行，覆盖 PyPSA-Eur v2025.07.0 `config.default.yaml` sector 段第 478–820 行的全部键，外加一处代码口径差异）：一致 56、已确认偏离 11、不适用 9、需用户决定 3。本模型原值引用 PyPSA-Earth 配置（`config.default.yaml`、`configs/config.asean.yaml`）或设定它的研究决定。新增配置块 `research.sector`（`scripts_project/s4b_layers.py`）。

**本步改动（原值 → 新值）：**

| 开关（PyPSA-Eur 行号） | PyPSA-Eur | 本模型原值与来源 | 新值 | 组件 |
|---|---|---|---|---|
| `methanation`（676）+ `min_part_load_methanation`（737） | true / 0.3 | 未建（PyPSA-Earth `config.default.yaml:1000` 为 true，但 S1 研究层配方 `build_research_assets.build_fragment` 未建，无决定） | true / 0.3 | 每节点 Sabatier 97 条：节点 H₂ + 节点捕集 CO₂（`co2 stored`）→ 节点气母线；效率 0.8、CO₂ 0.1584 t/MWh_H₂、投资 54,290 EUR/MW_H₂/a（technology-data v0.15.0 `methanation`，按 PyPSA-Eur 2094–2111 行乘效率） |
| `electrobiofuels`（779） | true | 未建（S2 遗漏，无决定） | true | 每节点 97 条：国家固体生物质池 + 节点 H₂ → 油；1.3283 MWh 油 / MWh 生物质、H₂ 1.0857 MWh/MWh；投资 192,156 EUR/MW_生物质/a（BtL × 效率 + BtL C stored × FT × 效率，PyPSA-Eur 4263–4304 行） |
| `min_part_load_fischer_tropsch`（735） | 0.5 | 0（S1 配方 `p_min_pu 0`；PyPSA-Earth `config.default.yaml:1006` 的 0.9 未被采用） | 0.5 | Fischer-Tropsch 100 条 |
| `co2_vent`（679） | false | true（S2 实现时自定，无已确认决定；历次冒烟放空量均为 0） | false（true 保留为敏感性） | 删除 97 条 `co2 vent` |

**指令点名的其余开关（已与 PyPSA-Eur 一致，本步只登记）：** `hydrogen_turbine` true（`research.hydrogen.h2_turbine`，PyPSA-Earth 746 行）、`hydrogen_fuel_cell` true、`SMR` / `SMR_cc` true（S1 配方）、`biomass_to_liquid` true（S2 生物质层）、`methanol.methanol_to_power.ocgt` true 与 `biomass_to_methanol` true（S3-3）。`SMR`、`SMR_cc`、`hydrogen_fuel_cell`、`biomass_to_liquid` 新增开关（默认 true，false 时删除相应组件，仅作敏感性）。`coal_cc: false` 与 PyPSA-Eur 一致。

**合成甲烷在第 64 项口径下的记账：** 天然气沿用"生产国记信用"——Sabatier 没有合成端口，CO₂ 取自节点捕集缓冲：DAC 来源的碳在捕集国记 −1 t，生物质来源的碳在捕集国记 −EF × 捕集率；合成甲烷与化石气同样在燃烧国按化石 EF 记排放。同国生产同国燃烧时净为 0（DAC/生物源）或只记一次化石碳（化石源捕集）；经管道出口时，信用留在生产国、排放记在燃烧国——这正是 S3 指令第 135 行写明的"沼气提纯和甲烷化在生产国记信用"的不对称。液体燃料（FT、甲醇化）维持 origin_neutral（合成时记碳），电制生物燃料按 BtL 处理（生物源碳：不记信用、不记排放）。

**已确认的偏离（11 行，逐项理由见表）：** 不建建筑供热与区域供热（S1 决定：不调用 add_heat，热服务内嵌于电力）、CHP（无城市集中供热母线）、BEV 需求侧响应与 V2G（S2：无东盟车队数据，DATA_PENDING）、地下储氢（S1：无东盟盐穴数据）、国家级封存上限与 50 年（第 20、28–30 项）、生物质国家池（第 36 项）、东盟外进口（第 17、18、64 项）、煤按节点（第 18 项，等价）、电力底座的直流与配网损耗（S1 冻结电力底座）。

**需要用户决定（3 行，未改动）：** (1) `electricity_grid_connection`（746 行，true）：technology-data v0.15.0（第 50 项成本层）删去了 `electricity grid connection` 行，PyPSA-Earth 默认也是 false，要采用需从 v0.13.2 层取成本行；(2) H₂/气管道压缩用电（756–761 行，0.018 / 0.01 MWh_el 每 MWh 每千公里）：PyPSA-Eur 需把双向管道拆成两条单向链路并在求解中约束容量相等（`lossy_bidirectional_links`，5727 行），影响约为输送量的 0.2–2.3%；(3) BtL 投资口径：PyPSA-Eur 乘效率（113,726 EUR/MW_生物质/a），本模型按 technology-data 单位 EUR/kW_th 直接取（252,723），在对齐电制生物燃料时发现。

### 0.2 验收容差（第 71 项，选项 1；`scripts_project/s4b_acceptance.py`）

**设计修正的说明（如实）：** 这是看到 S3B 结果后做的设计修正。理由：(i) S3B R4.4 的原始相对项 1e-7、对偶预算 1e-6 与 BarConvTol 挂钩，而 Gurobi 的 barrier 终止判据是缩放模型上的 FeasibilityTol / OptimalityTol（均为 1e-6，profile 未设，取默认），两者定义不一致；(ii) 右端为 0 的行（各国净零行：大气 Store 期末水平 ≤ 0）只有一个变量（期末水平 ~1e-3 t），因而没有相对项，而这个水平是全年 1e8–1e9 t CO₂ 流量之和。

**新阈值（求解前写入 `research.solver.interior`，k = 10，即选项 1 的"10 × 1e-6"）：**
- A1/A2 原始：行 |违反| ≤ 1e-3 + k × FeasibilityTol × max(|界|, Σ|a·x|, A_i)；列同理。A_i：各国净零行 = 该国 CO₂ 年毛流量（国家大气所有端口 |流量| × 权重之和）；生物质池的各行（能量平衡、期末水平上下界 `Store-fix-e-*`）= 池容量。
- A1/A2 对偶：平稳性残差按 V4 尺度 max(1, |c| + |a|ᵀ|π| + |rc|) 归一后 ≤ k × OptimalityTol；对偶符号：行按 V4 max(1, |π|)，列按与平稳性相同的列对偶活动量尺度（见下"补记"）。
- 间隙与互补性仍 ≤ 10 × BarConvTol = 1e-7。
- A3（含 A5）：V4 物理核对全部改为 1e-3 + k × FeasibilityTol × |参照|；`COUNTRY_CO2_CAP` 参照 = 毛流量，生物质池的能量与状态方程参照 = max(|值|, 池容量)。
- B1：期末水平 ≤ 上限 + 1e-3 + k × FeasibilityTol × 毛流量。B3：用量 ≤ 容量 × (1 + k × FeasibilityTol) + 1e-3，最低水平 ≥ −(1e-3 + k × FeasibilityTol × 容量)。
- 原 S3B 门槛（V4 代数与 `validation_dynamics.py` 未改）照常计算，`V5_GATES.json` 同时给出两套判定（`all_passed_barconvtol` / `all_passed_solver_tolerances`），主判定由 `acceptance_basis: solver_tolerances` 选择。

**补记（如实）：** 首轮重评中我只给生物质池的能量平衡行加了池容量参照，漏掉了同一批池的期末水平下界行（`Store-fix-e-lower`，S4A 的 18 行超限全在这里）；按已写明的规则（A3 的 `STORE_ENERGY_LOWER` 用池容量）补上。对偶符号的列失败全部是自由变量 `Link-p`（双向链路流量，没有界，其归约成本必须为 0），这里的"符号误差"就是归约成本本身，即对偶残差；V4 的 max(1, |rc|) 归一在 |rc| < 1 时是绝对值（EUR/MWh）。我改为与平稳性相同的列对偶活动量尺度——**这一点是在看到 S3B/S4A 数值后决定的**，V4 口径同时报告，列入 §8 请用户确认。

**新旧阈值下的结果（VERIFIED；S3B、S4A 为只读重评，`scripts_project/s4b_reevaluate_acceptance.py` 重建 linopy 模型只为取得行列名，重建的 clabels/vlabels 与导出数组逐项相同）：**

| 运行 | A1/A2 旧 → 新 | A3 旧 → 新 | B1 旧 → 新 | B3 旧 → 新 | 新口径下 A1/A2 的未通过项 |
|---|---|---|---|---|---|
| S3B 一体化主算 | ✗ → **✓** | ✗ → ✓ | ✗ → ✓ | ✓ → ✓ | — （行最大 0.19 × 预算；平稳性 1.19e-6；列对偶 3.98e-6） |
| S3B 一体化 producer_credit | ✗ → ✗ | ✗ → ✓ | ✗ → ✓ | ✗ → ✓ | 平稳性 4 列（`Line-s`，最大 5.69e-4） |
| S4A 一体化主算 | ✗ → ✗ | ✗ → ✓ | ✗ → ✓ | ✗ → ✓ | 平稳性 4 列（`Line-s`，最大 2.44e-4） |
| **S4B-0 一体化主算** | ✗ → ✗ | ✗ → ✓ | ✗ → ✓ | ✗ → ✓ | 平稳性 3 列（`Line-s`，最大 5.67e-4） |
| **S4B-0 不互联诊断** | ✗ → **✓** | ✓ → ✓ | （诊断不评） | ✓ → ✓ | — |

旧口径下 S4B-0 一体化的未通过项：原始 20 行（CO₂ 净零行 MM 0.0033、MY 0.0021、PH 0.0083、TH 0.0044 t 与生物质池期末水平 ≤ 0.002 MWh）、平稳性 5 列、对偶符号 10,640 项（V4 归一最大 4.2e-5）。新口径下 B1 最大比值 1.5e-5（相对预算），A3 最大比值 0.061（`Link_DISPATCH_UPPER`）。若取 k = 1（容差本身）：S4B-0 一体化原始行 0 项超限，平稳性 5 列。

**解读（INFERENCE）：** 新口径下唯一剩下的问题是少数线路潮流变量 `Line-s` 的平稳性残差（归一后 2–6 × 1e-4）。它们出现在基尔霍夫电压约束（系数为电抗，量级小）所在的列，属于 Gurobi 缩放模型上满足 OptimalityTol、换回原单位后被放大的对偶残差；基尔霍夫行归一化（第 69 项 (c)）未实施。是否对 `Line-s` 列另设尺度或实施 (c)，列入 §8。

### 0.3 LNG 接收站按成本开放扩建（第 72 项；VERIFIED）

`research.s3.gas.lng_expansion: cap_factor_cost`（主算）：上限沿用第 17 项（现有 × 2.5；只有拟建容量的站点到拟建容量），扩建成本 7,018 EUR/MW/a（PyPSA-Eur 进口分支 5a87cedd `prepare_sector_network.py` 第 4561 行 `terminal_capital_cost["shipping-lch4"]`，与液氢接收站同源），C 级，敏感性开关 `lng_expansion_cost_sensitivity` = ±0.5（3,509–10,527）。现有容量不计新投资（PyPSA 目标常数扣除）。参考来源已登记：Ulvestad & Overland 折算 8,020 EUR/MW/a、ERIA 2016 储罐口径（`lng_regas_capex_ref_*`）。`existing_only` 改为敏感性（登记行 `lng_terminal_expansion_mode` 状态改为 SENSITIVITY，新增 `lng_terminal_expansion_mode_s4b`、`lng_terminal_expansion_capex_main`）。LNG 进口发电机 9 → 16 个（7 个只有拟建容量的站点恢复，KH 重新有 LNG），上限合计 103.1 → 281.8 GW。B14 记录每台的投资。

### 0.4 诊断增加分国气松弛（第 73 项）

`gap_diagnostic` 在每个节点气母线上加一个罚价 10,000 EUR/MWh 的气源（与其他松弛相同；气平衡是节点级的，国内节点由国内候选管道相连），缺口表按国汇总（`gas_gap_mwh`、`gas_fixed_demand_mwh`）。主算不变；诊断产物继续带 `GAP_DIAGNOSTIC` 标签，不进入互联价值计算。

### 0.5 S3B 第 8 节其余事项

- 新加坡经管道向马来西亚转口：作为优化结果接受，不限制管道方向；再气化成本仍为 DATA_PENDING（解读时注明）。
- 越南生物质溢出改用甲烷：维持；启用甲烷化后溢出部分可由合成甲烷供给（不互联诊断中 VN Sabatier 597.6 TWh，见 0.6）。
- "其他"工业子部门：新增开关值 `asean_own_2019`（东盟各国 UNSD 2019 自身的"其他/建筑/采矿"载体构成 × 工业倍数，不做转换；表 `INDUSTRY_2050_SUMMARY_*_OTHER_ASEAN_OWN_2019.csv`），只实现，不运行；主表与 `idees_today` 表重算后逐字节不变。
- R1 衔接倍数：按 S3B 的取值接受。以上登记为 `s3b_section8_accepted_items` 与 `industry_other_bucket_asean_own_2019`。

### 0.6 重算与冒烟（VERIFIED；运行器 `run_s4b0_smoke.sh`，提交 3afb044d 构建）

**不互联情景的年度结构缺口（`scripts_project/s4b_structural_gap.py`，`evidence/s4b_0/analysis/`）：**

| 国家 | CO₂ 缺口 Mt/a（S3B 口径，所有化石计量都算不可避免） | CO₂ 缺口 Mt/a（计入替代路线：油 → 非化石油，气 → 合成/沼气甲烷） | 气缺口 TWh/a：S4A（无甲烷化、LNG 不扩建） | 气缺口：S4B-0 LNG 扩建后、甲烷化前 | 气缺口：甲烷化后 |
|---|---|---|---|---|---|
| KH | 26.24 | 13.42 | 20.4 | 5.7 | 0 |
| LA | 9.48 | 7.10 | 9.9 | 9.9 | 0 |
| MM | 14.82 | 5.36 | 0 | 0 | 0 |
| SG | 55.84 | 22.66 | 0 | 0 | 0 |
| VN | 146.16 | 5.44 | 446.4 | 221.1 | 0 |
| 其余 6 国 | 0 | 0 | 0 | 0 | 0 |

替代路线口径下仍不可避免的部分是过程排放、塑料焚烧与煤/褐煤终端用量；KH、LA、MM、SG 没有可用封存或封存上限不足、又无跨境管道，所以不互联主算仍然结构上不可行（第 49、53 项）。甲烷化所需电力（电解 + DAC）在各国均低于本国可变可再生潜力，故气缺口在"甲烷化后"为 0。

**冒烟（56×3h，Gurobi `formal_barrier` + 缩放，30 分钟看门狗）：**

| 运行 | 构建 | 状态 | barrier | 墙钟 | 峰值 RSS | LP 列 / 行 / 非零元 |
|---|---|---|---|---|---|---|
| 一体化主算 | 静态 PASS（43 s，0.59 GiB） | **OPTIMAL**，目标 6.6598e11 EUR/a（S4A 7.1200e11，−6.5%） | 140 次 / 140.8 s | 195 s | 3.38 GiB | 570,550 / 1,287,554 / 2.89 M |
| 不互联主算 | 静态 PASS | **NUMERIC**（"Numerical trouble encountered"，180 次 / 155.6 s，原始目标发散到 ~5e19）——预期（结构缺口），不触发止损 | 180 次 | 180 s | 3.15 GiB | 565,135 / 1,276,035 / 2.85 M |
| 不互联诊断（含电、CO₂、生物质、气松弛） | 静态 PASS | **OPTIMAL**，目标 1.2608e12（含松弛罚金） | 111 次 / 107.2 s | 165 s | 3.19 GiB | 576,831 / 1,299,200 / 2.90 M |

矩阵系数范围恢复到 [2e-4, 1e3]（S4A 冒烟为 [3e-9, 1e3]，`clip_p_max_pu` 修正生效）；barrier 迭代 92 → 140 次（INFERENCE：LNG 扩建与新增组件改变了最优面，迭代数不是 clip 修正的直接结果）。

**不互联诊断的分国缺口（GAP_DIAGNOSTIC，不进入互联价值）：** 电力 0、生物质 0、**气 0**（全部由合成甲烷与扩建后的 LNG 补足：Sabatier KH 20.4、LA 9.9、MM 3.9、SG 31.6、VN 597.6 TWh）；**CO₂：KH 13.42、LA 7.10、MM 4.64、SG 22.66 Mt/a**（合计 47.8 Mt；KH、LA、SG 与替代路线口径的结构表一致，MM 略低；VN 在优化中为 0，结构表的 5.44 Mt 是不计时段与路线细节的年度上界）。S3B 的诊断 NUMERIC / "Infeasible model" 问题已消除。

**甲烷化与 LNG 扩建前后（一体化主算，S4A → S4B-0；GW / TWh，56 代表时段年化）：** LNG 进口 903 → 2,388 TWh（16 个接收站全部扩到上限，扩建 178.7 GW）；气电（CCGT/OCGT/CCGT CC）134 → 269 GW、381 → 1,153 TWh；SMR 核电 241.5 → 132.8 GW、2,022 → 1,096 TWh；煤电 94.5 → 50.9 TWh；陆风 486 → 374 GW；海上风 509 → 527 GW；地面光伏 236 → 306 GW；SMR CC 制氢 608 → 720 TWh；一体化中 Sabatier、电制生物燃料、FT 产量均为 0（化石气更便宜）。解读（INFERENCE）：按 7,018 EUR/MW/a 扩建时，满负荷每 MWh 气的接收站成本约 0.8 EUR，而 LNG 价格 13.67 EUR/MWh、再气化加价仍为 0（DATA_PENDING），扩建上限本身成为约束（S3B §4.1 已预计）；更便宜的气挤出了 SMR 核电与部分陆风。这一结果对再气化加价与扩建上限高度敏感。

## 1. S4B-1 存量口径（第 77 项；`scripts_project/s4b_1_fleet_data.py`、`s4a_fleet.py`）

1. **在建计入、宣布与预建不计：** `research.fleet.include_construction: true`（保留），`false` 为敏感性。注册表新增 `fleet_survival_rule_committed_planned_item77`：S1 的 `NOT_INHERITED_COMMITTED_OR_PLANNED`（`S1_SELECTED_ASSET_SURVIVAL_2050.json`，45 条、3,881 MW）改为"只对在建放宽"。逐条对照 GIPT 2026-09（`FLEET_S1_NOT_INHERITED_ITEM77.csv`，49 个 GEM 子单元）：计入 25 个、1,420 MW（S4A-2 已补 8 个 560 MW；本步无投运年在建 17 个 860 MW）；不计 24 个——寿命规则下 2050 年前退役 7 个 261 MW、搁置 4 个 1,172 MW（含 1,050 MW 一台）、宣布 6 个 41 MW、预建 1 个 30 MW、在运无投运年 3 个 37 MW、不在 GIPT 3 个（VERIFIED）。
2. **无投运年的单元：** 在建 74 台、9,314 MW 计入——GIPT 2026-09 仍为"在建"，说明 2026 年前未投运，投运年 ≥ 2026（指令"≥ 2025"的严格化），任何寿命规则（≥ 25 a）下 2050 年在役；节点映射（同国最近 AC 节点，距离中位数 93 km、最大 313 km）与参数来源同 S4A-2；其中垃圾发电 70 MW 跳过（见第 4 条），实际补入 9,244 MW，组件 `existing_survivor::<节点>::<类>::S4B1`。在运 170 台、5,313 MW 不计（UNRESOLVED，生物质 1,922、风 1,332、油气 1,075、光伏 617、水电 267、地热 101 MW）。逐台列表 `FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv`、`FLEET_UNRESOLVED_OPERATING_NO_START_YEAR.csv`。
3. **移出 11 台：** `research.fleet.remove_not_operating_gipt2026: true`，2,854.4 MW（封存 TH CCGT 828 + 1,220；退役 TH 煤 150；取消 VN 煤 75；不在 GIPT 的 ID 煤 135 + 80 + 80、PH 油 242 + 23 + 10.9 + 10.5）。身份从 `existing_unit_components` 移到 `existing_unit_removed_s4b1` 并注明原因（数据更正），注册表逐台登记 `fleet_removed_*`；所在组件按单元容量减少 `p_nom`，固定运维按比例扣除（合计 −8.55e7 EUR/a），两个只含被移出单元的组件删除。
4. **垃圾发电继续跳过**（S4A 100 MW + 本步 70 MW），登记 `fleet_waste_to_energy_skipped_s4b`（DATA_PENDING），记入局限性。
5. **补入/移出前后的 2050 存量（MW_el；`FLEET_STOCK_2050_S4B1_BY_COUNTRY_CLASS.csv`；VERIFIED）：** 合计 261,101 → 267,491（+9,244 −2,854）。

| 国家 | S4A 后 | 补入（在建无投运年） | 移出 | S4B-1 后 | 主要变化 |
|---|---|---|---|---|---|
| ID | 80,020 | 3,215 | 295 | 82,940 | 煤 +2,200/−295、地热 +330、陆风 +597、径流 +88 |
| MY | 29,544 | 2,500 | 0 | 32,044 | CCGT +1,500、OCGT +1,000 |
| VN | 63,169 | 1,115 | 75 | 64,209 | 陆风 +752、海上风 +171、径流 +102、水库 +51、光伏 +39；煤 −75 |
| LA | 15,909 | 1,036 | 0 | 16,945 | 水库 +520、陆风 +350、径流 +166 |
| PH | 21,942 | 731 | 286 | 22,386 | 光伏 +460、抽蓄 +120、径流 +60、水库 +44、地热 +34、陆风 +13；油 −286 |
| MM | 7,804 | 647 | 0 | 8,451 | 水库 +481、OCGT +126、光伏 +40 |
| TH | 30,419 | 0 | 2,198 | 28,221 | CCGT −2,048、煤 −150 |
| BN / KH / SG / TL | 352 / 4,948 / 6,739 / 255 | 0 | 0 | 不变 | |

构建（`results_project/s4b/build_s4b1/`，两情景，不含日网络）：静态 PASS（各 42 s、0.57 GiB）；身份 1,104 个（另 11 个在移出登记中）；存量固定运维常数 1.0626e10 → 1.0806e10 EUR/a。测试 `test_s4b_1.py` 3 项通过；注册表新增片段 `s4b_1`（16 行），DATA_PENDING 39（+1 垃圾发电）。

## 2. S4B-2 地热、新建水电、抽蓄候选上限；核电敏感性开关（第 78、79 项；`s4b_2_candidates_data.py`、`s4b_candidates.py`）

**主算上限（`hydro_geothermal_cap: national_potential`，`pipeline_cap_statuses: announced_preconstruction`；VERIFIED）。** 国家上限 = S4A §3.2 的 A/B 级潜力 − S4B-1 之后的 2050 存量（水电 = 水库 + 径流，不含抽蓄）；无官方潜力的用 GEM GIPT 2026-09 项目库。

| 国家 | 新建水电（水库 + 径流）MW | 来源与等级 | 地热 MW | 来源与等级 | 抽蓄 MW（GEM，B） |
|---|---|---|---|---|---|
| VN | 22,038 = 40,000 − 17,962 | PDP VIII 第 500 号决定（A） | 45 | GEM 项目（B） | 1,500 |
| ID | 86,535 = 94,470 − 7,935 | EBTKE（B） | 22,421.5 = 23,590 − 1,168.5 | Badan Geologi 2024（B） | 2,400 |
| PH | 20,571 = 23,375 − 2,804 | DOE（B） | 3,124 = GEM 1,297 + 2050 年前退役存量原址重建 1,827 | GEM（B） | 7,958 |
| MM | 41,942 = 46,000 − 4,058 | ADB 2016（B） | 0 | — | 0 |
| MY | 水库 5,986 = 13,600 − 7,614；径流 2,371 = 2,500 − 129 | MyRER（B） | 229 | MyRER（B） | 0 |
| LA | 11,583 = 26,000 − 14,417（能矿部 18 GW 敏感性：3,583） | AEO8（C） | 0 | — | 100 |
| KH | 4,170 | GEM 项目库（B） | 0 | — | 0 |
| TH | 0（GEM 水电项目全是抽蓄） | GEM（B） | 0 | — | 2,480 |
| TL / BN / SG | 0 | GEM 无项目 / SOURCE_ZERO | 0 | — | 0 |
| **合计** | **195,196**（水库 161,296 + 径流 33,900） | | **25,820** | | **14,438** |

没有差值 < 0 的情况。登记 `candidate_cap_*`（34 行；片段 `s4b_2` 共 41 行），C 级行带敏感性区间（LA：能矿部口径 3,583 至 11,583）。

**项目库口径（需用户确认）：** 指令写"宣布 + 预建 + 在建"。但第 77 项已把在建单元计入 2050 存量（S4B-1），若候选上限再含在建，同一批项目会被算两次。主算因此只取宣布 + 预建；按字面含在建的口径保留为开关值 `announced_preconstruction_construction`（主算口径下抽蓄合计 14,438 → 16,798、地热 25,820 → 25,859、水电 186,839 → 187,069 MW），列入 §8。

**节点分配（第 78 项 c；`CANDIDATE_CAPS_S4B2_BY_NODE.csv`）：** 国家上限按 GEM 项目（宣布 + 预建 + 在建，即全部已识别站点）的容量份额分到同国最近 AC 节点（ID 水电 10 个节点、地热 13 个，MM 水电 9 个……）；没有项目的国家用同类存量份额；MY 地热（既无项目也无存量）按 MyRER 区域（半岛 162、沙巴 67 MW）平均分给区域内节点（C 级）。新建水电在水库与径流之间按该节点项目的技术类型划分（"常规 + 径流"各半，类型不明按同国存量比例）；没有项目的按同国存量比例。PH 地热原址重建 1,827 MW 落在 Luzon5 0（394）、Mindanao6 0（234）、Mindanao6 1（106）、Visayas7 0（1,093）。

**表示方式（C 级代理）与改正的 S1 候选缺陷（VERIFIED）：**
- 新建水库水电：单位容量入流与库容时长取同节点（否则同国、否则东盟）存量水库的容量加权值（max_hours 4.96–7.15 h）；入流属性按上限给出，新增钩子 `research_new_hydro_inflow` 加约束 spill_t ≥ inflow_t − r_t · p_nom（r_t = 单位容量入流），使可用入流与建成容量成正比——否则只建一部分甚至不建也能白得入流能量。S1 候选原为 `p_min_pu −1`、`efficiency_store 1`（等于可抽水），改为 0 / 0。
- 新建抽蓄：6 h、往返效率 0.75（每段 √0.75 = 0.866）。S1 候选把 technology-data 的往返效率 0.75 用在充、放两段上（实际往返 0.5625）。
- 新建径流：可用率取同节点（否则同国、否则东盟）存量径流的容量加权序列（均值 0.288）；S1 候选原为 1.0。
- 新建地热：可用率 0.7194（第 52 项 AEO8 C.4/C.5 容量因子，与存量相同）；S1 候选原为 1.0。
- 以上缺陷在上限为 0 时不起作用，本步放开上限时一并改正；均在 `research_candidates_s4b2.corrections` 中记录。

**敏感性开关：** `hydro_geothermal_cap: national_potential | national_potential_la_mem_18gw | gem_pipeline_only | zero`；`nuclear_cap: none`（主算，第 38 项）`| national_plans`（PH 4,800、VN 14,400、ID 10,000、TH 600 MW，其余 0；按国家对 `nuclear` 与 `nuclear SMR` 合计约束，钩子 `research_nuclear_national_cap`；只实现，不运行）。五个构建（主算两情景、zero、national_plans、gem_pipeline_only）全部静态 PASS（各约 41 s、0.58 GiB）；56×3h 建模检查：36 组入流约束、national_plans 下 4 条国家核电约束均正确安装（未求解）。

**成本核对（第 46、50、52 项；VERIFIED）：** 网络中新建核电 789,669、SMR 728,177、地热 306,946、径流 326,038、水库水电与抽蓄 193,291 EUR/MW/a，与 S4A-3 的一致性表逐项相同，本步未改。**附带发现（需用户决定，未改动）：** 风光候选（来自冻结的电力底座）并未使用第 50 项成本层：陆上风 114,912（成本层 99,000）、地面光伏 71,546（成本层 `solar-utility` 30,743）、屋顶光伏 57,483（36,610）EUR/MW/a；海上风 268,776–351,974（成本层 163,226 不含并网，网络值含按距离的并网成本）。S4A-3 的"9/9 一致"比较的是成本表，不是网络组件，这一点在 S4A 报告中说得不准确。它直接关系到第 74 项的"成本与性能口径一致"，列入 §8。

## 3. S4B-3 陆上风：实际发电校准 + 现代机型；资源分级（第 74、75 项；`s4b_3_wind_calibration.py`、`s4a_profiles.py`、`s4b_3_export.py`）

**3.1 观测容量因子（Ember 年度数据，CC BY 4.0，SHA256 b2ac49fa…；B 级；VERIFIED）。** CF_y = 发电量_y ÷（8,760 h × 当年与上年装机均值）：

| 国家 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 有效年份 | 中位数 | IRENA 图 2.12（S4A 读数） |
|---|---|---|---|---|---|---|---|---|---|---|
| PH（0.43–0.52 GW） | 0.273 | 0.267 | 0.332 | 0.275 | 0.350 | 0.389 | 0.348 | 7 | **0.332** | 约 35%（2024） |
| TH（1.1–1.55 GW） | 0.321 | 0.243 | 0.265 | 0.224 | 0.260 | 0.260 | 0.264 | 7 | **0.260** | （Other Asia 39%） |
| VN（0.37→6.18 GW） | 0.271 剔除（装机 +54%） | 0.252 弃风期 | 0.164 剔除（+692%） | 0.226 弃风期 | 0.241 | 0.241 | 缺装机 | 2 | **0.241**（含 2020/2022 也为 0.241） | 约 42%（2024） |
| ID（0.15 GW） | 0.381 | 0.361 | 0.333 | 0.271 | 0.366 | 0.355 | 缺装机 | 6 | 0.358（< 200 MW，不单独校准） | 约 26–38% |

其余东盟国家风电装机为 0。VN 2020–2022 年的弃风：未查到风电的定量数据；公开资料（IUCN 越南 2022-05《可再生能源的电网整合》、Energy Transition Partnership 2024《Managing Vietnam's Grid Issues for Effective Energy Transition》，检索摘要）记载 2021–2022 年输电阻塞导致风光项目被限发，唯一看到的定量数字是 2021 年约 13 亿 kWh 光伏未被调度（C 级）。这几年在主算中位数中剔除、单独列出。观测值（实际机队，含老旧机组与限发）低于 IRENA 新建项目值。

**3.2 模型在现有风电场处的 CF（2013 年 cutout；VERIFIED）。** GEM GIPT 2026-09 在运风电单元（陆上与近岸潮间带，投运 ≤ 2024 或年份不明）：PH 10 个 592 MW、TH 29 个 2,137 MW、VN 113 个 6,929 MW（其中陆上 5,095）、ID 3 个 157 MW、MM 1 个 210 MW；每个场取所在 0.3° 格点，复现 atlite 0.4.1 的算法（对数律外推 + 功率曲线插值），按容量加权。GEM 没有风机机型字段（只有油气机组有），公开项目资料无法逐场核实，校准机型取本机 atlite 的 **NREL 2020 ATB 4 MW**（转子 150 m、226 W/m²、轮毂 110 m，低比功率参考机型，与 2018–2022 年低风速机型相当，INFERENCE），V112 作对照：

| 国家 | 观测 | 模型 CF（α = 1）NREL 4 MW / V112 / DEA 2050 | α（NREL 4 MW，主算）| α（V112 对照）| α（DEA 2050 机型，诊断）|
|---|---|---|---|---|---|
| PH | 0.332 | 0.384 / 0.315 / 0.361 | **0.910** | 1.031 | 0.949 |
| TH | 0.260 | 0.120 / 0.080 / 0.109 | **1.294** | 1.475 | 1.344 |
| VN | 0.241 | 0.244 / 0.178 / 0.223 | **0.995** | 1.129 | 1.032 |
| 其余 8 国 | — | — | **1.046**（PH/TH/VN 按装机加权，C 级） | | |

全部 α 在 [0.8, 1.6] 内，未触发停止。**解读（INFERENCE）：** S4A 发现的"模型陆风 CF 比 GWA 低 2–3 倍"主要来自国家平均与 V112@80 m；在实际风电场格点上，用现代低比功率机型时 ERA5 已接近观测（VN、PH 的 α ≈ 1，PH 甚至略高估），只有 TH 需要 +29% 风速。

**3.3 新建陆上风机型（第 74 项口径）。** technology-data v0.15.0 `onwind` 2050 引用的 DEA 数据表（`technology_data_for_el_and_dh.xlsx`，"20 Onshore turbines"，GitHub v0.15.0 中最后修改 2022-03-17，git blob ce07675b，与本机审计副本逐字节相同）：单机 6 MW、转子 165 m、轮毂 110 m、比功率 280.6 W/m²、满负荷小时 3,800。atlite 本机机型中比功率最接近的是 V112（310.6 W/m²），NREL 4 MW 为 226 W/m²，均不吻合，故按 DEA 参数构造功率曲线：以 V112 的单位化曲线为形状，把部分负荷段的风速乘以 (280.6/310.6)^(1/3) = 0.9667（Cp 形状相同时额定风速与比功率的立方根成正比），切出风速保持 25 m/s，额定 6 MW、轮毂 110 m（atlite 自定义机型字典）。**与 2026 年 8 月版对照（用户指示）：** 新版 PDF 第 20 章修订于 2019 年 5 月与 2023 年 11 月，PDF 中没有数据表；图 24 给出 2050 年满负荷小时 3,800、比功率约 280.6 W/m²、轮毂 110 m，与引用版相同；单机容量与转子直径未出现在 PDF 中（在 2026 年数据表 xlsx 里，未授权下载），无法对比。主算用引用版。

**3.4 重建出力曲线（VERIFIED）。** 新变体 `profile_variant: calibrated_modern`（主算）：陆上风 = ERA5 100 m 风速 × 所在国 α（格点按面积最大的国家归属）+ DEA 2050 机型；海上风与光伏直接取 S4A `pypsa_eur` 的结果（同一规格，逐值相同，测试核对）。`resource_classes: 3`（主算），N = 1 对照；`clip_p_max_pu = 0.01`。每次运行（仅陆风，含 GWA 交叉检验）28 s、1.9 GiB（低于 1 h / 8 GiB）。文件 `research_inputs/renewable_v5/profiles_calibrated_modern_c{1,3}_3h.nc`（8.7 / 3.1 MB）。构建：两情景静态 PASS（44 s、0.66 GiB），新增分级发电机 647 台，陆风 `p_nom_max` 合计 8,916.8 GW 不变。

**3.5 校验（四方对比；`ONWIND_CF_CHECK_S4B3.csv`）。** 停止判据在计算前写入进度文件：最优级 CF > 1.10 × max（GWA IEC2 p90，IRENA 读数上沿；无本国读数的取 Other Asia 0.39）即停。

| 国家 | 观测 | IRENA | GWA 均值 / p90 | `pypsa_eur` 节点均值 / 最大 / 最优级 | **`calibrated_modern` 节点均值 / 最大 / 最优级（GW）** | GWA 缩放（交叉检验）最优级 | 阈值 |
|---|---|---|---|---|---|---|---|
| PH | 0.332 | 0.35 | 0.270 / 0.457 | 0.137 / 0.192 / 0.309 | 0.130 / 0.184 / 0.287（14.0） | 0.609 | 0.503 |
| VN | 0.241 | 0.43 | 0.304 / 0.480 | 0.092 / 0.123 / 0.199 | 0.117 / 0.154 / 0.230（16.0） | 0.587 | 0.528 |
| TH | 0.260 | 0.39 | 0.124 / 0.214 | 0.062 / 0.104 / 0.119 | 0.178 / 0.274 / 0.289（80.1） | 0.294 | 0.429 |
| ID | 0.358 | 0.38 | 0.129 / 0.272 | 0.055 / 0.221 / 0.078 | 0.075 / 0.273 / 0.116（131.9） | 0.395 | 0.418 |
| MY | — | 0.39 | 0.089 / 0.211 | 0.034 / 0.093 / 0.115 | 0.048 / 0.113 / 0.129（10.4） | 0.393 | 0.429 |
| LA | — | 0.39 | 0.099 / 0.225 | 0.043 / 0.134 / 0.085 | 0.075 / 0.220 / 0.125（9.2） | 0.389 | 0.429 |
| MM | — | 0.39 | 0.123 / 0.251 | 0.052 / 0.094 / 0.073 | 0.080 / 0.141 / 0.123（120.3） | 0.296 | 0.429 |
| KH | — | 0.39 | 0.109 / 0.165 | 0.055 / 0.066 / 0.075 | 0.091 / 0.112 / 0.127（44.3） | 0.341 | 0.429 |
| TL / BN / SG | — | 0.39 | | 0.049 / 0.021 / 0.059（均值） | 0.072 / 0.035 / 0.088（均值），最优级 0.259 / 0.067 / 0.105 | 0.516 / 0.291 / 0.398 | 0.429 |

（节点均值 / 最大 = 布局加权的 3 h 序列均值；最优级 = 第 3 级潜力加权的年均 CF。）没有国家超过阈值，**未触发停止**。单个节点的最优级最高为 PH5 0（1.4 GW @ 0.441）、ID_Papua19 0（0.409）、LA2 0（0.388）、VN2 4（0.381），潜力都很小。GWA 风速缩放（只作交叉检验）会使 PH、VN、TL 的最优级超过阈值（0.61 / 0.59 / 0.52），说明直接按 GWA 均值缩放会高估，支持按实际发电校准。未改动的 16 台候选（S4A 的 15 台 + `pypsa_eur` 3 级海上文件中单格点节点 PH_Mindanao6 1 的 DC 海上风）与陆风校准无关。

**局限（写入登记 `onwind_calibration_limitations_s4b3`）：** 观测年份（2019–2025）与 2013 年气象年不同（年际波动约 ±5–10%）；机型未知时 α 会吸收机型差异（V112 对照的 α 高 0.12–0.18）；海上风没有观测，不校准；Ember 不区分陆上与潮间带（VN 潮间带风场一并计入）；风电场按 0.3° 格点取值。

登记片段 `s4b_3`（21 行：观测 CF 4、α 11、机型 2、开关 2、交叉检验与局限 2）。测试 `test_s4b_3.py` 5 项；`test_s4a_profiles.py` 中两项原本固定 S4A 主算（`pypsa_eur`、1 级），按第 74、75 项改为显式测试 `pypsa_eur` 并断言新的主算设置。

（S4B-4 至 S4B-6 见后续各节。）

## 7. 附加诊断：4 个失败的 `test_gate4_activation`（只诊断，未修改、未跳过）

**被测对象：** 4 个失败项都在 `AppliedInputTests` 类，检查的是 Phase 4 Gate4 的 Assembly-V1 需求输入登记 `research_inputs/assembly_v1/registry.json`（2050 年需求记录）及 `check_assembly_inputs.check`、`rebuild_assembly_targets.derive`。同一文件中与水电相关的 `HydroAggregationTests`（6 项，依据 `hydro_decisions.json` 的 GATE4-20261005-HYDRO-PHYSICAL-POLICY-SEPARATION）全部通过。

**首次失败的提交（VERIFIED：在临时分离工作树中逐个提交运行该测试文件，运行后已删除工作树）：** 测试写于 36a8608c（2026-10-05），在 36a8608c、2a722b8d 两个提交上 13 项全过；0177f678（2026-10-06 05:03，"fix: recover original UNSD OtherNEC transaction aliases"）首次出现 2 项失败；59d02392（2026-10-06 08:17，"data: freeze assembly-v1 uncertainty boundaries"）再增 2 项；之后一直是这 4 项（c2f0fc34 未新增）。

| 测试 | 断言 | 首次失败 | 原因 | 其余断言在当前 HEAD 上 | 分类 |
|---|---|---|---|---|---|
| `test_nec_source_rows_unique_and_retained` | TransportNEC/OtherNEC 的 UNSD 源行共 15 条且唯一；值 = 基年值 | 0177f678 | 按已接受的 OtherNEC 规则（`GATE4_CONSOLIDATED_BASELINE_DECISIONS.json`，Methods.OtherNEC = ASSEMBLY_V1_OTHER_NEC_CONSTANT_2019，HUMAN_ACCEPTED；即 GATE4-20261005-CONSOLIDATED-BASELINE-CHOICES）机械恢复两条此前未映射的 UNSD 1234 LPG 行（`refresh_nec_alias_inputs.py`）：MM OtherNEC 油 5,146,140 → 5,526,910 MWh，源行 15 → 17 | 17 条且唯一；值 = 基年值 ✓ | (a) |
| `test_prior133_values_unchanged_new19_have_sources` | 7c4b9dda 时的 133 条已接受需求值不变；现有 152 条；`derive` 给出 152 条 | 0177f678 | 0177f678 使已接受需求 152 → 153；59d02392 按 GATE4-20261006-FINAL-CLOSURE（HUMAN_ACCEPTED；A 混合燃料基线、B 未报告部分列为覆盖边界、C 只用合格存量）把 18 条 PENDING 改为接受 → 171 | 133 条原值全部不变 ✓；现有 171 条，`derive` 171 条 | (a) |
| `test_rail_parent_not_posted_and_ph_stays_blocked` | 接受铁路非电需求的国家只有 ID/KH/MM/TH，PH 保持 PENDING；5 个载体拆分父项不入账 | 59d02392 | GATE4-20261006-FINAL-CLOSURE 写明"PH rail uses the already approved constant-2019 target method"（`GATE4_FINAL_HUMAN_REQUEST.txt` 第 111 行），PH 铁路改为接受 | 5 个父项仍为 ACCOUNTING、非必需、无值 ✓ | (a) |
| `test_coverage_and_ev_boundary_remain_guarded` | `NUMERIC_INPUT_READY` 为假；已知正值目标方法待定数 = 0；道路 EV 为边界项 | 59d02392 | 同一决定 B 把 15 条未报告账户列为 HUMAN_COVERAGE_BOUNDARY，`check_assembly_inputs.check` 相应排除，数值输入就绪变为真（这是该测试"在最终闭合前保持关闭"的本意被决定取代） | 待定数 0 ✓；EV 边界 ✓ | (a) |

**结论（VERIFIED + INFERENCE）：** 4 项都属于 (a)——测试固化的是 2026-10-05 的中间状态（计数与"尚未闭合"的标志），被 0177f678 的机械源行恢复（在 GATE4-20261005-CONSOLIDATED-BASELINE-CHOICES 规则下）和 GATE4-20261006-FINAL-CLOSURE 取代；除计数与状态外的全部断言在当前 HEAD 上仍成立，不是回归。它们不涉及水电、抽蓄或 S4B-2 的新建候选（S4B-2 用 GEM/潜力数据与存量代理，不读 Assembly-V1 需求登记）。**建议（需用户确认，§8）：** 将 4 项标为 `xfail(strict=True)`，原因分别写明 0177f678 / GATE4-20261006-FINAL-CLOSURE；或把期望值更新为 17 条、171 条、PH 接受、`NUMERIC_INPUT_READY` 为真。在确认前未修改、未跳过。
