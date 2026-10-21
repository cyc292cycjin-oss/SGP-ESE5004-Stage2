# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusID；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusID_2920_3h_unsolved.nc`（SHA256 `fe9c825f92b7…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusID`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 231.845 bn，目标值 231.845 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 4.50e-11 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusID/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.428** | 0.428 | 0.428 | 0.428 | 0.428 | 0.428 | 0.488 | 0.428 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| KH | **4.271** | 4.275 | 4.266 | 4.271 | 4.266 | 4.275 | 4.868 | 3.963 | -0.308 | -0.308 | 0.000 | 0.010 |
| LA | **0.365** | 0.372 | 0.358 | 0.369 | 0.355 | 0.375 | 0.416 | 0.303 | -0.062 | -0.062 | 0.000 | 0.014 |
| MM | **2.552** | 2.564 | 2.539 | 2.557 | 2.539 | 2.564 | 2.909 | 2.588 | 0.037 | 0.037 | 0.000 | 0.010 |
| MY | **20.029** | 20.035 | 20.024 | 20.026 | 20.024 | 20.035 | 22.833 | 20.029 | 0.000 | 0.000 | 0.000 | 0.010 |
| PH | **16.981** | 16.981 | 16.981 | 16.981 | 16.981 | 16.981 | 19.357 | 16.981 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **8.063** | 8.060 | 8.066 | 8.065 | 8.060 | 8.066 | 9.192 | 8.063 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **32.266** | 32.241 | 32.291 | 32.258 | 32.241 | 32.291 | 36.782 | 32.929 | 0.662 | 0.662 | 0.000 | 0.013 |
| TL | **0.381** | 0.381 | 0.381 | 0.381 | 0.381 | 0.381 | 0.434 | 0.381 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.316** | 61.315 | 61.317 | 61.316 | 61.315 | 61.317 | 69.897 | 60.986 | -0.330 | -0.330 | 0.000 | 0.010 |
| BUNKER | **85.193** | 85.193 | 85.193 | 85.193 | 85.193 | 85.193 | 97.116 | 85.193 | 0.000 | 0.000 | 0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | 0.000 | 0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 85.193 bn；余量 21.253 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
