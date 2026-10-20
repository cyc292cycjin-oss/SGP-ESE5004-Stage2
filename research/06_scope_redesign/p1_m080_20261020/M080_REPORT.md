# M08-0 报告：注册表补登与一致性修正（第 130 项；只改注册表，不改模型、不求解）

## 摘要（≤ 10 行）

1. 注册表按"筛查运行实际使用的值"补登：1,962 → 2,052 行（新增 90、修改 32、删除 0）；构建读取的数值无一改变；未求解、未连云、未调用 Gurobi，未改配置、构建 / 求解脚本、网络与既有结果。
2. §J 缺口 1–5 全部补登：风光（含屋顶光伏）分国候选上限 55 行与土地规则 / 密度 / 数据文件 SHA256；Astar 形状来源；地热新建投资 3,596.6 EUR2020/kW（及 FOM / VOM）；决定 72 下 LNG 分国上限（VN 278.67、ID 422.33、KH 14.67、PH 510.00 TWh/a 等），原"2.5 × 存量"行保留并加注。
3. 海上风（VERIFIED）：筛查网络用 NREL 2020ATB 5.5 MW、尾流 0.8855——注册表正确，S4R 写的"NREL 5 MW、无尾流"有误。M08-7 无需再改机型与尾流，只剩会改变 `p_nom_max` 的海上面积规则；航道栅格已在本机。
4. Astar（VERIFIED）：作者论文网络的基础负荷 = GEGIS（GlobalEnergyGIS）2030 年国别曲线（PyPSA-Earth 数据包 `Asia.nc`，SSP2-RCP2.6、ERA5 2013），9 国形状与 GEGIS 成比例（相关 ≥ 0.99999），LA / TL 借用 KH / ID。GEGIS 的开发者 / 论文本地未载明，未补填。
5. v0.13.2：新建组件全部用 v0.15.0（+ AEO8 SMR / 地热）；v0.13.2 数值上只出现在 SMR 寿命 / 效率代理与存量寿命（均与 v0.15.0 同值）以及**电力底座存量机组的成本与效率**（作者 v0.13.2 表：存量固定运维 108.1 亿 EUR/a，存量 CCGT 效率 0.57 对新建 0.60）——后者是两版本混用的统一性问题，交 M08，本步未改模型。
6. 状态 / 等级：natura → REGISTERED；v0.13.2 成本层 → 历史；KH / TL 封存 A → C；另修正同类过时状态 12 行（廓线变体 / 分级 / 廓线文件 6、航运栅格 1、存量地热 5）。未新增状态值（校验写在代码里），历史行用 REFERENCE_ONLY + "历史：已被 X 替代"。注册表相关测试 91 passed / 24 skipped，与基线一致。
7. S4R 新版本：`REGISTRY_ROWS_PROPOSED_v2.csv`（7 行改 add、错位行对齐、9 行注明被替代旧行）、`USER_DOWNLOAD_LIST_v2.md`（删 A1）；数据清单 v2 与附件 B 精简版已生成，精简版 664 格全部能在 v2 详表中原文找到。
8. 需要审阅端确认的 4 项与仍未解决的项见 §7、§8。

## 1. 边界、方法与核对

- 指令 SHA256 `7e72998d…144e` 与 `M080_INSTRUCTION_SHA256.txt` 一致。分支 `codex/m08-0-registry-backfill-20261020`，自 S4R 头 `cefab870` 开出，独立工作树 `/home/jin/wt_m080_20261020`（主检出在 S4O 分支，未动）。
- **筛查网络**：S4O 云包未求解网络 `integrated_365_24h_unsolved.nc`（SHA256 `4206ec5c…`）与 `disconnected_365_24h_unsolved.nc`（`b411223e…`），构建提交 `126110ff`，与包内 `SHA256SUMS` 一致；S4P 的网络提取即取自这两个文件。风光与 LNG 上限在一体化与不互联网络中完全相同。
- **只读提取**：`scripts/m080_extract.py`（12 s，峰值内存 0.57 GB）→ `evidence/M080_EXTRACT.json` 与 3 个 CSV；读网络、廓线文件属性、作者论文网络（`elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc`，SHA256 `06152be5…`）元数据与负荷、作者链数据文件哈希。
- **写入方式**：`scripts_project/m080_data.py` 生成 `fragments/m080.csv`（新行）与 `fragments/m080_corrections.csv`（对已有行的整行替换）；`d1_registry.py` 只增加片段名与"按 param_id 整行替换"几行，原片段不动（保留为历史）。修正行从原片段读取，脚本可重复运行。
- **复现性**：现有片段 + 主检出中的 `fragments/s4c_0.csv` 重拼，得到的注册表与 `cefab870` 逐字节一致（SHA256 `46e234d7…2e50`）。该片段被 `.gitignore` 的 `*.csv` 忽略、从未提交，干净检出无法重拼；本步强制入库。重拼时 `D1_EVIDENCE.json` 中 6 个源文件的记录哈希由主检出的 CRLF 版本变为 LF 版本（内容相同）。
- **构建是否读这些行**（按构建提交 `126110ff` grep）：只读 `smr_*_proxy`、`co2_storage_potential_*`、`co2_injection_cap_*` 的数值，本步未改这些数值；其余被修改的行构建不读。验收门不读注册表。前后对比（`scripts/m080_registry_diff.py`）确认：4 处 `value` 改动全是原 DATA_PENDING 占位行（构建不读）。
- **测试**：27 个读注册表的测试文件，排除唯一在玩具网络上求解的用例（`test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers`）：基线与每个子步骤后均为 91 passed / 24 skipped（缺既有构建，按设计跳过）。工作树另复制了两个被忽略的 finance 输入（不提交）。**如实说明**：开始时曾启动 `tests/research` 全量运行，约 25 s 后停止；按字母顺序，`test_s3b_r4.py`（可能还有 `test_s4c_3.py`）中在几节点玩具网络上用 HiGHS 的求解用例很可能已执行——不涉及研究网络、Gurobi 或云端。此后只跑上述子集。

## 2. 补登清单（新增 90 行、修改 32 行）

### 2.1 新增行

| 类别 | param_id | 行数 | 状态 | 等级 |
|---|---|---|---|---|
| 地面光伏分国上限 | `renewable_cap_built_solar_<CC>` | 11 | REGISTERED 11 | B |
| 屋顶光伏分国上限 | `renewable_cap_built_solar_rooftop_<CC>` | 11 | REGISTERED 11 | B |
| 陆上风分国上限 | `renewable_cap_built_onwind_<CC>` | 11 | REGISTERED 11 | B |
| 海上风 AC 分国上限 | `renewable_cap_built_offwind_ac_<CC>` | 11 | REGISTERED 10、SOURCE_ZERO 1（LA） | B |
| 海上风 DC 分国上限 | `renewable_cap_built_offwind_dc_<CC>` | 11 | REGISTERED 9、SOURCE_ZERO 2（LA、SG） | B |
| 土地类别（可用 LC100 代码） | `renewable_landcover_codes_built_{solar, onwind, offwind_ac, offwind_dc}` | 4 | REGISTERED | B |
| 装机密度 | `renewable_density_built_{solar, onwind, offwind_ac, offwind_dc}`（4.6 / 3 / 2 / 3 MW/km²） | 4 | REGISTERED | B |
| 数据文件 | `renewable_copernicus_lc100_file`、`renewable_gebco_file`、`renewable_eez_file` | 3 | REGISTERED | A |
| 廓线文件（构建实际读取） | `renewable_profile_file_calibrated_modern_{c1,c3}_3h` | 2 | REGISTERED | B |
| 屋顶光伏方法 | `renewable_rooftop_method_built` | 1 | REGISTERED | B |
| 海上风核实 | `renewable_offwind_profile_check_built` | 1 | REFERENCE_ONLY | B |
| Astar 形状 | `demand_astar_shape_source`、`demand_astar_shape_substitution`（C）、`demand_astar_shape_gegis_check`（REFERENCE_ONLY） | 3 | — | B / C |
| 地热新建 | `geothermal_new_investment_main`、`geothermal_new_FOM_main`、`geothermal_new_VOM_main`（±30 %） | 3 | REGISTERED | C |
| LNG 上限（决定 72） | `lng_import_cap_built_<CC>`、`lng_import_cap_rule_built`（C） | 12 | REGISTERED 8、SOURCE_ZERO 4（BN、LA、MM、TL） | B / C |
| GEM 版本核实 | `lng_gem_ggit_release_verified` | 1 | REFERENCE_ONLY | A |
| v0.13.2 使用情况 | `cost_v0132_usage_built` | 1 | REFERENCE_ONLY | B |

分国候选上限（GW，筛查网络 `p_nom_max` 合计，三个资源等级相加；VERIFIED）：

| 国家 | 地面光伏 | 屋顶光伏 | 陆上风 | 海上风 AC | 海上风 DC |
|---|---|---|---|---|---|
| BN | 1.4 | 1.5 | 10.5 | 7.3 | 2.2 |
| ID | 859.0 | 356.1 | 3,950.4 | 899.0 | 1,886.7 |
| KH | 359.4 | 16.8 | 319.9 | 16.9 | 30.5 |
| LA | 119.3 | 6.6 | 529.4 | 0 | 0 |
| MM | 825.6 | 28.3 | 1,621.2 | 133.5 | 133.8 |
| MY | 77.9 | 83.1 | 742.1 | 185.2 | 189.1 |
| PH | 298.9 | 74.1 | 549.8 | 172.2 | 107.4 |
| SG | 0.4 | 5.3 | 0.04 | 1.3 | 0 |
| TH | 1,108.5 | 165.9 | 579.8 | 134.8 | 189.7 |
| TL | 9.6 | 0.6 | 36.8 | 1.0 | 0.9 |
| VN | 411.3 | 122.3 | 576.7 | 121.7 | 513.9 |

- 来源链：筛查网络 ← 电力底座 `electric_base_2050_unsolved.nc`（`6772c674…`）← 作者论文网络。土地规则取自作者论文网络元数据（与 `pypsa-asean/config.default.yaml` 一致）：光伏可用类 20/30/40/50/60/90/100（林地 111–126、水体 80/200 排除）、陆上风含林地类且距城镇类 50 1 km、海上 80/200 + 水深 ≤ 50 m（GEBCO 2025）+ 离岸 30 km 分 AC / DC；全部技术排除 natura；`potential: simple`。Copernicus LC100 v3.0.1（2019 nrt）、GEBCO 2025、EEZ v11 经 PyPSA-Earth 数据包 `bundle_data_earth` 交付；登记的 SHA256 为本地作者链副本，作者本人副本未留哈希。各技术合计与 S4A 报告一致（陆上风 8,916.8、海上 AC 1,672.9、DC 3,054.3、光伏 4,071.4 GW；屋顶光伏 860.4 GW）。
- 屋顶光伏：作者代码有方法记录——`prepare_sector_network.py`（`use_building_size: true`）p_nom_max = 0.1 kW/m² × 屋顶可用面积（Microsoft Global ML Building Footprints × 按建筑面积分档的安装比例 0–0.66，`cluster_global_buildings.py`，Obane / IEEJ 方法）。MEET-D v1 写的"PyPSA-Earth 无屋顶潜力方法"有误。建筑输入不在本机，未复算。

### 2.2 修改行（整行替换；原片段不动）

| param_id | 改动 | 原因 |
|---|---|---|
| `lng_import_cap_{BN … VN}`（11） | 描述加注 | 只是决定 72 规则中"有存量节点 2.5 × 存量"的部分；网络值见 `lng_import_cap_built_*` |
| `protected_areas_local_natura` | REFERENCE_ONLY → REGISTERED；补来源与 SHA256 | 实际在用（作者 meta `natura: true`，`build_natura_raster: false` → 数据包文件）；Harvard Dataverse doi:10.7910/DVN/XIV9BL V1.3 `wdpa_reclass.tif`（3,356,668 B，MD5 `8e49e824…` = 本地 `natura.tiff`），Sosa Arango 2020，CC0 |
| `cost_layer_A_technology_data_v0_13_2_2050` | REGISTERED → REFERENCE_ONLY | 历史：已被 v0.15.0 层替代（决定 50）；配置中仍可作敏感性层 |
| `smr_lifetime_proxy`、`smr_efficiency_proxy` | 描述加注 | 构建读取（`s2_costs.py:88`），值与 v0.15.0 核电相同（40 a、0.326） |
| `geothermal_existing_FOM`、`geothermal_existing_CO2_intensity` | REGISTERED → REFERENCE_ONLY | 网络未用：存量地热 FOM 按 AEO8 行（0.4756 %/a），地热 CO₂ 未计（carrier co2_emissions = 0） |
| `geothermal_existing_{VOM, efficiency, investment}` | DATA_PENDING → REFERENCE_ONLY（值 `not_in_v0_13_2`） | 不再待补：网络用 AEO8 VOM、效率 1.0、存量无投资 |
| `geothermal_existing_lifetime` | 描述加注 | 经 S1 存续规则使用；与 v0.15.0 同值 |
| `co2_storage_potential_KH / _TL`、`co2_storage_component_KH_undiscovered_saline_text_about_85_mt`、`co2_storage_component_TL_ogci_aggregated` | A → C（数值不变） | OGCI CSRC Cycle 5 未能复核；分项行沿用国家行在 D1 登记的区间（0–0.132、0–0.25 Gt） |
| `renewable_ship_density_raster` | DATA_PENDING → REFERENCE_ONLY | 文件已在 raw12（SHA256 一致）；主算未用航道排除 |
| `renewable_profile_variant`、`renewable_resource_classes` | REGISTERED → REFERENCE_ONLY | 历史：已被 S4B-3 行替代（calibrated_modern、3 级） |
| `renewable_profile_file_{fork, pypsa_eur}_{c1, c3}_3h`（4） | REGISTERED → REFERENCE_ONLY | 对照文件：构建只读 calibrated_modern 文件 |

- 状态变化合计：DATA_PENDING → REFERENCE_ONLY 4、REFERENCE_ONLY → REGISTERED 1、REGISTERED → REFERENCE_ONLY 9；等级 A → C 4。DATA_PENDING 51 → 47。逐行明细：`evidence/M080_REGISTRY_DIFF.csv`。

## 3. 海上风电核实结论（第 2 项）

- **VERIFIED**：筛查网络读取 `profiles_calibrated_modern_c1/c3_3h.nc`（网络元数据 `research_renewable.files`）。两文件的 `offwind_ac`、`offwind_dc` 数组与 pypsa_eur 重建逐值相同（最大差 0），与 fork（作者默认）不同（最大差 0.776）。构建提交 `126110ff` 的 `s4a_profiles.py` 中 pypsa_eur 海上风 = `NREL_ReferenceTurbine_2020ATB_5.5MW`（hub 120 m）、`correction_factor 0.8855`。配置 `profile_variant: calibrated_modern`（海上与光伏沿用 pypsa_eur）。
- **哪一方有误**：注册表正确；S4R 的 `S4R_PLAN.md` §3.1、`UNIFICATION_CHECKLIST`"潜力：海上风"与 `REGISTRY_ROWS_PROPOSED` 的 `renewable_offshore_rule` 把"NREL 5 MW、无尾流"写为现状有误——这是作者原始 / fork 廓线的设置。按指令 S4R 原件不改，已在 `REGISTRY_ROWS_PROPOSED_v2.csv` 中改写；S4R_PLAN 与 UNIFICATION_CHECKLIST 原件中的同一措辞仍在，供 M08 参考。海上 `p_nom_max` 取自作者布局，与机型无关。
- **对 M08-7 工作量的影响（INFERENCE）**：M08-7 清单中的 `turbine` 与 `correction_factor` 两项已在主算，可删去，也不需为机型重建廓线（重算新海上布局时直接沿用 `s4a_profiles.py` 已有的 pypsa_eur 设置）。仍需做的是会改变 `p_nom_max` 的面积重算：固定 ≤ 60 m、漂浮 60–1,000 m、`ship_threshold 400`、DC 密度 3 → 2 MW/km²。所需 GEBCO 2025、EEZ v11、航运密度栅格均已在本机，A1 下载项删除，海上部分不再有下载阻塞。工作量的主体（栅格重算与新廓线）不变。

## 4. v0.13.2 使用情况（第 3 项）

| 位置 | 是否数值上用到 v0.13.2 | 结论 |
|---|---|---|
| 新建候选成本（构建回执 `cost_layer.rows`） | 否：全部为 v0.15.0，SMR 与地热为 AEO8 D.15 | — |
| SMR 寿命 / 效率代理（注册表 → `s2_costs.py`） | 是（标注为 v0.13.2） | 值与 v0.15.0 核电相同，数值无影响；已加注 |
| 存量机组寿命（S1 存续规则；存量地热寿命来源文件为 v0.13.2 `costs_2050.csv`） | 是 | 抽查 CCGT / OCGT / 煤 / 油 / 褐煤 / 核 / 风光 / 水电 / 抽蓄 / 地热 / 生物质 / 电池，v0.13.2 与 v0.15.0 寿命全部相同 |
| 存量地热 FOM、CO₂ 强度（注册表 v0.13.2 行） | 否 | 网络用 AEO8 行；CO₂ 未计。行改为 REFERENCE_ONLY |
| **电力底座存量组件的成本与效率**（Assembly V1 `model_cost_layer.json`：1,780 行中 1,186 行为"technology-data v0.13.2 已折算 EUR2020"，作者成本表年份 2030） | **是** | 存量固定运维常数 108.1 亿 EUR/a（目标函数常数）；继承的存量 CCGT 效率 0.57，而新建与 S4A 补入的 GEM CCGT 为 v0.15.0 的 0.60（作者 2030 表为 0.58；0.57 的确切出处未追到）。**两版本混用的统一性问题**，列入报告、交 M08，本步未改模型 |

- 注册表中引用 v0.13.2 的共 181 行：168 行是 v0.15.0 成本行（描述里附"v0.13.2 = x"作对照），另有 `cost_layer_A`、6 行 `geothermal_existing_*`、3 行 `smr_*` 与 2 行版本对照（REFERENCE_ONLY）。

## 5. Astar 来源结论（第 3 项）

- **查到了（VERIFIED）**："Astar"是全国终端用电账户名：年总量 UNSD 2019 → AEO8（S4J-1 `table_sectors` 下年总量来自需求表，Astar 只给小时形状与节点分配）。形状 = 作者论文网络 100 个地理节点的基础 AC 负荷 `p_set`（`allocate_assembly_inputs.py`，PIN `06152be5`），由 PyPSA-Earth `build_demand_profiles.py`（作者代码 `5bacad70`）从 GEGIS 国别曲线按 GDP / 人口分到节点。
- **机构、文件与版本**：文件 `data/ssp2-2.6/2030/era5_2013/Asia.nc`（3,540,928 B，SHA256 `7813f914…`），变量 `Electricity demand` 的属性写明"Projected electricity demand using GlobalEnergyGIS"、SSP2、RCP 2.6、预测年 2030、ERA5 天气年 2013、MWh；经 PyPSA-Earth 数据包 `bundle_data_earth`（sandbox.zenodo.org record 323567）交付；作者 `load_options`：ssp2-2.6、weather_year 2013、prediction_year 2030，LA ← KH × 1,456.62、TL ← ID × 47.35。
- **核对**：作者网络各国基础负荷合计的 3 h 形状与 GEGIS 曲线（3 h 均值）相关：BN / ID / KH / MM / PH / SG = 1.0（比例系数变异 ~1e-16），MY 0.999998、TH 0.99999、VN 0.9999999995；LA 对 KH 0.9957、TL 对 ID 1.0。
- **未补填**：GEGIS 的开发者 / 出版物在本地文件中没有写明，按"不编造"未补；数据包存于 Zenodo sandbox（非永久存档）。

## 6. S4R 产出新版本与数据清单 v2（第 5、6 项）

- `REGISTRY_ROWS_PROPOSED_v2.csv`（42 行）：`industry_cement_2050_VN`、`renewable_capacity_per_sqkm_solar`、`renewable_landuse_rule_solar`、`lng_terminal_capacity_source`、`lng_terminal_cap_rule`、`biomass_overflow_rule`、`nuclear_cost_rule` 改为 add；`lng_terminal_cap_rule` 按列名对齐（v1 只有 10 个字段，缺 `source_locator`）；9 行写明被替代的 param_id（如 `renewable_capacity_per_sqkm_solar` ← `renewable_density_built_solar`，`lng_terminal_cap_rule` ← `lng_terminal_expansion_mode_s4b`、`lng_import_cap_rule_built`、`lng_import_cap_built_*` 等），并注明 M08 写入时把旧行标为历史；`renewable_offshore_rule` 描述改写。`industry_cement_2050_VN` 的旧值 581 Mt 只在需求输入表中，注册表无同名行，照实保留。
- `USER_DOWNLOAD_LIST_v2.md`：文首修订说明；删去 A1，航运密度改列"已有图层"；B4 注明本地已有 OGCI PDF 但汇总表为图片。
- 数据清单 v2（`work/p1_meet_20261020/DATA_INVENTORY_v2.xlsx / .md`）与附件 B 精简版（`DATA_INVENTORY_BRIEF.xlsx / .md`）：主算输入 1,263 行，A 10.85 % / B 61.28 % / C 27.87 %（v1：1,185 行，11.73 / 59.32 / 28.95 %）；11 国同口径占比不变（核查表 9 / 19，表 1 现行 18 / 25、修正后 17 / 25）。精简版不含不一致项与 param_id，664 个数据格全部能在 v2 详表中原文找到（`evidence/M080_BRIEF_TRACE.json`）。v1 输出与 v1 脚本未动。

## 7. 需要审阅端确认的事项

1. **屋顶光伏等级**：按指令条件（"方法无记录的定 C"），作者代码有方法记录，定为 B；但建筑足迹输入不在本机、无法复算。若改为 C，需给定敏感性区间（本步不自行设定）。
2. **KH / TL 分项行的敏感性区间**：改 C 后校验要求带区间，沿用国家合计行在 D1 登记的区间（KH 0–0.132、TL 0–0.25 Gt），未另设。
3. **`d1_registry.py` 的修改**：为保留原片段作历史，增加了"按 param_id 整行替换"的修正层（几行代码）；这是注册表拼装工具，不是构建或求解脚本。
4. **`s4c_0.csv` 强制入库**：原文件被忽略、从未提交；入库后干净检出才能重拼注册表。

## 8. 仍未解决的项

- 电力底座存量机组成本 / 效率来自作者 v0.13.2 表（§4）——统一性问题，交 M08；存量 CCGT 效率 0.57 的确切出处未追到。
- GEGIS 的开发者 / 出版物未在本地文件中写明；Zenodo sandbox 非永久存档。
- 作者本人使用的 Copernicus / GEBCO / EEZ 副本未留哈希，只能登记本地作者链副本的 SHA256（同一数据包 URL）。
- 屋顶光伏的建筑输入不在本机，未复算。
- KH / TL 的 OGCI 数值：本地 PDF（SHA256 `ff21cd34…6d0f`，与 D1 一致）的汇总表为图片，未能复核。
- 外部对照来源（ESMAP / Solargis、Zhong、GIIGNL、各国规划）与 S4R 拟增行仍无注册表记录（属对照或 M08 写入项）。
- worldsteel SSY 2020 页码差异未核。
- S4R 原件（`S4R_PLAN.md` §3.1、`UNIFICATION_CHECKLIST`、`LNG_CAPACITY_COMPARISON.md`）中"NREL 5 MW、无尾流"与"GEM 2025-08"的措辞仍在原件中，M08 引用时以本报告与 v2 副本为准。

## 9. 交付与提交

| 文件 | 说明 |
|---|---|
| `M080_REPORT.md` | 本报告 |
| `REGISTRY_ROWS_PROPOSED_v2.csv`、`USER_DOWNLOAD_LIST_v2.md` | S4R 产出新版本（SHA256 见 `evidence/M080_S4R_V2_CHANGES.json`） |
| `M080_PROGRESS.md` | 子步骤、提交 SHA 与续行点 |
| `scripts/` | `m080_extract.py`（只读提取）、`m080_registry_diff.py`（前后对比）、`m080_s4r_v2.py`、`m080_brief_trace.py` |
| `evidence/` | `M080_EXTRACT.json`、`M080_VRE_CAPS_BY_COUNTRY.csv`、`M080_LNG_CAPS_BY_NODE.csv`、`M080_EXISTING_FLEET_COST_BASIS.csv`、`M080_REGISTRY_CHANGES.json`、`M080_REGISTRY_DIFF.csv / .json`、`M080_S4R_V2_CHANGES.json`、`M080_BRIEF_TRACE.json` |
| `work/p1_meet_20261020/` | `DATA_INVENTORY_v2.xlsx / .md`、`DATA_INVENTORY_BRIEF.xlsx / .md`、`evidence/MEET_DATA_STATS_v2.json`、`scripts/meet_data_inventory_v2.py` |
| 仓库 | `scripts_project/m080_data.py`、`scripts_project/d1_registry.py`、`research_inputs/registry_v5/{DATA_REGISTRY.csv, D1_EVIDENCE.json, DATA_PENDING_LIST.csv, fragments/m080.csv, fragments/m080_corrections.csv, fragments/s4c_0.csv}`；镜像 `research/06_scope_redesign/p1_m080_20261020/`、`research/06_scope_redesign/p1_meet_20261020/` |

注册表：`cefab870` 1,962 行（`46e234d7…2e50`）→ `880955b8` 2,052 行（`6950a15d…8dd2`）。提交顺序：M1 `4e1de488` → M2 `995256ff` → M3 `880955b8` → M4 `dca14c83` → M5 `fc964ea2` → M6 `c98bf5d9` → M7 收尾（见进度文件）。
