# Gate2 validation report

测试代码 HEAD：`1c77884f9b38445e148608ee199994e4ed57d3e5`。环境复用 WSL pypsa-earth：Python3.11.13、PyPSA0.30.3、pandas2.3.1、numpy1.26.4。没有改环境、没有运行任何 solver。

| 检查 | 结果 | 证据 |
|---|---|---|
| 原 shipping allocation/guard | 17/17 PASS | shipping_17.json / shipping.log |
| 原 Buildings combined strict | 1062/1062 PASS | buildings_1062.json / buildings.log |
| 新 Gate2 contracts + pinned-source/config/mutation tests | 70/70 PASS | gate2_all.log |
| Gate1 static suite | 20/20 PASS | gate1_static_20.log |
| Gate1 run-manifest schema methods | 7/7 PASS | gate1_schema.log |
| 9 CSV deterministic reconstruction | exact byte equality | CSV_REBUILD_SHA256.json |
| 原始文件 SHA256 再核验 | 4/4 source capsules PASS | gate2_rebuild.log / sources/manifest.json |
| 实际 Research config 消费 + six-table consistency | PASS | RESEARCH_CONFIG_CHECK.json |
| 未接受的真实 country/year materialisation | 44/44 拒绝 | BUILD_REPORT.json |
| 真实 source→sector | 217 个非空数值行转换核对 | conservation matrix |
| 真实 node→time 全链闭合 | PENDING | matrix 中按行标记 |

70 个测试含：重复身份/owner、typed boolean、unknown/NaN/inf/negative、文本零、原始 NaN、A* 未扣减/伪造转移/重复/超额、embedded/explicit、fixed/endogenous、bunker/domestic、CO2 无 energy、无效 destination、road share 量纲、country weights、snapshot weights、年总量、空时间形状、源 hash tamper、配置启用 legacy target、missing TL、44 thermal embedded、四类 bunker、真实全 future 未编数。

Synthetic conservation 使用明确标记的测试数值；不是 ASEAN 参数、实验结果或 solved network。气象/真实 GIS 和 accepted allocation 尚未验证。环境已有 PROJ database warning 如前；本轮静态/缓存测试通过不消除后续 GIS readiness 风险。

账本 1518 行，其中 accepted numeric=0；blocker CSV 1977 行（同一决策扩展到多国/多年，不能理解为同数量独立资料请求）。来源状态与表示冻结分别记录。

初轮 60、扩展 66、最终 70 是同一实现逐步增加防绕过测试的记录；对外最终结果采用 70。shipping/Buildings 后续代码未变，未重复跑正式实验。
