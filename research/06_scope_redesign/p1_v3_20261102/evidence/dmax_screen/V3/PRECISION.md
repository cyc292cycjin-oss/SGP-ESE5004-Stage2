# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen_dmax/runs/dfx/V3`（disconnected，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 282050565982.57947；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen_dmax/runs/dfx/V2 minus /root/autodl-tmp/v3_screen_dmax/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 95 次，原始 2.795343520e+11，对偶 2.795343500e+11，差 -2000 EUR（相对 7.15e-09），原始残差 0.000764，对偶残差 0.00445，互补 0.000927，839 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 99 次，原始 2.795343500e+11，对偶 2.795343490e+11，差 -1000 EUR（相对 3.58e-09），原始残差 0.00448，对偶残差 0.00108，互补 0.000351，875 s
- 最后一次迭代：第 111 次，原始 2.795343500e+11，对偶 2.795343480e+11，差 -2000 EUR（相对 7.15e-09），原始残差 0.00256，对偶残差 0.000338，互补 0.00025，989 s
- 返回数组的 KKT 摘要：原始 282050565982.614，对偶 282050564505.9716，差 -0.000001 bn，相对 5.24e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,275,267，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01025，最大为预算 0.0183 倍；一阶影响合计 82 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 2.01e-10 | 0.0100 | True |
| ID | 4.54e-08 | 0.0100 | True |
| KH | 7.04e-10 | 0.0100 | True |
| LA | 6.66e-10 | 0.0100 | True |
| MM | 6.41e-10 | 0.0100 | True |
| MY | 7.91e-10 | 0.0317 | True |
| PH | 2.94e-09 | 0.0100 | True |
| SG | 2.58e-10 | 0.0392 | True |
| TH | 2.25e-08 | 0.0108 | True |
| TL | 9.04e-11 | 0.0100 | True |
| VN | 7.34e-09 | 0.0450 | True |
| ASEAN | 5.69e-10 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.224812235960331e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.92e-10 | 2.58e-08 | 2.61e-08 | 0.00e+00 | 1.41e-09 | 0.0100 | True | True |
| ID | 1.72e-08 | 5.34e-07 | 5.51e-07 | 5.84e-09 | 5.25e-08 | 0.0100 | True | True |
| KH | 1.36e-09 | 7.08e-08 | 7.21e-08 | 1.35e-09 | 7.07e-09 | 0.0100 | True | True |
| LA | 2.95e-10 | 6.42e-08 | 6.45e-08 | 1.82e-09 | 7.76e-09 | 0.0100 | True | True |
| MM | 5.11e-10 | 2.39e-07 | 2.39e-07 | 4.09e-09 | 8.96e-09 | 0.0100 | True | True |
| MY | 2.56e-08 | 1.05e-07 | 1.30e-07 | 1.17e-09 | 2.09e-08 | 0.0317 | True | True |
| PH | 7.45e-09 | 9.87e-08 | 1.06e-07 | 9.77e-10 | 1.20e-08 | 0.0100 | True | True |
| SG | 4.33e-08 | 1.75e-08 | 6.08e-08 | 0.00e+00 | 2.74e-09 | 0.0392 | True | True |
| TH | 6.24e-08 | 9.82e-08 | 1.61e-07 | 1.22e-09 | 2.23e-08 | 0.0108 | True | True |
| TL | 1.14e-11 | 1.82e-08 | 1.82e-08 | 0.00e+00 | 1.24e-09 | 0.0100 | True | True |
| VN | 9.96e-09 | 1.19e-07 | 1.29e-07 | 2.21e-09 | 2.17e-08 | 0.0450 | True | True |
| ASEAN | 1.36e-07 | 3.64e-12 | 1.36e-07 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 67 s。
