# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen/runs/dfx/V1`（integrated，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 263596633674.85114；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v3_screen/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B15, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 125 次，原始 2.612262320e+11，对偶 2.612262050e+11，差 -2.7e+04 EUR（相对 1.03e-07），原始残差 0.702，对偶残差 0.00014，互补 0.00671，2507 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 125 次，原始 2.612262320e+11，对偶 2.612262050e+11，差 -2.7e+04 EUR（相对 1.03e-07），原始残差 0.702，对偶残差 0.00014，互补 0.00671，2507 s
- 最后一次迭代：第 146 次，原始 2.612262270e+11，对偶 2.612262190e+11，差 -8000 EUR（相对 3.06e-08），原始残差 2.47，对偶残差 0.000187，互补 0.00215，3116 s
- 返回数组的 KKT 摘要：原始 263596633674.9546，对偶 263596615579.89288，差 -0.000018 bn，相对 6.86e-08 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 2,316,229，超预算 3,845（与 `l23_violation_analysis.py` 一致：True），最大违反 1.319，最大为预算 3.972 倍；一阶影响合计 21,724 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.15e-07 | 0.0100 | True |
| ID | 5.42e-06 | 0.0100 | True |
| KH | 1.35e-06 | 0.0100 | True |
| LA | 3.66e-06 | 0.0100 | True |
| MM | 2.81e-06 | 0.0100 | True |
| MY | 1.35e-06 | 0.0313 | True |
| PH | 1.15e-06 | 0.0100 | True |
| SG | 1.96e-07 | 0.0384 | True |
| TH | 2.74e-06 | 0.0119 | True |
| TL | 1.79e-07 | 0.0100 | True |
| VN | 2.69e-06 | 0.0447 | True |
| ASEAN | 3.83e-08 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 2 / 3845；最大倍数的行是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.9270465467206033e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.39e-10 | 6.51e-07 | 6.51e-07 | 2.64e-09 | 4.03e-10 | 0.0100 | True | True |
| ID | 1.91e-08 | 1.13e-05 | 1.14e-05 | 2.33e-07 | 1.85e-07 | 0.0100 | True | True |
| KH | 3.72e-10 | 1.92e-06 | 1.92e-06 | 9.28e-08 | 1.86e-08 | 0.0100 | True | True |
| LA | 8.03e-10 | 2.29e-06 | 2.29e-06 | 1.84e-07 | 1.38e-08 | 0.0100 | True | True |
| MM | 9.86e-10 | 4.86e-06 | 4.86e-06 | 1.74e-07 | 3.32e-08 | 0.0100 | True | True |
| MY | 7.42e-09 | 2.82e-06 | 2.83e-06 | 9.57e-08 | 6.23e-08 | 0.0313 | True | True |
| PH | 3.90e-10 | 2.16e-06 | 2.16e-06 | 3.27e-08 | 3.28e-08 | 0.0100 | True | True |
| SG | 8.57e-10 | 4.81e-07 | 4.82e-07 | 3.06e-09 | 2.16e-08 | 0.0384 | True | True |
| TH | 5.53e-09 | 2.99e-06 | 3.00e-06 | 1.65e-07 | 8.88e-08 | 0.0119 | True | True |
| TL | 4.28e-11 | 3.80e-07 | 3.80e-07 | 2.04e-09 | 1.01e-09 | 0.0100 | True | True |
| VN | 2.16e-08 | 3.12e-06 | 3.15e-06 | 1.45e-07 | 4.91e-08 | 0.0447 | True | True |
| ASEAN | 5.39e-11 | 2.44e-13 | 5.41e-11 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 86 s。
