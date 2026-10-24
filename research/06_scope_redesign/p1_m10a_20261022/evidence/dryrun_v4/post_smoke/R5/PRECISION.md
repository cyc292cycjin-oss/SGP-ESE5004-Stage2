# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/m10a_dry/post_smoke/R5`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 247442934821.50006；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/m10a_dry/post_smoke/R2 minus /home/jin/m10a_dry/post_smoke/R1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 180 次，原始 2.463858340e+11，对偶 2.463858340e+11，差 0 EUR（相对 0.00e+00），原始残差 7.07e-05，对偶残差 2.09e-05，互补 4.27e-06，273 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 155 次，原始 2.463858340e+11，对偶 2.463858340e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0233，对偶残差 1.55e-07，互补 0.001，232 s
- 最后一次迭代：第 181 次，原始 2.463858340e+11，对偶 2.463858340e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000106，对偶残差 1.84e-05，互补 2.45e-06，275 s
- 返回数组的 KKT 摘要：原始 247442934821.46054，对偶 247442934818.84476，差 -0.000000 bn，相对 1.06e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 200,961，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.002675，最大为预算 0.002769 倍；一阶影响合计 6 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.46e-12 | 0.0100 | True |
| ID | 1.54e-09 | 0.0100 | True |
| KH | 1.14e-10 | 0.0100 | True |
| LA | 4.79e-10 | 0.0142 | True |
| MM | 1.49e-09 | 0.0100 | True |
| MY | 3.70e-10 | 0.0100 | True |
| PH | 2.66e-10 | 0.0100 | True |
| SG | 8.58e-12 | 0.0197 | True |
| TH | 9.04e-10 | 0.0129 | True |
| TL | 5.33e-12 | 0.0100 | True |
| VN | 0.00e+00 | 0.0100 | True |
| ASEAN | 5.82e-10 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 7.760035731107724e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.78e-13 | 3.83e-11 | 3.85e-11 | 3.44e-15 | 6.04e-14 | 0.0100 | True | True |
| ID | 4.13e-10 | 1.14e-09 | 1.55e-09 | 4.32e-12 | 1.96e-12 | 0.0100 | True | True |
| KH | 2.50e-11 | 1.23e-10 | 1.48e-10 | 1.48e-12 | 9.49e-13 | 0.0100 | True | True |
| LA | 2.22e-11 | 2.23e-10 | 2.45e-10 | 3.25e-12 | 2.16e-13 | 0.0142 | True | True |
| MM | 3.07e-11 | 5.97e-10 | 6.28e-10 | 3.95e-12 | 6.76e-13 | 0.0100 | True | True |
| MY | 7.69e-11 | 2.49e-10 | 3.26e-10 | 1.32e-12 | 1.25e-12 | 0.0100 | True | True |
| PH | 3.61e-11 | 2.40e-10 | 2.76e-10 | 1.62e-12 | 4.04e-13 | 0.0100 | True | True |
| SG | 7.48e-12 | 2.53e-11 | 3.28e-11 | 2.82e-14 | 6.73e-14 | 0.0197 | True | True |
| TH | 1.62e-09 | 7.15e-10 | 2.34e-09 | 1.72e-12 | 4.25e-13 | 0.0129 | True | True |
| TL | 4.83e-13 | 1.95e-11 | 2.00e-11 | 2.45e-14 | 6.09e-14 | 0.0100 | True | True |
| VN | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| ASEAN | 7.41e-10 | 1.19e-10 | 8.60e-10 | 0.00e+00 | 4.19e-14 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 17 s。
