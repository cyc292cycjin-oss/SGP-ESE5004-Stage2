# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4o_local/pkg_e2e/runs/20261019T133528Z_584/integrated`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 648381181410.4515；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY.json ledger_difference.total_bn_eur; SCREENING_UNVERIFIED runs, decision 112 a) - used until the batch has both STEPS runs
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A3, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 128 次，原始 6.454944550e+11，对偶 6.454944540e+11，差 -1000 EUR（相对 1.55e-09），原始残差 0.00509，对偶残差 1.62e-05，互补 0.00143，197 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 132 次，原始 6.454944540e+11，对偶 6.454944540e+11，差 0 EUR（相对 0.00e+00），原始残差 0.177，对偶残差 8.43e-05，互补 0.00104，203 s
- 最后一次迭代：第 141 次，原始 6.454944540e+11，对偶 6.454944540e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00648，对偶残差 6.03e-05，互补 2.88e-05，217 s
- 返回数组的 KKT 摘要：原始 648381181410.2358，对偶 648381181398.0205，差 -0.000000 bn，相对 1.88e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 200,361，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.009727，最大为预算 0.1142 倍；一阶影响合计 349 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.99e-10 | 0.0100 | True |
| ID | 2.04e-08 | 0.0100 | True |
| KH | 6.57e-08 | 0.0243 | True |
| LA | 2.40e-08 | 0.0274 | True |
| MM | 3.49e-08 | 0.0113 | True |
| MY | 2.99e-08 | 0.0321 | True |
| PH | 5.09e-08 | 0.0100 | True |
| SG | 2.93e-09 | 0.0100 | True |
| TH | 8.42e-08 | 0.0751 | True |
| TL | 1.76e-10 | 0.0100 | True |
| VN | 2.06e-08 | 0.5132 | True |
| ASEAN | 2.92e-08 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.3455277671308185e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 5.66e-12 | 4.12e-10 | 4.18e-10 | 1.02e-13 | 1.17e-12 | 0.0100 | True | True |
| ID | 1.56e-09 | 1.24e-08 | 1.40e-08 | 5.71e-11 | 4.68e-11 | 0.0100 | True | True |
| KH | 4.98e-11 | 3.62e-09 | 3.67e-09 | 2.04e-11 | 8.06e-12 | 0.0243 | True | True |
| LA | 1.61e-10 | 1.32e-08 | 1.34e-08 | 4.11e-11 | 7.90e-12 | 0.0274 | True | True |
| MM | 3.70e-11 | 2.38e-08 | 2.39e-08 | 5.79e-11 | 1.58e-11 | 0.0113 | True | True |
| MY | 3.22e-10 | 3.83e-09 | 4.16e-09 | 1.71e-11 | 1.33e-11 | 0.0321 | True | True |
| PH | 1.81e-10 | 2.64e-08 | 2.66e-08 | 2.25e-11 | 1.10e-11 | 0.0100 | True | True |
| SG | 5.92e-11 | 2.38e-09 | 2.44e-09 | 3.60e-13 | 1.45e-12 | 0.0100 | True | True |
| TH | 8.53e-09 | 4.38e-09 | 1.29e-08 | 2.10e-11 | 1.26e-11 | 0.0751 | True | True |
| TL | 2.55e-12 | 4.08e-10 | 4.11e-10 | 1.03e-12 | 2.10e-12 | 0.0100 | True | True |
| VN | 8.12e-10 | 3.95e-09 | 4.76e-09 | 4.50e-11 | 1.40e-11 | 0.5132 | True | True |
| ASEAN | 7.23e-10 | 1.34e-08 | 1.42e-08 | 0.00e+00 | 2.21e-12 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
