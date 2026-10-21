# M08a 报告：实施修正（上）——成本与货币、LNG、封存、风光布局、情景开关、门槛 V6（第 129–133 项；不求解）

**摘要（2026-10-21）**
1. 指令 v1（SHA256 `19c00a1e…`）与补充 01（`e3471b65…ec24`）均核对一致；分支 `codex/m08a-corrections-20261021`（M08-0 头 `30d281b8` + 普通 merge S4Q），每个任务一个提交并附单元测试。
2. A1 货币平减改为 technology-data 同口径（EEA HICP 逐年累乘 1.25733）；A2 SMR = 核电 × AEO8 同表比值（8,421 → 9,167 EUR2020/kW）；A3 存量机组按投运年取 v0.15.0 成本表（存量 FOM 10.806 → 10.050 bn/a，两情景相同）。
3. A4 LNG 取消 2.5 倍上限（`capex_only`，8,020 EUR2020/MW/a，再气化 1.26 EUR2020/MWh，液氢 × 1.2）；A5 封存统一为 ERIA-GCCSI 2024 P50（VN 106.07、PH 1.344 Mt/a）。
4. A6.1 地面光伏密度 5.1 MW/km²（× 1.1087）；A6.2 海上风改用 PyPSA-Eur v2025.07.0 面积规则并新增漂浮式：AC 1,783 GW、DC 2,714 GW、漂浮 4,436 GW（原 AC 1,673 / DC 3,054 GW）；atlite 全量 3 分 22 秒。
5. A7 四个情景开关由同一脚本确定性派生（含"去掉一国"整体移出、分国 WACC）；A8 `gates_v6.py` 与事先登记的运行规则；A9 账本美元列。
6. 补充 01：G2.2 子集键写入 `GATES_V6_NOTES.md` 第 6 节；b1 范围确认，老挝只保留通往区域外封存的过境通道并加强制检查；报告汇率改为输入汇率的倒数 1.139954。
7. 注册表 2,057 → 2,121 行（新增 64、修改 188、改为历史 39、删除 0），DATA_PENDING 47 → 46；拟增 v2 中本步 27 行全部写入，其余 16 行属 M08b。
8. 测试：`tests/research` 全量 **533 passed、64 skipped、0 failed**（5 个玩具求解用例排除，见醒目事项 1；跳过的均为 worktree 中没有的历史构建）。
9. 未求解（Gurobi 0 次）、未连云；网络重建与本机冒烟按指令放在 M08b 之后。

## ⚠ 醒目事项（请先看）

1. **边界偏离（如实披露）：** 测试子集中的 `tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model` 用 scipy `linprog`（HiGHS）解一个 4 列的玩具 LP（C1 判据的单元测试），本会话与上一会话的每次子集运行都执行了它。未调用 Gurobi，不涉及模型网络。原因：子集脚本只检索 `optimize(`，漏掉 `.solve(` 与 `linprog`。已改正：运行脚本改为检索三种写法，全量与子集都排除 5 个玩具求解用例（另外 4 个：`test_s3b_r4::test_scaling_round_trip_small_model`、`test_s4c_3::test_net_zero_hook_forces_non_fossil_bunkers`、`test_s4c_5::test_kvl_normalisation_exact`、`test_s4m_duals::test_dual_dataset_with_conflicting_dim_coords`，均未运行）。
2. **A5 遗留的构建缺陷（已修，否则 M08b 之后的重建会失败）：** 船运路线表 `CO2_SHIP_ROUTES_S4D2.csv` 有 70 条进入 TL 的路线，而 A5 后 TL 潜力为 0、不再建国家储罐；`s4d_layers.apply_intra_asean_shipping` 要求路线表与网络精确相等，会以 "ship route table does not match the network" 中止构建。改为丢弃并记录进入无储罐接收国的路线；缺少路线或多出进入有储罐国家的路线仍报错（`co2_ship_routes_receivers_rule`；测试 `test_m08a_a5`）。
3. **航道排除在东盟几乎不起作用（VERIFIED）：** PyPSA-Eur 阈值 400 × 8760 × 6 = 2,102.4 万次 AIS 位置 / 0.005° 格，高于东盟最繁忙航道（新加坡海峡 1,669 万、马六甲 136 万、南海主航道 ≤ 1,074 万）；超阈值像元主要在东海（13.1–29.4°N）。全区只排除 57.2 MW（AC 42.7、漂浮 14.5、DC 0）。规则照 PyPSA-Eur 实现未改；是否另定东盟阈值请用户决定（PROPOSED 敏感性，未实现）。
4. **S4R 回溯表 D7、D9 两项无效：** `s4r_r8_retro.py` 读错字段（D7 用 `cap_t`、D9 用 `p_nom_opt`/`p_nom_max`；门槛实际字段为 B2 `final_level_t`/`horizon_limit_t`、B14 `p_nom_opt_mw`/`p_nom_max_mw`），`GATES_RETRO_COMPARISON` 中这两项实际未算到，需在第三批后按 `gates_v6.py` 重算。S4R 文件未改。

## 1. 依据、分支与边界

- **依据：** `M08A_CLAUDE_CODE_INSTRUCTION.md` v1（SHA256 `19c00a1e127bc30c470a498fc2c765905a6923072452a02c50d4f3abeb849476`）、`M08A_SUPPLEMENT_01.md`（`e3471b65189aa8f6afef83f1fbfc28d4e07e3522230b325bdba056770768ec24`）；方案 `IMPLEMENTATION_PLAN.md` M08-1 至 M08-4、M08-7 至 M08-10；注册表第 129–133 项；`GATES_V6.md`（`5c0aa8b8…7f9`，未改）。
- **分支：** `codex/m08a-corrections-20261021`，worktree `/home/jin/wt_m08a_20261021`；自 M08-0 头 `30d281b8`，普通 merge S4Q 头 `22f53c84`（提交 `4247f21b`，冲突只在台账，双方保留）。draft PR 叠在 #44 上（见第 6 节）。
- **边界：** 未求解，未调用 Gurobi（含许可检查），未连云；未改既有结果与已发布网络文件。只读使用的既有网络：S4M-3 integrated / disconnected 构建（A3、A7、b1、A6.2 取证，均在内存中派生，变体文件用后删除）、冻结电力底座（两个测试经临时只读链接运行，链接已删除）。
- **联网：** 按补充 01 第 3 点，从 GitHub 标签 v2025.07.0 只读获取 `determine_availability_matrix.py`（6,920 B，`bdddee1e…`）、`build_ship_raster.py`（2,337 B，`bab4a06d…`）、`build_renewable_profiles.py`（与 S4C-1 登记的 `12fe6776…` 一致）、`rules/build_electricity.smk`（32,562 B，未使用）；前两者存于 `research_inputs/registry_v5/sources/*.py.txt`。

## 2. 逐项改动

### A1 货币平减（M08-1）— 提交 `77a9a07c`

- **改动：** `s2_0_cost_layer_v015.py` 按 technology-data v0.15.0 `scripts/_helpers.py` 第 220 行的口径回算：Eurostat `prc_hicp_aind` 欧洲经济区（EEA）年均变化率 2021–2025 逐年累乘，EUR2025 → EUR2020 = 1 / 1.2573346（2.9、9.2、6.4、2.6、2.5 %）；美元行用美国行。来源为 technology-data 自带 `inputs/prc_hicp_aind__custom_20097956_spreadsheet.xlsx`；用户下载 Sheet 6 交叉核对，2016–2025 EEA 年率逐值相同。
- **配置键：** `research.cost_layer.layers.technology_data_v0_15_0_2050_eur2020.rebase_index` = `eea_hicp_rate`（主）| `ea20_gdp_deflator`（原 S2-0 口径，对比；文件逐字节等于旧主层）；`rebase_variants` 列出两套文件。
- **测试：** 回算系数 × technology-data 升通胀系数 = 1（±0.1 %，按规则与未改动行两种方式）；非货币行不变（`test_m08a_a1.py`）。+4.8 % 残差消失（未改动来源的行等于 v0.13.2）。

### A2 核电同源与 AEO8 价格年（M08-2）— `0e39df2e`

- **改动：** SMR = technology-data v0.15.0 大型核电 × AEO8 D.15 同表比值：投资 × 1.0667（9,600 / 9,000）、FOM 份额 × 1.37、VOM × 0.43；寿命、效率、折现率随核电。SMR 投资 8,421 → 9,167 EUR2020/kW（+8.9 %）。
- **配置键：** `research.cost_layer.smr_cost_source` = `td_nuclear_x_aeo8_ratio`（主）| `aeo8_author_rule_2050`（原）；`research.cost_layer.aeo8_price_year_factor` = 1.0（敏感性 0.86；作用于地热新建投资，存量地热 FOM 常数保持未缩放口径）。
- **测试：** SMR 投资 = 核电 × 1.0667；FOM / VOM 比值；旧选项与系数（`test_m08a_a2.py`）。
- **注册表工具：** 新建 `scripts_project/m08a_data.py` → `fragments/m08a.csv`（新行）与 `fragments/m08a_corrections.csv`（整行替换，由不含 M08a 片段的装配生成，重跑结果相同）。

### A3 存量机组成本表（第 131 项）— `4cc95598`

- **规则：** 存量组件取 technology-data v0.15.0 `costs_<年份>` 表：投运年取最近的 5 年整，限制在 [2020, 2050]，2020 年前投运取 2020 表；FOM = FOM % × 投资，VOM 与燃料 Link 的效率取同表；同一组件含不同年份机组时按容量加权（效率保持燃料输入容量）。地热保留 AEO8（例外）。
- **配置键：** `research.fleet.existing_cost_basis` = `td_v0_15_0_by_commissioning_year`（主）| `author_v0_13_2`（原）；`research.fleet.existing_cost_year_rule` = {step 5, min 2020, max 2050, nearest}。
- **结果（在 S4M-3 网络上内存核算，VERIFIED）：** 存量 FOM 10.806 → 10.050 bn EUR2020/a，一体化与不互联相同；存量 CCGT 效率 0.56（2020 表）/ 0.57（2025 表），混合组件 0.5635，容量加权 0.5833 → 0.5662；317 个组件、1,075 台机组。水电 / 径流式 v0.15.0 无 VOM，按规则变为 0（原 0.53 / 0.44 EUR/MWh）。
- **测试：** 年份规则、CCGT 0.56 / 0.57、玩具网络、两情景存量 FOM 相同、旧模式（`test_m08a_a3.py`）。

### A4 LNG（M08-3）— `04d686fe`

- **改动：** `capex_only`：16 台 LNG 进口发电机 `p_nom_max = inf`（含 7 个仅规划站点），GEM GGIT 2025-09 运营 + 在建容量为下限；扩建 8,020.43 EUR2020/MW/a（Ulvestad & Overland 2012 换算，±50 %）；再气化加价 1.26 EUR2020/MWh 加到 LNG 进口边际成本；液氢码头 = LNG × 1.2 = 9,624.52 EUR2020/MW/a。
- **配置键：** `research.s3.gas.lng_expansion` = `capex_only`（主）| `cap_factor_cost`（原 2.5 倍上限）| `uncapped_cost` | `existing_only` | `cap_factor`；`lng_expansion_capital_cost_eur_per_mw_a` 8020.43；`lng_regasification_adder_eur_per_mwh` 1.26；`research.s3.imports.h2_terminal_capital_cost_rule` = `lng_x_factor`，`h2_terminal_lng_cost_factor` 1.2。
- **测试：** `p_nom_max` 为 inf，成本与加价写入，门槛 B14，液氢 × 1.2（`test_m08a_a4.py`）。
- **偏离 / 保留：** 液氢码头的容量上限仍沿用 S3-2 规则（LNG 存量 × 2.5 或规划容量），A4 只取消 LNG 上限；GEM 中 3 个无容量数据的 LNG 节点仍不建候选。

### A5 CO₂ 封存统一（M08-4）— `79b0f3e6`

- **改动：** 统一表 `research_inputs/co2_v5/CO2_STORAGE_POTENTIAL_UNIFIED.csv`：VN 5.3034、PH 0.0672、MY 128.773、ID 51.275、BN 18.5793、TH 16.024 Gt（ERIA-GCCSI 2024 P50），KH 0.09（IJGGC 2014 低值，C 级），TL / LA / MM 0（LA / MM 标 UNASSESSED），SG 0。年上限 = 潜力 ÷ `storage_years`（不再写死 /50）。
- **配置键：** `research.s2.co2.storage_potential_source` = `eria_gccsi_2024_unified`（主）| `registry_d1`（原）；`storage_potential_table`；`storage_potential_case` = p50 | low | high。
- **测试：** VN 106.07 Mt/a、PH 1.344 Mt/a（`test_m08a_a5.py`）。**后续修正**见醒目事项 2（`adc0460e`）。

### A6 风光布局（M08-7）

**A6.1 光伏（`f1de7cb5`）：** 地面光伏候选 `p_nom_max` × 5.1 / 4.6 = 1.108696，11 国相同，在分级前施加；屋顶与存量光伏不变，土地规则不变，不重算栅格。配置键 `research.renewable.solar_density`。测试 `test_m08a_a6.py`。

**A6.2 海上风面积规则（`b6c4f338`）：**

- **规则（VERIFIED，逐行核对）：** offwind-ac 水深 ≤ 60 m、离岸 ≤ 30 km（配置第 201–219 行）；offwind-dc 水深 ≤ 60 m、离岸 ≥ 30 km（220–238 行）；**新增 offwind-float** 水深 60–1,000 m、无离岸距离限制（239–260 行，NREL_ReferenceTurbine_5MW_offshore × 0.8855）；三者 2 MW/km²，排除分辨率 200 m，仅开阔海域，排除 natura，航道排除 = 密度 > ship_threshold 400 × 8760 × 6（`determine_availability_matrix.py` 第 126–133 行）。排除语义 = 该文件第 96–156 行（`max_depth` 排除 v < −max_depth、nodata −1000；`min_depth` 为其取反；离岸距离用陆上国家形状缓冲，max 取反）；潜力、layout、廓线、平均距离 = `build_renewable_profiles.py` 第 170–173、184、247、258–285、287–304 行。AC / DC 机型与尾流不改（S4A 起已是 NREL 2020ATB 5.5 MW × 0.8855）。
- **实现：** 新脚本 `scripts_project/m08a_offshore_profiles.py`（atlite ExclusionContainer → 可用矩阵 → 潜力 / 3 级分级 / 3 h 廓线 / 连接距离）；构建层 `s4a_layers.apply_offshore_rules` 把电力底座中所有可扩建的 offwind-ac / -dc 候选按"节点 × 分级"替换，新增 offwind-float 载体与发电机；成本层 `s4c_layers.apply_cost_layer_s4c1` 按分级距离计价（technology-data v0.15.0 `offwind` / `offwind-float` + station + 1.25 × (距离 × 海缆 + 登陆段 20 / 30 / 40 km × 陆缆)）；`CARRIER_COST_ROWS`（WACC）、台风溢价（漂浮式取所在节点 DC 的暴露度）、dust 层、`s2_solve` 可再生列表、静态审计、成本分解、S4C-1 成本审计同步加入 offwind-float。
- **配置键：** `research.renewable.offshore_rules` = `pypsa_eur_v2025_07`（主）| `author_pypsa_earth`（原：AC 2 / DC 3 MW/km²、≤ 50 m、无航道、无漂浮）；`research.renewable.offshore_dir` = `research_inputs/renewable_v5/offshore_m08a`。
- **耗时与资源（VERIFIED）：** 全量 3 分 22 秒，峰值内存 2.65 GB；航运栅格裁剪一次 167 s（裁剪文件 39 MB，本地）；永久输出约 20 MB（廓线 c1 4.9 MB、c3 14.7 MB、分级表 0.16 MB）+ 本地可用矩阵 21 MB。远低于原则 7 阈值。三次运行输出逐字节相同。
- **结果（11 国合计，GW）：**

| 载体 | as-built（作者规则） | 新规则 | 加权容量因子 | 加权距离 km |
|---|---|---|---|---|
| offwind-ac | 1,672.9 | 1,783.2 | 0.136 | 14.8 |
| offwind-dc | 3,054.3（3 MW/km²） | 2,714.3 | 0.246 | 110.6 |
| offwind-float | — | 4,435.8 | 0.162 | 104.1 |

  分国见 `evidence/M08A_A6_2_OFFSHORE_BY_COUNTRY.csv`（ID 漂浮 2,410 GW、PH 574 GW、VN 403 GW、MY 381 GW 最大）。
- **方法验证（VERIFIED）：** 同一脚本换用作者 PyPSA-Earth 规则复算得 AC 1,673.3 / DC 3,052.2 GW，与 as-built 相差 +0.02 % / −0.07 %；逐节点中位差 0.8 % / 2.0 %（S4A 把跨区格点按面积拆给节点，本脚本按区域内实际可用面积，INFERENCE）。
- **偏离 PyPSA-Eur 字面之处及理由（已登记）：** 排除 / 面积投影用 ESRI:54009（作者链 `area_crs`，等积）而非 EPSG:3035（欧洲专用）；GEBCO 2025 代替 2014；CORINE [44, 255] → Copernicus LC100 [80, 200]（作者链同义代码，远海抽样均为 200）；节点区域、3 级分级、距离口径沿用 S4A / S4C-1，与其他载体一致；航运栅格经 `/vsizip/` 按 `build_ship_raster.py` 同一窗口读取，不解压 9.8 GB 文件（抽样点与全球栅格逐值相同）。
- **测试：** 规则值 = 配置行、分级划分守恒、玩具网络上的替换与新增、成本公式（`test_m08a_a6.py` 7 项）；`test_s4a_profiles.py` 的 S4A 机制测试固定为作者规则，并新增"电力底座上的 A6.2"测试（经临时只读链接运行 4 passed）。
- **A6.3 海上风校准：** alpha 保持 1.0（F9，DATA_PENDING，`offwind_alpha_calibration_rule`）。**A6.4 开阔林：** 未实现（按指令）。

### A7 情景与联盟开关（M08-8 扩展）— `bf181b68`，补充 `adc0460e`

- **脚本：** `scripts_project/m08a_variants.py` 从 `s2_network.py` 构建的基础网络确定性派生所有变体（固定顺序：去掉一国 → 存量模式 → b1 → WACC），记录输入 / 输出 SHA256（`<name>_VARIANT_RECEIPT.json`）；构建脚本拒绝非缺省变体键（单一生成路径）。
- **开关（缺省 = 主算）：** `research.cross_border.stock_mode` remove_all | keep_stock_no_new；`research.disconnected.co2_shipping_intra_asean` allow | forbid；`research.coalition.remove_countries` [] | [ISO2…]；`research.finance.wacc_mode` uniform | country_specific（`country_wacc_table` = `COUNTRY_WACC_REAL_M08A.csv`，TL = KH / LA / MM 均值 0.0924，C 级；`distributed_wacc_rule` = technology_data_fixed | proportional）。
- **分布式 WACC 规则与理由：** 主规则 technology_data_fixed：成本表中折现率低于统一率的行（technology-data 屋顶光伏与分散式行 0.04）在分国模式下保持该家庭折现率——PyPSA-Eur / technology-data 把分散式折现率与系统折现率分开设定，IEA 观测站的 WACC 针对公用事业规模项目，不宜套到家庭投资；proportional（r_国 × 0.04 / 0.07）作敏感性。跨境资产用两端国家均值；线路纳入；无 country 列的底座组件按母线国家确定（原实现静默跳过 1,864 个）。
- **取证（S4M-3 基础网络，`--allow-stale-base`，VERIFIED）：** 五个变体两次派生逐字节相同；keep_stock 保留 16 条交流线 + Khlong Ngae–Gurun 300 MW 直流 + 6 条气管道；forbid 删除 552 条链路（船运 504 / 过境船运 42 / 铁路 6），保留 77 条区域外出口；去掉 VN：需求 11,576.6 → 9,339.5 TWh = 合计 − VN 2,237.0，无组件引用 VN 母线，燃料舱负荷保留；分国 WACC 改动 5,216 个组件，98 个屋顶光伏保持 0.04。
- **补充 01 第 2 点（b1 范围，用户确认）：** b1 = 不互联时禁止东盟区域内一切跨境 CO₂ 运输，含经老挝的铁路段。
- **补充 01 §2（老挝过境通道）：** 现有实现中老挝每个缓冲节点已有一条 `CO2 transit export extra-ASEAN`（S4D-1，第 93 项），b1 保留它；本步把规则写死并强制检查（`m08a_layers.check_landlocked_transit`、`co2_sink_channels`）：
  - 成本 = 铁路陆段（链路边际成本，`co2_lao_transit_land_cost_<node>` 9.66–24.57 EUR2020/t，含装车）+ 老挝本国区域外储罐单价 54.70 EUR2020/t（IEAGHG 2004 4,500 km 船运链 24.70，含液化、港口、缓冲罐与装船；+ 地质封存 30）——与沿海区域外出口同一口径；
  - 限制：只进入 `co2 sequestered extra-ASEAN LA`，不连越南、泰国国内储罐总线；
  - b1 后若有国家失去全部永久封存出口，变体脚本报错拒绝。
  - **与内陆国过境权惯例的关系（INFERENCE，仅作表述框架）：** UNCLOS 第十部分第 125 条规定内陆国出入海洋的权利与过境自由，GATT 1994 第 V 条规定过境自由；过境国承运而不储存，与"只能过境、不能存入邻国"的建模一致。去掉越南的变体中，该链路两端都在 LA，仍然保留（陆段经越南）——按过境权理解保留，**请用户确认**。
  - **各国 b1 下的封存出口（`evidence/M08A_B1_SINK_CHANNELS.csv`，VERIFIED，三种情形 32 行全部有出口）：**

| 国家 | 国内年上限（A5，Mt/a） | b1 前 | b1 后 | 说明 |
|---|---|---|---|---|
| BN | 371.6 | 本国 + 他国 + 区域外 | 本国 + 区域外 | |
| ID | 1,025.5 | 同上 | 本国 + 区域外 | |
| KH | 1.8 | 同上 | 本国 + 区域外 | |
| LA | 0 | 他国（铁路 / 过境船运）+ 区域外过境 | **区域外过境**（6 条） | 只能过境 |
| MM | 0 | 他国 + 区域外 | 区域外 | 内陆节点经国内管道至沿海 |
| MY | 2,575.5 | 本国 + 他国 + 区域外 | 本国 + 区域外 | |
| PH | 1.344 | 同上 | 本国 + 区域外 | |
| SG | 0 | 他国 + 区域外 | 区域外 | |
| TH | 320.5 | 本国 + 他国 + 区域外 | 本国 + 区域外 | |
| TL | 0（A5 后无国内储罐） | 他国 + 区域外 | 区域外 | |
| VN | 106.1 | 本国 + 他国 + 区域外 | 本国 + 区域外 | |

  （"A5 调整"情形在 S4M-3 网络上于内存中移除 TL 储罐及进入它的 77 条链路、按统一表改上限后施加 b1。）观察：MY_Peninsular22 0、PH_Visayas10 0、TH21 0 的 `co2 stored` 总线只连 FT 与 SMR CC，无缓冲、管道或封存——构建期即如此，与 b1 无关，单列为"直通总线"（`co2_passthrough_buses_note`）。

### A8 门槛 V6 与事先登记的运行规则（M08-9）— `7e38c500`，补充 `4c46f442`

- **实现：** `scripts_project/v5/gates_v6.py`：G1 = C1 (a)(b)(c)；G2.1 网络 SHA256 + 往返；G2.2 配置子集哈希（写入网络元数据与回执）；G2.3 结果完整性；诊断 D0–D16，D2 预算 10 × max(OptimalityTol, BarConvTol)；标签 ACCEPTED_LAYER2 / ACCEPTED_LAYER1 / NOT_ACCEPTED，求解器状态只记录。D7 / D9 / D10 用门槛实际字段并加 1e-3 + 10 ε_f 容差。
- **G2.2 子集（补充 01 第 1 点）：** 30 个键 = `GATES_V6.md` §2 原列表 26 个 + `cost_layer`（整段）、`site_candidates`、`disconnected`、`coalition`；不纳入 `solver.profile(s)`、`solver.acceptance`、`solver.run_rules`、`reporting`、状态标签、`fuel_bus_naming`、`config_overrides`。写入 `GATES_V6_NOTES.md` 第 6 节"实现说明：子集键清单"（明确是实现、不是修改定义；NOTES SHA256 `d296ddcf…` → `cad04000…`；`GATES_V6.md` 不改）；测试核对实现与说明表逐一相等。A6.2 新键在 `renewable` 段内，自动纳入。
- **运行规则（配置 `research.solver.acceptance` = gates_v6，`research.solver.run_rules`）：** 验收按 GATES_V6；正式 2920×3h 必须通过 C1 (c)；档案选择链：1e-6 T16 在 365×24h 第二级 C1 (a)(b)(c) 全过且与档案 A 目标相对差 ≤ 1e-5 → 正式用 1e-6 T16，否则档案 A，1e-5 档案永不作备选；TimeLimit 48 h，不收敛按 C1 分级判定，不重试、不改参数。运行脚本 `scripts_project/m08a_run_batch.sh`（S4O 云包脚本未改）。
- **测试：** D2 预算随 BarConvTol 变化；G2.2 对 `solver.profiles` 等不敏感、对情景开关 / `site_candidates` / 成本层口径键敏感；子集键 = 说明第 6 节；运行脚本以合成流水线端到端检验（无求解器）（`test_m08a_a8.py`）。

### A9 报告货币（M08-10）— `9fb4e584`，补充 `2a0a660b`

- **改动：** 账本导出增加美元列（`COUNTRY_COST_LEDGER_DETAIL.csv` 的 `usd2020` / `usd2020_length_split`，新增 `COUNTRY_COST_LEDGER_USD2020.csv`）；模型、LP 与 `eur` 列仍为 EUR2020。
- **补充 01 第 3 点（单一汇率双向一致）：** 报告汇率 = 输入汇率 `fx_usd_to_eur_2020` 的倒数 = 1 / 0.877228632573 = **1.139954** USD2020/EUR2020（补充 01 写作 1.13996，为舍入；实现按精确倒数），导出时由注册表计算；同一笔美元输入换成欧元再换回美元等于原值（测试精确到 1e-14）。ECB 2020 年均 1.1422 只作对照（`fx_report_ecb_2020_reference`，高 0.197 %）。
- **配置键：** `research.reporting.fx_per_eur2020` = `inverse_of_input`（主；补充 01 称 `finance.report_fx_usd_per_eur2020`，指同一键）；给数字只作对比，并记录 `consistent_with_input = false`。
- **测试：** `test_m08a_a9.py`（倒数、对比值标记、错误规则拒绝、往返、注册表行；`reporting` 不在 G2.2 子集）。

### A10 注册表 — 各任务提交 + `37e18984`、`4af11d13`

- 写入拟增 v2 中属于本步的 27 行；新增 EEA HICP 口径、存量年份规则、LNG 扩建模式、封存统一表、光伏密度、海上面积规则、四个情景开关定义、TL WACC 规则、分布式 WACC 规则、档案选择链等行（见第 4 节）。被替代的旧行改为 REFERENCE_ONLY，描述追加"历史：已被 X 替代"（39 行）。注册表测试全部通过。

## 3. 测试

- **全量（头 `4af11d13`，2026-10-21 14:27–14:28）：** `tests/research`（80 个文件）**533 passed、64 skipped、5 deselected、0 failed**，耗时 62.5 s（`evidence/M08A_FULL_TESTS.txt`）。排除的 5 个玩具求解用例见醒目事项 1。64 个跳过全部是"某步构建 / 汇总不在 worktree"（git 忽略的 `results_project`），例如 "S4C-1 build not present"；worktree 中复制了被忽略的 `research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv`（未提交）。
- **子集（每个任务提交前）：** 读注册表的文件 + `test_m08a_*.py`：97 → 144 passed，24 skipped（逐任务见第 2 节与进度文件）。
- **电力底座测试：** `test_s4a_profiles.py` 经临时只读链接到主检出的冻结电力底座运行，4 passed，链接已删除。

## 4. 注册表变化（基准 M08-0 头 `30d281b8`，`6d1b2c34…` → `53b051c1…`）

- 2,057 → 2,121 行：新增 64、修改 188、改为历史 39、删除 0（`evidence/M08A_REGISTRY_DIFF.csv/.json`）。其中 108 行只改定位文本中的回算系数（0.833196 → 0.795333 = 1/1.25733，A1）。
- 构建读取且有意改变的值：`co2_storage_potential_*`（A5）、`fuel_price_lng_regasification_adder`（A4）；其余构建读取行未改。
- 状态变化：REGISTERED → REFERENCE_ONLY 28、SOURCE_ZERO → REFERENCE_ONLY 7、SOURCE_ZERO → REGISTERED 2、DATA_PENDING → REGISTERED 3、DATA_PENDING → REFERENCE_ONLY 1、REFERENCE_ONLY → REGISTERED 1（航运密度栅格，A6.2 起使用）；等级变化 2 行（LA / MM UNASSESSED 行 C → A）。DATA_PENDING 47 → 46。
- 拟增 v2 覆盖（`evidence/M08A_REGISTRY_PROPOSED_V2_COVERAGE.csv`）：本步 27 行全部在册；16 行（需求锚定 6、工业产量 9、生物质溢出 1）属 M08b。

## 5. 仍未解决 / 待用户决定

1. **航道阈值：** PyPSA-Eur 阈值在东盟几乎不排除任何海域；是否设东盟敏感性阈值（例如 40 次 / 小时 = 210 万，可排除主航道）——待用户决定（PROPOSED）。
2. **去掉越南时的老挝过境：** 是否保留经越南陆段的过境通道（现为保留）。
3. **DATA_PENDING：** AEO8 价格年（`aeo8_cost_price_year`，敏感性 0.86）；CO₂ 封存成本 30 EUR/t 的价格年；海上风观测 CF（F9，alpha = 1.0）；东南亚专用再气化费率。
4. **S4R 回溯表 D7 / D9 无效**，第三批后按 `gates_v6.py` 重算（醒目事项 4）。
5. **派生文档行未重算：** 数据脚本按旧成本层写入注册表的货币文档行（如 `gas_pipeline_cost_onshore` 91.37）未重算；构建期价格直接取成本层，不受影响。
6. **液氢码头上限**仍为 S3-2 规则；GEM 中 3 个无容量数据的 LNG 节点不建候选。
7. **存量水电 VOM 变为 0**（v0.15.0 无此参数）。
8. **直通总线**（MY_Peninsular22 0、PH_Visayas10 0、TH21 0）：只作观察登记，未改。
9. **M08b 及之后：** 需求锚定、工业有用热与温度带、生物质溢出（M08b）；网络重建、静态检查、本机冒烟（M08b 之后，届时会首次在完整网络上检验 A6.2、A5 后的船运路线过滤与 b1 检查）；分摊流程（M12）。

## 6. 交付与提交

- **工作目录：** `work/p1_m08a_20261021/`（本报告、`M08A_PROGRESS.md`、`evidence/`、`scripts/`），镜像到 `research/06_scope_redesign/p1_m08a_20261021/`。
- **提交：** 第一会话 `4247f21b` → `77a9a07c` → `0e39df2e` → `4cc95598` → `04d686fe` → `79b0f3e6` → `bf181b68` → `7e38c500` → `9fb4e584` → `f1de7cb5` → `37e18984`；本会话 `4c46f442`（补充 01 第 1 点）→ `2a0a660b`（第 3 点）→ `adc0460e`（第 2 点与 §2、A5 后续修正）→ `b6c4f338`（A6.2）→ `4af11d13`（A10 差异）→ `7e5f44f4`（交付）→ 本报告定稿提交（见 PR）。
- **PR：** draft https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/45（base `codex/m08-0-registry-backfill-20261020`，即叠在 #44 上；仓库无 CI 检查）。
- **审阅 ZIP：** `work/p1_m08a_20261021/M08A_REVIEW.zip`，逐成员 SHA256 与 CRC32 见 `M08A_REVIEW_MANIFEST.csv`（ZIP 本身的 SHA256 在 `M08A_REVIEW_ZIP_SHA256.txt`）。内容：本报告、进度、指令与补充及其 SHA256、`evidence/`、`scripts/`、`GATES_V6_NOTES.md`、海上风分级表与日志、相对 `30d281b8` 的代码 / 配置 / 测试差异补丁 `M08A_CODE_DIFF.patch`。
- **台账：** `research/STAGE2_PROJECT_LEDGER.md` 追加 M08a 条目。
