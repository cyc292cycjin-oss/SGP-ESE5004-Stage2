# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/disconnected`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 698979559990.2317；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/disconnected minus /home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B14, B2, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 149 次，原始 6.959234510e+11，对偶 6.959234490e+11，差 -2000 EUR（相对 2.87e-09），原始残差 0.0214，对偶残差 2.05e-05，互补 0.00473，183 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 149 次，原始 6.959234510e+11，对偶 6.959234490e+11，差 -2000 EUR（相对 2.87e-09），原始残差 0.0214，对偶残差 2.05e-05，互补 0.00473，183 s
- 最后一次迭代：第 149 次，原始 6.959234510e+11，对偶 6.959234490e+11，差 -2000 EUR（相对 2.87e-09），原始残差 0.0214，对偶残差 2.05e-05，互补 0.00473，183 s
- 返回数组的 KKT 摘要：原始 698979559990.0227，对偶 698979557860.0247，差 -0.000002 bn，相对 3.05e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 216,558，超预算 1（与 `l23_violation_analysis.py` 一致：True），最大违反 0.3438，最大为预算 3.033 倍；一阶影响合计 3,237 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.75e-08 | 0.0100 | True |
| ID | 9.68e-07 | 0.0702 | True |
| KH | 5.69e-08 | 0.0188 | True |
| LA | 1.24e-07 | 0.0276 | True |
| MM | 9.77e-07 | 0.0100 | True |
| MY | 1.28e-07 | 0.0408 | True |
| PH | 3.40e-07 | 0.0177 | True |
| SG | 1.21e-08 | 0.0202 | True |
| TH | 8.14e-08 | 0.0615 | True |
| TL | 1.24e-08 | 0.0100 | True |
| VN | 1.52e-07 | 0.2496 | True |
| ASEAN | 3.60e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 1；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.326483793899077e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 8.25e-11 | 4.91e-08 | 4.92e-08 | 0.00e+00 | 1.34e-10 | 0.0100 | True | True |
| ID | 3.58e-08 | 1.25e-06 | 1.29e-06 | 1.03e-08 | 1.20e-08 | 0.0702 | True | True |
| KH | 1.50e-09 | 1.75e-07 | 1.77e-07 | 2.71e-09 | 1.25e-09 | 0.0188 | True | True |
| LA | 1.54e-09 | 1.87e-07 | 1.89e-07 | 5.21e-09 | 9.23e-10 | 0.0276 | True | True |
| MM | 1.80e-09 | 6.07e-07 | 6.09e-07 | 7.97e-09 | 1.58e-09 | 0.0100 | True | True |
| MY | 7.51e-09 | 2.32e-07 | 2.39e-07 | 2.17e-09 | 3.38e-09 | 0.0408 | True | True |
| PH | 9.00e-09 | 2.75e-07 | 2.84e-07 | 2.81e-09 | 3.62e-09 | 0.0177 | True | True |
| SG | 1.30e-09 | 2.31e-08 | 2.44e-08 | 0.00e+00 | 3.91e-10 | 0.0202 | True | True |
| TH | 1.56e-08 | 2.38e-07 | 2.54e-07 | 2.62e-09 | 4.65e-09 | 0.0615 | True | True |
| TL | 1.19e-11 | 5.36e-08 | 5.36e-08 | 0.00e+00 | 2.23e-12 | 0.0100 | True | True |
| VN | 2.56e-08 | 2.70e-07 | 2.95e-07 | 6.03e-09 | 6.48e-09 | 0.2496 | True | True |
| ASEAN | 2.66e-09 | 2.46e-07 | 2.48e-07 | 0.00e+00 | 2.24e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 12 s。
