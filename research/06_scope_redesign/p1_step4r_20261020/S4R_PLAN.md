# S4R 方案：统一修正方案与门槛重设（第 126、128 项；只读，不实施、不求解）

## 摘要（≤ 20 行）

1. **范围：** 指令 SHA256 `f80da6fd…ceeb` 核对一致；分支 `codex/s4r-unification-plan-20261020`（自 S4P 头 69b67a97，独立工作树），draft PR 叠在 #42 上。只读：未求解、未连云、未调用 Gurobi、未改生产代码与注册表；修正只写成方案，经面谈后在 M08 实施（`IMPLEMENTATION_PLAN.md`）。
2. **R1 需求（最重要）：** 同口径分解显示 S4P 偏差的主因是**工业路线全电化**（固定电力负荷 = AEO8 ATS 电力的 1.7–4.2×；需求表电力只高 0.7–1.5×）与**BAS 锚定**（模型 TFEC 1,220 Mtoe vs AEO8 BAS 1,108 / ATS 746）。推荐主锚 **AEO8 ATS 人均 × 人口（10 国 + TL 规则）**，对照 ERIA RPR FY2024 LCET-CN；工业物理产量按 11 国同一规则（基年 USGS / worldsteel × √总 GDP 增长，人均饱和上限，国家规划上限）：**VN 水泥 581 → 107 Mt，钢 80 → 70 Mt**；"其他工业"能耗与生物质溢出改为分温度带的有用热、载体内生（与 R4 同一规则，偏离 PyPSA-Eur 的固定路线，理由写明）。
3. **R2 潜力：** 模型光伏上限 / ESMAP Level-1 × 5.1 MW/km² 的比值 0.18–0.57（11 国全部 < 0.6）→ **系统性偏低**，可由功率密度（4.6 vs 5.1）与土地类别（全部林地与保护区排除）解释；推荐 11 国同一参数：密度 5.1（PyPSA-Eur）+ 开阔林 121–126 计入 + PyPSA-Eur 海上规则（60 m、漂浮、航道排除、5.5 MW 机型、0.8855 尾流）；调整后估算 VN ≥ 456 GW（仅密度）至 936 GW（ESMAP L1 上限）。海上风电 F9 校准方法同陆上 alpha，观测数据 DATA_PENDING。
4. **R3 LNG：** 模型表与 GEM GGIT 2025-09 一致；2025 年实际进口仅为运营容量的 12–55 %；7,018 EUR/MW/a **无来源无价格年（DATA_PENDING）**，推荐改用已登记的 Ulvestad 2012 换算值 8,020 EUR2020/MW/a（±50 %）；推荐**取消 2.5× 上限、按成本内生扩建**（与 F3 / F8 同口径）；再气化加价 1.26 EUR2020/MWh（0.5 USD/MMBtu，Argus 2024）。
5. **R4 生物质溢出：** PyPSA-Eur 没有溢出规则（ENSPRESO 潜力 > 需求；`solid_biomass_import` 缺省关闭）；推荐 11 国同一规则：溢出按等量有用热、分温度带由模型选择载体；第 36 项贸易规则保留（跨境生物质作敏感性），第 115 项 0.98 不再需要。
6. **R5 封存：** 统一 ERIA-GCCSI 2024 P50：VN 11.8 → 5.30 Gt（年上限 236 → 106 Mt）、PH 22.3 → 0.067 Gt；KH 取 IJGGC 2014 低值 0.09 Gt；TL / LA / MM 零（UNASSESSED）；年上限 = 潜力 ÷ 50 不变；30 EUR/t 价格年 DATA_PENDING。
7. **R6 成本与货币：** 消除 +4.8 % 平减残余（改用 HICP 回算）；AEO8 D.15 价格年 DATA_PENDING（敏感性 × 0.86）；核电同源：大型核电 technology-data（PyPSA-Eur 做法），SMR = 其 × AEO8 同表比值 1.067（修正"SMR 比 PWR 便宜"）；报告货币 **USD2020，1 EUR2020 = 1.1422 USD2020**；分国实际 WACC 表（IEA + Damodaran + IMF 通胀）：VN 4.6 %、ID 7.1 %、MY 4.4 %、TH 5.3 %、SG 2.9 %、KH 9.1 %、LA 7.6 %、MM 11.0 %——统一 7 % 对 VN / MY / PH / SG 偏高、对 KH / LA / MM 偏低（只做表）。
8. **R7 不互联定义：** 现行 = 删除全部区域内跨境固定网络（含 2025 存量，含 ID–SG / MM–TH / MY–TH 现有气管道），保留液体池、CO₂ 船运与区域外进口；推荐登记为主定义，"保留存量不新建"作敏感性；是否把船运类贸易视作互联由用户与师哥决定。
9. **R8 门槛：** `GATES_V6.md`（SHA256 `5c0aa8b8…7f9`，先于重评单独提交 d45955ea）：判据只有 C1 (a)(b)(c) + 结构检查（网络 SHA256、配置子集哈希、结果完整性），其余全部为诊断且容差随档案（对偶预算 10 × max(OptimalityTol, BarConvTol)）。重评：C1 可计算的 10 次运行（S4N 试点、S4O-6 ×3、S4Q ×6）全部 **ACCEPTED_LAYER2**（G2.2 子集哈希未导出，标 pending）；L23 / S4M-2 / S4N-C2 无 PRECISION → 不可计算。诊断 D2 在 V6 预算下仍对全部 365×24h 内点解与 1e-6 候选超预算（对偶符号误差 ≈ 100 × BarConvTol），**按规则未修改定义**，提请用户决定 D2 的 k（§R8）。
10. **R10 影响（INFERENCE）：** R1 为上游，使系统规模下降约 30–50 %；R1 + R2 + R3 + R4 合并后 B6 预计从 69 bn 降至约 25–45 bn，VN 份额约 55–70 %（仍最大）；R5 对差额 ±2 bn；R6 −2 bn；R7 −3–6 bn；分国 WACC 若采用：VN 差额 −10–15 bn、B6 再降。第三批（M10）建议 7 次运行（修正后 365×24h ×2、1e-6 第二级 ×4、2920×3h 探针 ×1），约 10–20 h。
11. 两张清单见 §11（需要用户决定 12 项、需要请示师哥 7 项）；用户下载清单 `USER_DOWNLOAD_LIST.md`（9 项）。

## 1. 前提（第 2 节已定口径，不再讨论）

2920×3h 正式分辨率；F3 每条 +20 GW 无国家对上限；F8 核电 / SMR 无政策上限；F7 主算统一 WACC 0.07；报告美元、模型欧元（第 125 项）；NZE 舍弃（第 124 项）；验收按 C1 分级；1e-6 第二级在第三批；F6 并列报告、F12 / F13 登记。

## 2. R1　需求重新锚定（F4）

### 2.1 同口径分解（`DEMAND_ANCHOR_COMPARISON.csv/.md`）

| 国 | (a) 基础电 | (b) 工业电（路线） | EV | (c) 固定电合计 | 需求表电力 | AEO8 ATS 电力 | 固定 / ATS | 表电 / ATS | 模型 TFEC | ATS TFEC | 模型 / ATS | 模型 / ERIA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VN | 197 | 964 | 82 | 1,253 | 712 | 507 | 2.47 | 1.40 | 220 | 154 | 1.43 | 1.83 |
| ID | 301 | 1,801 | 169 | 2,274 | 622 | 557 | 4.08 | 1.12 | 405 | 286 | 1.42 | 1.12 |
| TH | 209 | 473 | 242 | 947 | 501 | 352 | 2.69 | 1.42 | 271 | 136 | 2.00 | 1.86 |
| MY | 140 | 426 | 171 | 743 | 370 | 276 | 2.69 | 1.34 | 162 | 68 | 2.38 | 1.31 |
| PH | 104 | 102 | 91 | 299 | 195 | 174 | 1.72 | 1.12 | 76 | 55 | 1.38 | 1.18 |
| SG | 41 | 101 | 11 | 153 | 86 | 67 | 2.28 | 1.28 | 35 | 13 | 2.75 | 0.95 |
| MM | 15 | 81 | 11 | 116 | 26 | 28 | 4.17 | 0.94 | 26 | 13 | 1.96 | 0.80 |
| KH | 17 | 13 | 25 | 58 | 33 | 22 | 2.63 | 1.51 | 17 | 16 | 1.09 | 1.05 |
| LA | 5 | 7 | 6 | 18 | 14 | 21 | 0.88 | 0.66 | 5.4 | 5.6 | 0.97 | 0.79 |
| BN | 3 | 2 | 2 | 7.5 | 4.4 | 4.5 | 1.67 | 0.98 | 2.2 | 0.7 | 3.07 | 0.75 |
| TL | 0.9 | 0 | 0.9 | 1.8 | 0.9 | 2.3（规则） | 0.79 | 0.39 | 0.41 | 0.99（规则） | 0.41 | — |

（TWh / Mtoe；TL 的锚按 KH / LA / MM 均值 × UN WPP 人口规则。）

**口径差 vs 活动水平偏高的拆分（INFERENCE）：** 以 VN 为例，S4P 报告的"电力 +147 % vs 712"与"TFEC +83 % vs ERIA"中：① 口径差（净零下的工业路线电气化：工业电 964 TWh 来自 1,043 TWh 工业煤的路线转换）占电力偏差的约 2/3（1,253 − 712 = 541 TWh）；② 活动水平偏高（BAS 锚 vs ATS：TFEC 1.43×；工业乘数 4.6× vs ERIA 2.0×）占其余 1/3（712 vs 507 = +40 %）；③ 原料计入（非能源用途 70 TWh）影响小。ID 的"+157 %"几乎全是①（表电力 622 vs ATS 557 只高 12 %）。TH / MY 两者各半。SG / BN 的 TFEC 偏差来自非能源用途（石化原料 163 / 12 TWh），属口径差。

### 2.2 锚的选择

| 候选 | 覆盖 | 部门 / 年份 | 情景定义 | 与本模型契合 | 评价 |
|---|---|---|---|---|---|
| **ACE AEO8 (2024) ATS** | 10 国（无 TL）；人均 TFEC / 电力按国；部门总量按区域 | 2022–2050，5 部门 | 成员国已宣布目标（RE 份额、EE） | 本模型为每国净零 + STEPS 燃料价：活动水平宜取"目标"而非"基线"；AEO8 为东盟官方展望，项目已用其 ATS 相对因子 | **主锚（推荐）** |
| AEO8 BAS | 同上 | 同上 | 无新政策 | 现行锚；比 IEA STEPS 高 29 %（1,108 vs 860 Mtoe） | 上界敏感性 |
| ERIA RPR FY2024 LCET-CN | 10 国（TL 不详） | TFEC、发电 2050，部门有 | 碳中和 2050 | 与净零一致，但 LCET-CN 含载体结构（氢 46 % 发电等），锚活动量时需剥离 | **对照** |
| IEA SEAEO 2024 / WEO 2025 | 区域 | 2050 STEPS / APS | — | 无国别 | 区域合理性 |

**锚定方法（11 国同一）：** 国家 2050 TFEC = AEO8 C.8 ATS 人均 × D.1 人口；电力 = C.8 ATS 人均电力 × 人口（作为"基础电 + 工业电 + EV"之和的锚，路线电力从中扣除后得基础负荷）；部门份额 = AEO8 C.3 ATS 区域部门比例 × 各国 2019 部门结构的归一化（现行 k_sector 做法保留）；载体结构不锚定。TL：人均 = KH / LA / MM 均值，人口 UN WPP 2024（1.889 M，原文件 DATA_PENDING）。

### 2.3 工业物理产量（11 国同一规则；`DEMAND_ANCHOR_COMPARISON.csv` 第 b 组）

规则：2050 产量 = 基年产量（USGS 水泥 2019；worldsteel 粗钢 2019）× √(AEO8 总 GDP 增长 2022→2050，D.6 × D.1)，再取 min(人均饱和 × 2050 人口, 国家规划上限)。饱和水平：水泥 1.0 t/cap/a、粗钢 0.6 t/cap/a（INFERENCE：VN 钢铁战略 2050 人均成品钢 570–650 kg；水泥取 VN 2024 实际 1.1 t/cap 的近似上限）。二选一说明：选"人均饱和"为通用规则（11 国可用、不依赖各国是否有规划），国家规划上限只在存在时作第二道上限。

| | VN | ID | TH | MY | PH | KH |
|---|---|---|---|---|---|---|
| 水泥 现 → 建议（Mt） | 581 → **107**（人均上限；Decision 1266 ≤ 150 不绑定） | 313 → 148 | 160 → 68（人均上限） | 57 → 33 | 107 → 63 | 42 → 14 |
| 粗钢 现 → 建议（Mt） | 80 → **70**（Decision 261 65–70） | 28 → 13 | 14 → 7 | 20 → 12 | 6 → 4 | 0 |

AEO8 D.3 工业 GDP 对 MY / PH / SG / TH 印为负增长，不作驱动（登记）。氨 / 甲醇 / HVC：沿用 PyPSA-Eur 的 2050 路线份额（HVC_primary 0.4），活动量按 ATS 工业能耗缩放（现行 EU27 份额法保留）。

### 2.4 工艺路线与电气化率

现用 `pypsa_eur_2050`：JRC-IDEES 2050 比率把全部工业能耗按欧盟 2050 路线转为电 / 氢 / 甲烷 / 生物质 / 热。PyPSA-Eur 本身**不增长产量**（`build_industrial_production_per_country_tomorrow.py` 只重分配今日产量：St_primary_fraction、DRI_fraction、HVC_primary_fraction），其比率用于欧洲净零路线。对东盟：① 物理产量部门（钢、水泥、氨、甲醇、HVC）保留 PyPSA-Eur 2050 路线（统一、可追溯）；② "其他工业"回退桶（VN 1,043 TWh 煤的大部分）改为**有用热分温度带**（<150、150–400、>400 °C，JRC-IDEES 温度分布，C 级），由模型在电锅炉 / 热泵（仅低温）/ 氢锅炉 / 甲烷锅炉 / 生物质锅炉间内生选择——偏离 PyPSA-Eur，理由：东盟工业基础是煤与生物质热，固定欧盟路线使工业电力达 ATS 的 1.7–4.2×；用 ERIA LCET-CN 工业电力份额（ID 2050 20 %）作校准对照。11 国一致。

### 2.5 需求变体

现有：`growth_method` ratio / level；`country_allocation` aeo8_ats_relative / gdp / population；`industry.other_bucket` pypsa_eur_2050 / idees_today / asean_own_2019；`carrier_mode`。推荐主算：`growth_method: ats_anchor`（新）+ `other_bucket: useful_heat_bands`（新）；敏感性：BAS 锚（上界）、population 分配、pypsa_eur_2050 路线（现行）。

### 2.6 预计影响与偏差目标

锚定后同口径指标与 ATS 的偏差按构造为 0（TFEC、电力总量）；物理产量 ≤ 人均上限。全系统规模约 −30–50 %（TFEC 1,220 → 746 Mtoe；固定电力 5,870 → 约 2,000–2,500 TWh + 内生电气化）。B6 与分国差额按规模近似线性下降，且 VN 的光伏 / LNG 上限不再同时绑定（见 R10）。

## 3. R2　可再生潜力（F1、F9）

### 3.1 现有布局参数 vs 缺省（S4A §1.1–1.2 已核；本步复核）

| 参数 | 本模型（PyPSA-Earth / pypsa-asean） | PyPSA-Eur v2025.07.0 | PyPSA-Earth 缺省 | 偏离 |
|---|---|---|---|---|
| 光伏密度 | 4.6 MW/km² | 5.1（第 270 行） | 4.6 | 偏低 10 % |
| 光伏可用类 | Copernicus 20/30/40/50/60/90/100（灌木、草本、耕地、**城市**、裸地、湿地草本、苔藓）；排除全部林地 111–126 | CORINE 1–20、26、31、32（人工 + 农业 + 草地 + 裸岩）；排除林地 23–25 | 同本模型 | 规则同型；东盟林地占比高 → 影响大 |
| 保护区 | natura（WDPA）排除 | natura 排除 | natura | 相同；ESMAP L1 不排 |
| 光伏修正系数 | 0.854（作者）；`pypsa_eur` 变体 1.0 | 无 | 0.854 | 主算用 1.0（S4B-3） |
| 陆上风 | 3 MW/km²，V112 / DEA2050 + alpha | 3，V112 | 3 | 相同 |
| 海上风 | 水深 ≤ 50 m，AC/DC 按 30 km，密度 2/3，NREL 5 MW，无航道排除、无漂浮 | 固定 ≤ 60 m、漂浮 60–1,000 m、`ship_threshold 400`、2 MW/km²、2020ATB 5.5 MW、尾流 0.8855 | 同本模型 | 多项偏离 |
| 屋顶光伏 | 作者底座候选（S4A，C 级，无方法记录） | 无（PyPSA-Eur 用 solar-rooftop 技术但潜力来自 ENSPRESO） | — | 口径登记 |

### 3.2 对照（`POTENTIAL_COMPARISON.csv/.md`）

| 国 | 模型光伏 | ESMAP L1 份额 | ESMAP L1 × 5.1 | 模型 / ESMAP | 模型隐含用地占国土 | Zhong 高 / 中 | 官方 |
|---|---|---|---|---|---|---|---|
| VN | 411 | 59 % | 936 | 0.44 | 29 % | 2,847 / 94 | 963 |
| ID | 859 | 33 % | 3,016 | 0.28 | 10 % | 1,052 / 208 | 3,294 |
| TH | 1,108 | 75 % | 1,962 | 0.57 | 47 % | 10,538 / 23 | — |
| MY | 78 | 26 % | 428 | 0.18 | 5 % | 1,965 / 59 | 269 |
| PH | 299 | 46 % | 696 | 0.43 | 22 % | 1,910 / 45 | 58 |
| KH | 359 | 77 % | 695 | 0.52 | 44 % | 3,198 / 8 | — |
| MM | 826 | 52 % | 1,725 | 0.48 | 28 % | 7,717 / 30 | — |
| LA | 119 | 36 % | 429 | 0.28 | 11 % | 1,278 / 9 | — |
| SG / BN / TL | 0.4 / 1.4 / 9.6 | 49 / 12 / 63 % | 1.8 / 3.2 / 47.7 | 0.25 / 0.44 / 0.20 | 14 / 6 / 14 % | — | — |

**判断：系统性**（11 国全部 < 0.6，中位数 0.43；林地占比高的 ID / MY / LA 最低）。可由两个参数解释：密度 4.6 vs 5.1（×1.11）与土地类别（全部林地 + 保护区排除 vs ESMAP L1 只排密林 > 50 % 郁闭度、不排保护区）。Zhong "高"值（NREL 2022 技术潜力，无排除）高出 ESMAP 3–10×，"中"值为政策文件（PDP8 等），不作上限。

### 3.3 方案（11 国同一参数，不逐国改上限）

1. 光伏密度 5.1 MW/km²（PyPSA-Eur v2025.07.0 第 270 行；依据 DEA / NREL 用地密度）。
2. 光伏可用类加入 Copernicus 开阔林 121–126（郁闭度 15–70 %），保留密林 111–116、水体、保护区排除（ESMAP Level 1 的"密林 > 50 %"口径转译；PyPSA-Eur 的 CORINE 无开阔林类，属有理由的偏离）。
3. 调整后估算：仅密度 ×1.11（VN 456、ID 953、TH 1,230、MY 86 GW）；加开阔林后介于此与 ESMAP L1 × 5.1（VN 936、ID 3,016、MY 428）之间，精确值需栅格重算（Copernicus LC100 + WDPA 下载，见 `USER_DOWNLOAD_LIST.md`；M08-7）。
4. 陆上风：参数与 PyPSA-Eur 相同（3 MW/km²），不改；对照 Zhong 高值（模型 VN 577 vs 311、TH 580 vs 239、ID 3,950 vs 61——模型高）只作记录；低 CF 候选不会被建。
5. 海上风：对齐 PyPSA-Eur（60 m、漂浮 60–1,000 m、航道排除、2020ATB 5.5 MW、尾流 0.8855、2 MW/km²）；对照 WBG-ESMAP 技术潜力：VN 636 vs 599（1.06）、PH 280 vs 181、ID 2,786 vs 277（10×，未建）、KH 47 vs 0.13；MY / TH / BN / MM / TL / SG 在 ESMAP 无行（EEZ 无 ≥ 7 m/s），模型候选 CF 0.08–0.22 本批未建 → 无结果影响；各国现有规模与 2050 展望（VN 113–139 GW）只作对照。
6. **F9 海上廓线校准：** 方法同 S4B-3（ERA5 100 m 风速 × 国别 alpha，按 Ember 实测发电校准）；东盟并网海上风电几乎只有 VN 近岸 / 潮间带项目（Bac Lieu、Tra Vinh），Ember 国别海上发电量未单列 → 观测 CF **DATA_PENDING**；替代：世行越南路线图（2021）的净容量因数假设（页码 DATA_PENDING）或 GWA 海上 CF 图层作偏差缩放；数据到位前 alpha = 1.0 并在报告标注模型 CF 0.44–0.58 未校准。

预计影响：VN 不互联少建海上风 / SMR / 进口氢，差额 −15 至 −25 bn（F1）；在 R1 之后按比例缩小。

## 4. R3　LNG（F2、F12）

### 4.1 接收站容量（`LNG_CAPACITY_COMPARISON.csv/.md`）

模型表（GEM 2025-08）与 GEM GGIT 2025-09 逐国一致（运营 + 在建：ID 11.75、PH 14.7、TH 19.0、SG 11.0、MY 7.3、VN 4.0 Mtpa；拟建 KH 1.1、VN 25.86、TH 10.8、PH 9.5、SG 5.0、ID 2.3）。GIIGNL 2026 交叉核对：2025 年进口 TH 10.5、SG 5.7、ID 5.3、MY 2.3、PH 1.9、VN 0.5、MM 0.04 MT（运营容量利用率 12–55 %）；VN Thi Vai 1 → 3 MTPA 扩建中、Cai Mep 3（可扩 6）2025-06 投运，TH Map Ta Phut 3 5 → 10.8 MTPA（2029）。换算：1 Mtpa = 13.333 TWh/a = 1,522 MW。模型上限（2.5 × 存量 + 拟建）：VN 20.9、MY 18.3、ID 31.7、PH 38.3、SG 27.5、TH 47.5 Mtpa 当量；GEM 项目口径（运营 + 在建 + 拟建）：VN 29.9、TH 29.8、PH 24.2、SG 16.0、ID 14.1、MY 7.3、KH 1.1。

### 4.2 码头扩建成本 7,018 EUR/MW/a

依次查：PyPSA-Eur import 分支代码（`prepare_sector_network.py` 第 4560–4562 行：`"shipping-lch4": 7018,  # €/MW/a`，无来源注释）；technology-data v0.15.0（无 LNG 码头 / 再气化行，只有 LNG storage tank 838 EUR/m³ 与 CH4 liquefaction）；DEA 运输目录（检索未见 LNG 进口码头行）；IEA / OIES（未得公开单位成本）→ **DATA_PENDING**。替代：注册表已登记的 Ulvestad & Overland 2012 换算值 **8,020 EUR2020/MW/a**（100 USD/tpa，2011 年价假定，美国 GDP 平减 + ECB 2020 汇率；寿命 25 年、WACC 0.07 的年金 + 3.5 % FOM，`LNG_EXPANSION_EVIDENCE_S3B_R3.json`），±50 % 敏感性；H₂ 码头 = LNG × 1.2（沿用 PyPSA-Eur 相对关系）。

### 4.3 2.5× 上限的去留

| 选项 | 内容 | 评价 |
|---|---|---|
| **(a) 取消上限**（推荐） | 码头按有出处的成本内生扩建（`lng_expansion: capex_only`） | 与 F3 / F8"技术潜力口径、由模型选择"一致；码头单位成本（8,020 EUR/MW/a ≈ 0.9 EUR/MWh 满负荷）对结果影响小 |
| (b) GEM 项目口径上限 | 运营 + 在建 + 拟建 | 口径统一但"拟建"状态易变（VN 拟建 25.9 中 6 个单元无容量） |
| (c) 维持 2.5× | 现行 | 任意倍数；在 VN / MY / KH 三情景绑定，是 F2 的直接原因 |

预计影响：VN 不互联 −20 bn（220 TWh 进口氢制甲烷 → LNG + CCS / 船运）；MY 不互联气产自用（+13 bn）部分改为进口（−3–5 bn）；KH 小；TH 作为区域气枢纽的出口收入（14.2 bn）减少。

### 4.4 F12 再气化加价

观察值 0.3–1.3 USD/MMBtu（日本 ≈ 0.5、印度 0.75、Gate 0.35、中国 0.7–1.3；Argus 2024；Höegh / IGU 2017 0.3）→ 推荐 0.5 USD2024/MMBtu = **1.26 EUR2020/MWh**（× 0.73606 ÷ 0.29307 MWh/MMBtu）；东南亚专门值 DATA_PENDING。影响 < 0.5 bn。

## 5. R4　生物质溢出（F5）

PyPSA-Eur v2025.07.0：工业固体生物质需求为固定载体需求（`solid biomass for industry`），潜力来自 ENSPRESO（欧洲潜力 > 需求），`biomass_spatial: true`、`biomass_transport: false`、`solid_biomass_import.enable: false`（54 EUR/MWh、1,390 TWh 上限，缺省关）——**没有"需求 > 潜力"的处理规则**，因为欧洲不会出现；出现时模型不可行。东盟 VN / SG / BN 需求 > 潜力（VN 2.7×），本项目第 36 项把溢出改为固定甲烷需求（233 TWh）。

**统一规则（推荐）：** 溢出部分按等量有用热（溢出生物质 × 锅炉效率 0.90）进入其来源温度带（工业生物质 → 中 / 高温带；农业 → 低温带），由模型内生选择载体：电锅炉 0.99、热泵 COP 3.2（仅低温）、氢锅炉 0.90、甲烷锅炉 0.94、生物质锅炉 0.90（technology-data 行）。实现：`s3_0_industry.py` 输出三段有用热，`s2_layers.py` 新增 `industry heat medium / high` 母线与链路（M08-6）；配置键 `s2.industry.biomass_overflow_mode: useful_heat`。与第 36 项的关系：贸易规则（不跨境）保留，跨境生物质运输作敏感性（PyPSA-Eur `biomass_transport` 成本）；第 115 项 0.98 上限不再需要（固定需求不再等于潜力）。与 PyPSA-Eur 的偏离：固定载体 → 内生载体；理由：PyPSA-Eur 无此情形。预计影响：VN 不互联 −7 bn（与 R3 重叠），一体化 −3 bn。

## 6. R5　CO₂ 封存（F10；`CO2_STORAGE_UNIFIED.csv`）

| 国 | 现值 Gt（来源） | 统一值 Gt（ERIA-GCCSI 2024 P50 + 油气田；表号 / 页） | 年上限 Mt（÷ 50） |
|---|---|---|---|
| MY | 128.8（ERIA） | 128.8（T1.9 / 1.7 p.26；范围 81.8–198.8） | 2,575 |
| ID | 51.3（ERIA） | 51.3（T1.6 / 1.4 p.14–15；34.3–77.3） | 1,026 |
| BN | 18.6（ERIA） | 18.6（T1.12 p.35；13.6–25.6） | 372 |
| TH | 16.0（ERIA） | 16.0（T1.14 / 1.13 p.40；12.0–23.0） | 320 |
| **VN** | 11.8（IEA 2021 = ADB 2013 理论值） | **5.30**（T1.17 / 1.15 p.47；3.3–9.3） | **106** |
| **PH** | 22.3（IEA 2021） | **0.067**（T1.18 p.53，仅 Malampaya） | 1.3 |
| KH | 0.085（OGCI，不可复核） | 0.09（IJGGC 2014 预评估低值；高值 45 Gt 作敏感性） | 1.8 |
| TL | 0.25（OGCI，不可复核） | 0（DATA_PENDING；Bayu-Undan 10 Mtpa 项目作敏感性） | 0 |
| LA / MM / SG | 0 | 0（LA / MM 登记 UNASSESSED；SG 无潜力） | 0 |

封存成本 30 EUR/t：PyPSA-Eur 配置常数，价格年 DATA_PENDING（基准 GCCSI 2025 离岸 US$5–31/t、ERIA 2022 US$12.9/t）；注入爬坡只记录（Kasawari 3.3、Arthit 1 Mtpa、Tangguh 15 Mt 累计）。影响：VN 两情景各 +8–10 bn（DAC / 船运替代 130 Mt），差额 ±2；PH +2–4 bn；均不设政策上限。

## 7. R6　成本与货币（F14、核电、F7 准备；`COST_CURRENCY_FIXES.csv`、`COUNTRY_WACC_SENSITIVITY_TABLE.csv`）

1. **+4.8 % 残余：** technology-data 用 Eurostat HICP 把 2020 源值升到 EUR2025（+25.7 %），本项目用 EA20 GDP 平减回算（÷ 1.20）。推荐用同一 HICP 指数回算（`s2_0_cost_layer_v015.py rebase()` 的 deflator 改为 `prc_hicp_aind`），或直接取 technology-data 的 2020 源值；影响 B6 −1.8 bn。
2. **AEO8 D.15 价格年：** 附录 D.3 正文（p.195）与表均无年份，报告其他表用 2017 PPP 美元 → DATA_PENDING；处理：敏感性因子 [0.86, 1.00]（USD2023 → USD2020 = 0.887）。
3. **核电同源：** 现行大型核电 technology-data（Lazard USD2023 → EUR，混合通胀）9,003 EUR/kW，SMR AEO8 8,421（无年）→ SMR 反而便宜 6.5 %，与文献相反（EIA 2024 SMR 8,936 vs AP1000 7,861 USD2023/kW；INL 2024 SMR 中等 4,000 vs 大堆 3,750 USD2022/kW，SMR 高 7–14 %）。推荐：大型核电沿用 technology-data（PyPSA-Eur 做法），SMR = 大型核电 × AEO8 同表比值（9,600 / 9,000 = 1.067；FOM 比 1.37；VOM 比 0.43）——比值不依赖价格年；INL / ATB 2024 作敏感性集。结果 SMR 9,603 EUR/kW（+14 % vs 现）。
4. **无来源常数：** 码头 7,018（DATA_PENDING → 8,020）、封存 30 EUR/t（年 DATA_PENDING）、H₂ 码头 × 1.2（PyPSA-Eur 相对关系）；均登记。
5. **报告货币：** USD2020；单一汇率 **1 EUR2020 = 1.1422 USD2020**（ECB 2020 年均参考汇率，注册表 `fx_usd_to_eur_2020` 倒数）；如需 USD2024 再 × 1.1918（FRED A191RD3A086NBEA）。全文只用这一个汇率。
6. **F7 表：** 名义 WACC（IEA 观测站 2024 光伏中点：ID 9.75、VN 9.25、PH 7.75、TH 7.0、MY 6.5 %；其余 = MY 6.5 % + Damodaran 风险溢价差：SG 4.95、BN 5.73、KH 12.1、LA 16.6、MM 20.5 %）÷ IMF WEO 2026-10 通胀（2028–30 均值）→ 实际：ID 7.1、VN 4.6、PH 4.5、TH 5.3、MY 4.4、SG 2.9、BN 4.7、KH 9.1、LA 7.6、MM 11.0 %，TL DATA_PENDING。30 年年金比（国别 / 0.07）：VN 0.77、MY 0.75、SG 0.62、KH 1.21、MM 1.43。只做表，不跑。

## 8. R7　"不互联"的定义（F11）

现行（构建网络对比，VERIFIED）：删除全部区域内跨境固定网络组件——62 条线路、292 条链路（气管道 117 含现有 ID–SG 8,795 / MM–TH 13,845 / MY–TH 11,244 MW；氢管道 110；CO₂ 管道 55；直流 10）；保留区域液体池、CO₂ 船运（504 + 48 条）与全部区域外进口（两情景同集合、同价、同上限）。

| 议题 | 讨论 | 建议 |
|---|---|---|
| (a) 现有跨境设施是否删除 | 研究问题是"互联的成本责任分摊"：删除存量给出"完全不互联"的上界反事实；保留存量给出"不再新建"的增量口径 | 主定义：删除（现行，口径最清晰）；敏感性：保留 2025 存量、不新建 |
| (b) 船运贸易是否属互联 | 液体燃料池与 CO₂ 船运不需固定跨境基础设施，是全球市场的一部分；但 VN 不互联时从池购 40 TWh 非化石油品、MM 卖 25 bn 甲醇都属区域内贸易 | 保留在两情景（现行），在报告中把池内区域贸易额单列；是否视作互联由用户与师哥定 |
| (c) 区域外贸易一致性 | 已核：进口集合、价格、上限两情景相同（S4P §4.1） | 保持；在注册表写明 |

注册表行草案：`disconnected_definition_main`、`disconnected_definition_sensitivity`（`REGISTRY_ROWS_PROPOSED.csv`）；配置键 `cross_border.stock_mode`（M08-8）。影响：保留存量敏感性 B6 −3–6 bn（SG / TH / MY 气管道）。

## 9. R8　门槛重设（第 128 项）

- 定义：`GATES_V6.md`（SHA256 `5c0aa8b8ed322b75a63879fccfc19559606a0ad743ecafee3addfcbfe04fd7f9`，提交 d45955ea，先于重评）。要点：判据 G1 = C1 (a)(b)(c)（原文不变）+ G2 结构检查（网络 SHA256 / A4 读回；**配置子集哈希**替代整份 B12；结果完整性）；其余（原始 / 对偶残差、间隙、物理方程、净零、封存 / 码头 / 产量上限、需求守恒、路线、单向进口、情景互换、内点清理、整份哈希）全部为诊断，容差 `1e-3 + 10 × ε × ref`，对偶预算 `10 × max(OptimalityTol, BarConvTol)`；B2 / B14 / B15 新增容差。
- 前人做法（引用见 GATES_V6 §0）：PyPSA-Eur v2025.07.0 与 PyPSA-Earth 只检查 `status != "ok"` → warning，`"infeasible"` → raise，无 suboptimal 处理、无求解后残差门槛；可选 `check_objective`（缺省关）；Gurobi 以 BarConvTol / FeasibilityTol / OptimalityTol 定义 OPTIMAL。
- 重评（`GATES_RETRO_COMPARISON.csv/.md`，只用导出指标）：

| 运行组 | V5 `all_passed_solver_tolerances` | V6 标签 | D2 对偶比值（V5 / V6 预算） |
|---|---|---|---|
| L23 ×3（365×24h，suboptimal） | False | 不可计算（无 PRECISION） | 6.0e3–3.3e4 / 同 |
| S4M-2 A ×3 + 复跑（56×3h，optimal） | True | 不可计算（无 PRECISION；C1 在 S4Q 影子目录另算过，全过） | 0.04–0.24 / 同 |
| S4N 试点（365×24h，optimal） | False | **ACCEPTED_LAYER2**（G2.2 pending） | 865 / 865 |
| S4N C2 ×3（56×3h，1e-5 t32） | False | 不可计算 | 7.7e3 / 7.7e2 |
| S4O-6 ×3（365×24h，suboptimal） | False | **ACCEPTED_LAYER2**（G2.2 pending） | 3.9e3–6.6e3 / 同 |
| S4Q T8 / T16 ×6（56×3h，1e-6，optimal） | False | **ACCEPTED_LAYER2**（G2.2 pending） | 10.6–19.3 / 同（ε_d = 1e-6） |

- 观察（**不改定义**，提请决定）：D2 的对偶符号误差在内点解上约为 100 × BarConvTol（S4Q 1–2e-4 vs 1e-6；S4N 试点 8.6e-3 vs 1e-8），k = 10 使所有大规模内点解与 1e-6 候选在诊断上"超预算"，而 G1 全过——与第 119 项"精度由研究问题决定"一致，但若希望 D2 诊断在 optimal 运行上通常落在预算内，k 应取 100（Gurobi 对偶可行性在 barrier 下只收敛到 BarConvTol 量级，文档未给精确倍数）。是否在 V6.1 修订由用户决定。
- 资源：全部重评只读导出指标，< 1 分钟，无磁盘占用；未重载网络、未重建 LP。G2.2 需在 M08-9 把配置子集哈希写入网络 meta 后才能计算。

## 10. R9　统一性核查表

`UNIFICATION_CHECKLIST.csv/.md`：19 类输入 × 11 国 = 209 格；标出的口径差 / 例外 54 格（同一例外跨国重复计入）：TL 锚规则（需求 3 类）、VN 国家上限（水泥 / 钢）、陆上风 alpha（PH / TH / VN 实测 vs 均值）、水电 / 地热逐国官方来源（无统一方法，登记为例外）、SG 无大型核电、TL WACC 无来源、海上风 ESMAP 无行国家。

## 11. R10　影响估算与决定清单

### 11.1 影响（INFERENCE；方法 = 在 S4P 分解上的算术与比例缩放；F1 / F2 / F4 / F5 相互重叠，不加总）

| 修正 | 对 B6 | 对 VN 差额 | 对其他国 | 交互 |
|---|---|---|---|---|
| R1 需求（ATS 锚 + 产量 + 有用热） | −20–30 bn（规模 −30–50 %） | −15–25 bn | TH / MY / ID 两情景各 −30–45 %，差额按比例 | 上游：其后 R2 / R3 的绑定减弱，其影响按 0.5–0.7 折减 |
| R2 光伏上限（密度 + 开阔林） | −8–15 bn | −8–15 bn | KH / LA / TH 出口收入 −20–40 % | 与 R1 叠加后折减 |
| R3 取消 LNG 上限 | −10–15 bn | −10–15 bn | TH 气枢纽收入 −5–8；MY −3 | 与 R4 重叠（同一 224 TWh 甲烷） |
| R4 有用热溢出 | −3–5 bn | −3–5 bn | SG −0.5 | 与 R3 重叠 |
| R5 ERIA 封存 | ±2 bn | ±2 | VN / PH 绝对成本 +8–10 / +2–4 | 独立 |
| R6.1 HICP；R6.3 核电同源 | −1.8；+0.5–1 | −2.1；+1 | ID / TH 小 | 独立 |
| R7 保留存量（敏感性） | −3–6 bn | 0 | SG / TH / MY −1–2 | 独立 |
| F7 分国 WACC（敏感性） | −10–20 bn | −10–15 | KH / LA / MM 出口基地 +20–40 % 资本成本 | 与 R2 交互（出口基地） |
| **合并（主算 R1–R6）** | **B6 ≈ 25–45 bn**（从 69） | **VN ≈ 15–30 bn，份额 55–70 %** | TH 3–6、MY 1–3 | 方向稳健；量级待 M10 验证 |

### 11.2 需要用户决定

1. R1 主锚 AEO8 ATS（推荐）vs BAS；TL 规则（KH/LA/MM 均值 × UN WPP）。
2. R1.3 物理产量上限规则：人均饱和（水泥 1.0、钢 0.6 t/cap；推荐）vs 国家规划上限；VN 水泥 107 / 钢 70 Mt。
3. R2 光伏布局：密度 5.1 + 开阔林 121–126（推荐，需栅格重算与下载）vs 仅改密度。
4. R3 LNG 上限：取消（推荐）/ 项目口径 / 2.5×；码头成本 8,020 代替 7,018；再气化加价 1.26 EUR/MWh。
5. R5 封存统一 ERIA P50（VN 5.3、PH 0.067 Gt）；KH 低值 0.09；TL 零。
6. R6.1 HICP 回算（推荐）vs 2020 源值；R6.2 AEO8 价格年敏感性 0.86；R6.3 SMR = td 核电 × 1.067（推荐）vs INL 2024 同源。
7. R6.5 报告货币 USD2020（推荐）与汇率 1.1422；或 USD2024。
8. R7 主定义登记（删除存量）与"保留存量"敏感性。
9. R8 采纳 GATES_V6；D2 的 k 是否在 V6.1 改为 100（本步未改）。
10. M10 范围 7 次运行与 M08 顺序（`IMPLEMENTATION_PLAN.md`）。
11. 用户下载清单 9 项（`USER_DOWNLOAD_LIST.md`）。
12. 第 123 / 126 / 128 项等注册表登记（`REGISTRY_ROWS_PROPOSED.csv` 31 行）。

### 11.3 需要请示师哥

1. 工业路线：固定 PyPSA-Eur 2050 路线 vs 分温度带有用热内生选择（科学口径）。
2. 需求锚家族（AEO8 ATS vs ERIA LCET-CN）与"活动量锚定、载体内生"的边界。
3. 水泥 / 钢人均饱和水平的文献依据与取值。
4. 光伏土地规则：是否把开阔林计入（ESMAP L1 口径）；保护区是否排除（PyPSA-Eur 排、ESMAP L1 不排）。
5. "不互联"是否包含船运类贸易（液体池、CO₂ 船运）；现有跨境气管道是否删除。
6. 核电成本来源（technology-data × AEO8 比值 vs INL / ATB），以及"SMR ≥ 大型核电"的相对关系。
7. 门槛哲学：C1 作为唯一精度判据、D2 预算倍数（10 vs 100）、分国 WACC 敏感性设计（实际利率表）。

## 12. 文件

`S4R_PLAN.md`（本文件）、`GATES_V6.md` + `GATES_V6_SHA256.txt`、`GATES_RETRO_COMPARISON.csv/.md`、`IMPLEMENTATION_PLAN.md`、`UNIFICATION_CHECKLIST.csv/.md`、`DEMAND_ANCHOR_COMPARISON.csv/.md`、`POTENTIAL_COMPARISON.csv/.md`、`LNG_CAPACITY_COMPARISON.csv/.md`、`CO2_STORAGE_UNIFIED.csv/.md`、`COST_CURRENCY_FIXES.csv/.md`、`COUNTRY_WACC_SENSITIVITY_TABLE.csv/.md`、`REGISTRY_ROWS_PROPOSED.csv`、`USER_DOWNLOAD_LIST.md`、`EXTERNAL_SOURCES_S4R.md`、`S4R_EVIDENCE.json`、`S4R_PROGRESS.md`、`scripts/`（8 个只读脚本）、`evidence/`（Solargis 11 国表、GEM 11 国码头表、R1–R3 JSON）。分支提交：4fbddf28（对照表）→ d45955ea（GATES_V6 单独）→ 收尾提交（见进度文件）。
