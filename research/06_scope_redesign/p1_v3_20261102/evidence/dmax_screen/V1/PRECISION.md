# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen_dmax/runs/dfx/V1`（integrated，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 266272775892.55725；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2 minus /root/autodl-tmp/v3_screen_dmax/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B15, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 159 次，原始 2.639023740e+11，对偶 2.639023700e+11，差 -4000 EUR（相对 1.52e-08），原始残差 0.0591，对偶残差 0.028，互补 0.00111，3850 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 157 次，原始 2.639023740e+11，对偶 2.639023700e+11，差 -4000 EUR（相对 1.52e-08），原始残差 0.083，对偶残差 0.0369，互补 0.00128，3782 s
- 最后一次迭代：第 163 次，原始 2.639023740e+11，对偶 2.639023700e+11，差 -4000 EUR（相对 1.52e-08），原始残差 0.17，对偶残差 0.0247，互补 0.000996，3985 s
- 返回数组的 KKT 摘要：原始 266272775892.6115，对偶 266272772862.60904，差 -0.000003 bn，相对 1.14e-08 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 2,208,733，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.2431，最大为预算 0.6167 倍；一阶影响合计 3,290 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 4.69e-08 | 0.0100 | True |
| ID | 9.42e-07 | 0.0100 | True |
| KH | 1.89e-07 | 0.0100 | True |
| LA | 5.23e-07 | 0.0100 | True |
| MM | 4.16e-07 | 0.0100 | True |
| MY | 2.12e-07 | 0.0317 | True |
| PH | 1.67e-07 | 0.0100 | True |
| SG | 2.96e-08 | 0.0392 | True |
| TH | 3.39e-07 | 0.0108 | True |
| TL | 2.72e-08 | 0.0100 | True |
| VN | 4.16e-07 | 0.0450 | True |
| ASEAN | 9.37e-09 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.036623389167169e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.65e-10 | 1.27e-07 | 1.27e-07 | 2.10e-10 | 1.58e-09 | 0.0100 | True | True |
| ID | 2.55e-08 | 1.96e-06 | 1.99e-06 | 2.89e-08 | 7.56e-08 | 0.0100 | True | True |
| KH | 7.69e-09 | 2.97e-07 | 3.05e-07 | 1.02e-08 | 8.37e-09 | 0.0100 | True | True |
| LA | 3.46e-08 | 3.20e-07 | 3.55e-07 | 2.02e-08 | 7.20e-09 | 0.0100 | True | True |
| MM | 4.54e-09 | 7.88e-07 | 7.92e-07 | 2.26e-08 | 7.57e-09 | 0.0100 | True | True |
| MY | 7.87e-09 | 4.58e-07 | 4.66e-07 | 9.27e-09 | 3.92e-08 | 0.0317 | True | True |
| PH | 3.84e-09 | 3.96e-07 | 3.99e-07 | 6.77e-09 | 1.98e-08 | 0.0100 | True | True |
| SG | 2.79e-09 | 7.64e-08 | 7.92e-08 | 2.17e-10 | 5.37e-09 | 0.0392 | True | True |
| TH | 1.91e-08 | 4.29e-07 | 4.48e-07 | 1.38e-08 | 2.86e-08 | 0.0108 | True | True |
| TL | 2.32e-10 | 6.78e-08 | 6.80e-08 | 4.70e-10 | 1.89e-09 | 0.0100 | True | True |
| VN | 5.54e-08 | 5.09e-07 | 5.64e-07 | 1.64e-08 | 2.48e-08 | 0.0450 | True | True |
| ASEAN | 2.37e-10 | 1.37e-11 | 2.50e-10 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 85 s。
