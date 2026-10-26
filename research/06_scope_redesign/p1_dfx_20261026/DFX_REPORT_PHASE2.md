# DFX 阶段 2 报告：HPC 部署包草稿（NUS Atlas，PBS Pro；本机离线，未连 HPC）

**摘要（≤ 10 行）**
1. 草稿位于 `hpc_package_dfx/`（本分支 `research/06_scope_redesign/p1_dfx_20261026/`，副本在 `work/p1_dfx_20261026/`）：PBS 作业生成器 `make_pbs.sh`（队列 / 核数 / 内存 / walltime / TimeLimit / 项目名全部参数化，默认值取自用户实测的 `HPC_FACTS_20261026.md`）、五个作业体（单作业 F1+F2、两作业 F1 / F2、批级后处理、56 时段冒烟）、环境安装、登录节点预检、上线检查单、HPC 包组装脚本。全部 **PROPOSED**（未在 HPC 运行；`hpc_run_one.sh` / `hpc_batch_post.sh` 未做替身测试）。
2. 推荐执行方式：**单个 PBS 作业原样运行第四批 `run_batch4.sh`**（`SOLVE_MODE=split`，P1 探针 / 内存止损 / 早期测速 / 分级停批均为 B4P 已登记并有 10 个替身测试的逻辑），`parallel` 队列、96 核、210 GB（串行）或 400 GB（并行）、walltime 260 h。
3. 路径：代码与 conda 环境在 `$HOME`（20 GB 配额，环境约 3.3 GiB）；网络、运行目录、日志、结果包在 `/hpctmp/$USER/dfx_hpc`（500 GB，无备份，**60 天清除**）；许可只在 `~/.gurobi/gurobi.lic`（chmod 600），作业只经 `GRB_LICENSE_FILE` 引用，预检只查存在与权限位。
4. 冒烟作业 `dfx_smoke_56.pbs`：计算节点 `curl https://token.gurobi.com`（只记 HTTP 状态；用户已用作业 1028392 验证为 302）→ 一次 56 时段分进程求解（T16，TimeLimit 3,000 s）→ 后处理链 → `SMOKE_STATUS.txt`。
5. **两个必须先由用户决定并登记的事项：** (B1) TimeLimit：指令暂定 432,000 s（120 h），而 `run_batch4.sh` 登记值是 259,200 s / 墙钟 266,400 s——改登记值须在 `RUN_PLAN_B4` 补登并提交（B4P 文件改动，需授权）；(B2) `b4_batch4.py` 登记的基础网络仍是 v1（`ec80668f`：`bca20fc0…` / `b401a687…`），对 v2 网络 `run_batch4.sh` 阶段 0 会按设计安全停止——须在 AutoDL 筛查确认 v2 后把 `REGISTERED_SHA` / `REGISTERED_BYTES` / `BUILD_COMMIT` 改为 `08879f0b…` / `d90ca992…` / `72083fde` 并补登。
6. 内存申请依据 B4P 外推（INFERENCE）：F1 Gurobi 进程高值 160 GiB × 1.3 ≈ 210 GB；F2 149 × 1.3 ≈ 200 GB；≤ 360 GB 才能落到 32 台 367 GB 节点；v2 网络规模与 v1 同量级（负荷 +6.7 %，组件数相同），外推未按 v2 重做。
7. 维护窗口：2026-10-29 18:00 停止调度 → 10-31 06:00 关机 → 11-02 17:00 恢复；F1 / F2 最早 11-02 17:00 后提交；冒烟可在 10-29 18:00 前完成（排队约 3 min 实测）。
8. 本阶段未改任何 B4P / 第三批文件；未连 HPC、未下载任何数据；HPC 包尚未组装（`make_hpc_package.sh` 可在提交后于 WSL 组装，清单会把 B2 记为 `registration_pending`）。

## 1. 文件清单

| 文件 | 性质 | 内容 |
|---|---|---|
| `README_HPC.md` | PROPOSED | 内容、路径约定、参数表、作业流程、时限登记问题、与阶段 4 的关系 |
| `HPC_GO_LIVE_CHECKLIST.md` | PROPOSED | A 事实核实（10 项，`HPC_FACTS` 已核实 7 项）、B 用户决定（6 项）、C 上线步骤（8 步） |
| `make_pbs.sh` | PROPOSED | 参数 → `pbs/dfx_f12_both.pbs`、`dfx_f1_integrated.pbs`、`dfx_f2_disconnected.pbs`、`dfx_batch_post.pbs`、`dfx_smoke_56.pbs`；walltime = TimeLimit + 2 × 开销（5 h）；≤ 720 h 校验 |
| `hpc_job_both.sh` | PROPOSED | 单作业体：许可存在 / 600 检查 → B4P `preflight.sh`（含 licence 节：一次 WLS 令牌，≥ 330 s 后首次求解）→ `run_batch4.sh --auth "$DFX_AUTH"`（`CORES`、`MEM_QUOTA_GIB`、`SOLVE_MODE=split`、`REMOVE_LP=1`、`TMPDIR` 在 `/hpctmp`）→ 结果包列表 |
| `hpc_run_one.sh` | PROPOSED（未测试） | 两作业方案的单运行体：三进程 + 逐运行后处理 + 分级分类；墙钟用 `timeout` |
| `hpc_batch_post.sh` | PROPOSED（未测试） | 两作业后的批级参照 / 重评 / B6 / 汇总 / 导出 / 打包 |
| `hpc_smoke_56.sh` | PROPOSED | WLS 连通 + 56 时段分进程求解 + 后处理链 |
| `hpc_install_env.sh` | PROPOSED | 登录节点：miniforge → 第三批锁定环境（`env/install_env.sh`，缓存在 `/hpctmp`）→ 代码解包到 `$HOME/dfx_hpc/repo` 并链接为 `./repo` |
| `hpc_preflight.sh` | PROPOSED | 许可文件存在 / 属主 / 600、包内无许可特征串、路径、`SHA256SUMS`、2920×3h v2 网络 = DFX 登记值 + 回执、环境关键包、工具、配额、队列 |
| `make_hpc_package.sh` | PROPOSED | WSL 组装：2920×3h v2 网络 + 回执 + 成本表、代码归档、B4P `run_batch4.sh` / `preflight.sh`、第三批 `pack_results.sh` / `env/`、本目录、`pbs/`、`RUN_PLAN_B4.md`、`RUN_PLAN_DFX.md`、`SHA256SUMS`、清单（含 `registration_pending`） |

## 2. 参数与依据（全部取自 `HPC_FACTS_20261026.md`，待用户确认）

| 参数 | 取值 | 依据 |
|---|---|---|
| 队列 | `parallel` | 540 GB / 12–96 核 / 720 h；每用户 ≤ 8 作业、≤ 96 核；查询时 306 排队 / 107 运行，排队可能较久 |
| 核数 | 单作业 96；两作业各 48 | 档案 Threads 16；用户建议各 48 |
| 内存 | F1 210 GB、F2 200 GB；单作业串行 210 GB、并行 400 GB | B4P 分进程 Gurobi 峰值高值 160 / 149 GiB × 1.3；并行须两进程之和 ≤ 80 % 配额（309 ≤ 320） |
| TimeLimit | 432,000 s（参数；见 B1） | 指令阶段 2 暂定；B4P 估计 F1 barrier 9.5 / 56 / 146 h |
| walltime | 单作业 260 h；两作业各 130 h；冒烟 3 h；批级后处理 8 h | TimeLimit + 2 × 开销（进程 1 约 0.5 h、进程 3 约 3 h、后处理约 1.5 h）；≤ 720 h |
| 冒烟作业 | parallel 16 核 / 24 GB / 3 h | 56 时段分进程峰值 2.2–3.6 GiB；serial 队列 1 核会使 16 线程 barrier 极慢（备选，B6） |
| 环境 | 自装 miniforge + 第三批锁定（pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4、pandas 2.3.1、xarray 2025.1.2、scipy 1.15.2、netCDF4 1.7.2） | 集群模块 Gurobi 8 / 9.5、conda 3.6–4.12 太旧；WLS 在计算节点可用（作业 1028392，HTTP 302） |
| `-P` 项目名 | 不加 | 本次提交未要求 |

## 3. 安全与路径规则（已写入脚本）

- 许可：只在 `$HOME/.gurobi/gurobi.lic`（chmod 600，用户自行放置）；`hpc_job_both.sh` / `hpc_run_one.sh` / `hpc_smoke_56.sh` 只检查存在与权限位，经 `GRB_LICENSE_FILE` 传给 Gurobi 进程；`hpc_preflight.sh` 与 `make_hpc_package.sh` 检索包内许可特征串（不打印内容）；导出日志经许可行过滤。
- 账号、主机名、密码不出现在任何文件；授权原文只经 `qsub -v DFX_AUTH="…"` 传入。
- `/hpctmp` 60 天清除：结果包生成后立即下载并核对；`PBS_JOBS.txt` 记录作业号、节点、申请资源、cgroup 限制。
- 续跑：同一 `qsub` 命令；已结束的求解不重复；"已开始未结束" → `STOP_SAFE`，由用户决定（`RUN_PLAN_B4` 3.8）。

## 4. 未做与局限

- 未连 HPC、未下载；HPC 包未组装（等 F6 提交后可在 WSL 组装并核对 `SHA256SUMS`）。
- `hpc_run_one.sh` / `hpc_batch_post.sh` 未做替身测试；推荐路径不依赖它们。
- v2 2920×3h 的内存 / 时间估计沿用 B4P 对 v1 的外推（同量级假设），未重做探针（本机 Gurobi 调用已用完）。
- B1 / B2 的登记改动涉及 B4P 文件，须用户授权后另行提交。

直接进入阶段 3。
