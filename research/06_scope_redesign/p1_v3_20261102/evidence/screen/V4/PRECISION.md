# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen/runs/dfx/V4`（integrated，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 271232068844.6826；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v3_screen/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B15, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 174 次，原始 2.688616670e+11，对偶 2.688616640e+11，差 -3000 EUR（相对 1.12e-08），原始残差 0.0442，对偶残差 0.00103，互补 0.000948，4152 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 173 次，原始 2.688616670e+11，对偶 2.688616640e+11，差 -3000 EUR（相对 1.12e-08），原始残差 0.0461，对偶残差 0.00106，互补 0.000991，4118 s
- 最后一次迭代：第 186 次，原始 2.688616670e+11，对偶 2.688616640e+11，差 -3000 EUR（相对 1.12e-08），原始残差 0.0942，对偶残差 0.000791，互补 0.00075，4549 s
- 返回数组的 KKT 摘要：原始 271232068844.74786，对偶 271232066714.35544，差 -0.000002 bn，相对 7.85e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 2,125,369，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.367，最大为预算 0.6376 倍；一阶影响合计 2,936 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 4.04e-08 | 0.0100 | True |
| ID | 8.98e-07 | 0.0100 | True |
| KH | 1.63e-07 | 0.0100 | True |
| LA | 4.65e-07 | 0.0100 | True |
| MM | 3.64e-07 | 0.0100 | True |
| MY | 1.69e-07 | 0.0313 | True |
| PH | 1.55e-07 | 0.0100 | True |
| SG | 2.32e-08 | 0.0384 | True |
| TH | 2.77e-07 | 0.0119 | True |
| TL | 2.27e-08 | 0.0100 | True |
| VN | 3.76e-07 | 0.0447 | True |
| ASEAN | 7.54e-09 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 2.4078132599024467e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.36e-11 | 9.97e-08 | 9.97e-08 | 4.14e-11 | 2.99e-10 | 0.0100 | True | True |
| ID | 8.05e-09 | 1.50e-06 | 1.51e-06 | 1.63e-08 | 1.52e-08 | 0.0100 | True | True |
| KH | 1.86e-09 | 2.27e-07 | 2.29e-07 | 5.06e-09 | 1.86e-09 | 0.0100 | True | True |
| LA | 1.19e-09 | 2.17e-07 | 2.18e-07 | 1.04e-08 | 2.55e-09 | 0.0100 | True | True |
| MM | 6.44e-10 | 5.93e-07 | 5.94e-07 | 1.26e-08 | 3.34e-09 | 0.0100 | True | True |
| MY | 1.66e-08 | 3.41e-07 | 3.57e-07 | 4.48e-09 | 4.61e-09 | 0.0313 | True | True |
| PH | 1.90e-09 | 3.09e-07 | 3.10e-07 | 4.53e-09 | 2.65e-09 | 0.0100 | True | True |
| SG | 2.13e-10 | 5.96e-08 | 5.98e-08 | 4.59e-11 | 8.27e-10 | 0.0384 | True | True |
| TH | 2.78e-09 | 3.08e-07 | 3.10e-07 | 5.71e-09 | 4.17e-09 | 0.0119 | True | True |
| TL | 1.59e-11 | 5.44e-08 | 5.44e-08 | 2.76e-10 | 2.27e-10 | 0.0100 | True | True |
| VN | 3.78e-08 | 3.96e-07 | 4.34e-07 | 8.74e-09 | 4.84e-09 | 0.0447 | True | True |
| ASEAN | 6.70e-11 | 3.27e-11 | 9.97e-11 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 85 s。
