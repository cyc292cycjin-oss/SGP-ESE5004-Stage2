# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen/runs/dfx/V3`（disconnected，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 279089473192.1561；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v3_screen/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 104 次，原始 2.765732670e+11，对偶 2.765732540e+11，差 -1.3e+04 EUR（相对 4.70e-08），原始残差 0.0022，对偶残差 0.00591，互补 0.00241，873 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 150 次，原始 2.765732570e+11，对偶 2.765732560e+11，差 -1000 EUR（相对 3.62e-09），原始残差 0.154，对偶残差 0.00278，互补 0.00032，1269 s
- 最后一次迭代：第 158 次，原始 2.765732570e+11，对偶 2.765732560e+11，差 -1000 EUR（相对 3.62e-09），原始残差 0.0731，对偶残差 0.00229，互补 0.000267，1340 s
- 返回数组的 KKT 摘要：原始 279089473192.1961，对偶 279089471674.28314，差 -0.000002 bn，相对 5.44e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,278,861，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01655，最大为预算 0.03328 倍；一阶影响合计 153 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 4.02e-10 | 0.0100 | True |
| ID | 1.10e-07 | 0.0100 | True |
| KH | 9.89e-09 | 0.0100 | True |
| LA | 5.82e-10 | 0.0100 | True |
| MM | 2.14e-09 | 0.0100 | True |
| MY | 3.27e-09 | 0.0313 | True |
| PH | 1.90e-09 | 0.0100 | True |
| SG | 4.39e-09 | 0.0384 | True |
| TH | 8.46e-09 | 0.0119 | True |
| TL | 1.16e-10 | 0.0100 | True |
| VN | 1.21e-08 | 0.0447 | True |
| ASEAN | 6.91e-10 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.4302578929595354e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 1.98e-10 | 3.04e-08 | 3.06e-08 | 0.00e+00 | 6.33e-10 | 0.0100 | True | True |
| ID | 2.00e-08 | 6.39e-07 | 6.59e-07 | 5.43e-09 | 2.31e-08 | 0.0100 | True | True |
| KH | 1.45e-09 | 8.36e-08 | 8.50e-08 | 1.16e-09 | 2.79e-09 | 0.0100 | True | True |
| LA | 5.03e-10 | 7.26e-08 | 7.31e-08 | 1.77e-09 | 3.90e-09 | 0.0100 | True | True |
| MM | 4.82e-08 | 2.81e-07 | 3.29e-07 | 3.65e-09 | 4.83e-09 | 0.0100 | True | True |
| MY | 2.90e-08 | 1.25e-07 | 1.54e-07 | 1.08e-09 | 7.36e-09 | 0.0313 | True | True |
| PH | 1.74e-08 | 1.16e-07 | 1.34e-07 | 9.91e-10 | 4.83e-09 | 0.0100 | True | True |
| SG | 4.62e-08 | 2.04e-08 | 6.65e-08 | 0.00e+00 | 1.15e-09 | 0.0384 | True | True |
| TH | 6.87e-08 | 1.14e-07 | 1.83e-07 | 9.30e-10 | 8.57e-09 | 0.0119 | True | True |
| TL | 6.68e-11 | 2.11e-08 | 2.12e-08 | 0.00e+00 | 4.05e-10 | 0.0100 | True | True |
| VN | 1.72e-08 | 1.41e-07 | 1.59e-07 | 1.84e-09 | 8.29e-09 | 0.0447 | True | True |
| ASEAN | 7.76e-08 | 4.66e-12 | 7.76e-08 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 70 s。
