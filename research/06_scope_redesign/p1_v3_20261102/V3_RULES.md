# V3 规则（事先登记）

- 依据：决策清单第 159–169 项；`V3_DESIGN.md`；审阅决定 `V3_REVIEW_DECISIONS_PHASE1.md`（SHA256 `5bc090fe0bcc9808dd973b10ab47209b135b0134ffae9dd10cc355a7ea99de9b`）。
- 本文件提交后才构建 v3 网络；网络 SHA256 与方向性预测写入 `RUN_PLAN_V3.md` 提交后才求解。看到求解结果后不得修改规则、阈值或预测。
- 参数全部进注册表片段 `research_inputs/registry_v5/fragments/v3.csv`（37 行）；注册表 v3 SHA256 `ef1d6cdd872485b54e04df8f598c829665cc4803fe7332699d4dd83911455295`，2,317 行。

## 1. 不变项

AEO8 国家 × 部门总量与 v2 需求修复、成本表、求解档案 A、GATES_V6 / C1 验收阈值、2920×3h 正式分辨率、Owen 对偶价格分摊方法、第 35、89、93、96 项。

## 2. 第 160 项：`no_new_xb`

- 情景身份 `no_new_xb`（`configs/research/no_new_xb.yaml`），由已构建的一体化网络派生（`m08a_variants.py`，新模式 `no_new_xb`）。
- 存量认定：AC `s_nom_min > 0`（16 条 2,570 MW）、电力链路 `p_nom_min > 0`（1 条 300 MW）、`gas_pipeline_kind = existing_2025`（6 条 33,883.7 MW），连同 `-reversed` 孪生。钉住容量，`*_nom_extendable=False`。其余跨境线路、链路全部删除。
- MY–SG 气管无容量无管径：主算不建（D160-1 a）。
- 海运（CO₂ 船、液体船、老挝过境）属 `maritime_trade`，三情景相同。
- `B6 = Z(no_new_xb) − Z(integrated)`，两者都含存量 FOM。第 48 项扣除式废止（它从未进入代码）。
- 完全隔离：`s2_network.py --scenario disconnected` 保留，不进运行计划。
- 存量核查 `V3_XB_STOCK_CHECK.md` 只报告，网络不改；LA–TH 专线登记 `xb_stock_la_th_dedicated_lines = DATA_PENDING`。

### 2.1 X1：跨境输电存量来源（2026-11-02 用户决定，B 级）

审阅决定 X1 原要求以 S8 为唯一来源，但 S8 无逐行状态、口径无法确认（`V3_X1_STOP_NOTE.md`）。用户改定：**主算以 APG existing 为唯一来源**，只计运营中，在建不计。

- 来源：ACE APG 表，`research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv` 的 `apg_existing_mw` 列（Table 1，2024 年口径，第 94 项 S4E-1 已用）。
- 结果：现网已与该列逐对一致，**不换值，四个 E2 网络不重建**，SHA256 不变。
- 两情景相同：一体化作 `s_nom_min` / `p_nom_min`，`no_new_xb` 作不可扩建的固定容量。

| 国家对 | 旧值 = 新值（MW） | 可用容量（MW） |
|---|---:|---:|
| LA–TH（9 条） | 955 | 668.5 |
| MY–SG | 525 | 367.5 |
| MY–TH（AC 80 + DC 300） | 380 | 356 |
| KH–LA | 300 | 210 |
| KH–TH | 250 | 175 |
| ID–MY（砂拉越–西加里曼丹） | 230 | 161 |
| KH–VN | 200 | 140 |
| LA–MM | 30 | 21 |
| **合计** | **2,870** | |

- 可用容量 = 线路 `s_nom` × `s_max_pu` 0.7 + 链路额定容量。`-reversed` 孪生链路是同一资产，只计一次。
- 其余国家对（TH–MM、LA–VN、ID–SG、PH–MY、BN–MY、ID–MY 半岛–苏门答腊）APG 无 existing，存量为 0。
- 检验：`v3_static.py` 的 `stock_check` 逐对核对 APG existing = 一体化下界 = `no_new_xb` 固定容量，且 `no_new_xb` 跨境全部不可扩建；结果 `evidence/X1_STOCK_TABLE_V3.csv`，已并入 `all_structural_passed`。

### 2.2 待办 X1b：老挝对泰国电站专线（只登记，本补充不实施）

用户 2026-11-02 决定，**筛查前必须完成**：

- 以 EPPO「Power purchased from Lao PDR」清单为唯一来源（9 个项目，合同容量合计 5,427 MW，各项 COD 均在 2019 年及以前），作为 LA–TH 存量加入。
- 实施前逐项核对这些电站在网络中是否为在运的 LA 机组及所在节点，结果写入下一份报告。
- 影响：X1b 会改变网络，所有网络 SHA256、运行器登记值都要重做。本补充的冒烟和干跑都是 X1b 之前的结果。

### 2.3 X1b 规则（第 172、173 项，B 级；补充 02 实施）

**来源：** LA–TH 为 EPPO「Power purchased from Laos PDR」（页面日期 2016-03-29，存档快照 2026-06-11，SHA256 `680ed575…`），9 个项目、合同容量 5,427 MW；LA–VN 为 GEM 的 Xekaman 1、3，合计 572 MW（第 100 项已引用）。表 `research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv`，脚本 `scripts_project/v3_dedicated_lines.py`。

**只计运营中：** 逐项核对 GEM GIPT 2026-09 的状态和网络的存量机组（`existing_unit_components`）。11 项全部 `operating`、全部在网络中，全部计入。EPPO 表是 2016 年状态，当时未投运的 Hongsa、Xayaburi、Xe Pian-Xe Namnoy、Nam Ngiep 1 在 GEM 中已投运（2015–2019）。

**与 APG 不重复：** ACE 2024 项目档案第 9 章（第 21–23 页）列出的现有线路是七条 115 kV、协议类型 Energy Exchange 的线路，容量合计正好 955 MW（`research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv`）。同章另述"约 5,934.9 MW 发电并网（generation-to-grid）互联"，与这 955 MW 分列。所以 APG 的 955 MW 不含电站专线，不用扣除。

**建模：**

- 按"电站所在 LA 节点 + 着陆节点"合并（审阅决定允许），得 6 条专线，每条一对 forward / `-reversed` Link，双向，不可扩建，`p_nom` = 合同容量之和。
- 着陆节点取距电站节点最近的 TH（或 VN）节点，长度 = 大圆距离 × 1.25（与模型线路同口径）。
- 效率 = 1 − λ × 长度，λ 按第 108 项线损代理的 380 kV 4-bundle 线型、α 0.5 计算，每 km 1.2348e-4。
- `border_class=cross_border`，`transport_carrier=electricity`，`stock=dedicated_plant_line`，`p_nom_min = p_nom`。`apply_stock_mode` 因此把它们当存量保留。
- 一体化、`no_new_xb` 及完全隔离之外的所有情景相同。完全隔离网络不加。
- 存量 FOM 规则照常适用：HVAC overhead 的 FOM% × 投资 × 长度 × 容量，6 条合计 15.87 M EUR/a，两情景相同，不影响 B6，计入完全隔离 − `no_new_xb`。

| 专线 | 项目 | MW | km | 效率 |
|---|---|---:|---:|---:|
| LA2 1 – TH2 4 | Xayaburi | 1,220 | 400.5 | 0.9506 |
| LA2 2 – TH2 1 | Nam Ngum 2、Nam Ngiep 1 | 866 | 351.9 | 0.9565 |
| LA2 3 – TH2 1 | Theun-Hinboun、扩建、Nam Theun 2 | 1,388 | 278.7 | 0.9656 |
| LA2 4 – TH2 1 | Houayho、Xe Pian-Xe Namnoy | 480 | 373.9 | 0.9538 |
| LA2 5 – TH2 4 | Hongsa | 1,473 | 444.0 | 0.9452 |
| LA2 4 – VN2 2 | Xekaman 1、3 | 572 | 230.9 | 0.9715 |

**简化（写入局限）：** 专线不绑定电站，可双向，也可供节点上其他机组使用；合同容量低于或等于电站容量；着陆节点按最近节点取，不是实际落点（如 Xayaburi 实际走向 TH 东北部）；线损用代理线型，不是实际 230 / 500 kV 线路；专线损耗全部计在受端，线路代理是两端各半。

**对照（不是来源）：** ACE 的 5,934.9 MW 比 EPPO 的 5,427 MW 高 507.9 MW，审阅决定以 EPPO 为唯一来源，这一差额未计入。

## 3. 第 161 项：国家液体母线与船运

### 3.1 母线

每国 `{c} oil`、`{c} oil non-fossil`、`{c} methanol`、`{c} ammonia`，`country=c`，`location` = 枢纽节点（`LIQUID_HUB_NODES_V3.csv`）：BN4 0、ID_Java-Bali1 0、KH2 0、LA2 2、MM2 1、MY_Peninsular2 1、PH_Luzon5 0、SG2 0、TH2 3、TL11 0、VN2 5。

- 节点 oil、oil non-fossil 与国家母线之间沿用零成本双向链路（`oil pool`）。
- 甲醇合成、生物甲醇、Haber-Bosch 输出直连本国母线；FT、BtL、electrobiofuels 输出到节点非化石母线（D161-6 a）。

**有意偏离第 161 项之一（D161-4 a）：** 国内配送加价取 0。第 161 项写"先用统一加价代理"；外生消费下统一加价只增加常数，不改变国家间比较，所以不加。

**有意偏离第 161 项之二（D161-7 a）：** 液态 CO₂ 不设国家母线，保持第 92、93 项结构。CO₂ 从未有东盟统一母线，第 161 项的实质（按距离、两情景都有）已满足，且 71 个沿海节点比国家母线更细。单价继续用 IEAGHG 2004。

### 3.2 进口

油、甲醇、氨、FT 在 10 个沿海国各设一台，价格同 v2 世界价（第 17 项），容量内生无上限（D161-5 a）。LA 无进口，经过境链路。

### 3.3 船运

- 载体：非化石油、甲醇、氨；10 个沿海国两两有向，270 条；化石油不建（各国进口同价）。
- 单价 `c(d) = c_km × d`（S-B，主算），`η(d) = 1 − 4e-6 × d`（d 为 km）。

| 载体 | `c_km` EUR2020/(MWh·km) | 来源 |
|---|---|---|
| 甲醇 | `liquid_ship_ckm_td_methanol` | technology-data `MeOH transport ship`（B 级） |
| 非化石油 | `liquid_ship_ckm_td_oil` | technology-data `FT fuel transport ship`（B 级） |
| 氨 | `liquid_ship_ckm_td_ammonia` | technology-data `NH3 (l) transport ship`（B 级） |

- 年金 7 %；航速 15 节、年运营 8,000 h 为 C 级假设。原文献未能取得：Runge et al. 2020（SSRN 人机验证）、Cihlar et al. 2020（欧盟出版局 WAF 拦截），按 D161-2 用回退值。
- 货损 η：IRENA 2022 p.44，回程约 1 % / 5,000 km，按往返 ×2（C 级）。
- `research.liquids.ship_cost_scale` ±50 %；`ship_cost_basis = ieaghg` 是 S-A 上界敏感性（固定项 + 单程 km 项，η=1）。
- 距离：`LIQUID_SHIP_ROUTES_V3.csv`，0.05° 网格最短水路（D161-3 a）。
- 容量：`p_nom_extendable=False`，`p_nom = 该载体东盟年需求 ÷ 8,760 × 10`（D161-10 a）。**冒烟与筛查报告列出所有船运链路的容量对偶，非零即报告。**
- `border_class = maritime_trade`，归出口国，货到按进口国母线对偶结算。三情景相同。

### 3.4 老挝过境

`LA <carrier>` ↔ `VN <carrier>` 一对有向链路（化石油只入），单价 `(co2_land_transport_rail_unit_cost × 411.7 km + co2_land_transport_rail_loading_cost) / 热值`，`trade_class = transit`（D161-9 a，第 93 项类比）。里程取枢纽 `LA2 2` 到 `VN2 3`。

### 3.5 储罐

每国 `{c} methanol store`、`{c} ammonia store`、`{c} oil non-fossil store`，成本行不变（后者用 `General liquid hydrocarbon storage (product)`）。非化石油储罐是新增组件（D161-8 a）。

## 4. 第 162 项：燃料舱

- 模式 `research.bunkers.attribution = asean_account_nodal`。国家总量不变；节点份额用 Assembly 港口、机场规模权重（航空 82 个节点、船用 48 个节点）（D162-1 a、D162-2 a）。
- 航空：节点表计与非化石孪生保留，最终母线标 `ASEAN`，化石表计的大气端口改接 `co2 bunkers ASEAN`。
- 船用：`{node} bunker shipping methanol final` 母线 + `{c} methanol` → 该母线链路，无碳端口。
- 账户单独净零（`research_bunker_net_zero` 不变）。第 12 参与者按终端母线对偶买入。
- `bunkering_country` 敏感性保留。
- 推论（INFERENCE）：一国内节点分配不影响 LP 最优值。

## 5. 第 163 项：工业子部门

### 5.1 守恒

`Other_v3(c) = T_v2(c) − Σ_s E_s(c)`（D163-6 a）。`T_v2` 是网络绑定的 `INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv` 之和（3,820.054 TWh）。锚表 4,500 TWh 不动。`DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv` 比绑定表高 1.55 MWh（SG）、0.02 MWh（BN），来自其细分拆分，测试以绑定表为基准。

### 5.2 路线（D163-1）

| 国家 | 路线 |
|---|---|
| VN | APEC 2022 份额替换 UNSD 份额（C 级；数据年 2022 对基年 2019，**年份不一致**）。在隔离副本中重跑 `s3_0_industry.py`，其余国家结果与 v2 一致 |
| ID | **只对有色金属（镍、铝、氧化铝、铜）自下而上**；化工、造纸、食品维持 UNSD |
| MY | 铝自下而上 |
| 其余 | 维持 |

**数据限制（待审阅端知悉）：** D163-1 的 MY 石化（GIS）算不出能量。GIS 只有炼厂产能，没有石化产量，炼油能耗也不在工业终端。按"余量留在其他"，MY 石化能量留在其他，GIS 炼厂只用于节点分配。

### 5.3 镍（D163-2、D163-5）

Wei et al. 2020 表 8 Case 3-FeNi（RKEF，35 % Ni），换算成终端能源：

| 项 | 值 |
|---|---|
| 电 | (7,237 + 1,081) kWh/t 合金 ÷ 0.35 = **23.77 MWh/t Ni** |
| 燃料 | 天然气 616 kg × 50 MJ/kg + 无烟煤 569 kg × 29 MJ/kg = 47.3 GJ/t 合金 ÷ 0.35 = **37.54 MWh/t Ni** |
| 2050 载体 | 电保留；燃料（含还原剂）× 0.90 走 `industry heat high`，**33.79 MWh/t Ni** |

- 采矿能耗不计入（留在 `mining`）。
- 含镍量：USGS 2019 年 NPI 38.0 万 t + 镍铁 2.57 万 t + 镍锍 7.10 万 t。
- 上界敏感性 26 MWh/t NPI（`NIUPPER` 表）。
- 单列为有色金属。

### 5.4 其余有色金属

原铝、氧化铝、铜用 PyPSA-Eur 2050 比例表（`Aluminium - primary production`、`Alumina production`、`Other non-ferrous metals`）。MY 铝取亚太卷 2018 年 750 kt（估计）。

### 5.5 产量与增长

基年 2019（D163-3 a），增长 `G^((2050−基年)/28 × 0.5)`，与 v2 氨规则相同（脚本已断言）；2023 作敏感性（`NF2023` 表）。超量处理 D163-4 a，本次未触发。

### 5.6 结果

| 国家 | 总量 TWh | 新增显式 TWh | 其他占比 v2 → v3 |
|---|---:|---:|---|
| ID | 1,793.7 | 68.8 | 84.6 % → 80.8 % |
| VN | 888.0 | — | 74.7 % → 18.3 % |
| MY | 313.9 | 19.8 | 76.3 % → 70.0 % |
| 其余 | 不变 | — | 不变 |

## 6. 第 164 项：节点分配

| 子部门 | 来源 | 权重 |
|---|---|---|
| 钢铁 | GEM 运营厂 | 粗钢产能 |
| 水泥 | GEM 运营厂 | 熟料产能，缺失时水泥产能 × 0.656；纯粉磨国家（BN）用水泥产能 |
| 镍、铝、氧化铝、铜 | USGS 卷表 2（ID 省级人工编码）；MY 铝 GIS | 含镍当量或产能 |
| 炼油石化 | GIS（MY、VN、PH、MM、BN，只取运营）；USGS 卷表 2（ID 等权、TH 产能） | 产能 |
| 其余与"其他" | DOSE 制造业产出 | ID、MY、PH 2019；TH、VN 2018（D164-3 a） |
| KH、LA、MM、BN、SG、TL 的分散行业 | v2 规则 | 用电份额 |

- 点入 `regions_onshore.geojson`，落外面取同国最近节点（D164-1 a）。
- **省内按节点用电份额分摊（D164-4 b）：** 节点权重 = 用电份额 × 节点区域落在该省的面积比。
- 编码：TH、VN 直连；ID 手工对照（DOSE 东加含北加、南苏含西苏）；PH `PH_PROVINCE_REGION_CROSSWALK.csv`。
- 过程排放与非能源跟随设施（D164-5 a）：2.A 跟水泥；2.C 跟钢铁 + 有色（按 2050 能量加权）；2.B + 2.D 与非能源跟炼油石化；生活塑料焚烧保持 v2。
- 氨负荷在国家母线，节点键只作命名，保持 v2。

## 7. 第 165 项：EV

- **结构（D165-4）：** E2 主算：`research.s2.demand.ev_structure = smart`。开关：`flat`（v2）、`smart_v2g`（E3）、`uncontrolled`（E4），后两者只实现不运行。
- 负荷：`land transport EV` 接 EV 电池母线，形状 = 26 国平均 168 小时周型（2013，当地时钟，已还原夏令时）；D165-1 a。
- 时区：MM +6:30；TH、VN、KH、LA +7；MY、SG、PH、BN +8；TL +9；ID 按节点所在省 +7 / +8 / +9（16 / 17 / 6 个节点）。
- 对齐：2013 日历按当地星期（D165-3 a）；半小时线性插值；3 h 快照内平均；每节点年量等于 v2。
- 车队代理：`N = EV 年量 / a × ev_fleet_scale`，`a = 12,000 km / 5,319 km/MWh = 2.256 MWh/辆·年`（C 级，无库内来源），`ev_fleet_scale` ×0.5 / ×2。东盟合计约 3.2 亿辆当量，对照 `transport_data.csv` 现有车辆 2.65 亿，量级一致。
- Store：`e_nom = N × 0.05 MWh × 0.5`，`e_cyclic=True`，每日当地 7 时 `e_min_pu = 0.8`。
- 充电桩：`p_nom = N × 0.011 MW`，不可扩建，效率 0.9，`p_max_pu` = `plugin` 周型（D165-2）。
- E4：无 Store，负荷整体延后 3 小时（C 级，未运行）。
- 分辨率：`to_daily` 抹掉日内形状，365×24h 筛查基本不反映本项。

## 8. 账本与闸门

- `ASEAN_POOL` 无行，B16 差异项 ≈ 0。新结算主题 `liquid_trade_<载体>`，运费主题 `liquid_ship_freight`、`liquid_transit_freight`（进 `DIRECT`）。
- `bunker_standalone` 路线改为进口机组 → 国家母线 → 节点 → 表计。
- 闸门改名与新判据：`POOL_BUSES` 改按载体匹配；新增 `gate_b5_no_new_xb`；`gate_b6_cost` 只换标签。**验收阈值不变。**
- `gates_v6.SUBSET_KEYS` 增加 `liquids`（结构键，不是阈值）。

### 8.1 B13 判据修改（2026-11-02 补记，求解前）

补记原因：HiGHS 8 时段路径检查（`RUN_PLAN_V3.md` 第 6 节）中 B13 失败。B13 是结构判据，没有数值阈值；在 GATES_V6 中是诊断项 D13，不进入验收标签。

| | 判据（一条连到母线池的链路何时算违规） |
|---|---|
| 修改前 | `not others or 其余端口有不在网络中的母线`；`others` = 不在母线池里的端口 |
| 修改后 | `(not others and border_class != "maritime_trade") or 其余端口有不在网络中的母线` |

- 理由：旧判据假定每条连母线池的链路至少有一端在池外。第 161 项把池改成国家液体母线后，船运和老挝过境链路两端都是国家母线，这个假定不再成立。B13 要防的是能量经池离开模型，这些链路两端都在模型内，不构成出口。
- 修改只放行带 `maritime_trade` 标记、且全部端口都在网络内的链路。
- 修改前后对照（`evidence/B13_BEFORE_AFTER.json`，不求解）：

| 网络 | 连母线池的链路 | 旧判据标出 | 新判据标出 | 旧判据标出的是否恰为液体贸易链路 |
|---|---:|---:|---:|---|
| v3 一体化、`no_new_xb`（2920×3h、365×24h 共四个，数值相同） | 1,085 | 277 | 0 | 是：船运 270、过境 7 |
| v2 一体化 2920×3h | 746 | 0 | 0 | 无此类链路；判据修改不影响 v2 |

- 反例测试（`tests/research/test_v3.py`）：`test_b13_ship_between_national_buses_passes` 确认船运放行；`test_b13_counterexamples_still_fail` 确认三种情况仍然失败：两端都是国家母线但没有 `maritime_trade` 标记的链路；没有 `border_class` 列的旧网络上的同类链路；带 `maritime_trade` 标记但有一端在模型之外的链路。

### 8.2 56 时段下 B8 不通过（2026-11-02 补记，求解前）

补记原因：同一路径检查中 B8 失败。B8 在 GATES_V6 中是诊断项 D11，不进入验收标签，也不是指令第 4 条的冒烟验收项。**B8 的 1e-6 门槛不改，冒烟中 B8 照实报告为不通过。**

| 网络 | Transport 相对差 | B8 |
|---|---:|---|
| 2920×3h 全年（一体化、`no_new_xb`） | −7.8e-16 | 通过 |
| 365×24h 全年 | 7.8e-16 量级 | 通过 |
| 截短 56 时段（1 月 1 日至 7 日） | **−4.1146e-05** | 不通过 |
| 截短 8 时段（1 月 1 日） | +1.4977e-02 | 不通过 |

- 原因：`land transport EV` 从 v2 的恒定值改为 168 小时周型（第 165 项）。序列按全年归一，全年是 52 周加 1 天（2013 年 1 月 1 日是星期二，星期二比星期平均多一次），所以一周的均值不严格等于全年均值。其他部门的表负荷不受影响，相对差都在 1e-15 量级。
- 数量核对：记全年均值 = 1，星期二均值 = 1 + r，周均值 = W，则 365 = 52 × 7 × W + (1 + r)，得 W = 1 − r/364。8 时段的 r = +1.49772e-02，推出 W − 1 = −4.1146e-05，与 56 时段实测值相符。
- 这是截短假象，不是需求错误：全年网络逐部门闭合，`DEMAND_NETWORK_CHECK_V3.csv` 四个网络逐国逐载体闭合。冒烟中 EV 年当量需求比表低约 0.05 TWh（1,255.8 TWh × 4.1146e-05，Transport 部门中只有 EV 负荷随时间变化）。
- 只在预期之内：冒烟的 B8 若有 Transport 以外的部门超限，或 Transport 相对差不等于 −4.1146e-05，就不属于本条解释，须另行报告。

## 9. 预期结构差异（v3 对 v2，测试逐类型列出）

| 类型 | 变化 |
|---|---|
| Bus | 删 `ASEAN oil`、`ASEAN oil non-fossil`、`ASEAN methanol`、`ASEAN ammonia`、`ASEAN aviation international oil final`、`ASEAN shipping international methanol final`；增四类国家母线（44）、节点燃料舱终端 |
| Generator | 删 4 台 `ASEAN * import`；增 `{c} * import`（40） |
| Store | 删 2 个 ASEAN 储罐；增国家储罐（33）、EV 电池（96） |
| Link | 增船运（270）、过境（7）、节点燃料舱表计；改 `oil pool`、Haber-Bosch、裂解、甲醇合成、生物甲醇、甲醇 OCGT、工业甲醇、船用甲醇、FT 输出链路的端口；`BEV charger` 改容量与 `p_max_pu` |
| Load | 工业负荷按节点重分配；`land transport EV` 改时序；燃料舱负荷回到节点 |
| Generator（过程排放） | 节点重分配 |
| Link（`oil pool`，2026-11-02 补记） | 增 4 条：`MY_Peninsular22 0`、`PH_Luzon9 0`、`PH_Visayas10 0`、`TH21 0`。这 4 个节点在 v2 只有非化石油母线（FT 产地），设施分配（第 164 项）把工业用油放到这里，才有了化石油母线和配送链路；核对后 `oil pool` 与 `oil non-fossil pool` 各 100 条，化石计量与孪生计量各 585 个，无缺口 |
| 其他 | **不应有变化**（线路、发电、输电候选、成本、效率） |
