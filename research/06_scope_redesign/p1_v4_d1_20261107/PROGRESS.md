# D1 进度（V4_D1_INSTRUCTION.md v1，SHA256 189bcfa5…f8a5 已核对，与 V4_D1_SHA256.txt 一致）

- 分支 `codex/v4-d1-20261107`，起点 `7aa356e4` = `codex/v4-w08-20261106` 头（开工时本地与远端一致，fetch 核过）；`bd890bf9` 是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_w08_20261106/` 下 3 个文件（EVIDENCE.json、PROGRESS.md、evidence/REVIEW_ZIP_MANIFEST_bd890bf9.txt），交付目录之外 0 个。
- worktree `/home/jin/wt_v4_d1`；临时目录 `/home/jin/v4d1`。
- 交付目录 `work/p1_v4_d1_20261107/` = 仓库 `research/06_scope_redesign/p1_v4_d1_20261107/`（zip 不入库）。
- 求解额度：第 7 节 2 次 56 时段求解（v4 主算 F1、F2）；已用 0 次。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| D1-1 | 第 1 节：分支、worktree、祖先核实 | 完成 | （随 D1-2 提交） |
| D1-2 | 第 2 节：表目录按开关集命名、HVC 口径开关、EV 系数、运行器与状态脚本、定义文件草案 | 完成：`v4_common`（开关集加 `hvc_basis`、`missing_cost_rule` 两键；`out_<模式>` 只给主集，其余 `out_<模式>_<SHA 前 12 位>`；`check_network_meta` 在 `s2_network` / `m08a_variants` 导出前核对网络元数据 = 表目录 = 配置）；`v4_products.hvc_plants(basis)` / `load_items(hvc_basis)` 接入 `build_steps`（两种口径的 HVC 项与 I2 逐项相同，`tables/D1_HVC_REF_I2.csv`；整链 S7 口径 (a) 与 I2 `hvc_s2` 逐国差 ≤ 4.5e-7 TWh，`tables/D1_HVC_CHAIN_CHECK.csv`）；EV 系数 = 16.0712 / 53.19 × 1（注册表，未取整），W08 测试 `test_v4_transport_accounts.py` 两行断言随之改；`out_ras` / `out_iid` 重写：10 个网络读取表与 W08 逐字节相同，只 `SNAPSHOT.json`（EV）与 `V4_SWITCHES.json` 变；`hpc_v4/run_batch4.sh`、`hpc_v4/hpr_status.sh`（v3.1 包文件的副本，原文件 SHA 不变）；`s2_solve.py --package-commit`；`batch_def/BATCH_DEF_2920x3h_v4hpc.json` 草案（PROPOSED）；`test_v4_d1_prep.py` 14 项通过。`missing_cost_rule` 键在本步定义（开关集 SHA 覆盖它），作用在 D1-3 实现 | 见 git log（D1-2） |
| D1-3 | 第 3 节：油棕树干缺数成本规则 | 完成：`s2_layers.biomass_missing_cost` + `add_biomass_layer(missing_cost=…)`，`s2_network` 按 `switches(cfg)["missing_cost_rule"]` 接入；`proxy` 只作用于注册表成本 DATA_PENDING 且成本列为空的池（恰为 5 个油棕树干），代理价从注册表读（新行 `biomass_missing_cost_proxy` = 32 行同源代理价 6.26706128163，构建时再核一次）；`zero` 走原路径（无新账本 / 元数据键）；注册表 2,390 → 2,391 行（原有行 0 改动；新片段 `v4_d1.csv`，`scripts_project/v4_d1_registry.py`）；`test_v4_d1_missing_cost.py` 4 项通过；`DOWNLOAD_CANDIDATES.csv` 第 3 节 6 条（只列候选，INFERENCE） | 见 git log（D1-3） |
| D1-4 | 第 4 节：违反物理的登记区间 | 完成：扫描 1,486 行在用参数中带区间的 534 行、8 类检查（`evidence/PHYSICS_SCAN.json`），违反项 11 行，按同一规则截到物理界（`PHYSICS_BOUNDS_FIX.csv`；整行更正片段 `v4_d1_corrections.csv`，`d1_registry.assemble` 拆出，CORRECTIONS 末位）：BEV 充电效率、BEV 可用上限上端 → 1；甲醇 / t CO₂ 上端 → 4.02482（主值 4.0321 高于化学计量 0.18 %，只报告不改）；甲醇 / MWh H₂ 上端 → 0.8787（主值与界差 1.5e-7，取整）；电解制氨氢耗下端 → 5.91803（化学计量最小）；氨、甲醇热值三行区间退化为点；油品船运热值上端 → 13.9 MWh/t、天然气质量热值上端 → 50.04 GJ/t（甲烷热值上限）；船运年小时数上端 → 8,760。主值、状态、其余 2,380 行不变；构建代码不读区间列。另有 21 行"主值不在区间内"属多方法区间，非物理问题，只记录。`test_v4_d1_physics.py` 4 项；读注册表的 26 个测试文件 217 过 / 24 跳过（补齐被忽略的 `finance_v5` 两个输入后） | 见 git log（D1-4） |
| D1-5 | 第 5 节：T03 棕榈油厂纤维与 PKS 厂内自用份额 | 文献检索进行中（子代理） | |
| D1-6 | 第 6 节：抽蓄研究与建议 | 文献检索进行中（子代理） | |
| D1-7 | 第 7 节：网络重建、静态检查、求解前登记、2 次求解 | 未开始 | |
| D1-8 | 报告、证据、审阅包、推送 | 未开始 | |

续做点：D1-2。
