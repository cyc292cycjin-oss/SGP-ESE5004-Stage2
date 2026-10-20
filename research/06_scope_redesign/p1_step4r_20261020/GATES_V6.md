# GATES_V6：求解后验收门槛（第 128 项；原则 9）——定义先于套用

**状态：** PROPOSED（S4R，2026-10-20）。本文件在对任何历史运行重评之前单独提交；重评结果不得反过来修改本定义（若发现定义缺陷，写入 S4R 报告，由用户决定）。

## 0. 设计依据（前人做法）

| 来源 | 做法 | 引用 |
|---|---|---|
| PyPSA-Eur v2025.07.0 `scripts/solve_network.py` | `status, condition = n.optimize(**kwargs)`；`if status != "ok": logger.warning(...)`；`if "warning" in condition: raise RuntimeError("Solving status 'warning'. Discarding solution.")`；`if "infeasible" in condition: ... raise RuntimeError(...)`；可选 `check_objective_value`（`np.isclose(n.objective, expected_value, atol, rtol)`，缺省关闭，`atol 1_000_000`、`rtol 0.01`）。**没有**对 "suboptimal" 的处理，没有求解后 KKT / 物理残差检查；解直接 `export_to_netcdf` | GitHub tag v2025.07.0，`solve_network.py` 约第 770–795 行（check_objective_value）、第 900–940 行（状态处理）；`config/config.default.yaml` 第 1105–1109 行（check_objective） |
| PyPSA-Eur v2025.07.0 求解器档案 | `gurobi-default`: threads 32, method 2, crossover 0, **BarConvTol 1e-5**, Seed 123, AggFill 0, PreDual 0, GURO_PAR_BARDENSETHRESH 200；`gurobi-numeric-focus`: NumericFocus 3, BarHomogeneous 1, BarConvTol 1e-5, **FeasibilityTol 1e-4, OptimalityTol 1e-4**, ObjScale −0.5；`gurobi-fallback`: BarConvTol 1e-5, FeasibilityTol 1e-5, OptimalityTol 1e-5；HiGHS: primal / dual feasibility 1e-5, ipm_optimality 1e-4 | 库内副本 `research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml`，`solving.solver_options`（第 1056–1090 行） |
| PyPSA-Earth（pypsa-asean 检出）`scripts/solve_network.py` | 同一模式：`if status != "ok": logger.warning(...)`；`if "infeasible" in condition: raise RuntimeError("Solving status 'infeasible'")`；无其他求解后检查 | `pypsa-asean/scripts/solve_network.py` 第 1190–1207 行 |
| Gurobi 文档（参数与状态码） | `BarConvTol`（缺省 1e-8，范围 0–1）：barrier 在相对原始–对偶目标间隙、相对原始 / 对偶可行性与互补性都低于该容差时以 OPTIMAL 终止；`FeasibilityTol`（缺省 1e-6，1e-9–1e-2）：所有约束须满足到该容差；`OptimalityTol`（缺省 1e-6）：对偶可行性（简单形 / crossover 的 reduced cost）容差；状态 `OPTIMAL`："solved to optimality (subject to tolerances)"；`SUBOPTIMAL`："Unable to satisfy optimality tolerances; a sub-optimal solution is available"；`TIME_LIMIT`、`NUMERIC`、`INF_OR_UNBD` 如文档 | docs.gurobi.com Optimizer reference，Parameters 与 Optimization Status Codes 页（2026-10-20 读取） |
| 本项目 S4B-0（第 71 项选项 1） | 预算 = 10 × 求解器容差，行相对项按行活动参考量；对偶符号误差按驻点尺度 | `scripts_project/s4b_acceptance.py` 文档串 |
| 本项目 S4N / S4O（第 119、120 项） | 能否使用以 C1 (a)(b)(c) 为准；门槛只作数值信息 | `scripts_project/s4o_c1_precision.py` 文档串；注册表 `s4n_decision_119_precision_over_label` |
| S4Q 发现第 1 条 | 现行 A1_A2_S4B 的对偶预算固定为 10 × OptimalityTol（1e-5），不随档案 BarConvTol 变化：1e-6 候选档案六次 optimal 运行的对偶符号误差 1–2e-4 全部"不通过"，而 C1 全过 | `work/p1_step4q_20261020/S4Q_REPORT.md` §6 第 7 点、§9 第 1 条 |
| 文献中的精度报告惯例 | PyPSA-Eur / PyPSA-Earth 论文与文档只报告求解器与档案（BarConvTol 等），不另报 KKT 残差；OSeMOSYS / TIMES 类模型同样以求解器状态为准；对偶价格的使用以"interior point without crossover"为常规做法（PyPSA-Eur 文档 "Solving" 章） | PyPSA-Eur 文档 configuration / solving 节；Parzen et al. 2023（PyPSA-Earth），Hörsch et al. 2018（PyPSA-Eur）——均未定义求解后验收门槛 |

**结论：** 前人把"求解器 optimal 到其容差"当作充分条件，不做求解后残差门槛；本项目第 119 项已把"能否使用"改为由研究问题所需精度（C1）判定。V6 据此只保留两类**判据**，其余全部降为**诊断**，并把诊断容差与求解档案的容差绑定（S4Q 发现第 1 条）。

## 1. 符号与容差变量

- `ε_f = FeasibilityTol`（档案未设时取 Gurobi 缺省 1e-6）；`ε_o = OptimalityTol`（同，1e-6）；`ε_b = BarConvTol`（档案值：A 1e-8；候选 1e-6；pypsa_eur_default 1e-5）。
- 对偶残差的有效容差：`ε_d = max(ε_o, ε_b)`——barrier 返回的内点其对偶可行性只收敛到 BarConvTol 量级（S4Q §6 第 7 点的观察；Gurobi 文档 BarConvTol 定义），因此对偶类诊断随档案容差变化。
- 预算形式一律"绝对 + 相对"：`budget = a + k × ε × ref`，k = 10（S4B-0 选项 1，不变），绝对底 a = 1e-3（V4 原生单位），`ref` 为该行 / 列的活动参考量（S4B-0 定义不变）。
- 所有判据与诊断只用**返回解**（`solution/X, Pi, RC`）与导出文件计算；不调用求解器。

## 2. 判据（go / no-go；仅两类）

### G1　精度判据 = C1（第 119 项，原文不变）

| 代号 | 目的 | 计算口径 | 容差 | 类别 |
|---|---|---|---|---|
| G1a | 总成本精度 | 返回数组的原始目标与对偶目标之差（`kkt_summary.json`，原始单位） | ≤ 0.01 bn EUR 且相对 ≤ 1e-5 | 判据 |
| G1b | 分国一阶影响 | 原始违反 × 对偶的分国求和（L23 §6 方法；跨境行计入两国） | 每国 ≤ max(1 % × 该国"不互联 − 一体化"参照差额, 0.01 bn)；BN / SG / VN 生物质池行不主导 | 判据 |
| G1c | 价格质量 | B16 账本恒等式；KKT 残差对分国结算的影响 S_c + R_c | B16 相对误差 ≤ 1e-6；每国 S_c + R_c ≤ 同 (b) 的阈值 | 判据 |

分级不变：G1a + G1b 通过 → 第一层（总成本）可用；G1c 也通过 → 节点电价结算可用。**求解器状态不是判据**（optimal / suboptimal / time_limit 只作记录，见 D0）。

### G2　结构判据（必要检查）

| 代号 | 目的 | 计算口径 | 容差 | 类别 |
|---|---|---|---|---|
| G2.1 网络身份 | 求解的网络就是部署包登记的网络 | 输入网络文件 SHA256 = 包 `SHA256SUMS` / `BUILD_RECEIPT` 登记值；求解后网络 A4 读回（EXACT_SEMANTIC_ROUNDTRIP） | 精确相等 | 判据 |
| G2.2 配置子集哈希（替代现行 B12 整份配置哈希） | 影响网络与 LP 的配置子集未变 | 对 `research` 配置中决定网络构建与 LP 的键子集求 SHA256：`scenario`、`cross_border.*`、`fuels.price_scenario`、`finance.*`、`sector.*`、`s3.*`、`renewable.*`、`fleet.*`、`nuclear.*`、`candidates.*`、`hydro.*`、`hydrogen.*`、`cost_layer.active`、`numerics.*`、`network.*`、`corridors.*`、`bunkers.*`、`co2.*`、`s2.*`、`cost_scaling.*`、`carbon.*`、`demand.*`、`transmission.*`、`existing_cross_border_electricity.*`、`solver.scaling.*`、`solver.interior.*`；**不含** `solver.profile`、`solver.profiles.*`（档案与白名单的增减不改变网络 / LP）、注释与键顺序（按规范化 JSON 排序后哈希） | 与网络 meta 中记录的子集哈希精确相等 | 判据 |
| G2.3 结果完整性 | 导出齐全、可对账 | `EXPORTS.json` 列出的文件存在且 SHA256 一致；`solution/X, Pi, RC` 维度 = LP 列 / 行数；账本 B16 可计算（含于 G1c）；`SOLVE_RECEIPT.json` 含档案参数、终止状态、目标值、网络 SHA256 | 全部满足 | 判据 |

运行验收 = G1a ∧ G1b ∧ G1c ∧ G2.1 ∧ G2.2 ∧ G2.3。等级标签：`ACCEPTED_LAYER2`（全过）、`ACCEPTED_LAYER1`（G1c 不过，其余过）、`NOT_ACCEPTED`（其他）。

## 3. 诊断（只报告，不决定去留）

| 代号 | 目的 | 计算口径 | 容差（绝对 + 相对，随档案） | 对应现行门槛 |
|---|---|---|---|---|
| D0 求解器状态 | 记录 | `SOLVE_RECEIPT.json` termination；barrier 迭代、重启、停滞、TimeLimit | 无（记录） | （无） |
| D1 原始残差 | 行 / 列违反 | `\|violation_i\| ≤ 1e-3 + k ε_f ref_i`（S4B-0 不变） | k = 10 | A1_A2_S4B 原始部分 |
| D2 对偶残差 | 驻点、对偶符号 | 驻点 `\|c_j − a_jᵀπ − rc_j\| / max(1, \|c_j\| + \|a_j\|ᵀ\|π\| + \|rc_j\|) ≤ k ε_d`；对偶符号误差同尺度 ≤ k ε_d | **k = 10，ε_d = max(ε_o, ε_b)**（S4Q 发现第 1 条：随 BarConvTol） | A1_A2_S4B 对偶部分（现行固定 k ε_o） |
| D3 间隙与互补 | 相对原始–对偶间隙；互补 L1 / 目标尺度 | ≤ 10 × ε_b（不变） | 随档案 | A1_A2 gap / complementarity |
| D4 物理方程 | V4 物理检查（节点平衡、储能状态、CO₂ 账） | `1e-3 + k ε_f \|ref\|` | k = 10 | A3_S4B |
| D5 目标对账 | 资本 + 可变 + 固定常数 = 目标 | 相对 ≤ 1e-6 | 固定 | A5 |
| D6 分国净零 | 各国大气库终值 | `≤ cap + 1e-3 + k ε_f × 国家 CO₂ 总流量` | k = 10 | B1_S4B（现行无容差版 B1 废止） |
| D7 封存上限 | `co2 sequestered` 终值 | `≤ e_nom × (1 + k ε_f) + 1e-3`（**新增容差**） | k = 10 | B2（现行无容差） |
| D8 生物质池 | 用量 ≤ 潜力、终值 ≥ 0 | `≤ e_nom (1 + k ε_f) + 1e-3`；`≥ −(1e-3 + k ε_f e_nom)` | k = 10 | B3_S4B |
| D9 码头上限 | LNG / H₂ 码头 `p_nom_opt` | `≤ p_nom_max (1 + k ε_f) + 1e-3`（**新增容差**；若 R3 取消上限则改为"≤ 内生上限"诊断） | k = 10 | B14（现行无容差） |
| D10 国产气上限 | 年度产量 | `≤ cap (1 + k ε_f) + 1e-3`（**新增容差**） | k = 10 | B15（现行无容差） |
| D11 需求守恒 | 负荷归属、部门总量 | 相对 1e-6 | 固定 | B8 |
| D12 供给路线 | 每个终端母线 ≥ 2 条路线 | 结构 | — | B11 |
| D13 进口单向 / 价格相同 | 区域外进口符号；两情景进口价相同 | 精确 | — | B13、B16_import_prices |
| D14 情景互换 | 单一开关差异；B6 一体化 ≤ 不互联 | 精确 / 符号 | — | B5、B6 |
| D15 内点清理 | 近零量、同时充放电 | `τ_g = 10 ε_b max\|x_g\|` | 随档案 | INTERIOR_CHECKS |
| D16 整份配置哈希 | 记录（信息） | 现行 B12 | — | B12（降为诊断） |

每项诊断输出：是否在容差内、最大比值（violation / budget）、超预算行数、最差条目；不进入验收。

## 4. 与现行 V5 的对照

| 现行 | V6 |
|---|---|
| `all_passed_solver_tolerances`（A1_A2_S4B、A3_S4B、A5_S4B、B1_S4B、B3_S4B 全过）作标签 | 废止作判据；各项改为 D1–D8 诊断 |
| B12 整份配置哈希（新增档案即不通过） | G2.2 配置子集哈希（判据）+ D16 整份哈希（诊断） |
| B2 / B14 / B15 无容差 | D7 / D9 / D10 加 `1e-3 + 10 ε_f` 容差 |
| 对偶预算固定 10 × OptimalityTol | D2 用 10 × max(OptimalityTol, BarConvTol) |
| C1 (a)(b)(c) + optimal = 验收（第 120 项） | G1 (= C1) + G2 = 验收；optimal 只记录 |

## 5. 重评规则（第 128 项第 (3) 点）

- 对象：L23（一体化、不互联、不互联诊断）、S4M-2（档案 A 三情景）+ S4M-S2 复跑、S4N（试点一体化；C2 三次）、S4O-6（不互联、诊断、NZE）、S4Q（T8 / T16 各三情景）。
- 数据：只用各运行目录已导出的 `SOLVE_RECEIPT.json`、`V5_GATES.json`、`kkt_summary.json`、`INTERIOR_CHECKS.json`、`PRECISION.json`、`LEDGER_IDENTITY.json`；不重新加载求解后网络、不重建 LP（原则 7）。缺文件的项标"不可计算"。
- 输出：`GATES_RETRO_COMPARISON.csv/.md`，新旧标签并列：`V5 all_passed_solver_tolerances`、`V5 失败门槛列表`、`V6 验收等级`、`V6 诊断摘要`（D2 在旧预算与新预算下的比值）。
- 不得因结果修改本定义。

## 6. 实施位置（见 `IMPLEMENTATION_PLAN.md`）

- `scripts_project/v5/v5_gates.py` → 新增 `gates_v6.py`：`acceptance_v6(solve_dir, profile_params, reference)`；`s2_solve.py` 调用处把 `all_passed_*` 改为 `acceptance.v6.label`；`s4o_c1_precision.py` 的 `acceptance` 规则改引 G1 + G2；`run_365x24h.sh` 的停止条件改为 `NOT_ACCEPTED`。
- 单元测试：容差随档案变化（同一残差在 1e-8 / 1e-6 档案下的 D2 判定）；配置子集哈希对 `solver.profiles` 增减不敏感、对 `cross_border` 改动敏感；D7 / D9 / D10 在相对 1e-9 的数值噪声下为"在容差内"。
