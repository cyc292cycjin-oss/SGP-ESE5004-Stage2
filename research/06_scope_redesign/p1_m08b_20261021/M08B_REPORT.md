# M08b 报告：需求锚定、工业有用热、生物质溢出；重建网络与冒烟测试（第 126、129–134 项）

## 摘要（≤ 15 行）

1. **范围：** 指令 SHA256 `dde52c92…59b2` 核对一致；分支 `codex/m08b-demand-20261021`（自 M08a 头 `820c2cae`，独立 worktree），draft PR 叠在 #45 上；未连云。M11 台账条目已并入（用户选择：标"无项号"、按时间排在 M08a 前）。
2. **B1 需求锚定（VERIFIED）：** 新需求表键 `aeo8_ats_anchor`（AEO8 ATS 人均 × 人口，TL 按 KH/LA/MM 均值 × UN WPP 1,889,249.5）。11 国基础负荷 966.9 TWh（旧比率表 1,032.4；全部非负；S4R 965.9，+0.11 %，原因见 §1.2），交通锚 1,700 TWh（旧 2,991）。11 国活动量与锚的偏差 ≤ 1e-6，构建期逐国核对 ≤ 1e-9。
3. **物理产量：** 一条规则对 11 国：min(基年 × G^((2050−基年)/28 × 0.5), 人均饱和 × 人口, 规划上限)。水泥基年 USGS 2023、粗钢 worldsteel 2024。VN 水泥 107.0 Mt（人均上限绑定），VN 粗钢 40.64 Mt（增长规则；规划 70 Mt 不绑定）；11 国水泥 1,290 → 417 Mt，粗钢 152 → 98 Mt。
4. **B2 有用热与溢出：** "其他工业"桶按 JRC-IDEES OIS 温度分布拆成三档有用热（× 0.90），由模型在 technology-data v0.15.0 有条目的技术中内生选择；11 国工业固定用电 3,969 → 1,082 TWh，中温 688、高温 900 TWh 热由模型供给。溢出转甲烷与 0.98 上限删除，溢出改为有用热（仅 SG 农业 0.18 TWh）。
5. **B3：** 注册表 2,121 → 2,184 行（`53b051c1…` → `97b27c87…`；拟增 16 行全部写入，另 14 行规则 / 数据行，16 行改为历史，7 行粗钢改值）；`tests/research` 550 passed / 64 skipped / 0 failed（5 个玩具求解排除）。
6. **第 3 节（VERIFIED）：** 四个网络在干净提交 `ef01ceac` 上重建；B5、B8、B11 路线、B13、B16、G2.1、G2.2 与全部 M08b 静态检查通过；6 个变体两遍生成逐字节相同。
7. **第 4 节冒烟（用户 10-21 授权；VERIFIED）：** 2920×3h 前 56 时段、档案 A、TimeLimit 1,750 s，一体化与不互联各 1 次：两次均 optimal（357 / 320 s 求解，峰值 4.5 / 4.1 GiB），GATES_V6 均 **ACCEPTED_LAYER2**，C1 (a)(b)(c) 全过，B6 = +10.05 bn EUR（冒烟口径，无科学含义），账本恒等式、无固定甲烷溢出、LNG 不受上限、报告与导出完整——**通过**。
8. **补充 01（第 137 项，见 §8）：** 中温档拆为 A / B、居民 / 商业 / 农业燃料行锚定（**9 格取 0，醒目见 §8.3**）、`gates_v6.py` SHA 选择修正、各项登记；干净提交 `ec80668f` 上重建四网络，静态检查与变体两遍全过；**再次冒烟未执行，待用户授权**。

> **请审阅端注意（醒目）：**
> - **A. 氢供热无法表示。** technology-data v0.15.0 没有任何氢锅炉 / 氢直燃行；按第 133 项"只允许有条目的技术"，三档都不建氢供热。指令写">400 °C 只允许氢、甲烷、生物质"，两条规则在氢上冲突；现按第 133 项实现，待决定（选项：保持；或另立氢直燃行并登记来源）。
> - **B. 中温档上段无技术覆盖。** DEA 目录：电蒸汽锅炉 1–16 bar（≈ ≤ 200 °C）、燃料蒸汽锅炉 125–300 °C；150–400 °C 档的 200/300–400 °C 段没有对应 technology-data 行，现仍用这些锅炉供整个中温档。
> - **C. 指令写的构建脚本不是构建器。** `build_research_network.py` 现只含 S1 静态校验；网络由 `s2_network.py` 构建（一次构建同时写 2920×3h 与日均 365×24h）。
> - **D. `gates_v6.py accept --build-receipt` 对截断冒烟误取日网络 SHA。** 截断到 56 时段的回执记录 56 个快照，函数据"≤ 365"改用 365×24h 网络 SHA，G2.1 会人为失败；冒烟中改为显式 `--registered-sha256`（2920×3h 网络）。M08a 代码，未改，待定。

## 1. 逐项改动与测试结果

### 1.1 第 1 节：分支与 M11 条目

- worktree `/home/jin/wt_m08b_20261021`、分支 `codex/m08b-demand-20261021`（自 `820c2cae`）；M12 会话用其独立 worktree（`/home/jin/wt_m12_20261021`），本步未触碰。
- `research/STAGE2_PROJECT_LEDGER.md`：M11 草稿原样并入，标题"### M11（无决策项号；用户 10-21 11:52 授权：…）"，插在 M08a 条目之前（提交 `349146be`）。

### 1.2 B1 需求锚定（M08-5；提交 `9ca5d341`、`ef01ceac`）

**数据（`scripts_project/m08b_demand.py`，全部从源表读取）：** C.8 人均 TFEC / 人均电力（ATS 2050）与 D.1 人口来自 `AEO8_2050_BY_COUNTRY.csv`；C.3 ATS 面板来自 `AEO8_2050_ASEAN_TOTALS.csv`；居民电力 29.0 → 33.2 Mtoe（§3.1.3 p.61，唯一常数，已登记）；表 D.2 实际 GDP 由 AEO8 PDF 文字层摘录（p.190，`sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv`）；三份下载件复制入库，SHA256 与注册表登记一致。

**口径：**
- 部门权重 = 各国 2019 部门量（D1 表 `base_2019_mwh`）× ATS 区域部门增长（2022 → 2050），归一化；非能源用途并入工业；11 国同一方法。
- 基础负荷 = ATS 电力 × (居民 + 商业 + 农业及其他 + 交通 2019 既有电力) 份额。交通份额沿用 S4J-1 / S4R 口径（11 国 5.3 TWh；只算建筑 + 农业为 961.6 TWh）。锚值写入新表的电力行，经 `nonindustrial_electricity: table_sectors` 读出（Astar 只给小时形状和节点分摊）。
- 交通 = ATS TFEC × 交通权重；新表交通燃料行 = (交通锚 − 交通电力锚) × 2019 燃料结构，交通合计 = 锚且不与基础负荷重复。服务量换算与电气化沿用现行做法：陆路油当量 × PyPSA-Eur 2050 份额（EV 1 / FCEV 0 / ICE 0）与效率；AEO8 无分国载体效率，载体结构取需求表（C 级）。
- 工业（含 NEU）乘数 = 工业锚 / 2019 工业；用于氨、甲醇、HVC、其余能耗回退子部门、NEU 行、2.B/2.D 与非水泥过程排放；2.A.1 随水泥产量。
- 居民 / 商业 / 农业的燃料行与国际燃料舱不锚定，沿用比率表（未解决项）。

| 国 | 人口 2050（百万） | ATS 电力（TWh） | 基础负荷 新 | 旧（比率表） | S4R 补充 01 | 交通锚 | 旧交通 | 工业乘数 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.50 | 4.46 | 3.40 | 3.17 | 3.39 | 2.10 | 6.64 | 0.541 |
| KH | 20.30 | 22.07 | 12.80 | 17.38 | 12.78 | 82.75 | 97.35 | 4.015 |
| ID | 317.20 | 557.32 | 310.90 | 301.10 | 310.60 | 465.74 | 691.32 | 2.456 |
| LA | 9.80 | 20.90 | 9.02 | 4.92 | 9.01 | 19.65 | 21.04 | 2.669 |
| MY | 41.00 | 276.42 | 117.19 | 139.69 | 117.04 | 241.29 | 587.70 | 1.210 |
| MM | 59.90 | 27.73 | 18.19 | 14.51 | 18.18 | 18.31 | 41.42 | 0.935 |
| PH | 157.90 | 173.85 | 104.07 | 103.73 | 103.98 | 237.97 | 348.56 | 2.228 |
| SG | 5.90 | 66.81 | 34.37 | 41.23 | 34.34 | 14.70 | 41.05 | 0.746 |
| TH | 67.90 | 352.47 | 170.17 | 208.58 | 169.98 | 404.36 | 843.28 | 1.634 |
| TL | 1.89 | 2.32 | 2.32 | 0.90 | 2.32 | 6.79 | 3.07 | 7.634 |
| VN | 107.00 | 506.54 | 184.50 | 197.16 | 184.25 | 206.79 | 309.55 | 3.084 |
| **11 国** | | 2,010.9 | **966.9** | 1,032.4 | 965.9 | **1,700.4** | 2,991.0 | |

与 S4R 补充 01 的偏差：每国都略高，合计基础负荷 +1.05 TWh（+0.11 %）、交通 +2.0 TWh（+0.12 %）。原因：C.3 工业 2022 年取 ATS 面板印值 186 Mtoe（S4R 用 BAS 面板的 185.6），工业增长代理略低，其余部门份额相应略高；TL 人口改用 WPP 原值（1.8892 vs 1.889 M），影响可忽略。校验：10 国居民电力 428.2 TWh vs AEO8 ATS 386.1 TWh（+11 %，与 S4R 相同，登记）。工业乘数 < 1 的国家（BN 0.54、SG 0.75、MM 0.94）是 ATS 人均 TFEC 下降与权重共同作用的结果；TL 7.63 来自其极小的 2019 工业基数（INFERENCE）。

**物理产量（`INDUSTRY_OUTPUT_2050_M08B.csv`）：** G = D.2 实际 GDP 2050 / 2022（VN 3.760；S4R 由 D.6 × D.1 得 3.760）。

| 国 | 水泥基年 2023 | 增长规则 | 人均上限 | **水泥 2050** | 绑定 | 弹性 0.3–0.8 | 粗钢基年 2024 | 增长规则 | 人均上限 | **粗钢 2050** | 绑定 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | 0.32 e | 0.37 | 0.50 | 0.37 | 增长 | 0.35–0.40 | 0 | 0 | 0.30 | 0 | — |
| KH | 8.70 e | 13.62 | 20.30 | 13.62 | 增长 | 11.38–17.82 | 0 | 0 | 12.18 | 0 | — |
| ID | 66.92 | 112.82 | 317.20 | 112.82 | 增长 | 91.55–154.33 | 18.64 | 30.82 | 190.32 | 30.82 | 增长 |
| LA | 7.10 e | 10.84 | 9.80 | 9.80 | 人均 | 9.15–9.80 | 0 | 0 | 5.88 | 0 | — |
| MY | 23.19 | 38.38 | 41.00 | 38.38 | 增长 | 31.37–41.00 | 9.01 | 14.64 | 24.60 | 14.64 | 增长 |
| MM | 8.50 e | 11.98 | 59.90 | 11.98 | 增长 | 10.44–14.72 | 0.50 | 0.70 | 35.94 | 0.70 | 增长 |
| PH | 30.00 e | 55.92 | 157.90 | 55.92 | 增长 | 43.59–81.25 | 1.67 | 3.03 | 94.74 | 3.03 | 增长 |
| SG | 0 | 0 | 5.90 | 0 | — | 0 | 0.26 | 0.36 | 3.54 | 0.36 | 增长 |
| TH | 42.74 e | 66.94 | 67.90 | 66.94 | 增长 | 55.94–67.90 | 4.92 | 7.58 | 40.74 | 7.58 | 增长 |
| TL | 0 | 0 | 1.89 | 0 | — | 0 | 0 | 0 | 1.13 | 0 | — |
| VN | 106.95 | 202.55 | 107.00 | **107.00** | 人均 | 107.00 | 21.97 | 40.64 | 64.20 | **40.64** | 增长 |

（Mt；e = USGS 估计值，登记为 C 级；规划上限只有 VN：钢 70、水泥 150，均不绑定。）

**配置（`configs/research/baseline.yaml`）：** `research.demand.growth_method: ats_anchor`、`base_load_anchor: ats_buildings_agri`、`transport_anchor: ats_service`、`anchor_table`；`research.s2.industry.physical_output_rule: sqrt_gdp_capped` 及 `physical_output_elasticity / _percap_caps / _base_year / _plan_caps`；四张按键选表的映射加 `aeo8_ats_anchor`。旧方法保留为可选值：`growth_method ratio`（BAS 上界）/ `level`、`country_allocation` 变体、`physical_output_rule industry_multiplier`、`other_bucket pypsa_eur_2050`。构建拒绝不一致组合（`s2_layers.demand_anchor_settings`、`physical_output_settings`；产量参数须与生成表时一致，敏感性要重生成表）。

### 1.3 B2 工业有用热与生物质溢出（M08-6）

- **范围：** "其他工业"桶 = UNSD other / construction / mining（对应 JRC "Other industrial sectors"，S3B R2 的 `OTHER_BUCKET`）；其余能耗回退子部门与物理产量部门保留 PyPSA-Eur 2050 路线。
- **拆分（`m08b_heat_bands.py`，C 级）：** JRC-IDEES-2021 EU27 OIS 2019 终端能耗按过程 × 载体：低温 = 低焓热、热 / 蒸汽干燥、热 / 蒸汽驱动冷却；中温 = 蒸汽工艺；高温 = 热加工（燃料直燃）；机械 = 柴油机。份额：煤 3.2 / 21.2 / 75.6 / 0 %；油 5.2 / 18.4 / 42.6 / 33.8 %；气 9.1 / 27.4 / 63.6 / 0 %；生物质 15.1 / 84.9 / 0 / 0 %。热用途 × 0.90 = 有用热；机械部分保留原载体（11 国油 101 TWh）；其他桶电力保留为非热工业用电。
- **母线与链路（`s2_layers.HEAT_BAND_TECH`）：** 每节点三条热母线（低温沿用 `{node} industry heat`，新增 `… medium`、`… high`），映射见 §2。
- **溢出（`biomass_overflow_mode: useful_heat`）：** cap = 潜力；溢出 × 0.90 → 来源温度档（工业：按固定工业生物质的来源档比例——水泥窑燃料进高温，其余路线部门的蒸汽 / 干燥进中温；农业：低温）。删除"溢出转甲烷"主规则与第 115 项 0.98（键 `biomass_overflow_to_methane`、`biomass_overflow_cap_share` 从主配置移除；`methane` 模式只为重现 M08b 前网络保留）。第 36 项贸易规则不变。
- **结果（新主算，11 国）：** 工业固定用电 3,969 → 1,082 TWh；有用热低 150 / 中 688 / 高 900 TWh；固定工业生物质 1,232 → 272 TWh（全部 ≤ 潜力池）；溢出只剩 SG 农业 0.18 TWh。

### 1.4 B3 注册表与测试

- **注册表：** `m08b_data.py`（片段 `m08b.csv` 30 行 + `m08b_corrections.csv` 23 行）与 `s2_0_process_emissions.py`（33 行 `process_emissions_*_2050_ats_anchor_*`）。拟增 v2 的 M08b 16 行全部写入（`industry_steel_2050_VN` 为修改，其余新增）；本步新增规则 / 数据行：`demand_ats_residential_electricity`、`demand_aeo8_d2_real_gdp`、`demand_ats_anchor_table`、`industry_cement_2050_{BN…TH,TL}`（10 行）、`industry_other_bucket_heat_band_shares`、`industry_heat_band_technology_map`。改为历史 16 行：`demand_country_allocation_mode`、`demand_growth_method`、`s4j1_base_load_sectors`、`industry_other_bucket_mode`、`industry_biomass_overflow_to_gas_*`（11）、`s4m_decision_115_biomass_cap_share`；修改 7 行：`industry_steel_2050_{ID,MM,MY,PH,SG,TH,VN}`。注册表 2,121 → 2,184 行，SHA256 `53b051c1…` → `97b27c87…`；DATA_PENDING 46 不变。
- **测试：** 新增 `test_m08b_demand.py`（11 国活动量与锚 ≤ 1e-6，锚值从源表独立复算；基础负荷非负；VN 水泥 107.0、粗钢 40.64；每国 = min(增长, 人均, 规划) 且 ≤ 人均上限、规划不抬高；s3_0 表用规则产量；配置组合校验；注册表行）与 `test_m08b_heat.py`（三档之和 = 原能耗 × 0.90，从 2019 桶表独立复算；固定生物质 ≤ 潜力池；映射只用 v0.15.0 行、无氢、高温档无电输入、热泵只在低温；在合成两节点网络上建三档后，高温档没有来自电力 / 氢母线的链路；单档模式网络与 M08b 前完全相同）。改 2 处断言旧主算的测试（`test_s3b_r1.py:23`、`test_s3b_r2.py:31`，旧值改用副本断言）。
- **全量：** `tests/research` 550 passed、64 skipped、0 failed，5 个玩具求解用例排除（`evidence/M08B_FULL_TESTS_B3.txt`）。
- **数据链逐字节核对：** 重跑 s3_0 / s2b / s2_0 后，所有旧模式的工业汇总表与属地表逐字节不变；`INDUSTRY_2050_GAPS.csv`、`INDUSTRY_2050_OTHER_BUCKET.csv` 只追加新模式行；`industry_cement_clinker_ratio` 行记录的成本表 SHA256 由 M08a A1 前的旧值刷新为当前值（数值不变）。

## 2. 温度档映射表

规则（第 133 项）：每档只用 technology-data v0.15.0 有条目的技术；热泵只在低温档；>400 °C 档只有覆盖该温度的电加热行时才允许电加热；氢 / 甲烷 / 生物质中只建有条目的。代码 `s2_layers.HEAT_BAND_TECH`，表 `research_inputs/demand_v5/INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv`，注册表 `industry_heat_band_technology_map`；静态检查确认网络中每档的链路载体集合与此表相同（§3）。

| 温度档 | technology-data 行 | 链路载体 | 输入 | 效率 | 投资（EUR2020/kW） | FOM（%/a） | VOM（EUR2020/MWh） | 寿命 | 温度依据（DEA 工业过程热目录） |
|---|---|---|---|---|---|---|---|---|---|
| 低 <150 °C | electric boiler steam | industry electric boiler | 电 | 0.99 | 70.49 | 1.31 | 0.79 | 25 | 310.1：1–16 bar，典型 8 bar / 175 °C |
| 低 | industrial heat pump high temperature | industry heat pump | 电 | COP 3.2 | 845.88 | 0.09 | 3.14 | 20 | 302.b：≤150 °C（只用于低温档） |
| 低 | gas boiler steam | industry gas boiler | 甲烷 | 0.94 | 45.77 | 3.74 | 1.01 | 25 | 311.1c：蒸汽 125–300 °C |
| 低 | solid biomass boiler steam（+CC） | industry biomass boiler（CC） | 生物质 | 0.90 | 540.12 | 6.28 | 2.87 | 25 | 311.1e：蒸汽 125–300 °C |
| 中 150–400 °C | electric boiler steam | industry electric boiler | 电 | 0.99 | 70.49 | 1.31 | 0.79 | 25 | ≈ ≤200 °C（16 bar 饱和）；上段无覆盖（醒目 B） |
| 中 | gas boiler steam | industry gas boiler | 甲烷 | 0.94 | 45.77 | 3.74 | 1.01 | 25 | 125–300 °C；300–400 °C 无覆盖（醒目 B） |
| 中 | solid biomass boiler steam（+CC） | industry biomass boiler（CC） | 生物质 | 0.90 | 540.12 | 6.28 | 2.87 | 25 | 同上 |
| 高 >400 °C | direct firing gas | industry direct firing gas | 甲烷 | 1.00 | 15.10 | 1.03 | 0.28 | 15 | 312.a：400–800 °C 与 >800–1,600 °C |
| 高 | direct firing solid fuels（+CC） | industry direct firing biomass（CC） | 生物质 | 1.00 | 221.54 | 1.41 | 0.34 | 15 | 312.b：煤 / 生物质多燃料燃烧器，高温过程 |
| 高 | （无） | — | 电 | — | — | — | — | — | DEA 2026 版有电直燃 400–800 °C，但 v0.15.0 无对应行 → 不建 |
| 任一档 | （无） | — | 氢 | — | — | — | — | — | v0.15.0 无氢锅炉 / 氢直燃行 → 不建（醒目 A） |

注：投资、VOM 为模型所用成本层值（v0.15.0 costs_2050，经 EEA HICP 回算为 EUR2020，系数 0.79533）；FOM、寿命为原表值；CC 变体另加 biomass boiler capture × CO₂ 强度 × 捕集率，与原低温档规则相同。温度依据文本取自 DEA《Technology Data for Industrial Process Heat》2026 版（version 0006，ens.dk）；v0.15.0 数据来自该目录较早版本的数据表，行名编号沿用当时编号。中、低温档的电 / 燃气 / 生物质锅炉与低温档共用载体名（链路名带 ` medium` 后缀），成本层与 WACC 映射不需新键；高温档新增 3 个载体，已登记到 `s4c_layers.CARRIER_COST_ROWS`、`s4m_cost_breakdown`、捕集载体列表与 B11 母线字典。

## 3. 修正前后对比（第 3 节）

### 3.1 重建

- 构建器 `scripts_project/s2_network.py`（醒目 C），提交 `ef01ceac`，工作树干净（dirty 0），`PYTHONHASHSEED=0`；两次构建（integrated / disconnected），每次同时写 2920×3h 与其精确日均 365×24h，共四个网络（NZE 不再构建）。每次约 70 s、峰值 0.78 GB（远低于 1 h / 20 GB 阈值）。输入（集成契约、分配数组、底网）经临时符号链接指向主检出 `results_project`，输出在主检出 `results_project/m08b/builds/`（不入库）。
- 两次构建都是 `S2_SCENARIO_BUILT_STATIC_PASS`；构建期锚值核对（基础负荷、交通，11 国，≤ 1e-9）内置于 `s2_layers.add_demand_layer`。

### 3.2 变体生成测试（`m08a_variants.py`）

| 变体 | 基础网络 | 输出网络 SHA256（两遍相同） |
|---|---|---|
| 保留存量（keep_stock_no_new） | integrated | `01da0ad6…850a` |
| b1（不互联禁东盟内 CO₂ 船运） | disconnected | `54ac22a2…2919` |
| 去掉 VN | integrated | `0f6a5bd3…307a` |
| 去掉 TH | integrated | `b0900474…060e` |
| 去掉 LA | integrated | `9f96479e…5a97` |
| 分国 WACC | integrated | `5c7bc9d3…e3d5` |

每个变体生成两遍（不同输出目录），网络逐字节相同；回执只有 `output.path` 不同（`evidence/M08B_VARIANT_RECEIPTS.csv`、`M08B_VARIANT_RECEIPT_DIFFS.json`）。每遍约 4 s、0.7 GB。变体只作生成测试，未提交。

### 3.3 静态检查（`scripts_project/m08b_static.py`，`evidence/M08B_STATIC_CHECKS.json`）

| 检查 | integrated | disconnected |
|---|---|---|
| B5 单一开关（两情景配置只差 scenario / cross_border） | 通过 | — |
| B8 需求守恒（负荷 = 账本部门合计，无负负荷） | 通过 | 通过 |
| B11 供给路线（每个有负荷的终端母线 ≥ 2 条供给；含新中 / 高温母线） | 通过 | 通过 |
| B13 区域外进口单向 | 通过 | 通过 |
| B16 两情景进口价相同 | 通过 | — |
| G2.1 网络 SHA256 = 构建回执 + 回读组件一致 | 通过 | 通过 |
| G2.2 配置子集哈希 = 当前配置 | 通过 | 通过 |
| G2.3 导出完整性 | 需求解（见 §5） | 同左 |
| 365×24h = 2920×3h 日均（各负荷年能量相等） | 通过 | 通过 |
| 需求与锚表逐国一致（基础负荷 ≤ 1e-6；账本 11 国核对记录） | 通过 | 通过 |
| 无负负荷 | 通过 | 通过 |
| 温度档映射与 §2 一致（高温档无电 / 氢输入，热泵只在低温档） | 通过 | 通过 |
| 无固定甲烷溢出需求 | 通过 | 通过 |
| 固定生物质 ≤ 潜力池（11 国） | 通过 | 通过 |
| LNG 无上限（16 台 p_nom_max = inf，8,020.43 EUR2020/MW/a） | 通过 | 通过 |
| VN 封存上限 106.07 Mt/a（Store 与 meta 一致） | 通过 | 通过 |
| 地面光伏上限 = 旧值 × 1.1087（289 台逐台） | 通过 | 通过 |
| 海上风新规则（pypsa_eur_v2025_07；漂浮式 207 台） | 通过 | 通过 |
| B11 完整性（S1 时期"每节点有全部 S1 技术"） | **未通过** | **未通过** |

B11 完整性：缺 287 项（地热 / 径流水电要求每节点都有）；同一检查在修正前 S4M-3 网络上同样未通过，缺失项数完全相同（`scripts/m08b_b11_old.py`）——S4A 起候选改为按资源场址，此检查已过时，与 M08b 无关（VERIFIED）。指令中的"B11 路线"即供给路线检查，已通过。

### 3.4 修正前后对比（integrated；disconnected 的需求列逐国相同；修正前 = S4M-3 网络 `f50c8850`，即 S4N / S4O 云端包所用网络）

| 国 | 终端需求 前 | 后 | 基础电力 前 | 后 | 固定电力 前 | 后 | 水泥 前 | 后 | 粗钢 前 | 后 | 光伏上限 前 | 后 | 封存上限 前 | 后 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | 19.5 | 9.1 | 3.2 | 3.4 | 7.4 | 4.4 | 0.6 | 0.4 | 0 | 0 | 1.4 | 1.6 | 371.6 | 371.6 |
| KH | 125.9 | 89.8 | 17.4 | 12.8 | 58.1 | 48.2 | 41.7 | 13.6 | 0 | 0 | 359.4 | 398.4 | 1.7 | 1.8 |
| ID | 3,963.6 | 2,774.9 | 301.1 | 310.9 | 2,274.2 | 688.6 | 312.6 | 112.8 | 28.3 | 30.8 | 859.0 | 952.4 | 1,025.5 | 1,025.5 |
| LA | 38.5 | 35.1 | 4.9 | 9.0 | 18.4 | 22.6 | 17.7 | 9.8 | 0 | 0 | 119.3 | 132.3 | 0 | 0 |
| MY | 1,399.9 | 685.2 | 139.7 | 117.2 | 742.8 | 298.6 | 56.6 | 38.4 | 20.0 | 14.6 | 77.9 | 86.4 | 2,575.5 | 2,575.5 |
| MM | 197.2 | 125.8 | 14.5 | 18.2 | 115.6 | 40.9 | 12.9 | 12.0 | 0.7 | 0.7 | 825.6 | 915.3 | 0 | 0 |
| PH | 600.4 | 457.7 | 103.7 | 104.1 | 299.1 | 228.6 | 107.0 | 55.9 | 6.2 | 3.0 | 298.9 | 331.4 | 446.0 | 1.3 |
| SG | 266.8 | 116.4 | 41.2 | 34.4 | 152.6 | 66.1 | 0 | 0 | 1.6 | 0.4 | 0.4 | 0.5 | 0 | 0 |
| TH | 2,000.4 | 1,088.4 | 208.6 | 170.2 | 946.8 | 515.8 | 160.3 | 66.9 | 14.4 | 7.6 | 1,108.5 | 1,229.0 | 320.5 | 320.5 |
| TL | 2.1 | 4.8 | 0.9 | 2.3 | 1.8 | 4.4 | 0 | 0 | 0 | 0 | 9.6 | 10.7 | 5.0 | 0 |
| VN | 2,237.0 | 1,310.4 | 197.2 | 184.5 | 1,253.2 | 643.2 | 581.0 | 107.0 | 80.3 | 40.6 | 411.3 | 456.0 | 236.0 | 106.1 |
| **11 国** | **10,851** | **6,698** | **1,032** | **967** | **5,870** | **2,562** | **1,290** | **417** | **151.5** | **97.8** | **4,071** | **4,514** | **4,982** | **4,402** |

单位：需求 TWh/a，产量 Mt/a，光伏 GW，封存 Mt CO₂/a。定义（`evidence/BUILD_INPUT_CHANGES_M08B.json`）：终端需求 = 该国全部负荷（含有用热、原料、氢、氨 / 甲醇；区域池中的燃料舱不计），口径混合，只作前后对比；基础电力 = Astar 负荷；固定电力 = 基础 + 工业电 + 农机电 + 陆路 EV（S4R 定义）；光伏上限 = 地面光伏候选 p_nom_max 合计（屋顶 860 GW 不变）；封存上限 = 国家 `co2 sequestered` Store 的年上限。产量"前"为比率表主表，"后"为 ATS 锚 + 产量规则。PH / TL / VN 封存与 LNG 的变化来自 M08a A4 / A5，光伏 × 1.1087 与海上风来自 M08a A6，均是首次进入重建网络。

补充（integrated，11 国，TWh）：工业固定用电 3,969 → 1,082；陆路 EV 811 → 455；固定燃气终端 1,069 → 292；固定生物质 1,232 → 272；新增有用热中温 688、高温 900（低温 150）。

## 4. 网络大小与 SHA256

| 网络 | 分辨率 | 快照 | 大小（B） | MiB | SHA256 |
|---|---|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | 2920×3h | 2,920 | 63,426,039 | 60.49 | `cf189f3984d1e29cac30770c598a3bf7fa72a23537e70810cddaa247ccb15668` |
| `integrated_365_24h_unsolved.nc` | 365×24h | 365 | 30,844,832 | 29.42 | `d9fab9aae1477cf059ca6be9d377288789f31f9bb88485dbdb959f5ddc899ef1` |
| `disconnected_2920_3h_unsolved.nc` | 2920×3h | 2,920 | 62,754,113 | 59.85 | `af9f18816a4037928a372ff3e7d2175c8a742ff605241b9630713b5c1487e64e` |
| `disconnected_365_24h_unsolved.nc` | 365×24h | 365 | 30,172,906 | 28.78 | `7234216e5338322a453d488051fbb818afe904ce2829f4ab8fb16541bdc0dbc0` |

位置：主检出 `results_project/m08b/builds/<scenario>/`（不入库）；四个文件合计 186.4 MB。构建回执 `evidence/M08B_{integrated,disconnected}_BUILD_RECEIPT.json`。传输方案：按以往实测上行速率 36 KB/s（AutoDL 克隆机）至 0.16 MB/s（S4N 链路），四个网络约 20 分钟–1.4 小时（INFERENCE，取决于实例与线路；只传 2920×3h 或只传 365×24h 可相应减半或更少）；变体在云端由 `m08a_variants.py` 从基础网络生成（每个约 4 s），不需上传。

## 5. 冒烟测试结果（第 4 节）

**授权与前提：** 用户 2026-10-21 授权（"2920×3h 前 56 时段，一体化与不互联各 1 次，档案 A，TimeLimit 1,750 s"，并确认云端无运行）。开始前本机无 Gurobi / 求解进程，上次本机 Gurobi 会话在 10-19 / 10-20，间隔远超 5 分钟。许可只经 `GRB_LICENSE_FILE` 供求解进程使用（未读取、未复制）；违反量分析、C1 与 GATES_V6 在无许可变量的环境中运行。

**做法（`scripts/m08b_smoke.sh`，提交 `7381e91d`、工作树干净）：** `s2_solve.py --truncate 56 --label SMOKE_TEST_ONLY --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750`，每次在独立进程组中运行、墙钟 1,800 s 止损；串行，两次求解间隔 333 s；之后 `l23_violation_analysis.py`、`s4o_c1_precision.py run`、本批参照（不互联 − 一体化账本）+ 重评、`gates_v6.py accept`（显式 `--registered-sha256` = 构建回执中的 2920×3h 网络，见醒目 D）。未重试、未改参数。

| 项 | integrated | disconnected |
|---|---|---|
| 终止状态 | optimal | optimal |
| 求解时间（Gurobi）/ 全程 | 357 s / 422 s | 320 s / 366 s |
| 峰值内存 | 4.54 GiB | 4.07 GiB |
| LP 规模（列 / 行） | 684,545 / 1,518,001 | 660,895 / 1,464,427 |
| 目标值（EUR2020，56 时段年化权重） | 327.019 bn | 337.070 bn |
| C1 分级 | layer1_plus_nodal_price_settlement，(a)(b)(c) 全过；(a) 相对 2.0e-11 | 同左；(a) 相对 3.7e-11 |
| GATES_V6 标签 | **ACCEPTED_LAYER2** | **ACCEPTED_LAYER2** |
| G2.1 / G2.2 / G2.3 | 通过（SHA256 相等、回读精确） / 通过 / 通过（解维度 = LP） | 同左 |
| 诊断 D1–D13、D15、D16 | 全部在预算内（D2 对偶符号 5.1e-7，预算 1e-5） | 全部在预算内 |
| 账本恒等式（V5_GATES B16_LEDGER） | 通过 | 通过 |
| 固定甲烷溢出负荷 | 0 | 0 |
| LNG 码头（16 台，p_nom_max = inf） | p_nom_opt 合计 134.5 GW，有限 | 161.4 GW，有限 |
| 报告与导出文件 | 完整 | 完整 |

**B6** = 337.070 − 327.019 = **+10.05 bn EUR（相对 2.98 %）> 0**。冒烟只有 56 个 3 小时时段（7 天）按年化权重放大，数值没有科学含义，只说明两个情景都可解、结构与门槛正常；修正前同口径冒烟（S4M-2 / S4Q）目标值约 648 bn，下降主要来自需求锚定（INFERENCE）。

**判定（`scripts_project/m08b_smoke_eval.py` → `evidence/M08B_SMOKE_RESULT.json`）：** 第 4 节六项通过标准两次运行全部满足——**通过**。轻量证据在 `evidence/smoke/`（回执、门槛、V6、C1、账本、导出清单；不含求解日志与 stdout / stderr），复制件许可特征串扫描无命中。完整求解输出在主检出 `results_project/m08b/smoke/`（不入库）。

## 6. 仍未解决的项

1. **氢供热（醒目 A）：** 三档均无氢选项；若要允许，需另立有出处的氢锅炉 / 氢直燃成本行并登记（非 technology-data v0.15.0）。
2. **中温档上段覆盖（醒目 B）：** 200/300–400 °C 段没有专门技术行；可选：维持现状、把蒸汽工艺的一部分改归高温档、或为中温档加直燃。
3. **`gates_v6.py accept --build-receipt` 对截断运行的 SHA 选择（醒目 D）：** 建议把判断条件从"快照 ≤ 365"改为 `truncated_to` 为空且快照 = 365；本步未改。
4. **未锚定的燃料行：** 居民 / 商业 / 农业燃料（烹饪 LPG、生物质等）与国际燃料舱仍用比率表（BAS 增长）；是否也锚到 ATS（按部门 TFEC 锚 − 电力锚，可能出现负值）待定。
5. **交通载体效率：** AEO8 无分国 ATS 载体效率，服务量折算用需求表载体结构 + 现行 PyPSA-Eur 2050 份额（C 级）。
6. **其他桶机械用能：** 柴油机部分（11 国油 101 TWh，ID 65）保留为固定油需求，需由合成 / 生物燃料或 DAC 抵消；是否改为电气化（如按农机规则）待定。其他桶电力全部按非热用电保留（JRC 中热用电份额小）。
7. **工业乘数 < 1：** BN 0.54、SG 0.75、MM 0.94（ATS 人均 TFEC 下降所致）；TL 7.63（2019 工业基数极小）。规则 11 国一致，数值可接受与否待审。
8. **基础负荷口径：** 含 2019 交通既有电力 5.3 TWh（与 S4J-1 / S4R 966 TWh 一致）；指令原文只写建筑 + 农业（961.6 TWh）。
9. **B11 完整性检查过时：** S1 时期的逐节点技术完整性检查在 S4M-3 与 M08b 网络上同样失败（287 项），建议停用或改为按场址候选的版本。
10. **云端部署包：** S4O 包中的 `make_package.sh` 仍在清单文字里写 `biomass_overflow_cap_share 0.98`；第三批（M10）需按 M08b 头重新打包。
11. **注册表文档行：** M08a 遗留"派生货币文档行未重算"（M08a §5 第 9 项）未在本步处理。
12. **PyPSA-Eur 原规则对照：** 有用热温度分档是对 PyPSA-Eur 的偏离（S4R R1.4 已登记理由）；温度分布用 EU27 JRC-IDEES，东盟本地分布 DATA_PENDING（替代办法：按 ERIA LCET-CN 工业热 / 电份额校准）。

## 7. 提交与文件

**提交（分支 `codex/m08b-demand-20261021`，自 `820c2cae`）：** `349146be`（第 1 节，M11 条目）→ `9ca5d341`（B1/B2 数据表）→ `ef01ceac`（构建接入、注册表、测试；网络在此提交上构建）→ `7381e91d`（第 3 节静态检查与对比；冒烟在此提交上运行）→ `f0db44f2`（冒烟、报告、台账）→ 收尾提交（PR 链接、审阅 ZIP 清单）。draft PR：[cyc292cycjin-oss/SGP-ESE5004-Stage2#47](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/47)（base `codex/m08a-corrections-20261021`，叠在 #45 上）。

**代码（`scripts_project/`）：** 新增 `m08b_demand.py`、`m08b_heat_bands.py`、`m08b_data.py`、`m08b_static.py`、`m08b_smoke_eval.py`；修改 `s2_layers.py`、`s2_network.py`、`s3_0_industry.py`、`s2b_feedstock.py`、`s2_0_process_emissions.py`、`d1_registry.py`、`s4c_layers.py`、`s4m_cost_breakdown.py`、`s2_solve.py`（捕集载体列表）、`s3_7_results_summary.py`、`v5/v5_gates.py`；`configs/research/baseline.yaml`；测试 `tests/research/test_m08b_demand.py`、`test_m08b_heat.py`，改 `test_s3b_r1.py`、`test_s3b_r2.py`。

**数据（`research_inputs/`）：** `demand_v5/`：`DEMAND_ANCHOR_AEO8_ATS.csv`、`DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv`、`DEMAND_ANCHOR_M08B_EVIDENCE.json`、`INDUSTRY_OUTPUT_{BASE,2050}_M08B.csv`、`INDUSTRY_OUTPUT_PLAN_CAPS.csv`、`INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.{csv,json}`、`INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv`、`INDUSTRY_2050_*aeo8_ats_anchor*`、`*_OTHER_USEFUL_HEAT_BANDS.csv`、`sources/m08b/`（三份下载件 + D.2 摘录）；`registry_v5/`：`FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_anchor.csv`、片段 `m08b.csv` / `m08b_corrections.csv` / `process_emissions.csv`、`DATA_REGISTRY.csv`。

**交付目录 `work/p1_m08b_20261021/`（镜像到 `research/06_scope_redesign/p1_m08b_20261021/`）：** 本报告、`M08B_PROGRESS.md`、指令与 SHA256、`evidence/`（静态检查、对比、网络文件、变体回执、构建回执、冒烟结果与轻量证据、全量测试日志、温度档映射）、`scripts/`（WSL 运行脚本与探查脚本）、审阅 ZIP `M08B_REVIEW.zip`（逐成员 SHA256 + CRC 清单 `M08B_REVIEW_MANIFEST.csv`）。

**未入库（主检出 `results_project/m08b/`）：** `builds/`（四个网络 186.4 MB）、`variants/`（12 个变体网络）、`smoke/`（求解输出）、`trial1/`（试构建）。

## 8. 补充 01（第 137 项）：审阅决定、中温档拆分、燃料行锚定、重建（再次冒烟待授权）

**范围：** `M08B_SUPPLEMENT_01.md` v1，SHA256 `7a4e532e2f79fc00581d56057b83c8c1f5ed2eb8faa44d8e8ebe63f65e08d538`，与 `M08B_SUPPLEMENT_01_SHA256.txt` 一致（2026-10-21 核对）。同一分支 `codex/m08b-demand-20261021` 与 worktree；未连云；未调用 Gurobi（单元测试照旧排除 5 个玩具求解）。提交：`c2df3c75`（D 项）→ `ec80668f`（第 1–3 节，数据链与注册表一并重生成，故合为一个提交）→ 第 4 节证据与本节（收尾提交）。

**醒目：**
- **燃料行锚定后 9 格取 0**（8 格为负值，1 格无 2019 燃料行）：BN 居民 / 商业，MY 居民 / 商业，SG 居民 / 商业 / 农业，TH 商业为负；TL 商业为正但无载体结构。负值合计 −63.30 TWh，即这 8 格的部门总量取电力锚后，国家 TFEC 比 ATS TFEC 锚高 63.30 TWh（§8.3）。按补充 01 §3.3 取 0 并登记，未用其他来源填补；是否接受交审阅端判断。
- **第一轮的两处遗漏已补：** `INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv` 被 `*.csv` 忽略、首轮未入库（注册表行已引用其 SHA），本轮已提交；首轮报告 §6 第 12 项称"东盟温度分布 DATA_PENDING 已登记"，但注册表中并无该行，本轮补登（DATA_PENDING 46 → 47）。

### 8.1 第 1 节各项落实情况

| 项 | 决定 | 落实（VERIFIED，除另注） |
|---|---|---|
| A 氢供热 | 保持不建，登记局限与偏差方向 | 模型未改；注册表 `industry_heat_hydrogen_not_represented`：氢只能经合成甲烷间接进入工业供热，多一道转换损失，氢的作用可能被低估；与 PyPSA-Eur 一致 |
| B 中温档上段 | 拆分中温档 | §8.2 |
| C 构建脚本名称 | 报告与注册表更正 | 注册表 `network_builder_script` = `scripts_project/s2_network.py`（`build_research_network.py` 只含 S1 校验）；本报告 §3.1 已按此写 |
| D `gates_v6.py` SHA 选择 | 修正 + 单元测试 | `registered_sha_from_build_receipt()`：只有 `truncated_to` 为空且快照 = 365 才取日网络 SHA，其余（截断 56 时段、截断到 365 的探针、2920×3h）都取 2920×3h 网络；`test_m08b_s01.py` 7 种组合；M08a 批量运行测试不受影响（提交 `c2df3c75`） |
| 4 未锚定燃料行 | 居民 / 商业 / 农业锚到 ATS；燃料舱维持 UNSD 2019 | §8.3；燃料舱行仍为 2019 常量（测试断言锚定表中唯一未改动的部门是 InternationalBunkers） |
| 5 交通载体效率 | 维持（C 级），登记 | `demand_transport_carrier_efficiency_assumption`（C） |
| 6 其他桶柴油机 | 维持为固定油需求（C），登记 | `industry_other_bucket_mechanical_fuel`（C，标志行：无有出处的敏感性区间）；11 国 101.1 TWh 油，其中 ID 64.7 |
| 7 工业乘数 < 1 | 接受；列 TL 绝对量 | TL：人口 1.889 M，ATS TFEC 11.47 TWh、电力 2.32 TWh；工业锚 1.07 TWh 全部落在非能源用途（沥青 0.93、润滑油 0.15 TWh；2019 为 0.14 TWh × 乘数 7.63），工业部门本身为 0，网络中无工业电 / 热负荷；居民燃料 0.61 TWh（2019 生物质 0.21 × 2.95），农业燃料 0.55 TWh（2019 油 0.012 × 45.9）；TL 网络终端需求合计 5.24 TWh，占 11 国 6,423 TWh 的 0.08 %——数值很小 |
| 8 基础负荷含交通电力 | 核对是否重复 | **未重复，保留并写明**：交通燃料行 = 交通锚 − 交通电力锚，陆路 EV / FCEV / ICE 只由非电力的陆路行折算（`LAND_TRANSPORT_ACCOUNTS`，载体 ≠ 电力），交通电力行（账户 `UNSD_electricity_Transport`，11 国 5.31 TWh）只在基础负荷中计一次；逐国测试交通电力行 = 交通电力锚、燃料行 = 锚 − 电力锚（`demand_transport_electricity_counted_once`） |
| 9 B11 完整性检查过时 | 停用，登记理由，以路线检查替代 | `m08b_static.py` 不再调用 `gate_b11_completeness`，证据 JSON 记为 retired；注册表 `gate_b11_completeness_retired`；`s2_solve.py` 的 B11 一直是供给路线检查；`s1_solve.py` 保留旧检查只用于 S1 网络 |
| 10 云端部署包 | 留给 M09 / M10 | 本步未做 |
| 11 注册表派生货币文档行 | 本步重算，测试覆盖 | 34 行仍引用 M08a A1 前的成本层文件（`708daeba…` / `17b1b230…`，即现 `_ea20gdp` 变体）：10 行货币值按现行层重算（氨 / 甲醇 technology-data 的 investment / VOM 8 行，燃气管道陆上 91.37 → 87.22、海底 125.49 → 119.79 EUR2020/MW/km，均 × 0.9546 = 0.795333 / 0.833196），20 行非货币值不变、只换 SHA，4 行标志 / 方法行只换 SHA；先核对旧值等于旧层值再替换（`m08b_data.s01_cost_doc_rows`，清单 `evidence/M08B_S01_COST_DOC_ROWS.txt`）；测试：注册表中再无引用旧层 SHA 的行，引用现行层的行数值等于现行层。构建期价格一直取成本层，网络不受影响 |
| 12 温度分布用 EU27 | 维持，DATA_PENDING | 注册表 `industry_heat_band_asean_distribution`（DATA_PENDING；替代办法：按 ERIA LCET-CN 各国工业热 / 电份额校准）——首轮报告称已登记，实际未登记，本轮补登 |

**注册表：** 2,184 → 2,194 行（`97b27c87…` → `4c59adb7…`）；新增 10 行（上表 A、5、6、8、9、12、C 七行 + `industry_heat_band_medium_split`、`demand_sector_fuel_anchor_rule`、`demand_sector_fuel_anchor_zeroed`）；改写 M08b 自有行的说明（四档、燃料锚定）；修正片段 `m08b_corrections.csv` 23 → 57 行（+34 行第 11 项）。DATA_PENDING 46 → 47。

**测试：** `tests/research` 557 passed、64 skipped、0 failed，5 个玩具求解照旧排除（首轮 550 passed；新增 `test_m08b_s01.py` 5 项及 `test_m08b_heat.py` / `test_m08b_demand.py` 各 1 项；`evidence/M08B_S01_FULL_TESTS.txt`）。JRC-IDEES 工作簿是被忽略的输入，`m08b_tests.sh` 现指向主检出副本，使 200 °C 敏感性重算测试不被跳过。

### 8.2 中温档拆分（补充 01 §2）

- **分档：** 低 < 150 °C；中温 A 150–200 °C；中温 B 200–400 °C；高 > 400 °C。JRC-IDEES-2021 工作簿只有 `*_fec / *_ued / *_emi` 表，没有温度分布表；首轮的"温度分布"是过程 → 温度档映射，蒸汽工艺整体属 150–400 °C，没有 200 °C 断点 → 按 §2.1 在 150–400 °C 内按温度线性插值：中温 A = (200 − 150) / (400 − 150) = **0.2** × 中温份额，中温 B = 0.8；四种载体同一系数；固定工业生物质中属中温的部分（溢出来源档）也按此拆分。C 级，注册表 `industry_heat_band_medium_split`（敏感性 0.1–0.3）。配置键 `research.s2.industry.heat_band_medium_a_fraction: 0.2`，构建时与温度档表核对，不一致即拒绝（敏感性需重生成表）。
- **份额（JRC-IDEES OIS 2019）：** 煤 低 3.2 / 中 A 4.2 / 中 B 17.0 / 高 75.6 %；油 5.2 / 3.7 / 14.7 / 42.6 %（机械 33.8 %）；气 9.1 / 5.5 / 21.9 / 63.6 %；生物质 15.0 / 17.0 / 68.0 / 0 %。
- **技术映射（只用 technology-data v0.15.0 有条目的行；`INDUSTRY_HEAT_BAND_TECHNOLOGY_MAP.csv`、`s2_layers.HEAT_BAND_TECH`、注册表 `industry_heat_band_technology_map`）：**

| 温度档 | technology-data 行 | 链路载体 | 输入 | 温度依据 |
|---|---|---|---|---|
| 中温 A 150–200 °C | electric boiler steam | industry electric boiler | 电 | DEA 310.1：1–16 bar（16 bar 饱和约 200 °C），典型 8 bar / 175 °C → 只到中温 A |
| 中温 A | gas boiler steam | industry gas boiler | 甲烷 | DEA 311.1c：蒸汽 125–300 °C |
| 中温 A | solid biomass boiler steam（+CC） | industry biomass boiler（CC） | 生物质 | DEA 311.1e：蒸汽 125–300 °C |
| 中温 B 200–400 °C | gas boiler steam | industry gas boiler | 甲烷 | 覆盖 200–300 °C 段 |
| 中温 B | direct firing gas | industry direct firing gas | 甲烷 | 300–400 °C 段无蒸汽行覆盖；燃料燃烧可达该温度，取直燃行成本作代表（C 级） |
| 中温 B | direct firing solid fuels（+CC） | industry direct firing biomass（CC） | 生物质 | 同上（C 级） |
| 中温 B | （无电加热） | — | 电 | 没有覆盖 > 200 °C 的电加热行 |

  低温、高温两档与 §2 相同。链路名后缀 ` medium A` / ` medium B`，链路载体沿用原载体名（成本层、WACC、成本分解不需新键）。中温 B 按补充 01 所列只建上述三类，**未建固体生物质蒸汽锅炉**（DEA 311.1e 也覆盖到 300 °C）；生物质只经固体燃料直燃行进入中温 B——如需加入，请审阅端决定。
- **结果（integrated 与 disconnected 相同，11 国）：** 中温 A 137.5、中温 B 550.1 TWh（合计 687.6 = 首轮中温），高温 900.0、低温 149.8 TWh；敏感性 0.1 / 0.3 时中温 A 为 68.8 / 206.3 TWh。网络中中温 B 与高温母线的输入只有甲烷与固体生物质（静态检查 VERIFIED）。
- **INFERENCE：** DEA 写工业蒸汽典型 8 bar / 175 °C，线性插值可能使 200 °C 以下（可电气化）部分偏少；敏感性上限 0.3 可部分反映，东盟分档数据 DATA_PENDING。

### 8.3 居民、商业、农业燃料行的 ATS 锚定（补充 01 §3）

- **做法（`m08b_demand.py`）：** 部门燃料 = ATS 部门 TFEC 锚（ATS 国家 TFEC × 与交通相同的归一化 TFEC 权重：2019 部门 TFEC × C.3 ATS 增长）− 部门电力锚（`demand_base_load_rule` 中的同一部门锚）；部门内各燃料行按 2019 载体结构等比例缩放（比率表每部门只有一个乘数，故其载体结构就是 2019 结构）；负值取 0 并登记；有正锚但部门无任何 2019 燃料行的格无法分配载体，也记 0 并列出。构建期逐国逐部门核对燃料行 = 锚（≤ 1e-9），失败即拒绝构建。
- **11 国合计（TWh）：** 居民 673.7 → **435.3**，商业 286.7 → **154.4**，农业及其他 320.5 → **281.6**（前 = 比率表，BAS 增长）。
- **取 0 的格（注册表 `demand_sector_fuel_anchor_zeroed`）：**

| 国 | 部门 | 取 0 前的锚（TWh） | 原因 |
|---|---|---|---|
| BN | 居民 | −0.705 | 负值 |
| BN | 商业 | −1.469 | 负值 |
| MY | 居民 | −12.358 | 负值 |
| MY | 商业 | −22.875 | 负值 |
| SG | 居民 | −3.798 | 负值 |
| SG | 商业 | −11.067 | 负值 |
| SG | 农业及其他 | −0.124 | 负值 |
| TH | 商业 | −10.908 | 负值 |
| TL | 商业 | +0.127 | 2019 无燃料行（无载体结构） |

  负值格的部门总量取电力锚后，国家 TFEC 比 ATS TFEC 锚多 63.30 TWh（8 格合计）；"锚定后总量 = ATS 锚"只在其余格成立（测试逐格核对）。**INFERENCE（机制）：** C.3 中 ATS 居民 TFEC 下降（0.84 ×，传统生物质退出）而居民电力上升（1.14 ×）；BN、MY、SG、TH 的 2019 部门燃料占比小、电力占比大，部门 TFEC 权重小于电力权重。
- **连带变化（VERIFIED，网络）：** 固定燃气终端 292.0 → 285.1、固定生物质 272.0 → 275.9 TWh；农业机械电随农业油变化；**主算生物质溢出降为 0**（首轮唯一的溢出 SG 农业 0.18 TWh 随 SG 农业燃料取 0 消失）。

### 8.4 重建、静态检查、变体与对比（补充 01 §4.1、4.2、4.4）

- **重建：** 干净提交 `ec80668f`（dirty 0），`PYTHONHASHSEED=0`，`s2_network.py` 两次构建写出四个网络到主检出 `results_project/m08b/builds_s01/`（首轮 `builds/` 保留，供对比与首轮冒烟证据引用）；各约 73 s、峰值 0.78 GB；两次均 `S2_SCENARIO_BUILT_STATIC_PASS`。提交前在同一代码上的试构建（`trial_s01/`）与正式构建的 integrated 2920×3h 网络逐字节相同。
- **静态检查（`m08b_static.py --tag S01`，`evidence/M08B_S01_STATIC_CHECKS.json`）：** 两情景 B8、B11 供给路线（含中温 A / B 母线）、B13、G2.1、G2.2、365×24h = 2920×3h 日均，以及 M08b 专项（需求 = 锚表，含居民 / 商业 / 农业燃料行；无负负荷；温度档映射：中温 B 与高温无电 / 氢输入、电锅炉只在低温与中温 A、热泵只在低温；无固定甲烷溢出；固定生物质 ≤ 池；LNG 16 台无上限、8,020.43 EUR2020/MW/a；VN 封存 106.07 Mt/a；地面光伏 × 1.108696 逐台；海上风规则）全部**通过**；B5、B16 通过；G2.3 需求解；B11 完整性已停用（§8.1 第 9 项）。
- **变体两遍（`m08a_variants.py`，`evidence/M08B_S01_VARIANT_*`）：** 6 个变体每个生成两遍，网络逐字节相同，回执只差 `output.path`；每遍约 4 s、0.7 GB。

| 变体 | 基础网络 | 输出网络 SHA256（两遍相同） |
|---|---|---|
| 保留存量 | integrated | `f9c9a873…c67c5` |
| b1 | disconnected | `632e6a0e…584ef` |
| 去掉 VN | integrated | `d9c49a82…47563` |
| 去掉 TH | integrated | `0e4870c8…68f96` |
| 去掉 LA | integrated | `3fdc2803…e8d3a` |
| 分国 WACC | integrated | `f833ed8d…63a7` |

- **修正前后对比（integrated；disconnected 的需求列逐国相同；前 = S4M-3 网络，首轮 = M08b 第一轮网络，后 = 补充 01；`evidence/BUILD_INPUT_CHANGES_M08B_S01.*`）：**

| 国 | 终端需求 前 | 首轮 | 后 | 基础电力 前 | 后 | 固定电力 前 | 首轮 | 后 | 水泥 前 | 后 | 粗钢 前 | 后 | 光伏上限 前 | 后 | 封存上限 前 | 后 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | 20 | 9 | 9 | 3.2 | 3.4 | 7 | 4 | 4 | 0.6 | 0.4 | 0 | 0 | 1 | 2 | 371.6 | 371.6 |
| KH | 126 | 90 | 96 | 17.4 | 12.8 | 58 | 48 | 49 | 41.7 | 13.6 | 0 | 0 | 359 | 398 | 1.7 | 1.8 |
| ID | 3,964 | 2,775 | 2,671 | 301.1 | 310.9 | 2,274 | 689 | 689 | 312.6 | 112.8 | 28.3 | 30.8 | 859 | 952 | 1,025.5 | 1,025.5 |
| LA | 39 | 35 | 36 | 4.9 | 9.0 | 18 | 23 | 23 | 17.7 | 9.8 | 0 | 0 | 119 | 132 | 0 | 0 |
| MY | 1,400 | 685 | 648 | 139.7 | 117.2 | 743 | 299 | 296 | 56.6 | 38.4 | 20.0 | 14.6 | 78 | 86 | 2,575.5 | 2,575.5 |
| MM | 197 | 126 | 109 | 14.5 | 18.2 | 116 | 41 | 38 | 12.9 | 12.0 | 0.7 | 0.7 | 826 | 915 | 0 | 0 |
| PH | 600 | 458 | 427 | 103.7 | 104.1 | 299 | 229 | 229 | 107.0 | 55.9 | 6.2 | 3.0 | 299 | 331 | 446.0 | 1.3 |
| SG | 267 | 116 | 113 | 41.2 | 34.4 | 153 | 66 | 66 | 0 | 0 | 1.6 | 0.4 | 0 | 0 | 0 | 0 |
| TH | 2,000 | 1,088 | 1,026 | 208.6 | 170.2 | 947 | 516 | 509 | 160.3 | 66.9 | 14.4 | 7.6 | 1,108 | 1,229 | 320.5 | 320.5 |
| TL | 2 | 5 | 5 | 0.9 | 2.3 | 2 | 4 | 4 | 0 | 0 | 0 | 0 | 10 | 11 | 5.0 | 0 |
| VN | 2,237 | 1,310 | 1,281 | 197.2 | 184.5 | 1,253 | 643 | 644 | 581.0 | 107.0 | 80.3 | 40.6 | 411 | 456 | 236.0 | 106.1 |
| **11 国** | **10,851** | **6,697** | **6,423** | **1,032.4** | **966.9** | **5,870** | **2,561** | **2,552** | **1,290.4** | **416.8** | **151.5** | **97.8** | **4,071** | **4,514** | **4,981.7** | **4,402.2** |

| 国 | 居民燃料 前 | 后 | 商业燃料 前 | 后 | 农业燃料 前 | 后 | 中温（首轮） | 中温 A | 中温 B | 高温 |
|---|---|---|---|---|---|---|---|---|---|---|
| BN | 0.2 | 0 | 0 | 0 | 0.4 | 0.2 | 0.1 | 0.0 | 0.1 | 0.2 |
| KH | 12.1 | 13.8 | 9.8 | 12.4 | 14.3 | 19.7 | 0 | 0 | 0 | 0 |
| ID | 421.9 | 314.9 | 73.2 | 34.9 | 42.9 | 46.5 | 502.8 | 100.6 | 402.2 | 583.6 |
| LA | 8.8 | 8.5 | 6.6 | 5.3 | 3.6 | 5.3 | 0 | 0 | 0 | 0 |
| MY | 14.0 | 0 | 20.8 | 0 | 28.4 | 18.0 | 31.3 | 6.3 | 25.1 | 72.7 |
| MM | 40.4 | 18.8 | 30.4 | 12.9 | 42.7 | 27.2 | 18.0 | 3.6 | 14.4 | 8.3 |
| PH | 75.0 | 52.8 | 83.1 | 55.2 | 8.6 | 8.4 | 2.3 | 0.5 | 1.9 | 5.1 |
| SG | 0.6 | 0 | 2.8 | 0 | 0.3 | 0 | 3.5 | 0.7 | 2.8 | 8.5 |
| TH | 55.5 | 9.9 | 17.0 | 0 | 111.7 | 80.6 | 5.5 | 1.1 | 4.4 | 12.6 |
| TL | 0.2 | 0.6 | 0 | 0 | 0.0 | 0.6 | 0 | 0 | 0 | 0 |
| VN | 45.1 | 16.1 | 42.8 | 33.8 | 67.5 | 75.1 | 124.0 | 24.8 | 99.2 | 209.0 |
| **11 国** | **673.7** | **435.3** | **286.7** | **154.4** | **320.5** | **281.6** | **687.6** | **137.5** | **550.1** | **900.0** |

  单位与定义同 §3.4（需求 TWh/a、产量 Mt/a、光伏 GW、封存 Mt CO₂/a）；居民 / 商业 / 农业燃料 = 网络所用需求表中该部门全部非电力行（终端能源；前与首轮均为比率表，未锚定）；中温 = 其他桶（及溢出）有用热负荷。补充 01 只改变需求侧：终端需求 6,697 → 6,423 TWh（−274，主要是居民 / 商业燃料），固定电力 2,561 → 2,552 TWh，工业用电 1,081.9、陆路 EV 455.0 TWh 不变；水泥、粗钢、光伏、封存与首轮相同。

### 8.5 网络大小与 SHA256（补充 01 §4.4）

| 网络 | 分辨率 | 快照 | 大小（B） | MiB | SHA256 |
|---|---|---|---|---|---|
| `integrated_2920_3h_unsolved.nc` | 2920×3h | 2,920 | 64,106,133 | 61.14 | `bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab` |
| `integrated_365_24h_unsolved.nc` | 365×24h | 365 | 31,524,926 | 30.06 | `75704334dc11deeb06fc80f84ef197d65c3ac5bd658ab450e4ee1a93a3ccb19e` |
| `disconnected_2920_3h_unsolved.nc` | 2920×3h | 2,920 | 63,439,167 | 60.50 | `b401a68729524c885a8245962bc2a46706a1760c42ef40bdd9943e60a859bcc7` |
| `disconnected_365_24h_unsolved.nc` | 365×24h | 365 | 30,857,960 | 29.43 | `888a009b5f19eb34f7f1c24e36f7c8370617a9c405b1097a9caed0599cecbee4` |

位置：主检出 `results_project/m08b/builds_s01/<scenario>/`（不入库）；合计 189.9 MB；构建回执 `evidence/M08B_S01_{integrated,disconnected}_BUILD_RECEIPT.json`。

### 8.6 再次冒烟（补充 01 §4.3）——**未执行，待用户授权**

拟执行（与 §5 相同，只换网络与 SHA 选择）：`builds_s01` 的 2920×3h 网络截取前 56 时段，档案 A（`formal_barrier`），一体化与不互联各 1 次，TimeLimit 1,750 s（墙钟 1,800 s 止损），串行；之后 `l23_violation_analysis.py`、`s4o_c1_precision.py run`、本批参照与重评、`gates_v6.py accept --build-receipt`（用修正后的 SHA 选择，不再显式传 `--registered-sha256`）。通过标准同 §5：GATES_V6 = ACCEPTED_LAYER2、B6 > 0、账本恒等式、无固定甲烷溢出、LNG 不受上限、报告与导出完整；不通过只记录诊断，不重试、不改参数。执行前需确认：本机无其他 Gurobi 进程、距上次 Gurobi 会话 ≥ 5 分钟（上次为本日首轮冒烟）、云端无运行（须由用户确认）。

### 8.7 仍未解决的项（补充 01 之后）

1. **再次冒烟**待授权（§8.6）。
2. **燃料锚定 9 格取 0**（§8.3）：国家 TFEC 比 ATS 锚多 63.30 TWh；是否接受、或改用其他口径（例如负值格按比例从电力锚中扣减），需审阅端决定。
3. **200 °C 线性插值**可能低估中温 A（INFERENCE，§8.2）；0.1 / 0.3 敏感性需重生成表，未构建。
4. **中温 B 未含固体生物质蒸汽锅炉**（补充 01 列表未列；DEA 覆盖到 300 °C）。
5. 氢供热（局限已登记）、东盟温度分布（DATA_PENDING）、交通载体效率与其他桶柴油机（C 级）——均按决定维持。
6. 云端部署包留给 M09 / M10（S4O 包清单仍写 0.98，须按本分支头重新打包）。
7. `s3_1_gas_data.py` 中燃气管道成本仍是旧层字面值；注册表经 `m08b_corrections.csv` 整行替换为现行值，重跑 s3_1 不影响装配结果（替换前先核对旧值）。

**补充 01 文件：** 代码 `scripts_project/v5/gates_v6.py`、`m08b_heat_bands.py`、`s3_0_industry.py`、`s2_layers.py`、`m08b_demand.py`、`m08b_data.py`、`m08b_static.py`、`v5/v5_gates.py`、`configs/research/baseline.yaml`；测试 `test_m08b_s01.py`（新）、`test_m08b_heat.py`、`test_m08b_demand.py`；证据 `evidence/M08B_S01_*`、`BUILD_INPUT_CHANGES_M08B_S01.*`；脚本 `scripts/m08b_s01_*`、`m08b_tests.sh`、`m08b_variant_receipts.py`（加 `--variants / --tag`）；未入库 `results_project/m08b/{builds_s01,variants_s01,trial_s01}/`。审阅 ZIP `work/p1_m08b_20261021/M08B_S01_REVIEW.zip`（交付目录 + 补充 01 数据表与注册表片段 + 相对首轮头 58b8efdc 与 M08a 头 820c2cae 的代码差异；逐成员 SHA256 + CRC 清单 `M08B_S01_REVIEW_MANIFEST.csv`，ZIP 的 SHA256 见 `M08B_S01_REVIEW_ZIP_SHA256.txt`）；首轮 `M08B_REVIEW.zip` 不变。PR：[cyc292cycjin-oss/SGP-ESE5004-Stage2#47](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/47)（同一 draft PR，说明已更新）。
