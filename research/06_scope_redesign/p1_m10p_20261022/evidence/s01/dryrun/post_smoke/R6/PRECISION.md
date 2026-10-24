# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/m10p_dry_s01/post_smoke/R6`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier）；终止 `optimal`；目标 274756068655.39697；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/m10p_dry_s01/post_smoke/R2 minus /home/jin/m10p_dry_s01/post_smoke/R1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A5, B1, B8

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 161 次，原始 2.716935360e+11，对偶 2.716935360e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000269，对偶残差 7.81e-06，互补 1.46e-05，239 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 143 次，原始 2.716935360e+11，对偶 2.716935360e+11，差 0 EUR（相对 0.00e+00），原始残差 0.0226，对偶残差 1.59e-07，互补 0.00123，212 s
- 最后一次迭代：第 161 次，原始 2.716935360e+11，对偶 2.716935360e+11，差 0 EUR（相对 0.00e+00），原始残差 0.000269，对偶残差 7.81e-06，互补 1.46e-05，239 s
- 返回数组的 KKT 摘要：原始 274756068655.36746，对偶 274756068645.344，差 -0.000000 bn，相对 3.65e-11 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 221,996，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.00465，最大为预算 0.01124 倍；一阶影响合计 34 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 1.27e-10 | 0.0100 | True |
| ID | 7.41e-09 | 0.0100 | True |
| KH | 8.48e-10 | 0.0100 | True |
| LA | 2.87e-09 | 0.0142 | True |
| MM | 6.17e-09 | 0.0100 | True |
| MY | 3.36e-09 | 0.0100 | True |
| PH | 4.19e-09 | 0.0100 | True |
| SG | 5.36e-11 | 0.0197 | True |
| TH | 0.00e+00 | 0.0129 | True |
| TL | 6.37e-11 | 0.0100 | True |
| VN | 6.98e-09 | 0.0100 | True |
| ASEAN | 2.52e-09 | 0.0210 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.5475367124752714e-12（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 4.59e-12 | 2.10e-10 | 2.15e-10 | 4.20e-14 | 6.60e-13 | 0.0100 | True | True |
| ID | 1.45e-09 | 6.84e-09 | 8.29e-09 | 2.47e-11 | 2.28e-11 | 0.0100 | True | True |
| KH | 8.44e-11 | 8.89e-10 | 9.73e-10 | 9.10e-12 | 3.38e-12 | 0.0100 | True | True |
| LA | 4.28e-10 | 9.36e-10 | 1.36e-09 | 1.93e-11 | 2.04e-11 | 0.0142 | True | True |
| MM | 3.13e-11 | 3.06e-09 | 3.09e-09 | 2.41e-11 | 9.34e-12 | 0.0100 | True | True |
| MY | 1.50e-10 | 1.97e-09 | 2.12e-09 | 7.61e-12 | 5.06e-12 | 0.0100 | True | True |
| PH | 1.61e-10 | 2.70e-09 | 2.86e-09 | 1.01e-11 | 4.34e-12 | 0.0100 | True | True |
| SG | 8.07e-12 | 1.36e-10 | 1.45e-10 | 5.07e-13 | 6.57e-13 | 0.0197 | True | True |
| TH | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.0129 | True | True |
| TL | 4.84e-13 | 1.04e-10 | 1.05e-10 | 1.89e-13 | 7.24e-13 | 0.0100 | True | True |
| VN | 1.62e-09 | 3.40e-09 | 5.02e-09 | 2.13e-11 | 6.23e-12 | 0.0100 | True | True |
| ASEAN | 2.71e-09 | 1.14e-09 | 3.84e-09 | 0.00e+00 | 4.66e-13 | 0.0210 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 17 s。
