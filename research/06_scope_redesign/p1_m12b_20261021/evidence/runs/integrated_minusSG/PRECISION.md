# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusSG`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `suboptimal`；目标 301126045904.6008；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：False**（optimal False，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B15, B3, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 61 次，原始 2.987715310e+11，对偶 2.987705810e+11，差 -9.5e+05 EUR（相对 3.18e-06），原始残差 0.0969，对偶残差 0.000262，互补 3，108 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 65 次，原始 2.987714760e+11，对偶 2.987705400e+11，差 -9.36e+05 EUR（相对 3.13e-06），原始残差 0.174，对偶残差 0.00025，互补 2.89，115 s
- 最后一次迭代：第 75 次，原始 2.987714120e+11，对偶 2.987705050e+11，差 -9.07e+05 EUR（相对 3.04e-06），原始残差 0.643，对偶残差 0.00024，互补 2.78，132 s
- 返回数组的 KKT 摘要：原始 301126045904.5324，对偶 301123965642.6567，差 -0.002080 bn，相对 6.91e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 201,449，超预算 84（与 `l23_violation_analysis.py` 一致：True），最大违反 2.751，最大为预算 11.48 倍；一阶影响合计 43,507 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.91e-07 | 0.0100 | True |
| ID | 1.14e-05 | 0.0100 | True |
| KH | 9.29e-07 | 0.0100 | True |
| LA | 2.71e-06 | 0.0142 | True |
| MM | 4.25e-06 | 0.0100 | True |
| MY | 1.58e-06 | 0.0100 | True |
| PH | 1.21e-06 | 0.0100 | True |
| SG | 0.00e+00 | 0.0197 | True |
| TH | 1.78e-06 | 0.0129 | True |
| TL | 9.91e-08 | 0.0100 | True |
| VN | 3.68e-06 | 0.0100 | True |
| ASEAN | 1.55e-05 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 2 / 84；最大倍数的行是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.3433849909395635e-08（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.23e-07 | 3.54e-05 | 3.56e-05 | 2.25e-07 | 9.33e-08 | 0.0100 | True | True |
| ID | 1.05e-04 | 9.35e-04 | 1.04e-03 | 1.62e-05 | 5.65e-06 | 0.0100 | True | True |
| KH | 7.04e-06 | 1.32e-04 | 1.39e-04 | 5.85e-06 | 8.37e-07 | 0.0100 | True | True |
| LA | 8.78e-06 | 1.62e-04 | 1.71e-04 | 1.07e-05 | 1.06e-06 | 0.0142 | True | True |
| MM | 3.04e-06 | 3.67e-04 | 3.70e-04 | 1.12e-05 | 3.37e-06 | 0.0100 | True | True |
| MY | 2.63e-05 | 2.25e-04 | 2.52e-04 | 6.09e-06 | 1.23e-06 | 0.0100 | True | True |
| PH | 2.37e-05 | 1.56e-04 | 1.79e-04 | 1.60e-06 | 7.93e-07 | 0.0100 | True | True |
| SG | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0197 | True | True |
| TH | 2.36e-05 | 2.23e-04 | 2.46e-04 | 1.04e-05 | 2.29e-06 | 0.0129 | True | True |
| TL | 8.38e-08 | 1.77e-05 | 1.78e-05 | 2.78e-07 | 1.22e-07 | 0.0100 | True | True |
| VN | 4.81e-05 | 2.36e-04 | 2.84e-04 | 7.34e-06 | 1.86e-06 | 0.0100 | True | True |
| ASEAN | 1.27e-05 | 1.04e-04 | 1.17e-04 | 0.00e+00 | 1.06e-05 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
