# S4R：需要用户下载的文件清单 v2（M08-0 修订版；原件不改）

> **修订说明（M08-0，第 130 项，2026-10-20）**
> - 原件：`work/p1_step4r_20261020/USER_DOWNLOAD_LIST.md`（SHA256 `6b97f33ccf7a4c4d4acb610299e434628ce5f829c04a871dc8755fcdc1003c2d`），保留不动；本文件是新版本。
> - **删去 A1**（World Bank Global Shipping Traffic Density）：该数据集已在 `work/p2_data_intake/raw12/shipdensity_global.zip`（534,907,276 B，SHA256 `7d103de52acf355ffc2436909d5d98e9db93f74d6ad237680e5da6d6d24a9248`，M08-0 重新计算，与注册表 `offshore_shipdensity_raw12_verified` 一致；World Bank dataset 0037580，CC BY 4.0），无需下载。改列入 §0"已有图层"。注册表 `renewable_ship_density_raster` 已由 DATA_PENDING 改为 REFERENCE_ONLY（M08-0）。
> - 其余各项（A2–A5、B1–B7）原样保留，编号不变以便对照原件；"主算必需"组现为 A2–A5。
> - 相关结论（M08-0 第 2 项）：海上风电机型 2020ATB 5.5 MW 与尾流 0.8855 已在筛查网络中，M08-7 的海上对齐只剩会改变 `p_nom_max` 的面积规则（60 m、漂浮类、航道排除、DC 密度），所需 GEBCO、EEZ、航运密度栅格均已在本机。

（以下为原件内容，已按上述说明修订。）

## 0. 作者缓存与数据接收目录中已有、无需下载的图层（原件 2026-10-20 核对 `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/`；航运密度一行由 M08-0 补入）

| 图层 | 文件 | 说明 |
|---|---|---|
| Copernicus Global Land Cover 100 m v3.0.1（2019 nrt，离散分类，全球单文件） | `data/copernicus/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif`（1.71 GB） | 现网络布局即由此计算；开阔林 121–126 敏感性也只需此文件 → **原第 1 项（4–6 GB 瓦片）撤销** |
| 保护区（WDPA 栅格） | `data/natura/natura.tiff`（3.4 MB；Harvard Dataverse `wdpa_reclass.tif`，Sosa Arango 2020，CC0；`data/natura/metadata.json`） | 现网络的 natura 排除层；主算沿用。最新 WDPA 仅在用户要求更新保护区边界时才需下载（敏感性） |
| GEBCO 2025 水深 | `data/gebco/GEBCO_2025_sub_ice.nc`（1.35 GB） | 海上风电 60 m / 漂浮 60–1,000 m 规则可直接重算 |
| EEZ v11 | `data/eez/eez_v11.gpkg`（165 MB） | 同上 |
| World Bank Global Shipping Traffic Density（原 A1，M08-0 补入） | `work/p2_data_intake/raw12/shipdensity_global.zip`（535 MB，未解压；内含 tif 9.82 GB + ovr 3.29 GB；SHA256 `7d103de5…9248`） | R2 海上风电 `ship_threshold 400` 航道排除所需；用 GDAL `/vsizip/` 裁到东盟窗口即可，无需下载 |

## A. 主算必需

| # | 标题 | URL | 目标文件夹 | 用途 | 大小 / 备注 |
|---|---|---|---|---|---|
| A2 | USGS Minerals Yearbook，Cement 章世界产量表（最新年份；MCS 2025 只列 ID、VN） | https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information （Minerals Yearbook → Cement，Table "World production, by country or locality"） | `work/p1_s4r_downloads_20261020/R1_demand/` | R1.3 统一基年 2024 的水泥产量：TH / MY / PH / KH / LA / MM / BN（本步用国家统计或 EDGAR 2019 持平作过渡值，已标 DATA_PENDING） | PDF 约 1 MB；pubs.usgs.gov 的章节 URL 本步四种猜测均 404 |
| A3 | worldsteel Steel Data Viewer：2024 粗钢产量（SG、MM；WSIF 2025 只列前 50 名） | https://worldsteel.org/data/steel-data-viewer/ | 同上 | R1.3 统一基年（本步 SG 0.77 / MM 0.35 Mt 用 2019 值持平） | 网页导出 |
| A4 | UN World Population Prospects 2024，Timor-Leste 2050 中位人口 | https://population.un.org/wpp/ （Download Center → Standard Projections → Population） | 同上 | R1 TL 锚定规则（本步用二手引述 1.889 M） | Excel 数 MB |
| A5 | Eurostat HICP 年均指数 `prc_hicp_aind`（欧元区，2020–2025） | https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/ | `work/p1_s4r_downloads_20261020/R6_costs/` | R6.1 用 HICP 回算 technology-data v0.15.0（消除 +4.8 % 残余）；若改走"取 2020 源值"路径则需第 B5 项 | CSV < 1 MB |

（原 A1 已删去，见文首修订说明。）

## B. 仅敏感性需要

| # | 标题 | URL | 用途 | 大小 / 备注 |
|---|---|---|---|---|
| B1 | （撤销）Copernicus LC100 瓦片 | — | 开阔林敏感性用作者缓存的全球文件即可 | 0 |
| B2 | WDPA 最新版（World Database on Protected Areas，东南亚 11 国或全球） | https://www.protectedplanet.net/en/thematic-areas/wdpa | 保护区边界更新敏感性（现网络用 2020 Dataverse 栅格） | 全球包 > 1 GB |
| B3 | WBG-ESMAP Global Offshore Wind Technical Potential 国别 Excel | https://datacatalogfiles.worldbank.org/ddh-published/0037787/DR0045697/technicalpotential_countrylevel_wbg_esmap.xlsx | R2 海上风电对照原文件存档（数值已由 S4P 读取） | < 1 MB |
| B4 | OGCI CO₂ Storage Resource Catalogue Cycle 5, Appendix B Asia | https://www.ogci.com/wp-content/uploads/2025/11/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf | R5 KH 0.085 / TL 0.25 Gt 来源复核（主算已改 ERIA / 文献 / 零） | 5–10 MB，站点有 bot 检查。**M08-0 注：** 同名文件已在 `work/p2_data_intake/raw2/`（SHA256 `ff21cd34…6d0f`，与注册表 D1 记录一致），但各国汇总表为图片、文本提取不到数值，本步未能据此复核 |
| B5 | technology-data v0.15.0 源数据 `inputs/` 或 `outputs/costs_2020.csv` | https://github.com/PyPSA/technology-data/tree/v0.15.0 | R6.1 替代路径（直接取 2020 源值）与对比 | 仓库 ZIP 约 100 MB |
| B6 | IEA Cost of Capital Observatory 数据表（Dashboard 导出） | https://www.iea.org/reports/cost-of-capital-observatory/dashboard | F7 分国 WACC 敏感性表的原始区间 | — |
| B7 | ACE AEO8 成本表价格年（向 ACE 查询） | https://aseanenergy.org/publications/the-8th-asean-energy-outlook/ | R6.2 敏感性因子 0.86 的依据 | 需联系作者 |
