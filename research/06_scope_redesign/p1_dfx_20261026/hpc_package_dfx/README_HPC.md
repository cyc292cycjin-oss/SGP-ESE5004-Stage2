# DFX 阶段 2：NUS Atlas（PBS Pro）部署包草稿——第四批 F1 / F2（2920×3h v2 网络，分进程求解）

**状态：** PROPOSED（草稿；本机离线编写，未连 HPC；参数来自 `HPC_FACTS_20261026.md` 的实测事实，待用户在 HPC 上按 `HPC_GO_LIVE_CHECKLIST.md` 核实后定稿）。
**不含任何账号、密码、许可内容或主机登录信息。** 许可只放在 `~/.gurobi/gurobi.lic`（chmod 600），绝不进入项目目录、作业脚本、日志或结果包。

## 1. 内容

| 文件 | 用途 |
|---|---|
| `make_pbs.sh` | 由参数（队列、核数、内存、walltime、TimeLimit、可选项目名）生成 PBS 作业脚本；默认值 = `HPC_FACTS` 的建议值 |
| `pbs/*.pbs.template` | 作业脚本模板（占位符 `@QUEUE@` 等由 `make_pbs.sh` 填充）：`dfx_f12_both`（一个作业跑 F1 + F2，`run_batch4.sh` 原样执行，**推荐**）、`dfx_f1_integrated` / `dfx_f2_disconnected`（两个作业各跑一个运行，`hpc_run_one.sh`，PROPOSED，用前须替身测试）、`dfx_batch_post`（两作业方案的批级后处理）、`dfx_smoke_56`（56 时段冒烟 + WLS 连通验证） |
| `hpc_job_both.sh` | 作业体：在 `/hpctmp` 的运行目录里执行第四批 `run_batch4.sh --auth`（`SOLVE_MODE=split`、`CORES`、`MEM_QUOTA_GIB` 来自 PBS 申请） |
| `hpc_run_one.sh` | 作业体（PROPOSED）：单个运行的三进程（构建 → gurobipy → 映射）+ 逐运行后处理，供两作业方案 |
| `hpc_batch_post.sh` | 作业体（PROPOSED）：两运行结束后的批级参照 / 重评 / B6 / 汇总 / 打包 |
| `hpc_smoke_56.sh` | 作业体：计算节点上 `curl https://token.gurobi.com`（只看 HTTP 状态）→ 56 时段截短的分进程求解一次 → 后处理链 |
| `hpc_install_env.sh` | 家目录自装 miniforge + 第三批同一锁定环境（conda 包缓存放 `/hpctmp`，家目录 20 GB 配额） |
| `hpc_preflight.sh` | 上线前检查：许可文件存在与权限（不读内容）、环境关键包、网络 SHA256、工具、配额、`/hpctmp` 路径 |
| `make_hpc_package.sh` | 在 WSL 组装 HPC 包（2920×3h v2 网络 + 回执 + 成本表、代码归档、第三批环境锁定、第四批 `run_batch4.sh` / `preflight.sh` / `pack_results.sh`、本目录脚本、`SHA256SUMS`） |
| `HPC_GO_LIVE_CHECKLIST.md` | 需要用户在 HPC 上核实的事实与上线步骤 |

## 2. 路径约定（`HPC_FACTS` 第 1 节）

| 内容 | 位置 | 说明 |
|---|---|---|
| 代码（解包的 git archive）、conda 环境 | `$HOME/dfx_hpc/repo`、`$HOME/miniforge3/envs/pypsa-earth` | 家目录 20 GB 配额，有快照；环境约 3.3 GiB |
| conda 包缓存、pip 缓存、临时文件 | `/hpctmp/$USER/dfx_hpc/conda_pkgs_cache`、`/hpctmp/$USER/dfx_hpc/tmp` | 无备份；60 天未改动自动清除 |
| 网络、运行目录、日志、结果包 | `/hpctmp/$USER/dfx_hpc/package/networks`、`/hpctmp/$USER/dfx_hpc/runs/<batch>`、`/hpctmp/$USER/dfx_hpc/results` | **60 天清除：结果包生成后立即下载并核对 SHA256** |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600` | 作业里只通过 `GRB_LICENSE_FILE` 引用；`hpc_preflight.sh` 只检查存在与权限位 |

作业脚本以 `$PBS_O_WORKDIR` = `/hpctmp/$USER/dfx_hpc/package` 为起点；`REPO` 指向家目录的代码；`RUN_DIR` 在 `/hpctmp`。

## 3. 参数（`make_pbs.sh` 的默认值 = `HPC_FACTS` 建议；全部待确认）

| 参数 | 默认 | 依据 |
|---|---|---|
| `QUEUE` | `parallel` | 540 GB / 12–96 核 / 720 h；每用户 ≤ 8 作业、合计 ≤ 96 核 |
| `NCPUS` | 48（两作业方案各 48；单作业方案 96） | 档案 Threads 16；其余核留给分进程与 I/O（用户建议） |
| `MEM_GB` | F1 210、F2 200（单作业 210，串行；并行 400） | B4P 分进程 Gurobi 进程峰值高值 160 / 149 GiB × 1.3 ≈ 208 / 194 GiB；≤ 360 GB 可落在 32 台 367 GB 节点；并行须两进程之和 ≤ 80 % 配额（309 ≤ 320） |
| `TIME_LIMIT_S` | 432,000（120 h） | 指令阶段 2 暂定值，待用户确认；`run_batch4.sh` 登记值是 259,200 s（72 h），HPC 用 `ALLOW_UNREGISTERED=1` + `GUROBI_TIME_LIMIT_S` 覆盖**只能在用户登记新时限后**（见第 5 节） |
| `WALLTIME` | 单作业串行 `260:00:00`；两作业 F1 `130:00:00`、F2 `130:00:00`；冒烟 `03:00:00`；批级后处理 `08:00:00` | TimeLimit + 2 × 开销（进程 1 约 0.5 h、进程 3 约 3 h、后处理约 1.5 h → 开销约 5 h，×2 = 10 h）；≤ 720 h |
| `PROJECT` | 空（不加 `-P`） | 本次提交未要求 |
| `SOLVE_MODE` | `split` | B4P 等价证明；`RUN_PLAN_B4` 3.1 |

## 4. 作业流程（推荐：单作业 `dfx_f12_both.pbs`）

1. `hpc_install_env.sh`（登录节点；一次）→ `hpc_preflight.sh`（登录节点：许可权限、环境、SHA256、工具；**WLS 连通在冒烟作业里验证**）。
2. `qsub pbs/dfx_smoke_56.pbs`：计算节点 `curl -sS -o /dev/null -w "%{http_code}" https://token.gurobi.com`（期望 302）→ 56 时段分进程求解（档案 T16，TimeLimit 3,000 s）→ 后处理链 → `SMOKE_STATUS.txt`。optimal 且链路 exit 0 才继续。
3. 维护窗口之后（2026-11-02 17:00 起）`qsub pbs/dfx_f12_both.pbs`：作业体 `hpc_job_both.sh` 在 `/hpctmp/$USER/dfx_hpc/runs/batch4` 执行 `run_batch4.sh --auth "<用户授权原文>"`，`CORES=$NCPUS`、`MEM_QUOTA_GIB=$MEM_GB`、`SOLVE_MODE=split`、`REMOVE_LP=1`；P1 探针按登记规则决定 F2 是否并行（48 核 ≥ 33，但 F1 峰值 ≤ 40 % 配额在 210 GB 下不成立 → 串行；400 GB 并行配置见模板注释）。
4. 结束后 `pack_results.sh`（作业体内已调用）→ 结果包在 `/hpctmp/$USER/dfx_hpc/runs/batch4/`；`scp` 回本机并 `sha256sum -c`；**60 天内下载**。
5. 作业中断（walltime、节点故障）：同一命令再次 `qsub` 即续跑（已结束的求解不重复；"已开始未结束"的求解安全停止等用户，按 `RUN_PLAN_B4` 3.8 由用户决定更长时限重开）。

两作业方案（`dfx_f1_integrated.pbs` + `dfx_f2_disconnected.pbs` → `dfx_batch_post.pbs`）用 `hpc_run_one.sh` / `hpc_batch_post.sh`（PROPOSED）：排队更容易（各 48 核 / ≤ 210 GB），但驱动脚本是本草稿新写的，**用前须在本机做替身整链测试**（同 B4P 的 10 个替身测试），阶段 2 未做。

## 5. 时限的登记问题（需要用户决定）

`run_batch4.sh` 的登记值是 TimeLimit 259,200 s / 墙钟 266,400 s（`RUN_PLAN_B4` 3.1）。HPC 允许 720 h，指令暂定 432,000 s（120 h）。两种做法：
- **A（推荐）：** 用户确认 120 h 后，在 `RUN_PLAN_B4` 补充一节登记新时限（事先登记原则），并把 `run_batch4.sh` 顶部的 `R_TL` / `R_WALL` 改为 432,000 / 439,200 s 提交（这是 B4P 文件的改动，须用户授权）；作业脚本不用覆盖变量；
- **B：** 不改文件，作业里 `ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=432000 WALL_CAP_S=439200`——但这会把正式运行标为"未登记值"（`STATUS` 记 `NOTE:ALLOW_UNREGISTERED=1`），且关闭钩子拒绝检查，**不建议**。

`make_pbs.sh` 生成的作业脚本按 A 写（不覆盖变量）；`TIME_LIMIT_S` 参数只用于 walltime 计算与冒烟作业。

## 6. 与 AutoDL 365×24h 筛查（阶段 4）的关系

HPC 包引用阶段 1 已构建的 2920×3h v2 网络（SHA256 见 `make_hpc_package.sh` 顶部 / `RUN_PLAN_DFX` 第 1 节）。阶段 4 若发现需求问题需要重建，重建后更新 `make_hpc_package.sh` 的登记值并重新组装。AutoDL 筛查的 B6 与 Owen 份额是 2920×3h 正式运行的对照。
