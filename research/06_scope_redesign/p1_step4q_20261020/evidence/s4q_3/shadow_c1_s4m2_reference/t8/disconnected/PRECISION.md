# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/disconnected`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier_1e6）；终止 `optimal`；目标 698979559682.4272；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：S4M-2 56x3h profile A (Threads 8): disconnected - integrated ledger difference (s4m_A_disconnected minus s4m_A_integrated, COUNTRY_COST_LEDGER.csv total) - S4Q-3 fixed reference of the C1 (b)(c) per-country tolerance
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）；this batch: disconnected - integrated ledger difference (/ho… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 135 次，原始 6.959234560e+11，对偶 6.959234570e+11，差 1000 EUR（相对 1.44e-09），原始残差 0.0412，对偶残差 6.99e-05，互补 0.0169，169 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 141 次，原始 6.959234510e+11，对偶 6.959234500e+11，差 -1000 EUR（相对 1.44e-09），原始残差 0.0465，对偶残差 8.75e-05，互补 0.00344，177 s
- 最后一次迭代：第 142 次，原始 6.959234510e+11，对偶 6.959234500e+11，差 -1000 EUR（相对 1.44e-09），原始残差 0.0463，对偶残差 8.73e-05，互补 0.00343，178 s
- 返回数组的 KKT 摘要：原始 698979559682.2206，对偶 698979557996.4209，差 -0.000002 bn，相对 2.41e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 208,174，超预算 1（与 `l23_violation_analysis.py` 一致：True），最大违反 0.7422，最大为预算 1.295 倍；一阶影响合计 2,211 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 9.08e-09 | 0.0100 | True |
| ID | 6.94e-07 | 0.0702 | True |
| KH | 3.09e-08 | 0.0188 | True |
| LA | 8.93e-08 | 0.0276 | True |
| MM | 3.80e-07 | 0.0100 | True |
| MY | 5.44e-08 | 0.0408 | True |
| PH | 1.55e-07 | 0.0177 | True |
| SG | 5.20e-09 | 0.0202 | True |
| TH | 5.50e-08 | 0.0615 | True |
| TL | 7.14e-09 | 0.0100 | True |
| VN | 5.33e-07 | 0.2496 | True |
| ASEAN | 1.98e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 1；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 5.445665239675456e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.47e-11 | 3.52e-08 | 3.52e-08 | 0.00e+00 | 1.38e-10 | 0.0100 | True | True |
| ID | 9.15e-08 | 9.40e-07 | 1.03e-06 | 9.53e-09 | 1.06e-08 | 0.0702 | True | True |
| KH | 3.49e-09 | 1.30e-07 | 1.33e-07 | 2.40e-09 | 1.40e-09 | 0.0188 | True | True |
| LA | 3.87e-09 | 1.41e-07 | 1.44e-07 | 4.15e-09 | 8.11e-10 | 0.0276 | True | True |
| MM | 3.50e-09 | 4.08e-07 | 4.12e-07 | 7.20e-09 | 1.54e-09 | 0.0100 | True | True |
| MY | 1.86e-08 | 1.70e-07 | 1.89e-07 | 1.85e-09 | 3.01e-09 | 0.0408 | True | True |
| PH | 2.30e-08 | 2.06e-07 | 2.29e-07 | 2.06e-09 | 3.01e-09 | 0.0177 | True | True |
| SG | 3.37e-09 | 1.69e-08 | 2.02e-08 | 0.00e+00 | 2.84e-10 | 0.0202 | True | True |
| TH | 4.16e-08 | 1.63e-07 | 2.04e-07 | 2.03e-09 | 3.80e-09 | 0.0615 | True | True |
| TL | 3.32e-13 | 3.45e-08 | 3.45e-08 | 0.00e+00 | 6.22e-13 | 0.0100 | True | True |
| VN | 7.10e-08 | 2.45e-07 | 3.16e-07 | 4.29e-09 | 5.26e-09 | 0.2496 | True | True |
| ASEAN | 7.16e-09 | 1.78e-07 | 1.86e-07 | 0.00e+00 | 2.10e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 13 s。
