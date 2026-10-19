# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`results_project/s4o/s4o3/solves/s4o_integrated`（integrated，SMOKE_TEST_ONLY，档案 pypsa_eur_default）；终止 `optimal`；目标 648395012280.1625；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：False**（optimal True，(a) False，(b) True，(c) True）
- 分级：**not_layer1**（按电价结算：provisional）
- 分国容差参照：L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, B12

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 55 次，原始 6.455089400e+11，对偶 6.454858320e+11，差 -2.311e+07 EUR（相对 3.58e-05），原始残差 0.00206，对偶残差 0.00012，互补 27.9，75 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 58 次，原始 6.455082850e+11，对偶 6.454879360e+11，差 -2.035e+07 EUR（相对 3.15e-05），原始残差 0.0067，对偶残差 9.08e-05，互补 24.6，78 s
- 最后一次迭代：第 58 次，原始 6.455082850e+11，对偶 6.454879360e+11，差 -2.035e+07 EUR（相对 3.15e-05），原始残差 0.0067，对偶残差 9.08e-05，互补 24.6，78 s
- 返回数组的 KKT 摘要：原始 648395012279.9258，对偶 648376941199.4479，差 -0.018071 bn，相对 2.79e-05 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**False**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 184,312，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.0009757，最大为预算 0.8905 倍；一阶影响合计 679 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.56e-09 | 0.0100 | True |
| ID | 5.33e-08 | 0.0100 | True |
| KH | 6.25e-09 | 0.0243 | True |
| LA | 1.55e-08 | 0.0274 | True |
| MM | 5.96e-08 | 0.0113 | True |
| MY | 6.04e-09 | 0.0321 | True |
| PH | 5.35e-09 | 0.0100 | True |
| SG | 7.04e-10 | 0.0100 | True |
| TH | 8.66e-09 | 0.0751 | True |
| TL | 1.58e-09 | 0.0100 | True |
| VN | 4.25e-08 | 0.5132 | True |
| ASEAN | 4.78e-07 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.3874949341220715e-08（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.27e-08 | 3.15e-04 | 3.15e-04 | 1.91e-06 | 1.50e-06 | 0.0100 | True | True |
| ID | 6.25e-06 | 6.98e-03 | 6.98e-03 | 1.37e-04 | 7.99e-05 | 0.0100 | True | True |
| KH | 3.27e-07 | 1.07e-03 | 1.07e-03 | 4.80e-05 | 1.37e-05 | 0.0243 | True | True |
| LA | 3.29e-07 | 1.28e-03 | 1.28e-03 | 8.41e-05 | 2.14e-05 | 0.0274 | True | True |
| MM | 2.04e-07 | 2.50e-03 | 2.50e-03 | 8.62e-05 | 2.56e-05 | 0.0113 | True | True |
| MY | 1.63e-06 | 2.17e-03 | 2.17e-03 | 5.18e-05 | 3.10e-05 | 0.0321 | True | True |
| PH | 1.18e-06 | 1.35e-03 | 1.35e-03 | 1.71e-05 | 1.05e-05 | 0.0100 | True | True |
| SG | 5.10e-07 | 1.85e-04 | 1.85e-04 | 2.02e-06 | 3.33e-06 | 0.0100 | True | True |
| TH | 1.30e-06 | 1.67e-03 | 1.67e-03 | 7.92e-05 | 3.76e-05 | 0.0751 | True | True |
| TL | 6.92e-09 | 2.33e-04 | 2.33e-04 | 1.89e-06 | 1.37e-06 | 0.0100 | True | True |
| VN | 1.73e-06 | 1.88e-03 | 1.88e-03 | 6.94e-05 | 5.71e-05 | 0.5132 | True | True |
| ASEAN | 2.79e-07 | 7.73e-04 | 7.73e-04 | 0.00e+00 | 8.28e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
