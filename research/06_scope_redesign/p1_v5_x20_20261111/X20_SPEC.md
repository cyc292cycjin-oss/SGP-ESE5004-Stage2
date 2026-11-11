# X20 实施规格（A 段）：v5 输入修订（师哥 11-11 第 1–16 条的修订落地）

- **版本：** A 段 v1，2026-11-11 SGT。执行：Claude Code，模型 Opus 5.5（claude-opus-5-5）。
- **指令：** `V5_X20_INSTRUCTION.md`，SHA256 `5126e2a7…`，`sha256sum -c` → OK。用户启动时说明第 240–245 项已勾选，没有改动方案。决策清单原文不在工作区，本规格按指令第 1 节的文字执行。
- **性质：** 只写规格，不改代码，求解器 0 次。分支 `asean/v5-x20-20261111` 从 W14 包 COMMIT `26c2e47d025fdd4e46cb278718d93aeddabbe984` 新建。worktree `/home/jin/wt_v5_x20` 在 A 段为稀疏检出（只含本目录）。
- **代码行号：** 全部是 `26c2e47d` 的行号。读取来源有两处：`p1_v5_x03_renew_20261111/cache/code`（X10 已逐成员核对，1658/1658 一致）和 `/home/jin/wt_v4_w14`（`26c2e47d..ac75354c` 只改了 `research/` 下 33 个文件）。约 40 处关键行号已逐行打印核对，见 `logs/09_spotcheck_lines.log`。注册表行号 `REG L####` 会随新增行移动，B 段一律按 `param_id` 引用。
- **数字标注：** VERIFIED = 数组、输入表或回执；EXACT = 可逐项复核的算术；INFERENCE = 机制推断或一阶估计；PROPOSED = 未执行。下文"预期变化"一律是 INFERENCE，除非另行标注。
- **复用输入：** X03 报告 `c6352f89…`、X10 报告 `d0a8cb01…`、`BUNKER_CARBON_MEMO.md` `6789576d…`，两份审阅包的 SHA 与各自记录一致。B 段要复用的 66 个文件的 SHA256 见 `evidence/REUSED_INPUTS_SHA256.txt`。GWA v4 的 22 个 tif 已按下载日志逐个核对通过（`evidence/GWA_SHA256_FROM_LOG.txt`，共 1,212,580,616 B）。

---

## 0. 总表

| 编号 | 修订 | 开关（键）与取值，**粗体为 v5 主值** | 主要改动位置 | 新数据 | 预期网络变化 | F1 / F2 / B6 预期方向 | 待决 |
|---|---|---|---|---|---|---|---|
| ①1 | 陆上风电重建（GWA 逐格点校正 + Ember 回标） | `onwind_calibration`: **`gwa_cell_ember`** / `ember_country` | `s4b_3_wind_calibration.py:111,145-149`；`s4a_profiles.py:58-64,110-121,143-153`；`s4b_3_export.py:25-51`；`s4a_layers.py:27,156-177` | GWA v4 ws100 ×11（已下载）；新 `WIND_GWA_CELL_FACTOR_V5.nc` | 288 个陆上节点×等级的 `p_max_pu`；各等级 `p_nom_max` 份额（节点总量不变） | F1↑（TH 2 级 CF 下降）、F2↑ 较小；一阶 ΔB6 −0.90 bn（只算已建容量），候选越线 45 / 120 GW，**方向不定** | Q1 |
| ①2 | 存量风电取最好等级曲线 | `existing_wind_profile`: **`best_class`** / `class0` | `s4a_fleet.py:94,99` | 无 | 13 个组件（陆上 2,267.4 + 海上 251 MW）的 `p_max_pu` | ΔE +4.4 TWh，ΔB6 约 −0.03 bn | Q12 |
| ①3 | 海上风电东盟溢价 | `offwind_asean_premium_pct`: **0** / 10 / 20 / 30 | 新函数，放在 `s4b_layers.apply_typhoon_premium`（L91-120）旁；调用点 `s2_network.py:416` 之后 | 无 | 默认不变 | +10 %：只影响 F2，ΔB6 ≤ +0.6 bn | — |
| ①4 | 光伏（主值不变）、文档、MY/ID/VN 缩放、MY 两个变体 | `solar_cap_scale`: **{MY,ID,VN: 1.0}** / 0.5 / 2；`solar_landuse_my`: **`lc100`** / `open_forest` / `oil_palm` | `s4a_layers.apply_solar_density`（L136-151）之后、等级拆分之前 | LC100 国别类面积（X03 cache）；FAOSTAT 油棕面积 | 默认不变 | MY×2 ΔB6 ≈ −3.3、ID×2 ≈ +2.3 bn（一阶，敏感性用） | Q15 |
| ①5 | 水电入流分母、×1.1 出处、记账弃水报表、VN 小水电 | `hydro_inflow_denominator`: **`operating_only`** / `all_stock`；`hydro_inflow_multiplier`: **1.1** / 1.0 | `s4c_layers.apply_hydro_inflow_normalization`（L334-427，L364-369）；新增弃水报表；`s4c_2_data.py:22` | 无新下载（VN 小水电无本地数据，见 §1.5） | LA 存量入流 +约 19 TWh；ID / MY / MM 合计 +约 20 TWh；新建水库单位入流随之提高 | F1↓ 多于 F2↓，B6 ↑ 0.5–1 bn | Q14、Q17 |
| ①6 | ID 地热上限改为储量口径 | `geothermal_cap_id`: **`reserves_2017`**（17,506 − 存量）/ `proven_probable`（5,460 − 存量）/ `resource_potential`（23,590 − 存量） | `s4b_2_candidates_data.py:46,89-93,124`；`s4b_candidates.apply_candidate_caps`（L41-112）在构建时计算 | Badan Geologi 2017 分级（X03 SOURCES C3-5） | ID 地热上限 22,421.5 → 约 16,338（30 年存量）或约 15,750 MW（40 年存量） | F1↑（F1 建 17.3 GW，会触限），F2 基本不变 → B6 ↓ 0.3–1 bn | Q16 |
| ①7 | 生物质主值不变；复核 MM；更新 IRENA 对照表 | 只有查出错误时才加 `mm_biomass_fix` | `d1_biomass.py:269-291,372-387`；`v4_biomass_potential.py` | 无 | 无错误则不变 | 无错误则不变 | — |
| ②1 | 菲律宾直流存量覆盖表 | `ph_dc_stock`: **`ngcp_tdp`** / `frozen_base` | 新 `apply_ph_dc_stock`，挂在 `s2_network.py:318`（`apply_th_my_stock` 之后） | NGCP TDP 2025–2050 PDF（允许的下载 (b)） | PH 直流存量 16,193.28 + B2B 2,000 → 1,330 MW [EXACT] | F1 +0.05 至 +1.31 bn，F2 +0.05 至 +1.25 bn，B6 ≈ 0 | Q8 |
| ②2 | OSM 国内交流去重 + cables/3 | `ac_dedup`: **`dedup_cables`** / `dedup_only` / `frozen_base` | 新 `apply_ac_dedup`，挂在 `s2_network.py:318`；新表 `AC_DEDUP_V5.csv` | OSM API way 标签（允许的下载 (a)，≤ 50 MB） | MY 国内 5 条走廊约降到 1/3–2/9；BN、TL、LA、TH、KH、VN 少量 | F1 ≤ +0.245 bn，F2 ≈ 0，B6 ∈ [−0.245, 0] | Q6 |
| ②3 | 天然气上限改为"气田现状"规则 | `gas_cap_rule`: **`field_status`** / `reserve_average` / `marketed` | `s3_layers.py:96-116`（L113 前乘系数）；新表 `GAS_CAP_FRACTIONS_V5.csv` | X10 `GAS_CAPS_BY_COUNTRY.csv` | 上限合计 2,148.53 → 1,594.77 TWh [EXACT]；PH、TL 不再建井口发电机 | F1 +0.60、F2 +0.59 bn，B6 ≈ −0.007 bn | — |
| ②4 | ID 非能源用天然气按产品增长 | `neu_gas_growth`: **`product`** / `industry_multiplier` | `m08b_demand.py:324-335,383-395`；`v4_outputs.bn_neu_methanol`（L110-132）；表链 `v4_industry.py` | 无（USGS 合成氨表、`METHANOL_PLANTS_V4.csv` 已在库内） | ID NEU 气 84.37 → 约 0 TWh（10.8 MWh/t 口径）；其他国家按同一规则 | 两个场景燃料成本各 −1.1 至 −2.4 bn，B6 小 | Q7 |
| ②5 | 寿命判定改为 ≥ 2050；存量地热 40 年 | `lifetime_boundary`: **`inclusive`** / `strict`；`geothermal_existing_lifetime`: **40** / 30 | `s4a_2_fleet_data.py:34,91`；`asset_survival.py:23`；另有 4 处副本（§1.12） | 无 | GEM 新增 200 台、5,483.4 MW；S1 冻结存量另有 7 台、2,503.1 MW 在边界上 [VERIFIED]；地热 ID 约 +0.9 GW、PH +72 MW | 两个场景成本都下降，B6 小 | **Q2** |
| ②6 | 5 台近似坐标机组逐台核对 | `gem_coord_fix`: **`verified`** / `gem` | `s4a_fleet.add_gem_fleet`（L40-）读覆盖表；新表 `GEM_COORD_CORRECTIONS_V5.csv` | 公开资料（网页阅读，不下载） | 节点归属最多改变 4.23 GW | 小 | — |
| ③1 | CO₂ 封存：主值不变、改正出处描述、低情形开关、区域外容量参数 | `s2.co2.storage_potential_case`: **`p50`** / `low` / `iea_anchor_200` / `project_ramp_377`；`co2.extra_asean_capacity_mt`: **null**（不设上限） | `s2_layers.co2_storage_caps`（L44-75）；`s4c_layers.apply_extra_asean_storage`（L763-824，L805） | X10 `CO2_STORAGE_CASES.csv` | 默认不变 | 低情形下 F1 需改道 55 / 660 / 473 Mt | Q13 |
| ③2 | DAC 投资缩放键 | `cost_scaling.DAC`: **1.0** | `baseline.yaml:472-500`；`s1_candidates.apply_cost_scaling`（L81-96） | 无 | 默认比特级不变 | — | — |
| ③3 | EV 智能充电份额 | `s2.demand.ev_smart_share`: **1.0** / 0.5 | `v3_layers.apply_ev_structure`（L303-352） | 无 | 默认不变；0.5 时多出 98 个不可调负荷，充电桩与电池减半 | 0.5 时 F1、F2 都上升，B6 方向不定 | Q5 |
| ③4 | 配电网：负荷回到低压，双向 η = 0.97 | `distribution_grid`: **`lv_pypsa_eur`** / `hv_lossless` | `s2_network` 新增一层（需求层与 EV 层之后、`s2_network.py:411` 之前） | 无 | 负荷、BEV 充电桩、热泵移到 98 条 LV 母线；配电网拆成正反 98 + 98 条 | 两个场景各 +16 至 +36 bn/a，损耗 70–97 TWh/a，B6 小 | Q3、Q4 |
| ③5 | 燃料舱碳的事后归属报表 | 无开关（只做后处理） | 新 `scripts_project/v5_bunker_attribution.py` + `s2_solve` 导出调用 | 无 | 网络不变 | 不变 | — |
| ④1 | 导出时写 `meta['run_status']`、加 `build_history` | 无开关 | `s2_solve.py:449`（`post_solve`）到 `:502`（导出） | 无 | 只改元数据 | 不变 | Q11 |
| ④2 | 局限清单 | — | 新 `LIMITATIONS_V5.md` | — | — | — | — |
| 框架 | v5 开关集、元数据、注册表 | `research.demand.v5.enabled`: false（基线文件中）；v5 构建用 `--override demand.v5.enabled=true` 打开 | 新 `scripts_project/v5_common.py`；`v4_common.py:62-100,103-110` | — | v5 关闭时与 W14 数据逐值相同 | — | Q10 |
| 门槛 | 56 时段回归的内存门槛 | — | — | — | — | — | **Q18** |
| 磁盘 | worktree 放在哪里 | — | — | — | — | — | Q9 |

**待决问题共 18 个（§6）。** 其中 Q2（冻结底座）、Q18（内存门槛）、Q3/Q4（配电网范围与扣损）、Q1（风电回标口径）会改变 B 段的做法或可行性，需要先答复。其余各题都给了推荐默认值，可以一并确认。

---

## 0.1 框架：v5 开关集（全部修订共用；待决 Q10）

项目惯例：每项修订挂开关，v5 主值取新值，旧值留作回退。参照 `lng_regas_adder`（D2b）与 `v4_adjusted_t06`（D2c）的写法（`v4_common.py:62-73,83-100,135-144,179-180`）。

1. **配置段：** 在 `configs/research/baseline.yaml` 的 `research.demand` 下新增 `v5:` 段，与 `v4:`（L515-533）并列。
   - 段内写 `enabled: false`，下面逐键列出 v5 主值，写法同 v4 段。
   - 选 `demand` 下面，是因为 B12 覆盖整个 `research` 段，G2.2 的 `SUBSET_KEYS`（`v5/gates_v6.py:34-43`）本来就含 `demand`。这样不必改 `SUBSET_KEYS` 的定义。
   - 不属于 v5 段的四个键：③1 的 `s2.co2.storage_potential_case` 新取值、`co2.extra_asean_capacity_mt`、③2 的 `cost_scaling.DAC`、③3 的 `s2.demand.ev_smart_share`。这四个键的默认值就是现状，所以与开关集无关。
2. **新模块 `scripts_project/v5_common.py`：**
   - `V5_OFF`：每个键取 `26c2e47d` 的行为；`V5_MAIN`：§0 中的粗体值；`SWITCH_VALUES_V5`。
   - `switches_v5(cfg)`：v5 关闭时返回 `V5_OFF`；打开时返回 `V5_MAIN` 并用配置段覆盖，且要求 `demand.v4.enabled = true`，否则报错。
   - 另有 `check_v5`、`switch_sha_v5`（写法同 `v4_common.switch_sha` L179-180），以及 `check_network_meta_v5`，在 `s2_network.py:465` 与 `m08a_variants.py:145` 调用。
3. **网络元数据：** 新键 `n.meta["v5_x20"]`，内容为 `switches`、`switch_sha256`、每张新表的路径与 SHA256、各层账本摘要。各层也把自己的账本写入对应的 `research_*` meta 键（参照 `research_th_my_stock`）。
4. **表级开关：** 只有 ②4 `neu_gas_growth` 改动 v4 需求表链（`research_inputs/industry_v4/out_*`）。规则如下：
   - 只有 v5 打开时，才把它并入表目录的开关身份，键名 `v5_neu_gas_growth`。这样 v5 关闭时，`out_ras` 等 5 个目录和开关 SHA `d89ccbf4…` 都保持有效，W14 网络的 `check_network_meta` 仍然通过。
   - v5 主集目录名为 `out_ras_v5`，非主集为 `out_ras_v5_<sha12>`。需要修改 `v4_common.out_name`（L108-110）和 `is_main_set`（L103-105）。
   - 其余 v5 开关只在构建层生效，不进表目录身份。
5. **回归保证：** v5 关闭时每个新层第一行就返回。B 段第一个提交之后要做一项检查：在新 worktree 按 W14 命令重建，与 W14 网络 `86f6d6a0…` / `24e835f7…` 逐组件、逐值比对，期望完全相同。meta 只允许路径和新增的 `v5_x20` 键不同，比对方法同 W14 `w14_static.py` 的 diff，构建路径的问题见记忆中的"Network meta path dependence"。
6. **override：** 新键必须先写进 baseline.yaml，因为 `--override` 只接受已有键（`s2_network.py:283-288`）。B12 回放（`v5_gates.py:166-180`）同理。取值 `"off"` / `"on"` 一律加引号（YAML 1.1）。
7. **注册表：**
   - 新脚本 `scripts_project/v5_x20_registry.py`：新行写 `fragments/v5_x20.csv`，修改已有行写 `fragments/v5_x20_corrections.csv`（整行替换），两者都追加到 `d1_registry.FRAGMENTS` / `CORRECTIONS` 末尾（`d1_registry.py:20-34`）。
   - 运行顺序沿用 D2c 的 `run_registry.sh`：`v4_registry → v4_d1 → v4_d2a → v4_d2b → v4_d2c → v5_x20 → d1_registry`。首次运行前先放一个只有表头的占位 fragment。
   - baseline.yaml 的 SHA 被 `v4_registry.py:85-86` 引用，`test_v4_registry.py:13-26` 会核对，所以 baseline.yaml 每改一次都要重跑整条注册表链。
   - C 级、REGISTERED 的数值行必须给区间；非 DATA_PENDING 的行必须有 `source_sha256`（`d1_registry.validate` L113-136）。

---

## 1. 逐项规格

每项按同一顺序写：(a) 改动位置；(b) 开关；(c) v5 主值与数据（含 SHA256）；(d) 注册表；(e) 单元测试；(f) 预期网络变化；(g) 成本与 B6 方向（INFERENCE）；(h) 依赖。

### 1.1 ①1 陆上风电重建

**(a) 改动位置**
1. 新脚本 `scripts_project/v5_wind_gwa.py`，输出 `research_inputs/renewable_v5/WIND_GWA_CELL_FACTOR_V5.nc`（175 × 146 格点，体积约 0.2 MB）和摘要 `WIND_GWA_CELL_FACTOR_V5.csv`。
   - 每个 ERA5 格点的校正系数 f(y,x) = 该格点内全部 GWA v4 ws100 像元（11 国 tif 拼接，按像元面积加权）的均值 ÷ 该格点 ERA5 2013 `wnd100m` 的时间均值。
   - GWA 有效像元覆盖不足格点面积 50 % 的格点（海域、国界外）取 f = 1。f 截断到 [0.5, 3]，同 X03 `04b_gwa_lc100.py:112`，截断的格点数要报告。
   - 与 X03 04b 的区别：04b 按（节点, 格点）取值；本步按指令"对每个 ERA5 格点"只取一个值，`alpha_cutout` 也只能表达每格点一个值。
2. 校准端 `s4b_3_wind_calibration.py`：
   - 新增参数 `--cell-factor <nc>`，在 L111 的 `w100`（风场所在格点 `cells.iy, cells.ix`）上乘 f。必须与剖面端同时加，否则 alpha 会重复补偿。
   - 其余逻辑不动：L65-86 观测 CF、L104-109 风场筛选、L124-134 二分法、L117 与 L145 的 NREL ATB2020 4 MW 校准机型、L147 的 Ember `max_capacity_gw` 权重。
   - 输出写新文件 `WIND_CALIBRATION_ALPHA_V5.csv` 和 `WIND_CALIBRATION_S4B3_V5.json`，不覆盖 v4 的 `WIND_CALIBRATION_ALPHA.csv`。
   - L151 的越界检查目前只记录、不中止，与文件说明 L14 不一致。v5 输出改为越界即中止（v4 路径保持原样）。
3. 剖面端 `s4a_profiles.py`：
   - `VARIANTS`（L58-64）新增 `calibrated_gwa_v5`，内容为 `dict(method="wind", turbine="DEA2050", correction_factor=1.0, add_cutout_windspeed=True, alpha="alpha_main", cell_factor=True)`。
   - `alpha_cutout`（L110-121）在 L119 把 `grid` 乘上 f。
   - `cut_for` 的缓存键（L143-150）加入 cell_factor；`plain()` 的排除元组（L153）加 `"cell_factor"`。
   - 新增参数 `--cell-factor`；`--alpha-table`（L128）指向 V5 表。
4. 导出：`s4b_3_export.py`（L25-51）用 `--onwind-source` 指向新剖面，输出：
   - `research_inputs/renewable_v5/profiles_calibrated_gwa_v5_c{1,3}_3h.nc`（入 git，各约 3.1 / 8.7 MB，与现有同类文件相当 [VERIFIED 现有文件大小]）；
   - 类表 `S4A_PROFILE_CLASSES_c3.csv` 追加 variant 行（不改原有行）；
   - `MANIFEST.json`、`S4B3_PROFILES_LOG_c{N}.json`。
   - 海上风电与光伏照旧取 `results_project/s4a/profiles_full_c{N}_v2` 的 pypsa_eur 结果（L32）。B 段要核对这两类列与 `profiles_calibrated_modern_*` 逐字节相同。
5. 构建：`s4a_layers.VARIANTS`（L27）新增该 variant。`apply_renewable_profiles`（L156-177）的 variant 由 `v5_common.switches_v5` 决定：`gwa_cell_ember` 对应 `calibrated_gwa_v5`，`ember_country` 对应 baseline 的 `profile_variant: calibrated_modern`（L238）。等级规则不变：3 等级（L239），节点内 [cmin, cmax] 三等分（`s4a_profiles.py:180-189`），截断 0.01（L249）。

**(b) 开关** `research.demand.v5.onwind_calibration`：**`gwa_cell_ember`** / `ember_country`。

**(c) 主值与数据**
- alpha：PH、TH、VN 按原方法在 GWA 校正后的风速上单独校准。其余 8 国取三国容量加权值，区间取三国 alpha 的最小值到最大值，登记到注册表。
- 数据：
  - GWA v4 `*_wind-speed_100m.tif` 11 个，SHA 见 `evidence/GWA_SHA256_FROM_LOG.txt`，已核对；
  - ERA5 cutout `cutout-2013-era5.nc`，7,348,721,462 B，SHA256 `eaa033a3…`（X03 `ONWIND_CELLS_LOG.json`）；
  - 作者国界 `country_shapes.geojson` `0e981608…`；
  - Ember 输入文件与 GEM GIPT 同 S4B-3（`--ember` 参数，B 段登记 SHA）。
- 回标口径见 **Q1**。按指令字面，校准时在风场格点上用格点均值校正后的风速，TH 的 alpha 仍会含"风场选在格点内最好位置"的溢价。这与"TH 不再把高 alpha 推广到全国"之间的冲突需要先定。

**(d) 注册表**
- corrections：`onwind_alpha_<C>`（11 行，REG L1633–L1643）。PH、TH、VN 为 B 级；其余 8 国为 C 级，区间 = 三国最小值至最大值。
- 新行：
  - `v5_onwind_gwa_cell_factor`：表 SHA，B 级，来源 GWA v4 + ERA5 2013；
  - `v5_onwind_calibration_switch`：flag；
  - `renewable_profile_file_calibrated_gwa_v5_c1_3h` / `_c3_3h`：文件 SHA，同 REG L1986–L1987 的写法。
- `onwind_gwa_crosscheck_s4b3`（L1646）改为 REFERENCE_ONLY，并注明 GWA 3.3 常数（`s4b_3_wind_calibration.py:38`）来源不明、不再使用。

**(e) 单元测试**（新文件 `tests/research/test_v5_x20_wind.py`，另修改已有测试）
1. f ≡ 1 时，`calibrated_gwa_v5` 剖面与 `calibrated_modern` 逐值相同（玩具 cutout）。
2. 校准后，PH、TH、VN 风场格点的模型 CF 等于 Ember 观测值，|差| < 1e-6。
3. 8 国 alpha 等于三国的 `max_capacity_gw` 加权值；区间等于三国的最小值与最大值。
4. 各节点三个等级的潜力之和等于节点潜力（同 `s4a_profiles.py:189` 的断言）。
5. 已有测试需要改：
   - `test_s4a_profiles.py:41` 的变体集合；
   - `test_s4b_3.py:21-23` 的加权 alpha 改为按所用表读取；`:59-61` 的 added == 647、陆上 `p_nom_max` 合计 8916.8e3 保持不变，因为分级只改份额；
   - `s4i_static_audit.py:388` 写死的 alpha（0.910 / 1.294 / 0.995 / 1.046）改为读当前 alpha 表。

**(f) 预期网络变化**
- 288 个陆上"节点 × 等级"生成器的 `p_max_pu`。
- 各等级 `p_nom_max` 份额随重新分级改变，节点总量不变。
- 海上与光伏不变。
- 逐格点校正、未回标时的等级 CF 量级（X03 选项 3，INFERENCE）：

  | 国家 | 2 级 CF：现模型 | 逐格点校正后（未回标） |
  |---|---|---|
  | TH | 29.2 % | 19.6 % |
  | VN | 23.2 % | 28.0 % |
  | PH | 29.1 % | 28.6 % |
  | LA | 12.7 % | 15.5 % |
  | MM | 12.5 % | 15.8 % |
  | ID | 11.8 % | 6.5 % |
  | MY | 13.0 % | 7.4 % |

- 回标后各国水平按 alpha 整体平移。

**(g) 成本方向**
- F1 的陆上风电 75 % 在 TH（51.24 GW）[VERIFIED X03]，TH CF 下降使 F1 成本上升；F2 也上升，但幅度较小。
- 只算已建容量的一阶 ΔB6 为 −0.90 bn。另有 45 GW（F1）/ 120 GW（F2）候选机组越过盈亏线，所以 **B6 方向不定**，量级可能超过 1 bn。
- 受益排序：TH 下降，VN、PH、MM、LA 上升。

**(h) 依赖：** 先做 ①1，再做 ①2，因为 c2 曲线随 ①1 改变。B 段合理性检查见 §5 第 4 项第 (e) 条。

### 1.2 ①2 存量风电取节点最好等级

- **(a) 改动位置：** `s4a_fleet.py:94`。
  - 陆上取 `f"{node} onwind-2025 c{ncls-1}"`；海上取同样命名规则下 `offwind-ac` 的最高等级（`s4a_layers.py:112` 的命名）。最高等级不存在时，依次退到次高等级，并写入账本 `led["profile_class"]`。
  - 现行代码在候选缺失时只记 `skipped`（L95-96）。v5 改为列出并计数。
- **(b) 开关：** `existing_wind_profile`：**`best_class`** / `class0`。
- **(c) 主值：** 节点最好等级（3 等级时为 c2）。不需要新数据。
- **(d) 注册表：** 新行 `v5_existing_wind_profile_rule`（规则，C 级，依据 X03 §2）。
- **(e) 测试：**
  - 玩具网络：`best_class` 时存量风电取最高等级列，`class0` 时与 W14 逐值相同；
  - 最高等级缺失时退到次高等级。
- **(f) 网络变化：** 13 个组件（陆上 11 个 2,267.4 MW，海上 2 个 251 MW）[VERIFIED X03]。按 v4 曲线，组件 CF 变为 ID 34.9 %、PH 27.8–36.0 %、VN 21–45 %；①1 之后会再变。
- **(g) 成本方向：** ΔE 约 +4.4 TWh；F1 / F2 成本约 −168 / −202 M；ΔB6 约 −0.03 bn。
- **(h) 依赖：** 依赖 ①1（曲线）和 ②6（Truong Son 节点可能从 LA2 1 改为 LA2 2）。另见 Q12：存量光伏同样复制 `<node> solar-2025`（L94），也就是 0 级曲线。这不在第 1 节的修订范围内，是否一并处理需要答复。

### 1.3 ①3 海上风电东盟成本溢价

- **(a) 改动位置：** 新函数 `apply_offwind_asean_premium(n, cfg)`，放在 `s4b_layers.py` 的 `apply_typhoon_premium`（L91-120）旁边。
  - 作用对象：全部可扩建的 `offwind-ac` / `offwind-dc` / `offwind-float` 生成器（排除 `asset_role == existing_survivor`）。
  - 做法：`capital_cost × (1 + pct/100)`。
  - 调用点：`s2_network.py:416`（台风溢价）之后。此时成本层（L403）、`cost_scaling`（L415）、台风溢价都已执行，几个系数按乘法叠加，在账本中写明。
- **(b) 开关：** `offwind_asean_premium_pct`：**0** / 10 / 20 / 30（数值型，避开 on/off 布尔解析）。
- **(c) 主值：** 0，即不变。溢价乘在整个 capital_cost 上，含站和接入，与台风溢价的作用范围一致（`s4b_layers.py:116`）。
- **(d) 注册表：** 新行 `v5_offwind_asean_premium`，SENSITIVITY，取值 10 / 20 / 30，C 级。来源为 X03 §3.4 和 World Bank 越南路线图（二手，X03 SOURCES A5-1、A5-2）。
- **(e) 测试：** 玩具网络 +10 % 时只改可扩建海上机组；pct = 0 时比特级不变。
- **(f) 网络变化：** 默认无。
- **(g) 成本方向：** 只有 F2 建海上风电（VN 23.04 GW）[VERIFIED X03]。+10 % 时 ΔObj_F2 ≤ +0.6 bn，ΔB6 ≤ +0.6 bn。

### 1.4 ①4 光伏

1. **文档：** corrections `renewable_capacity_per_sqkm_solar`（REG L1941，`fragments/m08a.csv`）只改描述文字，数值 5.1 不变。写明：5.1 MW/km² 是"摊到全部可用地上的平均装机密度"，已含只用一小部分可用地的折减（PyPSA-Earth 4.6 = 45.6 × 10 %）；5.1 / 4.6 = 1.1087 只是两个模型密度的比值，任何来源中都没有这个系数（X03 §4.1）。
2. **缩放开关：**
   - `solar_cap_scale`：`{MY: 1.0, ID: 1.0, VN: 1.0}`，每国可取 0.5 / 1.0 / 2.0。
   - 实现：新函数，在 `s4a_layers.apply_solar_density`（L136-151，于 L164 调用）之后、等级拆分（L192-218）之前，把该国（按 `n.buses.country`）地面光伏 `carrier == "solar"` 的 `p_nom_max` 乘以系数。屋顶光伏与存量不变。
3. **MY 变体** `solar_landuse_my`：**`lc100`** / `open_forest` / `oil_palm`。
   - `open_forest`：把 LC100 121–126 类计入可用地，MY 上限 86.4 → 198 GW（X03 §4.5 [E]），国别系数 = 198 / 86.4。
   - `oil_palm`：把 FAOSTAT 2019–2023 油棕收获面积 51,700 km² × 5.1 MW/km² 计入，MY 上限 86.4 → 约 350 GW（×4.1，X03 §4.4 [E]）。
   - 两个变体的推荐做法都是不重算栅格，国别增量按现有各节点的光伏上限比例分配（INFERENCE，见 Q15）。开阔森林也可以用本机的 LC100 2019 栅格（X03 已用，WSL 作者链 `data/copernicus/PROBAV_LC100_…tif`）逐节点计算，代价是额外的栅格计算。油棕没有本地种植园栅格，只能按比例分配。
   - 数据：X03 `cache/gwa_lc100/lc100_country_class_area.csv`（SHA 在 `evidence/REUSED_INPUTS_SHA256.txt`）。油棕面积用库内 FAOSTAT 文件；没有本地文件则列入 `DOWNLOAD_CANDIDATES.csv`，该变体暂不实现。
4. **注册表：** 新行 `v5_solar_cap_scale_{MY,ID,VN}`（SENSITIVITY，0.5 / 2）、`v5_solar_openforest_MY`、`v5_solar_oilpalm_MY`（系数与面积，C 级）。`renewable_landuse_rule_solar`（L1973）的描述补一句：开阔森林已实现为开关。
5. **测试：** 默认比特级不变；×2 时只改该国地面光伏；变体系数与表一致；等级潜力之和守恒。
6. **网络变化与成本：** 默认不变。敏感性的一阶值（X03 §4.5）：

   | 情形 | ΔB6 |
   |---|---|
   | MY ×2 | ≈ −3.3 bn |
   | MY ×0.5 | ≈ +1.65 bn |
   | ID ×2 | ≈ +2.3 bn |
   | ID ×0.5 | ≈ −1.14 bn |

   这些开关供 X21 使用。

### 1.5 ①5 水电

1. **入流分母（`s4c_layers.py:364-369`）：**
   - 现行：`target_u = T * caps / caps.sum()`，`caps` 是网络里全部 `hydro existing` StorageUnit 加 `ror existing` Generator 的 p_nom（L351），含在建机组。
   - v5：每国单位入流 u_c = T_c ÷ caps_op_c。caps_op_c = 该国**已投运**机组的容量，口径见 Q14：冻结底座的作者机组，加上 meta `existing_unit_components` 中 `gem_status == operating` 且 `commissioning_year ≤ 2025` 的机组。
   - 每个存量水电和径流组件的入流 = u_c × p_nom × 现有形状。所以在建机组"按同国单位入流另加入流"；组件内混有投运与在建机组时，自然按 p_nom 计。
   - 径流照旧截断到 1（L389）。v4 D2A 重分类、入流为 0 的水库不计入分母（L351 之外另行排除）。
2. **新建水库：** 现行代码（`s4c_layers.py:411-416`）沿用"本国存量每 MW 入流"，v5 下自动变为 u_c。约束 `install_new_hydro_inflow_tie`（`s4b_candidates.py:189-201`）不改：它用 `inflow / p_nom_max`，所以入流和上限必须同步写入。
3. **×1.1：**
   - 来源：`s4c_2_data.py:22` 的常量 `MULTIPLIER = 1.1`，依据是作者链 pypsa-asean `config.default.yaml:445` `multiplier: 1.1`。PyPSA-Earth 默认值待查。B 段在本地作者仓库 `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean` 用 `git log -S "multiplier: 1.1"` 和 blame 找引入的提交与说明，再对照 PyPSA-Earth 文档（网页阅读）。
   - 找不到书面理由时登记为 C 级，区间 1.0–1.1。
   - 主值保留 1.1；开关取 1.0 时，T_c 除以目标表的 `multiplier` 列。目标表 `HYDRO_NATIONAL_TARGET_S4C2.csv` 不改。
4. **弃水报表：**
   - 新函数 `hydro_spill_report(n)`，放在 `s2_solve.py` 的导出流程里（与 `co2_flows`，L120-151，同一位置，L456 附近），写出 `HYDRO_SPILL.json`。
   - 内容：每国存量水库的真实弃水；新建水库（`research_new_hydro_inflow_tie` 列表）的"记账项"Σ 入流 × (1 − p_nom_opt / p_nom_max) 与"真实弃水"（总弃水减记账项）分列。
   - 另写一个独立脚本，对 v4 2920 已解网络复跑，作回归：须复现 X03 的 F1 527.0 / 519.9 / 7.1 TWh、F2 528.9 / 521.5 / 7.4 TWh [VERIFIED X03]。读网络前按内存门槛检查。
5. **VN 小水电：** 库内没有单一来源的分厂数据（只有 PDP VIII 原文一句，`potentials_v5/S4A3_WEB_QUOTES.json:44`）。EVN / IHA 的分厂数据不在允许下载的两类文件之内，所以写入局限清单，并列入 `DOWNLOAD_CANDIDATES.csv`（Q17）。
6. **开关：** `hydro_inflow_denominator`：**`operating_only`** / `all_stock`；`hydro_inflow_multiplier`：**1.1** / 1.0。
7. **注册表：**
   - corrections：`hydro_inflow_normalization_main`（L1195）描述改为"分母 = 已投运机组；在建机组按同国单位入流另加"。
   - 新行：`v5_hydro_inflow_denominator_rule`、`v5_hydro_inflow_multiplier_source`（1.1，C 级或按查到的出处定级）、`v5_hydro_spill_bookkeeping_rule`。
8. **测试：**
   - 玩具网络含投运和在建两类机组：单位入流 = T / caps_op；`all_stock` 时与 W14 相同；1.0 开关等于目标除以 1.1。
   - 弃水报表在玩具解上分开记账项和真实弃水。
   - `test_s4c_2.py:20-23` 不变；`s4i_static_audit.py:390-404` 的比值核对改为同一分母规则。
   - 那里分子含 PHS、归一化本身不含 PHS，口径不一致；这个问题列入局限，不在本步改。
9. **预期变化：**
   - LA 存量入流 39.4 → 约 58 TWh（+4.55 GW × 0.47 × 8,760 h ≈ +18.7 TWh）。
   - ID / MY / MM 合计 +约 20 TWh。
   - VN 在建只有 193 MW，变化小。
   - LA 新建水电单位入流从约 0.31 升到约 0.47，入流价值约 15 万 EUR/MW/a，仍低于投资。
   - F1 成本下降多于 F2，B6 ↑ 0.5–1 bn（X03 §5.5）。
10. **依赖：** ②5（水电寿命 100 年，边界规则对水电基本没有影响）；②6（Upper Yeywa 280 MW 可能从 MM2 5 改到 MM2 14，影响节点入流形状）。

### 1.6 ①6 地热上限（储量口径）

1. **主值：** ID 新建上限合计 = 2017 年全部储量 17,506 MW − ID 存量地热（以构建网络中的 `geothermal existing` 为准）。
   - 17,506 = 可能 12,046 + 概略 2,493 + 证实 2,967（Badan Geologi 2017，X03 SOURCES C3-5；原文单位误写为 GW）。
   - 开关 `proven_probable`：5,460 − 存量，"减存量"沿用主值的写法（Q16）。
   - 回退 `resource_potential`：23,590 − 存量，即现状。
2. **实现：** 现行上限固化在 `CANDIDATE_CAPS_S4B2_BY_NODE.csv` 里，算法是"潜力 − 某次构建网络的存量"（`s4b_2_candidates_data.py:124`）。存量会随 ②5 的寿命开关变化，所以 v5 改为**构建时计算**：在 `s4b_candidates.apply_candidate_caps`（L41-112）中，按 v5 开关取 ID 潜力，减去当前网络 ID 的 `geothermal existing` p_nom 之和，再按现有 BY_NODE 表中各 ID 节点的份额分配。这样不论寿命开关取几，"上限 + 存量 = 储量"都恒成立。其他国家的行不动。
3. **PH 原址重建上限：** `s4b_2_candidates_data.py:89-93` 写死了 `Start year + 30 <= 2050`，与 ②5 的寿命开关和边界规则不一致。v5 改用参数（寿命取 ②5 开关，边界取 ≥ 规则），同时重生成 BY_NODE 表中 PH 的行，写新文件 `CANDIDATE_CAPS_S4B2_BY_NODE_V5.csv`。
4. **其他国家的上限来源（逐一写明，数值不变）：**
   - PH 3,124 MW = GEM 管道 1,297 + 2050 年前退役机组原址重建 1,827（REG L355；对照行 L1701–L1703、L1671）；
   - MY 229 MW = SEDA MyRER，半岛 162 + 沙巴 67（L354，来源 L1700 `potential_geothermal_MY_myrer`）；
   - VN 45 MW = GEM 管道（L359；L1707 DATA_PENDING，L1708）；
   - 其余国家 0。
5. **注册表：**
   - 新行 `potential_geothermal_ID_reserves_2017`：17,506，数值 B 级；用作 2050 上限是 C 级，区间 5,460–23,590。
   - 新行 `potential_geothermal_ID_proven_probable_2017`：5,460，SENSITIVITY。
   - corrections：`candidate_cap_geothermal_ID`（L350）描述改为构建时计算。
6. **测试：**
   - 不论寿命取 30 或 40，Σ ID 上限 + ID 存量 = 17,506（以及 5,460、23,590）；
   - PH 重建量随寿命参数变化；
   - `resource_potential` 时与 W14 相同。
7. **预期变化：**
   - ID 上限 22,421.5 → 17,506 − 1,168.5 = 16,337.5 MW（30 年存量 [EXACT]）。40 年存量下约 15,750 MW（X10 按 GIPT 算存量 +920 MW，INFERENCE）。
   - F1 建了 ID 17,309.5 MW [VERIFIED X03]，会触限。F2 建 10,718 MW，不受影响。
   - B6 ↓ 0.3–1 bn，ID 受益下降。
8. **依赖：** ②5（存量）。

### 1.7 ①7 生物质（主值不变；复核 MM）

1. **复核步骤**（新脚本 `scripts_project/v5_mm_biomass_review.py`，只读）：按 `d1_biomass.py` 的链条（L269-291）逐品类重算 MM：FAOSTAT 2019–2023 均值 × 1.1716 × IRENA R-3 残余系数（五国众数）× 收集率 0.25 / 0.90 × (1 − 饲料份额 0.290) × 15 GJ/t。再与 IRENA 2022 的 33.2 PJ（`BIOMASS_CROSSCHECK_IRENA.csv` MM 行，比值 12.10）逐品类对照，找出差异来源，例如稻草与稻壳、"其他作物"、木材加工残余。
2. **"确有错误"的判定：** 只认算术、单位、数据映射或重复计算类错误。方法口径不同不算错误，例如 IRENA 不含某品类、收集率不同。
   - 查出错误：按同一方法改正，加开关 `mm_biomass_fix`：`corrected` / `v4`，改动 T06 表链（`v4_biomass_potential.py`）。
   - 只是口径差：不改，写进报告和局限，由用户决定。
3. **更新 `BIOMASS_CROSSCHECK_IRENA.csv`：** 现表由 `d1_biomass.py:372-387` 基于 v3 表生成，已过时（例如 ID 3,722 PJ）。v5 新写 `BIOMASS_CROSSCHECK_IRENA_V5.csv`，按当前 T06 表与网络实际池子计算，旧表保留。
4. **预期变化：** 无错误时不变。

### 1.8 ②1 菲律宾直流存量覆盖表

1. **实现：** 新函数 `apply_ph_dc_stock(n, corridors, cfg, repo)`，放在新模块 `scripts_project/v5_layers.py`。
   - 写法照 `s4f_layers.apply_th_my_stock`（L132-162），在 `s2_network.py:318` 紧接其后调用。
   - 这样之后的扩建上限（L409，自动等于新存量 + 20,000）、换流站规则（L410）、损耗孪生（L411，继承新值）都会自动使用新存量 [VERIFIED 调用顺序]。
2. **表 `research_inputs/corridors/PH_DC_STOCK_V5.csv`：** 列 = `component_type, component, action, frozen_base_mw, corrected_mw, grade, basis, ngcp_tdp_page`。

   | 元件 | 两端 | 冻结值 MW | 动作 | 新值 MW | 依据（NGCP TDP 2025–2050 页码，X10 已记录，B 段下载后复核） |
   |---|---|---|---|---|---|
   | `151018428-1_0+2` | PH_Visayas10 – PH_Luzon5 | 3,146.6 | set_capacity | 440 | Leyte–Luzon HVDC，p.43-44、51 |
   | `1006176982-1_0+1` | PH_Visayas10 – PH_Visayas7 | 2,573.3 | set_capacity | 440 | 同上 |
   | `convert_935_1501`（B2B 占位） | PH_Visayas10 – PH_Visayas7 | 2,000 | set_capacity 0，不可扩（Q8） | 0 | 占位换流器（`base_network.py:671`） |
   | `100000087-1_0+1` | PH_Luzon5 – PH_Luzon9 | 2,376.74 | set_capacity 0，保持可扩 | 0 | 经民都洛，2025 年不存在，p.35-36、39-40、51-52 |
   | `100000092-1_0+1` | PH_Visayas7 – PH_Luzon9 | 2,376.74 | set_capacity 0，保持可扩 | 0 | 同上 |
   | `1076672675-1_0+4` | PH_Mindanao6 – PH_Visayas7 | 5,719.9 | set_capacity | 450 | MVIP，p.3、5 |

   - 合计：5 条直流 16,193.28 + B2B 2,000 = 18,193.28 → 1,330 MW [EXACT]。
   - Leyte–Luzon 在模型中被拆成经 Visayas10 直流结点的两段，所以两段各 440 MW。
3. **冻结值核对：** TH-MY 函数核对的是 `p_nom_min`（L147）。不可扩的 B2B 的 `p_nom_min` 可能是 0，所以本函数对可扩元件核 `p_nom_min`，对不可扩元件核 `p_nom`，不符即报错。
4. **"移除 B2B"的实现（Q8）：** 改为 p_nom = 0 且不可扩，不删除元件。理由：删除后 `dc_to_ac`（`sector_adapter.py:52-59`）不再映射 PH_Visayas10，管道拓扑与候选结构检查可能失败（`s2_network.py:200,211,224`；`v5_gates.py:142`）。零容量在电气上等同于移除。
5. **连带：**
   - S4J-3 证据表 `DC_CONVERTERS_S4J3.*`、`test_s4j_3.py:52`（断言 `convert_935_1501` p_nom == 2000）只对 v4 构建成立，测试改为按开关判断。
   - `LOSS_LINKS_S4J2.csv`、`COMPONENT_SUBSEA_SHARE_S4C1.csv` 是证据或成本表，与容量无关，B 段核实。
   - PH_Luzon9（民都洛结点）的两条存量都变成 0。B 段要检查该母线上的负荷与本地机组：如有负荷，就由候选扩建或本地发电满足（民都洛 2025 年本来就未并网），并核实可行性。
6. **数据：** NGCP TDP 2025–2050 PDF，属于允许的下载 (b)，≤ 50 MB。下载到 `downloads/ngcp/`，记录 URL、字节数、SHA256 与页码截取。
7. **注册表：** `v5_ph_dc_stock_switch`（flag）；`ph_leyte_luzon_hvdc_2025`（440，A 级，NGCP）；`ph_mvip_2025`（450，A 级）；`ph_mindoro_dc_2025`（0，SOURCE_ZERO）；`ph_b2b_placeholder_2025`（0，SOURCE_ZERO）。
8. **测试：**
   - 表的冻结值合计 18,193.28，新值合计 1,330；
   - 玩具网络 set_capacity / 冻结值不符时报错；
   - 损耗孪生继承新值；`frozen_base` 时与 W14 相同。
9. **预期：** F1 +0.054 至 +1.311 bn，F2 +0.053 至 +1.254 bn，B6 一阶 −0.001 bn（X10 R2）。F1 / F2 可能在 Luzon–Visayas 方向新建直流（年化 61–106 kEUR/MW）或增加本岛发电。

### 1.9 ②2 OSM 国内交流重复记录

1. **识别**（新脚本 `scripts_project/v5_ac_dedup_data.py`）：
   - 输入：`data/osm-plus-prebuilt/0.1.1/all_lines_build_network.csv`。
   - 重复键：(way = `line_id` 中 "-" 之前的部分, min(bus0, bus1), max(bus0, bus1), voltage, round(length))，同 X10 `04b_x10_ac_reconstruct.py:43-46`。
   - 对 11 国全部扫描。X10 结果：331 组，其中 MY 294 组 / 885 行 [VERIFIED X10]。
2. **cables 标签**（允许的下载 (a)）：
   - 对重复组涉及的全部 way，用 OSM 官方 API `GET /api/0.6/ways?ways=<id,…>.json` 分批读取标签（每批 ≤ 100 个 id）。
   - 记录每批的 URL、字节数、SHA256 与时间，合计 ≤ 50 MB（预计 < 2 MB）。不带个人信息，User-Agent 用通用名称。
   - 有 `cables` 且能被 3 整除：回路数 = cables / 3。取不到或不能整除：维持去重后的值，并在表中标明 `cables_source = not_available`。
3. **映射到模型走廊：**
   - OSM 母线按点落在 `research_inputs/renewable_v5/regions_onshore.geojson`（100 节点母线区域）的哪个区域归到模型节点，限同国；落在区域外的用最近节点，并标记。
   - 这比 X10 的"最近聚类中心"近似更可靠：区域是基础母线 Voronoi 区按 busmap 合并而成。本机没有 `elec_s_100` 的 busmap，作者链只有 tutorial `elec_s_50` 的，已核实（`logs/06_author_chain.log`）。
   - 单行容量 s = √3 × i_nom(线型) × kV × 回路数，线型取 pypsa-earth 环境的 `line_types.csv`（同 X10）。
4. **系数法：**
   - 对每条模型国内线（节点对），计数容量 = 映射到它的 OSM 行 s 之和；去重容量 = 去重、按 cables 重算后的 s 之和；系数 = 去重 ÷ 计数；新 s_nom = 冻结 s_nom × 系数。
   - 只对重建核对通过的走廊施加：计数容量 ÷ 模型 s_nom 在 [0.8, 1.25] 内。不通过的走廊不改，列入局限并报告，例如 X10 中线 94 Sabah4 0 – Sarawak4 2 的重建值是模型的 140 倍。
   - 跨境线（23、91、92）不在本项范围。
5. **施加：** 新函数 `apply_ac_dedup`（`v5_layers.py`），在 `s2_network.py:318` 处、`apply_ph_dc_stock` 之后调用，读表 `research_inputs/corridors/AC_DEDUP_V5.csv`，列 = `line, bus0, bus1, country, frozen_s_nom, counted_mw, dedup_mw, factor, new_s_nom, num_parallel_new, osm_ways, cables_source, recon_check, grade`。
   - `s_nom` 与 `s_nom_min` 同时改：扩建上限用 `s_nom`（`s4f_layers.py:88`），跨境检查用 `s_nom_min`。
   - 阻抗处理见 Q6，推荐 S4G-1 的做法（`s4g_layers.py:66`）：按 `s_nom / (√3 · v · i_nom)` 重算 num_parallel，再由线型重算 x / r / b。这样回路数减少后 KVL 阻抗相应增大，与物理一致。
   - 不把任何国内线改成零容量可扩（`s4h_layers.py:82-85` 会报错）。
6. **开关：** `ac_dedup`：**`dedup_cables`** / `dedup_only` / `frozen_base`。
7. **注册表：** `v5_ac_dedup_switch`；每条改动的走廊一行 `v5_ac_dedup_<line>`（新 s_nom；去重部分 B 级，cables 部分 B 级，取不到 cables 的行注明）；`v5_osm_api_way_tags`（请求日志 SHA）。
8. **测试：**
   - 玩具 CSV 的重复分组；
   - 系数施加与 s_nom_min 同步；
   - 重建核对不通过的走廊不改；
   - `frozen_base` 时与 W14 相同；
   - 改阻抗时 x × num_parallel 守恒。
9. **预期**（X10，INFERENCE）：

   | 走廊 | 冻结 s_nom MW | 去重后 MW | 再按 cables（约 2/9） |
   |---|---|---|---|
   | MY_Peninsular2 0–1 | 54,241 | 18,079 | 约 12,050 |
   | Sabah4 0–1 | 9,216.7 | 3,071.9 | — |
   | Sarawak4 0–1 | 11,060 | 4,926 | — |
   | Sarawak4 0–2 | 10,529 | 4,999 | — |

   - F1 中 Peninsular2 0–1 峰值潮流 22.3 GW，会受约束，补建上界 +0.245 bn；F2 ≈ 0；ΔB6 ∈ [−0.245, 0]。
   - 阻抗改变后潮流重新分配，KVL 环流随之改变，影响 M12 / Owen 的环路项。B 段 56 时段回归中要报告 Owen 符号。

### 1.10 ②3 天然气上限（气田现状规则）

1. **实现：** 不改 v4 上限表 `GAS_PRODUCTION_CAPS_2050_V4.csv`。理由：改表会连带逃逸排放因子（`v4_gas_caps.py:42-44`）和表目录开关 SHA。
   - 新表 `research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv`，列 = `country, rule_a_reserve_average, rule_b_field_status, source, note`。
   - 在 `s3_layers.py:113`（`cap = float(r.cap_mwh_per_year)`）处乘该国系数。cap ≤ 0 时沿用 L115 的现有逻辑：不建井口发电机，逃逸行不适用，也就不会产生零右端项的年上限行，零松弛检查不受影响。
   - 逃逸因子仍按每 MWh 计，绝对逃逸量随产量下降。
2. **系数**（X10 `GAS_CAPS_BY_COUNTRY.csv` 第 32–33 列 [VERIFIED]）：

   | 国家 | 规则 B（主值） | 规则 A（开关） | 新上限 TWh（规则 B） |
   |---|---|---|---|
   | BN | 1 | 0.550868 | 106.66 |
   | ID | 1 | 0.554702 | 593.56 |
   | MM | 0.20 | 0.697472 | 36.93 |
   | MY | 1 | 0.374610 | 714.61 |
   | PH | 0 | 0.076246 | 0 |
   | TH | 0.128852 | 0.128852 | 46.92 |
   | TL | 0 | 0 | 0 |
   | VN | 1 | 1 | 96.09 |
   | 合计 | — | — | 1,594.77（规则 A 930.79） |

3. **开关：** `gas_cap_rule`：**`field_status`** / `reserve_average` / `marketed`（= v4）。
4. **注册表：** `v5_gas_cap_rule_switch`；`v5_gas_cap_fraction_<CC>` 共 8 行，C 级。来源为 X10 SOURCES：EI Statistical Review 2025、BP 2021 储量、World Bank 2023（MM）、Malampaya 延寿至约 2034 年（PH）、Bayu-Undan 2025-06 停产（TL）。系数 0 的国家状态记 SOURCE_ZERO。
5. **测试：**
   - 玩具网络：系数施加；系数 0 时不建井口发电机，`external_annual_caps` 中没有该国；
   - B15（`v5_gates.py:363-375`）与 D10（`gates_v6.py:200-204`）对缺席国家不报错；
   - `marketed` 时与 W14 相同。
6. **预期：** F1 +0.60、F2 +0.59 bn，ΔB6 −0.007 bn（X10 一阶）。缺口主要由 LNG 填补，每 MWh 贵 1–2 EUR。
7. **依赖：** ②4，ID 天然气需求下降后，ID 上限可能不再绑定。

### 1.11 ②4 ID 非能源用天然气按产品增长

1. **规则：** 对每国：NEU 天然气_2050 = max(0, NEU 天然气_2019 − 合成氨_2019 × 10.8 MWh/t（只计气头装置）− 甲醇_2019 × e_MeOH) × m_ind。
   - 合成氨与甲醇在 v4 中已作为产品负荷单独建模：合成氨负荷 × 5.166 MWh/t（`s3_0_industry.py:335-337`）；甲醇见 `v4_products.methanol_items`（L146-157）。所以它们的原料气不应再留在 NEU 行里。
   - 先例：BN 甲醇从 NEU 气中扣除（`v4_outputs.bn_neu_methanol`，L110-132）。
   - 现行做法：NEU_2019 × m_ind − 合成氨_2050 × 10.8（`m08b_demand.py:383-395`），其中 m_neu = m_ind（L335，ID 3.2034）。
2. **实现：**
   - 在 `m08b_demand.py` 的 DFX F2.4 块（L383-395）增加 `product` 分支：读 2019 合成氨（`ammonia_production.csv` 2019 列，`output_bases()` L161-197）和甲醇（`METHANOL_PLANTS_V4.csv`）。
   - 表链用 `v4_industry.py --config-switches` 重生成 `industry_v4/out_ras_v5`（表级开关见 §0.1 第 4 条）。
   - 只有 NEU 行改变，工艺排放与原料碳（`v4_outputs.py:137-160`）跟随 NEU 行。
3. **合成氨单耗：** 主值 10.8 MWh/t（与 DFX F2.4 一致）。ID 结果：2019 年 NEU 71.8 TWh − 合成氨 80.0 TWh → 0，所以 2050 年 NEU 84.37 → 约 0 TWh，消除 84.4 TWh。若改按 BAT 7.8 MWh/t，消除约 38.9 TWh。指令写的是"消除 39–84 TWh 的虚增"，取哪一端见 Q7。
4. **其他国家按同一规则检查：** B 段逐国输出表 `NEU_GAS_PRODUCT_RULE_V5.csv`，列 = NEU_2019、合成氨气头 2019、甲醇 2019、残差、2050 旧值 / 新值。
   - MY 有 Labuan / Sarawak 甲醇，可能下降。
   - TH 的 110.8 TWh 是石化原料，不是合成氨或甲醇，残差不变。
   - VN 合成氨部分为煤头，只扣气头部分。
5. **需先核实的前提（Q7）：** NEU 是否在 RAS 锚定的 TFEC 总量之内。
   - 若 NEU 只是"按工业乘数随行"（L324、L335 显示 m_neu = m_ind = 工业锚 / 2019 工业能耗），改 NEU 不影响锚。
   - 若 TFEC 锚含 NEU，减少 NEU 会改变 RAS 解，B 段停下报告。
6. **开关：** `neu_gas_growth`：**`product`** / `industry_multiplier`。
7. **注册表：** 新行 `v5_neu_gas_product_rule`（规则）、`v5_neu_gas_2050_<CC>`（新值）。corrections `demand_neu_2050_ID`：现存 v3.1 的 2.61861，与 v4 的 3.2034 不一致，改正。
8. **测试：** ID 残差为 0 时 NEU 为 0；TH 不变；`industry_multiplier` 时与 `out_ras` 逐字节相同；需求账本 B8 与 ATS 锚（`s2_layers.py:1171-1172`）通过。
9. **预期：** ID 天然气需求 −84.4 TWh（10.8 口径），ID 上限绑定放松，LNG 进口减少。两个场景燃料成本各约 −1.1 至 −2.4 bn，B6 小。

### 1.12 ②5 存量寿命（≥ 2050；地热 40 年）

1. **规则所在的全部位置**（agent 全树检索，已抽查 `s4a_2_fleet_data.py:34,91`、`asset_survival.py:23`）：

   | 位置 | 现行 | v5 |
   |---|---|---|
   | `s4a_2_fleet_data.py:91` | `op.retire_year > 2050` | `>=` |
   | `s4a_2_fleet_data.py:34` | `LIFETIME["Geothermal"] = 30` | 按开关取 40 / 30 |
   | `asset_survival.py:23` | `commissioning<=year<retirement` | `<=retirement`（见 Q2） |
   | `s4b_1_fleet_data.py:49` | `assert (rows.retire_year > 2050).all()` | `>=` |
   | `s4b_2_candidates_data.py:91` | `Start year + 30 <= 2050`（PH 地热重建） | 参数化（§1.6 第 3 条） |
   | `selected_closure.py:119` | `if y+life<=year:` 判退役 | 改为 `<`，同 Q2 |
   | `audit_residual_sources.py:24` | `>2050`（只审计） | `>=` |
   | `s2_layers.py:198-199` | 判断文字 "+ 30 a > 2050" | 按开关写文字 |

2. **冻结底座问题（Q2，必须先答复）：** 本步读了 `results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json`（3,079 条记录）。其中退役年恰好等于 2050、现行规则下为 NOT_ACTIVE 的有 7 台、2,503.1 MW [VERIFIED，`logs/10_s1_boundary.log`]：

   | 国家 | 技术 | 台数 | MW |
   |---|---|---|---|
   | SG | CCGT | 2 | 800.0 |
   | TH | CCGT | 1 | 670.0 |
   | MY | CCGT | 2 | 507.0 |
   | ID | CCGT | 2 | 466.1 |
   | MM | Hard Coal | 1 | 60.0 |

   - `asset_survival.py:23` 在 assembly 阶段使用（`unit_asset_survival.py:36`、`apply_selected_stock.py:43`、`integrate_surviving_assets.py:66`）。改它就要重新生成 `electric_base_2050_unsolved.nc`，`ELECTRIC_BASE_SHA`（`scenario_network.py:26`）随之改变，也就是改变冻结底座的身份。
   - 而且 X10 边界表中 SG CCGT 800、MY 507、ID 466.1、MM 煤电 60 MW 也作为"不在网络中的 GIPT 机组"出现。改为 ≥ 后，GEM 新增表（s4a_2）也会加入它们，可能**重复计入**。
   - 选项见 §6 Q2。
3. **地热 40 年：**
   - S1 记录中，ID 地热 30 年时存活 186.0 MW，40 年（≥）时 1,051.0 MW，另有 171.0 MW 没有投运年；PH 30 年 0 MW，40 年 72.0 MW [VERIFIED]。
   - GEM 新增中的地热（s4a_2，`LIFETIME` 同步取 40）由 B 段算出。X10 按 GIPT 全集估 ID +920 MW、PH +72 MW。
   - 实现：`s2_layers.geothermal_unit_table`（L187-201）在开关取 40 或边界取 inclusive 时，按 `CommissioningYear` 重新判定地热记录的存活状态，不再沿用 S1 的状态。这样不必重生成 S1 JSON。
4. **重生成的表**（写新文件名 `_V5`，v4 表不动）：
   - `FLEET_ADDITIONS_2050_V5.csv`（现 299 行）、`FLEET_COVERAGE_…`、`FLEET_S4A_EVIDENCE…`；
   - 同一次运行写出的 `GAS_FIELD_*` 和 `GAS_PRODUCTION_NODE_SHARES_GEM.csv`：B 段核对不变，变了就停下报告；
   - `FLEET_STOCK_2050_S4B1_BY_COUNTRY_CLASS.csv`；
   - `CANDIDATE_CAPS_S4B2_BY_NODE_V5.csv`。
   - `s4a_2_fleet_data.py` 要求 `--network` 参数，指向**不含 S4A identity** 的 s3b 冒烟构建，否则 `in_network` 会把已加入的机组排除。B 段先确认该网络的路径与 SHA，找不到就停下报告。
5. **开关：** `lifetime_boundary`：**`inclusive`** / `strict`；`geothermal_existing_lifetime`：**40** / 30。
6. **注册表：** corrections `fleet_lifetime_rule_s1`（描述改为 start + lifetime ≥ 2050）、`geothermal_existing_lifetime`（L1186：40，区间 30–50，C 级；依据 X10 §10①：Tiwi–MakBan 47 年、Kamojang 43 年）；新行 `v5_lifetime_boundary_switch`、`fleet_additions_2050_v5_<CC>`。
7. **测试：**
   - `test_s4a_fleet.py:20`（299 行）和 `:22`（`> 2050`）改为按表版本参数化；`test_s4b_1.py:19,26`；`test_gate4_selected_closure.py:34`（2025 + 25 = 2050 期望退役，视 Q2 决定是否改）；
   - 新测试：边界机组在 inclusive 下保留；地热 40 年存量与 S1 记录逐台一致；与冻结存量不重复（同一厂名与坐标不同时出现在冻结底座和新增表）。
8. **预期：**
   - 2050 存量 +5.5 GW（GIPT 口径，X10 [VERIFIED]）：LA 光伏 1,050、LA 风电 850、SG 气电 800、PH 光伏 571.5 + 73.5、MY 气电 507、ID 气电 466.1、VN 光伏 375、TH 光伏 108.7 等。
   - 若 Q2 选择重建冻结底座，再加 TH CCGT 670 MW。
   - 两个场景成本都下降（免费存量），B6 小；ID 地热上限（①6）相应减小。
   - 废弃物机组（TH 150、VN 102 MW）会被 `add_gem_fleet` 跳过，这是既有行为，记入局限。
9. **依赖：** 做在 ①6、②6、①5 之前。

### 1.13 ②6 近似坐标（5 台）

1. **对象**（X10 `GEM_APPROX_COORDS.csv` [VERIFIED]；5 台都不属于冻结存量，X10 表中 source 列写错）：

   | 机组 | MW | 现节点 | 次近节点 | 距离差 km | 所在表 |
   |---|---|---|---|---|---|
   | New Kapar | 2,100 | MY_Peninsular2 1 | MY_Peninsular2 0 | 43.21 | `FLEET_ADDITIONS_2050.csv` 第 144 行 |
   | Thai Binh CCGT 1-1 / 1-2 | 2 × 750 | VN2 6 | VN2 3 | 28.78 | 同上，第 247、248 行 |
   | Truong Son wind 2 | 350 | LA2 1 | LA2 2 | 20.81 | `FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv` 第 21 行 |
   | Upper Yeywa | 280 | MM2 5 | MM2 14 | 11.09 | 同上，第 26 行 |

2. **核对：** 逐台用公开资料（GEM wiki 项目页、业主或政府公告，只用网页阅读）确定厂址坐标，按同国最近节点（`s4a_2_fleet_data.py:72-77` 的大圆距离）重算归属。结果写入 `research_inputs/fleet_v5/GEM_COORD_CORRECTIONS_V5.csv`，列 = `gem_unit_id, plant, old_lat, old_lon, new_lat, new_lon, source_url, source_note, old_node, new_node, grade`。
3. **施加：** 在 `s4a_fleet.add_gem_fleet`（L40-，L46-60 读表处）按 `gem_unit_id` 覆盖节点，v4 表不动。
   - Truong Son 位于专线电厂节点。若改到 LA2 2，要同步核对 `DEDICATED_STOCK_STATUS_V3.csv` 的 `plant_node` 和 `v3_layers.dedicated_stock_at`（L100-111）。
   - Upper Yeywa 改节点后，影响该节点的水电入流形状（①5）。
4. **开关：** `gem_coord_fix`：**`verified`** / `gem`。
5. **注册表：** `v5_gem_coord_corrections`（表 SHA，B 级）。
6. **测试：** 覆盖后存量组件的 identity 容量之和等于 p_nom（`s2_network.py:236-242`）；`gem` 时与 W14 相同。
7. **预期：** 节点归属最多改变 4.23 GW，成本影响小。

### 1.14 ③1 CO₂ 封存

1. **主值不变：** P50 ÷ 50（`baseline.yaml:376-379`，`s2_layers.py:44-75`）。
2. **改正出处描述**（corrections）：`co2_injection_cap_unified_<CC>`（L396–L406）、`co2_storage_unified_table`（L462）、`co2_injection_cap_<CC>`（L385–L395），以及 `s4b_0_data.py:63,66` 生成的对照表行。写明：
   - ÷ 50 对应 PyPSA-Eur 的 `co2_sequestration_lifetime: 50`（资产寿命，`pypsa_eur_v2025.07.0_config.default.yaml:712`），不是潜力换算参数 `years_of_storage: 25`（L702）；
   - ÷ 50 比 PyPSA-Eur 的 ÷ 25 保守；
   - PyPSA-Eur 另有欧洲 2050 年总上限 250 Mt/a（L703-710），可作参照；
   - 决策 28–30；"50"在注册表中没有外部文献出处。
3. **低情形开关：** 扩展 `research.s2.co2.storage_potential_case` 的取值（L379）。

   | 取值 | 含义 | 来源 |
   |---|---|---|
   | `p50` | 主值 | 现有 |
   | `low` | (i)：ERIA P90 + 净烃 ÷ 50 | 已实现：`CO2_STORAGE_CASES["low"] = "low_gt"`，L44 |
   | `iea_anchor_200` | (ii-a)：东盟 200 Mt/a，ID 90，其余按 P50 份额 | X10 `CO2_STORAGE_CASES.csv` |
   | `project_ramp_377` | (ii-b)：已宣布容量高端 × 1.10²⁰ | 同上 |

   - (ii) 类是年上限，不是潜力，所以 `co2_storage_caps` 对这两类直接读年上限列（Mt/a），不除年数。
   - 数据写入新表 `research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv`，列 = `country, iea_anchor_200_mt, project_ramp_377_mt, source`。
   - 新列不允许空单元格（现行 L72 遇空单元格会静默回退到 P50），缺值即报错。
   - 各国数值 [VERIFIED X10]：

     | 情形 | BN | ID | KH | MY | PH | TH | VN | 合计 |
     |---|---|---|---|---|---|---|---|---|
     | (i) | 271.586 | 685.5 | 1.8 | 1,635.46 | 1.344 | 240.48 | 66.068 | 2,902.238 |
     | (ii-a) | 11.769701 | 90.0 | 1.8 | 81.575718 | 1.344 | 10.150958 | 3.359622 | 200.0 |
     | (ii-b) | 0 | 213.530848 | 0 | 89.475749 | 0 | 74.002499 | 0 | 377.009097 |

     LA / MM / SG / TL 三种情形都为 0。按指令取 CSV 值，TL / SG 不另定。
   - cap = 0 时不建国家储罐（L359-361），区域内船运会丢掉以该国为接收方的航线（`s4d_layers.py:176-182`）。B 段核实 (ii-b) 下 BN、KH、PH、VN 为 0 时构建仍然成功。
4. **区域外封存年容量参数：** 新键 `research.co2.extra_asean_capacity_mt`。
   - 主值 null：现状，不设上限（`s4c_layers.py:805` 没有 `e_nom_max`）。
   - 取值形式为按国家的字典，或"每国同一数值"，施加为各国区域外储罐的 `e_nom_max`（Mt）。不设东盟总量：总量的右端项会归入 SHARED，Owen 前提就失败（`m12_rhs_audit.py:82-88`）。
   - 取 0 时删除该国区域外储罐和出口链路，不设 `e_nom_max = 0`。原因：零右端项会被零松弛检查拒绝；`e_nom_max < 1000` 会被 dust cleanup 删掉储罐而留下链路（`s4l_layers.py:185-187,288-300`）。
   - 低情形下的数值在 X21 定，Q13 只确认设计。
5. **注册表：**
   - 新行 `v5_co2_storage_case_iea_anchor_200_<CC>`、`v5_co2_storage_case_project_ramp_377_<CC>`（SENSITIVITY，C 级；IEA 2021 / 项目清单，X10 SOURCES）、`v5_co2_extra_asean_capacity`（REFERENCE_ONLY，数值在 X21 定）。
   - corrections 见第 2 条。
6. **测试：**
   - `test_m08a_a5.py` 扩展新情形；(ii) 类直接取年上限；空单元格报错；
   - 区域外容量按国施加，0 时删除储罐与链路；
   - 默认与 W14 相同。
7. **预期：** 默认不变。低情形下 F1 需改道：(i) 55.3 Mt、(ii-a) 660.5 Mt、(ii-b) 473.0 Mt [VERIFIED X10]。区域外不设容量时，一阶成本上界为 F1 +16.3 / +11.7 bn。

### 1.15 ③2 DAC 投资缩放键

- 在 `baseline.yaml:472-500` 的 `cost_scaling` 中加 `DAC: 1.0`。`apply_cost_scaling`（`s1_candidates.py:81-96`）按 carrier 精确匹配，DAC 链路的 carrier 是 `"DAC"`（`s2_layers.py:443`）。因子为 1.0 时比特级不变。
- 缩放乘在 capital_cost 上，即年化投资 + FOM。这与其他 `cost_scaling` 键口径一致，在注册表描述中写明。
- 缩放账本目前不落盘。v5 把 `apply_cost_scaling` 的返回值写进 `n.meta["v5_x20"]["cost_scaling"]`。
- 以下审计会从 `costs_active_research.csv` 重算 DAC 成本，因子不为 1 时会误报：`s4i_static_audit.py:170`、`s4c_1_cost_audit.py:86`。改为读取缩放因子。
- **注册表：** 新行 `v5_dac_investment_scale`（1.0，SENSITIVITY，区间 1.5 / 2，C 级；依据 X10 §4 文献范围）。
- **测试：** 1.0 比特级不变；1.5 时只改 DAC 链路的 capital_cost。

### 1.16 ③3 EV 智能充电份额

1. **新键：** `research.s2.demand.ev_smart_share`，默认 1.0，与 `ev_structure` 等同段（`baseline.yaml:409-412`）。
2. **实现**（`v3_layers.apply_ev_structure` 的 smart 分支，L330-339），取 s 时：
   - 智能部分：车队按 s × N 计，充电桩 p_nom = s × N × 0.011，电池 e_nom = s × N × 0.05 × 0.5，EV 电池母线上的负荷 = s × p_set。
   - 不可调部分：新负荷 `<node> land transport EV uncontrolled`，曲线 = 行驶曲线推迟 `ev_uncontrolled_delay_h`（同 uncontrolled 模式，L326）÷ 0.9，年电量 = (1 − s) × 年行驶电量 ÷ 0.9。母线见 Q5。
   - 新负荷必须在遍历 `land transport EV` 负荷的循环（L324-325）之外建立，不能被 `str(z.bus)[: -len(" EV battery")]` 的解析误处理。
   - 新负荷的 carrier 用新名 `land transport EV uncontrolled`。账本、`FIXED_ELEC`（`m12_allocation.py:197`、`m08b_static.py:41`）、`s2_solve.py:89,168`、`s4i_static_audit.py:345` 的 carrier 汇总都要认这个新名。
3. **需求账本：** EV 的终端能量仍为 733.86 TWh。不可调部分在电网侧计量（÷ 0.9），在 `demand_owners` 中记换算系数，保证 B8（`v5_gates.py:245-258`）、ATS 锚（`s2_layers.py:1171-1172`）和 `m08b_static.py:106-111` 通过。日分辨率聚合（`daily_resolution.py:9-19`）对 s < 1 要另加测试。
4. **注册表：** 新行 `v5_ev_smart_share`（1.0，SENSITIVITY 0.5，C 级；依据 X10 §6(d)）。
5. **测试：**
   - s = 1 时比特级不变；s = 0.5 时能量守恒（智能 + 不可调 = 总量），充电桩和电池按 s 缩放；
   - `tests/research/test_v3_units.py:39-59` 增加 s 参数。
6. **预期：** 默认不变。s = 0.5 时约 367 TWh 终端电量变为不可移动，正午太阳能的消纳价值下降，F1、F2 成本都上升，B6 方向不定。
7. **依赖：** ③4（不可调部分与充电桩挂在哪个母线）。

### 1.17 ③4 配电网与负荷母线

1. **实现位置：** `s2_network.py` 新增一层 `apply_distribution_grid_v5`（`v5_layers.py`）。
   - 放在需求层（L384）、EV 层（L395）和工业热、炊事各层之后，在成本层（L403）与损耗拆分（L411）之前。
   - 不在 `build_research_assets` 里改，否则 `ELECTRIC_BASE_SHA` 会变（`s2_network.py:304-305`）。
   - Astar 份额以 `Load.bus` 为键（`s2_layers.py:639-642`），所以挪动必须放在 `add_demand_layer` 之后。
2. **移到低压母线的组件：** 照 PyPSA-Eur v2025.07.0 `insert_electricity_distribution_grid`（注册表副本 `pypsa_eur_v2025.07.0_prepare_sector_network.py:1479-1590`，已读原文）：
   - carrier 含 "electric" 的全部负荷（原文 L1567-1570）：Astar 基础负荷 `electricity`、`industry electricity`、`agriculture machinery electric` 等，`bus += " low voltage"`；
   - `BEV charger` 的 bus0（L1572-1573）；
   - carrier 含 "heat pump" 的全部链路的 bus0（L1578-1579）。本模型只有工业热泵 `industry heat pump`，只在低温带（`s2_layers.py:548,559`："industrial heat pumps up to 150 C (302.b) -> low band only"）；
   - "resistive heater"（L1581-1582）在本模型中不存在；
   - 本模型的 `industry electric boiler`、`cooking electric` 在 PyPSA-Eur 字面规则下留在高压，见 Q3。
   - 电解与 DAC 留在高压（PyPSA-Eur 同样不动它们）。
   - 屋顶光伏和家用电池已在低压，不动。
3. **配电网链路：**
   - 现有 98 条 `<node> electricity distribution grid`（双向，p_min_pu −1，η 1.0）改为正向（p_min_pu 0，η 0.97），另建 `-reversed` 孪生（LV → HV，η 0.97，capital_cost 0，length 0，可扩），同 S4J-2（`s4j_layers.py:128-145`）。
   - 容量同步用已有钩子 `research_lossy_bidirectional_sync`（`s4j_layers.py:166-179`，允许集 `assembly_components.py:103`）。B 段核实钩子是按 meta 列表还是按 carrier 收集配对，必要时把配电网对加进列表。
   - 配电网链路长度为 0，不能交给 `apply_transmission_losses`，它对长度 ≤ 0 报错（L124-126）。所以由本层自己拆分，只用静态效率 0.97（PyPSA-Eur 配置 L762-763）。
4. **扣损：** PyPSA-Eur 对 `carrier == "electricity"` 的负荷乘 0.97（原文 L1553-1565），理由是它的负荷数据含损耗。本模型的负荷来自终端消费表（`nonindustrial_electricity: table_sectors`），推断不含配电损耗；而且缩放 `p_set` 会破坏多处守恒检查（`scenario_network.py:169`、`s2_layers.py:1171-1172`、`m08b_static.py:106-111`、`v5_gates.py:255`）。**推荐不扣减**，见 Q4。
5. **账本同步：** 挪动后同步更新 `n.meta["s2_demand_ledger"]["loads"]` 与 `<scenario>_S2_DEMAND_OWNERSHIP.csv` 的 bus 列，参照 `s4c_layers.py:675-677`。
6. **需要逐项核对的衔接点（B 段）：**
   - 每个带负荷的节点都有 LV 母线（X17：LV 母线 98 个）。没有 LV 母线的节点，若有负荷就停下报告。
   - LV 母线的 `country` 由 `build_research_assets.py:112` 写入，所以 `s4d_ledger.owners`、`m12_allocation.load_energy_twh`、`m12_rhs_audit.Owners` 能按 country 列归属。在 v5 56 时段解上跑 `m12_rhs_audit`：要求 `owen_premise.passed`（L520）为真，SHARED = 0，unresolved = 0。
   - `s4c_layers.py:211` 的 `LOC_SUFFIXES` 不含 " low voltage"，要核实 LV 母线有 `location` 属性，否则补上。
   - 门检 B11 的 carrier 字典（`v5_gates.py:292`）不含 low voltage，核实 B11 对 v5 网络是否通过。
   - 零松弛检查、`static_validate_s2` 的需求归属（L135-146）、dust cleanup 合并零容量链路（`s4l_layers.py:242-248`）要确保不误合并孪生链路。
7. **开关：** `distribution_grid`：**`lv_pypsa_eur`** / `hv_lossless`（= 现状）。
8. **注册表：** corrections `s4j2_link_losses`（L2102，"distribution grid 0.97 not used"改为 v5 已采用）；新行 `v5_distribution_grid_efficiency`（0.97，B 级，PyPSA-Eur v2025.07.0 L762-763）、`v5_distribution_grid_lv_attachment`（规则）。
9. **测试：**
   - 玩具网络：负荷、充电桩、热泵移到 LV；孪生容量相等、两向效率 0.97；`hv_lossless` 时与 W14 相同；
   - 账本 bus 列更新；m12 前提在玩具上通过；Astar 守恒不受影响。
10. **预期：**
    - 两个场景系统成本各 +16.3 至 +36.4 bn/a，损耗 70–97 TWh/a（X10 §8）。
    - 配电容量需要覆盖低压净负荷峰值：刚性部分 322 GW；含现有 EV / 热泵调度时的同时刻净峰值 721 GW。
    - 屋顶光伏因自发自用而增值。B6 小（两个场景近似同幅）。
    - 工业热泵改由低压取电后，DAC 取热的成本上升，碳价可能上升。

### 1.18 ③5 燃料舱碳的事后归属报表

1. **新脚本** `scripts_project/v5_bunker_attribution.py`，并在 `s2_solve.py` 导出流程中调用（BUNKER_ACCOUNT.json 之后，L508-514 附近），写出 `BUNKER_CARBON_ATTRIBUTION.json` / `.csv`。不改优化。
2. **方法**（基于 X10 `08_x16_bunker.py`，修正两处）：
   - (1) 合成端碳：methanolisation 的 p4（`efficiency4`，`s3_layers.py:489-491`）与 FT 的大气端口，按生产国计。
   - (2) 去向：按各国液体母线之间的甲醇船运流（`methanol ship`）和本国消费者，比例混合，属 INFERENCE。消费者分为燃料舱（`<node> bunker shipping methanol`）、国内航运、OCGT 甲醇、其他。X10 脚本只把本国燃料舱算作归属燃料舱（L89），v5 修正为追踪贸易。
   - (3) 碳源：按各国 `co2 stored` 池的流入份额分为化石点源、工艺、DAC、生物源，并剔除 CO₂ 管道与船运转运，同 X10 L36-50。
3. **输出：** 生产国 × 使用去向（国家 × 用途）× 碳源，单位 Mt。
4. **校验：**
   - 各项合计等于合成端碳，相对差 < 1e-6。
   - 在 v4 2920 已解网络 F1 上，合计 130.96 Mt，燃料舱归属约 117–121 Mt（X10 备忘录）。只读，读网络前测内存门槛。
5. **测试：** 玩具网络两国一港，归属守恒。

### 1.19 ④1 导出元数据

1. **`meta['run_status']`：** 在 `s2_solve.py` `post_solve` 的 L449 与导出 `gate_a4_readback`（L502）之间写入，内容：
   - 求解状态与终止条件；
   - 本进程门检摘要（A1–A4、B 组结果）；
   - 实际激活的约束钩子（`n.meta["required_constraint_hooks"]`，经 `assembly_components.validate_hooks` L98-106 过滤）；
   - 授权文本 `a.authorization`；
   - COMMIT `a.package_commit`。目前它只写进 `SOLVE_RECEIPT.json`（L265-266），v5 同时写 meta；
   - 代码 SHA（`git_head`）与构建回执中的 `code_sha`。
2. **验收标签的时点（Q11）：** V6 验收由 `gates_v6.py accept`（L218-228、L314-321）在求解**之后**读 `SOLVE_RECEIPT.json` 生成（`run_batch4.sh:456-459`），导出网络时还没有。推荐在导出前于进程内调用 `gates_v6.acceptance_v6`（输入在内存中可得时）。不可得时写 `V6_PENDING`，并在 `V6_ACCEPTANCE.json` 旁写 sidecar，不重写 80 MB 的网络。
3. **`meta['build_history']`：** 把 X10 `META_STATUS_KEYS.csv` 中的过期顶层键原样移入：`interim_notice`、`skeleton_status`、`stage`、`asset_role`、`scientific_results_allowed`、`fullsc_network_complete`、`input_coverage_complete`、`source_is_solved`、`asset_qualification`、`resource_occupancy_status`、`qualification_dimensions.policy_constraint_qualification`。
   - `research_config.*` 内的状态键（`skeleton_status`、`stage`、`demand.status`、`s2.status`、`site_candidates.*.status`）**不移动**，因为 `research_config` 与 `research_config_sha256` 必须一致。只在 `build_history` 中注明它们已过期（Q11）。
   - 移动前，按"switch-all-read-points"的教训，全树检索每个键在求解后的读取点（例如 `install_research_constraint_hooks` 读 `solver_allowed`，`artifact_role` 被多处读取）。有读取的键保留原位并复制一份。
4. **测试：** 导出、回读后 `run_status` 与内存中的字典相同；`build_history` 含旧值；B12 / G2.2 哈希不变。

### 1.20 ④2 局限清单

新文件 `LIMITATIONS_V5.md`，同时放在交付目录和 `research/06_scope_redesign/p1_v5_x20_20261111/`，逐条写来源、影响与原因。

- **X03 §9，不在本步修订的：**
  - GEM 近似坐标的其余机组。例如 Jakarta wind farm 597 MW 的坐标在市区，不在 5 台之列，因为距离差规则只选了 5 台。
  - 未建机组的 p_nom 下界对偶是退化的。
  - PH5 0 等节点被标记为台风暴露，但台风溢价关闭。
  - `s4b_3_wind_calibration.py:38` 的 GWA 3.3 常数：本步改为 REFERENCE_ONLY，但常数本身仍在代码中。
- **X10 §13，不在本步修订的：**
  - GEM 气田覆盖不全（VN 18 %、MY 28 %），BN 气田数据为 2006 年，TL Greater Sunrise 未体现；
  - 封存储罐的 capital_cost 按 e_nom 计；
  - technology-data DAC 的压缩电耗可能重复计 0.15 MWh/t，heat-output 0.75 MWh/t 未使用；
  - EV 车队代理：12,000 km/a 在库内无出处，50 kWh 电池偏大，两轮车多；
  - VN 合成氨为煤头，扣除截断 9.8 TWh；
  - 米沙鄢内部交流海缆在同一节点内；
  - 区域外封存的容量依据缺失（本步只加参数）。
- **本步新发现：**
  - 存量光伏同样取 0 级曲线（Q12）；
  - `s4b_3` 的越界检查不中止（v4 路径）；
  - `s4i_static_audit` 的水电比值把 PHS 算进分子；
  - 废弃物发电机组被 `add_gem_fleet` 跳过；
  - VN 小水电没有分厂数据（Q17）；
  - ②2 中重建核对不通过的走廊；
  - ①4 变体的节点分配按比例近似。

---

## 2. 相互作用与实施顺序

**实施顺序**（B 段每项一个提交，提交信息写明修订编号与决策项，例如"X20 ②5（决策 244）: …"）：

| 步 | 内容 | 理由 |
|---|---|---|
| 0 | 框架：`v5_common.py`、baseline.yaml `demand.v5` 段（全部为 V5_OFF 时的等价值）、meta `v5_x20`、注册表占位；v5 关闭时重建，与 W14 逐值比对 | 先保证回退等于 v4 |
| 1 | ②5 寿命规则（按 Q2 的答复） | 改变 GEM 新增表与地热存量，是 ①6、②6、①5 的前提 |
| 2 | ②6 坐标 | 改变 Truong Son（①2）与 Upper Yeywa（①5）的节点 |
| 3 | ①1 陆上风电重建 | 改变全部陆上剖面与等级份额 |
| 4 | ①2 存量风电 | 依赖 ①1 的 c2 曲线与 ②6 的节点 |
| 5 | ①3、①4 | 互相独立，默认不变 |
| 6 | ①5 水电 | 依赖 ②5、②6 |
| 7 | ①6 地热 | 依赖 ②5 的存量 |
| 8 | ①7 生物质复核 | 独立；若改表要重建 T06 链 |
| 9 | ②1、②2 | 都挂在 `s2_network.py:318`，先 PH 后 AC；②2 需要 OSM API |
| 10 | ②4（表链重生成）、②3 | ②4 改需求表；②3 在构建层 |
| 11 | ③1、③2 | 默认不变 |
| 12 | ③4，然后 ③3 | ③3 的母线取决于 ③4 |
| 13 | ③5、④1、④2 | 后处理与元数据 |
| 14 | 注册表全链重跑、全量测试、全分辨率构建、静态检查、桥表、56 时段回归、报告、审阅包 | §5 |

**相互作用：**
1. **①1 × ①2：** 存量风电曲线跟随 c2，①1 之后 c2 的 CF 会变。
2. **①1 × 等级份额：** 剖面改变后节点内重新三等分，各等级 `p_nom_max` 改变（节点总量不变）。①1 的单元测试和 `test_s4b_3.py:59-61` 都依赖总量守恒。
3. **①1 × ①4：** 导出时光伏和海上风电列取自同一 pypsa_eur 来源，必须与 `calibrated_modern` 逐字节相同，否则 ①4 的"主值不变"不成立。
4. **②5 × ①6：** 上限 = 储量 − 存量，存量随寿命开关变，所以 ①6 在构建时计算（§1.6 第 2 条）。
5. **②5 × PH 地热重建：** `s4b_2_candidates_data.py:91` 写死 30 年，要随开关参数化。
6. **②5 × 冻结底座 × GEM 新增：** 边界机组可能重复计入（§1.12 第 2 条，Q2）。
7. **②5 × ②6：** 坐标覆盖要施加在 V5 新增表的机组上（按 `gem_unit_id`）。
8. **②6 × ①2 × ①5 × v3 专线表：** Truong Son 改节点后，取新节点的 c2 曲线，并核对专线电厂表；Upper Yeywa 改节点后影响入流形状。
9. **③4 × ③3：** 不可调 EV 负荷和充电桩 bus0 挂在同一个母线（LV 或 HV，Q5）。
10. **③4 × 热泵 × DAC：** 工业热泵改由 LV 取电后要付配电成本，DAC 的取热成本和碳价上升。电锅炉留在 HV（Q3），同一热母线上的两种技术成本口径不对称。
11. **③4 × Owen / M12：** LV 母线平衡的右端项归属本国（有 country 列），配电网是国内链路。B 段在 56 时段解上核对 `owen_premise`。
12. **③4 × 需求账本：** 不缩放 `p_set`（Q4），只改 bus 并同步账本。
13. **②1 / ②2 × 扩建上限、损耗孪生、交流损耗代理：** 都挂在 L318，下游自动继承新存量。②2 改阻抗后 KVL 环流改变，影响 M12 的环路转移项（见记忆"M12 Owen / KVL"）。
14. **②3 × ②4：** ID 需求下降后，ID 上限可能不再绑定，F1 中 LNG 进口下降。
15. **②3 × 逃逸排放与门检：** 系数为 0 的国家没有井口发电机，B15 / D10 不再列该国。
16. **③1 × 区域外封存：** 低情形必须同时设区域外容量（X21），否则只是把 CO₂ 改运出去。
17. **②4 × v4 表目录：** 只有 v5 打开时才并入表身份，v4 目录不变（§0.1 第 4 条）。
18. **全部 × B12 / 冒烟目标与报警线：** v5 网络的配置哈希与 W14 不同，W14 的冒烟目标（363,190,038,821.0828 / 376,143,650,003.4369）和报警线不再适用于 v5。B 段只拿它们作为"与 v4 同截取冒烟的差"，不作为判定。HPC 包不在 X20 范围内。
19. **④1 × 门检：** 移动元数据键之前，先确认没有门检在求解后读这些键。

---

## 3. 磁盘方案

**规则：** 本步新产生的网络、缓存、构建中间文件、日志、测试输出和打包文件一律写到 D 盘交付目录 `/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/`。WSL 家目录和 C 盘新增合计 ≤ 1 GB（WSL 根盘 `/dev/sdd` 的 vhdx 在 C 盘）。

| 产物 | 默认位置 | 改到 D 盘的办法 | 预计大小 |
|---|---|---|---|
| 全分辨率网络与构建回执 | `s2_network.py --output`（必填，L498） | `--output $D/builds/<set>/integrated`；变体 `m08a_variants.py --out $D/builds/<set>/no_new_xb`（L160-162） | 每套约 230 MB（W14 每套：2920×3h 两个 82.7 / 82.1 MB，365×24h 两个 34.9 / 34.2 MB，回执 1.7 MB [VERIFIED]）；按 3 套计约 0.7 GB |
| 构建时写入 `--output` 的成本表等 | 同上 | 同上 | 已含在上一行 |
| 风电剖面中间结果 | `s4a_profiles.py --output`（必填，L127） | `--output $D/profiles/…`；`s4b_3_wind_calibration.py --output $D/calib`；`s4b_3_export.py --onwind-source $D/profiles/…` | 约 0.1–0.5 GB |
| 正式剖面 nc（入 git） | `research_inputs/renewable_v5/` | 留在仓库（与现有同类文件一样入 git） | c1 + c3 约 12 MB；`.git` 对象同量 |
| atlite / dask 临时文件 | 系统临时目录 | 所有 B 段进程设 `TMPDIR=$D/tmp`；脚本中的 `tempfile.mkdtemp`（`v4_industry.py:159`）用 `--work $D/v4work` | ≤ 1 GB |
| v4 表链 `out_ras_v5` | `research_inputs/industry_v4/` | 留在仓库（小） | 约 0.3 MB |
| 注册表 | `research_inputs/registry_v5/` | 留在仓库 | 约 1.5 MB |
| 56 时段截取网络 | — | `$D/trunc56/` | 2 × 29 MB |
| 56 时段求解产物 | `s2_solve.py --output`（必填，L561-564） | `--output $D/smoke56/F{1,2}` | 两次约 0.6 GB（D2c 实测 549 MB）；`lp/`、`split/` 中间文件求解后保留在 D 盘 |
| 测试临时目录与缓存 | pytest 默认 `/tmp`；`__pycache__` 写在 worktree | `pytest --basetemp=$D/pytest_tmp -p no:cacheprovider`；`PYTHONPYCACHEPREFIX=$D/pycache` | 约 0.5–1 GB |
| 日志 | — | `$D/logs/` | < 50 MB |
| 下载（OSM JSON、NGCP PDF） | — | `$D/downloads/{osm,ngcp}/` | ≤ 100 MB |
| 构建所需符号链接 | worktree `results_project/` | `results_project/{assembly_v1,s1}` 指向主检出（只读）；`results_project/v5x20` 指向 `$D/builds`，供测试读取（`V4_D2A_BUILD` 等环境变量指向 D 盘的 365×24h 网络） | 0 |
| worktree | `/home/jin/wt_v5_x20`（A 段稀疏检出 1.7 MB） | 见 Q9 | 完整检出 720.3 MB（`26c2e47d` 跟踪文件合计 720,273,106 B [VERIFIED]） |

- **D 盘合计：** 约 3–5 GB（≤ 30 GB）。D 盘当前可用 207 GB。
- **WSL 家目录 / C 盘合计：**
  - 完整检出的 worktree 720 MB；
  - `.git` 新对象约 15–30 MB（剖面 nc、注册表、表格）；
  - 合计约 0.75 GB，在 1 GB 之内，余量约 250 MB。
- **注意：** 不在主检出 `results_project/` 下写任何新文件（`s1`、`assembly_v1` 只读）。

---

## 4. 全分辨率构建的预计内存峰值与时长

| 步骤 | 参照（VERIFIED） | v5 预计（INFERENCE） | 门槛判断（可用 ≥ 4 GiB 且峰值 ≤ 可用 / 2） |
|---|---|---|---|
| F1 构建（`s2_network`，含 2920×3h 与 365×24h） | W14：峰值 RSS 1,064,300 kB，1:31.40（三次构建一致）；D2c：1,066,156 kB，1:26 | 约 1.1–1.3 GB（新增约 200 个负荷与链路），约 1.5–2.5 分钟 | 可用 ≥ 4 GiB 即满足 |
| F2 变体（`m08a_variants`） | W14 每种分辨率数秒 | 同量级 | 满足 |
| 风电校准（`s4b_3`，L111 整读 `wnd100m` 的 `.values`） | 175 × 146 × 8,760 的 float32 ≈ 0.9 GB，float64 ≈ 1.8 GB | 约 2–3 GB | 需要可用 ≥ 6 GiB |
| 风电剖面（`s4a_profiles`，atlite 加 alpha / 校正后的 cutout 副本） | X03 逐格点 CF 计算 43.6 s，内存未记录 | 约 3–5 GB（cutout 副本加功率曲线转换）；c1 与 c3 共约 5–15 分钟 | 需要可用 ≥ 6–10 GiB。**B 段先跑 c1，用 `/usr/bin/time` 实测；预计峰值超过可用 / 2 时先停下报告**（指令 §0 内存条） |
| 静态检查（`w14_static` 类） | W14：0:27，828,560 kB | 同量级 | 满足 |
| 零松弛检查 | W14：0:50，713,508 kB | 同量级 | 满足 |
| 全量测试 | D2c：31:44（875 通过 / 1 失败 / 56 跳过） | 约 35–45 分钟，基线再跑一遍 | 测试内会构建网络，单个峰值约 1–2 GB |
| 56 时段 LP 构建 | W14 演练：F1 2.22 GiB / 36 s，F2 1.99 GiB / 29 s | 约 2.3–2.6 GiB | 满足 |
| **56 时段求解（Gurobi）** | D2c：F1 216.1 s、峰值 **7.27 GiB**；F2 148.5 s、**5.72 GiB**（`p1_v4_d2c_20261109/REPORT.md`）；W14 演练 runner 822 / 710 s | 约 6–8 GiB（行数略增） | **不满足：** WSL 总内存 11,483,643,904 B（10.7 GiB），开工时可用 10.6 GiB，一半为 5.3 GiB，小于 7.27 GiB。**见 Q18** |

**合计时长（INFERENCE）：** 构建 3 套约 10 分钟，剖面约 15 分钟，全量测试两遍约 80 分钟，56 时段回归约 30 分钟，其余脚本与检查约 1–2 小时。总计在 B 段 10 小时额度之内。

---

## 5. B 段检查清单的执行方式（指令第 3 节）

1. **逐项实施，每项一个提交**（顺序见 §2）：
   - 写消息文件与提交分两步，不并行（见记忆"commit message file sequencing"）；
   - 每次提交前对照被忽略文件清单：`*.csv` 等要 `git add -f`（`research_inputs` 下的新表）；
   - `git ls-files --eol` 检查不得有 CRLF；
   - 不用 `--no-verify`，不改 `core.hooksPath`；推送到 `asean/v5-x20-20261111`，不合并 main，不 force-push。
2. **全量单元测试：**
   - 先在同一 worktree 的 `26c2e47d` 上跑基线。命令同 D2c `full_tests.sh:12-18`：`--ignore test_m12_allocation.py`，并 deselect 5 个玩具 LP 测试（`test_s3b_r4`、`test_s4c_3`、`test_s4c_5`、`test_s4m_duals`、`test_s4o_2`），因为它们会调用求解器，计入 Gurobi 次数。
   - 先复制被忽略的 `finance_v5` 输入（D2c `copy_wacc.sh`）。
   - 再在 v5 头上跑同一命令。逐项比较：新增失败要么修复，要么证明在基线上同样失败（已知既有失败为 `test_s1_built_networks.py::…::test_static_validation_passes_on_reload`）。
   - 环境变量 `V4_D2A_BUILD` 等指向 D 盘的 v5 365×24h 网络，确保网络测试真的运行而不是跳过。跳过数要与基线对比。
3. **重建 v5 网络：**
   - F1：`s2_network.py --scenario integrated --override demand.v4.enabled=true --override demand.v5.enabled=true --output $D/builds/v5main/integrated`；F2：`m08a_variants.py --set cross_border.stock_mode=no_new_xb`。
   - 设 `PYTHONHASHSEED=0`、`PROJ_DATA` / `PROJ_LIB`、`TMPDIR=$D/tmp`；每次构建都用 `/usr/bin/time -v`，构建前按门槛测可用内存。
   - 记录 SHA256、构建时长和峰值内存。
   - 另做一套 v5 关闭的构建 `$D/builds/v5off`，与 W14 逐值比对（§0.1 第 5 条）。
4. **静态检查：**
   - (a) 构建内断言：`static_validate_s2`、`check_network_meta(_v5)`、`check_fuel_prices`、`compare_roundtrip`。
   - (b) `zero_slack_check.py --network …`：要求退出码 0，没有零余量强制行。
   - (c) `s3_6_gates_check.py`（B11–B16）、`s4i_static_audit.py`、`b4_batch4.py base-check`。
   - (d) 每个开关在默认值下与本规格一致：新脚本 `x20_static.py` 逐开关打印网络中的实际取值或效果，例如存量风电取的等级、PH 直流存量、各国气上限、ID 地热上限、LV 母线上的负荷数。
   - (e) 输入总量与本规格表对照：需求（按国家 × 部门）；资源（陆上风电各国各等级 CF 与潜力、光伏上限、水电入流、地热上限、生物质池）；碳（各国封存上限、区域外设置）。
   - 陆上风电合理性检查：各国各等级 CF 的 v4 → v5 对照，再与"GWA IEC3 毛值 ÷ r"对照，r 为三国风场点位"GWA 毛值 ÷ 实测"的比值（TH 1.07、VN 1.44、PH 1.52 [EXACT X03]）。
5. **桥表 `X20_BRIDGE.csv`：**
   - 列 = `revision, decision, switch, country, quantity, unit, v4_value, v5_value, delta, source_table, grade`。只列输入，不涉及求解结果。
   - 生成脚本 `x20_bridge.py`：在 v5off 与 v5main 两套未解网络上统计每项修订改变的量，例如陆上风电各国平均 CF 与潜力、存量风电 CF、PH 直流存量、MY 走廊 s_nom、各国气上限、NEU 气、2050 存量、地热上限、水电入流、配电网组件数与 LV 负荷量。
   - 报告中加一节。
6. **本机 56 时段回归（Gurobi 至多 4 次，同时运行的 Gurobi 进程 ≤ 8）：**
   - 截取方式同 W14：前 56 个时段，权重 8760/56（`s2_solve.py:22-35,276-280`；`w14_static.py:219-224`）。
   - 档案 `formal_barrier_1e6_t16`，`--scaling on`，按 D2c `smoke_d2c.sh:41-42` 的命令行，F1、F2 各 1 次，必要时各重跑 1 次。
   - 只按 `GRB_LICENSE_FILE` 读许可，不复制、不打印。先测 WSL 到 token.gurobi.com:443 的连通性（见记忆"WSL outbound blocks WLS token"）。
   - 报告：是否 optimal、目标值、与 v4 同截取冒烟的差、各国 Owen 分摊的符号（`m12_allocation` / `M12_OWEN`）。
   - **不对 56 时段结果作任何数量结论。** 这一步受 Q18 制约。
7. **`REPORT.md`：**
   - 第 0 节总表：修订编号、是否完成、开关名、主要变化、测试结果；
   - 每个数字标 EXACT / VERIFIED / INFERENCE；
   - 附"给师哥的逐条说明要点"更新版（每条一段：来源、可靠性判断、改了什么）。
8. **审阅包 `REVIEW_<报告 SHA256 前 8 位>.zip`：** 含规格、报告、桥表、CSV、脚本、EVIDENCE，不含网络文件；逐成员给出 SHA256 与 CRC。
   - 打包前对求解日志做许可文本清洗（见记忆"Solve stdout licence banner"），并扫描是否泄露主机名或许可内容。扫描模式只在运行时由环境变量提供，不写进脚本（见记忆"No host/port literals in scans"）。
9. **记录：** `PROGRESS.md` 在 B 段结束时记录 `df -h /`、交付目录大小与家目录增量；`EVIDENCE.json` 收录全部输入与产出的路径、字节数、SHA256、分支和提交号；另写 `SOURCES.csv`、`DOWNLOAD_CANDIDATES.csv`、台账条目。

---

## 6. 待决问题（B 段开始前需答复；"推荐"只是建议，由用户决定）

| 编号 | 优先 | 问题 | 选项 | 推荐 |
|---|---|---|---|---|
| **Q2** | 高 | ②5 把 `asset_survival.py:23` 改为"≤"，会让冻结存量中 7 台、2,503.1 MW（SG / TH / MY / ID CCGT 与 MM 煤电）回到 2050 存量。这要求重建冻结底座（`ELECTRIC_BASE_SHA` 改变），而且其中 SG / MY / ID / MM 的同名机组也会经 GEM 新增表再加一次。 | (a) 重建冻结底座：assembly 链用 ≥ 规则重跑，s4a_2 按厂名与坐标排除已在底座中的机组；(b) 冻结底座不动、`asset_survival.py:23` 不改，边界机组只经 GEM 新增表（GIPT 口径）进入；TH 670 MW 是否在 GIPT 边界上由 B 段核实；代码与底座的差异写入局限；(c) 两处都改代码，但不重跑 assembly（代码不再能复现底座，不推荐） | (b)。冻结底座身份是常设决策；GEM 新增本来就是"2050 年在役、冻结存量中缺失的机组"的通道 |
| **Q18** | 高 | 56 时段求解的预计峰值为 6–8 GiB（D2c 实测 F1 7.27 / F2 5.72 GiB）。WSL 总内存 10.7 GiB，"峰值 ≤ 可用的一半"不可能满足。 | (a) 用户调大 WSL 内存（`.wslconfig`，属于用户自己的设置，我不改）；(b) 对 56 时段求解改用"峰值 ≤ 可用 − 2 GiB"的门槛；(c) 降低线程数等，但对 barrier 的内存影响有限，且改档案就不能与 v4 冒烟直接比较；(d) B 段不做 56 时段回归 | (a) 或 (b)，由用户定 |
| **Q3** | 高 | ③4 照 PyPSA-Eur 字面规则，工业热泵（carrier 含 "heat pump"）移到 LV，而同一工业热母线上的 `industry electric boiler` 留在 HV；`cooking electric`（家庭终端用途）也留在 HV。 | (a) 字面规则：热泵 → LV，电锅炉与电炊具 → HV；(b) 热泵、电锅炉、电炊具都 → LV；(c) 热泵与电锅炉 → HV（工业用户多在中高压接入），电炊具 → LV | 指令写"热泵回到低压"，(a) 最贴近原文；(b) 能消除同一母线上两种技术成本口径不对称的问题。请审阅端定 |
| **Q4** | 高 | ③4 是否照 PyPSA-Eur 对基础负荷乘 0.97 扣损？ | (a) 不扣减：本模型负荷来自终端消费表，推断不含配电损耗，且缩放 `p_set` 会破坏多处守恒检查；(b) 扣减，并同时改守恒检查的口径 | (a) |
| **Q1** | 高 | ①1 回标口径。指令字面是：校准时在风场格点上用"格点均值校正"后的风速。这样 TH 的 alpha 仍含"风场选在格点内最好位置"的溢价（GWA 风场点位 27.9 % 对实测 26.0 %，比值 1.07），推广到全国，与"TH 不再推广高 alpha"冲突。 | (a) 字面：格点均值校正后回标；(b) 校准时风场格点改用"GWA 风场点位值 ÷ ERA5 格点均值"校正（只去掉选址溢价），剖面仍用格点均值校正；(c) 字面做法，但对 TH 另加约束，使 alpha 不超过某个上限 | (b)。它与审阅端的合理性检查"GWA 毛值 ÷ 风场点位比值"口径一致 |
| Q5 | 中 | ③3 不可调 EV 负荷的母线。指令写"挂 AC 侧"，而 ③4 主值把充电桩移到 LV。 | (a) 与充电桩 bus0 同一母线：③4 主值下为 LV，回退时为 AC；(b) 始终挂 AC（HV） | (a)。把"AC 侧"理解为"电网侧，而非 EV 电池母线" |
| Q6 | 中 | ②2 去重后的阻抗与核对失败的走廊。 | (a) 按 S4G-1 重算 num_parallel 与 x / r / b（物理一致，KVL 环流改变）；(b) 只改 s_nom，同 S4F-2 的做法；核对失败的走廊（如线 94）一律不改，写入局限 | (a) + 核对失败不改 |
| Q7 | 中 | ②4 合成氨单耗（10.8 → 消除 84.4 TWh；BAT 7.8 → 38.9 TWh），以及 NEU 是否在 RAS 锚定的 TFEC 内。 | 单耗取 10.8（与 DFX F2.4 一致）或 7.8；若 NEU 在锚内，B 段停下报告 | 10.8；B 段先核实锚 |
| Q8 | 低 | ②1"移除 B2B 占位换流器"实现为 p_nom = 0、不可扩，保留元件，以维持 `dc_to_ac` 映射与结构检查。 | 确认，或要求真正删除（需先证明结构检查不失败） | 确认 |
| Q9 | 中 | worktree 位置。B 段需要完整检出（720 MB），因为测试引用 `research/04`，注册表脚本读 `research/06`。 | (a) WSL 家目录完整检出（总增量约 0.75 GB，余量约 250 MB）；(b) 放在 D 盘 `/mnt/d/...`（C 盘为 0，但 9p 上的 git 与 Python 较慢，符号链接与权限有风险）；(c) 稀疏检出，排除 `research/04`、`05` | (a) |
| Q10 | 中 | 开关框架：放在 `research.demand.v5` 段（B12 与 G2.2 自动覆盖）；只有 `neu_gas_growth` 在 v5 打开时进入 v4 表目录身份，主集目录名为 `out_ras_v5`。 | 确认，或改为把 v5 键全部并入 v4 开关集（5 个表目录全部重写、SHA 全部改变，D2b 先例） | 确认 |
| Q11 | 低 | ④1：(1) V6 验收标签在导出时还没有生成，改为进程内计算，不可得时写 `V6_PENDING` 加 sidecar；(2) `research_config.*` 内的过期状态键不移动，只在 `build_history` 中注明。 | 确认，或要求导出后重写网络 | 确认 |
| Q12 | 中 | 本步新发现：存量光伏同样复制 `<node> solar-2025`（0 级，最差）曲线（`s4a_fleet.py:94`）。 | (a) 一并改为最好等级（扩展 ①2）；(b) 不改，写入局限 | 请审阅端定；第 1 节没有列入 |
| Q13 | 低 | ③1 区域外封存容量参数按国设定（Owen 安全）；取 0 时删除储罐与链路（避开零松弛与 dust 问题）；不设东盟总量。 | 确认 | 确认；数值在 X21 定 |
| Q14 | 低 | ①5"2019–2025 年已投运"定义为：冻结底座的作者机组，加上 GEM `operating` 且投运年 ≤ 2025 的机组。2019–2025 年间投运的机组只对中位数做了部分贡献，这里不作年内折算。 | 确认，或要求按投运年折算 | 确认 |
| Q15 | 低 | ①4 MY 两个变体不重算栅格，国别增量按现有节点上限比例分配。 | (a) 两个变体都按比例分配；(b) 开阔森林用本机 LC100 栅格逐节点计算，油棕仍按比例分配（种植园栅格不在允许的下载内） | (a)，变体只作敏感性用；要更精确就选 (b) |
| Q16 | 低 | ①6 开关"证实 + 概略 5,460 MW"同样减存量（5,460 − 存量）。 | 确认，或要求不减存量 | 确认 |
| Q17 | 低 | ①5 VN 小水电：库内没有单一来源的分厂数据，EVN / IHA 分厂数据不在允许下载的范围内，所以只写局限并列下载候选。 | 确认，或授权下载 | 确认 |

---

## 7. A 段产出

- `X20_SPEC.md`（本文件）、`PROGRESS.md`。
- `scripts/00–11`：开工检查、体积、引用、worktree、哈希、作者链、构建体积、X10 汇总、行号抽查、S1 边界、磁盘与内存事实，全部只读。
- `logs/`：各脚本输出。
- `evidence/`：`REUSED_INPUTS_SHA256.txt`（66 个复用输入）、`GWA_SHA256_FROM_LOG.txt`（22 个 GWA 文件）。
- `DOWNLOAD_CANDIDATES.csv`：A 段发现、需要用户另行授权的下载。
- **额度：** 求解器 0 次；本机计算约 5 分钟，主要是哈希 1.2 GB 的 GWA 文件和 WSL 只读检查；WSL 家目录新增 1.7 MB（稀疏 worktree）加 `.git` 元数据；D 盘交付目录新增 < 1 MB。
