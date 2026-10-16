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
| S4B-1 | 存量口径（第 77 项） | 未开始 | | |
| S4B-2 | 地热/新建水电/抽蓄上限，核电敏感性开关（第 78、79 项） | 未开始 | | |
| S4B-3 | 陆上风实际发电校准 + 现代机型；资源分级（第 74、75 项） | 未开始 | | |
| S4B-4 | 台风敏感性开关（第 76 项） | 未开始 | | |
| S4B-5 | 构建与冒烟 | 未开始 | | |
| S4B-6 | 云端资源估算与部署包更新（只准备） | 未开始 | | |
| 交付 | S4B_REPORT.md、S4B_EVIDENCE.json、DOWNLOAD_LIST.csv | 未开始 | | |

## 用户中途指示（2026-10-16，执行中收到）

1. **DEA 版本（第 74 项口径）：** 机型参数只取 technology-data v0.15.0 实际引用的 DEA 版本；若与 2026 年 8 月版不同，主算用引用版、新版只作对照，报告列两版单机容量/转子直径/轮毂高度差异；引用版取不到就停下报告。
   - 核实结果（VERIFIED）：GitHub `PyPSA/technology-data` 标签 v0.15.0 下 `inputs/technology_data_for_el_and_dh.xlsx` 最后修改提交 24da26c58b（2022-03-17，"update offshore assumptions to new DEA release"），之前 bd90c3327a（2022-02-21）；文件 git blob `ce07675ba570a3b6376910505bd2bebcf163c0ba`（707,234 B）与本机 `phase2/research_audit/research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx` 的 `git hash-object` 完全一致（SHA256 3ab3f613…）。表 "20 Onshore turbines" 2050：单机 6 MW、转子 165 m、轮毂 110 m、比功率 280.6 W/m²、平均 CF 0.434；投资 0.963 M€/MW（表头 2015€）。ens.dk 当前页面为 2026 年 8 月版（PDF media/8614，15.6 MB，作对照，后台下载中）。
2. **附加诊断：** 4 个失败的 `test_gate4_activation` 只诊断不修改，写入报告单独一节并列入用户决定事项（S4B-5 之前完成）。

## 续行点

S4B-0 已完成并提交；下一步 S4B-1（存量口径，第 77 项）。下载：Ember 年度 CSV 已取得（16,123,048 B，`sources_s4b/ember/`）；IBTrACS WP/NI 与 DEA 新版 PDF 在后台下载（2026-10-16 17:21 SGT 起，WP 约 50 KB/s）。
