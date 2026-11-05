# V3.1 燃料舱约束修正与重新打包——进度（第 195 项）

- 指令：`V3_FIX_INSTRUCTION.md` v1，SHA256 `f8ba88a29ff08aa6b11becf432809355d98f8a406f6e482debff482e5fdfa5aa`，与 `V3_FIX_SHA256.txt` 一致（2026-11-05 核对）。
- 开始条件：用户确认 AnyConnect 已断开、本机与 AutoDL 没有其他 Gurobi 进程（本机检查：WSL 与 Windows 都没有 Gurobi / 求解进程，Cisco AnyConnect 网卡 Disabled）。
- worktree `/home/jin/wt_v3_fix`，分支 `codex/v3-fix-20261105`，起点 `7d22dda112a3c18ed57e8c061d95e51915980417`。
- 会话脚本：`work/p1_v3_fix_20261105/scripts/`；会话目录 `/home/jin/v3fix`（演练包、干跑）；窗口构建 `results_project/v3fix`（主检出）。

## 额度记账

| 项 | 已用 / 上限 |
|---|---|
| 本机 Gurobi | 4 / 6（`evidence/GUROBI_CALLS.csv`） |
| 本机计算 | 约 2.0 h / 5 h |
| 磁盘新增 | 约 6.3 GB / 30 GB |

## 步骤

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | 核对 SHA256、开始条件、读文档、建 worktree | 完成 | — |
| 1 | 第 2 节修正与断言；下游用法排查与形状适配；静态零松弛检查与新测试 | 完成 | `ae849e1e` |
| 2 | 运行目录参数化、v3.1 定义、打包脚本、包测试 | 完成 | `64aea2e3` |
| 3 | 全量测试 @64aea2e3（855 / 5；新失败 1 项已修） | 完成 | `13ebce95` |
| 4 | bash 4.2 替身测试 43 项 | 完成 | — |
| 5 | 5.1 窗口复核（2 次）、5.2 回归（2 次，SMOKE_RESULT:PASS） | 完成 | — |
| 6 | 计划第 15 节、v3.1 指南（部署包 COMMIT） | 完成 | `d3b9a3bc` |
| 7 | 正式包、网络核对、干跑 bash 5 / 4.2、静态检查、全量 @d3b9a3bc（856 / 4 基线） | 完成 | — |
| 8 | 报告、证据、台账、镜像提交、推送、扫描、复制、最终行 | 进行中 | |

## 恢复点

收尾：`scripts/commit_mirror.sh scripts/msg_step5.txt research/06_scope_redesign/p1_v3_20261102/hpc_v31/fullsize_presolve.sh` → 推送 → `scripts/scan_fix.sh post` → `V3_HPC_PROGRESS.md` 最后一行（仓库与 work 两份）→ 提交推送 → 复制到 `work/p1_v3_20261102/` → 审阅 ZIP。
