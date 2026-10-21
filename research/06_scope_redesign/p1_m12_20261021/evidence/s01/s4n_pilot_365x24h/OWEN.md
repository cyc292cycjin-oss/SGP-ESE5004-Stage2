# OWEN（M12：Owen 分摊主值 = 对偶形式 y′b；补充 01 D1；只读，未求解）

- 运行：S4N_PILOT_365x24h；网络 `/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds/integrated/integrated_365_24h_unsolved.nc`（SHA256 `4206ec5c5d88…`）；对偶 `/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/full/export/integrated/DUALS_BY_CONSTRAINT.nc`。
- Owen 前提（右端项全部有主）：**True**。
- 恒等式（C1 (c) 对偶形式扩展）：11 国 + 燃料舱 = 516.252 bn，目标值 516.252 bn，相对误差 1.24e-07（≤ 1e-6：**True**）；共享 0.000 bn。
- C1 (c)（运行本身）：True；分摊可用：**True**。阈值来源：/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/top/pilot_integrated/PRECISION.json: this batch: disconnected - integrated ledger difference (/root/autodl-tmp/s4o_cloud/runs/20261019T162951Z_6896/disconnec。
- 差额方法：rows-only duals: KVL transfer from the solved line flows (p0; the loss proxy makes p0 differ slightly from the LP variable), residual = difference - KVL。

| 参与者 | **对偶形式 α 0.5** | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 | USD2020 | 市场形式 α 0.5 | 市场 − 对偶 | 其中 KVL 转移 | 残差影响 | C1 (b) 阈值 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BN | **0.765** | 0.765 | 0.765 | 0.765 | 0.765 | 0.765 | 0.872 | 0.765 | 0.000 | 0.000 | 0.000 | 0.010 |
| ID | **158.611** | 158.613 | 158.609 | 158.611 | 158.609 | 158.613 | 180.809 | 158.578 | -0.034 | -0.032 | -0.001 | 0.010 |
| KH | **2.785** | 2.789 | 2.781 | 2.786 | 2.781 | 2.789 | 3.175 | 2.779 | -0.006 | -0.007 | 0.002 | 0.024 |
| LA | **-1.126** | -1.118 | -1.133 | -1.122 | -1.136 | -1.115 | -1.283 | -1.382 | -0.257 | -0.257 | 0.001 | 0.027 |
| MM | **2.660** | 2.661 | 2.660 | 2.661 | 2.660 | 2.661 | 3.033 | 2.702 | 0.042 | 0.044 | -0.002 | 0.011 |
| MY | **66.602** | 66.747 | 66.456 | 66.596 | 66.453 | 66.751 | 75.923 | 66.635 | 0.034 | 0.034 | -0.000 | 0.032 |
| PH | **22.463** | 22.463 | 22.463 | 22.463 | 22.463 | 22.463 | 25.606 | 22.463 | 0.000 | 0.000 | 0.000 | 0.010 |
| SG | **21.112** | 21.110 | 21.115 | 21.115 | 21.110 | 21.115 | 24.067 | 21.112 | 0.000 | 0.000 | 0.000 | 0.010 |
| TH | **54.428** | 54.272 | 54.583 | 54.426 | 54.272 | 54.583 | 62.045 | 54.391 | -0.036 | -0.038 | 0.002 | 0.075 |
| TL | **-0.115** | -0.115 | -0.115 | -0.115 | -0.115 | -0.115 | -0.131 | -0.115 | 0.000 | 0.000 | 0.000 | 0.010 |
| VN | **110.375** | 110.374 | 110.376 | 110.374 | 110.374 | 110.376 | 125.822 | 110.631 | 0.257 | 0.264 | -0.007 | 0.516 |
| BUNKER | **77.692** | 77.692 | 77.692 | 77.692 | 77.692 | 77.692 | 88.565 | 77.692 | 0.000 | 0.000 | 0.000 | 0.012 |
| SHARED | **0.000** | 0.000 | 0.000 | 0.000 | — | — | 0.000 | -0.000 | -0.000 | 0.000 | -0.000 | — |

区间：每条跨境线（国家对行的 y′b 与该对的目标常数）的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国端点不能同时达到。

## 燃料舱参与者：严格单独成本（补充 01 D10）

- 严格单独成本（只用区域外非化石进口经计量链路满足燃料舱负荷；纯算术）= **106.446 bn**；Owen 对偶形式份额 77.692 bn；余量 28.753 bn；份额 ≤ 单独成本：**True**。
- ASEAN aviation international oil final：35.959 bn，239.55 TWh，单位成本 150.11–150.11 EUR/MWh，路线 ['ASEAN oil non-fossil import -> ASEAN aviation international oil meter non-fossil']；排除 ['ASEAN aviation international oil meter']
- ASEAN shipping international methanol final：70.487 bn，485.59 TWh，单位成本 145.16–145.16 EUR/MWh，路线 ['ASEAN methanol import -> ASEAN shipping international methanol']；排除 []
