# V3 全年 2920×3h 不可解诊断指令（决策清单第 194 项；审阅端撰写，2026-11-05 15:40 SGT）

**版本：** v1。开始前核对本文件 SHA256，与同目录 `V3_DIAG_SHA256.txt` 一致才执行。**所有过程说明、进度汇报和思考要点一律用中文输出。**

**执行方：** 新开 Claude Code 会话，模型 Opus 5.5，effort Xhigh。**开始条件：** 先问用户一次——AnyConnect 已断开、本机与 AutoDL 没有其他 Gurobi 进程；用户确认后开始。

## 0. 事实（11-05 HPC 正式批次）

- F1（`networks/integrated_2920_3h_unsolved.nc`）与 F2（`no_new_xb_2920_3h_unsolved.nc`）在 Atlas 上构建正常（约 50 分钟），Gurobi 预处理 233 s / 258 s 后返回 **INF_OR_UNBD，0 次 barrier 迭代**（"Presolve removed 56100896 rows and 11904979 columns … Model is infeasible or unbounded"）。运行器按 RUN_PLAN_B4 3.5 记为不可用并停批；F3、F4 未启动。资源、许可、运行器均正常（峰值 107.7 GB / 申请 300 GB）。
- 同一份网络用运行器的 `TRUNCATE=56` 截短后，本机与 HPC 冒烟都 optimal；365×24h 日分辨率筛查也 optimal。
- 审阅端已做的静态检查（不必重复，可引用）：发电机与链路每时段 p_min_pu ≤ p_max_pu；EV 电池 e_min_pu（≤ 0.8）在充电能力下全年可满足；时变数组无 NaN / inf；**不含项目自定义约束**的基础网络前两天窗口用 HiGHS 可解。由此推断：问题多半在项目自定义约束（`required_constraint_hooks` 安装的约束），或它们与全年某些时段的组合。这是推断，以你的证据为准。

## 1. 冻结点与工作方式

1. 代码：提交 `7d22dda112a3c18ed57e8c061d95e51915980417`（部署包 `hpc_package_v3/COMMIT`）。从该提交开新 worktree `/home/jin/wt_v3_diag`、新分支 `codex/v3-diag-20261105`。不进入、不改动其他 worktree。
2. 网络：直接读 `work/p1_v3_20261102/hpc_package_v3/networks/` 下的文件，先按 `pbs/HPC_PLAN.txt` 的 NETWORK 行核对 SHA256。**不重建网络，不改模型代码、配置、输入、注册表、求解档案、验收阈值或已登记预测。**
3. 诊断脚本只放在 `work/p1_v3_diag_20261105/scripts/`。建模必须走运行器正式路径所用的同一套函数（含全部 `required_constraint_hooks`），不得自己另写约束；先读 `run_batch4.sh` 与它调用的 Python，写明你复用了哪个入口。
4. 本次 Gurobi：串行，同一时刻只有 1 个 Gurobi 进程，每次结束后释放环境；许可已扩到 10 个会话（第 192 项），不需要 330 s 间隔。不读、不打印、不复制许可文件。

## 2. 步骤

1. **对照组：** 用运行器 `TRUNCATE=56` 的同一截短方式复现 F1 前 56 时段，只做到预处理（`Method=2, Crossover=0, BarIterLimit=0`，其余同 `formal_barrier_1e6_t16`），应得到 ITERATION_LIMIT 而不是 INF_OR_UNBD。复现不了就停下报告。
2. **按月切窗口（F1）：** 12 个窗口，每个 240 个时段（12 月 248 个），时段权重的处理与 `TRUNCATE` 完全相同（读代码确认并写明）。每个窗口只跑到预处理，记录状态、预处理耗时、内存峰值。
3. **缩小：** 对返回 INF_OR_UNBD 的窗口，先用 `DualReductions=0` 区分 INFEASIBLE 与 UNBOUNDED；再二分到能复现问题的最小窗口（周 → 天）。INFEASIBLE：用 linopy 的 `compute_infeasibilities()` / `print_infeasibilities()`（Gurobi IIS）列出冲突约束，映射回 PyPSA 组件、自定义约束名、节点、国家、时段与数值。UNBOUNDED：找出无界方向涉及的变量与它们的成本系数。
4. **12 个月全部可解时：** 问题在全年累计约束。按本机内存，从季度 → 半年逐步加长窗口；同时列出所有以全年求和、最后时段取值或年度上限形式写的约束（CO₂ 上限、封存上限、燃料舱、年度进口、生物质等），对比全年口径与截短口径的右端项。本机内存不够全年构建（约 110 GB + Gurobi 60 GB）时，停下报告，写出建议的 HPC 诊断作业（不提交）。
5. **F2：** 找到原因后，在 F2 同一窗口复现，确认是同一原因；再从网络数据判断 F3、F4 是否同样受影响（不必求解）。
6. **为什么 56 时段与日分辨率没暴露：** 用证据说明。
7. **修正方案（PROPOSED，不执行）：** 最小修正，写明改哪个文件哪一处、对其他时段与其他国家的影响，特别是**会不会让成本偏向或偏离某些国家**（研究问题是分国成本分摊）；以及对 365×24h 筛查结果是否需要重跑的判断。
8. **全尺寸预处理闸门（PROPOSED）：** 为以后的部署包设计一个"构建 + Gurobi 预处理后即停"的作业或本机步骤，写明资源与时长估计。

## 3. 产出

`work/p1_v3_diag_20261105/V3_DIAG_REPORT.md`（证据放 `evidence/`）：一句话根因；INFEASIBLE / UNBOUNDED；冲突约束清单（表）；涉及的组件、国家、时段；第 2 节第 5–8 步的结论；本次 Gurobi 次数与用时。提交、推送新分支，然后停止，等审阅端与 Fable 审查（第 194 项）。

## 4. 额度与停止条件

Gurobi 最多 40 次（全部只到预处理或 IIS，IIS 单次 ≤ 30 分钟）；HiGHS 不用；本机计算上限 6 小时；磁盘新增上限 30 GB；不连 HPC、不连云、不连 VPN。停止条件：本文件 SHA256 不符；对照组复现不了；需要改模型代码、网络、成本、求解档案、阈值或预测才能继续；需要超出本机内存的全年运行；可能泄露许可内容或登录信息；额度用尽。停下时在报告中写明原因和已完成的部分。
