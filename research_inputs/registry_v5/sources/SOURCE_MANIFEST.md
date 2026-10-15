# P2 数据入库：来源清单（2026-10-15）

用户于 2026-10-15 05:34 SGT 上传 `数据.zip`，原始文件逐字节保存在 `raw/`，SHA256 见 `SHA256SUMS.txt`。抽取结果在 `extraction/`，是只读整理，不是模型输入。进入模型前，仍需逐项写入数据登记表（A/B/C 分级）。

| 文件 | 文献 | 来源网址 | 用途 |
|---|---|---|---|
| raw/CarbonCaptureUtilisationandStorage_TheOpportunityinSoutheastAsia.pdf | IEA (2021) *CCUS: The Opportunity in Southeast Asia* | https://www.iea.org/reports/carbon-capture-utilisation-and-storage-the-opportunity-in-southeast-asia | CO₂ 封存潜力（二手汇编） |
| raw/1_Chapter-1-Geological-Storage-Potential-of-CO2-in-Southeast_Asia.pdf | ERIA/GCCSI (2024) 第 1 章，CO₂ 地质封存潜力 | https://eria.org/uploads/1_Chapter-1-Geological-Storage-Potential-of-CO2-in-Southeast_Asia.pdf | CO₂ 封存潜力（P10/P50/P90，盆地级） |
| raw/carbon-capture-storage-southeast-asia.pdf | ADB (2013) *Prospects for CCS in Southeast Asia* | https://www.adb.org/publications/prospects-carbon-capture-and-storage-southeast-asia | 封存潜力交叉验证；各国运输与封存成本 |
| raw/IRENA_Biofuel_Potential_SE_Asia_2017.pdf | IRENA (2017) *Biofuel Potential in Southeast Asia* | https://www.irena.org/Publications/2017/Jun/Biofuel-potential-in-Southeast-Asia-Raising-food-yields-reducing-food-waste-and-utilising-residues | 生物质潜力（5 国） |
| raw/IRENA_Biomass_Energy_Transition_2022.pdf | IRENA (2022) *Scaling up biomass for the energy transition: Untapped opportunities in Southeast Asia* | https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2022/Feb/IRENA_Biomass_Energy_Transition_2022.pdf | 生物质可收集量与可持续原则 |
| raw/GEM-GGIT-LNG-Teminals-2025-09.xlsx | Global Energy Monitor，Global Gas Infrastructure Tracker – LNG Terminals（2025-09 版） | https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker | LNG 接收站位置与容量 |

上传包中还有 GEM 的其他数据（Gas Pipelines、LNG Carrier、Energy Ownership），本次没有入库；需要时可以从用户上传的原包中取。

## 第二批（用户 2026-10-15 06:42 上传 `数据2.zip`）

原始文件保存在 `raw2/`，SHA256 见 `SHA256SUMS_raw2.txt`。

| 文件 | 文献 | 用途 | 抽取结果 |
|---|---|---|---|
| raw2/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf | OGCI CO₂ Storage Resource Catalogue Cycle 5，Appendix B: Asia（2025-08） | 11 国封存资源（SRMS 分级） | extraction/CO2_STORAGE_OGCI_EXTRACTION.md |
| raw2/CSRC_Cycle_3_Appendix_B_Asia.pdf | 同上 Cycle 3 | 交叉核对 | 同上 |
| raw2/210914_MOU-signed-on-Bayu-Undan-Carbon-Capture-and-Storage.pdf | Santos ASX 公告，2021-09-14 | 东帝汶 Bayu-Undan 年注入能力（约 10 Mtpa） | 同上 |
| raw2/210914-Bayu-Undan-…-Bayu-Undan.pdf | 同一公告的德顿语版 | 存档 | — |
| raw2/WorldEnergyOutlook2025.pdf | IEA WEO 2025 | 分情景化石燃料价格、CO₂ 价格 | extraction/WEO2025_FOSSIL_PRICES.md/.csv |
| raw2/8th ASEAN Energy Outlook_….pdf | ACE，第 8 版东盟能源展望（AEO8） | 2050 年各情景需求，用于口径和交叉核对 | extraction/AEO8_2050_DEMAND.md 及 CSV |
| raw2/Production_Crops_Livestock_E_All_Data.zip | FAOSTAT QCL | 生物质自下而上 | extraction/BIOMASS_RAW_DATA_SUMMARY.md 及 CSV |
| raw2/Forestry_E_All_Data.zip | FAOSTAT FO | 同上 | 同上 |
| raw2/What_a_Waste_3.0_COUNTRY_Dataset_&_Codebook.xlsx | World Bank What a Waste 3.0（国家级） | 城市垃圾，含 2050 预测 | 同上 |
| raw2/What_a_Waste_3.0_CITY_Dataset_&_Codebook.xlsx | 同上（城市级） | 备用，暂未使用 | — |
| raw2/Annual Report 2025.pdf | MIT CS3 2025 年报 | **不是所需文献**（原本要下载 Kearns et al. 2017），不使用 | — |

## 第三批（用户 2026-10-15 07:29 上传 `数据3.zip`）

原始文件保存在 `raw3/`，SHA256 见 `SHA256SUMS_raw3.txt`。

| 文件 | 文献 | 用途 | 抽取结果 |
|---|---|---|---|
| raw3/iamc_data-6f1635fd-….csv | IIASA SSP Scenario Explorer 导出：IIASA-WiC POP 2025（Population，百万人）、OECD ENV-Growth 2025（GDP\|PPP，十亿美元，2010/2015/2017 三种价格基准），SSP2，11 国，2025–2100 每 5 年 | 第 34 项：分国增长分配 | extraction/SSP2_2025_POP_GDP_ASEAN11.csv（只保留 Population 和 GDP\|PPP USD_2017，22 行） |
| raw3/ASFR_AE_SSPs_V15.csv | Wittgenstein Centre 分年龄、性别、教育的人口明细（区域为数字编码） | 不需要，存档不用 | — |

缺口：导出从 2025 年开始，没有 2019/2020 年的基年值，需从同一网站的 Historical Reference 情景或 World Bank WDI 补齐。

## 第四批（用户 2026-10-15 上传 WDI 导出）

原始文件保存在 `raw4/`，SHA256 见 `SHA256SUMS_raw4.txt`。

| 文件 | 文献 | 用途 | 抽取结果 |
|---|---|---|---|
| raw4/b5f8c3ae-…_Data.csv、raw4/b5f8c3ae-…_Series - Metadata.csv | World Bank WDI（DataBank 导出），11 国 GDP 与人口，2019–2025 | 补齐 SSP2 导出缺少的 2019–2025 段，形成 2019→2050 增长链（第 34 项） | extraction/GROWTH_CHAIN_2019_2050_WDI_SSP2.csv |

## 第五批（用户 2026-10-15 13:04 上传 `数据4.zip`）

原始文件保存在 `raw5/`，SHA256 见 `SHA256SUMS_raw5.txt`。

| 文件 | 文献 | 用途 | 抽取结果 |
|---|---|---|---|
| raw5/IEA_EDGAR_CO2_1970_2024.zip | EDGAR 2025 GHG（IEA-EDGAR CO2），JRC，https://edgar.jrc.ec.europa.eu/dataset_ghg2025 ，CC BY-NC-ND 4.0 | 各国工业过程排放（L19）、逸散排放、垃圾焚烧 | extraction/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv；说明见 extraction/EDGAR2025_USGS2025_PROCESS_EMISSIONS.md |
| raw5/mcs2025-cement.pdf | USGS Mineral Commodity Summaries 2025, Cement | 交叉核对（东盟只列出 ID、VN） | 同上，第 2 节 |
| raw5/mcs2025-iron-steel.pdf | USGS Mineral Commodity Summaries 2025, Iron and Steel | 交叉核对（东盟只列出 VN） | 同上 |

## 第六批（用户 2026-10-15 13:16 上传 `数据5.zip`）

原始文件保存在 `raw6/`（已重命名，原名对照见 extraction/BATCH6_BUNKERS_AND_FOREST_RESIDUES.md 第 3 节），SHA256 见 `SHA256SUMS_raw6.txt`。

| 文件 | 文献 | 用途 | 抽取结果 |
|---|---|---|---|
| raw6/UNSD_EB_2019_{BN,KH,LA,TL}.csv | UNSD Energy Balance Visualization，"Energy Balances" 导出，2019，TJ，https://unstats.un.org/unsd/energystats/dataPortal/ | 四国国际海运、航空燃料舱（D1 的 DATA_PENDING） | extraction/UNSD_EB_2019_BUNKERS_BN_KH_LA_TL.csv |
| raw6/JRC98626_biomass_potentials_in_europe_web_rev.pdf | Ruiz et al.（2015）JRC-EU-TIMES 生物质潜力报告（ENSPRESO 方法学） | 林业残余系数核查：无可迁移的残余/原木比，只有采收约束 | extraction/BATCH6_BUNKERS_AND_FOREST_RESIDUES.md |
