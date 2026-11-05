# V3.1 燃料舱约束修正与重新打包报告（决策清单第 195 项）

- **指令：** `work/p1_v3_fix_20261105/V3_FIX_INSTRUCTION.md` v1，SHA256 `f8ba88a29ff08aa6b11becf432809355d98f8a406f6e482debff482e5fdfa5aa`，与同目录 `V3_FIX_SHA256.txt` 一致（2026-11-05 核对）。
- **开始条件：** 用户确认 AnyConnect 已断开、本机与 AutoDL 没有其他 Gurobi 进程（本机另查：WSL 与 Windows 均无 Gurobi / 求解进程，Cisco AnyConnect 网卡为 Disabled）。之后未再停下等用户。
- **执行环境：** Claude Code，Opus 5.5。只在本机运行：不连 HPC、云或 VPN，不上传，不读许可文件内容（只核对其存在与权限）。
- **结论分级：** VERIFIED（实际数组、回执或运行记录）、EXACT（逻辑或逐项核验）、INFERENCE（机制解释）、PROPOSED（未执行）。

## 0. 摘要

1. **修正（第 2 节，`ae849e1e`）：** `install_bunker_net_zero` 改为"账户全部排放端口所在链路的 `Link-p` 逐时段 = 0"，约束名不变；`validate_bunker_account` 对等价性前提逐项断言，四个网络全年实测全部满足（82 个端口、系数 0.2571、无移除端口、`p_min_pu ≥ 0`、初值 0、非循环、权重 3 h）。
2. **下游（第 2.2 节）：** Owen 分摊的任何参与者都不依赖原标量对偶（只依赖右端项 0），**不触发停止条件**；两个价格表中燃料舱 CO₂ 账户母线的价格（原为燃料舱 CO₂ 影子价格，新写法下恒为 0）按规则置 NaN 并加说明；Owen 审计、C1、违反量表三处做形状适配，保持原归属。
3. **静态零松弛检查（第 4 节）：** 新脚本 `zero_slack_check.py`（不调用求解器）接入打包，F1–F4 全部通过；11 国净零行都有移除端口，封存上限为 0 的 LA、MM、SG、TL 没有封存账户（与审阅端的核对一致）。
4. **测试（第 3 节）：** 新测试 22 项；全量在最终提交上 856 通过 / 4 失败，4 项与 V14 基线逐项相同；中途 1 项新失败由新文件触发，已修；bash 4.2 替身测试 43 项通过。
5. **本机验证（第 5 节，Gurobi 4 / 6）：** 两个失败窗口在新代码上预处理通过（诊断时 INF_OR_UNBD）；56×3h 回归按 HPC 冒烟作业体本机演练 `SMOKE_RESULT:PASS`，目标相对差 2.45e-9 / 5.83e-10，12 个参与者 Owen 受益符号不变、最大差 17,757 EUR，各国台账最大差 14,288 EUR，B6 差 609 EUR。须知：迭代多 20–23 %，计算量多 19–41 %（不改登记值）。
6. **v3.1 包（第 6 节）：** `work/p1_v3_20261102/hpc_package_v3_1/`，COMMIT `d3b9a3bc`，`SHA256SUMS` 的 SHA256 `b82163615e13797139cb9353851791a9cff5ad3109335bda30c81a2ba44be1ee`，49 个文件 374.5 MB；网络与 v3 相同（8 / 8 与 `HPC_PLAN.txt` 一致）；一致性 60 / 60；干跑 bash 5 与 4.2 都通过；正式目录 `runs/batch5`、冒烟 `runs/smoke56_v31`、上传到新目录 `/hpctmp/$USER/hpr31/`；计划第 15 节与 v3.1 指南在任何 v3.1 HPC 求解之前提交；可选脚本 `fullsize_presolve.sh` 已备，未运行。
7. **终点：** 可以上 HPC。剩下的只有用户的步骤：按 `HPC_OPERATOR_GUIDE_V3.md`（v3.1）开头的清单连 VPN、单路上传到 `hpr31`、`sha256sum -c`、登录预检、冒烟（必须 PASS）、两次不提交演练，再提交 F1–F4 与批级作业。不连 HPC、不连云、不连 VPN、未上传。

## 1. 改动清单（文件、行、理由）

冻结点：部署包提交 `7d22dda112a3c18ed57e8c061d95e51915980417`；worktree `/home/jin/wt_v3_fix`，分支 `codex/v3-fix-20261105`。行号为改动后的位置。

### 1.1 修正与断言（提交 `ae849e1e`，指令第 1.2 条 ①）

| 文件 | 行 | 改动 | 理由 |
|---|---|---|---|
| `scripts_project/s4c_layers.py` | 689–706 `install_bunker_net_zero` | 原 `Store-e[末时段, co2 bunkers ASEAN] <= 0`（1 行）改为 `m.add_constraints(m["Link-p"].sel(Link=meters) == 0.0, name=BUNKER_ROW)`：全部排放端口所在链路 × 全部时段，约束名 `research_bunker_co2_limit` 不变；没有排放端口时报错 | 指令第 2.1 条；诊断第 9 节方案 1 |
| 同上 | 684–686 `bunker_metering_links` | 从 `validate_bunker_account` 的端口表取链路名（去重、保持端口顺序） | 挂接与静态检查共用 |
| 同上 | 476–525 `_efficiency_col`、`bunker_account_premises` | 等价性前提的实测与失败清单：(i) 端口全为排放端口、系数 > 0（含时变效率），无移除端口；(ii) 计量链路 `p_min_pu ≥ 0`（含时变）；(iii) 账户 `e_initial = 0`、非循环、无存储损耗；(iv) 全部时段 stores 与 objective 权重 > 0 | 指令第 2.2 条（(iii) 的"无存储损耗"是我加的：损耗为 1 时末时段水平只看最后一个时段，等价性不再成立；账户合同本来就是 0） |
| 同上 | 528–553 `validate_bunker_account` | 系数 = 0 不再放行（原只拒绝 < 0）；调用上一函数，任一前提不满足即报错。返回值的键不变（`present`、`store`、`ports`），所以构建时写入网络元数据的内容不变 | 指令第 2.2 条；保持重建网络逐字节一致 |
| 同上 | 46–50 | 模块说明补一句 V3.1 写法 | 文档 |
| 同上 | 708–723 `BUNKER_PRICE_NOTE`、`blank_bunker_account_price` | 价格表中燃料舱账户行置 NaN 并加说明列 `note` | 指令第 2.3 条（见第 2.2 节） |

### 1.2 下游形状适配（提交 `ae849e1e`，指令第 1.2 条 ②）

| 文件 | 行 | 改动 |
|---|---|---|
| `scripts_project/m12_rhs_audit.py` | 153–154 `Owners.array` | 该约束名下每一行的所有者都是 `BUNKER`（原标量行由第 139 行 `by_name` 归 BUNKER；多行带 `Link` 维后会改按计量链路的国家归属） |
| `scripts_project/s4o_c1_precision.py` | 165 `country_lookup` | 该约束名的行仍按原标量行的名称规则归属（无国家后缀 → `-`，未归属） |
| `scripts_project/l23_violation_analysis.py` | 90–91 `country_of` | 同上（违反量表的分国统计） |
| `scripts_project/s4b_acceptance.py` | 90 | 只改注释：第 93–95 行本来就对该名下的全部标签逐个赋行参照量，多行直接适用 |
| `scripts_project/s4d_ledger.py` | 314–315 `nodal_prices` | `NODAL_PRICES.csv` 的 `co2 bunkers ASEAN` 行：数值列 NaN，`note` 列说明 |
| `scripts_project/v5/v5_gates.py` | 408–412 `nodal_prices` | `nodal_prices_summary.csv` 同上 |

### 1.3 第 4 节静态检查与测试（提交 `ae849e1e`）

| 文件 | 内容 |
|---|---|
| `scripts_project/zero_slack_check.py`（新） | 见第 4 节 |
| `tests/research/test_v31_bunker_fix.py`（新） | 见第 3 节 |

### 1.4 打包、运行器与指南（提交 `64aea2e3`、`13ebce95` 与文档提交，指令第 1.2 条 ③④）

| 文件 | 行 | 改动 | 理由 |
|---|---|---|---|
| `scripts_project/b4_batch4.py` | 101–108、584 | `RUN_DIRS`（缺省 `runs/batch4`、`runs/smoke56`、`runs/build_only_f1`；定义文件 `run_dirs` 可覆盖，校验 `runs/名称`、首字符不为点、三者互不相同）；`hpc-plan` 增加 `RUNDIRS|…` 行 | 指令第 6.1 条：正式 `runs/batch5`、冒烟 `runs/smoke56_v31` |
| `hpc_package_src/hpr_job.sh` | 37–48、62、79 | 运行目录读 `pbs/HPC_PLAN.txt` 的 `RUNDIRS` 行（没有这一行时为 v2 / v3 的缺省），格式不合即拒绝；两处提示文字 | 同上；单一来源（定义文件 → `b4_batch4.py` → `HPC_PLAN.txt`） |
| `hpc_package_src/hpr_submit.sh` | 8–10、15–21、38、48–53、62、66 | 冒烟状态文件、正式目录（存在检查、STOP、启动锁、残留、`SUBMITTED.txt`）都用 `RUNDIRS` 的值 | 同上；`hpr3/runs/batch4` 的停批记录不会阻挡 v3.1 |
| `hpc_package_src/hpr_status.sh` | 4–9 | 缺省目录取 `RUNDIRS` 的正式目录 | 同上 |
| `hpc_package_src/hpr_consistency.py` | 146–152 | 定义文件带 `run_dirs` 时，加 3 行比对：正式 / 冒烟目录在计划文本、`b4_batch4.py`、`pbs/HPC_PLAN.txt` 三处相同；作业体读 `RUNDIRS` | 一致性检查覆盖新登记项（v2 / v3 的行数不变） |
| `batch_def/BATCH_DEF_2920x3h_v31hpc.json`（新） | 全文 | = v3 定义（脚本逐键断言）+ `run_dirs`，名称与说明改为 v3.1 | 指令第 6.1 条 |
| `hpc_v31/make_hpc_package_v31.sh`（新） | 全文 | v3 打包脚本的 v3.1 版：网络取自 v3 包（先按 v3 包的 `SHA256SUMS` 与定义文件核对）；**零松弛检查为出包闸门**（不通过就不出包，包内 `ZERO_SLACK_CHECK.json`）；要求计划已有第 15 节；`V31_DRILL=1` 时只在 work/ 以外打演练包并标注不得上传 | 指令第 4、6 节 |
| `RUN_PLAN_HPC_V3.md` | 开头说明、第 4、8、9、11 节路径、第 15 节（新） | v3.1 路径与修正记录 | 指令第 6.2 条 |
| `HPC_OPERATOR_GUIDE_V3.md` | 全文 | 更新为 v3.1（第 6 节） | 指令第 6.3 条 |
| `tests/research/test_v31_hpc_package.py`（新） | 全文 | 定义文件、`RUNDIRS` 与拒绝、一致性行、提交 / 状态 / 作业体使用 v3.1 目录（替身，无求解） | 指令第 3 节 |
| `tests/research/test_dfx_demand.py` | 322 | DFX F0.3 规则的豁免加上 `zero_slack_check.py`（V3.1 步骤的新文件，同 V3 的 `batch_def.py`） | 全量测试的新失败，原因在新增的打包闸门脚本（第 3 节） |

## 2. 断言结果与下游用法（指令第 2 节第 2、3 步）

### 2.1 四个网络的前提实测（VERIFIED，全年 2920 时段；`evidence/ZERO_SLACK_CHECK_F1_F4.json` 的 `bunker.premises_full_network`）

| 前提 | F1 | F2 | F3 | F4 |
|---|---|---|---|---|
| 端口数 / 计量链路数 | 82 / 82 | 82 / 82 | 82 / 82 | 82 / 82 |
| 端口系数（t/MWh） | 0.2571（全部，无时变效率） | 同左 | 同左 | 同左 |
| 移除端口 | 0 | 0 | 0 | 0 |
| 计量链路 `p_min_pu` 最小值（静态 / 时变） | 0.0 / 无时变 | 同左 | 同左 | 同左 |
| 账户 `e_initial`、循环、存储损耗 | 0、否、0 | 同左 | 同左 | 同左 |
| stores / objective 权重最小值 | 3 h / 3 h | 同左 | 同左 | 同左 |
| 结论 | 全部通过 | 全部通过 | 全部通过 | 全部通过 |

截短运行（56 时段，权重 8760/56 h）在每次挂接时同样经过这些断言（第 5 节两次求解都已通过）。

**等价性（EXACT，逻辑）：** 账户母线上只有这 82 个排放端口和账户 Store。端口系数 > 0、流量 ≥ 0，所以每个时段流入账户的量 ≥ 0；账户初值 0、非循环、无损耗，末时段水平 = Σ 权重 × 流入（权重 > 0）。于是"末时段水平 ≤ 0" ⇔ 每个时段的流入都为 0 ⇔ 每条计量链路的流量都为 0。两种写法下其余变量的可行集相同，最优目标相同。

### 2.2 下游用法表（读的是什么、形状变化后的处理、对数值有无影响）

检索方法：`git grep` 约束名、`BUNKER_ROW`、`BUNKER_CO2_BUS`、挂接名（`scripts/grep_usage.sh`），再查正式路径上按通用方式读取全部约束或对偶的代码（`scripts/grep_generic.sh`、`grep_duals.sh`、`grep_co2price.sh`、`grep_price2.sh`），以及 PyPSA 0.30.3 的 `assign_duals`。正式路径 = `run_batch4.sh` 调用的 `s2_solve.py`（构建 / 映射）、`b4_split_solve.py`、`l23_violation_analysis.py`、`s4o_c1_precision.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s4d_ledger_redo.py`、`v5/gates_v6.py`、`b4_batch4.py`。

| 位置 | 读的是什么 | 形状变化后的处理 | 对数值的影响 |
|---|---|---|---|
| `m12_rhs_audit.py` y'b（`audit` 中按约束循环的部分） | 每行右端项 × 对偶，只累加右端项非零的行 | 不变：新旧写法右端项都是 0 | 无：该行对任何参与者的 y'b 都是 0 |
| `m12_rhs_audit.py` 行所有者（`Owners.array` / `by_name`） | 约束名 → BUNKER | 适配：多行仍全部归 BUNKER（第 153 行） | 只影响分类计数（`RHS_FAMILIES.csv` 的行数归属）；右端项为 0，Owen 数值无影响 |
| `m12_rhs_audit.py` 分解（`decompose`） | π × A × x、π × b 按列 / 行所有者 | 通用，不改 | 新旧都是"对偶 × 约 0 的流量或水平"，数值可忽略（回归中 Owen 受益差见第 5.2 节） |
| `m12_allocation.py`（市场结算式、`bunker_standalone`） | 节点价格 × 流量；独立成本只看网络数据 | 不读该约束 | 无（燃料舱买方价格在航空终端母线，由非化石孪生链路决定） |
| Owen 对偶形式（`m12_rhs_audit.owen_summary`） | y'b + 列界项 + 目标常数 | 不读该约束的对偶本身 | **任何参与者的数值都不依赖原标量对偶**（该行右端项为 0；计量链路可扩建，列界无穷，无列界项）→ 不触发停止条件 |
| `s4b_acceptance.special_references` | 该名下全部标签 → 行参照量 = 账户毛流量 | 已是逐标签循环，多行直接适用 | 无（参照量在最优解处约为 0，预算即绝对下限） |
| `s4o_c1_precision.country_lookup`（C1 (b)(c) 的分国归属） | 通用：行按组件母线国家，标量行按名称后缀 | 适配：该名的行仍按名称规则（`-`） | 保持原归属；一阶成本为"违反量 × 对偶"，量级可忽略 |
| `l23_violation_analysis.country_of` / `decode` | 通用 | 适配同上；`decode` 已支持多维 | 只影响 `VIOLATIONS.json` 的分国统计 |
| `s3b_scaling`（`--scaling on`） | 选中 Store（生物质池、`co2 sequestered*`、捕集缓冲）的列与行 | 燃料舱账户不在选中之列，`Link-p` 不缩放 | 无 |
| `s4m_duals.write_duals`（`DUALS_BY_CONSTRAINT.nc`） | 每个约束的对偶，维度加约束名前缀 | 通用，多维直接适用 | 文件里该变量由标量变为（时段 × 链路） |
| PyPSA 0.30.3 `assign_duals(assign_all_duals=True)` | 按约束名中的 `-` 拆组件 / 属性 | 约束名不含 `-` → 新旧都列为未分配 | 求解后网络文件不受影响 |
| `s2_solve.py` 挂接清单、A6、B1_BUNKERS（`bunker_account_report`） | 约束名清单；账户末时段水平 | 名称不变；末时段水平在新写法下恒为约 0 | B1_BUNKERS 照常判定 |
| `s4d_ledger.nodal_prices` → `NODAL_PRICES.csv`；`v5_gates.nodal_prices` → `nodal_prices_summary.csv` | **`co2 bunkers ASEAN` 母线的对偶价格**：原写法下它就是原标量对偶沿 Store 链传过来的"燃料舱 CO₂ 影子价格" | **字段保留，值改为 NaN，加 `note` 列说明**（`BUNKER_PRICE_NOTE`）；没有构造替代量 | 新写法下该母线价格在任何对偶可行解中都为 0（账户容量成本 0、无末时段行 → 能量平衡对偶链为 0，INFERENCE），不是价格，所以置 NaN。其余母线不变；求解后网络文件中的原始对偶不动 |
| 台账结算列 `bunker_co2 bunkers`（`s4d_ledger.country_cost_ledger`） | 计量流量 × 该母线价格 | 不改（是金额，不是价格字段） | 原值只有几欧元（流量约 0）；新写法下为 0，见第 5.2 节 |
| `zero_slack_check.py`（新） | 该约束的行形式 | 新写法判为"显式逐变量为零" | — |

**停止条件核对：** 没有任何 Owen 参与者的数值依赖原标量对偶值（只依赖右端项 0）；只有两个价格表字段依赖它，已按规则置 NaN 并加说明。

## 3. 测试（指令第 3 节；不调用 Gurobi）

**新测试（VERIFIED）：**

| 文件 | 项数 | 内容 |
|---|---:|---|
| `test_v31_bunker_fix.py` | 17 | (a) 新写法：约束名不变，行 = 时段 × 计量链路（4 × 2），全是 `=`、右端项 0、单项系数 1，恰为 `Link-p(链路, t)`，不再有账户 `Store-e` 行；重复安装拒绝；前提实测值。(b) 8 种拒绝：移除端口（效率 < 0）、账户作为 bus0 被取出、静态 `p_min_pu < 0`、时变 `p_min_pu < 0`、`e_initial ≠ 0`、系数 = 0、存储损耗、零权重；挂接在前提失败时拒绝。(c) 零松弛检查：玩具网络上的旧写法判为强制行、燃料舱覆盖核对不通过；新写法判为显式逐变量为零且覆盖 2 × 3 行；有移除端口或上限为正的末时段行放行；上限 0 的年度加权和行判为强制行、上限为正的放行。下游：Owen 行所有者、C1 与违反量归属、两个价格表的 NaN 与说明（不带账户的网络不加列）。玩具网络用 datetime 时段（与研究网络相同；检查脚本第一版的时段比较缺陷正是由此暴露） |
| `test_v31_hpc_package.py` | 5 | v3.1 定义 = v3 + 运行目录；`hpc-plan` 的 `RUNDIRS` 与 4 种非法目录拒绝；生成作业脚本 → 一致性检查 `ALL_CONSISTENT` 且 3 行新比对一致；提交演练读 `runs/smoke56_v31`（v3 的冒烟通过不算）、正式提交写 `runs/batch5`、`runs/batch4` 中的停批记录不阻挡也不被改动；状态脚本缺省目录；冒烟作业体（替身）写到 `runs/smoke56_v31` 并判 PASS；正式作业体的残留拒绝指向 `runs/batch5`、非法 `RUNDIRS` 拒绝 |

调整的旧测试：没有断言"该约束是单行"的测试（检索 `tests/research`）；`test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers`（HiGHS 玩具 LP，无 Gurobi）在新写法下照样通过。唯一调整的是 `test_dfx_demand.py` 的豁免（见下）。

**全量 `tests/research`（提交 `64aea2e3`，输入布置同 V14：`results_project` 链接到主检出、6 个被忽略的输入复制；1,950 s；`evidence/tests/FULL_SUITE_64aea2e3.txt`）：855 通过、5 失败。**
- 4 项与 V14 全量（`1e7b503c`，831 通过 / 4 失败）逐项相同：`test_s1_built_networks::test_static_validation_passes_on_reload`（已知基线）与 `test_s3_gates.py` 的 `test_static_b_gates`、`test_b12_with_override`、`test_b12_s3b_rebuilt`（V14 已诊断：与前者同一根因，旧 S3-5 网络没有 `cross_border.stock_mode` 键）。
- **1 项新失败**：`test_dfx_demand.py::test_f0_changed_scripts_in_the_executed_lists`，断言信息只列 `scripts_project/zero_slack_check.py`——DFX 的 F0.3 规则要求 72083fde 之后 `scripts_project` 的改动在 DFX 执行清单内或属于豁免的 V3 新文件。原因在本次新增的打包闸门脚本，不指向模型，按无人值守规则修复：豁免它（同 V3 对 `batch_def.py` 的处理），该文件 14 项通过（提交 `13ebce95`）。
- 通过数核对：831（V14 @1e7b503c）+ 3（7d22dda1 新增的运行器测试）+ 22（本次新测试）− 1（新失败）= 855。
- 其中包括套件原有的玩具 LP（scipy `linprog` / HiGHS，无模型网络、无 Gurobi），照实列出。
- 最终提交上的全量重跑见第 6.4 节。

**bash 4.2（改动了 `hpr_job.sh`、`hpr_submit.sh`、`hpr_status.sh` 与新打包脚本）：**
- 语法：4 个脚本在本机编译的 bash 4.2.0 与 bash 5 下 `bash -n` 都通过；包上的完整静态检查见第 6.4 节。
- 替身测试（`PATH` 垫片让所有嵌套的 `bash` 都解析到 bash 4.2.0，`scripts/ut_bash42.sh`）：`test_v3_hpc_runner.py`、`test_hpr_two_jobs.py`、`test_b4p_batch4.py`、`test_v31_hpc_package.py` 共 **43 项全部通过**（458 s，提交 `13ebce95`，`evidence/tests/STANDIN_TESTS_bash42_13ebce95.txt`）。新代码只用了 bash 3 起就有的 `[[ =~ ]]` 与 here-string，没有数组展开。

## 4. 静态零松弛检查（指令第 4 节）

**脚本：** `scripts_project/zero_slack_check.py`，不调用求解器。两部分：
1. **挂接行的形式**：把网络截短到前 3 个时段，走与正式求解相同的建模路径（`l23_violation_analysis.build_model` = `create_model` + 全部必需挂接 + 去掉目标常数），逐行识别全部研究挂接（`research_*` / `Research*`）的形式：末时段 Store 水平 ≤ 上限、全年加权和 ≤ 上限、逐变量为零、逐变量上下界、其他。挂接形式与时段数无关，上限不随截短缩放（诊断报告第 6 节已核对两种口径右端项相同）。
2. **端口**：读全年网络（静态与时变 `p_min_pu`、效率取全部时段），把受约束 Store 所在母线上的每个端口（或受约束发电机自身出力）分为单向流入、移除、双向、零。

**判定：** 两种形式的行，若上限 ≤ 1e-9（末时段形式扣除 `e_initial`）且端口全部单向流入（无移除、无双向），判为零松弛强制行；除非该约束已按显式逐变量为零实现，否则拒绝（退出码 3）。燃料舱另核对：新写法是否恰好覆盖全部计量链路 × 全部时段，前提是否在全年网络上成立。输出 `ZERO_SLACK_CHECK.json`（每条约束：形式、上限、端口数、流入 / 移除 / 双向端口数、移除端口示例、结论）。

**接入打包：** `hpc_v31/make_hpc_package_v31.sh` 在复制网络、`base-check` 之后运行，结果行不是 `ZERO_SLACK_CHECK_RESULT:PASS` 就不出包；`ZERO_SLACK_CHECK.json` 随包，清单里登记结论。

**四个网络的结果（VERIFIED，`evidence/ZERO_SLACK_CHECK_F1_F4.json`；每个网络约 12–14 s，峰值 0.85 GB）：全部通过。**

| 约束族 | 形式 | 行（F1 / F2） | 结论 |
|---|---|---|---|
| `research_country_co2_limit-<国>`（11） | 末时段 Store 水平 ≤ 0 | 11 / 11 | **都有移除端口**（例：BN 28 个端口中 8 个移除，ID 1,453 中 312 个，最少的 TL 27 中 7 个；DAC、生物质末端捕集等）→ 不是强制行 |
| `research_co2_storage_cap-<国>`（7：BN、ID、KH、MY、PH、TH、VN） | 末时段封存水平 ≤ 上限 | 7 / 7 | 只有流入端口，但上限为正（1.34 Mt–2,575 Mt）→ 不是强制行 |
| 封存上限为 0 的 LA、MM、SG、TL | — | 无该行 | **没有 `co2 sequestered` 账户**，`install_co2_storage_cap` 不加行（JSON 的 `configured_caps_without_row`） |
| `ResearchImportAnnual-<发电机>`（19） | 全年加权和 ≤ 上限 | 19 / 19 | 上限为正（最小 2.61e4，最大 6.08e8，与 `Σ w·p` 同单位）→ 不是强制行 |
| `research_bunker_co2_limit` | 逐变量为零 | 1 族，246 行（82 × 3） | **显式逐变量为零**；覆盖 82 条计量链路 × 全部时段，无缺无多；全年前提成立 |
| `ResearchStoreDirection-*`（118） | 逐变量上界 | — | 不属于两种形式 |
| `ResearchBatteryNominal-*`、`research_lossy_bidirectional_sync-*`、`research_new_hydro_inflow-*` | 等式或带容量的不等式 | — | 不属于两种形式 |

F3、F4 与 F1、F2 逐项相同。审阅端的两项核对（11 国大气账户都有移除端口；封存上限为 0 的 LA、MM、SG、TL 没有封存账户）由脚本复核，结论相同。

**照实记录：** 第一次运行检查脚本时，"末时段"识别与燃料舱覆盖核对把 numpy `datetime64`（linopy 坐标）和 pandas `Timestamp`（网络时段）直接转字符串比较，格式不同，导致国家净零行落入"逐变量上界"、燃料舱覆盖判为不通过（`passed=False`，没有漏报，只是误报）。改为统一转成时间戳后比较，测试改用 datetime 时段覆盖这一点，重跑后结果如上。

（第 5.1 节两个窗口的 LP 也对照了诊断：行数恰好多 82 × 窗口时段数 − 1，见第 5.1 节。）

## 5. 本机验证（Gurobi 共 ≤ 6 次，串行，同一时刻 1 个进程）

每次调用前都检查了 WSL 到令牌服务器的 TCP 连通、没有其他求解 / 构建 / pytest 进程；账本 `evidence/GUROBI_CALLS.csv`，状态 `evidence/FIX_STATUS.txt`。

### 5.1 失败窗口复核（第 1、2 次调用，只到预处理；VERIFIED）

**方法：** 诊断入口原样复制到 `scripts/win/`（只改 worktree 路径、结果目录、授权文字与本会话的调用账本），在修正后的提交 `ae849e1e`（tracked 改动 0）上重建窗口，权重处理与运行器 `TRUNCATE` 相同；进程 2 是运行器的 `b4_split_solve.py --probe-ordering-only`（`BarIterLimit=0`，其余参数来自 `formal_barrier_1e6_t16`）；内存保护同诊断第 15–35 次调用：`--protect MemLimit=7 --protect SoftMemLimit=6`。判定按诊断的写法读 Gurobi 日志。

| 窗口 | 构建 s / 峰值 GiB | LP 行（新 / 诊断，差） | 列 | 预处理 s | 日志 | 结论 |
|---|---|---|---|---:|---|---|
| F1_M01 `[0,248)` | 97 / 8.51 | 7,077,475 / 7,057,140，**+20,335 = 82 × 248 − 1** | 3,192,900（相同） | 19.28 | `Presolved: 2301392 rows, 2195530 columns, 9198477 nonzeros`；ordering 55.4 s；之后 `Optimization exhausted available memory` | **通过**（诊断时 INF_OR_UNBD） |
| F2_M02 `[248,472)` | 73 / 6.76 | 6,205,085 / 6,186,718，**+18,367 = 82 × 224 − 1** | 2,800,578（相同） | 12.11 | `Presolved: 1924731 rows, 1887998 columns, 7723427 nonzeros`；ordering 17.0 s；之后 `Memory limit reached` | **通过**（诊断时 INF_OR_UNBD） |

两次都没有任何 infeasible / unbounded 判定。进程以退出码 1 结束，是预处理与 ordering 完成后 barrier 分配内存碰到 7 GB 硬上限——与诊断中预处理通过的窗口（第 16、17、22、24、25 次调用）相同，是运行保护，不影响预处理判定。非零元同样恰好多 20,335 / 18,367（每行 1 个），说明新行就是逐计量流量的单变量行。通过的窗口按诊断做法删除了 `problem.lp`（标签数组保留）。

### 5.2 56×3h 回归（第 3、4 次调用，完整求解；VERIFIED）

**方法：** "按运行器"——用 v3.1 打包脚本在提交 `13ebce95` 上打出**演练包**（`V31_DRILL=1`，`/home/jin/v3fix/drill_pkg_13ebce95`，标注不得上传；与正式包同一构建流程，零松弛闸门 PASS、一致性 `ALL_CONSISTENT`），在其中原样运行 HPC 冒烟作业体（`pbs/hpr3_smoke56.pbs` 的 `JOB_*` 值：17 核 / 32 GB；作业体依次 F1、F2、批级），只加本机演练开关 `HPR_LOCAL_DRILL=1`（不访问令牌服务器 HTTP、不做资源节）。路径 = 运行器 `run_batch4.sh --only`、split 三进程、`TRUNCATE=56`、`formal_barrier_1e6_t16`（Threads 16）、TimeLimit 3,000 s / 墙钟 3,600 s、运行目录 `runs/smoke56_v31`。作业内预检（guards、sha、networks、env、profile、code、tools）全部通过。F1 11:23:38–11:37:11 UTC，F2 11:37:11–11:49:23 UTC（两个 Gurobi 会话间由运行器保证 ≥ 330 s），批级 10 s；没有重试、没有改参数。正式包的代码提交 `d3b9a3bc` 与 `13ebce95` 相比只改了 `research/` 下的计划与指南（`git diff --name-only 13ebce95 d3b9a3bc -- . ':!research/'` 为空），所以回归覆盖的就是部署的代码。

**作业体自己的判定（`SMOKE_STATUS.txt`）：** F1、F2 都 optimal、`ACCEPTED_LAYER2`、与定义文件期望值的相对差 ≤ 1e-6，`POSTPROC_ERRORS:0`，`BATCH_DONE:True`，`HALTED:False`，**`SMOKE_RESULT:PASS`**。

**与修正前本机冒烟（`RUN_PLAN_V3.md` 第 25 节；`work/p1_v3_20261102/evidence/hpc/smoke/`）逐项对比（`scripts/compare_56.py` → `evidence/REGRESSION_56.json / .md`）：**

| 项 | F1（一体化） | F2（`no_new_xb`） |
|---|---|---|
| 终止 / V6 标签 / C1 abc | optimal / `ACCEPTED_LAYER2` / 111（修正前相同） | optimal / `ACCEPTED_LAYER2` / 111（修正前相同） |
| 目标值 EUR（新 / 修正前） | 329,705,565,613.54 / 329,705,566,422.24 | 342,268,691,264.84 / 342,268,691,464.46 |
| **相对差** | **2.45e-9**（≤ 1e-6） | **5.83e-10** |
| barrier 迭代 / 用时 s / work units（新 / 修正前） | 96 / 182.95 / 268.8 — 80 / 190.53 / 225.5 | 81 / 132.52 / 192.8 — 66 / 111.24 / 137.1 |
| Gurobi 峰值内存 GB | 5.96 | 4.44 |
| LP 行 / 列 / 非零（新 − 修正前） | +4,591 / 0 / +4,591（= 82 × 56 − 1） | 同左 |
| 燃料舱账户（`BUNKER_ACCOUNT.json`） | 末值 0.0 t，毛流量 0.0 t，B1_BUNKERS 通过 | 同左 |
| 不通过的闸门 | A1_A2、A1_A2_S4B、A3、B1、B3、B8（与修正前相同，都在预告内） | 同左去掉 B3（与修正前相同） |
| 价格表的燃料舱行 | `NODAL_PRICES.csv`：NaN + 说明 | 同左 |
| 各国台账 total 最大差 | 14,288 EUR（ID；容差 9.0e7） | 9,697 EUR（SG；容差 1.3e7） |

**12 个参与者的 Owen 受益（对偶形式，α 0.5，EUR）：**

| 参与者 | 修正前 | v3.1 | 差 | 容差 max(0.1 %, 1 M) | 符号 |
|---|---:|---:|---:|---:|---|
| BN | 183,701,363 | 183,701,318 | −44 | 1,000,000 | 相同 |
| ID | −712,338,328 | −712,324,394 | +13,934 | 1,000,000 | 相同 |
| KH | 366,217,943 | 366,210,039 | −7,904 | 1,000,000 | 相同 |
| LA | −108,247,676 | −108,244,795 | +2,881 | 1,000,000 | 相同 |
| MM | 298,044,120 | 298,047,239 | +3,119 | 1,000,000 | 相同 |
| MY | 869,653,853 | 869,654,570 | +716 | 1,000,000 | 相同 |
| PH | 130,118,580 | 130,117,636 | −943 | 1,000,000 | 相同 |
| SG | 2,770,373,847 | 2,770,372,760 | −1,088 | 2,770,374 | 相同 |
| TH | 4,073,042,313 | 4,073,051,875 | +9,562 | 4,073,042 | 相同 |
| TL | 26,311,973 | 26,311,953 | −19 | 1,000,000 | 相同 |
| VN | 1,368,915,059 | 1,368,907,066 | −7,994 | 1,368,915 | 相同 |
| BUNKER | 3,297,338,456 | 3,297,320,699 | −17,757 | 3,297,338 | 相同 |

B6 = 12,563,125,651 EUR（修正前 12,563,125,042，差 +609 EUR）。各国台账的逐主体差表（两个运行、12 个主体加 ASEAN_BUNKER）见 `evidence/REGRESSION_56.md`；燃料舱 CO₂ 结算列 `bunker_co2 bunkers` 由修正前的几欧元（F1：−0.44 至 +3.47 EUR）变为 0.0（新写法下账户母线价格为 0，计量流量为 0）。

**结论：** 没有任何参与者的 Owen 受益改变符号或超过 max(0.1 %, 1 M EUR)，目标值相对差 ≤ 1e-6，验收照旧：**通过，不触发停止条件**。各项差都在内点解的容差量级（BarConvTol 1e-6，目标约 3.3e11 EUR 时 1e-6 相对即 3.3e5 EUR）。

**须知（INFERENCE，不改登记值）：** 迭代数多 20–23 %、work units 多 19–41 %（F1 的 barrier 用时反而少 4 %，F2 多 19 %）。两种写法的预处理结果不同（新写法里 82 × 56 个计量变量直接被固定消去，原写法要经 Store 链代换聚合），内点路径随之不同；这与线程数造成的路径差异同属一类，一次 56 时段运行不足以外推到全年。按指令，TimeLimit、walltime、参考迭代数与第 26 节预测都不改；全年若明显更慢，由早期测速止损（Atlas 上每次迭代超过约 1,850 s）处理。

**冒烟期望值：** 定义文件里的期望值仍是修正前的本机冒烟值（指令：验收与预测不变）；v3.1 本机回归与之的相对差 2.45e-9 / 5.83e-10，远小于 HPC 冒烟判定所用的 1e-6。

## 6. v3.1 部署包（指令第 6 节）

### 6.1 包（VERIFIED）

`work/p1_v3_20261102/hpc_package_v3_1/`，由 `hpc_v31/make_hpc_package_v31.sh` 在干净提交 **`d3b9a3bca18755b50397f31d4b61abe39fb50c3f`** 上打出（包内 `COMMIT`；tracked 改动 0）。v3 包 `hpc_package_v3/` 原样保留。

| 项 | 值 |
|---|---|
| `SHA256SUMS` 的 SHA256 | **`b82163615e13797139cb9353851791a9cff5ad3109335bda30c81a2ba44be1ee`** |
| 文件 | `SHA256SUMS` 列 47 个；含它与 `HPC_PACKAGE_MANIFEST.json` 共 49 个；374,497,664 B（上传量 374,483,106 B，不含清单） |
| 代码 | `code_d3b9a3bc.tar.gz`（`git archive`，不含顶层 `research/`）；与回归所用 `13ebce95` 的代码逐文件相同 |
| 定义 | `BATCH_DEF.json` = `batch_def/BATCH_DEF_2920x3h_v31hpc.json`：`limits_status` REGISTERED，`run_dirs` = `runs/batch5` / `runs/smoke56_v31` / `runs/build_only_f1` |
| 网络与回执 | 四个 2920×3h 网络、两张构建回执、两张变体回执、成本表——9 个文件与 v3 包逐字节相同；四个网络的 SHA256 与字节数与 v3 包和 v3.1 包的 `pbs/HPC_PLAN.txt` 的 NETWORK 行 8 / 8 一致（`evidence/NETWORK_SHA256_CHECK.txt`）；无 365×24h 文件 |
| 新增 | `ZERO_SLACK_CHECK.json`（四个网络 PASS，打包闸门） |
| 运行与作业 | `run_batch4.sh`、`preflight.sh`、`pack_results.sh`、`hpc/`（作业体、PBS 生成、安装、登录预检、提交、状态、一致性检查）、`pbs/`（8 个作业脚本：walltime F1 / F2 / F3 / F4 = 260 / 262 / 260 / 262 h，批级 48 h，冒烟 4 h；`HPC_PLAN.txt` 含 `RUNDIRS|runs/batch5|runs/smoke56_v31|runs/build_only_f1`） |
| 环境 | `env/`（同 v3 包的锁文件；HPC 上已有环境，预检 `env` 节一致即复用） |
| 文档与参照 | `RUN_PLAN_HPC_V3.md`（含第 15 节）、`HPC_OPERATOR_GUIDE_V3.md`（v3.1）、`RUN_PLAN_V3.md`、`V3_RULES.md`、`HPC_FACTS_20261026.md`、`REFERENCE_VALUES.json` |
| 一致性 | `HPC_CONSISTENCY.json`：**60 行全部一致**（v3 的 57 行 + 运行目录 3 行） |
| 不进包 | 许可、cutout、LP 与解的数组、结果、`solve.log` / `solve.err`、账号与主机信息、365×24h 网络、演练包标记 |

**上传时间估计（单路）：** 374.5 MB；1 MB/s 约 6 分钟，0.1 MB/s 约 1 小时；按 AutoDL 上传曾实测的 0.058 MB/s 约 1.8 小时。NUS VPN 到 Atlas 的实际速度未测。

### 6.2 `RUN_PLAN_HPC_V3.md`（提交 `d3b9a3bc`，在任何 v3.1 HPC 求解之前）

开头加 v3.1 说明；第 4、8、9、11 节的路径改为 v3.1（`runs/batch5`、`runs/smoke56_v31`、`/hpctmp/<用户>/hpr31/`、本机结果目录 `hpc_results_v31`）；新增**第 15 节"v3.1 修正（第 195 项，2026-11-05）"**：根因一句话、改动文件与提交号、等价性前提实测、第 4 节检查结果、第 5 节两项验证、须知（迭代与计算量增加，不改登记值），并写明 TimeLimit、walltime、资源、早期测速、构建超时、验收与预测全部不变。

### 6.3 `HPC_OPERATOR_GUIDE_V3.md`（v3.1）

开头"用户上 HPC 操作清单"照 V14 格式重写为 (a)–(i)：(a) 连 VPN 前确认本机无 Gurobi、Claude Code 会话已停；(b) 连 AnyConnect 后只用 Windows 侧 `scp`，一条命令单路上传到**新目录** `/hpctmp/$USER/hpr31/`，之后 `sha256sum -c`；(c) 登录节点 `bash --version`、`qstat -u $USER` 必须没有 v3 残留作业（v3.1 的作业名与 v3 相同）、两次不提交演练（写明期望输出，冒烟路径必须是 `runs/smoke56_v31`）；(d) 单路上传与核对；(e) 登录预检（复用已装环境）与冒烟作业，**冒烟 PASS 前不提交正式批次**；(f) 一条命令提交五个作业，另附逐条提交；(g) 队列与排队原因；(h) 撤销时连同依赖作业；(i) 结果下载到 `hpc_results_v31` 与 60 天清理。步骤 A–H 全部改为 v3.1 路径（A1 另查 `"formal": "runs/batch5"` 与"不是演练包"，A3 另查 `RUNDIRS` 行），v3 的 `hpr3/` 明确写"不动"。命令中没有尖括号占位符（33 个代码块逐行检查，0 处）。

### 6.4 本机干跑、预检、静态检查与全量测试（`licence`、`resources` 两节除外；无求解器、无许可）

`scripts/dry_hpc31.sh`（V14 `dry_hpc2.sh` 的 v3.1 版：包复制到新目录后执行），bash 5.3.9 与本机编译的 bash 4.2.0 各一次，结果相同（`evidence/dry/`）：

| 步骤 | 结果（bash 5 = bash 4.2） |
|---|---|
| 预检 `guards,sha,networks,env,profile,code,tools` | `PREFLIGHT OK`：47 个文件 OK；环境 284 / 284；四个网络 `all_equal`；档案正确；TimeLimit 864,000、REGISTERED |
| `BUILD_ONLY=1 TRUNCATE=56` 四个运行 | 全部 `BUILD_CHECK passed`（约 140 s）；LP F1、F3 1,607,971 × 729,156、非零 3,720,313，F2、F4 1,560,389 × 707,802、非零 3,570,079（比 v3 各多 4,591 行与非零）；燃料舱行在挂接清单中 |
| 作业体 `JOB_MODE=build_only JOB_RID=F3`（本机演练开关） | 退出码 0，`BUILD_CHECK_F3 passed`，超时读到 5,400 s |
| 正式作业体 F1，环境里带测试开关 | **拒绝**（退出码 2），什么都没启动 |
| 正式作业体 F3，F1 未结束 | 退出码 3，`STOP_SAFE:PREDECESSOR_NOT_ENDED:F3:F1` 写在 **`runs/batch5/STOP_SAFE`**，没有启动运行 |
| `hpr_submit.sh --dry-run` | 5 行 `DRY-RUN: qsub` 依赖链正确，3 条预期提示（授权、冒烟——路径 `runs/smoke56_v31/SMOKE_STATUS.txt`、本机无 qsub），`DRY_RUN_OK`，没有写任何文件 |
| `hpr_status.sh` | 缺省目录 `runs/batch5` |

所有输出中都没有 `unbound`、`syntax error`、`command not found`。

**bash 4.2 静态检查（包上，`evidence/dry/BASH42_STATIC_d3b9a3bc.txt`）：** 18 个脚本与作业脚本 `bash -n` 全部通过；4.3 / 4.4 / 5 才有的写法命中 0；未加 `:-` / `+` 保护的数组展开清单与 V14（`7d22dda1`）相同，只有行号随改动平移，本次没有新增数组展开。

**最终提交上的全量测试：** 见第 7.1 节。

**泄露扫描：** 见第 7.2 节。

### 6.5 可选脚本 `hpc_v31/fullsize_presolve.sh`（未运行）

用于在 ≥ 256 GB 内存的机器（AutoDL）上对 F1、F2 做全年构建 + 只到预处理：进程 1 = 运行器同款 `s2_solve.py --split-stage build`（不截短，标签 `SMOKE_TEST_ONLY`，`formal_barrier_1e6_t16`），进程 2 = `b4_split_solve.py --probe-ordering-only --protect MemLimit=0.8 × 内存`；判定按诊断写法读 Gurobi 日志；两次 Gurobi 会话串行、间隔 ≥ 330 s。脚本头写明：估计（构建 40–50 分钟、峰值约 96–110 GiB、LP 约 5.5 GB + 数组约 8 GB；读入约 3 分钟、预处理 4–10 分钟、ordering 15–40 分钟、Gurobi 60–80 GB；每个网络 1.2–1.8 h，合计 2.5–3.5 h；磁盘 ≥ 60 GB）、所需上传文件（v3.1 包，实际用到的文件逐一列出；许可由用户放置）与期望输出（`runs/fullsize_presolve/FULLSIZE_PRESOLVE.txt`：`F1:PRESOLVE_PASSED:Presolved: …`、F2 同、`FULLSIZE_PRESOLVE_RESULT:PASS`）。没有 `--confirmed-by-user` 时拒绝；内存不足 250 GiB、磁盘不足 60 GiB、`./repo` 不是包提交、许可不是 600、已有求解进程、令牌不通时都拒绝。bash 4.2 / 5 语法检查通过；本步没有运行它（实测：无确认参数即拒绝，什么都不做）。

## 7. 资源记账、偏差与提交

### 7.1 资源与测试

| 项 | 用量 / 上限 |
|---|---|
| 本机 Gurobi | **4 / 6**：第 1、2 次预处理探针（88 s、37 s），第 3、4 次冒烟作业体（813 s、732 s，含构建与后处理；barrier 183 s、133 s）；无重试、无改参数；始终只有 1 个 Gurobi 进程，每次前检查令牌连通与进程 |
| 本机计算 | 约 **2.0 h / 5 h**（各步墙钟累计：两次全量测试 66 min、冒烟演练 26 min、bash 4.2 替身测试 8 min、干跑 6 min、窗口复核 5 min、两次打包 4 min、静态检查与快速测试、泄露扫描约 8 min） |
| 磁盘新增 | 约 **6.3 GB / 30 GB**（worktree 0.75 GB；`results_project/v3fix` 窗口构建 1.0 GB，通过的窗口已删 LP 文件；会话目录 `/home/jin/v3fix` 4.2 GB，含演练包、其运行目录与两次干跑；正式包 0.36 GB；work 目录 4 MB） |
| 下载 | 无（不下载 > 100 MB 的文件） |
| HPC、AutoDL、VPN | 未连接、未上传 |

**最终提交上的全量 `tests/research`（`d3b9a3bc`，1,995 s，`evidence/tests/FULL_SUITE_d3b9a3bc.txt`）：856 通过、4 失败**——4 项与 V14 基线逐项相同（`test_s1_built_networks::test_static_validation_passes_on_reload`，`test_s3_gates.py` 的 3 项，同一根因），没有新失败。856 = 第 3 节的 855 + 修好的 1 项。

### 7.2 泄露扫描（`evidence/leak/`）

**方法：** 同 V14：特征文件在仓库外（键名、ssh、IP、主机名），运行时读入，不写进脚本；本机许可文件的值只在内存中比较，从不打印；命中只输出遮蔽片段（`scripts/leak_classify.py`）。对象：本步分支目录（`hpc_v31/`、`batch_def/`、`hpc_package_src/`、`p1_v3_fix_20261105/`）、新包 49 个文件、会话目录 `/home/jin/v3fix`（排除干跑与演练运行目录），以及 `7d22dda1..HEAD` 的每个提交。

- **提交前（`pre`）：** 许可值命中 **0**；4 个提交命中 0。特征命中全部归类为非泄露：(1) 我写的 `scripts/ev_regression.sh` 在检查用的 grep 模式里写了许可键名（只有键名，没有值）——已改为不含完整键名的写法；(2) `scripts/win/diag_build.py`（诊断脚本原样复制）中的过滤词表；(3) 包内 `RUN_PLAN_V3.md` 的公共 DNS 地址（旧会话连通性测试说明）与 `env/` 锁文件中的软件版本号——与 v3 包同一份文件，V14 已归为同类；(4) 演练包解开的代码目录（会话目录，不交付、不提交）中的 `pixi.lock` 版本号、IEA 网页数字等仓库自身内容。**实际命中 0。**
- **推送后（`post`）：** 见 `V3_HPC_PROGRESS.md` 最后一行。

### 7.3 偏差、发现与说明（照实记录）

1. **前提多加一项：** 指令列的前提之外，我加了"账户无存储损耗"（损耗为 1 时末时段水平只看最后一个时段，等价性不成立；账户合同本来就是 0）。四个网络都满足。
2. **形状适配多两处：** 指令点名的 Owen 审计之外，C1（`s4o_c1_precision.country_lookup`）与违反量表（`l23_violation_analysis.country_of`）也按通用方式读取全部约束；多行带 `Link` 维后会改按计量链路的国家归属。为了"只做形状适配"，这两处都保持原标量行的按名归属（`-`）。
3. **价格表字段置 NaN：** 原写法下 `co2 bunkers ASEAN` 母线价格就是燃料舱 CO₂ 影子价格；新写法下它在任何对偶可行解中都为 0（账户容量成本 0、没有末时段行），所以按指令置 NaN、加说明，没有构造替代量。求解后网络文件中的原始对偶不动；台账的结算金额照常（流量 0 × 价格 0 = 0）。
4. **静态检查脚本第一版的缺陷：** 时段坐标比较的格式问题造成误报（判为不通过，不会漏报），已修正并用 datetime 时段的测试覆盖（第 4 节）。
5. **全量测试的新失败：** DFX F0.3 规则把新文件 `zero_slack_check.py` 列为"执行清单外的改动"；按无人值守规则（原因在新增的打包脚本）修复为豁免，同 V3 的 `batch_def.py`（第 3 节）。
6. **回归用的是演练包：** 第 5.2 节在 `13ebce95` 的演练包上运行；正式包 `d3b9a3bc` 与它相比只改了 `research/` 下的计划与指南，代码逐文件相同。演练包放在会话目录，标注不得上传，没有删除。
7. **迭代与计算量增加：** 56 时段上迭代多 20–23 %、work units 多 19–41 %。原因是预处理后的模型不同、内点路径不同（INFERENCE）。按指令不改时限、walltime、参考迭代数与预测；写入计划第 15 节"须知"，请审阅端知悉。
8. **作业名不变：** 定义文件只改了名称、说明与运行目录，作业名仍是 `hpr3_*`。所以指南在登录后先用 `qstat -u $USER` 确认没有 v3 残留作业，有就停下联系审阅端。
9. **Owen 的容差解读：** "差值超过 max(0.1 %, 1 M EUR)"按每个参与者 max(0.1 % × |修正前受益|, 1,000,000 EUR) 判定；各国台账 total 按同一容差列出（都没有超过）。
10. **本机结果目录：** v3.1 的结果下载到新目录 `work/p1_v3_20261102/hpc_results_v31`，与 v3 分开。
11. **一个会话脚本放在了 work 目录之外：** `/home/jin/v3fix_syntax.sh`（4 个脚本的 `bash -n`），内容已复制为 `scripts/syntax_check.sh`。

### 7.4 提交、推送与复制

**分支：** `codex/v3-fix-20261105`（自 `7d22dda1`；独立 worktree `/home/jin/wt_v3_fix`；不改 main、不 force-push、不合并；指令没有要求开 PR，本次没有开）。

| 提交 | 内容 |
|---|---|
| `ae849e1e` | 修正、前提断言、下游形状适配、静态零松弛检查、新测试 |
| `64aea2e3` | 运行目录参数化、v3.1 定义文件、v3.1 打包脚本、计划路径、包测试 |
| `13ebce95` | DFX F0.3 规则豁免新文件（全量测试的新失败） |
| **`d3b9a3bc`** | 计划第 15 节与 v3.1 指南（任何 v3.1 HPC 求解之前）；**部署包的 `COMMIT`** |
| 本报告所在的提交 | 报告、证据、会话脚本、`fullsize_presolve.sh`、台账条目；提交号与推送结果写在 `V3_HPC_PROGRESS.md` 最后一行（报告不能写自己的提交号） |

**复制到 `work/p1_v3_20261102/`：** `RUN_PLAN_HPC_V3.md`、`HPC_OPERATOR_GUIDE_V3.md`（v3.1 版；v3 版在 git `7d22dda1` 与 `hpc_package_v3/` 中）、`batch_def/BATCH_DEF_2920x3h_v31hpc.json`、`hpc_v31/`、`V3_REPORT_FIX.md`；复制前核对 work 中的旧文件与分支起点 `7d22dda1` 相同（没有其他会话改动）。
