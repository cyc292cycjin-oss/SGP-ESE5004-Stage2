# S4R 外部来源清单（带出处；检索 / 读取日期 2026-10-20）

| # | 来源 | 用于 | 定位 |
|---|---|---|---|
| 1 | ACE, 8th ASEAN Energy Outlook 2023–2050 (2024) | R1 锚：Table C.3 TFEC by sector（p.182）、C.8 Energy Indicators（人均 TFEC / 电力 ATS 2050，p.187）、D.1 人口（p.188）、D.2 / D.3 / D.6 GDP（p.188–190）、D.15 Cost Summary（p.197；价格年未注明） | 本机文本副本（S4P 子代理下载，scratchpad `pdfs/aeo8.pdf`） |
| 2 | ERIA, Analysis on Energy Cost of LCET-CN based on ERIA Energy Outlook Models 2024, RPR FY2024 No.12, Ch.2–16（国别章） | R1 对照：TFEC、发电、工业增长 | 经 S4P `EXT_DEMAND_BENCHMARKS.json`（页码在该文件） |
| 3 | IEA, Southeast Asia Energy Outlook 2024（p.54, 86）；SEAEO 2026 网页 | R1 区域对照 | 同上 |
| 4 | PyPSA-Eur v2025.07.0 `scripts/solve_network.py`（约第 770–795、900–940 行）；`config/config.default.yaml`（第 159–331 行可再生；第 1056–1109 行求解） | R8 前人做法；R2 布局参数 | GitHub tag v2025.07.0（raw 读取）；库内副本 `research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml` |
| 5 | PyPSA-Eur import 分支 5a87cedd `prepare_sector_network.py`（第 4560–4562 行码头常数；第 2537–2930 行生物质；`solid_biomass_import`）、`config.default.yaml`（第 805–809、932–990 行） | R3.2、R4、R1.4 | 库内副本 `pypsa_eur_data/` |
| 6 | PyPSA-Eur v2025.07.0 `scripts/build_industrial_production_per_country_tomorrow.py` | R1.4：2050 产量 = 今日产量重分配（St_primary_fraction、DRI_fraction、HVC_primary_fraction），不增长 | GitHub raw |
| 7 | PyPSA-Earth（pypsa-asean 检出）`scripts/solve_network.py` 第 1190–1207 行；`config.default.yaml` renewable 块 | R8；R2 现行参数 | 本机 `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean` |
| 8 | Gurobi Optimizer Reference：Parameters（BarConvTol、FeasibilityTol、OptimalityTol、NumericFocus）；Optimization Status Codes（OPTIMAL、SUBOPTIMAL、TIME_LIMIT、NUMERIC、INF_OR_UNBD） | R8 容差定义 | docs.gurobi.com |
| 9 | ESMAP / Solargis / World Bank (2020), Global Photovoltaic Power Potential by Country：方法 Ch.2 p.12–13（Level 1 / Level 2 排除规则）；国别表 `solargis_pvpotential_countryranking_2020_data.xlsx`（Country indicators：Evaluated area、Level 1 area %、PVOUT L1） | R2 光伏锚 | 用户下载 `F1_renewable_potential/` |
| 10 | Zhong et al. (2026) PNAS Nexus pgaf389, SI Table S3 Renewable resource potentials (GW)（SI p.10–11，来源列表） | R2 对照 | 用户下载 |
| 11 | Zhong et al. (2025) iScience, SI Table S6 Renewable energy resources by ASEAN country (GW)（mmc1.pdf p.10–11） | R2 对照 | 用户下载 |
| 12 | World Bank Group / ESMAP, Global Offshore Wind Technical Potential（country-level xlsx, EAP 表） | R2 海上风电 | 经 S4P `EXT_TECH_POLICY_BENCHMARKS.json` |
| 13 | Global Energy Monitor, Global Gas Infrastructure Tracker – LNG Terminals, September 2025 release（`GEM-GGIT-LNG-Teminals-2025-09.xlsx`，LNG Terminals 表） | R3 容量统一来源 | 用户下载 `F2_lng/gem-download (1).zip` |
| 14 | GIIGNL Annual Report 2026（2025 年进口表；Thailand / Vietnam 码头段） | R3 交叉核对 | 用户下载 |
| 15 | ERIA / GCCSI (2024) Comprehensive CCUS Research Report, Ch.1 Geological Storage Potential of CO2 in Southeast Asia（Tables 1.4–1.18；§1.3.8–1.3.9 p.56） | R5 | 经 S4P 子代理（页码在 `EXT_TECH_POLICY_BENCHMARKS.md` §C） |
| 16 | Int. J. Greenhouse Gas Control (2014), preliminary assessment of CO2 storage in Cambodia（doi:10.1016/j.ijggc.2014.08.016；Kyoto Univ. repository 2433/191190） | R5 KH 规则 | WebSearch 摘要 |
| 17 | Santos (2022) MoU on Bayu-Undan CCS；IFC project page（10 Mtpa） | R5 TL 规则 | WebSearch |
| 18 | USGS Mineral Commodity Summaries 2021 / 2025 (cement)；worldsteel Steel Statistical Yearbook 2020 Table 1、World Steel in Figures 2024 / 2025 | R1.3 基年产量 | 经 S4P `EXT_DEMAND_BENCHMARKS.md` §5 |
| 19 | Viet Nam Decision 1266/QĐ-TTg (2020-08-18) Annex I 水泥产能上限；Decision 261/QĐ-TTg (2026-02-09) 钢铁战略；Decision 768/QĐ-TTg (2025-04-15) 修订 PDP8 | R1.3 国家上限、电力对照 | 同上 |
| 20 | IEA Cost of Capital Observatory（2025 dashboard update；2024 年 FID 光伏区间） | R6.6 | 注册表 `finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv` |
| 21 | Damodaran (NYU Stern), Country Default Spreads and Risk Premiums, 2026-01-05 | R6.6 | 经 S4P `EXT_COST_BENCHMARKS.md` §7 |
| 22 | IMF World Economic Outlook (October 2026), PCPIPCH 通胀 2024–2030（DataMapper API） | R6.6 实际利率换算 | https://www.imf.org/external/datamapper/api/v1/PCPIPCH/... |
| 23 | UN World Population Prospects 2024（TL 2050 人口 1.889 M，二手引述 worldometer / populationpyramid） | R1 TL 规则（DATA_PENDING 原文件） | WebSearch |
| 24 | Argus Media (2024-09-13) 再气化费；Höegh LNG / IGU (2017) 0.3 USD/MMBtu | R3.4 再气化加价 | 经 S4P `EXT_COST_BENCHMARKS.md` §6 |
| 25 | INL/RPT-24-77048 Rev.2 (2024) Meta-Analysis of Advanced Nuclear Reactor Cost Estimations, Table A-1；EIA/S&L (2024) Capital Cost AEO2025 Table 1-2；Lazard LCOE+ v18.0 | R6.3 核电成本 | 经 S4P `EXT_COST_BENCHMARKS.md` §2–3 |
| 26 | PyPSA technology-data v0.15.0 `outputs/costs_2050.csv`（nuclear、LNG storage tank 行；无 LNG 码头行）；`LAYER_MANIFEST.json`（平减残余说明） | R6.1 / R3.2 | 库内 `research_inputs/cost_layers_v5/` |
| 27 | Ulvestad & Overland (2012) Int. J. Environ. Stud. 69(3)（码头 1 bn USD / 10 Mtpa） | R3.2 替代成本 | 注册表 `lng_regas_capex_ref_ulvestad_overland_2012` |
| 28 | Copernicus Global Land Cover 100 m v3.0.1（Buchhorn et al. 2020, Zenodo 3939050）；WDPA；World Bank Global Shipping Traffic Density（dataset 0037580） | R2 重算所需栅格（用户下载清单） | `USER_DOWNLOAD_LIST.md` |
| 29 | S4P / S4Q / S4O / S4N 报告与证据（本仓库） | 全部 | `work/p1_step4p_20261020/`、`work/p1_step4q_20261020/` 等 |

DATA_PENDING 汇总：AEO8 D.15 价格年；7,018 EUR/MW/a 码头成本来源；30 EUR/t 封存价格年；TL 人口原文件；TL 封存潜力；KH 封存可复核来源（仅 2014 预评估）；海上风电观测容量因数（F9）；IEA / IGU / OIES 东南亚再气化费；Copernicus / WDPA / 航运栅格（需下载后重算）。
