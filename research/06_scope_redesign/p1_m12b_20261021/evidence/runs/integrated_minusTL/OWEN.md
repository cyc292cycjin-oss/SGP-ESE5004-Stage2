# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusTL；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusTL_2920_3h_unsolved.nc`（SHA256 `4161b112fb08…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusTL`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 307.512 bn，目标值 307.512 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 1.78e-11 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusTL/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.330** | 0.330 | 0.330 | 0.330 | 0.330 | 0.330 | 0.377 | 0.330 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **82.425** | 82.426 | 82.423 | 82.425 | 82.423 | 82.426 | 93.960 | 82.417 | -0.007 | -0.007 | 0.000 | 0.010 |
| KH | **4.335** | 4.339 | 4.331 | 4.336 | 4.331 | 4.339 | 4.942 | 4.064 | -0.271 | -0.271 | 0.000 | 0.010 |
| LA | **0.550** | 0.557 | 0.543 | 0.554 | 0.540 | 0.560 | 0.627 | 0.479 | -0.072 | -0.072 | 0.000 | 0.014 |
| MM | **2.795** | 2.807 | 2.783 | 2.800 | 2.782 | 2.807 | 3.186 | 2.840 | 0.045 | 0.045 | 0.000 | 0.010 |
| MY | **20.949** | 20.953 | 20.945 | 20.945 | 20.942 | 20.956 | 23.881 | 20.956 | 0.007 | 0.007 | 0.000 | 0.010 |
| PH | **17.968** | 17.968 | 17.968 | 17.968 | 17.968 | 17.968 | 20.483 | 17.968 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.327** | 7.324 | 7.330 | 7.329 | 7.324 | 7.330 | 8.352 | 7.327 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **33.274** | 33.249 | 33.299 | 33.266 | 33.249 | 33.299 | 37.931 | 33.861 | 0.587 | 0.587 | 0.000 | 0.013 |
| TL | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.578** | 61.577 | 61.578 | 61.577 | 61.577 | 61.578 | 70.196 | 61.288 | -0.289 | -0.289 | 0.000 | 0.010 |
| BUNKER | **75.981** | 75.981 | 75.981 | 75.981 | 75.981 | 75.981 | 86.614 | 75.981 | -0.000 | 0.000 | -0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 75.981 bn；余量 30.465 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
