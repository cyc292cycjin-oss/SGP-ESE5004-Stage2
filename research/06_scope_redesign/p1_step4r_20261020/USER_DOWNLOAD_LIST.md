# S4R：需要用户下载的文件清单（本会话未自行下载 > 2 GB 或预计 > 30 分钟的文件；网页拒绝访问的未绕行）

| # | 标题 | URL | 目标文件夹 | 用途 | 大小 / 备注 |
|---|---|---|---|---|---|
| 1 | Copernicus Global Land Cover 100 m（LC100, 2019 discrete classification, 东南亚 20°×20° 瓦片，共约 6 块：E100N20、E100N00、E120N20、E120N00、E100N40、E140N00 等） | https://zenodo.org/records/3939050 （Buchhorn et al. 2020, v3.0.1） | `work/p1_s4r_downloads_20261020/R2_landcover/` | R2：按统一参数重算光伏 / 风电可用面积（M08 布局重建） | 每块约 0.5–1 GB，合计约 4–6 GB → 用户下载 |
| 2 | WDPA（World Database on Protected Areas）东南亚 11 国 shapefile（或全球 geodatabase） | https://www.protectedplanet.net/en/thematic-areas/wdpa | 同上 | R2：natura 等价的保护区排除层（现网络已用作者缓存，重算时需最新） | 全球包 > 1 GB |
| 3 | World Bank Global Shipping Traffic Density（已登记 raw12，535 MB，若本机缓存缺失再下载） | https://datacatalog.worldbank.org/search/dataset/0037580 | `work/p1_s4r_downloads_20261020/R2_shipping/` | R2：对齐 PyPSA-Eur `ship_threshold` 的航道排除 | 535 MB |
| 4 | WBG-ESMAP Global Offshore Wind Technical Potential 国别 Excel（`technicalpotential_countrylevel_wbg_esmap.xlsx`） | https://datacatalogfiles.worldbank.org/ddh-published/0037787/DR0045697/technicalpotential_countrylevel_wbg_esmap.xlsx | `work/p1_s4r_downloads_20261020/F1_renewable_potential/` | R2：海上风电技术潜力原文件（S4P 子代理已读取数值，建议存档） | < 1 MB |
| 5 | OGCI CO₂ Storage Resource Catalogue Cycle 5, Appendix B Asia（PDF，站点有 bot 检查） | https://www.ogci.com/wp-content/uploads/2025/11/CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf | `work/p1_s4r_downloads_20261020/R5_co2/` | R5：复核 KH 0.085 / TL 0.25 Gt 的来源 | 约 5–10 MB |
| 6 | UN World Population Prospects 2024，Timor-Leste 人口中位预测（2050） | https://population.un.org/wpp/ （Download Center → Standard Projections → Population） | `work/p1_s4r_downloads_20261020/R1_demand/` | R1：TL 锚定规则的人口（本步用二手引述 1.889 M，标 DATA_PENDING） | Excel 数 MB |
| 7 | IEA Cost of Capital Observatory 数据表（Dashboard 导出，若可下载） | https://www.iea.org/reports/cost-of-capital-observatory/dashboard | `work/p1_s4r_downloads_20261020/R6_wacc/` | R6：分国 WACC 表的原始区间（本步用注册表已登记的 2024 光伏区间） | — |
| 8 | ACE AEO8 成本数据价格年：向 ACE 查询或在 AEO8 第 D.3 节附件中寻找（本步在正文与附录 D 未找到） | https://aseanenergy.org/publications/the-8th-asean-energy-outlook/ | — | R6：AEO8 Table D.15 的价格年（DATA_PENDING） | 需联系作者 |
| 9 | technology-data v0.15.0 源数据 `inputs/`（DEA 2020 年价原表）或仓库 `outputs/costs_2020.csv` | https://github.com/PyPSA/technology-data/tree/v0.15.0 | `work/p1_s4r_downloads_20261020/R6_costs/` | R6：消除 +4.8 % 平减残余（取 2020 源值路径） | 仓库 ZIP 约 100 MB |
