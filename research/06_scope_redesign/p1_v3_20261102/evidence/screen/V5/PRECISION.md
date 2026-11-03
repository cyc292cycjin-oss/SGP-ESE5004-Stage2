# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen/runs/dfx/V5`（integrated，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 268726098775.54218；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v3_screen/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B15, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 137 次，原始 2.663556970e+11，对偶 2.663556900e+11，差 -7000 EUR（相对 2.63e-08），原始残差 0.116，对偶残差 0.0291，互补 0.00149，3422 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 127 次，原始 2.663556970e+11，对偶 2.663556890e+11，差 -8000 EUR（相对 3.00e-08），原始残差 0.15，对偶残差 0.00016，互补 0.00192，3091 s
- 最后一次迭代：第 137 次，原始 2.663556970e+11，对偶 2.663556900e+11，差 -7000 EUR（相对 2.63e-08），原始残差 0.116，对偶残差 0.0291，互补 0.00149，3422 s
- 返回数组的 KKT 摘要：原始 268726098775.61688，对偶 268726093863.1173，差 -0.000005 bn，相对 1.83e-08 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 2,116,838，超预算 2（与 `l23_violation_analysis.py` 一致：True），最大违反 0.1778，最大为预算 15.13 倍；一阶影响合计 3,918 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 5.24e-08 | 0.0100 | True |
| ID | 9.50e-07 | 0.0100 | True |
| KH | 2.18e-07 | 0.0100 | True |
| LA | 6.17e-07 | 0.0100 | True |
| MM | 4.91e-07 | 0.0100 | True |
| MY | 3.73e-07 | 0.0313 | True |
| PH | 1.86e-07 | 0.0100 | True |
| SG | 3.27e-08 | 0.0384 | True |
| TH | 5.31e-07 | 0.0119 | True |
| TL | 2.93e-08 | 0.0100 | True |
| VN | 4.60e-07 | 0.0447 | True |
| ASEAN | 1.00e-08 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 2；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.7800437542317117e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 8.15e-11 | 2.03e-07 | 2.03e-07 | 8.29e-10 | 1.15e-09 | 0.0100 | True | True |
| ID | 1.30e-08 | 2.60e-06 | 2.61e-06 | 5.66e-08 | 7.88e-08 | 0.0100 | True | True |
| KH | 2.17e-09 | 4.29e-07 | 4.31e-07 | 2.22e-08 | 9.01e-09 | 0.0100 | True | True |
| LA | 8.25e-09 | 4.78e-07 | 4.87e-07 | 4.20e-08 | 9.01e-09 | 0.0100 | True | True |
| MM | 7.69e-10 | 1.07e-06 | 1.07e-06 | 4.27e-08 | 1.55e-08 | 0.0100 | True | True |
| MY | 1.78e-09 | 6.34e-07 | 6.36e-07 | 2.14e-08 | 2.05e-08 | 0.0313 | True | True |
| PH | 1.21e-10 | 5.02e-07 | 5.03e-07 | 8.69e-09 | 1.27e-08 | 0.0100 | True | True |
| SG | 3.95e-10 | 1.07e-07 | 1.07e-07 | 8.62e-10 | 9.35e-09 | 0.0384 | True | True |
| TH | 2.69e-09 | 6.58e-07 | 6.61e-07 | 3.60e-08 | 2.86e-08 | 0.0119 | True | True |
| TL | 1.66e-11 | 8.97e-08 | 8.97e-08 | 6.60e-10 | 1.75e-09 | 0.0100 | True | True |
| VN | 2.42e-09 | 6.93e-07 | 6.95e-07 | 3.33e-08 | 2.44e-08 | 0.0447 | True | True |
| ASEAN | 1.73e-10 | 2.57e-11 | 1.99e-10 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 89 s。
