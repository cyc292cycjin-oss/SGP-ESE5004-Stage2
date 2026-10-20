# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/integrated`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 648381183628.2552；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：S4M-2 56x3h profile A (Threads 8): disconnected - integrated ledger difference (s4m_A_disconnected minus s4m_A_integrated, COUNTRY_COST_LEDGER.csv total) - S4Q-3 fixed reference of the C1 (b)(c) per-country tolerance
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）；this batch: disconnected - integrated ledger difference (/ho… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 68 次，原始 6.454948290e+11，对偶 6.454946690e+11，差 -1.6e+05 EUR（相对 2.48e-07），原始残差 0.0432，对偶残差 4e-05，互补 0.791，108 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 112 次，原始 6.454944560e+11，对偶 6.454944540e+11，差 -2000 EUR（相对 3.10e-09），原始残差 0.507，对偶残差 6.1e-05，互补 0.00388，171 s
- 最后一次迭代：第 112 次，原始 6.454944560e+11，对偶 6.454944540e+11，差 -2000 EUR（相对 3.10e-09），原始残差 0.507，对偶残差 6.1e-05，互补 0.00388，171 s
- 返回数组的 KKT 摘要：原始 648381183628.0332，对偶 648381181224.7736，差 -0.000002 bn，相对 3.71e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 198,035，超预算 9（与 `l23_violation_analysis.py` 一致：True），最大违反 6.89，最大为预算 7.698 倍；一阶影响合计 5,739 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 9.20e-09 | 0.0100 | True |
| ID | 6.77e-07 | 0.0702 | True |
| KH | 7.74e-08 | 0.0188 | True |
| LA | 6.90e-07 | 0.0276 | True |
| MM | 2.30e-06 | 0.0100 | True |
| MY | 2.75e-07 | 0.0408 | True |
| PH | 5.80e-07 | 0.0177 | True |
| SG | 1.23e-08 | 0.0202 | True |
| TH | 3.92e-07 | 0.0615 | True |
| TL | 7.91e-09 | 0.0100 | True |
| VN | 1.97e-07 | 0.2496 | True |
| ASEAN | 5.73e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 9；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.8019072474751203e-10（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.45e-10 | 5.21e-08 | 5.22e-08 | 1.86e-10 | 3.43e-10 | 0.0100 | True | True |
| ID | 9.57e-08 | 1.85e-06 | 1.94e-06 | 1.54e-08 | 1.48e-08 | 0.0702 | True | True |
| KH | 4.38e-09 | 2.16e-07 | 2.20e-07 | 4.93e-09 | 1.63e-09 | 0.0188 | True | True |
| LA | 4.45e-09 | 6.65e-07 | 6.69e-07 | 9.57e-09 | 2.13e-09 | 0.0276 | True | True |
| MM | 1.84e-09 | 6.99e-07 | 7.01e-07 | 1.08e-08 | 1.52e-09 | 0.0100 | True | True |
| MY | 2.30e-08 | 3.11e-07 | 3.34e-07 | 5.40e-09 | 6.22e-09 | 0.0408 | True | True |
| PH | 1.89e-08 | 3.70e-07 | 3.89e-07 | 2.67e-09 | 3.53e-09 | 0.0177 | True | True |
| SG | 6.46e-09 | 3.27e-08 | 3.92e-08 | 3.20e-10 | 6.38e-10 | 0.0202 | True | True |
| TH | 2.37e-08 | 3.65e-07 | 3.89e-07 | 7.98e-09 | 6.73e-09 | 0.0615 | True | True |
| TL | 7.87e-12 | 4.36e-08 | 4.36e-08 | 2.51e-10 | 3.50e-10 | 0.0100 | True | True |
| VN | 2.70e-08 | 3.32e-07 | 3.59e-07 | 7.99e-09 | 7.17e-09 | 0.2496 | True | True |
| ASEAN | 5.17e-09 | 1.54e-07 | 1.60e-07 | 0.00e+00 | 3.44e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
