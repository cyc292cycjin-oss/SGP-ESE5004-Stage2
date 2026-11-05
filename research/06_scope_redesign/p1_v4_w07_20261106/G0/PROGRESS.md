# V4 W07 G0（印尼定稿）进度

- 指令：`work/p1_v4_w07_20261106/V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`，与 `V4_W07_SHA256.txt` 一致（2026-11-06 核对）。本会话只执行 B-G0 节。
- 分支 `codex/v4-w07-g0-20261106`，自 `codex/v4-data-20261105` 头 `07e08f38` 新开；worktree `/home/jin/wt_v4_g0`；仓库外临时副本 `/home/jin/v4w07_g0/chain`。交付目录 `work/p1_v4_w07_20261106/G0/` = 仓库 `research/06_scope_redesign/p1_v4_w07_20261106/G0/`（不含 `extracted/`）。
- 只读：S0/S1/S2 交付（本分支 07e08f38 中的 `research/06_scope_redesign/p1_v4_data_20261105/`）、W11 交付（`work/p1_v4_ncv_20261106/`，分支 `codex/v4-ncv-20261106` a3ad32b5）、`downloads/`（含 `17_nickel_literature/` Wei 2020 原文）。
- 额度：求解器 0 次；本机计算上限 2 小时；磁盘新增上限 3 GB；不下载新数据（不需要 SDMX 查询）。

| 子步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| G0-0 | SHA256 核对；分支与 worktree；临时副本；未改动副本逐位复现仓库 ID 行（s3_0 四个输出逐字节相同，`T_v2` 与 v3"其他"偏差 0 MWh；补丁无环境变量逐字节相同；口径 II 路径 m08b + s3_0 逐字节相同） | 完成 | 随 G0-A |
| G0-A | 第 1、2、4 项：合并重算（热值 20.29 → 自备煤 (b) 中心值 → 镍 2023 基年 → 镍单耗按产品 → 水泥 (ii) → 钢只换空间 → 纸浆造纸闭环 → 乙烯含 LINE → 燃料木材 2010–2017 年均），4 种热值 × 2 种镍口径的逐步表、敏感性、口径 II 对照；对 S2、W11 的 5 项交叉验证；Wei 2020 原文核对与镍单耗（`ID_NICKEL_*`）；第 3 项生物质潜力核查（`ID_BIOMASS_POTENTIAL_CHECK.csv`） | 完成 | `7dda29ee` |
| G0-B | A6 统一输出表：`ID_SUBSECTORS_V4.csv`、`ID_CAPTIVE.csv`、`ID_BIOMASS_CHECK.csv`、`ID_NCV.csv`、`ID_NODE_SHARES.csv`、`ID_MISSING_DATA.csv`（`scripts/v4g0_tables.py`；自备电厂 4 种热值 × 4 档链运行） | 完成 | 见下 |
| G0-C | `REPORT.md`、`ID_DECISIONS.md`、`EVIDENCE.json`、台账条目草稿（不改共享台账）、审阅包 | 待做 | |

续做起点：G0-C（报告、待决问题、证据合并、审阅包）。
