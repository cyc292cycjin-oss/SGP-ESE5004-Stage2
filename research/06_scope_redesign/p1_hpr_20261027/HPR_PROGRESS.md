# HPR 进度（续跑点）

指令：`HPR_CLAUDE_CODE_INSTRUCTION.md`，SHA256 `f14cb0183058e8a44920eb6e887bb528af35fc38861303af1118e17984412d86`（核对一致，2026-10-27 12:50 SGT）。用户补充（2026-10-27）：步骤 D2 全尺寸 BUILD_ONLY 测试作业。
分支 `codex/hpr-20261027`（从 `codex/dfx-v3-20261026` 头 `82c32c53`），worktree `/home/jin/wt_hpr_20261027`，中间结果 `results_project/hpr/`（主检出），交付目录 `research/06_scope_redesign/p1_hpr_20261027/`（镜像到 `work/p1_hpr_20261027/`），辅助脚本 `/home/jin/hpr/`（镜像 `scripts/wsl_hpr/`）。
本机 Gurobi 调用：0 / 2。本机计算用时与磁盘见各步。

| 步骤 | 状态 | 提交 | 说明 |
|---|---|---|---|
| 0 核对指令 SHA、读入材料、建分支 | 完成 | — | worktree 建于 `82c32c53`；被忽略的 `research_inputs/finance_v5/*.csv` 从 DFX worktree 复制；`results_project/assembly_v1` 链接到主检出 |
| H1 现状复核 | 完成（表在报告中） | （本提交） | 两个 v2 2920×3h 网络 SHA256 / 字节 = B2；构建提交 `72083fde`；`run_batch4.sh` / `b4_batch4.py` / `RUN_PLAN_B4.md` 登记值逐项分类；阶段 2 草稿与 B1–B4 的不一致清单 |
| H2 RUN_PLAN_HPC.md | 完成 | （本提交） | 在任何 HPC 操作与 H4 求解之前提交 |
| H3 实现 + 替身测试 | 完成 | （本提交） | `run_batch4.sh --only` / `WAIT_START_OF` / `MEM_MEASURE` / cgroup 作业目录布局 / R_TL 864,000；`b4_batch4.py` B1–B2 登记值、`HPC_JOBS`、`hpc-plan`、参照对比；`preflight.sh` / `preflight_dfx.sh` CGROUP_ROOT 误报修正；`hpc_package_src/`（`make_pbs.sh`、`hpr_job.sh`、安装 / 登录预检 / 提交 / 状态 / 一致性 / 参照值）；`HPC_OPERATOR_GUIDE.md`；`evidence/H1_REVIEW.md`；`tests/research/test_hpr_two_jobs.py` 15 项 + B4P 10 项 + DFX / 第三批替身测试同进程 85 项通过（首轮 6 败已修：作业体 RUN_DIR 自赋值早于钩子检查、cgroup 作业目录须含作业号、mawk 双文件、一致性数值比较、测试编排 2 处） |
| H4 本机演练（2 次 Gurobi） | 待做 | | |
| H5 包 v9 + 操作手册 + 干跑 | 待做 | | |
| H6 检查单 | 待做 | | |
| H7 独立审查 | 待做 | | |
| 报告 + 证据 + 推送 | 待做 | | |

续跑说明：如本会话中断，从上表第一个"待做"步骤继续；已提交的内容以 git 历史为准；`results_project/hpr/*/STATUS.txt` 记录各运行的进度。
