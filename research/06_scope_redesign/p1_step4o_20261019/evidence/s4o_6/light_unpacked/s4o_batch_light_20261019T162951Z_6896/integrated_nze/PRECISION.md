# PRECISION（第 119 项 C1，第 120 项运行验收；只读，未启动 Gurobi）

- 运行：`/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/integrated_nze`（integrated，FORMAL_TRIAL_365X24H，档案 formal_barrier）；终止 `suboptimal`；目标 425761150197.1771；基于**最终返回解**（solution/X、Pi、RC）。
- **验收（第 120 项 = optimal + (a)(b)(c)）：False**（optimal False，(a) True，(b) True，(c) True）
- 分级：**layer1_plus_nodal_price_settlement**（按电价结算：usable）
- 分国容差参照：this batch: disconnected - integrated ledger difference (/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnected minus /root/autodl-tmp/s4n_pilot/integrated, COUNTRY_COST_LEDGER.csv total)
- 项目门槛（数值信息，不作判据）：`all_passed_solver_tolerances` False；不通过 A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B14, B15, B2, B3, B3_S4B

## (a) 总成本精度

- 第一轮停滞前最好迭代（原始残差最小）：第 206 次，原始 4.228744230e+11，对偶 4.228742830e+11，差 -1.4e+05 EUR（相对 3.31e-07），原始残差 3.92，对偶残差 3.42e-05，互补 0.0425，4970 s
- 最终返回解（日志中与回执 objective_lp 相同的迭代）：第 206 次，原始 4.228744230e+11，对偶 4.228742830e+11，差 -1.4e+05 EUR（相对 3.31e-07），原始残差 3.92，对偶残差 3.42e-05，互补 0.0425，4970 s
- 最后一次迭代：第 216 次，原始 4.228744180e+11，对偶 4.228742840e+11，差 -1.34e+05 EUR（相对 3.17e-07），原始残差 4.4，对偶残差 0.000101，互补 0.0408，5238 s
- 返回数组的 KKT 摘要：原始 425761150197.18463，对偶 425761014766.2082，差 -0.000135 bn，相对 3.18e-07 → 标准（≤ 0.01 bn 且 ≤ 1e-5）：**True**

## (b) 原始违反（L23 §6 方法）

- 有正违反的行 1,534,936，超预算 3,499（与 `l23_violation_analysis.py` 一致：True），最大违反 11.04，最大为预算 26.29 倍；一阶影响合计 66,699 EUR

| 国 | 一阶影响 bn | 阈值 bn | 通过 |
|---|---|---|---|
| BN | 7.45e-07 | 0.0100 | True |
| ID | 1.54e-05 | 0.0100 | True |
| KH | 3.93e-06 | 0.0243 | True |
| LA | 1.11e-05 | 0.0274 | True |
| MM | 8.49e-06 | 0.0113 | True |
| MY | 3.54e-06 | 0.0321 | True |
| PH | 3.69e-06 | 0.0100 | True |
| SG | 2.99e-07 | 0.0100 | True |
| TH | 5.62e-06 | 0.0751 | True |
| TL | 7.03e-07 | 0.0100 | True |
| VN | 6.67e-06 | 0.5159 | True |
| ASEAN | 6.84e-06 | 0.0122 | True |

- BN / SG / VN 生物质池行：超预算行中 4 / 3499；最大倍数的行不是此类行；仍占主导：**False**

## (c) 价格质量

- B16 账本恒等式：相对误差 1.90573875984556e-09（≤ 1e-6）→ **True**
- KKT 残差对分国结算的影响（INFERENCE；rows / columns by the component's bus country; cross-border components counted fully for both countries）：

| 国 | 驻点 S bn | 行互补 R bn | S+R bn | 列互补 K bn | 自由列符号 bn | 阈值 bn | S+R 通过 | 全部项通过 |
|---|---|---|---|---|---|---|---|---|
| BN | 3.91e-08 | 3.11e-06 | 3.15e-06 | 1.55e-08 | 1.83e-09 | 0.0100 | True | True |
| ID | 2.90e-06 | 6.71e-05 | 7.01e-05 | 1.36e-06 | 5.40e-07 | 0.0100 | True | True |
| KH | 2.34e-07 | 1.18e-05 | 1.20e-05 | 5.43e-07 | 1.80e-07 | 0.0243 | True | True |
| LA | 2.14e-07 | 1.43e-05 | 1.45e-05 | 9.89e-07 | 3.90e-07 | 0.0274 | True | True |
| MM | 6.29e-08 | 2.78e-05 | 2.78e-05 | 1.06e-06 | 2.80e-07 | 0.0113 | True | True |
| MY | 1.03e-06 | 1.58e-05 | 1.68e-05 | 4.73e-07 | 1.35e-07 | 0.0321 | True | True |
| PH | 5.27e-07 | 1.29e-05 | 1.35e-05 | 2.43e-07 | 9.72e-08 | 0.0100 | True | True |
| SG | 1.01e-07 | 1.68e-06 | 1.78e-06 | 1.76e-08 | 1.62e-08 | 0.0100 | True | True |
| TH | 1.35e-06 | 1.63e-05 | 1.76e-05 | 8.08e-07 | 2.63e-07 | 0.0751 | True | True |
| TL | 3.29e-09 | 3.12e-06 | 3.12e-06 | 1.54e-08 | 9.63e-09 | 0.0100 | True | True |
| VN | 1.13e-06 | 1.86e-05 | 1.98e-05 | 8.07e-07 | 6.16e-07 | 0.5159 | True | True |
| ASEAN | 1.20e-07 | 9.19e-06 | 9.31e-06 | 0.00e+00 | 1.08e-06 | 0.0122 | True | True |

- (c) 判定（B16 且每国 S+R ≤ 阈值）：**True**（全部项：True）

用时 67 s。
