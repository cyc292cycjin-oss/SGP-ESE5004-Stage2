# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusKH`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 304043071781.8167；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/disconnected minus /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke_s01/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B3, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 206 次，原始 3.017501380e+11，对偶 3.017501380e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00646，对偶残差 1.38e-06，互补 0.00025，329 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 191 次，原始 3.017501380e+11，对偶 3.017501380e+11，差 0 EUR（相对 0.00e+00），原始残差 0.028，对偶残差 3.85e-07，互补 0.000817，304 s
- 最后一次迭代：第 206 次，原始 3.017501380e+11，对偶 3.017501380e+11，差 0 EUR（相对 0.00e+00），原始残差 0.00646，对偶残差 1.38e-06，互补 0.00025，329 s
- 返回数组的 KKT 摘要：原始 304043071781.7305，对偶 304043071600.6969，差 -0.000000 bn，相对 5.95e-10 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 203,904，超预算 2（与 `l23_violation_analysis.py` 一致：True），最大违反 0.0552，最大为预算 1.426 倍；一阶影响合计 609 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.37e-10 | 0.0100 | True |
| ID | 6.37e-08 | 0.0100 | True |
| KH | 0.00e+00 | 0.0100 | True |
| LA | 6.17e-08 | 0.0142 | True |
| MM | 3.25e-07 | 0.0100 | True |
| MY | 1.41e-08 | 0.0100 | True |
| PH | 2.83e-09 | 0.0100 | True |
| SG | 1.29e-09 | 0.0197 | True |
| TH | 3.84e-08 | 0.0129 | True |
| TL | 4.66e-10 | 0.0100 | True |
| VN | 3.87e-08 | 0.0100 | True |
| ASEAN | 6.49e-08 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 2；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 7.448104850616122e-11（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 5.52e-12 | 3.88e-09 | 3.88e-09 | 9.53e-12 | 1.78e-11 | 0.0100 | True | True |
| ID | 3.83e-09 | 1.05e-07 | 1.09e-07 | 9.26e-10 | 2.46e-09 | 0.0100 | True | True |
| KH | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |
| LA | 2.13e-10 | 2.94e-08 | 2.96e-08 | 6.67e-10 | 3.16e-10 | 0.0142 | True | True |
| MM | 8.42e-11 | 7.48e-08 | 7.49e-08 | 7.49e-10 | 4.43e-10 | 0.0100 | True | True |
| MY | 7.53e-10 | 2.27e-08 | 2.35e-08 | 3.30e-10 | 7.58e-10 | 0.0100 | True | True |
| PH | 6.03e-10 | 1.71e-08 | 1.77e-08 | 2.13e-10 | 4.87e-10 | 0.0100 | True | True |
| SG | 4.21e-10 | 2.94e-09 | 3.36e-09 | 9.13e-12 | 6.65e-11 | 0.0197 | True | True |
| TH | 7.65e-10 | 2.55e-08 | 2.62e-08 | 4.96e-10 | 8.00e-10 | 0.0129 | True | True |
| TL | 2.24e-12 | 1.92e-09 | 1.92e-09 | 1.22e-11 | 3.00e-11 | 0.0100 | True | True |
| VN | 1.22e-09 | 2.87e-08 | 2.99e-08 | 5.33e-10 | 8.12e-10 | 0.0100 | True | True |
| ASEAN | 6.15e-10 | 1.23e-08 | 1.30e-08 | 0.00e+00 | 1.10e-10 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
