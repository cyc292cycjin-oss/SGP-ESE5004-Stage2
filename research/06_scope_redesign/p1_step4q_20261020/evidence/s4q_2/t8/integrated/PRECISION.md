# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/integrated`（integrated，SMOKE_TEST_ONLY，档案 formal_barrier_1e6）；终止 `optimal`；目标 648381184222.3383；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：True**（optimal True，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/home/jin/s4q_local/pkg/runs/20261020T001252Z_564/disconnected minus /home/jin/s4q_local/pkg/runs/20261020T001252Z_564/integrated, COUNTRY_COST_LEDGER.csv total)
- 重评记录：L23 365x24h ledger difference disconnected - integrated (res… → layer1_plus_nodal_price_settlement（验收 True）
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, B1, B12, B3

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 119 次，原始 6.454944570e+11，对偶 6.454944540e+11，差 -3000 EUR（相对 4.65e-09），原始残差 0.0222，对偶残差 1.02e-05，互补 0.00484，208 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 119 次，原始 6.454944570e+11，对偶 6.454944540e+11，差 -3000 EUR（相对 4.65e-09），原始残差 0.0222，对偶残差 1.02e-05，互补 0.00484，208 s
- 最后一次迭代：第 119 次，原始 6.454944570e+11，对偶 6.454944540e+11，差 -3000 EUR（相对 4.65e-09），原始残差 0.0222，对偶残差 1.02e-05，互补 0.00484，208 s
- 返回数组的 KKT 摘要：原始 648381184222.114，对偶 648381181216.7966，差 -0.000003 bn，相对 4.64e-09 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 200,309，超预算 0（与 `l23_violation_analysis.py` 一致：True），最大违反 0.3182，最大为预算 0.896 倍；一阶影响合计 3,995 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 9.55e-09 | 0.0100 | True |
| ID | 8.35e-07 | 0.0702 | True |
| KH | 7.35e-08 | 0.0188 | True |
| LA | 5.60e-07 | 0.0276 | True |
| MM | 1.10e-06 | 0.0100 | True |
| MY | 3.48e-07 | 0.0408 | True |
| PH | 2.66e-07 | 0.0177 | True |
| SG | 7.68e-09 | 0.0202 | True |
| TH | 2.25e-07 | 0.0615 | True |
| TL | 1.64e-08 | 0.0100 | True |
| VN | 1.27e-07 | 0.2496 | True |
| ASEAN | 4.24e-07 | 0.0199 | True |

- BN / SG / VN 生物质池行：超预算行中 0 / 0；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 4.715607208736743e-10（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 7.86e-11 | 6.27e-08 | 6.28e-08 | 1.31e-10 | 2.78e-10 | 0.0100 | True | True |
| ID | 5.39e-08 | 1.64e-06 | 1.70e-06 | 1.52e-08 | 1.32e-08 | 0.0702 | True | True |
| KH | 2.38e-09 | 2.32e-07 | 2.35e-07 | 5.43e-09 | 1.52e-09 | 0.0188 | True | True |
| LA | 2.31e-09 | 3.00e-07 | 3.02e-07 | 1.08e-08 | 2.12e-09 | 0.0276 | True | True |
| MM | 9.14e-10 | 7.58e-07 | 7.59e-07 | 1.26e-08 | 1.38e-09 | 0.0100 | True | True |
| MY | 1.36e-08 | 3.59e-07 | 3.73e-07 | 5.04e-09 | 5.45e-09 | 0.0408 | True | True |
| PH | 9.99e-09 | 3.03e-07 | 3.13e-07 | 3.83e-09 | 2.94e-09 | 0.0177 | True | True |
| SG | 3.64e-09 | 3.74e-08 | 4.10e-08 | 2.12e-10 | 4.78e-10 | 0.0202 | True | True |
| TH | 1.10e-08 | 4.02e-07 | 4.13e-07 | 7.63e-09 | 5.43e-09 | 0.0615 | True | True |
| TL | 4.53e-12 | 6.41e-08 | 6.41e-08 | 2.32e-10 | 2.50e-10 | 0.0100 | True | True |
| VN | 1.52e-08 | 3.77e-07 | 3.92e-07 | 9.74e-09 | 5.93e-09 | 0.2496 | True | True |
| ASEAN | 2.49e-09 | 2.37e-07 | 2.39e-07 | 0.00e+00 | 3.70e-09 | 0.0199 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 15 s。
