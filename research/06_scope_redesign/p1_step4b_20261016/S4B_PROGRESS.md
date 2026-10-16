# S4B 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4B_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-16 16:45 SGT），开始前核对 SHA256 = `52f1b758e00cfdeb1760c8cd04dbb10d4bfe8bb6bdf8beab3e1da499604dbc51`，与 `S4B_INSTRUCTION_SHA256.txt` 一致（2026-10-16，VERIFIED）。模型 Opus 5.5 xhigh。

分支 `codex/s4b-fixes-calibration-20261016`，自 S4A 最终提交 a58ca3fa 开出（已核实 = PR #25 的 headRefOid `a58ca3fa2c2b76ccc2eff92973832c07a8beada3`）；draft PR 叠在 #25 上（基分支 `codex/s4a-resources-fleet-20261016`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4b_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4b_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）、`formal_barrier` + 缩放（第 69 项）；止损：56×3h 单次 30 分钟、非最优即停不重试（唯一例外：不互联主算的预期不可行，S4B-5 第 2 条）。
资源（第 7 条）：只允许指令点名的三项下载（Ember 年度 CSV、IBTrACS WP/NI CSV、technology-data v0.15.0 onwind 2050 所引 DEA 原文），总量 ≤ 1 GB，放 `sources_s4b/` 并登记 SHA256；其他下载、新增磁盘 > 约 20 GB、本机单次计算 > 1 h 或 > 约 8 GiB、任何云端操作，先报告。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4B-0 | 补做第 70–73 项 + S3B §8 其余事项 + 重算与冒烟 | 完成 | 3afb044d（代码与数据）+ 冒烟证据提交（见下一行） | 第 70 项：`research.sector`（Sabatier 97、电制生物燃料 97、FT 最低负荷 0.5、co2 vent 关），对照表 79 行（一致 56 / 确认偏离 11 / 不适用 9 / 用户决定 3）；第 71 项：`s4b_acceptance.py`（k = 10 × FeasibilityTol/OptimalityTol，净零行用 CO₂ 毛流量、生物质池用容量），S3B/S4A 只读重评；第 72 项：`cap_factor_cost` 7,018 EUR/MW/a；第 73 项：节点气松弛；`asean_own_2019` 表；冒烟：一体化 OPTIMAL 6.6598e11（−6.5% vs S4A；LNG 全部扩到 2.5 倍、气电 1,153 TWh、SMR 1,096 TWh）、不互联主算 NUMERIC（预期）、不互联诊断 OPTIMAL（气缺口 0，CO₂ 缺口 KH 13.4 / LA 7.1 / MM 4.6 / SG 22.7 Mt）；新口径下一体化只剩 3 列 `Line-s` 平稳性残差（5.7e-4）；测试 411 通过 / 4 失败（test_gate4 既有）+ test_s4b_0 6 项 |
| S4B-1 | 存量口径（第 77 项） | 完成 | 31da24c8 | 在建计入（S1 规则只对在建放宽，45 条 S1 记录逐条对照：计入 25 个子单元 1,420 MW）；无投运年在建 74 台 9,314 MW 计入（垃圾 70 MW 跳过，补入 9,244 MW），在运 170 台 5,313 MW 不计；移出 11 台 2,854 MW（`remove_not_operating_gipt2026`）；存量 261,101 → 267,491 MW；两情景构建静态 PASS；test_s4b_1 3 项 |
| S4B-2 | 地热/新建水电/抽蓄上限，核电敏感性开关（第 78、79 项） | 完成 | 2d9e2f09 | 主算上限：新建水电 195.2 GW（水库 161.3 + 径流 33.9）、地热 25.8 GW（含 PH 原址重建 1.8）、抽蓄 14.4 GW；项目库只取宣布 + 预建（在建已入存量，字面口径为开关值，待用户确认）；入流按建成容量约束（新钩子）；改正 S1 候选缺陷（抽蓄往返 0.5625、水库可抽水、径流/地热可用率 1.0）；核电 `national_plans` 开关只实现；五个构建静态 PASS；发现风光候选成本沿用电力底座、未用第 50 项成本层（待用户决定） |
| S4B-3 | 陆上风实际发电校准 + 现代机型；资源分级（第 74、75 项） | 完成 | 5ed1da4a | 实测 CF（Ember 2023–2024）PH 0.332、TH 0.260、VN 0.241，ID 不足 200 MW 不校准；α（NREL ATB 2020 4 MW，S4A 布置与 cutout）PH 0.910、TH 1.294、VN 0.995，其余国家取三国容量加权 1.046；主算机型 DEA 2050（6 MW / 165 m / 110 m，引用版）；变体 `calibrated_modern`，3 级资源分级；最优级 CF 均未超过预先写定阈值；GWA 缩放作对照（会超过 PH/VN/TL 阈值，不采用）；test_s4b_3 5 项 |
| S4B-4 | 台风敏感性开关（第 76 项） | 完成 | 1c48eb04 | IBTrACS WP+NI 1980–2024，≥ 50 m/s、100 km，357 个风暴，最大 8.2 次/10 年；默认阈值 1 次/10 年时受影响节点：陆风/海上 AC PH5 0、PH_Luzon5 0、PH_Visayas7 0，海上 DC PH5 0、VN2 7；开关 `typhoon_premium: off`（主算）/ `on` × 1.25 只实现，构建核对 17 台发电机；raw12 船舶密度 SHA256 核对一致（未解压）；本机保护区 = natura.tiff（WDPA 衍生，CC0），完整 WDPA 未下载（> 2 GB，待用户决定）；test_s4b_4 3 项 |
| S4B-5 | 构建与冒烟 | 完成 | 7141868d（准备：诊断网络也写日网络、汇总脚本）+ 结果提交（见下一行） | 四个构建静态 PASS（各约 1 min 20 s、0.66 GiB，含 365×24h 日网络）；一体化主算 OPTIMAL 5.9438e11（120 次 / 214 s，墙钟 300 s，3.61 GiB）；不互联主算 NUMERIC（预期）；不互联诊断 OPTIMAL（CO₂ 缺口 KH 13.42 / LA 7.10 / MM 4.64 / SG 22.66 Mt，电、生物质、气 0）；一体化诊断（可选）SUBOPTIMAL，只记录；一体化门槛新旧口径均未通过（数值残差：barrier 精度低于 S4B-0，KKT 诊断已归类）；SMR 241.5 → 96.6 GW；ID 新建水电 77.2 GW（入流代理偏高，待用户决定）；测试 430 通过 / 4 失败（test_gate4 既有）|
| S4B-5 结果 | 证据与报告 §5 | 完成 | f3ff1e9a | 见上一行 |
| S4B-6 | 云端资源估算与部署包更新（只准备） | 完成 | c02ce694（脚本与估算）、949163f3（运行目录名修正；部署包代码快照） | 估算 §11：每运行 21 GiB（上限 30），串行 2.3–3.3 h、并行 1.7–2.6 h；部署包 `work/p1_step4b_20261016/cloud_package_dist/`（13 个文件 + 清单，193,276,010 B）；本机预检（资源项按预期失败）与空跑通过；修正 S3 版导出 `solve.log` 含许可横幅的问题 |
| 交付 | S4B_REPORT.md、S4B_EVIDENCE.json、DOWNLOAD_LIST.csv、台账条目、审阅 ZIP | 完成 | 交付提交（见 PR #26） | 摘要、第 70–81 项索引、§8 用户决定 14 项；未连接云端 |

## 用户中途指示（2026-10-16，执行中收到）

1. **DEA 版本（第 74 项口径）：** 机型参数只取 technology-data v0.15.0 实际引用的 DEA 版本；若与 2026 年 8 月版不同，主算用引用版、新版只作对照，报告列两版单机容量/转子直径/轮毂高度差异；引用版取不到就停下报告。
   - 核实结果（VERIFIED）：GitHub `PyPSA/technology-data` 标签 v0.15.0 下 `inputs/technology_data_for_el_and_dh.xlsx` 最后修改提交 24da26c58b（2022-03-17，"update offshore assumptions to new DEA release"），之前 bd90c3327a（2022-02-21）；文件 git blob `ce07675ba570a3b6376910505bd2bebcf163c0ba`（707,234 B）与本机 `phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx` 的 `git hash-object` 完全一致（SHA256 3ab3f613…）。表 "20 Onshore turbines" 2050：单机 6 MW、转子 165 m、轮毂 110 m、比功率 280.6 W/m²、平均 CF 0.434；投资 0.963 M€/MW（表头 2015€）。ens.dk 当前页面为 2026 年 8 月版（PDF media/8614，15,584,745 B，SHA256 de99f7a0…，作对照）：第 20 章修订记录为 2019 年 5 月与 2023 年 11 月（"财务与技术数据更新"），PDF 内无数据表；图 24（第 122–123 页）给出 2050 年满负荷小时 3,800、比功率 ≈ 280.6 W/m²、轮毂 110 m——与引用版完全相同；单机容量与转子直径不在 PDF 中（在未授权下载的 2026 xlsx 中），无法对比。主算用引用版参数。
2. **附加诊断：** 4 个失败的 `test_gate4_activation` 只诊断不修改，写入报告单独一节并列入用户决定事项（S4B-5 之前完成）。

## S4B-3 预先写定的停止判据（2026-10-16，在计算校准后节点/分级 CF 之前写入）

"明显超过"定义为：某国校准后陆上风最优级（3 级中的第 3 级）CF > 1.10 × max（GWA 3.3 IEC2 陆地 p90，IRENA RPGC 2024 新建项目读数上沿）；IRENA 读数取 ID 0.38、PH 0.35、VN 0.43（图 2.12），其余国家取 Other Asia 加权平均 0.39（表 2.3）。即阈值 ID 0.418、PH 0.503、VN 0.528、TH/MY/LA/KH/MM/BN/TL/SG 0.429。任一国超过即停下报告，不采用。α 判据：所用 α（校准机型）∉ [0.8, 1.6] 即停。

## 续行点

S4B-0 至 S4B-6 与交付全部完成（2026-10-16 约 19:45 SGT）。按指令停止，等待审阅；未连接云端，未做 365×24h 或 2920×3h 求解。下载三项均已取得并登记（`sources_s4b/SOURCES_S4B.csv`，合计 174.2 MB）。
