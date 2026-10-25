# 第四批运行计划（RUN_PLAN_B4）——2920×3h，F1 一体化 / F2 不互联，分进程求解

**版本：** B4P v1，2026-10-26（事先登记：本文件第 3 节的规则在看到任何 2920×3h 结果之前登记，之后不得修改；第 4–6 节的数值来自 B4P 的本机实测与外推，依据见 `B4P_REPORT.md` 第 1–2 节）。依据 `B4P_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `995ff344…8378b2`）A4 节与用户补充 1、2（2026-10-26 03:15 SGT）。
**状态：** 只是准备。实际上云在用户租机并授权后，按另一份执行指令进行。
**入口：** `run_batch4.sh`（运行与逐运行 / 批级后处理；第三批 `run_batch3.sh` 的同一套函数加第 3 节的新规则）、`preflight.sh`（预检）、`pack_results.sh`（结果打包，第三批同一文件）、`env/install_env.sh`（环境安装，B4P A3.3 支持按频道镜像）。运行表与阈值的唯一来源是代码中的 `scripts_project/b4_batch4.py`（`RUNS`、`MEMORY_STOP_FRACTION`、`PROJECTION_FRACTION`、`P1_*`）与 `run_batch4.sh` 顶部的登记常数（`R_TL`、`R_WALL`、`R_GAP`、`R_MODE`）。

---

## 1. 网络与代码

- **基础网络（指令第 0 节登记）：** M08b 补充 01 构建（提交 `ec80668f`，主检出 `results_project/m08b/builds_s01/`）的两个完整 2920×3h 网络。预检与运行脚本第 0 阶段同时核对构建回执（`network.sha256`、`code_sha`）与下表登记值（SHA256 与字节数）；两者任一不符即 `STOP_SAFE`。

| 文件 | 用途 | 大小（B） | SHA256 |
|---|---|---|---|
| `networks/integrated_2920_3h_unsolved.nc` | F1 | 64,106,133 | `bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab` |
| `networks/disconnected_2920_3h_unsolved.nc` | F2 | 63,439,167 | `b401a68729524c885a8245962bc2a46706a1760c42ef40bdd9943e60a859bcc7` |

- **365×24h 网络不入包**（预检发现即失败）。无变体。
- **代码：** 部署包提交（`COMMIT`）的 `git archive`，不含顶层 `research/`；含 B4P 的改动：`s2_solve.py`（`--split-stage build|assign`；求解后先落盘再记账：A3.1）、`b4_split_solve.py`（进程 2）、`b4_batch4.py`、`run_batch3.sh` 路径规范化（A3.2）、`install_env.sh` 按频道镜像（A3.3）。模型、网络、成本表、档案的求解参数、验收阈值与第三批相同，一律未改。
- **成本表：** 各自基础构建的 `costs_active_research.csv`。

## 2. 运行清单

档案 **`formal_barrier_1e6_t16`**（第三批 `PROFILE_CHOICE.json`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200）。

| 编号 | 运行 | 网络 | 情景 | 档案 | Threads | TimeLimit（s） | 墙钟（s，进程 2） | 成本表 | 作用 | 参考迭代数（3.4） |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | 一体化 2920×3h | `integrated_2920_3h` | integrated | 1e-6 T16 | 16 | 259,200 | 266,400 | integrated | c(N)、Owen 分摊、B6 基准 | 450 |
| F2 | 不互联 2920×3h | `disconnected_2920_3h` | disconnected | 1e-6 T16 | 16 | 259,200 | 266,400 | disconnected | B6 = F2 − F1 | 250 |

- 求解调用（每个运行一次，`SOLVE_MODE=split`，第 3.1 节）：进程 1 `s2_solve.py … --label BATCH4_2920X3H --split-stage build`（无许可）→ 进程 2 `b4_split_solve.py --run-dir runs/batch4/<编号> --remove-lp`（唯一的 Gurobi 进程）→ 进程 3 `s2_solve.py … --split-stage assign`（无许可，映射回网络并导出）。运行目录 `runs/batch4/<编号>/`，导出 `runs/batch4/export/<编号>/`，状态 `runs/batch4/STATUS.txt`。

## 3. 事先登记的规则（看结果前不得修改）

### 3.1 时限、墙钟与求解方式

1. 每个运行 **TimeLimit 259,200 s（72 h）**（指令 A4 第 1 项），不重试、不改参数、不 warm start。**风险登记：** A1 外推 F1 在 8470Q T16 的 barrier 用时为 9.5–146 h，中值约 56 h（第 4 节）；时限可能不够是已知风险，由 3.4 的早期测速在前约 20 次迭代后判定并止损，之后按 3.8 由用户决定是否以更长的登记时限重新开始。
2. **墙钟 266,400 s = TimeLimit + 7,200 s**，适用于进程 2（Gurobi 进程：读入 LP 文件、求解、写出解数组）。余量 7,200 s = 2 × 3,600 s：A1 外推 2920×3h 的 LP 文件读入 95–154 s、解数组按标签提取与写出不超过约 1,800 s（56 时段 1 s，按变量数线性放大），合计 < 3,600 s。进程 1（构建 + 写 LP 文件；外推 10–15 min，云端单核较慢按 1.35 倍计约 20 min）`timeout` **3,600 s**；进程 3（重建 + 映射 + 导出；按 56 时段 152 s 线性放大约 2.2 h，×1.35 约 3 h）`timeout` **32,400 s**（3 倍）。到达墙钟或超时终止整个进程组（TERM，30 s 后 KILL）；回执不含终止条件的视为求解前回执。
3. **求解方式 = 分进程（`R_MODE=split`）**：B4P 的等价判据成立（Fingerprint 相同；56×3h 完整求解的终止状态、迭代数、工作单元、目标值、解与对偶数组及全部导出逐位相同，`B4P_REPORT.md` 第 3.1 节），登记为第四批执行方式。三个进程使用同一网络、同一参数；进程 2 读入的 LP 文件由进程 1 用 linopy 的同一写出器生成；进程 3 核对重建模型的标签向量与进程 1 逐位相同后才映射。
4. 脚本拒绝启动：时限、墙钟、许可间隔、求解方式与本节登记值不同（只有测试和本机干跑可用 `ALLOW_UNREGISTERED=1`）；正式运行发现任何测试钩子即拒绝；无求解模式与 `--auth` 同时出现即拒绝。

### 3.2 顺序与并发（P1 探针）

1. 先启动 F1。F1 的 Gurobi 进程（进程 2）启动后监控 **3,600 s**（`P1_WINDOW_S`；覆盖读入、预求解、排序与首次因子分解的内存峰值——A1 外推 2920×3h 预求解 + 排序约 1,400–5,700 s，首次迭代在其后）。
2. 探针判定（`b4_batch4.py p1`）：取 `MONITOR_F1.csv` 前 3,600 s 内 cgroup 匿名内存（无 cgroup 时取进程组 RSS）的峰值；**峰值 ≤ 实例内存配额的 40 %（`P1_THRESHOLD`）且容器核数 ≥ 33（`P1_MIN_CORES`，16 + 16 线程加后处理）→ 立即启动 F2 并行**；否则 F2 等 F1 结束（含后处理）后再启动。阈值理由：F1、F2 两个 Gurobi 进程峰值之和（A1 中值 124 + 104 GiB，高值 160 + 149 GiB）须 ≤ 80 % 配额（3.3 的止损线）；F1 占 40 % 以内时 F2（不超过 F1 的 1.2 倍）之和不超过 80 %。按 A1，只有 ≥ 343 GiB（368 GB）的配置可能通过探针，240 GB 配置必然串行。
3. 许可间隔（学术 WLS）：上一 Gurobi 进程结束到下一次启动 ≥ **330 s**；距本脚本启动 ≥ 330 s。F2 与 F1 并行时两个会话 ≤ 许可上限 2。
4. 每次启动前检查：其他 `b4_split_solve.py` 进程不超过 1 个。

### 3.3 内存止损

- 监控每 60 s 读 cgroup `memory.stat` 的 **匿名内存**（v2 `anon`；v1 `rss`；**不含可回收的文件缓存**，第三批 S1 的教训）。任一时刻匿名内存 > 配额的 **80 %（`MEMORY_STOP_FRACTION`）** → 终止正在运行的 Gurobi 进程组，写 `STOP_SAFE:MEMORY:<编号>`，不再启动任何求解，报告用户。配额 = cgroup `memory.max`（无限制时取 MemTotal；`MEM_QUOTA_GIB` 可显式给出）。
- 80 % 的理由：Gurobi 排序 / 因子分解阶段的内存在几秒内可增长 10 %（本机 C4 从 8.9 到 10.5 GB 用了 3 s），留 20 % 给监控间隔内的增长与内核 / 文件缓存；超过 80 % 后剩余余量也容不下进程 3（A1：72–92 GiB）。

### 3.4 早期测速

- F1 的 Gurobi 日志记录到第 **20** 次 barrier 迭代后，用第 11–20 次迭代的平均耗时（日志时间列 t20 − t10 除以 10）× **450** + 已用时间（自进程 2 启动）得到预计总用时；**超过 TimeLimit 的 80 %（`PROJECTION_FRACTION`，207,360 s）→ 终止该进程组，写 `STOP_SAFE:PROJECTION:<编号>`**，报告用户。F2 同理，迭代数按 **250**。只在首次满 20 次迭代时判定一次（无提示重启不改变迭代计数）。
- 450 / 250 的依据：第三批 365×24h 一体化 253–465 次、不互联 116–228 次（R1–R11），取上限并留余量。A1 中值估计 F1 每次迭代约 580 s（8470Q T16）：20 次迭代后约 3.5 h 即可判定。

### 3.5 验收与停批

1. GATES_V6（G1 = C1 (a)(b)(c)，G2.1 网络 SHA256 = 登记值且回读精确，G2.2 配置子集哈希，G2.3 导出完整）；标签 ACCEPTED_LAYER2 / ACCEPTED_LAYER1 / NOT_ACCEPTED；求解器状态不是判据。本批 C1 参照由 F1、F2 生成（`BATCH_REFERENCE.json`）：先用缺省参照临时判定，参照生成后重评（`grade_history` 保留，临时标签另存 `V6_ACCEPTANCE_PROVISIONAL.json`）。
2. **分级（`b4_batch4.py stop-class`）：** G2 不通过 → 停批；无返回解（`solution/X.npy` 缺失：墙钟终止、求解失败、内存不足、到 TimeLimit 无可用解）或 C1 (a) 不通过 → 记为**不可用**（`UNUSABLE`）**并停批**（第四批只有两个运行，没有"其余运行继续"）；只有 C1 (b)/(c) 不通过 → 不停批。停批 = 不再启动新的求解；正在跑的另一个求解跑完并做后处理；批级汇总与结果打包照常写出；退出码 3。
3. **求解后异常（A3.1）：** 求解返回后先写终止状态、目标值、迭代信息，再写解与对偶数组，然后做导出 / 账本 / 门控；任一步异常记入回执 `post_solve_errors`，不改变终止状态与"有返回解"的判定；G2.3 照常核对导出完整性，缺项事后 `--repost` 补做。
4. **`SoftMemLimit`（A2.2）：不作为登记参数。** 本机未能用 Gurobi 调用验证"不触发时逐位相同"（8 次调用全部用于 A1 与分进程），按无人值守规则不采用。`b4_split_solve.py --protect SoftMemLimit=<GB>` 的通道保留；若用户决定采用（建议值 = 配额 GB × 0.85，高于 3.3 的 80 % 止损线，作为第二道保护），由执行指令登记后以 `PROTECT_PARAMS` 传入；触发时 Gurobi 状态 MEM_LIMIT（代码 17）→ linopy 终止条件 `internal_solver_error`、无解 → 按第 2 项"无返回解"处理（替身测试已覆盖该路径）。

### 3.6 每次求解后的后处理与资源条件

1. 顺序：违反量分析 → C1（参照见 3.5）→ M12 分摊（`--register`）与 Owen 对偶形式审计 → GATES_V6 → 分级分类 → 导出 `export/<编号>/`；违反分析与 C1 失败后重做一次（M10A D2）。
2. **与另一个运行求解并存的条件：** 后处理每步启动前读 cgroup 匿名内存；另一运行的 Gurobi 进程在跑且 **配额 − 匿名内存 < `POST_MEM_NEED_GIB` = 100 GiB** → 排队（每 60 s 复查），直到该求解结束或内存释放。100 GiB 的依据：违反量分析、C1、Owen 审计都重建 LP 模型（进程 1 的峰值：A1 外推 72–92 GiB，一体化）；取高值并留 10 %。
3. 单步超时 `POST_TIMEOUT_S` = **10,800 s**（3 倍余量：第三批 365×24h 云端违反分析 105 s、C1 72 s，本机 Owen 审计 54 s、M12 6.5 s；按 2920 为 365 的 8 倍线性放大约 15 min / 10 min / 7 min / 1 min，再按云端单核 1.35 倍计 ≤ 1 h）；超时或异常记 `POSTPROC_ERROR`，调度不变，事后 `POST_ONLY=1` 补做。
4. 线程预算：辅助步骤 OMP/MKL/OPENBLAS/NUMEXPR = 容器核数 − 正在运行的求解线程数（≥ 1）。

### 3.7 批级

1. **B6 = F2 − F1**（`v5_gates.gate_b6_cost`，目标值），分国账本差（11 国 + ASEAN）；
2. **Owen 对偶形式分摊**（主值 α 0.5，α 区间，市场形式并列，燃料舱作为参与者；`m12_allocation.py benefit`）与受益、比例规则对照；
3. **与第三批 365×24h 同名结果的对比**（R1 ↔ F1、R2 ↔ F2：目标值、B6、Owen 主值）：只描述，作为"分辨率影响"的证据，不判定（`BATCH4_SUMMARY.md`，`BATCH3_EXPORT=<第三批 export 目录>` 时生成）；
4. 汇总 `BATCH4_SUMMARY.json / .md`（含停批、安全停止、不可用、P1 判定、早期测速、求解后异常）。

### 3.8 资源止损后与安全停止

- 内存止损、早期测速止损、墙钟终止后：在更大的机器上**从头开始同一运行（参数不变）**，视为资源原因的重新开始，不算"重试"；每次都需要用户明确授权，并在报告中登记（新的 `RUN_DIR`）。早期测速止损后若用户决定延长时限，须在新的执行指令中登记新的 `R_TL` / `R_WALL`（求解参数不变）。
- 续跑时发现某运行"已开始但未结束"：不重跑，`STOP_SAFE:INTERRUPTED`，等用户；启动时已有求解进程、基础网络 SHA256 或字节数与登记值不符、缺少输入文件 → `STOP_SAFE`。
- 断点续跑：同一命令再次执行即续跑（`runs/batch4/`）：已结束的求解一律跳过；后处理各步只补缺失的输出。

## 4. 资源估计（INFERENCE；方法与数据点见 `B4P_REPORT.md` 第 1 节）

| 量 | F1 一体化（低 / 中 / 高） | F2 不互联（低 / 中 / 高） | 性质 |
|---|---|---|---|
| LP 行 / 列 / 非零 | 7.94–8.03e7 / 3.52–3.60e7 / 1.87–1.88e8 | 7.67–7.76e7 / 3.41–3.48e7 / 1.79–1.80e8 | INFERENCE（三点拟合，指数 ≈ 1） |
| Factor NZ | 4.5e9 / 6.7e9 / 8.4e9 | 2.2e9 / 2.3e9 / 2.9e9 | INFERENCE（稠密列区间两点 + 云端 365 锚定） |
| Factor Ops | 3.5e13 / 1.5e14 / 2.9e14 | 8.2e12 / 2.7e13 / 3.1e13 | INFERENCE |
| 进程 1（构建 + 写 LP）峰值 | 72–92 GiB | 68–79 GiB | INFERENCE（56–224 五点） |
| 进程 2（Gurobi）峰值 | 90 / 124 / 160 GiB | 68 / 104 / 149 GiB | INFERENCE |
| 进程 3（映射 + 导出）峰值 | 79–115 GiB | 75–99 GiB | INFERENCE |
| 分进程最大 | 90 / 124 / 160 GiB | 75 / 104 / 149 GiB | |
| 单进程峰值 | 162 / 206 / 253 GiB | 136 / 178 / 228 GiB | INFERENCE（进程 1 + 进程 2） |
| 8470Q T16 每次迭代 | 135 / 580 / 1,127 s | 31 / 150 / 218 s | INFERENCE（云端 T16 速率 × Ops） |
| barrier 用时（8470Q） | 9.5 / 56 / 146 h | 1.0 / 7 / 14 h | 迭代数 253 / 350 / 465；116 / 170 / 228 |
| 8352V（×1.15–1.5） | 11 / 77 / 218 h | 1.2 / 9.4 / 21 h | CPU 因子为假设 |
| EPYC 9754（×1.0–1.3） | 9.5 / 65 / 189 h | 1.0 / 8.2 / 18 h | CPU 因子为假设 |
| LP 文件（读后删除） | 5.1–5.4 GB | 5.0–5.2 GB | INFERENCE（五点，指数 1.03） |
| `lp/` 数组 | 6.3–6.4 GB | 6.1 GB | |
| 解数组 X / Pi / RC | 1.2 GB | 1.2 GB | |

## 5. 候选配置与实例规格

| 配置 | 分进程 F1 可跑（中 / 高） | 单进程可跑 | F2 并行（中 / 高） | 总用时 h（低 / 中 / 高） | 费用 ¥（低 / 中 / 高） | 主要风险 |
|---|---|---|---|---|---|---|
| AutoDL CPU 4 份（128 核 8352V / 240 GB） | 是 / 是 | 否 | 否 | 18 / 91 / 106 | 54 / 281 / 329 | F1 中值 77 h 超 72 h 时限；8352V 速率为假设 |
| AutoDL vGPU-48GB 4 卡（100 核 8470Q / 368 GB） | 是 / 是 | 是 / 是 | 是 / 否 | 14 / 63 / 82 | 156 / 730 / 943 | F1 中值 56 h 接近时限；并行只在中值内存下可行 |
| AutoDL RTX 4090D 4 卡（72 核 EPYC 9754 / 240 GB / 60 GB 盘） | 是 / 是 | 否 | 否 | 16 / 82 / 103 | 120 / 618 / 775 | F1 中值 65 h 接近时限；EPYC 9754 速率为假设；数据盘 60 GB 需 `REMOVE_LP=1` |
| 阿里云 r8i 256 GiB | 是 / 是 | 否 | 否（核数 < 33） | 16 / 73 / 99 | 以控制台为准 | 同上；核数不足并行 |
| 阿里云 r8i 512 GiB | 是 / 是 | 是 / 是 | 是 / 是 | 14 / 63 / 82 | 以控制台为准 | 费用 |

- "总用时"含两次运行的 barrier（F1 按 72 h 封顶）、进程 1 / 3、后处理与许可间隔；并行只在探针通过时。
- **推荐（能跑且最稳 → 最省钱）：** ① AutoDL vGPU-48GB 4 卡 8470Q / 368 GB（内存余量最大、CPU 速率有实测、F2 可并行）；② 阿里云 r8i 512 GiB（同样稳，单价待查）；③ AutoDL RTX 4090D 4 卡 EPYC 9754 / 240 GB（最省钱的可跑配置：分进程 F1 高值 160 GiB 仍在 80 % 配额 178 GiB 内，但余量小、串行、速率为假设）。CPU 4 份 8352V 最便宜但最慢。机器选择由用户决定。
- **实例规格（预检硬下限）：** 核数 ≥ 25；内存配额 ≥ **190 GiB**（分进程 F1 高值 160 GiB / 0.80 = 200 GiB，取 240 GB 一档的 223 GiB 能通过的下限）；数据盘在装好环境后可用 ≥ **45 GB**。并行需要 ≥ 33 核与 ≥ 343 GiB。

## 6. 磁盘用量与 60 GB 数据盘（补充 1）

- 持久用量（两个运行）：`lp/` 数组 2 × 6.4 GB + 解数组 2 × 1.2 GB + 对偶 NetCDF 2 × 0.6 GB + 求解后网络 2 × 1.3 GB + 导出副本 2 × 2.1 GB + 结果包 2 × 2.1 GB + 环境 3.3 GB + conda 缓存 0.75 GB + 部署包 0.4 GB ≈ **36 GB**；瞬时：LP 文件 5.4 GB（进程 2 读入后删除，`REMOVE_LP=1`）；两份 LP 文件都保留时约 46 GB。
- 60 GB 数据盘（4090D 配置）：**够用**（36 GB + 5.4 GB 瞬时 < 60 GB；预检要求装环境后可用 ≥ 45 GB）。压缩手段（登记）：`REMOVE_LP=1`（默认）；`TMPDIR` 在数据盘的运行目录内；结果包写出后可移到文件存储（`/root/autodl-fs`，免费 20 GB）；`lp/` 数组在 `export/batch/ARRAYS_MANIFEST.json` 登记后可按需移到文件存储。

## 7. 演练要求

打包前对两个基础网络类型在截短 2920×3h 网络上演练完整后处理链（56 个时段用真实本机结果，最大截短 182 用合成解），记录各步的耗时与峰值（`DRILL_B4.json`；`make_package.sh` 要求 `DRILL_JSON` 指向包提交的演练结果）。

## 8. 云端步骤（主机、端口、密码不写入任何文件）

1. 单路上传部署包 v7 → 全量 `sha256sum -c SHA256SUMS`；
2. `bash env/install_env.sh`（镜像：`CONDA_MIRROR_CONDA_FORGE` / `_BIOCONDA` 可设国内镜像，`CONDA_MIRROR_GUROBI` 不设即直连；先 `--check-mirrors`）；
3. 放置许可 → 在将要运行的同一 tmux shell 中 `PY=… GRB_LICENSE_FILE=… bash preflight.sh` → `PREFLIGHT OK`；
4. `PY=… GRB_LICENSE_FILE=… BATCH3_EXPORT=<可选> bash run_batch4.sh --auth "<用户授权原文>"`；中断后同一命令续跑；只重做后处理：`POST_ONLY=1 PY=… bash run_batch4.sh`（不带 `--auth`）；
5. 监控 `runs/batch4/STATUS.txt`、`MONITOR_F1.csv`（`cgroup_anon_gib` 列）、`PROJECTION_F1.json`（约 3.5 h 后）、`P1_DECISION.json`（1 h 后）；`STOP_SAFE:MEMORY` / `STOP_SAFE:PROJECTION` / `STOP_NOT_ACCEPTED` / `UNUSABLE` 即停批等用户；
6. 回收：先轻量包，再完整包（含求解后网络与对偶 NetCDF）；LP / 解数组留在实例数据盘（`ARRAYS_MANIFEST.json`）；删除许可并核实。
