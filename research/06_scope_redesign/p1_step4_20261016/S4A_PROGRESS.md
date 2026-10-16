# S4A 进度记录（防中断用；每个子步骤提交后更新）

分支 `codex/s4a-resources-fleet-20261016`（自 S3B 最终提交 05be057c 开出）；draft PR 叠在 PR #24 上（基分支 `codex/s3-gas-imports-shipping-20261015`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）、`formal_barrier`（第 69 项）+ 缩放；止损同 S3B（56×3h 上限 30 分钟，非最优即停、不重试）。
授权：第 70–73 项与 L14–L16（用户 2026-10-16）；工作原则第 3 条（优先沿用 PyPSA-Eur/Earth，东盟特有问题另行设计并写明原因）、第 6 条（止损）。不编造数据；表单/注册数据列入下载清单。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| 续行 01 | 清理中断的 31 GB 下载、改用 raw11 东盟 cutout、新增工作原则第 7 条 | 完成 | 随 S4A-1 提交 | 下载进程已无；删除部分文件 874,930,176 B + 日志 + 脚本，释放 0.87 GB；raw11 zip SHA256/MD5 一致，解压到 `cutouts/asean_zenodo_20325289/`（7.35 GB，ext4，gitignored）；范围 89.7–141.9°E / −14.4–29.1°N、0.3°、2013 全年逐时、15 变量；96 节点与 11 国陆海形状留 1 格缓冲全部在内；与教程 cutout 抽查逐值相同；气象年份 2013 与负荷/水电/出力曲线一致。**违规记录：** 全亚洲包下载未事先报告（第 6 条），已改正，见报告 §0 |
| S4A-0 | 分支、第十批数据核对、现状盘点、进度文件 | 完成 | fa7482c3 | raw10 两个文件 SHA256 与 `SHA256SUMS_raw10.txt` 一致（IRENA ffe8ce4b…、gem-data.zip b0d3139d…）；zip 内 `Global Integrated Power September 2026.xlsx`（183,404 行，东盟 6,958 行）、`Global-Oil-and-Gas-Extraction-Tracker-March-2026.xlsx`（东盟 250 个气/油田）；盘点结论见下 |
| S4A-1 | 风光资源与出力曲线（L14） | 完成 | 6cc72794 | 审计表 §1.1（cutout ERA5 2013 0.3°；V112 80 m / NREL 5 MW 90 m；光伏修正 0.854337；LC100 排除；水深 50 m；简单潜力）；PyPSA-Eur v2025.07.0 对照 §1.2；IRENA RPGC 2024 + GWA 3.3（44 个栅格 2.46 GB，`SHA256SUMS_gwa.txt`）三方对比 §1.3：模型陆风 CF 比 GWA 国家均值低 2–3 倍、比 IRENA PH/VN 新项目低 3–4 倍；改正 A 已实现为开关 `research.renewable.profile_variant: original|fork|pypsa_eur`（主算 pypsa_eur：海上 NREL 2020ATB 5.5 MW@120 m × 0.8855、光伏去修正；`resource_classes` N 级机制，默认 1）；改正 B 只 PROPOSED（GWA 偏差缩放、现代机型、漂浮式、航道排除）；台风 PROPOSED §1.5；重建脚本 `scripts_project/s4a_profiles.py`（各国 Voronoi 节点区域 + 作者潜力；教程周复现 corr 中位数 ≥ 0.992）；全年重建 c1 5 min 27 s / 3.71 GiB、c3 5 min 36 s / 4.06 GiB（首轮 float32 比较漏掉各节点最高 CF 格点，已修复并重跑，见 §1.6）；pypsa_eur 相对原曲线：陆风 ≈ 1.0、海上 AC ×1.21–1.61、DC ×1.15–1.52、光伏 ×1.17；应用到电力底座 423 台替换 / 15 台保留；注册表 `renewable_s4a` 40 行；构建静态 PASS（1 min 05 s / 0.60 GiB）；研究层测试 400 通过 / 4 失败（test_gate4 既有）。本提交把 `s2_network.py`/`v5_gates.py`/`baseline.yaml` 停在 S4A-1 状态；S4A-2 的代码（`s4a_fleet.py`、`s4a_2_fleet_data.py`、`fleet_v5/`）已在工作区，随 S4A-2 提交 |
| S4A-2 | 存量机组补全（L15）+ 气田产量节点分配 | 完成 | S4A-2 提交（哈希在 S4A-3 行提交时补填） | GEM GIPT 2026-09 按单元 ID 精确连接（745/748 个身份为 GEM ID）；S1 寿命规则判断 2050 在役；在运 + 在建计入（`include_construction: true`，§5 决定）；缺失 299 台 73,615 MW，补入 295 台 73,515 MW（137 个组件 `::S4A`，垃圾 100 MW 跳过 DATA_PENDING）：CCGT 30,962、煤 17,187、水电 8,385、光伏 5,724、OCGT 3,787、径流 3,010、抽蓄 2,600、地热 752、陆风 555、油 272、褐煤 200、海风 80；分国 ID 22,589、VN 20,256、PH 9,617、MY 5,864、LA 4,811；无投运年 244 台 14,628 MW 未补；反向核对 11 台 2,854 MW 未移除；FOM +2.398e9 EUR/a；气田分配开关 `gem_fields`（GOGET 最新年产量份额 → 最近节点，覆盖率 BN 0.99、PH 0.75、MM 0.41、ID 0.36、TH 0.36、MY 0.28、VN 0.18，TL 无 → 负荷份额 DATA_PENDING），气井 Generator 84 → 19；构建静态 PASS、B12/B14/B15 通过；测试 406 通过 / 4 失败（test_gate4 既有）；报告 §2 |
| S4A-3 | 核电/地热/水电候选潜力与成本（L16） | 待做 | — | |
| S4A-4 | 构建与冒烟（两情景，56×3h Gurobi） | 待做 | — | |
| 交付 | S4A_REPORT.md、S4A_EVIDENCE.json、DOWNLOAD_LIST.csv、资源估算更新 | 待做 | — | |

## S4A-0 盘点（2026-10-16）

- **出力曲线来源链：** 研究层电力底座 `electric_base_2050_unsolved.nc` 的 `p_max_pu` 继承自作者论文结果网络 `results-asean-paper-v1/baseline-aims-3H/elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc`（`ELECTRIC_BASE_ASSET_MANIFEST.json` inputs），2920 个 3h 时段、2013 年全年，季节变化真实（非周期重复）。本机只有教程 cutout `pypsa-asean/cutouts/asean-2013-era5-tutorial.nc`（2013-03-01 至 03-07，168 h，0.3°，x 89.7–141.9、y −14.4–29.1），作者 `resources/baseline-aims-3H-tutorial/renewable_profiles/*.nc` 同样只有 168 h。**全年 cutout 不在本机**；PyPSA-Earth Zenodo 包 `bundle_cutouts_asia.zip`（record 18039581，31.17 GB，含 ASEAN）可公开下载，**重建前估算（S4A-0，INFERENCE）：** 下载实测 1.8 MB/s（Zenodo 分段请求 100 MB 用 58 s）→ 31.17 GB 约 4.8–5.5 h；磁盘需 31 GB（zip）+ 解压后全亚洲 cutout（估 30–60 GB），本机剩余 934 GB；只对东盟范围（175×146 格点 × 8,760 h）做 atlite 转换：每个变量 0.9 GB（float32），风用 1 个时变量、光伏用 7 个，按时间分块后峰值估 3–4 GiB，低于本机 10 GiB；转换用时估 10–60 min。结论：不超过本机能力，S4A-0 起在后台只读下载（断点续传，完成后校验 MD5 f37ea8b3…），下载期间继续审计。
- **模型容量因子（S3B 冒烟网络，2920 时段加权）：** 陆上风国家均值 BN 0.020、ID 0.052、KH 0.052、LA 0.048、MM 0.048、MY 0.031、PH 0.135、SG 0.046、TH 0.060、TL 0.048、VN 0.090；节点最大 PH 0.254、ID 0.199、VN 0.129；海上风 DC 均值 VN 0.389（最大 0.541）、PH 0.209；光伏 0.127–0.155。
- **存量机组（网络，2050 在役）：** 748 个单元身份（煤/气/褐煤/油 Link、水电/抽蓄 StorageUnit、ROR/地热 Generator）；GEM 在运+在建（2026-09 GIPT）东盟合计：煤 134.0 GW、油气 136.3 GW、水电 63.9 GW、光伏 36.9 GW、风 13.6 GW、生物质 5.8 GW、地热 5.3 GW、核电 0。
- **气田：** GOGET 东盟 250 个单元，41 条天然气产量记录（最新年份），有坐标的在运气田 BN 1、ID 18、MM 1、MY 11、PH 1、TH 6、VN 2；KH/LA/SG 无（与 UNSD 上限 0 一致）。
