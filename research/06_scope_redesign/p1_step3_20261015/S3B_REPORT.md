# S3B 报告：修正轮（第 66–69 项）与云端正式试算准备

分支 `codex/s3-gas-imports-shipping-20261015`（draft PR #24，叠在 #23 上）。执行顺序 R4 → R1 → R2 → R3 → R5 → 冒烟 → 云端部署包。本机只做构建、56×3h 冒烟与诊断，不做 365×24h 或 2920×3h 正式求解，不连接云端。求解器 Gurobi 12.0.3（第 65 项，许可经 `GRB_LICENSE_FILE` 只读引用，不复制、不输出、不入库）。止损：单次运行超过预计用时 2 倍、56×3h 上限 30 分钟，或 Gurobi 返回非最优状态，立即停止并报告日志末尾，不重试、不换参数。结论分级 VERIFIED / EXACT / INFERENCE / PROPOSED。

## 摘要（≤10 行）

（全部小节完成后填写。）

---

## 1. R4 求解配置与缩放（第 69 项）

代码：`scripts_project/s3b_scaling.py`（缩放与还原）、`scripts_project/s3b_interior.py`（清理阈值、同时充放检查）、`scripts_project/v5/v5_gates.py::gate_a1_a2_interior`、`scripts_project/s2_solve.py`（`--solver-profile`、`--scaling`；求解改为 `m.solve` → 还原单位 → PyPSA 赋值）、`scripts_project/s3b_r4_solver_data.py`（登记片段 `solver_r4.csv`）、`scripts_project/s3b_r4_compare.py`（等价性对照）。配置 `research.solver`。证据 `evidence/s3b_r4/`。

### 1.1 求解器设置（EXACT）

基础为 PyPSA-Eur v2025.07.0 `config.default.yaml` 的 `solving.solver.options: gurobi-default`（第 1034–1035 行）与 `solver_options.gurobi-default`（第 1056–1064 行）：threads 32、method 2、crossover 0、BarConvTol 1e-5、Seed 123、AggFill 0、PreDual 0、GURO_PAR_BARDENSETHRESH 200。

| 参数 | PyPSA-Eur | `formal_barrier`（主算） | 理由（已登记 `solver_difference_*`） |
|---|---|---|---|
| Method | 2 | 2 | 同 |
| Crossover | 0 | 0（`crossover_diagnostic` 为 1） | 同；对照诊断单独开启 |
| BarConvTol | 1e-5 | **1e-8** | 关闭 crossover 后靠内点解本身保证精度；1e-8 即 Gurobi 默认值，比 PyPSA-Eur 严格 3 个数量级 |
| BarHomogeneous | 未设（numeric-focus / fallback 档为 1，第 1065–1083 行） | **1** | 区分真正不可行与数值问题（S3-7 的 crossover INF_OR_UNBD 即此类） |
| Threads | 32 | **8** | 本机 8 个物理核；云端并行时每情景 8 线程 |
| Seed | 123 | 123 | 同 |
| AggFill / PreDual / GURO_PAR_BARDENSETHRESH | 0 / 0 / 200 | 同 | 同 |
| NumericFocus | 未设 | 未设 | 按指令沿用 PyPSA-Eur（S3-7 的 NumericFocus 3 不再使用） |
| TimeLimit | 未设 | 1,750 s（56×3h）/ 10,800 s（云端 365×24h） | 止损规则，不是数值设置 |

开关 `research.solver.profile: formal_barrier | crossover_diagnostic`，命令行 `--solver-profile` 可覆盖，回执记录 `solver_profile` 与全部参数。

### 1.2 缩放（只实施 (a)(b)，EXACT）

- **(a) 目标常数移出 LP。** 三个只承载常数的固定列：PyPSA `objective_constant`（既有可扩建容量的投资常数，取值 5,723,738,530 EUR，目标系数 −1）、`Research_existing_FOM_constant`（固定为 1，系数 = 存量年固定运维 8,227,672,834 EUR）、`Research_existing_cross_border_FOM_constant`（固定为 1，系数 24,958,489 EUR）。三列均不出现在任何约束中（构建时核对），用 linopy `remove_variables` 移除；合计 +2,528,892,792.84 EUR 在求解后加回，`n.objective` = LP 目标 + 常数，总成本口径不变（回执同时记录 `objective` 与 `objective_lp`）。导出的 LP 在原单位下不含这三列，常数记为 `offset`。
- **(b) 大容量 Store 改用 GWh / kt。** 107 个生物质池（MWh→GWh）、8 个 CO₂ 封存库与 97 个捕集缓冲（t→kt）：`Store-e`、`Store-e_nom` 列乘 1000（约束与目标系数 ×1000），这些 Store 所属的行（能量平衡、e 与 e_nom 上下限、各国封存上限 `research_co2_storage_cap-*`）除以 1000。净效果：能量平衡中 `Store-p` 的系数由 156.43 变为 0.156，右端项 ÷1000，e_nom 的成本系数 ×1000。求解后缩放列的解 ×1000、缩放行的对偶 ÷1000、缩放列的归约成本 ÷1000，网络与全部报告仍为 MWh / t。不改网络本身。
- 基尔霍夫行归一化未实施（登记 `scaling_kirchhoff_not_applied`）。

### 1.3 等价性检验（当前 S3 网络，需求未改；VERIFIED）

网络：S3-7 一体化主算网络按新配置重建（`results_project/s3b/r4/integrated`；只改了配置哈希）。运行 A（`formal_barrier`，不缩放）导出的 LP 与 S3-7 Gurobi 冒烟导出的 LP **十个数组的 SHA256 全部相同**，即同一个 LP。

| 项 | 运行 A（不缩放） | 运行 B（缩放） | 判定 |
|---|---|---|---|
| Gurobi 状态 | OPTIMAL（barrier 92 次迭代 / 89.5 s，Crossover 0） | OPTIMAL | — |
| 目标值（常数加回）EUR/a | 698,803,334,599.39 | 698,803,334,578.86 | 与参照 6.98803335e11 相对差 5.7e-10 / 6.0e-10；A–B 相对差 2.9e-11（≤ 1e-6） |
| 求解用时 / 峰值 RSS | 105 s / 3.18 GiB | 111 s / 3.10 GiB | 比 S3-7（barrier + crossover 505 s）快约 5 倍 |
| 矩阵系数范围 | [2e-4, 1e3] | [2e-4, 1e3] | 不变（未做基尔霍夫归一） |
| 目标系数范围 | [1, 8e9] | **[2, 1e6]** | 常数列移除 |
| 边界范围 | [0.9, 6e9] | **[0.9, 3e4]** | 常数列移除 |
| 右端项范围 | [3e-4, 3e9] | **[3e-4, 5e8]** | 封存上限 ÷1000；剩余最大值来自国内气年度产量上限（未缩放） |
| Gurobi 警告 | 目标系数大、右端项大、边界大（3 条） | **无** | 消失 |

主要量抽查（`S3B_R4_EQUIVALENCE.json`，130 项：各技术装机、各发电机全年发电、主要链路全年流量、各国封存量、跨境线容量）：117 项差异 ≤ 1e-4（相对）或 ≤ 清理阈值；各国封存量 8 国完全一致。超出容差的 13 项分两类——(i) 接近 0 的量（氨进口 0.009 MWh、FT 油进口 1e-4 MWh、SMR 0.05 MWh、核电 0.04 MWh、液氢进口 0.006 MWh），均低于清理阈值，报告时记为 0；(ii) 成本相同的等价方案在内点解中的分摊差异：陆上风电 0.23%、海上风电 0.16%、DC 链路流量 0.94%、气管道流量 0.03%、炊事气链路 0.06%、国内气井口装机 0.02%。结论（INFERENCE）：缩放不改变最优值，主要量差异属于内点解在退化最优面上的分摊，不是缩放误差。

### 1.4 内点解的配套处理

**A1/A2 新口径（阈值在求解前登记于配置与登记表，求解后未调整）：**

| 准则 | 阈值（与 BarConvTol 挂钩） | 运行 A | 运行 B |
|---|---|---|---|
| 相对原始–对偶间隙 | ≤ 10 × BarConvTol = 1e-7 | 6.0e-11 ✓ | 3.1e-11 ✓ |
| 互补性 L1 / 目标尺度 | ≤ 1e-7 | 2.6e-10 ✓ | ✓ |
| 原始可行性（逐行/逐列） | 1e-3 + 1e-7 × 参考值（V4 预算，1e-7 = 10 × BarConvTol） | 1 行超出（最大 0.080） ✗ | 4 行超出（最大 0.017） ✗ |
| 对偶残差（平稳性，归一化） | ≤ 100 × BarConvTol = 1e-6 | 15 列超出（最大 5.2e-5） ✗ | 4 列（5.5e-5） ✗ |
| 对偶符号（归一化） | ≤ 1e-6 | 5,356 项超出（最大 0.029） ✗ | 5,269 项（0.0013） ✗ |

超出原始可行性预算的行全部是各国 CO₂ 净零行（大气 Store 期末水平 ≤ 0）：运行 A 中 ID 期末 +0.080 t；运行 B 中 ID +0.017、MY +0.0031、TH +0.0011、VN +0.0014 t（各国年 CO₂ 流量 1e8–1e9 t，相对 1e-10 量级）。同一原因使 A3 的 `COUNTRY_CO2_CAP` 与 B1 判为未通过（容差 1e-3 t，因上限为 0 而无相对项）。对偶平稳性与符号误差为绝对值 ≤ 0.03 EUR 级的小乘子，按 `max(1,|乘子|)` 归一后超过 1e-6。**判定（VERIFIED）：A1/A2 新口径未通过；间隙与互补性远低于阈值，未通过项是内点解在 Gurobi 默认可行/最优容差（1e-6，按 Gurobi 内部缩放后的模型）下的残差，按原单位折算后超过了与 1e-8 挂钩的预算。** 未在看到结果后放宽阈值。PROPOSED（待用户决定）：(1) 原始/对偶预算改为与 Gurobi `FeasibilityTol` / `OptimalityTol` 挂钩（10 × 1e-6），间隙仍用 10 × BarConvTol；或 (2) 维持阈值、在正式运行中把 `FeasibilityTol` / `OptimalityTol` 收紧到 1e-8；或 (3) A1/A2、B1 以 crossover 顶点解评定（冒烟第 4 条的诊断运行可提供对照）。

**清理阈值（登记 `interior_cleanup_threshold_rule`）：** 报告时 |x| < τ_g 记为 0，τ_g = 10 × BarConvTol × 该变量组的最大绝对值（组 = 组件 × 属性），下限 1e-6。推导：barrier 终止时相对互补性 ≤ BarConvTol，贴界变量的残余值与本组量级成比例；系数 10 覆盖预处理、后处理和单位还原。运行 B 的阈值：发电机装机 0.019 MW、链路装机 0.013 MW、线路 0.014 MW、Store 能量 54 t（最大 5.4e9）、链路流量 0.013 MW；低于阈值的值占各组绝对值总和的比例 ≤ 3e-8。CO₂ 净零行的 +0.017 t 远低于 Store 能量阈值 54 t。

**同时充放（运行 B）：** 电池 98 对、家庭电池 98 对均为 0 次；H₂ 储罐、气/氨/甲醇/CO₂ 储存是单一 p 变量，结构上不可能同时充放；**PHS existing**（存量抽水蓄能）有 3 个时段同时抽水和发电（运行 A 为 8 个），最大 681 MW，全年合计约 106.5 GWh——这是 LP 允许的"以效率损失消纳过剩电力"的退化解，顶点解中也可能出现，解读 PHS 运行时须留意。

**解读提醒（登记 `interior_solution_degeneracy_note`）：** 内点解可能把成本相同的等价方案分摊到多个选项上（见 1.3 的风电、DC 流量差异），解读装机与流量时须留意。

---

## 2. R1 需求增长改用倍数法（第 66 项）

（待填）

## 3. R2 工业"其他"子部门的敏感性（第 67 项）

（待填）

## 4. R3 LNG 接收站扩建成本与马新管道（第 68 项）

（待填）

## 5. R5 S3 报告第 11 节其余事项

（待填）

## 6. 冒烟测试（Gurobi，formal_barrier）

（待填）

## 7. 云端部署包与资源估算

（待填）

## 8. 需要用户决定的事项

（待填）
