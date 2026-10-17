# S4E 报告：补齐相邻跨境走廊（第 94 项）、统一 CO₂ 封存单价与船运细节（第 95 项），冒烟与重建部署包

**分支** `codex/s4e-corridors-storage-20261017`，自 S4D 最终提交 0429a0eb 开出；**draft PR** [cyc292cycjin-oss/SGP-ESE5004-Stage2#29](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/29)，叠在 #28 上；指令 `S4E_CLAUDE_CODE_INSTRUCTION.md`，SHA256 e5c184c1…bb7e9db，已核对。证据等级：VERIFIED（实际数组或回执）、EXACT（逐项核验）、INFERENCE（机理解释）、PROPOSED（未执行）。

## 摘要

1. **第 94 项：** 49 对陆上相邻节点对中新增 31 条交流候选；另有 APG 跨海 #4 / #7 / #16 三条直流候选、国内 #3 / #18a / #18b 三条直流候选。走廊图从 11 条边增至 14 条，BN、PH、TL 都已接入，11 国连通。存量只有 TH–MY 与 APG 不一致（2,646 vs 380 MW），已列出，未改动。
2. **第 95 项：** 所有地质封存统一按 30 EUR/t 计，东盟外为 54.70 EUR/t；船运改用逐对海上距离；老挝过境后可以船运进东盟各国封存（42 条链路）。过境口径与 LNG 不设上限两项敏感性已构建核对，未运行。
3. **冒烟（档案 A，56×3h）：** 三项都最优，目标值较 S4D 低 3.1–4.8 %。东盟外封存降为 0，CO₂ 改为在东盟内船运封存，每年 144 / 284 / 153 Mt。新走廊在一体化中全部建设，约 301 GW；BN、PH、TL 都有了跨境交换。
4. **门槛：** B5、B6（466.6 亿 EUR，6.9 %）、B16（相对误差 ≤ 7.6e-12）通过。不互联在新口径下全部门槛通过；一体化与 NZE 只有 A1_A2_S4B 未过，是 `Line-s` 残差，与以前同一性质。
5. **不互联 − 一体化分国差额（bn EUR）：** VN 20.4、MY 7.5、TH 4.8、SG 3.1、LA 2.6、KH 2.3、ID 2.1、MM 0.8、BN 0.6、TL 0.14、PH −0.6。BN、TL 第一次有了互联价值。
6. **部署包：** 已重建到 S4E 最终代码提交 a3d58a46，上传 232,117,286 B（221 MiB）。365×24h 单运行 25–52 分钟，串行 1.6–2.3 小时；预检内存下限上调为 36 / 72 / 104 GiB。联盟研究的运行量增至 383 个联盟，约 160–330 小时。
7. **需要用户决定 7 项**（§7），其中最关键的是：新候选走廊是否设容量上限（冒烟中建设规模远超 APG 规划），以及 TH–MY 存量。

## 1. 执行概况

| 节 | 内容 | 提交 | 测试 |
|---|---|---|---|
| S4E-0 | 登记对 S4D §9 八项的答复与联盟运行规则 | 8c67e792 | 479 通过 |
| S4E-1 | 补齐相邻跨境走廊（第 94 项） | 55780f9f | 485 通过 |
| S4E-2 | 统一封存单价与船运细节（第 95 项） | 2bfafb91 | 488 通过 |
| S4E-3 | 冒烟（三项，档案 A） | a3d58a46 | — |
| S4E-4 | 部署网络重建、打包、资源估算、交付 | 本交付提交（哈希见 `S4E_PROGRESS.md`） | 488 通过（`tests/research`） |

- 没有触发任何停止条件：走廊判定都清楚，最短共享边界 4.18 km，没有落在 0–1 km 之间的情形；存量冲突能判断（TH–MY 已列出）；BN、PH、TL 都已接入。
- 本步没有下载。没有连接云端，也没有做正式求解。本机计算单次 ≤ 5 分钟，峰值内存 ≤ 4.1 GiB。

## 2. 第 94 项：补齐相邻跨境走廊（S4E-1）

### 2.1 规则（注册表 `s4e1_corridor_rules`，脚本 `scripts_project/s4e_1_corridors.py`）

- **陆上相邻：** 不同国家节点的陆上区域（S4A 的 Voronoi 区域）共享边界 ≥ 1 km 即为相邻。判定时取一个区域的边界，与另一个区域外扩 1 km 后相交，以吸收国界形状没对齐的误差。1 km 门槛与 S4D-1 沿海判定的"角点接触"规则一致。
- **跨海：** 只加 ACE（2024）APG AIMS III 优先清单中的跨海项目，端点取两端区域最近的节点对；最近对已是陆上相邻对的不重复。"other initiative" 只登记为可选候选。
- **参数：** 沿用已有方法。
  - 线型：两端母线在同一陆块用交流线，否则用直流链路，对应补充 01 的同陆块判定。
  - 长度：大圆距离 × 1.25。
  - 海底份额：补充 01 规则。`SUBSEA_SHARE_S4E1.csv` 保留原表 133 行不变，另补新节点对。
  - 成本：第 50 项成本层；交流线 46.5 EUR/(MW·km·a)，直流另加换流站对。
  - 氢 / CO₂ / 气候选沿电力拓扑生成（第 59 项）。
  - 初始容量都是 0，可扩展。
- **开关：** `research.corridors.adjacency_completion: on`（主算）| `off`（原走廊表）。`off` 构建与 S4D-6 一体化网络逐组件完全一致（VERIFIED）。
- **第二遍补算：** 新拓扑会改变气网的连通性补齐（PyPSA-Eur 规则：没有管道候选的气母线，连到本国最近有候选的节点），由此多出 1 个国内节点对 ID_Nusa-Tenggara13 0–15 0。先用海底份额为 0 的构建取得完整拓扑，再用同一方法补算这一对。

### 2.2 陆上相邻判定表（49 对，`ADJACENCY_S4E1.csv`，VERIFIED）

| 国家对 | 节点 A | 节点 B | 共享边界（km） | 判定 | 新候选长度（km） |
|---|---|---|---|---|---|
| BN–MY | BN4 0 | MY_Sarawak4 2 | 418.0 | 新增交流候选 | 63 |
| ID–MY | ID_Kalimantan4 2 | MY_Sarawak4 1 | 391.3 | 新增交流候选 | 369 |
| ID–MY | ID_Kalimantan4 1 | MY_Sarawak4 2 | 349.4 | 新增交流候选 | 326 |
| ID–MY | ID_Kalimantan4 0 | MY_Sarawak4 0 | 204.0 | 新增交流候选 | 552 |
| ID–MY | ID_Kalimantan4 1 | MY_Sabah4 1 | 168.7 | 新增交流候选 | 212 |
| ID–MY | ID_Kalimantan4 8 | MY_Sarawak4 1 | 156.8 | 已有走廊（线路 23） | — |
| ID–MY | ID_Kalimantan4 10 | MY_Sarawak4 0 | 121.8 | 新增交流候选 | 573 |
| ID–MY | ID_Kalimantan4 10 | MY_Sarawak4 1 | 115.0 | 新增交流候选 | 597 |
| ID–MY | ID_Kalimantan4 1 | MY_Sarawak4 0 | 76.5 | 新增交流候选 | 479 |
| ID–MY | ID_Kalimantan4 9 | MY_Sarawak4 0 | 69.2 | 新增交流候选 | 534 |
| ID–MY | ID_Kalimantan4 1 | MY_Sabah4 0 | 4.9 | 新增交流候选 | 327 |
| ID–TL | ID_Nusa-Tenggara15 0 | TL11 0 | 226.9 | 新增交流候选 | 256 |
| KH–LA | KH2 1 | LA2 4 | 477.0 | 已有走廊（线路 43） | — |
| KH–TH | KH2 4 | TH2 1 | 256.0 | 新增交流候选 | 385 |
| KH–TH | KH2 4 | TH2 3 | 216.0 | 已有走廊（线路 47） | — |
| KH–TH | KH2 2 | TH2 3 | 162.8 | 新增交流候选 | 349 |
| KH–TH | KH2 1 | TH2 1 | 100.0 | 新增交流候选 | 480 |
| KH–VN | KH2 3 | VN2 5 | 308.9 | 新增交流候选 | 265 |
| KH–VN | KH2 1 | VN2 7 | 232.7 | 新增交流候选 | 405 |
| KH–VN | KH2 3 | VN2 0 | 162.9 | 新增交流候选 | 248 |
| KH–VN | KH2 1 | VN2 4 | 144.7 | 新增交流候选 | 398 |
| KH–VN | KH2 1 | VN2 5 | 119.7 | 新增交流候选 | 320 |
| KH–VN | KH2 0 | VN2 0 | 84.4 | 已有走廊（线路 39） | — |
| LA–MM | LA2 5 | MM2 13 | 229.5 | 已有走廊（线路 APG17_LA_MM） | — |
| LA–TH | LA2 2 | TH2 4 | 391.6 | 已有走廊（线路 56） | — |
| LA–TH | LA2 5 | TH2 4 | 337.0 | 已有走廊（线路 66） | — |
| LA–TH | LA2 3 | TH2 1 | 260.3 | 已有走廊（线路 58） | — |
| LA–TH | LA2 4 | TH2 1 | 223.0 | 已有走廊（线路 61） | — |
| LA–TH | LA2 0 | TH2 1 | 222.8 | 已有走廊（线路 49） | — |
| LA–TH | LA2 2 | TH2 1 | 207.7 | 已有走廊（线路 55） | — |
| LA–TH | LA2 1 | TH2 4 | 89.6 | 已有走廊（线路 53） | — |
| LA–VN | LA2 3 | VN2 3 | 604.7 | 已有走廊（线路 60） | — |
| LA–VN | LA2 5 | VN2 1 | 348.9 | 新增交流候选 | 390 |
| LA–VN | LA2 4 | VN2 2 | 295.7 | 已有走廊（线路 63） | — |
| LA–VN | LA2 0 | VN2 2 | 271.4 | 新增交流候选 | 283 |
| LA–VN | LA2 1 | VN2 1 | 263.9 | 新增交流候选 | 416 |
| LA–VN | LA2 1 | VN2 3 | 115.1 | 新增交流候选 | 420 |
| LA–VN | LA2 0 | VN2 3 | 48.3 | 新增交流候选 | 440 |
| LA–VN | LA2 4 | VN2 7 | 17.6 | 已有走廊（线路 64） | — |
| MM–TH | MM2 4 | TH2 4 | 470.5 | 已有走廊（线路 APG11_TH_MM） | — |
| MM–TH | MM2 4 | TH2 2 | 438.3 | 新增交流候选 | 454 |
| MM–TH | MM2 4 | TH2 3 | 315.3 | 新增交流候选 | 647 |
| MM–TH | MM2 10 | TH2 4 | 242.8 | 新增交流候选 | 490 |
| MM–TH | MM2 7 | TH2 4 | 237.0 | 新增交流候选 | 558 |
| MM–TH | MM2 13 | TH2 4 | 169.7 | 新增交流候选 | 593 |
| MM–TH | MM2 4 | TH2 5 | 145.8 | 新增交流候选 | 1106 |
| MM–TH | MM2 6 | TH2 4 | 49.8 | 新增交流候选 | 556 |
| MY–SG | MY_Peninsular2 1 | SG2 0 | 4.2 | 已有走廊（线路 92） | — |
| MY–TH | MY_Peninsular2 0 | TH2 0 | 496.8 | 已有走廊（线路 91;链路 250878579-1_0;链路 250878579-2_0;链路 250878579-3_0;链路 250878579-4_0;链路 Khlong Ngae – Gurun） | — |

新增 31 条交流候选：BN–MY 1、ID–MY 9、ID–TL 1、KH–TH 3、KH–VN 5、LA–VN 5、MM–TH 7。全部同陆块，海底份额 0；ID–TL 两端都在帝汶岛。

### 2.3 APG 跨海与国内项目（`APG_CROSS_SEA_S4E1.csv`、`APG_DOMESTIC_S4E1.csv`）

| APG | 项目 | 端点 | 大圆（km） | 判定 | 下两个候选端点 |
|---|---|---|---|---|---|
| 4 | Peninsular Malaysia - Sumatera | ID_Sumatra2 0 – MY_Peninsular2 1 | 229 | 新增直流候选 | MY_Peninsular2 1-ID_Sumatra3 3 347 km; MY_Peninsular2 0-ID_Sumatra3 2 371 km |
| 7 | Philippines - Sabah | MY_Sabah4 1 – PH_Mindanao6 0 | 682 | 新增直流候选 | PH_Mindanao6 0-MY_Sabah4 0 827 km; PH_Mindanao6 1-MY_Sabah4 1 843 km |
| 15 | East Sabah - North Kalimantan | ID_Kalimantan4 1 – MY_Sabah4 1 | 170 | 并入陆上相邻候选 | MY_Sabah4 0-ID_Kalimantan4 1 263 km; MY_Sabah4 1-ID_Kalimantan4 9 279 km |
| 16 | Singapore - Sumatera (#5 Batam merged) | ID_Sumatra2 0 – SG2 0 | 37 | 新增直流候选 | SG2 0-ID_Sumatra3 4 303 km; SG2 0-ID_Sumatra3 3 362 km |
| other1 | Singapore - Vietnam | SG2 0 – VN2 0 | 975 | 可选（其他倡议，不进主算） | SG2 0-VN2 5 1151 km; SG2 0-VN2 4 1279 km |
| other2 | Singapore - Cambodia | KH2 0 – SG2 0 | 1070 | 可选（其他倡议，不进主算） | SG2 0-KH2 3 1156 km; SG2 0-KH2 2 1163 km |

| APG | 国内项目 | 现有连接 | 端点 | 大圆（km） | 判定 |
|---|---|---|---|---|---|
| 3 | Sarawak - Peninsular Malaysia | — | MY_Peninsular2 1 – MY_Sarawak4 1 | 986 | 新增国内直流候选 |
| 8b | Sarawak - Sabah | 线路 94 | MY_Sabah4 0 – MY_Sarawak4 2 | 219 | 已有国内连接 |
| 18a | Kalimantan - Java | — | ID_Java-Bali1 1 – ID_Kalimantan4 12 | 548 | 新增国内直流候选 |
| 18b | Sumatera - Java | — | ID_Java-Bali1 0 – ID_Sumatra3 1 | 397 | 新增国内直流候选 |

| 直流候选 | 长度（km） | 海底份额 |
|---|---|---|
| APG4 ID_Sumatra2 0 - MY_Peninsular2 1 DC | 285 | 0.12 |
| APG7 MY_Sabah4 1 - PH_Mindanao6 0 DC | 852 | 0.65 |
| APG16 ID_Sumatra2 0 - SG2 0 DC | 46 | 0.55 |
| APG3 MY_Peninsular2 1 - MY_Sarawak4 1 DC | 1234 | 0.86 |
| APG18a ID_Java-Bali1 1 - ID_Kalimantan4 12 DC | 681 | 0.84 |
| APG18b ID_Java-Bali1 0 - ID_Sumatra3 1 DC | 495 | 0.33 |

- **#4 端点说明：** ID_Sumatra2 0 的母线在巴淡岛（104.03E, 1.08N），但其陆上区域约 65 % 位于苏门答腊本岛东岸。按"两端最近的节点"规则取它，#4 与 #16 的印尼端因此相同。替代端点是 ID_Sumatra3 3（北干巴鲁，347 km），列为用户决定事项。
- **国内连接（第 35 项"能跨国不能跨省"的一致性）：** #8b 已有线路 94；#3、#18a、#18b 原本没有任何连接，现作为国内直流候选加入，两个情景都有。

### 2.4 存量核对（`APG_STOCK_CHECK_S4E1.csv`）

| APG | 连接 | APG 存量（MW） | 模型 2025 存量（MW） | 结论 |
|---|---|---|---|---|
| 1 | 马来半岛–新加坡 | 525 | 525（线路 92） | 一致 |
| 2 | 泰国–马来半岛 | 380 | **2,645.6**（交流线 91 为 380；直流 Khlong Ngae–Gurun 300；另有 4 条 OSM 编号 250878579 的直流链路各 491.4） | **不一致：列出，未改动** |
| 6 | 砂拉越–西加里曼丹 | 230 | 230（线路 23，已在表中，不需补入） | 一致 |
| 9 | 泰国–老挝 | 955 | 955（9 条线合计） | 一致 |
| 10 | 老挝–越南 | — | 1.0（4 条名义容量线） | APG 未列存量，可忽略 |
| 12 | 越南–柬埔寨 | 200 | 200（线路 39） | 一致 |
| 13 | 老挝–柬埔寨 | 300 | 300（线路 43） | 一致 |
| 14 | 泰国–柬埔寨 | 250 | 250（线路 47） | 一致 |
| 17 | 老挝–缅甸 | 30 | 30（APG17_LA_MM） | 一致 |

TH–MY 的差异与 S3 报告的结论相同。冻结底网中这 4 条约 491 MW 的直流链路，很可能是同一条 300 MW 双极直流在 OSM 中的重复记录（INFERENCE）。按指令不改动已核实的存量，是否按 APG 订正交由用户决定（§7）。

### 2.5 走廊图与联盟

- **边：** 11 → 14 条，新增 BN–MY、ID–TL、MY–PH；11 国连成一个整体，没有孤立国家。
- **成员 ≥ 2 的连通联盟：** 81 → **383** 个，按规模 2–11 依次为 14 / 23 / 36 / 57 / 78 / 80 / 58 / 28 / 8 / 1。连单元素在内共 394 个。
- **构建（VERIFIED）：**
  - 一体化：跨境交流线 21 → 52，直流 5 → 8；氢 / CO₂ 跨境管道 21 → 55，气 27 → 61。
  - 不互联：跨境组件 0，三条国内直流保留。
- **账本：** 新的境内长度分摊表 `XB_LENGTH_SHARES_S4E1.csv` 覆盖 231 个跨境组件，账本默认读这张表。

## 3. 第 95 项：统一封存单价与船运细节（S4E-2）

- **(a) 封存单价统一（注册表 `co2_extra_asean_storage_cost_unified`，对第 89 项单价构成的修改）：**
  - 东盟外 = IEAGHG 2004 船运 4,500 km 24.698 + 统一封存 30（PyPSA-Eur `sector.co2_sequestration_cost`）= **54.698 EUR2020/t**；±50 % 作用于它。
  - 国内 store、东盟内船运的接收国与东盟外读同一个配置值 `s2.co2.sequestration_cost_eur_per_t`。ZEP 敏感性 `=16.0535` 因此同时作用于全部封存，构建核对：国内 16.05，东盟外 40.75。
  - 理由：同一种地质封存不应因所在地不同而用不同口径的成本，否则封存业务会被系统性地推到东盟外（工作原则第 8 条）。
- **(b) 航线距离：** 主算 `co2.ship_distance: sea_path`，按逐对最短海上航线计价，船运段 11.54–26.75 EUR/t；`route_factor`（大圆 × 1.091）作对照，单价 11.54–26.89。
- **(c) 老挝过境后船运：**
  - 每个老挝节点经铁路到最近海岸点所在的越南沿海节点（VN2 2 / VN2 3），再沿该节点的航线进入 BN、ID、KH、MY、PH、TH、TL 的国内封存，共 42 条 `CO2 transit ship` 链路，标为海运贸易；
  - 单价 25.6–48.0 EUR/t，另加接收国封存 30；
  - 局限：经越南海岸进入越南国内封存不在船运航线中，指令只定义了"其他国家"。
- **(d) 过境口径敏感性：** `co2.lao_transit_destination=existing_port`、`co2.lao_transit_mode=truck`。两项合用时陆运段 56–101 EUR/t，构建核对。
- **(e) LNG 不设上限：** 新模式 `s3.gas.lng_expansion=uncapped_cost`，16 个接收站无上限，扩建按 7,018 EUR/MW/a 计价；B14 在该模式下不设上限，核对通过。
- **(f) 联盟运行规则：** 已登记（`coalition_run_rule`），并写入 `CLOUD_DEPLOY_STEPS.md` §11 与部署包清单。

## 4. 冒烟（S4E-3，档案 A，56×3h，提交 2bfafb91）

| 运行 | 状态 | 目标（EUR） | 相对 S4D | LP 列 / 非零元 | barrier | 墙钟 / 峰值 |
|---|---|---|---|---|---|---|
| 一体化 STEPS | optimal | 6.30166e11 | −211 亿（−3.2 %） | 648,364 / 3.22 M | 120 次 / 165 s | 225 s / 3.86 GiB |
| 不互联 STEPS | optimal | 6.76828e11 | −218 亿（−3.1 %） | 635,197 / 3.14 M | 98 次 / 108 s | 166 s / 3.63 GiB |
| 一体化 NZE | optimal | 5.30241e11 | −268 亿（−4.8 %） | 648,364 / 3.22 M | 126 次 / 171 s | 225 s / 3.88 GiB |

- **新走廊建设（一体化，VERIFIED）：** 37 个新组件全部建设，合计约 301 GW（NZE 286 GW）。
  - 最大的几项：#18a 加里曼丹–爪哇（国内直流）40.5 GW、ID_Kalimantan4 9–MY_Sarawak4 0 22.9 GW、KH2 2–TH2 3 21.7 GW、LA2 0–VN2 3 15.8 GW、KH2 1–TH2 1 14.7 GW、KH2 3–VN2 0 13.8 GW、ID_Kalimantan4 1–MY_Sabah4 1 12.2 GW、MM2 4–TH2 5 12.1 GW。
  - APG 跨海：#7 MY–PH 5.4 GW、#16 ID–SG 4.5 GW、#4 ID–MY 0.49 GW；BN–MY 2.4 GW；ID–TL 0.21 GW。
  - 跨境管道有建设的：氢 22 条、CO₂ 16 条、气 34 条。
  - 这些规模远超 APG 的规划容量。例如 TH–KH 项目合计 900 MW、2040 年预测 1,315 MW；#18a 的 2040 年预测 435 MW。冒烟只有一月的一周（56 个时段），规模不能据此判断（§7 第 1 项）。
- **国内候选（两个情景都有）：** 不互联中 #18a 79.3 GW、#18b 3.9 GW、#3 0.1 GW。这是两个情景目标值都下降约 210–220 亿的主要原因：ID 不互联账本 222.2 → 205.6 bn。
- **BN / PH / TL 跨境交换（一体化）：** BN 进口 12.0 TWh；PH 进口 19.1、出口 18.8 TWh；TL 进口 0.31、出口 0.51 TWh。不互联中均为 0。
- **CO₂（与 S4D 对比）：**

| 运行 | 东盟内船运（Mt/a） | 运费（亿 EUR） | 东盟外封存（Mt/a，S4D） | 主要流向 |
|---|---|---|---|---|
| 一体化 | 144.4 | 20.9 | **0**（181.2） | VN→ID 70.2、VN→MY 58.7、VN→BN 12.5、MM→ID 3.0 |
| 不互联 | 284.0 | 38.8 | **0**（284.1） | SG→ID 92.2、VN→MY 52.4、MM→ID 49.0、VN→TH 41.5、KH→TH 25.9、VN→BN 12.2、LA→PH 5.65、VN→ID 3.2、LA→MY 1.94 |
| 一体化 NZE | 153.2 | 22.2 | **0**（189.1） | VN→ID 79.1、VN→MY 58.7、VN→BN 12.3、MM→ID 3.1 |

- **分国账本与恒等式：** B16 相对误差 3.6e-14 / 7.6e-12 / 4.1e-12；区域池剩余 −0.2 / −5.4 / −2.2 EUR。

| 国家 | BN | PH | TL | KH | LA | MM | SG | MY | ID | TH | VN | 燃料舱 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 不互联 − 一体化（S4E） | 0.59 | −0.61 | 0.14 | 2.27 | 2.64 | 0.82 | 3.12 | 7.54 | 2.10 | 4.77 | 20.43 | 2.84 |
| 同上（S4D） | 0.00 | −0.16 | 0.00 | 2.12 | 2.98 | 0.94 | 2.84 | 11.83 | 0.77 | 5.17 | 20.26 | 0.57 |

合计 46.66 bn EUR，等于 B6 差值（S4D 47.32）。BN、TL 第一次有了互联价值。PH 为负：互联后 PH 按节点对偶价格结算的账本成本略高于不互联，需要在成本分摊研究中关注。

- **门槛：** B5 通过（不互联跨境组件 0）；B6 通过（466.6 亿，6.9 %）。不互联在新口径下全部门槛通过；一体化与 NZE 只有 A1_A2_S4B 未过（`Line-s` 平稳性 39 / 37 个，同一性质）。
- **局限：** 冒烟只有 56 个时段，风光与互联规模不能据此判断（第 47 项）。装机发电对比文件沿用了 S4C 的文件名后缀 `_VS_S4C`，对比基准实际是 S4D 冒烟。

## 5. 云端部署包（S4E-4）

- **网络：**
  - 在 S4E 最终代码提交 a3d58a46 上重建四个网络，每个都有 2920×3h 与 365×24h 两种分辨率：一体化、不互联、一体化 NZE、不互联诊断。重建时工作树干净（`evidence/s4e_4/STATUS.txt`，dirty:0）。
  - 每次构建约 55 s、0.7 GB；网络哈希前缀 f9b7 / 91f9 / 4892 / b0b6。
  - 一体化、不互联、NZE 三个 2920×3h 网络与 S4E-3 冒烟所用网络逐组件比对，静态表与时间序列完全一致（`COMPARE_*: {}`，VERIFIED）。
- **包：** `work/p1_step4e_20261017/cloud_package_dist/`。
  - 代码 `code_a3d58a46.tar.gz`；共 15 个文件，上传总量 **232,117,286 B**（221.4 MiB），见 `PACKAGE_MANIFEST.json`。
  - 运行命令不变：`GRB_LICENSE_FILE=… bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<授权>"`。档案参数仍是必填，没有默认值。
  - 导出：账本、分国明细、恒等式、节点价格、CO₂ 流向（含 `CO2 transit ship`）、燃料舱账户。
  - 不互联诊断只在不互联主算非最优时运行。
  - 交付提交在 a3d58a46 之后改动了两处，都不是构建输入：
    - 新增 `scripts_project/s4e_4_collect_evidence.py`（证据收集），符合 `make_package.sh` 的 ALLOW 规则；
    - 提交 `cloud_package/preflight.sh` 的下限上调，它与包内 `preflight.sh` 哈希一致（174fc439…）。
  - 所以包内网络与交付提交的构建结果一致。
- **第一批敏感性（只登记，不打包运行，清单 `first_batch_sensitivities_registered_not_packaged`）：**

| 敏感性 | 覆盖项 | 注册表 | 本步核对 |
|---|---|---|---|
| 东盟外封存单价 ±50 %（作用于 54.70） | `co2.extra_asean_cost_scale=0.5 \| 1.5`（27.35 / 82.05 EUR/t） | `co2_extra_asean_storage_cost_unified`（范围） | 计价路径与 S4D 相同（S4D-6 ×1.5 已构建核对）；本步未单独构建 |
| ZEP 2011 统一封存 16.05 EUR/t | `s2.co2.sequestration_cost_eur_per_t=16.0535` | `co2_storage_cost_zep_sensitivity` | 已构建核对：国内 16.05，东盟外 40.75 |
| 单一航线系数 1.091 | `co2.ship_distance=route_factor` | `s4e2_ship_distance` | 已构建核对：11.54–26.89 EUR/t |
| 老挝过境：现有海港 / 罐车 | `co2.lao_transit_destination=existing_port`；`co2.lao_transit_mode=truck` | `s4e2_sensitivity_lao_transit` | 两项合用已构建核对：陆运段 56–101 EUR/t |
| LNG 不设上限，只计成本 | `s3.gas.lng_expansion=uncapped_cost`（7,018 EUR/MW/a） | `s4e2_sensitivity_lng_uncapped` | 已构建核对，B14 通过 |

- **联盟运行规则（第 95 项 f）：** 写入 `CLOUD_DEPLOY_STEPS.md` §11 与包清单 `coalition_run_rule`。规则：档案 A 非最优 → 用档案 C 重跑一次 → 仍非最优则标 UNVERIFIED。
- **资源（`CLOUD_RESOURCE_ESTIMATE.md` §14，INFERENCE）：**
  - 365×24h 单运行墙钟：一体化 36–51 min（悲观 74）、不互联 25–35、NZE 37–52；峰值内存中值 23 GiB、上限 32.3 GiB。
  - 串行 1.6–2.3 h（含诊断 2.8–4.0 h）；两通道 1.2–1.7 h；三通道 0.65–0.9 h。
  - 单运行内存上限 32.3 GiB 超过了原串行下限 32 GiB，所以 `preflight.sh` 的下限上调为 36 / 72 / 104 GiB；推荐值不变（≥ 48 / 96 / 128 GiB）。
  - 联盟研究：383 个联盟，串行约 160–330 h，三通道 55–110 h。
- **部署步骤：** `CLOUD_DEPLOY_STEPS.md` 已按 S4E 更新：目录、预检下限、§10 五项敏感性、§11 联盟运行规则。

## 6. 工作原则第 8 条检查汇总

| 建模决定 | 是否系统性地把成本推给或减轻某些国家 | 依据 / 量级 | 处理 |
|---|---|---|---|
| 补齐相邻走廊（第 94 项） | 原拓扑下 BN、TL 的互联价值按构造为 0，PH 只有跨海一条路；补齐后 BN 0.59、TL 0.14 bn EUR | 冒烟账本（§4） | 已实施 |
| 新候选不设容量上限 | 一体化中新走廊建设约 301 GW，远超 APG / AIMS 规划容量；互联价值会偏向 KH、LA、VN、TH 等陆上相邻国 | 冒烟 56 个时段，规模不可靠 | 用户决定事项 1 |
| 国内 APG 候选（#3、#18a、#18b）两个情景都有 | 避免把"省间不通"误记为跨境互联价值（第 35 项）；ID 不互联账本下降 16.6 bn，B6 由 47.32 变为 46.66 bn | 冒烟账本 | 已实施 |
| 统一封存单价（第 95 项 a） | S4D 中封存业务全部流向东盟外；统一后东盟外降为 0，封存资源国（ID、MY、BN、TH、PH）承接东盟内船运 | §4 CO₂ 表 | 已实施；ZEP 作敏感性 |
| 逐对海上距离（第 95 项 b） | 单一系数会低估绕马来半岛的航线（MM 到泰国湾侧，比值 2.2–2.6） | S4D-2 航线表 | 已实施；单一系数作对照 |
| 老挝过境后船运（第 95 项 c） | LA 在不互联中的出路从东盟外扩大到东盟内封存：LA→PH 5.65、LA→MY 1.94 Mt；LA 差额 2.98 → 2.64 bn | §4 | 已实施；不含经越南海岸进入越南国内封存（用户决定事项 5） |
| PH 互联价值为负 | 互联后 PH 按节点价格结算的账本成本比不互联高 0.61 bn | 冒烟账本，价格效应 | 用户决定事项 7 |
| TH–MY 存量（冻结底网 2,645.6 vs APG 380 MW） | 高估的存量减少 TH、MY 的扩建需要，并影响两国账本 | 很可能是 OSM 重复记录（INFERENCE） | 未改动（用户决定事项 2） |
| #4 端点取巴淡岛母线 | #4 与 #16 共用一个印尼端；苏门答腊本岛连接长度可能被低估（229 vs 347 km） | 最近节点规则 | 用户决定事项 3 |
| 联盟数目 81 → 383 | 新接入国家现在可以参加联盟，分摊不再把它们排除在外 | §2.5 | 运行范围由用户决定（事项 4） |

## 7. 需要用户决定的事项

1. **新候选走廊是否设容量上限：** 冒烟中 37 个新组件全部建设，合计约 301 GW。最大的是 #18a 40.5 GW（不互联 79.3 GW），APG / AIMS 2040 预测为 435 MW。可选做法：
   - 保持不设上限，由成本优化决定规模；
   - 按 APG / AIMS 的规划或预测容量设上限，没有数据的相邻对另定规则；
   - 先看 365×24h 的结果再决定，因为 56 个时段不能决定规模。
2. **TH–MY 存量：** 冻结底网 2,645.6 MW，APG 380 MW。差额主要来自 4 条 OSM 编号 250878579 的直流链路，各 491.4 MW。可选做法：
   - 保持冻结底网；
   - 删去疑似重复的 4 条（剩 680 MW）；
   - 对齐 APG 的 380 MW。
3. **#4 的印尼端点：** 现为 ID_Sumatra2 0（母线在巴淡岛，229 km，与 #16 共用）；替代为 ID_Sumatra3 3（北干巴鲁，347 km）。
4. **联盟研究范围：** 383 个联盟，串行约 160–330 h，三通道 55–110 h。可选做法：
   - 全部计算；
   - 先算两国联盟、"大联盟减一国"和大联盟；
   - 按规模分批计算。
5. **LA 经越南海岸进入越南国内封存：** 过境后船运只通往其他国家，不互联时 LA 到不了越南的国内封存。是否补上这条通道（陆运段 + 越南封存 30）。
6. **SG–VN、SG–KH（其他倡议）：** 现只登记为可选候选，没有进入主算。是否作为敏感性加入。
7. **PH 互联价值为负、新走廊与国内候选的效果分离：** 是否在云端加一次 `research.corridors.adjacency_completion=off` 的对照（需单独授权），用来区分补齐走廊与国内候选各自的贡献。

## 8. 下载与资源（工作原则第 7 条）

- **下载：** 无。本步只用了已有数据：S4A 区域、ACE 2024 APG 清单（S3 已入库）、补充 01、S4D 航线与过境表。
- **本机计算：**
  - 构建单次约 55 s / 0.7 GB；
  - 56×3h 求解单次 166–225 s，峰值 3.6–3.9 GiB；
  - 相邻判定与几何计算 < 1 min；
  - 没有超过 1 小时或约 8 GiB 的计算。
- **其他约束：**
  - 没有云端操作，没有正式求解。
  - Gurobi 许可只通过 `GRB_LICENSE_FILE` 引用。
  - 入库证据与部署包都扫描过许可特征串。代码包中的命中都是历史证据里的参数名列表、许可环境变量的存在性布尔标志（`environment_flags`），以及清洗脚本的关键词表，没有任何许可值（VERIFIED，掩码检查）。
- **测试：**
  - `tests/research` 488 通过、0 失败。
  - 整个 `tests/` 目录另有 17 个失败，全部出自 `tests/transport/test_shipping_allocation.py`。这是脚本式测试，从 `sys.argv` 读仓库根目录，在 pytest 中会把 `-q` 当成路径。该文件自 ee01f65a 以来没有改动，不在以往各步的测试口径内。

## 9. 交付清单（`work/p1_step4e_20261017/`，仓库镜像 `research/06_scope_redesign/p1_step4e_20261017/`）

- **报告与证据：** `S4E_REPORT.md`（本文件）、`S4E_EVIDENCE.json`、`S4E_PROGRESS.md`、`DOWNLOAD_LIST.csv`（沿用 S4D 并加 `status_s4e` 列，本步无下载）。
- **部署：**
  - `CLOUD_RESOURCE_ESTIMATE.md`（§14）、`CLOUD_DEPLOY_STEPS.md`；
  - 部署包脚本 `cloud_package/`；
  - 打包产物 `cloud_package_dist/`（不进 git）。
- **分步证据** `evidence/s4e_0` … `evidence/s4e_4`：
  - 注册表片段；
  - 相邻、APG 跨海 / 国内、存量核对、走廊、几何、海底份额与长度分摊表；
  - 构建状态；
  - 冒烟汇总；
  - 外推、重建状态与包清单。
- **代码：**
  - 新模块：`scripts_project/s4e_layers.py`；
  - 数据脚本：`s4e_0_data.py`、`s4e_1_corridors.py`、`s4e_1_length_shares.py`、`s4e_2_data.py`；
  - 汇总脚本：`s4e_3_summary.py`、`s4e_4_collect_evidence.py`；
  - 修改：`s2_network.py`、`s4c_layers.py`、`s4d_layers.py`、`s4d_ledger.py`、`scenario_network.py`、`s3_layers.py`、`v5/v5_gates.py`、`d1_registry.py`（登记片段）、`configs/research/baseline.yaml`；
  - 测试：`tests/research/test_s4e_1.py`、`test_s4e_2.py`。
- **注册表：** 片段 `s4e_0`、`s4e_1`、`s4e_2`。
- **审阅 ZIP：** `S4E_REVIEW.zip`，逐成员附 SHA256 与 CRC 清单。
