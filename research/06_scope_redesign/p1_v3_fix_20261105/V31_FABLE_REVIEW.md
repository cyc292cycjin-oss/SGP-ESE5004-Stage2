# v3.1 修正针对性独立审查报告（台账 W02，决策清单第 199 项）

- **指令：** `work/p1_v3_fix_20261105/V31_FABLE_REVIEW_INSTRUCTION.md` v1，SHA256 `eb805fc125567d8b14642a0259ef6997f51c6ddff9c2f1ab7e5b56dcbad67f6b`，与同目录 `V31_FABLE_REVIEW_SHA256.txt` 一致（2026-11-05 20:58 SGT 核对）。
- **执行环境：** Claude Code，Fable 5.1。独立审查者，未参与诊断与修正。只读：不改模型、代码、网络或部署包。**Gurobi 0 次，HiGHS 0 次**；只做静态读取（pypsa 0.30.3 / xarray 读网络数组）、`git grep`、文件比对。不连 HPC、云、VPN。本机计算约 45 分钟（上限 2 h），磁盘新增约 0.76 GB（审查 worktree 0.75 GB + 证据 0.7 MB；上限 5 GB）。
- **对象：** 分支 `codex/v3-fix-20261105` 头提交 `1117a07f`（本地与 origin 一致），包提交 `d3b9a3bc`（`1117a07f` 的祖先）。审查 worktree `/home/jin/wt_v31_review`，分支 `codex/v31-review-20261105`，从 `1117a07f` 开出。
- **未读：** 各 `V3_REVIEW_DECISIONS_*.md`、`V3_FIX_INSTRUCTION.md`、`V3_DIAG_INSTRUCTION.md`、`V3_FIX_PROGRESS.md`。
- **结论分级：** VERIFIED（实际数组、日志或文件比对）、EXACT（逻辑逐项核验）、INFERENCE（机制解释）、PROPOSED（未执行）。
- **审查脚本与数组查询输出：** `work/p1_v3_fix_20261105/review_v31/{scripts,evidence}/`（随本报告提交）。

## 0. 一句话结论

**可以提交正式批次**（前提不变：HPC 冒烟 `runs/smoke56_v31` 必须 PASS，见 `RUN_PLAN_HPC_V3.md` 第 15 节）。六个审查项没有 S1；两项 S2 都是"残余风险、不阻止提交"，列于下表供用户知悉。

## 1. S1 / S2 / S3 表

S1 = 可能使正式 B6 变化超过约 1 %、改变任一参与者 Owen 受益的符号或排序、或使全年仍不可解或使验收失效。

| 级别 | 编号 | 内容 | 对应审查项 |
|---|---|---|---|
| **S1** | — | **无** | — |
| S2 | S2-1 | **全年 2920×3h 在新代码下的预处理与可行性尚未实测**。诊断与修正只在 ≤ 248 时段窗口上做到"预处理通过"，"预处理通过"不是可行性证明；唯一的全年求解是 v3 的 365×24h（optimal）。可选脚本 `hpc_v31/fullsize_presolve.sh` 已备未运行。若全年仍在预处理失败，正式批次会在每个运行的前 1–2 小时停下（构建 + 预处理），损失以小时计、不以 240 h 计；这是用户的取舍（先跑 `fullsize_presolve.sh` 或直接以正式批次为测试），不是修正缺陷 | 1 |
| S2 | S2-2 | **迭代数增加不触发早期止损，但压缩 TimeLimit 余量**。止损规则只用第 11–20 次迭代的单次耗时，不用迭代数；56 时段上单次耗时没有变慢（F1 −20 %，F2 −3 %）。若全年迭代也多约 23 %（350 → 约 430），在接近止损阈值的 1,850 s/次时总耗时约 796 ks + 预求解 ≤ 864 ks，仍在 TimeLimit 内但余量不足 8 %；超过约 467 次迭代会以 TIME_LIMIT（非 STOP_SAFE）结束。按指令不改登记值 | 5 |
| S3 | S3-1 | 诊断报告第 5.3 节"再用单纯形确认不可行，共 292 万次迭代"没有日志支撑：IIS 日志 1800 s 内没有任何 `infeasible` 行，只有 `IIS computation: hitting time limit`。这反而削弱了"实质不可行"的可能，支持修正结论；只是措辞需改 | 1 |
| S3 | S3-2 | LP 统计中 RHS 下界 8e-14 的来源已查明：28 个**静态**负荷（`industry biomass demand` 27 个、`LA2 0 industry heat demand` 1 个，8.3e-14–3.8e-11 MW，无时间序列）进入节点平衡右端项。可被任何正供给满足，远小于 FeasibilityTol，不是不可行来源；建议下次重建网络时清零 < 1e-9 MW 的负荷（本次不重建） | 1 |
| S3 | S3-3 | `zero_slack_check.py` 的端口分类只看方向（`classify_port` 第 81–123 行），不看容量与下游去处。本次四个网络上每个移除端口都可扩建且下游有去处（第 4 节实测），所以结论不受影响；作为长期闸门建议补"容量 > 0 且下游有汇"的判定 | 3 |
| S3 | S3-4 | 两个价格表新增字符串列 `note`（宽表 `NODAL_PRICES.csv` 第 2805 行）。正式路径没有读取者；非正式路径的 `s4l_2_summary.py:190`、`l23_c9_summary.py:180` 若对该文件做数值运算会碰到字符串列。不影响本批 | 4 |
| S3 | S3-5 | 修正后的 56 时段 F1 迭代 96 次，高于 `RUN_PLAN_V3.md` 第 26 节预测所依据的"一体化 56 时段 80–83"区间；预测按指令不改，正式结果对照预测时应注明写法已变 | 5 |
| S3 | S3-6 | 诊断的删行 / 改写探针只在 8 个失败月窗口中的 3 个（F1 M01、F1 M02、F2 M02）上做过，修正后的复核也只做了 F1 M01、F2 M02。新写法已把该行从所有窗口中去掉，所以其余 5 个月的差别只在 S2-1 所述的"其他预处理问题"，不单列 | 1 |

## 2. 审查项 1：根因

**结论：诊断证据足以支持"必要行 = `research_bunker_co2_limit`，机制 = 零松弛行 + 预处理舍入"；没有发现被它掩盖的其他不可行来源；全年可行性未被证明（S2-1）。**

| 核对 | 证据 | 等级 |
|---|---|---|
| 只删该行（1 行）预处理即通过；右端项 0 → 1 t 即通过；改写为"计量流量 = 0 + 删行"即通过 | `work/p1_v3_diag_20261105/evidence/runs/F1_M02_reform/DEL_PROBE.json`（`rows_dropped: 1`，`fixed_zero.columns: 18368`，`verdict: PRESOLVE_PASSED`）；`F1_M02_rhs1/DEL_PROBE.json`（`row_label 7148145`，`rhs_old -0.0 → 1.0`，`PRESOLVE_PASSED`）；`F1_M01_del_bunker/`、`F2_M02_del_bunker/` 同 | VERIFIED |
| 原样 LP 为 INF_OR_UNBD、0 次 barrier 迭代 | `runs/F1_M02/p2_log_scrubbed.txt:49–50`（`Model is infeasible or unbounded`，`bar_iter_count: 0`） | VERIFIED |
| 参数敏感性：`DualReductions=0`、`Aggregate=0`、`Presolve=1` 通过，`NumericFocus=3` 仍失败 | 诊断报告第 5.2 节；与"对偶约简 + 聚合"的机制一致 | VERIFIED（读报告与账本） |
| 非无界：四个窗口 LP 负成本列 0 个、改进方向 0 个 | `evidence/lp_scan/LP_SCAN_F1_M01.json`：`negative_cost_columns: 0`，`improving_free_columns: 0`，`zero_cost_free_columns: 3377` | VERIFIED |
| IIS 未得出；日志无 `infeasible` | `runs/F1_M02_iis/gurobi_iis_log_scrubbed.txt:229–230`；`grep -ci infeasible` = 0（日志与 stdout 均为 0）→ S3-1 | VERIFIED |
| RHS 下界 8e-14 的来源 | 四个网络 `loads.p_set` 中 28 个 0 < |p_set| < 1e-9 的静态负荷，最小 `LA2 0 industry heat demand` 8.307e-14 MW，最大 `LA2 0 industry biomass demand` 3.787e-11 MW，其余 26 个为 ID 各节点 `industry biomass demand`；无时间序列（`review_v31/scripts/tiny.py` 输出；`evidence/store_checks2.json` → `tiny_static_loads`）。其他可成为右端项的量（时变负荷最小 1.66 MW、固定机组 / 链路 / 库的 p_nom·p_max_pu、e_initial、入流）都 ≥ 1e-2 → S3-2 | VERIFIED |
| 全年才出现的其他不可行来源 | 年度与末时段行在全年与截短口径下右端项相同（诊断 `evidence/ANNUAL_RHS_F1.json`，读取核对）；649 个 Store 中没有"循环且端口单向"或"初值 0、下界 0、只出流"的强制链（第 4 节）；网络中**没有**切负荷 / 高价备用发电机（`load_shedding_like_generators.count = 0`），所以若 3 小时峰荷超出可建容量会是硬不可行，但 56×3h（含 1 月峰）与 365×24h（全年）都 optimal，且供给侧容量基本可扩建；残余风险归入 S2-1 | VERIFIED + INFERENCE |

## 3. 审查项 2：等价性

**结论：精确算术下同一可行域、同一最优值；前提在 F1–F4 上全部成立（独立数组查询，与修正报告第 2.1 节一致）。**

独立实测（`review_v31/scripts/net_checks.py` → `evidence/net_checks.json`，四个网络相同）：

| 前提 | F1 / F2 / F3 / F4 实测 |
|---|---|
| 账户母线上只有 82 个 Link 端口（全部 `bus2`）+ 账户 Store，无其他组件 | `ports 82, distinct_links 82, non_link_attached [Store co2 bunkers ASEAN]` |
| 端口系数 > 0 含时变 | 静态 0.2571（min = max），时变效率列 0 个 |
| 计量 `p_min_pu ≥ 0` 含时变；`p_max_pu` | 静态 0.0（min = max），时变 `p_min_pu` 列 0 个；`p_max_pu` 1.0，时变 0 个 |
| 账户 `e_initial = 0`、非循环、无存储损耗 | 0.0 / False / 0.0；`e_min_pu −1`，`e_nom` 可扩建、上限 ∞、资本成本 0；时变库参数 0 个 |
| 全部权重 > 0 | objective / generators / stores 最小 3.0 h，和 8,760 h |
| 每个航空终端母线有可用的非化石孪生链路 | 82 / 82 个终端母线都有可扩建（或容量 > 0）的非计量进料链路 |

**等价性（EXACT）：** 账户 p_store = −Σ 0.2571·p_meter ≤ 0，e_T = Σ_t w_t·0.2571·Σ p_meter,t ≥ 0；e_T ≤ 0 ⇔ 全部 p_meter,t = 0。两种写法下其余变量的可行集与目标相同。`e_min_pu = −1` 只放宽库的下界，不参与。

**可扩建 `p_nom` 的成本与退化性（EXACT）：** 82 条计量链路全部 `p_nom_extendable`，`p_nom_max = ∞`，`capital_cost = 0`，`marginal_cost = 0`。`p_nom` 列零成本、只出现在 `Link-ext-p-upper/lower`（p ≤ p_nom·1，p ≥ p_nom·0）；两种写法下它都是"零成本、非改进"的自由方向（LP 扫描 `zero_cost_free_columns 3377`，`improving 0`），最优值不受影响，Gurobi 预处理把它固定或删除。账户 `e_nom`（零成本、∞ 上限）同理。新旧写法在这一点上完全相同，不新增退化。

**行数核对：** 新写法应多 82 × T − 1 行与非零元、列不变：F1_M01 +20,335、F2_M02 +18,367、56 时段 +4,591（修正报告 5.1 / 5.2，读取 `evidence/REGRESSION_56.md`）；`ZERO_SLACK_CHECK_F1_F4.json`：`rows 246 = 82 × 3`，`single_term_rows / equality_rows / zero_rhs: true`，`missing 0, extra 0`。VERIFIED。

## 4. 审查项 3：同类隐患（重点）

**结论：11 个国家净零行都不是强制行；移除端口可建、捕集 CO₂ 有去处；没有其他同构的零松弛链。不报 S1。**

**(a) 移除端口能否走流量（VERIFIED，`net_checks.json` → `countries`）：** 每国大气账户上的移除端口全部 `p_nom_extendable` 且 `p_nom_max = ∞`（"usable = removal"）：

| 国 | 移除端口（可用） | 类型 | 捕集 `co2 stored` 母线数 |
|---|---|---|---|
| BN | 8 (8) | DAC、biomass EOP CC、biogas upgrading、industry biomass boiler CC、industry direct firing biomass CC、industry biomass CC | 1 |
| ID | 312 (312) | 同上 | 39 |
| KH | 37 (37) | 同上 | 5 |
| LA | 48 (48) | 同上 | 6 |
| MM | 136 (136) | 同上 | 17 |
| MY | 53 (53) | 同上 | 7 |
| PH | 47 (47) | 同上 | 6 |
| SG | 7 (7) | 除 industry biomass CC 外同上 | 1 |
| TH | 48 (48) | 同上 | 6 |
| TL | 7 (7) | 同 SG | 1 |
| VN | 64 (64) | 同上 | 8 |

**(b) 捕集 CO₂ 的下游去处（VERIFIED，`store_checks2.json` → `co2_stored_buses_without_consumer`）：** 四个网络各 100 个 `co2 stored` 母线，**全部**至少有一条可用的消耗端口（`bus0` 取出或负效率消耗，容量可扩建或 > 0）：`CO2 sequestration`（→ 本国 `co2 sequestered`，仅 BN、ID、KH、MY、PH、TH、VN，上限为正）、`CO2 export extra-ASEAN`（→ `co2 sequestered extra-ASEAN <国>`：11 国都有，`e_nom_extendable`，上限 ∞，`capital_cost 54.70 EUR/t`——有价的无限汇）、`CO2 pipeline`、`CO2 ship`、LA 的 `CO2 transit ship / transit export`。**LA、MM、SG、TL** 没有本国封存账户，但每个捕集母线都有 `CO2 export extra-ASEAN`（SG、TL）或出口 + 管道 / 船运（LA、MM）。**F2 / F4（`no_new_xb`）** 管道减少、船运减少，但域外出口在四个网络中都在，所以每国都保有一条有价的汇。各国的 `co2 stored` 缓冲库是循环库（`e_cyclic True`），不能当净汇，不计入。

**(c) 其他同构链（VERIFIED，`store_checks2.json`）：** 649 个 Store 中，"循环且可用端口全部单向"0 个；"非循环、`e_initial ≤ 1e-9`、`e_min_pu ≥ 0`、只有出流端口"0 个；"无可用端口"0 个。只进流的非循环库只有：燃料舱账户（已显式逐变量）、7 个国家 `co2 sequestered`（上限 1.34 Mt–2,575 Mt）、11 个 `co2 sequestered extra-ASEAN`（上限 ∞、54.7 EUR/t）——都不是零松弛。`research_co2_storage_cap` 上限为 0 的 LA、MM、SG、TL 没有该行（`configured_caps_without_row`）。

**(d) 闸门方法的局限（S3-3）：** `zero_slack_check.py` 只按方向分类端口；本次网络中每个移除端口都可建、每个捕集母线都有汇，所以其 `removal_ports_present` 判定成立。若未来网络把某国的 DAC / CC 设为 `p_nom_max = 0`，或去掉域外出口，该国净零行会变成实质强制行而不被此闸门发现。

## 5. 审查项 4：下游

**结论：用法表完整；NaN 不进入任何总量或判定。**

- `git grep -nE "research_bunker_co2_limit|BUNKER_ROW|BUNKER_CO2_BUS|co2 bunkers|research_bunker_net_zero" -- scripts_project hpc_package_src`（`review_v31/scripts/grep_usage.sh`）：命中 `assembly_components.py`（建网挂接清单）、`l23_violation_analysis.py:90`、`m12_allocation.py:287`（独立成本读网络，不读约束）、`m12_rhs_audit.py:78/139/153`、`s2_solve.py:506`（B1_BUNKERS）、`s4b_acceptance.py:90–95`、`s4c_3_*`（登记文字）、`s4c_layers.py`、`s4d_ledger.py:10/45–46`、`s4i_static_audit.py`（建网审计）、`s4o_c1_precision.py:165`、`v3_data.py`、`v3_screen_tables.py:19`（筛查表列名）、`v3_static.py:232`、`zero_slack_check.py`。与修正报告 2.2 节表相比没有遗漏正式路径上的读取者。
- **NaN 的传播（VERIFIED）：** NaN 只写入 `s4d_ledger.nodal_prices`（`NODAL_PRICES.csv`，`s4d_ledger.py:314–315`）与 `v5_gates.nodal_prices`（`nodal_prices_summary.csv`，`v5_gates.py:408–412`）。台账结算用原始对偶 `n.buses_t.marginal_price`（`s4d_ledger.py:108`），不读价格表；`m12_allocation.py:216` 同样用原始对偶；`m12_rhs_audit` 的 y'b 只累加右端项非零的行（新旧都是 0）；`b4_batch4.py` 汇总与 `REFERENCE_VALUES.json` 对照只涉及目标值 / B6 / Owen（第 404–414、510 行，"description only"），不读价格表；`v5/gates_v6.py` 不读价格表（`git grep` 无命中）；`run_batch4.sh:465` 只把 `NODAL_PRICES.csv` 复制进导出。回归产物 `evidence/regression_56/F1/NODAL_PRICES.csv:2805` 为 `co2 bunkers ASEAN` 行：数值列空、`note` 列为说明文字；`COUNTRY_COST_LEDGER` 的 `bunker_co2 bunkers` 列 0.0（`REGRESSION_56.md`）。
- Owen 行所有者：`m12_rhs_audit.py:153` 对该名下所有行返回 BUNKER；C1 与违反量归属沿用名称规则（`s4o_c1_precision.py:165`、`l23_violation_analysis.py:90`）。`s4b_acceptance.py:93–95` 逐标签赋参照量，多行直接适用。EXACT。

## 6. 审查项 5：迭代增加与早期止损

**结论：误止损风险没有因 v3.1 增加；TimeLimit 余量略减（S2-2）。只评估，不改登记值。**

- **规则实现**（`b4_batch4.py:272–287 projection`，`run_batch4.sh:373–376`）：第 20 次迭代记录后，`(t20 − t10)/10 × 参考迭代数 + 已用时间 > 0.80 × 864,000 = 691,200 s` 则止损；参考迭代数 F1/F3 350、F2/F4 250（`BATCH_DEF.json` `iterations_reference`）。**迭代数不是输入**，只有第 11–20 次的单次耗时起作用。
- **56 时段实测**（`evidence/regression_56/*/SOLVE_RECEIPT.json`：F1 96 次 / 183.29 s / 269.6 work，F2 81 次 / 132.73 s / 193.5 work；修正前 80 / 190.53 / 225.5，66 / 111.24 / 137.1）：

| 量 | F1 新 / 旧 | F2 新 / 旧 |
|---|---|---|
| 迭代数 | 96 / 80（+20 %） | 81 / 66（+23 %） |
| 单次耗时 s | 1.91 / 2.38（−20 %） | 1.64 / 1.69（−3 %） |
| 单次 work units | 2.81 / 2.82（0 %） | 2.39 / 2.08（+15 %） |

- **评估（INFERENCE）：** 止损阈值仍是 Atlas 上约 1,840–1,860 s/次（第 14.2 节）；新写法的单次耗时没有变慢，所以被误止损的概率与 v3 相同。迭代数多 20–23 % 的后果在 TimeLimit：若全年 350 → 约 430 次、单次 1,850 s，总计约 796 ks + 预求解（1.4–9 ks）< 864 ks，余量约 60 ks；约 467 次以上则 TIME_LIMIT。投影用 350 次会低估约 20 %，使止损更少触发、TimeLimit 更可能触发——方向上不造成误止损。56 时段一次运行不足以外推到全年。

## 7. 审查项 6：部署包

全部核对通过（VERIFIED）：

| 项 | 结果 | 证据 |
|---|---|---|
| 网络与 v3 逐字节相同 | 4 个 `.nc` + 2 构建回执 + 2 变体回执 + 成本表 9 / 9 SHA256 相同；与 `pbs/HPC_PLAN.txt` NETWORK 行、`BATCH_DEF.json` `registered_sha / registered_bytes` 8 / 8 一致 | `sha256sum` 比对（本机）；`HPC_PLAN.txt:12–15` |
| 包完整性 | `sha256sum -c SHA256SUMS`：47 / 47 OK；`SHA256SUMS` 的 SHA256 `b8216361…`；`COMMIT` = `d3b9a3bca18755b50397f31d4b61abe39fb50c3f` | 本机 |
| `BATCH_DEF.json` | `limits_status REGISTERED`；`build_commit a1ef782b`（网络构建提交，与 NETWORK 行一致）；`run_dirs` = `runs/batch5` / `runs/smoke56_v31` / `runs/build_only_f1`；`HPC_PLAN.txt:23 RUNDIRS` 相同；时限、walltime、资源、冒烟期望值与 v3 定义相同 | 文件读取 |
| 第 15 节在任何 v3.1 HPC 求解之前提交 | `d3b9a3bc` 2026-11-05 19:51:46 SGT，已推送（origin 头 `1117a07f` 含之）；包内 `RUN_PLAN_HPC_V3.md` 与 work 副本相同、含第 15 节；本审查指令 21:20 写成时冒烟才排队 | `git log`、`diff` |
| 操作指南 | work 副本与包内副本相同；代码块内尖括号占位符 0 处（`awk` 扫描 33 个代码块）；`hpr31` 38 处、`runs/batch5` 29 处、`runs/smoke56_v31` 7 处；`hpr3/`、`runs/batch4` 只出现在"不动 / 拿错包"的提示；账号用 `$HPC_USER` 变量 | `grep` / `awk` |
| 运行目录单一来源 | `hpc/hpr_job.sh`、`hpr_submit.sh`、`hpr_status.sh` 都读 `RUNDIRS`（3 / 4 / 3 处） | `grep -c` |
| `zero_slack_check.py` 接入打包 | `hpc_v31/make_hpc_package_v31.sh:53–55`：结果行非 `ZERO_SLACK_CHECK_RESULT:PASS` 即 `REFUSED`、不出包；`ZERO_SLACK_CHECK.json` 在包内并登记于清单（第 99–109 行） | 读取 |
| 泄露扫描（遮蔽输出，`review_v31/scripts/leak_scan.py`，44 个文本文件 + 代码 tar 目录清单） | WLS 许可值 / UUID 形态 0；`GRB_LICENSE_FILE` 只有键名；主机名只有公开的 `atlas8.nus.edu.sg`（登录节点，指南必需）与 `token.gurobi.com`；IPv4 形态全部为软件版本号与 `1.1.1.1`（公共 DNS，V14 已归类）；端口形态全部为回执中的 `PPM:` 资产编号；实例名 0；`code_d3b9a3bc.tar.gz` 1,616 项中无 `.lic`、`known_hosts`、密钥文件，`results_project/` 只有 `.gitignore`。对 `p1_v3_fix_20261105/` 与 `hpc_v31/` 同样扫描：只有公开主机名、键名与提交信息中的 `noreply@anthropic.com` | 本机 |

## 8. 偏差与说明

1. 第一版网络脚本把"出口"只定义为 `bus0` 取出，曾把 MM 的 2–3 个 `co2 stored` 母线误判为"无出口"；第二版（`store_checks2.py`）把负效率消耗端口与容量都算入后，100 / 100 个母线都有可用消耗端口。两版输出都保留在 `review_v31/evidence/`。
2. 没有打开 LP 文件（诊断已删除通过窗口的 `problem.lp`），右端项来源由网络数组推断并与 LP 日志的 8e-14 对上（最小静态负荷 8.307e-14）。
3. 本报告不写台账条目、不改任何已交付文件；只新增 `V31_FABLE_REVIEW.md` 与 `review_v31/`。

## 9. 提交

分支 `codex/v31-review-20261105`（自 `1117a07f`，worktree `/home/jin/wt_v31_review`），镜像 `research/06_scope_redesign/p1_v3_fix_20261105/{V31_FABLE_REVIEW.md,review_v31/}`，推送到 origin。提交号见推送后的 `git log`（本文件不能写自己的提交号）。未创建 PR。
