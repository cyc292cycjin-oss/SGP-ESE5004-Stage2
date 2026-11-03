# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/v3_screen/runs/dfx/V2`（no_new_xb，DFX_365X24H，档案 formal_barrier_1e6_t16）；终止 `optimal`；目标 277944710210.22314；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/v3_screen/runs/dfx/V2 minus /root/autodl-tmp/v3_screen/runs/dfx/V1, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 87 次，原始 2.754036690e+11，对偶 2.754035910e+11，差 -7.8e+04 EUR（相对 2.83e-07），原始残差 0.000172，对偶残差 0.0277，互补 0.00999，924 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 95 次，原始 2.754036310e+11，对偶 2.754036270e+11，差 -4000 EUR（相对 1.45e-08），原始残差 0.00271，对偶残差 0.000946，互补 0.000388，1000 s
- 最后一次迭代：第 95 次，原始 2.754036310e+11，对偶 2.754036270e+11，差 -4000 EUR（相对 1.45e-08），原始残差 0.00271，对偶残差 0.000946，互补 0.000388，1000 s
- 返回数组的 KKT 摘要：原始 277944710210.32874，对偶 277944706732.1163，差 -0.000003 bn，相对 1.25e-08 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,279,871，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.01097，最大为预算 0.3478 倍；一阶影响合计 22 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 3.67e-11 | 0.0100 | True |
| ID | 9.13e-09 | 0.0100 | True |
| KH | 1.10e-09 | 0.0100 | True |
| LA | 1.06e-10 | 0.0100 | True |
| MM | 2.10e-10 | 0.0100 | True |
| MY | 5.52e-10 | 0.0313 | True |
| PH | 3.90e-10 | 0.0100 | True |
| SG | 3.57e-10 | 0.0384 | True |
| TH | 1.15e-09 | 0.0119 | True |
| TL | 9.33e-11 | 0.0100 | True |
| VN | 8.55e-09 | 0.0447 | True |
| ASEAN | 3.10e-10 | 0.0100 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 3.7989865046410316e-13（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 2.91e-10 | 3.64e-08 | 3.67e-08 | 0.00e+00 | 1.73e-09 | 0.0100 | True | True |
| ID | 2.60e-08 | 8.04e-07 | 8.30e-07 | 1.20e-08 | 6.97e-08 | 0.0100 | True | True |
| KH | 9.40e-10 | 1.03e-07 | 1.04e-07 | 2.78e-09 | 1.82e-08 | 0.0100 | True | True |
| LA | 1.42e-10 | 1.03e-07 | 1.03e-07 | 3.27e-09 | 1.80e-08 | 0.0100 | True | True |
| MM | 3.34e-10 | 3.59e-07 | 3.60e-07 | 8.74e-09 | 1.28e-08 | 0.0100 | True | True |
| MY | 2.26e-07 | 1.57e-07 | 3.82e-07 | 2.47e-09 | 2.95e-08 | 0.0313 | True | True |
| PH | 6.52e-08 | 1.40e-07 | 2.05e-07 | 1.41e-09 | 1.29e-08 | 0.0100 | True | True |
| SG | 1.26e-06 | 2.47e-08 | 1.28e-06 | 6.57e-11 | 9.78e-09 | 0.0384 | True | True |
| TH | 1.70e-06 | 1.41e-07 | 1.84e-06 | 2.23e-09 | 3.45e-08 | 0.0119 | True | True |
| TL | 3.98e-11 | 2.45e-08 | 2.46e-08 | 0.00e+00 | 8.70e-10 | 0.0100 | True | True |
| VN | 4.89e-08 | 1.74e-07 | 2.23e-07 | 3.51e-09 | 2.98e-08 | 0.0447 | True | True |
| ASEAN | 3.32e-06 | 5.44e-12 | 3.32e-06 | 0.00e+00 | 0.00e+00 | 0.0100 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 80 s。
