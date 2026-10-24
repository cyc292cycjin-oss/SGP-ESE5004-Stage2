# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/m10a_dry/post_smoke/R7`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 308187775538.148；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/m10a_dry/post_smoke/R2 minus /home/jin/m10a_dry/post_smoke/R1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 148 次，原始 3.064219260e+11，对偶 3.064219260e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00204，对偶残差 5.86e-06，互补 1.13e-05，217 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 143 次，原始 3.064219260e+11，对偶 3.064219260e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0415，对偶残差 6.45e-06，互补 0.000612，211 s
- 最后一次迭代：第 148 次，原始 3.064219260e+11，对偶 3.064219260e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00204，对偶残差 5.86e-06，互补 1.13e-05，217 s
- 返回数组的 KKT 摘要：原始 308187775538.12994，对偶 308187775534.305，差 -0.000000 bn，相对 1.24e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 232,369，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01968，最大为预算 0.02678 倍；一阶影响合计 21 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.14e-11 | 0.0100 | True |
| ID | 5.79e-09 | 0.0100 | True |
| KH | 5.65e-10 | 0.0100 | True |
| LA | 0.00e+00 | 0.0142 | True |
| MM | 4.84e-09 | 0.0100 | True |
| MY | 1.94e-09 | 0.0100 | True |
| PH | 2.02e-09 | 0.0100 | True |
| SG | 1.48e-10 | 0.0197 | True |
| TH | 4.02e-09 | 0.0129 | True |
| TL | 4.60e-11 | 0.0100 | True |
| VN | 1.71e-09 | 0.0100 | True |
| ASEAN | 2.19e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.6021868914180204e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 6.93e-13 | 1.56e-10 | 1.57e-10 | 4.97e-14 | 7.54e-13 | 0.0100 | True | True |
| ID | 3.61e-10 | 4.47e-09 | 4.83e-09 | 1.67e-11 | 2.58e-11 | 0.0100 | True | True |
| KH | 1.41e-11 | 6.62e-10 | 6.76e-10 | 6.92e-12 | 3.71e-12 | 0.0100 | True | True |
| LA | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0142 | True | True |
| MM | 2.75e-11 | 2.27e-09 | 2.29e-09 | 1.79e-11 | 1.02e-11 | 0.0100 | True | True |
| MY | 7.94e-11 | 2.31e-09 | 2.39e-09 | 5.10e-12 | 7.04e-12 | 0.0100 | True | True |
| PH | 3.47e-11 | 1.15e-09 | 1.18e-09 | 6.62e-12 | 5.12e-12 | 0.0100 | True | True |
| SG | 7.66e-12 | 1.01e-10 | 1.09e-10 | 6.24e-14 | 7.33e-13 | 0.0197 | True | True |
| TH | 1.31e-09 | 1.03e-09 | 2.34e-09 | 7.47e-12 | 6.48e-12 | 0.0129 | True | True |
| TL | 4.83e-13 | 7.27e-11 | 7.32e-11 | 1.26e-13 | 8.55e-13 | 0.0100 | True | True |
| VN | 2.65e-10 | 3.16e-09 | 3.43e-09 | 1.47e-11 | 6.67e-12 | 0.0100 | True | True |
| ASEAN | 1.29e-10 | 6.66e-10 | 7.95e-10 | 0.00e+00 | 6.66e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 20 s。
