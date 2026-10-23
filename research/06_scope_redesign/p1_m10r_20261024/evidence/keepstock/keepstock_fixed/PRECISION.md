# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r/regress_post/keepstock`（disconnected，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 318479975461.52246；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` True；不通过 A1_A2, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 104 次，原始 3.161254460e+11，对偶 3.161254470e+11，差 1000 EUR（相对 3.16e-09），原始残差 0.00244，对偶残差 6.64e-07，互补 0.00434，156 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 120 次，原始 3.161254430e+11，对偶 3.161254430e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0186，对偶残差 1.31e-06，互补 8.12e-05，180 s
- 最后一次迭代：第 122 次，原始 3.161254430e+11，对偶 3.161254430e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00361，对偶残差 1.1e-06，互补 1.66e-05，183 s
- 返回数组的 KKT 摘要：原始 318479975461.4802，对偶 318479975450.5823，差 -0.000000 bn，相对 3.42e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 217,602，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.05857，最大为预算 0.03675 倍；一阶影响合计 53 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 9.84e-11 | 0.0100 | True |
| ID | 2.77e-08 | 0.0100 | True |
| KH | 9.75e-10 | 0.0100 | True |
| LA | 4.60e-09 | 0.0142 | True |
| MM | 6.76e-09 | 0.0100 | True |
| MY | 1.39e-09 | 0.0100 | True |
| PH | 6.61e-10 | 0.0100 | True |
| SG | 1.28e-10 | 0.0197 | True |
| TH | 5.64e-10 | 0.0129 | True |
| TL | 3.24e-11 | 0.0100 | True |
| VN | 6.19e-09 | 0.0100 | True |
| ASEAN | 4.04e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.73478151421079e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.67e-12 | 2.33e-10 | 2.34e-10 | 0.00e+00 | 5.03e-13 | 0.0100 | True | True |
| ID | 3.34e-10 | 2.05e-08 | 2.09e-08 | 2.85e-11 | 1.41e-11 | 0.0100 | True | True |
| KH | 1.05e-11 | 7.94e-10 | 8.04e-10 | 1.31e-11 | 2.18e-12 | 0.0100 | True | True |
| LA | 5.10e-12 | 2.81e-09 | 2.82e-09 | 2.83e-11 | 2.51e-11 | 0.0142 | True | True |
| MM | 2.49e-11 | 4.30e-09 | 4.32e-09 | 3.60e-11 | 5.55e-12 | 0.0100 | True | True |
| MY | 8.07e-11 | 1.56e-09 | 1.64e-09 | 7.74e-12 | 4.03e-12 | 0.0100 | True | True |
| PH | 3.07e-11 | 1.17e-09 | 1.21e-09 | 1.40e-11 | 2.53e-12 | 0.0100 | True | True |
| SG | 6.14e-12 | 1.92e-10 | 1.98e-10 | 1.74e-14 | 8.33e-13 | 0.0197 | True | True |
| TH | 2.80e-10 | 1.76e-09 | 2.04e-09 | 1.12e-11 | 4.58e-12 | 0.0129 | True | True |
| TL | 2.92e-13 | 1.11e-10 | 1.11e-10 | 0.00e+00 | 4.25e-13 | 0.0100 | True | True |
| VN | 1.52e-10 | 4.04e-09 | 4.20e-09 | 2.84e-11 | 3.59e-12 | 0.0100 | True | True |
| ASEAN | 3.25e-10 | 9.32e-10 | 1.26e-09 | 0.00e+00 | 5.36e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
