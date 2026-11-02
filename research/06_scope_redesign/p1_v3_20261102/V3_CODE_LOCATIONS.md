# V3 代码定位（阶段 1.1）

- 基点：分支 `codex/v3-20261102`，起点 `0a20aefd`（`scripts_project/`、`research_inputs/`、`configs/` 与 HPC 包代码提交 `8ed41d97` 零差异，核对见 `V3_REPORT_PHASE1.md` 第 1 节）。
- 行号取自该基点。"执行清单"一列引用 `work/p1_dfx_20261026/CODE_MAP.md` 的分类：**建**＝生产管线/构建，**解**＝求解，**后**＝后处理，**批**＝批次与打包，**数**＝离线数据链，**否**＝不在实际执行清单中。
- 证据等级按项目约定：VERIFIED（读代码或网络数组）、INFERENCE（机制解释）。

## 1. 情景开关、跨境与存量识别、B6

| 内容 | 文件:行 | 函数 / 键 | 执行清单 | 说明 |
|---|---|---|---|---|
| 情景身份 | `configs/research/composition.json` | `identities.{integrated,disconnected}` | 建 | 每个情景＝基础文件 + `configs/research/baseline.yaml` + 情景文件；新增 `no_new_xb` 要在此登记身份 |
| 情景文件 | `configs/research/integrated.yaml`、`disconnected.yaml` | `research.cross_border.{electricity,H2,gas,co2}` | 建 | 只差四个开关（全真 / 全假）；`gate_b5_single_switch` 依赖这一点 |
| 配置总表 | `configs/research/baseline.yaml:219-228` | `research.cross_border`、`stock_mode` | 建 | `stock_mode: remove_all`（主）/`keep_stock_no_new`（敏感性，只能由变体脚本设置，构建拒绝） |
| 跨境打标 | `scripts_project/scenario_network.py:66` | `tag_cross_border` | 建 | 按 `buses.country` 判定；`country=ASEAN` 的母线不算跨境端口（第 71 行）；`MARITIME_TRADE_CARRIERS`（第 30 行）的链路标 `maritime_trade` |
| 跨境开关执行 | `scripts_project/s2_network.py:55`，调用在 `:385` | `apply_cross_border_switches_s2` | 建 | 开关关闭时 `mremove` 全部跨境线路 / 链路（含存量）；打开时校验 2025 下限并写存量 FOM 账 |
| 存量 FOM | `scenario_network.py:86`、`:133` | `existing_cross_border_fom`、`install_existing_cross_border_fom` | 建 / 解 | 只算电力走廊；目标函数加固定为 1 的常数列；**存量气管没有 FOM 项** |
| 存量气管 | `scripts_project/s3_layers.py:153-164` | `add_gas_network` | 建 | 读 `research_inputs/gas_v5/GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv`；容量为空的行（MY–SG）只记 `existing_pending`，不建链路 |
| 保留存量（v1 的 R9） | `scripts_project/m08a_layers.py:262` | `apply_stock_mode` | 建（变体） | 判定：AC `s_nom_min>0`、电力链路 `p_nom_min>0`、`gas_pipeline_kind=existing_2025`，连同 `-reversed` 孪生；`nom=min=max` 钉住但**保留扩建标志**；其余跨境组件删除；海运与东盟外选项不动 |
| 变体生成 | `scripts_project/m08a_variants.py:88`，默认值 `m08a_layers.py:151` | `derive` | 批 | R9 的 `out_scen="disconnected"`（第 107 行）——情景身份复用 disconnected，v3 要新身份 |
| 批次登记 | `scripts_project/m10_batch3_summary.py:43` | `RUNS["R9"]` | 批 | 只是第三批表；v3 另建运行表 |
| B5 闸门 | `scripts_project/v5/v5_gates.py:109` | `gate_b5_single_switch` | 解 | 要求配置差只在四开关内、不互联跨境组件数为 0；`no_new_xb` 不满足，需新判据 |
| B6 闸门 | `v5/v5_gates.py:126` | `gate_b6_cost` | 解 | `obj_int<=obj_dis*(1+1e-9)+1e-3`；差值＝`obj_dis-obj_int` |
| B6 调用 | `m10_batch3_summary.py:302`、`b4_batch4.py:307`、`dfx_batch.py:146`、`m08b_smoke_eval.py:67` | `b6` / `b6_gate` | 批 | 都直接传两个目标值 |
| 第 48 项扣除式 | **代码中不存在** | — | — | VERIFIED：第 48 项写的是"一体化总成本 − 存量跨境 FOM ≤ 不互联总成本"，但 `gate_b6_cost` 没有 FOM 参数，所有调用方都未扣减；注释只说明目标含 FOM 常数。v2 的 B6 = 14.6153 含这一差额（存量 FOM 899 万 EUR，v2 网络 `existing_cross_border_fom_eur`）。第 160 项后两情景都含 FOM，此差异自然消失 |
| 账本里的跨境 | `scripts_project/s4d_ledger.py:128-141` | `country_cost_ledger` | 后 | 存量 FOM 记到走廊实体；M10R 已修复变体删除零额行的问题（R9 缺陷） |
| Owen 受益 | `scripts_project/m12_allocation.py:732` | `benefit(int_dir, dis_dir, ...)` | 后 | `disconnected − integrated`；参数名写死为 disconnected，语义是"对照情景"，改名只影响标签 |
| 走廊拆分 | `m12_allocation.py:211` | `corridor_components` | 后 | 对照情景有跨境组件时同样适用（R9 已跑通，见 `m10s1` 记录） |
| 运行闸门入口 | `scripts_project/s2_solve.py:269-270` | `--scenario` 校验 | 解 | 网络 `meta.scenario` 必须等于参数；`:282` `config(a.repo, a.scenario)` 按情景取配置 → 新身份必须进 `composition.json` |
| 配置哈希 | `v5/gates_v6.py:33-48`、`v5/v5_gates.py:173` | `config_subset_sha256`、`gate_b12_hash` | 解 | 新键要进子集清单，且覆写键列表 `s2_network.py:52` 要同步 |

## 2. 液体母线、燃料舱账户、CO₂ 船运、东盟外进口

### 2.1 东盟液体统一母线（第 44 项）

| 内容 | 文件:行 | 函数 | 执行清单 | 说明 |
|---|---|---|---|---|
| 油池 | `s3_layers.py:247-273` | `add_imports`（`pool_bus`、`oil pool {node}`） | 建 | `ASEAN oil` + 每节点 `{node} oil` ↔ 池的零成本双向链路（`p_nom_extendable=True`、`p_min_pu=-1`） |
| 绿色载体池 | `s3_layers.py:277-284` | `add_imports` | 建 | `ASEAN ammonia`、`ASEAN methanol`、`ASEAN oil non-fossil` 各挂一台进口机组，`country=ASEAN` |
| 液氢进口 | `s3_layers.py:285-297` | `add_imports` | 建 | 在 LNG 接收站节点的 `{node} H2`，已是节点级，v3 不动 |
| 氨 / 甲醇转换 | `s3_layers.py:303-366` | `add_ammonia_methanol` | 建 | Haber-Bosch、裂解、甲醇合成、生物甲醇、甲醇 OCGT 的端口都接在 `ASEAN ammonia` / `ASEAN methanol`；区域储罐 `:327-328` |
| 非化石油池 | `s3_layers.py:406-416` | `add_fuel_carbon_mode` | 建 | `ASEAN oil non-fossil` + 每节点 `{node} oil non-fossil`；FT / BtL / electrobiofuels 输出到节点非化石母线（`:429-441`） |
| 需求侧端口 | `scripts_project/s2_layers.py:805-811`、`:894-904` | `add_demand_layer` | 建 | 船用甲醇、工业氨负荷、工业甲醇直接接 `ASEAN` 母线 |
| 跨境打标豁免 | `scenario_network.py:70-71` | `tag_cross_border` | 建 | `country=ASEAN` 视同非网络端口 |
| 进口单向闸门 | `v5/v5_gates.py:299-300`、`:302` | `gate_b13_imports_one_way`，`POOL_BUSES` | 解 | 母线名写死 |
| 进口价相同闸门 | `v5/v5_gates.py:364` | `gate_b16_import_prices_identical` | 解 | 比较两情景进口价 |
| 账本实体 | `s4d_ledger.py:30,38-42,84` | `POOL`、`bus_entities`、`_subject_settlement` | 后 | `country=ASEAN` 且非燃料舱母线 ＝ `ASEAN_POOL`；液体买卖按池对偶结算（`liquid_pool_*`） |
| Owen 代码 | `m12_allocation.py:200-208` | `entity_code` | 后 | `ASEAN_POOL` → `SHARED`（无主残差） |
| 右端审计 | `scripts_project/m12_rhs_audit.py:82-84,106` | 归属类别 | 后 | 池的无主组件为 SHARED；任何无主右端项须事先归属 |
| 移除一国变体 | `m08a_layers.py:179` | `apply_remove_countries` | 建（变体） | 只按 `buses.country` 删除；国家液体母线会随国家一起删掉（符合语义），燃料舱节点负荷需核对 |
| 全部引用 | 另有 `s3_2_imports_data.py`、`s3_3_ammonia_methanol_data.py`、`s3_5_fuel_carbon_data.py`、`s4b_0_data.py`、`s4b_layers.py`、`s4c_3_data.py`、`s4i_static_audit.py` | — | 数 / 否 | 数据脚本与静态审计里的字符串引用；静态审计复用时要改 |

### 2.2 燃料舱账户（第 88 项，修改第 10 项）

| 内容 | 文件:行 | 函数 | 执行清单 | 说明 |
|---|---|---|---|---|
| 配置 | `baseline.yaml:343-344` | `research.bunkers.attribution` | 建 | `asean_pool`（主）/ `bunkering_country` / `excluded` |
| 归属层 | `scripts_project/s4c_layers.py:496` | `apply_bunker_attribution` | 建 | 删除各国各节点的燃料舱负荷，合并成两条 ASEAN 负荷：`ASEAN aviation international oil demand`（239.55 TWh，化石表计 + 非化石孪生）、`ASEAN shipping international methanol`（485.59 TWh） |
| 账户 | `s4c_layers.py:516-518`、`:475`、`:582`、`:602` | `validate_bunker_account`、`install_bunker_net_zero`、`bunker_account_report` | 建 / 解 | `co2 bunkers ASEAN` 单独净零，钩子 `research_bunker_net_zero`，只允许排放端口 |
| 节点份额来源 | `s2_layers.py:120-123`、`:772`、`:796` | `ACCOUNT_FOR_SHARES` | 建 | 建网时已按 Assembly 的 `InternationalAviationBunker` / `InternationalShippingBunker` 节点份额落负荷，随后被 `apply_bunker_attribution` 合并 |
| 份额生成 | `results_project/assembly_v1/final_allocation/`（清单 `ports_sha256`、`airports_sha256`） | 方法 `SAME_COUNTRY_NEAREST_GEOGRAPHIC_NODE_{PORT,AIRPORT}_SIZE_WEIGHTS_FLAT_TIME` | 否（产物） | VERIFIED：v2 已有按港口 / 机场规模加权的节点份额，只是未在 `asean_pool` 下使用 |
| 账本 | `s4d_ledger.py:38-42` | `bus_entities` | 后 | `research_bunkers.asean_loads[*].bus` 与 `co2 bunkers ASEAN` → `ASEAN_BUNKER` |
| 第 12 参与者 | `m12_allocation.py:56-58,204-205` | `BUNKER`、`entity_code` | 后 | `ASEAN_BUNKER` → `BUNKER` |
| 单独成本 | `m12_allocation.py:281` | `bunker_standalone` | 后 | 只认挂在 `POOL`/`LB` 实体上的进口机组（`:305`）；国家母线后找不到路线，需改 |

### 2.3 CO₂ 船运（第 89、92、93、95、97、99 项）

| 内容 | 文件:行 | 函数 | 执行清单 | 说明 |
|---|---|---|---|---|
| 东盟外封存 | `s4c_layers.py:631` | `apply_extra_asean_storage` | 建 | 每国一个 `co2 sequestered extra-ASEAN <c>`，沿海节点各一条链路；老挝 `{node} co2 transit export extra-ASEAN` 带铁路段边际成本 |
| 东盟内船运 | `scripts_project/s4d_layers.py:149` | `apply_intra_asean_shipping` | 建 | **节点级**：71 个沿海缓冲节点 × 接收国，`{node} co2 ship to <j>`，共 434 条（`CO2 ship`），单价 = `co2_ship_chain_fixed_cost + co2_ship_chain_per_km_cost × km`；距离取海路 `sea_km` |
| 老挝过境 | `scripts_project/s4e_layers.py:147` | `apply_lao_transit_shipping` | 建 | `CO2 transit ship` 36 条，陆段 + 船段 |
| 老挝铁路入越 / 泰 | `s4f_layers.py` `apply_lao_vn_store`、`s4g_layers.py` `apply_lao_th_store` | — | 建 | `CO2 transit rail` 6 条 |
| 海路距离 | `scripts_project/s4d_2_ship_routes.py` | 0.05° 网格最短水路 | 数 | 可复用到港口节点对；现有表 `CO2_SHIP_ROUTES_S4D2.csv` 504 行，只含"沿海节点 → 接收国"，SG、LA 不是接收国 |
| 账本 | `s4d_ledger.py:70-71,88-89,125` | `owners`、`_subject_settlement` | 后 | `maritime_trade` 归出口国；运费 `co2_ship_freight`；封存服务按 `co2 sequestered <j>` 对偶结算 |

结论（VERIFIED）：**CO₂ 从来没有东盟统一母线**，第 92 项的结构已是节点到接收国国家封存、按海路距离计价。

### 2.4 东盟外进口（第 17、18 项）

`s3_layers.py:230` `add_imports`；价格表 `research_inputs/imports_v5/IMPORT_PRICES_2050.csv`（`s3_2_imports_data.py` 生成，已含 20 % 加价）；油价取 WEO（`s2_costs.fuel_price`）。v2 网络值：油 35.32、甲醇 145.16、氨 116.78、FT 150.11 EUR2020/MWh，均 `p_nom_extendable=True`、无上限。LNG 按接收站节点（`s3_layers.py:173`），液氢按 LNG 节点。

## 3. 工业子部门与节点分配

| 内容 | 文件:行 | 函数 / 表 | 执行清单 | 说明 |
|---|---|---|---|---|
| 国家 × 部门锚 | `scripts_project/m08b_demand.py:228`，`RATIO_TABLE`、`ANCHOR_TABLE`（`:50-51`） | `main`、`ras_split`（`:132`） | 数 | 写 `DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv`；工业行只有 `IndustryFinalEnergy` 与 `UNSD_electricity_Industry` 两个账户，共 4,500 TWh，**不含子部门** |
| 2019 子部门基数 | `research_inputs/assembly_v1/sources/industry_cache.json`（`s3_0_industry.py:35`） | UNSD 2019 子部门 × 载体 | 数 | 来自 `pypsa-asean/resources/.../base_industry_totals_2030.csv`，只作份额 |
| 子部门映射 | `scripts_project/s3_0_industry.py:67-76` | `MAPPING`、`OTHER_BUCKET` | 数 | "其他"桶＝`other`、`construction`、`mining and quarrying` 三个 UNSD 行 |
| 钢铁、水泥实物 | `s3_0_industry.py:182-231` | `main` | 数 | 2019 能耗从 UNSD 行或"其他"扣；2050 = 物理产出规则 × PyPSA-Eur 比例 |
| 其余子部门 | `s3_0_industry.py:232-247` | 能量回退 | 数 | 2019 能量 × 乘数 × 效率因子 × 2050 载体份额 |
| 氨 | `s3_0_industry.py:294-303` | DFX F2 | 数 | USGS 2019 产量 × 增长规则 |
| "其他"桶转有用热 | `s3_0_industry.py:309-325` | M08b B2 | 数 | 燃料按 JRC-IDEES OIS 份额转四个温度带，×0.90；电保留；机械用油保留 |
| 输出表 | `s3_0_industry.py:390-400` | `INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv` | 数 | 国家 × 载体（`pe_*`），**不分子部门、不分节点** |
| 物理产出 | `m08b_demand.py:156,195` | `output_bases`、`physical_output` | 数 | 水泥、钢、氨；新增镍等要进这里或新脚本 |
| 节点份额 | `s2_layers.py:579,603` | `allocation_node_shares`、`_shares_for` | 建 | `(country, account) → {node: share}`；工业、非能源、过程排放全部用 `IndustryFinalEnergy` 份额（`:120-123`），其来源是用电基荷份额（清单方法 `AUTHOR_BASE_LOAD_ANNUAL_NODE_SHARES_FLAT_TIME`） |
| 落负荷 | `s2_layers.py:818-913` | `add_demand_layer` | 建 | `sh` 一个国家一套份额，对所有载体相乘（`:863`）；**一张份额表乘全部工业载体**，所以按子部门分节点必须改成"子部门 × 载体 × 节点" |
| 过程排放 | `s2_layers.py:992-1009` | `add_demand_layer` | 建 | 也用 `IndustryFinalEnergy` 份额；设施法不改它就会与水泥、钢铁脱节 |
| 非能源 | `s2_layers.py:963-991` | `add_demand_layer` | 建 | 同样用该份额 |
| 重复实现 | `s2b_industry.py`（已退役）、`d1_demand_2050.py`（比例法） | — | 否 / 上游 | 不改；`d1_registry.py` 仍取哈希，不能删 |

总量口径（VERIFIED）：AEO8 锚表工业 4,500 TWh；经路线折算后实际绑定负荷 3,820 TWh（即指令所称 3,820）。两者之差是 2050 路线效率与有用热 0.90 系数，不是缺失。

## 4. 交通、BEV、时间

| 内容 | 文件:行 | 说明 |
|---|---|---|
| 陆运负荷 | `s2_layers.py:748-763` | `{node} land transport EV` 接 `{node} EV battery`（载体 `Li ion`），`p_set = 年量/8760`：**平负荷**，不在 `loads_t` 中（96 条，共 715.96 TWh） |
| 充电桩 | `s2_layers.py:756-758` | `{node} BEV charger`，效率 0.9，`p_max_pu = share_bev_avail_mean = 0.8` **常数**，`p_nom_extendable=True`，资本成本 0 |
| 智能充电 / V2G | `baseline.yaml:396` `bev_dsm: false`（注："no ASEAN fleet data (number of cars)"） | VERIFIED：v2 网络 EV Store 0 个、V2G 链路 0 条，电池母线只是过路母线 |
| 注册表 | `research_inputs/registry_v5/DATA_REGISTRY.csv` `share_bev_*` | PyPSA-Eur 默认值全部已登记（`bev_dsm true`、`availability 0.5`、`bev_energy 0.05`、`charge_rate 0.011`、`restriction 0.8 @ 7h`、`v2g true`），但只用了效率与平均可用率 |
| 上游实现 | `scripts/prepare_sector_network.py:2298` | `add_land_transport`：需要 `number cars`，v2 未调用 |
| 快照 | `s2_network.py:110`、`daily_resolution.py:21` | 2013-01-01 至 2013-12-31 21:00，3 h，无时区标记 |
| 时区 | v2 网络核实 | VERIFIED：各国太阳能平均峰值落在快照 03–06 时（经度 95–126°E 对应 UTC）；基荷峰在 09–12 时（当地 16–20 时）→ 快照为 **UTC**；天气年 **2013** |
| 日分辨率 | `daily_resolution.py:21` | `to_daily` 把时序按日平均：**日内形状在 365×24h 网络里被抹掉**，星期与季节形状保留；56 时段截短取 2920×3h 前 56 个时段（1 月第 1 周） |
| Astar 形状 | `scenario_network.py:154` | `bind_astar`，已是 UTC 时序，v3 不动 |

## 5. 账本与 Owen 中的液体与燃料舱（v3 需改动的点）

| 模块 | 现状 | v3 影响 |
|---|---|---|
| `s4d_ledger.bus_entities` | ASEAN 母线 → POOL / BUNKER | 国家液体母线 `country=<c>` 自动成为国家实体；POOL 无行（`pool=0`，保留常量）；燃料舱最终母线继续 `country=ASEAN`，靠 `research_bunkers` 表识别 |
| `s4d_ledger.owners` | 跨两国的链路要求 `border_class=cross_border`，否则报错（`:73-74`） | 液体船运必须进 `MARITIME_TRADE_CARRIERS`，否则 `nat` 含两国直接报错；老挝过境同样 |
| `s4d_ledger._subject_settlement` | 只有 pool / bunker / co2 / XB 四类 | 需新增液体贸易主题，否则落入 `other_settlement`（恒等式不受影响，报告不清） |
| `s4d_ledger.country_cost_ledger` | `DIRECT` 列表（`:211`）与 `co2_*_freight` 映射（`:125`） | 新运费主题要同时进 `m12_allocation.DIRECT`（`:194`），否则 `direct_costs_minus_objective` 对不上 |
| `m12_allocation.bunker_standalone` | 进口机组必须在 POOL / BUNKER 实体 | 改为沿"进口 → 国家母线 → 节点 → 燃料舱"找路线 |
| `m12_rhs_audit` | 按名称后缀归属行 | 国家液体母线行属于该国；船运链路端口跨两国，属于耦合行，须确认归类；运行前用截短网络验证 `premise` 通过 |
| `s4o_c1_precision` | `ENTITIES` 含 `ASEAN`（`:47`） | 取 `ASEAN_*` 求和，燃料舱仍在其中，无须改 |
| `v5_gates` | `POOL_BUSES`、B5 | 改名与新判据 |
