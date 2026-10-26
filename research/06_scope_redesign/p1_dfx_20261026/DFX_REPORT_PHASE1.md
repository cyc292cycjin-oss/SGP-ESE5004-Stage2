# DFX 阶段 1 报告：需求修复（v2 网络）、复核、冒烟与部署包 v8（本机；未连云）

**摘要（≤ 10 行）**
1. 指令 `DFX_CLAUDE_CODE_INSTRUCTION.md` v3 SHA256 `b60da4c6…5a6df` 与 `DFX_INSTRUCTION_SHA256.txt` 一致；暂停会话的遗留（分支 `codex/dfx-20261026`、worktree `/home/jin/wt_dfx_20261026`、`/home/jin/dfx/`）已记录、未沿用、未删除；无遗留进程，暂停会话 0 次 Gurobi 调用（`SECTION0_LEFTOVERS.md`）。
2. 新分支 `codex/dfx-v3-20261026`（基点 `55ab07c0`，与 `ec80668f` 的差异 11 个文件均与需求构建无关），提交：`834a0f19`（第 0 节 + `DFX_RULES.md`，早于任何 v2 构建）→ `72083fde`（F1–F4 代码、注册表、测试）→ `896828fd`（F5.1–5.4 构建 / 等价 / 复核 / 一阶预测 / `RUN_PLAN_DFX.md`，早于任何 v2 求解）→ `5405e477`（冒烟、F6 运行脚本 / 批次模块 / 包脚本 / 替身测试、阶段 2 草稿）→ 阶段 3 提交（`dfx_batch.py` 修复、报告、检查单、证据；哈希见 `DFX_EVIDENCE.json` `branch.log`）。
3. **只改需求**：v2 与 v1 四个网络逐组件比较，差异只在负荷（`loads` / `loads_t.p_set`）、随负荷增减的需求侧计量 / 终端 / 炊事 / 原料组件、过程排放发电机 `p_nom`（工业乘数的派生量）与需求 / 配置哈希 meta 键（测试 `test_f5_structural_equivalence`，4 个网络通过）。成本表、求解档案、验收阈值未改。
4. 需求总量 v1 7,147.6 → v2 **7,628.6 TWh（+481.0）**：交通 644 → 999（RAS 交通锚 2,661 TWh）、工业 3,516 → 3,820、居民 717 → 586、NEU 679 → 663（氨原料气扣除 197.0 TWh，VN 截断 8.2 TWh）、农业 −29。AEO8 ATS → v2 负荷分解闭合残差 **1.6e-10 TWh**。
5. 一阶预测（事先登记于 `RUN_PLAN_DFX.md`）：ΔC_一体化 +19.45、ΔC_不互联 +22.51、**ΔB6 +3.060 bn EUR**（预测 B6 ≈ 14.36 bn）；分国 MY +1.55、SG +1.15、VN +0.38、TH +0.12、ID −0.18（INFERENCE，大变动外推）。
6. 本机冒烟（2 次 Gurobi，56 时段截短 v2 2920×3h，`formal_barrier_1e6_t16`）：一体化 optimal 620 s / 6.99 GiB，不互联 optimal 727 s / 5.52 GiB，间隔 333 s；后处理链（含 Owen、批参照重评、GATES_V6 ACCEPTED_LAYER2 ×2、分级 accepted）全部 exit 0。**本机 Gurobi 调用 2 / 2 用完。**
7. 注册表 `DATA_REGISTRY.csv` 2,194 → **2,280 行**（SHA256 `4c59adb7…` → `7516113e…`），`REGISTRY_CHANGELOG_DFX.csv` 223 行（修改 137、新增 86），映射表 `REGISTRY_NETWORK_INPUT_MAP.csv` 200 行；逐行等于 v2 构建实际输入的测试通过。
8. 部署包 v8 `work/p1_dfx_20261026/cloud_package_dfx/`：提交 = 阶段 3 修复提交（`evidence/package/COMMIT`、`DFX_EVIDENCE.json` `package_v8`），20 个文件约 148.2 MB（两个 365×24h v2 网络 + 回执 + 成本表、代码归档、`run_dfx.sh` / `preflight_dfx.sh` / `pack_results.sh`、第三批同一环境锁定、`RUN_PLAN_DFX.md`、`BATCH3_REFERENCE_VALUES.json`），`SHA256SUMS` 全部 OK；干跑（完整 365×24h 与截短 56 的 BUILD_ONLY、11 项拒绝）在该提交重做并通过；本机预检除许可与资源节外 PREFLIGHT OK。首次构建（`5405e477`）因 `dfx_batch.py` 的导入副作用（见 9）修复而重建，旧包原样保留为 `cloud_package_dfx_superseded_5405e477/`。
9. 测试：需求子集 131 passed / 4 skipped；DFX 运行脚本替身 14 passed。第一次全量测试在第三批 / B4P 替身测试处出现 32 个失败——原因是 `dfx_batch.py` 首版在导入时改写了共享模块 `m10_batch3_summary` 的运行表常数（同一 pytest 进程内第三批测试拿到 V1 / V2 表）；已改为本模块内实现 `run_state`、不再触碰第三批模块，受影响测试文件在同一进程重跑通过；最终全量测试结果见第 9 节与阶段 3 P3。
10. 局限（不在修复范围，指令列出）：燃料舱口径、工业"其他桶"温度分布与 0.90、100 % BEV 能效比、显式制冷、水泥 / 钢参数、甲醇 / HVC 产量化、TL 规则；本次新增：氨原料气 10.8 MWh/t 为 SMR 路线上界（4.92 化学计量值登记为敏感性）、USGS 未列产量国家氨为 0（SG 氨负荷消失）。

## 0. 接手检查（指令第 0 节）

见 `SECTION0_LEFTOVERS.md`。要点：`git branch -a` / `git worktree list` 中有暂停会话的 `codex/dfx-20261026`（`b0dbd52c`，一个只含文档与脚本的提交）与 worktree `/home/jin/wt_dfx_20261026`（干净）；`/home/jin/dfx/` 4 个辅助文件；主检出 `results_project/` 无 dfx 目录；`ps` 无相关进程；暂停会话目录下无 `gurobi.log` / 求解回执 → 0 次 Gurobi 调用。处理：全部原样保留，不沿用；本指令用新分支 / 新 worktree / `results_project/dfx_v3/`；本指令第一次 Gurobi 调用（2026-10-26 14:58 UTC）与暂停会话无时间冲突。基分支核对：`55ab07c0` 与 `ec80668f` 在 `scripts_project/`、`research_inputs/`、`configs/` 的 11 个差异文件（B4P 的分进程求解 / 批次 / 环境脚本）均不在需求构建链上（`SECTION0_LEFTOVERS.md` 第 6 节）。

## 1. F0 代码地图

`CODE_MAP.md`（+ `CODE_MAP_TABLE.csv`、`CODE_MAP_DATA.json`）：`scripts_project/` 300 个文件归为生产管线（构建 31 / 求解 10 / 后处理 10 / 批次与打包 19）、数据链 87、测试与检查 36、一次性数据或证据脚本 96、已退役 11。实际执行清单由 `sitecustomize` 记录器得到：v1 构建 ×2、`--stop-before-solve` 与 `--split-stage build`（56 时段）、56 时段后处理链（违反量 / C1 / M12 / Owen / 账本重做 / GATES_V6 / stop-class）、数据链重跑 → 动态清单构建 32、求解 27、后处理 32、变体 2、数据链 13 个模块。需求链调用顺序（AEO8 / UNSD → 网络负荷）：`m08b_demand.py → m08b_heat_bands.py → s3_0_industry.py → s2b_feedstock.py → s2_0_process_emissions.py → m08b_data.py → dfx_data.py → d1_registry.py`，构建端 `s2_network.py → s2_layers.add_demand_layer`。F0.3 测试 `test_f0_changed_scripts_in_the_executed_lists`：F1–F4 改动的 8 个文件全部在实际执行清单内；重复实现（`d1_demand_2050.py`、`s2b_industry.py`、Gate2 `demand_*`）未改、已标出。第 14 节记录 F6 新增文件的归类。文件整理按指令留到正式运行之后。

## 2. F1–F4 改动与测试（提交 `72083fde`；规则原文见附录 A）

| 项 | 实现（文件） | 关键数值（VERIFIED，来自 v2 构建输入表） | 测试 |
|---|---|---|---|
| F1 NEU 移出包络 + RAS 部门拆分 | `m08b_demand.py`（`ras_split`、`t19` 不含 NEU、RAS 10 国、TL 沿用规则）、`d1_common.py` | 行 = C.8 × D.1 国家锚；列 = C.3 ATS 2050 部门值 × 11.63 × k，k = 0.999823954704（消除印刷合计舍入差 1.53 TWh）；11 次迭代收敛，行误差 3.4e-11、列误差 2.2e-16；部门锚（10 国 + TL）工业 4,500.0 / 交通 2,661.0 / 居民 615.1 / 商业 586.7 / 农业 325.5 TWh；负燃料锚取 0 共 8 格（+65.1 TWh：BN / MY / SG 居民与商业、TH / VN 居民），TL 商业正燃料锚无 2019 结构取 0（0.19 TWh）；工业乘数 BN 0.84 … VN 3.11，TL 工业 2019 为 0 → 乘数 0、NEU 乘数取 KH / LA / MM 均值 2.352 | `test_f1_ras_*`（和 = ΣA_c、部门和 = 缩放后 C.3、相对差 ≤ 1e-9、交通锚、NEU 不在能源用途锚） |
| F2 氨按产量 + NEU 气扣除 | `m08b_demand.py`（`AMMONIA_CSV`、产量规则、扣除）、`s3_0_industry.py`（替换 EU27 份额）、`dfx_data.py`（登记） | USGS MYB 2022 Nitrogen T12 2019（kt N × 17/14）：ID 7,407 / MY 1,457 / VN 1,396 kt NH₃，其余 0；× max(G,1)^((2050−2019)/28×0.5) → ID 13,491 / MY 2,598 / VN 2,907 kt（合计 19.0 Mt）；氨需求 × 5.166 MWh/t = 98.1 TWh，替换 EU27 份额 36.8 TWh；原料气 10.8 MWh/t（PyPSA-Eur `MWh_CH4_per_tNH3_SMR`，上界；JRC-IDEES-2021 无氨行）扣除 197.0 TWh（ID 145.7、MY 28.1、VN 23.2），VN 截断 8.17 TWh（NEU 气归 0） | `test_f2_*`（逐国 = USGS × 规则；MY ≠ 0；SG = 0；扣除与截断） |
| F3 HVC 只作用于原料 | `d1_common.py`（`HVC_FEEDSTOCK_ACCOUNTS`：石脑油、乙烷、LPG、NGL）、`s2b_feedstock.py`、`s2_layers.py`（`hvc_primary_scope`） | NEU 油 704.4 TWh：HVC 原料 579.1 × 0.4，非 HVC 产品 125.3 × 1.0（沥青、润滑油、蜡、石油焦等） | `test_f3_hvc_accounts_exhaustive`、`test_f3_network_scope` |
| F4 注册表刷新与补登 | `dfx_data.py`（片段 `dfx.csv` 86 行、更正 `dfx_corrections.csv` 69 行、映射表、变更日志）、`d1_registry.py`、`m08b_data.py` | 2,194 → 2,280 行；变更 223 行（修改 137：值 / 描述 / 来源 SHA / 敏感性；新增 86：炊具效率 0.08 / 0.16 / 0.53、清洁炊事开关、`HEAT_EFF` 0.90、HVC 范围开关、`node_allocation`、C.3 ATS 部门行、RAS 规则、氨产量规则与 USGS 来源、原料扣除规则与来源）；炊具 TH 0.16 超出原敏感性区间 → 区间上限改 0.25（记录） | `test_f4_registry_rows_equal_the_network`（映射到网络输入的每一行 = v2 实际输入，相对 1e-9）、`test_f4_table_rows_equal_the_inputs` |

配置 `configs/research/baseline.yaml` 只改需求键（`physical_output_base_year.ammonia: 2019`、HVC 开关注释）。`tests/research/test_m08b_demand.py` 3 处断言按新规则调整。

## 3. F5 构建、等价、复核与一阶预测（提交 `896828fd`）

- **构建（VERIFIED）：** M08b 同一命令（`s2_network.py --scenario {integrated,disconnected}`，`PYTHONHASHSEED=0`）于 `72083fde`（dirty 0）→ `results_project/dfx_v3/builds_v2/`：一体化 2920×3h `08879f0b…`（63,873,447 B）/ 365×24h `82928a4c…`（31,292,240 B）；不互联 `d90ca992…`（63,202,193 B）/ `5c75bfa0…`（30,620,986 B）；构建 84 / 76 s。v1 对照：同一路径在基提交重建（`builds_v1`）与 `ec80668f` 登记网络逐组件相同（仅 `n.meta.s2_layers` 构建路径字段不同）。
- **结构等价（VERIFIED）：** `test_f5_structural_equivalence`：除负荷外的差异——(a) 过程排放发电机 `p_nom`（EDGAR × 工业乘数）与 TL 过程排放源消失；(b) 随负荷有无而增减的需求侧组件（Link 114、Bus 52、Load +59 / −15）：氨负荷 BN / MM / PH / SG / TH 消失、MY 新增；TH / VN 居民燃料负荷归零；SG 农业、TH 商业由零转正；VN NEU 气截断为 0；(c) meta 中的需求账本与配置哈希键。其余组件与全部时序逐字段相等。
- **需求复核（VERIFIED）：** `scripts/review/dfx_demand_review.py`（复制自 DMD D1 / D3，只改输入路径与 DFX 规则；修正了 D1 农业账户漏掉 gas 载体——SG 农业天然气 1.21 GWh 在 v2 新出现）：`review/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1/v2.csv`、`DEMAND_DIFF_V2_V1.csv`（表与网络覆盖差 1.6e-6 TWh）、`DFX_BRIDGE_V2.csv`（20 步，闭合残差 1.6e-10 TWh）、`DFX_ELECTRICITY_PER_CAPITA_V2.csv`（固定电力 / ATS：TH 1.44 → 1.83、SG 0.99 → 1.31、MY 1.07 → 1.28）。分国总量变化：TH +251、MY +90、ID +68、SG +46 TWh。
- **一阶预测（INFERENCE；`DFX_FIRST_ORDER.md`，登记于 `RUN_PLAN_DFX.md` 第 4 节）：** DMD D5 方法（第三批 365×24h R1 / R2 与 R3 / R4 对偶价 × Δ负荷）：ΔD +481.0 TWh，ΔC_一体化 +19.450、ΔC_不互联 +22.510、ΔB6 +3.060 bn EUR（+3.488 bn USD），两对偶来源到 3 位小数相同；按类别：交通锚 +2.169、工业乘数 +1.173、氨 −0.153、农业 −0.082、建筑 −0.026、NEU 气 −0.021、HVC 0.000。

## 4. F5.5 本机冒烟（提交 `896828fd`；`results_project/dfx_v3/smoke_v2/SMOKE_SUMMARY.json`）

| 运行 | 网络 | 终止 | 求解 s | 峰值 GiB | 目标 EUR | C1 abc | GATES_V6 | 分级 |
|---|---|---|---|---|---|---|---|---|
| 一体化 56 | `08879f0b…` 截短 56 | optimal | 394（进程 620） | 6.99 | 3.40662e11 | 111（批参照，重评 1 次） | ACCEPTED_LAYER2 | accepted |
| 不互联 56 | `d90ca992…` 截短 56 | optimal | 495（进程 727） | 5.52 | 3.52091e11 | 111 | ACCEPTED_LAYER2 | accepted |

两次启动 14:58:19 / 15:14:12 UTC，间隔 333 s；TimeLimit 3,000 s、墙钟 3,600 s 未触及；违反量 → C1 → M12 → Owen 对偶形式（可用，前提未失败）→ 批参照 → 重评 → GATES_V6（登记 SHA = 2920×3h 网络）→ 分级 → B6（56 时段 11.43 bn，无科学意义）全部 exit 0。许可只经 `GRB_LICENSE_FILE` 传入求解进程。

## 5. F6 测试、运行计划与部署包 v8（提交 `5405e477`）

- **`RUN_PLAN_DFX.md`（事先登记，早于任何 v2 求解）：** V1 / V2 365×24h，档案 `formal_barrier_1e6_t16`，TimeLimit 初版 14,646 / 4,269 s（第三批 R3 / R4 实测 × 3）——**用户 2026-10-27 修订为 V1 21,600 s / V2 10,800 s**（提交 `16b209e2`，仍早于任何 v2 365×24h 求解），墙钟 + 1,200 s，间隔 ≥ 330 s，≥ 33 核才并行，V1 / V2 均为参照运行的分级停批，后处理（账本与 B16、B6 = V2 − V1、Owen 对偶形式、与第三批的对比——**修订后主参照 R3 / R4（同档案 optimal），R1 / R2 并列**——及一阶预测的对比），不做 LOO；规格下限 17 核 / 64 GiB / 45 GB，预计实例占用 3.5–6 h（修订后最坏 11–12 h）。
- **代码：** `scripts_project/dfx_batch.py`（运行表、登记时限、基础网络核对、分级、汇总）；`cloud_package_dfx/run_dfx.sh`（第三批 `run_batch3.sh` 派生）、`preflight_dfx.sh`、`make_package_dfx.sh`；`BATCH3_REFERENCE_VALUES.json`。
- **替身测试：** `tests/research/test_dfx_runner.py` 14 个（串 / 并行通道、批参照 + 重评 + B6 + 对比 + 打包 + 续跑、分级停批三类、墙钟终止、三类安全停止、BUILD_ONLY 与许可陷阱、正式命令的 9 类拒绝、预检守卫与硬下限、分级分类单元、无结果汇总）全部通过。
- **干跑（VERIFIED；`results_project/dfx_v3/dry_run_v8/DRY_RUN_DFX.json`）：** (1) 完整 365×24h BUILD_ONLY、登记路径：V1 LP 9,975,377 行 × 4,477,801 列、非零 23.46e6，构建 324 s，峰值 10.16 GiB；V2 9,629,180 × 4,325,607、22.38e6，159 s，9.96 GiB；BUILD_CHECK 两运行 passed（参数 = 档案 + 登记 TimeLimit、网络 SHA256 = 登记值、G2.2 子集相等、LP 已导出）；无求解器日志；许可变量指向不存在的文件；(2) 截短 56 + 测试开关：passed；(3) 正式命令在 `TRUNCATE` / `SOLVE_CMD` / `FAKE_*` / `GUROBI_TIME_LIMIT_S` / `WALL_CAP_S` / `LICENCE_GAP_S` 残留、`BUILD_ONLY` / `POST_ONLY` / `DRY` 与 `--auth` 同时出现、无许可文件、无 `--auth` 时全部 exit 2，未写任何 STATUS。
- **包 v8：** `work/p1_dfx_20261026/cloud_package_dfx/`，提交与文件表见 `evidence/package/PACKAGE_MANIFEST.json`（20 个文件约 148.2 MB；`SHA256SUMS` 与清单的 SHA256 记录在 `DFX_EVIDENCE.json` `package_v8`）；网络 SHA256 = 登记值、无 2920×3h 文件；构建输入核对：自 `72083fde` 起只有 `dfx_batch.py` 改动（不在 `s2_network.py` 导入闭包内）；首次构建（`5405e477`，`evidence/package_superseded_5405e477/`、`evidence/dry_run_5405e477/`）被修复后的第二次构建取代，旧包目录原样保留；环境锁定 = 第三批（538 个 conda 包 742.8 MB + 2 个 PyPI；关键包 pypsa 0.30.3 / linopy 0.5.5 / gurobipy 12.0.3 / numpy 1.26.4 / pandas 2.3.1 / xarray 2025.1.2 / scipy 1.15.2 / netCDF4 1.7.2 / h5netcdf 1.6.4 / dask 2025.7.0 / pyomo 6.9.3 / highspy 1.11.0 / python 3.11.13）；上传 36 / 100 / 318 KB/s 约 1.14 / 0.41 / 0.13 h。本机预检（包的副本）：guards / sha / networks / env / profile / code / tools → PREFLIGHT OK；resources 节在本机（16 核 / 10 GiB）按预期失败；licence 节未在本机运行（会占用第 3 次 Gurobi 调用）。

## 6. 本机资源（指令原则 7）

| 项 | 用量 | 上限 |
|---|---|---|
| Gurobi 调用 | 2（冒烟；均 56 时段、≤ 12.1 min、间隔 333 s；无重试） | 2 |
| 本机计算 | 约 2.4 h（F0 追踪 ≈ 10 min、数据链 ≈ 5 min、v1 / v2 构建 ≈ 8 min、复核链 ≈ 15 min ×3、测试子集 ≈ 2 min ×4、冒烟 29 min、替身测试 2 min、干跑 10 min、打包 1 min、全量测试见第 9 节；不含等待） | 4 h |
| 磁盘新增 | `results_project/dfx_v3/` 3.64 GB + worktree 0.65 GB + 工作目录 0.15 GB ≈ 4.4 GB | 30 GB |
| 下载 | 0 | — |

## 7. 文件清单（分支 `research/06_scope_redesign/p1_dfx_20261026/`，副本在 `work/p1_dfx_20261026/`）

`SECTION0_LEFTOVERS.md`、`DFX_RULES.md` + `DFX_RULES_NUMBERS.json`、`CODE_MAP.md` + `CODE_MAP_TABLE.csv` + `CODE_MAP_DATA.json`、`RUN_PLAN_DFX.md`、`DFX_PROGRESS.md`、`BATCH3_REFERENCE_VALUES.json`、`review/`（6 个复核表）、`evidence/`（D1 / 差异 / 分解 / 一阶 JSON + 冒烟 / 干跑 / 包 / 泄露扫描证据）、`scripts/review/`、`scripts/wsl_dfx3/`、`cloud_package_dfx/`（包脚本源）、`hpc_package_dfx/`（阶段 2 草稿）、`DFX_REPORT_PHASE1/2/3.md`、`DFX_EVIDENCE.json`、`PRE_AUTODL_CHECKLIST.md`。

## 8. 局限与需要用户注意的事项

1. 不在修复范围（指令）：燃料舱口径与增长；工业"其他桶"温度分布与有用热效率 0.90；100 % BEV 与 ICE / BEV 能效比；显式制冷；水泥 / 钢参数；甲醇与 HVC 的产量化（本机无东盟甲醇 / 乙烯产量数据）；TL 规则。
2. F2：氨原料气 10.8 MWh/t 是 SMR 路线天然气总量（上界），4.92 化学计量值登记为敏感性未跑；USGS 未列产量的国家（BN / KH / LA / MM / PH / SG / TH / TL）氨需求为 0——SG 与 TH 原有 EU27 权重氨负荷消失，MY 新增；VN 的 NEU 天然气被扣到 0 并截断 8.17 TWh。
3. 一阶预测是 +6.7 % 大变动的线性外推，只作对比描述。
4. 冒烟只证明 56 时段可行与链路跑通；365×24h 的时间 / 内存估计依据第三批 R3 / R4（RUN_PLAN 第 5 节）。
5. `test_f0` / `test_f4` 等 F0.3 与 F4.3 测试在 worktree 运行时依赖 `results_project/dfx_v3/` 中的追踪与构建回执（主检出路径）；在无该目录的检出中会跳过（标记 skip）。

## 9. 全量测试（F6.1）

- 第一次全量（`5405e477`，中止）：第三批 / B4P 替身测试 32 个失败——`dfx_batch.py` 首版在导入时改写了共享模块 `m10_batch3_summary` 的常数；修复（本模块内 `run_state`，不再触碰第三批模块）后，七个替身测试文件同进程重跑 76 passed / 1 skipped（`evidence/tests/affected.log`）。
- 第二次全量（`f73f5c06`，`evidence/tests/full_first_f73f5c06.log`）：708 passed / 58 skipped / 3 failed：(1) 本分支 F0.3 测试把 F6 新增的 `dfx_batch.py` 也当作检查对象——已改为只检查 F1–F4 提交的改动并要求后续改动只能是 `CODE_MAP.md` 第 14 节登记的 F6 文件；(2) `test_b4p_batch4.py::test_parallel_when_the_probe_passes` 在全量负载下的时序偶发（单独与同进程重跑均通过，B4P 文件未改）；(3) `test_s1_built_networks.py` 的 S1 静态校验——预存失败：本会话 worktree 初始化把 `results_project/s1` 链接到主检出，使基线里跳过的 S1 测试运行，旧 S1 网络 meta 缺少 M10R 新增的 `cross_border.stock_mode`（基提交 `55ab07c0` 临时 worktree 同样失败；主检出旧配置通过）；去除该链接后与基线环境一致。
- 最终全量（去除 s1 链接、F0.3 测试修正后）：见 `PRE_AUTODL_CHECKLIST.md` P3 与 `DFX_EVIDENCE.json` `tests.full_suite`。

直接进入阶段 2（`DFX_REPORT_PHASE2.md`）。

---

## 附录 A：`DFX_RULES.md` 原文（提交 `834a0f19`；下文由脚本原样附加）

# DFX_RULES —— 需求修复 F1–F4 的规则、数据来源与数值（事先登记）

**登记时间：** 2026-10-26（SGT），在任何 v2 网络构建之前提交。指令 v3 SHA256 `b60da4c6…5a6df`。本文件登记规则与来源；`DFX_RULES_NUMBERS.json`（原型脚本 `scripts/wsl_dfx3/ras_proto.py` 对 v1 表的只读计算）登记按这些规则算出的目标数值，供构建后逐项核对（相对差 ≤ 1e-9）。看到任何求解结果后，本文件不再修改。

## 0. 范围与不变项

- 只改需求：`scripts_project/m08b_demand.py`（F1、F2 产量与 NEU 扣除）、`scripts_project/s3_0_industry.py`（F2 替换）、`scripts_project/s2_layers.py`（F3 作用范围）、`scripts_project/s2b_feedstock.py`（F3 同一范围用于敏感性列）、新增 `scripts_project/dfx_data.py`（F4 注册表片段与更正）、`scripts_project/d1_registry.py`（登记新片段）、`configs/research/baseline.yaml`（F2 产量规则参数与 F3 开关注释，均在 `research.s2.industry` / `research.s2.demand` 需求键下）、测试。网络的其他组件、成本表、求解档案、GATES_V6 / C1 阈值一律不变。
- 数据链重跑顺序：`m08b_demand.py → m08b_heat_bands.py → s3_0_industry.py → s2b_feedstock.py → s2_0_process_emissions.py → m08b_data.py → dfx_data.py → d1_registry.py`（与 M08b 的 `m08b_data.sh` 相同，末尾加 `dfx_data.py`）。
- 国家代码：10 个 AEO8 国家 C10 = BN, KH, ID, LA, MY, MM, PH, SG, TH, VN；TL 在 AEO8 之外（TL 规则）。
- 单位：1 Mtoe = 11.63 TWh；kgoe/人 × 百万人 × 1e3 × 11.63 = MWh。

## 1. F1 —— NEU 移出 TFEC 包络；RAS 部门拆分（薄弱点 1、2）

**依据（核实）：** AEO8 附录 E（PDF 第 202 页）："Total Final Energy Consumption (TFEC): The sum of energy consumption by end-use sectors, excluding non-energy use and international transportation."；表 C.3（PDF 第 184 页，印刷页 182）ATS 2050：Industry 387、Transport 228.2、Residential 52.8、Commercial 50.4、Agriculture and Others 27.8，Total 746.2 Mtoe（本次用 pypdf 从 `aeo8.pdf` SHA256 `48c2a819…11c06` 文本层复核，与注册表来源文件 `AEO8_2050_ASEAN_TOTALS.csv`（SHA256 `0afdacd2…63e6`）一致）。

1. **国家锚不变：** A_c = C.8 ATS 2050 人均 TFEC（kgoe/人）× D.1 2050 人口（百万）× 1e3 × 11.63（MWh），10 国；来源文件 `AEO8_2050_BY_COUNTRY.csv`（SHA256 `875ef946…27d6`）。TL 按现行 `demand_anchor_tl_rule`（人均 = KH / LA / MM 均值，人口 UN WPP 2024 中位 1,889,249.5）。Σ_{C10} A_c = 8,676.778 TWh。
2. **NEU 不再计入部门权重：** 撤销 `m08b_demand.py` 第 185 行 `t19["Industry"] += NEU`；种子、权重、工业锚都只含能源用途（`sector ∈ {Industry, Transport, Residential, Commercial, AgricultureOthers}`）。2050 NEU = 2019 NEU（D1 表 `NonEnergyUse` 行 `base_2019_mwh`）× 该国工业乘数 m_ind（现行算法：NEU 行与工业行共用 `multiplier_total`），作为非能源需求加在能源用途之外。**TL：** 2019 工业能源用途为 0（D1 表 TL 五个工业行均为 0），工业乘数无定义 → NEU 乘数取 KH / LA / MM 工业乘数的简单均值（TL 规则的延伸：TL 的人均与 GDP 增长率同样取三国均值）；TL 工业行保持 0。
3. **RAS 双比例拟合（10 国 × 5 部门）：**
   - 种子 S_{c,s} = Σ D1 表（`DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv`，SHA256 `526a54bd…29c2`）该国该部门所有载体行的 `base_2019_mwh`（UNSD 2019 能源用途；部门映射沿用现行表的 `sector` 列）；不乘增长率（列缩放吸收统一乘子）；零种子保持 0（本次 50 格无零种子）；
   - 行约束 r_c = A_c；列约束 s_s = C.3 ATS 2050 印刷值 × 11.63e6 × k，k = Σ_{C10} A_c / Σ_s (C.3_s × 11.63e6) = 8,676.778 / 8,678.306 = **0.999823954704**（消除 C.8 × D.1 与 C.3 合计的舍入差）；
   - 迭代：先行后列交替缩放（X ← X · r_c / Σ_s X；X ← X · s_s / Σ_c X），直到行、列相对误差都 ≤ 1e-10，最多 1,000 次；不收敛即停下报告（原型：第 11 次迭代收敛，行误差 3.4e-11、列误差 2.2e-16）；
   - 结果 tfa_{c,s} = 2050 能源用途部门锚（MWh）。TL 不进 RAS：tfa_{TL,s} = A_TL × w_s / Σw，w_s = 2019 部门能源用途 × C.3 ATS 部门增长（2050 / 2022，ATS 面板印刷值），NEU 不在权重内。
4. **下游规则不改，只接收新锚：** 电力锚（A_el × 2019 部门电力 × ATS 电力增长的归一权重，居民电力增长 29.0 → 33.2 Mtoe）不变；交通燃料锚 = tfa_Transport − 交通电力锚；工业乘数 m_ind = tfa_Industry / 2019 工业能源用途；居民 / 商业 / 农业燃料锚 = tfa_s − 部门电力锚，负值取 0 并列出（`demand_sector_fuel_anchor_zeroed` 刷新），正值但无 2019 燃料行也取 0；钢 / 水泥产量规则、EV / FCEV / ICE 份额与效率、航运甲醇、炊事、农机、热档等代码不改。
5. **预期核对（写成测试）：** Σ_{c∈C10,s} tfa = Σ A_c（相对差 ≤ 1e-9）；Σ_c tfa_{c,s} = k × C.3_s × 11.63e6（≤ 1e-9）；10 国交通锚 2,653.499 TWh（≈ 2,654）；NEU 不在任何能源用途锚中（种子、工业锚、部门锚均不含 `NonEnergyUse` 行）；A_c 与 v1 锚表逐国相等。
6. **登记的目标值（原型，TWh）：** 10 国部门锚 Industry 4,500.018 / Transport 2,653.499 / Residential 613.956 / Commercial 586.049 / Agriculture and Others 323.257；11 国交通锚 2,660.986（v1 1,700.4）；负燃料锚 8 格合计 −65.149 TWh：BN 居民 −0.678、BN 商业 −1.035、MY 居民 −17.294、MY 商业 −16.221、SG 居民 −3.602、SG 商业 −4.175、TH 居民 −0.061、VN 居民 −22.084，另 TL 商业 +0.186 无 2019 燃料行（v1：9 格 −63.30 TWh；TH 商业与 SG 农业由负转正，TH 居民与 VN 居民由正转负）。工业乘数 m_ind（v1 → v2）：BN 0.541 → 0.839、KH 4.015 → 3.509、ID 2.456 → 2.619、LA 2.669 → 2.536、MY 1.210 → 1.378、MM 0.935 → 1.011、PH 2.228 → 2.078、SG 0.746 → 1.166、TH 1.634 → 2.022、VN 3.084 → 3.108、TL 7.634 → 2.352（NEU 用）。

## 2. F2 —— 氨需求按产量重建；扣除对应的 NEU 天然气原料（薄弱点 5 的氨部分）

1. **氨产量 2050（t NH₃）：** 基年 2019 产量来自本机 USGS Minerals Yearbook 2022 Nitrogen 工作簿 `usgs_myb1-2022-nitro-ert.xlsx`（SHA256 `9b055fcd…cc42`）表 T12 "AMMONIA: WORLD PRODUCTION, BY COUNTRY OR LOCALITY"（千吨含氮量）：Indonesia 6,100、Malaysia 1,200（r）、Vietnam 1,150（2019 列）；其他东盟国家未列出 → 0。含氮量 → NH₃ 按 PyPSA-Eur v2025.07.0 `build_ammonia_production.py`（SHA256 `5aca047c…b25e`）的同一换算 × 17/14，取自仓库已复现的 `registry_v5/sources/jrc_idees_2021/ammonia_production.csv`（SHA256 `c8414b7e…00b0`）2019 列：ID 7,407.143、MY 1,457.143、VN 1,396.429 kt NH₃。
   产量规则 = 与水泥、钢相同的增长项：NH3_2050 = NH3_2019 × max(G_c, 1)^((2050 − 2019) / 28 × 0.5)，G_c = AEO8 表 D.2 实际 GDP 2050 / 2022（`AEO8_TABLE_D2_REAL_GDP_PPP2017.csv`，SHA256 `9189d862…e793`；TL 取 KH / LA / MM 均值），弹性 0.5 = 注册表 `industry_output_elasticity` 现值；**不设人均饱和与规划上限**；登记但不运行的备选：弹性 0.3 / 0.8（写入输出表列 `ammonia_2050_elasticity_low/high_mt`）、"2019 产量保持不变"。写入 `INDUSTRY_OUTPUT_BASE_M08B.csv` / `INDUSTRY_OUTPUT_2050_M08B.csv` 新列（`ammonia_base_year` 2019、`ammonia_base_kt`、`ammonia_2050_mt`、`ammonia_binding` = growth），配置 `research.s2.industry.physical_output_base_year.ammonia: 2019`（构建核对配置 = 表）。
   登记的目标值：G_ID 2.9539、G_MY 2.8427、G_VN 3.7604 → 增长因子 1.8214 / 1.7831 / 2.0818 → NH3_2050 ID 13,491.140、MY 2,598.199、VN 2,907.045 kt，合计 18,996.4 kt（v1 隐含 6,170 kt）。
2. **能量换算：** 5.166 MWh_NH₃/t（比率表 `INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv`（SHA256 `bc7216fc…4384`）`Ammonia` 列 `ammonia` 行 = PyPSA-Eur `MWh_NH3_per_tNH3`，配置第 849 行）；沿用现行系数。目标值：ID 69.695、MY 13.422、VN 15.018 TWh，合计 98.135 TWh（v1 31.849 TWh：ID 9.948、TH 9.359、VN 7.650、SG 3.634、PH 1.001、MM 0.210、BN 0.047，MY 0）。
3. **替换，不叠加：** `s3_0_industry.py` 在 `aeo8_ats_anchor` 模式（有产量规则表的模式，与钢 / 水泥的做法一致）下，化工子行业能耗按 EU27 2019 权重分给 `Ammonia` 行业的那一份（权重 0.307500321533，未来载体份额 ammonia 1.0）不再生成氨需求：该份能量（2019 化工能耗 × 权重 × 乘数 × 效率系数 0.449）记入汇总表列 `pe_ammonia_eu27_share_dropped_mwh`，不计入任何载体；`pe_ammonia_mwh` = 第 1、2 条的产量法数值。甲醇、HVC、氯、其他化工、医药的权重与方法不变（权重不重新归一）。敏感性模式（`aeo8_ats_relative` / gdp / population / level 表）不改。局限：本机没有可用的东盟甲醇 / 乙烯产量数据，甲醇与 HVC 仍按 EU27 权重法。
4. **扣除原料天然气：** 各国 2050 NEU 天然气（D1 表 `NonEnergyUse` × `gas` 行，账户 `NonEnergy:Natural gas (including LNG)`，2050 值 = 2019 × m_ind）−= NH3_2050（t）× **10.8 MWh_CH₄/t NH₃**，扣到 0 为止，截断量逐国报告。
   - **来源与追溯：** JRC-IDEES-2021 Industry EU27 工作簿（`JRC-IDEES-2021_Industry_EU27.xlsx`，SHA256 `1fd3bc14…3dc3`）经逐表检索不含任何 "ammonia / NH3 / nitrogen" 行，只有化工原料合计行 "Chemicals: Feedstock (energy used as raw material)"，无法给出每吨氨的原料量（第一优先来源不可用）；第二优先来源：PyPSA-Eur v2025.07.0 `config.default.yaml`（SHA256 `bfbe9160…da787`）第 850 行 `MWh_CH4_per_tNH3_SMR: 10.8`，即工业比率脚本 `build_industry_sector_ratios.py`（SHA256 `70c45a81…0c61`）第 431–437 行用于从基础化工能耗（含 IDEES 原料天然气）中扣除当年氨产量的同一常数，也是仓库 `s3_0_industry.py` `PE["MWh_CH4_per_tNH3_SMR"]` 现行使用的常数。
   - **登记的局限（醒目）：** 10.8 MWh/t 是 SMR 路线的天然气总投入（重整原料 + 重整炉燃料），统计口径上只有原料部分进入 UNSD 非能源用途，因此它是原料量的**上限**；按化学计量（technology-data Haber-Bosch `hydrogen-input` 1.1484 MWh_H₂/MWh_NH₃ × 5.166，CH₄ + 2H₂O → CO₂ + 4H₂ 的 LHV 比 1.2055）的下限约 4.92 MWh/t，登记为敏感性区间 4.92–10.8，本次不运行。F2.2 已把 EU27 权重法分给氨的化工**能耗**份额去掉，10.8 中的燃料部分可能被再次扣除（过度修正），其量 = 产量 × (10.8 − 原料实际值)。
   - 登记的目标值（TWh，v2 乘数下）：ID NEU 天然气 188.071 − 145.704 = 42.367；MY 173.444 − 28.061 = 145.383；VN 23.228 − 31.396 → 0，截断 8.168；其他国家无氨产量，不扣。
5. **核对（测试）：** 氨需求逐国 = `ammonia_production.csv` 2019 × 规则 × 5.166（≤ 1e-9）；MY > 0；USGS 未列产量的国家（BN、KH、LA、MM、PH、SG、TH、TL）= 0；NEU 天然气行 = max(0, 2019 × m_ind − NH3 × 10.8)；截断量与登记值一致。

## 3. F3 —— HVC 系数只作用于 HVC 原料（薄弱点 8）

- `share_HVC_primary_fraction_2050` = 0.4（注册表现值，不改）只乘 NEU 油行中的 HVC 原料账户：**`NonEnergy:Naphtha`、`NonEnergy:Ethane`、`NonEnergy:Liquefied petroleum gas (LPG)`、`NonEnergy:Natural gas liquids`**（2019 合计 326.718 TWh）；非 HVC 产品账户系数 1.0：**`NonEnergy:Bitumen`、`NonEnergy:Lubricants`、`NonEnergy:Paraffin waxes`、`NonEnergy:Petroleum coke`、`NonEnergy:Gas Oil/ Diesel Oil`、`NonEnergy:Motor Gasoline`、`NonEnergy:Fuel oil`**（2019 合计 55.878 TWh）。D1 表中 NEU 油账户共 11 个，以上两组穷尽。NEU 煤、气行系数 1.0（不变）。
- 实现：`s2_layers.add_demand_layer` 的 NEU 负荷 = Σ_HVC 行 × 0.4 + Σ_非 HVC 行 × 1.0（每节点一个负荷，名称不变）；`s2b_feedstock.py` 的 `full_release_2050_t` 敏感性列用同一范围（主模式 territorial 不受影响，只改 meta 中记录的敏感性数值）。
- 开关 `research.s2.industry.hvc_recycling_applies_to_naphtha` 新定义：true = 系数作用于上列 HVC 原料账户（主值）；false = 不作用于任何 NEU 行。登记为注册表行 `hvc_primary_fraction_scope`。

## 4. F4 —— 注册表刷新与补登（薄弱点 7）

1. 刷新（按 v2 构建实际使用的数值，`dfx_corrections.csv` 全行替换，`REGISTRY_CHANGELOG_DFX.csv` 记行键、旧值、新值、原因）：`industry_ammonia_2050_{C}`、`industry_methanol_2050_{C}`、`industry_hydrogen_2050_{C}`、`industry_low_temperature_heat_2050_{C}`、`industry_coal_retained_2050_{C}`、`industry_steel_2050_{C}` 描述、`shipping_demand_domestic_2050`、`demand_tfec_2050_{C}`（= A_c，能源用途口径）、`demand_sector_fuel_anchor_zeroed`、`demand_anchor_family_main` / `demand_base_load_rule` / `demand_transport_anchor_rule` / `demand_sector_fuel_anchor_rule` 的描述（归一权重 → RAS）、`feedstock_full_release_2050_{C}`（F3 范围）、`feedstock_process_2B_2D_2050_{C}` 等由数据链脚本自动重写的行按脚本输出。
2. 补登（`dfx.csv` 新行）：炊具效率 `cookstove_efficiency_basic_ID` 0.08、`_TH` 0.16、`_default` 0.08、`cookstove_efficiency_modern` 0.53（来源 IEA Defining energy access: 2020 methodology, Table 2；配置 `cookstove_efficiency_source`）；清洁炊事开关 `clean_cooking_switch`（决定 23）；有用热效率 `industry_useful_heat_efficiency` 0.90（`s3_0_industry.HEAT_EFF`；technology-data solid biomass boiler steam 0.90）；`hvc_primary_fraction_scope`；`demand_node_allocation`（`assembly_v1_allocation_shares_then_astar`）；AEO8 C.3 ATS 2050 各部门数值行 `aeo8_c3_ats_2050_{sector}`（5 行 + 合计）与 2022 值；`demand_sector_split_ras`（规则、k、收敛、迭代次数）；`industry_ammonia_output_rule`、`industry_ammonia_production_2019_{C}`（USGS）、`industry_ammonia_feedstock_gas_per_t` 10.8（含上限说明与 4.92 下限）、`industry_ammonia_feedstock_gas_deducted_{C}`（扣除量与截断量）、`industry_ammonia_eu27_share_dropped_{C}`。
3. 映射表 `research_inputs/registry_v5/REGISTRY_NETWORK_INPUT_MAP.csv`：每个映射到网络输入的数值行 → 表 / 网络中的取法；测试逐行核对（相对容差 1e-9；网络级核对在 v2 网络文件存在时运行）。
4. 注册表原地更新（`DATA_REGISTRY.csv` 路径不变；旧版 SHA256 `4c59adb7…8720`，2,194 行，由 git 历史保留）。

## 5. F5 —— 构建、等价测试、复核、一阶预测、冒烟（事先登记的做法）

- 构建：`PYTHONHASHSEED=0`，`scripts_project/s2_network.py --scenario {integrated,disconnected} --output …`（与 `m08b_build.sh` 相同；每次写 2920×3h 与 365×24h），干净提交；v1 基线 = 同一 worktree 路径上在基提交 `55ab07c0`（需求代码 = `ec80668f`）重建的四个网络（`results_project/dfx_v3/builds_v1`，F0 已做），以排除 `s2_network.py:344` 的路径元数据差异；另核对 builds_v1 与 `ec80668f` 登记网络除该路径字段外逐字段相同。
- 结构等价测试（允许的差异，逐项列出，其余任何差异 = 失败）：`loads` / `loads_t.p_set`；因负荷变化而必然变化的派生项——`n.meta` 中的需求账本（`s2_demand_ledger`、`demand_owners`、`demand_identity`、`research_bunkers` 不变）、`research_config_sha256`（配置新增键）、`registry_sha256`（若记录）、过程排放发电机（`process emissions source`，p_nom = EDGAR × 工业乘数，乘数随 F1 变）、`dust_cleanup` 清理清单（负荷归零或新增引起的母线 / 链路存废）、新增负荷所需的母线 / 链路（如 MY 氨负荷落在区域氨母线上无需新链路）；其它组件（generators 除过程排放、links、lines、stores、storage_units、buses、carriers、global_constraints 及其时序）逐字段相等。
- 需求复核：`work/p1_dmd_20261026/scripts/` 的 `dmd_d1_demand.py`、`dmd_d3_benchmark.py` 复制到 `work/p1_dfx_20261026/scripts/` 改输入路径（原文件不改）；输出需求总表与 v1 逐项差、AEO8 ATS → v2 负荷分解（闭合残差 ≤ 1e-3 TWh）、分国人均用电与固定电力 / ATS 比值。
- 一阶预测：DMD `dmd_d5_duals.py` 方法——R1 / R2（第三批 365×24h，`export/R1`、`R2`）各负荷母线的年度负荷加权对偶价格，ΔD = v2 − v1 逐（国家, 账户, 载体）年量，ΔC = λ·ΔD，ΔB6 = ΔC_不互联 − ΔC_一体化，分国受益变化 = (λ_dis − λ_int)·ΔD_i；写入 `RUN_PLAN_DFX.md` 并在任何 v2 求解前提交；注明大变动外推。
- 本机冒烟（本指令 2 次 Gurobi 调用）：v2 2920×3h 一体化与不互联各截短到前 56 个时段，`s2_solve.py --truncate 56 --label SMOKE_TEST_ONLY --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 3000`，墙钟止损 3,600 s（≤ 60 分钟），串行，两次间隔 ≥ 330 s；之后违反量分析、C1、本批参照 + 重评、M12 分摊、Owen 对偶形式审计、GATES_V6；非 optimal 或不可行即停下报告，不调参、不重试。

## 6. F6 —— 365×24h 筛查运行计划骨架（细节与网络 SHA256 写入 `RUN_PLAN_DFX.md`）

- V1 = 365×24h v2 一体化、V2 = 365×24h v2 不互联；档案 `formal_barrier_1e6_t16`；TimeLimit = 第三批 R3 / R4 求解进程墙钟（4,882 / 1,423 s）× 3 = 14,646 / 4,269 s；墙钟止损 = TimeLimit + 1,200 s；两次启动间隔 ≥ 330 s；两会话并行只在核数 ≥ 33（2 × Threads 16 + 后处理 1）时，否则串行；验收 GATES_V6、C1（本批参照 = V1 / V2）；后处理同第三批 3.5 / 3.6（账本与 B16、B6 = V2 − V1、Owen 对偶形式 α 0.5 主值 / α 区间 / 市场形式 / 燃料舱）、与 R1 / R2 对比、实际 ΔB6 与一阶预测对比（只描述）；LOO 不做。
- 部署包 v8：两个 365×24h v2 网络 + 回执 + 成本表、代码归档、`RUN_PLAN_DFX.md`、运行 / 预检脚本、第三批同一环境锁定（pypsa 0.30.3、linopy 0.5.5、gurobipy 12.0.3、numpy 1.26.4、pandas 2.3.1、xarray 2025.1.2、scipy 1.15.2、netCDF4 1.7.2）、清单与 `SHA256SUMS`。

## 7. 不在本次范围（只在报告"局限"中列出）

燃料舱口径与增长；工业"其他桶"的温度分布与有用热效率；100 % BEV 与 ICE / BEV 能效比；显式制冷；水泥 / 钢参数；甲醇与 HVC 的产量化；TL 规则；氨原料量的实际原料 / 燃料拆分（本机无来源）。
