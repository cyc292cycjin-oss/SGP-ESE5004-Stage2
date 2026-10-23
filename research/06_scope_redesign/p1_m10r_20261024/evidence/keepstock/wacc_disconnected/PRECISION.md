# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r/wacc_disconnected`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 302021940622.4669；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 132 次，原始 2.985591240e+11，对偶 2.985591240e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00201，对偶残差 9.89e-07，互补 1.33e-05，200 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 129 次，原始 2.985591240e+11，对偶 2.985591240e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0523，对偶残差 1.67e-05，互补 0.000332，196 s
- 最后一次迭代：第 132 次，原始 2.985591240e+11，对偶 2.985591240e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00201，对偶残差 9.89e-07，互补 1.33e-05，200 s
- 返回数组的 KKT 摘要：原始 302021940622.4567，对偶 302021940612.525，差 -0.000000 bn，相对 3.29e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 211,328，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.03284，最大为预算 0.003308 倍；一阶影响合计 25 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.89e-11 | 0.0100 | True |
| ID | 1.59e-08 | 0.0100 | True |
| KH | 6.18e-10 | 0.0100 | True |
| LA | 1.45e-09 | 0.0142 | True |
| MM | 1.57e-09 | 0.0100 | True |
| MY | 9.78e-10 | 0.0100 | True |
| PH | 6.46e-10 | 0.0100 | True |
| SG | 3.25e-11 | 0.0197 | True |
| TH | 3.27e-10 | 0.0129 | True |
| TL | 3.01e-11 | 0.0100 | True |
| VN | 1.16e-09 | 0.0100 | True |
| ASEAN | 2.48e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 5.7376962504064235e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.13e-12 | 1.87e-10 | 1.88e-10 | 0.00e+00 | 4.02e-13 | 0.0100 | True | True |
| ID | 2.90e-10 | 9.19e-09 | 9.48e-09 | 2.36e-11 | 1.04e-11 | 0.0100 | True | True |
| KH | 1.48e-11 | 5.73e-10 | 5.88e-10 | 7.69e-12 | 1.25e-12 | 0.0100 | True | True |
| LA | 5.72e-12 | 7.21e-10 | 7.27e-10 | 1.96e-11 | 1.64e-12 | 0.0142 | True | True |
| MM | 3.46e-11 | 2.43e-09 | 2.47e-09 | 1.86e-11 | 4.89e-12 | 0.0100 | True | True |
| MY | 7.64e-11 | 1.05e-09 | 1.13e-09 | 5.17e-12 | 3.37e-12 | 0.0100 | True | True |
| PH | 3.62e-11 | 1.02e-09 | 1.05e-09 | 9.63e-12 | 2.12e-12 | 0.0100 | True | True |
| SG | 5.62e-12 | 1.26e-10 | 1.31e-10 | 0.00e+00 | 3.68e-13 | 0.0197 | True | True |
| TH | 2.03e-10 | 9.31e-10 | 1.13e-09 | 6.88e-12 | 2.27e-12 | 0.0129 | True | True |
| TL | 6.79e-13 | 8.80e-11 | 8.87e-11 | 0.00e+00 | 3.31e-13 | 0.0100 | True | True |
| VN | 1.30e-10 | 2.27e-09 | 2.40e-09 | 1.82e-11 | 3.32e-12 | 0.0100 | True | True |
| ASEAN | 8.17e-10 | 7.77e-10 | 1.59e-09 | 0.00e+00 | 3.69e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 14 s。
