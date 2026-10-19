# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4o_tmp/c2_c1/cal_disconnected`（disconnected，SMOKE_TEST_ONLY，档案 pypsa_eur_default）；终止 `optimal`；目标 698982530790.1426；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B12

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 59 次，原始 6.959375810e+11，对偶 6.959147040e+11，差 -2.288e+07 EUR（相对 3.29e-05），原始残差 0.00656，对偶残差 0.000114，互补 29.7，62 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 66 次，原始 6.959264220e+11，对偶 6.959214160e+11，差 -5.006e+06 EUR（相对 7.19e-06），原始残差 0.0977，对偶残差 0.00021，互补 6.46，69 s
- 最后一次迭代：第 66 次，原始 6.959264220e+11，对偶 6.959214160e+11，差 -5.006e+06 EUR（相对 7.19e-06），原始残差 0.0977，对偶残差 0.00021，互补 6.46，69 s
- 返回数组的 KKT 摘要：原始 698982530789.9171，对偶 698978333418.4656，差 -0.004197 bn，相对 6.00e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 181,424，超预算 23（与 `l23_violation_analysis.py` 一致：True），最大违反 0.06803，最大为预算 3.467 倍；一阶影响合计 5,642 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.49e-09 | 0.0100 | True |
| ID | 3.30e-07 | 0.0100 | True |
| KH | 2.71e-07 | 0.0243 | True |
| LA | 4.96e-07 | 0.0274 | True |
| MM | 1.26e-06 | 0.0113 | True |
| MY | 4.02e-08 | 0.0321 | True |
| PH | 4.63e-08 | 0.0100 | True |
| SG | 7.56e-09 | 0.0100 | True |
| TH | 2.28e-08 | 0.0751 | True |
| TL | 5.89e-09 | 0.0100 | True |
| VN | 3.77e-08 | 0.5132 | True |
| ASEAN | 3.12e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 23；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 5.797929227982274e-09（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.82e-09 | 6.77e-05 | 6.77e-05 | 0.00e+00 | 3.19e-07 | 0.0100 | True | True |
| ID | 3.11e-07 | 1.66e-03 | 1.66e-03 | 3.53e-05 | 1.87e-05 | 0.0100 | True | True |
| KH | 3.93e-09 | 2.18e-04 | 2.18e-04 | 7.10e-06 | 2.82e-06 | 0.0243 | True | True |
| LA | 8.75e-09 | 2.20e-04 | 2.20e-04 | 8.44e-06 | 3.19e-06 | 0.0274 | True | True |
| MM | 2.86e-08 | 6.16e-04 | 6.16e-04 | 2.00e-05 | 5.72e-06 | 0.0113 | True | True |
| MY | 1.10e-08 | 3.29e-04 | 3.29e-04 | 7.03e-06 | 2.46e-06 | 0.0321 | True | True |
| PH | 2.01e-09 | 3.26e-04 | 3.26e-04 | 4.10e-06 | 3.61e-06 | 0.0100 | True | True |
| SG | 4.78e-09 | 3.06e-05 | 3.06e-05 | 0.00e+00 | 2.98e-07 | 0.0100 | True | True |
| TH | 2.59e-08 | 2.88e-04 | 2.88e-04 | 6.46e-06 | 1.02e-05 | 0.0751 | True | True |
| TL | 1.70e-10 | 4.95e-05 | 4.95e-05 | 0.00e+00 | 3.27e-07 | 0.0100 | True | True |
| VN | 1.93e-08 | 3.94e-04 | 3.94e-04 | 1.06e-05 | 1.03e-05 | 0.5132 | True | True |
| ASEAN | 6.02e-09 | 1.96e-04 | 1.96e-04 | 0.00e+00 | 2.27e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 13 s。
