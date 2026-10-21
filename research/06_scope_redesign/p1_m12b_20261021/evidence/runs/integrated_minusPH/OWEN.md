# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusPH；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusPH_2920_3h_unsolved.nc`（SHA256 `b0ab59ad6322…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusPH`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 290.048 bn，目标值 290.048 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 1.94e-11 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusPH/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.329** | 0.329 | 0.329 | 0.329 | 0.329 | 0.329 | 0.375 | 0.329 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **82.537** | 82.539 | 82.535 | 82.537 | 82.535 | 82.539 | 94.088 | 82.532 | -0.004 | -0.004 | 0.000 | 0.010 |
| KH | **4.327** | 4.331 | 4.323 | 4.328 | 4.323 | 4.331 | 4.933 | 4.058 | -0.270 | -0.270 | 0.000 | 0.010 |
| LA | **0.532** | 0.539 | 0.525 | 0.535 | 0.522 | 0.542 | 0.606 | 0.459 | -0.073 | -0.073 | 0.000 | 0.014 |
| MM | **2.800** | 2.812 | 2.788 | 2.806 | 2.788 | 2.813 | 3.192 | 2.845 | 0.045 | 0.045 | 0.000 | 0.010 |
| MY | **20.937** | 20.941 | 20.933 | 20.933 | 20.930 | 20.944 | 23.867 | 20.942 | 0.004 | 0.004 | 0.000 | 0.010 |
| PH | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.350** | 7.347 | 7.352 | 7.352 | 7.347 | 7.352 | 8.378 | 7.350 | -0.000 | 0.000 | -0.000 | 0.020 |
| TH | **33.350** | 33.325 | 33.375 | 33.342 | 33.325 | 33.375 | 38.017 | 33.936 | 0.586 | 0.586 | 0.000 | 0.013 |
| TL | **0.357** | 0.357 | 0.357 | 0.357 | 0.357 | 0.357 | 0.407 | 0.357 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.571** | 61.570 | 61.571 | 61.570 | 61.570 | 61.571 | 70.188 | 61.283 | -0.287 | -0.287 | 0.000 | 0.010 |
| BUNKER | **75.958** | 75.958 | 75.958 | 75.958 | 75.958 | 75.958 | 86.588 | 75.958 | -0.000 | 0.000 | -0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 75.958 bn；余量 30.488 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
