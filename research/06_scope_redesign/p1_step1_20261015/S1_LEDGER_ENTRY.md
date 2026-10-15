## S1 部门耦合骨架、电力与氢 — 2026-10-15

- **范围：** 第一步（S1-1 至 S1-7）在本机完成；S1-8 日分辨率正式求解等待新云端实例（122 已到期，补充指令 02）。所有产物标注 `INTERIM_S1_SKELETON`，只有电力需求，结果无科学含义。分支 `codex/s1-coupling-skeleton-20261015`，基线 345fc30f。
- **适配层：** `scripts_project/sector_adapter.py` 调用上游 `add_hydrogen`（电解、燃料电池、H2 轮机、储氢罐、greenfield 管道），注入值来源逐项登记；不调用 `convert_conventional_generators_to_links`、`average_every_nhours`、`add_co2_budget`、`add_heat`、`add_residential`、`add_services`。母线命名统一为上游 `node carrier`（92 个燃料母线改名）。
- **退役：** 807 固定账户、1,256 计量 Link、`build_research_assets.py:214-250` 删除；`fixed_accounts` 一族与 `check_research_carriers`、`build_diagnostic_network` 移至 `scripts_project/retired/`；15 处守卫逐条写明替代（V5 B1/B5/B11/B12）。
- **存量：** 地热寿命 15→30 年（technology-data costs_2050.csv:1025，B 级）；ID 186 MW 按年龄存续但无性能合同未并入；Bataan 621 MW 按 GEM 原始记录（mothballed、无投运日期）排除；水电分国差异列出未改。
- **候选：** 核电大型堆（除 SG）/SMR（`p_nom_max=0`，DATA_PENDING）、地热/新水电/抽蓄站址候选（DATA_PENDING 共 485）、氢链与电池确认可扩展；成本缩放层全 1.0 时网络哈希一致（文件 + 内容）。
- **碳与情景：** 11 国大气 Store + `research_country_net_zero` 钩子；U4 结构性避免；`research.cross_border.*` 开关；integrated 保留 24 条跨境电力边（2025 下限、不计 CAPEX、FOM 常数 18.97 M EUR/a），disconnected 移除 24 条电力边与 20 条跨境氢管道。
- **构建与冒烟：** 两情景 2920×3h 与 365×24h 网络构建通过静态验证（峰值 RSS 0.50 GiB）；HiGHS 56×3h 冒烟：integrated 可解，V5 A1–A6、B1、B11、B12 通过，B5 通过；disconnected **不可行**，定位为新加坡在每国净零 + 无互联 + 无 SMR 数据 + 无进口下零排放供给仅为需求 5%，未放宽约束，B6 不可评估。
- **待用户决定：** B6 的"拆分存量跨境线路"前提与 PyPSA 0.30.3 `objective_constant` 不符且会改变基尔霍夫分流，本步改为 FOM 常数不拆分；SG 不可行的处理；作者 AEO8 成本覆盖是否沿用；决定 45 输电上限模式。
- **R12A：** D 阶段风电为 0 属经济合理（资源差 + 无碳约束 + 便宜化石/光伏）；作者参考模型风电 9.1 GW；外部容量因子未核实。
- **交付：** `research/06_scope_redesign/p1_step1_20261015/`（S1_REPORT.md、S1_EVIDENCE.json、CLOUD_RESOURCE_ESTIMATE.md、S1_CLOUD_DEPLOYMENT_PLAN.md、R12A、证据 JSON/CSV、测试记录）；云端部署包已打包未上传（`S1_RELEASE.tar.gz` SHA256 `615c9925…`）。
