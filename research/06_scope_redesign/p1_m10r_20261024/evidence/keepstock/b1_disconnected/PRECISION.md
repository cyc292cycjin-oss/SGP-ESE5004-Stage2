# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r/b1_disconnected`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 319682748223.1539；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 105 次，原始 3.171665320e+11，对偶 3.171665320e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00131，对偶残差 1.49e-05，互补 0.000606，150 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 104 次，原始 3.171665320e+11，对偶 3.171665320e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00132，对偶残差 1.23e-05，互补 0.000619，149 s
- 最后一次迭代：第 112 次，原始 3.171665320e+11，对偶 3.171665320e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00219，对偶残差 1.73e-07，互补 1.59e-05，161 s
- 返回数组的 KKT 摘要：原始 319682748223.10986，对偶 319682748214.0135，差 -0.000000 bn，相对 2.85e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 229,456，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.03756，最大为预算 0.0342 倍；一阶影响合计 43 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.31e-10 | 0.0100 | True |
| ID | 1.49e-08 | 0.0100 | True |
| KH | 3.72e-10 | 0.0100 | True |
| LA | 6.16e-09 | 0.0142 | True |
| MM | 6.30e-09 | 0.0100 | True |
| MY | 1.10e-09 | 0.0100 | True |
| PH | 1.11e-09 | 0.0100 | True |
| SG | 1.38e-10 | 0.0197 | True |
| TH | 2.49e-09 | 0.0129 | True |
| TL | 4.64e-11 | 0.0100 | True |
| VN | 4.18e-09 | 0.0100 | True |
| ASEAN | 6.18e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 9.058968961717183e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 5.29e-13 | 1.45e-10 | 1.46e-10 | 0.00e+00 | 5.57e-13 | 0.0100 | True | True |
| ID | 3.22e-10 | 7.14e-09 | 7.46e-09 | 2.19e-11 | 1.59e-11 | 0.0100 | True | True |
| KH | 1.23e-11 | 1.23e-09 | 1.24e-09 | 9.82e-12 | 1.84e-12 | 0.0100 | True | True |
| LA | 5.71e-12 | 2.64e-09 | 2.64e-09 | 2.17e-11 | 1.98e-12 | 0.0142 | True | True |
| MM | 2.52e-11 | 2.73e-09 | 2.76e-09 | 2.78e-11 | 6.02e-12 | 0.0100 | True | True |
| MY | 7.43e-11 | 1.71e-09 | 1.78e-09 | 5.44e-12 | 3.44e-12 | 0.0100 | True | True |
| PH | 3.87e-11 | 1.23e-09 | 1.27e-09 | 1.05e-11 | 3.14e-12 | 0.0100 | True | True |
| SG | 1.25e-11 | 1.44e-10 | 1.57e-10 | 0.00e+00 | 4.78e-13 | 0.0197 | True | True |
| TH | 8.56e-11 | 1.06e-09 | 1.15e-09 | 8.83e-12 | 3.16e-12 | 0.0129 | True | True |
| TL | 4.56e-13 | 1.00e-10 | 1.01e-10 | 0.00e+00 | 3.45e-13 | 0.0100 | True | True |
| VN | 1.42e-10 | 1.70e-09 | 1.84e-09 | 2.11e-11 | 4.20e-12 | 0.0100 | True | True |
| ASEAN | 1.17e-10 | 9.60e-10 | 1.08e-09 | 0.00e+00 | 6.12e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 13 s。
