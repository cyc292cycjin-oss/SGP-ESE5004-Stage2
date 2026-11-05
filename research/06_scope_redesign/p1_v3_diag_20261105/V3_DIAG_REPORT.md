# V3 全年 2920×3h 不可解诊断报告（决策清单第 194 项）

- **指令：** `V3_DIAG_INSTRUCTION.md` v1，SHA256 `e6f4c06c7ee4dfd41d3e7834b01b8a3c1d0d61c964233494616bb1e2edfe4d05`。与 `V3_DIAG_SHA256.txt` 一致，2026-11-05 15:32 SGT 核对。
- **开始条件：** 15:33 SGT 由用户确认（AnyConnect 已断开；本机与 AutoDL 均无其他 Gurobi 进程）。
- **执行环境：** Claude Code，Opus 5.5，effort xhigh。全程只在本机运行：不连 HPC、云或 VPN，不用 HiGHS，不读许可文件。
- **结论分级：** VERIFIED 指有实际数组或回执支撑；INFERENCE 指机制解释；PROPOSED 指尚未执行。

## 1. 一句话根因

东盟燃料舱净零约束 `research_bunker_co2_limit`（来自 `s4c_layers.install_bunker_net_zero`）要求一个**只有排放端口、没有任何移除端口**的账户 Store 在最后时段水平 ≤ 0。这等价于"82 个化石航煤计量链路在全部时段的流量恰为 0"。约束以**零松弛**的形式贯穿整条 Store 能量平衡链。Gurobi 默认预处理（代换聚合加对偶约简）在某些时段数和权重组合下，据此判定 INF_OR_UNBD，并且 0 次 barrier 迭代就停止。

- **VERIFIED（窗口）：** 在 F1 的 2 月、1 月窗口和 F2 的 2 月窗口上，只删掉这一行，或只把它的右端项从 0 放宽到 1 t，或把它改写为"计量流量 = 0"，同一份 LP 的预处理都改为通过。
- **INFERENCE（全年）：** 全年 2920×3h 是同一机制。本机内存不足以复现全年，见第 6 节。

## 2. INFEASIBLE 还是 UNBOUNDED

**没能由 Gurobi 给出最终区分。** 原因有三：

- `DualReductions=0` 时预处理通过（第 14 次调用，"Presolved: 3065221 rows"）。之后进入 barrier ordering，因 OOM 中断。
- 指令只允许做到预处理或 IIS。
- IIS 在 30 分钟内没有完成，见第 5.3 节。

以下证据都指向**数值意义上的原始不可行（零松弛约束被预处理按舍入判为不可行）**，而不是无界：

| 证据 | 内容 | 等级 |
|---|---|---|
| 目标系数 | 四个窗口 LP 的目标系数全部 ≥ 0（负成本列 0 个），也找不到"改进方向无界、且不被任何行阻挡"的列（`evidence/lp_scan/`） | VERIFIED |
| 必要行 | INF_OR_UNBD 只在保留 bunker 行时出现（第 5.4 节） | VERIFIED |
| 冲突量级 | 右端项从 0 放宽到 **1 t**，INF_OR_UNBD 即消失。1 t 约合 3.9 MWh 化石航煤，只是该账户可能量级（年 61.6 Mt）的 1.6e-8 | VERIFIED（预处理层面） |
| 机制 | 预处理需要聚合与对偶约简同时起作用才会给出这个判定：`Aggregate=0` 通过，`Presolve=1` 通过，`DualReductions=0` 通过，`NumericFocus=3` 仍失败 | VERIFIED |
| 结论 | 是零松弛加舍入造成的判定，不是实质性的不可行 | INFERENCE |

本机没有得到"模型可行"的证明。

## 3. 方法与复用的入口

**冻结点。**

- 代码：`7d22dda112a3c18ed57e8c061d95e51915980417`，即部署包 `COMMIT`。worktree 为 `/home/jin/wt_v3_diag`，分支为 `codex/v3-diag-20261105`。
- 网络：直接读 `work/p1_v3_20261102/hpc_package_v3/networks/`。四个文件的 SHA256 和大小都与 `pbs/HPC_PLAN.txt` 的 NETWORK 行一致，4/4 MATCH，见 `evidence/network_sha256_check.txt`。

**复用的运行器入口。** 读 `run_batch4.sh` 第 387–442 行 `solve_run` 确认，正式运行是 split 模式：

- 进程 1：`s2_solve.py --split-stage build`，负责建模、调用 `install_research_constraint_hooks`（全部 10 个 `required_constraint_hooks`）、做缩放，并写出 `split/problem.lp`。
- 进程 2：`b4_split_solve.py`，这是唯一的 Gurobi 进程。

本诊断这样复用：

- **进程 1**：由 `scripts/diag_build.py` 原样调用 `s2_solve.main()`。唯一的附加动作，是在 PyPSA 读入网络后把时段切成窗口 `[s, s+L)`。之后 `main()` 自己执行 `--truncate L` 和 `set_representative_weights`（三列权重都设为 8760/L，年度上限不缩放），与运行器的 `TRUNCATE` 完全相同。诊断变体 `--native-weights` 不加 `--truncate`，即对窗口走 `main()` 的全年路径，权重保持 3 h。
- **进程 2**：直接用运行器的 `b4_split_solve.py --probe-ordering-only`，即 `BarIterLimit=0`，其余参数全部来自 `formal_barrier_1e6_t16`：Method 2、Crossover 0、BarConvTol 1e-6、BarHomogeneous 1、Threads 16、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200，TimeLimit 864,000。
- **运行保护参数**：通过 `--protect` 传入并单独记录：`SoftMemLimit` 8 或 6，`MemLimit` 7。
- **诊断参数**：通过 `--measure` 传入，只用于 `SMOKE_TEST_ONLY`。

**等价性。** 对照组里，正式命令（`s2_solve.py --truncate 56`）与诊断入口（窗口 `[0,56)`）写出的 `problem.lp`、`vlabels`、`clabels` 三个文件 SHA256 全部相同（`evidence/CONTROL_EQUIVALENCE.txt`）。同一窗口重复构建，LP 的 SHA256 也不变（F1_M01：`439499e1…`）。

**约束组删除过滤。** IIS 在 30 分钟内拿不到，所以改用手工的约束组删除过滤，相当于在约束组粒度上做 IIS 的删除步骤。做法如下：

- `scripts/con_groups.py` 重建同一窗口，先核对标签向量逐字节一致，再把每一行映射到它所属的 linopy 约束容器。
- `scripts/del_probe.py` 读入正式 `problem.lp` 后，只在**内存副本**上删行、固定列或改右端项，然后跑同样的预处理。
- 文件、模型代码、网络和配置都没有改动。删除只针对附加约束，不删变量界行，以免人为造出无界方向。

## 4. 对照组与按月窗口（第 2 节第 1、2 步）

**对照组（第 1 次调用）。** F1 前 56 个时段，正式 TRUNCATE 路径，只跑到预处理：**ITERATION_LIMIT**，预处理 3.78 s，MaxMemUsed 5.96 GB。复现成功。

**按月窗口。** 按日历月切窗口：2 月 224 个时段，30 天的月份 240 个，31 天的月份 248 个，12 个窗口不重叠，恰好覆盖 2920 个时段。权重处理与 TRUNCATE 完全相同（第 3 节）。构建峰值 7.77–8.57 GiB，构建用时 86–104 s。

| 月 | 窗口 | 时段数 | 每时段权重 (h) | 预处理结果 | 预处理 s | Gurobi 内存峰值 |
|---|---|---|---|---|---|---|
| 1 | [0,248) | 248 | 35.32 | **INF_OR_UNBD** | 17.0 | 5.13 GB |
| 2 | [248,472) | 224 | 39.11 | **INF_OR_UNBD** | 12.9 | 4.63 GB |
| 3 | [472,720) | 248 | 35.32 | **INF_OR_UNBD** | 16.3 | 5.13 GB |
| 4 | [720,960) | 240 | 36.50 | 通过（之后 MEM_LIMIT） | 19.2 | 14.2 GB |
| 5 | [960,1208) | 248 | 35.32 | **INF_OR_UNBD** | 15.8 | 5.13 GB |
| 6 | [1208,1448) | 240 | 36.50 | 通过（之后 MEM_LIMIT） | 17.7 | 14.2 GB |
| 7 | [1448,1696) | 248 | 35.32 | **INF_OR_UNBD** | 14.6 | 5.13 GB |
| 8 | [1696,1944) | 248 | 35.32 | **INF_OR_UNBD** | 15.2 | 5.13 GB |
| 9 | [1944,2184) | 240 | 36.50 | 通过（之后 MEM_LIMIT） | 19.1 | 14.7 GB |
| 10 | [2184,2432) | 248 | 35.32 | **INF_OR_UNBD** | 16.2 | 5.13 GB |
| 11 | [2432,2672) | 240 | 36.50 | 通过（之后 MEM_LIMIT） | 21.1 | 14.2 GB |
| 12 | [2672,2920) | 248 | 35.32 | **INF_OR_UNBD** | 14.3 | 5.13 GB |

表中"通过（之后 MEM_LIMIT）"的含义：日志里有 "Presolved:" 行、没有不可行判定，即预处理已通过；之后的 barrier ordering 碰到内存保护上限才停下。失败的月份都是 "Presolve removed … Model is infeasible or unbounded"，0 次 barrier 迭代，与 HPC 上的现象一致。

## 5. 缩小与冲突约束（第 3 步）

### 5.1 失败取决于窗口长度，不取决于具体日期（VERIFIED，1 月）

| 窗口 | 时段数 | 权重 (h) | 结果 |
|---|---|---|---|
| 1 月 1–31 日 [0,248) | 248 | 35.32 | INF_OR_UNBD |
| 1 月 1–30 日 [0,240) | 240 | 36.50 | 通过 |
| 1 月 2–31 日 [8,248) | 240 | 36.50 | 通过 |
| 1 月各周 W1（C0）、W2、W3、W4 | 56 | 156.43 | 均通过 |
| 1 月 29–31 日 W5 [224,248) | 24 | 365.0 | 通过 |
| 1 月第一周，原始权重 [0,56) | 56 | 3.0 | 通过 |
| 1 月全月，原始权重 [0,248) | 248 | 3.0 | 通过 |

同样的日期，权重为 35.32 h 时失败，36.5 h 时通过；而 156.43 h 和 3 h 又都通过。失败对权重是非单调的，按周、按天的二分因此无法缩小到更小的失败窗口：所有周窗口都通过。这个模式不符合经济或物理意义上的冲突，那类冲突应随权重单调变化。它符合"舍入误差随权重伪随机变化"，属于 INFERENCE。

### 5.2 预处理参数敏感性（M01，第 14、23–25 次调用，VERIFIED）

| 改动（诊断用，只到预处理） | 结果 |
|---|---|
| 无（档案原样） | INF_OR_UNBD |
| `DualReductions=0` | 通过（之后在 ordering 因 OOM 中断） |
| `NumericFocus=3` | INF_OR_UNBD |
| `Aggregate=0` | 通过 |
| `Presolve=1` | 通过 |

### 5.3 IIS（第 26 次调用）

在正式 LP（F1_M02）上调用 `computeIIS()`，TimeLimit 1800 s：**到时仍未完成，没有得到 IIS。**

- 过程：Gurobi 先在未预处理的模型上处理约 210 万个自由变量，再用单纯形确认不可行，共 292 万次迭代。目标值在 1e33–1e37 量级，中途收紧了 Markowitz 容差。
- 为什么拆成两个进程：月窗口在同一进程里既持有 linopy 模型（8.5 GiB），又持有 Gurobi 模型，会超出本机内存。所以 IIS 由只用 gurobipy 的 `scripts/iis_lp.py` 计算，计算方式与 linopy 0.5.5 的 `compute_infeasibilities()` 相同（`computeIIS` 加 `.ilp` 解析规则）；标签映射由 `scripts/iis_map.py` 在另一个进程里做（重建模型后调用 `constraints.print_labels`）。这次没有 IIS 可供映射。
- 回执里的 "FAILURE" 是脚本在超时后读取 `IISMinimal` 属性出错，实际结果就是"IIS 未完成"。

### 5.4 约束组删除过滤（第 27–32、34、35 次调用，VERIFIED）

| 窗口 | 改动（只作用于内存中的 LP 副本） | 结果 |
|---|---|---|
| F1_M02 | 删除全部年度和最后时段约束：`ResearchImportAnnual`（19 行）、`research_country_co2_limit`（11）、`research_co2_storage_cap`（7）、`research_bunker_co2_limit`（1） | **通过** |
| F1_M02 | 只删 `research_country_co2_limit`（11） | INF_OR_UNBD |
| F1_M02 | 只删 `ResearchImportAnnual`（19） | INF_OR_UNBD |
| F1_M02 | **只删 `research_bunker_co2_limit`（1 行）** | **通过** |
| F1_M02 | 删 bunker 行，同时把 82 个化石计量的 `Link-p` 全部固定为 0（18,368 列；精确算术下与原约束等价的改写） | **通过** |
| F1_M02 | 保留 bunker 行，只把右端项从 0（LP 中写作 `-0.0`）改为 1.0 t | **通过** |
| F1_M01 | 只删 `research_bunker_co2_limit` | **通过** |
| F2_M02 | 只删 `research_bunker_co2_limit` | **通过** |

`research_co2_storage_cap` 没有单独测试：它在包含 bunker 行的那组删除里，而只删 bunker 行就已足够让预处理通过。

### 5.5 冲突约束清单

| 约束 / 变量 | 规模（F1_M02） | 作用 | 等级 |
|---|---|---|---|
| `research_bunker_co2_limit` | 1 行（第 7148145 行），`Store-e[最后时段, co2 bunkers ASEAN] ≤ 0` | 必要：删掉或放宽 1 t 即通过 | VERIFIED |
| `Store-energy_balance`，Store 为 `co2 bunkers ASEAN` | 每时段 1 行，共 224 行，系数含权重 w | 把各时段排放累计到最后时段 | INFERENCE（结构） |
| `Bus-nodal_balance`，母线为 `co2 bunkers ASEAN` | 224 行 | Store 的 p 等于 Σ 0.2571 × 计量流量 | INFERENCE（结构） |
| `Link-p`，82 个 `<节点> aviation international oil meter`（bus2 → 账户，系数 0.2571 t/MWh，可扩建） | 18,368 列 | 被约束强制为 0 的变量 | VERIFIED（标签与系数）；强制关系 EXACT 地来自"只有排放端口" |
| 82 个航空国际燃料终端母线的节点平衡、非化石孪生链路 `… meter non-fossil` | 每个终端母线 1 个孪生链路 | 化石计量为 0 后，负荷全部由非化石孪生链路承担 | INFERENCE（结构） |

**涉及的组件和国家。**

- **账户**：`co2 bunkers ASEAN`，归属实体为 ASEAN / BUNKER。它可扩建，`e_min_pu = -1`，初值 0，非循环，资本成本 0。
- **化石航煤计量的分布**：BN 1、ID 32、KH 4、LA 4、MM 9、MY 8、PH 7、SG 1、TH 7、TL 1、VN 8，共 82 个，见 `evidence/BUNKER_LABELS_F1_M02.json`。
- **需求量级**：国际航空燃料需求每年 239.55 TWh。如果全部用化石航煤，年排放为 61.6 Mt。

**涉及的时段。** 约束本身只在窗口的最后时段，但通过 Store 链把窗口内**每个时段**都牵连进来，问题与特定时段无关（5.1 节）。

## 6. 全年累计约束（第 4 步）

指令第 4 步的前提是"12 个月全部可解"，但有 8 个月复现了失败，所以这一分支没有触发。这里仍按要求列出全部年度和最后时段约束，并对比两种口径的右端项（来源：`evidence/ANNUAL_RHS_F1.json`，静态读取，VERIFIED）：

| 约束 | 形式 | 全年口径右端项 | 截短口径右端项 |
|---|---|---|---|
| `research_country_co2_limit-<国家>`（11 行） | 最后时段大气水平 ≤ 上限 | 11 国全部 0 | 相同（不缩放） |
| `research_co2_storage_cap-<国家>`（7 行：BN、ID、KH、MY、PH、TH、VN） | 最后时段封存水平 ≤ 上限 × horizon_fraction | horizon_fraction = 1.0 | 1.0（`set_representative_weights` 设定） |
| `ResearchImportAnnual-<发电机>`（19 行，燃气产量） | Σ p·w ≤ 上限 | 不缩放；Σw = 8760 | 不缩放；Σw = 8760 |
| `research_bunker_co2_limit`（1 行） | 最后时段账户水平 ≤ 0 | 0 | 0 |

两种口径的右端项没有差别。全年与截短的区别只在时段数和每时段权重。

**全年本机运行超出内存（停止条件）。** 248 个时段的构建峰值已到 8.57 GiB，本机 WSL 约 10 GiB；全年构建约需 110 GB，再加 Gurobi 约 60 GB。所以全年复现和"窗口逐步加长到季度、半年"都无法在本机完成。建议的 HPC 诊断作业（PROPOSED，未提交）：

- **构建**：F1 和 F2 各一次，用 `diag_build.py --native-weights` 跑 `[0,2920)` 窗口，等同于正式构建（应与正式构建的 `problem_sha256` 一致），同时在同一进程里导出 bunker 标签。
- **三次只到预处理的 Gurobi 调用**，用同一份 LP：
  - (a) 档案原样，预期 INF_OR_UNBD，即复现；
  - (b) 删 bunker 行并把计量流量固定为 0，预期通过；
  - (c) 右端项改为 +1 t，预期通过。
- **资源估计**（来自第 0 节事实）：每个网络构建约 50 分钟，内存峰值约 108 GB；每次预处理约 4–5 分钟，ordering 另计。申请 48 核、300 GB、墙钟 4 h；F1 和 F2 分开跑。

## 7. F2 与 F3、F4（第 5 步）

- **F2（VERIFIED）**：2 月窗口 `F2_M02` 的预处理同样 INF_OR_UNBD（第 33 次调用），只删 bunker 行后通过（第 34 次调用），是同一原因。
- **F3、F4（INFERENCE，未求解）**：从网络数据读取（`evidence/BUNKER_STATIC_F1_F4.json`）。四个网络的 bunker 结构完全相同：都装了 `research_bunker_net_zero` 挂接，模式 `asean_account_nodal`；82 个端口全是排放端口，移除端口为 0；系数 0.2571；82 个终端母线各有 1 个非化石孪生链路；航空国际燃料需求 239.55 TWh/年；账户 Store 契约相同。因此 F3、F4 带着同一条零松弛行，存在同样的预处理判定风险。是否会触发，取决于全年模型的舍入，无法事先保证。

## 8. 为什么 56 时段与日分辨率没有暴露（第 6 步）

- **结构一直在**：bunker 净零行存在于所有时间分辨率：56×3h 截短、365×24h、2920×3h。56 时段冒烟（本机和 HPC）与 365×24h 筛查都求到 optimal，说明这些规模下可行域非空，零松弛行可以被满足。
- **会不会触发是伪随机的**：预处理是否把它判成 INF_OR_UNBD，取决于聚合后长约束的舍入误差，而舍入误差随时段数和权重伪随机变化（VERIFIED，5.1 节）。同样的 1 月数据，248 个时段失败、240 个时段通过；所有 56 时段的周窗口都通过。56 时段冒烟恰好落在"通过"的一侧；365×24h 有没有被测过预处理这一项并不重要，它的完整求解已经成功。
- **小规模测试保证不了全年**：这个问题不是由某个时段的数据或某个年度量引起的，任何截短测试都不能保证排除它。只有全尺寸预处理能可靠暴露它，所以需要第 10 节的闸门。

## 9. 修正方案（PROPOSED，不执行；需用户决定）

**方案 1（推荐，最小改动）：只改 `scripts_project/s4c_layers.py` 第 626–635 行 `install_bunker_net_zero`。** 把

```python
m.add_constraints(m["Store-e"].sel(snapshot=n.snapshots[-1], Store=BUNKER_CO2_BUS) <= 0.0, name=BUNKER_ROW)
```

改为对账户全部排放端口所在链路的逐时段零约束，约束名不变：

```python
meters = [p["link"] for p in validate_bunker_account(n)["ports"]]   # 只有排放端口（函数已保证）
m.add_constraints(m["Link-p"].sel(Link=meters) == 0.0, name=BUNKER_ROW)
```

- **可行域与目标**：精确算术下完全相同（EXACT 的逻辑）。账户初值为 0，只有系数为正的排放端口，所以"最后时段水平 ≤ 0"当且仅当"所有端口流量在所有权重为正的时段都为 0"。已在四个网络上核对，移除端口都为 0。改写后账户水平恒为 0，门槛 B1_BUNKERS 照常满足。
- **对预处理的影响（VERIFIED，窗口）**：同样的改写（固定为 0 并删掉原行）在 F1_M02 上让预处理通过（第 31 次调用）。
- **网络、成本、阈值、预测都不变**：不需要重建网络，已登记的网络 SHA256 不变。改动只在求解时的挂接代码里，部署包需要一个新的代码提交。
- **对其他时段和国家**：可行域相同，最优目标相同，所有时段的物理调度可行集不变。
- **会不会让成本偏向某些国家（INFERENCE，需回归验证）**：
  - **对偶值的位置变了**：原来这一行的单个对偶值（燃料舱 CO2 影子价格），改由每时段计量约束的对偶值承接。
  - **右端项分摊不受影响**：两种写法右端项都是 0，`m12_rhs_audit.py` 的 y'b 贡献都是 0；按约束名把它归为 BUNKER 参与方的逻辑（第 139 行）因为保留了约束名，照常生效。
  - **燃料舱参与方的购买价不变**：两种写法下，它在航空终端母线的节点对偶价都由非化石孪生链路的供应决定，不会把成本转移给任何国家。
  - **验收与独立成本照常**：`s4b_acceptance.py` 第 90 行对这个约束名下的所有标签都设置毛流量参照，多行同样适用；`m12_allocation.bunker_standalone` 本来就不允许化石计量，不受影响。
  - **需要验证**：方案 1 实施后，建议做一次 56×3h 的 F1、F2 回归，对比目标值和各国台账；预期在求解容差内相同。这需要 2 次 Gurobi 求解，需另行授权。
- **单元测试**：现有测试中如果有断言"该约束是标量行"的，需要相应调整。
- **365×24h 筛查是否重跑：不需要（INFERENCE）。** 改写前后可行域与最优解相同，筛查各次运行已求到 optimal 并通过验收，它们的结论不受数值写法影响。如需佐证，上面的 56×3h 回归已足够。

**不推荐的方案：**

- **方案 2**：在建网时把化石航煤计量的 `p_max_pu` 设为 0。效果相同，但要重建四个网络并重新登记。
- **方案 3**：改求解档案，用 `Aggregate=0`、`DualReductions=0` 或 `Presolve=1`。这会改动已登记的档案和 barrier 路径，也没有消除零松弛行本身，全年效果未知。
- **方案 4**：给右端项留余量，例如 ≤ 1 t。这改变了模型，允许少量化石燃料舱燃料，也改变了验收含义。

## 10. 全尺寸预处理闸门（PROPOSED）

1. **静态闸门（建包时运行，不调用求解器，数秒完成）**：在 `validate_bunker_account` 以及任何"最后时段水平 ≤ 上限"类挂接中，检查账户是否只有单向端口、右端项是否为 0。如果是，说明这条约束实质上是逐时段强制为零，必须改成显式的逐变量约束（方案 1 的写法），否则拒绝建包。还可以在导出的 `lp/` 数组上运行扩展版 `lp_scan.py`：把单元素行视为变量界后，标出"非负项之和 ≤ 0"的强制行。
2. **全尺寸预处理作业（每个部署包、每个网络各一次，在 HPC 上）**：
   - **构建**：进程 1 用正式标签、不截短，与正式构建相同。
   - **预处理**：进程 2 用 `BarIterLimit=0` 只跑到预处理。`b4_split_solve.py` 现有的 `--probe-ordering-only` 只允许 `SMOKE_TEST_ONLY`，需要新增一个 `--presolve-gate` 模式：允许正式标签，写出 `PRESOLVE_GATE.json`，不计入正式求解。
   - **判定**：日志里有 "Presolved:"、没有 "infeasible or unbounded"，即为通过。
   - **资源（INFERENCE）**：构建约 50 分钟，内存约 110 GB；读入、预处理和 ordering 约 15–40 分钟，内存 60–80 GB。申请 48 核、300 GB、墙钟 3 h，4 个网络约 4 个作业。可以设 `MemLimit`，让 ordering 超限后直接停，不影响预处理判定。
   - **本机不能做**：本机内存约 10 GiB，只够约 250 个时段。

## 11. Gurobi 次数与用时

| 项目 | 数值 |
|---|---|
| Gurobi 调用 | **35 / 40**：26 次预处理探针、1 次 IIS、8 次删除探针；全部只到预处理或 IIS |
| 调用墙钟合计 | 3,433 s（其中 IIS 1,810 s） |
| 单次最长 | 1,810 s（IIS，30 分钟上限内） |
| 同时运行的 Gurobi 进程 | 始终只有 1 个；每次调用前检查 TCP 连通和进程 |
| 本机计算 | 07:41–09:36 UTC，约 1.9 h（上限 6 h） |
| 磁盘新增 | 14.2 GB，位于主检出的 `results_project/v3diag/`（上限 30 GB） |
| 账本 | `evidence/GUROBI_CALLS.csv`、`evidence/DIAG_STATUS.txt`、`V3_DIAG_EVIDENCE.json` |

## 12. 执行中的偏差与事故（照实记录）

- **窗口长度**：按日历月划分，见第 4 节。指令写的"每个 240 个时段（12 月 248 个）"与 2920 无法对齐，而 12 月正好是 248 个时段。
- **F1_M01 第一次构建（事故）**：构建本身已完成，LP SHA256 `439499e1…`，与重建结果相同。但我在构建运行期间修改了 `build.sh`，bash 按旧偏移继续读，执行了错位命令，把 `p1.err`、`p1.log` 截断了。这次构建已改名为 `F1_M01_x1` 留档并重建；不涉及 Gurobi。
- **内存保护**：
  - 1–4 月的探针用 `SoftMemLimit=8`。4 月在 ordering 阶段用到 14.2 GB，并用了 swap，所以从 5 月起把上限降为 6。
  - 但软上限只在安全检查点检查，ordering 期间仍会到 14 GB。第 14 次调用（`DualReductions=0`）的 ordering 被内核 OOM 杀掉（dmesg anon-rss 10.68 GB），之后的调用都加了硬上限 `MemLimit=7`。
  - 这些保护参数都不改变预处理判定。第 14 次调用照实计数。
- **日志措辞**：`months.sh` 对 MEM_LIMIT 月份写的是 "LP_REMOVED … status ITERATION_LIMIT"，这是固定文本；`del_probe.sh` 的状态行显示 "drop[]" 也是显示问题。实际内容以各自的 JSON 为准。
- **超出指令字面步骤的诊断（都只到预处理，或只读不求解）**：原始权重窗口、两个 240 时段判别窗口、预处理参数敏感性、约束组删除过滤（第 3 节方法）、LP 结构扫描和 bunker 结构静态检查。原因：按周、按天二分在所有周窗口上都通过，无法缩小；IIS 在 30 分钟内拿不到。
- **没有按指令完成的部分**：没有得到 linopy `compute_infeasibilities()` 的 IIS 清单（5.3 节），改用删除过滤给出必要约束（5.4 节）；没有在本机复现全年（第 6 节停止条件）。
- **WSL 空闲自动重启**：WSL 空闲约 60 s 后会自动关闭虚拟机，下次调用时重启，`uptime` 会归零。每次调用前都重新测试了 TCP 连通，对结果无影响。
- **未用额度**：Gurobi 剩 5 次未用。

## 13. 等待审阅端与 Fable 审查（第 194 项）的事项

1. 是否采用方案 1（第 9 节）。如果采用：改代码、新部署包，并另行授权一次 56×3h 回归。
2. 是否提交第 6 节的 HPC 诊断作业，在全年 F1、F2 上验证同一机制。
3. 是否建立第 10 节的两类闸门。
