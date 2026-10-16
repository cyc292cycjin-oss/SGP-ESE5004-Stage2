# S4B 进度记录（防中断用；每个子步骤提交后更新）

指令 `S4B_CLAUDE_CODE_INSTRUCTION.md`（v1，2026-10-16 16:45 SGT），开始前核对 SHA256 = `52f1b758e00cfdeb1760c8cd04dbb10d4bfe8bb6bdf8beab3e1da499604dbc51`，与 `S4B_INSTRUCTION_SHA256.txt` 一致（2026-10-16，VERIFIED）。模型 Opus 5.5 xhigh。

分支 `codex/s4b-fixes-calibration-20261016`，自 S4A 最终提交 a58ca3fa 开出（已核实 = PR #25 的 headRefOid `a58ca3fa2c2b76ccc2eff92973832c07a8beada3`）；draft PR 叠在 #25 上（基分支 `codex/s4a-resources-fleet-20261016`）。
仓库 `cyc292cycjin-oss/SGP-ESE5004-Stage2`；WSL 路径 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model`；交付目录 `research/06_scope_redesign/p1_step4b_20261016/`，镜像 `D:\ResearchWorkspaces\ASEAN\work\p1_step4b_20261016\`。
求解环境：`/home/jin/miniforge3/envs/pypsa-earth/bin/python`，`PYTHONHASHSEED=0`，Gurobi 12.0.3（`GRB_LICENSE_FILE=/home/jin/gurobi.lic` 只读引用）、`formal_barrier` + 缩放（第 69 项）；止损：56×3h 单次 30 分钟、非最优即停不重试（唯一例外：不互联主算的预期不可行，S4B-5 第 2 条）。
资源（第 7 条）：只允许指令点名的三项下载（Ember 年度 CSV、IBTrACS WP/NI CSV、technology-data v0.15.0 onwind 2050 所引 DEA 原文），总量 ≤ 1 GB，放 `sources_s4b/` 并登记 SHA256；其他下载、新增磁盘 > 约 20 GB、本机单次计算 > 1 h 或 > 约 8 GiB、任何云端操作，先报告。

## 子步骤状态

| 节 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4B-0 | 补做第 70–73 项 + S3B §8 其余事项 + 重算与冒烟 | 进行中 | | |
| S4B-1 | 存量口径（第 77 项） | 未开始 | | |
| S4B-2 | 地热/新建水电/抽蓄上限，核电敏感性开关（第 78、79 项） | 未开始 | | |
| S4B-3 | 陆上风实际发电校准 + 现代机型；资源分级（第 74、75 项） | 未开始 | | |
| S4B-4 | 台风敏感性开关（第 76 项） | 未开始 | | |
| S4B-5 | 构建与冒烟 | 未开始 | | |
| S4B-6 | 云端资源估算与部署包更新（只准备） | 未开始 | | |
| 交付 | S4B_REPORT.md、S4B_EVIDENCE.json、DOWNLOAD_LIST.csv | 未开始 | | |

## 续行点

从 S4B-0 开始（尚无提交）。
