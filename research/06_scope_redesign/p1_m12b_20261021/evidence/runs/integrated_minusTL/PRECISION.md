# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusTL`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 307511842420.801；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B3, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 193 次，原始 3.051596940e+11，对偶 3.051596940e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00225，对偶残差 6.78e-06，互补 9.96e-06，323 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 190 次，原始 3.051596940e+11，对偶 3.051596940e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0139，对偶残差 5.71e-07，互补 6.56e-05，319 s
- 最后一次迭代：第 193 次，原始 3.051596940e+11，对偶 3.051596940e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00225，对偶残差 6.78e-06，互补 9.96e-06，323 s
- 返回数组的 KKT 摘要：原始 307511842420.77484，对偶 307511842415.32947，差 -0.000000 bn，相对 1.77e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 222,040，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.006794，最大为预算 0.02421 倍；一阶影响合计 26 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.66e-11 | 0.0100 | True |
| ID | 4.09e-09 | 0.0100 | True |
| KH | 8.96e-10 | 0.0100 | True |
| LA | 1.97e-09 | 0.0142 | True |
| MM | 6.54e-09 | 0.0100 | True |
| MY | 1.86e-09 | 0.0100 | True |
| PH | 6.05e-10 | 0.0100 | True |
| SG | 7.90e-11 | 0.0197 | True |
| TH | 2.88e-09 | 0.0129 | True |
| TL | 0.00e+00 | 0.0100 | True |
| VN | 3.05e-09 | 0.0100 | True |
| ASEAN | 4.42e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.1195103661777322e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.36e-13 | 1.58e-10 | 1.58e-10 | 1.10e-14 | 1.83e-13 | 0.0100 | True | True |
| ID | 4.65e-10 | 5.78e-09 | 6.25e-09 | 1.46e-11 | 5.82e-12 | 0.0100 | True | True |
| KH | 1.60e-11 | 5.10e-10 | 5.26e-10 | 5.20e-12 | 2.37e-12 | 0.0100 | True | True |
| LA | 3.13e-11 | 8.63e-10 | 8.95e-10 | 1.08e-11 | 1.20e-12 | 0.0142 | True | True |
| MM | 2.68e-11 | 2.30e-09 | 2.32e-09 | 1.48e-11 | 2.18e-12 | 0.0100 | True | True |
| MY | 8.23e-11 | 1.44e-09 | 1.52e-09 | 4.57e-12 | 3.99e-12 | 0.0100 | True | True |
| PH | 1.72e-10 | 7.29e-10 | 9.01e-10 | 5.48e-12 | 1.32e-12 | 0.0100 | True | True |
| SG | 7.61e-12 | 1.48e-10 | 1.56e-10 | 2.97e-14 | 1.86e-13 | 0.0197 | True | True |
| TH | 5.17e-10 | 1.18e-09 | 1.70e-09 | 5.80e-12 | 1.70e-12 | 0.0129 | True | True |
| TL | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| VN | 1.49e-10 | 2.35e-09 | 2.50e-09 | 1.13e-11 | 3.49e-12 | 0.0100 | True | True |
| ASEAN | 3.01e-10 | 7.18e-10 | 1.02e-09 | 0.00e+00 | 1.54e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
