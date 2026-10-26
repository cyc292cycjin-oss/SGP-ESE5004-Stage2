# HPC 上线检查单（DFX 阶段 2 草稿；需要用户在 NUS Atlas 上核实的事实与步骤）

状态：PROPOSED。`HPC_FACTS_20261026.md` 已核实的项标 ✔；未核实的项列出查法。**任何一项不符就停下报告，不自行放宽。**

## A. 事实核实（登录节点）

| # | 项目 | 已知（HPC_FACTS） | 查法 / 待确认 |
|---|---|---|---|
| A1 | 队列 parallel：内存 ≤ 540 GB、12–96 核、walltime ≤ 720 h、每用户 ≤ 8 作业 / 96 核 | ✔ | `qstat -Q`、`qstat -Qf parallel`（再次确认 `resources_max.mem`、`max_user_res`） |
| A2 | 节点内存：32 台 367 GB、约 10 台 792 GB | ✔ | `pbsnodes -a \| grep -E "resources_available.(mem\|ncpus)"`；申请 ≤ 360 GB 才能落到 32 台节点 |
| A3 | 模块：Gurobi 8 / 9.5（不用）、conda 旧版（不用） | ✔ | `module avail`；本包自装 miniforge |
| A4 | 计算节点可达 `token.gurobi.com`（HTTP 302） | ✔（作业 1028392，serial 队列） | 冒烟作业再次记录 `WLS_TOKEN_HTTP` |
| A5 | 家目录 20 GB、`/hpctmp` 500 GB、60 天清除 | ✔ | `hpc s`、`quota -s`；环境约 3.3 GiB + 代码约 0.3 GB 在家目录 |
| A6 | 维护窗口 2026-10-29 18:00 停止调度 → 10-31 06:00 关机 → 11-02 17:00 恢复 | ✔ | 登录欢迎信息；F1 / F2 在 11-02 17:00 后提交；冒烟可在 10-29 18:00 前完成 |
| A7 | 计算节点有 GNU `time`（`/usr/bin/time -v`）、`setsid`、`timeout`、`pgrep`、`curl` | 未知 | 冒烟作业的工具检查行；缺 GNU time 则 `run_batch4.sh` 拒绝启动（需在 `$HOME` 编译 GNU time 或请管理员安装） |
| A8 | PBS 作业内的 cgroup 内存限制是否可见（`/sys/fs/cgroup/memory.max` 或 v1 `memory.limit_in_bytes`） | 未知 | 冒烟作业 `PBS_JOBS.txt` 的 `CGROUP:` 行；不可见时 `MEM_QUOTA_GIB`（= 申请内存）由作业脚本显式给出（已写） |
| A9 | PBS 是否导出 `NCPUS` / `PBS_O_WORKDIR`、是否需要 `-P` 项目名 | `-P` 未要求 ✔ | `make_pbs.sh PROJECT=` 可加；`JOB_NCPUS` 由生成脚本写死，不依赖 `NCPUS` |
| A10 | 登录节点交互 CPU 30 min 限制 | ✔ | `hpc_install_env.sh` 的 conda create 约 14 min（AutoDL 实测）；超时则重跑 |

## B. 需要用户决定（上线前）

| # | 决定 | 草稿取值 | 依据 / 备选 |
|---|---|---|---|
| B1 | TimeLimit 登记：改 `run_batch4.sh` 的 `R_TL` / `R_WALL`（259,200 / 266,400）为 432,000 / 439,200 并在 `RUN_PLAN_B4` 补登（方案 A），还是保持 72 h | 432,000 s（指令阶段 2 暂定） | B4P 估计 F1 barrier 9.5 / 56 / 146 h：72 h 覆盖中值，120 h 覆盖到约高值的 80 %；HPC 允许 720 h |
| B2 | 第四批登记输入改为 v2 网络（`b4_batch4.py` 的 `REGISTERED_SHA` / `REGISTERED_BYTES` / `BUILD_COMMIT` → 08879f0b… / d90ca992… / 72083fde）并在 `RUN_PLAN_B4` 补登 | 待 AutoDL 筛查确认 v2 后 | 不改则 `run_batch4.sh` 阶段 0 对 v2 网络安全停止（设计如此） |
| B3 | 单作业（96 核 / 210 GB 串行，或 400 GB 并行）还是两作业（各 48 核 / 210、200 GB）+ 批级后处理作业 | 单作业（`run_batch4.sh` 原样，已有 10 个替身测试） | 两作业方案的驱动脚本 `hpc_run_one.sh` / `hpc_batch_post.sh` 是草稿，用前须替身测试 |
| B4 | 内存申请：F1 210 GB（高值 160 GiB × 1.3）；并行 400 GB | 210 GB | ≤ 360 GB 才能落到 32 台 367 GB 节点；792 GB 节点只有约 10 台 |
| B5 | `REMOVE_LP=1`（Gurobi 读入后删除 5.4 GB LP 文件） | 是 | `/hpctmp` 500 GB 充足，但 60 天清除；保留 LP 文件无用 |
| B6 | 冒烟作业队列：parallel 16 核 / 24 GB / 3 h（草稿）还是 serial 1 核 / 15 GB | parallel | 档案 Threads 16；serial 1 核会使 16 线程 barrier 极慢但可验证许可 |

## C. 上线步骤（顺序；每步的输出留在 `/hpctmp/$USER/dfx_hpc/`）

1. 本机 `make_hpc_package.sh` 组装包 → 单路 `rsync`/`scp` 到 `/hpctmp/$USER/dfx_hpc/package` → `sha256sum -c SHA256SUMS` 全部 OK。
2. 用户自行放置许可：`mkdir -p ~/.gurobi && chmod 700 ~/.gurobi`，把 WLS 许可写入 `~/.gurobi/gurobi.lic`，`chmod 600`。（不经由本包、不经由会话文本。）
3. 登录节点 `bash hpc/hpc_install_env.sh`（约 15–30 min；家目录 +3.6 GB）→ `bash hpc/hpc_preflight.sh` → `HPC_PREFLIGHT OK`。
4. `bash hpc/make_pbs.sh`（按 B 节的决定传参数）→ `qsub -v DFX_AUTH="<授权原文>" pbs/dfx_smoke_56.pbs` → `runs/smoke_56/SMOKE_STATUS.txt`：`WLS_TOKEN_HTTP:302`、`SOLVE:optimal …`、各步 exit=0、`V6`、`STOPCLASS`。非 optimal 或任一步失败 → 停下报告，不重试。
5. B1 / B2 的登记提交完成后（用户授权的 B4P 文件改动 + `RUN_PLAN_B4` 补充）重新组装包、重新上传（步骤 1），再做步骤 3 的预检（代码变了）。
6. 维护窗口后：`qsub -v DFX_AUTH="<授权原文>" pbs/dfx_f12_both.pbs`；监控 `runs/batch4/STATUS.txt`、`MONITOR_F1.csv`（`cgroup_anon_gib` 对配额）、`P1_DECISION.json`、`PROJECTION_F1.json`；`qstat -u $USER`。
7. 结束：`runs/batch4/results_light_*.tar.gz`、`results_full_*.tar.gz` + `.sha256` → 下载 → 本机 `sha256sum -c`；**60 天内完成**。许可文件留在家目录由用户自行处理（不在包内，无需删除包内文件）。
8. 中断续跑：同一 `qsub` 命令；`STOP_SAFE:INTERRUPTED_*` 时按 `RUN_PLAN_B4` 3.8 由用户决定更长时限重开。
