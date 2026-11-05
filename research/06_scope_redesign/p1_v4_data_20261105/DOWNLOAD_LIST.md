# v4 工业细分数据下载清单（台账 W04；审阅端撰写，2026-11-05 21:00 SGT）

来源：师哥 11-05 两封邮件。**原则：** 文件名不改；每个来源放进对应子目录；同一来源有多个文件就全放一起；不要解压 zip / tar（Claude Code 在 W03 登记 SHA256 后再解）。下载时若网站要求登记用途，填 academic research（NUS, energy-system modelling）。
下载完成后把本文件末尾的"完成情况"表填上日期，截图给审阅端。

| 子目录 | 来源 | 网址 | 怎么下 | 期望得到 |
|---|---|---|---|---|
| `01_gem_steel` | GEM Global Iron & Steel Tracker | https://globalenergymonitor.org/projects/global-iron-steel-tracker/download-data/ | 点 Download data，填表（姓名、邮箱、机构、用途），邮件或页面给出下载链接 | 3 个 xlsx：plant-level、steel units、iron units（2026-09 版） |
| `02_gem_cement` | GEM Global Cement & Concrete Tracker | https://globalenergymonitor.org/projects/global-cement-concrete-tracker/download-data/ | 同上 | xlsx（水泥厂、熟料产能） |
| `03_gem_chemicals` | GEM Global Chemicals Inventory | https://globalenergymonitor.org/projects/global-chemicals-inventory/ | 页面上找 Download data，同上 | xlsx（基础化工设施、产能） |
| `04_sfi_pulp_paper` | Spatial Finance Initiative 造纸数据库 | https://cgfi.ac.uk/spatial-finance-initiative/geoasset-project/pulp-and-paper-database/ | 页面上的下载或登记链接 | xlsx / csv（纸浆与造纸厂、产能、产品） |
| `05_sfi_ethylene` | SFI 全球乙烯数据库（2025-12 版，CC BY 4.0） | https://zenodo.org/records/17866398 | 直接下载 | `Global_Ethylene_Production_Database_December_2025.xlsx`（237 kB） |
| `06_climate_trace` | Climate TRACE | https://climatetrace.org/data | 按国家下载：BN、KH、ID、LA、MY、MM、PH、SG、TH、TL、VN 各一个国家数据包（zip，内含各行业 csv）。若页面按行业下载，则下 manufacturing 全部行业 + fossil fuel operations 的 refining | 11 个 zip |
| `07_etsap_industrial_demand` | ETSAP 工业能源需求数据集（师哥给的 Scientific Data 论文的数据） | https://zenodo.org/records/15524913 （论文写 v2.0.2；若页面显示更新版本，下最新） | 直接下载 | 1 个 zip（约 0.7 MB），内含 01_Production_quantities、02_Energy_calculation、TIAM_regions.csv |
| `08_ffe_profiles` | FfE 德国工业电负荷归一化曲线 | https://opendata.ffe.de/dataset/normalized-industrial-electrical-load-profiles-germany/ | 页面上的全部 csv / 资源文件 | csv（按行业） |
| `09_nrel_heat` | NREL 制造业热负荷曲线（2014） | https://data.nlr.gov/submissions/118 | 只下这几个：`Manufacturing_Heat_Loadshapes.tar.gz`（9.2 MB）、`Process_heat_load_shapes.gzip`、`Boiler_load_shapes.gzip`（勘误版）、metadata JSON。**不要下 316 MB 的 CSV**（美国分县温度数据，用不到） | 4 个文件 |
| `10_unsd` | UNSD 能源统计 | https://unstats.un.org/unsd/energystats/data/ | **先不下。** 仓库已有 2019 年平衡表（v2 用过），W03 核对后若缺 2022 年再补 | — |
| `11_calliope_indonesia` | 师哥同事的 Calliope-Indonesia 模型 | https://github.com/JKALanger/calliope_indonesia | 页面绿色 Code 按钮 → Download ZIP | 1 个 zip；**未见许可证，引用前问师哥** |

已在库、不必再下：GEM Global Integrated Power Tracker（2026-09）、UNSD 2019、APEC 2022、USGS 各卷、JRC-IDEES-2021 比例表、PyPSA-Eur 2050 比例表。

## 完成情况

| 子目录 | 完成日期 | 文件数 | 备注 |
|---|---|---|---|
| 01 | | | |
| 02 | | | |
| 03 | | | |
| 04 | | | |
| 05 | | | |
| 06 | | | |
| 07 | | | |
| 08 | | | |
| 09 | | | |
| 11 | | | |
