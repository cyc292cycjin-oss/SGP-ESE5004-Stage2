# S4F 报告：单条输电扩建上限（第 96 项）、S4E 其余事项（第 97 项），冒烟、重建部署包与上云前清单

**分支** `codex/s4f-extension-caps-20261017`，自 S4E 最终提交 bcda8001 开出；**draft PR** [cyc292cycjin-oss/SGP-ESE5004-Stage2#30](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/30)，叠在 #29 上；指令 `S4F_CLAUDE_CODE_INSTRUCTION.md`，SHA256 28d7458d…7216f03，已核对。证据等级：VERIFIED（实际数组或回执）、EXACT（逐项核验）、INFERENCE（机理解释）、PROPOSED（未执行）。

## 摘要

1. **第 96 项：** 按 PyPSA-Eur v2025.07.0 的实际做法，`lines.max_extension` = 20,000 MW 以新增量口径同时作用于每条交流线和每条 DC 链路；`links.max_extension` 不使用（用户同意）；管道不设上限。开关 `research.network.max_extension`：`none` 构建与 S4E 网络逐组件一致；`apg_plans`（18 组 APG 上限）只构建核对。
2. **第 97 项：**
   - TH–MY（停止 01 → 用户方案 1）：线路 91 = 80 MW（C 级），Khlong Ngae–Gurun 300 MW，删除 4 条 OSM 重复直流，合计 380 MW = APG；
   - #4 印尼端改为北干巴鲁（432 km，直流）；老挝经铁路进入越南国内封存（6 条链路）；SG–VN / SG–KH 为第二批敏感性；
   - `tests/transport` 已修复，整个 `tests/` 516 项通过。
3. **作者 readjust 清单（只记录）：** 19 条跨境交流线的容量被压到 AIMS 总量但阻抗未变，`s_nom` 与线型额定之比 0.0001–1.15，其中 16 条在交流环路中。
4. **冒烟（56×3h）：** 三项都最优，目标值较 S4E 高 1.4–2.4 %。新走廊合计 263 GW（S4E 301），单条最大 20 GW；触及上限的组件：一体化 11 个、不互联 6 个。B5、B6（541.3 亿 EUR，7.8 %）、B16 与全部求解器容差门槛通过。
5. **不互联 − 一体化分国差额（bn EUR）：** VN 22.0、ID 9.6、TH 6.2、MY 5.1、LA 4.0、KH 2.3、SG 2.0、PH 1.05（由负转正）、MM 1.0、BN 0.8、TL 0.27。
6. **部署包：** 重建到 S4F 最终代码提交 7e09744d，上传 232,095,769 B。365×24h 单运行 34–67 min（悲观 98 min），串行 2.0–2.8 h；预检下限 36 / 72 / 104 GiB 不变。
7. **需要用户决定 4 项（§7），上云前清单见 §10。** 最关键的是作者 readjust 线的处理。

## 1. 执行概况

| 节 | 内容 | 提交 | 测试 |
|---|---|---|---|
| S4F-0 | 登记对 S4E §7 七项的答复；核查 PyPSA-Eur 两个键 | fd866f08 | `tests/research` 488 通过 |
| S4F-1 | 单条输电扩建上限（第 96 项） | e80509bf | 493 通过 |
| 停止 01 | 线路 91 不是 Sadao–Chuping（限时核查约 3.5 分钟，只读）→ 用户选方案 1 | — | — |
| S4F-2 | TH–MY 存量、#4 端点、老挝进越南封存、SG–VN / SG–KH、`tests/transport`（第 97 项） | d9bc8012 | 499 通过；整个 `tests/` 516 通过 |
| S4F-3 | 冒烟（三项，档案 A） | 7e09744d | — |
| S4F-4 | 部署网络重建、打包、资源估算 §15、部署步骤 | 34835d55 | 499 / 516 通过 |
| S4F-5 | 上云前清单、报告与交付 | 本交付提交（哈希见 PR #30） | — |

- 停止条件中，PyPSA-Eur 两个键都找到了，`tests/transport` 的失败也不涉及逻辑错误；只有 TH–MY 一项触发停止（停止 01），已按用户答复处理。
- 本步没有下载，没有连接云端，也没有做正式求解。本机计算单次 ≤ 5 分钟，峰值内存 ≤ 4.1 GiB。

## 2. 第 96 项：单条输电扩建上限（S4F-1，提交 e80509bf）

### 2.1 PyPSA-Eur 的实际做法（本地已入库副本，VERIFIED）

PyPSA-Eur v2025.07.0 的配置与代码副本都在 `research_inputs/registry_v5/sources/`：配置 SHA256 bfbe9160…，`prepare_sector_network.py` SHA256 612c4a0c…。`s4f_1_data.py` 会逐行断言下表中的行号与内容。

| 位置 | 内容 |
|---|---|
| `config.default.yaml` 第 324 行 | `lines:` 段 `max_extension: 20000 #MW` |
| `config.default.yaml` 第 340 行 | `links:` 段 `max_extension: 30000 #MW` |
| `prepare_sector_network.py` 第 6415–6417 行 | `maxext = snakemake.params["lines"]["max_extension"]`；不为 None 时调用 `limit_individual_line_extension(n, maxext)` |
| 同上，第 5573–5577 行 | `n.lines["s_nom_max"] = n.lines["s_nom"] + maxext`；`hvdc = n.links.index[n.links.carrier == "DC"]`；`n.links.loc[hvdc, "p_nom_max"] = n.links.loc[hvdc, "p_nom"] + maxext` |

- **口径：**
  - 上限是**新增量**（存量 + 20,000 MW），不是总量。
  - 作用于**全部交流线**和**全部 `DC` 链路**，不含 B2B 与管道。
  - 部门耦合流程里，直流链路用的也是 `lines.max_extension`；`prepare_sector_network.py` 不读 `links.max_extension`。
- **与审阅端理解的差异：** 审阅端理解为交流、直流各有一个值。按 PyPSA-Eur 的实际做法执行：一个值（20,000 MW）同时作用于交流和直流，`links.max_extension` 不使用（用户 2026-10-17 同意）。
- **管道：** PyPSA-Eur 对新建氢管道、CO₂ 管道（`add_co2_network`）、新建气管道（`gas pipeline new`）都不设单条上限，所以本模型也不设（注册表 `s4f1_pipeline_extension_caps`）。

### 2.2 实现（`scripts_project/s4f_layers.py`）

- **开关 `research.network.max_extension`：**
  - `pypsa_eur`（主算）：在跨境开关之后施加，两个情景同一规则，跨境与国内、存量与新候选都适用；
  - `none`（原状，对照）；
  - `apg_plans`（保守敏感性，只构建核对）。
- **20,000 MW 的来源：** 读注册表 `pypsa_eur_lines_max_extension`（B 级）。
- **`apg_plans`：** 在 `pypsa_eur` 上限之外，每个 APG 项目组再加一条约束：组内线路 `s_nom` 与直流链路 `p_nom` 之和 ≤ max(组内 2025 存量, 规划上限)。约束由新钩子 `research_apg_corridor_cap` 实现，写法与核电国别上限钩子相同。
  - **取值规则：** 规划上限取 `total_MW`（范围取上端，"600/TBC" 取 600）与 `aims3_2040_projection_MW` 中较大者。#16 并入 #5 巴淡–新加坡的 3,400 MW。
  - **组的划分：** 连接项目两端区域（节点名前缀）的全部线路与直流链路。
  - **覆盖范围：** 18 组（`APG_PLAN_CAPS_S4F1.csv`）。#8a（TBC）以及 SG–VN、SG–KH 没有数字，沿用 PyPSA-Eur 上限。

### 2.3 构建核对（VERIFIED，`evidence/s4f_1/STATUS.txt`）

- `none` 构建与 S4E 一体化网络逐组件完全一致（`{}`）。
- 主算构建与 S4E 网络只有 `Line.s_nom_max`、`Link.p_nom_max` 两列不同：
  - 138 条线都是 `s_nom + 20000`，16 条 DC 链路都是 `p_nom + 20000`；
  - 管道与 B2B 仍无上限。
- `apg_plans` 构建带有钩子 `research_apg_corridor_cap` 和 18 组上限。

### 2.4 受上限约束的组件（S4E-3 冒烟中超过上限的组件，`MAX_EXTENSION_EXCESS_S4E3.csv`）

| 运行 | 超限组件 | 其中跨境 / 国内 | 超出合计 | 单条最大新增 |
|---|---|---|---|---|
| 一体化 STEPS | 22 | 8 / 14 | 405.6 GW | 87.8 GW（线路 91 TH–MY） |
| 不互联 STEPS | 16 | 0 / 16 | 555.3 GW | 106.0 GW（ID 爪哇国内线 1） |
| 一体化 NZE | 20 | 8 / 12 | 367.8 GW | 87.0 GW |

上限约束的不只是新走廊，也包括大量国内存量线：TH、VN、ID（爪哇、加里曼丹）的国内线。这些是 56 时段冒烟中的扩建量，规模本身不能据此判断。

## 3. 第 97 项：S4E 其余事项（S4F-2，提交 d9bc8012）

### 3.1 (a) TH–MY 存量（停止 01 → 用户决定方案 1）

- **限时核查（只读，约 3.5 分钟，`S4F_STOP_01_LINE91.md`）：** 线路 91 是聚类伪影下的 TH–MY 交流代表线，不是 Sadao–Chuping。
  - pypsa-asean 的 `busmap` 把 Chuping 一端的母线 844 分进了泰国聚类，Sadao–Chuping（简化线 1408）因此成了泰国聚类内部的线，在聚合时被丢掉。
  - 线路 91 的成员是马来西亚国内线 1599 和一条泰国 115 kV 边境线（OSM 234442756，止于 Sungai Kolok）。两者的 `num_parallel` 之和 6.448026 + 0.113487 = 6.561513，与冻结底网完全一致。
- **380 MW 的来源（已查明，VERIFIED）：** 作者 `final_asean_adjustment.py` 的 `readjust_existing_interconnections`（第 296–347 行，第 309 行为 `("MY", "TH", 380)`），把 AIMS 2024 的国家对存量总量按长度分摊到存量跨境**交流线**上。它不改直流链路，所以含 300 MW 直流的 APG 总量 380 MW 全部记在了交流线 91 上，而直流仍保留 4 × 491.4 + 300 MW，造成重复计算。按线型公式，线路 91 应为 √3 × 380 × 2.58 × 6.5615 = 11,142 MW。
- **处理（`TH_MY_STOCK_S4F2.csv`，构建时施加，开关 `research.network.th_my_stock`）：**

| 组件 | 冻结底网（MW） | S4F（MW） | 依据 | 等级 |
|---|---|---|---|---|
| OSM 250878579-1_0 … -4_0（直流） | 4 × 491.4 | 删除 | 同一 OSM way 拆成 -1..-4，几何相同（100.45E 6.71N – 100.54E 5.81N，约 111 km），300 kV、单回、`dc=True`；与 Khlong Ngae – Gurun 是同一条线 | B |
| Khlong Ngae – Gurun（直流） | 300 | 300 | AIMS `new_links.csv`：existing，2002，110 km，300 MW | B |
| 线路 91（交流） | 380 | **80**（`s_nom`、`s_nom_min`） | 聚类伪影：成员线不是 Sadao–Chuping；按 AIMS 线型 94-AL1/15-ST1A（0.35 kA）× 132 kV × √3 = 80.02 MW 推算，等于 APG 380 − 300；`num_parallel` 与阻抗不变 | C |
| **TH–MY 合计** | **2,645.6** | **380 = APG** | | |

- **开关与固定点：**
  - `apg_aims`（主算）| `frozen_base`（原值，对照）。
  - 冻结底网文件与其 SHA 固定点（`ELECTRIC_BASE_SHA`）不变；修正在构建时施加，施加前逐项核对冻结底网的原值，不符就报错。
  - 走廊表在内存中同步修正：删去 4 行，线路 91 的存量下限改为 80，使跨境集合检查与存量下限检查保持一致。
  - 新的固定点：注册表 `th_my_line91_s_nom_2025`（80 MW，C 级，敏感性 80–380）、`th_my_hvdc_khlong_ngae_gurun_2025`（300 MW，B 级）、`s4f2_th_my_stock`（修正表 SHA）。每次构建回执记录修正表的路径和 SHA。
  - `tests/research/test_s4e_1.py` 中主走廊表路径的断言改为 `CORRIDORS_S4F2.csv`。

### 3.2 (b) APG #4 印尼端点

- **端点：** 印尼端改为 ID_Sumatra3 3（北干巴鲁），#16 新加坡–苏门答腊保持巴淡端（ID_Sumatra2 0）。
- **参数：** 方法与 S4E-1 相同。

| | S4E-1 | S4F-2 |
|---|---|---|
| 组件 | `APG4 ID_Sumatra2 0 - MY_Peninsular2 1 DC` | `APG4 ID_Sumatra3 3 - MY_Peninsular2 1 DC` |
| 大圆距离 | 228.2 km | 345.8 km |
| 长度（× 1.25） | 285.3 km | 432.2 km |
| 海底份额 | 0.118 | 0.236 |
| 类型 | 直流 | 直流（不同陆块） |

- **配套表：** 主走廊表改为 `CORRIDORS_S4F2.csv`（`research.corridors.corridors_table_s4f2`），行数不变。`SUBSEA_SHARE_S4F2.csv` 保留 S4E-1 原有各行，只补新节点对；用海底份额为 0 的构建做第二遍补算（主算、含可选候选各一次），没有新增节点对。
- **长度分摊：** 新表 `XB_LENGTH_SHARES_S4F2.csv`（235 个跨境组件，含可选候选），账本默认读这张表。

### 3.3 (c) 老挝经过境进入越南国内封存

- **开关：** `research.co2.lao_transit_vn_store: on`（主算）| `off`。
- **链路：** 每个老挝节点经铁路到越南沿海节点（VN2 2 / VN2 3）后，有一条链路 `<node> co2 transit to VN store` 通往 `co2 sequestered VN`：
  - 载体 `CO2 transit rail`；
  - 链路边际成本 = 陆运段（注册表 `co2_lao_transit_land_cost_<node>`，9.66–24.57 EUR/t）；
  - 越南封存单价 30 EUR/t 和越南年注入上限都在 store 上，所以这部分 CO₂ 占用越南的上限；
  - 共 6 条，两个情景都有。
- **贸易类别：** 标为贸易，即第 92 项的贸易类 `border_class = maritime_trade`。它不属于跨境网络：不计入 B5，跨境开关不移除它。
  - 账本把运费记给老挝（科目 `co2_transit_rail_freight`），封存服务按越南 store 的对偶价格结算。
  - 求解后的 `CO2_FLOWS.json` 新增 `lao_transit_vn_store`。
- **局限：** 敏感性 `lao_transit_destination=existing_port` 中，过境终点在泰国港口的老挝节点没有对应的"进入泰国国内封存"链路（只按指令实现越南）。

### 3.4 (d) SG–VN、SG–KH（第二批敏感性）

- **开关：** `research.corridors.optional_sg_vn_kh: off`（主算）| `on`。打开时，`OPTIONAL_CORRIDORS_S4F2.csv` 的两条直流候选会追加到走廊表：
  - SG2 0–VN2 0：1,212.6 km，海底份额 0.769；
  - KH2 0–SG2 0：1,330.2 km，海底份额 0.847。
- **管道候选：** 氢 / CO₂ / 气候选沿新拓扑同样生成。
- **构建核对：** 构建通过（`integrated_sg_vn_kh`）：两条直流加入，一体化跨境直流 6 条（主算 4 条），氢管道候选 57 条（主算 55 条）。
- **登记：** 注册表 `s4f2_sensitivity_sg_vn_kh`；未运行。

### 3.5 (g) `tests/transport` 的 17 个既有失败

- **原因（VERIFIED）：** `tests/transport/test_shipping_allocation.py` 是脚本式测试，在模块顶层用 `sys.argv.pop(1)` 取两个命令行参数（仓库根目录、结果文件）。在 pytest 下它把 pytest 的参数当成了根目录。
- **不是逻辑错误：** 以原脚本方式运行（`python tests/transport/test_shipping_allocation.py . <结果>`），17 项全部通过。不触发停止条件。
- **修正：** 只在作为脚本运行时读命令行参数；在 pytest 下取本文件所在的仓库根目录，不改动 `sys.argv`。脚本用法保持不变。
- **结果：** 整个 `tests/` 目录在 pytest 下 516 项全部通过。

## 4. 作者 `readjust_existing_interconnections` 改过 `s_nom` 的跨境交流线（只记录，未修改）

- **来源：** 作者脚本 `research/00_source_provenance/official/author_run/scripts/final_asean_adjustment.py` 第 296–347 行（SHA256 dc89f99e…），开关在 `configs/config.asean.yaml` 第 208 行（`readjust_existing_interconnections: true`）。
- **作者的做法：**
  - 选出 `build_year ≤ 2024` 的跨境交流线；
  - 按 9 个国家对（第 303–313 行，方向敏感）把 AIMS 2024 的存量总量按长度比例分摊到各线，`s_nom` 与 `s_nom_min` 都设为这个值；
  - **只改交流线，不改直流链路，也不改 `num_parallel`、`x`、`r`。**
- **复现：** `scripts_project/s4f_2_readjust_audit.py` 在冻结底网（SHA256 6772c674…）上复现了这一选线条件，得到 19 条线、8 个国家对。冻结底网中没有 LA–MM 交流线，APG17 是 S3 才加的。
  - 各国家对的 `s_nom` 之和与作者的 AIMS 总量逐对相等（VERIFIED）：ID–MY 230、KH–LA 300、KH–TH 250、KH–VN 200、LA–TH 955、LA–VN 1、MY–SG 525、MY–TH 380 MW。
  - 全部线路都是聚类后的 380 kV 代表线型 `Al/St 240/40 4-bundle 380.0`（i_nom 2.58 kA）。
- **列的含义：**
  - **按线型的额定：** √3 × v_nom × i_nom × num_parallel，取 bus0 的 v_nom。
  - **交流环路：** 该线位于冻结底网交流线图的环上，即不是桥；同一对母线之间的并联线也算。
  - **经第三国交流通路：** 去掉该国家对的全部交流线后，两端母线仍有交流通路相连，也就是必须经过第三国。

| 国家对 | 线路 | s_nom（MW） | √3·v_nom·i_nom·num_parallel（MW） | 比值 | x（Ω） | num_parallel | 长度（km） | 交流环路 | 同国家对其他交流线 | 经第三国交流通路 |
|---|---|---|---|---|---|---|---|---|---|---|
| ID-MY | 23 | 230.00 | 11,286.3 | 0.0204 | 14.86 | 6.646 | 401.5 | 否 | 0 | 否 |
| KH-LA | 43 | 300.00 | 2,184.1 | 0.1374 | 55.38 | 1.286 | 289.5 | 是 | 0 | 是 |
| KH-TH | 47 | 250.00 | 927.8 | 0.2695 | 159.66 | 0.546 | 354.6 | 是 | 0 | 是 |
| KH-VN | 39 | 200.00 | 2,055.6 | 0.0973 | 47.87 | 1.211 | 235.6 | 是 | 0 | 是 |
| LA-TH | 49 | 69.93 | 513.9 | 0.1361 | 223.40 | 0.303 | 274.8 | 是 | 8 | 是 |
| LA-TH | 52 | 120.00 | 104.8 | 1.1454 | 1880.32 | 0.062 | 471.6 | 是 | 8 | 是 |
| LA-TH | 53 | 101.91 | 13,406.1 | 0.0076 | 12.48 | 7.895 | 400.5 | 是 | 8 | 是 |
| LA-TH | 55 | 89.54 | 15,654.4 | 0.0057 | 9.39 | 9.219 | 351.9 | 是 | 8 | 是 |
| LA-TH | 56 | 91.30 | 256.9 | 0.3553 | 583.31 | 0.151 | 358.8 | 是 | 8 | 是 |
| LA-TH | 58 | 70.91 | 11,406.3 | 0.0062 | 10.21 | 6.717 | 278.7 | 是 | 8 | 是 |
| LA-TH | 61 | 95.15 | 12,406.2 | 0.0077 | 12.59 | 7.306 | 373.9 | 是 | 8 | 是 |
| LA-TH | 62 | 203.28 | 256.9 | 0.7911 | 1298.73 | 0.151 | 798.9 | 是 | 8 | 是 |
| LA-TH | 66 | 112.97 | 9,121.6 | 0.0124 | 20.33 | 5.372 | 444.0 | 是 | 8 | 是 |
| LA-VN | 59 | 0.39 | 4,468.7 | 0.0001 | 48.15 | 2.632 | 515.1 | 是 | 3 | 是 |
| LA-VN | 60 | 0.20 | 5,585.9 | 0.0000 | 20.07 | 3.289 | 268.4 | 是 | 3 | 是 |
| LA-VN | 63 | 0.17 | 1,966.2 | 0.0001 | 49.05 | 1.158 | 230.9 | 是 | 3 | 是 |
| LA-VN | 64 | 0.24 | 983.1 | 0.0002 | 137.34 | 0.579 | 323.2 | 是 | 3 | 是 |
| MY-SG | 92 | 525.00 | 513.9 | 1.0216 | 195.16 | 0.303 | 240.1 | 否 | 0 | 否 |
| MY-TH | 91 | 380.00 | 11,142.1 | 0.0341 | 10.32 | 6.562 | 275.4 | 否 | 0 | 否 |

### 读表要点（INFERENCE，供用户判断）

1. **比值普遍远小于 1：** LA–VN 四条约 0.0001；LA–TH 七条 0.006–0.36；ID–MY 23、MY–TH 91 约 0.02–0.03。作者只把容量压到 AIMS 总量，阻抗（`x`）仍对应聚类时累加出的大量并联回路。在线性潮流（基尔霍夫）约束下：
   - 这些线的电抗很小，会按阻抗分得大量潮流，但容量很小，很快成为约束；
   - 在环路中，这会限制整个环路的潮流分布，或者促使模型在这些线上扩建。
2. **16 条在交流环路中：** KH–LA、KH–TH、KH–VN、LA–TH、LA–VN 都可以经第三国形成环路。以下三条是桥，不在环路中：
   - ID–MY 23（Sarawak–West Kalimantan）、MY–SG 92、MY–TH 91（S4F 已设为 80 MW）；
   - 它们的潮流只由两端的功率平衡决定，阻抗不影响分配。
   - S4E-1 的相邻候选线一旦建设，会形成新的环路；上表的环路判断只针对 2025 年的存量网络。
3. **少数线的比值大于或接近 1：** LA–TH 52（1.145）、MY–SG 92（1.022）、LA–TH 62（0.791）。这些线的 `s_nom` 与线型额定大致相符，或略高于线型额定。
4. **单条上限的口径：** S4F 主算的单条扩建上限按 `s_nom + 20,000 MW` 计，`s_nom` 取作者调整后的值，阻抗不随扩建更新（PyPSA 线性潮流的常规做法）。
5. **本节没有修改任何一条线。** 是否处理以及怎样处理，列为用户决定事项（§7 第 1 项）。可选做法：
   - 保持现状；
   - 按 `s_nom / 线型额定` 同比缩放 `num_parallel` 与阻抗，使电气参数与容量一致；
   - 只对处在环路中的线做上述调整。

## 5. 冒烟（S4F-3，档案 A，56×3h，代码 d9bc8012，提交 7e09744d）

| 运行 | 状态 | 目标（EUR） | 相对 S4E | LP 列 / 非零元 | barrier | 墙钟 / 峰值 |
|---|---|---|---|---|---|---|
| 一体化 STEPS | optimal | 6.39063e11 | +89.0 亿（+1.41 %） | 648,478 / 3.22 M | 168 次 / 223 s | 285 s / 3.88 GiB |
| 不互联 STEPS | optimal | 6.93191e11 | +163.6 亿（+2.42 %） | 635,539 / 3.14 M | 150 次 / 170 s | 225 s / 3.54 GiB |
| 一体化 NZE | optimal | 5.38893e11 | +86.5 亿（+1.63 %） | 648,478 / 3.22 M | 117 次 / 152 s | 210 s / 3.85 GiB |

### 5.1 单条上限生效后的输电建设（与 S4E 冒烟对比，VERIFIED）

| 指标 | 一体化 S4F | 一体化 S4E | 不互联 S4F | 不互联 S4E |
|---|---|---|---|---|
| 全部线路 + DC 链路的新增容量 | 868 GW | 1,469 GW | 356 GW | 1,060 GW |
| 新走廊（S4E-1 候选与 APG 直流）合计 | 263.0 GW（37 个全部建设） | 301.3 GW | 24.7 GW（国内 3 个） | 83.3 GW |
| 新走廊单条最大 | 20.0 GW（ID_Kalimantan4 9–MY_Sarawak4 0，触及上限） | 40.5 GW（#18a） | 20.0 GW（#18a，触及上限） | 79.3 GW（#18a） |
| 触及上限的组件（新增 ≥ 上限 − 1 MW） | 11（跨境 5、国内 6） | — | 6（全部国内） | — |

- **触及上限的组件：**
  - 一体化：
    - 跨境 5 个：ID_Kalimantan4 9–MY_Sarawak4 0（相邻候选）、LA–TH 61（存量 95 MW）、LA–VN 60（存量 0.2 MW）、MY–SG 92（525 MW）、MY–TH 91（80 MW）；
    - 国内 6 个：ID 1（爪哇）、TH 99 / 100、VN 105 / 108 / 109。
  - NZE：与一体化相同。
  - 不互联：ID 1、13、22，#18a 加里曼丹–爪哇直流，TH 100，VN 107。
  - LA–TH 61 与 LA–VN 60 都在作者 readjust 清单里（§4）：存量被压得很低，而电抗很小、处在环路中。
- **主要新走廊（一体化）：**
  - #18a 19.6 GW（S4E 40.5）、#18b 15.0 GW、#4（北干巴鲁端）14.2 GW（S4E 巴淡端 0.49 GW）、#3 13.3 GW；
  - LA2 0–VN2 3 12.2 GW、KH2 2–TH2 3 12.0 GW；
  - #16 7.5 GW（S4E 4.5）、#7 MY–PH 3.8 GW（S4E 5.4）、BN–MY 2.4 GW、ID–TL 0.23 GW。
- **跨境管道（建设 > 1 MW 的条数，一体化）：** 氢 19、CO₂ 18、气 41。
- **TH–MY：** 线路 91 从 80 MW 扩到上限 20,080 MW；Khlong Ngae–Gurun 从 300 MW 扩到 2,000 MW（未触及上限）。
- **成本：** 单条上限使三个运行的目标值都升高 1.4–2.4 %。不互联升得更多，因为国内大扩建（#18a、爪哇、越南）受限。
- **局限：** 冒烟只有一月的一周（56 个时段），规模不能据此判断（第 47 项）；上限是否真正起约束作用，要看 365×24h 的结果。

### 5.2 分国账本（不互联 − 一体化，bn EUR）与 B16

| 国家 | KH | LA | VN | TH | MY | ID | PH | BN | TL | MM | SG | 燃料舱 | 合计 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S4F | 2.25 | 3.96 | 21.97 | 6.20 | 5.14 | 9.55 | 1.05 | 0.80 | 0.27 | 1.01 | 1.96 | −0.04 | **54.13** |
| S4E | 2.27 | 2.64 | 20.43 | 4.77 | 7.54 | 2.10 | −0.61 | 0.59 | 0.14 | 0.82 | 3.12 | 2.84 | 46.66 |

- **合计：** 54.13 bn EUR，等于 B6 差值。
- **ID：** 2.10 → 9.55，主要因为不互联中 #18a 与爪哇国内线受上限约束。
- **PH：** 由 −0.61 变为 +1.05，第一次有了正的互联价值。按第 97 项 e，正式结果出来后再用账本明细分析。
- **LA：** 2.64 → 3.96。
- **B16：** 相对误差 3.6e-11 / 3.4e-12 / 7.2e-13；区域池剩余 22.9 / −2.6 / 0.4 EUR。

### 5.3 CO₂ 流向

| 运行 | 东盟内船运（Mt/a） | 运费（亿 EUR） | 主要流向 | 老挝进越南封存（Mt/a） | 东盟外 |
|---|---|---|---|---|---|
| 一体化 | 137.9（S4E 144.4） | 19.9 | VN→MY 59.8、VN→BN 45.4、VN→ID 29.9、MM→ID 2.8 | 0 | 0 |
| 不互联 | 298.4（S4E 284.0） | 40.6 | SG→ID 92.1、VN→ID 66.5、VN→MY 54.7、MM→ID 49.0、KH→TH 22.0、VN→BN 10.1、KH→ID 3.9 | **7.50**（LA2 3 5.65、LA2 0 1.82、LA2 4 0.02；运费 0.73 亿） | 0 |
| 一体化 NZE | 145.8（S4E 153.2） | 21.1 | VN→MY 59.7、VN→BN 43.0、VN→ID 40.2、MM→ID 2.8 | 0 | 0 |

- **不互联中的老挝 CO₂：** 全部改走"铁路过境 → 越南国内封存"，与 S4E 中老挝过境后船运的量相当（S4E：LA→PH 5.65、LA→MY 1.94 Mt），因为陆运段比船运便宜。
- **越南国内封存在三个运行中都用满（236 Mt/a）：** 老挝 CO₂ 占用越南的上限，越南自身更多地船运出口（不互联 VN→ID 由 S4E 的 3.2 增至 66.5 Mt）。
- **一体化：** 老挝不用铁路过境，CO₂ 经跨境 CO₂ 管道进入泰国封存（LA→TH 管道净流量约 38.0 Mt，VERIFIED，`CO2_FLOWS.json`）。其中约 28.4 Mt 是经 VN→LA 管道转运过来的越南 CO₂，因为越南自身封存已经用满。

### 5.4 门槛

- **B5：** 通过，不互联中跨境组件为 0。
- **B6：** 通过，541.3 亿 EUR，7.8 %。
- **三个运行 `all_passed_solver_tolerances` 都通过，包括 `A1_A2_S4B`。** S4E 中一体化与 NZE 的 `A1_A2_S4B` 未过（`Line-s` 平稳性 39 / 37 个），这次通过，平稳性最大归一化残差 6.5e-8 / 7.6e-8（INFERENCE：单条上限去掉了少数特大线路的数值尺度问题）。
- **旧口径：** `A1_A2` 与 `A3`（BarConvTol 口径）仍未过，与以前同一性质。

## 6. 工作原则第 8 条检查汇总

| 建模决定 | 是否系统性地把成本推给或减轻某些国家 | 依据 / 量级 | 处理 |
|---|---|---|---|
| 单条扩建上限 20,000 MW（第 96 项） | 两个情景同一规则。受约束的大多是国内存量线（S4E 冒烟：一体化 22 个超限组件中 14 个国内、不互联 16 个全部国内），而且集中在 TH、VN、ID，会提高这些国家国内输电的边际成本 | S4E 冒烟超限表；S4F 冒烟触及上限的组件见 §5 | 已实施（PyPSA-Eur 实际做法） |
| 交流、直流同一上限，不用 `links.max_extension` | 直流（跨海、国内跨岛）比 PyPSA-Eur 电力流程的 30,000 MW 更紧；受影响的是靠跨岛直流互联的国家（ID、MY、PH） | `prepare_sector_network.py` 第 6415 行 | 已实施（用户同意） |
| TH–MY 存量对齐 APG 380 MW（第 97 项 a） | 原 2,645.6 MW 高估了存量，等于免费给 TH、MY 约 2.27 GW 互联容量 | §3.1 | 已实施；`frozen_base` 作对照 |
| 线路 91 = 80 MW（C 级，聚类伪影） | TH–MY 交流代表线成员不是 Sadao–Chuping，80 MW 只是总量口径 | 停止 01 | 已实施；成员结构未改（§7 第 1 项） |
| 作者 readjust 的 19 条跨境交流线 | 容量压到 AIMS 总量但阻抗未变，环路中的线（LA–TH、LA–VN、KH–*）会扭曲潮流分配，影响 LA、KH、TH、VN 的互联价值 | §4 | 只记录（§7 第 1 项） |
| #4 端点改为北干巴鲁（第 97 项 b） | 苏门答腊本岛–马来半岛的连接长度由 285 km 增至 432 km，成本更高；不再与 #16 共用巴淡母线 | §3.2 | 已实施 |
| 老挝进越南封存（第 97 项 c） | LA 在不互联中多了一条出路（陆运段 9.7–24.6 EUR/t + 越南封存 30），占用越南的年注入上限 | §3.3 | 已实施；越南封存容量是否被挤占见 §5 |
| SG–VN、SG–KH 不进主算 | 新加坡只能经马来半岛和苏门答腊互联 | §3.4 | 第二批敏感性 |

## 7. 需要用户决定的事项

1. **作者 readjust 改过的 19 条跨境交流线（§4，只记录）：** 容量被压到 AIMS 总量，但 `num_parallel` 与阻抗没有改，`s_nom` 与线型额定之比低至 0.0001–0.03。其中 16 条处在交流环路中。
   - 冒烟里 LA–TH 61（95 MW）和 LA–VN 60（0.2 MW）都扩建到了单条上限。
   - TH–MY 线路 91 也是聚类伪影：成员线不是 Sadao–Chuping，S4F 只改了容量。
   - 可选做法：
     - 保持现状；
     - 按 `s_nom / 线型额定` 同比缩放这些线的 `num_parallel` 与阻抗，使电气参数与容量一致；
     - 只对处在环路中的 16 条做上述调整；
     - 回到聚类前，按 OSM / AIMS 重新确定跨境存量线的组成（工作量较大，可能需要重建底网）。
2. **`apg_plans` 敏感性的取值规则（§2.2）：**
   - 规划上限取 `total_MW` 与 2040 预测中较大者，#16 并入 #5 的 3,400 MW；
   - 组按项目两端区域划分；没有数字的项目（#8a、SG–VN、SG–KH）沿用 PyPSA-Eur 上限。
   - 是否采用，或改为只取 `total_MW`、只取 2040 预测。
3. **老挝过境的 `existing_port` 敏感性：** 过境终点在泰国港口（是拉差）的老挝节点没有"进入泰国国内封存"的链路。第 97 项 c 只针对越南，是否按同一原则补上泰国。
4. **上云前需要用户提供的信息与授权：** 实例访问方式、许可文件路径、运行方式与授权原文，见 §10。

本步不需要决定、已记录的事项：
- 联盟研究范围：交付后与第 14 项一并请师哥判断（第 97 项 f）。
- PH 互联价值：S4F 冒烟中由负转正（+1.05 bn）；按第 97 项 e，正式结果后用账本明细分析。
- 越南封存在三个冒烟运行中都用满：老挝进越南封存占用越南的年注入上限，按第 97 项 c 的设计执行，S4F 冒烟中只在不互联出现，为 7.5 Mt。

## 8. 下载与资源（工作原则第 7 条）

- **下载：** 无。本步只用了已入库的资料：
  - PyPSA-Eur v2025.07.0 配置与 `prepare_sector_network.py`；
  - AIMS 输电项目表；
  - OSM 预制线路表；
  - pypsa-asean 本地运行的网络与映射；
  - 作者原始运行脚本。
- **本机计算：**
  - 构建单次约 47 s / 0.7 GB；
  - 56×3h 求解单次 210–285 s，峰值 3.5–3.9 GiB；
  - 线路 91 核查约 3.5 分钟；
  - 没有超过 1 小时或约 8 GiB 的计算。
- **其他约束：**
  - 没有云端操作，没有正式求解。
  - Gurobi 许可只通过 `GRB_LICENSE_FILE` 引用。
  - 入库证据与部署包都扫描过许可特征串（结果见 §10.1）。
- **测试：** `tests/research` 499 项 通过；整个 `tests/` 516 项 全部通过，`tests/transport` 的 17 项已修复。

## 9. 交付清单（`work/p1_step4f_20261017/`，仓库镜像 `research/06_scope_redesign/p1_step4f_20261017/`）

- **报告与证据：** `S4F_REPORT.md`（本文件）、`S4F_EVIDENCE.json`、`S4F_PROGRESS.md`、`S4F_STOP_01_LINE91.md`、`DOWNLOAD_LIST.csv`（沿用 S4E 并加 `status_s4f` 列，本步无下载）。
- **部署：**
  - `CLOUD_RESOURCE_ESTIMATE.md`（§15）、`CLOUD_DEPLOY_STEPS.md`；
  - 部署包脚本 `cloud_package/`；
  - 打包产物 `cloud_package_dist/`（不进 git）。
- **分步证据** `evidence/s4f_0` … `evidence/s4f_4`：
  - 注册表片段；
  - PyPSA-Eur 核对与超限表；
  - TH–MY 修正表、走廊 / 海底份额 / 长度分摊表、作者 readjust 清单；
  - 构建状态；
  - 冒烟汇总；
  - 外推、重建状态与包清单。
- **代码：**
  - 新模块：`scripts_project/s4f_layers.py`；
  - 数据脚本：`s4f_0_data.py`、`s4f_1_data.py`、`s4f_1_excess.py`、`s4f_2_corridors.py`、`s4f_2_length_shares.py`、`s4f_2_readjust_audit.py`；
  - 汇总脚本：`s4f_3_summary.py`、`s4f_4_collect_evidence.py`；
  - 修改：`s2_network.py`、`s2_solve.py`、`assembly_components.py`、`scenario_network.py`、`s4d_ledger.py`、`s4e_layers.py`、`d1_registry.py`、`configs/research/baseline.yaml`；
  - 测试：`tests/research/test_s4f_1.py`、`test_s4f_2.py`；修改 `test_s4e_1.py`（主走廊表固定点）、`tests/transport/test_shipping_allocation.py`。
- **注册表：** 片段 `s4f_0`、`s4f_1`、`s4f_2`。
- **审阅 ZIP：** `S4F_REVIEW.zip`，逐成员附 SHA256 与 CRC 清单。

## 10. 上云前清单（S4F-5）

### 10.1 部署包

- **位置：** `work/p1_step4f_20261017/cloud_package_dist/`（不进 git）。
- **代码提交：** 7e09744dc89324c472497cce45025add19a11b6b（`code_7e09744d.tar.gz`）。
- **规模：** 共 15 个文件，上传总量 **232,095,769 B**（221.3 MiB）。
- **校验：** 上传后在实例上运行 `sha256sum -c SHA256SUMS`。

| 文件 | SHA256 |
|---|---|
| `COMMIT` | `4bd70d53d9fbce005f3507b48458a8f956df7556fb583afb0f9c4f9073a5bd9e` |
| `DATA_CONFIG_MANIFEST.json` | `392451df9ba15548d062cafb7cf3e47243b44453a8b5d081800f97c884b3bd34` |
| `code_7e09744d.tar.gz` | `e7b94af483b910c0d74b8bcde2e7f5fd00fb3fbc4416e636cd739c3e71765a44` |
| `conda_explicit_linux64.txt` | `62f2935b6677194a298b44d12cbb1cc0a85d1566cd4e28aea55136fd86dc3e0f` |
| `environment_pypsa-earth.yml` | `f2d28554d08b48bda83037b14ebc1d201b550283e1c36dc4b2657d31f0fe67a3` |
| `networks/disconnected_365_24h_unsolved.nc` | `a8a159f54cf3256a3c32b8beeccaaf743b98d31e8bd7949ff9d0e4080e159923` |
| `networks/disconnected_BUILD_RECEIPT.json` | `cd1193b5c0ba7073322b2edfd66e76d12a2364212d28e20ccbb3a4f494ddeb5d` |
| `networks/disconnected_gap_diagnostic_365_24h_unsolved.nc` | `d89caf9a7ecddd0ac0d5d9bd6e225f8d794335947de4d5326f95e0d24ac84e58` |
| `networks/disconnected_gap_diagnostic_BUILD_RECEIPT.json` | `f3d336dc7472edf339eabbc407d0dd435a6ea9447a77ccf818c1983ed500f1bf` |
| `networks/integrated_365_24h_unsolved.nc` | `e3dcd911702903d2aa259fb5912ace8fba2e28a0c8a259e64893d46ccce47c1b` |
| `networks/integrated_BUILD_RECEIPT.json` | `14ff7871245522dea29a4d993767e4d382c20ba71594dc3b53f2d936c9e6434a` |
| `networks/integrated_nze_365_24h_unsolved.nc` | `b263ac8f4151ad2696bdb7cc18efe05a89e98e25810cd947a569a7180a530db7` |
| `networks/integrated_nze_BUILD_RECEIPT.json` | `7a9308b1166c294c25a3ca6514123476725f260972f93a970b23e76c7a21ef6f` |
| `preflight.sh` | `742a671e6e688856b5cb1b87d76c01a506d2416c5f018214bedf451b694a1ae0` |
| `run_365x24h.sh` | `e663c865b7ce4fe0e1649637de94a1401263e1ef0ad9769d44fb70de55731bf2` |
| `PACKAGE_MANIFEST.json` | `faf48932c3f578a3dbef2c397e7635a1352679ee26353b5871ba40d3e2d50359` |

### 10.2 实例规格（下限 / 推荐；AutoDL 按内存与 CPU 核数选机型）

| 运行方式 | 内存（下限 / 推荐） | vCPU | 数据盘（`/root/autodl-tmp` 可用） | 预计墙钟（不含诊断；含诊断） |
|---|---|---|---|---|
| 串行 | 36 GB / ≥ 48 GB | ≥ 8 | ≥ 35 GB | 2.0–2.8 h（悲观 4.0 h）；含诊断 3.1–4.4 h |
| 两通道 | 72 GB / ≥ 96 GB | ≥ 16 | ≥ 45 GB | 1.4–1.9 h（竞争 +10–20 %；悲观 2.8 h）；含诊断 1.8–2.5 h |
| 三通道 | 104 GB / ≥ 128 GB | ≥ 24 | ≥ 50 GB | 0.8–1.1 h（悲观 1.6 h）；含诊断 1.8–2.5 h |

- 单运行墙钟（INFERENCE，`CLOUD_RESOURCE_ESTIMATE.md` §15）：一体化 48–67 min（悲观 98）、不互联 37–52 min（悲观 75）、NZE 34–47 min（悲观 68）、不互联诊断（只在需要时）约 70–100 min（悲观 145）。
- 单运行峰值内存中值 / 上限：23 / 32.3 GiB。
- 每运行 8 线程，Gurobi TimeLimit 10,500 s，墙钟上限 3 h。

### 10.3 需要用户提供的信息

1. **实例访问方式：** 由用户自己经 SSH 或 JupyterLab 登录实例并执行各步骤。Claude Code 不连接云端，也不需要、不接收登录密码或密钥。用户只需确定所选运行方式（serial / lanes2 / lanes3）与实例规格，并写入授权原文。
2. **许可文件的放置路径：** 例如 `/root/.gurobi/gurobi.lic`（权限 600）。运行时只通过 `GRB_LICENSE_FILE` 引用，Claude Code 不读取、不复制、不输出其内容。WLS 许可需要实例能 HTTPS 出站访问 Gurobi 令牌服务器。
3. **结果目录：** 下载后在本机存放的位置，建议 `work/p1_step4f_20261017/cloud_results/`。
4. **首次正式运行的授权原文：** 见 10.4。

### 10.4 首次正式运行的授权原文模板

> 我授权在 AutoDL 实例（规格：＿＿＿；区域：＿＿＿）上，用部署包 `cloud_package_dist`（代码提交 7e09744dc89324c472497cce45025add19a11b6b，`SHA256SUMS` 已核对）执行 S4F 首批 365×24h 正式运行：一体化 STEPS、不互联 STEPS、一体化 NZE，以及仅在不互联主算非最优时自动运行的不互联诊断。
> 求解档案 A（`--solver-profile formal_barrier`），运行方式 ＿＿＿（serial / lanes2 / lanes3）。每运行 Gurobi TimeLimit 10,500 s，墙钟上限 3 h；不重试、不改参数、不 warm start。
> 许可文件位于 ＿＿＿，只通过 `GRB_LICENSE_FILE` 引用。结果打包下载后带回本机审阅。
> 第二批敏感性与联盟研究不在本次授权范围内。
> 授权人：＿＿＿；时间：＿＿＿（SGT）。

运行命令（授权后由用户在实例上执行，`--auth` 填入上述原文与时间）：

```bash
PY=$PY GRB_LICENSE_FILE=<许可路径> bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth "<授权原文与时间>"
```
