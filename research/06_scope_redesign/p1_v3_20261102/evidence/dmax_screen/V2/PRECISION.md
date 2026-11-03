# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2`（no_new_xb，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 280846622930.2719；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2 minus /root/autodl-tmp/v3_screen_dmax/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 98 次，原始 2.783055500e+11，对偶 2.783055400e+11，差 -1e+04 EUR（相对 3.59e-08），原始残差 0.000462，对偶残差 0.000523，互补 0.0018，1251 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 108 次，原始 2.783055440e+11，对偶 2.783055420e+11，差 -2000 EUR（相对 7.19e-09），原始残差 0.00715，对偶残差 0.000171，互补 0.000438，1387 s
- 最后一次迭代：第 111 次，原始 2.783055440e+11，对偶 2.783055420e+11，差 -2000 EUR（相对 7.19e-09），原始残差 0.004，对偶残差 0.000109，互补 0.000285，1429 s
- 返回数组的 KKT 摘要：原始 280846622930.3493，对偶 280846621323.27924，差 -0.000002 bn，相对 5.72e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,277,022，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01609，最大为预算 0.03426 倍；一阶影响合计 34 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 7.62e-11 | 0.0100 | True |
| ID | 1.93e-08 | 0.0100 | True |
| KH | 1.10e-09 | 0.0100 | True |
| LA | 1.51e-10 | 0.0100 | True |
| MM | 3.95e-10 | 0.0100 | True |
| MY | 5.88e-10 | 0.0317 | True |
| PH | 2.14e-09 | 0.0100 | True |
| SG | 2.49e-10 | 0.0392 | True |
| TH | 2.40e-09 | 0.0108 | True |
| TL | 6.75e-11 | 0.0100 | True |
| VN | 7.64e-09 | 0.0450 | True |
| ASEAN | 4.81e-10 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.755688400932451e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.95e-11 | 2.89e-08 | 2.89e-08 | 0.00e+00 | 1.74e-09 | 0.0100 | True | True |
| ID | 9.57e-09 | 5.94e-07 | 6.03e-07 | 7.41e-09 | 6.34e-08 | 0.0100 | True | True |
| KH | 3.95e-10 | 7.89e-08 | 7.93e-08 | 1.73e-09 | 1.55e-08 | 0.0100 | True | True |
| LA | 2.13e-10 | 7.72e-08 | 7.75e-08 | 2.13e-09 | 1.33e-08 | 0.0100 | True | True |
| MM | 4.04e-10 | 2.66e-07 | 2.66e-07 | 5.30e-09 | 1.12e-08 | 0.0100 | True | True |
| MY | 1.34e-08 | 1.21e-07 | 1.34e-07 | 1.49e-09 | 3.07e-08 | 0.0317 | True | True |
| PH | 8.40e-09 | 1.07e-07 | 1.16e-07 | 1.01e-09 | 1.55e-08 | 0.0100 | True | True |
| SG | 1.66e-07 | 1.92e-08 | 1.85e-07 | 2.60e-11 | 6.97e-09 | 0.0392 | True | True |
| TH | 4.14e-08 | 1.08e-07 | 1.49e-07 | 1.41e-09 | 3.00e-08 | 0.0108 | True | True |
| TL | 4.57e-11 | 1.97e-08 | 1.97e-08 | 0.00e+00 | 1.26e-09 | 0.0100 | True | True |
| VN | 6.66e-09 | 1.33e-07 | 1.39e-07 | 2.29e-09 | 2.92e-08 | 0.0450 | True | True |
| ASEAN | 2.30e-07 | 7.24e-13 | 2.30e-07 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 72 s。
