# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/m10p_dry/post_smoke/R2`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 317745965908.25806；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/m10p_dry/post_smoke/R2 minus /home/jin/m10p_dry/post_smoke/R1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 152 次，原始 3.152297500e+11，对偶 3.152297500e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00355，对偶残差 2.01e-05，互补 2.23e-05，228 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 126 次，原始 3.152297500e+11，对偶 3.152297500e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0411，对偶残差 2.8e-06，互补 0.000962，188 s
- 最后一次迭代：第 152 次，原始 3.152297500e+11，对偶 3.152297500e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00355，对偶残差 2.01e-05，互补 2.23e-05，228 s
- 返回数组的 KKT 摘要：原始 317745965908.21735，对偶 317745965903.02905，差 -0.000000 bn，相对 1.63e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 231,145，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01665，最大为预算 0.0102 倍；一阶影响合计 49 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.11e-10 | 0.0100 | True |
| ID | 1.66e-08 | 0.0100 | True |
| KH | 6.27e-10 | 0.0100 | True |
| LA | 7.10e-09 | 0.0142 | True |
| MM | 5.58e-09 | 0.0100 | True |
| MY | 2.06e-09 | 0.0100 | True |
| PH | 6.78e-10 | 0.0100 | True |
| SG | 1.34e-10 | 0.0197 | True |
| TH | 6.29e-09 | 0.0129 | True |
| TL | 5.37e-11 | 0.0100 | True |
| VN | 6.68e-09 | 0.0100 | True |
| ASEAN | 7.14e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.4544992234069164e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.76e-12 | 2.62e-10 | 2.64e-10 | 0.00e+00 | 1.79e-12 | 0.0100 | True | True |
| ID | 1.61e-09 | 1.47e-08 | 1.63e-08 | 3.43e-11 | 5.54e-11 | 0.0100 | True | True |
| KH | 2.76e-10 | 1.13e-09 | 1.40e-09 | 1.51e-11 | 6.32e-12 | 0.0100 | True | True |
| LA | 9.00e-12 | 1.44e-09 | 1.45e-09 | 3.25e-11 | 6.68e-12 | 0.0142 | True | True |
| MM | 2.41e-11 | 4.87e-09 | 4.90e-09 | 4.14e-11 | 2.11e-11 | 0.0100 | True | True |
| MY | 1.37e-10 | 1.59e-09 | 1.72e-09 | 7.67e-12 | 1.20e-11 | 0.0100 | True | True |
| PH | 8.22e-11 | 1.69e-09 | 1.78e-09 | 1.59e-11 | 1.04e-11 | 0.0100 | True | True |
| SG | 5.17e-11 | 1.98e-10 | 2.50e-10 | 0.00e+00 | 1.31e-12 | 0.0197 | True | True |
| TH | 4.58e-09 | 2.52e-09 | 7.10e-09 | 1.34e-11 | 1.16e-11 | 0.0129 | True | True |
| TL | 3.25e-13 | 1.46e-10 | 1.46e-10 | 0.00e+00 | 1.73e-12 | 0.0100 | True | True |
| VN | 1.56e-09 | 3.30e-09 | 4.86e-09 | 3.23e-11 | 1.32e-11 | 0.0100 | True | True |
| ASEAN | 5.22e-09 | 2.06e-09 | 7.28e-09 | 0.00e+00 | 2.03e-12 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 16 s。
