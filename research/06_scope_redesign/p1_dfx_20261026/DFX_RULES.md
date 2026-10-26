# DFX_RULES —— 需求修复 F1–F4 的规则、数据来源与数值（事先登记）

**登记时间：** 2026-10-26（SGT），在任何 v2 网络构建之前提交。指令 v3 SHA256 `b60da4c6…5a6df`。本文件登记规则与来源；`DFX_RULES_NUMBERS.json`（原型脚本 `scripts/wsl_dfx3/ras_proto.py` 对 v1 表的只读计算）登记按这些规则算出的目标数值，供构建后逐项核对（相对差 ≤ 1e-9）。看到任何求解结果后，本文件不再修改。

## 0. 范围与不变项

- 只改需求：`scripts_project/m08b_demand.py`（F1、F2 产量与 NEU 扣除）、`scripts_project/s3_0_industry.py`（F2 替换）、`scripts_project/s2_layers.py`（F3 作用范围）、`scripts_project/s2b_feedstock.py`（F3 同一范围用于敏感性列）、新增 `scripts_project/dfx_data.py`（F4 注册表片段与更正）、`scripts_project/d1_registry.py`（登记新片段）、`configs/research/baseline.yaml`（F2 产量规则参数与 F3 开关注释，均在 `research.s2.industry` / `research.s2.demand` 需求键下）、测试。网络的其他组件、成本表、求解档案、GATES_V6 / C1 阈值一律不变。
- 数据链重跑顺序：`m08b_demand.py → m08b_heat_bands.py → s3_0_industry.py → s2b_feedstock.py → s2_0_process_emissions.py → m08b_data.py → dfx_data.py → d1_registry.py`（与 M08b 的 `m08b_data.sh` 相同，末尾加 `dfx_data.py`）。
- 国家代码：10 个 AEO8 国家 C10 = BN, KH, ID, LA, MY, MM, PH, SG, TH, VN；TL 在 AEO8 之外（TL 规则）。
- 单位：1 Mtoe = 11.63 TWh；kgoe/人 × 百万人 × 1e3 × 11.63 = MWh。

## 1. F1 —— NEU 移出 TFEC 包络；RAS 部门拆分（薄弱点 1、2）

**依据（核实）：** AEO8 附录 E（PDF 第 202 页）："Total Final Energy Consumption (TFEC): The sum of energy consumption by end-use sectors, excluding non-energy use and international transportation."；表 C.3（PDF 第 184 页，印刷页 182）ATS 2050：Industry 387、Transport 228.2、Residential 52.8、Commercial 50.4、Agriculture and Others 27.8，Total 746.2 Mtoe（本次用 pypdf 从 `aeo8.pdf` SHA256 `48c2a819…11c06` 文本层复核，与注册表来源文件 `AEO8_2050_ASEAN_TOTALS.csv`（SHA256 `0afdacd2…63e6`）一致）。

1. **国家锚不变：** A_c = C.8 ATS 2050 人均 TFEC（kgoe/人）× D.1 2050 人口（百万）× 1e3 × 11.63（MWh），10 国；来源文件 `AEO8_2050_BY_COUNTRY.csv`（SHA256 `875ef946…27d6`）。TL 按现行 `demand_anchor_tl_rule`（人均 = KH / LA / MM 均值，人口 UN WPP 2024 中位 1,889,249.5）。Σ_{C10} A_c = 8,676.778 TWh。
2. **NEU 不再计入部门权重：** 撤销 `m08b_demand.py` 第 185 行 `t19["Industry"] += NEU`；种子、权重、工业锚都只含能源用途（`sector ∈ {Industry, Transport, Residential, Commercial, AgricultureOthers}`）。2050 NEU = 2019 NEU（D1 表 `NonEnergyUse` 行 `base_2019_mwh`）× 该国工业乘数 m_ind（现行算法：NEU 行与工业行共用 `multiplier_total`），作为非能源需求加在能源用途之外。**TL：** 2019 工业能源用途为 0（D1 表 TL 五个工业行均为 0），工业乘数无定义 → NEU 乘数取 KH / LA / MM 工业乘数的简单均值（TL 规则的延伸：TL 的人均与 GDP 增长率同样取三国均值）；TL 工业行保持 0。
3. **RAS 双比例拟合（10 国 × 5 部门）：**
   - 种子 S_{c,s} = Σ D1 表（`DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv`，SHA256 `526a54bd…29c2`）该国该部门所有载体行的 `base_2019_mwh`（UNSD 2019 能源用途；部门映射沿用现行表的 `sector` 列）；不乘增长率（列缩放吸收统一乘子）；零种子保持 0（本次 50 格无零种子）；
   - 行约束 r_c = A_c；列约束 s_s = C.3 ATS 2050 印刷值 × 11.63e6 × k，k = Σ_{C10} A_c / Σ_s (C.3_s × 11.63e6) = 8,676.778 / 8,678.306 = **0.999823954704**（消除 C.8 × D.1 与 C.3 合计的舍入差）；
   - 迭代：先行后列交替缩放（X ← X · r_c / Σ_s X；X ← X · s_s / Σ_c X），直到行、列相对误差都 ≤ 1e-10，最多 1,000 次；不收敛即停下报告（原型：第 11 次迭代收敛，行误差 3.4e-11、列误差 2.2e-16）；
   - 结果 tfa_{c,s} = 2050 能源用途部门锚（MWh）。TL 不进 RAS：tfa_{TL,s} = A_TL × w_s / Σw，w_s = 2019 部门能源用途 × C.3 ATS 部门增长（2050 / 2022，ATS 面板印刷值），NEU 不在权重内。
4. **下游规则不改，只接收新锚：** 电力锚（A_el × 2019 部门电力 × ATS 电力增长的归一权重，居民电力增长 29.0 → 33.2 Mtoe）不变；交通燃料锚 = tfa_Transport − 交通电力锚；工业乘数 m_ind = tfa_Industry / 2019 工业能源用途；居民 / 商业 / 农业燃料锚 = tfa_s − 部门电力锚，负值取 0 并列出（`demand_sector_fuel_anchor_zeroed` 刷新），正值但无 2019 燃料行也取 0；钢 / 水泥产量规则、EV / FCEV / ICE 份额与效率、航运甲醇、炊事、农机、热档等代码不改。
5. **预期核对（写成测试）：** Σ_{c∈C10,s} tfa = Σ A_c（相对差 ≤ 1e-9）；Σ_c tfa_{c,s} = k × C.3_s × 11.63e6（≤ 1e-9）；10 国交通锚 2,653.499 TWh（≈ 2,654）；NEU 不在任何能源用途锚中（种子、工业锚、部门锚均不含 `NonEnergyUse` 行）；A_c 与 v1 锚表逐国相等。
6. **登记的目标值（原型，TWh）：** 10 国部门锚 Industry 4,500.018 / Transport 2,653.499 / Residential 613.956 / Commercial 586.049 / Agriculture and Others 323.257；11 国交通锚 2,660.986（v1 1,700.4）；负燃料锚 8 格合计 −65.149 TWh：BN 居民 −0.678、BN 商业 −1.035、MY 居民 −17.294、MY 商业 −16.221、SG 居民 −3.602、SG 商业 −4.175、TH 居民 −0.061、VN 居民 −22.084，另 TL 商业 +0.186 无 2019 燃料行（v1：9 格 −63.30 TWh；TH 商业与 SG 农业由负转正，TH 居民与 VN 居民由正转负）。工业乘数 m_ind（v1 → v2）：BN 0.541 → 0.839、KH 4.015 → 3.509、ID 2.456 → 2.619、LA 2.669 → 2.536、MY 1.210 → 1.378、MM 0.935 → 1.011、PH 2.228 → 2.078、SG 0.746 → 1.166、TH 1.634 → 2.022、VN 3.084 → 3.108、TL 7.634 → 2.352（NEU 用）。

## 2. F2 —— 氨需求按产量重建；扣除对应的 NEU 天然气原料（薄弱点 5 的氨部分）

1. **氨产量 2050（t NH₃）：** 基年 2019 产量来自本机 USGS Minerals Yearbook 2022 Nitrogen 工作簿 `usgs_myb1-2022-nitro-ert.xlsx`（SHA256 `9b055fcd…cc42`）表 T12 "AMMONIA: WORLD PRODUCTION, BY COUNTRY OR LOCALITY"（千吨含氮量）：Indonesia 6,100、Malaysia 1,200（r）、Vietnam 1,150（2019 列）；其他东盟国家未列出 → 0。含氮量 → NH₃ 按 PyPSA-Eur v2025.07.0 `build_ammonia_production.py`（SHA256 `5aca047c…b25e`）的同一换算 × 17/14，取自仓库已复现的 `registry_v5/sources/jrc_idees_2021/ammonia_production.csv`（SHA256 `c8414b7e…00b0`）2019 列：ID 7,407.143、MY 1,457.143、VN 1,396.429 kt NH₃。
   产量规则 = 与水泥、钢相同的增长项：NH3_2050 = NH3_2019 × max(G_c, 1)^((2050 − 2019) / 28 × 0.5)，G_c = AEO8 表 D.2 实际 GDP 2050 / 2022（`AEO8_TABLE_D2_REAL_GDP_PPP2017.csv`，SHA256 `9189d862…e793`；TL 取 KH / LA / MM 均值），弹性 0.5 = 注册表 `industry_output_elasticity` 现值；**不设人均饱和与规划上限**；登记但不运行的备选：弹性 0.3 / 0.8（写入输出表列 `ammonia_2050_elasticity_low/high_mt`）、"2019 产量保持不变"。写入 `INDUSTRY_OUTPUT_BASE_M08B.csv` / `INDUSTRY_OUTPUT_2050_M08B.csv` 新列（`ammonia_base_year` 2019、`ammonia_base_kt`、`ammonia_2050_mt`、`ammonia_binding` = growth），配置 `research.s2.industry.physical_output_base_year.ammonia: 2019`（构建核对配置 = 表）。
   登记的目标值：G_ID 2.9539、G_MY 2.8427、G_VN 3.7604 → 增长因子 1.8214 / 1.7831 / 2.0818 → NH3_2050 ID 13,491.140、MY 2,598.199、VN 2,907.045 kt，合计 18,996.4 kt（v1 隐含 6,170 kt）。
2. **能量换算：** 5.166 MWh_NH₃/t（比率表 `INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv`（SHA256 `bc7216fc…4384`）`Ammonia` 列 `ammonia` 行 = PyPSA-Eur `MWh_NH3_per_tNH3`，配置第 849 行）；沿用现行系数。目标值：ID 69.695、MY 13.422、VN 15.018 TWh，合计 98.135 TWh（v1 31.849 TWh：ID 9.948、TH 9.359、VN 7.650、SG 3.634、PH 1.001、MM 0.210、BN 0.047，MY 0）。
3. **替换，不叠加：** `s3_0_industry.py` 在 `aeo8_ats_anchor` 模式（有产量规则表的模式，与钢 / 水泥的做法一致）下，化工子行业能耗按 EU27 2019 权重分给 `Ammonia` 行业的那一份（权重 0.307500321533，未来载体份额 ammonia 1.0）不再生成氨需求：该份能量（2019 化工能耗 × 权重 × 乘数 × 效率系数 0.449）记入汇总表列 `pe_ammonia_eu27_share_dropped_mwh`，不计入任何载体；`pe_ammonia_mwh` = 第 1、2 条的产量法数值。甲醇、HVC、氯、其他化工、医药的权重与方法不变（权重不重新归一）。敏感性模式（`aeo8_ats_relative` / gdp / population / level 表）不改。局限：本机没有可用的东盟甲醇 / 乙烯产量数据，甲醇与 HVC 仍按 EU27 权重法。
4. **扣除原料天然气：** 各国 2050 NEU 天然气（D1 表 `NonEnergyUse` × `gas` 行，账户 `NonEnergy:Natural gas (including LNG)`，2050 值 = 2019 × m_ind）−= NH3_2050（t）× **10.8 MWh_CH₄/t NH₃**，扣到 0 为止，截断量逐国报告。
   - **来源与追溯：** JRC-IDEES-2021 Industry EU27 工作簿（`JRC-IDEES-2021_Industry_EU27.xlsx`，SHA256 `1fd3bc14…3dc3`）经逐表检索不含任何 "ammonia / NH3 / nitrogen" 行，只有化工原料合计行 "Chemicals: Feedstock (energy used as raw material)"，无法给出每吨氨的原料量（第一优先来源不可用）；第二优先来源：PyPSA-Eur v2025.07.0 `config.default.yaml`（SHA256 `bfbe9160…da787`）第 850 行 `MWh_CH4_per_tNH3_SMR: 10.8`，即工业比率脚本 `build_industry_sector_ratios.py`（SHA256 `70c45a81…0c61`）第 431–437 行用于从基础化工能耗（含 IDEES 原料天然气）中扣除当年氨产量的同一常数，也是仓库 `s3_0_industry.py` `PE["MWh_CH4_per_tNH3_SMR"]` 现行使用的常数。
   - **登记的局限（醒目）：** 10.8 MWh/t 是 SMR 路线的天然气总投入（重整原料 + 重整炉燃料），统计口径上只有原料部分进入 UNSD 非能源用途，因此它是原料量的**上限**；按化学计量（technology-data Haber-Bosch `hydrogen-input` 1.1484 MWh_H₂/MWh_NH₃ × 5.166，CH₄ + 2H₂O → CO₂ + 4H₂ 的 LHV 比 1.2055）的下限约 4.92 MWh/t，登记为敏感性区间 4.92–10.8，本次不运行。F2.2 已把 EU27 权重法分给氨的化工**能耗**份额去掉，10.8 中的燃料部分可能被再次扣除（过度修正），其量 = 产量 × (10.8 − 原料实际值)。
   - 登记的目标值（TWh，v2 乘数下）：ID NEU 天然气 188.071 − 145.704 = 42.367；MY 173.444 − 28.061 = 145.383；VN 23.228 − 31.396 → 0，截断 8.168；其他国家无氨产量，不扣。
5. **核对（测试）：** 氨需求逐国 = `ammonia_production.csv` 2019 × 规则 × 5.166（≤ 1e-9）；MY > 0；USGS 未列产量的国家（BN、KH、LA、MM、PH、SG、TH、TL）= 0；NEU 天然气行 = max(0, 2019 × m_ind − NH3 × 10.8)；截断量与登记值一致。

## 3. F3 —— HVC 系数只作用于 HVC 原料（薄弱点 8）

- `share_HVC_primary_fraction_2050` = 0.4（注册表现值，不改）只乘 NEU 油行中的 HVC 原料账户：**`NonEnergy:Naphtha`、`NonEnergy:Ethane`、`NonEnergy:Liquefied petroleum gas (LPG)`、`NonEnergy:Natural gas liquids`**（2019 合计 326.718 TWh）；非 HVC 产品账户系数 1.0：**`NonEnergy:Bitumen`、`NonEnergy:Lubricants`、`NonEnergy:Paraffin waxes`、`NonEnergy:Petroleum coke`、`NonEnergy:Gas Oil/ Diesel Oil`、`NonEnergy:Motor Gasoline`、`NonEnergy:Fuel oil`**（2019 合计 55.878 TWh）。D1 表中 NEU 油账户共 11 个，以上两组穷尽。NEU 煤、气行系数 1.0（不变）。
- 实现：`s2_layers.add_demand_layer` 的 NEU 负荷 = Σ_HVC 行 × 0.4 + Σ_非 HVC 行 × 1.0（每节点一个负荷，名称不变）；`s2b_feedstock.py` 的 `full_release_2050_t` 敏感性列用同一范围（主模式 territorial 不受影响，只改 meta 中记录的敏感性数值）。
- 开关 `research.s2.industry.hvc_recycling_applies_to_naphtha` 新定义：true = 系数作用于上列 HVC 原料账户（主值）；false = 不作用于任何 NEU 行。登记为注册表行 `hvc_primary_fraction_scope`。

## 4. F4 —— 注册表刷新与补登（薄弱点 7）

1. 刷新（按 v2 构建实际使用的数值，`dfx_corrections.csv` 全行替换，`REGISTRY_CHANGELOG_DFX.csv` 记行键、旧值、新值、原因）：`industry_ammonia_2050_{C}`、`industry_methanol_2050_{C}`、`industry_hydrogen_2050_{C}`、`industry_low_temperature_heat_2050_{C}`、`industry_coal_retained_2050_{C}`、`industry_steel_2050_{C}` 描述、`shipping_demand_domestic_2050`、`demand_tfec_2050_{C}`（= A_c，能源用途口径）、`demand_sector_fuel_anchor_zeroed`、`demand_anchor_family_main` / `demand_base_load_rule` / `demand_transport_anchor_rule` / `demand_sector_fuel_anchor_rule` 的描述（归一权重 → RAS）、`feedstock_full_release_2050_{C}`（F3 范围）、`feedstock_process_2B_2D_2050_{C}` 等由数据链脚本自动重写的行按脚本输出。
2. 补登（`dfx.csv` 新行）：炊具效率 `cookstove_efficiency_basic_ID` 0.08、`_TH` 0.16、`_default` 0.08、`cookstove_efficiency_modern` 0.53（来源 IEA Defining energy access: 2020 methodology, Table 2；配置 `cookstove_efficiency_source`）；清洁炊事开关 `clean_cooking_switch`（决定 23）；有用热效率 `industry_useful_heat_efficiency` 0.90（`s3_0_industry.HEAT_EFF`；technology-data solid biomass boiler steam 0.90）；`hvc_primary_fraction_scope`；`demand_node_allocation`（`assembly_v1_allocation_shares_then_astar`）；AEO8 C.3 ATS 2050 各部门数值行 `aeo8_c3_ats_2050_{sector}`（5 行 + 合计）与 2022 值；`demand_sector_split_ras`（规则、k、收敛、迭代次数）；`industry_ammonia_output_rule`、`industry_ammonia_production_2019_{C}`（USGS）、`industry_ammonia_feedstock_gas_per_t` 10.8（含上限说明与 4.92 下限）、`industry_ammonia_feedstock_gas_deducted_{C}`（扣除量与截断量）、`industry_ammonia_eu27_share_dropped_{C}`。
3. 映射表 `research_inputs/registry_v5/REGISTRY_NETWORK_INPUT_MAP.csv`：每个映射到网络输入的数值行 → 表 / 网络中的取法；测试逐行核对（相对容差 1e-9；网络级核对在 v2 网络文件存在时运行）。
4. 注册表原地更新（`DATA_REGISTRY.csv` 路径不变；旧版 SHA256 `4c59adb7…8720`，2,194 行，由 git 历史保留）。

## 5. F5 —— 构建、等价测试、复核、一阶预测、冒烟（事先登记的做法）

- 构建：`PYTHONHASHSEED=0`，`scripts_project/s2_network.py --scenario {integrated,disconnected} --output …`（与 `m08b_build.sh` 相同；每次写 2920×3h 与 365×24h），干净提交；v1 基线 = 同一 worktree 路径上在基提交 `55ab07c0`（需求代码 = `ec80668f`）重建的四个网络（`results_project/dfx_v3/builds_v1`，F0 已做），以排除 `s2_network.py:344` 的路径元数据差异；另核对 builds_v1 与 `ec80668f` 登记网络除该路径字段外逐字段相同。
- 结构等价测试（允许的差异，逐项列出，其余任何差异 = 失败）：`loads` / `loads_t.p_set`；因负荷变化而必然变化的派生项——`n.meta` 中的需求账本（`s2_demand_ledger`、`demand_owners`、`demand_identity`、`research_bunkers` 不变）、`research_config_sha256`（配置新增键）、`registry_sha256`（若记录）、过程排放发电机（`process emissions source`，p_nom = EDGAR × 工业乘数，乘数随 F1 变）、`dust_cleanup` 清理清单（负荷归零或新增引起的母线 / 链路存废）、新增负荷所需的母线 / 链路（如 MY 氨负荷落在区域氨母线上无需新链路）；其它组件（generators 除过程排放、links、lines、stores、storage_units、buses、carriers、global_constraints 及其时序）逐字段相等。
- 需求复核：`work/p1_dmd_20261026/scripts/` 的 `dmd_d1_demand.py`、`dmd_d3_benchmark.py` 复制到 `work/p1_dfx_20261026/scripts/` 改输入路径（原文件不改）；输出需求总表与 v1 逐项差、AEO8 ATS → v2 负荷分解（闭合残差 ≤ 1e-3 TWh）、分国人均用电与固定电力 / ATS 比值。
- 一阶预测：DMD `dmd_d5_duals.py` 方法——R1 / R2（第三批 365×24h，`export/R1`、`R2`）各负荷母线的年度负荷加权对偶价格，ΔD = v2 − v1 逐（国家, 账户, 载体）年量，ΔC = λ·ΔD，ΔB6 = ΔC_不互联 − ΔC_一体化，分国受益变化 = (λ_dis − λ_int)·ΔD_i；写入 `RUN_PLAN_DFX.md` 并在任何 v2 求解前提交；注明大变动外推。
- 本机冒烟（本指令 2 次 Gurobi 调用）：v2 2920×3h 一体化与不互联各截短到前 56 个时段，`s2_solve.py --truncate 56 --label SMOKE_TEST_ONLY --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 3000`，墙钟止损 3,600 s（≤ 60 分钟），串行，两次间隔 ≥ 330 s；之后违反量分析、C1、本批参照 + 重评、M12 分摊、Owen 对偶形式审计、GATES_V6；非 optimal 或不可行即停下报告，不调参、不重试。

## 6. F6 —— 365×24h 筛查运行计划骨架（细节与网络 SHA256 写入 `RUN_PLAN_DFX.md`）

- V1 = 365×24h v2 一体化、V2 = 365×24h v2 不互联；档案 `formal_barrier_1e6_t16`；TimeLimit = 第三批 R3 / R4 求解进程墙钟（4,882 / 1,423 s）× 3 = 14,646 / 4,269 s；墙钟止损 = TimeLimit + 1,200 s；两次启动间隔 ≥ 330 s；两会话并行只在核数 ≥ 33（2 × Threads 16 + 后处理 1）时，否则串行；验收 GATES_V6、C1（本批参照 = V1 / V2）；后处理同第三批 3.5 / 3.6（账本与 B16、B6 = V2 − V1、Owen 对偶形式 α 0.5 主值 / α 区间 / 市场形式 / 燃料舱）、与 R1 / R2 对比、实际 ΔB6 与一阶预测对比（只描述）；LOO 不做。
- 部署包 v8：两个 365×24h v2 网络 + 回执 + 成本表、代码归档、`RUN_PLAN_DFX.md`、运行 / 预检脚本、第三批同一环境锁定（pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4、pandas 2.3.1、xarray 2025.1.2、scipy 1.15.2、netCDF4 1.7.2）、清单与 `SHA256SUMS`。

## 7. 不在本次范围（只在报告"局限"中列出）

燃料舱口径与增长；工业"其他桶"的温度分布与有用热效率；100 % BEV 与 ICE / BEV 能效比；显式制冷；水泥 / 钢参数；甲醇与 HVC 的产量化；TL 规则；氨原料量的实际原料 / 燃料拆分（本机无来源）。
