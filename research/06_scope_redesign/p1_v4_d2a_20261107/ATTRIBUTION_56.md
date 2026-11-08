# v4 成本上升归因（56 时段，两因素 Shapley；V4 D2a 第 7 节；Fable F-22）

- **因素：** 需求 D（v4 需求与工业表、曲线、过程排放与原料碳）；资源上限 P（v4 生物质潜力含 T04、0.99 上限、商品气上限）。其余 v4 改动在所有角上取 v4 值。
- **角：** (D4,P4) = 第 6 节冒烟；(D4,P31)、(D31,P4) = 本节 4 次求解；**(D31,P31) 未求解（额度）**，用 v3.1 网络的冒烟值加已知其他改动近似（INFERENCE，`evidence/ATTRIB_INPUTS.json`）。
- **56 时段结果只给方向，不作结论**（冬夏季节与储能跨期在 56 时段中不存在）。

## 1. 目标值（EUR，含常数项）

| 角 | F1 一体化 | F2 `no_new_xb` | B6 = F2 − F1 | 等级 |
|---|---:|---:|---:|---|
| (D31,P31) | 331,145,046,403.92 | 343,639,187,359.38 | 12,494,140,955.46 | INFERENCE（近似） |
| (D4,P31) | 329,853,409,059.36 | 342,431,438,654.97 | 12,578,029,595.62 | VERIFIED（求解回执） |
| (D31,P4) | 362,445,881,245.89 | 374,597,076,484.48 | 12,151,195,238.59 | VERIFIED（求解回执） |
| (D4,P4) | 348,819,582,511.57 | 361,150,691,045.29 | 12,331,108,533.72 | VERIFIED（求解回执） |

## 2. Shapley 拆分（bn EUR）

| 量 | 总变化 (D4,P4) − (D31,P31) | φ_D 需求 | φ_P 资源上限 | 交互项 (D 在 P4 − D 在 P31) | D 先 / P 先 |
|---|---:|---:|---:|---:|---|
| 一体化目标值 | +17.675 | -7.459 | +25.134 | -12.335 | D 先: D -1.292 P +18.966; P 先: P +31.301 D -13.626 |
| `no_new_xb` 目标值 | +17.512 | -7.327 | +24.839 | -12.239 | D 先: D -1.208 P +18.719; P 先: P +30.958 D -13.446 |
| B6 | -0.163 | +0.132 | -0.295 | +0.096 | D 先: D +0.084 P -0.247; P 先: P -0.343 D +0.180 |

## 3. 按参与者（bn EUR）

| 参与者 | 量 | (D31,P31) | (D4,P31) | (D31,P4) | (D4,P4) | φ_D | φ_P |
|---|---|---:|---:|---:|---:|---:|---:|
| MY | Owen benefit (B6 allocation) | +0.870 | +0.916 | +1.165 | +1.066 | -0.026 | +0.222 |
| ID | Owen benefit (B6 allocation) | -0.712 | -0.010 | +0.782 | +1.076 | +0.499 | +1.290 |
| SG | Owen benefit (B6 allocation) | +2.770 | +3.138 | +2.662 | +2.937 | +0.321 | -0.155 |
| BUNKER | Owen benefit (B6 allocation) | +3.297 | +2.884 | +2.062 | +2.414 | -0.030 | -0.853 |
| MY | integrated cost ledger | +25.251 | +31.492 | +27.434 | +33.531 | +6.169 | +2.111 |
| ID | integrated cost ledger | +91.076 | +89.016 | +109.879 | +95.638 | -8.150 | +12.713 |
| SG | integrated cost ledger | +10.041 | +11.514 | +10.167 | +11.752 | +1.529 | +0.182 |
| BUNKER | integrated cost ledger | +76.075 | +73.549 | +85.210 | +84.303 | -1.716 | +9.944 |

## 4. 近似项（(D31,P31)）

| 项 | F1 | F2 | 来源 |
|---|---:|---:|---|
| v3.1 网络冒烟目标值 | 329,705,565,613.54 | 342,268,691,464.46 | F1 W08 R0 (v3.1 package integrated network solved on the W08 code; the v3.1 package smoke gives 329,705,566,422.24, +808.69 EUR); F2 v3.1 package local smoke results_project/v3hpc/smoke_hpc/no_new_xb |
| trunk_proxy_cost_D1 | 1,449,347,508.86 | 1,449,345,260.81 | D1 section 7: realised dV of the proxy cost on the W08 solution (trunk pools fully used; the same holds for the v3.1 smoke, zero-cost pools), scaled 1:1 (INFERENCE) |
| phs_reclass_lower_bound_terms_D2a | -33,339,621.97 | -101,815,968.21 | D2a SMOKE56_D2A.md section 1: PHS capacity value + TH inflow re-sharing + new-reservoir completion (lower-bound terms at the D1 duals, used as the estimate; sign of the new reservoir indefinite) |
| methanol_coefficient_first_order_D2a | 23,472,903.48 | 22,966,602.32 | D2a SMOKE56_D2A.md section 1: first order at the D1 solution (no bound) |

## 5. 读法

- φ_D 与 φ_P 之和恒等于总变化；交互项（D 的边际在 P4 与 P31 下的差）衡量两因素的非可加性。
- 参与者行：Owen 受益是 B6 的分摊（正 = 互联受益），一体化台账是各国在 F1 的成本份额；(D31,P31) 行来自 v3.1 冒烟的分摊 + 其他改动的按国近似。
- 本表只给方向；正式归因在 2920×3h 批次上重做（Fable F-22 第 3 点）。
