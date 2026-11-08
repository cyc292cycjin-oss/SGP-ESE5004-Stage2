# HPC 正式运行计划 v4（RUN_PLAN_HPC_V4）——v4 主算一对 F1（一体化）、F2（`no_new_xb`），2920×3h，NUS Atlas（PBS Pro），每个运行一个作业 + 一个批级作业

**版本：** V4 W14 v1，2026-11-09（SGT）。依据 `work/p1_v4_w14_20261109/V4_W14_INSTRUCTION.md` v2（SHA256 `6cb103dbe8822cd48d1fa699ec947be2a682d371e14337b13dceed38597d2243`，与同目录登记文件一致；台账 W14；决策清单第 213、215、216、221、222、223 项）。模板：v3.1 计划 `hpc_package_v3_1/RUN_PLAN_HPC_V3.md`（第 1–15 节）。
**状态：** 本文件在任何 v4 HPC 提交之前提交入库（登记先于结果，第 0 节）；它是 v4 包的登记计划。第 8 节报警线与第 9 节预测在任何 v4 HPC 求解之前写定，求解后不改。
**单一来源：** 定义文件 `batch_def/BATCH_DEF_2920x3h_v4hpc.json`（包内 `BATCH_DEF.json`）→ `scripts_project/b4_batch4.py`（运行表、登记网络、时限、作业表、冒烟期望值）→ `run_batch4.sh`（经 `b4_batch4.py hpc-plan` / `runmeta` 读取）、`preflight.sh`、`hpc/make_pbs.sh` 生成的作业脚本、`hpc/hpr_submit.sh`；`hpc/hpr_consistency.py` 把本文件与这些来源逐项比对（包内 `HPC_CONSISTENCY.json`，必须 `ALL_CONSISTENT` 才出包）。
**模型、网络、成本表、求解档案参数、GATES_V6 / C1 阈值一律不改。** 本步不改模型代码、输入、配置与注册表，只新增打包与运行计划文件及 v4 包专用的 HPC 脚本（`hpc_v4/preflight.sh`、`hpc_v4/make_hpc_package_v4.sh`、`hpc_v4/make_reference_values_v4.py`）。

---

## 0. 目的与范围（决策第 222 项，审阅端摘录）

- **今晚只提交 v4 主算一对**（F1 一体化、F2 `no_new_xb`）加批级后处理，作为数据重构后的主结果；敏感性在 W19 登记后另批提交（与师哥 11-10 面谈后定）。
- **登记值：** 求解档案 `formal_barrier_1e6_t16`（与 v3.1 相同）；TimeLimit 259,200 s（72 h）；早期测速止损 0.8 × TimeLimit，参考迭代一体化 350、`no_new_xb` 300；进程 1 构建超时 7,200 s；walltime 96 h；资源 F1 48 核 / 300 GB、F2 48 核 / 250 GB、批级 12 核 / 120 GB（与 v3.1 相同，不在今晚改核数）；HPC 目录 `/hpctmp/$USER/hpr4`，运行目录 `runs/batch6`、`runs/smoke56_v4`；**正式提交前 HPC 冒烟必须 PASS**。
- **第 213、216 项：** 不做 AutoDL 筛查与只预处理作业。**第 214 项第⑤条：** 凸性上下界是报警线（第 8 节）。**第 215 项第①、②条：** 状态脚本同时显示两种目标值口径（含常数项的 `objective` 与 LP 值 `objective_lp`，`hpc/hpr_status.sh`）；运行器把包的 `COMMIT` 写入 `RUN.json` 与求解回执（`run_batch4.sh` → `s2_solve.py --package-commit`）。
- **登记先于结果：** 运行计划、时限、验收与预测都在任何 HPC 提交之前提交入库；**非 optimal 不重试、不改参数**。
- **不在本批：** 敏感性对（W19）、F3 / F4 类的第二对、365×24h、AutoDL。

## 1. 运行

| 编号 | 对 | 运行 | 包内网络文件 | 字节 | SHA256 | 情景 | 成本表 | 档案 | 作用 |
|---|---|---|---|---:|---|---|---|---|---|
| F1 | A | v4 主算一体化 | `networks/integrated_2920_3h_unsolved.nc` | 82,749,911 | `86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d` | integrated | `networks/integrated_costs_active_research.csv` | `formal_barrier_1e6_t16` | c(N)、Owen 分摊、B6 基准 |
| F2 | A | v4 主算 `no_new_xb` | `networks/no_new_xb_2920_3h_unsolved.nc` | 82,112,443 | `24e835f74365f63f6dc2c848f81bb43727e082be6c34f2c3aca0594641b25187` | no_new_xb | 同上 | 同上 | B6 = F2 − F1 |

- **一对：** A = F1 / F2；B6 = Z(F2) − Z(F1)（`gate_b6_cost`），M12 受益按 Owen 对偶形式（α 0.5 主值）。
- **构建：** 分支 `codex/v4-w14-20261109` 提交 `59b128ea047de600adbd2a54e6e84b48a1544fe5`（W14-1；dirty 0，`PYTHONHASHSEED=0`；`scripts/build_w14.sh main`：`s2_network.py --scenario integrated --override demand.v4.enabled=true`，`m08a_variants.py --set cross_border.stock_mode=no_new_xb`）。该提交在 `research/` 之外与 D2c 头 `4e83d71e` 逐文件相同（本步不改代码、输入、配置），与包的代码提交 `COMMIT` 也相同（打包脚本核对 `git diff` 为空才出包）。回执：`integrated_BUILD_RECEIPT.json`（F1，`code_sha` = 构建提交）、`no_new_xb_2920_3h_VARIANT_RECEIPT.json`（F2 ← F1）；两运行共用一张成本表。**365×24h 网络不入包**（预检发现即失败）。
- **为什么构建提交不是包的提交（如实说明）：** 指令第 2.1 条要求"在包的代码提交上构建"。网络 SHA256 与构建提交必须写进定义文件（`registered_sha`、`build_commit`，`base-check` 核对回执的 `code_sha`），而定义文件本身属于包的代码提交，所以构建提交只能早于包的提交（v3 先例：构建 `a1ef782b`、包 `d3b9a3bc`）。等价性由两条核对保证：(1) 两个提交在 `research/` 之外逐文件相同，代码包内容相同；(2) 在包的提交上于同一 worktree 路径重建一次，两张 2920×3h 网络与构建提交的文件逐字节相同（`STATIC_CHECKS.md` 第 4 节）。
- **v4 开关集（网络元数据，预检核对）：** `v4_w08.switch_sha256` = `d89ccbf47b0002e65246ce75ba06158f76c340f5091127f6658eec06ed727a62`，表目录 `research_inputs/industry_v4/out_ras`（主集：`biomass_potential v4_adjusted_t06`、`source_band_basis post_product`、`lng_regas_adder asean_tariffs`、`missing_cost_rule proxy` 等）；构建覆盖 F1 `demand.v4.enabled=true`，F2 另加 `cross_border.stock_mode=no_new_xb`；配置哈希 F1 `6db27beb…`、F2 `78cb4d7c…`（= 由配置文件与记录的覆盖重组后的哈希，B12 恒等）。登记在定义文件 `v4_meta`，包的预检 `networks` 节逐项核对（D1 的 `v4_common.check_network_meta`）。
- **与 D2c 冒烟网络的关系（`STATIC_CHECKS.md` 第 3 节）：** 两张网络与 D2c 冒烟网络（`db33f84e…` / `f03aab19…`）在全部组件表与时间序列上逐值相同，只有元数据里构建 worktree 路径（地热母线映射来源）与变体的基网 SHA256 不同；按 `--truncate 56` 同一规则截出的 56 时段网络亦逐组件相同。
- **档案（不改）：** `formal_barrier_1e6_t16`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200；`--scaling on`。
- **求解方式（不改）：** `SOLVE_MODE=split`：进程 1 构建（无许可）→ 进程 2 `b4_split_solve.py`（唯一的 Gurobi 进程，读入后删除 LP 文件）→ 进程 3 映射与导出（无许可）。
- **一次求解：** 每个运行只求解一次；不重试、不改参数、不热启动；非 optimal 照实记录并按第 7 节分级。

## 2. 时限与 PBS walltime

### 2.1 依据（v3.1 实测，VERIFIED；`work/p1_v31_w15_20261106/HPC_RUNTIME_FACTS.md`）

v3.1 2920×3h 在 Atlas（AMD EPYC 7R13，Gurobi 12.0.3，16 线程）上：进程 2 F1 39,224 s（10.90 h，迭代 244）、F2 20,245 s（5.62 h，153）、F3 23,179 s、F4 29,979 s（218）；进程 1 1,025–3,414 s（超时 5,400 s 的 19–63 %）；进程 3 1,031–2,846 s；逐运行后处理 1,035–3,296 s；进程 2 峰值 RSS 102.95–116.40 GiB；整批 37 h（含 F3 排队 13.9 h）。

**v4 LP 规模比 r（VERIFIED，56 时段 LP）：** D2c 冒烟 v4 F1 行 1,604,504、列 729,105、非零 3,722,003，v3.1 本机回归 F1 1,607,971 / 729,156 / 3,720,313 → r = 1.00045；F2 3,571,769 / 3,570,079 → r = 1.00047。规则 T = max(72 h, 2 U′)、U′ = 10.9 h × 1.5（迭代）× 1.5（节点）× r = 24.5 h × r，r ≤ 1.47 时取 72 h：**r ≈ 1.0005，TimeLimit 72 h 成立**（INFERENCE：2920 的规模比按 56 时段推断；v4 与 v3.1 的组件数也几乎相同，`STATIC_CHECKS.md` C7）。

### 2.2 取值（决策第 222 项）

| 量 | 值（s） | 依据 |
|---|---|---|
| 登记状态 | **REGISTERED** | 第 222 项（审阅端摘录，按用户勾选执行）；PROPOSED 时 `hpr_job.sh`（formal）、`hpr_submit.sh`、`run_batch4.sh`（正式运行）都拒绝 |
| **TimeLimit** `R_TL` / `TIME_LIMIT_S` | **259,200**（72 h），F1、F2 相同 | 第 222 项；第 2.1 节 |
| **进程 2（Gurobi）墙钟** `R_WALL` / `WALL_CAP_S` | **266,400** = TimeLimit + 7,200 | 沿用 v2 / v3 的余量 2 × 3,600 s（LP 读入、解数组写出） |
| 进程 1 超时 `BUILD_TIMEOUT_S` | **7,200** | 第 222 项：v3.1 F4 用了 3,414 s（63 % of 5,400 s），节点间单线程差 3.3 倍 |
| 进程 3 超时 `ASSIGN_TIMEOUT_S` | 32,400 | 不改（v3.1 实测 ≤ 2,846 s） |
| 后处理单步超时 `POST_TIMEOUT_S` | 10,800 | 不改 |
| 打包超时 `PACK_TIMEOUT_S` | 7,200 | 不改 |
| 逐运行后处理估计 | 3,900（65 min） | 不改（v3.1 实测 1,035–3,296 s） |
| 运行器启动后首次 Gurobi 的间隔 | 330 | 不改（`R_GAP`，WLS 令牌 ≥ 5 min） |
| 作业体开销估计 | 1,800 | 不改 |
| 等待启动的上限 `WAIT_START_MAX_S` | 7,200 | 不改：F2 等 F1 的 Gurobi 启动，再等启动锁（第 4 节） |
| **PBS walltime F1** | **345,600**（`96:00:00`） | 330 + 7,200 + 266,400 + 32,400 + 2 × 3,900 + 1,800 = 315,930；F1 无等待项；余量 29,670 s |
| **PBS walltime F2** | **345,600**（`96:00:00`） | 315,930 + 2 × 7,200（等 F1 启动 + 启动锁）= 330,330；余量 15,270 s |
| PBS walltime 批级作业 | 172,800（`48:00:00`） | 沿用 v3.1；正常为分钟级（v3.1 1,173 s），若某运行的后处理在其作业内未完成，`POST_ONLY=1` 补做 |

早期测速（第 5 节）的止损线 = 0.80 × 259,200 = **207,360 s**（57.6 h）。v3.1 四个运行的外推最大 44,194 s，只占该线的 21 %。

**整批时长（INFERENCE）：** F1 与 F2 同时运行（F2 在 F1 开始后可调度，Gurobi 在 F1 启动 ≥ 330 s 后启动），批级作业在两者结束后。按 v3.1 实测，计算约 13 h（F1 作业）+ 批级 0.3 h，另加排队；walltime 96 h 全部用满约 4 天，远在 `/hpctmp` 60 天自动清除之内。

## 3. PBS 资源

| 作业 | 队列 | 资源 | walltime | 内存配额 `MEM_QUOTA_GIB` | 核数 `CORES` | 依赖 |
|---|---|---|---|---|---|---|
| **F1** `hpr4_f1` | `parallel` | `select=1:ncpus=48:mem=300gb` | 96:00:00 | **300** | 48 | 无 |
| **F2** `hpr4_f2` | `parallel` | `select=1:ncpus=48:mem=250gb` | 96:00:00 | **250** | 48 | `-W depend=after:<F1 作业号>`（F1 开始执行后才可调度）；运行器 `WAIT_START_OF=F1` |
| **批级** `hpr4_batch` | `parallel` | `select=1:ncpus=12:mem=120gb` | 48:00:00 | 120 | 12 | `-W depend=afterany:<F1>:<F2>`（F1、F2 无论怎样结束都放行） |

- 内存沿用 v3.1：F1 300 GB、F2 250 GB；止损线 80 %：F1 **240 GiB**、F2 **200 GiB**。v3.1 实测进程 2 峰值 RSS ≤ 116.4 GiB，v4 LP 同规模（r ≈ 1.0005）。定义文件保留 v3 的高值估计 F1 208 / F2 194 GiB（检查单 H-P4：300 ≥ 1.25 × 208 = 260、250 ≥ 1.25 × 194 = 242.5）。
- **核数：** F1 与 F2 同时 = 96 核 = `parallel` 每用户合计上限；批级 12 核在两者结束后运行。每用户 ≤ 8 个作业：3 个。
- 300 / 250 GB ≤ 约 360 GB，可落在 367 GB 节点；单作业 ≤ 540 GB、walltime ≤ 720 h（`HPC_FACTS_20261026.md`）。
- 不加 `-P`；无 `-V`（测试开关由预检 `guards` 节再查一次）。

## 4. 许可会话（任意时刻 ≤ 2 个 Gurobi 会话，会话启动间隔 ≥ 330 s）

- **≤ 2 个会话：** 只有 F1、F2 两个求解；运行器另在启动锁内核对共享运行目录中"已启动未结束"的其他求解少于 2 个。
- **F2 等 F1（两重机制，同 v3.1）：** `qsub -W depend=after:<F1>`，运行器 `--only F2` 以 `WAIT_START_OF=F1` 运行：F2 的进程 2 等到 `F1/.solve_start` 距今 ≥ 330 s（或 F1 已结束求解 / 未经 Gurobi 就结束），上限 `WAIT_START_MAX_S`，超时 `STOP_SAFE:WAIT_START:F2`。
- **启动锁：** 每个运行在启动 Gurobi 前用原子 `mkdir runs/batch6/.gurobi_start_lock` 取得锁，锁内等到距其他运行的每次 Gurobi 启动与结束、本运行器启动都 ≥ 330 s，写出 `.solve_start` 后立即释放；锁不会被自动打破（操作指南步骤 G3）。
- **已知局限（沿用 v3.1 第 4 节，不改求解路径）：** `.solve_start` 早于 `gp.Env()` 真正建立 WLS 会话；两次会话启动的实际间隔理论上可能略小于 330 s。本批只有两个会话，不超过上限。
- 正式作业不运行预检的 `licence` 节；作业开头只检查许可文件存在与权限 600。许可可用性由冒烟作业验证。
- **v4 运行期间（从冒烟作业开始到最后一个求解结束），本机与 AutoDL 都不得启动 Gurobi 会话**（同一 WLS 许可）。
- 许可只经 `GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic` 引用；绝不进入包、代码、作业脚本、日志、结果包；导出日志经过滤；结果打包前检索许可特征串（`pack_results.sh`），命中即拒绝。

## 5. 止损与保护（沿用 v3.1，参考迭代数按第 222 项）

1. **内存止损 → `STOP_SAFE:MEMORY:<编号>`：** 作业 cgroup 匿名内存（不可见时为进程组 RSS 之和）超过配额的 **80 %** → 终止该 Gurobi 进程组，不再启动任何求解。
2. **早期测速 → `STOP_SAFE:PROJECTION:<编号>`：** 第 20 次 barrier 迭代后，第 11–20 次平均耗时 × 参考迭代数 + 已用时间 > 0.80 × TimeLimit → 终止。**参考迭代数：F1 350；F2 300**（第 222 项；v3.1 F4 已到 218 = 250 的 87 %）。止损线 207,360 s：F1 在 Atlas 上每次迭代超过约 (207,360 − 预求解与排序) / 370 ≈ 550 s 时止损（v3.1 F1 147.9 s / 次，约 3.7 倍余量）；F2 超过约 (207,360 − 预求解与排序) / 320 ≈ 640 s（v3.1 F2 112.5 s）。
3. **墙钟：** 进程 2 到 266,400 s 终止整个进程组。
4. **求解结果先落盘；** 进程 3 的异常记入回执，不改变终止状态。
5. **不重试、不改参数、不热启动。** `SoftMemLimit` 不作为登记参数。
6. **P1 探针不使用**（每个运行一个作业）。

## 6. 中断与重开

- 资源原因中断的运行：从头重开须用户明确授权，登记为"资源原因的重新开始"（新的运行目录），不算重试。
- 续跑：同一运行目录再次提交同一作业 → 已结束的跳过（`SKIP_ENDED`）；已开始未结束 → `STOP_SAFE:INTERRUPTED_<编号>`。
- **维护重叠检查：** 提交前确认登录欢迎信息中没有与预计运行期重叠的维护通知（walltime 96 h，约 4 天）；有就停下报告。
- `/hpctmp` 60 天未改动自动清除：见第 10 节。

## 7. 验收、分级与批级后处理

1. **验收（第 222 项；与 W08–D2c 冒烟同一定义）：** 终止 optimal；C1 (a)(b)(c) 接受；GATES_V6 批级重评后 **`ACCEPTED_LAYER2`**；未通过的闸门在 v3.1 并集 {A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B3, B8} 内（v3.1 F4 的 B15、B3_S4B 由审阅端按第 120 项接受，不在本并集；超出并集即报审阅端）。先用缺省参照给临时判定（`V6_ACCEPTANCE_PROVISIONAL.json`），批级作业用 F1、F2 的账本生成本批参照 `BATCH_REFERENCE.json` 并重评。
2. **分级与停批（运行器，不改）：** G2 不通过 → `STOP`；无返回解或 C1 (a) 不通过 → `UNUSABLE` 并 `STOP`（两个运行都适用）；只有 C1 (b)/(c) 不通过 → 不停。停批 = 共享运行目录中的 `STOP` / `STOP_SAFE` 让尚未进入进程 2 的运行放弃启动（`NOT_STARTED_<编号>`）；已在求解的运行跑完并后处理。
3. **逐运行后处理在各自作业内完成**（违反量 → C1 临时 → M12 → Owen 对偶形式 → GATES_V6 → 分级 → 导出 `export/<编号>/`）。
4. **批级作业**（`POST_ONLY=1`，无许可）在两个运行都落定后：补做缺失的后处理 → `BATCH_REFERENCE.json` → C1 / Owen 重评、GATES_V6 终标签 → **B6 = Z(F2) − Z(F1)**（`gate_b6_cost`）与分国账本差 → **Owen 对偶形式受益**（`M12_BENEFIT/`）→ **与 v3.1 基线的对照**（`REFERENCE_VALUES.json` → `BATCH4_SUMMARY.json` 的 `reference_comparison`：v3.1 2920×3h F1 / F2 主对照、D2c 本机 56 时段冒烟、v3.1 本机 56 时段回归；目标值差、ΔB6、每个参与者的 Owen 份额差与受益差；只描述，不设阈值）→ `BATCH4_SUMMARY.json / .md` → 结果包（light / full）。任一运行未验收：照常重评与汇总，结果包标记 `halted`，退出码 3。
5. "落定" = 已结束（`.ended`），或运行目录有 `STOP` / `STOP_SAFE` 且该运行从未开始求解。
6. **结果回来后（本机，不在 HPC）：** 按第 8 节核对报警线（违反则必有错，先查数据链，不改参数重试）；按第 9 节对照预测；失败门是否在并集内；结论交审阅端。

## 8. 报警线（第 214 项第⑤条；求解前写定）

**规则 EXACT，数值取 v3.1 2920×3h HPC 的解与对偶**（`work/p1_v3_20261102/hpc_results_v31/unpacked/export/F1`、`F2` 的 `DUALS_BY_CONSTRAINT.nc` 与已解网络；本机无 Gurobi 进程、可用内存 ≥ 8 GiB、两运行依次读取）。脚本 `scripts/w14_bounds_pre.py`，证据 `evidence/W14_BOUNDS_PRE.json`、分项 `tables/W14_BOUNDS_PRE.csv`。**凸性下界是报警线，不是通过门：违反则必有错；在界内不证明正确。**

**变动集合（脚本逐组件、逐列、逐时间序列枚举 v3.1 与 v4 两张未解网络的全部差异，未能归类的条数为 0）：**

| 类 | 内容（F1；F2 相同） | 计法 |
|---|---|---|
| 右端类（下界） | 负荷静态 1,834 条、时间序列 567 条（v4 新增 457 条工业曲线），两侧只有一侧的负荷；30 个固体生物质池的 `e_initial` / `e_nom`（含删除的 5 个纤维池）；96 个 EV 电池 `e_nom`、96 个充电桩与 187 条船运 / 过境铁路的 `p_nom`（均为固定容量）；78 个过程排放源 `p_nom`（固定、强制注入）；泰国抽蓄 `p_nom` 950 → 171 MW；8 个水库来水；18 个国产气年度上限 | V(b) 对 b 凸，v3.1 对偶为次梯度：ΔV_LP ≥ y′Δb（带符号原始对偶，linopy 约定：≤ 行 y ≤ 0、≥ 行 y ≥ 0，含时段权重）。节点平衡右端 = 负荷；Store 首时段能量平衡右端 = −e_initial；固定容量上下界右端 = pu × 容量；水库能量平衡右端 = −eh × 来水；年度上限 Σw·p ≤ cap |
| 结构（对偶延拓，下界） | 新增 70 条终端能源核算母线（只由新计量链路从既有母线供给）及其负荷；新增泰国 TH2 4 水库（608.2 MW，D2a）；删除的链路、发电机与母线 | 新母线的对偶取 y_f(t) = min_k (w·mc_k + y_bus0 − Σ_j≥2 η_j y_bus_j) / η_1，使全部新链路的降低成本非负（延拓后的对偶对 v4 LP 仍可行，弱对偶保持下界）；新水库按 D2a 规则 −min(容量 × Σ max(y,0)，来水能量 × max 价格)；删除的变量是限制，项为 0 |
| 成本类 | 树干 5 池边际成本 0 → 6.267 EUR/MWh；LNG 进口 16 台 +0.7907 EUR/MWh | V(c) 对 c 凹：上界 = Δc′x_v31（一阶，可行域不变时为真上界）；Δc ≥ 0 且变量 ≥ 0，下界 0 |
| 系数类（只给一阶估计，**无界**） | 燃气输送逸散系数 `efficiency2` 18 条；甲醇化 `efficiency3` / `efficiency4` 各 97 条 | FO = −Σ_t Δη_j × p0(t) × y_bus_j(t) |
| 常数项（精确） | 固定容量的资本 / 固定运维常数项（如泰国抽蓄固定运维） | v4 常数（D2c 冒烟回执，本包网络截短后与之逐组件相同）− v3.1 常数（HPC 回执；v3.1 的 2920 与 56 时段回执相同，常数项与时段无关） |

**合成（D1 / D2a 规则，第 214 项第⑤条）：** 报警线 ΔV ≥ Δ常数 + 右端下界 + 结构下界 + 成本类下界（0）− 容差 − 2 × |系数类一阶|；容差 1e-6 × |V_v31|（档案的障碍收敛容差）。ΔV、目标值都**含常数项**；LP 值（`objective_lp`）的报警线 = 目标值报警线 − v4 常数项（F1 2,366,478,274.24、F2 2,537,155,330.33 EUR）。

| 运行 | v3.1 目标值（EUR，含常数项） | Δ常数（精确） | 右端下界 | 结构下界 | 成本类 下界 / 一阶上界 | 系数类一阶（无界） | 容差 | **报警线 ΔV ≥** | **目标值应 ≥（含常数项）** | LP 值应 ≥ |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| F1 | 305,052,496,175.77 | −3.92 M | +7,939.36 M | +2,292.06 M | 0 / +1,681.03 M | +52.91 M | 0.31 M | **+10,121.37 M** | **315,173,866,702.07** | 312,807,388,427.83 |
| F2 | 317,028,875,628.39 | −3.92 M | +12,145.80 M | +2,416.53 M | 0 / +2,106.55 M | +44.76 M | 0.32 M | **+14,468.58 M** | **331,497,457,504.98** | 328,960,302,174.65 |

- **主要分项（F1 / F2，bn EUR）：** 池初始能量 +46.12 / +27.52（东盟固体生物质潜力 1,990.8 → 1,252.1 TWh，含纤维池删除）；负荷 −39.52 / −16.78（生物质终端 −28.18 / −4.84、工业热中温 B −13.20 / −13.49 等降，燃气终端 +5.05 / +5.41、工业电力 +2.55 / +2.14 等升）；新核算母线负荷 +2.46 / +2.59；过程排放源 +1.27 / +1.28；EV 电池上下界 −0.16 / −0.19；燃气年度上限 +0.16 / +0.24；新水库 −0.17 / −0.18。
- **须知（INFERENCE，不影响报警线的有效性）：** v3.1 解中 VN 固体生物质池是零余量池（固定需求 ≈ 池，W12 F7），其对偶退化，F1 与 F2 取到的值不同：VN 的池项 + 生物质终端负荷项合计 F1 −4.90 bn、F2 −0.64 bn。退化对偶仍是最优对偶，下界有效，只是 F1 的界更弱。由此，两运行一阶估计之差（ΔB6 一阶 +4.75 bn）中约 +4.26 bn 是退化对偶的假象，**不用作 B6 预测**（第 9 节）。
- **一阶估计（INFERENCE，非判据）：** ΔV ≈ 下界 + 成本类一阶上界 + 系数类一阶 = F1 +11.96 bn、F2 +16.71 bn。按 W08 冒烟的经验（大变动下一阶值低于实际 2.6–2.9 倍，二阶项为工业热价下降等），实际 ΔV 预计明显高于一阶值（第 9 节）。

## 9. 预测（INFERENCE；求解前写定，求解后不改）

**方法与依据：** (a) v3.1 2920×3h 实测（F1 305.0525、F2 317.0289 bn，B6 11.9764 bn，迭代 244 / 153，进程 2 10.90 / 5.62 h，峰值 RSS 116.4 / 106.7 GiB）；(b) 56 时段的 v4 − v3.1 实际差（D2c 冒烟对 v3.1 本机回归：ΔZ F1 +33.484、F2 +33.875 bn，ΔB6 +0.390 bn，迭代 89 / 80 对 96 / 81）；(c) 两种外推——平移（2920 的 Z_v4 = Z_v31 + ΔZ_56）与比例（Z_v4 = Z_v31 × Z_v4,56 / Z_v31,56）；(d) 第 8 节下界与一阶值；(e) LP 规模比 r = 1.0005。

| 量 | F1 一体化 | F2 `no_new_xb` | 说明 |
|---|---|---|---|
| 目标值（含常数项）最可能 | **336–339 bn** | **348–351 bn** | 平移 338.54 / 350.90；比例 336.03 / 348.40 |
| 目标值区间 | 325–350 bn（且 ≥ 报警线 315.17） | 337–362 bn（且 ≥ 331.50） | 56 时段与 2920 的 ΔZ 之比未知，取 ±约 12 bn |
| LP 值 `objective_lp`（= 目标值 − 常数项 2.366 / 2.537 bn） | 333.7–336.6 bn（区间 322.6–347.6） | 345.5–348.5 bn（区间 334.5–359.5） | 两种口径在 `hpr_status.sh` 同时显示 |
| barrier 迭代 | 最可能 210–260；区间 180–320 | 最可能 140–200；区间 120–260 | v3.1 244 / 153（F4 218）；56 时段 v4 比 v3.1 少 7 / 1 次；均低于止损参考 350 / 300 |
| 进程 2 峰值 RSS | 105–130 GiB | 95–120 GiB | r ≈ 1.0005；Gurobi 自报 `MaxMemUsed` 约高 25 %（F1 145–165 GB）；远低于止损线 240 / 200 GiB |
| 进程 2 用时 | 8–20 h | 4–12 h | v3.1 10.9 / 5.6 h；节点差 1.3 倍、迭代差 ±25 % |
| 进程 1 / 进程 3 / 后处理 | 1,000–3,500 s / 1,000–3,000 s / 1,000–3,500 s | 同左 | v3.1 实测；进程 1 低于超时 7,200 s |
| 早期测速外推 | 占止损线 207,360 s 的 15–45 % | 10–35 % | v3.1 外推 44,194 / 28,403 s |
| 作业时长 | 11–24 h | 6–16 h | 均远低于 walltime 96 h；批级作业 15–40 min |

- **B6 = Z(F2) − Z(F1)：符号为正（把握高）；最可能 11.8–13.0 bn，区间 10.5–14.5 bn。** 平移 12.37、比例 12.35；剔除 VN 退化对偶后的一阶 ΔB6 +0.49 → 12.47 bn。v3.1 中 56 → 2920 的 B6 变化为 −0.59 bn（12.56 → 11.98）。
- **各国 Owen 受益（对偶形式，α 0.5）的符号：** 方法——v3.1 2920 受益 + 56 时段上 v4 − v3.1 的受益变化（平移，INFERENCE；v3.1 自身 56 与 2920 的分国受益差可达数 bn、ID 与 LA 曾异号，所以只给符号与把握）。**为正（把握较高）：** BN（+0.08）、ID（+2.21）、KH（+0.11）、LA（+0.73）、MM（+0.32）、MY（+2.33）、SG（+3.17）、TL（+0.12）、VN（+3.67）；**大概率为正：** BUNKER（+0.36；燃料舱受益在 3 小时与日分辨率之间曾变号）；**不确定：** TH（−0.06，近 0）、PH（−0.65；v3.1 2920 为 +0.016，56 时段 v4 为 −0.54）。12 个参与者受益之和 = B6。
- **不在预测内：** 失败门的具体集合（只要求在 v3.1 并集内，第 7 节）；Owen 的 α 区间与市场形式（批级汇总照常给出）。

**与第 8 节的关系：** 预测的最可能区间都高于报警线（F1 336 > 315.2，F2 348 > 331.5）；若实测低于报警线，必有错（先查数据链，不改参数重试）；若实测落在预测区间之外而高于报警线，只记录，交审阅端。

## 10. 结果回收

- **每个运行结束后**（`hpc/hpr_status.sh` 显示 `ended`）：用户回收该运行的中间导出 `runs/batch6/export/<编号>/`（G1：单路一个 `tar` 打包 + `sha256sum`，不含 `*.nc`，见操作指南步骤 F1），不必等批级作业。
- **批级作业结束后**（G2）：`runs/batch6/results_light_final_*.tar.gz`、`results_full_final_*.tar.gz` 与各自的 `.sha256`（停批时 `*_halted_*`）。用户单路下载到 `D:\ResearchWorkspaces\ASEAN\work\p1_v4_w14_20261109\hpc_results_v4\`，本机核对 SHA256（PowerShell `Get-FileHash`）；先 light 后 full，一次一个文件。
- **60 天清除：** `/hpctmp` 中 60 天未改动的文件自动清除；LP / 解数组（约 2 × 7.8 GB，`ARRAYS_MANIFEST.json` 登记 SHA256）留在 `/hpctmp`，需要时在清除前另行下载。

## 11. 测试作业（登记为测试，不属于正式运行）

| 作业 | 队列 / 资源 | walltime | 内容 | 判据 |
|---|---|---|---|---|
| 环境安装 `hpr4_install`（通常不需要） | `serial`，`ncpus=1:mem=8gb` | 02:00:00 | 与 v3.1 同一锁文件；HPC 上已有环境，登录预检 `env` 节 key packages 一致即复用，不提交本作业 | `INSTALL_STATUS.txt` |
| **冒烟** `hpr4_smoke56`（正式提交前必须 PASS） | `parallel`，`ncpus=17:mem=32gb` | 04:00:00 | 作业体依次以 `JOB_MODE=smoke56` 运行 F1 体、F2 体、批级体：`TRUNCATE=56 ALLOW_UNREGISTERED=1 GUROBI_TIME_LIMIT_S=3000 WALL_CAP_S=3600`，标签 `SMOKE_TEST_ONLY`，运行目录 `runs/smoke56_v4`；两次 Gurobi 会话串行（间隔 ≥ 330 s） | `SMOKE_STATUS.txt`：F1、F2 optimal、ACCEPTED、后处理 0 错、批级 `DONE`；目标值与期望值（D2c 本机冒烟：F1 363,190,038,821.0828、F2 376,143,650,003.4369 EUR）相对差 ≤ 1e-6；`SMOKE_RESULT:PASS` |
| 全尺寸 BUILD_ONLY `hpr4_build_only_f1`（可选，审阅端要求时） | `parallel`，`ncpus=48:mem=300gb` | 03:00:00 | 只跑进程 1，记录峰值、LP 字节、构建与写出秒数；运行目录 `runs/build_only_f1_v4` | `BUILD_ONLY_STATUS.txt`：`BUILD_CHECK_F1 passed`；参考：峰值约 96 GiB、LP 约 5.5 GB、≤ 3,500 s |

- 测试作业的开关只在对应作业体内导出；正式作业在开关残留、授权缺失、运行目录含测试残留时拒绝（退出码 2）。
- **本机演练（第 3 节，`DRILL_REPORT.md`）：** 在包的解压副本中原样运行冒烟作业脚本 `pbs/hpr4_smoke56.pbs`（只加本机演练开关）与提交脚本的 dry-run；演练副本不在 work/ 下，不得上传。

## 12. 登记常数一览（检查单 H-P3 的比对清单）

| 常数 | 值 | 来源 |
|---|---|---|
| 登记状态 | **REGISTERED** | 定义文件 `limits_status` |
| 网络 SHA256 / 字节 F1、F2 | 第 1 节 | 定义文件 `registered_sha` / `registered_bytes` |
| 构建提交 | `59b128ea047de600adbd2a54e6e84b48a1544fe5` | 定义文件 `build_commit` |
| v4 开关集 / 表目录 / 配置哈希 | 第 1 节 | 定义文件 `v4_meta`（预检 `networks` 节） |
| TimeLimit / 进程 2 墙钟 / 间隔 | 259,200 / 266,400 / 330 | 定义文件 `limits`（`run_batch4.sh` 经 `hpc-plan` 读取） |
| 求解方式 | split | `run_batch4.sh` `R_MODE`、作业体 `SOLVE_MODE=split` |
| 进程 1 / 3 超时 | 7,200 / 32,400 | 定义文件 `limits` |
| 后处理单步 / 打包超时 | 10,800 / 7,200 | 定义文件 `limits` |
| 内存止损分数 | 0.80 | `b4_batch4.py` `MEMORY_STOP_FRACTION`、运行器缺省 |
| 早期测速分数 / 迭代参考（F1 / F2） | 0.80 / 350、300 | `b4_batch4.py` `PROJECTION_FRACTION`；定义文件 `iterations_reference`（运行器经 `runmeta` 读取） |
| 等待启动上限 | 7,200 | 定义文件 `limits` |
| 后处理并存内存条件 | 100 GiB | `b4_batch4.py` `POST_MEM_NEED_GIB`、运行器缺省 |
| PBS F1 | parallel / 48 / 300gb / 96:00:00 | 定义文件 `hpc_jobs` → `pbs/hpr4_f1.pbs` |
| PBS F2 | parallel / 48 / 250gb / 96:00:00 | `pbs/hpr4_f2.pbs`；`WAIT_START_OF=F1` |
| walltime 余量（每个正式作业 ≥ 7,200 s） | F1 29,670 / F2 15,270 | `b4_batch4.py walltime_components`（`per_job.margin_s`），一致性检查逐作业核对 |
| PBS 批级 | parallel / 12 / 120gb / 48:00:00 | `pbs/hpr4_batch.pbs` |
| PBS 冒烟 | parallel / 17 / 32gb / 04:00:00 | `pbs/hpr4_smoke56.pbs` |
| PBS BUILD_ONLY | parallel / 48 / 300gb / 03:00:00 | `pbs/hpr4_build_only_f1.pbs` |
| PBS 安装 | serial / 1 / 8gb / 02:00:00 | `pbs/hpr4_install.pbs` |
| 依赖 | F2 `after:F1`、批级 `afterany:F1:F2` | 定义文件 `hpc_jobs` → `hpc/hpr_submit.sh` |
| 一对 | A：F1 / F2 | 定义文件 `pair` |
| 冒烟期望值 | F1 363,190,038,821.0828；F2 376,143,650,003.4369 EUR（迭代 89 / 80） | 定义文件 `smoke_expected`（D2c 本机冒烟） |

## 13. 路径约定（HPC）

| 内容 | 位置 |
|---|---|
| 包目录（= `PBS_O_WORKDIR`，作业从这里提交） | `/hpctmp/<用户>/hpr4/`（新目录；v3 的 `hpr3/`、v3.1 的 `hpr31/` 保留不动） |
| 代码 | `/hpctmp/<用户>/hpr4/repo/`（预检 `sha` 节解包，`.package_commit` = `COMMIT`） |
| conda 环境 | `$HOME/miniforge3/envs/pypsa-earth`（HPR 步骤已装；预检 `env` 节核对，一致即复用） |
| 运行目录 | 正式 `runs/batch6/`；冒烟 `runs/smoke56_v4/`；BUILD_ONLY `runs/build_only_f1_v4/`（定义文件 `run_dirs` → `pbs/HPC_PLAN.txt` 的 `RUNDIRS` 行，作业体、提交与状态脚本都读这一行） |
| 结果包 | `runs/batch6/results_{light,full}_final_*.tar.gz`（+ `.sha256`） |
| 许可 | `$HOME/.gurobi/gurobi.lic`，`chmod 600`，用户自行放置（v3 / v3.1 时已放好） |
| 作业日志 | `/hpctmp/<用户>/hpr4/<作业名>.o<作业序号>` |

## 14. 同期禁止

HPC 冒烟与正式求解期间（冒烟作业开始到最后一个求解结束），本机与 AutoDL 不调用 Gurobi（WLS 许可共用）。

## 15. 与 v3.1 计划（`RUN_PLAN_HPC_V3.md`）的差异

| 项 | v3.1 | v4（本计划） |
|---|---|---|
| 运行 | F1–F4 两对（EV ×0.5 敏感性为第 B 对） | F1、F2 一对（敏感性 W19 另批） |
| 网络 | v3 构建 `a1ef782b`（72.0 / 71.4 MB） | v4 主算 W14 构建 `59b128ea`（82.7 / 82.1 MB），元数据开关集登记并预检 |
| TimeLimit / 进程 2 墙钟 | 864,000 / 871,200 s | **259,200 / 266,400 s** |
| 进程 1 超时 | 5,400 s | **7,200 s** |
| 参考迭代 | 350 / 250 / 350 / 250 | **350 / 300** |
| walltime | 260 / 262 / 260 / 262 h，批级 48 h | **96 / 96 h**，批级 48 h |
| 依赖 | F2 after:F1；F3 afterany:F1；F4 afterany:F2；批级 afterany:F3:F4 | **F2 after:F1；批级 afterany:F1:F2** |
| 作业名 | `hpr3_*` | **`hpr4_*`** |
| HPC 目录 / 运行目录 | `hpr31/`，`runs/batch5`、`runs/smoke56_v31` | **`hpr4/`，`runs/batch6`、`runs/smoke56_v4`、`runs/build_only_f1_v4`** |
| 运行器 / 状态脚本 | v3.1 `run_batch4.sh`、`hpr_status.sh` | D1 副本：包 `COMMIT` 写入 `RUN.json` 与回执；状态同时显示含常数项目标值与 LP 值 |
| 预检 | v3.1 `preflight.sh` | + v4 开关集与网络元数据一致性检查（`networks` 节） |
| 冒烟期望值 | v3 本机冒烟 329.71 / 342.27 bn | D2c 本机冒烟 363.19 / 376.14 bn |
| 批级对照 | v3 365×24h、56 时段冒烟 | v3.1 2920×3h 主对照、D2c 与 v3.1 的 56 时段冒烟 |
| 报警线 / 预测 | 第 26 节预测 | 第 8 节报警线（v3.1 全年对偶）+ 第 9 节预测 |
| 环境、档案、求解方式、验收、止损分数、许可规则 | — | 不变 |
