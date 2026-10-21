# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusMY；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusMY_2920_3h_unsolved.nc`（SHA256 `8c80817621fc…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMY`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 289.523 bn，目标值 289.523 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 3.79e-11 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMY/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.481** | 0.481 | 0.481 | 0.481 | 0.481 | 0.481 | 0.548 | 0.481 | -0.000 | 0.000 | -0.000 | 0.010 |
| ID | **81.987** | 81.987 | 81.987 | 81.987 | 81.987 | 81.987 | 93.461 | 81.987 | -0.000 | -0.000 | -0.000 | 0.010 |
| KH | **4.337** | 4.341 | 4.333 | 4.338 | 4.333 | 4.341 | 4.944 | 4.097 | -0.240 | -0.240 | -0.000 | 0.010 |
| LA | **0.464** | 0.471 | 0.457 | 0.467 | 0.454 | 0.474 | 0.529 | 0.432 | -0.032 | -0.032 | 0.000 | 0.014 |
| MM | **2.650** | 2.663 | 2.638 | 2.656 | 2.638 | 2.663 | 3.021 | 2.683 | 0.032 | 0.032 | 0.000 | 0.010 |
| MY | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| PH | **18.030** | 18.030 | 18.030 | 18.030 | 18.030 | 18.030 | 20.553 | 18.030 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.283** | 7.283 | 7.283 | 7.283 | 7.283 | 7.283 | 8.303 | 7.283 | 0.000 | 0.000 | -0.000 | 0.020 |
| TH | **33.310** | 33.287 | 33.333 | 33.300 | 33.287 | 33.333 | 37.972 | 33.844 | 0.534 | 0.534 | 0.000 | 0.013 |
| TL | **0.253** | 0.253 | 0.253 | 0.253 | 0.253 | 0.253 | 0.288 | 0.253 | 0.000 | 0.000 | -0.000 | 0.010 |
| VN | **61.706** | 61.705 | 61.707 | 61.706 | 61.705 | 61.707 | 70.342 | 61.412 | -0.294 | -0.294 | 0.000 | 0.010 |
| BUNKER | **79.023** | 79.023 | 79.023 | 79.023 | 79.023 | 79.023 | 90.082 | 79.023 | -0.000 | 0.000 | -0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | 0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 79.023 bn；余量 27.423 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
