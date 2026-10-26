# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/dfx_v8/runs/dfx/V1`（integrated，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 270785244510.473；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/dfx_v8/runs/dfx/V2 minus /root/autodl-tmp/dfx_v8/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B15, B2, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 325 次，原始 2.684307120e+11，对偶 2.684305120e+11，差 -2e+05 EUR（相对 7.45e-07），原始残差 8.31，对偶残差 1.1e-05，互补 0.0601，5320 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 325 次，原始 2.684307120e+11，对偶 2.684305120e+11，差 -2e+05 EUR（相对 7.45e-07），原始残差 8.31，对偶残差 1.1e-05，互补 0.0601，5320 s
- 最后一次迭代：第 335 次，原始 2.684307020e+11，对偶 2.684305150e+11，差 -1.87e+05 EUR（相对 6.97e-07），原始残差 8.48，对偶残差 1.07e-05，互补 0.0561，5488 s
- 返回数组的 KKT 摘要：原始 270785244510.66745，对偶 270785056369.66238，差 -0.000188 bn，相对 6.95e-07 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,808,188，超预算 12,154（与 `l23_violation_analysis.py` 一致：True），最大违反 16.62，最大为预算 81.44 倍；一阶影响合计 189,829 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.67e-06 | 0.0100 | True |
| ID | 5.00e-05 | 0.0100 | True |
| KH | 8.90e-06 | 0.0100 | True |
| LA | 2.29e-05 | 0.0125 | True |
| MM | 2.22e-05 | 0.0100 | True |
| MY | 9.38e-06 | 0.0291 | True |
| PH | 1.32e-05 | 0.0100 | True |
| SG | 1.48e-06 | 0.0384 | True |
| TH | 1.36e-05 | 0.0183 | True |
| TL | 1.08e-06 | 0.0100 | True |
| VN | 2.60e-05 | 0.0357 | True |
| ASEAN | 2.07e-05 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 6 / 12154；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 9.608093057597286e-09（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.79e-09 | 4.71e-06 | 4.71e-06 | 1.08e-08 | 1.10e-08 | 0.0100 | True | True |
| ID | 1.15e-06 | 1.12e-04 | 1.13e-04 | 1.36e-06 | 5.18e-07 | 0.0100 | True | True |
| KH | 8.32e-08 | 1.62e-05 | 1.62e-05 | 4.86e-07 | 9.68e-08 | 0.0100 | True | True |
| LA | 4.58e-08 | 1.89e-05 | 1.89e-05 | 9.93e-07 | 1.04e-06 | 0.0125 | True | True |
| MM | 7.18e-08 | 4.64e-05 | 4.64e-05 | 1.05e-06 | 3.00e-07 | 0.0100 | True | True |
| MY | 2.90e-07 | 2.47e-05 | 2.49e-05 | 4.75e-07 | 1.36e-07 | 0.0291 | True | True |
| PH | 1.02e-07 | 1.96e-05 | 1.97e-05 | 2.72e-07 | 7.25e-08 | 0.0100 | True | True |
| SG | 4.14e-08 | 3.07e-06 | 3.11e-06 | 8.46e-09 | 3.04e-08 | 0.0384 | True | True |
| TH | 4.31e-07 | 2.36e-05 | 2.40e-05 | 7.48e-07 | 2.55e-07 | 0.0183 | True | True |
| TL | 6.17e-09 | 2.24e-06 | 2.25e-06 | 1.60e-08 | 7.82e-09 | 0.0100 | True | True |
| VN | 3.49e-07 | 2.69e-05 | 2.72e-05 | 7.61e-07 | 1.95e-07 | 0.0357 | True | True |
| ASEAN | 1.13e-07 | 1.24e-05 | 1.25e-05 | 0.00e+00 | 7.31e-07 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 81 s。
