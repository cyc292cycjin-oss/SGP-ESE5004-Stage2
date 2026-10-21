# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusSG；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusSG_2920_3h_unsolved.nc`（SHA256 `17571f2f5e8f…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusSG`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 301.124 bn，目标值 301.126 bn，差 -0.002 bn（|差| ≤ 0.01 bn：**True**；相对误差 6.91e-06 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusSG/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.330** | 0.330 | 0.330 | 0.330 | 0.330 | 0.330 | 0.376 | 0.330 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **82.956** | 82.957 | 82.954 | 82.956 | 82.954 | 82.957 | 94.566 | 82.950 | -0.006 | -0.007 | 0.001 | 0.010 |
| KH | **4.345** | 4.349 | 4.341 | 4.346 | 4.341 | 4.349 | 4.953 | 4.074 | -0.271 | -0.271 | 0.000 | 0.010 |
| LA | **0.550** | 0.557 | 0.543 | 0.554 | 0.540 | 0.560 | 0.627 | 0.478 | -0.072 | -0.072 | 0.000 | 0.014 |
| MM | **2.784** | 2.796 | 2.772 | 2.790 | 2.772 | 2.797 | 3.174 | 2.831 | 0.046 | 0.046 | 0.000 | 0.010 |
| MY | **20.982** | 20.984 | 20.981 | 20.981 | 20.978 | 20.987 | 23.919 | 20.990 | 0.007 | 0.007 | 0.000 | 0.010 |
| PH | **17.978** | 17.978 | 17.978 | 17.978 | 17.978 | 17.978 | 20.494 | 17.978 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **33.268** | 33.243 | 33.293 | 33.260 | 33.243 | 33.293 | 37.924 | 33.852 | 0.584 | 0.584 | 0.000 | 0.013 |
| TL | **0.357** | 0.357 | 0.357 | 0.357 | 0.357 | 0.357 | 0.407 | 0.357 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.592** | 61.591 | 61.593 | 61.592 | 61.591 | 61.593 | 70.212 | 61.305 | -0.287 | -0.287 | 0.000 | 0.010 |
| BUNKER | **75.981** | 75.981 | 75.981 | 75.981 | 75.981 | 75.981 | 86.615 | 75.981 | 0.000 | 0.000 | 0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.000 | 0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 75.981 bn；余量 30.464 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
