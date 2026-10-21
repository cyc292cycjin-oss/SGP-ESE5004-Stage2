# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/disconnected`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 337070020174.8012；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 155 次，原始 3.345538040e+11，对偶 3.345538040e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0015，对偶残差 4.48e-06，互补 1.86e-05，223 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 147 次，原始 3.345538040e+11，对偶 3.345538040e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0231，对偶残差 5.32e-06，互补 0.000473，212 s
- 最后一次迭代：第 156 次，原始 3.345538040e+11，对偶 3.345538040e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00188，对偶残差 2.29e-06，互补 1.58e-05，225 s
- 返回数组的 KKT 摘要：原始 337070020174.74054，对偶 337070020162.30743，差 -0.000000 bn，相对 3.69e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 225,312，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.001403，最大为预算 0.02044 倍；一阶影响合计 47 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 6.51e-11 | 0.0100 | True |
| ID | 1.72e-08 | 0.0131 | True |
| KH | 3.91e-10 | 0.0100 | True |
| LA | 6.74e-09 | 0.0148 | True |
| MM | 5.19e-09 | 0.0100 | True |
| MY | 2.65e-09 | 0.0100 | True |
| PH | 2.76e-09 | 0.0100 | True |
| SG | 6.54e-11 | 0.0207 | True |
| TH | 1.42e-09 | 0.0124 | True |
| TL | 4.13e-11 | 0.0100 | True |
| VN | 2.38e-09 | 0.0116 | True |
| ASEAN | 9.39e-09 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.244061804376837e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.19e-12 | 2.05e-10 | 2.07e-10 | 0.00e+00 | 6.11e-13 | 0.0100 | True | True |
| ID | 3.83e-10 | 1.25e-08 | 1.29e-08 | 2.67e-11 | 1.66e-11 | 0.0131 | True | True |
| KH | 3.66e-11 | 1.02e-09 | 1.06e-09 | 1.01e-11 | 2.09e-12 | 0.0100 | True | True |
| LA | 6.09e-12 | 2.08e-09 | 2.09e-09 | 2.66e-11 | 2.48e-12 | 0.0148 | True | True |
| MM | 2.59e-11 | 3.19e-09 | 3.22e-09 | 2.67e-11 | 5.87e-12 | 0.0100 | True | True |
| MY | 9.03e-11 | 1.55e-09 | 1.64e-09 | 5.49e-12 | 4.04e-12 | 0.0100 | True | True |
| PH | 7.73e-11 | 3.49e-09 | 3.56e-09 | 1.15e-11 | 3.36e-12 | 0.0100 | True | True |
| SG | 9.38e-12 | 1.26e-10 | 1.36e-10 | 0.00e+00 | 4.54e-13 | 0.0207 | True | True |
| TH | 7.55e-10 | 1.94e-09 | 2.69e-09 | 9.74e-12 | 3.80e-12 | 0.0124 | True | True |
| TL | 2.79e-13 | 1.09e-10 | 1.09e-10 | 0.00e+00 | 5.68e-13 | 0.0100 | True | True |
| VN | 2.07e-10 | 2.36e-09 | 2.56e-09 | 2.31e-11 | 4.27e-12 | 0.0116 | True | True |
| ASEAN | 9.02e-10 | 3.58e-09 | 4.49e-09 | 0.00e+00 | 7.26e-13 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 14 s。
