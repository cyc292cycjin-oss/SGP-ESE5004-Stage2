# M08A 进度（随进度更新）

- 指令：`M08A_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `19c00a1e127bc30c470a498fc2c765905a6923072452a02c50d4f3abeb849476`（与 `M08A_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不求解、不调用 Gurobi（含许可检查）、不连云；不改既有结果与已发布网络文件。
- 工作树：`/home/jin/wt_m08a_20261021`，分支 `codex/m08a-corrections-20261021`（自 M08-0 头 `30d281b8`）。
- `GATES_V6.md` SHA256 `5c0aa8b8…7f9` 核对一致。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 0 | 开分支 + 普通 merge S4Q（`22f53c84`）；冲突仅台账，双方保留 | 完成 | 4247f21b |
| A1 | 货币平减 EEA HICP（系数 1/1.2573346；对比变体与旧主层逐字节相同；注册表 2,057 → 2,061；测试子集 97 passed / 24 skipped） | 完成 | 见下一行提交记录 |
| A2 | 核电同源、AEO8 价格年 | 待做 | |
| A3 | 存量机组成本表 | 待做 | |
| A4 | LNG | 待做 | |
| A5 | CO₂ 封存统一 | 待做 | |
| A6 | 风光布局 | 待做 | |
| A7 | 情景与联盟开关 | 待做 | |
| A8 | 门槛 V6 与运行规则 | 待做 | |
| A9 | 报告货币 | 待做 | |
| A10 | 注册表 | 待做 | |
| 交付 | 报告、测试、台账、PR | 待做 | |

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

## 接续点

A1 代码已写（`d1_common.py` HICP 函数、`s2_0_cost_layer_v015.py` 两变体、`s2_costs.layer_files`、`d1_cost_layers`、配置 `rebase_index`），已重新生成成本层；待：测试、注册表重拼、提交。
