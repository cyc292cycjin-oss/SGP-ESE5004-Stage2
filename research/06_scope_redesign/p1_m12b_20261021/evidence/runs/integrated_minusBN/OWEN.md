# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusBN；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusBN_2920_3h_unsolved.nc`（SHA256 `44374fb527fe…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusBN`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 307.519 bn，目标值 307.519 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 1.40e-12 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusBN/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **82.387** | 82.389 | 82.385 | 82.387 | 82.385 | 82.389 | 93.917 | 82.382 | -0.005 | -0.005 | -0.000 | 0.010 |
| KH | **4.335** | 4.339 | 4.331 | 4.335 | 4.331 | 4.339 | 4.941 | 4.064 | -0.271 | -0.271 | 0.000 | 0.010 |
| LA | **0.548** | 0.555 | 0.541 | 0.552 | 0.538 | 0.558 | 0.625 | 0.477 | -0.071 | -0.071 | 0.000 | 0.014 |
| MM | **2.794** | 2.806 | 2.782 | 2.799 | 2.781 | 2.806 | 3.185 | 2.839 | 0.046 | 0.046 | 0.000 | 0.010 |
| MY | **20.950** | 20.953 | 20.946 | 20.945 | 20.942 | 20.957 | 23.882 | 20.955 | 0.005 | 0.005 | 0.000 | 0.010 |
| PH | **17.970** | 17.970 | 17.970 | 17.970 | 17.970 | 17.970 | 20.485 | 17.970 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.326** | 7.323 | 7.328 | 7.328 | 7.323 | 7.328 | 8.351 | 7.326 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **33.278** | 33.253 | 33.304 | 33.271 | 33.253 | 33.304 | 37.936 | 33.864 | 0.585 | 0.585 | 0.000 | 0.013 |
| TL | **0.357** | 0.357 | 0.357 | 0.357 | 0.357 | 0.357 | 0.407 | 0.357 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.577** | 61.576 | 61.578 | 61.577 | 61.576 | 61.578 | 70.195 | 61.288 | -0.289 | -0.289 | 0.000 | 0.010 |
| BUNKER | **75.998** | 75.998 | 75.998 | 75.998 | 75.998 | 75.998 | 86.634 | 75.998 | -0.000 | 0.000 | -0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 75.998 bn；余量 30.448 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
