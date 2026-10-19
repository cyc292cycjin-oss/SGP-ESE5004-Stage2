# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnected`（disconnected，FORMAL_TRIAL_365X24H，档案 formal_barrier）；终止 `suboptimal`；目标 585495017158.94；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：False**（optimal False，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnected minus /root/autodl-tmp/s4n_pilot/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 False）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B14, B15, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 111 次，原始 5.824405060e+11，对偶 5.824480460e+11，差 7.54e+06 EUR（相对 1.29e-05），原始残差 0.306，对偶残差 0.000186，互补 1.06，874 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 273 次，原始 5.824389090e+11，对偶 5.824456480e+11，差 6.739e+06 EUR（相对 1.16e-05），原始残差 1.85，对偶残差 0.0357，互补 0.507，2093 s
- 最后一次迭代：第 287 次，原始 5.824387890e+11，对偶 5.824447540e+11，差 5.965e+06 EUR（相对 1.02e-05），原始残差 9，对偶残差 0.0363，互补 0.451，2202 s
- 重启后原始残差最小的迭代：第 250 次，原始 5.824391050e+11，对偶 5.824473330e+11，差 8.228e+06 EUR（相对 1.41e-05），原始残差 0.783，对偶残差 0.0014，互补 0.679，1915 s
- 重启：第 126 次（1003 s）
- 返回数组的 KKT 摘要：原始 585495017158.8187，对偶 585495778659.6765，差 0.000762 bn，相对 1.30e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,153,092，超预算 821（与 `l23_violation_analysis.py` 一致：True），最大违反 7.407，最大为预算 12.18 倍；一阶影响合计 29,802 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 6.98e-07 | 0.0100 | True |
| ID | 5.75e-06 | 0.0100 | True |
| KH | 1.00e-06 | 0.0243 | True |
| LA | 7.73e-07 | 0.0274 | True |
| MM | 1.04e-06 | 0.0113 | True |
| MY | 7.03e-06 | 0.0321 | True |
| PH | 1.24e-06 | 0.0100 | True |
| SG | 6.92e-07 | 0.0100 | True |
| TH | 9.22e-07 | 0.0751 | True |
| TL | 2.93e-07 | 0.0100 | True |
| VN | 4.61e-06 | 0.5159 | True |
| ASEAN | 5.60e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 3 / 821；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 6.451861796672047e-07（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.20e-06 | 2.34e-05 | 2.66e-05 | 0.00e+00 | 4.66e-08 | 0.0100 | True | True |
| ID | 4.75e-04 | 7.43e-04 | 1.22e-03 | 1.64e-05 | 5.95e-06 | 0.0100 | True | True |
| KH | 5.81e-05 | 1.09e-04 | 1.67e-04 | 3.83e-06 | 2.53e-06 | 0.0243 | True | True |
| LA | 2.55e-05 | 1.03e-04 | 1.29e-04 | 4.27e-06 | 3.80e-06 | 0.0274 | True | True |
| MM | 8.94e-05 | 3.39e-04 | 4.29e-04 | 1.18e-05 | 4.83e-06 | 0.0113 | True | True |
| MY | 1.33e-04 | 1.38e-04 | 2.71e-04 | 2.76e-06 | 3.41e-07 | 0.0321 | True | True |
| PH | 7.79e-05 | 1.34e-04 | 2.12e-04 | 2.61e-06 | 1.89e-06 | 0.0100 | True | True |
| SG | 1.47e-05 | 1.38e-05 | 2.85e-05 | 0.00e+00 | 2.61e-08 | 0.0100 | True | True |
| TH | 3.50e-04 | 1.27e-04 | 4.77e-04 | 2.67e-06 | 1.69e-06 | 0.0751 | True | True |
| TL | 1.18e-06 | 2.38e-05 | 2.50e-05 | 0.00e+00 | 3.25e-07 | 0.0100 | True | True |
| VN | 2.75e-04 | 1.56e-04 | 4.31e-04 | 4.65e-06 | 2.78e-06 | 0.5159 | True | True |
| ASEAN | 2.48e-04 | 9.73e-05 | 3.46e-04 | 0.00e+00 | 1.55e-05 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 53 s。
