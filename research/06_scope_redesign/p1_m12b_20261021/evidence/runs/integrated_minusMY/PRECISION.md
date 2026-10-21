# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMY`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 289523276210.1538；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 144 次，原始 2.868505860e+11，对偶 2.868505860e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000528，对偶残差 5.11e-07，互补 3.64e-05，219 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 139 次，原始 2.868505860e+11，对偶 2.868505860e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0174，对偶残差 1.38e-06，互补 0.00117，212 s
- 最后一次迭代：第 147 次，原始 2.868505860e+11，对偶 2.868505860e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0227，对偶残差 3.37e-05，互补 1.09e-05，223 s
- 返回数组的 KKT 摘要：原始 289523276210.10284，对偶 289523276199.17，差 -0.000000 bn，相对 3.78e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 230,007，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.1857，最大为预算 0.0241 倍；一阶影响合计 145 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.40e-10 | 0.0100 | True |
| ID | 5.42e-08 | 0.0100 | True |
| KH | 7.23e-09 | 0.0100 | True |
| LA | 9.64e-09 | 0.0142 | True |
| MM | 1.83e-08 | 0.0100 | True |
| MY | 0.00e+00 | 0.0100 | True |
| PH | 4.34e-09 | 0.0100 | True |
| SG | 1.24e-09 | 0.0197 | True |
| TH | 2.17e-08 | 0.0129 | True |
| TL | 2.14e-10 | 0.0100 | True |
| VN | 1.11e-08 | 0.0100 | True |
| ASEAN | 2.37e-08 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 5.998461880753589e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 6.18e-13 | 1.42e-10 | 1.43e-10 | 0.00e+00 | 2.62e-13 | 0.0100 | True | True |
| ID | 5.15e-10 | 1.76e-08 | 1.81e-08 | 1.60e-11 | 8.24e-12 | 0.0100 | True | True |
| KH | 1.70e-11 | 3.02e-09 | 3.04e-09 | 6.11e-12 | 9.76e-13 | 0.0100 | True | True |
| LA | 1.39e-10 | 1.16e-08 | 1.18e-08 | 1.36e-11 | 1.02e-12 | 0.0142 | True | True |
| MM | 2.73e-11 | 2.73e-08 | 2.73e-08 | 1.68e-11 | 2.78e-12 | 0.0100 | True | True |
| MY | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| PH | 5.41e-11 | 7.77e-09 | 7.83e-09 | 6.85e-12 | 1.37e-12 | 0.0100 | True | True |
| SG | 7.37e-12 | 4.88e-10 | 4.95e-10 | 0.00e+00 | 2.22e-13 | 0.0197 | True | True |
| TH | 3.39e-09 | 1.86e-08 | 2.20e-08 | 5.97e-12 | 2.67e-12 | 0.0129 | True | True |
| TL | 1.75e-12 | 1.19e-10 | 1.21e-10 | 6.92e-14 | 2.31e-13 | 0.0100 | True | True |
| VN | 4.50e-10 | 1.21e-08 | 1.26e-08 | 1.40e-11 | 4.21e-12 | 0.0100 | True | True |
| ASEAN | 2.04e-10 | 2.51e-09 | 2.72e-09 | 0.00e+00 | 2.82e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
