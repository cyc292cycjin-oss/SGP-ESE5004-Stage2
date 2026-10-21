# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：S4O6_DISCONNECTED_365x24h；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds/disconnected/disconnected_365_24h_unsolved.nc`（SHA256 `b411223e85c7…`）；对偶 `/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/disconnected/DUALS_BY_CONSTRAINT.nc`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展）：11 国 + 燃料舱 = 585.496 bn，目标值 585.495 bn，相对误差 1.30e-06（≤ 1e-6：**False**）；共享 0.000 bn。
- C1 (c)（运行本身）：True；分摊可用：**False**。阈值来源：/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/disconnected/PRECISION.json: this batch: disconnected - integrated ledger difference (/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnec。
- 差额方法：rows-only duals: KVL transfer from the solved line flows (p0; the loss proxy makes p0 differ slightly from the LP variable), residual = difference - KVL。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.879** | 0.879 | 0.879 | 0.879 | 0.879 | 0.879 | 1.002 | 0.879 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **159.247** | 159.247 | 159.247 | 159.247 | 159.247 | 159.247 | 181.534 | 159.247 | -0.000 | 0.000 | -0.000 | 0.010 |
| KH | **5.205** | 5.205 | 5.205 | 5.205 | 5.205 | 5.205 | 5.934 | 5.205 | 0.000 | -0.000 | 0.000 | 0.024 |
| LA | **1.356** | 1.356 | 1.356 | 1.356 | 1.356 | 1.356 | 1.546 | 1.356 | 0.000 | 0.000 | 0.000 | 0.027 |
| MM | **3.833** | 3.833 | 3.833 | 3.833 | 3.833 | 3.833 | 4.370 | 3.833 | 0.000 | 0.000 | 0.000 | 0.011 |
| MY | **69.841** | 69.841 | 69.841 | 69.841 | 69.841 | 69.841 | 79.615 | 69.841 | -0.000 | 0.000 | -0.000 | 0.032 |
| PH | **22.472** | 22.472 | 22.472 | 22.472 | 22.472 | 22.472 | 25.618 | 22.472 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **22.045** | 22.045 | 22.045 | 22.045 | 22.045 | 22.045 | 25.130 | 22.045 | -0.000 | 0.000 | -0.000 | 0.010 |
| TH | **61.905** | 61.905 | 61.905 | 61.905 | 61.905 | 61.905 | 70.569 | 61.905 | -0.000 | -0.006 | 0.006 | 0.075 |
| TL | **0.009** | 0.009 | 0.009 | 0.009 | 0.009 | 0.009 | 0.010 | 0.009 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **162.227** | 162.227 | 162.227 | 162.227 | 162.227 | 162.227 | 184.931 | 162.226 | -0.000 | 0.000 | -0.000 | 0.516 |
| BUNKER | **76.477** | 76.477 | 76.477 | 76.477 | 76.477 | 76.477 | 87.180 | 76.477 | 0.000 | 0.000 | 0.000 | 0.012 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 76.477 bn；余量 29.969 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
