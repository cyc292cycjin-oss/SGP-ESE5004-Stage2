# S4O-6 整批汇总（只读）

| 运行 | 终止 | 目标 EUR | barrier 迭代 / 秒 / WU | 重启（迭代） | 峰值 RSS | C1 分级 / 验收 | 不通过的门槛（信息） |
|---|---|---|---|---|---|---|---|
| disconnected | suboptimal | 585,495,017,158.94 | 287 / 2201.57 / 2177.96 | 126 | 12.9 GiB | layer1_plus_nodal_price_settlement / False | A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B14, B15, B3, B3_S4B |
| disconnected_gap | suboptimal | 585,497,545,941.42 | 245 / 1919.55 / 1866.56 | 124 | 13.2 GiB | layer1_plus_nodal_price_settlement / False | A1_A2, A1_A2_S4B, A3, A3_S4B, B12, B14, B15, B3, B3_S4B |
| integrated_nze | suboptimal | 425,761,150,197.18 | 216 / 5238.26 / 3638.01 | 无 | 15.2 GiB | layer1_plus_nodal_price_settlement / False | A1_A2, A1_A2_S4B, A3, A3_S4B, B1, B12, B14, B15, B2, B3, B3_S4B |

- **B6（本批不互联 − 试点一体化）：69.2429 bn EUR**（相对 0.1341）；L23（筛查未验证）68.9696 bn

| 国 / 实体 | 不互联 − 一体化 bn（S4O） | L23 bn |
|---|---|---|
| ASEAN_BUNKER | -1.2155 | -1.2188 |
| ASEAN_POOL | -0.0004 | -0.0002 |
| BN | 0.1143 | 0.1143 |
| ID | 0.6692 | 0.6693 |
| KH | 2.4263 | 2.4261 |
| LA | 2.7384 | 2.7403 |
| MM | 1.1311 | 1.1328 |
| MY | 3.2056 | 3.2101 |
| PH | 0.0098 | 0.0099 |
| SG | 0.9324 | 0.9319 |
| TH | 7.5131 | 7.5101 |
| TL | 0.1234 | 0.1237 |
| VN | 51.5950 | 51.3202 |

- **NZE − 一体化（本批 NZE − 试点一体化）：-90.4910 bn EUR**（相对 -0.1753）；L23 -90.4616 bn
