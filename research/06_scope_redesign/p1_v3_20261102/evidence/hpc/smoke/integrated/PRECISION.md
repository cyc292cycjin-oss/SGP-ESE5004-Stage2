# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/integrated`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 329705566422.23596；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/no_new_xb minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B3, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 66 次，原始 3.273353650e+11，对偶 3.273351160e+11，差 -2.49e+05 EUR（相对 7.61e-07），原始残差 0.00345，对偶残差 0.0136，互补 0.27，160 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 80 次，原始 3.273351640e+11，对偶 3.273351580e+11，差 -6000 EUR（相对 1.83e-08），原始残差 0.0681，对偶残差 0.00156，互补 0.00771，191 s
- 最后一次迭代：第 80 次，原始 3.273351640e+11，对偶 3.273351580e+11，差 -6000 EUR（相对 1.83e-08），原始残差 0.0681，对偶残差 0.00156，互补 0.00771，191 s
- 返回数组的 KKT 摘要：原始 329705566422.17535，对偶 329705560583.9154，差 -0.000006 bn，相对 1.77e-08 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 207,478，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.545，最大为预算 0.1079 倍；一阶影响合计 1,083 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.02e-10 | 0.0100 | True |
| ID | 6.64e-07 | 0.0100 | True |
| KH | 4.20e-09 | 0.0100 | True |
| LA | 5.92e-09 | 0.0136 | True |
| MM | 1.64e-08 | 0.0100 | True |
| MY | 1.78e-07 | 0.0100 | True |
| PH | 6.61e-08 | 0.0100 | True |
| SG | 7.09e-09 | 0.0277 | True |
| TH | 9.41e-08 | 0.0199 | True |
| TL | 4.87e-10 | 0.0100 | True |
| VN | 4.30e-08 | 0.0176 | True |
| ASEAN | 3.54e-09 | 0.0330 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.8363922592213962e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 4.05e-10 | 1.53e-07 | 1.53e-07 | 3.66e-10 | 4.15e-11 | 0.0100 | True | True |
| ID | 7.38e-08 | 2.78e-06 | 2.85e-06 | 3.19e-08 | 2.16e-08 | 0.0100 | True | True |
| KH | 2.67e-09 | 4.08e-07 | 4.11e-07 | 1.08e-08 | 2.06e-09 | 0.0100 | True | True |
| LA | 3.01e-09 | 4.60e-07 | 4.63e-07 | 2.07e-08 | 2.73e-09 | 0.0136 | True | True |
| MM | 1.43e-09 | 1.11e-06 | 1.11e-06 | 2.25e-08 | 4.10e-09 | 0.0100 | True | True |
| MY | 1.63e-07 | 6.86e-07 | 8.49e-07 | 1.27e-08 | 8.18e-09 | 0.0100 | True | True |
| PH | 7.86e-08 | 5.01e-07 | 5.79e-07 | 3.80e-09 | 3.79e-09 | 0.0100 | True | True |
| SG | 1.11e-06 | 1.19e-07 | 1.23e-06 | 5.03e-10 | 1.97e-09 | 0.0277 | True | True |
| TH | 3.63e-07 | 6.39e-07 | 1.00e-06 | 2.02e-08 | 1.01e-08 | 0.0199 | True | True |
| TL | 6.68e-11 | 9.28e-08 | 9.28e-08 | 5.13e-10 | 5.63e-11 | 0.0100 | True | True |
| VN | 5.27e-08 | 6.90e-07 | 7.43e-07 | 1.43e-08 | 1.21e-08 | 0.0176 | True | True |
| ASEAN | 1.75e-06 | 4.80e-11 | 1.75e-06 | 0.00e+00 | 0.00e+00 | 0.0330 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 21 s。
