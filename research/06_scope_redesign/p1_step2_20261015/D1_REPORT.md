# D1 数据加工与数据登记报告（2026-10-15）

分支 `codex/d1-data-registry-20261015`（自 S1 分支 `codex/s1-coupling-skeleton-20261015` @ 929c35c7 开出）。本步只读取 `work/p2_data_intake/` 原始数据、生成 `research_inputs/*_v5/` 下的加工文件、脚本与测试；未修改任何原始数据，未构建网络，未求解。所有结论按 VERIFIED / EXACT / INFERENCE / PROPOSED 分级。

## 0. 十行摘要

1. 数据登记表 `research_inputs/registry_v5/DATA_REGISTRY.csv` 共 669 行：A 级 201、B 级 206、C 级 262；状态 REGISTERED 436、DATA_PENDING 98、SENSITIVITY 55、REFERENCE_ONLY 28、SOURCE_ZERO 28、CANDIDATE_ONLY 24。每行带来源、定位、SHA256、脚本与敏感性区间（VERIFIED，`tests/research/test_d1_registry.py` 11 项通过）。
2. CO₂ 封存主算值（Gt）：MY 128.77、ID 51.28、PH 22.3、BN 18.58、TH 16.02、VN 11.8、TL 0.25、KH 0.085、LA/MM/SG 0；年注入上限 = 潜力 ÷ 50（EXACT）。
3. 化石燃料 2050 价格（WEO 2025 NZE，EUR2020/MWh 低位热值）：原油 11.62、LNG（日本到岸代理）13.67、动力煤 5.17；STEPS 2050 作高价敏感性 35.32 / 27.07 / 8.86（EXACT，换算链逐项登记）。
4. LNG 终端（GEM 2025-09）：现有再气化能力 TH 19.0、PH 14.7、ID 11.75、SG 11.0、MY 7.3、VN 4.0 Mtpa，已映射到最近网络节点；年进口上限 = 2.5 × 现有（EXACT）。UNSD 2019 国内化石产量上限按国家、载体登记（EXACT）。
5. 作者 AEO8 成本规则已逐行解码并以 1.9e-15 相对误差复现作者输出（VERIFIED）：USD→EUR 用 ECB 2020 年均价 0.877229；D.17 衰减只在 D.15 `technology` 与 D.17 `Technology` 标签相同时生效，"Solar PV"≠"Solar" 使光伏完全未衰减，"Oil and Gas"≠"Oil"/"Gas" 同理。
6. 两套成本层已登记并可用 `research.cost_layer.active` 切换：A 层 technology-data v0.13.2 2050（主算）、B 层 AEO8 作者规则（敏感性）；SMR 8,421 EUR2020/kW、FOM 1.146 %/a、VOM 1.93 EUR/MWh（C 级 ±30 %）。
7. 2050 需求表 `research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv`：东盟十国分部门合计与 AEO8 BAS 2050 完全一致（相对误差 2e-16，EXACT）；国别按 GDP 乘数分配、人口乘数作敏感性；电力行已标记为"已在现有 2,617.8 TWh 负荷中"，表内电力合计 2,395.8 TWh（比值 0.915，未调参）。
8. 需求侧技术份额 47 项按 PyPSA-Eur v2025.07.0 `config.default.yaml` 行号登记为 C 级；采暖类 3 项标为 REFERENCE_ONLY（东盟不适用，决定 25）。
9. 生物质：IRENA 2017 R-3→R-1a 复现误差 0.1–1.6 %（证实总量不含油棕果与椰子两行）；FAOSTAT 当前修订版复现误差收获侧 −2.4～−6.7 %、加工侧 −3～−18 %；11 国 2050 潜力合计约 8,670 PJ（ID 4,068、TH 1,410、MY 1,069、PH 687、VN 663、MM 453、KH 220、LA 90、TL 4.5、SG 3.4、BN 2.0），成本 C 级 ±50 %，来源为 2024 年东南亚公开价格调查。
10. 过程排放与工业产量无本地数据：55 行 DATA_PENDING，下载清单 11 项（EDGAR 2025、USGS MCS 2025、UNSD 四国舱燃料等）。

## 1. 第 1 节：数据登记表

### 1.1 结构与原则

- 文件：`research_inputs/registry_v5/DATA_REGISTRY.csv`，列为 `param_id, description, value, unit, country, node, tier, source, source_locator, source_sha256, derivation_script, sensitivity_low, sensitivity_high, decision_ref, status`。
- 分级：A = 直接来源原值；B = 可复现推导（脚本 + 输入哈希）；C = 假设（必带敏感性区间，由 `d1_registry.validate` 强制校验）。
- 单位统一为 MWh / MW / EUR2020 / tCO₂；18 个换算系数单独登记（`conv_*`、`fx_*`、`deflator_*`），来源为 UNSD 2014 换算文档（p.xxiii–xxiv）、IPCC 2006 第 2 卷第 1 章表 1.2 与 Box 1.1、NIST SP 811 附录 B.9、US EIA 换算页、FRED A191RD3A086NBEA、ECB 参考汇率（currency_converter 0.18.9 内置文件）。
- 来源文件副本与哈希：`research_inputs/registry_v5/sources/`（提取文件、SHA256SUMS、PyPSA-Eur 配置、UNSD/IPCC PDF、FRED CSV、S1 节点坐标）。原始 PDF 仍只在 `work/p2_data_intake/raw*`，登记表以 SHA256SUMS 记录其哈希。
- 汇总脚本 `scripts_project/d1_registry.py` 合并 8 个片段（`registry_v5/fragments/`），输出 `DATA_PENDING_LIST.csv`、`DOWNLOAD_LIST.csv`、`D1_EVIDENCE.json`（57 个产出文件哈希）。

### 1.2 CO₂ 封存潜力（`d1_co2_storage.py`，决定 28–30）

| 国家 | 主算 Gt | 构成 | 低 Gt（来源） | 高 Gt（来源） | 年注入上限 Mt/a |
|---|---|---|---|---|---|
| MY | 128.773 | ERIA 咸水层 P50 127（Table 1.9）+ 油气田净 1.773（Table 1.7） | 80（IEA 2021 p.35） | 198.773（ERIA P10 197 + 1.773） | 2,575.5 |
| ID | 51.275 | ERIA 咸水层 P50 49（Table 1.6）+ 油气田净 2.275（Tables 1.4–1.5） | 8.4（IEA） | 77.275（ERIA P10 75 + 2.275） | 1,025.5 |
| PH | 22.3 | IEA p.35：咸水层 22 + 气田 0.3（源自 ADB 2013） | 0.067（ERIA 仅 Malampaya） | 23.318（OGCI C5） | 446.0 |
| BN | 18.579 | ERIA 咸水层 P50 18（Table 1.12）+ 油气田净 0.5793（Table 1.10） | 0.558（OGCI） | 25.579（ERIA P10 25 + 0.5793） | 371.6 |
| TH | 16.024 | ERIA 咸水层 P50 15（Table 1.14）+ 油气田净 1.024（Table 1.13） | 10（ADB 2013） | 23.024（ERIA P10 22 + 1.024） | 320.5 |
| VN | 11.8 | IEA p.35：深部咸水层 10.4 + 枯竭油气田 1.4（ADB 2013） | 5.303（ERIA） | 21.75（OGCI） | 236.0 |
| TL | 0.25 | OGCI C5 汇总 | 0 | 0.25 | 5.0 |
| KH | 0.085 | OGCI C5 文本：约 85 Mt 未发现咸水层 | 0（ERIA：未评估） | 0.132（OGCI 含次商业 0.047） | 1.7 |
| LA, MM | 0 | ERIA p.56："unknown as no analysis has been completed"，登记 DATA_PENDING | 0 | — | 0 |
| SG | 0 | ERIA p.56 / IEA p.32：无封存潜力 | 0 | 0 | 0 |

- 四个口径（IEA / ERIA / ADB / OGCI）的全部国家值及 20 条文献内部不一致已在 `sources/CO2_STORAGE_EXTRACTION.md` §5–§6 中登记，主算值的构成行单列（`co2_storage_component_*`）。ERIA 咸水层为开放边界资源估算，作者自称"may be overly optimistic"（p.10）；决定 28 的 ÷50 年注入上限是唯一的可用性折减，建议 S2 报告中保留此提示（INFERENCE）。
- 独立对照：MY 的 IEA 80 / ERIA Malay 83 / Junin & Hasbollah 84 一致；PH 的 ERIA 口径（0.067）与 ADB/IEA（22–23）相差 300 倍，是最大的跨文献分歧，已写入低值。

### 1.3 化石燃料价格（`d1_fuel_prices.py`）

WEO 2025 Table 2.3（PDF p.109，USD MER 2024）→ EUR2020/MWh（低位热值）：

| 载体 | WEO 条目 | NZE 2050 | STEPS 2050（高价敏感性） | 2024（参考） | technology-data v0.13.2 2050 | NZE/td |
|---|---|---|---|---|---|---|
| 原油 | IEA crude oil 25 / 76 / 79 USD/bbl | 11.62 | 35.32 | 36.71 | 52.91 | 0.22 |
| 天然气 | Japan（纯 LNG 进口，再气化前，GCV）4.9 / 9.7 / 13.5 USD/MBtu | 13.67 | 27.07 | 37.67 | 24.57 | 0.56 |
| 动力煤 | Japan 6,000 kcal/kg 49 / 84 / 151 USD/t | 5.17 | 8.86 | 15.93 | 9.55 | 0.54 |

换算链（均已登记）：USD2024→USD2020 = 105.377/125.587 = 0.83908（FRED A191RD3A086NBEA）；USD2020→EUR2020 = 0.877229（ECB 2020 年均价，与作者成本管线相同）；合计 0.73612。气：1 MBtu = 0.29307107 MWh（NIST），GCV→NCV ÷0.90（UNSD 天然气标准系数，与冻结需求重建一致）。煤：6,000 kcal/kg × 4.1868 = 25.1208 GJ/t = 6.978 MWh/t（按净值到岸口径处理）。油：EIA 5.689 MMBtu/bbl（GCV）× 0.95（IPCC Box 1.1）= 1.5839 MWh/bbl；IEA 惯用 1 bbl ≈ 0.136 toe = 1.582 MWh，相差 0.1 %。燃料母线口径为 NCV（登记 `fuel_price_basis`）。东南亚无专属价格，日本 LNG 作代理并已显式登记；再气化加价无来源，列 DATA_PENDING。

### 1.4 LNG 终端（`d1_lng_terminals.py`）

| 国家 | 现有（运行+在建）Mtpa | 单元 | 缺容量单元 | 年进口上限 TWh/a（2.5×） | 映射节点 | 拟建候选 Mtpa |
|---|---|---|---|---|---|---|
| TH | 19.0 | 3 | 0 | 633.3 | TH2 3 | 10.8 |
| PH | 14.7 | 3 | 0 | 490.0 | PH_Luzon9 0 | 9.5 |
| ID | 11.75 | 6 | 1（Gresik，拟建） | 391.7 | ID_Java-Bali1 0/2、ID_Nusa-Tenggara12 0、ID_Sumatra3 0 | 2.3 |
| SG | 11.0 | 3 | 0 | 366.7 | SG2 0 | 5.0 |
| MY | 7.3 | 2 | 3（拟建） | 243.3 | MY_Peninsular2 1 | 0 |
| VN | 4.0 | 3 | 6（含在建 Haiphong FSRU） | 133.3 | VN2 5 | 25.86 |
| BN, KH, LA, MM, TL | 0 | — | — | 0 | — | KH 1.1 |

能量系数 1 Mtpa = 1e6 t × 48.0 GJ/t（IPCC 天然气缺省 NCV，区间 46.5–50.4）= 13.333 TWh/a。独立对照：GEM 自带国家汇总表（operating + construction）ID 11.45+0.3、PH 10.3+4.4、SG 11.0、TH 19.0、MY 7.3、VN 4.0，与单元求和一致（EXACT）。拟建单元 24 个登记为 CANDIDATE_ONLY，其中 9 个无容量为 DATA_PENDING。节点映射用 S1 网络母线坐标（`sources/s1_network_nodes_xy.csv`）最近邻，同时记录最近港口（上游 `ports.csv`）。

### 1.5 国内化石产量上限（`d1_fossil_production.py`）

UNSD 2019 一次产量（NCV，TWh/a）：ID 煤 4,415.9、气 727.6、油 472.9；MY 气 849.5、油 363.2、煤 24.8；TH 气 367.2、油 226.3、煤 54.8；VN 煤 338.0、油 134.6、气 103.6；MM 气 184.9、煤 13.4、油 5.2；BN 气 109.8、油 70.4；PH 煤 53.5、气 43.0、油 6.0；LA 煤 60.5；TL 气 61.3、油 11.1；KH 煤 0.3；SG 无产量（SOURCE_ZERO）。煤 = Hard coal + Brown coal 聚合行（无烟煤/褐煤为子集，不重复计）；气 = "Gross production" TJ(GCV)×0.90（UNSD 文件没有净产量行，含放空与回注，属上界，已登记 `fossil_production_gas_basis`）；油 = 原油 42.3 GJ/t + 凝析液 44.2 GJ/t。价格与进口相同。本项在 intake 中没有第二来源可对照，已在登记表注明。

### 1.6 SMR 与存量地热

- SMR（决定 46，C 级）：AEO8 D.15 "Nuclear SMR" 9,600 kUSD/MW × 0.877229 = 8,421.4 EUR2020/kW；FOM = 110.0/9,600 = 1.1458 %/a；VOM 2.2 × FX = 1.930 EUR/MWh。AEO8 未给成本年份，D.17 没有核电衰减，故为年份无关的"当前成本"。±30 %（5,895–10,948 EUR/kW）的理由：区间下界低于 technology-data v0.13.2 核电 8,594 EUR/kW，上界覆盖 v0.15.0 核电 10,806 EUR/kW（EUR2025 口径），即把两版 technology-data 大型堆成本都包在内；寿命与效率在 AEO8 中缺失，用 technology-data 核电 40 年 / 0.326 作代理（C 级）。作者映射表没有 SMR 行，S1 之前 SMR 的 `cost_technology` 为 null。
- 存量地热（ID 186 MW，B 级）：technology-data v0.13.2 `geothermal` 只有 5 个参数：FOM 2.0 %/a、寿命 30 年、CO₂ 强度 0.12 tCO₂/MWh_th、区域供热附加 25 %、供热输入 0.8。没有 efficiency / VOM / investment 行（仅 `central geothermal heat source` 与 `organic rankine cycle` 有投资），三项登记 DATA_PENDING；B 层有 AEO8 "Geothermal average" 2,481.7 EUR/kW（含 0.31 衰减）、FOM 0.689 %/a、VOM 0.263 EUR/MWh 可作敏感性。

## 2. 第 2 节：成本口径（决定 46 方案 A）

### 2.1 作者 AEO8 转换规则（逐行，`pypsa-asean/scripts/append_cost_data.py`）

| 行 | 代码 | 含义与发现 |
|---|---|---|
| 14–33 | `rename_subtech = {...}` | D.15 子技术→technology-data 名称：Coal average→coal、Oil average→oil、Gas Turbine→OCGT、Gas Combined Cycle→CCGT、Nuclear average→nuclear、Large Hydro→hydro、Small Hydro→ror、Geothermal average→geothermal、Solar average→solar、Solar PV→solar-utility、Solar PV Rooftop→solar-rooftop、Wind Onshore→onwind、Wind Offshore→offwind、Bioenergy average→biomass、Biogas→biogas、Lithium Ion Batteries→battery inverter、Pumped Hydro→Pumped-Storage-Hydro-bicharger。Nuclear SMR 不在表内。 |
| 52–54 | `declining = pd.read_csv(...).set_index(["Technology","Parameter"])[year].unstack()` | 读 D.17，按年份列（通配符 2050）取 Capex/Opex 衰减。 |
| 56–73 | `regional_factor` | `configs/config.asean.yaml:169 regional_factor: false` → 系数 1，D.18 的 1.47 未应用。 |
| 79–81 | `app_costs[["capital_cost","FOM","VOM"]] *= get_yearly_currency_exchange_rate("USD","EUR",2020)` | 第三个位置参数在 `process_cost_data.py` 签名中是 `default_exchange_rate`（兜底值），年份实际来自模块常量 `TECH_DATA_REFERENCE_YEAR = 2020`（第 91 行）；结果 0.8772286（ECB 2020 年 366 个日值均值，本步用同一软件包复算一致）。 |
| 84–88 | `for t in declining.index: app_costs.loc[app_costs.technology == t, "capital_cost"] *= 1 - Capex; VOM *= 1 - Opex` | 以 D.17 `Technology` 标签匹配 D.15 `technology` 列。匹配成功：Wind、Bioenergy、Hydro、Geothermal、Coal、Energy Storage；**不匹配**："Solar PV" vs D.15 "Solar"，"Oil and Gas" vs "Oil"/"Gas"。因此光伏完全没有衰减（D.17 Solar PV 2050 Capex 0.76 未生效），油气本来衰减为 0 无影响（INFERENCE，由数值 VERIFIED）。 |
| 106 | `FOM = row["FOM"] / row["capital_cost"] * 100` | FOM 百分比用衰减后的资本成本做分母，衰减技术的 FOM% 被放大：onwind 3.53 %/a（未衰减应为 2.54 %）、biomass 6.56 %（3.87 %）、battery inverter 17.1 %。 |

数值核验（VERIFIED，`cost_layers_v5/LAYER_B_VERIFICATION_VS_AUTHOR_OUTPUT.csv`）：复现 17 项技术 × 3 参数 = 51 个值与作者输出 `resources/baseline-aims-3H-tutorial/costs_2050_sec.csv`（SHA256 `bbcc6390…`）最大相对差 1.9e-15。指令中的两例：solar-utility 850,911.77 EUR/MW = 970 × 0.877229 × 1000（无衰减）；onwind 991,619.25 = 1,570 × 0.877229 × (1−0.28) × 1000。

### 2.2 两套成本层与配置开关

- A 层（主算）`cost_layers_v5/LAYER_A_TECHNOLOGY_DATA_V0_13_2_2050.json`：technology-data v0.13.2 `outputs/costs_2050.csv` 全部技术，EUR2020，不执行作者 append 步骤。覆盖检查（`LAYER_A_COVERAGE_WATCHLIST.csv`）：研究网络用到的技术中，`geothermal` 无投资/效率/VOM（见 1.6），`biomass boiler steam` 不存在（可用 `biomass boiler`），其余齐全。
- B 层（敏感性）`LAYER_B_AEO8_AUTHOR_RULE_2050.csv`：按作者规则复现的 17 项 + 追加 `nuclear SMR`，列含 D.15 原值、FX、衰减、是否匹配、EUR2020/kW、FOM %、VOM。
- 配置：`configs/research/baseline.yaml` 新增 `research.cost_layer`（`active: technology_data_v0_13_2_2050`，两层文件路径，`smr_cost_source: aeo8_author_rule_2050`）；加载入口 `d1_cost_layers.load_cost_layer(config)`，测试 `test_cost_layer_config_switch` 覆盖两种取值。S1 的 `cost_scaling` 层保持不变。

### 2.3 technology-data 新版本只读核对（不升级，PROPOSED 交用户决定）

| 版本 | 行数 | 与 v0.13.2 公共行中变化 | 新增/删除技术 | 主要差异 |
|---|---|---|---|---|
| v0.13.4 | 1,236 | 4 行 | 0 / 0（新增 7 个参数行） | `biogas`/`biogas CC` "CO2 stored" 0.0868→0.1447 tCO₂/MWh_th；`central water pit storage` FOM/投资；研究网络监视清单内无变化 |
| v0.15.0 | 1,280 | 378 行（共 1,224） | +7（CO2 dense phase compression、Enhanced Weathering、HVAC submarine、HVAC underground、biomass boiler capture、distribution grid reinforcement、grey methanol synthesis）/ −1（electricity grid connection） | 新增 `currency_year` 列，投资类多数改为 2025 年价（405 行），表现为统一 +25.7 %（onwind 1,019→1,286、solar-utility 293→368、nuclear 8,594→10,806、electrolysis 1,000→1,257 EUR/kW）；实质变化：核燃料 3.41→7.45 EUR/MWh_th（+118 %）、煤燃料 −30 %、油燃料 −23 %、气燃料 −7 %；Fischer-Tropsch 单位重构（EUR/MW_FT→EUR/kW_FT/year，效率 0.80→0.75，寿命 20→25）；HVDC submarine 1,008→2,680（+166 %）、HVDC overhead +13 % |

若升级到 v0.15.0 需先把 2025 年价回算到 EUR2020，否则与研究层 `model_price_year 2020` 不一致。比较表：`cost_layers_v5/TECHNOLOGY_DATA_VERSION_COMPARISON_2050.csv`。

## 3. 第 3 节：2050 需求（决定 22、34；`d1_demand_2050.py`）

### 3.1 口径与方法

- 基年 2019：燃料来自冻结重建 `research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json`（SHA `28c20901…`）273 个账户，其中 18 个用已接受的"最大重叠基线"值（决定 A，`ASSEMBLY_V1_BLEND_BASELINE.json`），82 个为有证据零值，23 个 UNRESOLVED 行保留原值并标记（合计仅 0.02 TWh）；电力按 UNSD 2019 电力交易分部门（`electricity.json`）；非能源用途 47 行（`nonenergy_reference`）；国际舱燃料来自同一重建。
- 部门映射：IndustryFinalEnergy→Industry；Road/DomesticAviation/DomesticShipping/RailNonElectric/TransportNEC/TransportEmbeddedFuelParent→Transport；ResidentialFuel→Residential；ServicesFuel→Commercial；Agriculture/OtherNEC→Agriculture and Others；国际舱燃料与非能源在 AEO8 TFEC 之外单列。
- 增长：各部门东盟十国 2050 合计 = AEO8 BAS 2050（Appendix C.3，Mtoe × 11.63 TWh/Mtoe）；国别权重 = 2019 国家-部门能量 × GDP 乘数 2019→2050（`GROWTH_CHAIN_2019_2050_WDI_SSP2.csv`：WDI 2019–2025 + SSP2 2025–2050，ID 2.80、VN 4.12、PH 3.73、TH 1.83、MY 2.36、SG 1.70、KH 4.66、LA 3.27、MM 1.80、BN 1.59、TL 2.67）；部门校准因子 k = 目标 ÷ Σ(基年 × GDP 乘数)：Industry 1.2055、Transport 1.4174、Residential 0.2954、Commercial 0.9229、Agriculture&Others 1.0143。东帝汶不在 AEO8 总量内，沿用研究层做法，取同一 k 但不参加校准求和。
- 载体：国家-部门内部按 2019 载体份额保持不变，不为对齐 AEO8 分燃料表调参；电力行标记 `in_existing_electricity_load=true` 并附研究层 Astar 2050 值。
- 2019→2022：AEO8 附录只印 2005 与 2022 两个历史年，没有 2019；因此采用"2050 绝对值锚定"，把 AEO8-2022 ÷ UNSD-2019 的隐含比值作为一致性检查报告（登记 `demand_2019_2022_bridge`）。
- 非能源用途：按国家工业乘数（GDP 乘数 × k_Industry）增长；国际舱燃料：保持 2019 常数（研究层约定 `ASSEMBLY_V1_BUNKER_CONSTANT_2019`），BN/KH/LA/TL 的国际航运舱燃料在 UNSD 2019 导出中无交易行，登记 DATA_PENDING（不估算）。

### 3.2 结果与交叉核对（`DEMAND_2050_CROSSCHECKS.json`）

| 部门 | 2019 基年（十国，TWh） | AEO8 2022 ÷ 基年 | 2050 表值（十国，TWh） | AEO8 BAS 2050 | 相对差 |
|---|---|---|---|---|---|
| Industry | 5,759 | 1.133 | 6,524.4 | 561.0 Mtoe = 6,524.4 | 2e-16 |
| Transport | 1,167 | 1.447 | 4,360.1 | 374.9 Mtoe = 4,360.1 | −2e-16 |
| Residential | 940 | 0.780 | 793.2 | 68.2 Mtoe = 793.2 | 2e-16 |
| Commercial | 347 | 0.988 | 882.7 | 75.9 Mtoe = 882.7 | −1e-16 |
| Agriculture & Others | 125 | 0.820 | 323.3 | 27.8 Mtoe = 323.3 | 0 |
| 合计 | — | — | 12,884.9 | 1,107.9 Mtoe | 舍入内 |

- 隐含 2022/2019 比值偏离 1 的两处（交通 1.447、居民 0.780）说明 UNSD 重建的交通基年低于、居民基年高于 AEO8 口径（居民含传统生物质 259 TWh）；因为 2050 水平由 AEO8 绝对值锚定，这只影响国别与载体分配，不影响合计（INFERENCE）。
- 电力：表内电力合计 2,395.8 TWh（东盟十一国）vs 现有 Astar 负荷 2,617.8 TWh vs AEO8 C.2 电力 2,616.8 TWh，比值 0.915；分国比值在 `electricity_vs_existing_astar_2050`。电力行不得作为新 Load 加入（已标记），S2 显式电气化用电需从 Astar 扣除。
- 分载体合计（十国，未调参）vs AEO8 C.2 BAS 2050：煤 2,419.6 TWh / 2,584.2（0.94）；油 5,388.1 / 5,219.5（1.03）；气 898.8 / 976.9（0.92）；生物质 1,749.8 / 1,479.3（1.18，AEO8 口径为 Bioenergy + Traditional Biomass）；电力 2,395.0 / 2,616.8（0.92）。
- 国别份额变化 2019→2050（GDP 法，`DEMAND_2050_COUNTRY_SHARES_2019_2050.csv`）：工业 VN 0.208→0.302、TH 0.155→0.100、ID 0.406→0.400、MY 0.112→0.093、SG 0.041→0.025、PH 0.036→0.048；交通 TH 0.280→0.195、PH 0.121→0.171、VN 0.076→0.119、MY 0.226→0.202、ID 0.215→0.228。人口法敏感性文件 `DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv`（例如工业 TH 0.128、VN 0.206）。
- 非能源 2050（TWh）：TH 595.2、MY 451.6、ID 345.7、SG 160.6、VN 75.7、PH 49.3、BN 13.4、MM 12.4、KH 0.9、TL 0.5、LA 0.1。国际舱燃料 2019 常数（TWh）：SG 638.6、TH 68.2、MY 34.3、PH 20.7、VN 17.7、ID 13.8、KH 1.9、BN 1.3、MM 0.9、LA 0.4、TL 0.0。
- 交通 2050 的 `unclassified_fuel`（TransportEmbeddedFuelParent，十国 32 TWh）原样保留，S2 需指定载体。

## 4. 第 4 节：需求侧技术份额（决定 21；`d1_demand_shares.py`）

来源 PyPSA-Eur v2025.07.0 `config/config.default.yaml`（SHA `bfbe9160…`，副本在 sources/），按行号登记 47 项 C 级：陆路交通 2050 电动 1 / 燃料电池 0 / 内燃机 0（第 584/576/592 行，轨迹 2040 起作敏感性）；效率 53.19 / 30.003 / 16.0712 百公里每 MWh（600–602）；航运 2050 甲醇 1 / 氢 0 / 油 0（619/611/627，S3 用）；航空需求因子 1（637）；农业机械电动 0.5 / 油 0.5（603–604）；工业 2050 一次钢 0.3、DRI 1、一次铝 0.2、HVC 一次 0.4 / 机械回收 0.30 / 化学回收 0.20、环境封存 0、垃圾发电 false（823–887）；BEV 参数 9 项（560–574）；甲醇与氨工艺系数（607–609、849–853）。东盟不适用（REFERENCE_ONLY）：`reduce_space_heat_exogenously`（641）、`reduce_space_heat_exogenously_factor` 0.29（642）、`district_heating.progress` 1.0（487）；决定 25：制冷留在电力负荷。

## 5. 第 5 节：生物质（决定 31、32、36；`d1_biomass.py`）

### 5.1 IRENA 2017 复现（VERIFIED）

- 解析 R-3a–e（PDF 27–36）262 行作物残余因子与 2010 残余量；因子一致性：R-3 残余 = R-2 产量 × 因子 × 收集率，收获侧最大偏差 2.9 %、加工侧 15 %（因子四舍五入，如稻谷实际 1.325）。
- R-3 行求和（剔除 "Oil, palm fruit" 与 "Coconuts"）对 R-1a：ID H 817.5/816、P 496.3/494；MY 78.2/77、44.4/44；PH 297.7/297、217.7/218；TH 477.4/476、430.6/429；VN 385.1/384、267.3/267 PJ，误差 0.1–1.6 %，证实 IRENA 总量不含油棕果与椰子（`REPLICATION_R3_VS_R1A.csv`）。
- FAOSTAT 2010 当前修订版 × IRENA 因子（`REPLICATION_FAOSTAT2010_VS_R1A.csv`，匹配 R-3 残余质量 99.4–100 %）：收获侧误差 ID −5.5 %、MY −4.4 %、PH −6.7 %、TH −4.3 %、VN −2.4 %；加工侧 −4.0 / −3.0 / −18.3 / −7.9 / −9.4 %。最大偏差来自 FAOSTAT 事后修订：菲律宾 2010 甘蔗 30,167 kt（IRENA 引用）→ 17,929 kt（当前），马来西亚甘蔗/玉米量级很小偏差大但绝对量可忽略（`REPLICATION_FAOSTAT2010_VS_R3_BY_CATEGORY.csv`）。方法可接受，按指令扩展到 11 国。

### 5.2 2050 潜力（`BIOMASS_POTENTIAL_2050.csv`，MWh/a，含低/高层与成本）

方法：FAOSTAT 2019–2023 均值 × 增长 1.1717（1.1 %/a 至 2030、0.3 %/a 至 2050，IRENA 2022）× RPR × 收获残余 25 %（主）/ 50 %（高）、加工残余 90 % × (1 − 饲料份额，IRENA 2017 R-1c 五国比值，其余国家用五国合计 29 %，C 级) × 15 GJ/t；低层再乘 2050 收集率 0.75（农业）/ 0.90（木质）。油棕按 IRENA 2022 Box 4 质量平衡（EFB 21 %、纤维 14.4 %、PKS 6.4 %、POME 58.3 % of FFB），老树干按 Appendix A（面积 × 4 % × 140 株 × 2 t，叶片只入高层，干物质 20 % 作低层）；椰子按 IRENA 因子 3.0/0.5；木材加工残余 = FAOSTAT FO "Wood residues" 产量 × 0.90 × 9.14 GJ/m³（UNSD）；城市固废 = What a Waste 3.0 2050 预测 × (食物 + 园林份额) × 11.6 GJ/t（IPCC，区间 6.8–18.0）。

| 国家 | 合计 PJ | 稻 | 甘蔗 | 玉米 | 木薯 | 椰子 | 其他作物 | 油棕 EFB/纤维/PKS/POME/树干 | 木材加工 | MSW 有机 |
|---|---|---|---|---|---|---|---|---|---|---|
| ID | 4,068 | 398 | 114 | 129 | 106 | 305 | 337 | 780 / 535 / 238 / 111 / 570 | 3.2 | 441 |
| TH | 1,410 | 233 | 335 | 41 | 197 | 15 | 126 | 57 / 39 / 18 / 8 / 40 | 49.4 | 252 |
| MY | 1,069 | 10 | 0 | 0 | 0 | 6 | 14 | 317 / 217 / 97 / 45 / 217 | 11.5 | 134 |
| PH | 687 | 96 | 58 | 44 | 11 | 173 | 115 | 1.7 / 1.2 / 0.5 / 0.2 / 2.7 | 待补 | 184 |
| VN | 663 | 194 | 28 | 22 | 40 | 20 | 144 | — | 5.3 | 210 |
| MM | 453 | 169 | 38 | 15 | 2 | 19 | 110 | — | 待补 | 101 |
| KH | 220 | 75 | 2 | 7 | 73 | 1 | 10 | 1.8 / 1.2 / 0.5 / 0.3 / 2.1 | 待补 | 46 |
| LA | 90 | 23 | 5 | 4 | 22 | — | 36 | — | 待补 | 待补 |
| TL / SG / BN | 4.5 / 3.4 / 2.0 | | | | | | | | | |

交叉核对（`BIOMASS_CROSSCHECK_IRENA.csv`）：作物残余（不含油棕、椰子）对 IRENA 2017 S-1 2050（25 %、扣饲料）：ID 0.76、PH 0.86、TH 0.94、VN 0.98；MY 0.31（S-1 含棕榈仁残余行 105 PJ，本表记在油棕类）。主算合计对 IRENA 2022 可收集量：ID 1.6×、TH 1.4×、VN 1.4×；MY 5.4×、MM 13.6×（IRENA 2022 两国只算木质）。差异来源：本表含椰子、全部作物、MSW、棕榈纤维与树干，而 IRENA 2022 每国只选 3 种作物并用 75 % 收集率（本表低层）。

### 5.3 可持续性约束（已登记 `biomass_constraint_*`）

无土地利用变化（不计能源作物，IRENA 2022 p.15–16）；收获残余移除 ≤25 %（脚注 10/17/21）；加工残余优先、收集 90 %；2050 收集率 75 % / 90 %；只计人工林与加工残余，天然林与现有薪柴不计（p.41/63/84/105）；饲料扣除；不跨境（决定 36）。

### 5.4 成本（L13，C 级 ±50 %，EUR2020/MWh）

来源：NRI/NEDO 2024 东南亚残余采购价（含运费，2024-11 访谈，PDF p.6–8）与 ERIA/IEEJ 2024 AZEC 报告 Table 3.8（印尼 Rp/kg）；换算用 15,565 IDR/USD（NEDO 同页汇率）、USD2024→EUR2020 0.73612、热值 15 GJ/t 或 ERIA 给出的 kcal/kg。稻（稻壳 Rp290/kg、秸秆路边收集 Rp237/kg）2.99；蔗渣（ID 31、TH 29–35 USD/t）5.56；玉米芯（ID 63、TH 53）10.25；PKS（TH 74、MY 59–68、ID Rp825–960/kg，NCV 3,500 kcal/kg）11.74；EFB（TH 11、MY 3–4、ID Rp45–68/kg）1.07；纤维 = EFB 代理 1.07；木材加工残余（锯末 Rp350–600/kg，NCV 2,450 kcal/kg）7.88；木薯/椰子/其他作物 = 三类农残均值代理 6.27；POME 与 MSW 0（无原料价，MSW 有倾倒费）；油棕树干无价格 → DATA_PENDING。对照：technology-data v0.13.2 `solid biomass` 燃料 13.65 EUR/MWh（JRC ENSPRESO 欧洲），东南亚残余价格普遍低于欧洲口径。文本证据摘录在 `biomass_v5/sources/`。

## 6. 第 6 节：过程排放与工业产量（L19）

本地无数据：`process_emissions_{cement,chemicals,metals}_{ISO}` 与 `industrial_output_{cement,steel}_{ISO}` 共 55 行 DATA_PENDING。下载清单见第 8 节（EDGAR_2025_GHG、USGS MCS 2025）。EDGAR 页面说明分部门用 IPCC 1996 代码（2A/2B/2C），年度表为 xlsx，1970–2024，许可 CC BY-NC-ND 4.0。

## 7. DATA_PENDING 清单（98 行，`registry_v5/DATA_PENDING_LIST.csv`）

| 组 | 行数 | 说明 |
|---|---|---|
| process_emissions_* / industrial_output_* | 55 | 第 6 节，EDGAR/USGS |
| biomass_potential_*_logging_residues | 11 | 无东南亚伐木残余系数 |
| biomass_potential_*_wood_processing_residues | 7 | FAOSTAT FO 无 BN/KH/LA/MM/PH/SG/TL 木材残余产量 |
| biomass_cost_*_oil_palm_trunk | 5 | 无树干价格 |
| lng_candidate_* | 9 | GEM 拟建/在建单元无容量（含 VN Haiphong FSRU 在建） |
| demand_bunker_pending_*_InternationalShippingBunker | 4 | BN/KH/LA/TL 2019 国际航运舱燃料无 UNSD 行 |
| geothermal_existing_{efficiency,VOM,investment} | 3 | technology-data v0.13.2 无地热发电行 |
| co2_storage_potential_unassessed_{LA,MM} | 2 | 无国家评估，按决定 30 取 0 |
| biomass_potential_LA_msw_organic | 1 | WaW 老挝无成分数据 |
| fuel_price_lng_regasification_adder | 1 | 无再气化加价来源 |

## 8. 需要用户下载的清单（`registry_v5/DOWNLOAD_LIST.csv`）

| 名称 | 链接 | 需要的字段 |
|---|---|---|
| EDGAR_2025_GHG 年度化石 CO₂ 分国分部门 | https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2025_GHG/IEA_EDGAR_CO2_1970_2024.zip | xlsx：Country_code_A3、ipcc_code_1996（2A/2B/2C）、Y_1970…Y_2024（kt CO₂） |
| USGS MCS 2025 Cement | https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-cement.pdf | World production 表：国家、2023、2024e（千吨） |
| USGS MCS 2025 Iron and Steel | https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-iron-steel.pdf | World production, raw steel：国家、2023、2024e（百万吨） |
| UNSD 能源统计：BN/KH/LA/TL 2019 国际航运舱燃料 | https://unstats.un.org/unsd/energystats/dataPortal/ | Fuel oil / Gas-diesel oil – International marine bunkers，2019，kt |
| 伐木残余系数（FAO/IEA Bioenergy/JRC ENSPRESO） | https://data.jrc.ec.europa.eu/dataset/74ed5a04-7d74-4807-9eab-b94774309d9f | 残余/原木比（t/m³）、可持续移除份额 |
| 油棕树干/叶片原料价格 | https://www.nedo.go.jp/content/800028002.pdf（无此项，需另找） | USD/t 到厂价、含水率 |
| What a Waste 3.0 老挝成分 | https://datacatalog.worldbank.org/search/dataset/0039597 | Composition – food / garden（% 重量） |
| LA/MM 国家 CO₂ 封存评估 | https://www.eria.org/research/carbon-capture-utilisation-and-storage-in-asean | 分盆地 Gt，P10/P50/P90 |
| GEM 无容量 LNG 单元 | https://www.gem.wiki/Haiphong_FSRU 等 | CapacityinMtpa |
| 东盟 LNG 再气化费 | https://www.iea.org/reports/world-energy-outlook-2025 | USD/MBtu |
| technology-data 地热发电参数（v0.15.0 待用户决定） | https://github.com/PyPSA/technology-data/releases | geothermal investment / efficiency / VOM |

## 9. 独立对照汇总

| 项 | 对照来源 | 结果 |
|---|---|---|
| CO₂ 封存 | IEA 2021 / ADB 2013 / OGCI C5 vs ERIA 2024 | 低/高值取跨文献极值；PH 分歧最大（0.067 vs 23.3 Gt） |
| 燃料价格 | technology-data v0.13.2 2050 燃料行 | NZE 为其 0.22 / 0.56 / 0.54 倍 |
| LNG 能力 | GEM 国家汇总表 | 与单元求和一致 |
| 作者成本规则 | 作者输出 costs_2050_sec.csv | 51 值相对差 ≤1.9e-15 |
| SMR | technology-data 核电 v0.13.2 / v0.15.0 | 8,421 介于 8,594 与 10,806（EUR2025）之间 |
| 需求 | AEO8 C.2 分燃料、研究层 Astar | 煤 0.94、油 1.03、气 0.92、生物质 1.18、电 0.92 |
| 生物质 | IRENA 2017 R-1a/S-1、IRENA 2022 Tables 11/18/26/35/41 | 复现 ≤1.6 %；2050 比值见 5.2 |
| 化石产量上限 | — | intake 中无第二来源，待补 |

## 10. 交付与测试

- 脚本：`scripts_project/d1_common.py`、`d1_co2_storage.py`、`d1_fuel_prices.py`、`d1_lng_terminals.py`、`d1_fossil_production.py`、`d1_cost_layers.py`、`d1_demand_2050.py`、`d1_demand_shares.py`、`d1_biomass.py`、`d1_registry.py`；测试 `tests/research/test_d1_registry.py`（11 项通过，命令与日志见 `D1_TEST_RUN.json`）。
- 加工文件：`research_inputs/registry_v5/`（登记表、片段、燃料价格、化石产量、来源副本）、`demand_v5/`、`biomass_v5/`、`cost_layers_v5/`、`lng_terminals_v5/`；配置 `configs/research/baseline.yaml` 新增 `research.cost_layer`。
- 本目录 `research/06_scope_redesign/p1_step2_20261015/` 保存报告、登记表副本、DATA_PENDING 与下载清单、证据 JSON、测试记录；同步到 `work/p1_step2_20261015/`。
- 未做：网络构建、求解、原始数据修改、technology-data 升级。待用户决定：是否升级 technology-data（第 2.3 节）、地热发电参数来源、过程排放数据下载。
