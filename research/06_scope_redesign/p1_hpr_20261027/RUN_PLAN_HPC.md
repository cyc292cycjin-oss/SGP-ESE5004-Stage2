# HPC 正式运行计划（RUN_PLAN_HPC）——第四批 F1 / F2，2920×3h v2 网络，NUS Atlas（PBS Pro）两作业方式

**版本：** HPR v1，2026-10-27（SGT）。依据 `HPR_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `f14cb018…412d86`）与用户 2026-10-27 12:43 SGT 确认的 B1–B4，以及用户 2026-10-27 的补充（步骤 D2：全尺寸 BUILD_ONLY 测试作业）。
**登记时间：** 本文件在任何 HPC 操作、任何本机 2920×3h v2 求解（H4 演练）之前提交（`1f62176f`，2026-10-27 13:19:34 SGT）；看到任何结果后第 2–7 节的规则与数值不再修改（修改只能作为新的、登记在前的计划修订）。
**修订（2026-10-27，独立审查 H7 之后；第 2–7 节的数值与规则未改，只补说明）：** §4 第 6 条措辞（本机许可文件不写路径）；§5 第 1 项补 rss 模式下 cgroup 列为空的说明（审查 N-03）；§7 第 5 项补"停批情形下从未启动的运行视为落定"的放行条件（审查 F-06）；§9 BUILD_ONLY 行补 D2 结果的判读规则（审查 F-16）；§11 作业日志位置更正为提交目录（审查 F-10）。
**与 `RUN_PLAN_B4.md`（B4P v1，2026-10-26）的关系：** 本文件只改写 B1–B4 涉及的登记值（输入网络、TimeLimit 与派生墙钟、资源配额）和因 PBS 两作业方式不再适用的机制（P1 探针）；`RUN_PLAN_B4.md` 第 3.3–3.8 节的规则（内存止损、早期测速、验收与停批、后处理、资源止损后的重开）全部沿用，并在下文逐条写明。模型、网络构建、成本表、求解档案参数、GATES_V6 / C1 阈值一律不改。
**单一来源：** 代码中的登记常数——`scripts_project/b4_batch4.py`（`REGISTERED_SHA`、`REGISTERED_BYTES`、`BUILD_COMMIT`、`TIME_LIMIT_S`、`WALL_CAP_S`、`LICENCE_GAP_S`、`HPC_JOBS`、`MEMORY_STOP_FRACTION`、`PROJECTION_FRACTION`）与 `run_batch4.sh` 顶部的 `R_TL` / `R_WALL` / `R_GAP` / `R_MODE`；PBS 作业脚本由 `make_pbs.sh` 从 `b4_batch4.py hpc-plan` 生成；`hpr_consistency.py` 把本文件、作业脚本、运行器、预检中的值列表比对（检查单 H-P3）。

---

## 1. 运行

| 编号 | 运行 | 网络文件 | 字节 | SHA256 | 情景 | 成本表 | 档案 | 作用 |
|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 2920×3h v2 | `networks/integrated_2920_3h_unsolved.nc` | 63,873,447 | `08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271` | integrated | `networks/integrated_costs_active_research.csv` | `formal_barrier_1e6_t16` | c(N)、Owen 分摊、B6 基准 |
| F2 | 不互联 2920×3h v2 | `networks/disconnected_2920_3h_unsolved.nc` | 63,202,193 | `d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7` | disconnected | `networks/disconnected_costs_active_research.csv` | `formal_barrier_1e6_t16` | B6 = F2 − F1 |

- **构建（B2）：** 分支 `codex/dfx-v3-20261026` 提交 `72083fde6bffd89580869af6dd00885a8d76721f`（dirty 0，`PYTHONHASHSEED=0`），DFX F5.1 构建到主检出 `results_project/dfx_v3/builds_v2/<scenario>/`；构建回执 `<scenario>_BUILD_RECEIPT.json`（`network.sha256` = 上表，`code_sha` = 构建提交）。与 DFX 365×24h v2 筛查网络（`82928a4c…` / `5c75bfa0…`）出自同一次构建。**365×24h 网络不入包**（预检发现即失败）。
- **档案（B4，不改）：** `formal_barrier_1e6_t16`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200；`--scaling on`。
- **求解方式（B4）：** `SOLVE_MODE=split`（`run_batch4.sh` 登记值 `R_MODE=split`）：进程 1 `s2_solve.py … --label BATCH4_2920X3H --split-stage build`（无许可）→ 进程 2 `b4_split_solve.py --run-dir <运行目录> --remove-lp`（唯一的 Gurobi 进程；`REMOVE_LP=1`，读入后删除约 5.4 GB 的 LP 文件）→ 进程 3 `s2_solve.py … --split-stage assign`（无许可）。B4P 等价证明（56×3h 逐位相同）不变。
- **一次求解：** 每个运行只求解一次；不重试、不改参数、不热启动；非 optimal 照实记录并按第 7 节分级。

## 2. 时限与 PBS walltime

| 量 | 值（s） | 依据 |
|---|---|---|
| **TimeLimit（B1）** `R_TL` / `TIME_LIMIT_S` | **864,000**（240 h），F1 = F2 | 用户决定 B1；B4P 外推 F1 barrier 9.5 / 56 / 146 h（v2 迭代可能多约 30 %：最高约 190 h < 240 h） |
| **进程 2（Gurobi）墙钟** `R_WALL` / `WALL_CAP_S` | **871,200** = 864,000 + 7,200 | 沿用 B4P 3.1 第 2 项的开销余量 2 × 3,600 s（LP 读入 95–154 s、解数组写出 ≤ 1,800 s）；到时终止整个进程组（TERM，30 s 后 KILL） |
| 进程 1 超时 `BUILD_TIMEOUT_S` | 3,600 | B4P：构建 + 写 LP 10–15 min，云端单核慢 1.35 倍约 20 min；3 倍 |
| 进程 3 超时 `ASSIGN_TIMEOUT_S` | 32,400 | B4P：重建 + 映射 + 导出约 2.2–3 h；3 倍 |
| 后处理单步超时 `POST_TIMEOUT_S` | 10,800 | B4P 3.6 第 3 项（3 倍余量）；违反分析与 C1 失败后重做一次 |
| 打包超时 `PACK_TIMEOUT_S` | 7,200 | B4P |
| 逐运行后处理估计 | 3,900（65 min） | B4P 6.1：违反分析 / C1 / Owen 各约 20 min（55 s × 16 × 1.35），M12 约 1 min，GATES_V6 与分级 < 1 min |
| 运行器启动后首次 Gurobi 的间隔 | 330 | B4P 3.2 第 3 项（`R_GAP`，WLS 令牌 ≥ 5 min） |
| 作业体开销（记录、预检、导出）估计 | 1,800 | HPR 估计 |
| F2 等待 F1 Gurobi 启动的上限 `WAIT_START_MAX_S` | 7,200 | 第 4 节：F1 的进程 1 ≤ 3,600 s + 330 s 间隔 + 预检与余量 |
| **PBS walltime F1** | **918,000**（`255:00:00`） | 330 + 3,600 + 871,200 + 32,400 + 2 × 3,900 + 1,800 = 917,130 → 向上取整到 255 h；≤ 720 h |
| **PBS walltime F2** | **925,200**（`257:00:00`） | 917,130 + 7,200（等待 F1 启动的上限）= 924,330 → 257 h；≤ 720 h |
| PBS walltime 批级作业 | 43,200（`12:00:00`） | 参照 / 重评 / 受益 / 汇总 / 打包为分钟级；若某运行的后处理步骤在本作业内未完成，`POST_ONLY=1` 补做最多 4 步 × 10,800 s |

早期测速（第 5 节）的止损线 = 0.80 × 864,000 = **691,200 s**。

## 3. PBS 资源（B3）

| 作业 | 队列 | 资源 | walltime | 内存配额 `MEM_QUOTA_GIB` | 核数 `CORES` | 依赖 |
|---|---|---|---|---|---|---|
| **F1** `hpr_f1` | `parallel` | `select=1:ncpus=48:mem=300gb` | 255:00:00 | **300** | 48 | 无 |
| **F2** `hpr_f2` | `parallel` | `select=1:ncpus=48:mem=250gb` | 257:00:00 | **250** | 48 | `-W depend=after:<F1 作业号>`（F1 开始执行后才可调度） |
| **批级** `hpr_batch` | `parallel` | `select=1:ncpus=12:mem=120gb` | 12:00:00 | 120 | 12 | `-W depend=afterany:<F1>:<F2>`（两者结束后，无论退出码） |

- 内存配额 = 申请值（PBS `gb` = 2^30 B；作业体把 `MEM_QUOTA_GIB=300 / 250` 显式传给运行器，不依赖 cgroup 是否可见）。F1 300 GiB ≥ B4P 高值 160 GiB × 1.25 = 200；F2 250 ≥ 149 × 1.25 = 186.25（检查单 H-P4）。止损线 80 %：F1 **240 GiB**，F2 **200 GiB**（第 5 节）。
- 48 + 48 = 96 核 = `parallel` 队列每用户合计上限（`HPC_FACTS` 队列表）；批级作业 12 核在两者结束后才运行，不与之同时占核。每用户 ≤ 8 个作业：F1、F2、批级 = 3 个。
- 300 GB / 250 GB 都 ≤ 约 360 GB，可落在 32 台 367 GB 节点（96 核 33 台、64 核 8 台都容得下 48 核）；不申请 792 GB 节点。单作业内存 ≤ 540 GB 上限；walltime ≤ 720 h。
- 不加 `-P` 项目名（本次提交未要求）；无 `-V`（登录 shell 的变量不带入作业，测试开关由预检 `guards` 节再查一次）。

## 4. 许可会话

- 学术 WLS 最多 **2 个并发会话**。F1 的进程 2 占 1 个，F2 的进程 2 占 1 个；任意时刻 ≤ 2。
- **F2 的第一次 Gurobi 会话必须在 F1 第一次会话开始 ≥ 330 s 之后。实现（两重）：** (a) `qsub -W depend=after:<F1>`：F2 只在 F1 开始执行后调度；(b) 运行器 `run_batch4.sh --only F2` 以 `WAIT_START_OF=F1` 运行：F2 的进程 1（构建，无许可）照常进行，进程 2 启动前等待共享运行目录中 `F1/.solve_start`（F1 进程 2 的启动时刻，由 F1 的运行器写出）存在且距今 ≥ `LICENCE_GAP_S` = 330 s；F1 已结束求解（`F1/.solve_end`）或 F1 未经 Gurobi 就结束（`F1/.ended`，如构建失败）也放行。等待超过 `WAIT_START_MAX_S` = 7,200 s 仍无 F1 的启动标记 → `STOP_SAFE:WAIT_START:F1`（F2 不求解，等用户）。
- **正式作业（F1 / F2 / 批级）不运行预检的 `licence` 节**（那是一次 Gurobi 会话）；作业开头只检查许可文件存在与权限位 600。许可是否可用由步骤 D 的冒烟作业验证。
- 每个运行器启动后首次 Gurobi 距运行器启动 ≥ 330 s（B4P 3.2 第 3 项，沿用）；每次启动前检查本节点上其他 `b4_split_solve.py` 进程不超过 1 个。
- **F1 / F2 运行期间，本机与任何云端都不得启动 Gurobi 会话**（本机 WSL 的许可文件与 HPC 上的 `~/.gurobi/gurobi.lic` 是同一 WLS 许可）。F2 结束后才空出 1 个会话；F1 结束后空出 2 个。
- 许可只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；绝不进入包、代码、作业脚本、日志、结果包；导出日志经 `licen[cs]e|registered to|wls(access|secret)|academic` 过滤；打包前检索许可特征串，命中即拒绝打包。

## 5. 止损与保护（B4P 3.3–3.4 沿用，计量方式按 PBS 写明）

1. **内存止损 → `STOP_SAFE:MEMORY:<编号>`：** 每 60 s 读本作业**实际可见**的内存计量，超过配额（第 3 节 `MEM_QUOTA_GIB`）的 **80 %**（`MEMORY_STOP_FRACTION`）→ 终止正在运行的 Gurobi 进程组，不再启动任何求解，报告用户。计量取法（`MEM_MEASURE=auto`，作业体与运行器记录实际取法）：
   - **首选：PBS 作业 cgroup 的匿名内存。** 作业体从 `/proc/self/cgroup` 解析本作业的 cgroup 路径（v2：`/sys/fs/cgroup/<path>/memory.stat` 的 `anon`；v1：`/sys/fs/cgroup/memory/<path>/memory.stat` 的 `total_rss`），把该目录作为 `CGROUP_ROOT` 传给运行器。不含可回收的文件缓存（第三批 S1 的教训）。不得把节点根 cgroup（含其他用户作业）当作本作业的计量——作业体核对路径非 `/`。
   - **不可见时：进程树 RSS 之和。** 作业 cgroup 的内存控制器不存在或不可读 → 运行器每 60 s 对进程 2 的进程组（`pgrep -g <pgid>`）求 `ps -o rss` 之和（`rss_gib_group`，与监控 CSV 同一列），对同一 80 % 线判定；STATUS 记 `mem_measure=rss`。
   - 两种计量都在 `MONITOR_<编号>.csv` 中逐分钟记录（`rss_gib_group`、`cgroup_anon_gib`、`cgroup_mem_limit_gib`）；**rss 模式下**（作业体未找到含本作业号的 cgroup）运行器不读任何 cgroup 文件，CSV 的两列 cgroup 值为空、STATUS 记 `cgroup_anon_source=none(rss_mode)`（审查 F-07 / N-03 的说明，2026-10-27；计量规则本身不变）。
2. **早期测速 → `STOP_SAFE:PROJECTION:<编号>`：** 沿用 B4P 3.4：第 20 次 barrier 迭代记录后，第 11–20 次迭代平均耗时 × 参考迭代数（F1 **450**、F2 **250**）+ 已用时间（自进程 2 启动）> 0.80 × TimeLimit = **691,200 s** → 终止该进程组，报告用户；只在首次满 20 次迭代时判定一次。
3. **墙钟：** 进程 2 到 871,200 s 终止整个进程组（TERM → 30 s → KILL）；回执不含终止条件的视为求解前回执（无返回解）。
4. **求解结果先落盘（A3.1）：** 进程 2 返回后先写 `split/SPLIT_SOLVE.json`（终止状态、目标值、迭代、Work、MaxMemUsed）与原始解数组，进程 3 再映射、导出、记账、门控；进程 3 任一步异常记入回执 `post_solve_errors`，不改变终止状态与"有返回解"的判定。
5. **不重试、不改参数、不热启动**（任何状态）。`SoftMemLimit` 不作为登记参数（B4P 3.5 第 4 项不变）。
6. **P1 探针不再使用：** 两作业方式下 F1、F2 各在自己的节点与 cgroup 内运行，`--only` 单运行模式不做 P1 探针、不写 `P1_DECISION.json`；B4P 3.2 第 1–2 项由第 4 节的许可间隔与 PBS 依赖取代。

## 6. 中断与重开

- 因计划维护、节点故障、PBS 终止（walltime）、内存或时限保护而中断的运行：**从头重开同一运行（参数不变）须用户明确授权**，登记为"资源原因的重新开始"（新的 `RUN_DIR`，报告中登记），不算重试。
- 续跑判定（同一 `RUN_DIR` 再次提交同一作业）：已结束的求解一律跳过（`SKIP_ENDED`）；"已开始未结束"的求解（`.started` 存在、`.ended` 不存在）→ `STOP_SAFE:INTERRUPTED_<编号>`，等用户；后处理各步只补缺失的输出。
- **维护重叠检查：** 提交前（步骤 E）必须确认 HPC 登录欢迎信息中没有与预计运行期（提交时刻起 F1 最长 255 h ≈ 10.6 天，F2 257 h）重叠的新维护通知；有就停下报告，不提交。已知维护窗口：2026-10-29 18:00 停止调度 → 10-31 06:00 关机 → 11-02 17:00 恢复；**F1 / F2 只在 11-02 17:00 之后提交**。
- `/hpctmp` 60 天未改动自动清除：运行目录、结果包都在 `/hpctmp/<用户>/hpr/`，结果包生成后尽快下载（第 8 节）；运行中的文件持续改动，不受清除影响。

## 7. 验收、分级与后处理

1. **验收 = GATES_V6 + C1（阈值不改）：** 与第三批 / 第四批相同：先用缺省参照给出临时 C1 判定与 GATES_V6 标签（`V6_ACCEPTANCE_PROVISIONAL.json`），F1、F2 账本齐备后生成本批参照 `BATCH_REFERENCE.json` 并重评（`grade_history` 保留）。
2. **分级与停批（B4P 3.5 沿用）：** `b4_batch4.py stop-class`：G2 不通过 → `STOP`；无返回解或 C1 (a) 不通过 → `UNUSABLE` 并 `STOP`（两个运行都是本批参照，没有"其余继续"）；只有 C1 (b)/(c) 不通过 → 不停。两作业方式下"停批 = 不再启动新的求解"体现在**共享运行目录**：F1 作业写出的 `STOP` / `STOP_SAFE` 会被尚未进入进程 2 的 F2 运行器看到并放弃启动（`NOT_STARTED_F2`）；已在求解的另一运行跑完并后处理。
3. **逐运行后处理在各自作业内完成**（`run_batch4.sh --only <编号>` 的 `post_run`）：违反量分析 → C1（临时参照）→ M12 分摊（`--register`）→ Owen 对偶形式审计 → GATES_V6（`--build-receipt`）→ 分级 → 导出 `export/<编号>/`（清洗后的日志，无 LP / 解数组）。每步 `timeout 10,800 s`，违反分析与 C1 失败后重做一次（M10A D2）；异常记 `POSTPROC_ERROR`，调度不变。
4. **批级作业**（`hpr_batch`，第 3 节；`POST_ONLY=1 bash run_batch4.sh`，无许可、无 `--auth`）在两作业都结束后：补做缺失的逐运行后处理步骤（幂等）→ `BATCH_REFERENCE.json` → C1 重评、Owen 重评、GATES_V6 终标签、分级 → **B6 = F2 − F1**（`gate_b6_cost`）与分国账本差 → **Owen 对偶形式分摊**（α 0.5 主值、α 区间、市场形式并列、燃料舱参与者；`m12_allocation.py benefit`）与受益、比例规则对照 → **与 365×24h v2 V1 / V2（DFX 阶段 4）及第三批 R3 / R4（R1 / R2 并列）的对比**（只描述，不判定；参照数值来自包内 `REFERENCE_VALUES.json`，不含任何结果文件原文）→ `BATCH4_SUMMARY.json / .md` → 导出 `export/batch/` → 结果包（light / full）。任一运行未验收：批级作业照常重评与汇总，结果包标记 `halted`，退出码 3。
5. 两作业未全部"落定"时批级作业拒绝运行（`not_ready`，退出码 2）——依赖 `afterany` 保证正常情况下不会发生。"落定" = 该运行已结束（`.ended`），**或**运行目录里有 `STOP` / `STOP_SAFE` 且该运行从未开始求解（无 `.started`，即因另一运行的停批而 `NOT_STARTED`）；此时批级作业照常重评、汇总并打出 `*_halted_*` 结果包（审查 F-06 的修订，2026-10-27）。已开始未结束的运行永远不算落定。

## 8. 结果回收

- 批级作业结束后 `/hpctmp/<用户>/hpr/runs/batch4/` 下有 `results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与各自的 `.sha256`（停批时为 `*_halted_*`）。用户尽快下载到 `D:\ResearchWorkspaces\ASEAN\work\p1_hpr_20261027\hpc_results\`，本机核对 SHA256（PowerShell `Get-FileHash`）。
- LP / 解数组（约 2 × 7.6 GB）留在 `/hpctmp`（`ARRAYS_MANIFEST.json` 登记 SHA256），60 天后自动清除；需要时另行下载。

## 9. 测试作业（登记为测试，不属于正式运行）

| 作业 | 队列 / 资源 | walltime | 内容 | 判据 |
|---|---|---|---|---|
| **环境安装** `hpr_install` | `serial`，`ncpus=1:mem=8gb` | 02:00:00 | 计算节点上：Miniforge 到 `$HOME/miniforge3`（安装包由作业下载；受限时在登录节点 `curl -o` 下载后 `MINIFORGE_SH=` 传入）→ `env/install_env.sh`（第三批锁定 538 个 conda 包 + 2 个 PyPI 包，缓存在 `/hpctmp/<用户>/hpr/conda_pkgs_cache`）→ `env_check.py` → 解包代码到包目录 `./repo`（= `COMMIT`）→ 登录节点预检各节 | `INSTALL_STATUS.txt`：`ENV_CHECK:key_all_equal=true`、`REPO:<提交>`、`PREFLIGHT:exit=0` |
| **冒烟** `hpr_smoke56`（步骤 D） | `parallel`，`ncpus=17:mem=32gb` | 04:00:00 | 作业体依次以 `JOB_MODE=smoke56` 运行 F1 体、F2 体、批级体（同一代码路径）：`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`，标签 `SMOKE_TEST_ONLY`，运行目录 `runs/smoke56`；两次 Gurobi 会话串行（间隔 ≥ 330 s）；计算节点 `curl https://token.gurobi.com` 只记 HTTP 状态码 | `SMOKE_STATUS.txt`：两运行 optimal、ACCEPTED_LAYER2、后处理与批级 exit 0、`DONE`；目标值与本机 H4 演练值（一体化 340,661,983,874.5359 / 不互联 352,091,303,417.9458 EUR）相对偏差 ≤ 1e-6（跨机器只记录差异，不要求逐位） |
| **全尺寸 BUILD_ONLY** `hpr_build_only_f1`（步骤 D2，用户 2026-10-27 补充） | `parallel`，`ncpus=48:mem=300gb` | 02:30:00（估计 70 min × 2：预检 5 min + 进程 1 ≤ 60 min + 写入测速与清理 5 min） | `BUILD_ONLY=1 bash run_batch4.sh --only F1`（无 `--auth`、无许可）：只跑进程 1——完整 2920×3h v2 一体化网络的构建、LP 数组导出、LP 文件写出；运行目录 `runs/build_only_f1`（与正式目录隔离）；记录峰值内存（GNU time）、LP 文件字节数、构建秒数（`lp.build_seconds`）与写出秒数（`split.write_seconds`）、`/hpctmp` 写入速度（LP 字节 / 写出秒数，另加 1 GiB `dd` 顺序写测速）、cgroup 可见性；结束后删除 LP 文件 `split/problem.lp`（数组 `lp/` 保留，约 6.4 GB，60 天后清除） | `BUILD_ONLY_STATUS.txt`：`BUILD_CHECK_F1 passed`、`LP_DELETED`；参考预期：峰值 72–92 GiB（B4P 外推）、LP 5.1–5.4 GB、≤ 3,600 s。**结果只用于核对估计，不改变第 2–3 节的登记值**；峰值 > 150 GiB 或构建 > 3,600 s（超时安全停止）→ 先报告审阅端再做步骤 E；峰值 100–150 GiB → 批级作业（120 GiB）补做后处理（重建 LP，峰值与进程 1 同量级）可能不够，由审阅端提出是否提高 `hpr_batch` 内存（登记值变更，用户决定）后再做步骤 E（审查 F-16） |

- 三个测试作业都可在 2026-10-29 18:00 维护前完成，也可在 11-02 17:00 之后做（用户决定）。
- 测试作业用到的 `TRUNCATE` / `ALLOW_UNREGISTERED` / `BUILD_ONLY` 只在对应作业体内导出；**正式作业（`JOB_MODE=formal`）在这些开关残留、`--auth` 缺失、运行目录含测试残留（`.cond` 为 `build_only` / 标签 `SMOKE_TEST_ONLY`）时拒绝**（退出码 2，不写 STATUS）；`run_batch4.sh` 自身的拒绝（测试钩子、未登记时限、`--auth` 与无求解模式并存）保持不变。

## 10. 登记常数一览（检查单 H-P3 的比对清单）

| 常数 | 值 | `b4_batch4.py` | `run_batch4.sh` | 作业脚本 / `make_pbs.sh` | 预检 |
|---|---|---|---|---|---|
| 网络 SHA256 F1 / F2 | `08879f0b…` / `d90ca992…` | `REGISTERED_SHA` | 阶段 0 `base-check` | 包清单 | `networks` 节 |
| 网络字节 F1 / F2 | 63,873,447 / 63,202,193 | `REGISTERED_BYTES` | 同上 | — | 同上 |
| 构建提交 | `72083fde…` | `BUILD_COMMIT` | 同上 | — | 同上 |
| TimeLimit | 864,000 | `TIME_LIMIT_S` | `R_TL` | `JOB_TIME_LIMIT_S`（只用于记录） | `profile` 节 `R_TL` |
| 进程 2 墙钟 | 871,200 | `WALL_CAP_S` | `R_WALL` | — | — |
| 许可间隔 | 330 | `LICENCE_GAP_S` | `R_GAP` | — | — |
| 求解方式 | split | — | `R_MODE` | `SOLVE_MODE=split` | `code` 节 |
| 进程 1 / 3 超时 | 3,600 / 32,400 | — | `BUILD_TIMEOUT_S` / `ASSIGN_TIMEOUT_S` 缺省 | — | — |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | — | `POST_TIMEOUT_S` / `PACK_TIMEOUT_S` 缺省 | — | — |
| 内存止损分数 | 0.80 | `MEMORY_STOP_FRACTION` | 缺省读取 | — | `code` 节 |
| 早期测速分数 / 迭代参考 | 0.80 / 450、250 | `PROJECTION_FRACTION`、`RUNS[*].iterations_reference` | `ITERS_REF` | — | `code` 节 |
| F2 等待 F1 启动上限 | 7,200 | `WAIT_START_MAX_S` | `WAIT_START_MAX_S` 缺省 | F2 作业 `WAIT_START_OF=F1` | — |
| PBS F1 | parallel / 48 / 300gb / 255:00:00 | `HPC_JOBS["F1"]` | — | `hpr_f1.pbs` | `resources` 节下限 = 申请值 |
| PBS F2 | parallel / 48 / 250gb / 257:00:00 | `HPC_JOBS["F2"]` | — | `hpr_f2.pbs` | 同上 |
| PBS 批级 | parallel / 12 / 120gb / 12:00:00 | `HPC_JOBS["batch"]` | — | `hpr_batch.pbs` | — |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00 | `HPC_JOBS["smoke56"]` | — | `hpr_smoke56.pbs` | — |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 02:30:00 | `HPC_JOBS["build_only_f1"]` | — | `hpr_build_only_f1.pbs` | — |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `HPC_JOBS["install"]` | — | `hpr_install.pbs` | — |
| 后处理并存内存条件 | 100 GiB | — | `POST_MEM_NEED_GIB` 缺省 | — | — |

## 11. 路径约定（HPC）

| 内容 | 位置 |
|---|---|
| 包目录（= `PBS_O_WORKDIR`，作业从这里提交） | `/hpctmp/<用户>/hpr/` |
| 代码（预检 `sha` 节 / 安装作业解包） | `/hpctmp/<用户>/hpr/repo/`（`.package_commit` = `COMMIT`） |
| conda 环境 | `$HOME/miniforge3/envs/pypsa-earth`（家目录 20 GB 配额，约 3.3 GiB） |
| conda 包缓存、pip 缓存 | `/hpctmp/<用户>/hpr/conda_pkgs_cache`、`/hpctmp/<用户>/hpr/tmp` |
| 运行目录 | 正式 `runs/batch4/`；冒烟 `runs/smoke56/`；BUILD_ONLY `runs/build_only_f1/`（均在包目录下） |
| 结果包 | `runs/batch4/results_{light,full}_final_*.tar.gz`（+ `.sha256`） |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600`，用户自行放置；只经 `GRB_LICENSE_FILE` 引用 |
| 作业日志 | `/hpctmp/<用户>/hpr/<作业名>.o<作业序号>`（PBS 把 `-j oe` 的输出放回提交目录；作业脚本不设 `-o`） |

## 12. 由准备端确定、请审阅确认的取值（不在 B1–B4 内）

1. walltime 的构成（第 2 节）：F1 255 h、F2 257 h；逐运行后处理估计 65 min、作业体开销 30 min、F2 等待上限 2 h。
2. 批级作业资源：parallel 12 核 / 120 GB / 12 h（为可能的后处理补做留 ≥ 100 GiB）。
3. 冒烟作业资源：parallel 17 核 / 32 GB / 4 h；两运行串行。
4. 安装作业：serial 1 核 / 8 GB / 2 h；在计算节点安装（登录节点 30 min CPU 限制）。
5. 正式作业不做预检 `licence` 节（避免多一个 WLS 会话）；许可可用性由冒烟作业证明。
6. 停批信号跨作业共享（第 7 节第 2 项）：F1 的 `STOP` / `STOP_SAFE` 会阻止尚未开始求解的 F2。
7. HPC 冒烟与本机演练的目标值比较只记录相对偏差（跨机器浮点差异），不作为验收。
