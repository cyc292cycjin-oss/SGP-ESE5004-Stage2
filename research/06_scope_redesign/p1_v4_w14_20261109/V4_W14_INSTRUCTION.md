# v4 W14：打包 v4 主算一对（F1 一体化、F2 no_new_xb）并准备 HPC 提交（台账 W14；决策清单第 213、215、216、221、222、223 项；审阅端撰写，2026-11-09 00:30 SGT；v2 改于 02:30）

**版本：** v2（相对 v1 只改基线分支：由 D2b 改为 D2c，冒烟期望值相应取 D2c）。开始前核对本文件 SHA256，与同目录 `V4_W14_SHA256.txt` 一致才执行。**所有过程说明、进度汇报和思考要点一律用中文输出。**

**执行方：** 新开 Claude Code 会话，**模型 Opus 5.5**，effort Xhigh；开工先确认会话模型，不是则停下告诉用户。**只在审阅端通过 D2c 之后启动。**
**性质：** 构建、打包与本机演练。不连 HPC（上传、预检、提交都由用户操作）；不改模型代码、输入、配置与注册表（只新增打包与运行计划文件，以及 v4 包专用的 HPC 脚本）；本机至多 2 次 56 时段求解（第 3 节演练；用户启动本指令即授权）。**不跳过 git hooks（不用 `--no-verify`，不用 `-c core.hooksPath=…`），不合并 main，不 force-push。** 许可文件只按 `GRB_LICENSE_FILE` 读取，不复制、不打印、不入包。

**先读：** `work/p1_v3_20261102/hpc_package_v3_1/` 的 `HPC_OPERATOR_GUIDE_V3.md`、`RUN_PLAN_HPC_V3.md`、`BATCH_DEF.json`、`pack_results.sh`、`preflight.sh`；`work/p1_v4_d1_20261107/` 的 `hpc_v4/`、`batch_def/BATCH_DEF_2920x3h_v4hpc.json`；`work/p1_v31_w15_20261106/HPC_RUNTIME_FACTS.md`、`BASELINE_V31.md` 第 0 节；`work/p1_v4_d2b_20261108/REPORT.md`；`work/p1_v4_d2c_20261109/REPORT.md` 与 `SMOKE56_D2C.md`；本文件第 0 节。

## 0. 已确认的决策（审阅端摘录）

- **第 222 项（待用户勾选，按其执行）：** 今晚只提交 v4 主算一对（F1 一体化、F2 `no_new_xb`）加批级后处理，作为数据重构后的主结果；敏感性在 W19 登记后另批提交（与师哥 11-10 面谈后定）。登记值：求解档案 `formal_barrier_1e6_t16`（与 v3.1 相同）；TimeLimit 259,200 s（72 h）；早期测速止损 0.8 × TimeLimit，参考迭代一体化 350、`no_new_xb` 300；进程 1 构建超时 7,200 s；walltime 96 h；资源 F1 48 核 / 300 GB、F2 48 核 / 250 GB、批级 12 核 / 120 GB（与 v3.1 相同，不在今晚改核数）；HPC 目录 `/hpctmp/$USER/hpr4`，运行目录 `runs/batch6`、`runs/smoke56_v4`；正式提交前 HPC 冒烟必须 PASS。
- **第 213、216 项：** 不做 AutoDL 筛查与只预处理作业。**第 214 项第⑤条：** 凸性上下界是报警线。**第 215 项第①、②条：** 状态脚本同时显示两种目标值口径；运行器写入包的 `COMMIT`。
- **登记先于结果：** 运行计划、时限、验收与预测都在任何 HPC 提交之前提交入库；非 optimal 不重试、不改参数。

## 1. 分支

从 `codex/v4-d2c-20261109` 当前头提交新开 `codex/v4-w14-20261109`，worktree `/home/jin/wt_v4_w14`。从 D2c 的 `PROGRESS.md` 或审阅包文件名读出 D2c 审阅包对应的提交，核实它是头提交的祖先、二者之间只改了 D2c 交付目录，否则停下。包的代码提交（`COMMIT`）= 本分支上打包前最后一次提交。

## 2. 网络

1. 在包的代码提交上构建 v4 主算一体化与 `no_new_xb` 的 **2920×3h** 网络（v4 主开关集；网络元数据记录开关集 SHA256 与表目录），以及同一规则截取的 56 时段网络。2920×3h 只构建网络，不在本机构建 LP。
2. 全部静态检查（W08、D1、D2a、D2b、D2c 各步的检查，含零松弛门与"无新的零余量行"）在 2920×3h 与 56 时段网络上都通过。
3. 核对 56 时段网络与 D2c 冒烟网络是否相同（SHA256 或逐组件）。相同则 HPC 冒烟期望值取 D2c 冒烟的目标值；不同则说明原因，并在第 3 节演练中求解得到期望值。

## 3. 打包与本机演练

1. 以 v3.1 包为模板生成 `hpc_package_v4`：代码包（`code_<提交>.tar.gz`）、`COMMIT`、两张 2920×3h 网络与构建回执、`BATCH_DEF.json`（由 D1 草案更新：只含 F1、F2、批级 `afterany:F1:F2`、`smoke56`、`install`、`build_only_f1`；登记值见第 0 节；`limits_status: REGISTERED`）、`pbs/`、`hpc/`（D1 的 `hpc_v4/` 脚本，作业名 `hpr4_*`）、`env/`（与 v3.1 同一锁文件，预检一致即复用 HPC 上已装环境）、`preflight.sh`（含 D1 的开关集与网络元数据一致性检查）、`pack_results.sh`、`SHA256SUMS`、`HPC_PACKAGE_MANIFEST.json`。许可类字符串扫描（`pack_results.sh` 同一正则）对整个包为 0。
2. **本机演练**：在包的解压副本中运行提交脚本的 dry-run（必须以 `DRY_RUN_OK` 结束，依赖顺序 F1 → F2（`after:F1`）→ 批级（`afterany:F1:F2`））与冒烟作业体（`TRUNCATE=56`，F1 → F2 → 批级；这是授权的 2 次求解，若第 2 节已确认与 D2c 冒烟网络相同，可只跑预检与 dry-run 而不求解，并说明）。演练结果：SMOKE PASS、目标值与期望值相对差 ≤ 1e-6、批级后处理 exit 0、0 NOTE。演练包不得上传。

## 4. 运行计划与事前登记

写 `RUN_PLAN_HPC_V4.md` 并在打包前提交：目的与范围（第 0 节）；登记值；验收（C1 (a)(b)(c) + GATES_V6 `ACCEPTED_LAYER2`，失败门在 v3.1 并集内）；**报警线**：用 v3.1 2920×3h 的 F1、F2 对偶与解（`work/p1_v3_20261102/hpc_results_v31/unpacked/`）按第 214 项第⑤条给出 v4 相对 v3.1 目标值变化的下界（右端类）与一阶上界（成本类），系数类只给一阶估计并注明无界——**求解前写定**；**预测**（写明方法与依据：两种目标值、B6 的符号与区间、各国 Owen 受益符号、迭代数、内存峰值、用时）；批级后处理内容（B6、Owen、与 v3.1 基线的对照）；结果回收（G1 中间导出、G2 结果包、60 天清除）。读取 v3.1 已解网络时遵守内存规则（本机无 Gurobi 进程、可用内存 ≥ 8 GiB，一次一个）。

## 5. 操作指南

写 `HPC_OPERATOR_GUIDE_V4.md`（中文，按 v3.1 指南的步骤与格式）：A 本机核对与单路上传到 `/hpctmp/$USER/hpr4`（PowerShell，用户名用 `$HPC_USER` 变量，不写进文件）；B atlas8 上 `sha256sum -c` 与登录预检；C 冒烟提交与判读（期望值、PASS 判据）；D 正式提交（只在冒烟 PASS、登录欢迎信息无维护通知之后）；E 监控（`hpr_status` 同时显示两种目标值）；F 回收（G1、G2）；G 出现 STOP / STOP_SAFE 时的处理。在开头用一张表列出与 v3.1 指南的全部差异。

## 6. 产出、额度与停止条件

- **交付目录** `work/p1_v4_w14_20261109/`：`hpc_package_v4/`（上传用，不入库）、`RUN_PLAN_HPC_V4.md`、`HPC_OPERATOR_GUIDE_V4.md`、`STATIC_CHECKS.md`、`DRILL_REPORT.md`、`REPORT.md`（第 0 节结论摘要：包的 `COMMIT`、包 SHA256SUMS 的 SHA256、文件数与大小、网络 SHA256、冒烟期望值、待决问题）、`EVIDENCE.json`、`PROGRESS.md`、审阅包。
- **额度：** 求解器至多 2 次（第 3 节）；本机计算上限 4 小时；磁盘新增上限 10 GB；不下载。
- **停止条件：** 本文件 SHA256 不符；会话模型不是 Opus 5.5；D2c 审阅提交不是头提交的祖先或差异超出交付目录；任何静态检查不通过；演练不是 PASS 或 dry-run 不是 `DRY_RUN_OK`；包中出现许可类字符串；需要改模型代码、输入、配置或注册表；需要连 HPC；可能泄露许可内容或登录信息。
