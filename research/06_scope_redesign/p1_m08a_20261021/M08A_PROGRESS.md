# M08A 进度（随进度更新）

- 指令：`M08A_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `19c00a1e127bc30c470a498fc2c765905a6923072452a02c50d4f3abeb849476`（与 `M08A_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不求解、不调用 Gurobi（含许可检查）、不连云；不改既有结果与已发布网络文件。
- 工作树：`/home/jin/wt_m08a_20261021`，分支 `codex/m08a-corrections-20261021`（自 M08-0 头 `30d281b8`）。
- `GATES_V6.md` SHA256 `5c0aa8b8…7f9` 核对一致。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | 开分支 + 普通 merge S4Q（`22f53c84`）；冲突仅台账，双方保留 | 完成 | 4247f21b |
| A1 | 货币平减 EEA HICP（系数 1/1.2573346；对比变体与旧主层逐字节相同；注册表 2,057 → 2,061；测试子集 97 passed / 24 skipped） | 完成 | 77a9a07c |
| A2 | 核电同源（SMR 8,421 → 9,167 EUR/kW）、AEO8 价格年系数；新增 `m08a_data.py` 片段机制；测试 100 / 24 | 完成 | 0e39df2e |
| A3 | 存量机组按投运年取 v0.15.0 表（`m08a_layers.py`）；存量 FOM 10.806 → 10.050 bn/a，两情景相同；CCGT 0.56 / 0.57；测试 105 / 24 | 完成 | 4cc95598 |
| A4 | LNG `capex_only`（16 台 p_nom_max = inf）、8,020.43、加价 1.26、液氢 × 1.2；测试 110 / 24 | 完成 | 04d686fe |
| A5 | 封存统一表（VN 106.07、PH 1.344 Mt/a；年上限 = 潜力 / storage_years）；测试 114 / 24 | 完成 | 79b0f3e6 |
| A6.1 | 地面光伏 p_nom_max × 5.1/4.6（分级前、11 国同一系数；屋顶 / 存量不变）；底座测试 3 passed | 完成 | f1de7cb5 |
| A6.2 | 海上风面积规则（PyPSA-Eur v2025.07.0：≤60 m、漂浮式 60–1,000 m、航道 400×8760×6、2 MW/km²、200 m、ESRI:54009）；`m08a_offshore_profiles.py` 全量 3 分 22 秒、峰值 2.65 GB；AC 1,783.2 / DC 2,714.3 / 漂浮 4,435.8 GW（as-built 1,672.9 / 3,054.3）；作者规则复算 1,673.3 / 3,052.2 GW；航道仅排除 57.2 MW；接入 `s4a_layers.apply_offshore_rules`、成本层、审计 / dust / 台风列表；测试 144 / 24 + 电力底座 4 passed | 完成 | 见 git log |
| A7 | 四个开关 + `m08a_variants.py`（确定性派生、回执 SHA256）；取证 5 个变体；测试 120 / 24 | 完成 | bf181b68 |
| A8 | `v5/gates_v6.py`、子集哈希写入网络与回执、`solver.run_rules`、运行脚本 `m08a_run_batch.sh`；测试 130 / 24 | 完成 | 7e38c500 |
| A9 | 账本美元列（明细 `usd2020*` 列 + 美元宽表）；发现输入汇率差 0.20 %；测试 133 / 24 | 完成 | 9fb4e584 |
| A10（部分） | A6.1 注册表行（光伏密度、土地规则、开阔林触发、海上 alpha）+ co2_sequestration_cost_price_year、co2_storage_vn_shipping_interaction；注册表 2,111 行（`5b79654d…`），m08a 新行 50、修正 42；测试 136 / 24 | 完成 | 见 git log |
| S01-1 | 补充 01 第 1 点：`GATES_V6_NOTES.md` 第 6 节"实现说明：子集键清单"（30 键），测试子集键 = 说明表；NOTES SHA256 `d296ddcf…` → `cad04000…`；测试 137 / 24 | 完成 | 4c46f442 |
| S01-3 | 补充 01 第 3 点：报告汇率 = 1 / `fx_usd_to_eur_2020` = 1.139954（`reporting.fx_per_eur2020: inverse_of_input`）；ECB 1.1422 作对照行；测试 138 / 24 | 完成 | 2a0a660b |
| S01-2 | 补充 01 第 2 点 + §2：b1 范围确认；老挝过境通道保留并强制检查（`check_landlocked_transit`、`co2_sink_channels`）；**A5 遗留构建缺陷修正**（船运路线表 70 条 TL 路线，`apply_intra_asean_shipping` 精确相等检查会使重建失败）；取证 32 行全有出口；测试 140 / 24 | 完成 | adc0460e |
| A10（余） | 海上规则行（A6.2 之后）；整步注册表差异表 | 待做 | |
| 交付 | 全量测试、报告、台账、PR、审阅 ZIP | 待做 | |

## 代码探查要点（2026-10-21，供接续）

- 环境：WSL `/home/jin/miniforge3/envs/pypsa-earth/bin/python`；脚本放 `/home/jin/m08a_*.sh`（`$` 变量不能放在 `wsl bash -lc` 字符串中）；`*.csv/*.xlsx` 被忽略，需 `git add -f`；worktree 缺 `research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv`（副本在 `/home/jin/wt_m080_20261020/research_inputs/finance_v5/`）。
- 测试：只跑读注册表的 27 个文件，排除 `test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers`、`test_s3b_r4.py::test_scaling_round_trip_small_model`（HiGHS 玩具求解）；先 grep `optimize(`。
- 构建：`s2_network.build_scenario_s2` 两次独立构建（integrated / disconnected，仅 cross_border 四开关不同）；override 解析 `s2_network.py:274-288`，`NEW_OVERRIDE_KEYS` 与 `v5_gates.gate_b12_hash:163` 同步。
- A1：构建期价格全部来自 `s2_costs.build_research_costs` 的 prepared 表；数据脚本写入注册表的派生货币行（如 gas_pipeline_cost_*）只是文档。
- A2：SMR 在 `s2_costs.py:86-93`（注册表 smr_*），地热 `s2_costs.py:94-104`（AEO8 字面量 × fx）。
- A3：存量参数来自冻结底座（`integrate_surviving_assets.py`，作者 v0.13.2），构建期不改；`n.meta["existing_unit_components"][unit]` 有 commissioning_year / capacity_mw / component；FOM 常数 `n.meta["existing_annual_fixed_om_eur"]`（10.806 bn，两情景相同），组件列 `existing_fixed_om_eur_per_mw_year`、`existing_annual_fixed_om_eur`，一致性校验 `assembly_components.py:108-114`；Link `p_nom = MW_el / eff`、`marginal_cost = VOM × eff`；映射 `s4a_fleet.py:31 FUEL_OF` 与 87-133；插入点 `s2_network.py:340` 之后。
- A4：`s3_layers.py:155-187` LNG（模式校验 158、capex 160、p_max 173；已有 `uncapped_cost`）；加价 57/180 已有代码路径；液氢码头 `s3_layers.py:249-258` 成本写死 8421.6；B14 `v5_gates.py:325`；测试 test_s4b_0 / test_s3b_r3 / test_s3_imports / test_s3_gas_network / test_s4c_0 / test_s4e_2 / test_d1_registry::test_lng_caps。
- A5：`s2_layers.py:262-285` 读注册表 `co2_injection_cap_{c}`（÷50 写死在 `d1_co2_storage.py`）；测试 test_d1_registry::test_co2_storage、test_s2_built_networks::test_s2_co2_two_layer_storage（TL Store 将消失）。
- A7：CO₂ 东盟内船运 carrier `CO2 ship`、`CO2 transit ship`、`CO2 transit rail`（maritime_trade）；区域外 `CO2 export extra-ASEAN`、`CO2 transit export extra-ASEAN`（bus1 carrier `co2 sequestered extra-ASEAN`）；液体池母线 `ASEAN oil|oil non-fossil|ammonia|methanol`，接入 `oil pool <node>` 等；进口点 `<node> LNG import`、`<node> H2 import`；燃料舱负荷 country=ASEAN；WACC `s4c_layers.py:120-159`（solar rooftop 的 0.04 会被覆盖，TL 缺值报错）。硬编码 100 节点 / 11 国检查：`s2_network.py:114`、`country_carbon.py:91,108`、`v5_gates.py:86`。
- A8：对偶预算 `s4b_acceptance.budgets():44`；C1 `s4o_c1_precision.py`（STD:50，acceptance 206-208）；`s2_solve.py` 写 SOLVE_RECEIPT / V5_GATES；运行脚本 `research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh`（白名单 104、TimeLimit 111、停止条件 323-333）。
- A9：账本 CSV 写在 `s2_solve.py:376-378`（`s4d_ledger.ledger_table`）；注册表 `fx_usd_to_eur_2020` = 0.8772286（倒数 1.13996，与 1.1422 差约 0.2 %）。
- A6：光伏 p_nom_max 只在 `s4a_layers.apply_renewable_profiles` 拆分（c3）；乘系数放在其开头（:43 后），须在 dust（s4l，最后一层）之前；测试 test_s4a_profiles.py:59,75 会受影响。`s4a_profiles.py` 不算可用面积，复用作者 `potential`；现行海上规则只在作者链（AC 2 MW/km² ≤50 m ≤30 km；DC 3 MW/km² ≤50 m ≥30 km）。缓存：cutout `research_model/cutouts/asean_zenodo_20325289/cutout-2013-era5.nc`（7.35 GB）、GEBCO `pypsa-asean/data/gebco/GEBCO_2025_sub_ice.nc`、EEZ `pypsa-asean/data/eez/eez_v11.gpkg`、natura、航运 zip 535 MB（tif 9.8 GB）。本机 16 线程 / 10 GiB。估算 25–60 min、峰值 3–5 GiB、永久 <1 GB（推断）。漂浮式行 `offwind-float*` 在 costs_2050 1186-1197（有）。新载体要改的位置：s4a_layers:26、s4c_layers:72/240、s4c_1_offwind_distance:47、baseline cost_scaling、s4l_layers:51、s4b_layers:112、s4m_cost_breakdown:41/103 等；测试 test_s4a_profiles:27、test_s4c_1:53。
- A10：`d1_registry.py` 片段列表 FRAGMENTS(:20-24)、修正 CORRECTIONS(:26)，整行替换、id 不得重复；"历史：已被 X 替代"追加在描述末尾。

## 接续点（2026-10-21，第一会话结束时；上下文约 60 % 以上，按指令请用户开新会话）

已完成并提交：0、A1–A5、A6.1、A7–A9、A10 部分（提交见上表；分支已推送 origin）。工具脚本（WSL）：
- `/home/jin/m08a_tests.sh`：`m08a_data.py` → `d1_registry.py` → 无求解测试子集（读注册表的文件 + `tests/research/test_m08a_*.py`；排除两个 HiGHS 玩具求解用例）；`REASSEMBLE=0` 跳过重拼，`TAILN` 控制输出行数。
- `/home/jin/m08a_commit.sh`：把 `work/p1_m08a_20261021/{M08A_*.md,evidence,scripts}` 镜像到 `research/06_scope_redesign/p1_m08a_20261021/`，`git add -A` + 强制加入 `/home/jin/m08a_force.txt` 所列被忽略路径，按 `/home/jin/m08a_msg.txt` 提交（消息末尾带 Co-Authored-By）。
- 注册表新行：`scripts_project/m08a_data.py`（每任务一个函数；`main(steps=...)` 已含 a2–a10；新任务要追加函数名）；修正行用 `Corrections.supersede/modify`。

### 下一会话要做

1. **A6.2 海上风面积规则**（指令 A6 第 2 项；估算 25–60 min、峰值 3–5 GiB、永久 < 1 GB，未超原则 7 阈值，INFERENCE）：
   - 先联网只读核对 PyPSA-Eur v2025.07.0 `scripts/determine_availability_matrix.py`（航道 `ship_threshold × 8760 × 6`、`min_depth` 写法）与 `build_ship_raster.py`；配置副本 `research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml` 第 201–260 行（AC / DC ≤ 60 m、30 km 分界、ship_threshold 400、excluder_resolution 200、2 MW/km²；漂浮 60–1,000 m、NREL_ReferenceTurbine_5MW_offshore、landfall 40 km）。
   - 新脚本（建议 `scripts_project/m08a_offshore_profiles.py`）：节点海上区域沿用 `s4a_profiles.py`（Voronoi 裁到作者 offshore_shapes）；ExclusionContainer 加 Copernicus 80/200（invert）、natura、GEBCO 深度、航运密度栅格（`/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw12/shipdensity_global.zip`，可用 /vsizip/ 免解压）、离岸距离缓冲；cutout `research_model/cutouts/asean_zenodo_20325289/cutout-2013-era5.nc`；输出新变体廓线（AC / DC / float × c3）、分级潜力表、离岸距离表（`s4c_1_offwind_distance.py` 同法）。
   - 构建接入：新配置键（如 `renewable.offshore_rules: pypsa_eur_v2025_07 | author_pypsa_earth`）；`s4a_layers` 对海上 AC / DC 用新潜力替换（不再拆分底座值），新增 `offwind-float` 发电机与载体；成本 `s4c_layers.CARRIER_COST_ROWS` 与 `apply_cost_layer_s4c1`（offwind-float + float-station + submarine × 距离 + underground × landfall）；`cost_scaling` 加 offwind-float；载体列表 s4l_layers:51、s4b_layers:112、s4m_cost_breakdown:41/103、s4c_1_cost_audit:60、price_basis:129、build_research_assets:91、selected_closure:31、s4i_static_audit:28；测试 test_s4a_profiles:27、test_s4c_1:53；漂浮式成本行 costs_2050 `offwind-float*` 存在（1186–1197 行）。
   - 注册表：`renewable_offshore_rule`（v2 行），被替代 `renewable_landcover_codes_built_offwind_ac/dc`、`renewable_density_built_offwind_dc`、`renewable_offshore_depth_rule` → REFERENCE_ONLY。
2. **全量测试**：`tests/research` 全部文件（先 `grep -n "optimize(" tests/research/*.py`，只排除玩具求解用例并在报告中写明），写明通过数。
3. **交付**：`M08A_REPORT.md`（开头 15 行以内摘要；逐项改动、配置键、测试、偏离与理由；注册表变化与未决项；开头醒目标出下列发现），`STAGE2_PROJECT_LEDGER.md` 追加 M08a 条目，draft PR（`gh pr create --repo cyc292cycjin-oss/SGP-ESE5004-Stage2 --base codex/m08-0-registry-backfill-20261020 --draft`，叠在 #44 上），审阅 ZIP（逐成员 SHA256 + CRC 清单）。注册表整步差异：`research/06_scope_redesign/p1_m080_20261020/scripts/m080_registry_diff.py`（基准 M08-0 头 `30d281b8`，注册表 `6d1b2c34…`）。

### 已发现、须写入报告的事项

1. **G2.2 子集**：按 GATES_V6 原列表实现，另加 `cost_layer`（整段）、`site_candidates`、`disconnected`、`coalition`（理由：这些键改变网络 / LP，原列表只有 `cost_layer.active`）；`GATES_V6.md` 未改，请用户确认。
2. **汇率**：注册表 `fx_usd_to_eur_2020` = 0.8772286（倒数 1.13996）与报告汇率 1.1422（ECB 2020 年均）差 0.20 %；拟增行"= 1/fx_usd_to_eur_2020"的说法有误，已更正；输入汇率未改，待用户决定。
3. **分国 WACC**：原 `apply_wacc_mode` 对缺 `country` 列的底座组件静默跳过（S4M-3 网络 1,864 个），已改为按母线国家确定；线路与跨境资产（两端均值）纳入。
4. **S4R 重评脚本缺陷**：`s4r_r8_retro.py` 的 D7 用 `cap_t`、D9 用 `p_nom_opt`/`p_nom_max`，与门槛实际字段（B2 `final_level_t`/`horizon_limit_t`，B14 `p_nom_opt_mw`/`p_nom_max_mw`）不符，`GATES_RETRO_COMPARISON` 中 D7/D9 实际未算到；gates_v6 已用正确字段。
5. **存量计数**：方案"24 条电力边"为走廊表原始计数；S4M-3 网络中 2025 年容量 > 0 的跨境电力边为 16 条交流线 + 1 条直流（Khlong Ngae–Gurun 300 MW）；气管道 6 条（3 个国家对）与方案一致。
6. **b1 解释**：`forbid` 同时删除 `CO2 transit rail`（老挝经铁路进入 VN / TH 国家封存），理由是同一贸易的陆上段；请用户确认。
7. **液氢码头上限**仍沿用 S3-2 规则（LNG 存量 × 2.5 或规划容量），A4 只取消 LNG 上限；GEM 中 3 个无容量数据的 LNG 节点仍不建候选。
8. **验收字段**：`s4o_c1_precision.py` 的 `acceptance`（第 120 项规则）保留未改；V6 标签由 `gates_v6.py accept` 在 C1 之后产出（运行脚本已串接）。
9. **派生文档行**：数据脚本按旧成本层写入注册表的货币文档行（如 `gas_pipeline_cost_onshore` 91.37）未重算；构建期价格直接取成本层，不受影响。
10. **存量水电 VOM**：technology-data v0.15.0 无 hydro / ror VOM，按规则变为 0（原 0.53 / 0.44 EUR/MWh）；存量 FOM 合计 10.806 → 10.050 bn EUR2020/a。
11. **SMR**：8,421 → 9,167 EUR2020/kW（+8.9 %）。
12. **A5 遗留构建缺陷（已修）**：`CO2_SHIP_ROUTES_S4D2.csv` 有 70 条进入 TL 的路线；A5 后 TL 潜力 0 无国家储罐，`s4d_layers.apply_intra_asean_shipping` 的精确相等检查会让按现行配置的重建失败。改为丢弃并记录进入无储罐接收国的路线（`co2_ship_routes_receivers_rule`）。
13. **直通总线（观察，未改）**：MY_Peninsular22 0、PH_Visayas10 0、TH21 0 的 `co2 stored` 总线只连 FT / SMR CC，无缓冲、管道或封存（`co2_passthrough_buses_note`）。
14. **去掉越南 + b1**：老挝过境链路两端都在 LA，越南移出后仍保留（陆段经越南）；按内陆国过境权惯例理解，请用户确认。
15. **补充 01 汇率**：补充写 1.13996，精确倒数 1/0.877228632573 = 1.139954；实现按精确倒数。
