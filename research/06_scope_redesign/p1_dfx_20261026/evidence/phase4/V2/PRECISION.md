# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/dfx_v8/runs/dfx/V2`（disconnected，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 285400557542.6173；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/dfx_v8/runs/dfx/V2 minus /root/autodl-tmp/dfx_v8/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B15, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 117 次，原始 2.828843420e+11，对偶 2.828848230e+11，差 4.81e+05 EUR（相对 1.70e-06），原始残差 0.823，对偶残差 4.16e-05，互补 0.27，964 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 116 次，原始 2.828843420e+11，对偶 2.828848230e+11，差 4.81e+05 EUR（相对 1.70e-06），原始残差 0.976，对偶残差 4.16e-05，互补 0.27，955 s
- 最后一次迭代：第 127 次，原始 2.828842350e+11，对偶 2.828846760e+11，差 4.41e+05 EUR（相对 1.56e-06），原始残差 2.45，对偶残差 3.78e-05，互补 0.245，1049 s
- 返回数组的 KKT 摘要：原始 285400557542.8377，对偶 285399591221.2009，差 -0.000966 bn，相对 3.39e-06 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,238,188，超预算 476（与 `l23_violation_analysis.py` 一致：True），最大违反 3.281，最大为预算 17.87 倍；一阶影响合计 19,310 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 6.61e-07 | 0.0100 | True |
| ID | 6.17e-06 | 0.0100 | True |
| KH | 1.10e-06 | 0.0100 | True |
| LA | 8.59e-07 | 0.0125 | True |
| MM | 9.79e-07 | 0.0100 | True |
| MY | 3.25e-06 | 0.0291 | True |
| PH | 8.71e-07 | 0.0100 | True |
| SG | 4.93e-07 | 0.0384 | True |
| TH | 6.11e-07 | 0.0183 | True |
| TL | 7.74e-08 | 0.0100 | True |
| VN | 2.07e-06 | 0.0357 | True |
| ASEAN | 2.14e-06 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 3 / 476；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.5073512869393708e-07（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.75e-08 | 2.02e-05 | 2.03e-05 | 0.00e+00 | 3.65e-08 | 0.0100 | True | True |
| ID | 1.03e-04 | 5.56e-04 | 6.58e-04 | 7.53e-06 | 4.48e-06 | 0.0100 | True | True |
| KH | 3.97e-06 | 6.70e-05 | 7.10e-05 | 1.80e-06 | 5.82e-07 | 0.0100 | True | True |
| LA | 4.03e-06 | 6.42e-05 | 6.82e-05 | 2.28e-06 | 1.11e-06 | 0.0125 | True | True |
| MM | 8.27e-06 | 2.34e-04 | 2.43e-04 | 5.29e-06 | 1.54e-06 | 0.0100 | True | True |
| MY | 2.00e-05 | 1.05e-04 | 1.24e-04 | 1.53e-06 | 5.50e-07 | 0.0291 | True | True |
| PH | 1.29e-05 | 9.51e-05 | 1.08e-04 | 1.21e-06 | 6.99e-07 | 0.0100 | True | True |
| SG | 2.58e-06 | 1.10e-05 | 1.36e-05 | 0.00e+00 | 2.26e-08 | 0.0384 | True | True |
| TH | 5.60e-05 | 9.30e-05 | 1.49e-04 | 1.41e-06 | 7.10e-07 | 0.0183 | True | True |
| TL | 2.01e-07 | 1.03e-05 | 1.05e-05 | 0.00e+00 | 1.47e-07 | 0.0100 | True | True |
| VN | 4.32e-05 | 1.22e-04 | 1.65e-04 | 2.69e-06 | 9.93e-07 | 0.0357 | True | True |
| ASEAN | 2.87e-05 | 6.55e-05 | 9.42e-05 | 0.00e+00 | 8.51e-06 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 66 s。
