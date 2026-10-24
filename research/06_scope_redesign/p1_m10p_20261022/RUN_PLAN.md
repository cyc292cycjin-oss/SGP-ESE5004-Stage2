# 第三批运行计划（RUN_PLAN）——365×24h，单卡实例，两个 Gurobi 会话并行

**版本：** M10P v4（M10A 补充 01：时限登记值变更、两项稳健性修改），2026-10-23。依据 `M10P_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `bd2461e7…bbd1`）第 2–4 节、第 133、138–141 项，`M10P_SUPPLEMENT_01.md`（SHA256 `49a4593d…9205`）第 1 节的六项决定（第 142 项），`M10A_CLAUDE_CODE_INSTRUCTION.md`（SHA256 `d7db9497…7f98a`）B5 的实现层修复（第 10 节第 1–6 项），以及 `M10A_SUPPLEMENT_01.md`（SHA256 `4abdff42…dd70`，第 145 项，用户 2026-10-22 同意）的三项决定 D1–D3（第 10 节第 7–9 项）。
**状态：** 只是准备。实际上云在用户租卡并授权后，按另一份执行指令进行；本文件第 3 节的规则在看到任何结果之前登记，之后不得修改。v1 → v2 的改动都来自补充 01 的决定；v2 → v3 只改实现（运行脚本的进程计数、后处理超时与线程预算、临时目录、测试开关防护）；**v3 → v4 变更了第 3.1 节的 365×24h 时限登记值（21,600 / 22,500 → 28,800 / 30,000 s，第 10 节第 7 项记录理由），并在第 3.5 节加入违反分析与 C1 的一次重做（第 10 节第 8 项）、第 5 节改为预检硬下限（第 10 节第 9 项）——变更时新网络在 365×24h 上没有任何求解结果**，其余规则一字未改。
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
| R1 | 一体化 | 基础 `integrated_365_24h` | integrated | A | 8 | 28,800 | 30,000 | integrated | 本批参照、Owen 分摊、c(N) |
| R2 | 不互联 | 基础 `disconnected_365_24h` | disconnected | A | 8 | 28,800 | 30,000 | disconnected | 本批参照、B6 |
| R3 | 一体化 | 基础 `integrated_365_24h` | integrated | 1e-6 T16 | 16 | 28,800 | 30,000 | integrated | 第二级容差验证（第 127 项） |
| R4 | 不互联 | 基础 `disconnected_365_24h` | disconnected | 1e-6 T16 | 16 | 28,800 | 30,000 | disconnected | 同上 |
| R5 | 去 VN | `integrated_365_24h` + `coalition.remove_countries=[VN]` | integrated | A | 8 | 28,800 | 30,000 | integrated | 365×24h 去一国复核（第 133、139 项） |
| R6 | 去 TH | 同上 `[TH]` | integrated | A | 8 | 28,800 | 30,000 | integrated | 同上 |
| R7 | 去 LA | 同上 `[LA]` | integrated | A | 8 | 28,800 | 30,000 | integrated | 同上 |
| R8 | 不互联 b1 | `disconnected_365_24h` + `disconnected.co2_shipping_intra_asean=forbid` | disconnected | A | 8 | 28,800 | 30,000 | disconnected | 敏感性（第 132 项） |
| R9 | 不互联保留存量 | `integrated_365_24h` + `cross_border.stock_mode=keep_stock_no_new` | disconnected | A | 8 | 28,800 | 30,000 | integrated | 敏感性（第 132 项 2a） |
| R10 | 分国 WACC 一体化 | `integrated_365_24h` + `finance.wacc_mode=country_specific` | integrated | A | 8 | 28,800 | 30,000 | integrated | 敏感性（第 132 项第 5 项） |
| R11 | 分国 WACC 不互联 | `disconnected_365_24h` + `finance.wacc_mode=country_specific` | disconnected | A | 8 | 28,800 | 30,000 | disconnected | 同上 |

- 保留存量变体（R9）按 `m08a_variants.py` 的定义只能由一体化网络派生，得到不互联情景的网络；分国 WACC 变体用各自基础构建的成本表（`--costs`）。
- 求解调用（每个运行一次）：`s2_solve.py --solver gurobi --solver-profile <档案> --scaling on --time-limit <TimeLimit> --costs-table <成本表> --label BATCH3_365X24H`；运行目录 `runs/batch3/<编号>/`，导出 `runs/batch3/export/<编号>/`，状态 `runs/batch3/STATUS.txt`。
- P1（2920×3h 探针）已删除（补充 01 第 3 项）。

## 3. 事先登记的规则（看结果前不得修改）

### 3.1 时限与求解

1. 365×24h 每次 TimeLimit **28,800 s**、墙钟 **30,000 s**（M10A 补充 01 D1，第 145 项，2026-10-23 登记，变更时新网络在 365×24h 上无任何求解结果；v1–v3 为 21,600 / 22,500 s，理由见第 10 节第 7 项）。不重试，不改参数，不 warm start。
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
   - **第 1、2 步的一次重做（M10A 补充 01 D2，第 145 项）：** 退出码非 0 或超时时，把该步不完整的输出改名为 `*.failed<n>` 保留，立即以相同环境与参数重做**一次**（`STATUS.txt` 记 `POSTPROC_RETRY:<编号>:<步骤>:exit=…`）；重做仍失败则按 3.3 第 3 项处理（C1 不可计算 = C1 (a) 不通过）。不重跑求解，分类代码、阈值与 3.3 表格不变；其他后处理步骤只记录不停批（第 10 节第 2 项）。
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
- 最坏情况（v4：每个运行都跑到墙钟 30,000 s = 8.33 h）：三个阶段最长通道分别 1、2、3 个运行，8.33 × 6 = 50 h，加后处理与间隔约 52 h（v1–v3 按墙钟 6.25 h 为约 40 h）。正常情况下时限只在运行确实变慢时才多花时间，总时长不变（约 20–25 h，见下）。
- **M10A 复核（v3，INFERENCE）：** 上表按旧网络（S4M-3）估计。M08b 修正后的网络 365×24h 多 11.5 % 行、12.8 % 非零元；56×3h 同机同档案对比，新网络每次迭代耗时约 +10 %、迭代数相近（129–181 对 141）。按 S4N 3.3 h × 1.10–1.15（规模）× 1.1–1.3（两会话并行）估计 R1 墙钟 **4.0–4.9 h**，上限超过原 TimeLimit 6 h 的 75 %（M10A 报告"需要用户决定"第 1 项 → 补充 01 D1 把时限改为 8 h，4.9 h 为其 61 %）；R5–R7 同量级，R2 约 0.8–1.0 h。各阶段按此为 4.5–5.4 / 8.6–11 / 6.5–7.7 h，合计约 **20–25 h**。每次后处理实测 / 外推合计约 6–8 分钟（第 5 节），低于上表的 0.3 h。

## 5. 资源与实例规格（补充 01 第 4 项）

- **租用建议（不变）：** ≥ 25 核（第 2 阶段配对需 16 + 8 = 24 核）、内存约 90 GB 以上、数据盘约 80 GB；推荐 1 卡 8481C / 8470Q 一类机器。
- **预检硬下限（M10A 补充 01 D3，第 145 项）：** `preflight.sh` 只在核数 < 25、容器内存 < **64 GiB**（预计峰值约 34 GiB，约 2 倍余量）或包目录所在数据盘可用 < **45 GB**（预计用量约 30 GiB；预检在装好环境之后做）时 `PREFLIGHT FAILED`（核与内存取容器 cgroup 配额，磁盘取包目录所在盘）。v1–v3 的硬下限 92 GiB / 60 GB 与租用建议相同，而 AutoDL 标的内存与磁盘单位可能是 GB 而不是 GiB，实际够用的实例也可能卡在预检，所以把硬下限放宽到实际需要，租用建议与硬下限分开写。
- **内存：** 两个 365×24h 会话各约 15 GiB（S4N 实测 15.1 GiB；T16 会话线程多，可能略高）+ 另一通道的后处理约 9 GiB，约 40 GiB；92 GiB 留有余量。本机实测 365×24h LP 构建峰值 10.15 GiB。
- **后处理资源（M10A B3）：** 旧网络 365×24h 云端实测（S4N 试点，8470Q）违反分析 105 s / 9.3 GB、C1 72 s / 9.3 GB，均单线程（CPU 100 %）；本机实测 M12 分摊 6.5 s / 0.8 GB、GATES_V6 验收 < 1 s、单运行导出打包 7 s、Owen 对偶形式审计（`--duals` 模式）54 s / 8.1 GiB，新网络仅构建 65 s / 10.0 GiB（M12 S8）。外推到新网络云端（INFERENCE）：每次后处理约 6–8 分钟、峰值约 11 GiB；与另一通道的求解同时最多约 11 + 17 GiB，两会话同时约 34 GiB，远低于 92 GiB。运行脚本给每个后处理步骤 `POST_TIMEOUT_S`（默认 1,800 s，约为实测的 10 倍以上）与线程预算（容器核数减去正在运行的求解线程，至少 1）。
- **磁盘：** 预计用量约 30 GiB（INFERENCE）：
  - 每个 365×24h 运行目录约 1.8 GB——本机实测 R1 的 LP 数组 0.80 GB（`--stop-before-solve`，10,052,113 行 × 4,509,642 列，2,363 万非零元），其余按 56×3h 冒烟运行目录的行数比例（7.2 倍）估计——另加导出副本约 0.26 GB（S4N 实测）；11 个运行约 23 GB；
  - 结果打包（`final` 或 `halted`）约 1.8 GB；环境约 3.3 GiB + 包缓存约 0.75 GB；部署包与解包代码约 0.4 GB；变体 7 × 31 MB。
- **环境：** `env/install_env.sh`：538 个 conda 包（下载 742.8 MB，`env/ENV_DOWNLOAD.json`）+ 2 个 PyPI 包，安装后约 3.3 GiB；预计 5–15 分钟（2–20 MB/s，含解压；INFERENCE）。按 S4N 补充 01：下载超过 2 GB 或耗时超过 30 分钟先停下报告。安装后 `env_check.py` 逐包核对，关键包（python 3.11.13、pypsa 0.30.3、linopy 0.5.5、xarray 2025.1.2、pandas 2.3.1、numpy 1.26.4、scipy 1.15.2、gurobipy 12.0.3、netCDF4 1.7.2、h5netcdf 1.6.4、dask 2025.7.0、pyomo 6.9.3、highspy 1.11.0）必须完全相同。
- **系统盘与数据盘（M10A B5.4）：** `install_env.sh` 把 conda 包缓存（`CONDA_PKGS_DIRS`，约 0.75 GB 压缩包 + 约 3.3 GB 解压）、`TMPDIR` 与 pip 缓存放到包目录（`<包目录>/conda_pkgs_cache`、`<包目录>/tmp`），不占约 30 GB 的系统盘；`run_batch3.sh` 把 `TMPDIR` 设为 `runs/batch3/tmp`——linopy 0.5.5 在 `io_api=None` 时把每次求解的 LP 问题文件写入临时目录再由 Gurobi 读入（S4N 回执 solve_seconds 比 barrier 多 283 s 即此开销），365×24h 两会话并行约数 GB，落在数据盘。

## 6. 部署包与上传量

- 内容与每个文件的 SHA256：`PACKAGE_MANIFEST.json`、`SHA256SUMS`。约 149 MB：代码归档约 82.5 MB（不含 `research/`；含 `research_inputs/`、`data/` 等运行所需目录），两个网络 62.4 MB，两份构建回执 3.5 MB，其余（成本表、脚本、环境锁定、清单、计划）约 0.3 MB。
- **上传：** 单路上传（一个 rsync 流，不开并行流，不中断带 `--partial` 的传输），传后在实例上全量 `sha256sum -c SHA256SUMS`；失败的文件单独重传后再全量核对；全部通过后才放置许可。
- **预计上传时间（KB = 1000 B）：** 36 KB/s（S4O-6 AutoDL 克隆机上行）约 1.15 h；100 KB/s 约 25 分钟；318 KB/s 约 8 分钟。准确字节数见 `PACKAGE_MANIFEST.json`。

## 7. 云端步骤（供执行指令参考；主机、端口、密码不写入任何文件）

1. 单路上传部署包 → 全量 `sha256sum -c SHA256SUMS`。
2. `bash env/install_env.sh`（非克隆实例；克隆实例若已有同版本环境，可直接 `env/env_check.py` 核对）。
3. 按授权方式放置许可 → **在将要运行批次的同一个 tmux shell 中** `PY=<环境 python> GRB_LICENSE_FILE=<许可路径> bash preflight.sh` → `PREFLIGHT OK`（v3 新增 `guards` 节：该 shell 中残留任何测试 / 干跑开关——`ALLOW_UNREGISTERED`、`BUILD_ONLY`、`POST_ONLY`、`DRY`、`TRUNCATE`、`*_CMD`、`FAKE_*`、时限覆盖——即 `PREFLIGHT FAILED`，先 `unset`）。
4. 在 tmux 中：`PY=<环境 python> GRB_LICENSE_FILE=<许可路径> bash run_batch3.sh --auth "<用户授权原文>"`；中断后用同一命令续跑。只重做后处理：`POST_ONLY=1 PY=<环境 python> bash run_batch3.sh`（不启动任何求解；**不带 `--auth`**——v3 起无求解模式与 `--auth` 同时出现即拒绝启动，正式运行发现测试钩子也拒绝启动）。
5. 监控 `runs/batch3/STATUS.txt` 与 `MONITOR_<编号>.csv`；`POSTPROC_ERROR:<编号>:<步骤>:exit=…` 行（与 `runs/batch3/POSTPROC_ERRORS`）表示某个后处理步骤异常或超时：调度不受影响，批次结束后用 `POST_ONLY=1` 补做即可；`STOP_NOT_ACCEPTED` / `STOP_SAFE` 才是停批。
6. 下载：先轻量包 `results_light_*`（预计几十 MB），再完整包 `results_full_*`（预计约 1.8 GB：S4N 单个 365×24h 运行压缩后 159 MB × 11；各附 `.sha256`）；LP / 解数组留在实例数据盘（`export/batch/ARRAYS_MANIFEST.json`）。按 S4O-6 实测下行约 4 MB/s 约 8 分钟，0.3 MB/s 约 1.7 h（INFERENCE）。

## 8. 本计划中由准备端确定、请审阅确认的取值

1. 每个阶段用两条固定通道、各自依次推进，而不是严格成对等待（3.2 第 2 项）：第 2 阶段 R3 与 R5、R4 与 R6 大致同时，但 R4 / R6 不等待对方的前一个运行结束。
2. 第 3 阶段的通道分配（A = R7、R9、R11；B = R8、R10）按历史时长使两条通道接近（约 5 h 对 4 h）。
3. 无返回解时 G2 只核对不需要解的部分（3.3 第 3 项），验收或分类不可读按 G2 不通过停批。
4. 去一国检查不使用记为不可用的 R5–R7（3.6 第 3 项）。

## 9. 第四批开始时的 2920×3h 内存实测（补充 01 第 3 项；不在第三批中）

- P1 从第三批删除。2920×3h 的内存实测改到第四批开始时进行：第四批租用大内存机器，正式运行前用 1 小时作探针监控，**超过可用内存的 80 % 即止损**，再调整机器。具体做法写入第四批的执行指令。
- 参考：本机 365×24h 构建峰值 10.15 GiB；2920×3h 的 LP 约为 365×24h 的 8 倍，仅构建粗估约 80 GiB（INFERENCE）。P1 的计时与内存解析函数（`m10_batch3_summary.py p1_summary`）保留供第四批使用。

## 10. v3（M10A 上云前审查）的实现层改动——第 3 节规则不变

来源：`work/p1_m10a_20261022/M10A_REPORT.md`（发现编号同报告）。每项都有替身流水线测试；修复前后第 3.3 节表格逐格行为对照见报告第 5 节。

1. **F1（S1）`run_batch3.sh` `busy()`：** 原实现 `ps -eo cmd | grep -c '[s]2_solve.py'` 把 `/usr/bin/time` 包装进程与 python 进程各计一次，一个正在跑的求解计为 2，而第二条通道启动前要求 `< 2` → 正式运行第 1 阶段 R2 必然 `STOP_SAFE:SOLVER_BUSY_R2`，整批在 R1 之后停下等人（本机实证；替身测试的命令行原不含 `s2_solve.py`，从未覆盖）。现只计 python 进程（排除 `time` / `setsid` / `env` 包装行），替身求解器改以 `scripts_project/s2_solve.py` 同名包装启动，所有调度测试都经过这一检查。
2. **F2（S2）后处理超时与异常记录：** 违反分析、C1、M12 分摊、Owen 对偶形式、去一国右端项检查、重评、批级去一国 / 受益 / 汇总 / 打包每步在 `timeout -k 30 $POST_TIMEOUT_S`（默认 1,800 s；打包 7,200 s）下运行；非零退出或超时记 `POSTPROC_ERROR:<编号>:<步骤>:exit=<码>` 与 `POSTPROC_ERRORS`，汇总 `BATCH3_SUMMARY.json/.md` 列出，调度不变，事后 `POST_ONLY=1` 补做。C1 输入缺失（违反分析异常或超时）仍按 3.3 第 3 项"C1 不可计算 = C1 (a) 不通过"分类；M12 / Owen / 右端项检查的输出不进入 G2.3（只核对已登记的导出），其异常不改变标签——与修复前相同，现在多了记录与超时保护。
3. **F3（S2）线程预算：** 辅助 Python 进程（后处理、变体生成、核对、汇总、打包）带 `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `NUMEXPR_MAX_THREADS` = 容器核数 − 当时正在运行的求解线程数（至少 1）；云实例 `nproc` 为宿主机 208 而配额 25 核。求解命令及其环境不变（测试核对求解进程看到的 `OMP_NUM_THREADS` 为空），唯一新增的是 `TMPDIR`（第 4 项）。
4. **F4（S2）临时目录与缓存：** `TMPDIR=runs/batch3/tmp`（求解的 LP 问题文件也落在此）；`install_env.sh` 的 `CONDA_PKGS_DIRS` / `TMPDIR` / `PIP_CACHE_DIR` 指向包目录（第 5 节）。
5. **F7（S2）测试开关防护：** `preflight.sh` 新增 `guards` 节（默认第一节）；`run_batch3.sh` 正式运行（求解模式且无 `ALLOW_UNREGISTERED`）发现 `*_CMD` / `TRUNCATE` / `FAKE_*` 即 `REFUSED`，`BUILD_ONLY` / `POST_ONLY` / `DRY` 与 `--auth` 同时出现即 `REFUSED`；`STATUS.txt` 的 `START` 行记录 `tmpdir`、`post_timeout_s`、`allow_unregistered`、`hooks`。本机测试（`ALLOW_UNREGISTERED=1`）与干跑（无 `--auth`）用法不变。
6. 工具要求增加 `timeout`（coreutils；`preflight.sh tools` 节检查）。

v4（`M10A_SUPPLEMENT_01.md`，第 145 项，用户 2026-10-22 启动消息"同意第 145 项"；登记日期 2026-10-23；**变更时新网络在 365×24h 上没有任何求解结果**，不违反"看到结果后不改规则"）：

7. **D1 时限登记值变更（第 3.1 节）：** 365×24h 每次 TimeLimit 21,600 → **28,800 s**（6 → 8 h），墙钟 22,500 → **30,000 s**（余量 900 → 1,200 s，约为 M10A F8 实测开销 500–560 s 的 2 倍）；适用于 R1–R11 全部运行，两个档案相同。**理由：** M10A B4 估计 R1、R5–R7、R10 的墙钟为 4.0–4.9 h，上限超过原时限的 75 %；R1 到时限没有可用解会停掉整批，R5–R7 是去一国检查的核心证据，R10 是敏感性。延长时限只在运行确实变慢时才多花时间，正常情况下总时长不变；最坏情况 6 × 30,000 s ≈ 50 h，加后处理与间隔约 52 h（第 4 节）。实现：`run_batch3.sh` 的登记常数 `R_TL` / `R_WALL`（脚本仍拒绝任何与登记值不同的时限 / 墙钟 / 许可间隔）、`preflight.sh` 档案检查的 TimeLimit 参数、测试、本文件第 2 节表与第 3.1 节；与 365×24h 第三批无关的历史值（S4O、M08a 的 21,600 / 22,500）不改。
8. **D2 违反分析与 C1 只重做一次（第 3.5 节）：** 退出码非 0 或超时 → 不完整输出改名 `*.failed<n>` 保留 → 以相同环境与参数重做一次（`POSTPROC_RETRY`）→ 仍失败按 3.3 第 3 项"C1 不可计算 = C1 (a) 不通过"。不重跑求解，不改 `stop_class` / 阈值 / 3.3 表格；其他后处理步骤保持第 2 项做法。**理由：** 求解成功但后处理偶然失败（瞬时 I/O 或内存峰值）不应让 R1、R2 的一次失败停掉其余约 15 小时的运行；确定性错误重做后仍失败，结论不变。测试：R2 的违反分析"第一次失败、重做成功"（不停批）与"两次都失败"（按规则停批），R6 的 C1 同样两种（正常 / 不可用）。
9. **D3 预检资源硬下限（第 5 节）：** 内存 92 → **64 GiB**，数据盘可用 60 → **45 GB**，核数 25 不变；租用建议仍为内存约 90 GB 以上、数据盘约 80 GB。测试：`test_preflight_resource_floor`（cgroup v2 配额 25 核 / 70 GiB 通过，60 GiB 或 20 核不通过）。

## 11. 第三批补做（S1）——登记于任何补做结果出现之前（M10R，2026-10-24；第 3 节规则不变）

**背景（第三批结果，`work/p1_m10_20261022/M10_REPORT.md`）：** R1–R10 已求解，9 个 ACCEPTED_LAYER2；R9（不互联保留存量）求解正常（C1 (a)(b) 通过），但分国账本代码在"一体化派生、按不互联求解、保留跨境存量"的网络上 `KeyError: '59'`（跨境 FOM 账本 meta 里零容量候选线路的行指向被变体删除的设备），B16 不可计算 → C1 (c)、M12、Owen 不可计算、G2.3 不过 → 按 3.3 第 3 项停批；R11 未启动。缺陷在 M10R 中定位并修复（`scripts_project/s4d_ledger.py`、`m12_rhs_audit.py`；修复提交见 `research/06_scope_redesign/p1_m10r_20261024/M10R_REPORT.md`），修复对其余 9 个已接受运行的任何后处理结果不产生改变（56×3h 五个数据集逐项回归相同；365×24h 的 9 个运行与 R11 的网络都不走修复的代码路径，`XB_LEDGER_CHECK_365.json`）。

### 11.1 范围

1. **R9 后处理重做（不重新求解）：** 用修复后的代码对 R9 重做全部后处理（账本与 B16、违反分析、C1、M12 分摊、Owen 对偶形式、GATES_V6、分级分类），输出写到新目录；原运行目录、原标签（NOT_ACCEPTED）、批次 `STOP` 与原汇总不改。R9 的新标签**只能**由这条路径得到，并按 11.3 登记为"事后修复的代码缺陷"。
2. **R11（分国 WACC 不互联）单独补跑：** 此前从未启动；档案 A、Threads 8、TimeLimit 28,800 s、墙钟 30,000 s、许可间隔 330 s、变体（`EXPECTED_VARIANTS.json` 核对）、成本表（disconnected）、C1 参照（本批 `BATCH_REFERENCE.json`）、验收与分级停批规则——全部与第 2、3 节该运行的登记值相同。求解一次，不重试。
3. **批级补算：** 在新目录中重算 R9 − R2、R11 − R2 与信息项 R11 − R10，以及新的批级汇总 `BATCH3_SUMMARY_S1.json / .md`（B6、去一国、受益、第二级比较按原批结果照抄）；原 `BATCH3_SUMMARY.json / .md` 不改。

### 11.2 执行方式（`run_batch3.sh` 的按运行选择模式；默认关闭，批次模式行为未变）

| 步骤 | 命令（在包目录、运行批次的同一 tmux shell 中；`PY=<环境 python>`） | 许可 | 输出 |
|---|---|---|---|
| (a) R9 重做 | `PY=… bash run_batch3.sh --repost R9 --into runs/batch3_s1`（无 `--auth`；原实例以外需 `--arrays <含 lp/ 与 solution/ 的目录>`） | 不需要 | `runs/batch3_s1/R9/`、`runs/batch3_s1/export/R9/`、`REPOST.json`、`REPOST_CHECK.json`、`results_*_repost_R9_*` |
| (b) R11 补跑 | `GRB_LICENSE_FILE=<许可> PY=… bash run_batch3.sh --auth "<用户授权原文>" --only R11` | 需要 | `runs/batch3/R11/`、`runs/batch3/export/R11/`、`results_*_only_R11_*` |
| (c) 批级补算 | `PY=… bash run_batch3.sh --summary-s1 --into runs/batch3_s1 --use R9=runs/batch3_s1/R9` | 不需要 | `runs/batch3_s1/batch_s1/BATCH3_SUMMARY_S1.json / .md`、`results_*_summary_s1_*` |

- **`--only` 的语义：** 只求解所列的、从未启动过的运行；已结束的运行一律拒绝启动（不重试）。批次 `STOP`（R9 的 g2）在该模式下被**承认并记录**（`STATUS.txt` 的 `ONLY_MODE` 行），不阻止所选运行；所选运行自身按 3.3 第 3 项分级：G2 不过 → 追加 `STOP`、不再启动后续所选运行、退出码 3；无返回解或 C1 (a) 不过 → `UNUSABLE`，继续；只有 (b)/(c) 不过 → 不停。不做重评（本批参照已是最终参照）、不做第二级比较、不改批级汇总；结果包只含所选运行。启动前存在 `STOP_SAFE` 则拒绝（安全停止先由用户处理）。
- **`--repost` 的语义：** 无求解模式（不读许可、不留间隔、拒绝 `--auth`）；输入只读（求解后网络、对偶、回执、门控从原目录读取或链接，LP / 解数组链接），违反分析重算后与原结果逐项比较（代码未改 → 必须相同，`REPOST_CHECK.json`），C1 (a)(b) 数值必须与原值相同；分类只记录（`STOP_CLASS.json`），不写 `STOP` / `UNUSABLE`。
- **机器：** 优先原实例（同一 CPU，R11 与 R10 可比；R9 的 LP / 解数组仍在数据盘）。原实例开不了有卡模式时，可在任何 ≥ 25 核、≥ 64 GiB 的实例上做：R11 只依赖部署包（v6）；R9 重做所需的 LP 数组用 `s2_solve.py --stop-before-solve` 在登记网络上确定性重建（M10P / M10A 干跑已证明逐字节相同），解数组 `solution/` 从原实例取回，求解后网络与对偶从完整包中取（`--arrays`）。两种做法在报告中如实记录。
- **规则：** R11 求解一次、不重试；R9 不重新求解；阈值、档案、时限、网络、成本表与停批分级不改。

### 11.3 "事后修复的代码缺陷"的登记方式

R9 的标签变更在报告与台账中按以下格式登记，缺一不可：**原标签**（NOT_ACCEPTED，`STOP_NOT_ACCEPTED:R9:g2`，2026-10-24 00:27:53 SGT）；**原因**（后处理代码缺陷：跨境 FOM 账本 meta 的零容量候选行在保留存量变体中指向被删除的设备；求解本身正常）；**修复提交**（M10R 的提交 SHA）；**回归证据**（56×3h 五个数据集修复前后逐项相同；365×24h 结构核对 9 个运行不走修复路径；56×3h 保留存量复现：修复前同一 KeyError，修复后 B16 成立、C1 (c) 可计算、ACCEPTED_LAYER2）；**新标签**（由 `--repost` 得到，附 `REPOST_CHECK.json`：违反分析逐项相同、C1 (a)(b) 相同）。求解不重做，阈值不改。

### 11.4 演练要求（本次的教训）

每次打包前，对 **7 个变体加 2 个基础网络的每一种网络类型**（一体化、不互联、去 VN / TH / LA、b1、保留存量、分国 WACC 一体化 / 不互联）在 56×3h 上演练一遍完整的后处理链（账本与 B16、违反分析、C1、M12、Owen、GATES_V6、分类）：有真实 56×3h 求解结果的类型用真实结果，其余用维数正确的合成解只验证"能跑通、不报错、恒等式可算"，并注明哪些是合成数据（`DRILL_POSTPROC.json`；脚本 `research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh`；`make_package.sh` 要求 `DRILL_JSON` 指向当前提交的完整演练结果）。
