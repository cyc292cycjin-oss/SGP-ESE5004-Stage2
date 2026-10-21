# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：SMOKE_56x3h；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc`（SHA256 `513f56a65c7e…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4o/s4o3/solves/s4o_integrated`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展）：11 国 + 燃料舱 = 648.377 bn，目标值 648.395 bn，相对误差 2.79e-05（≤ 1e-6：**False**）；共享 0.000 bn。
- C1 (c)（运行本身）：True；分摊可用：**False**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4o/s4o3/solves/s4o_integrated/PRECISION.json: L23 365x24h ledger difference disconnected - integrated (research/06_scope_redesign/p1_l23_run1_20261019, L23_C9_SUMMARY。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.184** | 0.184 | 0.184 | 0.184 | 0.184 | 0.184 | 0.209 | 0.184 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **206.198** | 206.200 | 206.196 | 206.198 | 206.196 | 206.200 | 235.056 | 206.255 | 0.058 | 0.051 | 0.007 | 0.010 |
| KH | **6.393** | 6.397 | 6.389 | 6.394 | 6.389 | 6.397 | 7.288 | 5.483 | -0.910 | -0.911 | 0.001 | 0.024 |
| LA | **-0.427** | -0.420 | -0.434 | -0.423 | -0.438 | -0.417 | -0.487 | -0.708 | -0.280 | -0.281 | 0.001 | 0.027 |
| MM | **8.334** | 8.347 | 8.321 | 8.340 | 8.321 | 8.347 | 9.500 | 8.391 | 0.057 | 0.055 | 0.003 | 0.011 |
| MY | **68.756** | 68.939 | 68.573 | 68.751 | 68.570 | 68.942 | 78.378 | 68.707 | -0.049 | -0.051 | 0.002 | 0.032 |
| PH | **24.306** | 24.306 | 24.306 | 24.306 | 24.306 | 24.306 | 27.708 | 24.308 | 0.001 | 0.000 | 0.001 | 0.010 |
| SG | **20.290** | 20.288 | 20.293 | 20.293 | 20.288 | 20.293 | 23.130 | 20.291 | 0.000 | 0.000 | 0.000 | 0.010 |
| TH | **80.364** | 80.159 | 80.569 | 80.356 | 80.159 | 80.569 | 91.611 | 81.205 | 0.842 | 0.840 | 0.001 | 0.075 |
| TL | **-0.247** | -0.247 | -0.247 | -0.247 | -0.247 | -0.247 | -0.281 | -0.247 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **139.674** | 139.674 | 139.675 | 139.674 | 139.674 | 139.675 | 159.222 | 139.974 | 0.299 | 0.298 | 0.002 | 0.513 |
| BUNKER | **94.552** | 94.552 | 94.552 | 94.552 | 94.552 | 94.552 | 107.785 | 94.552 | 0.000 | 0.000 | 0.000 | 0.012 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 94.552 bn；余量 11.894 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
