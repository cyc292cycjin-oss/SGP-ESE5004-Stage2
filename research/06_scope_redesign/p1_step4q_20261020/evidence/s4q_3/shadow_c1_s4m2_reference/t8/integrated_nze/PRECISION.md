# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/integrated_nze`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier_1e6）；终止 `optimal`；目标 547960257786.0746；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：S4M-2 56x3h profile A (Threads 8): disconnected - integrated ledger difference (s4m_A_disconnected minus s4m_A_integrated, COUNTRY_COST_LEDGER.csv total) - S4Q-3 fixed reference of the C1 (b)(c) per-country tolerance
- 重评记录：this batch: disconnected - integrated ledger difference (/ho… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 129 次，原始 5.450735310e+11，对偶 5.450735280e+11，差 -3000 EUR（相对 5.50e-09），原始残差 0.0129，对偶残差 1.25e-05，互补 0.00621，204 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 138 次，原始 5.450735300e+11，对偶 5.450735280e+11，差 -2000 EUR（相对 3.67e-09），原始残差 0.0335，对偶残差 1.44e-05，互补 0.00474，220 s
- 最后一次迭代：第 138 次，原始 5.450735300e+11，对偶 5.450735280e+11，差 -2000 EUR（相对 3.67e-09），原始残差 0.0335，对偶残差 1.44e-05，互补 0.00474，220 s
- 返回数组的 KKT 摘要：原始 547960257786.0325，对偶 547960254873.767，差 -0.000003 bn，相对 5.31e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 203,069，超预算 16（与 `l23_violation_analysis.py` 一致：True），最大违反 0.2592，最大为预算 4.241 倍；一阶影响合计 6,076 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.85e-09 | 0.0100 | True |
| ID | 6.22e-07 | 0.0702 | True |
| KH | 2.37e-07 | 0.0188 | True |
| LA | 1.08e-06 | 0.0276 | True |
| MM | 1.70e-06 | 0.0100 | True |
| MY | 3.02e-07 | 0.0408 | True |
| PH | 2.32e-07 | 0.0177 | True |
| SG | 1.77e-08 | 0.0202 | True |
| TH | 8.04e-07 | 0.0615 | True |
| TL | 9.94e-09 | 0.0100 | True |
| VN | 4.65e-07 | 0.2496 | True |
| ASEAN | 6.23e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 16；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.9980682764522e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.07e-10 | 5.86e-08 | 5.87e-08 | 1.76e-10 | 3.26e-10 | 0.0100 | True | True |
| ID | 7.55e-08 | 1.49e-06 | 1.57e-06 | 1.68e-08 | 1.32e-08 | 0.0702 | True | True |
| KH | 3.26e-09 | 2.59e-07 | 2.62e-07 | 6.70e-09 | 2.84e-09 | 0.0188 | True | True |
| LA | 3.11e-09 | 4.46e-07 | 4.49e-07 | 1.31e-08 | 1.79e-09 | 0.0276 | True | True |
| MM | 1.24e-09 | 7.36e-07 | 7.38e-07 | 1.48e-08 | 1.39e-09 | 0.0100 | True | True |
| MY | 1.90e-08 | 3.45e-07 | 3.63e-07 | 5.88e-09 | 5.50e-09 | 0.0408 | True | True |
| PH | 1.45e-08 | 3.04e-07 | 3.18e-07 | 3.97e-09 | 3.00e-09 | 0.0177 | True | True |
| SG | 5.04e-09 | 4.00e-08 | 4.50e-08 | 3.69e-10 | 4.86e-10 | 0.0202 | True | True |
| TH | 1.53e-08 | 3.76e-07 | 3.91e-07 | 9.66e-09 | 7.07e-09 | 0.0615 | True | True |
| TL | 6.02e-12 | 6.39e-08 | 6.39e-08 | 2.49e-10 | 3.63e-10 | 0.0100 | True | True |
| VN | 2.11e-08 | 3.85e-07 | 4.06e-07 | 1.11e-08 | 6.78e-09 | 0.2496 | True | True |
| ASEAN | 3.33e-09 | 2.11e-07 | 2.14e-07 | 0.00e+00 | 4.28e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
