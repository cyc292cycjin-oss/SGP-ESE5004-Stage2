# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4o_tmp/c2_c1/cal_integrated_nze`（integrated，SMOKE_TEST_ONLY，档案 pypsa_eur_default）；终止 `optimal`；目标 547962131395.837；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 57 次，原始 5.450911530e+11，对偶 5.450618480e+11，差 -2.93e+07 EUR（相对 5.38e-05），原始残差 0.00194，对偶残差 0.000185，互补 35.6，82 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 64 次，原始 5.450754040e+11，对偶 5.450717030e+11，差 -3.701e+06 EUR（相对 6.79e-06），原始残差 0.0949，对偶残差 5.74e-05，互补 4.51，91 s
- 最后一次迭代：第 64 次，原始 5.450754040e+11，对偶 5.450717030e+11，差 -3.701e+06 EUR（相对 6.79e-06），原始残差 0.0949，对偶残差 5.74e-05，互补 4.51，91 s
- 返回数组的 KKT 摘要：原始 547962131395.7808，对偶 547959109548.9069，差 -0.003022 bn，相对 5.51e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 184,487，超预算 4（与 `l23_violation_analysis.py` 一致：True），最大违反 0.421，最大为预算 6.176 倍；一阶影响合计 4,356 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 6.17e-08 | 0.0100 | True |
| ID | 6.14e-07 | 0.0100 | True |
| KH | 3.40e-08 | 0.0243 | True |
| LA | 3.81e-08 | 0.0274 | True |
| MM | 5.69e-07 | 0.0113 | True |
| MY | 6.17e-08 | 0.0321 | True |
| PH | 3.85e-08 | 0.0100 | True |
| SG | 8.18e-09 | 0.0100 | True |
| TH | 7.84e-08 | 0.0751 | True |
| TL | 1.16e-08 | 0.0100 | True |
| VN | 6.47e-08 | 0.5132 | True |
| ASEAN | 2.78e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 4；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.0300062256137308e-08（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.43e-08 | 6.04e-05 | 6.04e-05 | 5.19e-07 | 1.85e-07 | 0.0100 | True | True |
| ID | 4.68e-06 | 1.14e-03 | 1.14e-03 | 3.03e-05 | 1.41e-05 | 0.0100 | True | True |
| KH | 2.73e-07 | 1.96e-04 | 1.96e-04 | 1.14e-05 | 2.97e-06 | 0.0243 | True | True |
| LA | 2.30e-07 | 2.34e-04 | 2.34e-04 | 1.98e-05 | 4.59e-06 | 0.0274 | True | True |
| MM | 1.46e-07 | 4.23e-04 | 4.23e-04 | 1.85e-05 | 2.73e-06 | 0.0113 | True | True |
| MY | 1.21e-06 | 3.50e-04 | 3.52e-04 | 1.19e-05 | 6.96e-06 | 0.0321 | True | True |
| PH | 8.97e-07 | 2.17e-04 | 2.18e-04 | 2.78e-06 | 2.42e-06 | 0.0100 | True | True |
| SG | 3.31e-07 | 3.47e-05 | 3.50e-05 | 5.15e-07 | 5.80e-07 | 0.0100 | True | True |
| TH | 9.78e-07 | 2.94e-04 | 2.95e-04 | 1.93e-05 | 9.38e-06 | 0.0751 | True | True |
| TL | 5.14e-09 | 4.05e-05 | 4.05e-05 | 3.74e-07 | 1.31e-07 | 0.0100 | True | True |
| VN | 1.29e-06 | 3.06e-04 | 3.07e-04 | 1.54e-05 | 1.36e-05 | 0.5132 | True | True |
| ASEAN | 2.08e-07 | 1.15e-04 | 1.15e-04 | 0.00e+00 | 1.65e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
