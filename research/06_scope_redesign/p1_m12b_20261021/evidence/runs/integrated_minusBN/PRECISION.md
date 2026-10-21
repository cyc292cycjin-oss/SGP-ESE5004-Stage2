# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusBN`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 307518893134.1833；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 154 次，原始 3.051788780e+11，对偶 3.051788780e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000107，对偶残差 3.17e-06，互补 1.33e-06，266 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 145 次，原始 3.051788780e+11，对偶 3.051788780e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00627，对偶残差 6.79e-07，互补 0.00049，248 s
- 最后一次迭代：第 155 次，原始 3.051788780e+11，对偶 3.051788780e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000204，对偶残差 3.73e-06，互补 7.43e-07，268 s
- 返回数组的 KKT 摘要：原始 307518893134.1644，对偶 307518893133.75305，差 -0.000000 bn，相对 1.34e-12 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 231,041，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.002199，最大为预算 0.001012 倍；一阶影响合计 4 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 0.00e+00 | 0.0100 | True |
| ID | 8.62e-10 | 0.0100 | True |
| KH | 3.95e-10 | 0.0100 | True |
| LA | 2.88e-10 | 0.0142 | True |
| MM | 5.41e-10 | 0.0100 | True |
| MY | 1.53e-10 | 0.0100 | True |
| PH | 9.36e-11 | 0.0100 | True |
| SG | 1.32e-11 | 0.0197 | True |
| TH | 9.06e-10 | 0.0129 | True |
| TL | 1.43e-12 | 0.0100 | True |
| VN | 5.19e-10 | 0.0100 | True |
| ASEAN | 2.73e-10 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.4137892368191066e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| ID | 3.57e-10 | 3.22e-10 | 6.78e-10 | 1.26e-12 | 2.81e-12 | 0.0100 | True | True |
| KH | 1.37e-11 | 1.01e-10 | 1.15e-10 | 4.89e-13 | 1.93e-12 | 0.0100 | True | True |
| LA | 2.94e-11 | 6.40e-11 | 9.34e-11 | 1.04e-12 | 3.73e-13 | 0.0142 | True | True |
| MM | 3.17e-11 | 2.10e-10 | 2.41e-10 | 1.21e-12 | 9.61e-13 | 0.0100 | True | True |
| MY | 7.54e-11 | 8.63e-11 | 1.62e-10 | 3.89e-13 | 2.07e-12 | 0.0100 | True | True |
| PH | 3.22e-11 | 7.49e-11 | 1.07e-10 | 4.05e-13 | 5.26e-13 | 0.0100 | True | True |
| SG | 7.59e-12 | 1.21e-11 | 1.97e-11 | 7.35e-15 | 8.67e-14 | 0.0197 | True | True |
| TH | 5.55e-10 | 1.90e-10 | 7.45e-10 | 6.17e-13 | 6.30e-13 | 0.0129 | True | True |
| TL | 4.83e-13 | 5.03e-12 | 5.51e-12 | 1.01e-14 | 8.73e-14 | 0.0100 | True | True |
| VN | 1.31e-10 | 1.10e-10 | 2.41e-10 | 9.83e-13 | 2.66e-12 | 0.0100 | True | True |
| ASEAN | 9.16e-11 | 8.59e-11 | 1.78e-10 | 0.00e+00 | 6.72e-14 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
