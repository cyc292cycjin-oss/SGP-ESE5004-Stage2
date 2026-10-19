# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnected_gap`（disconnected，GAP_DIAGNOSTIC，档案 formal_barrier）；终止 `suboptimal`；目标 585497545941.4175；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：False**（optimal False，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnected minus /root/autodl-tmp/s4n_pilot/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 False）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B12, B14, B15, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 103 次，原始 5.824397920e+11，对偶 5.824375750e+11，差 -2.217e+06 EUR（相对 3.81e-06），原始残差 2.08，对偶残差 0.000106，互补 0.526，832 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 222 次，原始 5.824414370e+11，对偶 5.824394700e+11，差 -1.967e+06 EUR（相对 3.38e-06），原始残差 0.196，对偶残差 0.000414，互补 1.2，1723 s
- 最后一次迭代：第 245 次，原始 5.824394520e+11，对偶 5.824385410e+11，差 -9.11e+05 EUR（相对 1.56e-06），原始残差 24，对偶残差 0.0104，互补 0.528，1920 s
- 重启后原始残差最小的迭代：第 222 次，原始 5.824414370e+11，对偶 5.824394700e+11，差 -1.967e+06 EUR（相对 3.38e-06），原始残差 0.196，对偶残差 0.000414，互补 1.2，1723 s
- 重启：第 124 次（1013 s）
- 返回数组的 KKT 摘要：原始 585497545941.2672，对偶 585493628966.8247，差 -0.003917 bn，相对 6.69e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,128,607，超预算 5（与 `l23_violation_analysis.py` 一致：True），最大违反 0.3384，最大为预算 7.443 倍；一阶影响合计 5,171 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.05e-07 | 0.0100 | True |
| ID | 1.61e-06 | 0.0100 | True |
| KH | 2.30e-07 | 0.0243 | True |
| LA | 1.88e-07 | 0.0274 | True |
| MM | 2.80e-07 | 0.0113 | True |
| MY | 3.33e-07 | 0.0321 | True |
| PH | 2.10e-07 | 0.0100 | True |
| SG | 5.30e-08 | 0.0100 | True |
| TH | 1.91e-07 | 0.0751 | True |
| TL | 8.12e-08 | 0.0100 | True |
| VN | 7.39e-07 | 0.5159 | True |
| ASEAN | 1.11e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 1 / 5；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.816415350591477e-07（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.76e-06 | 7.15e-05 | 7.32e-05 | 0.00e+00 | 3.47e-07 | 0.0100 | True | True |
| ID | 2.38e-04 | 1.96e-03 | 2.20e-03 | 3.55e-05 | 1.81e-05 | 0.0100 | True | True |
| KH | 2.97e-05 | 2.69e-04 | 2.99e-04 | 7.81e-06 | 5.47e-06 | 0.0243 | True | True |
| LA | 1.50e-05 | 2.72e-04 | 2.87e-04 | 1.01e-05 | 6.33e-06 | 0.0274 | True | True |
| MM | 4.70e-05 | 8.51e-04 | 8.98e-04 | 2.37e-05 | 1.17e-05 | 0.0113 | True | True |
| MY | 6.62e-05 | 3.89e-04 | 4.56e-04 | 6.99e-06 | 2.27e-06 | 0.0321 | True | True |
| PH | 4.07e-05 | 3.75e-04 | 4.16e-04 | 5.45e-06 | 4.25e-06 | 0.0100 | True | True |
| SG | 6.85e-06 | 3.82e-05 | 4.50e-05 | 0.00e+00 | 3.38e-07 | 0.0100 | True | True |
| TH | 1.65e-04 | 3.62e-04 | 5.27e-04 | 7.08e-06 | 5.25e-06 | 0.0751 | True | True |
| TL | 1.20e-06 | 6.08e-05 | 6.20e-05 | 0.00e+00 | 7.43e-07 | 0.0100 | True | True |
| VN | 1.37e-04 | 4.71e-04 | 6.08e-04 | 1.27e-05 | 7.79e-06 | 0.5159 | True | True |
| ASEAN | 1.18e-04 | 2.65e-04 | 3.83e-04 | 0.00e+00 | 4.02e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 52 s。
