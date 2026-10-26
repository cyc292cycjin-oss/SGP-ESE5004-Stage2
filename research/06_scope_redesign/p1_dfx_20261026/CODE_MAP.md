# CODE_MAP — `scripts_project/` 代码地图（DFX F0）

- 生成日期：2026-10-26；工作树 `/home/jin/wt_dfx_v3_20261026`（分支 `codex/dfx-v3-20261026`）。
- 范围：`scripts_project/` 下全部 300 个文件（298 个 `.py`、2 个 `.sh`；其中 `v5/` 子目录 4 个、`retired/` 子目录 10 个），每个文件恰好归入下列一类。
- 数据来源：`CODE_MAP_TABLE.csv`（逐文件的追踪/静态/注册表/测试标志）与 `CODE_MAP_DATA.json`（同一信息的列表形式），两者与本文件同在 `research/06_scope_redesign/p1_dfx_20261026/`。
- 行数取自 F0 快照（`CODE_MAP_TABLE.csv`）。撰写本文件时，工作树中 `m08b_demand.py`、`d1_common.py`、`s2_layers.py`、`s2b_feedstock.py` 已含 DFX F1–F3 的修改（代码中有 `DFX F1.2` / `F2.4` / `F3` 标记），这些文件的实际行数已与快照不同；分类不受影响。
- 本文件只做归类，没有运行任何脚本，也没有改动任何仓库文件。

## 1. 分类汇总

| 类别 | 文件数 | 说明 |
|---|---:|---|
| 生产管线 / 构建 | 31 | v1 网络构建（`s2_network.py` 及其导入的层、成本、载体、校验模块；`in_build` 为真，或由 `s2_network.py` 导入） |
| 生产管线 / 求解 | 10 | `s2_solve.py` 求解驱动及仅在求解路径导入的模块（`in_solve` 为真；含分进程求解的进程 2 `b4_split_solve.py`） |
| 生产管线 / 后处理 | 10 | 求解后的闸门、精度证据、账本、Owen 分摊、违反量分析及 `s2_solve.py` 求解后懒加载的导出模块 |
| 生产管线 / 批次与打包 | 19 | 第三/第四批与 M08a 批次的入口与打包辅助（4 个）；另有仅静态可达的 Gate4–Gate6 支持库（15 个，追踪均未导入） |
| 数据链（离线生成 research_inputs 表与注册表片段） | 87 | DFX 需求修复重跑的 7 个脚本；上游不重跑的 D1/S2/S3/M08 基础表与片段 22 个；各阶段（S3B–S4O）注册表片段与输入表生成 58 个 |
| 测试与检查工具 | 36 | 静态校验、烟测评估、回归/单元测试脚本、验证器 |
| 一次性数据或证据脚本 | 96 | 各阶段的提取、探针、汇总、证据收集脚本（Gate4–Gate6、S1–S4M、L23 等） |
| 已退役 | 11 | `retired/` 目录的 10 个文件，加 `s2b_industry.py` |
| **合计** | **300** | |

要点：

1. **在 v1 构建/求解/后处理轨迹中被导入的文件合计 45 个**（构建 31、求解 27、后处理 28，三者大量重叠）；其余约 255 个文件是入口脚本、离线数据脚本、测试和一次性证据脚本。
2. **需求链的实际执行者是 `m08b_demand.py`**（经 `growth_method: ats_anchor`）；`d1_demand_2050.py` 是上游（其输出作输入、其常量被导入）；`build_research_demand.py` / `demand_*.py`（Gate2 家族）在任何追踪中都未执行，仅被 `test_demand_accounting.py` 与 Gate2/3 哈希守卫证据引用。详见第 3 节。
3. 重复实现已在第 3.3 节标出（只改实际执行的一份，另一份不删除）。

## 2. 证据来源与判定规则

### 2.1 动态追踪（2026-10-26）

在 `scripts_project/` 内记录每次运行实际被 `import` 的模块（`sys.modules` 记录，原始记录 `results_project/dfx_v3/f0_trace/modules.jsonl`），共四组运行：

| 标志 | 运行 | 模块数 |
|---|---|---:|
| `in_build` | v1 网络构建 `s2_network.py`（与 `ec80668f` 同一命令） | 31 |
| `in_solve` | `s2_solve.py --stop-before-solve` 与 `--split-stage build` | 27 |
| `in_post` | 56 快照后处理链：`l23_violation_analysis.py`、`s4o_c1_precision.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s4d_ledger_redo.py`、`v5/gates_v6.py`、`m10_batch3_summary.py` | 28 |
| `in_variants` | `m08a_variants.py --help` | 2 |

### 2.2 静态闭包

- `in_batch_shell`：批次/打包 shell 脚本中被直接引用。这些 shell 位于 `scripts_project/` 之外：第三批 `research/06_scope_redesign/p1_m10p_20261022/cloud_package/{run_batch3.sh, preflight.sh, pack_results.sh, make_package.sh}`，第四批 `research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/{run_batch4.sh, preflight.sh, make_package.sh}`，以及 `scripts_project/m08a_run_batch.sh`（数据文件中记作 `preflight_b3.sh`、`preflight_b4.sh`、`make_package_b4.sh` 等）。各 shell 引用的脚本：

| shell | 引用的 `scripts_project/` 文件 |
|---|---|
| `run_batch3.sh` | `l23_violation_analysis.py`, `m08a_variants.py`, `m10_batch3_summary.py`, `m12_allocation.py`, `m12_rhs_audit.py`, `s2_solve.py`, `s4d_ledger_redo.py`, `s4o_c1_precision.py`, `v5/gates_v6.py` |
| `run_batch4.sh` | `b4_batch4.py`, `b4_split_solve.py`, `l23_violation_analysis.py`, `m12_allocation.py`, `m12_rhs_audit.py`, `s2_solve.py`, `s4d_ledger_redo.py`, `s4o_c1_precision.py`, `v5/gates_v6.py` |
| `preflight_b3.sh` | `m10_batch3_summary.py` |
| `preflight_b4.sh` | `b4_batch4.py`, `s2_solve.py` |
| `pack_results.sh` | （无） |
| `make_package_b4.sh` | `s2_network.py` |
| `m08a_run_batch.sh` | `l23_violation_analysis.py`, `m08a_variants.py`, `m12_allocation.py`, `m12_rhs_audit.py`, `s2_solve.py`, `s4o_c1_precision.py`, `v5/gates_v6.py` |

- `in_batch_closure`（79 个）：上述被引用脚本的静态 AST import 闭包。**闭包包含函数内的懒加载 import，是上界**，并不意味着批次运行真的会加载它们。
- `in_data_chain`（59 个）：离线需求数据链 7 个起点（`m08b_demand.py`、`m08b_heat_bands.py`、`s3_0_industry.py`、`s2b_feedstock.py`、`s2_0_process_emissions.py`、`m08b_data.py`、`d1_registry.py`）的静态 import 闭包。`m08b_data.py` 导入 `s2_layers.HEAT_BAND_TECH`，由此把整条构建库（`s2_layers.py` 及其依赖）拉进闭包，所以该标志同样是上界。

### 2.3 注册表与测试引用

- `registry_rows`：`research_inputs/registry_v5/DATA_REGISTRY.csv` 中 `derivation_script` 列引用该文件的行数。注册表由 `d1_registry.py` 从 `research_inputs/registry_v5/fragments/*.csv` 汇编，所以有注册表行的脚本大多就是写片段的脚本。
- `tests`：`tests/research/*.py` 中导入或引用该文件的测试。表格中最多列出 3 个测试名，更多时写“等 N 个”。

### 2.4 归类优先级

1. `retired/` 目录 → 已退役。
2. 指令点名的后处理入口（`l23_violation_analysis.py`、`s4o_c1_precision.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s4d_ledger.py`、`s4d_ledger_redo.py`、`v5/gates_v6.py`）及 `s2_solve.py` 求解后引用的 `s4m_duals.py`、`s4m_cost_breakdown.py` → 后处理；批次入口（`m10_batch3_summary.py`、`b4_batch4.py`、`m08a_variants.py`、`m08a_run_batch.sh`）→ 批次与打包。
3. 其余按 `in_build` → 构建、`in_solve` → 求解、`in_post` → 后处理 的顺序取第一个命中（共享核心模块三者皆真时归构建）。`s2_network.py`（构建入口）归构建，`b4_split_solve.py`（分进程求解的进程 2）归求解。
4. 写 `research_inputs` 表或注册表片段的脚本（有 `registry_rows` 或在数据链闭包内）→ 数据链。
5. 文档串自称检查/测试/静态校验/烟测评估/验证器的脚本 → 测试与检查工具（即使它们在静态闭包内，如 `test_gate6_*`）。
6. 其余在静态闭包内、但无任何动态标志的库模块 → 批次与打包的 B 区（Gate4–Gate6 无损/精度/库存审计支持库）。
7. 其余各阶段的提取、汇总、证据脚本 → 一次性；有注册表行写“注册表 N 行”，有测试写测试名，都没有写“无引用（报告证据）”。

### 2.5 追踪盲区（读标志时必须知道）

- **入口脚本不记入自己那次追踪的导入记录。** `l23_violation_analysis.py` 不在 `post_violations` 列表中、却在 `post_c1` 与 `post_owen` 中；`s4o_c1_precision.py` 不在 `post_c1` 中、却在 `post_owen` 中；`m12_allocation.py` 不在 `post_m12` 中、却在 `post_owen` 中；`s4d_ledger_redo.py` 不在 `post_ledger_redo` 列表中；`s2_network.py` 不在构建列表中。因此 `s4d_ledger_redo.py`、`m12_rhs_audit.py`、`v5/gates_v6.py` 的 `in_post` 为假不等于“没有执行”；`m12_rhs_audit.py` 在任何标签的导入列表中都未出现，`post_gates` 与 `post_stopclass` 两个标签的记录为空，它们的归类依据是 shell 引用与指令点名。
- **懒加载。** `--stop-before-solve` 不进入求解后分支，所以 `s4m_duals.py`、`s4m_cost_breakdown.py`（`s2_solve.py` 第 439、465 行）、`s3b_interior.py`（第 488 行）、`netcdf_readback.py`、`validation_dynamics.py`（`v5/v5_gates.py` 第 62、72 行）在追踪中未出现，真实求解会加载它们。
- **静态闭包是上界。** 第 7.2 节 B 区的 15 个库模块来自 `gate6_execution_context.py`、`scenario_network.py`、`build_research_assets.py`、`asset_survival.py`、`integrate_surviving_assets.py` 的函数内 import，追踪中均未触发。
- **`retired/` 的引用解析。** `run_gate6_baseline.py`、`inventory_audit.py`、`finish_gate5_lossless.py` 等用裸模块名 `from fixed_accounts import ...`、`from fixed_inventory_scaling import ...`，而这些模块现在位于 `retired/` 子目录。在 `scripts_project/*.py` 内未检索到把 `retired/` 加入 `sys.path` 的语句，所以这些引用在当前布局下可能无法解析（未实际运行验证）。

## 3. 需求链调用顺序

### 3.1 数据流（有序列表）

下面按“离线生成 → 构建读取”的顺序列出。标注 **[DFX 重跑]** 的是 DFX 需求修复要重跑的 7 个脚本；标注 **[上游，不重跑]** 的脚本，其输出作为输入保留。

1. **输入（不是脚本）。** AEO8（ACE，第 8 版东盟能源展望）表 C.3 / C.8 / D.1 / D.2 的提取表：`research_inputs/registry_v5/sources/AEO8_2050_ASEAN_TOTALS.csv`、`research_inputs/registry_v5/sources/AEO8_2050_BY_COUNTRY.csv`、`research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv`；UN WPP 2024 人口 `research_inputs/demand_v5/sources/m08b/unpopulation_dataportal_20261020224306.csv`；UNSD 2019 冻结重建 `research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json`、`electricity.json`、`FROZEN_ACCEPTED_BUNKER_2019.json`。
2. `d1_demand_2050.py` **[上游，不重跑]**：UNSD 2019 基年 × 桥接 × AEO8 BAS 增长，按国家×部门×载体写**比例表** `research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv`（以及 `_GDP_` / `_POP_` / `_LEVEL_` / `_BRIDGE_GDP_SENSITIVITY.csv` 敏感性表与片段 `fragments/demand_2050.csv`）。在 ATS 锚方法下这张表只提供行结构与 2019 基数（`m08b_demand.py` 中 `RATIO_TABLE` 常量的注释），其 AEO8 常量被 `m08b_demand.py`、`m08b_data.py` 导入。
3. `m08b_demand.py` **[DFX 重跑]**：读比例表，按 AEO8 C.8 人均 TFEC × D.1 人口和 C.3 ATS 部门增长计算部门锚，写 ATS 锚表 `DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv`、国家锚 `DEMAND_ANCHOR_AEO8_ATS.csv`、物理产出 `INDUSTRY_OUTPUT_BASE_M08B.csv`、`INDUSTRY_OUTPUT_PLAN_CAPS.csv`、`INDUSTRY_OUTPUT_2050_M08B.csv` 与证据 `DEMAND_ANCHOR_M08B_EVIDENCE.json`（均在 `research_inputs/demand_v5/`）。
4. `m08b_heat_bands.py` **[DFX 重跑]**：只读 JRC-IDEES-2021 工业工作簿（`pd.read_excel`），写 `INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv` / `.json`；不读需求表，但 `s3_0_industry.py` 与构建都要读它。
5. `s3_0_industry.py` **[DFX 重跑]**：读 ATS 锚表、`INDUSTRY_OUTPUT_2050_M08B.csv`、热量温度带表 `INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv`，以及上游的工业部门比例表 `INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv`（`s3_0_industry_ratios.py` 写）、`INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv`（`s3b_r2_ois_today.py` 写）、`BIOMASS_POTENTIAL_2050.csv`（`d1_biomass.py` 写）；写 `INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv` 及 `_TD_SENSITIVITY`、`_OTHER_USEFUL_HEAT_BANDS` 等变体和片段 `fragments/industry_2050.csv`。
6. `s2_0_process_emissions.py` **[DFX 重跑]**：读比例表、ATS 锚表与 `INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv`（源码注释要求在 `s3_0_industry.py` 之后运行），写 `process_emissions_*` 注册表行（`fragments/process_emissions.csv`，含 `process_emissions_*_2050_ats_anchor_*`）、`PROCESS_EMISSIONS_2019_2050.csv`、`FEEDSTOCK_CARBON_BOUNDARY_2019.csv`。
7. `s2b_feedstock.py` **[DFX 重跑]**：读各需求表的非能源（NEU）行与 `FEEDSTOCK_CARBON_BOUNDARY_2019.csv`，写 `FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_anchor.csv`（及其他分配方式的同名系列，位于 `research_inputs/registry_v5/`）和片段 `fragments/feedstock_territorial.csv`。
   - 顺序说明：指令列出的顺序是 `s2b_feedstock.py` 在 `s2_0_process_emissions.py` 之前，但代码显示 `s2b_feedstock.py` 读取 `s2_0_process_emissions.py` 写出的 `FEEDSTOCK_CARBON_BOUNDARY_2019.csv`；该表只含 2019 量（NEU 2019 与 EDGAR 2019），不随需求修复变化，所以对已有文件两者无硬性先后；全新生成时应让 `s2_0_process_emissions.py` 在先。
8. `m08b_data.py` **[DFX 重跑]**：从构建实际使用的表中取值，写 `fragments/m08b.csv` 与 `fragments/m08b_corrections.csv`（源码头注释：在 `m08b_demand.py`、`m08b_heat_bands.py`、`s3_0_industry.py` 之后运行，然后运行 `d1_registry.py`）。
9. `d1_registry.py` **[DFX 重跑]**：把 `fragments/*.csv`（含上面各步的片段与 `*_corrections`）汇编为 `research_inputs/registry_v5/DATA_REGISTRY.csv`，并写 `DATA_PENDING_LIST.csv`、`D1_EVIDENCE.json`；缺少任一片段即中止。第 175 行（F0 快照位置）把 26 个脚本（含已退役的 `s2b_industry.py`）的 SHA256 写入 `D1_EVIDENCE.json`，这些文件必须存在。
10. **构建** `s2_network.py`：读 `DATA_REGISTRY.csv`；按配置 `research.demand.country_allocation` + `growth_method` 取需求表（`configs/research/baseline.yaml` 的 `tables_by_allocation`，主方案为 ATS 锚表），并把 `FEEDSTOCK_CARBON_BOUNDARY_2019.csv` 等传给下一步。
11. **负荷写入** `s2_layers.add_demand_layer`：读需求表和边界表、`DEMAND_ANCHOR_AEO8_ATS.csv`（`anchor_table`，构建时检查基荷与交通总量）、`INDUSTRY_2050_SUMMARY_*`（路径取自配置 `pypsa_eur_tables`）与 `FEEDSTOCK_CARBON_TERRITORIAL_*`（`territorial_tables`），用 `n.add("Load", ...)` 创建负荷；过程排放从注册表读 `process_emissions_*_2050[_ats_anchor]_*` 行；热量温度带表（`INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv`）与物理产出表（`INDUSTRY_OUTPUT_2050_M08B.csv`）由同文件中的 `heat_band_settings` / `physical_output_settings` 读取。（`s2_layers.py` 正在被 DFX 修改，故此处不写行号。）

执行证据：这 7 个脚本是离线运行的，不在 v1 构建/求解/后处理的动态追踪中。它们的执行依据是：数据链静态闭包（59 个文件）、注册表 `derivation_script`（`s3_0_industry.py` 114 行、`s2b_feedstock.py` 82 行、`s2_0_process_emissions.py` 195 行、`m08b_data.py` 81 行、`d1_registry.py` 17 行）、测试（`test_m08b_demand.py`、`test_m08b_heat.py`、`test_m08b_s01.py`），以及构建在运行时读取它们的输出文件（第 10–11 步）。

### 3.2 四个需求模块家族：哪一个真正执行

| 家族 | 文件 | 状态 | 证据 |
|---|---|---|---|
| Gate2 契约（旧） | `build_research_demand.py`、`check_research_demand.py`、`demand_accounting.py`、`demand_sources.py`、`demand_buildings.py`、`demand_transport.py`、`demand_industry_agriculture.py` | **不在任何生产轨迹中执行**；实质是退役候选，但因有测试而没有归入已退役 | 全部标志为假、`registry_rows` 0；`tests/research/test_demand_accounting.py` 导入 `demand_accounting`、`demand_sources`、`build_research_demand`、`check_research_demand`（`demand_buildings` 等经 `build_research_demand.py` 间接被执行）；`configs/research/baseline.yaml` 第 5 行 `research_demand.builder` 仍写着 `build_research_demand.py`，但 `scripts_project/*.py` 内没有读取该键的代码；Gate2/Gate3 哈希守卫证据 JSON 列有这些文件；`retired/check_research_carriers.py` 导入 `check_research_demand` |
| D1 比例法（上游） | `d1_demand_2050.py`（比例表）、`d1_demand_shares.py`（外生需求侧技术份额） | **上游，不重跑**：输出是输入，代码常量被导入 | `d1_demand_2050.py`：`in_data_chain` 真（被 `m08b_demand.py` / `m08b_data.py` 导入常量）、注册表 94 行；`d1_demand_shares.py`：注册表 47 行 |
| M08b 锚方法（现行） | `m08b_demand.py`（+ `m08b_heat_bands.py`、`m08b_data.py`、`s3_0_industry.py`） | **实际执行**（离线数据链，`growth_method: ats_anchor` 为主方案） | `in_data_chain` 真、`test_m08b_demand.py`；构建读取其 ATS 锚表（`baseline.yaml` 的 `tables_by_allocation.aeo8_ats_anchor` 与 `anchor_table`） |
| 构建侧消费者 | `s2_layers.py` 的 `add_demand_layer` | **实际执行**（构建、求解、后处理三条追踪都导入） | `in_build` / `in_solve` / `in_post` 均真 |

### 3.3 重复实现（F1–F4 只改实际执行的一份，另一份不删除）

| 逻辑 | 实际执行的一份 | 另一份（标出，不删除） | 说明 |
|---|---|---|---|
| 2050 部门总量与非能源（NEU）增长 | `m08b_demand.py`（`growth_method: ats_anchor`，主方案） | `d1_demand_2050.py`（`ratio` / `level` 方法，原主方案；NEU 随工业乘数增长，写入比例表与敏感性表） | ATS 锚表以比例表为行结构与 2019 基数，`ratio` / `level` 仅作敏感性；两份各有一套部门总量逻辑，DFX 的 NEU/RAS 改动只落在 `m08b_demand.py` |
| 工业终端能源 2050 | `s3_0_industry.py`（PyPSA-Eur 比例，JRC-IDEES） | `s2b_industry.py`（R1，技术数据法；已退役，`s3_0_industry.py` 只读其冻结结果 `INDUSTRY_2050_SUMMARY_aeo8_ats_relative_S2B_FROZEN.csv` 作比较列） | 不要删除 `s2b_industry.py`：`d1_registry.py` 仍对其取哈希 |
| 需求账本与部门分账 | `d1_demand_2050.py` + `m08b_demand.py`（数据链）和 `s2_layers.add_demand_layer`（构建） | Gate2 家族 `demand_accounting.py` / `demand_buildings.py` / `demand_transport.py` / `demand_industry_agriculture.py` / `build_research_demand.py` | 旧契约，仅测试覆盖 |
| 非能源（NEU）原料碳 | `s2_layers.add_demand_layer` 的 NonEnergyUse 段（构建时）与 `s2b_feedstock.py`（离线表） | `s2_0_process_emissions.py` 的 2019 边界表（只含 2019 量） | 三处都碰 NEU 的燃料账户，DFX F2/F3 的改动需同时检查 |

### 3.4 DFX 重跑清单与上游依赖

| 脚本 | 角色 | 读取的上游输出（不重跑） |
|---|---|---|
| `m08b_demand.py` | DFX 重跑 | `d1_demand_2050.py`（比例表、AEO8 常量） |
| `m08b_heat_bands.py` | DFX 重跑 | 无（只读 JRC-IDEES 工作簿） |
| `s3_0_industry.py` | DFX 重跑 | `s3_0_industry_ratios.py`（`INDUSTRY_SECTOR_RATIOS_*.csv`）、`s3b_r2_ois_today.py`（`INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv`）、`d1_biomass.py`（`BIOMASS_POTENTIAL_2050.csv`）、`s2_0_cost_layer_v015.py`（technology-data v0.15.0 EUR2020 成本表） |
| `s2_0_process_emissions.py` | DFX 重跑 | `d1_demand_2050.py`（比例表与敏感性表）、`d1_fossil_production.py`（`FOSSIL_PRODUCTION_CAPS_2050.csv`） |
| `s2b_feedstock.py` | DFX 重跑 | `d1_demand_2050.py`、`s2_0_process_emissions.py`（2019 边界表）、`DATA_REGISTRY.csv` 现有行（`share_HVC_primary_fraction_2050`） |
| `m08b_data.py` | DFX 重跑 | 全部既有片段与 `*_corrections`（`m080_data.py`、`m08a_data.py` 等写出），`s2_layers.HEAT_BAND_TECH` |
| `d1_registry.py` | DFX 重跑 | `d1_registry.FRAGMENTS` 列出的全部片段与 3 个 `*_corrections` 文件；要求第 3.1 节第 9 步提到的 26 个脚本文件存在 |

## 4. 生产管线 / 构建（31）

v1 网络构建 `s2_network.py --repo . --scenario <s> --output ...`：S1 骨架 + 成本层 C + CO2/生物质/需求/热层，导出 2920×3h 网络并派生 365×24h 日度网络，不调用求解器。入口排第一行，其后按文件名排序；证据列的动态标志显示该模块是否也被求解、后处理轨迹导入。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `s2_network.py` | 486 | S2 情景构建入口：S1 骨架 + 成本层 C + CO2/生物质/需求/热层，导出 2920×3h 网络并派生 365×24h 日度网络。 | 动态: 未导入；静态: 批次shell+批次闭包；注册表 1 行；测试: test_m08b_s01, test_s4d_4, test_s4d_6；构建入口脚本：以 __main__ 运行，不记入自己那次追踪的导入列表；make_package 引用它 |
| `assembly_components.py` | 169 | 共享的生产/合成装配机制（合并输入组件、校验钩子、全局约束检查），不含求解器与科学默认值。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_hydro_policy_separation, test_s1_adapter_daily_v5, test_surviving_asset_integration |
| `build_research_assets.py` | 237 | 构建真实的 Gate4 开发资产（含碳载体片段 build_fragment），不做优化、不含求解容量。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包 |
| `build_research_network.py` | 128 | S1 对未求解研究情景网络的静态校验（取代 Assembly V1 守卫）；s2_network.py 引用其 REQUIRED_PER_NODE，构建追踪中被导入。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_s1_built_networks |
| `carrier_architecture.py` | 348 | 国家/节点载体片段，不做全网装配、不含求解器。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_carrier_carbon, test_gate4_continue 等 4 个 |
| `country_carbon.py` | 140 | 分国家大气核算与 2050 净零上限（S1-5，决策 9、10）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s1_built_networks, test_s1_country_carbon |
| `d1_common.py` | 288 | D1 共享辅助：注册表行、哈希、单位常量、research_inputs 目录常量。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_d1_registry, test_m08a_a1；构建追踪中被导入，同时是整个数据链脚本（d1_*/m08b_*/s2b_*/s3_0_*）的共享库 |
| `daily_resolution.py` | 45 | 把 2920×3h 未求解研究网络精确归约为 365×24h（S1-8 输入）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s1_adapter_daily_v5 |
| `m08a_layers.py` | 426 | M08a 构建层（决策 129–133）；s2_network.py 导入 apply_existing_vintage_costs，本身不求解。 | 动态: 构建+变体；静态: 批次闭包；注册表 2 行；测试: test_m08a_a3, test_m08a_a7 |
| `network_checks.py` | 63 | 从已退役 build_diagnostic_network.py 保留下来的无求解器网络辅助函数（S1-2）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包 |
| `phase4_static.py` | 188 | 只读 Phase4 校验钩子与配置读取，从不装配模型或调用 optimize。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_m08a_a2, test_m08a_a3 等 27 个 |
| `s1_candidates.py` | 97 | S1-4 发电/储能候选与分技术成本缩放层（决策 37–41）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s1_scenario_switches |
| `s2_costs.py` | 183 | S2-1：由有效成本层生成供网络构建器使用的研究成本表（决策 46、50、52）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；注册表 4 行；测试: test_m08a_a1, test_m08a_a2 等 6 个 |
| `s2_layers.py` | 1161 | 在 S1 骨架之上的 S2 组件层（CO2、生物质、工业热与 add_demand_layer 等；不在需求所有权表之外创建 Load）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_m08a_a5, test_m08b_demand 等 8 个 |
| `s3_layers.py` | 460 | 在 S2 情景网络之上的 S3 模型层（气网、进口、氨/甲醇、燃料碳模式）。 | 动态: 构建；静态: 批次闭包；注册表 1 行；测试: test_m08a_a4 |
| `s4a_fleet.py` | 187 | S4A-2（L15）：把 2050 年在运但冻结电力基线中缺失的 GEM 机组加入网络。 | 动态: 构建；静态: 批次闭包 |
| `s4a_layers.py` | 235 | S4A-1（L14）：重建电力基线风光候选的可用率曲线（含 s4b_3 的 calibrated_modern 变体与 M08a 海上分类）。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_m08a_a6, test_s4a_profiles |
| `s4b_candidates.py` | 136 | S4B-2（决策 78、79）：把地热/新建水电/新建抽蓄上限及核电计划上限套用到 S1 站点候选。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；注册表 1 行 |
| `s4b_layers.py` | 121 | S4B-0（决策 70）：与 PyPSA-Eur v2025.07.0 sector 默认值对齐的部门技术开关；含台风溢价。 | 动态: 构建；静态: 批次闭包 |
| `s4c_layers.py` | 708 | S4C 模型层（决策 82–90）：成本层、WACC、水电入流归一化、燃油舱归属、东盟外封存等。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；注册表 1 行；测试: test_m08a_a6, test_m08a_a7 等 6 个 |
| `s4d_layers.py` | 217 | S4D 模型层（决策 91–93）：东盟内 CO2 海运、沿海节点出口等。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_m08a_a5, test_s4d_1 等 6 个 |
| `s4e_layers.py` | 202 | S4E 模型层（决策 94–95）：走廊直流链路、国内候选、老挝过境航运。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_s4e_1, test_s4e_2, test_s4g_2 |
| `s4f_layers.py` | 225 | S4F 模型层（决策 96–97）：老挝-越南存储、最大扩容、泰马存量、可选走廊。 | 动态: 构建；静态: 批次闭包+数据链闭包；测试: test_s4f_1, test_s4f_2 |
| `s4g_layers.py` | 100 | S4G 模型层（决策 98–99）：老挝-泰国储存、交流线路阻抗重设。 | 动态: 构建；静态: 批次闭包；测试: test_s4g_1, test_s4g_2 |
| `s4h_layers.py` | 99 | S4H 模型层（决策 100–101）：候选并联数、老越存量。 | 动态: 构建；静态: 批次闭包；测试: test_s4h_1, test_s4h_2 |
| `s4j_layers.py` | 196 | S4J 模型层（决策 104–106）：直流换流器规则与输电损耗。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s4j_2, test_s4j_3 |
| `s4k_layers.py` | 160 | S4K 模型层（决策 108）：交流线路线性损耗代理。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s4k_1 |
| `s4l_layers.py` | 329 | S4L 模型层（决策 113(1)）：近零量（dust）清单与清理（apply_dust_cleanup）。 | 动态: 构建；静态: 批次闭包；测试: test_s4l_1 |
| `scenario_network.py` | 265 | S1 情景构建器：冻结电力基线 + 上游氢库 + 研究载体配方。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_m08a_a7, test_s1_scenario_switches 等 4 个 |
| `sector_adapter.py` | 142 | 对上游 prepare_sector_network.py 的适配器，作为组件库使用（S1-1，R0）。 | 动态: 构建+求解+后处理；静态: 批次闭包+数据链闭包；测试: test_s1_adapter_daily_v5, test_s4b_0 |
| `v5/__init__.py` | 2 | V5 验收骨架包（S1-7）；A 组复用冻结 V4 代数，B 组为新增。 | 动态: 构建+求解 |

## 5. 生产管线 / 求解（10）

`s2_solve.py`（含 `--stop-before-solve` 与 `--split-stage build`）及仅在求解路径被导入的模块；`b4_split_solve.py` 是分进程求解的进程 2。构建与求解共用的核心模块已归入第 4 节。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `asset_survival.py` | 32 | 2050 年机组年龄/状态的显式筛选；缺失证据既不当零也不当无穷。 | 动态: 求解+后处理；静态: 批次闭包+数据链闭包；测试: test_gate4_selected_closure, test_limited_ocgt_and_blend_bounds, test_source_scope |
| `b4_split_solve.py` | 207 | 分进程求解的进程 2：只用 gurobipy/numpy/psutil 读入已构建的 LP 并求解。 | 动态: 未导入；静态: 批次shell+批次闭包；测试: test_b4p_split；进程 2 不导入 scripts_project 内其他模块，故动态标志为空；run_batch4.sh 调用 |
| `gate5_resources.py` | 122 | 只读的 Gate5 准入、有界监控与当前历史选择（求解路径导入其 sha 等辅助）。 | 动态: 求解+后处理；静态: 批次闭包+数据链闭包 |
| `gate6_execution_context.py` | 130 | 与声明绑定的 Gate6 能力对象：元数据只作溯源、从不构成许可（求解路径导入）。 | 动态: 求解+后处理；静态: 批次闭包+数据链闭包 |
| `integrate_surviving_assets.py` | 182 | 物化已通过资格审查的现有机组，不推断日期、映射与成本。 | 动态: 求解+后处理；静态: 批次闭包+数据链闭包；测试: test_gate4_activation, test_hydro_policy_separation, test_surviving_asset_integration |
| `s1_solve.py` | 165 | S1 求解驱动：LP 构建、一次求解、原始/对偶导出、V5 A 组与 B1/B11/B12 闸门。 | 动态: 求解+后处理；静态: 批次闭包 |
| `s2_solve.py` | 567 | S2 求解驱动（含 --stop-before-solve 与 --split-stage build），求解后调用 V5 闸门、账本与导出。 | 动态: 求解+后处理；静态: 批次shell+批次闭包；测试: test_b4p_batch4, test_b4p_split 等 6 个 |
| `s3b_scaling.py` | 194 | S3B R4：在模型创建与求解之间对 linopy 模型做 LP 缩放，网络本身不变。 | 动态: 求解+后处理；静态: 批次闭包；测试: test_s3b_r4, test_s4c_5 |
| `v5/kkt_algebra.py` | 189 | 为 V5 A 组原样复用的 V4 KKT 代数（S1-7）。 | 动态: 求解 |
| `v5/v5_gates.py` | 406 | V5 闸门骨架（S1-7）：A 组复用冻结 V4 代数与物理，B 组为新增；s2_solve.py 求解后调用 A1–A6 与 B 组闸门。 | 动态: 求解；静态: 批次闭包；测试: test_m08a_a4, test_s4d_4, test_s4d_6 |

## 6. 生产管线 / 后处理（10）

求解后的验收、精度证据、账本与分摊：批次脚本（`run_batch3.sh`、`run_batch4.sh`、`m08a_run_batch.sh`）逐次调用其中的入口脚本；`s4m_duals.py`、`s4m_cost_breakdown.py` 由 `s2_solve.py` 求解后懒加载。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `l23_violation_analysis.py` | 202 | L23 C9（用户补充 2026-10-19）：对非最优求解做只读原始违反量分析（不调用求解器、不改参数）。 | 动态: 后处理；静态: 批次shell+批次闭包；批次脚本逐次调用；被 s4o_c1_precision.py 导入 |
| `m12_allocation.py` | 994 | M12 C1：系统成本按 Owen（1975）分摊到 11 国与国际燃油舱第 12 参与者。 | 动态: 后处理；静态: 批次shell+批次闭包；测试: test_m10r_keepstock_ledger, test_m12_allocation |
| `m12_rhs_audit.py` | 785 | M12 C2：Owen 分摊所依据 LP 的右端项归因审计（用 linopy 重建同一模型）。 | 动态: 未导入；静态: 批次shell+批次闭包；测试: test_m10r_keepstock_ledger, test_m12_allocation |
| `s4b_acceptance.py` | 356 | S4B-0（决策 71 方案 1）：与 Gurobi 容差挂钩、含行活动相对项的验收预算（all_passed 等判定）。 | 动态: 后处理；静态: 批次闭包；测试: test_s4b_0, test_s4d_3；后处理追踪中被导入；s4d_ledger_redo.py 用其 all_passed 重算 B16_LEDGER 标志 |
| `s4d_ledger.py` | 308 | S4D-3（决策 91a）：国家成本账本、恒等闸门 B16_LEDGER 与节点电价（求解后、对已解网络只读）。 | 动态: 后处理；静态: 批次闭包；注册表 1 行；测试: test_m08a_a9, test_m10r_keepstock_ledger 等 4 个；被 m12_allocation.py 与 s4d_ledger_redo.py 导入 |
| `s4d_ledger_redo.py` | 118 | M10R（第三批收尾）：对已求解运行重算国家成本账本导出（修复保留存量账本缺陷），不调用求解器。 | 动态: 未导入；静态: 批次shell+批次闭包；测试: test_m10r_keepstock_ledger；run_batch3.sh / run_batch4.sh 调用；入口脚本本身不计入追踪导入记录 |
| `s4m_cost_breakdown.py` | 265 | S4M 补充 01（S4M-S1 第 3 项/S4M-S2）：分组件资本成本拆分导出（只读，不改模型）。 | 动态: 未导入；静态: 批次闭包；测试: test_s4m_cost_breakdown；s2_solve.py 求解后懒加载（--stop-before-solve 路径不触发） |
| `s4m_duals.py` | 131 | S4M 补充 01：按约束名导出约束对偶（仅导出）。 | 动态: 未导入；静态: 批次闭包；测试: test_s4m_duals；s2_solve.py 求解后懒加载（--stop-before-solve 路径不触发） |
| `s4o_c1_precision.py` | 428 | S4O-2（决策 120）：运行管线中的逐运行精度证据（决策 119 C1），只读、仅 Python、不调用求解器。 | 动态: 后处理；静态: 批次shell+批次闭包；测试: test_s4o_2；批次脚本逐次调用；GATES_V6 的 G1 标准来源 |
| `v5/gates_v6.py` | 330 | GATES_V6（决策 128、133）：仅依据返回的解与导出文件的求解后验收（G1=C1、G2 结构检查），含批次运行规则；从不调用求解器。 | 动态: 构建+求解；静态: 批次shell+批次闭包；注册表 1 行；测试: test_m08a_a8, test_m08a_a9 等 4 个；追踪标志显示构建/求解已导入（s2_network.py 导入 config_subset_sha256），作为入口脚本在后处理链中执行（accept / select-profile / formal-check） |

## 7. 生产管线 / 批次与打包（19）

### 7.1 A 区：批次入口与辅助（4）

被批次/打包 shell 直接引用，或是批次运行表与变体生成器。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `b4_batch4.py` | 378 | B4P 第四批的运行表与只读辅助函数，供 run_batch4.sh 与 preflight 调用。 | 动态: 未导入；静态: 批次shell+批次闭包；测试: test_b4p_batch4, test_b4p_split |
| `m08a_run_batch.sh` | 221 | M08a A8（决策 133）：无人值守第三/第四批的运行脚本（规则先于运行登记）。 | 动态: 未导入；测试: test_m08a_a8, test_m12_allocation；shell 脚本，追踪标志不适用；它引用 l23_violation_analysis、m08a_variants、m12_*、s2_solve、s4o_c1_precision、v5/gates_v6 |
| `m08a_variants.py` | 167 | M08a A7：由已构建基础网络确定性生成情景/联盟/融资变体（--help 追踪仅导入 m08a_layers）。 | 动态: 变体；静态: 批次shell+批次闭包；注册表 1 行；测试: test_m08a_a7 |
| `m10_batch3_summary.py` | 523 | M10P：第三批运行表、时间表与只读辅助函数，供 run_batch3.sh 与 preflight 调用，并被 b4_batch4.py 导入。 | 动态: 未导入；静态: 批次shell+批次闭包；测试: test_m10p_batch3, test_m10r_s1_modes；56 快照后处理链的追踪入口之一，故不记入导入列表 |

### 7.2 B 区：仅静态闭包可达的 Gate4–Gate6 支持库（15）

这些模块在批次/打包脚本的静态 import 闭包内（经 `gate6_execution_context.py`、`scenario_network.py`、`build_research_assets.py`、`asset_survival.py`、`integrate_surviving_assets.py` 等的函数内 import 到达），但 2026-10-26 的所有追踪都没有导入它们，`registry_rows` 全为 0。它们是 Gate4–Gate6 无损导出、精度交接、库存审计的遗留库，不在 v1 构建/求解/后处理的活动路径上。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `carbon_architecture.py` | 181 | 电力政策口径与物理全系统 CO2 报告口径分离的视图（Gate4–6 遗留库，有测试）。 | 动态: 未导入；静态: 批次闭包+数据链闭包；测试: test_carrier_carbon, test_final_closure 等 4 个 |
| `closeout_gate5_metadata.py` | 153 | 以证据为门槛的仅元数据衍生品（Gate5 收尾），不建模型、不调用求解器。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `execute_gate5_lossless.py` | 67 | 仅在既有真实运行授权之后调用的分离式无损集成（Gate5）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `finish_gate5_lossless.py` | 110 | 后续另行授权的 Gate5 执行的求解后消费者。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `gate5_cloud_resources.py` | 116 | Linux cgroup 传输适配器，不改模型与数值选项。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `gate6_result.py` | 96 | 仅用于 Gate6 的求解后处理：一次原生读取，再做证据门控的元数据定稿。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `inventory_audit.py` | 81 | 来源身份审计与先验舍入预算，不改来源（Gate5 库存）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `inventory_audit_3h.py` | 87 | 原始 3h 来源链审计，不做日均、不建模、不求解（Gate5/6）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `lossless_gate5_lifecycle.py` | 330 | 分离式无损 Gate5 所有权原语；本模块从不运行求解器。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `precision_handoff.py` | 260 | 冻结 Linopy 0.5.5 的 float64、限内存 HiGHS 交接（Gate5/6 库）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `price_basis.py` | 152 | 研究侧 EUR2020 价格层，保留冻结来源值与先前换算（scenario_network.build_scenario、build_research_assets 懒加载）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `run_gate5_validation.py` | 89 | 仅限授权的 Gate5 验证运行，从不启动 Gate6 或正式实验。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `run_gate6_baseline.py` | 205 | Gate6 基线：默认文件预检，显式的测试/构建/求解边界（gate6_execution_context.py 懒加载其 resource_admission）。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `selected_closure.py` | 131 | Gate4 显式选择、来源固定的资源分配与成本语义（asset_survival.py、build_research_assets.py、integrate_surviving_assets.py 懒加载）。 | 动态: 未导入；静态: 批次闭包+数据链闭包；测试: test_gate4_selected_closure |
| `validation_temporal.py` | 40 | 全年时间归约（仅输入、按组件守恒），run_gate5_validation.py 使用。 | 动态: 未导入；静态: 批次闭包+数据链闭包；测试: test_validation_temporal |

## 8. 数据链（离线生成 research_inputs 表与注册表片段，87）

这些脚本离线运行，写 `research_inputs/` 下的表和 `research_inputs/registry_v5/fragments/*.csv` 注册表片段，`d1_registry.py` 再汇编成 `DATA_REGISTRY.csv`。构建与求解不运行它们，只读它们的输出。

### 8.1 DFX 需求修复重跑（7）

执行顺序见第 3.1 节。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `m08b_demand.py` | 288 | M08b B1：AEO8 ATS 活动锚与 aeo8_ats_anchor 需求表，写 ATS_ANCHOR 表、DEMAND_ANCHOR_AEO8_ATS.csv、INDUSTRY_OUTPUT_*_M08B.csv。 | 动态: 未导入；静态: 数据链闭包；测试: test_m08b_demand；DFX 重跑；DFX 修复的需求入口 |
| `m08b_heat_bands.py` | 118 | M08b B2：JRC-IDEES-2021 其他工业桶的温度带拆分，写 INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv。 | 动态: 未导入；静态: 数据链闭包；测试: test_m08b_heat；DFX 重跑；只读 JRC-IDEES 工作簿，不读需求表 |
| `s3_0_industry.py` | 460 | S3-0.1（决策 61）：用复现的 PyPSA-Eur 部门比例求 ASEAN 工业终端能源 2050，含 M08b aeo8_ats_anchor 与有用热桶变体，写 INDUSTRY_2050_SUMMARY_*.csv。 | 动态: 未导入；静态: 数据链闭包；注册表 114 行；DFX 重跑；读取 ATS_ANCHOR 表、INDUSTRY_OUTPUT_2050_M08B.csv、INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv |
| `s2_0_process_emissions.py` | 175 | S2-0.3：工业过程排放、逸散排放与化工原料边界（EDGAR 2025），写 process_emissions 片段与 PROCESS_EMISSIONS_2019_2050.csv。 | 动态: 未导入；静态: 数据链闭包；注册表 195 行；DFX 重跑；须在 s3_0_industry.py 之后（读取 INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv 与 ATS_ANCHOR 表） |
| `s2b_feedstock.py` | 168 | R2（决策 56）：领土口径的化工原料碳，写 FEEDSTOCK_CARBON_TERRITORIAL_2050_*.csv 与 feedstock_territorial 片段。 | 动态: 未导入；静态: 数据链闭包；注册表 82 行；DFX 重跑 |
| `m08b_data.py` | 402 | M08b 及补充 01 的注册表行（需求锚定/有用热步骤），写 fragments/m08b.csv 与 m08b_corrections.csv。 | 动态: 未导入；静态: 数据链闭包；注册表 81 行；测试: test_m08b_s01；DFX 重跑；须在 m08b_demand / m08b_heat_bands / s3_0_industry 之后、d1_registry 之前运行；导入 s2_layers.HEAT_BAND_TECH，故其静态闭包涵盖整条构建库 |
| `d1_registry.py` | 185 | D1 第 1/6/7 节：由各 d1_* 及后续步骤的片段汇编 DATA_REGISTRY.csv，并写下载清单、DATA_PENDING 清单与 D1_EVIDENCE.json。 | 动态: 未导入；静态: 数据链闭包；注册表 17 行；DFX 重跑；第 175 行把 26 个脚本（含 s2b_industry.py）的 SHA256 写入 D1_EVIDENCE.json，这些文件必须存在 |

### 8.2 上游基础表与片段，不重跑（22）

D1、S2-0、S3、S3B、M08-0、M08a 阶段的基础表与注册表片段。输出作为输入保留；DFX 不重跑它们。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `d1_biomass.py` | 504 | D1 第 5 节（决策 31、32）：按国家×类别的 2050 可持续生物质供给潜力，写 BIOMASS_POTENTIAL_2050.csv。 | 动态: 未导入；注册表 264 行；输出被 s2_network.py 与 s3_0_industry.py 读取（上游，DFX 不重跑） |
| `d1_co2_storage.py` | 156 | D1 第 1 节：CO2 地质封存潜力与年注入上限（决策 28–30）。 | 动态: 未导入；注册表 34 行 |
| `d1_cost_layers.py` | 284 | D1 第 2 节（决策 46 方案 A）：两个已登记的成本层与作者 AEO8 规则。 | 动态: 未导入；注册表 67 行；测试: test_d1_registry |
| `d1_demand_2050.py` | 492 | D1 第 3 节（决策 22、34）：2050 年国家×部门×载体终端能源需求比例表，写 DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv 及敏感性表。 | 动态: 未导入；静态: 数据链闭包；注册表 94 行；上游，DFX 不重跑；输出是 m08b_demand.py / s3_0_industry.py / s2b_feedstock.py / s2_0_process_emissions.py 的输入，其 AEO8 常量被 m08b_demand.py、m08b_data.py 导入 |
| `d1_demand_shares.py` | 146 | D1 第 4 节（决策 21）：PyPSA-Eur v2025.07.0 的外生需求侧技术份额。 | 动态: 未导入；注册表 47 行 |
| `d1_fossil_production.py` | 105 | D1 第 1 节：基于 UNSD 2019 能源统计的国内化石燃料产量上限。 | 动态: 未导入；注册表 66 行；输出 FOSSIL_PRODUCTION_CAPS_2050.csv 被 s2_0_process_emissions.py 与 s3_1_gas_data.py 读取 |
| `d1_fuel_prices.py` | 128 | D1 第 1 节：基于 WEO 2025 表 2.3 的 2050 化石燃料进口价格。 | 动态: 未导入；注册表 27 行 |
| `d1_lng_terminals.py` | 141 | D1 第 1 节：GEM GGIT LNG 接收站（2025-09）并映射到最近网络节点。 | 动态: 未导入；注册表 57 行 |
| `m080_data.py` | 491 | M08-0（条目 130）：注册表回填与一致性修正，只动注册表（写 m080 片段与 m080_corrections）。 | 动态: 未导入；注册表 95 行 |
| `m08a_data.py` | 532 | M08a（决策 129–133）：实施步骤的注册表行（无构建、无求解；写 m08a 片段与 m08a_corrections）。 | 动态: 未导入；注册表 71 行 |
| `s2_0_cost_layer_v015.py` | 306 | S2-0.1（决策 50）：technology-data v0.15.0 成本层换算为 EUR2020，作为新主层。 | 动态: 未导入；注册表 188 行；输出的 technology_data_v0.15.0_EUR2020 成本表被 s3_0_industry.py 读取（上游，不重跑） |
| `s3_0_corridors.py` | 147 | S3-0（决策 59/62）：APG AIMS III 走廊（泰-缅、老-缅）并入走廊表，并交叉核对。 | 动态: 未导入；注册表 8 行 |
| `s3_0_industry_ratios.py` | 219 | S3-0.1（决策 61）：由 JRC-IDEES-2021（EU27）复现 PyPSA-Eur v2025.07.0 工业部门比例。 | 动态: 未导入；注册表 55 行；输出 INDUSTRY_SECTOR_RATIOS_*.csv 被 s3_0_industry.py 读取（上游，不重跑） |
| `s3_1_gas_data.py` | 136 | S3-1 数据层：现有跨境天然气管道（GEM GGIT 2025-11）、国内产量上限与 LNG 参考。 | 动态: 未导入；注册表 27 行 |
| `s3_2_imports_data.py` | 108 | S3-2 数据层：东盟外进口价格（决策 17/18/64），写 IMPORT_PRICES_2050.csv。 | 动态: 未导入；注册表 18 行；输出被 s3_layers.py 读取 |
| `s3_3_ammonia_methanol_data.py` | 53 | S3-3（决策 44）：氨/甲醇层参数的注册表片段。 | 动态: 未导入；注册表 8 行 |
| `s3_4_shipping_data.py` | 64 | S3-4（决策 10）：航运需求的注册表片段。 | 动态: 未导入；注册表 9 行 |
| `s3_5_fuel_carbon_data.py` | 47 | S3-5（决策 64）：燃料碳归属模式与 PyPSA-Eur 燃料来源核对的注册表片段。 | 动态: 未导入；注册表 5 行 |
| `s3_7_import_price_decline.py` | 85 | S3-7（用户补充 2026-10-16 第 1 项）：进口供应链 2040→2050 的成本下降，写 research_inputs/imports_v5。 | 动态: 未导入；注册表 16 行 |
| `s3b_r2_ois_today.py` | 103 | S3B R2（决策 67）：JRC-IDEES-2021 EU27 2019 年其他工业部门（OIS_fec）的载体结构。 | 动态: 未导入；注册表 9 行；输出 INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv 被 s3_0_industry.py 读取（上游，不重跑） |
| `s3b_r3_lng_data.py` | 102 | S3B R3（决策 68）：LNG 再气化终端扩容与马-新管道容量（lng_r3 片段）。 | 动态: 未导入；注册表 5 行 |
| `s3b_r4_solver_data.py` | 48 | S3B R4（决策 69）：求解器配置、缩放规则与内点阈值的注册表片段。 | 动态: 未导入；注册表 15 行 |

### 8.3 阶段性注册表片段与输入表生成（S3B–S4O，不重跑，58）

各阶段（S4A–S4O、M08a 海上风电）的注册表片段（`*_data.py`）和输入表生成脚本（出力曲线、候选上限、沿海节点、海运路线、长度占比等）。证据列注明其输出被哪个构建层或账本读取。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `m08a_offshore_profiles.py` | 257 | M08a A6.2：海上风电合格面积、潜力与 3h 出力曲线，输出到 research_inputs/renewable_v5/offshore_m08a。 | 动态: 未导入；测试: test_m08a_a6；输出被 s4a_layers.py 读取（上游，不重跑） |
| `s4a_1_data.py` | 97 | S4A-1（L14，决策 70–73）：注册表片段 renewable_s4a（再分析来源、曲线链参数等）。 | 动态: 未导入；注册表 39 行 |
| `s4a_1_export.py` | 52 | S4A-1：把重建的出力曲线（s4a_profiles.py 输出）压缩导出到 research_inputs/renewable_v5。 | 动态: 未导入；输出被 s4a_layers.py 读取（上游，不重跑） |
| `s4a_2_fleet_data.py` | 172 | S4A-2（L15）：现有机组对 GEM 全球电力追踪表的覆盖核对，及 2050 需补充机组，写 FLEET_ADDITIONS_2050.csv。 | 动态: 未导入；注册表 28 行；输出被 s4a_fleet.py 读取 |
| `s4a_3_potentials.py` | 286 | S4A-3（L16，决策 39）：新建候选潜力 p_nom_max 及其公开来源的审计，写 research_inputs/potentials_v5。 | 动态: 未导入；注册表 88 行 |
| `s4a_profiles.py` | 215 | S4A-1（L14，决策 70–73）：由 ERA5 重建各研究节点的风光可用率曲线，输出供 s4a_1_export.py 导出。 | 动态: 未导入；注册表 1 行；输出经 s4a_1_export.py 进入 research_inputs/renewable_v5（上游，不重跑） |
| `s4b_0_data.py` | 156 | S4B-0：决策 70 开关表（模型与 PyPSA-Eur sector 块对比）及决策 70–73 的注册表片段，写 SECTOR_SWITCHES_VS_PYPSA_EUR.csv。 | 动态: 未导入；注册表 14 行；输出被 s4b_layers.py 读取 |
| `s4b_1_fleet_data.py` | 130 | S4B-1（决策 77）：2050 现有存量规则（移除已取消/封存/退役机组）。 | 动态: 未导入；注册表 16 行 |
| `s4b_2_candidates_data.py` | 243 | S4B-2（决策 78、79）：地热、新建水电与抽蓄候选上限、节点分配与核电计划上限，写 CANDIDATE_CAPS_S4B2_BY_NODE.csv。 | 动态: 未导入；注册表 41 行；输出被 s4b_candidates.py 读取 |
| `s4b_3_data.py` | 59 | S4B-3 注册表片段（决策 74、75）：陆上风电观测 CF、校准系数、风机、出力曲线变体与局限。 | 动态: 未导入；注册表 21 行 |
| `s4b_3_export.py` | 56 | S4B-3：把 profile_variant=calibrated_modern 的出力曲线导出到 research_inputs/renewable_v5（格式同 s4a_1_export.py）。 | 动态: 未导入；输出被 s4a_layers.py 读取 |
| `s4b_3_wind_calibration.py` | 183 | S4B-3（决策 74、75）：对照观测发电量（Staffell & Pfenninger 2016）校准陆上风电，写 WIND_CALIBRATION_ALPHA.csv。 | 动态: 未导入；测试: test_s4b_3；输出被 s4a_profiles.py 读取 |
| `s4b_4_data.py` | 51 | S4B-4 注册表片段（决策 76）：台风暴露、溢价开关与延期的海上条目。 | 动态: 未导入；注册表 9 行 |
| `s4b_4_typhoon.py` | 134 | S4B-4（决策 76）：由 IBTrACS v04r01 计算风电候选的热带气旋暴露，写 TYPHOON_EXPOSURE_BY_NODE.csv。 | 动态: 未导入；输出被 s4b_layers.py 读取 |
| `s4c_0_data.py` | 162 | S4C-0（决策 85、86、90）：注册表片段 s4c_0 与融资表。 | 动态: 未导入；注册表 31 行 |
| `s4c_1_data.py` | 90 | S4C-1 注册表片段（决策 82；补充 01 / 决策 16）。 | 动态: 未导入；注册表 13 行 |
| `s4c_1_offwind_distance.py` | 181 | S4C-1 第 2 项（决策 82）：各节点×资源类别的海上风电并网距离，写 OFFWIND_CONNECTION_DISTANCE_S4C1.csv。 | 动态: 未导入；输出被 s4c_layers.py 读取 |
| `s4c_1_subsea_shares.py` | 189 | S4C-1 第 5 项（补充 01，决策 16）：各跨境走廊的海底段几何占比，写 research_inputs/corridors。 | 动态: 未导入；注册表 1 行 |
| `s4c_2_data.py` | 71 | S4C-2（决策 83）：国家水电入流目标及注册表片段 s4c_2。 | 动态: 未导入；注册表 12 行 |
| `s4c_3_data.py` | 53 | S4C-3（决策 88，修改决策 10）：注册表片段 s4c_3（燃油舱归属开关与 CO2 账户规则）。 | 动态: 未导入；注册表 7 行 |
| `s4c_4_data.py` | 147 | S4C-4（决策 89）：东盟外 CO2 封存选项单位成本（液化+远洋运输）。 | 动态: 未导入；注册表 8 行 |
| `s4d_0_data.py` | 70 | S4D-0：注册表片段 s4d_0（用户对 S4C 报告第 8 节十项决策的回答）。 | 动态: 未导入；注册表 11 行 |
| `s4d_1_coastal_nodes.py` | 130 | S4D-0 第 2 项/S4D-1 第 1 项（决策 93）：各节点 CO2 链清单与沿海节点表，写 COASTAL_NODES_S4D1.csv 与 PORTS_ASEAN_TO_NODES_S4D1.csv。 | 动态: 未导入；输出被 s4e_layers.py 与 s4d_1_data.py 读取 |
| `s4d_1_coastline.py` | 133 | S4D-1 第 1 项（决策 93）：以物理海岸线（方案 A）确定沿海节点，写 COASTAL_NODES_S4D1_FINAL.csv。 | 动态: 未导入；输出被 s4d_layers.py 读取 |
| `s4d_1_data.py` | 213 | S4D-1 数据（决策 93）：CO2 仅沿海节点出口、老挝过境定价，写 LAO_TRANSIT_S4D1.csv 与注册表片段 s4d_1。 | 动态: 未导入；注册表 17 行；输出被 s4e_layers.py 读取 |
| `s4d_2_data.py` | 96 | S4D-2 数据（决策 92 修订）：两种情景下的东盟内 CO2 海运，注册表片段 s4d_2。 | 动态: 未导入；注册表 8 行 |
| `s4d_2_ship_routes.py` | 130 | S4D-2（决策 92）：沿海节点间海路距离与航运路线系数，写 CO2_SHIP_ROUTES_S4D2.csv。 | 动态: 未导入；输出被 s4d_layers.py 与 s4e_layers.py 读取 |
| `s4d_3_data.py` | 136 | S4D-3 数据（决策 91a）：跨境组件的境内长度占比（账本敏感性）、账本规则与只读检查，写 XB_LENGTH_SHARES_S4D3.csv。 | 动态: 未导入；注册表 5 行；输出被 s4d_ledger.py 读取 |
| `s4d_6_data.py` | 38 | S4D-6 数据：第一批敏感性的注册表片段 s4d_6（已登记，未打包未运行）。 | 动态: 未导入；注册表 4 行 |
| `s4e_0_data.py` | 42 | S4E-0：注册表片段 s4e_0（用户对 S4D 报告第 9 节八项决策的回答）。 | 动态: 未导入；注册表 9 行 |
| `s4e_1_corridors.py` | 329 | S4E-1（决策 94，落实决策 15）：补全相邻跨境走廊。 | 动态: 未导入；注册表 8 行 |
| `s4e_1_length_shares.py` | 26 | S4E-1：S4E 互联构建中每条跨境线路/链路的境内长度占比，写 XB_LENGTH_SHARES_S4E1.csv。 | 动态: 未导入；输出被 s4d_ledger.py 读取 |
| `s4e_2_data.py` | 57 | S4E-2（决策 95）：统一 CO2 封存成本基准与分国对海运距离的注册表片段。 | 动态: 未导入；注册表 6 行 |
| `s4f_0_data.py` | 40 | S4F-0：注册表片段 s4f_0（用户对 S4E 报告第 7 节七项决策的回答）。 | 动态: 未导入；注册表 7 行 |
| `s4f_1_data.py` | 109 | S4F-1 数据（决策 96）：PyPSA-Eur 单条线路/链路扩容上限的注册表片段。 | 动态: 未导入；注册表 5 行；测试: test_s4f_1 |
| `s4f_2_corridors.py` | 243 | S4F-2（决策 97 a、b、d）：泰马存量修正表、APG #4 印尼端点、新马/新越可选候选。 | 动态: 未导入；注册表 10 行 |
| `s4f_2_length_shares.py` | 26 | S4F-2：S4F 互联构建（含新-越/新-柬可选候选）每条跨境线路的境内长度占比，写 XB_LENGTH_SHARES_S4F2.csv。 | 动态: 未导入；输出被 s4d_ledger.py 读取 |
| `s4g_0_data.py` | 36 | S4G-0：注册表片段 s4g_0（用户对 S4F 报告第 7 节四项决策的回答）。 | 动态: 未导入；注册表 4 行 |
| `s4g_1_data.py` | 118 | S4G-1 数据（决策 98）：作者 readjust 设置的 19 条跨境交流线路的电气参数，写 READJUST_IMPEDANCE_S4G1.csv。 | 动态: 未导入；注册表 3 行；测试: test_s4g_1 |
| `s4g_2_data.py` | 33 | S4G-2 数据（决策 99 a、b）：老挝过境 existing_port 敏感性的泰国国家储存，apg_plans 规则确认。 | 动态: 未导入；注册表 3 行 |
| `s4h_0_data.py` | 37 | S4H-0：注册表片段 s4h_0（用户对 S4G 报告第 7 节四项决策的回答）。 | 动态: 未导入；注册表 5 行 |
| `s4h_1_data.py` | 83 | S4H-1 数据（决策 100）：老越电网间存量为 0（AIMS 口径）、四条聚类老越线作为零容量候选。 | 动态: 未导入；注册表 3 行 |
| `s4h_2_data.py` | 227 | S4H-2 数据（决策 101）：交流候选的参考电抗，写 XB_LENGTH_SHARES_S4H2.csv。 | 动态: 未导入；注册表 8 行；输出被 s4d_ledger.py 读取 |
| `s4h_3_registry.py` | 33 | S4H-3 注册表片段 s4h_3：决策 100 的 IPP 出口线估计相对老越账本差异。 | 动态: 未导入；注册表 1 行 |
| `s4j_0_data.py` | 74 | S4J-0：注册表片段 s4j_0（用户对 S4I 报告第 5 节的回答）。 | 动态: 未导入；注册表 18 行 |
| `s4j_1_data.py` | 128 | S4J-1 数据（决策 104，S4I K1）：由需求表部门得到的非工业电力基荷。 | 动态: 未导入；注册表 4 行 |
| `s4j_2_data.py` | 173 | S4J-2 数据与检查（决策 105a，S4I U1）：输电损耗按 PyPSA-Eur v2025.07.0。 | 动态: 未导入；注册表 4 行 |
| `s4j_3_data.py` | 102 | S4J-3 数据（决策 105b，S4I U2；决策 107a 重写）：泰马直流链路与换流器背靠背。 | 动态: 未导入；注册表 3 行 |
| `s4k_0_data.py` | 47 | S4K-0：注册表片段 s4k_0（决策 108：交流线路线性损耗代理替代 PyPSA 分段切线）。 | 动态: 未导入；注册表 6 行 |
| `s4k_1_data.py` | 232 | S4K-1 数据与检查（决策 108）：交流线路线性损耗代理。 | 动态: 未导入；注册表 6 行 |
| `s4l_0_data.py` | 63 | S4L-0 数据：注册表片段 s4l_0（决策 112 a/b：L23 首批四个运行的标注）。 | 动态: 未导入；注册表 5 行 |
| `s4l_1_data.py` | 193 | S4L-1 数据（决策 113(1)）：S4K-3 网络上的近零量清单、阈值与影响表。 | 动态: 未导入；注册表 7 行 |
| `s4l_2_data.py` | 49 | S4L-2 数据（决策 113(2)）：新求解配置 formal_barrier_crossover 的注册表片段。 | 动态: 未导入；注册表 4 行 |
| `s4l_5_data.py` | 132 | S4L-5（用户授权的附加诊断，仅诊断，不是主运行）：注册表片段 s4l_5。 | 动态: 未导入；注册表 3 行 |
| `s4l_6_data.py` | 44 | S4L-6 数据：注册表片段 s4l_6（S4L 报告之后的用户决策：采用清理）。 | 动态: 未导入；注册表 4 行 |
| `s4m_0_data.py` | 50 | S4M-0 数据：注册表片段 s4m_0（决策 114–116：主运行设置，dust 清理开启、crossover 等）。 | 动态: 未导入；注册表 5 行 |
| `s4o_0_data.py` | 57 | S4O 数据：注册表片段 s4o_0（决策 118、119：以精度证据取代原闸门等）。 | 动态: 未导入；注册表 4 行 |
| `s4o_1_data.py` | 46 | S4O 补充 01 数据：注册表片段 s4o_1（决策 121：生产配置回到配置 A）。 | 动态: 未导入；注册表 4 行 |

## 9. 测试与检查工具（36）

静态校验、烟测评估、回归/单元测试脚本与验证器。其中 `test_*.py` 是位于 `scripts_project/` 内的 Gate5/Gate6 无求解测试（不同于 `tests/research/` 下的 pytest 测试），与 `run_gate1_checks.py`、`run_gate3_validation.py`、`run_gate6_no_solver_tests.py`、`run_lossless_freeze_tests.py` 同属遗留测试套件；`s3b_interior.py`、`netcdf_readback.py`、`validation_dynamics.py` 是求解后闸门懒加载的检查模块。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `check_assembly_inputs.py` | 125 | 失败即关闭的 Assembly V1 输入闸门，不建网络、不调用求解器。 | 动态: 未导入；测试: test_assembly_input_freeze, test_gate4_activation 等 4 个 |
| `check_research_demand.py` | 39 | 读取 Gate2 研究配置并校验其表，不调用求解器（依赖 build_research_demand.py）。 | 动态: 未导入；测试: test_demand_accounting |
| `m08b_smoke_eval.py` | 78 | M08b 第 4 节：按指令验收标准评估本地 56×3h 烟测（只读、不求解）。 | 动态: 未导入 |
| `m08b_static.py` | 249 | M08b 第 3 节：重建网络的静态检查，并与修正前网络比较（不求解）。 | 动态: 未导入；测试: test_m08b_s01 |
| `m10r_synthetic_solution.py` | 121 | M10R B3.3：对无真实 56×3h 求解的网络类型生成合成已解运行，仅用于演练后处理链与账本恒等式（标记 SYNTHETIC_TEST_ONLY）。 | 动态: 未导入 |
| `netcdf_readback.py` | 45 | （已解）网络的语义 NetCDF 往返检查（V5 闸门 A4，由 v5_gates 懒加载）。 | 动态: 未导入；静态: 批次闭包 |
| `research_topology.py` | 56 | 对固定预建电力输入做严格的引用完整性审计，不建模型、不求解。 | 动态: 未导入；测试: test_topology_integrity |
| `run_gate1_checks.py` | 30 | 不借助任何求解器，重跑集成工程与静态回归。 | 动态: 未导入 |
| `run_gate3_validation.py` | 27 | 运行有界 Gate3 测试并保留逐测试结果，从不求解。 | 动态: 未导入 |
| `run_gate6_no_solver_tests.py` | 49 | 本地/云端同一套有界无求解器测试：硬陷阱、持久日志、不做完整构建。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `run_lossless_freeze_tests.py` | 48 | 顺序执行的无求解测试套件，所有产物与临时载荷留在 D 盘。 | 动态: 未导入 |
| `s1_compare.py` | 65 | S1 的跨情景 V5 闸门（B5、B6）与成本层哈希恒等检查（B12）。 | 动态: 未导入 |
| `s3_0_kh_check.py` | 75 | S3-0.4：柬埔寨交通链检查（仅报告，不改模型）。 | 动态: 未导入 |
| `s3_6_gates_check.py` | 60 | S3-6：在已构建网络上运行静态（无求解器）V5 B 组闸门（B11、B12 等）。 | 动态: 未导入 |
| `s3b_interior.py` | 86 | S3B R4.4（决策 69）：无 crossover 的内点解配套检查（s2_solve.py 求解后懒加载）。 | 动态: 未导入；静态: 批次闭包 |
| `s4c_3_config_key_check.py` | 96 | S4C-3 第 2 项：核查 research.cost_layer.registry 配置键位置错放（077ebd0b 至 9a5ea111）的影响。 | 动态: 未导入 |
| `s4g_1_check.py` | 122 | S4G-1（决策 98）对已构建网络的检查（无求解）。 | 动态: 未导入 |
| `s4m_s1_check.py` | 109 | S4M 补充 01 的 S4M-S1 清单：对单个求解目录的只读检查（对偶、约束、成本拆分，不求解）。 | 动态: 未导入 |
| `test_chunk_build.py` | 29 | 证明小规模 eager/分块全量传输一致，不运行或预处理。 | 动态: 未导入 |
| `test_gate5_cloud_resources.py` | 119 | 无原生求解：cgroup、不变守卫、持久单次调用声明与路径。 | 动态: 未导入 |
| `test_gate5_lossless_integration.py` | 49 | 准备真实微型 LP 而不求解，模拟已授权执行边界。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `test_gate5_metadata_closeout.py` | 73 | 仅合成的元数据/序列化闸门，不作物理验证声明。 | 动态: 未导入 |
| `test_gate5_resources.py` | 95 | 无优化无预处理：小矩阵、模拟守卫、有界缓冲。 | 动态: 未导入 |
| `test_gate6_authorization_flow.py` | 149 | TEST_ONLY：真实授权/声明/构建/钩子，有界四步网络。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `test_gate6_baseline_3h.py` | 166 | 仅合成工程夹具，绝非生产解/见证。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `test_inventory_mapping.py` | 63 | SYNTHETIC_TEST_ONLY：非零对偶、同模型钩子、物理导出映射。 | 动态: 未导入 |
| `test_inventory_reformulation.py` | 144 | LOCAL_DIAGNOSTIC_ONLY：有界 A/B/C 比较与物理负例。 | 动态: 未导入 |
| `test_lossless_export.py` | 69 | 完全不用优化的顺序导出与来源寿命测试。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `test_lossless_gate5_lifecycle.py` | 116 | 无优化：元数据、映射与原生合同的正负例测试。 | 动态: 未导入 |
| `test_precision_handoff.py` | 88 | SYNTHETIC_TEST_ONLY：数值交接回归，绝非研究结果。 | 动态: 未导入 |
| `test_precision_handoff_no_solve.py` | 57 | 仅 binary64 交接回归：不优化、不 LP 求解、不预处理。 | 动态: 未导入 |
| `test_solver_result_qualification.py` | 83 | 模拟冻结接口的结果状态，无任何求解器调用。 | 动态: 未导入 |
| `validate_fullsc_final.py` | 92 | 实际未求解网络检查，不创建优化模型或求解器。 | 动态: 未导入 |
| `validation_dynamics.py` | 104 | 验证求解的独立方程（V5 A 组物理，由 v5_gates 懒加载），从不声称完整成本/CO2。 | 动态: 未导入；静态: 批次闭包+数据链闭包；测试: test_s2b_supplement02 |
| `verify_gate5_infeasibility.py` | 48 | 对保存的 LP 矛盾做可移植的精确算术验证，无求解器。 | 动态: 未导入 |
| `verify_precision_evidence.py` | 46 | 对保存的精确局部证书/见证做可移植的无求解器验证。 | 动态: 未导入 |

## 10. 一次性数据或证据脚本（96）

各阶段的提取、探针、汇总、证据收集脚本。证据列写明其输出是否仍被注册表（“注册表 N 行”）或测试引用；都没有的写“无引用（报告证据）”，即只被该阶段报告引用。Gate2 家族（`build_research_demand.py`、`demand_*.py`）也在此类，见第 3.2 节。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `allocate_assembly_inputs.py` | 118 | 依据固定的外生作者输入，生成国家/节点/时间的实际分配（Assembly V1 阶段输入分配）。 | 无引用（报告证据） |
| `apply_gate4_baseline_choices.py` | 83 | 确定性地套用当前泰国及铁路/NEC 的人工选择（Gate4 基线决策）。 | 无引用（报告证据） |
| `apply_selected_stock.py` | 69 | 由冻结的机组、队列与资源输入可复现地构建选定存量（Gate4）。 | 无引用（报告证据） |
| `asset_lifetime_override.py` | 29 | 仅对明确点名的现有机组队列施加有来源的寿命覆盖（Gate4 遗留，仅测试引用）。 | 测试: test_limited_ocgt_and_blend_bounds |
| `audit_closure_choices.py` | 133 | Gate4 残差证据与条件选择的精确审计，不改输入、不求解。 | 无引用（报告证据） |
| `audit_hydro_qualification.py` | 121 | 只读的 Gate4 实际资产（水电资格）审计，不调用求解器（文档串为空，依据 argparse 描述）。 | 无引用（报告证据） |
| `audit_lossless_projection.py` | 70 | 复用冻结块证据的无损投影审计，不建新模型、不求解、不做预处理。 | 无引用（报告证据） |
| `audit_residual_sources.py` | 90 | 基于当前选定合同与缓存来源 ID 的有界残差来源审计（Gate4）。 | 测试: test_source_scope |
| `audit_selected_assets.py` | 80 | 对实际开发网络的验证，读取仅输入合同与导出（Gate4）。 | 无引用（报告证据） |
| `blend_uncertainty.py` | 96 | 针对已缓存 UNSD 混合燃料对的不入账核算包络（Gate4 遗留，仅测试引用）。 | 测试: test_limited_ocgt_and_blend_bounds |
| `build_complete_assembly.py` | 64 | 施加显式存量完整性边界并准备完整的未求解输入（Gate4 遗留）。 | 无引用（报告证据） |
| `build_research_demand.py` | 123 | 由固定来源胶囊重建 Gate2 观测/合同表（Gate2 需求账；生产追踪未执行，仅测试引用）。 | 测试: test_demand_accounting |
| `build_survival_decision_evidence.py` | 65 | 有界、可复现的存续决策证据，只输出候选、不写活输入（Gate4）。 | 无引用（报告证据） |
| `demand_accounting.py` | 239 | Gate2 需求合同（核算与账本校验），不含上游需求构建、不改网络、不求解。 | 测试: test_demand_accounting；Gate2 家族，仅 test_demand_accounting.py 引用 |
| `demand_buildings.py` | 37 | Gate2 建筑部门 R/S 分账（不合成采暖、炊事、区域供热存量）。 | 无引用（报告证据）；Gate2 家族，无直接测试，仅被 build_research_demand.py 导入（后者被测试覆盖） |
| `demand_industry_agriculture.py` | 52 | Gate2 工业/农业固定终端能源核心（保留煤/生物质，不以 CO2 替代 MWh）。 | 无引用（报告证据）；Gate2 家族，无直接测试，仅被 build_research_demand.py 导入 |
| `demand_sources.py` | 61 | Gate2 固定观测胶囊读取器与账本行构造器。 | 测试: test_demand_accounting；Gate2 家族，仅 test_demand_accounting.py 引用 |
| `demand_transport.py` | 62 | Gate2 公路终端能源合同、铁路内嵌与四个独立燃料账户。 | 无引用（报告证据）；Gate2 家族，无直接测试，仅被 build_research_demand.py 导入 |
| `final_closure_inputs.py` | 123 | 冻结的 Assembly V1 人工边界，来源记录不被改写（Gate4，有测试）。 | 测试: test_final_closure |
| `gate5_cloud_preflight.py` | 144 | 只读/仅构建/仅测试的 Gate5 云端闸门，不调用真实求解器。 | 无引用（报告证据） |
| `gate5_cloud_worker.py` | 96 | Gate5 持久监督器与证据收集器，只运行一个受保护的子进程。 | 无引用（报告证据） |
| `gate5_memory_preflight.py` | 33 | Gate5 默认只读内存预检，执行需另行显式授权。 | 无引用（报告证据） |
| `l23_c9_summary.py` | 286 | L23 C9 首轮汇总（只读、不求解）：第一批云端 365×24h 运行的结果汇总。 | 无引用（报告证据） |
| `l23_collect_evidence.py` | 78 | L23 C9：由已下载结果生成首批云端运行的轻量证据 L23_RUN1_EVIDENCE.json。 | 无引用（报告证据） |
| `prepare_existing_stock_contract.py` | 41 | 当前人工范围下有来源资格的现有设备代理（Gate4）。 | 无引用（报告证据） |
| `prepare_hydro_group_contract.py` | 85 | 审定仅输入的年度水电组与明确接受的抽蓄代理（Gate4）。 | 无引用（报告证据） |
| `probe_crossover.py` | 13 | 单个固定块的 HiGHS crossover 依据探针（文档串为空，依据代码）。 | 无引用（报告证据） |
| `profile_gate5_lossless.py` | 257 | 365 快照仅构建/传输的剖析，严禁运行/预处理调用（Gate5）。 | 无引用（报告证据） |
| `r12a_wind_diagnosis.py` | 73 | R12A（只读）：D 阶段研究模型中陆上与海上风电装机为零的原因诊断。 | 无引用（报告证据） |
| `rebuild_assembly_targets.py` | 54 | 由固定原始来源与人工方法重新推导已接受的目标值（Gate4）。 | 测试: test_gate4_activation |
| `reconcile_unsd_blends.py` | 23 | 基于质量的石油/生物燃料可审计对账，从不把缺失当零。 | 无引用（报告证据） |
| `reconstruct_base_accounts.py` | 243 | 由固定 UNSD 行（而非缓存标签）重建 2019 终端燃料账户（Gate4）。 | 测试: test_gate4_activation, test_gate4_continue, test_gate4_selected_closure |
| `recover_asset_mapping.py` | 35 | 恢复缓存的首段映射并提出分区安全的第二段。 | 无引用（报告证据） |
| `refresh_canonical_coverage.py` | 36 | 仅刷新既有有界来源排除项，不增加新需求或方法。 | 无引用（报告证据） |
| `refresh_diagnostic_qualification.py` | 87 | 更新已审定的存量解释与 NetCDF 元数据，从不重建。 | 测试: test_limited_ocgt_and_blend_bounds |
| `refresh_nec_alias_inputs.py` | 63 | 在已接受的 OtherNEC 规则下机械恢复 UNSD1234 叶子。 | 无引用（报告证据） |
| `residual_account_mapping.py` | 70 | 由原始行与官方 DSD 推导的 UNSD 重叠/请求恒等式（Gate4）。 | 测试: test_gate4_selected_closure |
| `review_gate6_dec.py` | 95 | 只读的逐事件来源/拓扑证据，不含政策赋值或模型（Gate6）。 | 无引用（报告证据） |
| `run_gate5_bounded_once.sh` | 14 | Gate5 一次授权的验证尝试（无重试循环、无检查点续跑）。 | 无引用（报告证据） |
| `run_gate5_precision_retry.py` | 110 | 由字节一致的已接受日度输入做一次授权的 Gate5 重试。 | 无引用（报告证据） |
| `run_gate5_stable_inventory.py` | 170 | Gate5 稳定库存重试：由字节一致的已接受日度输入做一次授权重试。 | 无引用（报告证据） |
| `s1_inputs_review.py` | 186 | S1-3 存量审查与 S1-6 走廊表，对每个冻结文件只读。 | 测试: test_s1_adapter_daily_v5 |
| `s2_structural_gap.py` | 76 | S2-7：逐国年度基础上的无求解净零结构可行性表（决策 49/53）。 | 无引用（报告证据） |
| `s3_7_lp_ranges.py` | 101 | S3-7（用户补充第 2 项）：56×3h 烟测 LP 的系数范围（不求解）。 | 无引用（报告证据） |
| `s3_7_results_summary.py` | 107 | S3-7：已解 56×3h 烟测/gap_diagnostic 网络的结果汇总（SMOKE_TEST_ONLY）。 | 无引用（报告证据） |
| `s3b_explore_lp.py` | 68 | R4 探索（不求解）：目标常数列、可做单位缩放的候选 Store 及引用它们的约束组。 | 无引用（报告证据） |
| `s3b_gas_flows.py` | 80 | S3B R3：已解网络的天然气供应结构（LNG 进口、国内产量、跨境管道流）。 | 无引用（报告证据） |
| `s3b_r4_compare.py` | 100 | S3B R4.3 等价检验：缩放前后 formal_barrier 解的比较。 | 无引用（报告证据） |
| `s4a_1_compare.py` | 78 | S4A-1 第 6 步：重建的风光出力曲线与原网络曲线及各变体/分类的比较。 | 无引用（报告证据） |
| `s4a_4_smoke_compare.py` | 109 | S4A-4：烟测中风、光、地热、水电、核电及化石与储能的分国装机与发电对比。 | 无引用（报告证据） |
| `s4b_5_kkt_diag.py` | 111 | S4B-5：对完成的烟测中决策 71 闸门失败做只读诊断（重建 linopy 模型，不调用求解器）。 | 无引用（报告证据） |
| `s4b_5_summary.py` | 198 | S4B-5 烟测汇总：运行表（状态、目标、LP 规模、内点法、时间、内存）与 S4A 的比较。 | 无引用（报告证据） |
| `s4b_reevaluate_acceptance.py` | 71 | S4B-0 第 2 项：按决策 71 预算重评已完成的烟测（S3B、S4A），历史结果只读。 | 无引用（报告证据） |
| `s4b_smoke_summary.py` | 69 | S4B 烟测汇总：已解 56×3h 网络与参考烟测的分国装机/发电对比。 | 无引用（报告证据） |
| `s4b_structural_gap.py` | 111 | S4B-0 第 6 项：不连网情景 CO2 与气的年度结构缺口（无求解，含甲烷化与 LNG 扩容）。 | 无引用（报告证据） |
| `s4c_1_cost_audit.py` | 209 | S4C-1 第 3–4 项（决策 82）：对每个可扩展组件的资本成本相对决策 50 成本层的审计。 | 无引用（报告证据） |
| `s4c_2_hydro_diagnosis.py` | 123 | S4C-2 第 1 项（决策 83）：校正之前的分国水电入流诊断（输出写 research_inputs/hydro_v5 诊断表）。 | 无引用（报告证据） |
| `s4c_2_hydro_report.py` | 53 | S4C-2 报告表：各国作者基线入流，S4A/S4B 增补前后对比。 | 无引用（报告证据） |
| `s4c_3_bunker_report.py` | 87 | S4C-3 报告表（决策 88）：各国国际燃油舱需求及其在三种归属模式下的 CO2。 | 无引用（报告证据） |
| `s4c_5_compare.py` | 140 | S4C-5（决策 84）：Kirchhoff 行归一化等价检验与 s2_solve.py 运行目录的求解设置比较表。 | 无引用（报告证据） |
| `s4c_5_extrapolate.py` | 62 | S4C-5（决策 84）：求解配置 A/C 的云端时间与内存外推。 | 无引用（报告证据） |
| `s4c_6_summary.py` | 139 | S4C-6 烟测汇总：运行表、BarConvTol 与求解容差下的闸门。 | 无引用（报告证据） |
| `s4d_1_coast_diagnostic.py` | 76 | S4D-1 停机诊断（决策 93）：按指令规则部分节点沿海性不明确的原因（写 research_inputs/co2_v5 诊断表）。 | 无引用（报告证据） |
| `s4d_1_port_regions.py` | 55 | S4D-1 停机诊断（决策 93）：各港口/LNG 接收站所处节点的陆上区域（点在多边形内）。 | 无引用（报告证据） |
| `s4d_4_summary.py` | 74 | S4D-4（决策 91b）汇总：56×3h 烟测上的联盟验证及走廊图连通联盟计数。 | 无引用（报告证据） |
| `s4d_5_summary.py` | 117 | S4D-5 烟测汇总：互联与不互联 STEPS 及互联 NZE 对比。 | 无引用（报告证据） |
| `s4d_6_collect_evidence.py` | 80 | S4D 交付物：从回执、汇总、注册表与 git 收集轻量证据 S4D_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4e_3_summary.py` | 103 | S4E-3 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4D 的对比。 | 无引用（报告证据） |
| `s4e_4_collect_evidence.py` | 61 | S4E 交付物：轻量证据 S4E_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4f_1_excess.py` | 49 | S4F-1（决策 96）报告表：S4E-3 烟测解中扩容超过 PyPSA-Eur 单线上限的线路/直流链路。 | 无引用（报告证据） |
| `s4f_2_readjust_audit.py` | 83 | S4F 报告节（仅记录，不改模型）：作者 readjust_existing_interconnections 改动过 s_nom 的跨境交流线路（写 research_inputs/corridors 记录表）。 | 无引用（报告证据） |
| `s4f_3_summary.py` | 100 | S4F-3 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4E-3 的对比。 | 无引用（报告证据） |
| `s4f_4_collect_evidence.py` | 69 | S4F 交付物：轻量证据 S4F_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4g_1_la_vn.py` | 104 | S4G-1 第 6 项（仅记录）：老挝-越南运行中跨境线路的仓库内证据（写 research_inputs/corridors 记录文件）。 | 无引用（报告证据） |
| `s4g_3_summary.py` | 118 | S4G-3 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4F-3 的对比。 | 无引用（报告证据） |
| `s4g_4_collect_evidence.py` | 71 | S4G 交付物：轻量证据 S4G_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4h_3_summary.py` | 134 | S4H-3 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4G-3 的对比。 | 无引用（报告证据） |
| `s4h_4_collect_evidence.py` | 70 | S4H 交付物：轻量证据 S4H_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4i_coalition_estimate.py` | 71 | S4I（条目 103）D 节：联盟研究在学术许可下的算力估计（推断，不求解）。 | 无引用（报告证据） |
| `s4i_followups.py` | 228 | S4I（条目 103）续做（S4I_RESUME_01）：A3/A5/A6 细节与 B2–B4 节的证据文件。 | 无引用（报告证据） |
| `s4i_lp_ranges.py` | 107 | S4I（条目 103）C 节：冻结网络 LP 的静态系数范围告警（仅建模，不求解）。 | 无引用（报告证据） |
| `s4i_static_audit.py` | 801 | S4I（条目 103，2026-10-18）：四个冻结 S4H 网络的云端前静态审计（只读，不求解、不下载）。 | 无引用（报告证据） |
| `s4j_5_review.py` | 137 | S4J-5 静态复核：对四个 S4J 网络重跑 S4I 审计并与 S4I 逐项比较。 | 无引用（报告证据） |
| `s4j_6_detail.py` | 128 | S4J-6 细节（补充 01 b）：泰马走廊构建与潮流（交流线路与直流双向）。 | 无引用（报告证据） |
| `s4j_6_summary.py` | 142 | S4J-6 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4H-3 的对比。 | 无引用（报告证据） |
| `s4j_7_collect_evidence.py` | 80 | S4J 交付物：轻量证据 S4J_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4k_2_review.py` | 98 | S4K-2 静态复核：对四个 S4K 网络（365×24h）重跑 S4I 审计并逐项比较。 | 无引用（报告证据） |
| `s4k_3_summary.py` | 149 | S4K-3 烟测汇总：互联/不互联 STEPS 与互联 NZE 相对 S4J-6 的对比。 | 无引用（报告证据） |
| `s4k_5_collect_evidence.py` | 71 | S4K 交付物：轻量证据 S4K_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4l_2_summary.py` | 218 | S4L-2 汇总（决策 113(2)）：56×3h 诊断矩阵 {S4K-3 网络, S4L-1 清理后网络} × 求解配置。 | 无引用（报告证据） |
| `s4l_4_collect_evidence.py` | 95 | S4L 交付物：轻量证据 S4L_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `s4m_2_summary.py` | 67 | S4M-2 烟测汇总：三个 S4M 烟测运行（主设置，56×3h，配置 A）。 | 无引用（报告证据） |
| `s4m_5_collect_evidence.py` | 103 | S4M 交付物：轻量证据 S4M_EVIDENCE.json（不求解）。 | 无引用（报告证据） |
| `source_scope.py` | 103 | 套用两项经人工批准的有界统计范围解释（Gate4，有测试）。 | 测试: test_source_scope |
| `trace_asset_survival.py` | 47 | 机组存续证据追踪（文档串为空，依据代码：读取 GEM 工作簿与缓存并调用 asset_survival.select_asset）。 | 无引用（报告证据） |
| `unit_asset_survival.py` | 59 | 在任何节点/技术聚合之前先筛选来源机组（Gate4）。 | 测试: test_gate4_activation, test_surviving_asset_integration |

## 11. 已退役（11）

`retired/` 目录的 10 个文件（仓库自己的退役标记），加 `s2b_industry.py`（已被 `s3_0_industry.py` 取代）。

| 文件 | 行数 | 用途（一句话） | 证据（追踪标志 / 注册表行数 / 测试） |
|---|---:|---|---|
| `retired/audit_fixed_price_residual.py` | 121 | 只读的 Gate4 实际网络与残差来源证据审计，不求解。 | 动态: 未导入 |
| `retired/build_diagnostic_network.py` | 177 | 独立的局部诊断网络，从不放宽完整模型闸门（S1-2 已退役，辅助函数迁入 network_checks.py）。 | 动态: 未导入 |
| `retired/check_research_carriers.py` | 40 | 校验 Gate3 合同与 11 国结构模板，不含完整网络（build_research_network.py 注明该模块已退役）。 | 动态: 未导入 |
| `retired/diagnose_gate5_fixed_blocks.py` | 82 | 有界的精确输入子矩阵预处理诊断，不运行优化。 | 动态: 未导入 |
| `retired/fixed_account_scope.py` | 17 | 经人工授权的附加商品范围，无推断接受。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `retired/fixed_accounts.py` | 120 | 外部待定、严格固定商品的可撤销资格审查。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `retired/fixed_inventory_scaling.py` | 106 | 仅针对合格固定库存组的可逆二次幂缩放映射。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `retired/gate6_fixed_term_contract.py` | 33 | 未来获批区域比较的可观察不变量，不含收益。 | 动态: 未导入；静态: 批次闭包+数据链闭包 |
| `retired/validate_diagnostic_preservation.py` | 50 | 实际网络相对先前交付输入资产的保真校验，无求解器。 | 动态: 未导入 |
| `retired/verify_local_fixed_diagnosis.py` | 71 | 已提取局部块的精确有理数证书/见证。 | 动态: 未导入 |
| `s2b_industry.py` | 284 | R1（决策 55）：按 2050 工艺路线的工业终端能源；已被 s3_0_industry.py 取代（s3_0_industry.py 仅保留其冻结结果 *_S2B_FROZEN.csv 作比较列）。 | 动态: 未导入；注意：d1_registry.py 第 175 行仍把它的 SHA256 写入 D1_EVIDENCE.json，文件须保留；D1_EVIDENCE.json 与 d1_registry.py 的字符串中也出现其路径 |

## 12. 分类存疑与复核建议

| 文件 | 分类 | 存疑原因 |
|---|---|---|
| `v5/gates_v6.py` | 后处理 | 标志显示 `in_build`、`in_solve` 为真（`s2_network.py` 导入其 `config_subset_sha256`），`in_post` 为假；按指令它是后处理入口（`accept` / `select-profile` / `formal-check`，批次 shell 调用），故归后处理 |
| `m12_rhs_audit.py`、`s4d_ledger_redo.py` | 后处理 | `in_post` 为假，原因是入口脚本不记入自己的导入记录（见 2.5）；依据 shell 引用与指令点名归后处理 |
| `build_research_demand.py`、`demand_accounting.py`、`demand_sources.py`、`demand_buildings.py`、`demand_transport.py`、`demand_industry_agriculture.py`、`check_research_demand.py` | 一次性 / 测试 | 任务说明把前六个列为退役候选；核查发现它们被 `test_demand_accounting.py` 导入（`demand_buildings` 等经 `build_research_demand.py`），按“有测试则不退役”未归入已退役；`build_research_demand.py` 的文档串是“重建 Gate2 观测/合同表”，并非“只含 S1 检查”。实质上它们不在生产路径上，若要真正退役需同时处理测试与 `baseline.yaml` 第 5 行 |
| `s2b_industry.py` | 已退役 | 无任何标志、无测试、无注册表行，已被 `s3_0_industry.py` 取代；但 `d1_registry.py` 第 175 行对其取 SHA256 写入 `D1_EVIDENCE.json`，`D1_EVIDENCE.json` 与 `d1_registry.py` 的下载清单字符串也出现其路径——删除或移动会让 `d1_registry.py` 重跑失败 |
| `retired/fixed_account_scope.py`、`retired/fixed_accounts.py`、`retired/fixed_inventory_scaling.py`、`retired/gate6_fixed_term_contract.py` | 已退役 | 静态标志（`in_batch_closure`、`in_data_chain`）为真，因为 `run_gate6_baseline.py` 等以裸模块名导入；但追踪均未导入，且文件已移入 `retired/`，裸名导入在当前布局下可能无法解析 |
| `d1_common.py` | 构建 | 构建追踪导入它，故按优先级归构建；它同时是整条数据链（`d1_*`、`m08b_*`、`s2b_*`、`s3_0_*`）的共享库，DFX 修改它时影响离线数据链 |
| `build_research_network.py` | 构建 | 文档串是“S1 静态校验”（可归检查类），但 `in_build` 为真（`s2_network.py` 导入 `REQUIRED_PER_NODE`），按标志归构建 |
| `s3b_interior.py`、`netcdf_readback.py`、`validation_dynamics.py` | 测试与检查 | 它们由 `s2_solve.py` / `v5/v5_gates.py` 求解后懒加载，也可归后处理；按指令示例（`netcdf_readback.py`）和文档串归检查工具 |
| 第 7.2 节 B 区 15 个库模块 | 批次与打包 | 仅静态可达、无任何动态标志；归批次与打包是按指令的规则，实际更像 Gate4–Gate6 遗留库，可能整体属退役候选 |
| `m10r_synthetic_solution.py`、`s4m_s1_check.py` | 测试与检查 | 前者是合成解演练工具，后者是单个求解目录的清单检查，都未被 shell 引用；也可归一次性 |
| `s4c_2_hydro_diagnosis.py`、`s4d_1_coast_diagnostic.py`、`s4d_1_port_regions.py`、`s4f_2_readjust_audit.py`、`s4g_1_la_vn.py` | 一次性 | 输出写入 `research_inputs/` 子目录（诊断/记录表），但没有注册表行也没有构建层读取它们的证据，故按一次性处理；与 8.3 的输入表生成脚本边界相邻 |
| `s4a_profiles.py`、`m08a_offshore_profiles.py` | 数据链 | 输出经导出脚本/直接进入 `research_inputs/renewable_v5` 并被 `s4a_layers.py` 读取，但自身的注册表行少（1 行/0 行）；归数据链而非一次性 |
| `asset_lifetime_override.py`、`blend_uncertainty.py`、`final_closure_inputs.py`、`source_scope.py` 等 Gate4 遗留 | 一次性 | 有测试引用但不在任何轨迹中，按“一次性（有测试）”处理 |

## 13. 执行清单的补全与 F0.3 结果（执行端补记，2026-10-26）

- 第 2.5 节指出入口脚本不记入自己的导入记录：`CODE_MAP_TABLE.csv` / `CODE_MAP_DATA.json` 已重算，把每次追踪的 argv[0]（`s2_network.py`、`s2_solve.py`、`l23_violation_analysis.py`、`s4o_c1_precision.py`、`m12_allocation.py`、`m12_rhs_audit.py`、`s4d_ledger_redo.py`、`v5/gates_v6.py`、`m10_batch3_summary.py`、`m08a_variants.py` 及数据链脚本）计入所在清单；本文件各表的标志以重算前的快照为准，差异只在这些入口脚本本身（它们本来就按指令点名归入各自类别）。重算后的动态清单：构建 32、求解 27、后处理 32、变体 2、数据链 13 个模块。
- **数据链实际执行清单（新增第五份清单；`CODE_MAP_DATA.json` `dynamic.data_chain`）：** DFX 用同一记录器重跑数据链（`m08b_demand.py → m08b_heat_bands.py → s3_0_industry.py → s2b_feedstock.py → s2_0_process_emissions.py → m08b_data.py → dfx_data.py → d1_registry.py`），实际导入 / 执行的模块为这 8 个入口脚本加 `d1_common.py`、`d1_demand_2050.py`、`carrier_architecture.py`、`s2_costs.py`、`s2_layers.py`（后三者由 `m08b_data.py` 导入热档技术映射）。
- **F0.3 核对（测试 `tests/research/test_dfx_demand.py::test_f0_changed_scripts_in_the_executed_lists`）：** F1–F4 改动的 `scripts_project/` 文件——`m08b_demand.py`、`s3_0_industry.py`、`s2b_feedstock.py`、`s2_layers.py`、`d1_common.py`、`m08b_data.py`、`d1_registry.py`、新增 `dfx_data.py`——全部在构建 / 求解 / 后处理 / 批次 / 数据链的实际执行清单之内（`executed_union`）。重复实现的另一份（`d1_demand_2050.py` 的 NEU 与部门总量逻辑、`s2b_industry.py`、Gate2 `demand_*` 族）未改动，见第 3.3 节。
- 第 7 节 B 区的 15 个仅静态可达的库模块、`s2b_industry.py` 与 `retired/` 下文件的归档整理，按指令 F0 第 4 条留到正式运行之后、论文代码公开之前另行处理，本次不动。


## 14. F6 新增文件的归类（执行端补记，2026-10-26）

| 文件 | 类别 | 说明 |
|---|---|---|
| `scripts_project/dfx_batch.py`（新） | 生产管线 / 批次与打包 | DFX 365×24h 筛查的运行表（V1 / V2）、登记时限、基础网络核对（回执 + 登记 SHA256 / 字节）、分级停批分类、批级汇总（B6 = V2 − V1，与第三批 R1 / R2 及一阶预测的对比）；导入 `m10_batch3_summary.py` 的只读辅助函数并替换其模块常数，不改第三批文件 |
| `research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh`（新） | 生产管线 / 批次与打包（包脚本） | 由第三批 `run_batch3.sh` 派生的 DFX 运行脚本：一个阶段两条通道，≥ 33 核才并行，每运行登记时限，V1 / V2 都是参照运行的分级停批；无变体 / 去一国 / 第二级比较 / S1 模式 |
| `cloud_package_dfx/preflight_dfx.sh`、`make_package_dfx.sh`（新） | 包脚本 | 由 B4P `preflight.sh` / `make_package.sh` 派生：365×24h v2 网络、登记时限、硬下限 17 核 / 64 GiB / 45 GB；v8 包组装（要求本提交的干跑记录） |
| `research/06_scope_redesign/p1_dfx_20261026/BATCH3_REFERENCE_VALUES.json`（新） | 包数据 | 第三批 R1 / R2（R3 / R4）目标值、B6、Owen α 主值分摊、账本总额 + 登记的一阶预测；供 `dfx_batch.py summary --reference` |
| `tests/research/test_dfx_runner.py`（新） | 测试 | `run_dfx.sh` / `dfx_batch.py` / `preflight_dfx.sh` 的替身整链测试（14 个），复用第三批替身流水线 `tests/research/fixtures/m10p_fake_pipeline.py` |
| `research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/*`（新） | 阶段 2 草稿（PROPOSED） | NUS Atlas PBS 作业生成器、作业体、环境安装、预检、检查单、HPC 包组装；不在任何本机执行清单中 |
| `scripts/wsl_dfx3/*`（镜像） | 一次性辅助脚本 | 本会话的 WSL 辅助脚本（提交、追踪、构建、复核链、冒烟、探针、干跑）；证据性质，不是入口 |
