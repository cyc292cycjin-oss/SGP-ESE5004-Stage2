# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/integrated`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 327019334823.7231；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 132 次，原始 3.246648030e+11，对偶 3.246648030e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00169，对偶残差 1.37e-05，互补 1.3e-05，228 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 121 次，原始 3.246648030e+11，对偶 3.246648030e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0249，对偶残差 1.44e-05，互补 0.0012，207 s
- 最后一次迭代：第 132 次，原始 3.246648030e+11，对偶 3.246648030e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00169，对偶残差 1.37e-05，互补 1.3e-05，228 s
- 返回数组的 KKT 摘要：原始 327019334823.6729，对偶 327019334817.23645，差 -0.000000 bn，相对 1.97e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 214,653，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.05271，最大为预算 0.007887 倍；一阶影响合计 40 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.13e-11 | 0.0100 | True |
| ID | 7.60e-09 | 0.0131 | True |
| KH | 1.64e-09 | 0.0100 | True |
| LA | 1.07e-08 | 0.0148 | True |
| MM | 5.70e-09 | 0.0100 | True |
| MY | 1.47e-09 | 0.0100 | True |
| PH | 2.78e-10 | 0.0100 | True |
| SG | 4.47e-10 | 0.0207 | True |
| TH | 7.70e-09 | 0.0124 | True |
| TL | 1.77e-11 | 0.0100 | True |
| VN | 3.49e-09 | 0.0116 | True |
| ASEAN | 1.86e-09 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.4802913387590524e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.61e-13 | 1.88e-10 | 1.88e-10 | 2.93e-14 | 4.40e-13 | 0.0100 | True | True |
| ID | 3.74e-10 | 5.91e-09 | 6.29e-09 | 2.40e-11 | 1.43e-11 | 0.0131 | True | True |
| KH | 1.70e-11 | 8.75e-10 | 8.92e-10 | 8.06e-12 | 2.12e-12 | 0.0100 | True | True |
| LA | 1.71e-11 | 8.83e-10 | 9.00e-10 | 1.75e-11 | 2.36e-11 | 0.0148 | True | True |
| MM | 2.61e-11 | 5.79e-09 | 5.82e-09 | 2.17e-11 | 5.28e-12 | 0.0100 | True | True |
| MY | 8.70e-11 | 1.43e-09 | 1.52e-09 | 7.51e-12 | 4.11e-12 | 0.0100 | True | True |
| PH | 3.22e-11 | 1.15e-09 | 1.18e-09 | 9.58e-12 | 3.29e-12 | 0.0100 | True | True |
| SG | 7.64e-12 | 1.49e-09 | 1.50e-09 | 2.93e-14 | 3.79e-13 | 0.0207 | True | True |
| TH | 1.27e-09 | 2.15e-09 | 3.42e-09 | 1.01e-11 | 4.96e-12 | 0.0124 | True | True |
| TL | 3.83e-13 | 1.00e-10 | 1.00e-10 | 1.26e-13 | 5.14e-13 | 0.0100 | True | True |
| VN | 1.56e-10 | 2.73e-09 | 2.88e-09 | 1.90e-11 | 7.43e-12 | 0.0116 | True | True |
| ASEAN | 1.22e-09 | 1.03e-09 | 2.25e-09 | 0.00e+00 | 4.19e-13 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
