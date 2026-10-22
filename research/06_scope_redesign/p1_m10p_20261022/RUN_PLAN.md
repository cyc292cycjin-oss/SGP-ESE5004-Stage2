# 第三批运行计划（RUN_PLAN）——365×24h，单卡实例，两个 Gurobi 会话并行

**版本：** M10P v2（补充 01），2026-10-22。依据 `M10P_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `bd2461e7…bbd1`）第 2–4 节、第 133、138–141 项，以及 `M10P_SUPPLEMENT_01.md`（SHA256 `49a4593d…9205`）第 1 节的六项决定（第 142 项）。
**状态：** 只是准备。实际上云在用户租卡并授权后，按另一份执行指令进行；本文件第 3 节的规则在看到任何结果之前登记，之后不得修改。v1 → v2 的改动都来自补充 01 的决定，此时尚无任何第三批结果。
**入口：** `run_batch3.sh`（运行与逐运行 / 批级后处理）、`preflight.sh`（预检）、`pack_results.sh`（结果打包）、`env/install_env.sh`（非克隆部署的环境安装）。运行表与排程的唯一来源是代码中的 `scripts_project/m10_batch3_summary.py` `RUNS` 与 `SCHEDULE`。

---

## 1. 网络与代码

- **基础网络（用户 2026-10-22 决定 A）：** M08b 补充 01 构建（提交 `ec80668f`，主检出 `results_project/m08b/builds_s01/`），即 M08b 冒烟与 M12b 去一国所用、G2.1 已登记的文件。M10P-2 在干净提交 `b46fc23d` 上重建：数据逐项相同，只有元数据中构建 worktree 的路径不同（`NETWORK_REBUILD_CHECK.json`）。

| 文件 | 用途 | 大小（B） | SHA256 |
|---|---|---|---|
| `networks/integrated_365_24h_unsolved.nc` | R1、R3、R5–R7、R9、R10 的基础网络 | 31,524,926 | `75704334dc11deeb06fc80f84ef197d65c3ac5bd658ab450e4ee1a93a3ccb19e` |
| `networks/disconnected_365_24h_unsolved.nc` | R2、R4、R8、R11 的基础网络 | 30,857,960 | `888a009b5f19eb34f7f1c24e36f7c8370617a9c405b1097a9caed0599cecbee4` |

- **2920×3h 网络不入包：** P1 已从第三批删除（补充 01 第 3 项，见第 9 节）。
- **变体：** 云端由 `m08a_variants.py` 从基础网络生成（`PYTHONHASHSEED=0`，不加 `--allow-stale-base`），不上传变体文件；每个变体的 SHA256 与本机干跑得到的 `EXPECTED_VARIANTS.json` 比较（本机两遍逐字节相同，见 `VARIANT_REPRODUCIBILITY.json`）。
- **代码：** 部署包提交（`COMMIT`）的 `git archive`，**不含仓库顶层 `research/` 目录**（补充 01 第 5 项：静态检查与干跑确认运行时不读取该目录，无需保留的文件）；`preflight.sh` 解包到 `./repo`。
- **已知小项（补充 01 第 6 项）：** `scripts_project/s2_network.py:344` 把构建 worktree 的绝对路径写入网络元数据，使不同目录的重建 SHA256 不同（数据相同）。**暂不修**，正式运行完成后再修：现在修改会使四个网络的 SHA256 全部改变、需要重新登记，而云端不重建网络，对运行没有影响。`m08a_variants.py` 的同类问题已修正（只记录成本表文件名与 SHA256，提交 `eac6c3e0`），用户已接受。

## 2. 运行清单

单位：TimeLimit / 墙钟为秒。档案 A = `formal_barrier`（Threads 8，BarConvTol 1e-8）；1e-6 T16 = `formal_barrier_1e6_t16`（Threads 16，BarConvTol 1e-6）。两档案其余参数相同（Method 2、Crossover 0、BarHomogeneous 1、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200）。

| 编号 | 运行 | 网络（基础 / 变体 `--set`） | 求解情景 | 档案 | Threads | TimeLimit | 墙钟 | 成本表 | 作用 |
|---|---|---|---|---|---|---|---|---|---|
| R1 | 一体化 | 基础 `integrated_365_24h` | integrated | A | 8 | 21,600 | 22,500 | integrated | 本批参照、Owen 分摊、c(N) |
| R2 | 不互联 | 基础 `disconnected_365_24h` | disconnected | A | 8 | 21,600 | 22,500 | disconnected | 本批参照、B6 |
| R3 | 一体化 | 基础 `integrated_365_24h` | integrated | 1e-6 T16 | 16 | 21,600 | 22,500 | integrated | 第二级容差验证（第 127 项） |
| R4 | 不互联 | 基础 `disconnected_365_24h` | disconnected | 1e-6 T16 | 16 | 21,600 | 22,500 | disconnected | 同上 |
| R5 | 去 VN | `integrated_365_24h` + `coalition.remove_countries=[VN]` | integrated | A | 8 | 21,600 | 22,500 | integrated | 365×24h 去一国复核（第 133、139 项） |
| R6 | 去 TH | 同上 `[TH]` | integrated | A | 8 | 21,600 | 22,500 | integrated | 同上 |
| R7 | 去 LA | 同上 `[LA]` | integrated | A | 8 | 21,600 | 22,500 | integrated | 同上 |
| R8 | 不互联 b1 | `disconnected_365_24h` + `disconnected.co2_shipping_intra_asean=forbid` | disconnected | A | 8 | 21,600 | 22,500 | disconnected | 敏感性（第 132 项） |
| R9 | 不互联保留存量 | `integrated_365_24h` + `cross_border.stock_mode=keep_stock_no_new` | disconnected | A | 8 | 21,600 | 22,500 | integrated | 敏感性（第 132 项 2a） |
| R10 | 分国 WACC 一体化 | `integrated_365_24h` + `finance.wacc_mode=country_specific` | integrated | A | 8 | 21,600 | 22,500 | integrated | 敏感性（第 132 项第 5 项） |
| R11 | 分国 WACC 不互联 | `disconnected_365_24h` + `finance.wacc_mode=country_specific` | disconnected | A | 8 | 21,600 | 22,500 | disconnected | 同上 |

- 保留存量变体（R9）按 `m08a_variants.py` 的定义只能由一体化网络派生，得到不互联情景的网络；分国 WACC 变体用各自基础构建的成本表（`--costs`）。
- 求解调用（每个运行一次）：`s2_solve.py --solver gurobi --solver-profile <档案> --scaling on --time-limit <TimeLimit> --costs-table <成本表> --label BATCH3_365X24H`；运行目录 `runs/batch3/<编号>/`，导出 `runs/batch3/export/<编号>/`，状态 `runs/batch3/STATUS.txt`。
- P1（2920×3h 探针）已删除（补充 01 第 3 项）。

## 3. 事先登记的规则（看结果前不得修改）

### 3.1 时限与求解

1. 365×24h 每次 TimeLimit 21,600 s、墙钟 22,500 s。不重试，不改参数，不 warm start。
2. 墙钟到达时终止整个进程组（TERM，30 s 后 KILL），待进程组全部退出后再导出；回执不含终止条件的视为求解前回执（`killed_pre_solve` / `none`）。
3. 脚本拒绝启动：时限、墙钟或许可间隔与本节登记值不同（只有测试和本机干跑可用 `ALLOW_UNREGISTERED=1`）。

### 3.2 两个会话与顺序（补充 01 第 1 项）

1. 同时最多两个 Gurobi 会话。每个阶段两条通道，通道内依次运行；**两条通道只在各自最大 Threads 之和不超过容器核数时同时跑**，否则合成一条通道、两边轮流取运行。R3、R4（Threads 16）在同一条通道，任何时刻不会有两个 T16 会话。
2. 顺序（`SCHEDULE`）：
   - 第 0 阶段（不用许可）：输入齐全、基础网络 SHA256 = 构建回执、生成 7 个变体并与 `EXPECTED_VARIANTS.json` 比较；
   - 第 1 阶段：R1 | R2（8 + 8 = 16 核）→ 本批参照（`BATCH_REFERENCE.json`）与重评；
   - 第 2 阶段：通道 A = R3 → R4（T16），通道 B = R5 → R6（档案 A）：**R3 与 R5 同时跑，R4 与 R6 同时跑，合计 16 + 8 = 24 核**；之后第二级比较与第四批档案选择；
   - 第 3 阶段：通道 A = R7 → R9 → R11，通道 B = R8 → R10（A + A = 16 核）；
   - 批级后处理与结果打包（`final`）。
   - 只改顺序，不改档案与参数。两条通道各自依次推进，不严格等待对方：R4 在 R3 结束（加许可间隔）后开始，R6 在 R5 结束后开始；任何时刻至多一个 T16 加一个档案 A 会话（≤ 24 核）。
   - 容器核数不足 24 时第 2 阶段合成一条通道（R3 → R5 → R4 → R6），不足 16 时第 1、3 阶段也合成一条通道。实例规格要求 ≥ 25 核（第 5 节），正常情况下不会出现。
3. **第二级的速度比较受并行负载影响，只作参考**（R3 / R4 与档案 A 运行同时跑，R1 / R2 与另一个档案 A 运行同时跑，负载不同）；判据仍是 C1 与目标相对差（3.4）。
4. 许可（学术 WLS 至多 2 个会话，令牌关闭后至少保留 5 分钟）：同一通道内上一个求解结束到下一个开始 ≥ 330 s；每个阶段开始前距所有求解的最晚结束、以及距本脚本启动（预检的许可检查、此前中断的脚本）≥ 330 s。后处理只用 Python，运行时移除 `GRB_LICENSE_FILE`。
5. 每次启动前检查：其他 `s2_solve.py` 进程不超过 1 个。

### 3.3 验收（GATES_V6）与分级停批（补充 01 第 2 项）

1. G1 = C1 (a)(b)(c)（`s4o_c1_precision.py`，第 119 项），G2 = 结构检查（G2.1 网络 SHA256 = 登记值且回读精确；G2.2 配置子集哈希；G2.3 导出完整）。标签 ACCEPTED_LAYER2 / ACCEPTED_LAYER1 / NOT_ACCEPTED；求解器状态不是判据。
   - G2.1 登记值：基础网络取构建回执（365×24h 未截断取日网络 SHA）；变体取变体回执 `output.sha256`。
2. **阈值参照：** C1 (b)(c) 的分国阈值用本批 R1、R2 的分国差额（`s4o_c1_precision.py reference`，即 `BATCH_REFERENCE.json`）。R1、R2 都有账本之前完成的运行先用缺省参照作**临时判定**；参照生成后对所有已完成运行重评（`regrade`，`grade_history` 保留；临时标签另存为 `V6_ACCEPTANCE_PROVISIONAL.json`），再重新验收。之后的运行直接用本批参照。
3. **分级停批（取代 v1 的"C1 (a) 或 G2 不通过即停批"）：** 每个标签不是 ACCEPTED_* 的运行由 `m10_batch3_summary.py stop-class` 分类（写 `STOP_CLASS.json`）：

   | 情况 | R1、R2 | R3–R11 |
   |---|---|---|
   | G2 不通过（结构或输入问题） | **停批** | **停批** |
   | 无返回解（墙钟终止、求解失败、内存不足、到 TimeLimit 无可用解） | **停批**（本批参照缺失） | 记为**不可用**，继续其余运行 |
   | 有解但 C1 (a) 不通过（含 C1 不可计算） | **停批** | 记为**不可用**，继续其余运行 |
   | 只有 C1 (b) / (c) 不通过（临时或最终） | 不停批（第 138 项 D12） | 不停批 |

   - **无返回解时的 G2：** G2.1 的回读与 G2.3（解的维数、目标值、导出）都需要解，无解时必然不过，这不是结构或输入问题。因此无返回解的运行只核对不需要解的部分：输入网络 SHA256 = 登记值（求解前回执；回执未写出时用运行脚本在启动前算的 SHA256），以及配置子集哈希（求解前回执中有记录时）。这两项不过 → 按 G2 不通过停批。
   - 验收文件缺失或不可读、分类结果不可读 → 按 G2 不通过处理（停批）。
   - **停批：** 不再启动新的求解；另一条通道上正在跑的求解跑完并做后处理；批级汇总与结果打包照常写出；脚本以退出码 3 停在安全状态等用户。
   - **不可用：** 写入 `runs/batch3/UNUSABLE`（编号、类别、时间）与 `STATUS.txt`（`UNUSABLE:<编号>:<类别>`），不重跑；批级后处理中不作为 c(N − i) 进入去一国检查（R5–R7），敏感性差额标为不可用，R3 / R4 不可用则第二级比较不通过（第四批用档案 A）；汇总 `BATCH3_SUMMARY.json / .md` 列出全部不可用运行。批次照常跑完时以退出码 0 结束（`DONE:…:unusable=<编号>`）。
4. **对偶形式（第 138 项）：** M12 对偶形式验收 = 恒等式 |Σ 11 国 + 燃料舱 − c(N)| ≤ 0.01 bn，且每个参与者的残差影响 ≤ max(该参与者参照差额的 1 %, 0.01 bn)（`m12_allocation.DUAL_ACCEPTANCE_RULE`）；本批参照生成后对已完成运行按同一参照重评（`m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json`）。

### 3.4 第四批档案选择（第 133 项）

- R3、R4 的 C1 (a)(b)(c) 全过，且与 R1、R2 的目标相对差都 ≤ 1e-5 → 第四批用 1e-6 T16；否则用档案 A。1e-5 档案不作备选。
- 实现：`m10_batch3_summary.py level2` 写 `LEVEL2.json`（两情景都列出；缺运行或不可用即视为不通过），`gates_v6.py select-profile` 写 `PROFILE_CHOICE.json`（`research.solver.run_rules.profile_chain`，C1 标志取最终验收的 G1）。
- 求解时间与迭代次数的比较只作参考（3.2 第 3 项），不进入判据。

### 3.5 每次求解后的后处理（自动，按此顺序）

1. 违反量分析（`l23_violation_analysis.py` → `VIOLATIONS.json`；有解时）；
2. C1（`s4o_c1_precision.py run`，参照见 3.3 第 2 项）→ `PRECISION.json / .md`；
3. M12 分摊（`m12_allocation.py run --register`）与 Owen 对偶形式（`m12_rhs_audit.py audit`，导出数组存在时）：对偶形式为主值，市场形式并列，α 区间，燃料舱作为参与者；输出登记到 `EXPORTS.json`（在验收之前，使 G2.3 核对最终导出清单）；
4. R5–R7：去一国右端项检查（`m12_rhs_audit.py loo`，对 R1 的右端项按族与所有者比较）；
5. GATES_V6（`gates_v6.py accept`）→ `V6_ACCEPTANCE.json`；分级停批分类（3.3 第 3 项）→ `STOP_CLASS.json`；
6. 导出到 `export/<编号>/`（清洗后的日志，无 LP / 解数组，无原始求解日志）。

### 3.6 批级后处理（第 3 阶段之后；停批时照常执行）

1. **B6** = R2 − R1 的目标值（`v5_gates.gate_b6_cost`），并列 M12 受益（`m12_allocation.py benefit`）；
2. **受益与比例规则对照**（`m12_allocation.py benefit --loo-check`）；
3. **去一国检查**：R1 作 c(N)，R5–R7 中未记为不可用的作 c(N − i)，`m12_allocation.py loo --standalone R2`（同档案、同分辨率；D8 加回）；被排除的运行写入 `STATUS.txt`（`unusable_left_out`）；
4. **敏感性差额**（新 − 基准）：R8 对 R2、R9 对 R2、R10 对 R1、R11 对 R2——目标值、分国账本总额、Owen 对偶形式份额；两边都不是 NOT_ACCEPTED 才标为可用（不可用运行的标签为 NOT_ACCEPTED，并单列 `unusable`）。另列信息项 R11 − R10（分国 WACC 下的 B6），不作判定；
5. **第二级比较**：R3、R4 对 R1、R2（3.4）；
6. 汇总 `BATCH3_SUMMARY.json / .md`（含停批、安全停止与不可用运行）。

### 3.7 无人值守与安全停止

运行期间按以上规则自行处理，不询问。规则没有覆盖的情况停在安全状态（写 `STOP_SAFE` 与原因，不再启动任何求解，记录并等待用户）：
- 续跑时发现某运行"已开始但未结束"（实例重启或脚本被终止）：**不重跑**（不重试），等用户；
- 启动时已有 `s2_solve.py` 进程在跑；某次启动前已有 ≥ 2 个其他求解进程；
- 基础网络 SHA256 与构建回执不符；变体 SHA256 与本机干跑不符或变体缺失；缺少输入文件。

**断点续跑：** 同一命令再次执行即续跑（同一 `runs/batch3/`）：已结束的求解一律跳过（`SKIP_ENDED_*`，含已记为不可用的运行），后处理各步只补缺失的输出；重评、验收、分类、汇总可重复执行。

## 4. 顺序与时长估计（INFERENCE）

依据（VERIFIED 的历史测量，网络为 S4M-3 版本，M08b 修正后时长可能不同）：S4N 试点一体化 365×24h 档案 A（8470Q，25 核容器，Threads 8）求解 11,470 s、墙钟 3:19 h、408 次迭代、峰值 15.1 GiB；S4O-6（8481C）不互联 2,202 s、NZE 5,238 s；S4Q 1e-6 两档案在 56×3h 上 work units 为档案 A 的 0.67–0.94。两会话并行时共享内存带宽，按 1.1–1.3 倍放慢估计（无实测；第 2 阶段 24 核同时忙，放慢可能更多）。每次后处理与许可间隔合计约 0.3 h。

| 阶段 | 内容 | 估计 |
|---|---|---|
| 0 | 变体生成与核对、启动间隔 | ~0.1 h |
| 1 | R1（~3.3 h）| R2（~1.2 h）+ 后处理、参照、重评 | 3.8–4.5 h |
| 2 | A：R3（~3 h）→ R4（~1 h）；B：R5（~3 h）→ R6（~3 h）；由通道 B 决定 | 7.2–8.4 h |
| 3 | A：R7（~3 h）→ R9（~1 h）→ R11（~1 h）；B：R8（~1 h）→ R10（~3 h）；由通道 A 决定 | 6.4–7.4 h |
| 批级 | 去一国、受益、敏感性、汇总、`final` 打包 | ~0.5 h |
| **合计** | | **约 18–21 h** |

- 与 v1（R3、R4 先后跑，第 3 阶段 7 个运行）相比，求解时间的下界约省 1 h；第 2 阶段通道 A 约有 2 h 只用 8 核（R5 + R6 比 R3 + R4 长），第 3 阶段要等第 2 阶段两条通道都结束才开始（INFERENCE）。
- 最坏情况（每个运行都跑到墙钟 6.25 h）：三个阶段最长通道分别 1、2、3 个运行，6.25 × 6 = 37.5 h，加后处理与间隔约 40 h。

## 5. 资源与实例规格（补充 01 第 4 项）

- **实例规格：** ≥ 25 核（第 2 阶段配对需 16 + 8 = 24 核）、内存 ≥ 92 GiB、数据盘可用 ≥ 60 GB；推荐 1 卡 8481C / 8470Q 一类机器。`preflight.sh` 按此检查（核与内存取容器 cgroup 配额，磁盘取包目录所在盘），不满足即 `PREFLIGHT FAILED`。
- **内存：** 两个 365×24h 会话各约 15 GiB（S4N 实测 15.1 GiB；T16 会话线程多，可能略高）+ 另一通道的后处理约 9 GiB，约 40 GiB；92 GiB 留有余量。本机实测 365×24h LP 构建峰值 10.15 GiB。
- **磁盘：** 预计用量约 30 GiB（INFERENCE）：
  - 每个 365×24h 运行目录约 1.8 GB——本机实测 R1 的 LP 数组 0.80 GB（`--stop-before-solve`，10,052,113 行 × 4,509,642 列，2,363 万非零元），其余按 56×3h 冒烟运行目录的行数比例（7.2 倍）估计——另加导出副本约 0.26 GB（S4N 实测）；11 个运行约 23 GB；
  - 结果打包（`final` 或 `halted`）约 1.8 GB；环境约 3.3 GiB + 包缓存约 0.75 GB；部署包与解包代码约 0.4 GB；变体 7 × 31 MB。
- **环境：** `env/install_env.sh`：538 个 conda 包（下载 742.8 MB，`env/ENV_DOWNLOAD.json`）+ 2 个 PyPI 包，安装后约 3.3 GiB；预计 5–15 分钟（2–20 MB/s，含解压；INFERENCE）。按 S4N 补充 01：下载超过 2 GB 或耗时超过 30 分钟先停下报告。安装后 `env_check.py` 逐包核对，关键包（python 3.11.13、pypsa 0.30.3、linopy 0.5.5、xarray 2025.1.2、pandas 2.3.1、numpy 1.26.4、scipy 1.15.2、gurobipy 12.0.3、netCDF4 1.7.2、h5netcdf 1.6.4、dask 2025.7.0、pyomo 6.9.3、highspy 1.11.0）必须完全相同。

## 6. 部署包与上传量

- 内容与每个文件的 SHA256：`PACKAGE_MANIFEST.json`、`SHA256SUMS`。约 149 MB：代码归档约 82.5 MB（不含 `research/`；含 `research_inputs/`、`data/` 等运行所需目录），两个网络 62.4 MB，两份构建回执 3.5 MB，其余（成本表、脚本、环境锁定、清单、计划）约 0.3 MB。
- **上传：** 单路上传（一个 rsync 流，不开并行流，不中断带 `--partial` 的传输），传后在实例上全量 `sha256sum -c SHA256SUMS`；失败的文件单独重传后再全量核对；全部通过后才放置许可。
- **预计上传时间（KB = 1000 B）：** 36 KB/s（S4O-6 AutoDL 克隆机上行）约 1.15 h；100 KB/s 约 25 分钟；318 KB/s 约 8 分钟。准确字节数见 `PACKAGE_MANIFEST.json`。

## 7. 云端步骤（供执行指令参考；主机、端口、密码不写入任何文件）

1. 单路上传部署包 → 全量 `sha256sum -c SHA256SUMS`。
2. `bash env/install_env.sh`（非克隆实例；克隆实例若已有同版本环境，可直接 `env/env_check.py` 核对）。
3. 按授权方式放置许可 → `PY=<环境 python> GRB_LICENSE_FILE=<许可路径> bash preflight.sh` → `PREFLIGHT OK`。
4. 在 tmux 中：`PY=<环境 python> GRB_LICENSE_FILE=<许可路径> bash run_batch3.sh --auth "<用户授权原文>"`；中断后用同一命令续跑。只重做后处理：`POST_ONLY=1 PY=<环境 python> bash run_batch3.sh`（不启动任何求解）。
5. 监控 `runs/batch3/STATUS.txt` 与 `MONITOR_<编号>.csv`。
6. 下载：先轻量包 `results_light_*`（预计几十 MB），再完整包 `results_full_*`（预计约 1.8 GB：S4N 单个 365×24h 运行压缩后 159 MB × 11；各附 `.sha256`）；LP / 解数组留在实例数据盘（`export/batch/ARRAYS_MANIFEST.json`）。按 S4O-6 实测下行约 4 MB/s 约 8 分钟，0.3 MB/s 约 1.7 h（INFERENCE）。

## 8. 本计划中由准备端确定、请审阅确认的取值

1. 每个阶段用两条固定通道、各自依次推进，而不是严格成对等待（3.2 第 2 项）：第 2 阶段 R3 与 R5、R4 与 R6 大致同时，但 R4 / R6 不等待对方的前一个运行结束。
2. 第 3 阶段的通道分配（A = R7、R9、R11；B = R8、R10）按历史时长使两条通道接近（约 5 h 对 4 h）。
3. 无返回解时 G2 只核对不需要解的部分（3.3 第 3 项），验收或分类不可读按 G2 不通过停批。
4. 去一国检查不使用记为不可用的 R5–R7（3.6 第 3 项）。

## 9. 第四批开始时的 2920×3h 内存实测（补充 01 第 3 项；不在第三批中）

- P1 从第三批删除。2920×3h 的内存实测改到第四批开始时进行：第四批租用大内存机器，正式运行前用 1 小时作探针监控，**超过可用内存的 80 % 即止损**，再调整机器。具体做法写入第四批的执行指令。
- 参考：本机 365×24h 构建峰值 10.15 GiB；2920×3h 的 LP 约为 365×24h 的 8 倍，仅构建粗估约 80 GiB（INFERENCE）。P1 的计时与内存解析函数（`m10_batch3_summary.py p1_summary`）保留供第四批使用。
