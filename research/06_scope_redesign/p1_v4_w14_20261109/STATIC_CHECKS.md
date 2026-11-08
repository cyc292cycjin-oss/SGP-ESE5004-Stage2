# W14 第 2 节：网络构建、静态检查与 D2c 冒烟网络比对

- **标记：** VERIFIED（数组或回执）、EXACT（逐项核验）、INFERENCE、PROPOSED。数值见 `STATIC_CHECKS.json`、`evidence/W14_NETWORK_DIFF.json`、`evidence/W14_TRUNC56.json`、`evidence/ZERO_SLACK_CHECK_W14.json`；脚本 `scripts/build_w14.sh`、`scripts/w14_static.py`、`scripts/w14_checks.sh`；日志 `logs/build_main.txt`、`logs/static.txt`、`logs/zero_slack.txt`。
- **不调用求解器，不在本机构建 2920×3h 的 LP**（零松弛门只在 3 个时段上建钩子行）。

## 1. 构建（第 2.1 条；VERIFIED）

| 项 | 值 |
|---|---|
| 构建提交 | `59b128ea047de600adbd2a54e6e84b48a1544fe5`（W14-1；`research/` 之外与 D2c 头 `4e83d71e` 逐文件相同；dirty 0） |
| 规则 | `s2_network.py --scenario integrated --override demand.v4.enabled=true`；`m08a_variants.py --set cross_border.stock_mode=no_new_xb`（2920×3h、365×24h）；`PYTHONHASHSEED=0`；与 W08–D2c 相同 |
| 用时 / 峰值 | 一体化 1 分 31 秒 / 1.06 GB；变体两种分辨率各数秒（2026-11-08 19:49:59–19:51:40 UTC） |
| **F1 一体化 2920×3h** | `86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d`，82,749,911 字节 |
| **F2 `no_new_xb` 2920×3h** | `24e835f74365f63f6dc2c848f81bb43727e082be6c34f2c3aca0594641b25187`，82,112,443 字节 |
| 365×24h（只用于 C1 对照，不入包） | 一体化 `10759e04…`，`no_new_xb` `08ce15f9…` |
| 网络元数据（开关集 / 表目录） | `v4_w08.switch_sha256` = `d89ccbf47b0002e65246ce75ba06158f76c340f5091127f6658eec06ed727a62`，`tables_dir` = `research_inputs/industry_v4/out_ras`（主集） |
| 输出 | 主检出 `results_project/v4w14/builds/main/`（不入库） |

## 2. 全部静态检查（第 2.2 条；W08、D1、D2a、D2b、D2c 各步；2920×3h 两网均通过）

| 检查（来源） | 判据 | F1 一体化 | F2 `no_new_xb` |
|---|---|---|---|
| C1 工业负荷对表（W08） | 逐国 ≤ 1e-6 MWh；曲线年均 = 常数 ≤ 1e-9；365 对 2920 ≤ 1e-6 | 1.07e-6 MWh / 4.4e-16（457 条曲线）/ 0 | 同左 |
| C2 EV = 陆运燃料 × 未取整系数；铁路对表；无父行（W08、D1） | ≤ 1e-6 | 2.2e-16 / 1.9e-9 MWh / 0 | 同左 |
| C3 固体生物质池（W08 F7、D2a–D2c） | 固定需求 / 池 ≤ 0.99；VN 余量 ≥ 1 %；**无新的零余量池**（≥ 0.999，D2c 也无） | 最高 0.99（VN）/ VN 余量 1.0 % / 无（D2c 无） | 同左 |
| C4 国产气年度上限对表（W08、D2a） | 0；机组数 = D2c | 0 / 19（D2c 19）；合计 2,148.53 TWh | 同左 |
| C5 曲线（W08） | 记录 | 工业电力 3 小时峰均比 1.075（BN）–1.242（TH）；ID 三个时区 UTC+7 / +8 / +9 | 同左 |
| C6 v4 身份（W08、D1） | 元数据开关集 SHA = 表目录 `V4_SWITCHES.json`；主集 | 是（`d89ccbf4…`，`out_ras`，主集：`biomass_potential v4_adjusted_t06`、`source_band_basis post_product`、`lng_regas_adder asean_tariffs`、`missing_cost_rule proxy`、`meoh_per_tco2 stoichiometric`、`hvc_basis b` 等 20 项） | 是 |
| **C6b 开关集与网络元数据一致性（D1，第 214 项第⑧条；包的预检同一检查）** | `v4_common.check_network_meta`（配置 = 表目录 = 网络元数据）通过；网络 `research_config_sha256` = 由配置文件与网络记录的覆盖重组后的哈希（B12 恒等） | 通过；覆盖 `demand.v4.enabled=true`；配置哈希 `6db27beb…` = 重组值 | 通过；覆盖另加 `cross_border.stock_mode=no_new_xb`；`78cb4d7c…` = 重组值 |
| C7 对 v3.1 的结构（W08、D1；只列出） | 记录 | 母线 3,115 → 3,056（删 129：甲醇终端 77、农业 / 工业煤终端 39 等；增 70：油、生物质、炊事、煤、气终端核算母线）；链路 8,774 → 8,784（删 130 / 增 140）；发电机删 5 台外部煤（ID 小节点）；Store 删 5 个纤维池；StorageUnit 增 1（TH2 4 水库，D2a）；负荷 2,188 → 2,153 | 同左（链路 8,491 → 8,501，线路 102） |
| C9 树干代理成本（D1） | 5 个树干 Store 的边际成本 = 注册表 `biomass_missing_cost_proxy`；台账记规则 | 6.26706128163 EUR/MWh，5 / 5；规则 `proxy` | 同左 |
| C10 网络溢出台账 = 表（Fable F-05，D2a） | ≤ 1e-3 MWh | 1.9e-4 / 上限 4.3e-4 | 同左 |
| C11 带份额台账 = 表（D2b） | 0 | 0 | 0 |
| C12 LNG 边际成本 = D2c（D2b、D2c） | 0 | 0（16 台） | 0（16 台） |
| **零松弛门（V3.1，无求解器）** | 无强制零余量行；燃料舱为显式逐变量为零 | **通过**：705 行（其他形式 667、上限为正 26、有移除端口 11、显式逐变量为零 1），无强制行 | **通过**：589 行（551 / 26 / 11 / 1） |

## 3. 与 D2c 冒烟网络比对（第 2.3 条；VERIFIED）

**C8（W14 对 D2c，逐组件表、逐列、逐时间序列）：** 两网两分辨率（2920×3h、365×24h）**数据逐值相同**（无静态列、时间序列、组件集合差异；时段与权重相同）。SHA256 不同的原因只在元数据：

| 网络 | 不同的元数据叶 | D2c | W14 |
|---|---|---|---|
| F1、F2（两种分辨率） | `s2_layers/geothermal/bus_mapping_source/path`（构建 worktree 路径，内容相同；已知问题，记忆 `network-meta-path-dependence`） | `/home/jin/wt_v4_d2c/results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json` | `/home/jin/wt_v4_w14/...`（同长度，所以字节数相同） |
| F2（两种分辨率） | `research_variant/base/sha256`（基网 SHA，随上一行变） | `db33f84e…` / `2b31d60c…` | `86f6d6a0…` / `10759e04…` |

**56 时段网络（同一规则截取：`s2_solve.py --truncate 56` 的 `set_snapshots(前 56 个)` + `set_representative_weights`，权重 8760 / 56，年度量不缩放）：**

| 运行 | W14 截取 SHA256 | D2c 截取 SHA256 | 数据 | 元数据差异 | 时段 | 权重和 | 池未缩放 |
|---|---|---|---|---|---|---|---|
| F1 | `0dc78bae…` | `5f5c520c…` | **逐组件相同** | 同上（路径） | 56（2013-01-01 00:00 – 01-07 21:00） | 8,760.0 | 是 |
| F2 | `36a01824…` | `63b19c95…` | **逐组件相同** | 同上（路径、基网 SHA） | 56 | 8,760.0 | 是 |

截取后的 56 时段网络上，与时段无关的检查（C3、C4、C6、C6b、C9、C10、C11、C12）全部通过，零松弛门通过（705 / 589 行，无强制行）。

**结论（第 2.3 条）：** 56 时段网络与 D2c 冒烟网络逐组件相同（元数据只差构建路径），**HPC 冒烟期望值取 D2c 冒烟的目标值**：F1 363,190,038,821.0828、F2 376,143,650,003.4369 EUR（含常数项；迭代 89 / 80；`SMOKE56_D2C.md` 第 2 节）。第 3 节演练仍按授权求解 2 次，以在包的解压副本中原样验证冒烟作业体（`DRILL_REPORT.md`）。

## 4. 在包的代码提交上重建核对（第 2.1 条；VERIFIED；包提交之后补入）

**为什么需要这一节：** 指令要求"在包的代码提交上构建"。网络 SHA256 与构建提交必须登记在定义文件里（`registered_sha`、`build_commit`；`base-check` 核对构建回执的 `code_sha`），而定义文件本身属于包的代码提交，所以登记所用的构建只能在更早的提交上做（v3 先例：构建 `a1ef782b`、包 `d3b9a3bc`）。包里放的是构建提交 `59b128ea` 的网络与回执；下面证明它们与"在包的代码提交上构建"的结果逐字节相同。

| 重建所在提交 | 规则 / 路径 | F1 2920×3h | F2 2920×3h | F1 365×24h | F2 365×24h | 回执差异 |
|---|---|---|---|---|---|---|
| `12083cf5`（第二次打包的提交） | `scripts/build_w14.sh rebuild_pkg`，同一 worktree 路径 | **逐字节相同** `86f6d6a0…` | **逐字节相同** `24e835f7…` | 相同 `10759e04…` | 相同 `08ce15f9…` | 只有 `build_seconds`、`code_sha`（`59b128ea` → `12083cf5`）与输出路径 |
| **`26c2e47d`（包的 `COMMIT`）** | `scripts/build_w14.sh rebuild_pkg_26c2e47d` | **逐字节相同** | **逐字节相同** | 相同 | 相同 | 同上 |

- 三个提交在 `research/` 之外逐文件相同（`git diff --name-only 59b128ea 26c2e47d -- . ':!research/'` 为空，打包脚本出包前也核对）；包内 `networks/integrated_2920_3h_unsolved.nc` 与 `builds/main` 的文件逐字节相同（`logs/final_drill.txt`）。
- 日志：`logs/rebuild_and_dry_12083cf5.txt`、`logs/build_rebuild_pkg.txt`、`logs/final_drill.txt`、`logs/build_rebuild_pkg_26c2e47d.txt`。
