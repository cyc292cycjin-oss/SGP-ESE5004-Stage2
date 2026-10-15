## S2B 修正轮（补充指令 02，第 55–60 项）— 2026-10-15

- **范围：** 在 S2 分支上追加 R3 → R1 → R2 → R5 → R6 → R4 → R7 → 构建与冒烟，每节一个提交（bd6debcd、cff39662、ab85b7ce、09a517c7、182bce70、d337d986、47ce2e15 + 构建/报告两个提交）；draft PR #23 同步更新。无正式求解。
- **R3（57）：** 分国分配改用 AEO8 C.8 人均终端能源 × D.1 人口的相对因子 r_c（Σ人均×人口 431.96 / 746.07 Mtoe vs 432.2 / 746.2）；TH 2,325 → 3,399 TWh，PH 1,447 → 999，VN 2,900 → 2,559；GDP/人口分配为敏感性表；`research.demand.country_allocation`。
- **R1（55）：** `s2b_industry.py`：钢铁（worldsteel 2019 + PyPSA-Eur 0.3/1.0 + H₂ 1.7、电 0.322 + technology-data 电炉 0.6395）、水泥（EDGAR 2.A.1/0.52 熟料 + technology-data 窑炉/粉磨比率，窑炉燃料→甲烷）；其余子部门 2019 载体份额 × 乘数，PyPSA-Eur 比率待 JRC-IDEES-2021（DATA_PENDING，已入下载清单）；低温热行 0；生物质超潜力→甲烷（VN 23.6、SG 0.14 TWh）；工业氢 73.7 TWh；工业电力显式并从 Astar 扣除；VN 工业煤 995 → 513 TWh。
- **R2（56）：** `s2b_feedstock.py`：EDGAR 2.B+2.D × 乘数入过程母线；废塑料焚烧（What a Waste 3.0 × IPCC 表 2.4）入大气；出口/填埋不计；属地 vs 全量释放（Mt/a）：ID 73.8 vs 63.8、TH 39.8 vs 104.6、MY 23.4 vs 79.2、SG 21.5 vs 16.0；LA 塑料份额、KH/TH/VN 露天焚烧份额 DATA_PENDING。
- **R5（59）：** 氢/CO₂ 候选 = 电力拓扑（PyPSA-Eur create_network_topology）：109 条、跨境 19 对（与 S2 相同节点对；氢 20 → 19，去掉 via HVDC 重复；MY–TH 长度 132.6 → 275.4 km）；MM 无跨境电力走廊 → 数据缺口。
- **R6（60）：** DAC 热 1.4 MWh_th/t 取自节点工业低温热母线（technology-data 第 938–942 行，PyPSA-Eur add_dac 组合）；电 0.55 MWh/t；electric_cop1 为敏感性。
- **R4（58）：** 截断运行权重 8760/N、年度上限不缩放，B12 登记权重与哈希。**R7：** B11 只判有负荷母线（辅助母线单列）；A3/A5 把松弛×罚款计入已知项。
- **构建与冒烟：** 两情景构建通过（RSS 0.58 GiB）；冒烟两情景不可行（MM 过程 + 塑料无去向；不互联 KH/LA/SG/VN）；gap_diagnostic（全年口径）最优：一体化只剩 MM 5.13 Mt/a，不互联 VN 234.5 / KH 16.5 / SG 12.8 / LA 8.6 / MM 5.1 Mt/a，电力与生物质缺口 0；MM 的化石终端能源由 FT（生物质 CC 碳 + 电解氢）与 BtL 替代；结构上界（化石供给不变）与诊断缺口的差额即合成燃料碳循环。门槛 A1–A6、B2、B3、B8、B12 通过，B11 细化后通过；B1/B5/B6 不可评估。测试 371 通过 / 4 基线失败。
- **待用户决定：** JRC-IDEES-2021 下载授权；钢铁/水泥替代比率是否接受；MM 跨境走廊（TH–MM/LA–MM）；R2 数据缺口代理；KH 交通链；子部门拆分缺口；full_release 敏感性是否正式运行。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（S2B_REPORT.md、S2_EVIDENCE.json v2、S2B_TEST_RUN.json、CLOUD_RESOURCE_ESTIMATE.md §7、evidence/s2b/、S2_PROGRESS.md）；镜像 `work/p1_step2_20261015/`。
