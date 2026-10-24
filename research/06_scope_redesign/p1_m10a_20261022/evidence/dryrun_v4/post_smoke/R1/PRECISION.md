# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/m10a_dry/post_smoke/R1`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 307847440010.6307；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/m10a_dry/post_smoke/R2 minus /home/jin/m10a_dry/post_smoke/R1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 129 次，原始 3.054929080e+11，对偶 3.054929080e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000186，对偶残差 6.45e-06，互补 1.16e-05，219 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 113 次，原始 3.054929080e+11，对偶 3.054929080e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00623，对偶残差 7.36e-07，互补 0.00083，191 s
- 最后一次迭代：第 129 次，原始 3.054929080e+11，对偶 3.054929080e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000186，对偶残差 6.45e-06，互补 1.16e-05，219 s
- 返回数组的 KKT 摘要：原始 307847440010.5978，对偶 307847440007.00275，差 -0.000000 bn，相对 1.17e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 223,810，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.001872，最大为预算 0.03575 倍；一阶影响合计 29 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.13e-11 | 0.0100 | True |
| ID | 4.64e-09 | 0.0100 | True |
| KH | 2.01e-09 | 0.0100 | True |
| LA | 1.64e-09 | 0.0142 | True |
| MM | 5.80e-09 | 0.0100 | True |
| MY | 1.93e-09 | 0.0100 | True |
| PH | 2.04e-09 | 0.0100 | True |
| SG | 3.67e-11 | 0.0197 | True |
| TH | 4.79e-09 | 0.0129 | True |
| TL | 2.73e-11 | 0.0100 | True |
| VN | 3.05e-09 | 0.0100 | True |
| ASEAN | 3.90e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 7.915305525635052e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.39e-13 | 1.63e-10 | 1.64e-10 | 7.76e-14 | 1.08e-12 | 0.0100 | True | True |
| ID | 3.74e-10 | 4.55e-09 | 4.93e-09 | 2.20e-11 | 4.00e-11 | 0.0100 | True | True |
| KH | 9.38e-12 | 7.93e-10 | 8.02e-10 | 9.32e-12 | 7.48e-12 | 0.0100 | True | True |
| LA | 7.56e-11 | 7.16e-10 | 7.92e-10 | 1.82e-11 | 8.04e-12 | 0.0142 | True | True |
| MM | 2.63e-11 | 2.18e-09 | 2.21e-09 | 2.37e-11 | 1.50e-11 | 0.0100 | True | True |
| MY | 7.66e-11 | 1.40e-09 | 1.47e-09 | 7.03e-12 | 9.92e-12 | 0.0100 | True | True |
| PH | 3.03e-11 | 8.29e-10 | 8.59e-10 | 8.39e-12 | 8.29e-12 | 0.0100 | True | True |
| SG | 7.58e-12 | 1.20e-10 | 1.28e-10 | 1.04e-13 | 1.15e-12 | 0.0197 | True | True |
| TH | 4.62e-10 | 1.93e-09 | 2.39e-09 | 1.08e-11 | 1.25e-11 | 0.0129 | True | True |
| TL | 4.83e-13 | 8.22e-11 | 8.27e-11 | 2.12e-13 | 1.34e-12 | 0.0100 | True | True |
| VN | 2.21e-10 | 2.81e-09 | 3.04e-09 | 1.85e-11 | 1.21e-11 | 0.0100 | True | True |
| ASEAN | 1.85e-10 | 6.88e-10 | 8.73e-10 | 0.00e+00 | 1.08e-12 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 19 s。
