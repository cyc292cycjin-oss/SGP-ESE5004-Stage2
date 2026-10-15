# S1 报告：部门耦合骨架、电力与氢（2026-10-15）

**分支** `codex/s1-coupling-skeleton-20261015`（基线 `codex/p0-sector-coupling-audit-20261014` @345fc30f）。所有网络和结果均标注 `INTERIM_S1_SKELETON`；本步只有电力需求，**结果不具备科学含义**。

## 结论摘要（≤10 行）

1. S1-1 至 S1-7 已在本机完成：适配层、固定账户退役、存量复核、候选、分国碳记账、情景开关、V5 骨架，345 项单元测试通过（4 项基线即失败的旧测试除外，与 S1 无关）。
2. 两个情景的 2920×3h 与 365×24h 未求解网络已构建并通过静态验证；两次独立构建字节级一致；成本缩放系数全为 1.0 时网络文件哈希与不加该层完全一致（B12）。
3. S1-8 正式日分辩率求解**未执行**：本机 Gurobi 为 pip 受限许可（规模受限、2026-11-23 到期），122 实例已到期，云端授权暂停（补充指令 02）。云端部署包已打包未上传。
4. 冒烟测试（HiGHS，56×3h，`SMOKE_TEST_ONLY`）：integrated 可解，V5 A1–A6、B1、B11、B12 全部通过；**disconnected 不可行**，原因已定位：新加坡在"每国净零 + 无互联 + 无 SMR 数据 + 无分子进口"下零排放供给潜力仅为需求的 5%，未放宽任何约束。
5. 存量：地热寿命改为 technology-data 30 年后，ID 有 186 MW 按年龄存续，但集成合同无地热性能记录，未并入；Bataan 核电按 GEM 原始记录（mothballed、无投运日期）排除；水电分国差异已列出，未修改。
6. 决定与代码冲突一项待用户裁决：B6 要求把存量跨境线路拆成"不可扩展 + 可扩展"两部分的前提（PyPSA 对全部 `s_nom_opt` 收资本成本）与 PyPSA 0.30.3 不符（`objective_constant` 已扣除存量），且并联 AC 线路会改变基尔霍夫分流；本步改用"存量 FOM 常数 + 不拆分"，详见第 10 节。
7. 追加只读任务 R12A（风电为 0）已完成：D 阶段模型风电为 0 属经济合理（资源差 + 无碳约束 + 便宜化石与光伏）；作者参考模型风电并非 0（9.1 GW）；外部容量因子值未核实。见 `R12A_WIND_ZERO_DIAGNOSIS.md`。
8. 待云端：两个情景 365×24h 的 Gurobi 正式试算、A 组/B 组门槛、检验数/节点价格/跨境流量导出；资源估算见 `CLOUD_RESOURCE_ESTIMATE.md`。

## 1. 本机完成 vs 等待云端（补充指令 02 §3）

| 项 | 状态 |
|---|---|
| S1-1 适配层 | 完成（`scripts_project/sector_adapter.py`） |
| S1-2 退役与守卫重写 | 完成（第 5 节） |
| S1-3 存量复核 | 完成（第 7 节） |
| S1-4 候选与成本缩放 | 完成（第 6 节） |
| S1-5 分国碳记账 | 完成（第 6 节） |
| S1-6 网络与情景开关 | 完成（第 6 节） |
| S1-7 V5 骨架 | 完成（A 组复用 V4，B1/B5/B6/B11/B12 实现；第 9 节） |
| 构建（2920×3h + 365×24h，两个情景） | 完成于本机（峰值 RSS 0.50 GiB，15 s/情景） |
| 冒烟测试（56×3h，HiGHS） | 完成（integrated 可解；disconnected 不可行并已定位） |
| S1-8 日分辨率正式求解（Gurobi） | **等待云端**（新实例信息到位后按 `S1_CLOUD_DEPLOYMENT_PLAN.md` 执行） |
| 云端部署包 | 已打包未上传（`S1_RELEASE.tar.gz` + `S1_RELEASE_MANIFEST.json` + `S1_RELEASE_DELIVERY.json`） |
| R12A 风电诊断 | 完成（`R12A_WIND_ZERO_DIAGNOSIS.md/.json`） |

## 2. 求解环境（补充指令 01 §3）

- **本机许可复查（只读）：** 运行所有 S1 脚本的环境是 WSL `/home/jin/miniforge3/envs/pypsa-earth/bin/python`（Python 3.11.13、gurobipy 12.0.3、pypsa 0.30.3、linopy 0.5.5）。原始输出：`Restricted license - for non-production use only - expires 2026-11-23`；`gurobi_cl --license` 显示使用 `/home/jin/miniforge3/envs/pypsa-earth/lib/gurobi.lic`（pip 自带受限许可）；3000 变量探测报 `Model too large for size-limited license`。Windows 与 WSL 均未发现学术许可文件或 `GRB_LICENSE_FILE`/`GUROBI_HOME`。Gurobi 把 Windows 与 WSL 视为不同主机，学术许可需在 WSL 内单独激活；本步未动任何许可文件（`S1_LOCAL_LICENSE_REVIEW.json`）。
- **云端环境：** 122 实例已到期（补充指令 02）。D 阶段记录的环境：cgroup 90 GiB、Python 3.11.13、gurobipy 12.0.3、WLS 许可路径绑定 `/root/.config/gurobi/gurobi.lic`。本次会话两次 SSH 探测均 `Connection refused`，之后按指令不再连接。
- **部署与回传回执：** 未产生（未上传）。部署包已打包：`S1_RELEASE.tar.gz`（33 个文件，3,963,058 字节，SHA256 `615c9925c8bef339e86c85111d0ff9c649234eb7851e37053552a3c95439da8c`；清单 SHA256 `23b0d9b22e54991d870c3b45e70ea686df2f6a12b230e01903379cd4f832826c`）。部署计划：`S1_CLOUD_DEPLOYMENT_PLAN.md`。
- **两个情景的峰值内存与耗时（本机实测，VERIFIED）：**

| 步骤 | integrated | disconnected |
|---|---|---|
| 网络组装（2920×3h + 精确 365×24h 聚合 + 导出） | 0.50 GiB，14.5 s | 0.50 GiB，13.4 s |
| 冒烟 LP 建模 + HiGHS IPM/交叉 + 门槛（56×3h） | ≈1.2 GiB，约 3 min（求解 163 s） | 0.84 GiB，32 s（不可行即停） |
| 正式 365×24h Gurobi 求解 | 未执行（等待云端） | 未执行 |

- **构建前内存预估（补充指令 02 §1.2）：** 预估峰值 3.5 GiB（依据 C02 日网络构建实测 2.77 GiB RSS ×1.25），WSL 可用 9.94 GiB，阈值 7.94 GiB → 允许本机构建；实测 0.50 GiB（`results_project/s1/S1_BUILD_MEMORY_ESTIMATE.json`、`S1_BUILD_MEMORY_MEASURED.json`）。

## 3. 改动文件清单

**新增**
- `scripts_project/sector_adapter.py` — 上游 `prepare_sector_network` 适配层（注入全局变量、`NOT_CALLED` 清单、`add_hydrogen` 后处理）。
- `scripts_project/country_carbon.py` — 每国大气母线/Store、端口重接、U4 修正、排放登记（每吨一次）、`research_country_net_zero` 钩子、排放分国报告。
- `scripts_project/scenario_network.py` — S1 情景构建器（改名、上游氢、研究配方、候选、跨境标签/开关、输电上限参数、Astar 需求、成本缩放、静态验证、2920 与 365 导出）。
- `scripts_project/s1_candidates.py` — 核电（大型堆/SMR）、地热/新水电/抽蓄站址候选、可扩展性确认、成本缩放层。
- `scripts_project/daily_resolution.py` — 2920×3h → 365×24h 精确有理数平均（C02 算法）。
- `scripts_project/network_checks.py` — 从退役的 `build_diagnostic_network.py` 保留的无求解器助手。
- `scripts_project/s1_inputs_review.py` — S1-3 存量复核（地热重算、Bataan、水电对比）与跨境走廊表生成。
- `scripts_project/s1_solve.py` — 求解驱动（LP 导出、唯一一次 optimize、原始向量、V5 A 组 + B1/B11/B12、检验数/节点价格/跨境流量导出、不可行诊断）。
- `scripts_project/s1_compare.py` — 跨情景 B5/B6；成本缩放层哈希一致性（文件哈希 + 与变量顺序无关的内容哈希）。
- `scripts_project/v5/{__init__,kkt_algebra,v5_gates}.py`、`v5/V5_CONTRACT.json` — V5 骨架。
- `scripts_project/r12a_wind_diagnosis.py` — R12A 只读诊断。
- `research_inputs/asset_survival/lifetime_decisions_s1.json` — 地热寿命 30 年（B 级），其余条目与原文件逐项相同。
- `research_inputs/corridors/cross_border_corridors.csv` — 24 条现有跨境电力边（列 `from,to,carrier,length_km,subsea_share,source` + 组件标识与 2025 容量）。
- `workflow/research_s1.smk`；`scripts_project/retired/README.md`；测试 `tests/research/test_s1_country_carbon.py`、`test_s1_scenario_switches.py`、`test_s1_adapter_daily_v5.py`、`test_s1_built_networks.py`。

**修改**
- `configs/research/baseline.yaml`（新增 `research:` 段）、`integrated.yaml`、`disconnected.yaml`（`research.cross_border` 开关）。
- `scripts_project/carrier_architecture.py`（命名、每国大气、守卫重写、TRANSPORT 角色、市场白名单）、`assembly_components.py`（守卫、`register_upstream_loads`、钩子白名单）、`integrate_surviving_assets.py`（国家大气端口、常数变量名）、`build_research_assets.py`（`build_fragment` 去固定账户/计量链/氢重复项）、`build_research_network.py`（`static_validate_s1`）、`validate_fullsc_final.py`、`validation_dynamics.py`、`price_basis.py`（技术映射）、`check_assembly_inputs.py`、`build_complete_assembly.py`、`refresh_diagnostic_qualification.py`（导入改向）。
- 测试：`test_assembly_input_freeze.py`、`test_carrier_carbon.py`、`test_gate4_continue.py`、`test_hydro_policy_separation.py`、`test_phase4_static.py`、`test_surviving_asset_integration.py`。

**退役（移至 `scripts_project/retired/`，内容未改）**：`fixed_accounts.py`、`fixed_account_scope.py`、`fixed_inventory_scaling.py`、`audit_fixed_price_residual.py`、`diagnose_gate5_fixed_blocks.py`、`verify_local_fixed_diagnosis.py`、`gate6_fixed_term_contract.py`、`check_research_carriers.py`、`build_diagnostic_network.py`、`validate_diagnostic_preservation.py`。退役测试移至 `tests/research/retired/`（7 个）。

## 4. 决定与实现对照

| 编号 | 决定 | 实现位置 |
|---|---|---|
| 3 | 优先沿用上游 | `sector_adapter.py`：上游 `add_hydrogen` 原样调用（电解、燃料电池、H2 轮机、储氢罐、greenfield 管道）。东盟特有设计并写明原因：每国大气（上游只有单一 `co2 atmosphere`）、直流换流母线的管道端点重映射（上游假定 DC 链路连接 AC 母线）、`node <carrier>` 命名统一 |
| 4 | 数值登记等级/来源 | 核电选址表 C 级（`baseline.yaml research.nuclear`）；地热寿命 B 级（`lifetime_decisions_s1.json`）；成本全部来自价格层 EUR2020 表并逐组件资格核验（`price_basis.qualify_network_costs`，0 项待定） |
| 8/15/18 | 两个极端情景；2025 跨境资产为起点；不切断东盟外进口 | `integrated.yaml`/`disconnected.yaml`；`scenario_network.apply_cross_border_switches`（24 条边下限 = 2025 容量、可扩展；disconnected 移除 24 条电力边与 20 条跨境氢管道）；外部化石供给 Generator 在两情景中都保留 |
| 9/10 | 每国净零 | `country_carbon.add_country_atmosphere` + `add_country_net_zero`（最后时段 Store 水平 ≤ 配置上限，主算 0）；`research.carbon.constraint_scope: asean_total` 为敏感性开关 |
| 13/41 | 配置开关、碳上限数值、成本缩放 | `research.cross_border.*`、`research.carbon.country_cap_tco2`、`research.cost_scaling`（28 类技术，默认 1.0）；`s1_candidates.apply_cost_scaling` |
| 35 | 国内氢管道两情景都内生 | 上游 greenfield 管道 110 条（integrated）/90 条（disconnected），国内 90 条在两情景中相同 |
| 37 | 候选技术 | 电力底座候选（光伏、屋顶光伏、陆上/海上风电、电池、户用电池）+ 核电大型堆/SMR + 地热/新 ROR/新水库/新抽蓄（`DATA_PENDING`）+ 上游氢链 + OCGT/CCGT；煤/油只保留存量 |
| 38 | 核电选址 | `research.nuclear.large_pwr.allowed_countries`（除 SG）、`smr.allowed_countries`（11 国）；不受 `add_electricity.py:772` 规则限制 |
| 39 | 先补存量地热/水电再新建 | 存量复核（第 7 节）；新建候选结构 + `p_nom_max=0` |
| 42 | 上游作组件库、研究层保留电力底座 | 冻结电力底座 SHA `6772c674…` 不改动；上游函数只用 `add_hydrogen`（`NOT_CALLED`：`convert_conventional_generators_to_links`、`average_every_nhours`、`add_co2_budget`、`add_heat`、`add_residential`、`add_services`） |
| 45（待决） | 输电扩建总量上限参数 | `research.transmission.volume_limit_mode: inherit_reference_constant`（保持冻结常数 353,746,853.5 MW·km，相对当前存量线路量的隐含倍数 2.79/2.82）；`factor_of_existing` 模式待决 |

## 5. 拆除的守卫及其替代

| 守卫 | 原来防的是什么 | 新口径下由什么取代 |
|---|---|---|
| `build_research_network.py:42`（owners==loads） | 非 registry 的 Load（EV、热、工业氢等） | 保留"每个 Load 只有一个归属"的表：归属可为 REGISTRY 或 UPSTREAM_FUNCTION（`register_upstream_loads`）；V5 B11 检查完整性 |
| `:55-68`（跨国非电力组件/隐藏跨国路径） | 跨境 H2/气/CO₂ 管道 | 删除；所有 Line/Link 打 `border_class` 标签，由 `research.cross_border` 控制；V5 B5（不互联情景跨境容量/流量=0）、B12（开关/哈希） |
| `:69`（`co2 sequestered` Store） | 地质封存 | 删除；封存在 S2 由配置引入 |
| `:93-104`（耦合路径白名单） | Sabatier、H2 轮机、合成氨等 | 删除；V5 B11 检查每节点必备技术/路径，`DATA_PENDING` 单列 |
| `:105-122`（生物质义务路由） | 生物质内生化 | 随固定账户删除；生物质 S2 内生 |
| `validate_fullsc_final.py:72`（FT 必须喂 oil Load） | FT 改为内生供给 | 删除 |
| `:91`（EV/Road parent Load） | EV Load | 删除；部门 Load 经单一归属表进入（S2） |
| `:127-133`（政策必须关闭、待定空权重） | 净零约束 | 由 `research_country_net_zero` 钩子取代；V5 B1 |
| `carrier_architecture.py:44-45` | 跨境非电力 Link | 重写：转换/存储组件仍单国；`TRANSPORT` 角色可跨两国；网络层标签 + B5 |
| `carrier_architecture.py:55` | 新外部商品（H2/NH3/甲醇/LNG 进口） | 重写：任何有来源记录的商品；进口不受不互联情景切断（决定 18） |
| `assembly_components.py:9-11` | CO₂ `primary_energy` GlobalConstraint | 保留为 U4 防线：国家上限是 Store 水平钩子，不是载体系数 |
| `:62-63`（Load 目的母线载体白名单） | 服务/热/H2 Load | 重写：Load 可挂在载体母线本身或 final-energy 接口 |
| `:77-78`（钩子白名单） | 新钩子 | 扩展：`research_country_net_zero`、`research_cross_border_existing_fom` |
| `check_research_carriers.py:14-15, 27-30` | 跨境开关必须为 false；情景不得有差异 | 模块退役；`research.cross_border` + B5/B12（`test_phase4_static` 改为"只差开关"） |
| `check_assembly_inputs.py:47-53` | Road EV 必须嵌入 Astar | 删除；S2 物化部门需求，B11 |

另：`validation_dynamics.py:70-73, 88-89, 93-94`（固定账户核验、政策空值=200）删除，改为每国大气水平 ≤ 上限的物理检查；`integrate_surviving_assets.py:132` 大气端口改为所在国。

## 6. 骨架内容（两个情景）

### 6.1 命名与适配层（S1-1）
- **命名决定：** 采用上游 `"<node> <carrier>"`。电力底座中 92 个 `"<node> :: <fuel>"` 母线（coal 42、gas 34、lignite 8、oil 8）在加载时改名（规则 `' :: ' → ' '`），全部映射见 `S1_EVIDENCE.json → builds.*.rename_map_count` 与网络元数据 `fuel_bus_rename_map`；示例 `BN4 0 :: gas → BN4 0 gas`。研究层新建母线一律 `bus_name(node,carrier)=node+' '+carrier`；大气母线 `co2 atmosphere {ISO2}`。
- **注入的全局变量及来源**（`sector_adapter.INJECTED_GLOBALS`）：`snakemake`（SimpleNamespace：`params.sector_options`=合成配置 sector 段 + `research.hydrogen` 覆盖；`params.countries`=11 国；`params.h2_underground=False`；`input.pipelines`=空 CSV → greenfield；`wildcards.planning_horizons='2050'`）、`options`（同上）、`spatial`（`define_spatial(97 个空间节点, options)`：96 AC 母线 + 无换流器的 DC 母线 `PH_Luzon9 0`）、`countries`、`pop_layout`（只用索引）、`investment_year=2050`、`demand_sc`（`research_assembly.demand_scenario`）、`costs`（EUR2020 价格层表）。
- **上游 `add_hydrogen` 产物：** 97 个 H2 母线、97 电解、97 燃料电池、97 H2 轮机（OCGT 代理）、97 储氢罐、110 条 greenfield 管道（沿 AC 线路与 DC 链路）；对 3 个换流器耦合的 DC 母线做了端点重映射（5 次，1 条自环管道删除，2 条改名 `… via HVDC`）；上游未创建 Load（归属表登记 0 条）；**欧洲专用参数处理**：`network_limit` 2000 GWkm 不施加（上游在 `solve_network.py` 中实现，研究层不用）；气管改氢系数 0.8 不施加（`gas_network_repurposing=False`，空管道文件）；`hydrogen_colors=False`；地下储氢关闭（无东盟洞穴数据，`DATA_PENDING`）。
- **研究配方保留：** SMR、SMR CC（捕集到 `node co2 captured`）、FT、OCGT、CCGT 候选各 100；外部化石供给 400 个 Generator 不动；电解/燃料电池/储氢罐从配方中去掉以免与上游重复。

### 6.2 组件清单（按组件/载体；国家覆盖数见表，分国明细在 `S1_EVIDENCE.json → builds.*.inventory`）

integrated（2920×3h）：1,005 母线、1,247 Generator、1,496 Link、304 Store、237 StorageUnit、105 Line、96 Load（Astar 电力，2,617.76 TWh/a，4 个换流器侧 DC 母线无 Astar 需求）。

| 组件 | 载体 | 数量 | 国家数 | 现有容量合计 | 可扩展 | 跨境 | DATA_PENDING |
|---|---|---|---|---|---|---|---|
| Generator | solar / solar rooftop / onwind | 98 / 98 / 98 | 11 | 0 | 全部 | — | — |
| Generator | offwind-ac / offwind-dc | 72 / 72 | 10 | 0 | 全部 | — | — |
| Generator | nuclear（大型堆） | 96 | 10（无 SG） | 0 | 全部 | — | — |
| Generator | nuclear SMR | 97 | 11 | 0 | 全部（`p_nom_max=0`） | — | 97 |
| Generator | geothermal / ror（新） | 97 / 97 | 11 | 0 | 全部（`p_nom_max=0`） | — | 194 |
| Generator | gas / coal / oil / lignite（外部供给） | 100 ×4 | 11 | 无限量 | 全部 | — | — |
| Generator | ror existing | 22 | 6 | 6,500 MW | 否 | — | — |
| Link | CCGT existing / coal existing / lignite existing / oil existing | 34 / 42 / 8 / 8 | 8/8/5/4 | 74,924 / 253,862 / 13,094 / 5,846 MW_th | 否 | — | — |
| Link | OCGT / CCGT / SMR / SMR CC / FT | 100 ×5 | 11 | 0 | 全部 | — | — |
| Link | H2 Electrolysis / H2 Fuel Cell / H2 turbine | 97 ×3 | 11 | 0 | 全部 | — | — |
| Link | H2 pipeline | 110（dis 90） | 11 | 0 | 全部 | 20（dis 0） | — |
| Link | battery/home battery charger+discharger、distribution grid | 98 ×5 | 11 | 0 | 全部 | — | — |
| Link | DC / B2B | 10 (dis 5) / 3 | — | 18,459 / 6,000 MW | DC 可扩展 | 5（dis 0） | — |
| Line | AC | 105（dis 86） | — | 384,799 MW | 全部 | 19（dis 0） | — |
| Store | battery / home battery / H2 Store Tank | 98 / 98 / 97 | 11 | 0 | 全部 | — | — |
| Store | co2 atmosphere | 11 | 11 | — | `e_min_pu=-1` | — | — |
| StorageUnit | hydro existing / PHS existing | 40 / 3 | 8 / 2 | 38,766 / 2,686 MW | 否 | — | — |
| StorageUnit | hydro / PHS（新） | 97 / 97 | 11 | 0 | 全部（`p_nom_max=0`） | — | 194 |

disconnected 与 integrated 的差别仅为：移除 19 条跨境 AC 线路、5 条跨境 DC 链路、20 条跨境氢管道；Generator/Store/StorageUnit/Load/Bus 集合完全相同（`test_s1_built_networks`）。配置差异仅 `research.scenario` 与 `research.cross_border.*`（B5 配置差异集 = 允许集）。

### 6.3 分国碳记账（S1-5）
- 11 个 `co2 atmosphere {ISO2}` 母线各配一个 Store（`e_nom_extendable`、`e_min_pu=-1`、`e_initial=0`）。电力底座 92 个存量化石 Link 的 `bus2` 从 `ReportingCO2 atmosphere` 重接到所在国大气（93 次改动含删除旧母线）；OCGT/CCGT/SMR/SMR CC 直接连所在国大气。排放端口共 492 个（存量 92 + 新建 400），每个组件只有一个大气端口，端口国 = 组件物理端口国（`country_carbon.validate_country_attribution`）。
- U4：所有 Carrier 的 `co2_emissions` 为 0（电力底座已为 0，`fix_u4` 零改动）；Generator 不带载体碳强度，碳只经 Link 端口记账。
- 约束：`add_country_net_zero` 在 `extra_functionality` 阶段为每国加 `Store-e[最后时段, 大气] ≤ 上限`（11 条，冒烟测试中确认生成：`research_country_co2_limit-XX`）；`asean_total` 模式一条合计约束。
- 冒烟测试排放分国报告：`EMISSIONS_BY_COUNTRY.json`（所有国家最终水平 0.0，`every_tonne_booked_once=True`）。

### 6.4 跨境与情景开关（S1-6）
- 标签：全部 Line/Link 带 `border_class`（domestic/cross_border）与 `transport_carrier`（electricity/H2/gas/co2/local）。
- integrated：24 条现有电力边以 2025 容量为下限（`s_nom_min = s_nom`，可扩展）；存量跨境容量**不计 CAPEX**（PyPSA `objective_constant`）**只计 FOM**：按价格层 HVAC overhead / HVDC overhead / HVDC inverter pair 的 FOM% × investment × 长度 × 2025 容量，合计 18,966,302.7 EUR/a，以固定为 1 的变量 `Research_existing_cross_border_FOM_constant` 一次计入目标（与存量机组 FOM 做法一致）。
- disconnected：移除 24 条电力边与 20 条跨境氢管道；`existing_cross_border_fom_eur = 0`。
- 走廊表 `research_inputs/corridors/cross_border_corridors.csv`：24 行（电力底座 + Gate4 控制集；容量取 `s_nom_min`/`p_nom_min`；`subsea_share=0`，因冻结底座无 `underwater_fraction`，与 `build_electric` 资本成本规则一致）；新走廊待 L18。
- 输电总量上限：参数化，默认继承冻结常数（第 4 节）。

## 7. 存量核查（S1-3）

**地热寿命。** `lifetime_decisions_s1.json`：Geothermal 30 年，来源 technology-data `outputs/costs_2050.csv` 第 1025 行 `geothermal,lifetime,30.0,years,"Aghahosseini, Breyer 2020 …"`（文件 SHA256 `d9fe69fc…`），B 级（公开可引用的技术数据、非东盟机组观测），理由：原 15 年是 powerplantmatching 通用填充值、无地热来源且使所有地热在 2050 前退役。重算（单元级、仅 Geothermal，其余记录逐字不变）：31 个单元中 3 个由 NOT_ACTIVE_2050 → SURVIVES_2050（`GEM:G100000700240` 91 MW 2021、`G100000700262` 45 MW 2021、`G100000700263` 50 MW 2022，退役年 2051/2051/2052），8 个由"按观测年上限证明退役"→ UNRESOLVED_COMMISSIONING（2025+30 > 2050，不再能证明退役），其余不变。**2050 存续地热（MW）：ID 186，PH 0**（15 年时全部为 0）。**未并入网络**：集成合同 `SELECTED_INTEGRATION_CONTRACT.json` 没有 `Geothermal` 性能记录（效率/FOM/VOM），按规则进入 pending，未编造。另注：GEM 在运地热 ID 2,431.9 MW、PH 1,937.0 MW，而冻结 `powerplants.csv` 只匹配到 31 个单元（≈1,323 MW），存量地热覆盖缺口属 R12 数据核查。

**Bataan 核电（PH，621 MW）。** GEM `Global-Nuclear-Power-Tracker-July-2024.xlsx`（SHA `0e9c1291…`）原始行：`Status=mothballed`，`Start Year`、`First Criticality Date`、`First Grid Connection`、`Commercial Operation Date` 均为空，`Construction Start Date=1976-07-01`。判定：从未商业运行 → `EXCLUDED_NEVER_COMMERCIAL_OPERATION`（冻结存量中它本就是 `UNRESOLVED_EXISTING_STATUS`，不在电力底座；S1 存量文件 `results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json` 明确标注）。

**水电（只报告差异）。** 研究层存量 vs GEM 在运（MW）：

| 国家 | 研究层合计 | GEM 合计 | 差 | 主要差异项 |
|---|---|---|---|---|
| ID | 5,038 | 5,369 | −331 | Reservoir −110、ROR −221 |
| KH | 1,298 | 1,298 | 0 | — |
| LA | 9,220 | 9,745 | −525 | Reservoir −525、ROR +60、GEM "unknown" 60 |
| MM | 3,014 | 3,014 | 0 | ROR +74 vs GEM "unknown" 74（子类归类差异） |
| MY | 6,104 | 6,158 | −54 | ROR −54 |
| PH | 2,963 | 3,436 | −473 | GEM 338 MW "conventional and run-of-river" 混合类 + ROR 差异 |
| TH | 3,570 | 3,570 | 0 | 子类互换：研究层 PHS 1,950 / 水库 1,620，GEM PHS 1,171 / 水库 2,399（779 MW 归类不同） |
| VN | 16,745 | 16,701 | +44 | ROR +398 vs GEM "unknown" 398；Reservoir +44 |
| BN/SG/TL | 0 | 0 | 0 | — |

明细见 `results_project/s1/S1_STOCK_REVIEW.json → hydro`。差异来源是 Gate4 冻结匹配与子类归类，不是本步修改范围。

## 8. 求解结果

**正式日分辨率求解未执行**（见第 2 节）。以下为冒烟测试（HiGHS IPM+交叉、56×3h、`SMOKE_TEST_ONLY`），只检验机制，不得用于任何结论或结果表。

| | integrated | disconnected |
|---|---|---|
| 状态 | ok / optimal | **infeasible**（HiGHS，32 s） |
| LP 规模 | 238,824 列 / 525,328 行 / 1,092,510 非零元 | 同量级 |
| 目标值 | 1.6727×10¹¹（56 时段上摊全年年金，不可解读） | — |
| 每国净零约束 | 11 条已生成且在最后时段生效（所有国家大气水平 0.0） | 11 条已生成 |
| 冒烟装机（>0，MW/MWh） | 核电 114,177；光伏 310,605；屋顶 172,400；陆上风 115,517；海上风 16,060+51,465；电池 1,172,538 MWh（充 107,231 / 放 109,442 MW）；户用电池 336,839 MWh；存量水电 38,766、PHS 2,686、ROR 6,500；存量化石容量保留但零出力 | — |
| 跨境容量/流量 | 44 条跨境边（24 电 + 20 氢），优化容量 133,086 MW，56 时段跨境能量 10.8 TWh（两向合计） | 0 条（结构） |
| 检验数 | 3,229 个容量变量导出（`capacity_reduced_costs.csv`）；交叉得到的顶点上全部为 0（退化：边际价值由容量约束对偶承担）；已核验 `c − Aᵀπ` 与解算器检验数一致（最大差 3.9e-3，相对 1e-12 量级） | — |
| 节点价格 | 导出 1,005 母线（`nodal_prices*.csv`）；56 时段上年金摊销使电价约 3,600 EUR/MWh，无解读价值 | — |

**disconnected 不可行的定位（未放宽任何约束）：** 结构性供给诊断（`INFEASIBILITY_DIAGNOSIS.json`）显示 11 国中只有新加坡无法用零排放资源覆盖需求：56 时段需求 2,425,295 MWh，光伏+屋顶+海上风电潜力上限 130,745 MWh（5%），无水电，大型堆按选址表不允许，SMR `p_nom_max=0`（数据待定），无氢/分子进口（S3），不互联无法从马来西亚进口 → 每国净零（上限 0）下无可行解。其余 10 国要么有无上限核电候选要么可再生潜力远大于需求。这是决定 38（SG 只允许 SMR）+ SMR 数据缺失 + 本步无进口的组合结果，不是代码错误；在 S3 接入分子进口或用户决定 SMR 数据/新加坡核电选址前，disconnected 情景在"每国净零"下将保持不可行。

## 9. V5 已实现门槛的结果（冒烟，`RESEARCH_V5_SKELETON`，不是正式验收）

| 门槛 | integrated | disconnected |
|---|---|---|
| A1/A2 KKT 代数 + 行列预算（V4 算法原样，D=R=1） | PASS：相对间隙 2.6e-13；行/列越界 0；驻点越界 0；对偶符号越界 0 | 无解，不适用 |
| A3 物理方程（母线平衡、多端口、储能状态、容量/出力界、LV 上限、每国碳上限） | PASS（0 项失败） | — |
| A4 NetCDF 回读 | PASS（`scripts_project/netcdf_readback.py`：21 个时序表逐值一致；PyPSA 导出时省略的全默认列 `Link.p2/p3`（各 1,496 列、默认 0）按声明默认值恢复后比较，与 D 阶段 `daily_physics.netcdf_roundtrip` 规则相同；派生拓扑列 `sub_network`/`x_pu` 等不比较）。首两轮失败分别来自派生表 `SubNetwork` 与派生列 `Bus.sub_network`，均为求解时 PyPSA 重算的簿记量，不是结果 | — |
| A5 FOM 只计一次 | PASS：目标 = 新建年金 158.78 bn + 可变 0.24 bn + 已知固定 8.24 bn（存量机组 FOM 8,224.5 M + 存量跨境 FOM 19.0 M） | — |
| A6 规模绑定 | PASS（LP 维度与网络 SHA 与回执一致） | — |
| B1 每国净零（范围：存量化石、OCGT/CCGT、SMR/SMR CC） | PASS：11 国最终水平 0.0 ≤ 0；每吨只记一次 | — |
| B5 两情景只差开关；不互联跨境容量/流量=0 | PASS（配置差异集 = {scenario, cross_border.*}）；disconnected 跨境组件 0、容量 0；流量项因无解标记 NOT_EVALUABLE（结构已满足） | |
| B6 一体化成本 ≤ 不互联 | **NOT_EVALUABLE**：disconnected 无最优解，未为取得可比成本放宽任何约束 | |
| B11 技术/路径完整性 | PASS：缺失 0；`DATA_PENDING` 485（单列） | 同 |
| B12 配置开关与哈希一致 | PASS；成本缩放层全 1.0 哈希一致（文件 + 内容）；两次独立构建字节一致（`PYTHONHASHSEED=0`，因 PyPSA 按集合顺序写组件） | 同 |

取消的 V4 门槛：`807_inventory`、`385_obligations`（随固定账户退役）。

## 10. DATA_PENDING 清单

| 项 | 数量/位置 | 缺什么 |
|---|---|---|
| nuclear SMR 候选 | 97 节点，`p_nom_max=0` | SMR 反应堆成本/寿命（technology-data "SMR" 是蒸汽甲烷重整） |
| geothermal 新建候选 | 97 节点 | 站址潜力（MW）；另注 technology-data 地热 `CO2 intensity` 0.12 t/MWh 未建模 |
| ror / hydro / PHS 新建候选 | 97 ×3 | 站址潜力、入流/出力曲线、水库时长（PHS 暂用既有 6 h 决定作过渡） |
| 存量地热集成 | ID 186 MW | 集成合同的地热性能记录（效率/FOM/VOM） |
| 地下储氢 | 全部节点 | 东盟洞穴数据 |
| 新跨境走廊 | 走廊表只有 24 条现有边 | L18 数据 |

## 11. 遗留问题与需要用户决定的事项

1. **B6 的"拆分存量跨境线路"要求与代码现实冲突（决定与代码冲突，按指令报告不自行变通）。** 指令前提"PyPSA 对可扩展线路按全部 `s_nom_opt` 收取资本成本"在 PyPSA 0.30.3 不成立：`optimize.py:87-110` 把 `capital_cost × 初始 s_nom` 作为 `objective_constant` 扣除，`validation_dynamics.OBJECTIVE_RECONCILIATION` 也按 `(s_nom_opt − s_nom) × capital_cost` 核对。此外把 AC 线路拆成并联的"不可扩展 + 可扩展"两条会改变基尔霍夫电压定律的分流（固定阻抗下新线路即使容量为 0 也必须按导纳比承担潮流）。本步实现：不拆分，存量跨境容量不计 CAPEX（PyPSA 既有行为）、FOM 按价格层参数一次计入（可由 `research.existing_cross_border_electricity.fom_on_existing` 关闭）。请用户确认是否接受，或要求改为 DC 链路可拆/AC 不拆的方案。
2. **disconnected 在每国净零下不可行（新加坡）。** 需要决定：允许 SG 大型堆？提供 SMR 数据？或等 S3 分子进口后再求解 disconnected。
3. **作者成本覆盖。** 风电/光伏（及 SMR 等）成本在作者原始 `costs_2050.csv` 中来自 8th AEO（光伏投资约为 technology-data 的 2.9 倍，风电略低），新口径是否沿用需决定（R12A）。
4. **输电总量上限**（决定 45）：当前继承冻结常数 353.7 M MW·km（隐含 2.79 倍）；`factor_of_existing` 模式已实现待选。
5. **存量地热 186 MW 待性能合同；GEM 在运地热 4.4 GW 与冻结匹配 1.3 GW 的覆盖缺口** → R12。
6. 冒烟测试中 HiGHS 顶点上容量变量检验数全为 0（退化），正式 Gurobi 求解时需同时导出容量约束对偶以表达边际价值；已在 `Pi.npy` 中保存全部对偶。
7. 退役模块的历史执行脚本（gate5/gate6 运行器）仍引用 `fixed_accounts`，它们不是新口径入口，S4 统一处理。
8. 旧测试 `test_gate4_activation.py` 4 项在基线分支即失败（与 S1 无关，基线记录 `evidence/baseline_pytest_full.log`）。

## 12. 测试与运行记录

- 单元/集成测试：`pytest tests/research`（WSL）：S1 分支 **343 通过 / 4 失败**（4 项为基线即失败的 `test_gate4_activation.py`）；基线分支 345fc30f：405 通过 / 4 失败（同 4 项）。记录：`S1_TEST_RUN.json`、`evidence/*pytest*.log`。
- 新增测试：`test_s1_country_carbon.py`（7）、`test_s1_scenario_switches.py`（10）、`test_s1_adapter_daily_v5.py`（12）、`test_s1_built_networks.py`（8，依赖已构建网络）。
- 运行记录：构建回执 `evidence/integrated/integrated_BUILD_RECEIPT.json`、`evidence/disconnected/…`；哈希/确定性 `evidence/S1_COST_LAYER_HASH_CHECK.json`、`S1_DETERMINISM_CHECK.json`；冒烟 `evidence/smoke/*/SOLVE_RECEIPT.json`、`V5_GATES.json`、`EMISSIONS_BY_COUNTRY.json`、`INFEASIBILITY_DIAGNOSIS.json`、`S1_SMOKE_B5_B6.json`；机器可读汇总 `S1_EVIDENCE.json`。
- 网络文件（未提交，SHA 在 `S1_EVIDENCE.json`）：`results_project/s1/{integrated,disconnected}/*_2920_3h_unsolved.nc`、`*_365_24h_unsolved.nc`。
