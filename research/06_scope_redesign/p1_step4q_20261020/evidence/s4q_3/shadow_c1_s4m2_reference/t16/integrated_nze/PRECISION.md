# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T004641Z_8849/integrated_nze`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 547960257359.3216；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：S4M-2 56x3h profile A (Threads 8): disconnected - integrated ledger difference (s4m_A_disconnected minus s4m_A_integrated, COUNTRY_COST_LEDGER.csv total) - S4Q-3 fixed reference of the C1 (b)(c) per-country tolerance
- 重评记录：this batch: disconnected - integrated ledger difference (/ho… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 142 次，原始 5.450735310e+11，对偶 5.450735280e+11，差 -3000 EUR（相对 5.50e-09），原始残差 0.0223，对偶残差 3.55e-05，互补 0.00572，220 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 143 次，原始 5.450735300e+11，对偶 5.450735280e+11，差 -2000 EUR（相对 3.67e-09），原始残差 0.0375，对偶残差 3.56e-05，互补 0.00504，221 s
- 最后一次迭代：第 147 次，原始 5.450735300e+11，对偶 5.450735280e+11，差 -2000 EUR（相对 3.67e-09），原始残差 0.0457，对偶残差 5.57e-05，互补 0.00386，227 s
- 返回数组的 KKT 摘要：原始 547960257359.2796，对偶 547960254979.3955，差 -0.000002 bn，相对 4.34e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 200,797，超预算 7（与 `l23_violation_analysis.py` 一致：True），最大违反 0.5758，最大为预算 1.985 倍；一阶影响合计 5,952 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.12e-08 | 0.0100 | True |
| ID | 8.73e-07 | 0.0702 | True |
| KH | 1.31e-07 | 0.0188 | True |
| LA | 9.61e-07 | 0.0276 | True |
| MM | 1.74e-06 | 0.0100 | True |
| MY | 4.04e-07 | 0.0408 | True |
| PH | 4.47e-07 | 0.0177 | True |
| SG | 2.41e-08 | 0.0202 | True |
| TH | 5.63e-07 | 0.0615 | True |
| TL | 1.85e-08 | 0.0100 | True |
| VN | 2.65e-07 | 0.2496 | True |
| ASEAN | 5.58e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 7；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.4918652345602393e-10（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.35e-10 | 5.16e-08 | 5.19e-08 | 1.27e-10 | 2.93e-10 | 0.0100 | True | True |
| ID | 6.93e-08 | 1.26e-06 | 1.33e-06 | 1.30e-08 | 1.54e-08 | 0.0702 | True | True |
| KH | 3.65e-09 | 2.01e-07 | 2.05e-07 | 4.30e-09 | 1.87e-09 | 0.0188 | True | True |
| LA | 3.59e-09 | 2.83e-07 | 2.87e-07 | 8.19e-09 | 1.91e-09 | 0.0276 | True | True |
| MM | 2.15e-09 | 7.96e-07 | 7.99e-07 | 9.02e-09 | 1.38e-09 | 0.0100 | True | True |
| MY | 1.76e-08 | 3.04e-07 | 3.21e-07 | 4.52e-09 | 6.60e-09 | 0.0408 | True | True |
| PH | 1.50e-08 | 2.59e-07 | 2.74e-07 | 2.71e-09 | 3.62e-09 | 0.0177 | True | True |
| SG | 5.35e-09 | 4.33e-08 | 4.86e-08 | 2.75e-10 | 6.17e-10 | 0.0202 | True | True |
| TH | 1.69e-08 | 3.12e-07 | 3.29e-07 | 6.34e-09 | 6.82e-09 | 0.0615 | True | True |
| TL | 7.28e-11 | 4.88e-08 | 4.89e-08 | 1.75e-10 | 2.84e-10 | 0.0100 | True | True |
| VN | 2.04e-08 | 4.04e-07 | 4.24e-07 | 7.39e-09 | 7.21e-09 | 0.2496 | True | True |
| ASEAN | 3.55e-09 | 1.76e-07 | 1.80e-07 | 0.00e+00 | 2.93e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
