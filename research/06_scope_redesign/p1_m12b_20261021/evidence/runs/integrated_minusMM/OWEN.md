# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusMM；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusMM_2920_3h_unsolved.nc`（SHA256 `3ec9ed06a2a2…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMM`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 305.079 bn，目标值 305.079 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 1.07e-11 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusMM/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.331** | 0.331 | 0.331 | 0.331 | 0.331 | 0.331 | 0.377 | 0.331 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **81.993** | 81.994 | 81.991 | 81.993 | 81.991 | 81.994 | 93.468 | 81.984 | -0.008 | -0.008 | 0.000 | 0.010 |
| KH | **4.352** | 4.356 | 4.347 | 4.352 | 4.347 | 4.356 | 4.961 | 4.108 | -0.244 | -0.244 | 0.000 | 0.010 |
| LA | **0.546** | 0.553 | 0.539 | 0.550 | 0.536 | 0.556 | 0.623 | 0.516 | -0.030 | -0.030 | -0.000 | 0.014 |
| MM | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| MY | **20.818** | 20.822 | 20.815 | 20.814 | 20.811 | 20.825 | 23.732 | 20.827 | 0.008 | 0.008 | 0.000 | 0.010 |
| PH | **17.984** | 17.984 | 17.984 | 17.984 | 17.984 | 17.984 | 20.501 | 17.984 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.300** | 7.298 | 7.303 | 7.302 | 7.298 | 7.303 | 8.322 | 7.300 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **33.328** | 33.315 | 33.341 | 33.325 | 33.315 | 33.341 | 37.992 | 33.877 | 0.549 | 0.549 | 0.000 | 0.013 |
| TL | **0.357** | 0.357 | 0.357 | 0.357 | 0.357 | 0.357 | 0.407 | 0.357 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.573** | 61.572 | 61.574 | 61.573 | 61.572 | 61.574 | 70.190 | 61.298 | -0.276 | -0.276 | 0.000 | 0.010 |
| BUNKER | **76.497** | 76.497 | 76.497 | 76.497 | 76.497 | 76.497 | 87.203 | 76.497 | -0.000 | 0.000 | 0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.000 | 0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 76.497 bn；余量 29.949 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
