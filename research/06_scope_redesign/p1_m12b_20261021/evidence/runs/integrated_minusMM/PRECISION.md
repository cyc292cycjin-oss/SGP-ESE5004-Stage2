# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMM`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 305078631238.75；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 108 次，原始 3.026121710e+11，对偶 3.026121710e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000137，对偶残差 2.78e-06，互补 5.81e-06，145 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 103 次，原始 3.026121710e+11，对偶 3.026121710e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00573，对偶残差 3.6e-06，互补 0.00036，137 s
- 最后一次迭代：第 108 次，原始 3.026121710e+11，对偶 3.026121710e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000137，对偶残差 2.78e-06，互补 5.81e-06，145 s
- 返回数组的 KKT 摘要：原始 305078631238.71686，对偶 305078631235.49786，差 -0.000000 bn，相对 1.06e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 206,055，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.003738，最大为预算 0.003776 倍；一阶影响合计 10 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.31e-11 | 0.0100 | True |
| ID | 2.04e-09 | 0.0100 | True |
| KH | 1.10e-09 | 0.0100 | True |
| LA | 1.10e-09 | 0.0142 | True |
| MM | 0.00e+00 | 0.0100 | True |
| MY | 3.94e-10 | 0.0100 | True |
| PH | 4.11e-10 | 0.0100 | True |
| SG | 1.86e-11 | 0.0197 | True |
| TH | 2.38e-09 | 0.0129 | True |
| TL | 1.27e-11 | 0.0100 | True |
| VN | 2.03e-09 | 0.0100 | True |
| ASEAN | 6.14e-10 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 8.6207443377255e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.37e-13 | 7.26e-11 | 7.28e-11 | 1.62e-14 | 3.06e-13 | 0.0100 | True | True |
| ID | 3.55e-10 | 2.01e-09 | 2.37e-09 | 9.26e-12 | 9.31e-12 | 0.0100 | True | True |
| KH | 9.82e-12 | 2.93e-10 | 3.03e-10 | 5.18e-12 | 1.80e-12 | 0.0100 | True | True |
| LA | 1.38e-11 | 3.42e-10 | 3.56e-10 | 1.06e-11 | 1.38e-12 | 0.0142 | True | True |
| MM | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| MY | 8.26e-11 | 4.43e-10 | 5.25e-10 | 2.75e-12 | 2.18e-12 | 0.0100 | True | True |
| PH | 3.33e-11 | 3.72e-10 | 4.05e-10 | 4.54e-12 | 1.90e-12 | 0.0100 | True | True |
| SG | 7.76e-12 | 5.08e-11 | 5.85e-11 | 1.75e-14 | 3.15e-13 | 0.0197 | True | True |
| TH | 4.71e-10 | 5.54e-10 | 1.02e-09 | 5.59e-12 | 2.28e-12 | 0.0129 | True | True |
| TL | 4.83e-13 | 3.70e-11 | 3.75e-11 | 7.43e-14 | 3.40e-13 | 0.0100 | True | True |
| VN | 1.43e-10 | 1.06e-09 | 1.21e-09 | 1.08e-11 | 3.74e-12 | 0.0100 | True | True |
| ASEAN | 7.17e-11 | 2.46e-10 | 3.17e-10 | 0.00e+00 | 2.60e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 14 s。
