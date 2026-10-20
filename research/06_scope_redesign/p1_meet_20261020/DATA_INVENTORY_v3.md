# MEET-D 数据清单 v3（面谈材料附件 B 底稿）

**v3（M08-0 补充 01，第 131 项后重跑）**。同内容 Excel：`DATA_INVENTORY_v3.xlsx`（5 张表）；精简版（附件 B 底稿，最新）：`DATA_INVENTORY_BRIEF.xlsx / .md`（旧精简版改名为 `DATA_INVENTORY_BRIEF_v2.*`）；生成脚本：`scripts/meet_data_inventory_v3.py`；实算统计：`evidence/MEET_DATA_STATS_v3.json`。v1、v2 保留不动。

## 要点（≤ 10 行）

1. 注册表 2,057 行（提交 1be5ce02，SHA256 `6d1b2c34…0fa4`）：A 267 / B 1,290 / C 500；REGISTERED 1,142、REFERENCE_ONLY 555、SOURCE_ZERO 139、SENSITIVITY 128、DATA_PENDING 47、CANDIDATE_ONLY 35、ZERO_BY_DECISION 11。
2. 主算输入 1,263 行：A 10.85 %、B 60.33 %、C 28.82 %。C 级 364 行中生物质 197 行（54.1 %）、工业产量与路线 57 行、交通份额 20 行。
3. 11 国完全同口径：S4R 核查表 19 类中 9 类（47.4 %）；本清单表 1 的 25 类中现行 18 类（72.0 %）、修正后 17 类（68.0 %）。不同口径的主要来源：水电 / 地热逐国官方来源、封存三源混用（修正后统一 ERIA）、陆上风 alpha、TL 规则、SG 核电。修正后少 1 类，是因为工业产量改为统一规则后，各国基年数据等级不同被如实记为例外；封存由“否”变为“有例外”。
4. M08-0 补登与补充 01：v1 的注册表缺口 1–5 均已登记，注册表 1,962 → 2,057 行；补充 01 把屋顶光伏改为 C 级（±50 %），核实 GEGIS 文献（Mattsson et al. 2021），登记 4 个已获取文件（USGS 水泥 2023、worldsteel 粗钢 2024、UN WPP TL 人口、Eurostat HICP）。
5. 不一致项 12 项（§I，含 M08-0 与补充 01 的新发现 3 项）：电力底座存量机组的成本与效率仍来自作者 v0.13.2 表，属统一性问题，交 M08（拟改用 v0.15.0 对应投运年份）；technology-data 升通胀口径为欧洲经济区（EEA）年变化率，不是 EU27 或欧元区。
6. 修正后各项均为第 129 项确认的方案，尚未实施（M08）。

## A. 说明

| 项目 | 内容 |
|---|---|
| 用途 | 面谈材料附件 B「数据清单」底稿：主算每类输入的来源、等级、11 国口径与修正方向；敏感性数据；收集未采用的数据；待补与 C 级假设。 |
| 版本 | v3：M08-0 补充 01（第 131 项）后重跑；v1（DATA_INVENTORY.*，注册表 cefab870）、v2（DATA_INVENTORY_v2.*，注册表 880955b8）与旧精简版（DATA_INVENTORY_BRIEF_v2.*）保留不动。 |
| 注册表版本 | 仓库 research_inputs/registry_v5/DATA_REGISTRY.csv，提交 1be5ce02（分支 codex/m08-0-registry-backfill-20261020，补充 01 P4）；SHA256 6d1b2c341fa32e3af5b2d996b31708322c81255a28839be82fe930285a020fa4；v1 基准 cefab870（1,962 行），v2 基准 880955b8（2,052 行）。 |
| 其他资料 | M08-0：work/p1_m080_20261020/（M080_REPORT.md 含补充 01 一节、REGISTRY_ROWS_PROPOSED_v2.csv（补充 01 后 43 行）、USER_DOWNLOAD_LIST_v2.md、evidence/）；补充 01 已获取的 4 个文件：work/p1_s4r_downloads_20261020/R1_demand、R6_costs；S4R：work/p1_step4r_20261020/（S4R_PLAN.md 已按补充 01 修订、UNIFICATION_CHECKLIST、REGISTRY_ROWS_PROPOSED（v1，本版改用 v2）、各对照表、USER_DOWNLOAD_LIST）；S4P：work/p1_step4p_20261020/（EXTERNAL_SOURCES.md、evidence/）；下载目录 work/p1_s4r_downloads_20261020/；决定第 126、129 项（台账 S4R 条目与 S4R_SUPPLEMENT_01.md）。data_registry/：仓库中无此目录，D 盘工作区 data_registry/ 只有 buildings_phase3a4（第三阶段建筑数据模板，与当前主算无关）。 |
| 等级口径（注册表） | A = 直接来源；B = 可复现的推导（脚本 + 输入哈希）；C = 假设，必须附敏感性范围（D1_DATA_INSTRUCTION.md 第 20–22 行；scripts_project/d1_common.py）。 |
| 状态口径（注册表） | REGISTERED 主算使用；SOURCE_ZERO 来源给出 0；ZERO_BY_DECISION 按决定取 0；SENSITIVITY 敏感性；REFERENCE_ONLY 只作对照或记录；CANDIDATE_ONLY 候选（未作上限）；DATA_PENDING 待补。 |
| 主算输入的定义 | 数据类 T01–T25 中状态为 REGISTERED、SOURCE_ZERO、ZERO_BY_DECISION 的行（SOURCE_ZERO 与 ZERO_BY_DECISION 也是进入主算的 0 值）。非数据类 X1–X3（求解与验收设置、步骤记录、核算规则）另列。 |
| 分类方法 | 按 param_id 前缀逐行归类（先匹配者优先），2,057 行全部归类、无遗漏；规则见 scripts/meet_data_inventory_v3.py（v1 规则 + M08-0 与补充 01 新行的前缀，放在通用前缀之前）。 |
| “修正后”的含义 | 第 126 项方案经第 129 项确认的方向；均未实施，写“方案，M08 实施”。 |
| 结论等级 | 统计数字为脚本实算（VERIFIED）；“修正后”数值来自 S4R（PROPOSED）；影响量级标 INFERENCE。 |
| 只读声明 | 本脚本只读注册表与 S4R / M08-0 文件；未求解、未连云、未调用 Gurobi、未改模型 / 配置 / 既有结果。注册表的修改在 M08-0 中进行（见 M080_REPORT.md）。 |
| 附件 B 用：等级 | A = 直接取自来源；B = 可复现的推导（有处理脚本与输入文件哈希）；C = 假设，附敏感性范围。 |
| 附件 B 用：主算输入 | 主算实际使用的数据行（含来源给出 0 与按决定取 0 的行），不含敏感性、对照与待补行。 |
| 精简版 | DATA_INVENTORY_BRIEF.xlsx / .md 为附件 B 底稿：表 1 各格取自本表“附件 B：…”五列，表 3、表 4 取自本表对应列（同文）；不含不一致项与 param_id。 |

## B. 注册表总行数与等级分布（实算）

| 等级 | 行数 | 占比 |
|---|---|---|
| A | 267 | 13.0 % |
| B | 1290 | 62.7 % |
| C | 500 | 24.3 % |
| 合计 | 2057 | 100.0 % |

## C. 按状态分布（实算）

| 状态 | 行数 | 占比 |
|---|---|---|
| REGISTERED | 1142 | 55.5 % |
| REFERENCE_ONLY | 555 | 27.0 % |
| SOURCE_ZERO | 139 | 6.8 % |
| SENSITIVITY | 128 | 6.2 % |
| DATA_PENDING | 47 | 2.3 % |
| CANDIDATE_ONLY | 35 | 1.7 % |
| ZERO_BY_DECISION | 11 | 0.5 % |
| 合计 | 2057 | 100.0 % |

## D. 等级 × 状态（实算）

| 等级 | CANDIDATE_ONLY | DATA_PENDING | REFERENCE_ONLY | REGISTERED | SENSITIVITY | SOURCE_ZERO | ZERO_BY_DECISION | 合计 |
|---|---|---|---|---|---|---|---|---|
| A | 25 | 10 | 94 | 111 | 1 | 26 | 0 | 267 |
| B | 7 | 1 | 383 | 701 | 108 | 90 | 0 | 1290 |
| C | 3 | 36 | 78 | 330 | 19 | 23 | 11 | 500 |
| 合计 | 35 | 47 | 555 | 1142 | 128 | 139 | 11 | 2057 |

## E. 主算输入中 A / B / C 级的占比（实算）

| 口径 | 行数 | A | B | C |
|---|---|---|---|---|
| 主算输入（数据类 T01–T25，主算状态） | 1263 | 137（10.85 %） | 762（60.33 %） | 364（28.82 %） |
| 对照 1：含非数据类 X1–X3 | 1292 | 137（10.6 %） | 791（61.22 %） | 364（28.17 %） |
| 对照 2：数据类，仅 REGISTERED | 1113 | 111（9.97 %） | 672（60.38 %） | 330（29.65 %） |

## F. 11 国完全同口径的类别占比（实算）

| 口径 | 完全同口径类 | 总类数 | 占比 | 说明 |
|---|---|---|---|---|
| 统一性核查表 19 类（无“否”且无例外说明的类；描述修正后口径） | 9 | 19 | 47.4 % | 209 格中标出 64 格（与 S4R 自报一致）；完全同口径：需求：工业能耗与路线、潜力：光伏（地面）、潜力：屋顶光伏、潜力：生物质、LNG 接收站、区域外进口价（氢 / 氨 / 甲醇 / FT / 原油 / 煤）、技术成本、跨境候选通道、存量机组 |
| 本清单表 1 的 25 类（现行） | 18 | 25 | 72.0 % | 有例外 4；是 18；否 3 |
| 本清单表 1 的 25 类（修正后） | 17 | 25 | 68.0 % | 有例外 6；是 17；否 2 |

## G. 各类别行数与主算等级（实算）

| 代号 | 类别 | 全部行 | 主算行 | 主算 A | 主算 B | 主算 C | DATA_PENDING | SENSITIVITY | REFERENCE_ONLY | CANDIDATE_ONLY |
|---|---|---|---|---|---|---|---|---|---|---|
| T01 | 需求：终端能耗总量与国别增长 | 87 | 66 | 11 | 51 | 4 | 0 | 12 | 9 | 0 |
| T02 | 需求：基础电力负荷（居民、商业、农业及其他） | 14 | 6 | 0 | 1 | 5 | 0 | 0 | 8 | 0 |
| T03 | 需求：交通（陆运、航运、航空、燃料舱） | 41 | 33 | 5 | 8 | 20 | 0 | 0 | 8 | 0 |
| T04 | 需求：工业物理产量与工艺（钢、水泥、氨、甲醇、HVC、铝） | 109 | 77 | 13 | 25 | 39 | 1 | 0 | 31 | 0 |
| T05 | 需求：工业热与其他工业能耗（路线、比率、生物质溢出） | 135 | 69 | 1 | 50 | 18 | 0 | 10 | 56 | 0 |
| T06 | 排放核算输入：过程排放、原料碳、废弃物、逸散 | 245 | 162 | 5 | 142 | 15 | 0 | 36 | 47 | 0 |
| T07 | 风光廓线（共用：ERA5 2013 cutout、atlite 重建） | 18 | 5 | 1 | 4 | 0 | 0 | 0 | 13 | 0 |
| T08 | 潜力：光伏（地面） | 20 | 15 | 1 | 14 | 0 | 0 | 1 | 4 | 0 |
| T09 | 潜力：屋顶光伏 | 17 | 12 | 0 | 0 | 12 | 0 | 0 | 5 | 0 |
| T10 | 潜力与廓线：陆上风 | 61 | 31 | 0 | 22 | 9 | 0 | 1 | 27 | 2 |
| T11 | 潜力与廓线：海上风 | 47 | 33 | 2 | 31 | 0 | 0 | 0 | 14 | 0 |
| T12 | 水电（含径流、抽蓄） | 65 | 36 | 1 | 34 | 1 | 4 | 0 | 19 | 6 |
| T13 | 地热 | 39 | 15 | 0 | 12 | 3 | 9 | 0 | 12 | 3 |
| T14 | 生物质（潜力、成本） | 265 | 249 | 11 | 41 | 197 | 6 | 0 | 10 | 0 |
| T15 | CO₂ 封存与区域内运输 | 71 | 51 | 18 | 18 | 15 | 2 | 0 | 18 | 0 |
| T16 | LNG 接收站与气网 | 113 | 48 | 11 | 33 | 4 | 10 | 2 | 29 | 24 |
| T17 | 区域外进口与兜底选项价格 | 42 | 21 | 0 | 12 | 9 | 0 | 1 | 20 | 0 |
| T18 | 国内化石燃料产量上限 | 87 | 85 | 33 | 47 | 5 | 1 | 0 | 1 | 0 |
| T19 | 燃料价格与燃料碳 | 37 | 12 | 1 | 11 | 0 | 2 | 6 | 17 | 0 |
| T20 | 技术成本 | 242 | 181 | 3 | 178 | 0 | 0 | 52 | 9 | 0 |
| T21 | WACC / 贴现率 | 19 | 2 | 0 | 2 | 0 | 11 | 0 | 6 | 0 |
| T22 | 跨境候选通道（电力、管道）与网络损耗 | 66 | 10 | 0 | 7 | 3 | 0 | 0 | 56 | 0 |
| T23 | 核电 / SMR | 17 | 5 | 0 | 0 | 5 | 0 | 5 | 7 | 0 |
| T24 | 存量机组 | 37 | 15 | 1 | 14 | 0 | 1 | 1 | 20 | 0 |
| T25 | 货币、汇率与单位换算 | 24 | 24 | 19 | 5 | 0 | 0 | 0 | 0 | 0 |
| X1 | 非数据：求解、验收与数值设置 | 53 | 20 | 0 | 20 | 0 | 0 | 1 | 32 | 0 |
| X2 | 非数据：步骤记录、决定与问答 | 65 | 0 | 0 | 0 | 0 | 0 | 0 | 65 | 0 |
| X3 | 非数据：模型结构与核算规则 | 21 | 9 | 0 | 9 | 0 | 0 | 0 | 12 | 0 |

## H. S4R 拟增 / 改注册表行（REGISTRY_ROWS_PROPOSED_v2，实算）

| 项目 | 值 |
|---|---|
| REGISTRY_ROWS_PROPOSED_v2.csv 行数（M08-0 新版本） | 43 |
| action 分布 | add 34；modify 9 |
| 等级分布 | A 3；B 14；C 26 |
| modify 且注册表有同名行 | 9 |
| 非 add 但注册表无同名行 | 0（v2 已全部改为 add） |
| 写明被替代旧行的新行 | 10 |

## I. 不一致项与 M08-0 处理结果

| 编号 | 事项 | v1 所见 | M08-0 处理结果 | 现状 / 仍需处理 |
|---|---|---|---|---|
| 1 | LNG 进口上限分国值 | 注册表只有“2.5 × 存量”行（VN 133.33、ID 391.67、KH 0、PH 490.00 TWh/a），与网络不符。 | 补登 lng_import_cap_built_*（网络实值：VN 278.67、ID 422.33、KH 14.67、PH 510.00、MY 243.33、SG 366.67、TH 633.33 TWh/a；一体化 = 不互联）与规则行 lng_import_cap_rule_built；原 2.5 × 行保留并注明只是规则的一部分。 | 已修正。 |
| 2 | 海上风机型与尾流 | 注册表写 2020ATB 5.5 MW + 0.8855，S4R 把“NREL 5 MW、无尾流”写为现状。 | VERIFIED：筛查廓线海上风与 pypsa_eur 重建逐值相同，构建提交 126110ff 的 s4a_profiles.py 为 2020ATB 5.5 MW、0.8855；注册表正确，S4R 有误；新增核实行 renewable_offwind_profile_check_built；REGISTRY_ROWS_PROPOSED_v2 的 renewable_offshore_rule 已改。 | 已修正（S4R 原件不改；S4R_PLAN §3.1、UNIFICATION_CHECKLIST 的同一措辞仍在原件中）。 |
| 3 | GEM LNG 版本标注 | 注册表 2025-09，S4R 记 2025-08。 | 文件 About 页写明 September 2025 release（创建 2025-10-14）；S4R 下载的工作簿与注册表来源 SHA256 相同；新增 lng_gem_ggit_release_verified。注册表其他 GEM 数据集（气管道 2025-11、GIPT 2026-09、GOGET 2026-03）标注与文件一致。 | 注册表无需改；S4R 原件中的“2025-08”为误记。 |
| 4 | 航运密度栅格 | raw12 已有文件，但 renewable_ship_density_raster 仍为 DATA_PENDING，下载清单 A1 仍列为必需。 | SHA256 复算一致（7d103de5…9248）；renewable_ship_density_raster 改为 REFERENCE_ONLY（主算未用）；USER_DOWNLOAD_LIST_v2 删去 A1。 | 已修正。 |
| 5 | natura 保护区栅格状态 | 实际在用但为 REFERENCE_ONLY。 | 改为 REGISTERED，补 Harvard Dataverse wdpa_reclass.tif V1.3（MD5 与本地 natura.tiff 一致，CC0）。 | 已修正。 |
| 6 | 成本层 v0.13.2 | v0.13.2 与 v0.15.0 两个“主算”成本层同为 REGISTERED。 | cost_layer_A_* 改为 REFERENCE_ONLY（历史）；SMR 寿命 / 效率代理与存量机组寿命取自 v0.13.2，但与 v0.15.0 同值；存量地热 v0.13.2 FOM / CO₂ 行未被网络使用，改为 REFERENCE_ONLY；新增 cost_v0132_usage_built；补充 01 新增 existing_fleet_cost_source_unification（统一性问题，M08 处理），拟增行加 existing_fleet_cost_rule（v0.15.0 对应投运年份）。 | 部分交 M08：电力底座存量机组的成本与效率仍来自作者 v0.13.2 表（存量固定运维 108.1 亿 EUR/a，存量 CCGT 效率 0.57 对新建 0.60；0.57 与 v0.15.0 costs_2025 相同），属统一性问题，本步不改模型。 |
| 7 | KH / TL 封存等级 | OGCI 来源未能复核却为 A 级。 | KH、TL 国家合计行与 OGCI 分项行由 A 改为 C，数值不变（分项行沿用国家行的 D1 敏感性区间）；本地 PDF 汇总表为图片，同样无法复核。 | 已修正。 |
| 8 | REGISTRY_ROWS_PROPOSED 自身问题 | 1 行列错位；7 行 action 非 add 但注册表无同名行。 | REGISTRY_ROWS_PROPOSED_v2.csv：7 行改为 add；错位行按列名对齐；9 行写明被替代的 param_id，注明 M08 写入时把旧行标为历史。 | 已修正（新版本，原件不改）。 |
| 9 | 台账 S4R 条目计数 | 台账写“54 格标出”，实为 64 格。 | M08-0 台账条目注明 64 格（台账历史条目不改）。 | 已注明。 |
| 10 | 廓线变体与资源分级的旧 REGISTERED 行（M08-0 新发现） | — | renewable_profile_variant（pypsa_eur）、renewable_resource_classes（1）已被 S4B-3 行（calibrated_modern、3）替代 → REFERENCE_ONLY（历史）；筛查实际读取的 profiles_calibrated_modern_c1 / c3 文件原无注册行 → 补登；pypsa_eur / fork 廓线文件行改为对照。 | 已修正。 |
| 11 | 注册表片段 s4c_0.csv 未入库（M08-0 新发现） | — | 该片段被 .gitignore 的 *.csv 忽略、从未提交，干净检出无法重拼注册表；M08-0 强制入库，重拼结果与原注册表逐字节一致。 | 已修正。 |
| 12 | technology-data 升通胀的 HICP 口径（补充 01 新发现） | 审阅端以为是 EU27 指数（2025/2020 = 1.256）；S4R 拟用“欧元区”回算。 | technology-data v0.15.0 源码 scripts/_helpers.py 第 220 行取欧洲经济区（EEA）年均变化率并累乘：2021–2025 年 2.9、9.2、6.4、2.6、2.5 %，系数 1.25733（+25.7 %）；v0.13.2 取 EU27。下载文件中 EU27 与 EEA 的年变化率相同，EU27 指数比 1.25624（差 0.09 %，四舍五入），欧元区 1.2256。 | 已登记（download_eurostat_hicp_aind_2016_2025）；M08-1 回算应用 EEA 年变化率累乘（拟增行已加注）。 |

## J. 注册表缺口：M08-0 补登后的状态（仍无记录者照实保留）

| 编号 | v1 缺口 | M08-0 后的状态 |
|---|---|---|
| 1 | 地面光伏、陆上风、海上风分国候选上限，Copernicus LC100 土地类别，各技术密度 | 已补登：renewable_cap_built_*（55 行，含屋顶光伏）、renewable_landcover_codes_built_*、renewable_density_built_*、renewable_copernicus_lc100_file / gebco_file / eez_file（文件 SHA256 为本地作者链副本；作者本人副本未留哈希）。 |
| 2 | 屋顶光伏候选潜力 | 已补登数值与方法（renewable_rooftop_method_built，作者代码有记录）；建筑足迹输入不在本机，不可复现——补充 01 定为 C 级，敏感性 0.5×–1.5×，描述中记录与 AEO8 / PDP8 / MyRER 的比值。 |
| 3 | 基础负荷小时形状（Astar） | 已查清并补登：GEGIS（GlobalEnergyGIS）2030 年国别曲线，经 PyPSA-Earth 分配；补充 01 核实原始文献 Mattsson, Verendel, Hedenus, Reichenberg (2021) Energy Strategy Reviews 33, 100606（doi:10.1016/j.esr.2020.100606）；LA / TL 借用曲线登记为 C 级例外；数据包在 sandbox.zenodo.org（非永久存档）。 |
| 4 | 地热新建投资主算值 | 已补登 geothermal_new_investment_main（3,596.6 EUR2020/kW）及 FOM / VOM 行（C，±30 %）。 |
| 5 | 决定 72 下 LNG 分国进口上限 | 已补登 lng_import_cap_built_*（见 §I 第 1 项）。 |
| 6 | ESMAP / Solargis、Zhong、GIIGNL、各国规划需求等外部对照来源 | 仍无记录（属对照，不影响主算）。 |
| 7 | worldsteel SSY 2020 页码（p.1 / p.3 vs Table 1 p.5） | 未核（不在本步范围）。 |
| 8 | VN 水泥 2050 旧值 581 Mt | 只在需求输入表 INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv 中，注册表无同名行（照实保留；REGISTRY_ROWS_PROPOSED_v2 中 industry_cement_2050_VN 为 add）。 |

## K. v1 → v2 → v3 对比（实算）

| 项目 | v1 | v2 | v3 |
|---|---|---|---|
| 注册表行数 | 1962.0 | 2052.0 | 2057.0 |
| 等级 A | 263.0 | 263.0 | 267.0 |
| 等级 B | 1220.0 | 1301.0 | 1290.0 |
| 等级 C | 479.0 | 488.0 | 500.0 |
| 状态 CANDIDATE_ONLY | 35.0 | 35.0 | 35.0 |
| 状态 DATA_PENDING | 51.0 | 47.0 | 47.0 |
| 状态 REFERENCE_ONLY | 534.0 | 550.0 | 555.0 |
| 状态 REGISTERED | 1071.0 | 1142.0 | 1142.0 |
| 状态 SENSITIVITY | 128.0 | 128.0 | 128.0 |
| 状态 SOURCE_ZERO | 132.0 | 139.0 | 139.0 |
| 状态 ZERO_BY_DECISION | 11.0 | 11.0 | 11.0 |
| 主算输入行数 | 1185.0 | 1263.0 | 1263.0 |
| 主算输入 A 级占比 % | 11.73 | 10.85 | 10.85 |
| 主算输入 B 级占比 % | 59.32 | 61.28 | 60.33 |
| 主算输入 C 级占比 % | 28.95 | 27.87 | 28.82 |

## 表 1　主算输入（按输入类别）

### 1. 需求：终端能耗总量与国别增长

- **模型中的用途：** 给出 11 国 2050 年分部门、分载体终端能耗（需求表），驱动全部固定负荷与燃料需求。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 基年 UNSD Energy Statistics 2019 国别能源平衡 × 2019→2022 桥接（ACE《8th ASEAN Energy Outlook 2023–2050》(2024) Chapter 1 与 Appendix C.3）× AEO8 BAS 部门增长（Table C.3，印刷页 p.182）× ATS 国别相对因子 r_c（Table C.8 人均终端能耗，p.187 × Table D.1 人口，p.188；决定 57）；比率法（决定 66）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 66：A 11、B 51、C 4；全部 87 行；S4R：B
- **11 国覆盖情况（缺哪些国家、如何补）：** 10 国按 AEO8 表；TL 不在 AEO8 表中，r_c 用 GDP 相对因子 0.970（demand_aeo8_ats_relative_factor_TL）。修正后 TL 用 KH / LA / MM 均值 × UN WPP 2024 人口（原文件已获取：TL 2050 中位 1,889,249.5 人，M08 实施）。
- **是否同口径（是 / 否 / 有例外）：** 现行：有例外；修正后：有例外。方法 11 国同一；TL 因 AEO8 不覆盖按规则补（S4R 核查表 1 格标出）。
- **处理脚本：** scripts_project/d1_demand_2050.py
- **修正前 → 修正后（第 129 项）：** 现：模型 TFEC 1,220 Mtoe（11 国，比率法 × BAS 增长）→ 拟：AEO8 ATS 人均 × 人口，只锚活动量、载体内生（ATS 746 Mtoe；第 126、129 项已定主锚）。方案，M08 实施（M08-5）。
- **注册表 param_id 范围：** demand_aeo8_*、demand_tfec_2050_*、demand_country_*、demand_growth_method、demand_bridge_2019_2022_*、demand_sector_calibration_k_*、demand_mtoe_to_mwh、demand_base_year、demand_basis_gap_*；敏感性 demand_gdp_multiplier_*、demand_wdi_*；拟增 demand_anchor_family_main / _control、demand_anchor_tl_rule（REGISTRY_ROWS_PROPOSED）
- **附件 B：用途（精简）：** 给出 11 国 2050 年分部门、分载体终端能耗（需求表），驱动全部固定负荷与燃料需求。
- **附件 B：来源（精简）：** UNSD Energy Statistics 2019 国别能源平衡；ACE《第 8 版东盟能源展望》（AEO8，2024）BAS 部门增长（Table C.3）与 ATS 国别人均终端能耗（Table C.8）× 人口（Table D.1）
- **附件 B：11 国覆盖（精简）：** 10 国按 AEO8；TL 不在 AEO8 内，按规则补
- **附件 B：修正方向（精简）：** 改为锚定 AEO8 ATS 人均 × 人口的活动量，载体结构内生（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 66：A 11、B 51、C 4
- **附件 B：是否同口径：** 现行：有例外；修正后：有例外

### 2. 需求：基础电力负荷（居民、商业、农业及其他）

- **模型中的用途：** 非工业固定电力负荷的年总量与小时形状。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 年总量 = 需求表（T01 链）中居民、商业 / 公共、农业及其他与 2019 既有交通电力之和（第 104 项，research.demand.nonindustrial_electricity = table_sectors）；小时形状 = 作者链 Astar 负荷曲线按年总量归一（S4J-1）——Astar 形状来源（M08-0 补登，VERIFIED）：作者论文网络的基础负荷 = PyPSA-Earth build_demand_profiles 由 GEGIS 国别曲线（data/ssp2-2.6/2030/era5_2013/Asia.nc，文件属性“Projected electricity demand using GlobalEnergyGIS”，SSP2-RCP2.6、预测年 2030、ERA5 天气年 2013；PyPSA-Earth 数据包 bundle_data_earth）按 GDP / 人口分到节点；9 国形状与 GEGIS 成比例（相关 ≥ 0.99999），LA / TL 借用 KH / ID 曲线（作者 load_options；补充 01 登记为 C 级例外：复制曲线、归一到均值 1 后乘 scale）。GEGIS 原始文献（补充 01 核实）：Mattsson, Verendel, Hedenus, Reichenberg (2021) Energy Strategy Reviews 33, 100606，doi:10.1016/j.esr.2020.100606（作者链 PyPSA-Earth 文档引用该 DOI，Crossref 元数据一致）。农机电气化份额：PyPSA-Eur v2025.07.0 config.default.yaml 第 603–606 行。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 6：B 1、C 5；全部 14 行；S4R：B
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国同一方法；TL 年总量随 T01 的 TL 规则。
- **是否同口径（是 / 否 / 有例外）：** 现行：有例外；修正后：有例外。TL 随 T01 规则（S4R 核查表 1 格标出）。
- **处理脚本：** scripts_project/s4j_1_data.py（登记）、scripts_project/s2_layers.py（构建）、scripts_project/d1_demand_shares.py
- **修正前 → 修正后（第 129 项）：** 11 国 1,032 → 966 TWh（VN 197 → 184、ID 301 → 311、TH 209 → 170，全部非负）；拟：ATS 国家电力（C.8 × D.1）× 归一化部门权重中的建筑 + 农业及其他份额。方案，M08 实施（M08-5）。
- **注册表 param_id 范围：** s4j1_*（REFERENCE_ONLY 记录）、share_agriculture_*；M08-0 补登 demand_astar_shape_source / _substitution / _gegis_check；拟增 demand_base_load_rule
- **附件 B：用途（精简）：** 非工业固定电力负荷的年总量与小时形状。
- **附件 B：来源（精简）：** 年总量取自需求表中居民、商业、农业及其他与 2019 年交通电力；小时形状为 GEGIS（GlobalEnergyGIS；Mattsson et al. 2021, Energy Strategy Reviews 33, 100606）2030 年国别负荷曲线（SSP2-RCP2.6，ERA5 2013 天气年；PyPSA-Earth 数据包）；LA、TL 分别借用 KH、ID 曲线（例外，C 级）
- **附件 B：11 国覆盖（精简）：** 11 国同一方法；TL 年总量随需求规则
- **附件 B：修正方向（精简）：** 年总量改为 AEO8 ATS 国家电力 × 建筑与农业份额（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 6：B 1、C 5
- **附件 B：是否同口径：** 现行：有例外；修正后：有例外

### 3. 需求：交通（陆运、航运、航空、燃料舱）

- **模型中的用途：** 陆运服务需求与载体份额（BEV / FCEV / ICE），航运、航空燃料需求与燃料舱归属。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 需求表交通行（T01 链）；陆运 2050 电动 1 / 燃料电池 0 / 内燃 0（PyPSA-Eur v2025.07.0 config.default.yaml 第 576、584、592 行），效率 53.19 / 30.003 / 16.0712（第 600–602 行），BEV 参数（第 560–574 行）；航运 2050 甲醇 1（第 611–634 行）；航空需求因子 1（第 637 行）；国际燃料舱按 2019 常量（决定 10）、归属 asean_pool（决定 88）；燃料舱核对用 UNSD Energy Balance 2019。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 33：A 5、B 8、C 20；全部 41 行；S4R：—（S4R 核查表未单列）
- **11 国覆盖情况（缺哪些国家、如何补）：** 份额与效率为区域统一值；BN / KH / LA / TL 国际海运燃料舱为 0（UNSD 无流量，SOURCE_ZERO）。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。欧洲 2050 份额统一用于 11 国（C 级，偏离未逐国校准）。
- **处理脚本：** scripts_project/d1_demand_2050.py、scripts_project/d1_demand_shares.py、scripts_project/s3_4_shipping_data.py、scripts_project/s4c_3_data.py
- **修正前 → 修正后（第 129 项）：** 现：交通终端能耗 11 国 2,991 TWh → 拟：锚 ATS 服务量（锚 1,698 TWh 终端能耗当量；模型 / 锚 1.1–3.2），电气化程度按现行做法。方案，M08 实施（M08-5）。
- **注册表 param_id 范围：** share_land_*、share_bev_*、share_transport_*、share_shipping_*、share_aviation_*、share_source_version、shipping_*、bunker_demand_*、bunker_methanol_*、demand_bunker_*；拟增 demand_transport_anchor_rule
- **附件 B：用途（精简）：** 陆运服务需求与载体份额（BEV / FCEV / ICE），航运、航空燃料需求与燃料舱归属。
- **附件 B：来源（精简）：** 需求表交通行；陆运、航运、航空 2050 年载体份额与效率取 PyPSA-Eur v2025.07.0 缺省配置；国际燃料舱按 UNSD 2019 常量
- **附件 B：11 国覆盖（精简）：** 区域统一份额与效率；BN、KH、LA、TL 国际海运燃料舱为 0（来源为 0）
- **附件 B：修正方向（精简）：** 改为锚定 AEO8 ATS 交通服务量（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 33：A 5、B 8、C 20
- **附件 B：是否同口径：** 现行：是；修正后：是

### 4. 需求：工业物理产量与工艺（钢、水泥、氨、甲醇、HVC、铝）

- **模型中的用途：** 钢、水泥、氨、甲醇、HVC、铝的物理产量与工艺份额，决定工业电 / 氢 / 热需求与过程排放。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 粗钢 2019：worldsteel Steel Statistical Yearbook 2020 (concise)（注册表定位 Total p.1、By process p.3）× 国别乘数；水泥 = EDGAR 2025 2.A.1 过程 CO₂ ÷ 0.52（IPCC 2006 Vol.3 Ch.2）÷ 熟料比 0.656（technology-data v0.15.0 cement finishing）× 乘数；氨、甲醇按 JRC-IDEES 2021 EU27 份额派生；2050 路线份额（一次钢 0.3、DRI 1、一次铝 0.2、HVC 回收 0.30 / 0.20）PyPSA-Eur v2025.07.0 config.default.yaml 第 823–887 行。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 77：A 13、B 25、C 39；全部 109 行；S4R：水泥 C；粗钢 B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** 粗钢 BN / KH / LA / TL 不在 worldsteel 表中 → 0（SOURCE_ZERO）；熟料 SG / TL EDGAR 无 → 0。修正后：水泥基年 2023（USGS 年鉴 2023 表 T22，11 国同一来源，SG、TL 不在表中按 0）、粗钢基年 2024（worldsteel Steel Data Viewer，BN、KH、LA、TL 不在表中按 0）——文件已获取，M08 实施。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：有例外。现行同一方法；修正后规则与基年来源 11 国同一（水泥 USGS 2023、钢 worldsteel 2024），例外：部分国家为 USGS 估计值（e），不在表中的国家按 0，VN 规划只作上限——S4R 核查表 12 格标出。
- **处理脚本：** scripts_project/s3_0_industry.py、scripts_project/s3_3_ammonia_methanol_data.py、scripts_project/d1_demand_shares.py
- **修正前 → 修正后（第 129 项）：** VN 水泥 581 → 107.0 Mt（人均上限绑定）、粗钢 80.3 → 40.7 Mt；11 国水泥 1,290 → 410、钢 152 → 97 Mt；规则 2050 = min(基年 × G^ε, 人均饱和 × 人口, 规划上限)，基年水泥 2023（USGS）、钢 2024（worldsteel）（补充 01，文件已获取；S4R 的数值按原基年数据算出，M08 按新文件重算），ε = 0.5、饱和 1.0 / 0.6 t/人登记为假设（C）。方案，M08 实施（M08-5）。
- **注册表 param_id 范围：** industry_steel_*、industry_clinker_*、industry_cement_clinker_ratio、industry_ammonia_*、industry_methanol_*、share_St_* / share_DRI_* / share_HVC_* / share_Al_* / share_MWh_*、ammonia_methanol_*、steel_process_structure_2019；拟增 industry_output_rule_2050、industry_output_base_year、industry_output_elasticity、industry_percap_saturation_*、industry_cement_2050_VN、industry_output_plan_sensitivity_VN；拟改 industry_steel_2050_VN
- **附件 B：用途（精简）：** 钢、水泥、氨、甲醇、HVC、铝的物理产量与工艺份额，决定工业电 / 氢 / 热需求与过程排放。
- **附件 B：来源（精简）：** 粗钢：worldsteel《Steel Statistical Yearbook 2020》；水泥：EDGAR 2025 过程 CO₂ 按 IPCC 2006 排放因子与熟料比反推；氨、甲醇：JRC-IDEES 2021 份额；2050 工艺份额：PyPSA-Eur v2025.07.0
- **附件 B：11 国覆盖（精简）：** BN、KH、LA、TL 无粗钢生产；SG、TL 无熟料生产（来源为 0）
- **附件 B：修正方向（精简）：** 2050 产量 = min（基年 × GDP 增长弹性，人均饱和 × 人口，国家规划上限），11 国同一规则；基年水泥 2023（USGS 年鉴）、粗钢 2024（worldsteel）；VN 水泥 581 → 107.0 Mt、粗钢 80.3 → 40.7 Mt（按原基年估算，M08 按新文件重算）（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 77：A 13、B 25、C 39
- **附件 B：是否同口径：** 现行：是；修正后：有例外

### 5. 需求：工业热与其他工业能耗（路线、比率、生物质溢出）

- **模型中的用途：** 工业低温热、“其他工业”回退桶能耗与载体路线，固体生物质需求超出潜力部分的处理。
- **主算来源（机构、文件、年份、版本，表号或页码）：** UNSD 2019 工业能耗（需求表）× 乘数；载体比率 JRC-IDEES-2021 EU27（2019）× PyPSA-Eur v2025.07.0 build_industry_sector_ratios.py（pypsa_eur_2050 路线，决定 61）；效率因子 21 行（JRC-IDEES）；生物质溢出转甲烷（决定 36）+ 上限份额 0.98（决定 115）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 69：A 1、B 50、C 18；全部 135 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国同一方法；UNSD 子部门行缺失的国家由活动量 × 比率推导（S2B，INDUSTRY_2050_GAPS.csv）；TL 低温热为 0。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。11 国同一方法（S4R 核查表 0 格标出）；欧洲路线比率用于东盟属方法偏离，理由见 S4R_PLAN §2.4。
- **处理脚本：** scripts_project/s3_0_industry.py、scripts_project/s3_0_industry_ratios.py、scripts_project/s3b_r2_ois_today.py、scripts_project/s4l_5_data.py、scripts_project/s4m_0_data.py
- **修正前 → 修正后（第 129 项）：** 工业电力 VN 964 / ID 1,801 TWh（固定路线）→ 内生；“其他工业”改为有用热三温度带（<150、150–400、>400 °C）、载体内生；生物质溢出改为等量有用热（× 0.90），第 115 项 0.98 不再需要。方案，M08 实施（M08-6）。
- **注册表 param_id 范围：** industry_low_temperature_heat_*、industry_other_*、industry_ois_*、industry_efficiency_*、industry_ratio_source、industry_sector_ratios_*、industry_coal_*、industry_biomass_overflow_*、industry_hydrogen_*、industry_carrier*、industry_pe_*、industry_subsector_*、s4m_decision_115_*、s4l5_biomass_*；拟增 industry_route_mode_proposed、biomass_overflow_rule、demand_industry_electricity_not_anchored
- **附件 B：用途（精简）：** 工业低温热、“其他工业”回退桶能耗与载体路线，固体生物质需求超出潜力部分的处理。
- **附件 B：来源（精简）：** UNSD 2019 工业能耗；载体比率 JRC-IDEES-2021 EU27 与 PyPSA-Eur v2025.07.0 路线；固体生物质超出潜力部分转为甲烷
- **附件 B：11 国覆盖（精简）：** 11 国同一方法；UNSD 子部门缺失时由活动量推导
- **附件 B：修正方向（精简）：** “其他工业”与生物质溢出改为分温度带有用热、载体内生（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 69：A 1、B 50、C 18
- **附件 B：是否同口径：** 现行：是；修正后：是

### 6. 排放核算输入：过程排放、原料碳、废弃物、逸散

- **模型中的用途：** 净零约束中的过程排放、化工原料碳、废塑料焚烧与国内化石燃料逸散排放。
- **主算来源（机构、文件、年份、版本，表号或页码）：** EDGAR_2025_GHG（IEA-EDGAR CO2 v4，IPCC 2006 分类，2019）2.A / 2.C × 工业乘数；原料碳 territorial（决定 56）= EDGAR 2.B + 2.D × 乘数；废弃物 What a Waste 3.0 国别数据集 × IPCC 2006 Vol.5 Ch.2 Table 2.4；逸散 = EDGAR 1.B ÷ UNSD 2019 产量。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 162：A 5、B 142、C 15；全部 245 行；S4R：—（S4R 核查表未单列）
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国；EDGAR 空值国家为 0（SOURCE_ZERO）；LA 塑料份额缺失用加权均值（C）；BN / TL 处理方式缺失按 0。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。同一来源、同一方法；缺项按统一规则补。
- **处理脚本：** scripts_project/s2_0_process_emissions.py、scripts_project/s2b_feedstock.py、scripts_project/d1_demand_shares.py
- **修正前 → 修正后（第 129 项）：** 不在第 126、129 项修正清单内（不变）。按工业乘数外推的部分会随 M08 重建需求表而变化（INFERENCE，S4R 未单列）。
- **注册表 param_id 范围：** process_emissions_*、edgar_*、feedstock_*、plastics_*、waste_*、fugitive_factor_*、share_waste_*
- **附件 B：用途（精简）：** 净零约束中的过程排放、化工原料碳、废塑料焚烧与国内化石燃料逸散排放。
- **附件 B：来源（精简）：** EDGAR 2025（IEA-EDGAR CO₂ v4，2019 年）过程与非能源排放；废弃物 What a Waste 3.0 + IPCC 2006；逸散 = EDGAR 1.B ÷ UNSD 产量
- **附件 B：11 国覆盖（精简）：** 11 国；来源为空的国家记 0，缺项按统一规则补
- **附件 B：修正方向（精简）：** 不在修正清单内
- **附件 B：等级（主算行实算）：** 主算行 162：A 5、B 142、C 15
- **附件 B：是否同口径：** 现行：是；修正后：是

### 7. 风光廓线（共用：ERA5 2013 cutout、atlite 重建）

- **模型中的用途：** 光伏、陆上风、海上风的 3 小时可用率廓线（每节点 3 个资源等级）。
- **主算来源（机构、文件、年份、版本，表号或页码）：** ERA5 2013 atlite cutout：PyPSA-meets-Earth & Andreyana (2026) PyPSA-Earth Weather Databundle of ASEAN v1（Zenodo doi:10.5281/zenodo.20325289；ERA5 C3S CDS doi:10.24381/cds.adbb2d47）；atlite 0.4.1；作者排除布局复用；PyPSA-Eur v2025.07.0 renewable 缺省（config.default.yaml 第 179–275 行）；resource_classes = 3（决定 75）；主变体 calibrated_modern（决定 74）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 5：A 1、B 4；全部 18 行；S4R：—
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国同一 cutout 与方法；单一天气年 2013。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。—
- **处理脚本：** scripts_project/s4a_profiles.py（生成）、scripts_project/s4a_1_data.py、scripts_project/s4b_3_data.py（登记）
- **修正前 → 修正后（第 129 项）：** 不变。
- **注册表 param_id 范围：** renewable_cutout_source、renewable_profile_*、renewable_resource_classes*、renewable_method_validation_*、renewable_rebuild_vs_original_*
- **附件 B：用途（精简）：** 光伏、陆上风、海上风的 3 小时可用率廓线（每节点 3 个资源等级）。
- **附件 B：来源（精简）：** ERA5 2013 年（PyPSA-Earth 东盟气象数据包 v1，Zenodo 10.5281/zenodo.20325289）；atlite 0.4.1；PyPSA-Eur v2025.07.0 缺省设置；每节点 3 个资源等级
- **附件 B：11 国覆盖（精简）：** 11 国同一数据与方法；单一天气年 2013
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 5：A 1、B 4
- **附件 B：是否同口径：** 现行：是；修正后：是

### 8. 潜力：光伏（地面）

- **模型中的用途：** 各节点地面光伏候选容量上限 p_nom_max。
- **主算来源（机构、文件、年份、版本，表号或页码）：** PyPSA-Earth（pypsa-asean）作者布局：Copernicus Global Land Cover 100 m v3.0.1（2019 nrt；可用类 20/30/40/50/60/90/100，排除林地 111–126、水体 80）、natura 保护区栅格（Sosa Arango 2020，Harvard Dataverse doi:10.7910/DVN/XIV9BL，WDPA）、4.6 MW/km²。分国上限值、土地类别、密度与 Copernicus 文件 SHA256 已由 M08-0 补登（数值 = 筛查网络 p_nom_max，继承自作者论文网络）；natura 行由 REFERENCE_ONLY 改为 REGISTERED（Harvard Dataverse wdpa_reclass.tif V1.3，MD5 与本地一致）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 15：A 1、B 14；全部 20 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国同一布局（BN 1.4、SG 0.4 GW 量小）。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。与 PyPSA-Eur 同型（S4R 核查表 0 格标出）。
- **处理脚本：** 作者链 pypsa-asean（build_renewable_profiles）；登记 scripts_project/s4a_1_data.py、scripts_project/s4a_3_potentials.py；对照 work/p1_step4r_20261020/scripts/s4r_r2_potentials.py
- **修正前 → 修正后（第 129 项）：** 密度 4.6 → 5.1 MW/km²（PyPSA-Eur v2025.07.0 第 270 行），p_nom_max × 1.1087（VN 411 → 456、ID 859 → 952、TH 1,108 → 1,229 GW），土地类别与保护区不变；开阔林 121–126 作上界敏感性（触发规则 IMPLEMENTATION_PLAN §2.1）。方案，M08 实施（M08-7）。
- **注册表 param_id 范围：** protected_areas_local_natura（M08-0 改 REGISTERED）、renewable_cap_built_solar_*、renewable_landcover_codes_built_solar、renewable_density_built_solar、renewable_copernicus_lc100_file（M08-0 补登）、renewable_correction_factor_solar_fork（SENSITIVITY）、potential_solar_*（REFERENCE_ONLY，官方对照）；拟增 renewable_capacity_per_sqkm_solar、renewable_landuse_rule_solar、renewable_openforest_sensitivity_trigger
- **附件 B：用途（精简）：** 各节点地面光伏候选容量上限。
- **附件 B：来源（精简）：** PyPSA-Earth 布局：Copernicus 全球土地覆盖 100 m v3.0.1（2019 年）可用类 20/30/40/50/60/90/100；WDPA 保护区栅格（Harvard Dataverse，Sosa Arango 2020，CC0）排除；4.6 MW/km²
- **附件 B：11 国覆盖（精简）：** 11 国同一布局
- **附件 B：修正方向（精简）：** 密度 4.6 → 5.1 MW/km²（与 PyPSA-Eur 一致），土地类别与保护区不变；开阔林作上界敏感性（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 15：A 1、B 14
- **附件 B：是否同口径：** 现行：是；修正后：是

### 9. 潜力：屋顶光伏

- **模型中的用途：** 屋顶光伏候选容量上限（分布式）。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 作者电力底座的 solar rooftop 候选（S4A 继承）：作者链 PyPSA-Earth prepare_sector_network.py（use_building_size）= 0.1 kW/m² × 屋顶可用面积（Microsoft Global ML Building Footprints × 按建筑面积分档的安装比例 0–0.66，cluster_global_buildings.py，Obane / IEEJ 方法）——分国值与方法已由 M08-0 补登（建筑输入不在本机，未复算；v1 写“PyPSA-Earth 无屋顶潜力方法”有误）；补充 01 改为 C 级（不可复现），敏感性 0.5×–1.5×；对照（只记录）：AEO8 p.140 ID 194–655 GWp（模型 / 对照 0.54–1.84）、MY 34 GWp（2.45）、VN 370 GWp（0.33），MyRER 屋顶 42 GW（MY 1.98），PDP8 屋顶 48.2 GW（VN 2.54）；成本 technology-data v0.15.0 solar-rooftop（cost_C_solar_rooftop_*）；贴现率 0.04（technology-data 自带值，见 discount_rate_uniform_main 描述）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 12：C 12；全部 17 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国均有候选（BN 1.5 … ID 356.1 GW）。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。同一作者规则（S4R 核查表 0 格标出）。
- **处理脚本：** 作者链（本项目无登记脚本）；scripts_project/s4a_3_potentials.py 只登记官方对照值
- **修正前 → 修正后（第 129 项）：** 不变（C 级，±50 %）。
- **注册表 param_id 范围：** renewable_cap_built_solar_rooftop_*、renewable_rooftop_method_built（M08-0 补登）；potential_solar_rooftop_*（REFERENCE_ONLY：AEO8 p.140、PDP8、MyRER）；成本行 cost_C_solar_rooftop_*（计入 T20）
- **附件 B：用途（精简）：** 屋顶光伏候选容量上限（分布式）。
- **附件 B：来源（精简）：** PyPSA-Earth 方法：Microsoft Global ML Building Footprints 屋顶面积 × 按建筑面积分档的安装比例 × 0.1 kW/m²；成本 technology-data v0.15.0
- **附件 B：11 国覆盖（精简）：** 11 国均有候选；建筑原始数据不在本机，无法复现，定为 C 级（±50 %）
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 12：C 12
- **附件 B：是否同口径：** 现行：是；修正后：是

### 10. 潜力与廓线：陆上风

- **模型中的用途：** 陆上风候选上限、容量因数校准与新机型。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 上限：PyPSA-Earth 布局 3 MW/km²（Copernicus 可用类含林地 111–126，距城镇类 50 1 km）——分国上限与土地规则已由 M08-0 补登；廓线 ERA5 100 m 风速 × alpha（Staffell & Pfenninger 2016 方法，S4B-3 校准，决定 74）；观测 CF：Ember yearly electricity data（CC BY 4.0）2019–2025；新机型 DEA Technology Data sheet “20 Onshore turbines”（technology-data v0.15.0 引用，2050）；台风暴露 IBTrACS v04r01（溢价主算关闭）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 31：B 22、C 9；全部 61 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** alpha：PH / TH / VN 实测（B）；其余 8 国用三国容量加权均值 1.046（C）。
- **是否同口径（是 / 否 / 有例外）：** 现行：有例外；修正后：有例外。alpha 分国实测 vs 均值，登记为口径差（S4R 核查表 11 格标出）。
- **处理脚本：** scripts_project/s4b_3_wind_calibration.py（计算）、scripts_project/s4b_3_data.py、scripts_project/s4b_4_data.py、scripts_project/s4a_1_data.py
- **修正前 → 修正后（第 129 项）：** 不变（与 PyPSA-Eur 同为 3 MW/km²）。
- **注册表 param_id 范围：** renewable_cap_built_onwind_*、renewable_landcover_codes_built_onwind、renewable_density_built_onwind（M08-0 补登）、onwind_alpha_*、onwind_observed_cf_ember_*、onwind_new_turbine_dea2050、onwind_calibration_*、onwind_gwa_*、renewable_gwa33_*、renewable_cf_irena2024_onshore_*、renewable_turbine_hub_height_onwind、renewable_proposed_*、typhoon_*、potential_onwind_*、potential_wind_*
- **附件 B：用途（精简）：** 陆上风候选上限、容量因数校准与新机型。
- **附件 B：来源（精简）：** PyPSA-Earth 布局 3 MW/km²（Copernicus 可用类含林地，距城镇 1 km）；ERA5 100 m 风速按各国观测发电（Ember 2019–2025）校准；DEA 2050 机型
- **附件 B：11 国覆盖（精简）：** PH、TH、VN 按实测校准，其余 8 国用三国加权均值
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 31：B 22、C 9
- **附件 B：是否同口径：** 现行：有例外；修正后：有例外

### 11. 潜力与廓线：海上风

- **模型中的用途：** 海上风（AC / DC）候选上限、并网成本与廓线。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 上限：PyPSA-Earth 布局（GEBCO 2025 水深 ≤ 50 m、离岸 30 km 分 AC / DC、AC 2 / DC 3 MW/km²、无航道排除、无漂浮）——分国上限、土地规则与 GEBCO / EEZ 文件已由 M08-0 补登；廓线用 PyPSA-Eur v2025.07.0 缺省（NREL_ReferenceTurbine_2020ATB_5.5MW @120 m、尾流 0.8855）——M08-0 核实：筛查廓线的海上风与 pypsa_eur 重建逐值相同；并网成本 PyPSA-Eur 公式（add_electricity.py 第 541、555–576 行，决定 82），线路长度系数 1.25。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 33：A 2、B 31；全部 47 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** ESMAP 无行的 MY / TH / BN / MM / TL / SG 候选保留（预期不被选）；LA 内陆无；SG 无直流候选。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。方法 11 国同一；S4R 核查表把 ESMAP 无行国家的说明记为 11 格“例外”，不是口径差。
- **处理脚本：** scripts_project/s4c_1_offwind_distance.py、scripts_project/s4c_1_data.py、scripts_project/s4a_1_data.py、scripts_project/s4b_4_data.py
- **修正前 → 修正后（第 129 项）：** 对齐 PyPSA-Eur：固定 ≤ 60 m、漂浮 60–1,000 m、ship_threshold 400（航运密度栅格已在 raw12）、DC 密度 3 → 2 MW/km²；机型 5.5 MW 与尾流 0.8855 已在主算（M08-0 核实，无需改）；F9 海上 alpha 校准（观测 CF DATA_PENDING，暂 1.0）。方案，M08 实施（M08-7）。
- **注册表 param_id 范围：** renewable_cap_built_offwind_ac_* / _dc_*、renewable_landcover_codes_built_offwind_*、renewable_density_built_offwind_*、renewable_gebco_file、renewable_eez_file、renewable_offwind_profile_check_built（M08-0 补登）、offwind_*、offshore_*、renewable_offshore_depth_rule、renewable_ship_density_raster（M08-0 改 REFERENCE_ONLY）、renewable_correction_factor_offwind_pypsa_eur、renewable_turbine_hub_height_offwind_*、renewable_cf_irena2024_offshore_*、potential_offwind_*；拟增 renewable_offshore_rule、offwind_alpha_calibration_rule
- **附件 B：用途（精简）：** 海上风（AC / DC）候选上限、并网成本与廓线。
- **附件 B：来源（精简）：** PyPSA-Earth 布局（GEBCO 2025 水深 ≤ 50 m，离岸 30 km 分交 / 直流，2 / 3 MW/km²）；机型 NREL 2020ATB 5.5 MW、尾流修正 0.8855（PyPSA-Eur 缺省）；并网成本按 PyPSA-Eur 公式
- **附件 B：11 国覆盖（精简）：** 11 国同一方法；LA 为内陆国，SG 无直流候选
- **附件 B：修正方向（精简）：** 水深 60 m、增设漂浮式、航道排除、密度统一 2 MW/km²（已确定方案，尚未实施）；机型与尾流已与 PyPSA-Eur 一致
- **附件 B：等级（主算行实算）：** 主算行 33：A 2、B 31
- **附件 B：是否同口径：** 现行：是；修正后：是

### 12. 水电（含径流、抽蓄）

- **模型中的用途：** 新建水电 / 径流 / 抽蓄候选上限，存量水电入流。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 候选上限 = 国家潜力 − 存量（决定 78）：VN Decision 500/QĐ-TTg（PDP8）III.1.b（A）；ID EBTKE 潜力统计 94,470 MW（B）；PH DOE RE briefer p.6（B）；MY SEDA MyRER（B）；MM ADB (2016) Myanmar Energy Sector Assessment p.13（B）；LA AEO8 p.75 引文献 [44]（C）；KH GEM GIPT 2026-09 管线（B）；BN / SG 无资源，TH / TL 管线为 0（SOURCE_ZERO）。抽蓄 = GEM 管线（宣布 + 前期，决定 86 b）。入流 = Ember 年发电量 × pypsa-asean config.default.yaml 第 445 行（national_observed，决定 83）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 36：A 1、B 34、C 1；全部 65 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** KH / TH / TL 官方水电潜力 DATA_PENDING；11 国抽蓄分国潜力 DATA_PENDING（用 GEM 管线）。
- **是否同口径（是 / 否 / 有例外）：** 现行：否；修正后：否。逐国官方来源，无统一方法，登记为例外（S4R 核查表 11 格标出）。
- **处理脚本：** scripts_project/s4b_2_candidates_data.py、scripts_project/s4a_3_potentials.py、scripts_project/s4c_2_data.py、scripts_project/s4c_0_data.py
- **修正前 → 修正后（第 129 项）：** 不变。
- **注册表 param_id 范围：** candidate_cap_hydro_*、candidate_cap_PHS_*、candidate_cap_switch_s4b2、candidate_pipeline_statuses_confirmed、candidate_new_*、hydro_inflow_*、hydro_smoke_*、potential_hydro_*、potential_PHS_*、cand_hydro_* / cand_ror_* / cand_PHS_*
- **附件 B：用途（精简）：** 新建水电 / 径流 / 抽蓄候选上限，存量水电入流。
- **附件 B：来源（精简）：** 新建上限 = 各国官方潜力 − 存量（VN PDP8、ID EBTKE、PH DOE、MY SEDA、MM ADB 2016、LA AEO8、KH GEM 项目库）；抽蓄 = GEM 项目库；存量入流按 Ember 年发电量校准
- **附件 B：11 国覆盖（精简）：** KH、TH、TL 官方水电潜力待补；抽蓄分国潜力待补（暂用 GEM 项目库）
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 36：A 1、B 34、C 1
- **附件 B：是否同口径：** 现行：否；修正后：否

### 13. 地热

- **模型中的用途：** 新建地热候选上限、存量地热参数与新建成本。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 候选上限（决定 78）：ID Badan Geologi / PSDMBP 2024-08-26（23,590 MW − 存量 = 22,421.5 MW）；MY SEDA MyRER 229 MW；PH GEM 管线等 3,124 MW；VN GEM 45 MW；其余 7 国 0（SOURCE_ZERO）。新建投资：AEO8 Table D.15 “Geothermal average” 4,100 kUSD/MW × 0.877229（决定 52）= 3,596.6 EUR2020/kW，FOM 0.4756 %/a、VOM 0.263 EUR2020/MWh（C，±30 %）——M08-0 补登独立值行。存量地热（M08-0 核实）：FOM / VOM 按同一 AEO8 行定价，寿命 30 a（v0.13.2 与 v0.15.0 同值），CO₂ 未计；原 v0.13.2 的 FOM / CO₂ 强度行改为 REFERENCE_ONLY。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 15：B 12、C 3；全部 39 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** BN / KH / LA / MM / SG / TH / TL / VN 官方潜力 DATA_PENDING（用 0 或 GEM 管线值）；存量地热效率 / VOM / 投资行由 DATA_PENDING 改为 REFERENCE_ONLY（网络用 AEO8 值，M08-0）。
- **是否同口径（是 / 否 / 有例外）：** 现行：否；修正后：否。逐国来源（同水电，S4R 核查表合并在“水电 / 地热”类）。
- **处理脚本：** scripts_project/s4b_2_candidates_data.py、scripts_project/s4a_3_potentials.py、scripts_project/d1_cost_layers.py
- **修正前 → 修正后（第 129 项）：** 投资的 AEO8 价格年 DATA_PENDING，敏感性 × [0.86, 1.00]（R6.2）。方案，M08 实施（M08-2）。
- **注册表 param_id 范围：** geothermal_new_investment_main / _FOM_main / _VOM_main（M08-0 补登）、candidate_cap_geothermal_*、geothermal_existing_*、potential_geothermal_*、cand_geothermal_*；拟增 aeo8_cost_price_year
- **附件 B：用途（精简）：** 新建地热候选上限、存量地热参数与新建成本。
- **附件 B：来源（精简）：** 新建上限：ID 地质局 2024、MY SEDA、PH / VN GEM 项目库，其余国家 0；新建投资 AEO8 Table D.15 Geothermal average 4,100 kUSD/MW × 2020 汇率 = 3,596.6 EUR2020/kW（±30 %）
- **附件 B：11 国覆盖（精简）：** 8 国官方潜力待补（暂按 0 或项目库值）
- **附件 B：修正方向（精简）：** AEO8 价格年未注明，作 × [0.86, 1.00] 敏感性（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 15：B 12、C 3
- **附件 B：是否同口径：** 现行：否；修正后：否

### 14. 生物质（潜力、成本）

- **模型中的用途：** 11 国固体生物质 / 沼气潜力池与原料成本。
- **主算来源（机构、文件、年份、版本，表号或页码）：** FAOSTAT QCL / FO 2019–2023 均值 × 增长 1.1716（IRENA 2022）× IRENA 2017 / 2022 残余比与收集率（0.75 农业 / 0.90 木质）；伐木残余主算为 0（决定 54）；城市固废 What a Waste 3.0 × IPCC 2006；成本 NRI / NEDO 2024、ERIA / IEEJ 2024 AZEC 价格调查（C，±50 %），USD2024 / IDR2024 × 0.73606 → EUR2020。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 249：A 11、B 41、C 197；全部 265 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国；IRENA 2017 饲料扣除只覆盖五国，其余用五国合计 0.2895（C）；油棕树干成本 5 国 DATA_PENDING；LA 城市固废成分 DATA_PENDING。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。11 国同一方法（S4R 核查表 0 格标出）。
- **处理脚本：** scripts_project/d1_biomass.py、scripts_project/s4c_0_data.py
- **修正前 → 修正后（第 129 项）：** 潜力不变；溢出规则改为有用热（见 T05）。方案，M08 实施（M08-6）。
- **注册表 param_id 范围：** biomass_potential_*、biomass_cost_*、biomass_constraint_*、biomass_growth_*、biomass_lhv_*、biomass_logging_*、biomass_msw_*、biomass_wood_*、biomass_methane_*、biomass_cross_*、biomass_replication_*、btl_capital_cost_x_efficiency
- **附件 B：用途（精简）：** 11 国固体生物质 / 沼气潜力池与原料成本。
- **附件 B：来源（精简）：** FAOSTAT 2019–2023 × IRENA 2017 / 2022 残余比与收集率；城市固废 What a Waste 3.0；成本 NRI / NEDO 2024、ERIA / IEEJ 2024（±50 %）
- **附件 B：11 国覆盖（精简）：** 11 国；油棕树干成本 5 国待补，LA 城市固废成分待补
- **附件 B：修正方向（精简）：** 潜力不变；溢出规则见工业热
- **附件 B：等级（主算行实算）：** 主算行 249：A 11、B 41、C 197
- **附件 B：是否同口径：** 现行：是；修正后：是

### 15. CO₂ 封存与区域内运输

- **模型中的用途：** 各国地质封存潜力与年注入上限；区域内 CO₂ 船运、管道、老挝过境成本。
- **主算来源（机构、文件、年份、版本，表号或页码）：** ERIA / GCCSI (2024) Comprehensive CCUS Research Report Ch.1（ID / MY / BN / TH P50，Tables 1.4–1.18）（A）；VN 11.8、PH 22.3 Gt：IEA (2021) CCUS: The Opportunity in Southeast Asia p.35（B）；KH 0.085、TL 0.25 Gt：OGCI / CSRC Cycle 5 (2025) Appendix B Asia（未能复核，M08-0 由 A 改为 C；本地 PDF 的汇总表为图片，文本提取不到数值）；LA / MM / SG 为 0；年上限 = 潜力 ÷ 50（决定 28）；船运链 IEAGHG (2004) PH4/30 Table 5-3（US$2004 × 1.16898）11.42 EUR/t + 0.00295 EUR/(t·km)，航线系数 1.091；老挝过境 Stolaroff et al. (2021) Table 2（USD2018）；封存成本 30 EUR/t（PyPSA-Eur v2025.07.0 config 第 711 行，价格年 DATA_PENDING）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 51：A 18、B 18、C 15；全部 71 行；S4R：A/B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** LA / MM 未评估（DATA_PENDING，按 0）；TL 无国家评估；SG 无封存潜力。
- **是否同口径（是 / 否 / 有例外）：** 现行：否；修正后：有例外。现行 ERIA / IEA / OGCI 三源混用；修正后统一 ERIA P50，KH / TL / LA / MM / SG 按规则（S4R 核查表 5 格标出）。
- **处理脚本：** scripts_project/d1_co2_storage.py、scripts_project/s4d_1_data.py、scripts_project/s4d_2_data.py、scripts_project/s4e_2_data.py、scripts_project/s4c_1_data.py、scripts_project/s4d_0_data.py
- **修正前 → 修正后（第 129 项）：** VN 11.8 → 5.303 Gt（年上限 236 → 106 Mt）、PH 22.3 → 0.067、KH 0.085 → 0.09（IJGGC 2014 低值）、TL 0.25 → 0（UNASSESSED）；VN 约 130 Mt/a 改走区域内船运（INFERENCE）。方案，M08 实施（M08-4；第 129 项已定）。
- **注册表 param_id 范围：** co2_storage_*、co2_injection_cap_*、co2_ship_*、co2_land_*、co2_lao_*、co2_sequestration_*、co2_chain_*、co2_inland_*、co2_intra_asean_shipping_switch、co2_ts_*、coastal_nodes_*、s4d1_*、s4d2_*、s4e2_*；拟改 co2_storage_potential_VN / PH / KH / TL / unassessed_LA / unassessed_MM；拟增 co2_sequestration_cost_price_year、co2_storage_vn_shipping_interaction
- **附件 B：用途（精简）：** 各国地质封存潜力与年注入上限；区域内 CO₂ 船运、管道、老挝过境成本。
- **附件 B：来源（精简）：** ERIA / GCCSI 2024（ID、MY、BN、TH P50）；IEA 2021（VN、PH）；OGCI CSRC Cycle 5（KH、TL，未能复核，C 级）；年注入上限 = 潜力 ÷ 50；运输链 IEAGHG 2004、Stolaroff et al. 2021；封存 30 EUR/t（PyPSA-Eur）
- **附件 B：11 国覆盖（精简）：** LA、MM 未评估（按 0）；SG 无封存潜力
- **附件 B：修正方向（精简）：** 统一为 ERIA 2024 P50，KH、TL 按规则；VN 11.8 → 5.3 Gt（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 51：A 18、B 18、C 15
- **附件 B：是否同口径：** 现行：否；修正后：有例外

### 16. LNG 接收站与气网

- **模型中的用途：** LNG 再气化容量与进口上限、码头扩建成本、国内与跨境气管道。
- **主算来源（机构、文件、年份、版本，表号或页码）：** GEM Global Gas Infrastructure Tracker – LNG Terminals（September 2025 release，文件 About 页核实；S4R 的“2025-08”为误记）：存量 = 运营 + 在建（A）；进口上限 = 有存量节点 2.5 × 存量（C，决定 17）、无存量节点按拟建容量（决定 72）——分国值 M08-0 补登：VN 278.67、ID 422.33、KH 14.67、PH 510.00、MY 243.33、SG 366.67、TH 633.33 TWh/a；扩建成本 7,018 EUR/MW/a（PyPSA-Eur import 分支 5a87cedd prepare_sector_network.py 第 4561 行代码常数，无来源、无价格年，C）；气管道 GEM GGIT Gas Pipelines 2025-11（B）；容量换算 PyPSA-Eur build_gas_input_locations.py 第 127 行。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 48：A 11、B 33、C 4；全部 113 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** BN / KH / LA / MM / TL 无存量（SOURCE_ZERO），KH 有拟建 1.1 Mtpa；MY–SG 管道容量 DATA_PENDING；9 个拟建单元容量 DATA_PENDING。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。同一 GEM 数据集、同一上限规则（S4R 核查表 0 格标出）。
- **处理脚本：** scripts_project/d1_lng_terminals.py、scripts_project/s3_1_gas_data.py、scripts_project/s3b_r3_lng_data.py、scripts_project/s4b_0_data.py、scripts_project/s4c_0_data.py
- **修正前 → 修正后（第 129 项）：** 取消 2.5× 上限、按成本内生扩建（lng_expansion: capex_only）；码头成本 7,018 → 8,020 EUR2020/MW/a（Ulvestad & Overland 2012，±50 %）；H₂ 码头 = LNG × 1.2。方案，M08 实施（M08-3；第 129 项已定）。
- **注册表 param_id 范围：** lng_import_cap_built_*、lng_import_cap_rule_built、lng_gem_ggit_release_verified（M08-0 补登）、lng_existing_capacity_*、lng_import_cap_*（2.5 × 存量部分，M08-0 加注）、lng_import_cap_factor、lng_mwh_per_mtpa、lng_terminal_*、lng_candidate_*、lng_regas_capex_ref_*、lng_upstream_*、gas_pipeline_*、pipeline_gem_*；拟改 lng_terminal_expansion_capex_main；拟增 lng_terminal_capacity_source、lng_terminal_cap_rule
- **附件 B：用途（精简）：** LNG 再气化容量与进口上限、码头扩建成本、国内与跨境气管道。
- **附件 B：来源（精简）：** GEM 全球天然气基础设施追踪 LNG 码头 2025 年 9 月版；有存量节点上限 2.5 × 存量、无存量节点按拟建容量（VN 278.67、ID 422.33、PH 510.00、TH 633.33 TWh/a 等）；扩建成本 7,018 EUR/MW/a（PyPSA-Eur）；气管道 GEM 2025 年 11 月版
- **附件 B：11 国覆盖（精简）：** BN、LA、MM、TL 无码头；KH 只有拟建 1.1 Mtpa；部分拟建单元容量缺失
- **附件 B：修正方向（精简）：** 取消 2.5 倍上限、按有出处成本内生扩建，码头成本改为 8,020 EUR2020/MW/a（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 48：A 11、B 33、C 4
- **附件 B：是否同口径：** 现行：是；修正后：是

### 17. 区域外进口与兜底选项价格

- **模型中的用途：** 区域外绿色载体（氢、氨、甲醇、FT 燃料）进口价、区域外 CO₂ 封存价与进口结构（兜底选项）。
- **主算来源（机构、文件、年份、版本，表号或页码）：** Neumann, Hampp, Brown (2025) Nat. Commun. doi:10.1038/s41467-025-60652-1，结果数据 Zenodo 10.5281/zenodo.14872184（2040 假设、欧洲到岸最低价）× 1.2（决定 17），EUR2020：氢 105.75、氨 116.78、甲醇 145.16、FT 150.11 EUR/MWh；2040→2050 降幅估计 9–12 %（technology-data v0.15.0 costs_2040 / costs_2050 × Neumann Table A.1 份额）；区域外封存 54.70 EUR2020/t = IEAGHG 2004 PH4/30 船运链 4,500 km（24.70）+ 统一封存 30（决定 95 a）；氢进口在 LNG 码头节点，上限 = 码头上限；原油 / 煤为区域池 / 节点池、无上限（价格见 T19）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 21：B 12、C 9；全部 42 行；S4R：B
- **11 国覆盖情况（缺哪些国家、如何补）：** 区域统一价，两情景相同。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。S4R 核查表 0 格标出。
- **处理脚本：** scripts_project/s3_2_imports_data.py、scripts_project/s3_7_import_price_decline.py、scripts_project/s4c_4_data.py、scripts_project/s4d_1_data.py、scripts_project/s4d_2_data.py、scripts_project/s4e_2_data.py
- **修正前 → 修正后（第 129 项）：** 不变（再气化加价作用于 LNG，见 T16 / T19）。
- **注册表 param_id 范围：** import_price_*、import_h2_terminal_rule、import_oil_structure、import_coal_structure、import_chain_decline_*、co2_extra_asean_*、co2_intra_vs_extra_asean_cost_note
- **附件 B：用途（精简）：** 区域外绿色载体（氢、氨、甲醇、FT 燃料）进口价、区域外 CO₂ 封存价与进口结构（兜底选项）。
- **附件 B：来源（精简）：** Neumann, Hampp, Brown (2025) Nat. Commun.（Zenodo 10.5281/zenodo.14872184）× 1.2；区域外封存 = IEAGHG 2004 船运链 + 30 EUR/t
- **附件 B：11 国覆盖（精简）：** 区域统一价
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 21：B 12、C 9
- **附件 B：是否同口径：** 现行：是；修正后：是

### 18. 国内化石燃料产量上限

- **模型中的用途：** 煤、油、气国内供应年上限及节点分配；逸散因子的分母。
- **主算来源（机构、文件、年份、版本，表号或页码）：** UNSD Energy Statistics Database 2019 国别产量（A）→ 2050 年上限 = 2019 产量（B，决定 43）；气田节点分配 GEM Global Oil and Gas Extraction Tracker 2026-03（C）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 85：A 33、B 47、C 5；全部 87 行；S4R：—（S4R 核查表未单列）
- **11 国覆盖情况（缺哪些国家、如何补）：** 无产量国家为 0（SOURCE_ZERO）；TL 气 2050 上限沿用 2019（Bayu-Undan 已枯竭，S4P 待核实）；TL 节点分配 DATA_PENDING。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。同一来源、同一规则。
- **处理脚本：** scripts_project/d1_fossil_production.py、scripts_project/s3_1_gas_data.py、scripts_project/s4a_2_fleet_data.py
- **修正前 → 修正后（第 129 项）：** 不变。
- **注册表 param_id 范围：** fossil_production_*、gas_production_*
- **附件 B：用途（精简）：** 煤、油、气国内供应年上限及节点分配；逸散因子的分母。
- **附件 B：来源（精简）：** UNSD 2019 国别产量；2050 上限 = 2019 产量；气田节点分配 GEM 油气开采追踪 2026 年 3 月版
- **附件 B：11 国覆盖（精简）：** 无产量国家为 0；TL 节点分配待补
- **附件 B：修正方向（精简）：** 不变
- **附件 B：等级（主算行实算）：** 主算行 85：A 33、B 47、C 5
- **附件 B：是否同口径：** 现行：是；修正后：是

### 19. 燃料价格与燃料碳

- **模型中的用途：** 区域外 LNG、原油、煤价格（国产气 = LNG 价，决定 43）与燃料碳计法。
- **主算来源（机构、文件、年份、版本，表号或页码）：** IEA World Energy Outlook 2025 Table 2.3（p.109）STEPS 2050（决定 85）：天然气（日本）9.7 USD/MBtu → 27.07、原油 76 USD/bbl → 35.32、动力煤（日本）84 USD/t → 8.86 EUR2020/MWh（NCV）；USD2024 → EUR2020 × 0.73606（FRED A191RD3A086NBEA × ECB 2020 年均）；燃料碳按 PyPSA-Eur，进口绿色载体零碳（决定 64）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 12：A 1、B 11；全部 37 行；S4R：—（S4R 核查表未单列）
- **11 国覆盖情况（缺哪些国家、如何补）：** 区域统一价。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。—
- **处理脚本：** scripts_project/d1_fuel_prices.py、scripts_project/s3_5_fuel_carbon_data.py、scripts_project/s4c_0_data.py
- **修正前 → 修正后（第 129 项）：** 再气化加价 0 → 1.26 EUR2020/MWh（0.5 USD2024/MMBtu；东南亚专门值仍 DATA_PENDING）。方案，M08 实施（M08-3）。
- **注册表 param_id 范围：** fuel_price_*、fuel_carbon_*；拟改 fuel_price_lng_regasification_adder
- **附件 B：用途（精简）：** 区域外 LNG、原油、煤价格（国产气 = LNG 价，决定 43）与燃料碳计法。
- **附件 B：来源（精简）：** IEA《World Energy Outlook 2025》Table 2.3 STEPS 2050：气 27.07、油 35.32、煤 8.86 EUR2020/MWh
- **附件 B：11 国覆盖（精简）：** 区域统一价
- **附件 B：修正方向（精简）：** LNG 加再气化费 1.26 EUR2020/MWh（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 12：A 1、B 11
- **附件 B：是否同口径：** 现行：是；修正后：是

### 20. 技术成本

- **模型中的用途：** 全部新建技术的投资、FOM、VOM、效率、寿命（发电、储能、电解、合成、CCS、DAC、线路、管道）。
- **主算来源（机构、文件、年份、版本，表号或页码）：** PyPSA technology-data v0.15.0（tag commit 07e43575）outputs/costs_2050.csv，EUR2025 → EUR2020 × 0.833196（= 100 / EA20 GDP 平减 2025，ECB MNA）（决定 50）；SMR 与地热投资例外（见 T23、T13）。存量机组（电力底座）的成本与效率沿用作者成本表（technology-data v0.13.2，2030 年值）：存量固定运维常数 108.1 亿 EUR/a，继承的存量 CCGT 效率 0.57（新建 0.60）——M08-0 核实，统一性问题交 M08。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 181：A 3、B 178；全部 242 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国同表。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。11 国同表；平减残余 +4.8 %（升通胀用 HICP、回算用 GDP 平减）作用于全部行（S4R 核查表 0 格标出）。
- **处理脚本：** scripts_project/s2_0_cost_layer_v015.py、scripts_project/d1_cost_layers.py、scripts_project/s4c_1_data.py
- **修正前 → 修正后（第 129 项）：** 改用 technology-data 升通胀的同一口径回算：Eurostat HICP（prc_hicp_aind）欧洲经济区 EEA 年均变化率累乘，2020→2025 系数 1.2573（补充 01 核实：technology-data v0.15.0 用 EEA，不是欧元区；文件已获取），消除 +4.8 % 残余（B6 −1.8 bn）；存量机组改用 v0.15.0 对应年份（如 costs_2020 / costs_2025）的成本与效率，统一来源与版本、保留老机组效率较低。方案，M08 实施（M08-1；存量部分在重建时）。
- **注册表 param_id 范围：** cost_C_*（176 行）、cost_layer_*（cost_layer_A_* 由 M08-0 改 REFERENCE_ONLY）、cost_v0132_usage_built（M08-0）、download_eurostat_hicp_aind_2016_2025（补充 01）、technology_data_*、cand_cost_consistency_check、config_cost_*、cost_audit_*；敏感性层 cost_B_*（51 行）；拟增 cost_layer_deflator_hicp
- **附件 B：用途（精简）：** 全部新建技术的投资、FOM、VOM、效率、寿命（发电、储能、电解、合成、CCS、DAC、线路、管道）。
- **附件 B：来源（精简）：** PyPSA technology-data v0.15.0（2050 年），EUR2025 → EUR2020；SMR、地热用 AEO8；存量机组成本与效率沿用作者成本表（technology-data v0.13.2）
- **附件 B：11 国覆盖（精简）：** 11 国同表
- **附件 B：修正方向（精简）：** 按 technology-data 同一通胀口径（欧洲经济区 HICP 年变化率）回算，消除 +4.8 % 残余；存量机组改用 v0.15.0 对应年份（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 181：A 3、B 178
- **附件 B：是否同口径：** 现行：是；修正后：是

### 21. WACC / 贴现率

- **模型中的用途：** 资本成本年金化。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 统一实际贴现率 0.07（technology-data v0.15.0 / pypsa-asean config.default.yaml costs.fill_values 第 579 行；决定 90）；8 个分散式行（含屋顶光伏）0.04（technology-data 自带值）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 2：B 2；全部 19 行；S4R：B/C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国统一。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。主算统一；分国表只作敏感性（S4R 核查表 TL 1 格标出，指敏感性表）。
- **处理脚本：** scripts_project/s4c_0_data.py
- **修正前 → 修正后（第 129 项）：** 主算不变；分国实际 WACC 表（IEA Cost of Capital Observatory 2025 + Damodaran 2026-01 + IMF WEO 2026-10）只做表、作敏感性（TL DATA_PENDING）。
- **注册表 param_id 范围：** discount_rate_uniform_main、finance_wacc_mode、wacc_country_model_*（DATA_PENDING）、wacc_iea_*、wacc_irena_*；拟增 wacc_country_real_table
- **附件 B：用途（精简）：** 资本成本年金化。
- **附件 B：来源（精简）：** 统一实际贴现率 7 %（technology-data / PyPSA-Earth 缺省）；分布式技术 4 %
- **附件 B：11 国覆盖（精简）：** 11 国统一
- **附件 B：修正方向（精简）：** 主算不变；分国实际 WACC 只作敏感性
- **附件 B：等级（主算行实算）：** 主算行 2：B 2
- **附件 B：是否同口径：** 现行：是；修正后：是

### 22. 跨境候选通道（电力、管道）与网络损耗

- **模型中的用途：** 跨境交流 / 直流候选线路、存量、扩建上限、长度与海缆份额、线路损耗。
- **主算来源（机构、文件、年份、版本，表号或页码）：** ACE (2024) APG Interconnections Project Profiles Table 1 p.2（APG / AIMS III 优先项目）+ 陆地邻接补齐（S4E-1，决定 94）+ S4H-2 候选（决定 101）→ 通道表 CORRIDORS_S4H2；每条扩建上限 +20,000 MW（PyPSA-Eur v2025.07.0 config 第 324 行，决定 96）；长度 = 大圆距离 × 1.25（冻结底座 19 条存量跨境线中位数）；AIMS 存量（TH–MY HVDC 300 MW、LA–VN 0 MW）；线路成本见 T20；交流损耗线性代理（决定 108）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 10：B 7、C 3；全部 66 行；S4R：B
- **11 国覆盖情况（缺哪些国家、如何补）：** 各国至少 1 条候选（BN / PH / TL 各 1）。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。S4R 核查表 0 格标出。
- **处理脚本：** scripts_project/s3_0_corridors.py、scripts_project/s4e_1_corridors.py、scripts_project/s4f_2_corridors.py、scripts_project/s4h_2_data.py、scripts_project/s4c_1_data.py、scripts_project/s4k_1_data.py
- **修正前 → 修正后（第 129 项）：** 主算不变（F3 已定）；登记不互联定义（删除全部区域内跨境固定网络，含存量；“保留存量不新建”作敏感性）。方案，M08 实施（M08-8，登记）。
- **注册表 param_id 范围：** corridor_*、pypsa_eur_lines_max_extension、la_vn_grid_stock_2025、th_my_*、s4e1_* … s4k1_*（多为 REFERENCE_ONLY 步骤记录）；拟增 disconnected_definition_main / _sensitivity
- **附件 B：用途（精简）：** 跨境交流 / 直流候选线路、存量、扩建上限、长度与海缆份额、线路损耗。
- **附件 B：来源（精简）：** ACE (2024) APG 互联项目概况（AIMS III 优先项目）+ 陆地邻接补齐；每条扩建上限 +20 GW（PyPSA-Eur）；长度 = 大圆距离 × 1.25
- **附件 B：11 国覆盖（精简）：** 各国至少 1 条候选
- **附件 B：修正方向（精简）：** 主算不变；明确不互联定义（删除全部区域内跨境网络，含存量）
- **附件 B：等级（主算行实算）：** 主算行 10：B 7、C 3
- **附件 B：是否同口径：** 现行：是；修正后：是

### 23. 核电 / SMR

- **模型中的用途：** 大型核电与 SMR 候选的允许条件与成本。
- **主算来源（机构、文件、年份、版本，表号或页码）：** 允许：大型核电 10 国（SG 除外，决定 38）、SMR 11 国，无上限（决定 79，nuclear_cap = none）；大型核电成本 technology-data v0.15.0 nuclear（Lazard v16.0 来源）9,003 EUR2020/kW；SMR：ACE AEO8 (2024) Appendix D Table D.15（p.197）9,600 kUSD/MW × 0.877229 = 8,421 EUR2020/kW、FOM 1.146 %/a、VOM 1.93 EUR/MWh（C，价格年未注明）；寿命 / 效率代理 technology-data v0.13.2 nuclear 40 a / 0.326（与 v0.15.0 同值，M08-0 核实）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 5：C 5；全部 17 行；S4R：C
- **11 国覆盖情况（缺哪些国家、如何补）：** 11 国统一成本；SG 不允许大型核电。
- **是否同口径（是 / 否 / 有例外）：** 现行：有例外；修正后：有例外。SG 大型核电不允许（决定 38）；S4R 核查表记为“否”（11 格标出）。
- **处理脚本：** scripts_project/d1_cost_layers.py、scripts_project/s4b_2_candidates_data.py、scripts_project/s4a_3_potentials.py
- **修正前 → 修正后（第 129 项）：** SMR = technology-data 核电 × AEO8 同表比值（投资 1.0667、FOM 1.37、VOM 0.43）→ 9,603 EUR2020/kW。方案，M08 实施（M08-2）。
- **注册表 param_id 范围：** smr_*、nuclear_cap_switch_s4b2、nuclear_plan_cap_*（SENSITIVITY）、cand_nuclear_*、cand_smr_*、potential_nuclear_*；拟增 nuclear_cost_rule
- **附件 B：用途（精简）：** 大型核电与 SMR 候选的允许条件与成本。
- **附件 B：来源（精简）：** 大型核电 technology-data v0.15.0（9,003 EUR2020/kW）；SMR AEO8 Table D.15（8,421 EUR2020/kW）
- **附件 B：11 国覆盖（精简）：** 11 国统一成本；SG 不允许大型核电
- **附件 B：修正方向（精简）：** SMR 改为同源比值（technology-data 核电 × AEO8 SMR / 大型堆比值）（已确定方案，尚未实施）
- **附件 B：等级（主算行实算）：** 主算行 5：C 5
- **附件 B：是否同口径：** 现行：有例外；修正后：有例外

### 24. 存量机组

- **模型中的用途：** 2050 年仍在役的存量机组（容量、类型、节点）及其运维成本。
- **主算来源（机构、文件、年份、版本，表号或页码）：** Global Energy Monitor, Global Integrated Power Tracker 2026-09（CC BY 4.0，东盟 6,958 单元）+ 冻结电力底座（S4A / S4B-1）；在役规则 = 投运年 ≤ 2050 < 投运年 + 寿命（configs/powerplantmatching_config.yaml 第 419–432 行；决定 77 放宽在建单元）；存量 FOM 用作者表 costs_2030_elec.csv（EUR，2020 / 2023 / 2010–15 混合年份）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 15：A 1、B 14；全部 37 行；S4R：B
- **11 国覆盖情况（缺哪些国家、如何补）：** TL 无新增行（其余 10 国有 fleet_additions_2050_*）；垃圾发电单元跳过（DATA_PENDING）。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。S4R 核查表 0 格标出。
- **处理脚本：** scripts_project/s4a_2_fleet_data.py、scripts_project/s4b_1_fleet_data.py
- **修正前 → 修正后（第 129 项）：** 存量 FOM 按年份用 EA20 GDP 平减到 2020（两情景相同，B6 不受影响）；存量成本与效率改用 technology-data v0.15.0 对应投运年份的数值（补充 01：现为作者 v0.13.2 表，统一性问题，M08 处理）。方案，M08 实施（重建时）。
- **注册表 param_id 范围：** fleet_*；existing_fleet_cost_source_unification（补充 01：存量成本表版本，统一性问题，M08 处理）
- **附件 B：用途（精简）：** 2050 年仍在役的存量机组（容量、类型、节点）及其运维成本。
- **附件 B：来源（精简）：** Global Energy Monitor 全球综合电力追踪 2026 年 9 月版 + 作者电力底座；2050 年在役 = 投运年 + 寿命 > 2050
- **附件 B：11 国覆盖（精简）：** TL 无新增；垃圾发电单元未建模
- **附件 B：修正方向（精简）：** 存量运维费按年份统一平减到 2020 年；存量成本与效率改用 technology-data v0.15.0 对应投运年份（重建时）
- **附件 B：等级（主算行实算）：** 主算行 15：A 1、B 14
- **附件 B：是否同口径：** 现行：是；修正后：是

### 25. 货币、汇率与单位换算

- **模型中的用途：** 全部货币输入统一到 EUR2020；能量与体积单位换算。
- **主算来源（机构、文件、年份、版本，表号或页码）：** ECB 欧元参考汇率 2020 年均 0.877229 EUR/USD（currency_converter 0.18.9 内置 eurofxref-hist）（B）；EA20 GDP 平减指数（ECB Data Portal MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N）（A）；美国 GDP 平减（FRED A191RD3A086NBEA）（A）；UNSD 2014 标准净热值、IPCC 2006 Vol.2 Ch.1 Table 1.2、IEA toe 定义（A）。
- **数据等级（注册表实算；S4R 核查表）：** 主算行 24：A 19、B 5；全部 24 行；S4R：—（S4R 核查表未单列）
- **11 国覆盖情况（缺哪些国家、如何补）：** 通用。
- **是否同口径（是 / 否 / 有例外）：** 现行：是；修正后：是。只有一个汇率。
- **处理脚本：** scripts_project/d1_registry.py、scripts_project/d1_cost_layers.py、scripts_project/s2_0_cost_layer_v015.py、scripts_project/s4c_4_data.py、scripts_project/s4d_1_data.py
- **修正前 → 修正后（第 129 项）：** 报告货币 USD2020，1 EUR2020 = 1.1422 USD2020（= 1 / 0.877229）；如需 USD2024 再 × 1.1918；模型货币仍为 EUR2020（第 125、126 项）。方案，M08 实施（M08-10，导出层加美元列）。
- **注册表 param_id 范围：** conv_*、deflator_*、fx_usd_to_eur_2020 / _2024、author_rule_fx_usd_eur_2020；拟增 report_currency_rule
- **附件 B：用途（精简）：** 全部货币输入统一到 EUR2020；能量与体积单位换算。
- **附件 B：来源（精简）：** ECB 2020 年均汇率 0.877229 EUR/USD；EA20 GDP 平减（ECB）；美国 GDP 平减（FRED）；UNSD 2014 与 IPCC 2006 热值
- **附件 B：11 国覆盖（精简）：** 通用
- **附件 B：修正方向（精简）：** 报告货币改为 USD2020（1 EUR2020 = 1.1422 USD2020），模型仍为 EUR2020
- **附件 B：等级（主算行实算）：** 主算行 24：A 19、B 5
- **附件 B：是否同口径：** 现行：是；修正后：是

## 表 2　敏感性使用的数据

| 序号 | 类别 | 来源 | 用于哪项敏感性 | 记录位置（注册表 / 证据文件） |
|---|---|---|---|---|
| 1 | 需求 | World Bank WDI 2019–2025 + IIASA SSP2 2025 GDP 乘数 | 国别分配变体 country_allocation = gdp | demand_gdp_multiplier_*（11 行）、demand_wdi_real_gdp_growth_2019_2022_asean10（SENSITIVITY） |
| 2 | 需求 | ACE AEO8 (2024) BAS 情景（Table C.3 p.182） | 需求上界敏感性（修正后 BAS 由主算链转为敏感性） | demand_aeo8_bas_2050_*（现为主算链 REGISTERED）；S4R IMPLEMENTATION_PLAN §5 |
| 3 | 需求 | AEO8 ATS 的 country_allocation 其余三种（gdp / population / level） | 国别分配方法敏感性 | demand_country_allocation_mode（REGISTERED，主值 aeo8_ats_relative）；S4R IMPLEMENTATION_PLAN §5 |
| 4 | 工业产量 | 增长弹性 ε 0.3–0.8；人均饱和 水泥 0.6–1.2、粗钢 0.4–0.8 t/人（依据 Bleischwitz et al. 2018 GEC 48、van Ruijven et al. 2016 RCR 112、Pauliuk et al. 2013 RCR 71、Global Cement、worldsteel 人均表，均为饱和证据，无点估计） | R1.3 产量规则敏感性 | 注册表无记录（S4R 拟增 industry_output_elasticity、industry_percap_saturation_cement / _steel；DEMAND_ANCHOR_COMPARISON.csv 的 *_low / *_high 列） |
| 5 | 工业产量 | Viet Nam Decision 261/QĐ-TTg (2026-02-09) 钢铁战略 2050 年 65–70 Mt；Decision 1266/QĐ-TTg (2020-08-18) Annex I 水泥 ≤ 150 Mt/a | VN 规划值敏感性（只作上限，不抬高主算产量） | 注册表无记录（S4R 拟增 industry_output_plan_sensitivity_VN） |
| 6 | 工业路线 | JRC-IDEES-2021 EU27 × PyPSA-Eur v2025.07.0 pypsa_eur_2050 固定路线（现行主算） | 修正后作路线敏感性（对照有用热内生） | industry_ratio_source、industry_efficiency_*（现为 REGISTERED）；S4R IMPLEMENTATION_PLAN §5 |
| 7 | 工业路线 | JRC-IDEES-2021 Industry EU27 sheet OIS_fec 2019 载体份额 | “其他工业”桶 other_bucket = ois_today | industry_ois_today_*（8 行，SENSITIVITY） |
| 8 | 工业路线 | UNSD 2019 各国“其他工业”自身载体结构 | other_bucket = asean_own_2019 | industry_other_bucket_asean_own_2019（SENSITIVITY） |
| 9 | 生物质 | 第 115 项溢出上限份额 0.98（S4L-5 诊断） | 生物质溢出上限诊断（修正后不再需要） | s4l5_biomass_overflow_cap_share（SENSITIVITY）；s4m_decision_115_biomass_cap_share（REGISTERED） |
| 10 | 生物质 | 第 36 项贸易规则：跨境生物质 | 生物质跨境贸易敏感性 | biomass_cross_*（REGISTERED，规则行）；S4R IMPLEMENTATION_PLAN §5 |
| 11 | 排放核算 | PyPSA-Eur 缺省“原料碳全部释放”（非能源用途 × technology-data CO₂ 强度） | feedstock_carbon_mode = full_release | feedstock_full_release_2050_*（11 行，SENSITIVITY） |
| 12 | 排放核算 | EDGAR 2025 × 需求 level 方法的工业乘数 | 需求 level 方法下的过程排放 | process_emissions_*_2050_level_*（25 行，SENSITIVITY） |
| 13 | 光伏 | pypsa-asean config.default.yaml 第 418 行 solar 校正 0.854337（Pietzcker et al. 2014） | 原链光伏廓线校正对照 | renewable_correction_factor_solar_fork（SENSITIVITY） |
| 14 | 光伏 | Copernicus Global Land Cover 100 m v3.0.1 开阔林类 121–126（作者缓存全球文件 1.71 GB）；ESMAP / Solargis (2020) Level 1 × 5.1 MW/km² 上界 | 开阔林上界敏感性 s4r_openforest（按触发规则升级） | 注册表无记录（S4R 拟增 renewable_openforest_sensitivity_trigger；POTENTIAL_COMPARISON.csv、evidence/SOLARGIS_ESMAP_2020_ASEAN11.csv） |
| 15 | 光伏 | WDPA 最新版（2026-10，未下载，> 2 GB） | 保护区边界更新敏感性 | download_declined_wdpa_full（REFERENCE_ONLY）；USER_DOWNLOAD_LIST B2 |
| 16 | 陆上 / 海上风 | IBTrACS v04r01（Knapp et al. 2010）暴露 + Tarp-Johansen & Clausen (2006) 台风机型溢价 +25 %（20–30 %） | 台风溢价 typhoon_premium = on | typhoon_premium_switch（SENSITIVITY）、typhoon_* |
| 17 | 海上风 | 观测海上 CF（VN 只有近岸项目；来源 DATA_PENDING） | F9 海上 alpha 校准（到位前 alpha = 1.0） | 注册表无记录（S4R 拟增 offwind_alpha_calibration_rule） |
| 18 | LNG | GEM GGIT LNG Terminals 2025-09：(b) 项目口径（运营 + 在建 + 拟建）、(c) 2.5 × 存量、existing_only | R3 LNG 上限敏感性（主算取消上限后） | lng_terminal_expansion_cap_factor、lng_terminal_expansion_mode（SENSITIVITY）；s4d6_sensitivity_lng_cap、s4e2_sensitivity_lng_uncapped（REFERENCE_ONLY） |
| 19 | LNG | Ulvestad & Overland (2012) Int. J. Environ. Stud. 69(3) 码头 1 bn USD / 10 Mtpa → 8,020 EUR2020/MW/a | 码头成本 ±50 % | lng_regas_capex_ref_ulvestad_overland_2012（REFERENCE_ONLY；拟改 lng_terminal_expansion_capex_main） |
| 20 | 进口价 | Neumann et al. (2025) Zenodo 14872184 × 1.2 | 进口价 ±20 % | import_price_sensitivity（SENSITIVITY）、import_price_sensitivity_low_fraction |
| 21 | 燃料价 | IEA WEO 2025 Table 2.3 CPS / NZE 2050 | 化石燃料价格情景（NZE 已按第 124 项舍弃） | fuel_price_*_CPS_2050_optional、fuel_price_*_NZE_2050_main（6 行，SENSITIVITY） |
| 22 | 燃料价 | ECB 2024 年均汇率 0.9244 后再欧元平减（备选换算路径，+7 %） | 燃料换算路径敏感性 | fx_usd_to_eur_2024（REGISTERED，备选）；S4R 拟登记 fuel_price_conversion_path（未列入 REGISTRY_ROWS_PROPOSED） |
| 23 | 技术成本 | ACE AEO8 (2024) Appendix D Table D.15 / D.17 × 作者规则（层 B） | 成本层 B 敏感性（research.cost_layer） | cost_B_*（51 行）、cost_layer_B_aeo8_author_rule_2050（SENSITIVITY） |
| 24 | 技术成本 | FRED A191RD3A086NBEA（USD2023 → USD2020 = 0.887） | AEO8 价格年因子 × [0.86, 1.00]（SMR、地热） | 注册表无记录（S4R 拟增 aeo8_cost_price_year） |
| 25 | 核电 | VN Decision 768/QĐ-TTg；PH PEP 2023–2050 Vol I p.19–20（4,800 MW）；ID RUPTL / 新闻约 10 GW；TH PDP 草案 600 MW SMR | 核电国家规划上限 nuclear_cap = national_plans | nuclear_cap_switch_s4b2、nuclear_plan_cap_ID / PH / TH / VN（SENSITIVITY） |
| 26 | 存量机组 | GEM GIPT 2026-09 在建单元 | 在建单元是否计入 2050 存量 | fleet_include_construction_units（SENSITIVITY） |
| 27 | WACC | IEA Cost of Capital Observatory 2025；Damodaran (2026-01) Country Risk Premiums；IMF WEO 2026-10 CPI | F7 分国实际 WACC（面谈议题） | 注册表无记录（S4R 拟增 wacc_country_real_table；COUNTRY_WACC_SENSITIVITY_TABLE.csv）；wacc_country_model_* 为 DATA_PENDING |
| 28 | CO₂ 封存 | ERIA / GCCSI (2024) P90 / P10；IJGGC (2014) KH 高值 45 Gt；Santos (2022) / IFC Bayu-Undan 10 Mtpa | 封存潜力敏感性 | co2_storage_potential_* 的 sensitivity_low / high 列（现为旧口径）；S4R CO2_STORAGE_UNIFIED.csv |
| 29 | CO₂ 运输 | IEAGHG (2004) PH4/30：区域外封存成本 × 0.5 / 1.5；船运航线系数 0.75 / 1.25 | 首批登记、未运行的敏感性 | s4d6_sensitivity_extra_asean_cost、s4d6_sensitivity_ship_route_factor（REFERENCE_ONLY） |
| 30 | CO₂ 运输 | ZEP (2011) Figure 19 离岸咸水层封存 Medium 14 EUR2009/t → 16.05 EUR2020/t | 封存成本敏感性 | co2_storage_cost_zep_sensitivity（REFERENCE_ONLY） |
| 31 | CO₂ 运输 | 老挝过境至最近既有港口（第 95 项 d） | 老挝过境路线敏感性 | s4e2_sensitivity_lao_transit（REFERENCE_ONLY） |
| 32 | 跨境通道 | ACE (2024) APG Interconnections / AIMS III 规划容量（18 个项目） | apg_plans：按规划容量设上限 | s4f1_apg_plan_caps、s4g2_apg_plans_rule_confirmed（REFERENCE_ONLY） |
| 33 | 跨境通道 | 作者 readjust 阻抗；SG–VN / SG–KH 通道 | 第二批登记、未运行的敏感性 | s4g2_sensitivity_readjust_author、s4f2_sensitivity_sg_vn_kh（REFERENCE_ONLY） |
| 34 | 不互联定义 | 现网络 2025 存量（24 条电力边 + 3 条气管道） | “保留存量不新建”敏感性 | 注册表无记录（S4R 拟增 disconnected_definition_sensitivity） |

## 表 3　收集过但未采用的数据

| 序号 | 数据 | 来源（机构、文件、年份） | 查过的环节 | 未采用原因 | 记录位置 |
|---|---|---|---|---|---|
| 1 | 光伏 / 风电官方潜力 | VN Decision 500/QĐ-TTg（PDP8）与 Decision 768 光伏 963 GW、陆上风 221 GW、海上风 600 GW；ID ESDM 2023 光伏 3,294 GW；MY SEDA MyRER 269 GW；PH DOE CREZ 光伏 58 GW / 陆上风 94 GW；NREL 2000 菲律宾风图谱 | 注册表（S4A-3）；S4P §4.3 | 各国方法、排除规则与年份不一，只作合理性对照。 | potential_solar_*、potential_onwind_*、potential_offwind_VN_*（REFERENCE_ONLY） |
| 2 | 光伏潜力 | ESMAP / Solargis / World Bank (2020) Global Photovoltaic Power Potential by Country，Level 1 面积（Ch.2 p.12–13；国别表 solargis_pvpotential_countryranking_2020_data.xlsx） | S4R R2 | Level 1 不排除保护区、只排除郁闭度 ≥ 50 % 的密林，与 PyPSA-Eur 口径不同；只用于比值分解与开阔林敏感性上界。 | 注册表无记录（S4R evidence/SOLARGIS_ESMAP_2020_ASEAN11.csv、POTENTIAL_COMPARISON.csv） |
| 3 | 光伏 / 风电潜力 | Zhong et al. (2026) PNAS Nexus pgaf389 SI Table S3（高 / 中潜力，10 国） | S4R R2 | “高”值为 NREL 技术潜力、无土地排除，高出 ESMAP 3–10 倍，量级过高，不作上限。 | 注册表无记录（S4R POTENTIAL_COMPARISON.csv） |
| 4 | 光伏 / 风电潜力 | Zhong et al. (2025) iScience SI Table S6（mmc1.pdf p.10–11） | S4R R2 | 与 PNAS Nexus 同一口径，只作对照。 | 注册表无记录（S4R POTENTIAL_COMPARISON.csv） |
| 5 | 模型代码 | ESI_APG_Model_v2.3.zip（Zhong 等配套代码，用户下载） | S4R 资料 | 只登记了文件哈希，未用于任何数值。 | 注册表无记录（S4R_EVIDENCE.json 输入清单） |
| 6 | 光伏栅格 | Global Solar Atlas 光伏潜力栅格 zip（global-pv-potential-study-raster-data-layers，约 1 GB） | S4R 资料 | 未解压、未使用（主算只改密度，不需栅格重算）。 | 注册表无记录（S4R_EVIDENCE.json：raster zip not used） |
| 7 | 海上风潜力 | World Bank Group / ESMAP Global Offshore Wind Technical Potential（国别 xlsx）；WB Offshore Wind Roadmap for Vietnam (2021) / Philippines (2022) | S4P EXT_TECH_POLICY_BENCHMARKS；S4R R2 | 只作海上风对照（VN 599、PH 181、ID 277 GW）；主算沿用布局并拟对齐 PyPSA-Eur 规则。 | potential_offwind_PH_doe_wb_roadmap_technical（REFERENCE_ONLY）；ESMAP 国别表注册表无记录 |
| 8 | 陆上风 CF | Global Wind Atlas 3.3 国别统计（DTU / World Bank） | 注册表（S4A-1） | 只作陆上风 CF 交叉核对。 | renewable_gwa33_*、onwind_gwa_crosscheck_s4b3（REFERENCE_ONLY） |
| 9 | 风电 CF | IRENA (2025) Renewable Power Generation Costs in 2024，Table 4.3（海上）、Figure 2.12（陆上，图读） | 注册表（S4A-1） | 无东盟海上值；陆上为图读值，只作对照。 | renewable_cf_irena2024_*（REFERENCE_ONLY） |
| 10 | 屋顶光伏潜力 | ACE AEO8 (2024) p.140（ID 194–655 GWp、MY 34 GWp、VN 370 GWp）；PDP8 屋顶 48.2 GW；MyRER 屋顶 42 GW | 注册表（S4A-3） | 各来源口径不一，只作对照；主算沿用作者候选。 | potential_solar_rooftop_*（REFERENCE_ONLY） |
| 11 | 需求锚 | ERIA (2024) Analysis on Energy Cost of LCET-CN, RPR FY2024 No.12 国别章（TFEC、发电、工业） | S4P §4.4.1；S4R R1 | 情景包含载体结构（碳中和 2050），作对照锚，不作主锚。 | 注册表无记录（S4R 拟增 demand_anchor_family_control）；S4P evidence/EXT_DEMAND_BENCHMARKS.json |
| 12 | 需求锚 | IEA Southeast Asia Energy Outlook 2024（p.54、86）与 2026 网页（STEPS / APS） | S4P §4.4.1；S4R R1 | 只有区域值，作区域合理性检查。 | 注册表无记录（S4P evidence/EXT_DEMAND_BENCHMARKS.json） |
| 13 | 国家电力规划 | VN Decision 768/QĐ-TTg（修订 PDP8，经 KPMG 2025）；ID RUKN 2025–2060（Kepmen 85.K/2025）；PH PEP 2023–2050 Vol. I；MY NETR 2023 / IRENA METO 2023；KH PDP 2022–2040；SG EMA Energy 2050 Committee Report；TH PDP2024 草案（Agora 2024） | S4P §4.4.1 | 各国口径、年份与情景不一，只作对照（VN 电力与 PDP8 一致，ID / TH / MY 偏高）。 | 注册表无记录（S4P evidence/EXT_DEMAND_BENCHMARKS.json） |
| 14 | 氢需求 / 目标 | VN Decision 165/QĐ-TTg (2024)；ID 国家氢氨路线图 (2025)；MY HETR (2023) / NETR；SG National Hydrogen Strategy (2022) | S4P EXT_DEMAND_BENCHMARKS | 政策目标而非需求锚，只作对照。 | 注册表无记录（S4P evidence/EXT_DEMAND_BENCHMARKS.json） |
| 15 | 工业产量对照 | USGS Mineral Commodity Summaries 2021（VN 97、ID 70 Mt 水泥 2019）；Asosiasi Semen Indonesia 2024 销量；RIPIN 2015–2035；ID 钢需求 100 Mt（新闻）；SEAISI 产能（经 Wood Mackenzie） | S4P §4.4.1 第 5 节 | 只作对照；修正后基年用 USGS MCS 2025 / worldsteel WSIF 2025。 | 注册表无记录（S4P evidence/EXT_DEMAND_BENCHMARKS.json） |
| 16 | 水电 / 地热其他官方数字 | ESDM 2023（水电 95 GW、地热 23 GW）；ESDM 部长 2025（地热 23.7 GW，ThinkGeoEnergy）；PH CREZ 地热 365 MW、PEP 新增 1,355 MW | 注册表（S4A-3） | 同一国家有多个数字，主算取一个来源，其余只作对照。 | potential_hydro_ID_esdm_2023、potential_geothermal_*（REFERENCE_ONLY） |
| 17 | 抽蓄潜力 | ANU Global Greenfield PHES Atlas（Stocks et al. 2021，东南亚 2,210,850 GWh）；VN PDP8 抽蓄 2050 目标；TH EGAT 规划 | 注册表（S4A-3） | 图集为区域合计、分国站点清单未处理；规划为目标非潜力；只作对照。 | potential_PHS_*（REFERENCE_ONLY / DATA_PENDING） |
| 18 | 核电规划 | VN Decision 768（4,000–6,400 MW）；PH PEP（4,800 MW）；ID 约 10 GW（Stimson 2025、AP 2026）；AEO8 区域 10 GW | 注册表（S4A-3）；S4P §4.3 | 主算无政策上限（决定 38、79），只作对照与敏感性上限来源。 | potential_nuclear_*（REFERENCE_ONLY） |
| 19 | 技术成本版本 | technology-data v0.13.2 / v0.13.4 costs_2050.csv | 注册表（D1） | 已由 v0.15.0 取代（决定 50），只作版本对照。 | technology_data_v0_13_4_comparison、technology_data_v0_15_0_comparison（REFERENCE_ONLY）；cost_layer_A_technology_data_v0_13_2_2050 已由 M08-0 改为 REFERENCE_ONLY（历史） |
| 20 | 外部成本基准 | IEA WEO 2025 Table B.4b（亚洲核电 2,500–2,800 USD2024/kW、光伏 / 陆上风）；IRENA RPGC 2024；EIA / S&L (2024) AEO2025 Table 1-2；INL/RPT-24-77048 Rev.2 Table A-1；世行 VN 海上风路线图 2021 Table 9.2 | S4P §4.7.1 | 只作合理性对照；主算统一用 technology-data（11 国同表）。 | 注册表无记录（S4P evidence/EXT_COST_BENCHMARKS.json） |
| 21 | 进口价基准 | IRENA (2022) 氢贸易 Part I；Hydrogen Council (2023)；Neumann et al. (2024) arXiv 2404.03927；BNEF（二手）；DLR (2025)；IRENA (2022) 氨 | S4P §4.7.1 | 主算用 Neumann 2025 数据集（PyPSA 体系、价格年明确），其余只作对照。 | 注册表无记录（S4P evidence/EXT_COST_BENCHMARKS.json）；arXiv 原文存于 registry_v5/sources/neumann2024/（未跟踪） |
| 22 | LNG 码头成本 | ERIA (2016) RPR FY2016 No.7b Ch.6 LNG 供应链投资 | 注册表（S3B R3） | 日元口径、含储罐，不可直接换算，只作参考。 | lng_regas_capex_ref_eria_2016（REFERENCE_ONLY） |
| 23 | LNG 进口量 | GIIGNL Annual Report 2026（2025 年进口量与码头动态）；ar-2026-major-flows.pdf | S4R R3 | 只作容量交叉核对（2025 年利用率 12–55 %），不设上限；major-flows 文件未引用数值。 | 注册表无记录（S4R LNG_CAPACITY_COMPARISON.csv、S4R_EVIDENCE.json） |
| 24 | 再气化费 | Argus Media (2024-09-13)；Höegh LNG / IGU (2017) 0.3 USD/MMBtu；IGU World LNG Report 2024、OIES NG149（未能取得） | S4P §4.7.1；S4R R3.4 | 不是东南亚专门值，只用于确定加价 0.5 USD/MMBtu 的区间。 | fuel_price_lng_regasification_adder（DATA_PENDING）；S4P evidence/EXT_COST_BENCHMARKS.json |
| 25 | 封存与运输成本基准 | GCCSI (2025-12) Cost of CO2 Storage（离岸 US$5–31/t）；ERIA (2022) Vol. II（US$12.9/t）；BEIS (2018)、IEAGHG (2020) 船运成本 | S4P §4.5；注册表（S4C-4） | 只作 30 EUR/t 与船运链的合理性对照。 | co2_extra_asean_cost_crosscheck（REFERENCE_ONLY） |
| 26 | 封存成本参考 | ADB (2013) Prospects for CCS in SE Asia：ID 管道 + 封存 17 USD2011/t | 注册表（D1） | 只作对照。 | co2_ts_cost_reference_ID_2011USD（REFERENCE_ONLY） |
| 27 | CO₂ 陆运 | Stolaroff et al. (2021) Table 2 卡车 0.111 $/t-km；Gao et al. (2011) 铁路（经 Stolaroff 转引） | 注册表（S4D-1） | 主算用铁路（用户决定），卡车只作备选，铁路交叉核对在区间内。 | co2_land_transport_truck_unit_cost、co2_land_transport_crosscheck（REFERENCE_ONLY） |
| 28 | CCS 项目 | Kasawari 3.3 Mtpa（2027）、Arthit 约 1 Mtpa（2028）、Tangguh UCC 约 15 Mt 累计 | S4R R5 | 只记录注入爬坡，不设政策上限。 | 注册表无记录（S4R CO2_STORAGE_UNIFIED.md） |
| 29 | WACC 名义值 | IEA Cost of Capital Observatory（2025 dashboard，名义税后）；IRENA (2023)（未能取得） | 注册表（S4C-0）；S4P §4.7.1 | 名义税后值，主算用统一实际 0.07；只用于分国 WACC 表。 | wacc_iea_*、wacc_irena_*（REFERENCE_ONLY） |
| 30 | 保护区栅格 | WDPA 全分辨率最新版（WDPA_Oct2026_Public，4.68 GB shp / 2.00 GB gdb，HTTP HEAD 2026-10-16） | 注册表（S4B-4） | > 2 GB，未下载（用户决定）；主算沿用 2020 Dataverse 栅格。 | download_declined_wdpa_full（REFERENCE_ONLY） |
| 31 | 海上风规则 | 浮式海上风、航道排除、PyPSA-Eur 装机密度、60 m 水深（第 76 项推迟） | 注册表（S4B-4） | 推迟到首批云端试算之后；修正方案拟对齐。 | offshore_deferred_items_s4b4（REFERENCE_ONLY） |
| 32 | 风电方法提案 | GWA 偏差缩放（S4A-1.4B）；IEC T 级台风机型溢价（决定 3） | 注册表（S4A-1） | 提案未实施（CANDIDATE_ONLY）；台风溢价另作敏感性。 | renewable_proposed_gwa_bias_scaling、renewable_proposed_typhoon_class（CANDIDATE_ONLY） |
| 33 | 采暖类份额 | PyPSA-Eur v2025.07.0：reduce_space_heat_exogenously（第 641–642 行）、district_heating.progress（第 487 行） | 注册表（D1） | 东盟不适用（决定 25：制冷留在电力负荷）。 | share_reduce_*、share_district_*（REFERENCE_ONLY） |
| 34 | 排放口径 | EDGAR 2025 2.B（化工）、2.D（非能源产品）、4.C 化石部分（垃圾焚烧）作过程排放 | 注册表（S2-0） | 由原料碳核算覆盖，避免重复计入。 | edgar_nonenergy_*、edgar_waste_*、部分 process_emissions_*（REFERENCE_ONLY） |
| 35 | 氨 / 甲醇工艺成本 | technology-data v0.15.0 costs_2050（Haber-Bosch、甲醇合成等 28 行） | 注册表（S3-3） | 成本层已含同一数据，这里只复现以便核对。 | ammonia_methanol_*（REFERENCE_ONLY 29 行） |

## 表 4　DATA_PENDING 与 C 级假设

| 序号 | 类型 | 项目 | 影响国家 | 当前处理方式 | 计划如何补齐 | 记录位置 |
|---|---|---|---|---|---|---|
| 1 | 注册表待补（DATA_PENDING） | 钢铁基年工艺结构（BF-BOF / EAF） | 产钢国 | 现行不需要（未显式建钢铁路线） | 仅在显式建模钢铁路线时补（worldsteel SSY） | steel_process_structure_2019（A，DATA_PENDING） |
| 2 | 注册表待补（DATA_PENDING） | 抽蓄分国潜力 | 11 国 | 抽蓄候选 = GEM 管线（宣布 + 前期） | ANU 图集分国站点清单需处理；未列入下载清单 | potential_PHS_per_country_ALL_DATA_PENDING（C） |
| 3 | 注册表待补（DATA_PENDING） | 水电官方潜力 | KH、TH、TL | KH 用 GEM 管线 4,170 MW；TH、TL 为 0 | 官方或一手潜力文件；未列入下载清单 | potential_hydro_KH / TH / TL_DATA_PENDING（C） |
| 4 | 注册表待补（DATA_PENDING） | 地热官方潜力 | BN、KH、LA、MM、SG、TH、TL、VN、PH（总资源） | 按 0 或 GEM 管线值（VN 45 MW） | 未列入下载清单 | potential_geothermal_*_DATA_PENDING（9 行，C） |
| 5 | 注册表待补（DATA_PENDING） | 油棕树干原料成本 | ID、KH、MY、PH、TH | 潜力已登记，成本缺失（注册表未写明替代值） | 未列入下载清单 | biomass_cost_*_oil_palm_trunk（5 行，C） |
| 6 | 注册表待补（DATA_PENDING） | 城市固废成分（沼气潜力） | LA | 无成分数据，潜力未计 | What a Waste 成分数据；未列入下载清单 | biomass_potential_LA_msw_organic_biogas（C） |
| 7 | 注册表待补（DATA_PENDING） | LA / MM 封存潜力 | LA、MM | 按 0（决定 30） | 无国家评估；修正方案拟改状态为 UNASSESSED（不是 SOURCE_ZERO） | co2_storage_potential_unassessed_LA / MM（C；S4R 拟改 A 级 UNASSESSED） |
| 8 | 注册表待补（DATA_PENDING） | MY–SG 气管道容量 | MY、SG | 容量未知（GEM 1991 年运营，70 km） | 未列入下载清单 | gas_pipeline_existing_malaysia_singapore（B） |
| 9 | 注册表待补（DATA_PENDING） | 拟建 LNG 单元容量 | ID 1、MY 3、VN 5 个单元 | GEM 无容量，按 0 | 修正后取消 2.5× 上限、按成本内生扩建，影响减小 | lng_candidate_*（9 行，A） |
| 10 | 注册表待补（DATA_PENDING） | TL 气田节点分配 | TL | 按负荷份额 | 未列入下载清单 | gas_production_node_allocation_TL（C） |
| 11 | 注册表待补（DATA_PENDING） | LNG 再气化加价 | LNG 进口国 | 未加（0） | 修正方案拟 1.26 EUR2020/MWh（0.5 USD2024/MMBtu，第 129 项已定）；东南亚专门值仍 DATA_PENDING | fuel_price_lng_regasification_adder、fuel_price_regasification_adder_s4c（C） |
| 12 | 注册表待补（DATA_PENDING） | 分国实际 WACC | 11 国 | 主算统一 0.07，不受影响 | 分国实际 WACC 敏感性表已算 10 国（TL DATA_PENDING）；原始区间需 IEA 观测站导出（下载清单 B6） | wacc_country_model_*（11 行，C） |
| 13 | 注册表待补（DATA_PENDING） | 垃圾发电存量单元 | 有垃圾发电的国家（约 170 MW） | 跳过（模型无垃圾燃料路径） | 无计划（模型局限） | fleet_waste_to_energy_skipped_s4b（C） |
| 14 | 统一性核查识别的待补数据 | AEO8 Table D.15 价格年 | 11 国（SMR、地热投资） | 视作 EUR2020（× 0.877229，未平减） | 敏感性 × [0.86, 1.00]；下载清单 B7（向 ACE 查询） | 注册表无记录（S4R 拟增 aeo8_cost_price_year） |
| 15 | 统一性核查识别的待补数据 | LNG 码头成本 7,018 EUR/MW/a 的来源与价格年 | LNG 进口国 | 主算用 7,018（PyPSA-Eur import 分支代码常数） | 改用 Ulvestad & Overland 2012 换算 8,020 EUR2020/MW/a（±50 %） | lng_terminal_expansion_capex_main（C，REGISTERED）；S4R 拟改 |
| 16 | 统一性核查识别的待补数据 | CO₂ 封存成本 30 EUR/t 的价格年 | 11 国 | 视作 EUR2020 | 登记 DATA_PENDING，±50 % 敏感性 | 注册表无记录（S4R 拟增 co2_sequestration_cost_price_year） |
| 17 | 统一性核查识别的待补数据 | TL 2050 人口原文件 | TL | 已获取（unpopulation_dataportal_20261020224306.csv：UN WPP 2024，TL 2050 中位 1,889,249.5 人），M08 实施 | M08 实施 | download_un_wpp2024_tl_population_2050（REFERENCE_ONLY，补充 01）；S4R 拟增 demand_anchor_tl_rule |
| 18 | 统一性核查识别的待补数据 | TL 封存潜力 | TL | 现 0.25 Gt（OGCI，未能复核）→ 拟 0 | 无国家评估；Bayu-Undan 10 Mtpa 作项目型敏感性 | co2_storage_potential_TL（M08-0 由 A 改 C，REGISTERED）；S4R 拟改 |
| 19 | 统一性核查识别的待补数据 | KH 封存可复核来源 | KH | 现 0.085 Gt（OGCI，未能复核）→ 拟 0.09（IJGGC 2014 低值） | OGCI CSRC Cycle 5 Appendix B 本地已有，但汇总表为图片、未能复核 | co2_storage_potential_KH（M08-0 由 A 改 C，REGISTERED）；S4R 拟改 |
| 20 | 统一性核查识别的待补数据 | 海上风观测容量因数（F9） | VN 等海上风国家 | alpha = 1.0 | 数据到位后按 S4B-3 方法校准；来源未定 | 注册表无记录（S4R 拟增 offwind_alpha_calibration_rule） |
| 21 | 统一性核查识别的待补数据 | USGS 年鉴水泥世界表（水泥基年 2023） | 11 国（SG、TL 不在表中，按 0） | 已获取（myb1-2023-cemen-ERT.xlsx：USGS 年鉴 2023 水泥表 T22，2019–2023 年），M08 实施；水泥基年 2023，11 国同一来源 | M08 实施 | download_usgs_myb2023_cement_world_t22（REFERENCE_ONLY，补充 01）；S4R 拟增 industry_output_base_year |
| 22 | 统一性核查识别的待补数据 | worldsteel 粗钢产量（钢铁基年 2024） | 11 国（BN、KH、LA、TL 不在表中，按 0） | 已获取（exp-2026-10-20_15_02_22.xlsx：worldsteel Steel Data Viewer，2021–2025 年），M08 实施；钢铁基年 2024，11 国同一来源 | M08 实施 | download_worldsteel_crude_steel_2021_2025（REFERENCE_ONLY，补充 01）；S4R 拟增 industry_output_base_year |
| 23 | 统一性核查识别的待补数据 | Eurostat HICP 年均指数与年变化率 | 全部 technology-data 行（11 国） | 已获取（prc_hicp_aind$defaultview_spreadsheet.xlsx：Eurostat HICP 2016–2025），M08 实施；technology-data v0.15.0 按欧洲经济区（EEA）年均变化率升通胀（2020→2025 系数 1.2573），回算用同一口径 | M08 实施 | download_eurostat_hicp_aind_2016_2025（REFERENCE_ONLY，补充 01）；S4R 拟增 cost_layer_deflator_hicp |
| 24 | 统一性核查识别的待补数据 | 产量–GDP 弹性点估计、人均饱和一手序列 | 11 国 | ε = 0.5、饱和 1.0 / 0.6 t/人，登记为假设（C） | 文献只给饱和证据；无下载项 | 注册表无记录（S4R 拟增 industry_output_elasticity、industry_percap_saturation_*） |
| 25 | 统一性核查识别的待补数据 | TL WACC | TL | 无 IEA 条目、无 Damodaran 行 | 无计划 | wacc_country_model_TL（C）；S4R COUNTRY_WACC_SENSITIVITY_TABLE.csv |
| 26 | C 级假设（主算行，按类别汇总） | 需求：终端能耗总量与国别增长：C 级主算行 4 行 | 见注册表各行（多为区域统一值） | AEO8 未给 2019 值的部门（居民、商业、农业及其他）2019→2022 桥接取 1；交通桥接按份额推算 | 随需求锚定方法改写（修正方案） | 注册表 T01 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 27 | C 级假设（主算行，按类别汇总） | 需求：基础电力负荷（居民、商业、农业及其他）：C 级主算行 5 行 | 见注册表各行（多为区域统一值） | PyPSA-Eur 欧洲农机电气化份额直接采用 | 无替代来源；随需求活动量锚定 | 注册表 T02 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 28 | C 级假设（主算行，按类别汇总） | 需求：交通（陆运、航运、航空、燃料舱）：C 级主算行 20 行 | 见注册表各行（多为区域统一值） | PyPSA-Eur 欧洲 2050 交通份额、BEV 参数直接采用 | 修正后锚 ATS 服务量（修正方案）；份额仍为 C 级 | 注册表 T03 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 29 | C 级假设（主算行，按类别汇总） | 需求：工业物理产量与工艺（钢、水泥、氨、甲醇、HVC、铝）：C 级主算行 39 行 | 见注册表各行（多为区域统一值） | 氨、甲醇需求按 EU27 份额派生；PyPSA-Eur 2050 路线份额与工艺系数 | 修正后产量规则（ε、饱和水平为新增 C 级假设） | 注册表 T04 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 30 | C 级假设（主算行，按类别汇总） | 需求：工业热与其他工业能耗（路线、比率、生物质溢出）：C 级主算行 18 行 | 见注册表各行（多为区域统一值） | 工业氢需求（H₂-DRI 1.7 MWh/t 等派生）与 2050 工业保留煤（均为 0） | 修正后有用热内生（修正方案） | 注册表 T05 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 31 | C 级假设（主算行，按类别汇总） | 排放核算输入：过程排放、原料碳、废弃物、逸散：C 级主算行 15 行 | 见注册表各行（多为区域统一值） | 未收集垃圾份额以未收集人口份额代理、LA 塑料份额代理、排放边界规则 | 无下载项 | 注册表 T06 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 32 | C 级假设（主算行，按类别汇总） | 潜力与廓线：陆上风：C 级主算行 9 行 | 见注册表各行（多为区域统一值） | 8 国 alpha 用 PH / TH / VN 容量加权均值；台风暴露节点判定规则 | 无计划（登记为口径差） | 注册表 T10 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 33 | C 级假设（主算行，按类别汇总） | 水电（含径流、抽蓄）：C 级主算行 1 行 | 见注册表各行（多为区域统一值） | LA 水电潜力引 AEO8 p.75 文献 [44] | 无计划 | 注册表 T12 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 34 | C 级假设（主算行，按类别汇总） | 生物质（潜力、成本）：C 级主算行 197 行 | 见注册表各行（多为区域统一值） | 原料成本 ±50 %；FAOSTAT × IRENA 系数派生的潜力 | 无下载项（成本为 2024 年东南亚公开价格调查） | 注册表 T14 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 35 | C 级假设（主算行，按类别汇总） | CO₂ 封存与区域内运输：C 级主算行 15 行 | 见注册表各行（多为区域统一值） | CO₂ 船运链、老挝过境、陆运成本与航线系数 | 无下载项 | 注册表 T15 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 36 | C 级假设（主算行，按类别汇总） | LNG 接收站与气网：C 级主算行 4 行 | 见注册表各行（多为区域统一值） | 2.5× 上限、7,018 码头成本、扩建模式 | 修正后取消上限、改 8,020（修正方案） | 注册表 T16 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 37 | C 级假设（主算行，按类别汇总） | 区域外进口与兜底选项价格：C 级主算行 9 行 | 见注册表各行（多为区域统一值） | 进口价 2040→2050 降幅估计、敏感性下限、区域外封存成本换算 | 无下载项 | 注册表 T17 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 38 | C 级假设（主算行，按类别汇总） | 国内化石燃料产量上限：C 级主算行 5 行 | 见注册表各行（多为区域统一值） | 气田节点分配（GEM GOGET 2026-03） | 无下载项 | 注册表 T18 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 39 | C 级假设（主算行，按类别汇总） | 跨境候选通道（电力、管道）与网络损耗：C 级主算行 3 行 | 见注册表各行（多为区域统一值） | 通道节点对与长度、TH–MY 91 号线存量容量 | 无下载项 | 注册表 T22 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |
| 40 | C 级假设（主算行，按类别汇总） | 核电 / SMR：C 级主算行 5 行 | 见注册表各行（多为区域统一值） | SMR 成本取 AEO8 D.15（价格年未注明）、效率代理 | 修正后同源比值规则（修正方案） | 注册表 T23 类 C 级行（分类规则见 scripts/meet_data_inventory.py） |

