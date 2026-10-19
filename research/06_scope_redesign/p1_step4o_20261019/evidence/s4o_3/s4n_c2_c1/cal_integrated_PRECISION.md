# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4o_tmp/c2_c1/cal_integrated`（integrated，SMOKE_TEST_ONLY，档案 pypsa_eur_default）；终止 `optimal`；目标 648385210748.3729；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B12

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 58 次，原始 6.455134730e+11，对偶 6.454844320e+11，差 -2.904e+07 EUR（相对 4.50e-05），原始残差 0.000282，对偶残差 0.000145，互补 35.2，85 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 65 次，原始 6.454984830e+11，对偶 6.454928240e+11，差 -5.659e+06 EUR（相对 8.77e-06），原始残差 0.0944，对偶残差 0.000129，互补 6.85，93 s
- 最后一次迭代：第 65 次，原始 6.454984830e+11，对偶 6.454928240e+11，差 -5.659e+06 EUR（相对 8.77e-06），原始残差 0.0944，对偶残差 0.000129，互补 6.85，93 s
- 返回数组的 KKT 摘要：原始 648385210748.1354，对偶 648380125881.0222，差 -0.005085 bn，相对 7.84e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 184,283，超预算 4（与 `l23_violation_analysis.py` 一致：True），最大违反 0.02302，最大为预算 7.861 倍；一阶影响合计 5,902 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 9.50e-09 | 0.0100 | True |
| ID | 6.94e-07 | 0.0100 | True |
| KH | 4.76e-08 | 0.0243 | True |
| LA | 6.21e-08 | 0.0274 | True |
| MM | 2.74e-07 | 0.0113 | True |
| MY | 7.34e-08 | 0.0321 | True |
| PH | 5.47e-08 | 0.0100 | True |
| SG | 5.08e-09 | 0.0100 | True |
| TH | 9.22e-08 | 0.0751 | True |
| TL | 5.97e-09 | 0.0100 | True |
| VN | 8.28e-08 | 0.5132 | True |
| ASEAN | 4.50e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 4；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.4771033652143345e-09（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.67e-08 | 8.62e-05 | 8.62e-05 | 5.02e-07 | 4.02e-07 | 0.0100 | True | True |
| ID | 3.25e-06 | 2.05e-03 | 2.05e-03 | 3.60e-05 | 2.09e-05 | 0.0100 | True | True |
| KH | 1.95e-07 | 3.09e-04 | 3.10e-04 | 1.31e-05 | 3.86e-06 | 0.0243 | True | True |
| LA | 1.68e-07 | 3.58e-04 | 3.58e-04 | 2.31e-05 | 5.96e-06 | 0.0274 | True | True |
| MM | 1.08e-07 | 7.34e-04 | 7.34e-04 | 2.38e-05 | 6.89e-06 | 0.0113 | True | True |
| MY | 8.41e-07 | 4.73e-04 | 4.74e-04 | 1.32e-05 | 8.39e-06 | 0.0321 | True | True |
| PH | 6.05e-07 | 3.80e-04 | 3.81e-04 | 5.32e-06 | 2.90e-06 | 0.0100 | True | True |
| SG | 3.11e-07 | 5.46e-05 | 5.49e-05 | 5.19e-07 | 8.54e-07 | 0.0100 | True | True |
| TH | 6.82e-07 | 4.57e-04 | 4.57e-04 | 2.06e-05 | 9.31e-06 | 0.0751 | True | True |
| TL | 3.56e-09 | 6.85e-05 | 6.85e-05 | 4.77e-07 | 3.69e-07 | 0.0100 | True | True |
| VN | 8.92e-07 | 5.22e-04 | 5.23e-04 | 1.88e-05 | 1.50e-05 | 0.5132 | True | True |
| ASEAN | 1.43e-07 | 2.31e-04 | 2.31e-04 | 0.00e+00 | 2.79e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
