# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusID`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 231845009512.85455；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 109 次，原始 2.317866210e+11，对偶 2.317866210e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000255，对偶残差 3.98e-06，互补 1.78e-05，94 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 101 次，原始 2.317866210e+11，对偶 2.317866210e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00485，对偶残差 8.09e-05，互补 0.000347，86 s
- 最后一次迭代：第 109 次，原始 2.317866210e+11，对偶 2.317866210e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000255，对偶残差 3.98e-06，互补 1.78e-05，94 s
- 返回数组的 KKT 摘要：原始 231845009512.82483，对偶 231845009502.42438，差 -0.000000 bn，相对 4.49e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 121,102，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.004214，最大为预算 0.09807 倍；一阶影响合计 36 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.65e-11 | 0.0100 | True |
| ID | 0.00e+00 | 0.0100 | True |
| KH | 1.90e-09 | 0.0100 | True |
| LA | 4.17e-09 | 0.0142 | True |
| MM | 1.33e-08 | 0.0100 | True |
| MY | 1.24e-09 | 0.0100 | True |
| PH | 1.69e-09 | 0.0100 | True |
| SG | 5.06e-11 | 0.0197 | True |
| TH | 5.20e-09 | 0.0129 | True |
| TL | 3.59e-11 | 0.0100 | True |
| VN | 3.16e-09 | 0.0100 | True |
| ASEAN | 5.42e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.6023225140631197e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.11e-13 | 2.43e-10 | 2.43e-10 | 1.32e-13 | 1.68e-12 | 0.0100 | True | True |
| ID | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| KH | 1.41e-11 | 1.27e-09 | 1.29e-09 | 1.18e-11 | 9.90e-12 | 0.0100 | True | True |
| LA | 1.33e-11 | 2.25e-09 | 2.27e-09 | 2.23e-11 | 9.47e-12 | 0.0142 | True | True |
| MM | 2.57e-11 | 6.96e-09 | 6.99e-09 | 3.15e-11 | 2.53e-11 | 0.0100 | True | True |
| MY | 1.12e-10 | 1.75e-09 | 1.86e-09 | 9.64e-12 | 1.54e-11 | 0.0100 | True | True |
| PH | 4.67e-11 | 2.08e-09 | 2.13e-09 | 1.06e-11 | 1.45e-11 | 0.0100 | True | True |
| SG | 4.01e-12 | 1.70e-10 | 1.74e-10 | 1.29e-13 | 1.58e-12 | 0.0197 | True | True |
| TH | 9.95e-11 | 2.66e-09 | 2.76e-09 | 1.42e-11 | 1.73e-11 | 0.0129 | True | True |
| TL | 3.00e-13 | 1.27e-10 | 1.27e-10 | 0.00e+00 | 2.04e-12 | 0.0100 | True | True |
| VN | 1.23e-10 | 2.50e-09 | 2.62e-09 | 2.36e-11 | 2.17e-11 | 0.0100 | True | True |
| ASEAN | 2.30e-09 | 1.49e-09 | 3.80e-09 | 0.00e+00 | 2.04e-12 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 10 s。
