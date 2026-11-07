# D2a 进度（V4_D2A_INSTRUCTION.md v1，SHA256 4920db63…38fa 已核对，与 V4_D2A_SHA256.txt 一致；开工 2026-11-07 14:45 SGT）

- 分支 `codex/v4-d2a-20261107`，起点 `4026c1c84d8d349e9bb8c11f3e6da8f82588d621` = `codex/v4-d1-20261107` 头（fetch 核过，本地 = 远端）；`6142d8ac`（D1 审阅包）是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_d1_20261107/` 下 3 个文件（PROGRESS.md、evidence/REVIEW_ZIP_MANIFEST_6142d8ac.txt、scripts/leak_scan.sh），交付目录之外 0 个。
- worktree `/home/jin/wt_v4_d2a`；临时目录 `/home/jin/v4d2a`；主检出 `results_project/v4d2a/`（构建与冒烟输出，不入库）。
- 交付目录 `work/p1_v4_d2a_20261107/` = 仓库 `research/06_scope_redesign/p1_v4_d2a_20261107/`（zip 不入库）。
- 求解额度：至多 6 次（第 6 节 2 次、第 7 节至多 4 次）；已用 0 次。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| D2a-1 | 第 1 节：分支、worktree、祖先核实 | 完成 | （随 D2a-2 提交） |
| D2a-2 | 第 2 节：Fable 修复 F-01 / F-02 / F-05 / F-06 / F-07，F-03 / F-04 口径说明，S4 顺手修复 | 进行中 | |
| D2a-3 | 第 3 节：甲醇 / 氢、EFB 热值基准（T04）、抽蓄存量对账、抽蓄敏感性开关 | 待做 | |
| D2a-4 | 第 4 节：重排修正（封存对偶、S-B 船运、偏向列、v31 参照）与 W19 候选表 | 待做 | |
| D2a-5 | 第 5 节：重建 56 时段网络、静态检查、检查点 | 待做 | |
| D2a-6 | 第 6 节：求解前登记报警线、2 次冒烟 | 待做 | |
| D2a-7 | 第 7 节：成本上升归因（至多 4 次求解） | 待做 | |
| D2a-8 | 第 8 节：报告、证据、审阅包、推送 | 待做 | |

续做点：D2a-2 开始（代码阅读完成，先改 v4_common / v4_industry / v4_industry_cache / v4_outputs）。
