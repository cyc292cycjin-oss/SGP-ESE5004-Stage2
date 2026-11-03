# HPC 正式运行计划 v3（RUN_PLAN_HPC_V3）——F1–F4，2920×3h v3 网络，NUS Atlas（PBS Pro），每个运行一个作业 + 一个批级作业

**版本：** V3 HPC v1，2026-11-04（SGT）。依据 `V3_HPC_PACKAGE_INSTRUCTION.md`（台账 V14，SHA256 `29dc0b0f…`）第 5 节、审阅决定 `V3_REVIEW_DECISIONS_INDEP.md`（第 186、187 项）、v2 模板 `work/p1_hpr_20261027/RUN_PLAN_HPC.md`（HPR v1，用户 B1–B4 与 D2 补充）。
**状态：** 本文件在任何 F1–F4 的 HPC 求解之前提交。第 2 节的 TimeLimit、walltime、进程 1 超时与批级 walltime 是 **PROPOSED**，由审阅端与用户决定后才登记（登记 = 定义文件 `limits_status` 改为 `REGISTERED` 并重新打包）；登记之前正式作业与提交脚本都拒绝运行。其余各节沿用 v2 已登记的规则，按四个运行写明。
**单一来源：** 定义文件 `batch_def/BATCH_DEF_2920x3h_v3hpc.json`（包内 `BATCH_DEF.json`）→ `scripts_project/b4_batch4.py`（运行表、登记网络、时限、作业表、冒烟期望值）→ `run_batch4.sh`（经 `b4_batch4.py hpc-plan` / `runmeta` 读取）、`preflight.sh`、`hpc/make_pbs.sh` 生成的作业脚本、`hpc/hpr_submit.sh`；`hpc/hpr_consistency.py` 把本文件与这些来源逐项比对（包内 `HPC_CONSISTENCY.json`，必须 `ALL_CONSISTENT` 才出包）。
**模型、网络、成本表、求解档案参数、GATES_V6 / C1 阈值一律不改。**

---

## 1. 运行

| 编号 | 对 | 运行 | 包内网络文件 | 字节 | SHA256 | 情景 | 成本表 | 档案 | 作用 |
|---|---|---|---|---:|---|---|---|---|---|
| F1 | A | 一体化（S-A） | `networks/integrated_2920_3h_unsolved.nc` | 72,050,034 | `8b5fd663d6c783e9af549bec8394700c9b4b5785b1ec809ab7d8e668d78657ef` | integrated | `networks/integrated_costs_active_research.csv` | `formal_barrier_1e6_t16` | c(N)、Owen 分摊、B6 基准 |
| F2 | A | `no_new_xb`（S-A） | `networks/no_new_xb_2920_3h_unsolved.nc` | 71,411,694 | `e2837e4ada978e0d05fc04108d7ceb99567e41c33b6837ab4447be74bdd918b7` | no_new_xb | 同上 | 同上 | B6 = F2 − F1 |
| F3 | B | 一体化，EV 车队代理 ×0.5 | `networks/integrated_ev05_2920_3h_unsolved.nc` | 72,050,068 | `c4eb7c44a54175ba06d7d60d4926cb095fc0ec603eced4ff28aecd8493bcb063` | integrated | 同上 | 同上 | 第 186 项敏感性 |
| F4 | B | `no_new_xb`，EV 车队代理 ×0.5 | `networks/no_new_xb_ev05_2920_3h_unsolved.nc` | 71,411,730 | `0bbe235e08654f566afe8f94eb2299a9ed1a8bb1f791520f8206449e02c3bac7` | no_new_xb | 同上 | 同上 | B6 = F4 − F3 |

- **两对：** A = F1 / F2，B = F3 / F4；B6 与 M12 受益按对计算，批级汇总另给两对比较（ΔB6、每个参与者的 Owen 受益与符号，只描述，不判定）。
- **构建：** 分支 `codex/v3-hpc-20261104` 提交 `a1ef782b8c8f0b6cb0ef67b3fe66a7493865e9b7`（dirty 0，`PYTHONHASHSEED=0`），规则 `V3_RULES.md` 第 12 节，登记与核对 `RUN_PLAN_V3.md` 第 24.1 节（逐元素核对全部通过，静态检查通过）。回执：`integrated_BUILD_RECEIPT.json`（F1）、`integrated_ev05_BUILD_RECEIPT.json`（F3）、`no_new_xb_2920_3h_VARIANT_RECEIPT.json`（F2 ← F1）、`no_new_xb_ev05_2920_3h_VARIANT_RECEIPT.json`（F4 ← F3，定义文件里 F4 的 `parent` 为 `integrated_ev05`）。四个运行共用一张成本表（两次构建逐字节相同，`7cee9c1a…`）。**365×24h 网络不入包**（预检发现即失败）。
- **档案（不改）：** `formal_barrier_1e6_t16`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200；`--scaling on`。
- **求解方式（不改）：** `SOLVE_MODE=split`：进程 1 构建（无许可）→ 进程 2 `b4_split_solve.py`（唯一的 Gurobi 进程，读入后删除 LP 文件）→ 进程 3 映射与导出（无许可）。
- **一次求解：** 每个运行只求解一次；不重试、不改参数、不热启动；非 optimal 照实记录并按第 7 节分级。

## 2. 时限与 PBS walltime

### 2.1 外推（INFERENCE，方法与数据）

**数据：** (1) B4P 对 v2 F1 2920×3h 的外推（`RUN_PLAN_B4.md` 第 4 节，8470Q、T16）：每次迭代 135 / 580 / 1,127 s，迭代 253 / 350 / 465 次；F2 每次迭代 31 / 150 / 218 s。(2) v3 / v2 在 365×24h 同档案、同机型（AutoDL 8470Q 25 核）上的每次迭代：一体化 V1 21.3–24.4 s 对 DFX v2 V1 16.4 s，比值 **1.30–1.49**；`no_new_xb` V2 10.5–12.9 s 对 v2 V2 8.3 s，比值 1.27–1.55。(3) v3 迭代数：一体化 56 时段 80–83、365×24h 146–186；`no_new_xb` 56 时段 66–77、365×24h 95–111（56 时段 E2 曾两次 suboptimal）。(4) D2（Atlas，v2 F1 全尺寸 BUILD_ONLY）：进程 1 合计 2,382 s（构建 1,359.9 s + 写出 773.2 s），峰值 91.99 GiB，节点 AMD EPYC 7R13 48 核。(5) v3 LP 比 v2 列 +4.84 %、行 +4.07 %、非零约 +3.4 %（`RUN_PLAN_V3.md` 第 24.1 节）。

**方法：** barrier 用时 = v2 每次迭代（B4P）× v3 / v2 每次迭代比 × v3 迭代数 × CPU 因子（Atlas EPYC 7R13 对 8470Q：1.0 / 1.3 / 1.6，为假设；D2 的单线程构建比 B4P 的云端估计慢约 1.1–1.7 倍，EPYC 7R13 无 AVX-512）。v3 2920×3h 迭代数取 365×24h 实测为下端，按 56 → 365 的增长外推到 2920 为上端（一体化约 350，`no_new_xb` 约 165，后者再按 E2 末段发散历史放到 250）。

| 量 | F1、F3 一体化（低 / 中 / 高） | F2、F4 `no_new_xb`（低 / 中 / 高） |
|---|---|---|
| 每次迭代（8470Q T16） | 175 / 812 / 1,679 s | 39 / 210 / 338 s |
| 迭代数 | 160 / 250 / 350 | 111 / 165 / 250 |
| barrier（8470Q） | 7.8 / 56 / 163 h | 1.2 / 9.6 / 23 h |
| barrier（Atlas，× 1.0 / 1.3 / 1.6） | **7.8 / 73 / 261 h** | **1.2 / 12.5 / 38 h** |
| 预求解 + 排序（B4P 1,400–5,700 s × CPU） | 0.4–2.5 h | 0.2–1.5 h |
| 高高情形（迭代 465、每次 1,679 s、× 1.6） | 347 h | — |

### 2.2 取值

| 量 | 值（s） | 依据 |
|---|---|---|
| 登记状态 | **PROPOSED** | 审阅端与用户决定后改为 REGISTERED 并重新打包；PROPOSED 时 `hpr_job.sh`（formal）、`hpr_submit.sh`、`run_batch4.sh`（正式运行）都拒绝 |
| **TimeLimit（PROPOSED）** `R_TL` / `TIME_LIMIT_S` | **1,296,000**（360 h），F1–F4 相同 | 覆盖第 2.1 节 F1 高值 261 h + 预求解 2.5 h 并留约 37 % 余量，也覆盖高高情形 347 h；F2、F4 远低于此（高值 38 h），统一取值只增加其 walltime 申请。v2 登记值 864,000 s（240 h）低于 F1 高值，高值情形会在约 20 次迭代后被早期测速止损（第 5 节）后由用户决定以更长时限重开 |
| **进程 2（Gurobi）墙钟** `R_WALL` / `WALL_CAP_S` | **1,303,200** = TimeLimit + 7,200 | 沿用 v2 的余量 2 × 3,600 s（LP 读入 ≤ 154 s、解数组写出 ≤ 1,800 s） |
| 进程 1 超时 `BUILD_TIMEOUT_S` | **7,200** | **PROPOSED。** D2 用了 3,600 s 的 66 %（2,382 s）；v3 约大 5 % → 约 2,500 s；`/hpctmp` 写入约 7–17 MB/s 会波动；按 B4P 的约 3 倍余量取 7,200 s（v2 3,600 s 只剩 1.44 倍） |
| 进程 3 超时 `ASSIGN_TIMEOUT_S` | 32,400 | 不改（B4P 2.2–3 h × 3）；按 D2 的单线程速度估计 5–7 h，余量 1.3–1.8 倍，见第 12 节可选提议 |
| 后处理单步超时 `POST_TIMEOUT_S` | 10,800 | 不改 |
| 打包超时 `PACK_TIMEOUT_S` | 7,200 | 不改 |
| 逐运行后处理估计 | 3,900（65 min） | 不改（B4P 6.1） |
| 运行器启动后首次 Gurobi 的间隔 | 330 | 不改（`R_GAP`，WLS 令牌 ≥ 5 min） |
| 作业体开销估计 | 1,800 | 不改 |
| 等待启动的上限 `WAIT_START_MAX_S` | 7,200 | 不改：F2 等 F1 的 Gurobi 启动；F3、F4 等启动锁与间隔（第 4 节） |
| **PBS walltime F1** | **1,353,600**（`376:00:00`） | **PROPOSED。** 330 + 7,200 + 1,303,200 + 32,400 + 2 × 3,900 + 1,800 = 1,352,730 → 376 h；≤ 720 h |
| **PBS walltime F2** | **1,360,800**（`378:00:00`） | **PROPOSED。** 1,352,730 + 7,200（等待上限）= 1,359,930 → 378 h |
| **PBS walltime F3** | **1,360,800**（`378:00:00`） | **PROPOSED。** 同 F2（等待启动锁与间隔的上限） |
| **PBS walltime F4** | **1,360,800**（`378:00:00`） | **PROPOSED。** 同 F2 |
| PBS walltime 批级作业（PROPOSED） | 172,800（`48:00:00`） | 四个运行；正常为分钟级，若某运行的后处理在其作业内未完成，`POST_ONLY=1` 每运行补做最多 4 步 × 10,800 s（v2 两个运行 12 h） |

早期测速（第 5 节）的止损线 = 0.80 × 1,296,000 = **1,036,800 s**（288 h）。

**整批时长：** F1 与 F2 同时运行，F3 在 F1 结束后、F4 在 F2 结束后开始，所以总时长约为 max(F1 + F3, F2 + F4) 加排队（D2 约 13 h）。按第 2.1 节：中值约 2 × 75 h ≈ 6–7 天；高值约 2 × 265 h ≈ 22 天；全部用满时限约 31 天，仍在 `/hpctmp` 60 天自动清除之内（运行中文件持续改动），但每个运行结束后应先下载其导出（第 8 节）。

## 3. PBS 资源

| 作业 | 队列 | 资源 | walltime | 内存配额 `MEM_QUOTA_GIB` | 核数 `CORES` | 依赖 |
|---|---|---|---|---|---|---|
| **F1** `hpr3_f1` | `parallel` | `select=1:ncpus=48:mem=300gb` | 376:00:00 | **300** | 48 | 无 |
| **F2** `hpr3_f2` | `parallel` | `select=1:ncpus=48:mem=250gb` | 378:00:00 | **250** | 48 | `-W depend=after:<F1 作业号>`（F1 开始执行后才可调度） |
| **F3** `hpr3_f3` | `parallel` | `select=1:ncpus=48:mem=300gb` | 378:00:00 | **300** | 48 | `-W depend=afterany:<F1>`（F1 结束后，无论退出码） |
| **F4** `hpr3_f4` | `parallel` | `select=1:ncpus=48:mem=250gb` | 378:00:00 | **250** | 48 | `-W depend=afterany:<F2>` |
| **批级** `hpr3_batch` | `parallel` | `select=1:ncpus=12:mem=120gb` | 48:00:00 | 120 | 12 | `-W depend=afterany:<F3>:<F4>`（F3、F4 结束后；它们又在 F1、F2 之后，所以四个都结束） |

- 内存沿用 v2：F1、F3 300 GB，F2、F4 250 GB（指令第 5.5 条）；止损线 80 %：F1、F3 **240 GiB**，F2、F4 **200 GiB**。v3 进程 2 峰值外推（B4P 值 × 1.3，因 v3 每次迭代多约 49 % 运算、因子非零约多 30 %）：F1、F3 117 / 161 / 208 GiB，F2、F4 88 / 135 / 194 GiB；1.25 倍检查（检查单 H-P4）：300 ≥ 260、250 ≥ 242.5。F2、F4 的高值离止损线只有 3 %，见第 12 节可选提议。
- **核数：** 任何时刻最多两个正式作业（F1 与 F2；之后 F3 与 F2、F1 与 F4 或 F3 与 F4）= 96 核 = `parallel` 每用户合计上限；批级 12 核在四个都结束后才运行。每用户 ≤ 8 个作业：5 个。
- 300 / 250 GB ≤ 约 360 GB，可落在 32 台 367 GB 节点；单作业 ≤ 540 GB、walltime ≤ 720 h。
- 不加 `-P`；无 `-V`（测试开关由预检 `guards` 节再查一次）。
- **批级作业只设一个，排在四个运行之后**（指令第 5.4 条允许的两种之一）：F3、F4 各 48 核在跑时，"第 A 对"的批级作业受每用户 96 核的上限，本来就要等 F3 或 F4 结束才能调度，单独设它几乎换不来时间，却要给运行器加按对选择的逻辑。F1、F2 的逐运行后处理（临时 C1、账本、M12、Owen、GATES_V6 临时标签、导出）在各自作业内完成，结束后即可按第 8 节先下载。

## 4. 许可会话（任意时刻 ≤ 2 个 Gurobi 会话，会话启动间隔 ≥ 330 s）

- **≤ 2 个会话：** F1 与 F3 串行（`afterany`），F2 与 F4 串行，所以同时最多两个求解；运行器另在启动锁内核对共享运行目录中"已启动未结束"的其他求解少于 2 个，否则等待（上限 `WAIT_START_MAX_S`，超时 `STOP_SAFE:START_LOCK`）。
- **F2 等 F1（沿用 v2 两重机制）：** `qsub -W depend=after:<F1>`，运行器 `--only F2` 以 `WAIT_START_OF=F1` 运行：F2 的进程 2 等到 `F1/.solve_start` 距今 ≥ 330 s（或 F1 已结束求解 / 未经 Gurobi 就结束）。
- **启动锁（新增，所有运行）：** 每个运行在启动 Gurobi 前用原子 `mkdir runs/batch4/.gurobi_start_lock` 取得锁（跨节点也有效），锁内等到距其他运行的每次 Gurobi 启动、任何运行的 Gurobi 结束与本运行器启动都 ≥ 330 s，且其他在跑的 Gurobi 少于 2 个，写出 `.solve_start` 后立即释放。这样 F3 与 F2、F3 与 F4、F4 与 F1 的启动无论何时重合都保持间隔。锁不会被自动打破：若持锁作业在这几分钟内被杀，其他运行等满 `WAIT_START_MAX_S` 后 `STOP_SAFE:START_LOCK`，由用户确认没有运行器持锁后删除该目录（操作指南第 7 节）。
- 正式作业不运行预检的 `licence` 节；作业开头只检查许可文件存在与权限 600。许可可用性由冒烟作业验证。
- **F1–F4 运行期间（从第一个正式作业开始到最后一个求解结束），本机与 AutoDL 都不得启动 Gurobi 会话**（同一 WLS 许可）。
- 许可只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；绝不进入包、代码、作业脚本、日志、结果包；导出日志经过滤；打包前检索许可特征串，命中即拒绝。

## 5. 止损与保护（沿用 v2，参考迭代数按 v3 重登记）

1. **内存止损 → `STOP_SAFE:MEMORY:<编号>`：** 作业 cgroup 匿名内存（不可见时为进程组 RSS 之和）超过配额的 **80 %** → 终止该 Gurobi 进程组，不再启动任何求解。
2. **早期测速 → `STOP_SAFE:PROJECTION:<编号>`：** 第 20 次 barrier 迭代后，第 11–20 次平均耗时 × 参考迭代数 + 已用时间 > 0.80 × TimeLimit → 终止。**参考迭代数（v3 登记）：F1、F3 350；F2、F4 250。** 方法：v2 的规则是"取同模型的迭代数区间上端"（第三批 365×24h 253–465 → 450）。v3 的区间按第 2.1 节：一体化 160–350、`no_new_xb` 111–250，各取上端。v2 的 450 / 250 偏高只会让止损更宽松；v3 改为 350 后，按 TimeLimit 1,296,000 s，F1 只有在每次迭代超过约 2,800 s（第 2.1 节高值 1,679 s × 1.6 = 2,687 s 之上）时才止损。
3. **墙钟：** 进程 2 到 1,303,200 s 终止整个进程组。
4. **求解结果先落盘；** 进程 3 的异常记入回执，不改变终止状态。
5. **不重试、不改参数、不热启动。** `SoftMemLimit` 不作为登记参数。
6. **P1 探针不使用**（每个运行一个作业）；单机批次模式在四个运行时拒绝运行。

## 6. 中断与重开

- 资源原因中断的运行：从头重开须用户明确授权，登记为"资源原因的重新开始"（新的运行目录），不算重试。
- 续跑：同一运行目录再次提交同一作业 → 已结束的跳过（`SKIP_ENDED`）；已开始未结束 → `STOP_SAFE:INTERRUPTED_<编号>`。
- **维护重叠检查：** 提交前确认登录欢迎信息中没有与预计运行期重叠的维护通知（F1 + F3 最长约 31 天）；有就停下报告。
- `/hpctmp` 60 天未改动自动清除：见第 8 节。
- 启动锁残留：见第 4 节。

## 7. 验收、分级与后处理

1. **验收 = GATES_V6 + C1（阈值不改）：** 先用缺省参照给出临时判定（`V6_ACCEPTANCE_PROVISIONAL.json`），批级作业用 F1、F2 的账本生成本批参照 `BATCH_REFERENCE.json` 并重评四个运行（F3、F4 同用 F1、F2 的本批参照，与第一次筛查中 V3–V5 用 V1、V2 参照相同）。
2. **分级与停批：** G2 不通过 → `STOP`；无返回解或 C1 (a) 不通过 → `UNUSABLE` 并 `STOP`，**四个运行都适用**；只有 C1 (b)/(c) 不通过 → 不停。停批 = 共享运行目录中的 `STOP` / `STOP_SAFE` 让尚未进入进程 2 的运行放弃启动（`NOT_STARTED_<编号>`），例如 F1 不可用时 F3 不再求解；已在求解的运行跑完并后处理。
3. **逐运行后处理在各自作业内完成**（违反量 → C1 临时 → M12 → Owen 对偶形式 → GATES_V6 → 分级 → 导出 `export/<编号>/`）。
4. **批级作业**（`POST_ONLY=1`，无许可）在四个运行都落定后：补做缺失的后处理 → `BATCH_REFERENCE.json` → C1 / Owen 重评、GATES_V6 终标签 → **B6 = F2 − F1（第 A 对）与 B6 = F4 − F3（第 B 对）**（`gate_b6_cost`）与分国账本差 → **Owen 对偶形式受益按对**（`M12_BENEFIT/`、`M12_BENEFIT_B/`）→ **两对比较**（ΔB6、每个参与者两对的受益与符号是否相同；只描述，Owen 符号的稳健性由审阅端判断）→ 与 `REFERENCE_VALUES.json` 的对比（v3 365×24h 重跑与第一次筛查 V1 / V2、两次本机 56 时段冒烟；只描述）→ `BATCH4_SUMMARY.json / .md` → 结果包（light / full）。任一运行未验收：照常重评与汇总，结果包标记 `halted`，退出码 3。
5. "落定" = 已结束（`.ended`），或运行目录有 `STOP` / `STOP_SAFE` 且该运行从未开始求解。已开始未结束的运行永远不算落定，批级作业拒绝运行（`not_ready`）。

## 8. 结果回收

- **每个运行结束后**（`hpc/hpr_status.sh` 显示 `ended`）：用户下载该运行的导出 `runs/batch4/export/<编号>/`（单路一个 `tar` 打包 + `sha256sum`，见操作指南第 6 节），不必等批级作业。
- 批级作业结束后：`runs/batch4/results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与各自的 `.sha256`（停批时 `*_halted_*`）。用户尽快下载到 `D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results\`，**单路**，本机核对 SHA256（PowerShell `Get-FileHash`）。
- LP / 解数组（约 4 × 7.8 GB）留在 `/hpctmp`（`ARRAYS_MANIFEST.json` 登记 SHA256），60 天未改动自动清除；需要时另行下载。

## 9. 测试作业（登记为测试，不属于正式运行）

| 作业 | 队列 / 资源 | walltime | 内容 | 判据 |
|---|---|---|---|---|
| 环境安装 `hpr3_install`（通常不需要） | `serial`，`ncpus=1:mem=8gb` | 02:00:00 | 同 v2；HPC 上已有环境，登录预检 `env` 节 key packages 一致（284 / 284）即复用，不提交本作业 | `INSTALL_STATUS.txt` |
| **冒烟** `hpr3_smoke56`（正式提交前必须 PASS） | `parallel`，`ncpus=17:mem=32gb` | 04:00:00 | 作业体依次以 `JOB_MODE=smoke56` 运行 F1 体、F2 体、批级体：`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`，标签 `SMOKE_TEST_ONLY`，运行目录 `runs/smoke56`；两次 Gurobi 会话串行（间隔 ≥ 330 s）；F3、F4 与 F1、F2 走同一代码路径，不进冒烟 | `SMOKE_STATUS.txt`：F1、F2 optimal、ACCEPTED、后处理与批级 exit 0、`DONE`；目标值与本机冒烟（`RUN_PLAN_V3.md` 第 25 节：F1 329,705,566,422.23596、F2 342,268,691,464.4567 EUR）相对偏差 ≤ 1e-6（跨机器只记录差异） |
| 全尺寸 BUILD_ONLY `hpr3_build_only_f1`（可选） | `parallel`，`ncpus=48:mem=300gb` | 02:30:00 | 同 v2 的 D2：只跑进程 1，记录峰值、LP 字节、构建与写出秒数 | `BUILD_ONLY_STATUS.txt`：`BUILD_CHECK_F1 passed`；参考：峰值约 96 GiB、LP 约 5.5 GB、≤ 2,700 s |

- 测试作业的开关只在对应作业体内导出；正式作业在开关残留、`--auth` 缺失、运行目录含测试残留时拒绝（退出码 2）。
- 冒烟作业的两次 Gurobi 会话也要遵守第 4 节最后一条的同期禁止。

## 10. 登记常数一览（检查单 H-P3 的比对清单）

| 常数 | 值 | 来源 |
|---|---|---|
| 登记状态 | **PROPOSED** | 定义文件 `limits_status` |
| 网络 SHA256 / 字节 F1–F4 | 第 1 节 | 定义文件 `registered_sha` / `registered_bytes` |
| 构建提交 | `a1ef782b8c8f0b6cb0ef67b3fe66a7493865e9b7` | 定义文件 `build_commit` |
| TimeLimit / 进程 2 墙钟 / 间隔 | 1,296,000 / 1,303,200 / 330 | 定义文件 `limits`（`run_batch4.sh` 经 `hpc-plan` 读取） |
| 求解方式 | split | `run_batch4.sh` `R_MODE`、作业体 `SOLVE_MODE=split` |
| 进程 1 / 3 超时 | 7,200 / 32,400 | 定义文件 `limits` |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | 定义文件 `limits` |
| 内存止损分数 | 0.80 | `b4_batch4.py` `MEMORY_STOP_FRACTION`、运行器缺省 |
| 早期测速分数 / 迭代参考（F1 / F2 / F3 / F4） | 0.80 / 350、250、350、250 | `b4_batch4.py` `PROJECTION_FRACTION`；定义文件 `iterations_reference`（运行器经 `runmeta` 读取） |
| 等待启动上限 | 7,200 | 定义文件 `limits` |
| 后处理并存内存条件 | 100 GiB | `b4_batch4.py` `POST_MEM_NEED_GIB`、运行器缺省 |
| PBS F1 | parallel / 48 / 300gb / 376:00:00 | 定义文件 `hpc_jobs` → `pbs/hpr3_f1.pbs` |
| PBS F2 | parallel / 48 / 250gb / 378:00:00 | `pbs/hpr3_f2.pbs`；`WAIT_START_OF=F1` |
| PBS F3 | parallel / 48 / 300gb / 378:00:00 | `pbs/hpr3_f3.pbs` |
| PBS F4 | parallel / 48 / 250gb / 378:00:00 | `pbs/hpr3_f4.pbs` |
| PBS 批级 | parallel / 12 / 120gb / 48:00:00 | `pbs/hpr3_batch.pbs` |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00 | `pbs/hpr3_smoke56.pbs` |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 02:30:00 | `pbs/hpr3_build_only_f1.pbs` |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `pbs/hpr3_install.pbs` |
| 依赖 | F2 `after:F1`、F3 `afterany:F1`、F4 `afterany:F2`、批级 `afterany:F3:F4` | 定义文件 `hpc_jobs` → `hpc/hpr_submit.sh` |
| 两对 | A：F1 / F2；B：F3 / F4 | 定义文件 `pair` |

## 11. 路径约定（HPC）

| 内容 | 位置 |
|---|---|
| 包目录（= `PBS_O_WORKDIR`，作业从这里提交） | `/hpctmp/<用户>/hpr3/`（与 v2 的 `/hpctmp/<用户>/hpr/` 分开） |
| 代码 | `/hpctmp/<用户>/hpr3/repo/`（预检 `sha` 节解包，`.package_commit` = `COMMIT`） |
| conda 环境 | `$HOME/miniforge3/envs/pypsa-earth`（HPR 步骤已装；预检 `env` 节核对） |
| 运行目录 | 正式 `runs/batch4/`；冒烟 `runs/smoke56/`；BUILD_ONLY `runs/build_only_f1/` |
| 结果包 | `runs/batch4/results_{light,full}_final_*.tar.gz`（+ `.sha256`） |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600`，用户自行放置 |
| 作业日志 | `/hpctmp/<用户>/hpr3/<作业名>.o<作业序号>` |

## 12. PROPOSED 取值与可选提议（审阅端与用户决定）

| 项 | v2 登记值 | 提议（PROPOSED） | 理由 |
|---|---|---|---|
| TimeLimit（F1–F4） | 864,000 s（240 h） | **1,296,000 s（360 h）** | 第 2.1 节：F1、F3 高值 261 h 超过 240 h，高高情形 347 h；止损线随之为 288 h |
| PBS walltime F1 / F2–F4 | 255 h / 257 h | **376 h / 378 h** | 由 TimeLimit 与各项开销求和（第 2.2 节）；≤ 720 h |
| 进程 1 超时 | 3,600 s | **7,200 s** | D2 已用 66 %，v3 约大 5 %；按约 3 倍余量 |
| 批级 walltime | 12 h | **48 h** | 四个运行的补做上限 |
| 可选：F2、F4 内存 | 250 GB | 300 GB | 高值 194 GiB 离止损线 200 GiB 只有 3 %；300 GB 仍落在 367 GB 节点；不提议时保持 250 GB |
| 可选：进程 3 超时 | 32,400 s | 43,200 s | 按 D2 单线程速度估计 5–7 h，余量 1.3–1.8 倍；walltime 相应 +3 h |
| 可选：F2、F4 单独 TimeLimit | — | 864,000 s | 高值 38 h，240 h 已足够；需要运行器支持按运行的时限（现在没有），不建议本批做 |

**登记方式：** 用户与审阅端确定取值后，下一步改定义文件（`limits_status: REGISTERED`，必要时改数值）与本文件第 2、3、10、12 节，重新打包（`hpc_v3/make_hpc_package_v3.sh`）与干跑，再上传。

## 13. 同期禁止

HPC 正式求解期间（第一个正式作业开始到最后一个求解结束），本机与 AutoDL 不调用 Gurobi（WLS 许可共用）；冒烟作业期间同样。
