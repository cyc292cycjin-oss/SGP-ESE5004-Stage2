# v4 W10 第一阶段：C 级参数按影响排序（台账 W10；决策清单第 201、211 项）

- **指令：** `work/p1_v4_w10_20261106/V4_W10_INSTRUCTION.md` v1，SHA256 `14165bf102dbfcb25fa06255a4884474691515a33eb3b86866886d8542a160ed`，与同目录 `V4_W10_SHA256.txt` 一致（开工前核对，VERIFIED）。
- **分支与目录：** `codex/v4-w10-20261106`，从 `codex/v4-i2-20261106` 头 `aad8e476` 新开；worktree `/home/jin/wt_v4_w10`。交付目录 `work/p1_v4_w10_20261106/` = 仓库 `research/06_scope_redesign/p1_v4_w10_20261106/`（`cache/` 与审阅 zip 不入库）。没有碰 W08 的分支、worktree 与目录。
- **性质：** 只读分析。没有改仓库中的代码、输入、注册表；**求解器 0 次**；没有构建网络；没有下载数据。本机计算约 3 分钟（6 个已解网络提取 61 s，每次重排 20 s），磁盘新增约 25 MB。
- **标记：** VERIFIED（读到的表、代码、对偶）、EXACT（逐项可复现的计算）、INFERENCE（推断、外推、凭记忆的来源）、PROPOSED（建议，未实施）。数据等级沿用 I2：A 实际统计、B 官方 / 国家统计、C 推导、D 模型估计或假设、E 缺失。金额单位 EUR2020，"M" = 百万，"bn" = 十亿；ΔB6 = ΔZ(F2) − ΔZ(F1)，Z 为 LP 目标值（与 B6 的定义一致：DFX_SUMMARY "B6 = V2 − V1"）。

## 0. 结论摘要

1. **口径对账（VERIFIED）：** 第 201 项的"在用 1,436 个、C 级 441 个"恰好等于 DFX F4 版注册表（`72083fde`，2,280 行）中状态为 REGISTERED + SENSITIVITY + DATA_PENDING 的行；按参数名前缀分族，生物质 193、工业 55、路线份额 43、潜力 27、CO₂ 22、WACC 15、其他 86，与第 201 项逐族相同。当前头 `aad8e476`（2,321 行）同口径为 1,464 / **462**，多出的 21 行全是 v3 片段（液体船运 16、EV 车队 2、规则 2、LA–TH 专线 1）；两版共有的 441 行在值、单位、状态、登记区间、来源 SHA256、描述上逐列相同（`C_GRADE_INVENTORY_META.json`）。
2. **462 行的去向（EXACT，`C_GRADE_INVENTORY.csv`，互斥计数）：** 需求侧 79 行按第 211 项引用 I2，不重复；主算中不起作用 54 行（退化区间 16、国别 WACC 15——主算 `wacc_mode = uniform`、只作进口价敏感性输入 4、TL 无封存评估 3、只作用于完全隔离情景 3 等）；离散规则 / 开关 32 行（无一阶）；重复与情景选择 15 行；**可一阶排序 282 行**。每行都给出进入网络的代码位置（构建时在 worktree 中定位到 `文件:行`，462 行全部找到）。
3. **方法与校核（VERIFIED / EXACT）：** 用已解结果的对偶做包络定理一阶估计：成本类 = 用量 × 单价变动；容量与潜力类 = 约束对偶 × 右端变动；效率类 = −Σ(价格 × 流量) × 效率变动；路线份额 = Σ(价格 × 负荷变动)。价格取母线平衡对偶 ÷ 时段权重，与导出的 `NODAL_PRICES.csv` 均值最大相对差 4.5e-6；6 个网络全部可扩展机组的容量平稳性残差 ≤ 5.6e-9（相对年金单价），未建候选的进入缺口无一为负（`evidence/CHECKS.json`）。局部导数是 EXACT，外推到一档是 INFERENCE。
4. **参照组与稳定性（INFERENCE，待决第 1 问）：** 以补充 07 的 365×24h（V1 / V2，B6 14.5738 bn）为参照；v3 筛查 365×24h（B6 14.3481 bn）与之 Spearman 0.991、前 30 重合 28；v3.1 56×3h 冒烟（与 2920×3h 同一网络文件截取一周，B6 12.5631 bn）Spearman 0.872、重合 21。冒烟只代表一个旱季周（权重 156.4 h），屋顶光伏上限、LA 风电、气田分配等项名次大幅变化，所以按"全年数量最接近 2920×3h"取补充 07。
5. **影响高度集中（INFERENCE）：** 282 行中 |ΔB6| ≥ 1 bn 的 6 行、≥ 100 M 的 18 行、≥ 10 M 的 51 行；**前 30 行占全部可排序 |ΔB6| 之和的 96 %**。前 10：WACC 模式切换 −3.51 bn（规则切换）、MY 屋顶光伏上限 +50 % −2.06 bn、EV 每百公里效率 −20 % +1.50 bn、陆路交通 30 % 转 ICE −1.42 bn、ICE 效率 −20 % −1.18 bn、BEV 充电效率 −20 % +1.18 bn、VN 等海上风电 alpha +24 % −0.73 bn、LNG 再气化加价 3.27 EUR/MWh +0.67 bn、CO₂ 船运固定段 +50 % +0.56 bn、TH 气田节点分配改负荷份额 +0.43 bn（表 T1）。
6. **生物质（INFERENCE，待决第 4 问）：** 193 行（占 C 级 42 %）对 B6 合计只有 0.43 bn（2.6 %），只有 10 行 ≥ 10 M——F1 与 F2 都在本国内用本国生物质，变化几乎抵消。但它们对**系统成本与分国 Owen 分摊**很大：ID 油棕树干潜力取登记上端（681 TWh）时 F1 −20.4 bn、几乎全归 ID；Owen 影响前 10 中生物质占 5 行（表 T2）。按 B6 排序升级生物质优先级低，按 Owen 排序则 ID / MY 油棕残余是最优先。
7. **WACC（VERIFIED / INFERENCE，待决第 3 问）：** 15 行国别 WACC 在主算中不起作用；把它们打开（`country_specific`，用 `COUNTRY_WACC_REAL_M08A.csv` 的 11 国实际利率）一阶为 F1 −7.73 bn、F2 −11.23 bn、**ΔB6 −3.51 bn**，Owen 影响最大 TH −4.48 bn。数据升级只需核实 11 国实际 WACC；主算模式是用户决定。
8. **不可靠的一阶估计（表 T4，`UNRELIABLE_FIRST_ORDER.csv` 129 行，其中 TOP30 中 19 行）：** 候选会进入 24 行——**地热处在进入边缘**：MY、PH、VN 未建地热候选的进入缺口只有年金单价的 0.004–0.11 %，ID 一个节点顶到上限（μ = 102,066 EUR/MW/a），地热投资 / FOM（C 级 ±30 %）一降就会大量新建；SMR 在 ID、SG 的进入缺口为 1.9 %、2.6 %。变动过大 50 行（屋顶光伏 ±50 %、风电 alpha 区间端点的 ΔCF/CF 达 36–66 %、交通 / 航运 20–45 % 的载体转移等）。零余量 / 退化对偶 3 行：KH CO₂ 注入上限 1.8 Mt/a 恰好用满但对偶为 0。网络中无候选 9 行（DATA_PENDING 地热 8 国、TH / TL 水电：`s4a_3_potentials.py` 规定 `p_nom_max = 0`）。名次不稳 8 行。离散规则（33 行，含需求侧的生物质溢出规则 1 行）中**原料碳全释放口径**（SENSITIVITY）量级最大：按 F2、F1 国家 CO₂ 对偶之差估 ΔB6 约 MY +0.96、TH −0.62、SG +0.21、BN +0.10 bn。
9. **新发现（VERIFIED）：** (a) 油棕树干**成本** DATA_PENDING 在网络中按 **0 EUR/MWh** 进入（`s2_layers.py:467`：成本列为空即 `marginal_cost = 0`），ID 158.5 TWh 全部用满；取代理价 9.40 EUR/MWh 时 ID 系统成本 +1.49 bn。(b) 3 行登记了但构建不读：`share_aviation_demand_factor`、`share_HVC_demand_factor`、`share_bev_avail_max`；`share_bev_avail_mean` 被 v3 EV 结构 E2 覆盖。(c) `co2_extra_asean_storage_cost` 与 `co2_extra_asean_offshore_storage_eur2009` 只属于决策 89 的备选口径，主算用 `co2_extra_asean_storage_cost_unified`（54.698 = 船运链 24.698 + 30）。(d) DATA_PENDING 潜力在网络中没有候选，一阶无法估值，升级它们是"补候选"而不是敏感性。
10. **下载候选（`W10_DOWNLOAD_CANDIDATES.csv`，30 行，来源全部 INFERENCE 待核实网址）：** 难度低、可先做的 9 项：国别 WACC（IEA 资本成本观察站）、LNG 再气化费率（TH ERC、MY 能源委员会、SG SLNG、ID BPH Migas 公布值）、CO₂ 船运成本（IEAGHG 2020、ZEP 2024）、封存成本价格年、LNG 终端投资（IGU 2024）、BEV 充电效率、TH–MY 91 号线额定容量、甲醇合成两项（每 t CO₂ 的甲醇量可按化学计量直接推导为 4.025 MWh/t，无需下载）。中等难度：屋顶光伏潜力数据集、按车型的交通能效、分气田产量与登陆点、ID 油棕翻种统计、LA–TH 专线、风电场实测。高难度且影响小：EV 年行驶里程、充电行为、农机电动化。
11. **重排接口（VERIFIED，`evidence/SELFTEST.json` 3 项 PASS）：** `rerank_with_results.py` 接受任意组 F1 / F2 结果目录，重算第 2–3 节全部表；缓存命中时重跑逐字节相同；组顺序不影响结果；单独给一组时与多组运行中该组的列完全一致。v3.1 2920×3h 结果到位后的命令见第 4 节。
12. **提交过程的一处偏差（VERIFIED）：** W10-1、W10-2/3/4 两次提交时命令多带了 `-c core.hooksPath=.git/hooks`。已核实仓库未设置 `core.hooksPath`、公共目录 `hooks/` 只有 `.sample` 文件、`pre-commit` 未安装，因此没有任何 hook 被跳过；之后的提交已去掉该参数。

### 0.1 待决问题（每条带推荐）

1. **参照组：** 推荐在 2920×3h 结果到位前以补充 07 365×24h 为准（全年数量、EV 下限已按第 182 项修正）；冒烟只作结构检查。若审阅端认为"同一网络文件"更重要，可改用 `--reference smoke56v31` 一条命令重排。
2. **交通与 EV 参数归哪一侧：** 前 10 中有 4 行是 PyPSA-Eur 的交通与 EV 常数（EV 效率、ICE 效率、BEV 充电效率、电动化份额），它们改变 EV 用电量。推荐把效率与车队参数作为本阶段的数据升级对象（按东盟车型构成，两轮车占比高），把电动化份额作为情景，不作数据升级。
3. **WACC 主算模式：** 由用户决定；推荐先核实 11 国实际 WACC 表，再在 v4 正式批次把 `country_specific` 作为一个直接求解的敏感性（一阶 ΔB6 −3.51 bn，量级第一）。
4. **生物质按 Owen 另排：** 推荐另设按 Owen 影响的升级清单（表 T2）：ID / MY 油棕树干潜力与成本、ID EFB 与纤维潜力；对 B6 的排序不变。
5. **油棕树干成本按 0 进网：** 是否在 v4 正式批次前改为代理价（6.27 EUR/MWh，注册表对无来源残余的代理）是改输入，需用户决定；推荐改，并在 W08 合入后的第二阶段处理。
6. **地热与 SMR 处在进入边缘：** 推荐在 v4 正式批次中直接求解"地热投资 −30 %"一档；SMR 同理（ID、SG）。
7. **原料碳全释放口径：** 量级与前 10 相当，推荐列入 v4 正式批次的直接求解敏感性。
8. **KH CO₂ 注入上限零余量零对偶：** 与 v3.1 燃料舱问题同属"恰好用满"的结构，推荐在 2920×3h 结果中复查其对偶与预处理行为。
9. **来源核实：** 全部候选来源凭记忆列出（INFERENCE），网址须审阅端核实后再交用户下载。

## 1. 参数清单

### 1.1 口径与对账

| 版本 | 注册表行 | 在用（REGISTERED + SENSITIVITY + DATA_PENDING） | 其中 C 级 | 生物质 | 工业 | 路线份额 | 潜力 | CO₂ | WACC | 其他 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `72083fde`（DFX F4，第 201 项所据） | 2,280 | 1,436 | 441 | 193 | 55 | 43 | 27 | 22 | 15 | 86 |
| `aad8e476`（I2 头，本次） | 2,321 | 1,464 | 462 | 193 | 55 | 43 | 27 | 22 | 15 | 107 |

分族规则（EXACT）：`biomass_*`、`industry_*`、`share_*`、`co2_*`、`wacc_*`、`potential_* / renewable_cap_* / candidate_cap_* / nuclear_plan_cap_*`，其余为"其他"。新增 21 行（VERIFIED）：`liquid_ship_*` 16、`ev_annual_km_per_vehicle`、`ev_mwh_per_vehicle_year`、`bunker_node_rule`、`liquid_co2_structure_rule`、`xb_stock_la_th_dedicated_lines`；删除 0 行。

### 1.2 清单内容

`C_GRADE_INVENTORY.csv` 每行：编号、数值、单位、国家、状态、登记区间、**一档**（低 / 高）及其依据、**为何是 C**（由描述与族规则归纳：代理值、假设、来源未复核、无可引用来源、规则开关等）、来源、决策号、生成脚本、**进入网络的代码位置**（`文件:行`）、进入哪些组件、主算是否起作用、一阶机制（JSON）与备注。主要入网路径（VERIFIED）：

| 族 | 入网路径 | 组件 |
|---|---|---|
| 生物质成本 / 潜力 | `s2_layers.add_biomass_layer`（`s2_layers.py:452`、`:469`） | Store `<国> biomass <品类>`：`e_nom = e_initial = 潜力`，`marginal_cost = 成本`，只放不充 |
| CO₂ 船运 / 陆运 / 区外封存 | `s4d_layers.py`、`s4e_layers.py`、`v3_layers.py:287` | Link `CO2 ship`、`CO2 transit *`；Store `co2 sequestered extra-ASEAN <国>` |
| CO₂ 封存上限与成本 | `s2_layers.py:39`、`:342` | 全局约束 `research_co2_storage_cap-<国>`；Store `co2 sequestered <国>` 年金 30 EUR/t |
| 液体船运 | `v3_layers.ship_unit`（`:79`）、`add_liquid_shipping`（`:264`） | Link `<载体> ship`、`liquid transit rail` |
| EV 车队代理 | `v3_layers.apply_ev_structure`（`:303`） | Store `EV battery`、Link `BEV charger` |
| 交通 / 航运 / 农机份额 | `s2_layers.add_demand_layer`（`:654`、`:658`、`:822`） | 各类负荷与计量链 |
| LNG / H₂ 终端、进口 | `s3_layers.py:81`、`:191`、`:38` | Generator `LNG import`、`H2 import` 等 |
| 气田节点分配 | `s3_layers.py:88` | 全局约束 `ResearchImportAnnual-<节点> gas production` |
| 风电校准 / 台风溢价 | `s4a_profiles.py:55`、`s4b_layers.py:91` | 风电 `p_max_pu`、年金 |
| WACC 模式 | `s4c_layers.apply_wacc_mode`（`:123`） | 全部可扩展组件年金 |
| 互联线与走廊 | `s4f_2_corridors.py:5`、`s3_0_corridors.py:6` | Line `91`、`APG11_TH_MM`、`APG17_LA_MM` |

**T7　机制分布（462 行）**

| 机制 | 行数 | 机制 | 行数 |
|---|---:|---|---:|
| `store_mc` | 103 | `demand_I2` | 75 |
| `store_pot` | 69 | `zero` | 58 |
| `discrete` | 33 | `link_mc` | 23 |
| `new_capacity_rc` | 13 | `gen_pnom_max` | 11 |
| `gen_cf` | 9 | `fixed_emission_scale` | 8 |
| `gas_alloc` | 5 | `agri_shift` | 4 |
| `link_pnom_fixed` | 3 | `scalar_rhs` | 3 |
| `transport_shift` | 3 | `meoh_eff` | 3 |
| `hb_eff` | 3 | `shipping_shift` | 3 |
| `ev_load_scale` | 2 | `unbuilt_check` | 2 |
| `store_enom_fixed` | 2 | `aeo8_factor` | 2 |
| `lao_rail` | 2 | `store_cc` | 2 |
| `gen_cc_part` | 2 | `gen_mc` | 2 |
| `line_length_cc` | 2 | `store_pot_scale` | 2 |
| `gen_cc` | 2 | `typhoon` | 1 |
| `line_existing` | 1 | `new_store_bus_value` | 1 |
| `su_pnom_max` | 1 | `link_eff_km` | 1 |
| `store_floor` | 1 | `link_eff` | 1 |
| `store_cc_factor` | 1 | `ev_fleet` | 1 |
| `wacc_mode` | 1 | `gen_mc_rel` | 1 |


## 2. 一阶影响

### 2.1 一档的取法

1. 有登记区间（C 级数值行都有，`d1_registry.validate` 强制）：一档 = 主值到登记低值、主值到登记高值，两个方向都算，排序取 |ΔB6| 较大者（EXACT 取值）。
2. DATA_PENDING 行（PROPOSED）：油棕树干成本 0 → 注册表代理 6.27 × 1.5；LA 城市有机垃圾潜力 → KH 值 × 垃圾量比；封存成本价格年 → 系数 0.86–1.0（类比 AEO8 价格年，决策 131）；海上风电 alpha → 陆上代理 alpha 的相对区间；LA–TH 专线 → ±50 %（D1 L13 的 C 级默认幅度）；地热 / 水电 / 抽蓄潜力 → 描述中引用的数字。
3. 规则 / 开关：有登记备选的按备选一次切换（WACC 模式、气田分配、台风溢价、进口价格 −20 %）；没有备选的不做一阶（离散）。
4. 成对的份额（陆路交通电动 / ICE、航运甲醇 / 燃油、农机电动 / 燃油）按"同一移动"算一次，另一行标重复。0→1 的燃料电池车与航运氢份额标"情景选择"，不排序。

### 2.2 机制与公式（`rerank_with_results.py`，EXACT 实现）

| 机制 | ΔZ 的一阶式 | 用到的量 |
|---|---|---|
| 生物质成本 `store_mc` | 放出量 × Δ成本 | Store 放出能量 |
| 生物质潜力 `store_pot` | −稀缺租 × Δ潜力（只对用尽的池；未用尽为 0） | 稀缺租 = 放出加权 (λ − 成本) |
| 封存 / 区外封存成本 `store_cc` | 新增容量 × Δ年金 | `e_nom_opt − e_nom` |
| 链路单价 `link_mc`、`lao_rail` | 流量 × Δ边际成本（固定段、每 km、航线系数、热值反比） | Link 流量、`route_km` |
| 效率 `link_eff`、`hb_eff`、`meoh_eff` | −Σ_t λ_bus_k · w · p0 × Δη_k | 各端口价格与流量 |
| 容量上限 `gen_pnom_max`、`su_pnom_max` | −上界对偶 × Δ上限 | `Generator-ext-p_nom-upper` 对偶 |
| 风电 CF `gen_cf` | −Σ_t \|μ_t\| · p_max_pu · p_nom × ΔCF/CF；ΔCF/CF = ε × Δα/α | 出力上界对偶；ε = 2.76（ID 行）/ 1.59（海上用 PH 行） |
| 固定容量 `link_pnom_fixed`、`store_enom_fixed`、`ev_fleet`、`store_floor` | −容量价值 × Δ容量；下限：Σ 下界对偶 × e_nom × Δ下限 | `*-fix-*` 对偶 |
| 存量线路 `line_existing` | F1：(−年金 + 下界对偶 + 上界对偶) × Δ存量；F2：−拥塞价值 × Δ存量 | 线路对偶 |
| 走廊长度 `line_length_cc` | 新增容量 × 年金 × Δ长度 / 长度 | — |
| 全局约束 `scalar_rhs` | 对偶 × Δ右端 | `research_co2_storage_cap-*` |
| 路线份额 `transport_shift`、`shipping_shift`、`agri_shift`、`ev_load_scale` | Σ λ × Δ负荷（含 EV 车队随负荷缩放） | 负荷价值、目标载体母线均价 |
| WACC 模式 `wacc_mode` | 新增容量 × 年金 × [(AF(r_国) + FOM) / (AF(0.07) + FOM) − 1] | 成本明细表的投资、FOM、寿命 |
| 气田分配 `gas_alloc` | −Σ_节点 Δ上限 × 节点价值（有约束取对偶，无井口节点取 气价 − 生产成本） | `ResearchImportAnnual` 对偶 |
| 新增潜力 `new_capacity_rc` | 国内有紧候选：−紧候选对偶 × Δ潜力；无候选：不可表示 | — |

**Owen 近似（INFERENCE）：** 分国影响 = ΔZ(F1) 按受影响组件、负荷或约束所在国汇总（跨境线路各半，国际燃料舱归 BUNKER）。对 RHS 类参数这与 Owen 对偶式 y'b 的一阶变化一致；对成本类参数，真实的 Owen 变化会经价格扩散到进口国，这里只按组件所在国记，是近似。

### 2.3 已解结果

| 组 | F1（一体化） | F2（no_new_xb） | 分辨率 | 船运口径 | B6 |
|---|---|---|---|---|---:|
| `s07`（参照） | 补充 07 V1，目标 266.2728 bn | V2，280.8466 bn | 365×24h（EV 下限按第 182 项） | S-B | 14.5738 bn |
| `screen` | 筛查 V1，263.5966 bn | V2，277.9447 bn | 365×24h（EV 下限被日均化） | S-B | 14.3481 bn |
| `smoke56v31` | v3.1 演练包冒烟 F1，329.7056 bn | F2，342.2687 bn | 56×3h（2920×3h 网络截取一周） | S-A | 12.5631 bn |

所有网络的 SHA256、价格核对与平稳性残差见 `evidence/CHECKS.json` 与 `EVIDENCE.json`。船运参数在口径不同的运行中仍用该运行的流量计算，并标注"口径未生效"。

### 2.4 不可靠的情形

**T4　不可靠一阶估计的类别（一行可有多个标记）**

| 类别 | 行数 | 其中 TOP30 |
|---|---:|---:|
| 候选会进入（未建候选的进入缺口小于变动） | 24 | 6 |
| 变动过大（一档 ≥ 50 % 作用在紧约束上、或 ≥ 20 % 的载体转移、或 |ΔCF/CF| > 20 %） | 50 | 11 |
| 受影响的新增容量在 F1 / F2 相差 > 50 % | 10 | 1 |
| 约束由紧变松或由松变紧 | 1 | 0 |
| 零余量 / 退化对偶 | 3 | 0 |
| 名次在另一组结果中进出前 30 的两倍 | 8 | 5 |
| 网络中无对应候选 | 9 | 0 |
| 情景选择（0→1） | 2 | 0 |
| 用了代理价格或代理候选 | 5 | 3 |
| 上界估计 | 8 | 0 |
| 网络中不存在的资源 | 1 | 0 |
| 离散规则 / 开关（无一阶） | 33 | 0 |
| **不可靠表合计** | 129 | 19 |


**建议在 v4 正式批次中直接求解的敏感性（PROPOSED，按预期信息量）：** ① WACC `country_specific`；② EV 用电量 ×1.25（同时覆盖 EV 效率、ICE 效率、BEV 充电效率三行）；③ 屋顶光伏上限 MY / VN / SG / TH ±50 %（一次同向）；④ 地热投资 −30 %；⑤ 风电 alpha 代理国与海上 alpha 取登记端点；⑥ 气田分配 `load_shares`；⑦ 原料碳全释放口径；⑧ ID / MY 油棕树干潜力低档与成本代理价（为 Owen）；⑨ EV 车队 ×0.5 已在 F3 / F4（第 186 项），不另加。

### 2.5 排序稳定性

`RERANK_SUMMARY.json`：参照组对筛查 Spearman 0.991（前 30 重合 28，移出 `onwind_alpha_LA`、`share_bev_dsm_restriction_value`）；对冒烟 0.872（重合 21，移出屋顶光伏 BN / MY / VN、农机三行、91 号线、LA–TH 专线、ID 油棕树干潜力）。冒烟中 `onwind_alpha_LA` 升到第 1、气田分配 ID 号的符号相反，原因是该周为 LA 旱季、权重 156.4 h，年量被一周放大。

## 3. 排序与来源

### 3.1 前 30 项

**T1　TOP30（参照组 s07；EUR 百万；方向 = |ΔB6| 较大的一端）**

| # | 参数 | 主值 | 一档（低 / 高） | 方向 | ΔZ(F1) | ΔZ(F2) | **ΔB6** | Owen 最大（国） | 筛查名次 | 冒烟名次 | 一阶可靠性标记 |
|---:|---|---:|---|---|---:|---:|---:|---|---:|---:|---|
| 1 | `scenario_switch_wacc_mode` | uniform | 备选规则 / 备选规则 | 高 | -7,725.6 | -11,232.4 | **-3,506.7** | -4,483.6（TH） | 1 | 2 | 规则切换 |
| 2 | `renewable_cap_built_solar_rooftop_MY` | 8.315e+04 | 4.157e+04 / 1.247e+05 | 高 | -725.2 | -2,783.0 | **-2,057.8** | -725.2（MY） | 2 | 274 | 变动过大、名次不稳:smoke56v31 |
| 3 | `share_transport_electric_efficiency` | 53.19 | 42.55 / 63.83 | 低 | 6,546.9 | 8,048.3 | **1,501.4** | 1,690.3（ID） | 4 | 7 |  |
| 4 | `share_land_transport_electric_share_2050` | 1 | -0.3 / 0 | 低 | 35,915.0 | 34,495.8 | **-1,419.2** | 11,215.2（TH） | 3 | 14 | 变动过大 |
| 5 | `share_transport_ice_efficiency` | 16.07 | 12.86 / 19.29 | 低 | -4,911.8 | -6,095.9 | **-1,184.1** | -1,277.4（ID） | 5 | 12 |  |
| 6 | `share_bev_charge_efficiency` | 0.9 | 0.72 / 1.08 | 低 | 4,911.8 | 6,095.9 | **1,184.1** | 1,277.4（ID） | 6 | 11 |  |
| 7 | `offwind_alpha_calibration_rule` | DATA_PENDING | -0.1302 / 0.2379 | 高 | -5.8 | -731.0 | **-725.2** | -5.8（VN） | 10 | 5 | 变动过大、候选会进入 |
| 8 | `fuel_price_lng_regasification_adder` | 1.26 | 0.7535 / 3.265 | 高 | 208.4 | 880.7 | **672.3** | 119.6（VN） | 7 | 8 | 候选会进入 |
| 9 | `co2_ship_chain_fixed_cost` | 11.42 | 5.708 / 17.12 | 高 | 242.4 | 799.1 | **556.7** | 239.0（PH） | 9 | 10 |  |
| 10 | `gas_production_node_allocation_TH` | 0.3631 | 备选规则 / 备选规则 | 高 | -775.5 | -346.9 | **428.6** | -775.5（TH） | 8 | 4 | 规则切换、代理值 |
| 11 | `onwind_alpha_MY` | 1.046 | 0.9095 / 1.294 | 高 | -28.7 | -447.6 | **-419.0** | -28.7（MY） | 11 | 23 | 变动过大、候选会进入 |
| 12 | `co2_sequestration_cost_price_year` | DATA_PENDING | 0.86 / 1 | 低 | -2,740.9 | -3,050.1 | **-309.2** | -1,406.0（ID） | 12 | 15 | 候选会进入 |
| 13 | `gas_production_node_allocation_MY` | 0.277 | 备选规则 / 备选规则 | 高 | -521.3 | -771.5 | **-250.2** | -521.3（MY） | 13 | 22 | 规则切换、代理值 |
| 14 | `biomass_potential_ID_oil_palm_trunk` | 1.585e+08 | 3.169e+07 / 6.814e+08 | 高 | -20,357.7 | -20,571.8 | **-214.1** | -20,357.7（ID） | 20 | 31 | 变动过大 |
| 15 | `renewable_cap_built_solar_rooftop_SG` | 5336 | 2668 / 8005 | 低 | 63.3 | 226.6 | **163.3** | 63.3（SG） | 14 | 25 | 变动过大 |
| 16 | `gas_production_node_allocation_ID` | 0.3589 | 备选规则 / 备选规则 | 高 | -440.2 | -587.0 | **-146.8** | -440.2（ID） | 19 | 6 | 规则切换、代理值 |
| 17 | `renewable_cap_built_solar_rooftop_VN` | 1.223e+05 | 6.113e+04 / 1.834e+05 | 低 | 0.0 | 121.5 | **121.5** | 0.0（—） | 15 | 278 | 变动过大、名次不稳:smoke56v31 |
| 18 | `xb_stock_la_th_dedicated_lines` | DATA_PENDING | -0.5 / 0.5 | 低 | 2.5 | 122.5 | **120.0** | 2.5（LA） | 16 | 69 | 名次不稳:smoke56v31 |
| 19 | `lng_terminal_expansion_capex_main` | 8020 | 4010 / 1.203e+04 | 低 | -31.5 | -125.8 | **-94.2** | -31.5（VN） | 18 | 18 | F1/F2 投资差大、候选会进入 |
| 20 | `share_MWh_MeOH_per_tCO2` | 4.032 | 3.226 / 4.839 | 低 | -668.7 | -762.6 | **-93.9** | -397.5（ID） | 17 | 19 |  |
| 21 | `th_my_line91_s_nom_2025` | 80 | 80 / 380 | 高 | -3.7 | -93.1 | **-89.4** | -1.8（MY） | 21 | 44 | 变动过大 |
| 22 | `ev_annual_km_per_vehicle` | 1.2e+04 | 6000 / 2.4e+04 | 低 | -1,628.8 | -1,713.9 | **-85.1** | -455.7（TH） | 22 | 9 | 变动过大 |
| 23 | `share_bev_dsm_restriction_value` | 0.8 | 0.64 / 0.96 | 低 | -1,303.0 | -1,371.1 | **-68.1** | -364.6（TH） | 46 | 27 |  |
| 24 | `onwind_alpha_LA` | 1.046 | 0.9095 / 1.294 | 高 | -67.0 | -0.4 | **66.5** | -67.0（LA） | 114 | 1 | 变动过大、名次不稳:screen、候选会进入 |
| 25 | `share_agriculture_machinery_electric_efficiency` | 0.3 | 0.24 / 0.36 | 低 | 318.8 | 384.9 | **66.1** | 123.7（TH） | 24 | 32 | 推断映射 |
| 26 | `share_MWh_MeOH_per_MWh_H2` | 0.8787 | 0.703 / 1.054 | 低 | 9,130.2 | 9,192.8 | **62.6** | 6,776.0（ID） | 30 | 13 |  |
| 27 | `share_agriculture_machinery_fuel_efficiency` | 0.7 | 0.56 / 0.84 | 高 | 255.0 | 307.9 | **52.9** | 98.9（TH） | 28 | 34 | 推断映射 |
| 28 | `co2_ship_chain_per_km_cost` | 0.002952 | 0.001476 / 0.004427 | 低 | -77.9 | -130.1 | **-52.2** | -76.6（PH） | 25 | 24 |  |
| 29 | `share_agriculture_machinery_electric_share` | 0.5 | 0.4 / 0.6 | 低 | 1,024.5 | 975.9 | **-48.6** | 425.9（TH） | 29 | 48 | 推断映射 |
| 30 | `renewable_cap_built_solar_rooftop_BN` | 1461 | 730.6 / 2192 | 低 | 7.7 | 56.1 | **48.4** | 7.7（BN） | 27 | 269 | 变动过大、名次不稳:smoke56v31 |


### 3.2 按 Owen 影响

**T2　按 Owen 分摊影响排序的前 10（可排序行；EUR 百万）**

| # | 参数 | Owen 最大（国） | ΔZ(F1) | ΔB6 | B6 名次 | 标记 |
|---:|---|---|---:|---:|---:|---|
| 1 | `share_shipping_methanol_share_2050` | -21,544.4（BUNKER） | -22,240.0 | 7.3 | 54 | 变动过大 |
| 2 | `biomass_potential_ID_oil_palm_trunk` | -20,357.7（ID） | -20,357.7 | -214.1 | 14 | 变动过大 |
| 3 | `share_land_transport_electric_share_2050` | 11,215.2（TH） | 35,915.0 | -1,419.2 | 4 | 变动过大 |
| 4 | `share_MWh_MeOH_per_MWh_H2` | 6,776.0（ID） | 9,130.2 | 62.6 | 26 |  |
| 5 | `scenario_switch_wacc_mode` | -4,483.6（TH） | -7,725.6 | -3,506.7 | 1 | 规则切换 |
| 6 | `biomass_potential_MY_oil_palm_trunk` | -4,446.4（MY） | -4,446.4 | 37.6 | 33 | 变动过大 |
| 7 | `biomass_potential_ID_oil_palm_efb` | 2,050.7（ID） | 2,050.7 | 22.2 | 38 |  |
| 8 | `share_transport_electric_efficiency` | 1,690.3（ID） | 6,546.9 | 1,501.4 | 3 |  |
| 9 | `biomass_cost_ID_oil_palm_trunk` | 1,489.6（ID） | 1,489.6 | -0.0 | 149 |  |
| 10 | `biomass_potential_ID_oil_palm_fibre` | 1,406.2（ID） | 1,406.2 | 15.2 | 46 |  |


### 3.3 分族

**T3　分族汇总（第 201 项分族；EUR 百万）**

| 族 | 行数 | 可排序 | Σ\|ΔB6\| | 占比 | 最大 \|ΔB6\| | ≥ 10 M 的行 | 最大 \|ΔZ\| |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 107 | 55 | 6,843.6 | 41.7% | 3,506.7 | 19 | 11,232.4 |
| route_share | 43 | 18 | 5,735.3 | 34.9% | 1,501.4 | 12 | 50,223.0 |
| potential | 27 | 25 | 2,434.0 | 14.8% | 2,057.8 | 5 | 2,783.0 |
| co2 | 22 | 9 | 983.0 | 6.0% | 556.7 | 5 | 3,050.1 |
| biomass | 193 | 175 | 434.6 | 2.6% | 214.1 | 10 | 20,571.8 |
| industry | 55 | 0 | 0.0 | 0.0% | 0.0 | 0 | 0.0 |
| wacc | 15 | 0 | 0.0 | 0.0% | 0.0 | 0 | 0.0 |
| **合计** | 462 | 282 | 16,430.5 | 100 % | | 51 | |

注：Σ|ΔB6|、占比、最大值只计可排序行（重复行与情景选择行不计，否则路线份额族会把同一移动算两次）。

### 3.4 升级路径与下载候选

**T6　TOP30 的升级路径（`W10_DOWNLOAD_CANDIDATES.csv` 摘要；来源全部 INFERENCE，待核实网址）**

| # | 参数 | 现等级 → 可升级到 | 难度 | 主要候选来源（节选） |
|---:|---|---|---|---|
| 1 | `scenario_switch_wacc_mode` | C → B（ID/MY/PH/TH/VN）；C（其余 6 国仍按 CRP 法） | 低 | IEA Cost of Capital Observatory（2024/2025 更新，各国公用事业光伏 / 风电 WACC 区间） |
| 2 | `renewable_cap_built_solar_rooftop_MY` | C → B | 中 | MY：SEDA Malaysia Renewable Energy Roadmap (MyRER) 屋顶潜力 |
| 3 | `share_transport_electric_efficiency` | D → B | 中 | IEA Global EV Outlook 2025（分车型每公里电耗） |
| 4 | `share_land_transport_electric_share_2050` | D → B | 中 | ACE AEO8 ATS 情景的 2050 交通燃料结构（AEDS） |
| 5 | `share_transport_ice_efficiency` | D → B | 中 | IEA GEVO 2025 / IEA Fuel Economy in Southeast Asia |
| 6 | `share_bev_charge_efficiency` | D → B | 低 | IEA GEVO（充电损失） |
| 7 | `offwind_alpha_calibration_rule` | E → C（偏差系数）/ B（若有实测） | 中 | World Bank / ESMAP Offshore Wind Roadmap for Vietnam (2021) 各站点容量因子 |
| 8 | `fuel_price_lng_regasification_adder` | D → B | 低 | TH ERC 公布的 PTT LNG（Map Ta Phut）终端服务费 |
| 9 | `co2_ship_chain_fixed_cost` | C → B | 低 | IEAGHG (2020) The status and challenges of CO2 shipping infrastructures |
| 10 | `gas_production_node_allocation_TH` | C → B | 中 | TH DMF（矿物燃料司）分气田月产量 |
| 11 | `onwind_alpha_MY` | D → C / B（有风电场实测时） | 中 | Global Wind Atlas 3（DTU，已用于 gwa_mean_ws100 检查） |
| 12 | `co2_sequestration_cost_price_year` | E → B | 低 | PyPSA-Eur v2025.07.0 文档与 config 历史（co2_sequestration_cost 的价格年） |
| 13 | `gas_production_node_allocation_MY` | C → B | 中 | MY PETRONAS / Suruhanjaya Tenaga 国家能源平衡（分区域产量） |
| 14 | `biomass_potential_ID_oil_palm_trunk` | C → B | 中 | ID 种植园总署 Statistik Perkebunan Kelapa Sawit（翻种面积、树龄结构） |
| 15 | `renewable_cap_built_solar_rooftop_SG` | C → B | 中 | SG：SERIS / EMA 新加坡光伏路线图（屋顶潜力） |
| 16 | `gas_production_node_allocation_ID` | C → B | 中 | ID SKK Migas 年报（分合同区产量） |
| 17 | `renewable_cap_built_solar_rooftop_VN` | C → B | 中 | VN：MOIT / GIZ 屋顶光伏潜力研究 |
| 18 | `xb_stock_la_th_dedicated_lines` | E → B | 中 | EGAT 年报（老挝 IPP 购电与专线） |
| 19 | `lng_terminal_expansion_capex_main` | D → B | 低 | IGU World LNG Report 2024（再气化终端单位投资） |
| 20 | `share_MWh_MeOH_per_tCO2` | C → A（化学计量，EXACT 可推导） | 低 | 化学计量 CO2 + 3H2 → CH3OH + H2O：每 t CO2 产甲醇 32.04 / 44.01 t × 5.528 MWh/t ≈ 4.025 MWh |
| 21 | `th_my_line91_s_nom_2025` | C → B | 低 | EGAT / TNB 年报中 Sadao–Bukit Keteri 132 kV（或 115 kV）互联额定容量 |
| 22 | `ev_annual_km_per_vehicle` | D → C / B | 中至高 | 各国车辆年行驶里程统计（TH 陆运厅、VN、ID 交通部门调查） |
| 23 | `share_bev_dsm_restriction_value` | D → D（保留，敏感性） | 高 | 东盟充电行为调查（ADB / ICCT，若有） |
| 24 | `onwind_alpha_LA` | D → C / B（有风电场实测时） | 中 | LA Monsoon Wind（600 MW）运行数据（EDL / 开发商） |
| 25 | `share_agriculture_machinery_electric_efficiency` | D → C | 高 | FAO 农业机械化统计 |
| 26 | `share_MWh_MeOH_per_MWh_H2` | C → B | 低 | DEA Technology Data for Renewable Fuels（甲醇合成效率） |
| 27 | `share_agriculture_machinery_fuel_efficiency` | D → C | 高 | FAO 农业机械化统计 |
| 28 | `co2_ship_chain_per_km_cost` | C → B | 低 | IEAGHG (2020) The status and challenges of CO2 shipping infrastructures |
| 29 | `share_agriculture_machinery_electric_share` | D → C | 高 | FAO 农业机械化统计 |
| 30 | `renewable_cap_built_solar_rooftop_BN` | C → B | 中 | Joshi et al. (2021) Nature Communications 12:5738 全球屋顶光伏潜力网格数据（figshare） |


全部字段（所需字段、获取方式、备注）在 `W10_DOWNLOAD_CANDIDATES.csv`。

### 3.5 其余 C 级参数为何可以保留

**T5　其余 432 行的处理（`REMAINING_C_TREATMENT.csv` 按理由归并；EUR 百万）**

| 理由 | 行数 | Σ\|ΔB6\| | 最大 \|ΔB6\| | 建议的敏感性处理 |
|---|---:|---:|---:|---|
| \|ΔB6\| < 1 M EUR，影响小 | 181 | 14.5 | 1.0 | 不做单独敏感性 |
| 需求侧（第 211 项，I2 已排） | 79 | 0.0 | 0.0 | 由 I2 / W08 的需求敏感性覆盖 |
| 主算中不起作用（开关关闭、未被读取、退化区间等） | 54 | 0.0 | 0.0 | 只在对应开关打开时检查（同开关一起做敏感性） |
| 1–10 M EUR，影响小 | 41 | 142.4 | 9.8 | 不做单独敏感性；族级同向扰动覆盖 |
| 离散规则 / 开关 | 32 | 0.0 | 0.0 | 若开关对 B6 有意义，在 v4 正式批次以备选规则直接求解 |
| ≥ 10 M EUR 但未进前 30 | 21 | 465.6 | 41.9 | 族级同向扰动（如生物质成本全部 ±50 %、潜力全部低档）一次求解 |
| 与主参数同一机制（重复） | 13 | 1,508.3 | 1,419.2 | 随主参数 |
| 网络中无对应候选（DATA_PENDING → p_nom_max 0） | 9 | 0.0 | 0.0 | 补候选数据后作为新候选进入（数据升级而非敏感性） |
| 情景选择（0→1） | 2 | 3,513.3 | 3,481.8 | 作为情景（例如 FCEV / 航运氢）而非数据敏感性 |


逐行理由在 `REMAINING_C_BY_ROW.csv`。要点：生物质 151 行 |ΔB6| < 1 M，保留 C 级、不做单独敏感性；10 M 以上未进前 30 的 21 行（9 行生物质潜力、7 行其他、2 行 CO₂ 等）建议用"族级同向扰动"一次求解覆盖；需求侧 79 行由 I2 / W08 覆盖。

## 4. 重排接口

`rerank_with_results.py`（交付目录根）：

```
python rerank_with_results.py \
  --set v31_2920=<hpc_results_v31>/runs/batch5/F1,<hpc_results_v31>/runs/batch5/F2 \
  --set s07=<补充 07 export/V1>,<export/V2> \
  --reference v31_2920 --inventory C_GRADE_INVENTORY.csv --repo /home/jin/wt_v4_w10 --cache cache --out rerank_v31
```

每个运行目录需要 `*_solved.nc`、`DUALS_BY_CONSTRAINT.nc`、`NODAL_PRICES.csv`、`COMPONENT_COST_BREAKDOWN.csv`、`costs_active_research.csv`、`RUN.json`、`m12_owen/OWEN.csv`（`s2_solve.py` / `b4_batch4.py` 的导出目录都有）。提取按网络 SHA256 缓存。内存（INFERENCE）：365×24h 提取峰值 1.4 GiB，2920×3h 时段数为 8 倍，估计 6–10 GiB，本机 10 GiB WSL 偏紧，必要时在内存更大的机器上只做提取（提取结果是几十 MB 的 CSV，可拷回本机重排）。输出与本次同名的五张表和 `RERANK_SUMMARY.json`。

## 5. 产出、预算与停止条件

- 产出：`REPORT.md`、`C_GRADE_INVENTORY.csv`（+ `_META.json`）、`IMPACT_FIRST_ORDER.csv`（+ `_BY_SET.csv`）、`TOP30.csv`、`W10_DOWNLOAD_CANDIDATES.csv`、`UNRELIABLE_FIRST_ORDER.csv`、`REMAINING_C_TREATMENT.csv`（+ `REMAINING_C_BY_ROW.csv`）、`RERANK_SUMMARY.json`、`rerank_with_results.py`、`scripts/`（清单、表格、核对、报告表）、`evidence/`、`EVIDENCE.json`、`PROGRESS.md`、`LEDGER_ENTRY_DRAFT.md`、审阅包 `REVIEW_<提交>.zip` 与清单 `REVIEW_MANIFEST.csv`（逐成员 SHA256 与 CRC32）。
- 预算：求解器 0 次（上限 0）；本机计算约 3 分钟（上限 3 小时）；磁盘新增约 25 MB（上限 3 GB）。
- 停止条件核对：SHA256 相符；没有需要改仓库或求解的步骤（改油棕树干成本、WACC 模式等都写成待决问题）；没有写入 W08 的目录、worktree 或分支；导出与报告中没有许可内容或登录信息（求解日志未读取、未复制）。
- 台账：共享台账在本目录之外，按"只写本目录"的要求只写草稿 `LEDGER_ENTRY_DRAFT.md`。
