# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/no_new_xb`（no_new_xb，SMOKE_TEST_ONLY，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 342268691464.4567；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/no_new_xb minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/smoke_hpc/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 59 次，原始 3.397278240e+11，对偶 3.397275630e+11，差 -2.61e+05 EUR（相对 7.68e-07），原始残差 0.00677，对偶残差 0.11，互补 0.394，101 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 66 次，原始 3.397276120e+11，对偶 3.397276120e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0135，对偶残差 0.124，互补 0.00767，111 s
- 最后一次迭代：第 66 次，原始 3.397276120e+11，对偶 3.397276120e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0135，对偶残差 0.124，互补 0.00767，111 s
- 返回数组的 KKT 摘要：原始 342268691464.3869，对偶 342268692086.959，差 0.000001 bn，相对 1.82e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 204,578，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.2161，最大为预算 0.00924 倍；一阶影响合计 745 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.35e-08 | 0.0100 | True |
| ID | 4.38e-07 | 0.0100 | True |
| KH | 8.77e-10 | 0.0100 | True |
| LA | 3.36e-09 | 0.0136 | True |
| MM | 3.51e-09 | 0.0100 | True |
| MY | 8.16e-08 | 0.0100 | True |
| PH | 1.02e-09 | 0.0100 | True |
| SG | 5.60e-09 | 0.0277 | True |
| TH | 2.54e-08 | 0.0199 | True |
| TL | 1.85e-10 | 0.0100 | True |
| VN | 1.72e-07 | 0.0176 | True |
| ASEAN | 2.09e-09 | 0.0330 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.0400410698169561e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.97e-08 | 1.06e-07 | 1.26e-07 | 0.00e+00 | 1.48e-10 | 0.0100 | True | True |
| ID | 1.34e-06 | 2.21e-06 | 3.55e-06 | 3.00e-08 | 4.03e-08 | 0.0100 | True | True |
| KH | 4.05e-08 | 2.96e-07 | 3.36e-07 | 6.87e-09 | 2.18e-08 | 0.0100 | True | True |
| LA | 6.83e-09 | 2.92e-07 | 2.99e-07 | 8.79e-09 | 3.41e-08 | 0.0136 | True | True |
| MM | 1.48e-08 | 9.58e-07 | 9.73e-07 | 1.90e-08 | 7.77e-09 | 0.0100 | True | True |
| MY | 8.21e-06 | 5.49e-07 | 8.76e-06 | 6.35e-09 | 2.81e-08 | 0.0100 | True | True |
| PH | 4.91e-06 | 4.22e-07 | 5.34e-06 | 4.05e-09 | 6.02e-09 | 0.0100 | True | True |
| SG | 9.07e-05 | 8.48e-08 | 9.08e-05 | 3.50e-11 | 1.38e-08 | 0.0277 | True | True |
| TH | 2.17e-05 | 4.14e-07 | 2.21e-05 | 6.87e-09 | 4.50e-08 | 0.0199 | True | True |
| TL | 2.24e-10 | 7.28e-08 | 7.30e-08 | 0.00e+00 | 5.97e-11 | 0.0100 | True | True |
| VN | 1.96e-06 | 5.18e-07 | 2.48e-06 | 1.10e-08 | 2.84e-08 | 0.0176 | True | True |
| ASEAN | 1.29e-04 | 3.70e-13 | 1.29e-04 | 0.00e+00 | 0.00e+00 | 0.0330 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 19 s。
