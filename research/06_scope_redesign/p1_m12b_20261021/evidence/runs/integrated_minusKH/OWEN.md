# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：M12B_integrated_minusKH；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/variants/integrated_minusKH_2920_3h_unsolved.nc`（SHA256 `1d6eb114eb06…`）；对偶 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusKH`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展，第 138 项 C1 同口径）：11 国 + 燃料舱 = 304.043 bn，目标值 304.043 bn，差 -0.000 bn（|差| ≤ 0.01 bn：**True**；相对误差 5.96e-10 仅供参考）；共享 0.000 bn。
- 残差影响 ≤ C1 (b) 阈值 max(差额 1 %, 0.01 bn)：**True**；对偶形式验收：**True**。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m12b/integrated_minusKH/PRECISION.json: this batch: disconnected - integrated ledger difference (/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/res。
- 差额方法：exported arrays: exact decomposition by owner (KVL rows; other rows' complementarity; column complementarity; stationarity residual)。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.331** | 0.331 | 0.331 | 0.331 | 0.331 | 0.331 | 0.377 | 0.331 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **82.326** | 82.328 | 82.324 | 82.326 | 82.324 | 82.328 | 93.848 | 82.319 | -0.007 | -0.007 | 0.000 | 0.010 |
| KH | **0.000** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.010 |
| LA | **0.533** | 0.542 | 0.525 | 0.537 | 0.525 | 0.542 | 0.608 | 0.446 | -0.087 | -0.087 | 0.000 | 0.014 |
| MM | **2.833** | 2.845 | 2.820 | 2.838 | 2.820 | 2.846 | 3.229 | 2.880 | 0.047 | 0.047 | 0.000 | 0.010 |
| MY | **20.956** | 20.960 | 20.952 | 20.952 | 20.949 | 20.963 | 23.889 | 20.963 | 0.007 | 0.007 | 0.000 | 0.010 |
| PH | **17.950** | 17.950 | 17.950 | 17.950 | 17.950 | 17.950 | 20.462 | 17.950 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **7.338** | 7.335 | 7.340 | 7.340 | 7.335 | 7.340 | 8.364 | 7.338 | 0.000 | 0.000 | 0.000 | 0.020 |
| TH | **33.674** | 33.650 | 33.698 | 33.667 | 33.650 | 33.698 | 38.387 | 34.065 | 0.391 | 0.391 | 0.000 | 0.013 |
| TL | **0.357** | 0.357 | 0.357 | 0.357 | 0.357 | 0.357 | 0.407 | 0.357 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **61.672** | 61.672 | 61.672 | 61.672 | 61.672 | 61.672 | 70.304 | 61.322 | -0.351 | -0.351 | 0.000 | 0.010 |
| BUNKER | **76.073** | 76.073 | 76.073 | 76.073 | 76.073 | 76.073 | 86.720 | 76.073 | 0.000 | 0.000 | 0.000 | 0.021 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | 0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 76.073 bn；余量 30.373 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
