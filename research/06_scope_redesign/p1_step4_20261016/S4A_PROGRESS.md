# S4A 进度记录（防中断用；每个子步骤提交后更新）

分支 `codex/s4a-resources-fleet-20261016`（自 S3B 最终提交 05be057c 开出）；draft PR 叠在 PR #24 上（基分支 `codex/s3-gas-imports-shipping-20261015`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）、`formal_barrier`（第 69 项）+ 缩放；止损同 S3B（56×3h 上限 30 分钟，非最优即停、不重试）。
授权：第 70–73 项与 L14–L16（用户 2026-10-16）；工作原则第 3 条（优先沿用 PyPSA-Eur/Earth，东盟特有问题另行设计并写明原因）、第 6 条（止损）。不编造数据；表单/注册数据列入下载清单。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4A-0 | 分支、第十批数据核对、现状盘点、进度文件 | 完成 | 本节提交 | raw10 两个文件 SHA256 与 `SHA256SUMS_raw10.txt` 一致（IRENA ffe8ce4b…、gem-data.zip b0d3139d…）；zip 内 `Global Integrated Power September 2026.xlsx`（183,404 行，东盟 6,958 行）、`Global-Oil-and-Gas-Extraction-Tracker-March-2026.xlsx`（东盟 250 个气/油田）；盘点结论见下 |
| S4A-1 | 风光资源与出力曲线（L14） | 待做 | — | |
| S4A-2 | 存量机组补全（L15）+ 气田产量节点分配 | 待做 | — | |
| S4A-3 | 核电/地热/水电候选潜力与成本（L16） | 待做 | — | |
| S4A-4 | 构建与冒烟（两情景，56×3h Gurobi） | 待做 | — | |
| 交付 | S4A_REPORT.md、S4A_EVIDENCE.json、DOWNLOAD_LIST.csv、资源估算更新 | 待做 | — | |

## S4A-0 盘点（2026-10-16）

- **出力曲线来源链：** 研究层电力底座 `electric_base_2050_unsolved.nc` 的 `p_max_pu` 继承自作者论文结果网络 `results-asean-paper-v1/baseline-aims-3H/elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc`（`ELECTRIC_BASE_ASSET_MANIFEST.json` inputs），2920 个 3h 时段、2013 年全年，季节变化真实（非周期重复）。本机只有教程 cutout `pypsa-asean/cutouts/asean-2013-era5-tutorial.nc`（2013-03-01 至 03-07，168 h，0.3°，x 89.7–141.9、y −14.4–29.1），作者 `resources/baseline-aims-3H-tutorial/renewable_profiles/*.nc` 同样只有 168 h。**全年 cutout 不在本机**；PyPSA-Earth Zenodo 包 `bundle_cutouts_asia.zip`（record 18039581，31.17 GB，含 ASEAN）可公开下载，**重建前估算（S4A-0，INFERENCE）：** 下载实测 1.8 MB/s（Zenodo 分段请求 100 MB 用 58 s）→ 31.17 GB 约 4.8–5.5 h；磁盘需 31 GB（zip）+ 解压后全亚洲 cutout（估 30–60 GB），本机剩余 934 GB；只对东盟范围（175×146 格点 × 8,760 h）做 atlite 转换：每个变量 0.9 GB（float32），风用 1 个时变量、光伏用 7 个，按时间分块后峰值估 3–4 GiB，低于本机 10 GiB；转换用时估 10–60 min。结论：不超过本机能力，S4A-0 起在后台只读下载（断点续传，完成后校验 MD5 f37ea8b3…），下载期间继续审计。
- **模型容量因子（S3B 冒烟网络，2920 时段加权）：** 陆上风国家均值 BN 0.020、ID 0.052、KH 0.052、LA 0.048、MM 0.048、MY 0.031、PH 0.135、SG 0.046、TH 0.060、TL 0.048、VN 0.090；节点最大 PH 0.254、ID 0.199、VN 0.129；海上风 DC 均值 VN 0.389（最大 0.541）、PH 0.209；光伏 0.127–0.155。
- **存量机组（网络，2050 在役）：** 748 个单元身份（煤/气/褐煤/油 Link、水电/抽蓄 StorageUnit、ROR/地热 Generator）；GEM 在运+在建（2026-09 GIPT）东盟合计：煤 134.0 GW、油气 136.3 GW、水电 63.9 GW、光伏 36.9 GW、风 13.6 GW、生物质 5.8 GW、地热 5.3 GW、核电 0。
- **气田：** GOGET 东盟 250 个单元，41 条天然气产量记录（最新年份），有坐标的在运气田 BN 1、ID 18、MM 1、MY 11、PH 1、TH 6、VN 2；KH/LA/SG 无（与 UNSD 上限 0 一致）。
