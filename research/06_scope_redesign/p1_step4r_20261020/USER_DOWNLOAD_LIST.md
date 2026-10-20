# S4R：需要用户下载的文件清单（已按补充 01 §3 修订：分"主算必需"与"仅敏感性需要"；本会话未自行下载 > 2 GB 或预计 > 30 分钟的文件；网页拒绝访问的未绕行）

## 0. 作者缓存中已有、无需下载的图层（2026-10-20 核对 `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/`）

| 图层 | 文件 | 说明 |
|---|---|---|
| Copernicus Global Land Cover 100 m v3.0.1（2019 nrt，离散分类，全球单文件） | `data/copernicus/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif`（1.71 GB） | 现网络布局即由此计算；开阔林 121–126 敏感性也只需此文件 → **原第 1 项（4–6 GB 瓦片）撤销** |
| 保护区（WDPA 栅格） | `data/natura/natura.tiff`（3.4 MB；Harvard Dataverse `wdpa_reclass.tif`，Sosa Arango 2020，CC0；`data/natura/metadata.json`） | 现网络的 natura 排除层；主算沿用。最新 WDPA 仅在用户要求更新保护区边界时才需下载（敏感性） |
| GEBCO 2025 水深 | `data/gebco/GEBCO_2025_sub_ice.nc`（1.35 GB） | 海上风电 60 m / 漂浮 60–1,000 m 规则可直接重算 |
| EEZ v11 | `data/eez/eez_v11.gpkg`（165 MB） | 同上 |

## A. 主算必需

| # | 标题 | URL | 目标文件夹 | 用途 | 大小 / 备注 |
|---|---|---|---|---|---|
| A1 | World Bank Global Shipping Traffic Density（栅格；注册表 `renewable_ship_density_raster` 已登记为 DATA_PENDING） | https://datacatalog.worldbank.org/search/dataset/0037580 | `work/p1_s4r_downloads_20261020/R2_shipping/` | R2 海上风电对齐 PyPSA-Eur `ship_threshold 400` 的航道排除（海上规则对齐仍在主算；若用户决定海上规则也延后到敏感性，则本项移到 B 组） | 535 MB（< 2 GB，M08 会话可自行下载；本步未下载） |
| A2 | USGS Minerals Yearbook，Cement 章世界产量表（最新年份；MCS 2025 只列 ID、VN） | https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information （Minerals Yearbook → Cement，Table "World production, by country or locality"） | `work/p1_s4r_downloads_20261020/R1_demand/` | R1.3 统一基年 2024 的水泥产量：TH / MY / PH / KH / LA / MM / BN（本步用国家统计或 EDGAR 2019 持平作过渡值，已标 DATA_PENDING） | PDF 约 1 MB；pubs.usgs.gov 的章节 URL 本步四种猜测均 404 |
| A3 | worldsteel Steel Data Viewer：2024 粗钢产量（SG、MM；WSIF 2025 只列前 50 名） | https://worldsteel.org/data/steel-data-viewer/ | 同上 | R1.3 统一基年（本步 SG 0.77 / MM 0.35 Mt 用 2019 值持平） | 网页导出 |
| A4 | UN World Population Prospects 2024，Timor-Leste 2050 中位人口 | https://population.un.org/wpp/ （Download Center → Standard Projections → Population） | 同上 | R1 TL 锚定规则（本步用二手引述 1.889 M） | Excel 数 MB |
| A5 | Eurostat HICP 年均指数 `prc_hicp_aind`（欧元区，2020–2025） | https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/ | `work/p1_s4r_downloads_20261020/R6_costs/` | R6.1 用 HICP 回算 technology-data v0.15.0（消除 +4.8 % 残余）；若改走"取 2020 源值"路径则需第 B5 项 | CSV < 1 MB |

## B. 仅敏感性需要

| # | 标题 | URL | 用途 | 大小 / 备注 |
|---|---|---|---|---|
| B1 | （撤销）Copernicus LC100 瓦片 | — | 开阔林敏感性用作者缓存的全球文件即可 | 0 |
| B2 | WDPA 最新版（World Database on Protected Areas，东南亚 11 国或全球） | https://www.protectedplanet.net/en/thematic-areas/wdpa | 保护区边界更新敏感性（现网络用 2020 Dataverse 栅格） | 全球包 > 1 GB |
| B3 | WBG-ESMAP Global Offshore Wind Technical Potential 国别 Excel | https://datacatalogfiles.worldbank.org/ddh-published/0037787/DR0045697/technicalpotential_countrylevel_wbg_esmap.xlsx | R2 海上风电对照原文件存档（数值已由 S4P 读取） | < 1 MB |
| B4 | OGCI CO₂ Storage Resource Catalogue Cycle 5, Appendix B Asia | https://www.ogci.com/wp-content/uploads/2025/11/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf | R5 KH 0.085 / TL 0.25 Gt 来源复核（主算已改 ERIA / 文献 / 零） | 5–10 MB，站点有 bot 检查 |
| B5 | technology-data v0.15.0 源数据 `inputs/` 或 `outputs/costs_2020.csv` | https://github.com/PyPSA/technology-data/tree/v0.15.0 | R6.1 替代路径（直接取 2020 源值）与对比 | 仓库 ZIP 约 100 MB |
| B6 | IEA Cost of Capital Observatory 数据表（Dashboard 导出） | https://www.iea.org/reports/cost-of-capital-observatory/dashboard | F7 分国 WACC 敏感性表的原始区间 | — |
| B7 | ACE AEO8 成本表价格年（向 ACE 查询） | https://aseanenergy.org/publications/the-8th-asean-energy-outlook/ | R6.2 敏感性因子 0.86 的依据 | 需联系作者 |
