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
| H4 本机演练（2 次 Gurobi） | 完成 | `be5e49fd`（演练提交）；记录在本提交 | `/home/jin/hpr/h4_drill.sh`：生成的 `pbs/hpr_smoke56.pbs` 作为 bash 执行（模拟 `PBS_O_WORKDIR` / `PBS_JOBID=local.h4drill` / `NCPUS=17`），包副本 `/home/jin/hpr_drill/pkg`，运行目录 `results_project/hpr/h4/runs/smoke56`：F1 06:35:07Z–06:38:38Z optimal 113 次、目标 340661983874.5359；F2 06:47:53Z–06:51:29Z optimal 139 次、352091303417.9458（间隔 555 s）；均 ACCEPTED_LAYER2；后处理与批级 exit 0；B6 11.4293 bn；与 DFX F5.5 冒烟逐位相同（目标值、Gurobi 目标、迭代、X / Pi / RC、lp 数组、全部导出；`OWEN.json` 只差路径 / 标签，求解网络只差 meta 的授权文本）。**本机 Gurobi 调用 2 / 2 已用完** |
| H5 包 v9 + 操作手册 + 干跑 | 完成（包重建于 `69b0b7d1`） | `86af83f3`（首次构建，保留为 `hpc_package_superseded_86af83f3`）、`69b0b7d1` | `work/p1_hpr_20261027/hpc_package/`（36 文件；`SHA256SUMS` 全部 OK）；`HPC_OPERATOR_GUIDE.md`；干跑 `results_project/hpr/dry_run_v9/`（预检 7 节 OK、resources 本机失败属预期、licence 节未跑；截短 56 BUILD_ONLY 经作业脚本 exit 0；20 个拒绝用例全部 exit ≠ 0 且未写 STATUS）；`hpr_consistency.py` ALL_CONSISTENT；泄露扫描：许可值 / ssh / host 0，版本号误报 10 处（环境锁定文件）、历史提交键名字面量 1 处（R1 口径） |
| H6 检查单 | 进行中 | | `PRE_HPC_CHECKLIST.md`：H-P1–H-P12 PASS（H-P8 有保留 R1；R2–R4 保留项）；H-P13 等第二轮复核；H-P14 等最终推送 |
| H7 独立审查 | 第一轮完成，修正中 | （本提交） | 第一轮：阻断 0 / 非阻断 18（`INDEPENDENT_REVIEW.md` 第 2 节原文）；逐条处理见第 3 节：代码 / 脚本修正 F-04、F-06、F-07、F-11、F-13、F-14、F-15、F-17（含 2 个新替身测试），手册 / 计划修正 F-01、F-02、F-03、F-05、F-08、F-09、F-10、F-12、F-16、F-18；待用户确认 F-09（回执中的本机用户名路径，检查单 R4）、待 HPC 核实 F-08 / F-14 / F-05(b)。修正后：替身测试重跑、包 v9 重建、干跑 / 一致性 / 扫描 / 全量测试重做，再请同一子代理复核（第二轮） |
| 报告 + 证据 + 推送 | 待做 | | |

续跑说明：如本会话中断，从上表第一个"待做"步骤继续；已提交的内容以 git 历史为准；`results_project/hpr/*/STATUS.txt` 记录各运行的进度。
