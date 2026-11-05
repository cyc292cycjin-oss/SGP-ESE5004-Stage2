# HPC 正式运行计划 v3（RUN_PLAN_HPC_V3）——F1–F4，2920×3h v3 网络，NUS Atlas（PBS Pro），每个运行一个作业 + 一个批级作业

**版本：** V3 HPC v1，2026-11-04（SGT）。依据 `V3_HPC_PACKAGE_INSTRUCTION.md`（台账 V14，SHA256 `29dc0b0f…`）第 5 节、审阅决定 `V3_REVIEW_DECISIONS_INDEP.md`（第 186、187 项）、v2 模板 `work/p1_hpr_20261027/RUN_PLAN_HPC.md`（HPR v1，用户 B1–B4 与 D2 补充）。
**状态：** 本文件在任何 F1–F4 的 HPC 求解之前提交。第 2 节的 TimeLimit、walltime、进程 1 超时与批级 walltime 原为 PROPOSED（V3 HPC v1），**2026-11-04 由审阅端按用户授权决定并登记**（`V3_HPC_UNATTENDED.md` 第 1 节；推导见第 14 节）：定义文件 `limits_status` 为 `REGISTERED`，包按登记值重新打出。第 2.2、3、5、10 节已改为登记值，第 12 节保留原 PROPOSED 取值作为记录。其余各节沿用 v2 已登记的规则，按四个运行写明。
**单一来源：** 定义文件 `batch_def/BATCH_DEF_2920x3h_v3hpc.json`（包内 `BATCH_DEF.json`）→ `scripts_project/b4_batch4.py`（运行表、登记网络、时限、作业表、冒烟期望值）→ `run_batch4.sh`（经 `b4_batch4.py hpc-plan` / `runmeta` 读取）、`preflight.sh`、`hpc/make_pbs.sh` 生成的作业脚本、`hpc/hpr_submit.sh`；`hpc/hpr_consistency.py` 把本文件与这些来源逐项比对（包内 `HPC_CONSISTENCY.json`，必须 `ALL_CONSISTENT` 才出包）。
**模型、网络、成本表、求解档案参数、GATES_V6 / C1 阈值一律不改。**
**v3.1（2026-11-05，决策清单第 195 项）：** 燃料舱净零约束改为逐计量流量为零的等价写法，部署包换成新的代码提交与 v3.1 定义文件 `batch_def/BATCH_DEF_2920x3h_v31hpc.json`（与 v3 定义只差名称、说明与运行目录），见第 15 节。v3.1 的正式运行目录为 `runs/batch5/`（HPC 上 `hpr3/runs/batch4/` 是 v3 的停批记录，保留不动），冒烟目录为 `runs/smoke56_v31/`，包目录为 `/hpctmp/<用户>/hpr31/`；下文各节的路径已按 v3.1 写。TimeLimit、walltime、资源、早期测速、构建超时、验收与预测全部不变。

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
| 登记状态 | **REGISTERED** | 2026-11-04 审阅端按用户授权决定（第 14 节）；原为 PROPOSED，PROPOSED 时 `hpr_job.sh`（formal）、`hpr_submit.sh`、`run_batch4.sh`（正式运行）都拒绝 |
| **TimeLimit** `R_TL` / `TIME_LIMIT_S` | **864,000**（240 h），F1–F4 相同 | 第 14.1 节：T = max(72 h, min(240 h, 2 × U))，U = 263.7 h → 240 h（上限截断；T < U 的后果见第 14.2 节）。原 PROPOSED 1,296,000 s（360 h） |
| **进程 2（Gurobi）墙钟** `R_WALL` / `WALL_CAP_S` | **871,200** = TimeLimit + 7,200 | 沿用 v2 的余量 2 × 3,600 s（LP 读入 ≤ 154 s、解数组写出 ≤ 1,800 s） |
| 进程 1 超时 `BUILD_TIMEOUT_S` | **5,400** | 第 14.3 节：D2 实测 2,382 s，v3 约大 4 % → 约 2,500 s，余量约 2.2 倍。原 PROPOSED 7,200 s，v2 3,600 s |
| 进程 3 超时 `ASSIGN_TIMEOUT_S` | 32,400 | 不改（B4P 2.2–3 h × 3）；按 D2 的单线程速度估计 5–7 h，余量 1.3–1.8 倍，见第 12 节可选提议 |
| 后处理单步超时 `POST_TIMEOUT_S` | 10,800 | 不改 |
| 打包超时 `PACK_TIMEOUT_S` | 7,200 | 不改 |
| 逐运行后处理估计 | 3,900（65 min） | 不改（B4P 6.1） |
| 运行器启动后首次 Gurobi 的间隔 | 330 | 不改（`R_GAP`，WLS 令牌 ≥ 5 min） |
| 作业体开销估计 | 1,800 | 不改 |
| 等待启动的上限 `WAIT_START_MAX_S` | 7,200 | 不改：F2 等 F1 的 Gurobi 启动；F3、F4 等启动锁与间隔（第 4 节） |
| **PBS walltime F1** | **936,000**（`260:00:00`） | 第 14.4 节：330 + 5,400 + 871,200 + 32,400 + 2 × 3,900 + 1,800 = 918,930；F1 无等待；"F3 同 F1" → 260 h，余量 17,070 s；≤ 720 h |
| **PBS walltime F2** | **943,200**（`262:00:00`） | 第 14.4 节：918,930 + 2 × 7,200（等 F1 启动 + 启动锁，审查第 6 条）= 933,330，+ 2 h → 262 h，余量 9,870 s |
| **PBS walltime F3** | **936,000**（`260:00:00`） | 第 14.4 节：918,930 + 7,200（启动锁）= 926,130，+ 2 h → 260 h，余量 9,870 s |
| **PBS walltime F4** | **943,200**（`262:00:00`） | 第 14.4 节：同 F3 的 926,130；"F4 同 F2" → 262 h，余量 17,070 s |
| PBS walltime 批级作业 | 172,800（`48:00:00`） | 四个运行；正常为分钟级，若某运行的后处理在其作业内未完成，`POST_ONLY=1` 每运行补做最多 4 步 × 10,800 s（v2 两个运行 12 h）；`V3_HPC_UNATTENDED.md` 第 1 节未列，沿用原提议的保守值（第 14.5 节） |

早期测速（第 5 节）的止损线 = 0.80 × 864,000 = **691,200 s**（192 h）。

**整批时长：** F1 与 F2 同时运行，F3 在 F1 结束后、F4 在 F2 结束后开始，所以总时长约为 max(F1 + F3, F2 + F4) 加排队（D2 约 13 h）。按第 2.1 节：中值约 2 × 75 h ≈ 6–7 天；F1、F3 若到时限约 2 × 245 h ≈ 20 天；walltime 全部用满约 2 × 261 h ≈ 22 天，仍在 `/hpctmp` 60 天自动清除之内（运行中文件持续改动），但每个运行结束后应先下载其导出（第 8 节）。

## 3. PBS 资源

| 作业 | 队列 | 资源 | walltime | 内存配额 `MEM_QUOTA_GIB` | 核数 `CORES` | 依赖 |
|---|---|---|---|---|---|---|
| **F1** `hpr3_f1` | `parallel` | `select=1:ncpus=48:mem=300gb` | 260:00:00 | **300** | 48 | 无 |
| **F2** `hpr3_f2` | `parallel` | `select=1:ncpus=48:mem=250gb` | 262:00:00 | **250** | 48 | `-W depend=after:<F1 作业号>`（F1 开始执行后才可调度） |
| **F3** `hpr3_f3` | `parallel` | `select=1:ncpus=48:mem=300gb` | 260:00:00 | **300** | 48 | `-W depend=afterany:<F1>`（F1 结束后，无论退出码；F1 没有正常结束、又没有停批时，F3 的作业体写 `STOP_SAFE:PREDECESSOR_NOT_ENDED`，不启动，审查第 3 条） |
| **F4** `hpr3_f4` | `parallel` | `select=1:ncpus=48:mem=250gb` | 262:00:00 | **250** | 48 | `-W depend=afterany:<F2>`（同 F3 的前序检查） |
| **批级** `hpr3_batch` | `parallel` | `select=1:ncpus=12:mem=120gb` | 48:00:00 | 120 | 12 | `-W depend=afterany:<F3>:<F4>`（F3、F4 结束后；它们又在 F1、F2 之后，所以四个都结束） |

- 内存沿用 v2：F1、F3 300 GB，F2、F4 250 GB（指令第 5.5 条）；止损线 80 %：F1、F3 **240 GiB**，F2、F4 **200 GiB**。v3 进程 2 峰值外推（B4P 值 × 1.3，因 v3 每次迭代多约 49 % 运算、因子非零约多 30 %）：F1、F3 117 / 161 / 208 GiB，F2、F4 88 / 135 / 194 GiB；1.25 倍检查（检查单 H-P4）：300 ≥ 260、250 ≥ 242.5。F2、F4 的高值离止损线只有 3 %，见第 12 节可选提议。
- **核数：** 任何时刻最多两个正式作业（F1 与 F2；之后 F3 与 F2、F1 与 F4 或 F3 与 F4）= 96 核 = `parallel` 每用户合计上限；批级 12 核在四个都结束后才运行。每用户 ≤ 8 个作业：5 个。
- 300 / 250 GB ≤ 约 360 GB，可落在 32 台 367 GB 节点；单作业 ≤ 540 GB、walltime ≤ 720 h。
- 不加 `-P`；无 `-V`（测试开关由预检 `guards` 节再查一次）。
- **批级作业只设一个，排在四个运行之后**（指令第 5.4 条允许的两种之一）：F3、F4 各 48 核在跑时，"第 A 对"的批级作业受每用户 96 核的上限，本来就要等 F3 或 F4 结束才能调度，单独设它几乎换不来时间，却要给运行器加按对选择的逻辑。F1、F2 的逐运行后处理（临时 C1、账本、M12、Owen、GATES_V6 临时标签、导出）在各自作业内完成，结束后即可按第 8 节先下载。

## 4. 许可会话（任意时刻 ≤ 2 个 Gurobi 会话，会话启动间隔 ≥ 330 s）

- **≤ 2 个会话：** F1 与 F3 串行（`afterany`），F2 与 F4 串行，所以同时最多两个求解；运行器另在启动锁内核对共享运行目录中"已启动未结束"的其他求解少于 2 个，否则等待（上限 `WAIT_START_MAX_S`，超时 `STOP_SAFE:START_LOCK`）。
- **F2 等 F1（沿用 v2 两重机制）：** `qsub -W depend=after:<F1>`，运行器 `--only F2` 以 `WAIT_START_OF=F1` 运行：F2 的进程 2 等到 `F1/.solve_start` 距今 ≥ 330 s（或 F1 已结束求解 / 未经 Gurobi 就结束）。
- **启动锁（新增，所有运行）：** 每个运行在启动 Gurobi 前用原子 `mkdir runs/batch5/.gurobi_start_lock`（v3 为 `runs/batch4/`；锁在正式运行目录内）取得锁（跨节点也有效），锁内等到距其他运行的每次 Gurobi 启动、任何运行的 Gurobi 结束与本运行器启动都 ≥ 330 s，且其他在跑的 Gurobi 少于 2 个，写出 `.solve_start` 后立即释放。这样 F3 与 F2、F3 与 F4、F4 与 F1 的启动无论何时重合都保持间隔。锁不会被自动打破：若持锁作业在持锁期间被杀，其他运行等满 `WAIT_START_MAX_S` 后 `STOP_SAFE:START_LOCK`，由用户确认没有运行器持锁、审阅端同意后把该目录改名移开（操作指南步骤 H3）；`hpr_submit.sh --resume` 发现锁目录即拒绝（审查第 6 条）。持锁时间正常为几分钟；当另一个运行的 Gurobi 刚启动或结束（< 330 s）、或已有 2 个在跑时，可以合法持锁到 `WAIT_START_MAX_S`。
- **已知局限（审查第 2 条，不改求解路径）：** `.solve_start` 由运行器在启动进程 2 时写出，早于 `b4_split_solve.py` 里 `gp.Env()` 真正建立 WLS 会话（之前还有 import 与读入 LP 标签）；`.solve_end` 比进程退出最多晚约 5 s。所以两次会话启动的实际间隔 = 330 s + 后者的延迟 − 前者的延迟，理论上可能略小于 330 s。本批不改：同时只有 F1、F2 两个会话，不超过上限；F3、F4 开会话前还有约 40 分钟无许可的构建（进程 1），与前一个会话的间隔自然远大于 330 s。
- 正式作业不运行预检的 `licence` 节；作业开头只检查许可文件存在与权限 600。许可可用性由冒烟作业验证。
- **F1–F4 运行期间（从第一个正式作业开始到最后一个求解结束），本机与 AutoDL 都不得启动 Gurobi 会话**（同一 WLS 许可）。
- 许可只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；绝不进入包、代码、作业脚本、日志、结果包；导出日志经过滤；打包前检索许可特征串，命中即拒绝。

## 5. 止损与保护（沿用 v2，参考迭代数按 v3 重登记）

1. **内存止损 → `STOP_SAFE:MEMORY:<编号>`：** 作业 cgroup 匿名内存（不可见时为进程组 RSS 之和）超过配额的 **80 %** → 终止该 Gurobi 进程组，不再启动任何求解。
2. **早期测速 → `STOP_SAFE:PROJECTION:<编号>`：** 第 20 次 barrier 迭代后，第 11–20 次平均耗时 × 参考迭代数 + 已用时间 > 0.80 × TimeLimit → 终止。**参考迭代数（v3 登记）：F1、F3 350；F2、F4 250。** 方法：v2 的规则是"取同模型的迭代数区间上端"（第三批 365×24h 253–465 → 450）。v3 的区间按第 2.1 节：一体化 160–350、`no_new_xb` 111–250，各取上端。v2 的 450 / 250 偏高只会让止损更宽松。按登记的 TimeLimit 864,000 s，止损线 691,200 s，F1、F3 在 Atlas 上每次迭代超过约 1,840–1,860 s 时止损（第 14.2 节；第 2.1 节中值 1,056 s、高值 2,686 s）。
3. **墙钟：** 进程 2 到 871,200 s 终止整个进程组。
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

- **每个运行结束后**（`hpc/hpr_status.sh` 显示 `ended`）：用户下载该运行的导出 `runs/batch5/export/<编号>/`（v3.1；单路一个 `tar` 打包 + `sha256sum`，见操作指南第 6 节），不必等批级作业。
- 批级作业结束后：`runs/batch5/results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与各自的 `.sha256`（停批时 `*_halted_*`）。用户尽快下载到 `D:\ResearchWorkspaces\ASEAN\work\p1_v3_20261102\hpc_results\`，**单路**，本机核对 SHA256（PowerShell `Get-FileHash`）。
- LP / 解数组（约 4 × 7.8 GB）留在 `/hpctmp`（`ARRAYS_MANIFEST.json` 登记 SHA256），60 天未改动自动清除；需要时另行下载。

## 9. 测试作业（登记为测试，不属于正式运行）

| 作业 | 队列 / 资源 | walltime | 内容 | 判据 |
|---|---|---|---|---|
| 环境安装 `hpr3_install`（通常不需要） | `serial`，`ncpus=1:mem=8gb` | 02:00:00 | 同 v2；HPC 上已有环境，登录预检 `env` 节 key packages 一致（284 / 284）即复用，不提交本作业 | `INSTALL_STATUS.txt` |
| **冒烟** `hpr3_smoke56`（正式提交前必须 PASS） | `parallel`，`ncpus=17:mem=32gb` | 04:00:00 | 作业体依次以 `JOB_MODE=smoke56` 运行 F1 体、F2 体、批级体：`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`，标签 `SMOKE_TEST_ONLY`，运行目录 `runs/smoke56_v31`（v3 为 `runs/smoke56`）；两次 Gurobi 会话串行（间隔 ≥ 330 s）；F3、F4 与 F1、F2 走同一代码路径，不进冒烟 | `SMOKE_STATUS.txt`：F1、F2 optimal、ACCEPTED、后处理与批级 exit 0、`DONE`；目标值与本机冒烟（`RUN_PLAN_V3.md` 第 25 节：F1 329,705,566,422.23596、F2 342,268,691,464.4567 EUR）相对偏差 ≤ 1e-6（跨机器只记录差异） |
| 全尺寸 BUILD_ONLY `hpr3_build_only_f1`（可选） | `parallel`，`ncpus=48:mem=300gb` | 02:30:00 | 同 v2 的 D2：只跑进程 1，记录峰值、LP 字节、构建与写出秒数 | `BUILD_ONLY_STATUS.txt`：`BUILD_CHECK_F1 passed`；参考：峰值约 96 GiB、LP 约 5.5 GB、≤ 2,700 s |

- 测试作业的开关只在对应作业体内导出；正式作业在开关残留、`--auth` 缺失、运行目录含测试残留时拒绝（退出码 2）。
- 冒烟作业的两次 Gurobi 会话也要遵守第 4 节最后一条的同期禁止。

## 10. 登记常数一览（检查单 H-P3 的比对清单）

| 常数 | 值 | 来源 |
|---|---|---|
| 登记状态 | **REGISTERED** | 定义文件 `limits_status` |
| 网络 SHA256 / 字节 F1–F4 | 第 1 节 | 定义文件 `registered_sha` / `registered_bytes` |
| 构建提交 | `a1ef782b8c8f0b6cb0ef67b3fe66a7493865e9b7` | 定义文件 `build_commit` |
| TimeLimit / 进程 2 墙钟 / 间隔 | 864,000 / 871,200 / 330 | 定义文件 `limits`（`run_batch4.sh` 经 `hpc-plan` 读取） |
| 求解方式 | split | `run_batch4.sh` `R_MODE`、作业体 `SOLVE_MODE=split` |
| 进程 1 / 3 超时 | 5,400 / 32,400 | 定义文件 `limits` |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | 定义文件 `limits` |
| 内存止损分数 | 0.80 | `b4_batch4.py` `MEMORY_STOP_FRACTION`、运行器缺省 |
| 早期测速分数 / 迭代参考（F1 / F2 / F3 / F4） | 0.80 / 350、250、350、250 | `b4_batch4.py` `PROJECTION_FRACTION`；定义文件 `iterations_reference`（运行器经 `runmeta` 读取） |
| 等待启动上限 | 7,200 | 定义文件 `limits` |
| 后处理并存内存条件 | 100 GiB | `b4_batch4.py` `POST_MEM_NEED_GIB`、运行器缺省 |
| PBS F1 | parallel / 48 / 300gb / 260:00:00 | 定义文件 `hpc_jobs` → `pbs/hpr3_f1.pbs` |
| PBS F2 | parallel / 48 / 250gb / 262:00:00 | `pbs/hpr3_f2.pbs`；`WAIT_START_OF=F1` |
| PBS F3 | parallel / 48 / 300gb / 260:00:00 | `pbs/hpr3_f3.pbs` |
| PBS F4 | parallel / 48 / 250gb / 262:00:00 | `pbs/hpr3_f4.pbs` |
| walltime 余量（每个正式作业 ≥ 7,200 s） | F1 17,070 / F2 9,870 / F3 9,870 / F4 17,070 | `b4_batch4.py walltime_components`（`per_job.margin_s`），一致性检查逐作业核对 |
| PBS 批级 | parallel / 12 / 120gb / 48:00:00 | `pbs/hpr3_batch.pbs` |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00 | `pbs/hpr3_smoke56.pbs` |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 02:30:00 | `pbs/hpr3_build_only_f1.pbs` |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `pbs/hpr3_install.pbs` |
| 依赖 | F2 `after:F1`、F3 `afterany:F1`、F4 `afterany:F2`、批级 `afterany:F3:F4` | 定义文件 `hpc_jobs` → `hpc/hpr_submit.sh` |
| 两对 | A：F1 / F2；B：F3 / F4 | 定义文件 `pair` |

## 11. 路径约定（HPC）

| 内容 | 位置 |
|---|---|
| 包目录（= `PBS_O_WORKDIR`，作业从这里提交） | v3.1：`/hpctmp/<用户>/hpr31/`（新目录；v3 的 `/hpctmp/<用户>/hpr3/` 与 v2 的 `/hpctmp/<用户>/hpr/` 保留不动） |
| 代码 | `/hpctmp/<用户>/hpr31/repo/`（预检 `sha` 节解包，`.package_commit` = `COMMIT`） |
| conda 环境 | `$HOME/miniforge3/envs/pypsa-earth`（HPR 步骤已装；预检 `env` 节核对） |
| 运行目录 | 正式 `runs/batch5/`；冒烟 `runs/smoke56_v31/`；BUILD_ONLY `runs/build_only_f1/`（定义文件 `run_dirs` → `pbs/HPC_PLAN.txt` 的 `RUNDIRS` 行，作业体、提交与状态脚本都读这一行；v3 为 `runs/batch4/`、`runs/smoke56/`） |
| 结果包 | `runs/batch5/results_{light,full}_final_*.tar.gz`（+ `.sha256`） |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600`，用户自行放置 |
| 作业日志 | `/hpctmp/<用户>/hpr31/<作业名>.o<作业序号>` |

## 12. 原 PROPOSED 取值与可选提议（记录；2026-11-04 已按第 14 节决定）

下表是 V3 HPC v1 提交时的 PROPOSED 取值，保留作记录；登记值见第 2.2、3、10 与 14 节。三项可选提议未被采纳（F2、F4 内存保持 250 GB，进程 3 超时保持 32,400 s，不设按运行的 TimeLimit）。

| 项 | v2 登记值 | 提议（PROPOSED） | 理由 |
|---|---|---|---|
| TimeLimit（F1–F4） | 864,000 s（240 h） | **1,296,000 s（360 h）** | 第 2.1 节：F1、F3 高值 261 h 超过 240 h，高高情形 347 h；止损线随之为 288 h |
| PBS walltime F1 / F2–F4 | 255 h / 257 h | **376 h / 378 h** | 由 TimeLimit 与各项开销求和（第 2.2 节）；≤ 720 h |
| 进程 1 超时 | 3,600 s | **7,200 s** | D2 已用 66 %，v3 约大 5 %；按约 3 倍余量 |
| 批级 walltime | 12 h | **48 h** | 四个运行的补做上限 |
| 可选：F2、F4 内存 | 250 GB | 300 GB | 高值 194 GiB 离止损线 200 GiB 只有 3 %；300 GB 仍落在 367 GB 节点；不提议时保持 250 GB |
| 可选：进程 3 超时 | 32,400 s | 43,200 s | 按 D2 单线程速度估计 5–7 h，余量 1.3–1.8 倍；walltime 相应 +3 h |
| 可选：F2、F4 单独 TimeLimit | — | 864,000 s | 高值 38 h，240 h 已足够；需要运行器支持按运行的时限（现在没有），不建议本批做 |

**登记方式（已执行，第 14 节）：** 改定义文件（`limits_status: REGISTERED` 与数值）与本文件第 2、3、5、10 节，重新打包（`hpc_v3/make_hpc_package_v3.sh`，旧包改名保留）与干跑，再由用户上传。

## 13. 同期禁止

HPC 正式求解期间（第一个正式作业开始到最后一个求解结束），本机与 AutoDL 不调用 Gurobi（WLS 许可共用）；冒烟作业期间同样。

## 14. 审阅端按用户授权决定（2026-11-04）

**依据：** `work/p1_v3_20261102/V3_HPC_UNATTENDED.md` v1（SHA256 `bd985bc9a7a30d247f03e1fa61048941d79d8870fb9b348a696449bcfe05f8df`，与同目录登记文件一致）第 1 节，用户 2026-11-04 02:27 SGT 授权审阅端代为决定原 PROPOSED 取值。本节在任何 F1–F4 的 HPC 求解之前提交。模型、网络、成本表、求解档案、GATES_V6 / C1 阈值与 `RUN_PLAN_V3.md` 第 26 节的预测都不改。

### 14.1 TimeLimit（F1–F4 相同）

规则：T = max(72 h, min(240 h, 2 × U))，向上取整到 12 h 的倍数；U 为 F1 求解时长的外推上界。

**U 的方法（第 2.1 节，INFERENCE）：** U = 单次迭代耗时 × 迭代数 × CPU 因子 + 预求解与排序，每一项都取保守端：
- 单次迭代：B4P 对 v2 F1 2920×3h 的高值 1,127 s（8470Q T16）× v3 / v2 单次迭代比的上端 1.49（365×24h 同档案、同机型实测 1.30–1.49）= **1,679 s**；
- 迭代数：一体化 56 时段 80–83 次、365×24h 146–186 次，按 56 → 365 的增长外推到 2920 为上端 **350 次**；
- CPU 因子：Atlas EPYC 7R13 对 8470Q 取假设区间 1.0 / 1.3 / 1.6 的上端 **1.6**；
- barrier：1,679 × 350 × 1.6 = 940,240 s = 261.2 h；预求解与排序取上端 2.5 h（B4P 1,400–5,700 s × 1.6）；**U = 263.7 h**。

2 × U = 527 h → min(240 h, 527 h) = 240 h → max(72 h, 240 h) = 240 h（已是 12 h 的倍数）。**T = 864,000 s（240 h）**；进程 2 墙钟 = T + 7,200 = **871,200 s**。

### 14.2 早期测速止损

仍为 **0.80 × T = 691,200 s**；参考迭代数取 U 所用的 350 次（F1、F3），F2、F4 保持 250 次（`no_new_xb` 区间上端，第 5 节）。

**须知（INFERENCE）：** 上限 240 h 截断后 T < U。止损在第 20 次迭代判定：第 11–20 次平均耗时 × 350 + 第 20 次的日志时间（≈ 预求解 + 20 × 平均耗时）> 691,200 s，即 Atlas 上每次迭代超过约 **(691,200 − 预求解) / 370 ≈ 1,840–1,860 s**（预求解 0.4–2.5 h）时止损。这低于 U 假设的 2,686 s / 次（1,679 × 1.6），高于中值 1,056 s / 次（812 × 1.3）。所以按本取值，F1、F3 只有落在第 2.1 节高值区间的上段（每次迭代 ≥ 约 69 % 的 U 假设）时才会被止损；授权第 1 节第 2 条"只有比 U 慢很多时才触发"在本取值下不完全成立。这是规则中 240 h 上限的直接结果，按授权不改；被止损时按第 6 节由用户决定以更长时限重开（新运行目录，资源原因的重新开始）。

### 14.3 进程 1 构建超时

**5,400 s**：D2（Atlas，v2 F1 全尺寸 BUILD_ONLY）实测 2,382 s，v3 LP 约大 4 %（列 +4.84 %、行 +4.07 %、非零约 +3.4 %）→ 约 2,500 s，余量约 2.2 倍。

### 14.4 PBS walltime（v2 `RUN_PLAN_HPC.md` 第 2 节的构成公式）

基础项 = 运行器启动后首次 Gurobi 的间隔 330 + 进程 1 超时 5,400 + 进程 2 墙钟 871,200 + 进程 3 超时 32,400 + 逐运行后处理估计 2 × 3,900 + 作业体开销 1,800 = **918,930 s**。等待项：F2 等 F1 的 Gurobi 启动（`WAIT_START_OF`，上限 7,200 s）后再等启动锁（上限 7,200 s，审查第 6 条），共两项；F3、F4 等启动锁，一项；F1 没有等待项。

| 作业 | 等待项 | 求和（s） | + 2 h 余量（h） | 登记 walltime | 余量（s） |
|---|---|---:|---:|---|---:|
| F1 | 0 | 918,930 | 257.26 | **260:00:00**（"F3 同 F1"） | 17,070 |
| F2 | 2 | 933,330 | 261.26 | **262:00:00** | 9,870 |
| F3 | 1 | 926,130 | 259.26 | **260:00:00** | 9,870 |
| F4 | 1 | 926,130 | 259.26 | **262:00:00**（"F4 同 F2"） | 17,070 |

每个作业的余量都 ≥ 7,200 s，全部 ≤ Atlas `parallel` 队列上限 720 h（`HPC_FACTS_20261026.md`）。F1、F3 取同一值，F2、F4 取同一值，各取同对中较保守的一个。一致性检查逐作业核对"walltime ≥ 求和"与"余量 ≥ 7,200 s"。

### 14.5 资源与批级作业

F1、F3 300 GB，F2、F4 250 GB，均 48 核；批级 12 核 / 120 GB（与原值相同）。批级 walltime 第 1 节未列，沿用原提议的保守值 **48 h**（四个运行的补做上限 4 × 4 × 10,800 s，正常为分钟级）。

### 14.6 审查第 2 条

`.solve_start` 早于真正建立会话：列为已知局限（第 4 节），本次不改求解路径，理由见第 4 节与报告。

### 14.7 登记的落实

定义文件 `batch_def/BATCH_DEF_2920x3h_v3hpc.json`：`limits_status` `REGISTERED`，`time_limit_s` 864,000、`build_timeout_s` 5,400，walltime F1 / F2 / F3 / F4 = `260:00:00` / `262:00:00` / `260:00:00` / `262:00:00`，其余不变；包按此重新打出（`hpc_package_v3/`，旧包 `hpc_package_v3_superseded_1e7b503c/` 改名保留），一致性检查全部一致后出包。
