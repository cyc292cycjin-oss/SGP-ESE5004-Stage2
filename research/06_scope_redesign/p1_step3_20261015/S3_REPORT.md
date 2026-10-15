# S3 报告：天然气网络、东盟外进口、氨/甲醇、航运与燃料碳归属（第 61–64 项已确认）

分支 `codex/s3-gas-imports-shipping-20261015`（自 S2 分支 @ 8d61bd37 开出）；仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`。结论分级：VERIFIED / EXACT / INFERENCE / PROPOSED。本轮没有正式求解，只有本地构建、56×3h 冒烟与 gap_diagnostic。

## 摘要（≤10 行）

（S3 全部子步骤完成后填写。）

---

## 1. S3-0 收尾修正

### 1.1 第 61 项：PyPSA-Eur 工业部门比率（JRC-IDEES-2021）

**复现方法（VERIFIED）。** `scripts_project/s3_0_industry_ratios.py` 以 importlib 原样加载本地登记的 PyPSA-Eur v2025.07.0 `scripts/build_industry_sector_ratios.py`（SHA 70c45a81…），替换 `snakemake` 与 `scripts._helpers` 为桩，输入 `raw8/JRC-IDEES-2021_EU27.zip` 解出的 `JRC-IDEES-2021_Industry_EU27.xlsx`（SHA 1fd3bc14…），参数取 `config.default.yaml` 815–910 行（`reference_year` 2019，`ammonia: true`）。调用的函数与行号：`iron_and_steel` 102、`chemicals_industry` 296、`nonmetalic_mineral_products` 635、`pulp_paper_printing` 832、`food_beverages_tobacco` 991、`non_ferrous_metals` 1057、`transport_equipment` 1259、`machinery_equipment` 1309、`textiles_and_leather` 1361、`wood_and_wood_products` 1410、`other_industrial_sectors` 1455；`load_idees_data` 79–99。输出 `registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv`（12 行 × 27 列，含 `heat` 低温热行）。

**氨产量输入（VERIFIED）。** 该脚本在 431–436 行用 `resources/ammonia_production.csv`（USGS）扣除 2019 年 EU27 的合成氨能耗。该资源按 PyPSA-Eur 规则复现：`retrieve.smk` 299–305 行给出 USGS 氮矿物年鉴表 `myb1-2022-nitro-ert.xlsx` 的公开地址，`scripts/build_ammonia_production.py` 读表 T12（skiprows 5、skipfooter 7、`--`→NaN、ktN×17/14）。两文件只读获取并登记（表：2026-10-15T10:30:38Z，SHA 9b055fcd…；脚本 10:29:18Z，SHA 5aca047c…；规则文件 10:29:53Z）。EU27 2019 合成氨 = 15,712.9 kt NH₃（18 国），替代 S2B 报告里 17,000 kt 的配置注释代理（C 级 → B 级）。

**与公开 PyPSA-Eur 结果的对比。** PyPSA-Eur 不发布 `industry_sector_ratios.csv` 产物，无法逐值对照；可核对的是配置常数行（如 DRI+EAF 氢 1.7 MWh/t、Ammonia 5.166、Methanol 5.528、HVC 机械回收 0.547、化学回收 6.9）与脚本输出一致（EXACT）。

**2050 比率摘录（MWh/t，EXACT，节选）：**

| 部门 | 电 | 甲烷 | 氢 | 生物质 | 低温热 | 煤/焦 | 过程排放 t/t |
|---|---|---|---|---|---|---|---|
| Electric arc | 1.122 | 0.167 | 0 | 0 | 0.005 | 0 | 0.041 |
| DRI + Electric arc | 1.444 | 0.167 | 1.700 | 0 | 0.005 | 0 | 0.041 |
| Integrated steelworks | 1.032 | 0.332 | 0 | 0 | 0 | 0.154+0.185 | 0.774 |
| HVC（不含石脑油 12.62） | 2.454 | 3.295 | 0.173 | 0 | 0.182 | 0 | −0.063（+0.490 原料） |
| Cement | 0.107 | 0.556 | 0 | 0.198 | 0.004 | 0 | 0.525 |
| Alumina / Al primary | 1.393 / 14.761 | 3.690 / 0 | 0 | 0 | 0.015 / 0.045 | 0 | 0 / 1.507 |
| Other industrial sectors | 0.242 | 0 | 0 | 0.071 | 0.008 | 0 | 0 |

**应用到东盟（`scripts_project/s3_0_industry.py`，覆盖 S2B 的 `INDUSTRY_2050_SUMMARY_*.csv`）：**
- 钢铁、水泥按活动量：粗钢 2050 = worldsteel 2019 × 工业乘数，0.3 DRI+EAF / 0.7 Electric arc；水泥 = EDGAR 2.A.1/0.52 熟料 ÷ 0.656（technology-data 熟料投入）× Cement 比率。S2B 的 technology-data 替代比率改为敏感性文件 `INDUSTRY_2050_SUMMARY_*_TD_SENSITIVITY.csv`（开关 `research.s2.industry.ratio_source: jrc_idees_2021 | technology_data_v015`）。
- 其余 UNSD 子部门按能量：2019 能耗 × 乘数 × 效率因子（PyPSA-Eur 2050 单耗 ÷ EU27 2019 单耗）× 2050 载体份额；UNSD→PyPSA-Eur 映射与 EU27 2019 能耗权重见 `demand_v5/INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv`（C 级）。化工子部门按 EU27 能耗拆成 HVC 28.9% / 合成氨 30.8% / 氯碱 4.3% / 甲醇 2.7% / 其他化工 24.2% / 制药 9.1%（脚本 431–448 行的扣减逻辑）。
- HVC 口径（INFERENCE，已登记）：PyPSA-Eur 把 IDEES 基础化工的原料天然气计入 `methane`（脚本 330–345 行），石脑油单列为原料；本轮 2019 单耗按同一口径（能耗 + 原料天然气 − 氨/氯/甲醇能耗）/52 Mt = 6.67 MWh/t，2050 为 6.10（不含石脑油），效率因子 0.915；若严格只算能源用途，因子为 0.86 且甲烷份额为 0——两者差别只影响 HVC 部分。
- 低温热行接入现有节点工业低温热母线（`IndustryLowTemperatureHeat` 负荷）。氨、甲醇行在 S3-0 暂按 PyPSA-Eur `ammonia: false` 路线折算（氨 → 1.148 MWh H₂ + 0.048 MWh 电 /MWh NH₃，配置 849/852/853 行；甲醇 → 1.854 MWh CH₄ + 0.030 MWh 电 /MWh MeOH，904–906 行），开关 `ammonia_methanol_mode`，S3-3 切到全区母线。
- 生物质超出国家潜力的部分改甲烷（第 36 项）：SG 17.8 TWh、VN 214.0 TWh（与 S2B 同）。
- 氯碱副产氢使国家净工业氢为负时记 0、不计信用（仅 BN，−0.008 TWh）。

**三列对比（TWh/a，2050，主分配 aeo8_ats_relative；VERIFIED）。** 煤保留量：S3-0 全部国家为 0（2050 比率中只有一体化长流程钢保留煤/焦，而主路线为 H₂-DRI + 废钢电炉）。

BAS 固定结构（2019 载体份额 × 乘数）：

| 国家 | 生物质 | 煤 | 电 | 气 | 油 | 合计 |
|---|---|---|---|---|---|---|
| BN | 0.0 | 0.0 | 1.2 | 0.0 | 2.4 | 3.6 |
| ID | 642.1 | 1002.2 | 305.7 | 415.9 | 314.6 | 2680.5 |
| KH | 11.2 | 5.8 | 15.2 | 0.0 | 12.9 | 45.1 |
| LA | 4.0 | 4.6 | 8.4 | 0.0 | 0.3 | 17.3 |
| MM | 41.9 | 7.3 | 11.2 | 6.3 | 52.2 | 118.9 |
| MY | 0.0 | 37.0 | 219.5 | 250.7 | 91.5 | 598.7 |
| PH | 22.9 | 50.6 | 87.4 | 2.3 | 51.1 | 214.3 |
| SG | 0.0 | 4.2 | 42.4 | 27.4 | 80.6 | 154.6 |
| TH | 187.3 | 162.4 | 278.5 | 142.5 | 183.0 | 953.7 |
| TL | 0 | 0 | 0 | 0 | 0 | 0 |
| VN | 209.1 | 994.9 | 490.5 | 24.3 | 19.1 | 1737.9 |
| 东盟 | 1118.5 | 2269.0 | 1459.8 | 869.4 | 807.7 | 6524.4 |

S2B（technology-data 钢铁/水泥 + 其余子部门 2019 份额；冻结自提交 8d61bd37）：

| 国家 | 生物质 | 煤 | 电 | 气 | 油 | 氢 | 合计 |
|---|---|---|---|---|---|---|---|
| BN | 0.0 | 0.0 | 1.2 | 0.3 | 2.1 | 0.0 | 3.6 |
| ID | 587.4 | 904.7 | 317.0 | 479.8 | 280.6 | 13.7 | 2583.2 |
| KH | 2.3 | 0.2 | 15.2 | 24.6 | 2.7 | 0.0 | 45.0 |
| LA | 0.0 | 0.0 | 8.4 | 10.5 | 0.0 | 0.0 | 18.9 |
| MM | 41.9 | 0.1 | 11.7 | 11.6 | 52.2 | 0.4 | 117.9 |
| MY | 0.0 | 0.0 | 222.6 | 277.7 | 89.2 | 9.7 | 599.2 |
| PH | 22.6 | 8.9 | 99.3 | 63.2 | 38.8 | 3.0 | 235.8 |
| SG | 0.0 | 4.2 | 42.6 | 27.4 | 80.6 | 0.8 | 155.6 |
| TH | 187.3 | 93.7 | 260.2 | 204.5 | 161.1 | 7.0 | 913.8 |
| TL | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| VN | 110.2 | 512.8 | 525.2 | 382.4 | 10.9 | 39.0 | 1580.5 |
| 东盟 | 951.7 | 1524.6 | 1503.3 | 1482.0 | 718.0 | 73.7 | 6253.3 |

S3-0（IDEES 比率，全部子部门；煤、油为 0）：

| 国家 | 生物质 | 电 | 气 | 低温热 | 氢 | 氨 | 甲醇 | 合计 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.1 | 2.1 | 0.9 | 0.1 | 0.0 | 0.1 | 0.0 | 3.2 |
| ID | 529.8 | 1717.3 | 184.9 | 53.9 | 12.9 | 14.0 | 1.4 | 2514.2 |
| KH | 10.2 | 12.2 | 22.1 | 0.4 | 0.0 | 0.0 | 0.0 | 44.9 |
| LA | 4.8 | 6.6 | 9.4 | 0.2 | 0.0 | 0.0 | 0.0 | 21.0 |
| MM | 26.8 | 77.0 | 7.4 | 2.5 | 0.3 | 0.5 | 0.0 | 114.5 |
| MY | 121.4 | 406.1 | 33.2 | 12.2 | 9.7 | 0.0 | 0.0 | 582.6 |
| PH | 71.4 | 97.4 | 59.2 | 4.0 | 2.9 | 1.4 | 0.1 | 236.4 |
| SG | 0.0 | 96.1 | 28.0 | 3.3 | 0.2 | 9.6 | 1.0 | 138.2 |
| TH | 271.8 | 450.7 | 106.6 | 19.8 | 6.0 | 18.5 | 1.9 | 875.3 |
| TL | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| VN | 110.2 | 918.9 | 546.2 | 27.2 | 38.4 | 10.9 | 1.1 | 1652.9 |
| 东盟 | 1146.4 | 3784.4 | 998.0 | 123.5 | 70.6 | 55.0 | 5.6 | 6183.5 |

**需要注意的后果（INFERENCE）。** 东盟工业电力从 S2B 的 1,503 TWh 升到 3,784 TWh，煤 1,525 → 0、油 718 → 0。原因是多数国家的 UNSD 工业表只有化工、钢铁和"其他"行（ID/MY/SG/KH/LA/BN 没有非金属矿物、造纸、食品等行），"其他"桶映射到 PyPSA-Eur `Other industrial sectors`，其 2050 比率 76% 为电。ID 的 1,002 TWh 工业煤（含镍冶炼等）因此几乎全部电化。这是第 61 项的直接结果，不是数据错误；若用户希望为"其他"桶保留更多燃料份额，需另行决定。

**登记：** `fragments/industry_sector_ratios.csv`（55 行：比率、参数、效率因子、USGS 来源）、`fragments/industry_2050.csv`（108 行）。缺口表 `INDUSTRY_2050_GAPS.csv`（108 行，均为 C 级推算说明：无 UNSD 行时从"其他"桶取能量等）。

### 1.2 第 59/62 项：走廊 TH–MM、LA–MM 与 APG 核对

**新增走廊（EXACT）。** `scripts_project/s3_0_corridors.py` 向 `corridors/cross_border_corridors.csv` 追加两行（24 → 26 行），线路在构建时由 `s2_layers.add_apg_corridor_lines` 生成：

| 走廊 | 节点对 | 选点依据 | 长度 | 2025 容量 | 处理 |
|---|---|---|---|---|---|
| APG #11 TH–MM | MM2 4 (97.98E, 16.70N) – TH2 4 (99.99E, 17.55N) | 两国 AC 节点大圆距离最小对 233 km（次近 MM2 4–TH2 2 364 km、MM2 1–TH2 4 386 km） | 233 × 1.25 = 291.8 km | 0 | 可扩建候选（s_nom 0） |
| APG #17 LA–MM | LA2 5 (101.52E, 20.40N) – MM2 13 (99.21E, 21.77N) | 最小对 284 km（次近 MM2 7–LA2 5 407 km） | 284 × 1.25 = 354.7 km | 30 MW 存量（s_nom_min） | 扩建内生（APG 规划 100–600 MW 仅作参考） |

长度系数 1.25 是基础网 19 条既有跨境 AC 线 `length/大圆距离` 的中位数（与 PyPSA-Eur `lines.length_factor` 一致）。单位投资 42.01 EUR/MW/km/a 取既有跨境线中位数（基础网统一值）；线型 `Al/St 240/40 4-bundle 380.0`、`s_max_pu` 0.7 与每公里电气参数取并联数最接近中位数的既有跨境线（Line 43 KH–LA，并联数 1.286；构建回执 `apg_corridor_additions`）。H₂/CO₂ 候选管道随电力拓扑自动再生成：跨境候选 19 → 21（新增 LA–MM、MM–TH），缅甸 17 节点 21 条国内候选一个连通分量，不再是无 CO₂ 去向的孤岛。

**24 走廊 vs 18 个 APG 优先项目核对（`corridors/CORRIDOR_APG_CROSSCHECK_2024.csv`，VERIFIED）：**

| 分类 | APG 项目 | 说明 |
|---|---|---|
| 已覆盖（表中有） | #1 MY–SG 525 MW（Line 92）；#2 TH–MY 380（Line 91 + 4 条 HVDC 491.4 + Khlong Ngae–Gurun 300 = 2645.6 MW，表值 ≫ APG 的 380）；#6 Sarawak–W.Kalimantan 230（Line 23）；#9 TH–LA 955（9 条线）；#10 LA–VN（4 条 0.2–0.4 MW 线，合计 1.0 MW；APG 未给既有容量）；#12 VN–KH 200；#13 LA–KH 300；#14 TH–KH 250 | 差异只记录，不改表 |
| 本轮新增 | #11 TH–MM、#17 LA–MM | 第 62 项 |
| 仅 APG（同国家对但另一段） | #4 Peninsular–Sumatera、#15 E.Sabah–N.Kalimantan | 表中 ID–MY 只有 #6；不新增 |
| 仅 APG | #5/#16 SG–Sumatera/Batam、#7 PH–Sabah、#8a Sarawak–Brunei、其他 SG–VN、SG–KH | 不新增 |
| 单国内部（范围外） | #3 Sarawak–Peninsular、#8b Sarawak–Sabah、#18a/b Kalimantan/Sumatera–Java | 国内输电内生 |
| 仅表中 | 无 | |

### 1.3 第 63 项：废塑料代理值（`s2b_feedstock.py`，C 级）

| 项 | 代理值 | 依据 | 敏感性 |
|---|---|---|---|
| LA 塑料占 MSW 份额 | 0.165 | 10 个有数据国家按 2050 MSW 加权均值（BN 0.29、KH 0.10、ID 0.19、MY 0.24、MM 0.105、PH 0.1055、SG 0.136、TH 0.176、TL 0.097、VN 0.10） | 0 – 0.29 |
| KH/TH/VN 未收集垃圾露天焚烧份额 | 0.739 | 有数据的 ID 0.739、MM 0.21、PH 0.163 按 MSW 加权 | 0 – 0.739 |

结果：LA 塑料焚烧 0.12 Mt CO₂/a（原 0）；KH 0.60、TH 2.54、VN 2.23 Mt（含代理份额）；登记行 `waste_plastic_share_LA` 等由 DATA_PENDING 改为 C 级 REGISTERED，`feedstock_plastics_burned_co2_2050_*` 的敏感性区间并入代理值的 0 / 最大值。

### 1.4 柬埔寨交通链核对（只报告，`scripts_project/s3_0_kh_check.py` → `KH_TRANSPORT_CHAIN_CHECK.json`）

| 环节 | 数值 | 结论 |
|---|---|---|
| UNSD EB 2019 交通油品：公路 73,274 TJ、铁路 9,718、国内航空 3,047、国内航运 2,513 | = 20.35 / 2.70 / 0.85 / 0.70 TWh | 与 D1 2019 基准四项逐一相等（VERIFIED） |
| D1 链：r_KH 1.326 × k_transport 3.925 = 5.206 | 2050 交通燃料 128.0 TWh | 算术一致（EXACT） |
| 对照：Astar 2050 KH 电力 26.8 TWh；D1 2050 电力行合计 31.3 TWh | 交通燃料 / Astar = 4.8（2019 年交通燃料 / 全部用电 = 2.4） | 异常 |
| 东盟层面：D1 交通 2019 基准合计 1,161 TWh（99.8 Mtoe） vs AEO8 2022 历史 145.2 Mtoe（比值 0.69）；D1 2050 合计 4,335 TWh = 372.7 Mtoe ≈ AEO8 **BAS** 2050 交通 374.9 Mtoe（ATS 为 228.2） | 隐含东盟乘数 3.73 | k 偏大的来源（INFERENCE） |

解读（INFERENCE）：KH 的 2019 基准正确；5.2 倍来自 (a) 部门校准目标是 AEO8 BAS 2050 部门总量而非 ATS；(b) UNSD 2019 基准比 AEO8 2022 历史低 31%（口径与年份差），把 k 推到 3.93；(c) KH 的 ATS 人均增长因子 1.33 高于均值。各国交通乘数：BN 1.9、SG 2.3、MM 2.3、LA 3.1、MY 3.2、PH 3.6、TH 3.8、TL 3.8、ID 4.0、VN 5.1、KH 5.2。是否改用 ATS 总量或 AEO8 历史口径的基准，由用户决定；本轮未改模型。

### 1.5 S3-0 结构表与冒烟

年度结构性缺口表 `results_project/s3/S3_STRUCTURAL_GAP_ANNUAL.json`（证据副本 `evidence/s3_0/`）：

| 国家 | 不可避免 CO₂（化石终端 + 过程 + 塑料）Mt/a | 存储上限 Mt/a | 跨境 CO₂ 候选 | 一体化 | 不互联 |
|---|---|---|---|---|---|
| BN | 0.82 | 371.6 | 0 | 可行 | 可行 |
| ID | 353.5（S2B 787.6） | 1025.5 | 1 | 可行 | 可行 |
| KH | 28.2 | 1.7 | 3 | 可行 | 缺口 26.5 |
| LA | 9.0 | 0 | 15 | 可行 | 缺口 9.0 |
| MM | 13.8（S2B 28.1） | 0 | 2（新增） | 可行 | 缺口 13.8 |
| MY | 78.5 | 2575.5 | 3 | 可行 | 可行 |
| PH | 84.1 | 446.0 | 0 | 可行 | 可行 |
| SG | 54.9 | 0 | 1 | 可行 | 缺口 54.9 |
| TH | 170.4 | 320.5 | 12 | 可行 | 可行 |
| TL | 0.03 | 5.0 | 0 | 可行 | 可行 |
| VN | 365.6（S2B 506.6） | 236.0 | 5 | 可行 | 缺口 129.6 |

不可避免 CO₂ 从 S2B 的 1,946 Mt/a 降到 1,159 Mt/a，主因是工业煤、油按 IDEES 比率归零；生物质缺口两情景均为 0。

**冒烟（56×3h，第 58 项权重 156.43 h/时段，HiGHS IPM + crossover，各一次求解，无重试；`evidence/s3_0/`）：**

| 运行 | HiGHS 状态 | 目标值 EUR/a | 用时 | 结论 |
|---|---|---|---|---|
| 一体化 冒烟 | IPM "imprecise"，crossover "imprecise"，基解原始不可行量 1.03e1 → `Model status: Infeasible` | —（未写入） | 512 s | 见下 |
| 一体化 gap_diagnostic | IPM optimal，crossover imprecise（原始不可行量 4.3），`Optimal` | 5.4216e11 | 520 s，峰值 2.3 GiB | 电力、CO₂、生物质松弛全部为 0（生物质松弛合计 3e-4 MWh，为数值噪声）；11 国净排放 = 0；门槛 A1–A6、B2/B3/B8/B11/B12 全部通过 |
| 不互联 冒烟 | IPM "primal infeasible"，crossover 未运行 | — | 64 s | 真实不可行 |
| 不互联 gap_diagnostic | IPM optimal，`Optimal` | 2.0185e12 | 316 s，峰值 2.2 GiB | CO₂ 缺口 KH 16.5 / LA 8.5 / MM 4.3 / SG 11.9 / VN 96.4 Mt/a（S2B：16.55 / 8.61 / 5.13 / 12.84 / 234.47）；电力、生物质缺口 0 |

**一体化"结构可行、冒烟不可行"的原因（VERIFIED 的事实 + INFERENCE 的解读）。** 两个 LP 只差 108 个松弛列（每国电力/CO₂/生物质各一列，带罚款）。gap_diagnostic 解中所有松弛为 0，即原冒烟 LP 的全部约束在该解下同时满足——一体化网络在 56×3h 结构下**可行**，且逐国净零可达。冒烟 LP 的 HiGHS 日志显示 IPM 未达到最优容差（"imprecise"），crossover 得到的基解原始不可行量 1.03e1 MW 级，HiGHS 据此报 `Infeasible`；而带松弛列的 LP 条件更好，IPM 收敛到 optimal。使 LP 条件变差的触界约束（在最优解处同时成立）：(a) 4 个国家的年度封存上限恰好触界（ID 1,025.5、KH 1.7、TH 320.5、VN 236.0 Mt）；(b) 107 个有限生物质池中大部分用尽到 100%（BN 全部、ID 多数），且 BN、SG 的固定生物质终端需求等于本国潜力（第 36 项溢出规则使二者相等，是等式约束）；(c) 时段权重 156.43 把每个时段的流量放大到年尺度，使系数跨度从 1e0（效率）到 1e9（Store 上限 t）。年度外部进口上限：S3-0 无（计数 0）；跨境电力线下界 s_nom_min 均不触界（最优容量远高于 2025 存量，如 Line 60 41.4 GW、APG11 6.2 GW、APG17 1.2 GW）；权重和 8,760 h 核对通过（B12）。因此不是任一平衡的物理缺口，而是求解精度问题；主算约束未放宽，未开特例。对云端日分辨率运行的建议（PROPOSED，未执行）：保留 IPM，但在授权运行时启用 HiGHS 的 `run_crossover: off` 或放宽 `ipm_optimality_tolerance`，并在回执中登记。

不互联情景的不可行是真实的（IPM 直接判原始不可行），缺口与结构表一致（无存储且无跨境管道的 KH/LA/MM/SG 与超出本国上限的 VN）；VN 缺口由 S2B 的 234 Mt 降到 96 Mt，因为工业煤按 IDEES 比率电化后不可避免 CO₂ 减少。

---

## 2. S3-1 天然气网络与国内生产

代码：`scripts_project/s3_1_gas_data.py`（数据层）、`scripts_project/s3_layers.py::add_gas_network`（模型层，在 `s2_network.build_scenario_s2` 的需求层之后、跨境开关之前调用）；配置 `research.s3.gas`，`research.cross_border.gas: true`（情景文件统一设 true/false）。构建输出 `results_project/s3_1/`（证据副本 `evidence/s3_1/`）。

**2.1 节点气母线（VERIFIED）。** 沿用 PyPSA-Eur `gas_network` 结构：每个 AC 节点和 HVDC 换流节点一个 `<node> gas` 母线（100 个）。S2 的用气组件已全部在节点气母线上（CCGT/OCGT/CCGT CC、SMR/SMR CC、工业燃气锅炉、清洁炊事、工业与原料计量链路；沼气提纯 97 条链路向节点气母线供气），本轮不改接。S1/S2 配方中每个节点的无限量外部气源（100 个 `EXTERNAL_SUPPLY` 发电机，13.674 EUR/MWh）被移除，气只能来自国内生产、LNG 接收站和管道。

**2.2 管道（VERIFIED）。** 候选：每条电网连接（AC 线 + DC 链路，与 R5 的 H₂/CO₂ 候选同拓扑）一条双向候选，共 111 条，其中跨境 21 条（含本轮走廊 LA–MM、MM–TH）；成本 technology-data v0.15.0 `CH4 (g) pipeline` 91.37 EUR/MW/km（年金 7.99 EUR/MW/km/a，寿命 50 a）与 `CH4 (g) submarine pipeline` 125.49（13.88，30 a），海底份额取走廊表。连通性补全（PyPSA-Eur `prepare_sector_network.py` 1968–2010 行，`gas_network_connectivity_upgrade: 1`，配置 768 行）：电网拓扑之外的 14 个带气母线的节点（印尼的 Maluku/Nusa Tenggara/Papua 岛屿节点与 Batam 节点、3 个 HVDC 换流节点 PH_Visayas10 0、MY_Peninsular22 0、TH21 0）各加一条到本国最近气母线的双向候选（大圆 × 1.25；最长 Papua19→Sulawesi 2,299 km，仅为候选）。2025 年跨境存量（第 15 项，GEM GGIT 2025-11 第九批）：

| 管道 | 节点对 | 投运 | bcm/a | MW_NCV | 方向 | 处理 |
|---|---|---|---|---|---|---|
| Gresik–Batam–Singapore | ID_Sumatra2 0 → SG2 0 | 2003 | 4.75 | 5,126 | 单向 | p_nom_min = 容量，可扩建 |
| West Natuna | ID_Sumatra2 0 → SG2 0 | 2001 | 3.4 | 3,669 | 单向 | 同上 |
| Malaysia Singapore | MY_Peninsular2 1 → SG2 0 | 1991 | — | — | — | DATA_PENDING（GEM 无容量），只有走廊候选 |
| TTM | MY_Peninsular22 0 ↔ TH21 0 | 2007 | 10.42 | 11,244 | 双向（JDA 气供两国） | p_nom_min = 容量 |
| Yetagun | MM2 4 → TH2 2 | 2000 | 4.1 | 4,424 | 单向 | 同上 |
| Yadana 1 | MM2 4 → TH2 2 | 1998 | 5.2 | 5,611 | 单向 | GEM 登记为缅甸单国，终点 Daminseik 为对泰出口落地点 |
| Zawtika | MM2 4 → TH2 2 | 2014 | 3.53 | 3,809 | 单向 | GEM 登记为缅甸单国，经 Kanbauk 接 Yadana 系统 |

换算：1 bcm/a = 1,199 MW（PyPSA-Eur `build_gas_input_locations.py` 127 行，GCV 口径）× 0.90（登记表 `fuel_price_basis` GCV→NCV）。缅泰三条合计 12.83 bcm/a，与 GEM 泰国境内 Ban I-Tong–Ratchaburi 段 12.93 bcm/a 相符（交叉核对）。节点依据登记在 `gas_v5/GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv` 的 `node_basis` 列：缅泰管道落地点 Kanbauk/Daminseik（14.5N）取最南的缅甸节点 MM2 4，泰国端 Ratchaburi 取 TH2 2，与电力统一走廊 MM2 4–TH2 4 不同，故存量链路与候选分列；TTM 用 HVDC 走廊节点对；印尼–新加坡两条经 Batam（ID_Sumatra2 0）。不建模：JDA–Arthit（联合开发区产量已含在马、泰 UNSD 产量内，容量 DATA_PENDING）、中缅管道（出口东盟外）、Trans-ASEAN（搁置）。`research.cross_border.gas = false` 时移除全部 27 条跨境气管道（不互联情景核对通过）。

**2.3 国内生产（第 43 项，VERIFIED 结构 / C 级分配）。** 年产量上限 = UNSD 2019 各国天然气毛产量（D1 `FOSSIL_PRODUCTION_CAPS_2050.csv`）：BN 109.8、ID 727.6、MY 849.5、MM 184.9、PH 43.0、TH 367.2、TL 61.3、VN 103.6 TWh/a；KH、LA、SG 为 0。每个节点一个井口发电机（价格 = 进口价 13.674 EUR/MWh）经交付链路进入节点气母线，链路第二出口按 S2-0 逸散因子（tCO₂/MWh 产量：BN 0.00452、ID 0.00392、MY 0.00445、MM 0.00024、PH 0.00334、TH 0.00513、TL 0.00109、VN 0.00633）记入本国大气；年度上限由 `external_annual_caps` 钩子（`ResearchImportAnnual-*` 约束）执行，共 84 个节点（BN 1、ID 39、MY 7、MM 17、PH 5、TH 6、TL 1、VN 8）。节点分配按各国 AC 节点电力负荷份额（C 级，登记 `gas_production_node_allocation`）：第九批 GEM 表没有坐标，气田/处理厂落点无法登记，留作数据缺口。TL 的 2019 年产量全部出口（UNSD 能源平衡：产量 164,980 TJ = 出口），上限只是可用性上界。

**2.4 LNG（第 17、19 项，VERIFIED）。** 接收站位置与容量取 D1 登记（`LNG_IMPORT_TERMINALS_GEM_2025.csv`，运营 + 在建 = 现有）；每个接收站节点一个进口发电机，p_nom = 现有、p_nom_max = 2.5×；只有拟建的站址 p_nom = 0、p_nom_max = 拟建容量（现有为 0 的处理方式）；无容量数据的站址不建（MY_Peninsular2 0、MY_Peninsular22 0、VN2 4）。价格 WEO 2025 NZE 2050 日本 LNG 到岸价 13.674 EUR/MWh_NCV；再气化加价仍为 DATA_PENDING（本轮按 0），方向：LNG 成本被低估，相对国内生产、管道与非气方案偏向 LNG。接收站扩建不计资本成本（C 级登记 `lng_terminal_expansion_capex`，PyPSA-Eur 固定气入口容量，无可引用的接收站 capex）。

| 节点 | 现有 MW | 拟建 MW | p_nom_max MW |
|---|---|---|---|
| ID_Java-Bali1 0 / 1 2 / Nusa-Tenggara12 0 / Sumatra3 0 | 12,329 / 457 / 533 / 4,566 | 0 | 2.5× |
| ID_Maluku16 0 | 0 | 3,501 | 3,501 |
| KH2 0 | 0 | 1,674 | 1,674 |
| MY_Peninsular2 1 | 11,111 | 0 | 27,778 |
| PH_Luzon9 0 / PH_Luzon5 0 | 22,374 / 0 | 12,177 / 2,283 | 55,936 / 2,283 |
| SG2 0 | 16,743 | 7,610 | 41,857 |
| TH2 3 | 28,919 | 16,438 | 72,298 |
| VN2 5 | 6,088 | 22,770 | 15,221（2.5× 规则，低于拟建） |
| VN2 0 / 2 / 3 / 6 | 0 | 4,566 / 2,283 / 4,566 / 5,175 | = 拟建 |

**2.5 构建结果。** 两情景构建通过（Link 4,805 → 5,020：+111 候选 +14 补全 +6 存量 +84 交付链路；Generator 1,439 = −100 外部气源 +84 井口 +16 LNG；Bus +84 井口）；静态验证通过；年度结构表与 S3-0 相同（气网不改变不可避免 CO₂）。登记表 1,255 行（片段 `gas_network.csv` 29 行）；测试 `tests/research/test_s3_gas_network.py`（3 项）。

## 3. S3-2 东盟外进口（第 17、18、64 项）

代码：`scripts_project/s3_2_imports_data.py`（价格表 `research_inputs/imports_v5/`）、`s3_layers.add_imports`（在气网层之后调用）；配置 `research.s3.imports`；`scenario_network.tag_cross_border` 把国家标签为 `ASEAN` 的全区母线排除在跨境判定之外（第 18 项：油、氨、甲醇不受管网约束）。构建输出 `results_project/s3_2/`（证据 `evidence/s3_2/`）。

**3.1 化石燃料（VERIFIED）。** LNG 经接收站（S3-1，WEO NZE 日本到岸价 13.674 EUR/MWh）。油：一个全区油池母线 `ASEAN oil`，外部进口发电机按 WEO NZE 2050 原油进口价 11.618 EUR/MWh（D1 `fuel_price_oil_NZE_2050_main`），100 个节点油母线经免费双向分配链路接入油池，S2 的 100 个节点外部油源移除；FT/BtL 产出仍在节点油母线上（S3-5 再分化石/非化石）。煤、褐煤：沿用 S2 结构——**分节点**各一个无限量单向外部供给（5.169 / 6.617 EUR/MWh），不互联。燃烧排放仍由消费侧计量链路记入消费国大气。

**3.2 绿色载体价格登记表（第 17 项，+20%；EUR2020/MWh）。** 来源：Neumann 等（arXiv:2404.03927；Nature Communications 2025，doi:10.1038/s41467-025-60652-1）的结果数据集 Zenodo 10.5281/zenodo.14872184 `results.parquet`（CC-BY-4.0，只读获取 2026-10-15T16:18:42Z，SHA 65894a1c…；11.7 MB，不入 git）。取法与 PyPSA-Eur 进口分支（提交 5a87cedd，`add_import_options` 4616–4620 / 4703–4708 行）相同：情景 `default`、年份 2040（数据集仅此一年；正文引用的即这些值：FT 125–132、管道氢 74–88 EUR/MWh）、`Cost per MWh delivered`、按出口地取最小值。

| 载体（esc） | 最低到岸基准 | 最低出口地 | +10% 内出口行数 | 应用价 ×1.20 | 敏感性 ±20% | 模型母线 |
|---|---|---|---|---|---|---|
| 液氢船运 shipping-lh2 | 88.13 | EH（西撒哈拉） | 8 | 105.75 | 84.6 / 126.9 | 16 个 LNG 接收站节点的 `<node> H2` |
| 氨船运 shipping-lnh3 | 97.32 | EH | 17 | 116.78 | 93.4 / 140.1 | `ASEAN ammonia` |
| 甲醇船运 shipping-meoh | 120.97 | EH | 41 | 145.16 | 116.1 / 174.2 | `ASEAN methanol` |
| FT 合成油船运 shipping-ftfuel | 125.09 | CL（智利） | 77 | 150.11 | 120.1 / 180.1 | `ASEAN oil non-fossil` |
| 参考：管道氢 / 绿色 LNG / HVDC 电 | 73.79 / 121.77 / 40.05 | EH | — | — | — | 不建（无陆路出口通道 / LNG 已按化石价 / 非进口选项） |

正文页码：arXiv v1 p.12（管道氢 ≈57、船运氢 84、衍生物 88–110、甲醇低于 FT）与 p.15 表 A.1（FT 参考 109.8，2050 假设）；Nature Communications 正文（FT 125–132、管道氢 74–88、船运氢比最低管道供应高 18%、十个地区在最低成本 +10% 内）。两组数字差别来自 2040 vs 2050 技术成本假设，本轮采用已发表（2040）数据集值并登记（B 级）。**代表性（INFERENCE，C 级登记）：** 数据集给的是到欧洲入口的成本，最低出口地（西撒哈拉、智利、阿根廷）离欧洲和东盟都远，海运在到岸成本中占比小，且有多个地区落在最小值 +10% 以内（智利之外还有十个），因此"欧洲最小值 ×1.20"作为东盟代理；论文没有东盟供给曲线。两个情景同一组价格；只进不出（全部为发电机）；开关 `research.s3.imports.price_sensitivity`（−0.2 / 0 / +0.2）。

**3.3 接收站。** 液氢按 PyPSA-Eur 进口分支的做法进 LNG 接收站节点（`translate` 字典 shipping-lh2 → lng，约 4540 行）：p_nom_max = 该节点 LNG 接收能力（现有 ×2.5 或拟建），终端资本成本 7,018 × 1.2 = 8,421.6 EUR/MW/a（4560–4563 行）；现有氢接收能力为 0 的处理方式即"借用 LNG 站址与容量上限，按终端成本付费"。氨、甲醇、FT 油按 PyPSA-Eur 的 copperplated 处理（全区母线，无容量约束）。

**3.4 碳处理（第 64 项）。** 进口绿色载体在进口国记零：进口发电机没有 CO₂ 端口，载体 `co2_emissions = 0`。PyPSA-Eur 进口分支的做法：进口链路对含碳载体加一个到大气的负系数端口（`co2_intensity` 字典 4553–4557 行；`efficiency2 = -CO2 intensity` 4659–4665、4711–4717 行），即把出口国 DAC 的碳作为进口方的负排放记入，燃烧时再按消费侧排放，净零。本模型用非化石母线（燃烧侧 EF 0、生产侧不记信用）实现同样的净结果，避免把负排放记到无法归国的全区母线（S3-5 详述）。

**3.5 构建结果。** 两情景构建通过（Link 5,020 → 5,120：+100 油池链路；Generator 1,439 → 1,359：−100 节点外部油源 +1 油进口 +3 绿色载体进口 +16 液氢进口；Bus +4 全区母线）；跨境标记：油池链路全部 domestic；静态验证通过；结构表与 S3-1 相同（`s2_structural_gap.py` 已排除 `ASEAN` 池行）；登记表 1,274 行（片段 `imports.csv` 19 行）；测试 376 通过 / 4 基线失败（新增 `test_s3_imports.py` 2 项）。

## 4. S3-3 氨与甲醇

（待填）

## 5. S3-4 航运

（待填）

## 6. S3-5 燃料碳归属（第 64 项）

（待填；模式对比与 SG 船用甲醇算例）

## 7. S3-6 V5 门槛

（待填）

## 8. S3-7 构建与冒烟

（待填）

## 9. 天然气数据缺口清单

| 项 | 状态 | 处理 | 影响方向 |
|---|---|---|---|
| Malaysia–Singapore 管道容量（GEM 无） | DATA_PENDING（下载清单） | 只有 MY_Peninsular2 1–SG2 0 走廊候选，无存量 | 低估新加坡既有进口能力 |
| JDA–Arthit 管道容量（GEM 无） | DATA_PENDING | 不建跨境链路；JDA 产量已含在马、泰 UNSD 产量 | 无直接影响 |
| LNG 站址缺容量（MY 3 个单元、VN 6 个、ID 1 个） | DATA_PENDING（D1 清单保留） | 不建或按已知单元建 | 低估 MY/VN 接收能力 |
| 再气化加价 | DATA_PENDING | 0 | LNG 成本低估 |
| 国内生产的节点分配 | C 级（负荷份额） | GEM 第九批无坐标；GIS 路由文件未提供 | 气田所在节点的供给被摊平 |
| 接收站扩建 capex | C 级（0） | 无可引用来源 | 扩建偏便宜 |
| bcm→MW 换算 | B 级（PyPSA-Eur 1,199 MW/bcm × 0.90） | GCV/NCV 口径差 ±10% | 管道容量 ±10% |
| TL 产量全部出口 | 已注明 | 上限保留 | TL 国内可用气可能高估 |
| Yadana 1 / Zawtika 跨境判定 | B 级（落地点 + 泰国境内段 12.93 bcm/a 交叉核对） | 建为 MM2 4 → TH2 2 | — |

## 10. 测试、证据与交付

（待填）

## 11. 待用户决定的事项

（待填）
